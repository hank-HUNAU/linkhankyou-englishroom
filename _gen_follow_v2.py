# -*- coding: utf-8 -*-
"""篇章读写单页生成器 v3：_templates_v2/读写_模板.html → 篇章页/读写_pXXX_slug.html

- 每篇产出 1 个 HTML（两流程：流程①逐句听 / 流程②逐句听写），替代 v2 三页结构
- 数据源：assets/timeline.json（篇目与句数）、_book_extra.json（U8-U11 arts）、词汇诊断 stem glob
- 回写 index.html ==FOLLOW-FILES== 块：FOLLOW_FILES[pg] = {"page": "读写_….html"}；FOLLOW_META={s,q:0,v}
- _legacy_follow_v1/ 归档保留，不再读写。
用法：python _gen_follow_v2.py
"""
import re, os, glob, json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
TPLDIR = os.path.join(ROOT, "_templates_v2")
OUT = os.path.join(ROOT, "篇章页")
IDX = os.path.join(ROOT, "index.html")
TPL = open(os.path.join(TPLDIR, "读写_模板.html"), encoding="utf-8").read()
BE = json.load(open(os.path.join(ROOT, "_book_extra.json"), encoding="utf-8"))
TL = json.load(open(os.path.join(ROOT, "assets", "timeline.json"), encoding="utf-8"))

pages = sorted(int(k[1:]) if k.startswith("p") else int(k) for k in TL.keys())

# slug 优先取词汇诊断页 stem（u7_p67 / u12_p110 两种 padding 都兼容）
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
    name = "读写_%s_%s.html" % (p3, slug)
    html = TPL
    html = html.replace("__BOOK_EXTRA__",
        "var BOOK_EXTRA=" + json.dumps(BE["book"], ensure_ascii=False)
        + ";Object.keys(BOOK_EXTRA).forEach(function(k){ BOOK[k]=BOOK_EXTRA[k]; });")
    html = html.replace("__PG__", str(pg)).replace("__TITLE__", "课文 p%03d" % pg)
    assert "__PG__" not in html and "__BOOK_EXTRA__" not in html, "占位符未替换干净: %s" % pg
    open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n").write(html)
    files[str(pg)] = {"page": name}
    print("p%s → %s" % (p3, name))

assert len(files) == 33, "篇目数应为 33，实际 %d" % len(files)

# ---- 回写 index.html ==FOLLOW-FILES== 块（读写单页 page） ----
site = open(IDX, encoding="utf-8").read()
meta = {}
for pg2 in pages:
    p3b = "%03d" % pg2
    vq = 1 if (glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%03d_*.html" % pg2))
               or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%d_*.html" % pg2))) else 0
    meta[str(pg2)] = {"s": len(TL.get("p" + p3b, [])), "q": 0, "v": vq}
# ---- FOLLOW_VOCAB：篇号 → 词汇诊断页文件名（修 U8-U11 key 与文件名不匹配 404） ----
vq_files = {}
for pg2 in pages:
    p3b = "%03d" % pg2
    g = (glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%03d_*.html" % pg2))
         or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%d_*.html" % pg2)))
    if g:
        vq_files[str(pg2)] = os.path.basename(g[0])
payload = ("window.FOLLOW_VOCAB=" + json.dumps(vq_files, ensure_ascii=False, sort_keys=True) + ";"
           + "window.FOLLOW_FILES=" + json.dumps(files, ensure_ascii=False, sort_keys=True) + ";"
           + "window.FOLLOW_META=" + json.dumps(meta, ensure_ascii=False, sort_keys=True) + ";")
m = re.search(r"<!-- ==FOLLOW-FILES==.*?</script>", site, re.S)
assert m, "index.html 未找到 ==FOLLOW-FILES== 块"
block = "<!-- ==FOLLOW-FILES== 由 _gen_follow_v2.py 维护（读写单页 page）；?pg= 深链路由用 -->\n<script>" + payload + "</script>"
site2 = site[:m.start()] + block + site[m.end():]
open(IDX, "w", encoding="utf-8", newline="\n").write(site2)
print("生成", len(files), "页 →", OUT)
print("FOLLOW_FILES/FOLLOW_META 回写完成（%d 篇）" % len(files))
