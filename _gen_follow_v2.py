# -*- coding: utf-8 -*-
"""篇章三页生成器 v2：_templates_v2/{预习,复习,听写}_模板.html → 篇章页/{预习,复习,听写}_pXXX_slug.html

- 数据源沿用 v1：_quiz_bank.json（12 篇 47 题）、_book_extra.json、assets/timeline.json、
  词汇诊断 stem glob（VQKEY 三模式共用）。
- 每篇产出 3 页（预习=聆听+盲听答题 / 复习=逐句跟读 / 听写=抽句三方式），并注入 __SIBLINGS__ 三页互链。
- 回写 index.html 的 ==FOLLOW-FILES== 块为三页结构：
    FOLLOW_FILES[pg] = {listen:"预习_…", follow:"复习_…", dictate:"听写_…"}；FOLLOW_META 同 v1。
- _legacy_follow_v1/ 归档保留，不再读写。
用法：python _gen_follow_v2.py
"""
import re, os, glob, json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))          # codex-handoff
TPLDIR = os.path.join(ROOT, "_templates_v2")
OUT = os.path.join(ROOT, "篇章页")
IDX = os.path.join(ROOT, "index.html")
STAGES = ["listen", "follow", "dictate"]
PREFIX = {"listen": "预习", "follow": "复习", "dictate": "听写"}

TPL = {s: open(os.path.join(TPLDIR, PREFIX[s] + "_模板.html"), encoding="utf-8").read() for s in STAGES}

try:
    QBANK = json.load(open(os.path.join(ROOT, "_quiz_bank.json"), encoding="utf-8"))
except FileNotFoundError:
    QBANK = {}
BE = json.load(open(os.path.join(ROOT, "_book_extra.json"), encoding="utf-8"))

# 页码清单：模板 UNIT_GROUPS 条目 [66,"dv",...] + BOOK_EXTRA 覆盖篇目（与 v1 同口径）
pages = sorted({int(m) for m in re.findall(r'\[(\d+),"(?:rt|ls|sp|cu|dv|pd)"', TPL["listen"])} | {int(k) for k in BE["book"]})

# slug 优先取词汇诊断页 stem；无诊断页的篇目用 pXXX
slug_map = {}
for f in sorted(glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p*.html"))):
    m = re.search(r"_u\d+_(p\d+)_(.+)\.html$", os.path.basename(f))
    if m and m.group(1) not in slug_map:
        slug_map[m.group(1)] = m.group(2)

files = {}
os.makedirs(OUT, exist_ok=True)
for pg in pages:
    p3 = "%03d" % pg
    slug = slug_map.get("p" + p3) or slug_map.get("p" + str(pg)) or ("p%03d" % pg)
    qz = (QBANK.get(p3) or QBANK.get("p%03d" % pg) or {}).get("quiz", [])
    vqkey = ""
    g = (glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_" + p3 + "_*.html"))
         or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%d_*.html" % pg))
         or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%03d_*.html" % pg)))
    if g:
        vqkey = re.search(r"词汇诊断_(u\d+_p\d+_.+)\.html$", os.path.basename(g[0])).group(1)
    siblings = {s: "%s_%s_%s.html" % (PREFIX[s], p3, slug) for s in STAGES}
    names = set(siblings.values())
    for s in STAGES:
        html = TPL[s]
        html = html.replace("__SIBLINGS__", json.dumps(siblings, ensure_ascii=False))
        html = html.replace("__VQKEY__", vqkey)
        html = html.replace("__QDATA__", json.dumps(qz, ensure_ascii=False))
        html = html.replace("__BOOK_EXTRA__", "var BOOK_EXTRA=" + json.dumps(BE["book"], ensure_ascii=False) + ";Object.keys(BOOK_EXTRA).forEach(function(k){ BOOK[k]=BOOK_EXTRA[k]; });")
        html = html.replace("__UG_EXTRA__", "Object.assign(UNIT_GROUPS, " + json.dumps(BE["ug"], ensure_ascii=False) + ");")
        html = html.replace("__PG__", str(pg)).replace("__TITLE__", "课文 p%03d" % pg)
        assert "__PG__" not in html and "__SIBLINGS__" not in html and "__VQKEY__" not in html, "占位符未替换干净: %s %s" % (pg, s)
        open(os.path.join(OUT, siblings[s]), "w", encoding="utf-8", newline="\n").write(html)
    files[str(pg)] = siblings
    print("p%s → %s" % (p3, " / ".join(siblings[x] for x in STAGES)))

assert len(files) == 25, "篇目数应为 25，实际 %d" % len(files)
assert len(os.listdir(OUT)) == 75, "篇章页 应为 75 个文件，实际 %d" % len(os.listdir(OUT))

# ---- 回写主站 ==FOLLOW-FILES== 块（三页结构 + FOLLOW_META 同 v1） ----
site = open(IDX, encoding="utf-8").read()
payload = "window.FOLLOW_FILES=" + json.dumps(files, ensure_ascii=False, sort_keys=True) + ";"
meta = {}
for pg2 in pages:
    p3b = "%03d" % pg2
    qzn = len((QBANK.get(p3b) or QBANK.get("p%03d" % pg2) or {}).get("quiz", []))
    vq = 1 if glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%03d_*.html" % pg2)) or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%d_*.html" % pg2)) else 0
    meta[str(pg2)] = {"s": len(json.load(open(os.path.join(ROOT, "assets", "timeline.json"), encoding="utf-8")).get("p" + p3b, [])),
                      "q": qzn, "v": vq}
payload += "window.FOLLOW_META=" + json.dumps(meta, ensure_ascii=False, sort_keys=True) + ";"

m = re.search(r"<!-- ==FOLLOW-FILES==.*?</script>", site, re.S)
assert m, "index.html 未找到 ==FOLLOW-FILES== 块"
block = "<!-- ==FOLLOW-FILES== 由 _gen_follow_v2.py 维护（三页结构 listen/follow/dictate）；?pg= 深链路由用 -->\n<script>" + payload + "</script>"
site2 = site[:m.start()] + block + site[m.end():]
open(IDX, "w", encoding="utf-8", newline="\n").write(site2)
print("生成", len(files) * 3, "页 →", OUT)
print("FOLLOW_FILES/FOLLOW_META 回写完成（%d 篇）" % len(files))
