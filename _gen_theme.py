# -*- coding: utf-8 -*-
"""单元主题词汇生成器：Think Starter Wordlist.xlsx → 词汇诊断_theme_uN.html（U1-U6/U8-U11 共 10 页）
   + 回写主站 index.html 的 THEME/THEME_TITLE（U7/U12 保留现有手输版）。
   中文释义：_dict_cache.json 命中即用；缺失的联网查（有道）并写回缓存。
   用法：python _gen_theme.py [--offline]"""
import re, os, json, sys, time
import openpyxl, requests

ROOT = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(ROOT, "..", "Think Starter Wordlist.xlsx")
VD = os.path.join(ROOT, "词汇诊断")
CACHE = os.path.join(VD, "_dict_cache.json")
TPL = os.path.join(VD, "词汇诊断_theme_u7.html")
IDX = os.path.join(ROOT, "index.html")
OFFLINE = "--offline" in sys.argv

POS_ZH = {"noun": "名词", "verb": "动词", "adj": "形容词", "adv": "副词", "phr": "短语", "phrase": "短语",
          "preposition": "介词", "pronoun": "代词", "number": "数词", "exclamation": "感叹词", "conj": "连词"}

def load_cache():
    return json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
cache = load_cache()

def fetch_zh(word, example):
    """有道词典页抓中文释义（与 assess 管线同源缓存结构）。"""
    try:
        r = requests.get("https://dict.youdao.com/result?word=%s&lang=en" % requests.utils.quote(word), timeout=10)
        its = []
        # 简易提取：li 结构中的 "词性. 中文"
        for m in re.finditer(r'<li><p><span[^>]*>([a-z]+\.)</span><span>([^<]{1,60})</span>', r.text):
            its.append(m.group(1) + " " + m.group(2).strip())
        if not its:
            for m in re.finditer(r'<span class="trans"[^>]*>([^<]{1,60})</span>', r.text):
                its.append(m.group(1).strip())
        return its[:4]
    except Exception:
        return []

def zh_of(word):
    w = word.lower()
    if w in cache and cache[w].get("zh_items"):
        return cache[w]["zh_items"]
    if OFFLINE:
        return []
    its = fetch_zh(word, "")
    if its:
        cache[w] = {"phonetic": "", "zh_items": its}
        return its
    return []

# ── 1. 读 xlsx ──
wb = openpyxl.load_workbook(XLSX, read_only=True)
rows = list(wb["Sheet1"].iter_rows(min_row=2, values_only=True))
units = {}
for r in rows:
    if not r[0] or not r[1]:
        continue
    u = int(r[1])
    units.setdefault(u, []).append({
        "w": str(r[0]).strip(), "page": r[2], "en": (r[3] or "").strip(),
        "pos": (r[4] or "").strip(), "ex": (r[5] or "").strip(), "ipa": (r[6] or "").strip(),
    })
print("xlsx 单元:", {u: len(v) for u, v in sorted(units.items())})

# ── 2. 补 zh（联网，含缓存回写）──
need = [w["w"] for u in sorted(units) for w in units[u] if w["w"].lower() not in cache]
print("需联网补释义:", len(need), "词")
for i, w in enumerate(need):
    its = zh_of(w)
    if i % 40 == 0:
        json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)  # 周期回写
        print("  进度 %d/%d" % (i, len(need)), flush=True)
    time.sleep(0.25)
json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("释义补齐完成")

# ── 3. 生成 10 页 ──
tpl = open(TPL, encoding="utf-8").read()
gen = {}
for u in sorted(units):
    if u in (7, 12):
        continue  # 保留现有手输版
    raw = []
    for x in units[u]:
        its = zh_of(x["w"])
        zh = its[0] if its else x["en"]
        poszh = POS_ZH.get(x["pos"].lower(), x["pos"] or "—")
        raw.append([x["w"], x["ipa"], x["pos"][:4] or "—", zh, "—", poszh, x["ex"] or "—"])
    h = tpl
    h = re.sub(r"const RAW = \[[\s\S]*?\n\];", "const RAW = " + json.dumps(raw, ensure_ascii=False) + ";", h, count=1)
    h = re.sub(r"const TOTAL_COUNT = \d+;", "const TOTAL_COUNT = %d;" % len(raw), h, count=1)
    h = h.replace('key: "theme_u7",', 'key: "theme_u%d",' % u)
    h = h.replace('title: "Unit 7 · 单元主题词汇"', 'title: "Unit %d · 单元主题词汇"' % u)
    h = h.replace("<title>Unit 7 · 单元主题词汇 · 词汇诊断", "<title>Unit %d · 单元主题词汇 · 词汇诊断" % u)
    fn = os.path.join(VD, "词汇诊断_theme_u%d.html" % u)
    open(fn, "w", encoding="utf-8").write(h)
    gen[u] = raw
    print("生成 theme_u%d (%d 词)" % (u, len(raw)))

# ── 4. 主站 THEME/THEME_TITLE 扩充（U7/U12 保留）──
site = open(IDX, encoding="utf-8").read()
m = re.search(r"var THEME = \{[\s\S]*?\n\};", site)
assert m, "THEME 未定位"
add = []
for u in sorted(units):
    if u in (7, 12) or u not in gen:
        continue
    words = [{"w": x["w"], "ipa": x["ipa"], "pos": x["pos"][:4], "zh": (zh_of(x["w"])[0] if zh_of(x["w"]) else x["en"]),
              "ex": x["ex"]} for x in units[u]]
    add.append('  "%d": %s' % (u, json.dumps(words, ensure_ascii=False)))
new_theme = m.group(0)[:-2] + ",\n" + ",\n".join(add) + "\n};"
site = site.replace(m.group(0), new_theme, 1)
m2 = re.search(r"var THEME_TITLE = \{[^}]*\};", site)
assert m2
new_title = m2.group(0)[:-1] + "".join(", '%d':'单元主题词汇 · Unit %d 全书词表'" % (u, u) for u in sorted(gen)) + " };"
site = site.replace(m2.group(0), new_title, 1)
open(IDX, "w", encoding="utf-8").write(site)
print("主站 THEME/THEME_TITLE 扩充完成（+10 单元）")
