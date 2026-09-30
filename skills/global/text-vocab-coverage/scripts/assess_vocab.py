#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对任意课文做多词表词汇命中率检测（KET/PET/AWL/GSL 可插拔）。

用法:
  python assess_vocab.py --text "全文..."                          # 直接给课文
  python assess_vocab.py --file 课文.txt|课文.md                    # 读文件全文
  python assess_vocab.py --xlsx 文件.xlsx --sheet 句库 --col 2       # 读表格某列(0基)
  python assess_vocab.py --stdin                                    # 管道输入

输出(写到 cwd):
  vocab_report.xlsx  覆盖率总览(各词表+合并+超纲+专名/数字) + 每词表命中明细 + 超纲词
  vocab_report.json  结构化结果
词表: 读 <skill>/wordlists/registry.json 声明的词表; 把 AWL/GSL 做成同格式 json 放入即并行纳入。
词表格式: {"entries":[{"head":"...","pos":"...","raw":"..."}]}  (A2/B1 官方或自建均可)
判定: 数字/专名分流 -> 各词表短语整查(最长优先) -> 单词 lemma 候选(表面优先)逐词表命中。
Range(广度): 以"句"为单位记录跨句数。
"""
import os, sys, re, json, argparse, collections, glob

from entity_classify import load_lexicon, classify_proper

# ---------------- 词形归一 ----------------
IRREG = {
    "am": "be", "is": "be", "are": "be", "was": "be", "were": "be", "been": "be", "being": "be",
    "has": "have", "had": "have", "having": "have",
    "does": "do", "did": "do", "done": "do", "doing": "do",
    "says": "say", "said": "say", "went": "go", "gone": "go", "goes": "go",
    "saw": "see", "seen": "see", "made": "make", "making": "make",
    "took": "take", "taken": "take", "taking": "take",
    "got": "get", "gotten": "get", "gave": "give", "given": "give",
    "came": "come", "found": "find", "left": "leave", "thought": "think", "thoughts": "thought",
    "bought": "buy", "brought": "bring", "told": "tell",
    "felt": "feel", "kept": "keep", "knew": "know", "known": "know",
    "put": "put", "ran": "run", "sat": "sit", "stood": "stand", "wrote": "write",
    "written": "write", "won": "win", "wore": "wear", "children": "child",
    "people": "person", "men": "man", "women": "woman", "feet": "foot",
    "teeth": "tooth", "mice": "mouse", "best": "good", "better": "good",
    "worst": "bad", "worse": "bad", "babies": "baby", "watched": "watch",
}
CONTR = {"can't": "can", "won't": "will", "shan't": "shall",
         "don't": "do", "doesn't": "do", "didn't": "do",
         "isn't": "be", "aren't": "be", "wasn't": "be", "weren't": "be",
         "hasn't": "have", "haven't": "have", "hadn't": "have",
         "couldn't": "can", "shouldn't": "should", "wouldn't": "will",
         "mustn't": "must", "mightn't": "might",
         "i'm": "be", "you're": "be", "we're": "be", "they're": "be",
         "i've": "have", "you've": "have", "we've": "have", "they've": "have",
         "i'll": "will", "you'll": "will", "he'll": "will", "she'll": "will",
         "they'll": "will", "we'll": "will", "it's": "it", "there's": "be"}
NUMBERS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
    "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety", "hundred", "thousand", "million", "billion",
}
TOK_RE = re.compile(r"[A-Za-z']+|\d+")

def tokenize(s):
    return TOK_RE.findall(s)

def base_word(tok):
    t = tok.lower()
    if t in CONTR: return CONTR[t]
    if t.endswith("'s"): t = t[:-2]
    elif t.endswith("s'"): t = t[:-2]
    elif t.endswith("n't"): t = t[:-2]
    elif "'" in t: t = t.split("'", 1)[0]
    return t

def stem_suffix(w):
    if w.endswith("ies") and len(w) > 3: return w[:-3] + "y"
    if w.endswith("es") and len(w) > 2:
        s = w[:-2]
        return s if s[-1] in "sxz" or s.endswith("ch") or s.endswith("sh") else s + "e"
    if w.endswith("s") and not w.endswith("ss") and len(w) > 2: return w[:-1]
    if w.endswith("ing"):
        b = w[:-3]
        cands = [b, b + "e"]
        if len(b) >= 2 and b[-1] == b[-2]: cands.append(b[:-1])
        for c in cands:
            if c and re.fullmatch(r"[a-z]+", c): return c
        return b
    if w.endswith("ed"):
        b = w[:-2]
        if len(b) >= 2 and b[-1] == b[-2]: b = b[:-1]
        for c in (b, b + "e"):
            if re.fullmatch(r"[a-z]+", c): return c
        return b
    if w.endswith("er"): return w[:-2]
    if w.endswith("est"): return (w[:-3] or w)
    return w

def lemmatize(tok):
    t = tok.lower()
    if t in IRREG: return IRREG[t]
    s = stem_suffix(t)
    if s == t: return t
    return IRREG.get(s, s)

def lemma_candidates(word):
    t = base_word(word)
    if not t: return []
    out = [t]
    if t in IRREG: out.append(IRREG[t])
    s = stem_suffix(t)
    if s != t: out.extend([s, IRREG.get(s, s)])
    if t.endswith("ing"):
        b = t[:-3]
        if len(b) >= 2 and b[-1] == b[-2]: out.extend([b + "e", b[:-1]])
        out.append(b)
    if t.endswith(("es", "s")) and len(t) > 2 and not t.endswith("ing"):
        out.append(t[:-1])
    return list(dict.fromkeys(c for c in out if re.fullmatch(r"[a-z]+", c)))

def split_head(head):
    parts = []
    for seg in head.lower().split("/"):
        seg = seg.strip()
        if seg: parts.append(seg)
    return parts or [head.lower().strip()]

# ---------------- 词表加载 ----------------
def load_wordlist(path):
    d = json.load(open(path, encoding="utf-8"))
    words, phrs, pos = set(), {}, {}
    for e in d["entries"]:
        hds = [e["head"]] + e.get("forms", [])
        for h in hds:
            for head in split_head(h):
                if " " in head:
                    phrs.setdefault(head, e["pos"])
                else:
                    words.add(head); pos.setdefault(head, e["pos"])
    return {"words": words, "phrs": phrs, "pos": pos, "src": os.path.basename(path)}

def discover_wordlists(skill_dir):
    wd = os.path.join(skill_dir, "wordlists")
    reg = os.path.join(wd, "registry.json")
    order = json.load(open(reg, encoding="utf-8"))["wordlists"] if os.path.exists(reg) else []
    order = [w["key"] for w in order]
    found = {os.path.splitext(os.path.basename(jf))[0]: jf
             for jf in glob.glob(os.path.join(wd, "*.json")) if os.path.basename(jf) != "registry.json"}
    keys = [k for k in order if k in found] + sorted(set(found) - set(order))
    return [(k, found[k], load_wordlist(found[k])) for k in keys]

# ---------------- 课文加载 ----------------
def load_sentences(args):
    if args.text:
        text = args.text
    elif args.stdin:
        text = sys.stdin.read()
    elif args.xlsx:
        import openpyxl
        wb = openpyxl.load_workbook(args.xlsx, read_only=True)
        ws = wb[args.sheet]
        return [str(r[args.col]).strip() for r in ws.iter_rows(min_row=2, values_only=True)
                if r[args.col] and str(r[args.col]).strip()]
    else:
        if not args.file: sys.exit("需提供 --text/--file/--xlsx/--stdin 之一")
        text = open(args.file, encoding="utf-8").read()
    sents = []
    for para in re.split(r"\n\s*\n", text):
        for s in re.split(r"(?<=[.!?])\s+", para.strip()):
            if s.strip(): sents.append(s.strip())
    return sents

# ---------------- 主判定 ----------------
def assess(sentences, wls):
    n = len(wls)
    lex = load_lexicon()
    per_key = [{} for _ in range(n)]
    hit_tok = [set() for _ in range(n)]
    out_items = []
    numbers_n = proper_n = 0
    for si, s in enumerate(sentences):
        toks = tokenize(s)
        n_l = len(toks)
        # 各词表短语整查(最长 5→2)
        for ki, (key, path, wl) in enumerate(wls):
            used = [False] * n_l
            for L in range(5, 1, -1):
                i = 0
                while i + L <= n_l:
                    if any(used[i + k] for k in range(L)):
                        i += 1; continue
                    seq = " ".join(t.lower() for t in toks[i:i + L])
                    if seq in wl["phrs"]:
                        a = per_key[ki].setdefault(("phrase", seq),
                            {"type": "phrase", "lemma": seq, "form": seq, "pos": wl["phrs"][seq],
                             "freq": 0, "nsent": set(), "examples": []})
                        a["freq"] += 1; a["nsent"].add(si)
                        if len(a["examples"]) < 2: a["examples"].append(s)
                        for k in range(L):
                            used[i + k] = True; hit_tok[ki].add((si, i + k))
                    i += 1
        # 逐 token 单词判定
        ti = 0
        while ti < n_l:
            t = toks[ti]
            if re.fullmatch(r"\d+", t) or base_word(t) in NUMBERS:
                numbers_n += 1; out_items.append(("num", t, base_word(t), [])); ti += 1; continue
            cands = lemma_candidates(t)
            hits = [ki for ki, (k, p, wl) in enumerate(wls)
                    if any(c in wl["words"] for c in cands)]
            is_cap = t[0].isupper()
            if not hits:
                fb = cands[0] if cands else (base_word(t) or t.lower())
                if is_cap:
                    etype, canon, end = classify_proper(toks, ti, lex)
                    proper_n += (end - ti)
                    for k in range(ti, end):
                        out_items.append(("ent", toks[k], canon, etype))
                    ti = end
                    continue
                else:
                    out_items.append(("out", t, fb, []))
            else:
                lm = next((c for c in cands if c in wls[hits[0]][2]["words"]), cands[0])
                out_items.append(("word", t, lm, hits))
                for ki in hits:
                    key, path, wl = wls[ki]
                    a = per_key[ki].setdefault(("word", lm),
                        {"type": "word", "lemma": lm, "form": t, "pos": wl["pos"].get(lm, ""),
                         "freq": 0, "nsent": set(), "examples": []})
                    a["freq"] += 1; a["nsent"].add(si)
                    if len(a["examples"]) < 2: a["examples"].append(s)
                    hit_tok[ki].add((si, ti))
            ti += 1
    return per_key, hit_tok, out_items, numbers_n, proper_n, len(out_items)

# ---------------- 报告 ----------------
def write_report(wls, per_key, hit_tok, out_items, numbers_n, proper_n, total, out_stem, source):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    thin = Side(style="thin", color="D9D9D9"); border = Border(left=thin, right=thin, top=thin, bottom=thin)
    hdr_fill = PatternFill("solid", fgColor="2E8B57"); hdr_font = Font(color="FFFFFF", bold=True)
    hit_fill = PatternFill("solid", fgColor="E2F0E6")
    xlsx = out_stem + ".xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "覆盖率"
    ws.append(["词表", "命中token", "token占比", "命中词条", "词表总词条"])
    for c in range(1, 6):
        cell = ws.cell(1, c); cell.fill = hdr_fill; cell.font = hdr_font
    for ki, (key, path, wl) in enumerate(wls):
        ws.append([key, len(hit_tok[ki]), "%.1f%%" % (100.0 * len(hit_tok[ki]) / total),
                   len(per_key[ki]), len(wl["words"]) + len(wl["phrs"])])
    merged = len(set().union(*hit_tok)) if hit_tok else 0
    ws.append(["合并命中", merged, "%.1f%%" % (100.0 * merged / total), "-", "-"])
    ws.append(["超纲", max(0, total - merged - numbers_n - proper_n),
               "%.1f%%" % (100.0 * max(0, total - merged - numbers_n - proper_n) / total), "-", "-"])
    ws.append(["实体/专名", proper_n, "%.2f%%" % (100.0 * proper_n / total), "-", "-"])
    ws.append(["数字", numbers_n, "%.2f%%" % (100.0 * numbers_n / total), "-", "-"])
    ws.append(["全部token", total, "100.0%", "-", "-"])
    for i, w in enumerate((14, 11, 12, 10, 12), 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    COL = ["词/短语", "词性", "类型", "频次", "跨句", "原文例句"]; WID = (26, 16, 8, 8, 8, 90)
    for ki, (key, path, wl) in enumerate(wls):
        heads = sorted(per_key[ki].values(), key=lambda a: (-a["freq"], a["lemma"]))
        sub = wb.create_sheet("命中-" + str(key))
        sub.append(["词表", "命中词条数", "共 %d 词条 · 课文:%s" % (len(heads), source)])
        for c in range(1, len(COL) + 1):
            cell = sub.cell(2, c); cell.fill = hdr_fill; cell.font = hdr_font
        sub.append(COL)
        for a in heads:
            sub.append([a["lemma"], a["pos"], "短语" if a["type"] == "phrase" else "单词",
                        a["freq"], len(a["nsent"]), a["examples"][0] if a["examples"] else ""])
            for c in range(1, len(COL) + 1):
                cell = sub.cell(sub.max_row, c); cell.border = border; cell.fill = hit_fill
        for i, w in enumerate(WID, 1):
            sub.column_dimensions[get_column_letter(i)].width = w
        sub.freeze_panes = "A4"
    oc = collections.Counter(it[2] for it in out_items if it[0] == "out")
    ws_o = wb.create_sheet("超纲词")
    ws_o.append(["词", "频次"])
    for c in range(1, 3):
        cell = ws_o.cell(1, c); cell.fill = hdr_fill; cell.font = hdr_font
    for w, c in oc.most_common():
        ws_o.append([w, c])
    for i, w in enumerate((24, 8), 1):
        ws_o.column_dimensions[get_column_letter(i)].width = w
    wb.save(xlsx)
    out = {"source": source, "total": total, "numbers": numbers_n, "proper": proper_n,
           "tokens": [{"kind": k, "form": f, "lemma": l, "hit": h} for k, f, l, h in out_items]}
    with open(out_stem + ".json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    return xlsx

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=None)
    ap.add_argument("--file", default=None)
    ap.add_argument("--xlsx", default=None)
    ap.add_argument("--sheet", default="C4 句库时间轴")
    ap.add_argument("--col", type=int, default=2)
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--out", default="vocab_report")
    a = ap.parse_args()
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wls = discover_wordlists(skill_dir)
    if not wls:
        sys.exit("未找到任何词表: %s/wordlists" % skill_dir)
    sents = load_sentences(a)
    if not sents:
        sys.exit("课文为空, 请提供课文输入")
    per_key, hit_tok, out_items, numbers_n, proper_n, total = assess(sents, wls)
    out_stem = os.path.join(os.getcwd(), a.out)
    xlsx = write_report(wls, per_key, hit_tok, out_items, numbers_n, proper_n, total, out_stem,
                        " | ".join(k for k, _, _ in wls))
    print("saved:", xlsx)
    print("词表:", " ".join("%s(%.1f%%)" % (k, 100.0 * len(h) / total) if total else k
                            for (k, p, wl), h in zip(wls, hit_tok)))

if __name__ == "__main__":
    main()