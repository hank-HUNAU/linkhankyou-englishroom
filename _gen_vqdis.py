# -*- coding: utf-8 -*-
"""词汇诊断页生成器：分析 JSON + 有道词典 + 反推模板 → 单页 HTML。

用法：python _gen_vqdis.py u8_p075 u8_p077 u8_p078 u8_p080
链路：词汇诊断/篇章词汇_产出/<key>.json（assess 逐词判定）
      + 有道词典（音标/中文义项，复用 student_cards.fetch）
      + 词汇诊断/_模板_词汇诊断页.html（RAW/PASSAGE/CATS 占位）
   → 词汇诊断/词汇诊断_<key>.html
词条选取：kind==word，按显示词去重（常规屈折还原词原；不规则词形保留原形式，如
children/feet/went），剔除功能词与 <3 字母词。层级/CEFR 恒按词族原形标注。
"""
import os, sys, json, re, glob, importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))
VD = os.path.join(ROOT, "词汇诊断")
TEMPLATE = os.path.join(VD, "_模板_词汇诊断页.html")

STOP = set("""a an the and or but so if because when while of to in on at for from with by about over
under into as than that this these those it its he she they we you i his her their our your my me him
them us be is are was were am been being do does did have has had can could will would shall should
may might must not no yes there here then now very too also just only other another some any all both
each every more most much many few little own same such up down out off""".split())
CAT_CN = {"n": "名词", "v": "动词", "adj": "形容词", "adv": "副词", "prep": "介词", "pron": "代词",
          "conj": "连词", "det": "冠词", "num": "数词", "excl": "叹词", "art": "冠词"}

def sentences_of(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text)) if s.strip()]

def text_of(key):
    m = re.search(r"p\d+", key)                   # u7_p67_sportwonders -> p67
    num = m.group(0) if m else key.split("_")[-1]
    # 命名兼容：p%03d 补零（U1-U4/U7-U12）与 p 后不补零（U5/U6）两种约定都试
    digits = num.lstrip("p")
    cands = [num] if num != digits else []
    cands += ["p" + digits, "p%03d" % int(digits)] if digits.isdigit() else [digits]
    seen, ordered = set(), []
    for c in cands:
        if c not in seen:
            seen.add(c); ordered.append(c)
    for sub in ("篇章文本_U1_U4", "篇章文本_U5_U6", "篇章文本_U8", "篇章文本_U7_U12"):
        for c in ordered:
            for f in glob.glob(os.path.join(VD, sub, "*" + c + "*.txt")):
                return open(f, encoding="utf-8").read()
    return ""

def body_of(key):
    """正文（去掉首行标题），用于取例句。"""
    t = text_of(key)
    return t.split("\n", 1)[1] if "\n" in t else t

def parse_zh(items):
    if not items: return "", ""
    m = re.match(r"\s*([a-z]+)\.\s*(.+)", str(items[0]))
    return (m.group(1), m.group(2).strip()) if m else ("", str(items[0]).strip())

POS_NORM = {"vt": "v", "vi": "v"}   # 及物/不及物归并为 v，避免词性比对失配（say=vt vs said=v）

def pick_zh(items, lemma, pos_l):
    """不规则词形（显示词 ≠ 词原）的义项挑选，词性以词原为准：
    ① 含 lemma 且提及过去式/过去分词/复数的释义（如 “go 的过去式”）；
    ② 词性与词原一致的释义（said→v. 说，best→adj. 最好的）；
    ③ 退回第一义。"""
    if not items: return []
    pos_l = POS_NORM.get(pos_l, pos_l)
    for it in items:
        s = str(it)
        if lemma in s and any(k in s for k in ("过去", "复数")): return [s]
    if pos_l:
        for it in items:
            m = re.match(r"\s*([a-z]+)\.", str(it))
            if m and POS_NORM.get(m.group(1), m.group(1)) == pos_l: return [it]
    return [items[0]]

def load_fetch():
    spec = importlib.util.spec_from_file_location(
        "sc", os.path.join(ROOT, "skills", "global", "student-vocab-cards", "scripts", "student_cards.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.fetch

def load_assess():
    """复用 assess_vocab 的 base_word/stem_suffix/IRREG，保证与判定链口径一致。"""
    spec = importlib.util.spec_from_file_location(
        "av", os.path.join(ROOT, "skills", "global", "article-vocab-analyzer", "scripts", "assess_vocab.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def display_word(av, form, lemma):
    """委托 assess_vocab.display_word（单一来源，_gen_vqdis 与 teacher_prep 共用）。"""
    return av.display_word(form, lemma)

def resolve(key):
    """u8_p075 -> 实际文件名 u8_p075_musicintheforest（取分析 json，排除 .vocab.json）。"""
    p = os.path.join(VD, "篇章词汇_产出", key + ".json")
    if os.path.exists(p): return key
    for f in sorted(glob.glob(os.path.join(VD, "篇章词汇_产出", key + "*.json"))):
        b = os.path.basename(f)[:-5]
        if not b.endswith(".vocab"): return b
    raise SystemExit("找不到分析 json: " + key)

CACHE_PATH = os.path.join(VD, "_dict_cache.json")
def load_cache():
    return json.load(open(CACHE_PATH, encoding="utf-8")) if os.path.exists(CACHE_PATH) else {}

def cached_fetch(fetch, cache, w, ex):
    if w in cache: return cache[w]
    try: fd = fetch(w, context=ex)
    except Exception: fd = {}
    cache[w] = {"phonetic": fd.get("phonetic", ""), "zh_items": fd.get("zh_items") or []}
    json.dump(cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False)   # 逐词落盘
    return cache[w]

def build_rows(key, fetch, cache, av):
    toks = json.load(open(os.path.join(VD, "篇章词汇_产出", key + ".json"), encoding="utf-8"))["tokens"]
    sents = [title_of(key)] + sentences_of(body_of(key))   # 标题单列，仅供标题词取例句
    picked, seen, miss = [], set(), []
    for t in toks:
        if t.get("kind") != "word": continue
        w = display_word(av, t["form"], t["lemma"].lower())
        if len(w) < 3 or w in STOP or w in seen: continue
        seen.add(w)
        lm = t["lemma"].lower()
        ex = next((s for s in sents if re.search(r"\b" + re.escape(w) + r"\w*", s, re.I)), "")
        fd = cached_fetch(fetch, cache, w, ex)
        if not (fd.get("phonetic") or fd.get("zh_items")) and w != lm:
            fd = cached_fetch(fetch, cache, lm, ex)   # 词形查词失败 → 回落词原
        ipa = fd.get("phonetic") or ""
        items = fd.get("zh_items")
        if w != lm and items:
            pos_l = parse_zh(cached_fetch(fetch, cache, lm, ex).get("zh_items"))[0]   # 词原词性
            items = pick_zh(items, lm, pos_l)
        pos, zh = parse_zh(items)
        if not (ipa or zh): miss.append(w)
        lv = (t.get("layer") or "") + ("·" + t["cefr"] if t.get("cefr") else "")
        picked.append([w, ipa, pos, zh, lv, CAT_CN.get(pos, ""), ex])
    return picked, miss

def title_of(key):
    txt = text_of(key)
    first = txt.split("\n", 1)[0].strip() if txt else ""
    return first or key

# ── P1-2 构建期干扰项审计：镜像页面 pickDistractors 的 band/cefr 拆层逻辑 ──
_VQ_STEM_RE = re.compile(r"(ings|ing|ied|ed|ies|es|s|er|est|ly)$")

def _vq_en_stem(s):
    x = re.sub(r"[^a-z]", "", (s or "").lower())
    return _VQ_STEM_RE.sub("", x)

def _vq_en_close(a, b):
    x, y = _vq_en_stem(a), _vq_en_stem(b)
    if not x or not y: return False
    if x == y: return True
    return len(x) >= 4 and len(y) >= 4 and (x.startswith(y) or y.startswith(x))

def _vq_zh_clean(s):
    return re.sub(r"[（(].*?[)）]", "", s or "").translate({ord(c): None for c in "，,、;；。.！!？? "})

def _vq_zh_close(a, b):
    x, y = _vq_zh_clean(a), _vq_zh_clean(b)
    if not x or not y: return False
    return x == y or x in y or y in x

def audit_distractors(rows, fk):
    weak = []
    for w in rows:
        en, pos, zh, lv = w[0], w[2], w[3], w[4]
        band, _, cefr = lv.partition("·")
        zh_l = zh.strip().lower()
        def usable(x):
            return (x[3].strip().lower() != zh_l
                    and not _vq_en_close(x[0], en)
                    and not _vq_zh_close(x[3], zh))
        pool_pos = [x for x in rows if x is not w and x[2] == pos and usable(x)]
        pool_cefr = [x for x in pool_pos if cefr and x[4].endswith("·" + cefr)]
        pool_band = [x for x in pool_pos if band and x[4].partition("·")[0] == band]
        if len(pool_cefr) < 3 or len(pool_band) < 3:
            weak.append((w[0], pos, lv, len(pool_cefr), len(pool_band), len(pool_pos)))
    if weak:
        print("   干扰项审计: %d/%d 词同层池<3（运行时逐层降级至同词性/全体兜底）" % (len(weak), len(rows)))
        for t in weak[:10]:
            print("     %s（%s·%s）cefr池%d 词表池%d 同词性池%d" % t)
    else:
        print("   干扰项审计: 同层池全部 ≥3 ✓")

def main():
    keys = sys.argv[1:]
    tpl = open(TEMPLATE, encoding="utf-8").read()
    fetch = load_fetch(); av = load_assess(); cache = load_cache()
    for key in keys:
        fk = resolve(key)
        rows, miss = build_rows(fk, fetch, cache, av)
        unit = fk.split("_")[0]                   # u8 -> 8
        title = "Unit %s · %s" % (unit[1:], title_of(fk))
        html = (tpl.replace("/*__RAW__*/", json.dumps(rows, ensure_ascii=False))
                   .replace('"__KEY__"', json.dumps(fk))
                   .replace('"__TITLE__"', json.dumps(title))
                   .replace("/*__CATS__*/", json.dumps(rows_cats(rows), ensure_ascii=False))
                   .replace("__PAGETITLE__", title)
                   .replace("__UNIT_NO__", unit[1:])
                   .replace("__NWORDS__", str(len(rows))))
        # P0-1 构建期断言：占位符清零 + 单元号全页一致（防实例化张冠李戴）
        for ph in ("__PAGETITLE__", "__UNIT_NO__", "__NWORDS__", "__KEY__", "__TITLE__", "__CATS__"):
            if ph in html:
                raise SystemExit("[%s] 构建失败：占位符 %s 未被替换" % (fk, ph))
        import re as _re
        wrong_unit = sorted({m for m in _re.findall(r"Unit \d+", html) if m != "Unit " + unit[1:]})
        if wrong_unit:
            raise SystemExit("[%s] 构建失败：页面残留他单元标题 %s" % (fk, wrong_unit))
        # 词数断言：占位符必须清零、且正确词数必须在场（2026-10-24 修：旧断言查字面
        # "共 50 词"会误伤恰好 50 词的篇章——模板早先用 __NWORDS__ 占位，无硬编码可残留）
        if "__NWORDS__" in html or ("共 %d 词" % len(rows)) not in html:
            raise SystemExit("[%s] 构建失败：词数占位符异常（应有「共 %d 词」）" % (fk, len(rows)))
        out = os.path.join(VD, "词汇诊断_%s.html" % fk)
        audit_distractors(rows, fk)
        open(out, "w", encoding="utf-8").write(html)
        print("[%s] %d 词（词典缺失 %d）· %s → %s" % (fk, len(rows), len(miss), title, os.path.basename(out)))
        if miss: print("   miss:", miss[:15])

def rows_cats(rows):
    cs = ["全部"]
    for r in rows:
        if r[5] and r[5] not in cs: cs.append(r[5])
    if "专有名词" not in cs: cs.append("专有名词")
    return cs

if __name__ == "__main__":
    main()
