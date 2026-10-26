# -*- coding: utf-8 -*-
"""学生自主软分支·记忆词卡后处理
主技能 article-vocab-analyzer 的任务结果(分层+原句+归属+CEFR) → 逐词调在线词典(有道 jsonapi)
补全学生记忆数据 → 输出学生记忆词卡 xlsx。

学生记忆数据(技术文档 §7):
  原句照搬 | 该词在原句中的词性+本义 | 屈折/词形变化 | 同源派生1个
  英-英简义或译文 | 真实发音(音标+音频链接) | 难度锚点(层/CEFR) | 典型搭配1-2例

用法:
  python student_cards.py --file 课文.txt --out 学生记忆卡
  python student_cards.py --text "..." --out 卡            # 直接给文本
  python student_cards.py --file 课文.txt --limit 5        # 只对前几个词联网补全(调试)
  python student_cards.py --file 课文.txt --offline        # 断网: 只出主技能结果,不查词典
"""
import os, sys, re, json, io, glob, time, html, subprocess, urllib.request, urllib.parse, argparse

def _main_dir():
    """向上查找真实主技能目录(article-vocab-analyzer)，部署处与工作区均通用。"""
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        # 两种布局都认：<root>/skills/article-vocab-analyzer 与 <root>/article-vocab-analyzer（词汇教学技能包-*）

        for cand in (os.path.join(d, "skills", "article-vocab-analyzer"),
                     os.path.join(d, "article-vocab-analyzer")):
            if os.path.exists(os.path.join(cand, "scripts", "assess_vocab.py")):
                return os.path.abspath(cand)
        d = os.path.dirname(d)
    return None
MAIN = _main_dir() or os.path.abspath("article-vocab-analyzer")
ASSESS = os.path.join(MAIN, "scripts", "assess_vocab.py")
# worktree 平铺优先：本文件同级有 assess_vocab.py 时用它(开发版最新)，否则回退部署位
_flat = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assess_vocab.py")
if os.path.exists(_flat):
    ASSESS = _flat
WL = os.path.join(MAIN, "wordlists")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "Referer": "https://dict.youdao.com/"}

# ---------- 1. 调主技能，拿到 json(唯一lemma/layer/cefr) 与 report.xlsx(原句/词性) ----------
def run_main(text=None, file=None, stem="sb_tmp"):
    cmd = [sys.executable, ASSESS, "--out", stem]
    if text:
        cmd += ["--text", text]
    else:
        cmd += ["--file", file]
    subprocess.check_call(cmd)
    toks = json.load(io.open(stem + ".json", encoding="utf-8"))["tokens"]
    words = {}
    for t in toks:
        if t.get("kind") not in ("word", "out"):
            continue
        lm = t.get("lemma", "")
        if not lm:
            continue
        rec = words.setdefault(lm, {"layer": t.get("layer", ""), "cefr": t.get("cefr", ""), "forms": []})
        f = t.get("form", "")
        if f and f not in rec["forms"]:
            rec["forms"].append(f)
    # 从 report.xlsx 命中明细/超纲 提取 原句+词性
    try:
        import openpyxl
    except ImportError:
        return words, {}
    wb = openpyxl.load_workbook(stem + ".xlsx", read_only=True)
    meta = {}
    for sn in wb.sheetnames:
        ws = wb[sn]
        for row in ws.iter_rows(values_only=True):
            if not row or not row[0]:
                continue
            col = list(row)
            if sn.startswith("命中"):   # 词/短语|词性|类型|频次|跨句|CEFR|原文例句
                w = col[0]
                if w and isinstance(w, str) and len(w) < 40 and w not in meta:
                    meta[w] = {"pos": col[1] or "", "example": col[6] or ""}
            elif sn == "超纲词":        # 词|频次|CEFR|原文例句
                w = col[0]
                meta.setdefault(w, {"pos": "", "example": col[3] if len(col) > 3 else ""})
    wb.close()

    # 专名词(认识清单)：kind=proper 的词形 + 频次
    proper = {}
    for t in toks:
        if t.get("kind") == "proper" and t.get("form"):
            proper[t["form"]] = proper.get(t["form"], 0) + 1
    return words, meta, proper

# ---------- 3.5 词性锚点：轻量POS标注(原句→单一词性)，不可用则回退词表 pos ----------
_PTB2BASE = {
    "NN": "n", "NNS": "n", "NNP": "n", "NNPS": "n",
    "VB": "v", "VBD": "v", "VBG": "v", "VBN": "v", "VBP": "v", "VBZ": "v",
    "JJ": "adj", "JJR": "adj", "JJS": "adj",
    "RB": "adv", "RBR": "adv", "RBS": "adv", "RP": "adv",
    "IN": "prep", "PRP": "pron", "PRP$": "pron", "DT": "det",
    "MD": "modal", "CC": "conj", "CD": "num", "EX": "det", "UH": "exclam",
}
_SFX = [("ly", "adv"), ("ous", "adj"), ("ive", "adj"), ("ful", "adj"), ("al", "adj"),
        ("est", "adj"), ("tion", "n"), ("ment", "n"), ("ness", "n"), ("ity", "n"),
        ("ing", "v"), ("ed", "v"), ("er", "n"), ("s", "n")]

def _base(p):
    """折合到一个基础词性缩写(词表 pos / 有道 trs pos / 剑桥 pos 头三者通用)。"""
    p = re.sub(r"[^a-z]", "", p.lower())
    if p in ("vt", "vi", "vti", "intransitive", "transitive", "verb"):
        return "v"
    if p.startswith("adj") or p in ("p", "modify"):
        return "adj"
    if p.startswith("adv"):
        return "adv"
    if p.startswith("n"):
        return "n"
    if p.startswith("prep"):
        return "prep"
    if p.startswith("art") or p.startswith("det"):
        return "det"
    if p.startswith("pron"):
        return "pron"
    if p.startswith("conj"):
        return "conj"
    if p.startswith("num"):
        return "num"
    if p.startswith("exclam") or p.startswith("excl") or p.startswith("interj"):
        return "exclam"
    if p.startswith("modal") or p.startswith("aux"):
        return "modal"
    return p

_POSOK = {"n", "v", "adj", "adv", "prep", "pron", "det", "conj", "num", "exclam", "modal"}
def _wordlist_posset(pos):
    """词表 pos 字符串(n / adj & adv / N/A) → 基础词性命中集合(仅留合法词性)。"""
    if not pos or pos.strip().upper() in ("N/A", "NA", "-"):
        return set()
    s = pos.replace("&", " ").replace("/", " ").replace(",", " ")
    return {b for b in (_base(x) for x in re.split(r"\s+", s)) if b in _POSOK}

_pos_cache = {}
def _sentence_pos(word, example, forms):
    """对原句做轻量POS标注，返回目标词的基础词性(如 'adj')；失败返回 ''，由调用方回退词表 pos。"""
    try:
        import nltk
        if example not in _pos_cache:
            try:
                nltk.data.find("taggers/averaged_perceptron_tagger_eng")
            except LookupError:
                nltk.download("averaged_perceptron_tagger_eng", quiet=True)
            _pos_cache[example] = nltk.pos_tag(nltk.word_tokenize(example))
        cand = {word.lower()} | {f.lower() for f in (forms or [])}
        for w, t in _pos_cache[example]:
            if w.lower() in cand:
                b = _PTB2BASE.get(t)
                if b:
                    return b
    except Exception:
        pass
    # 启发式兜底(无标注可用时仍尽量取单一词性)
    wl = word.lower()
    for suf, b in _SFX:
        if wl.endswith(suf) and len(wl) > len(suf) + 2:
            return b
    return ""

def _example_form(lemma, forms, example):
    """从原句判定该 lemma 在该句中的具体词形(单形)。
    仅在例句中命中某 form 才返回它，否则回退 lemma 本身(原句不可用/未命中)。"""
    if example:
        for f in [lemma] + [x for x in (forms or []) if x != lemma]:
            if re.search(r"(?<![A-Za-z])" + re.escape(f) + r"(?![A-Za-z])", example, re.I):
                return f
    return lemma

# ---------- 3.5 剑桥英英简义 + 词典CEFR徽标 + 音标兜底 ----------
CAM_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36",
          "Accept-Language": "en-GB,en;q=0.9"}
_IGN = {"add to word list"}
import re as _re

_STOP = frozenset("""a an the and or but if because so then while as for of in on at to from
with without by about against between into through during before after above below
up down out off over under again further once here there all any both each few more
most other some such no nor not only own same than too very s t can will just don
should now is are was were be been being am do does did have has had having
i you he she it we they me him her us them my your our their its this that these
those what which who whom whose when where why how""".split())
def _ctx_words(sentence, excl=frozenset()):
    """从原句抽取实义搭配词：小写、纯字母、长度>=3、去停用词、去排除词(self)。"""
    out = set()
    for w in _re.findall(r"[A-Za-z]+", sentence):
        w = w.lower()
        if len(w) < 3 or w in _STOP or w in excl:
            continue
        out.add(w)
    return out

def cambridge_fetch(word, acc=frozenset(), context="", excl=frozenset()):
    """抓剑桥英英释义。acc=允许词性; context=原句(用于同词性内按搭配词选最贴近义项);
    excl=需从搭配词中剔除的词(通常是词本身)。"""
    req = urllib.request.Request(
        "https://dictionary.cambridge.org/dictionary/english/" + urllib.parse.quote(word),
        headers=CAM_UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        h = r.read().decode("utf-8", "ignore")
    def _clean(x):
        return html.unescape(_re.sub(r"<[^>]+>", "", x)).strip()
    def _def_text(c):
        """从一个 def-block 片段精确截取定义正文。定义条常含跨引(如 to (cause to) compete in
        a race:)，故以 def-div 的收尾 </div> 为结束界，再剥标签(保留 cross-ref 词)并去尾冒号。"""
        m = _re.search(r'class="def ddef_d[^"]*"[^>]*>(.*?)</div>', c, _re.S)
        if not m:
            return ""
        d = _clean(m.group(1)).strip()
        while d.endswith(":") or d.endswith(" -"):
            d = d[:-1].strip()
        return d
    # 按 pos-body 分组 → ((base_pos, [(def, [examps])]))
    groups = []
    for b in _re.split(r'class="pos-body', h)[1:]:
        pm = _re.search(r'class="pos[^"]*"[^>]*>\s*([a-z]+)\s*<', b)
        pabbr = _base(pm.group(1)) if pm else ""
        chunks = _re.split(r'class="def-block', b)[1:]
        if not chunks:
            chunks = [b]
        senses = []
        for c in chunks:
            d = _def_text(c)
            if len(d) < 8 or d.lower() in _IGN or _re.fullmatch(r'[AB][12]', d):
                continue
            exs = [_clean(x) for x in _re.findall(r'class="(?:eg|examp)[^"]*"[^>]*>(.*?)</', c, _re.S)]
            exs = [x for x in exs if x]
            senses.append((d, exs))
        if senses or pabbr:
            groups.append((pabbr, senses))
    if not groups:  # 无 pos-body 容器 → 整个页面当一块，词性留空
        senses = []
        for c in (_re.split(r'class="def-block', h)[1:] or [h]):
            d = _def_text(c)
            if len(d) < 8 or d.lower() in _IGN or _re.fullmatch(r'[AB][12]', d):
                continue
            exs = [_clean(x) for x in _re.findall(r'class="(?:eg|examp)[^"]*"[^>]*>(.*?)</', c, _re.S)]
            senses.append((d, [x for x in exs if x]))
        groups = [("", senses)]
    # CEFR 徽标：优先 ddef_h 内单字母等级，其次扫描定义里的 A2/B1 徽标
    def _badges(seg):
        z = [html.unescape(_re.sub(r'<[^>]+>', '', x)).strip()
             for x in _re.findall(r'class="ddef_h[^"]*"[^>]*>(.*?)</', seg, _re.S)]
        z += [html.unescape(_re.sub(r'<[^>]+>', '', x)).strip()
              for x in _re.findall(r'class="ddef_d[^"]*"[^>]*>(.*?)</', seg, _re.S)]
        return [x for x in z if _re.fullmatch(r'[AB][12]', x)]
    cefr = _badges(h)
    # ① 按词性过滤候选义项
    cand = [s for pabbr, ss in groups if (not acc) or pabbr in acc for s in ss]
    if not cand:  # 结构解析未命中/无匹配词性 → 全量回退，仍参与搭配选义
        cand = [s for _, ss in groups for s in ss] or [s for s in [(_def_text(h), [])] if s[0]]
    if not cand:
        cand = [s for s in [(_def_text(h), [])] if s[0]]
    # ② 同词性内按原句搭配词选最贴近义项
    sel_idx, locked = 0, False
    if context and cand:
        ctx = _ctx_words(context, excl)
        best, best_sc, best_i = None, 0, 0
        for i, s in enumerate(cand):
            sc = max(len(set(_ctx_words(ex, excl)) & ctx) for ex in (s[1] or [""]))
            if sc > best_sc:
                best, best_sc, best_i = s, sc, i
        if best is not None and best_sc > 0:
            cand = [best]; sel_idx, locked = best_i, True
    pick = [s[0] for s in cand[:3]]
    ipa = ""
    for m in _re.findall(r'class="ipa dipa[^"]*"[^>]*>(.*?)</', h):
        ipa = _clean(m)
        if ipa:
            break
    return {"e2e": "；".join(pick),
            "e2e_list": list(pick),
            "camb_cefr": (cefr[0] if cefr else ""),
            "ipa": ipa,
            "idx": sel_idx, "locked": locked}

# ---------- 3. 有道词典补全 ----------
def fetch(word, acc=frozenset(), context="", excl=frozenset()):
    """acc: 允许的基础词性命中集合(空=不过滤，取全部义项);
    context: 原句(传给剑桥做同词性内搭配选义); excl: 需剔出的搭配词(词本身)。"""
    req = urllib.request.Request(
        "https://dict.youdao.com/jsonapi?q=" + urllib.parse.quote(word), headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read().decode("utf-8", "ignore"))
    out = {"phonetic": "", "szh": "", "e2e": "", "e2e_list": [], "zh_items": [], "derived": "", "speech": "", "camb_cefr": "", "examples": []}
    # 音标 + 真实发音音频(simple.word[0] 的 ukphone/uk/usspeech)
    sim = d.get("simple") or {}
    sw = {}
    if isinstance(sim, dict) and isinstance(sim.get("word"), list) and sim.get("word"):
        sw = sim["word"][0]
    out["phonetic"] = sw.get("ukphone") or sw.get("usphone") or ""
    if not out["phonetic"]:
        out["phonetic"] = (d.get("ec", {}).get("word") or [{}])[0].get("phonetic") or ""
    _sp = sw.get("ukspeech") or sw.get("usspeech")
    if _sp:
        _au = _sp.split("&type=")[0]
        _ty = "1" if "ukspeech" in sw and sw.get("ukspeech") == _sp else ("2" if sw.get("usspeech") == _sp else "1")
        out["speech"] = "https://dict.youdao.com/dictvoice?audio=%s&type=%s" % (_au, _ty)
    ec = d.get("ec", {})
    wl = ec.get("word", [{}])[0] if isinstance(ec.get("word"), list) and ec.get("word") else {}
    if not out["phonetic"]:
        out["phonetic"] = wl.get("phonetic") or ""
    # 中文本义(按义项, 带词性缩写)；有词性锚点时只保留匹配词性的义项
    trs = wl.get("trs", [])
    # 有道 trs 无独立 pos 字段，词性缩写内嵌在释义文本开头(如 "n. ..." / "v. ..." / "【名】")
    _POSPREF = ["n.", "v.", "adj.", "adv.", "prep.", "pron.", "det.", "art.", "conj.", "num.",
                "exclam.", "int.", "interj.", "abbr.", "modal.", "aux.", "phr."]
    _CNPOS = {"名": "n", "动": "v", "形容词": "adj", "副词": "adv", "介词": "prep",
              "代词": "pron", "数词": "num", "连词": "conj", "叹词": "exclam", "冠词": "det"}
    def _tr_pos(t):
        if not t.get("tr") or not t["tr"][0].get("l"):
            return ""
        i = t["tr"][0]["l"].get("i", "")
        if isinstance(i, list):
            i = "".join(i)
        s = i.lstrip()[:16].lower()
        for pre in _POSPREF:
            if s.startswith(pre):
                return _base(pre.rstrip("."))
        cm = _re.match(r"【([^】]{1,4})】", i.lstrip())
        if cm:
            return _CNPOS.get(cm.group(1), "")
        return ""
    sel = trs
    if acc:
        match_pos = [t for t in trs if _tr_pos(t) in acc]
        if match_pos:  # 无任何匹配才回退全量
            sel = match_pos
    def lvl(t):
        if not t.get("tr"):
            return ""
        l = (t["tr"][0].get("l") or {})
        i = l.get("i", "")
        if isinstance(i, list):
            i = "".join(i)
        return i
    zh_all = [lvl(t) for t in sel]
    def _fst(z):  # 取单个义项的首个子义(首个"；"前)；有道常把众多子义合并进一条 l.i
        if not z:
            return ""
        z0 = z.split("；")[0]
        if "（人名）" in z0 or "人名" in z0 or "地名" in z0:
            return ""  # 专名(人/地名)义项教学用处小，剔除
        return z0
    out["szh"] = "；".join([_fst(z) for z in zh_all if z])[:400]
    # 完整本义义项列表(逐条首子义, 去专名)，供卡片切"例句义/其他义项"
    out["zh_items"] = [x for x in (_fst(z) for z in zh_all) if x]
    # 英英简义(simple 里的 definition)
    sdef = sim.get("definition") if isinstance(sim, dict) else None
    if isinstance(sdef, list):
        out["e2e"] = " ".join([x.get("@value", "") for x in sdef])
    # 派生词(rel_word.rels[].rel.words[].word)
    rel = d.get("rel_word", {})
    for item in rel.get("rels", []) or []:
        g = item.get("rel") or {}
        got = []
        for x in g.get("words", []) or []:
            w = x.get("word", "")
            if isinstance(w, list):
                w = "".join(w)
            if w:
                got.append(w)
        if got:
            out["derived"] = "，".join(got[:6]); break
    # 双语例句(最多3条)
    for sp in (d.get("blng_sents_part") or {}).get("sentence-pair", []) or []:
        if len(out["examples"]) >= 3:
            break
        en = (sp.get("sentence-eng") or "").replace("<b>", "").replace("</b>", "")
        zh = sp.get("sentence-translation", "")
        if en:
            out["examples"].append((en, zh))
    # 剑桥：英英简义 + 词典CEFR徽标 + 音标兜底；并据此收敛有道本义
    try:
        cb = cambridge_fetch(word, acc, context, excl)
        if cb["e2e"]:
            out["e2e"] = cb["e2e"]
        if not out["phonetic"] and cb["ipa"]:
            out["phonetic"] = cb["ipa"]
        out["camb_cefr"] = cb["camb_cefr"]
        if sel:
            # 本义随剑桥收敛：取该词性下前2个义项的首个子义（不用跨词典 idx 回指——义序并不可靠）
            out["szh"] = "；".join([_fst(z) for z in zh_all[:2] if z])
            out["zh_items"] = [x for x in (_fst(z) for z in zh_all) if x]  # 全量义项仍保留(供例句义/扩展义切分)
    except Exception:
        pass
    return out

# ---------- 3.6 原文例句译文(在线翻译接口, MyMemory 免签) ----------
_GLOSS_CACHE = {}
def _gloss(en, offline=False):
    """原文例句 → 中文译文。忠实通顺且符合汉语句法；按整句缓存，--offline 时留空。"""
    en = (en or "").strip()
    if not en or offline:
        return ""
    if en in _GLOSS_CACHE:
        return _GLOSS_CACHE[en]
    out = ""
    try:
        url = "https://api.mymemory.translated.net/get?langpair=en|zh-CN&q=" + urllib.parse.quote(en)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        out = (d.get("responseData") or {}).get("translatedText") or ""
    except Exception:
        pass
    _GLOSS_CACHE[en] = out
    return out

# ---------- 3.7 专名中文义(有道 simple 整词义) ----------
_PROP_CN_CACHE = {}
def _proper_cn(word, offline=False):
    """专名(地名/机构/物名)的中文义/音译。取有道 simple 词条中文义；--offline 时留空。"""
    if offline or not word:
        return ""
    if word in _PROP_CN_CACHE:
        return _PROP_CN_CACHE[word]
    out = ""
    try:
        url = "https://dict.youdao.com/jsonapi?q=" + urllib.parse.quote(word)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=12) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        ec = (d.get("ec") or {}).get("word") or []
        if ec:
            for t in (ec[0].get("trs") or []):
                tr = (t.get("tr") or [{}])[0].get("l") or {}
                i = tr.get("i")
                if isinstance(i, list):
                    i = "".join(i)
                if i:
                    out = str(i).lstrip()[:60]; break
    except Exception:
        pass
    _PROP_CN_CACHE[word] = out
    return out

# ---------- 4. 组装学生记忆卡 ----------
def main():
    ap = argparse.ArgumentParser(description="学生记忆词卡(主技能结果+在线词典后处理)")
    ap.add_argument("--file", default=None)
    ap.add_argument("--text", default=None)
    ap.add_argument("--out", default="学生记忆卡")
    ap.add_argument("--limit", type=int, default=0, help="只对前N个词联网补全(0=全部)")
    ap.add_argument("--offline", action="store_true", help="不查在线词典")
    ap.add_argument("--layer-filter", default=None, help="只处理指定层，逗号分隔，如 KET,PET")
    a = ap.parse_args()
    if a.text is None and a.file is None:
        ap.error("需要 --file 或 --text")

    words, meta, proper = run_main(a.text, a.file, "__sb_" + a.out)
    import openpyxl
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "学生记忆卡"
    ws.append(["Word", "归属层", "CEFR", "原句照搬", "原句词性",
               "例句词形", "例句本义", "例句义·英英", "其他词形", "本义扩展·其他义项",
               "音标", "派生词", "双语例句", "发音音频"])
    n_net = 0
    _real, _fake = [], []
    for i, (lm, rec) in enumerate(words.items()):
        if a.layer_filter and rec["layer"] not in [x.strip() for x in a.layer_filter.split(",")]:
            continue
        m = meta.get(lm, {})
        forms = sorted(set(rec.get("forms", [])))[:8]
        # 词性锚点：原句轻量POS标注优先 → 无原句则用词表 pos 集合
        sp = ""
        acc = _wordlist_posset(m.get("pos", ""))
        if m.get("example"):
            sp = _sentence_pos(lm, m["example"], rec.get("forms", []))
            if sp:
                acc = {sp}
        din = {"phonetic": "", "szh": "", "e2e": "", "e2e_list": [], "zh_items": [], "derived": "", "speech": "", "camb_cefr": "", "examples": []}
        if not a.offline:
            if a.limit and n_net >= a.limit:
                pass  # 超出联网配额，保持空
            else:
                try:
                    din = fetch(lm, acc, m.get("example", ""), {lm}); n_net += 1
                except Exception:
                    din = {"phonetic": "", "szh": "", "e2e": "", "e2e_list": [], "zh_items": [], "derived": "", "speech": "", "camb_cefr": "", "examples": []}
        # 方案3：单形单义优先 —— 例句词形 + 例句本义(首条) 放前，其余(其他词形/其他义项)作扩展
        eform = _example_form(lm, forms, m.get("example", ""))
        other_forms = " ".join(f for f in forms if f != eform)
        zh = din.get("zh_items") or []
        zh_main = zh[0] if zh else ""          # 例句本义 = 该词性下首条义项(词典序, 最贴近核心/语境)
        zh_rest = "；".join(zh[1:])             # 其他义项
        e2e_list = din.get("e2e_list") or []
        e2e_main = e2e_list[0] if e2e_list else (din["e2e"] if din["e2e"] else "")
        e2e_rest = "；".join(e2e_list[1:])
        ex2 = " || ".join("%s / %s" % x for x in din["examples"])
        ws.append([lm, rec["layer"], rec["cefr"] or din.get("camb_cefr") or "", m.get("example", ""),
                   sp if sp else m.get("pos", ""),
                   eform, zh_main, e2e_main, other_forms, (zh_rest + e2e_rest).strip("；"),
                   din["phonetic"], din["derived"], ex2, din["speech"]])
        # 实词/虚词表：听写·默写抽查用。词性=例句判定(singular)；英文/中文=搭配选义后的中选义。
        # 超纲词常无词性锚点(sp 与词表 pos 皆空)，用有道释义开头词性缩写补全后归类。
        bpos = (sp or m.get("pos", "")).lower()
        bdisp = sp or m.get("pos", "")
        if not bpos and zh_main:
            # 从例句本义释义前缀提取词性(如 "n. 快艇" → n)；防超纲词误入虚词表
            _zhp = zh_main.lstrip()
            for _p in ("num.", "adj.", "adv.", "n.", "v."):
                if _zhp.startswith(_p):
                    bpos = _p.rstrip("."); bdisp = bpos; break
            else:
                for _k, _v in (("【名】", "n"), ("【动】", "v"), ("【形】", "adj"), ("【副】", "adv"), ("【数】", "num")):
                    if _zhp.startswith(_k):
                        bpos, bdisp = _v, _v; break
        if any(bpos.startswith(p) for p in ("n", "v", "adj", "adv", "num")):
            _real.append([lm, bdisp, e2e_main, zh_main, m.get("example", "")])
        else:
            _fake.append([lm, bdisp, e2e_main, zh_main, m.get("example", "")])
        if i % 20 == 0:
            print("  .. 处理", lm)
    # —— 新增「实词表」「虚词表」：听写·默写抽查 ——
    HDR = ["词", "例句词性", "英文含义", "中文含义", "原文例句", "译文"]
    for sheet, rows, title in (("实词表", _real, "实词(名/动/形/副/数)"), ("虚词表", _fake, "虚词(介词/代词/冠/连/情态等)")):
        sh = wb.create_sheet(sheet)
        sh.append([title, "共 %d 词" % len(rows)])
        sh.append(HDR)
        for r in rows:
            sh.append([r[0], r[1], r[2], r[3], r[4], _gloss(r[4], a.offline)])
        for c, w in enumerate((20, 14, 42, 42, 80, 62), 1):
            sh.column_dimensions[openpyxl.utils.get_column_letter(c)].width = w
    # —— 专名词表(认识清单)：地名/机构/物名等，补中文义 ——
    if proper:
        psh = wb.create_sheet("专名词")
        psh.append(["专名词表(认识清单)", "共 %d 个 · 地名/机构/物名等首字母大写词" % len(proper)])
        psh.append(["专名", "频次", "中文义"])
        for w, n in proper.items():
            psh.append([w, n, _proper_cn(w, a.offline)])
        for c, wd in enumerate((22, 8, 42), 1):
            psh.column_dimensions[openpyxl.utils.get_column_letter(c)].width = wd
    wb.save(a.out + ".xlsx")
    for ext in (".json", ".xlsx"):
        try:
            os.remove("__sb_" + a.out + ext)
        except OSError:
            pass
    print("完成: %d 词 -> %s.xlsx (联网补全 %d 词)" % (len(words), a.out, n_net))

if __name__ == "__main__":
    main()