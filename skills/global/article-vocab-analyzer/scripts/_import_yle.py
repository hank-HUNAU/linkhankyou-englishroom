# -*- coding: utf-8 -*-
"""导入剑桥少儿英语官方词表（Pre A1 Starters / A1 Movers / A2 Flyers）。

来源：Cambridge English 官方 wordlist PDF（2018 版，Pre A1–A2 Young Learners）。
用法：python _import_yle.py <yle-wordlist.pdf> [输出目录]
产出：wordlists/A1_Starters.json, A1_Movers.json, A2_Flyers.json（格式同 KET.json）

分段（2018 版 PDF 页码，1 基）：Starters p4–7 / Movers p8–11 / Flyers p12–15。
解析策略：全文 token 流 + POS 边界扫描（PDF 常把多条词挤在一行，逐行解析不可靠）。
"""
import re, json, os, sys
from pypdf import PdfReader

POSW = {"n", "v", "adj", "adv", "det", "prep", "conj", "pron", "excl", "dis", "int", "title", "poss"}
PAGE_HDR = re.compile(r"^\d*\s*(Pre A1 Starters|A1 Movers|A2 Flyers).*wordlist")
LETTER = re.compile(r"^[A-Z]$")
KEYLINE = re.compile(r"^(adj|adv|conj|det|dis|excl|int|n|poss|prep|pron|v)\s+(adjective|adverb|conjunction|determiner|discourse|exclamation|interrogative|noun|possessive|preposition|pronoun|verb)")
NOTE = ("(No words", "Letters & numbers", "Numbers Candidates", "Names ", "Candidates will be expected")

def postfix(entries):
    """修补 PDF 丢失 POS 的粘连条目（a.m./p.m. (for time)）。"""
    out = []
    for h, p in entries:
        m = re.match(r"^([ap]\.m\. \(for time\))\s+(.+)$", h)
        if m:
            out.append((m.group(1), "adv")); out.append((m.group(2), p))
        else:
            out.append((h, p))
    return out

def _item(toks, k):
    n = len(toks)
    if k >= n: return None
    t = toks[k].lower().strip(".,")
    if t == "poss":
        k += 1
        if k >= n or toks[k].lower().strip(".,") not in POSW: return None
        k += 1
    elif t in POSW:
        k += 1
    else:
        return None
    if k + 1 < n and toks[k].lower() == "of" and toks[k + 1].lower() in ("place", "time"):
        k += 2
    return k

def match_pos(toks, i):
    n = len(toks)
    end = _item(toks, i)
    if end is None: return None
    while end < n and toks[end] == "+":
        e2 = _item(toks, end + 1)
        if e2 is not None:
            end = e2; continue
        if end + 1 < n and toks[end + 1].lower() in ("time", "place"):
            end += 2; continue
        break
    return end

def clean_lines(reader, pages):
    out, skip_next = [], False
    for i in pages:
        for ln in (reader.pages[i].extract_text() or "").splitlines():
            ln = ln.replace("\u00a0", " ").strip()
            if not ln or PAGE_HDR.match(ln) or LETTER.match(ln) or KEYLINE.match(ln): continue
            if ln in ("Numbers", "Names"):      # 说明标题行，其下一行为名单列表
                skip_next = True; continue
            if skip_next:
                skip_next = False; continue
            if ln.startswith(NOTE): continue
            out.append(ln)
    return out

def scan(tokens):
    entries, buf = [], []
    i, n = 0, len(tokens)
    while i < n:
        m = match_pos(tokens, i)
        if m is not None and buf:
            entries.append((" ".join(buf), " ".join(tokens[i:m])))
            buf = []; i = m
        else:
            buf.append(tokens[i]); i += 1
    if buf: entries.append((" ".join(buf), ""))  # 尾部残留（如 a.m. 丢 POS）
    return entries

SECS = [("A1_Starters", 3, 7, "Pre A1 Starters"), ("A1_Movers", 7, 11, "A1 Movers"), ("A2_Flyers", 11, 15, "A2 Flyers")]

def main():
    pdf = sys.argv[1]
    outdir = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wordlists"))
    reader = PdfReader(pdf)
    for name, a, b, label in SECS:
        toks = " ".join(clean_lines(reader, range(a, b))).split()
        raw = postfix(scan(toks))
        seen, entries = set(), []
        for h, p in raw:
            h = h.strip()
            if not h or h.lower() in seen: continue
            # 名单列表残留：无 POS 且含多个首字母大写词
            if not p and sum(1 for t in h.split() if t[:1].isupper()) >= 2: continue
            seen.add(h.lower())
            entries.append({"head": h, "pos": (p.split()[0] if p else ""), "raw": f"{h} ({p})" if p else h})
        json.dump({"source": f"Cambridge English {label} (2018)", "entries": entries, "forms": []},
                  open(os.path.join(outdir, name + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[{name}] {label}: {len(entries)} 条（原始 {len(raw)}）")
        longs = [e["head"] for e in entries if len(e["head"].split()) > 4]
        if longs: print("   长 head 复核:", longs[:6])

if __name__ == "__main__":
    main()
