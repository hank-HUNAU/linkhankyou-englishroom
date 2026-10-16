# -*- coding: utf-8 -*-
"""跟读听写单文件生成器：_模板_跟读页.html → 跟读听写/跟读听写_pXXX_slug.html
   页码清单 = BOOK/UNIT_GROUPS 覆盖的篇目（模板内含全量数据，仅需注入启动页码/标题）。
   同时回写 index.html 的 ==FOLLOW-FILES== 块（主站 ?pg= 深链路由 + followLive 用）。
   用法：python _gen_follow.py"""
import re, os, glob, json

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, "_模板_跟读页.html")
OUT = os.path.join(ROOT, "跟读听写")
IDX = os.path.join(ROOT, "index.html")

tpl = open(TPL, encoding="utf-8").read()
try:
    QBANK = json.load(open(os.path.join(ROOT, "_quiz_bank.json"), encoding="utf-8"))
except FileNotFoundError:
    QBANK = {}
BE = json.load(open(os.path.join(ROOT, "_book_extra.json"), encoding="utf-8"))
# 页码清单：模板 UNIT_GROUPS 条目 [66,"dv",...]
pages = sorted({int(m) for m in re.findall(r"\[(\d+),\"(?:rt|ls|sp|cu|dv|pd)\"", tpl)} | {int(k) for k in BE["book"]})
# slug 优先取词汇诊断页 stem；无诊断页的篇目用 timeline.json 标题 slug
slug_map = {}
for f in glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p*.html")):
    m = re.search(r"_u\d+_(p\d+)_(.+)\.html$", os.path.basename(f))
    if m: slug_map[m.group(1)] = m.group(2)
tj = json.load(open(os.path.join(ROOT, "assets", "timeline.json"), encoding="utf-8"))
def title_slug(page):
    # timeline.json 无标题；从正课文清单.csv 取
    return None
files = {}
os.makedirs(OUT, exist_ok=True)
for pg in pages:
    p3 = "%03d" % pg
    slug = slug_map.get("p"+p3) or slug_map.get("p"+str(pg)) or ("p%03d" % pg)
    fn = "跟读听写_%s_%s.html" % (p3, slug)
    qz = (QBANK.get(p3) or QBANK.get("p%03d" % pg) or {}).get("quiz", [])
    vqkey = ""
    g = (glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_" + p3 + "_*.html"))
         or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%d_*.html" % pg))
         or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%03d_*.html" % pg)))
    if g:
        vqkey = re.search(r"词汇诊断_(u\d+_p\d+_.+)\.html$", os.path.basename(g[0])).group(1)
    html = tpl.replace("__VQKEY__", vqkey)
    html = html.replace("__QDATA__", json.dumps(qz, ensure_ascii=False))
    html = html.replace("__BOOK_EXTRA__", "var BOOK_EXTRA=" + json.dumps(BE["book"], ensure_ascii=False) + ";Object.keys(BOOK_EXTRA).forEach(function(k){ BOOK[k]=BOOK_EXTRA[k]; });")
    html = html.replace("__UG_EXTRA__", "Object.assign(UNIT_GROUPS, " + json.dumps(BE["ug"], ensure_ascii=False) + ");")
    html = html.replace("__PG__", str(pg)).replace("__TITLE__", "课文 p%03d" % pg)
    open(os.path.join(OUT, fn), "w", encoding="utf-8").write(html)
    files[str(pg)] = fn
# 回写主站 FOLLOW_FILES 块
site = open(IDX, encoding="utf-8").read()
payload = "window.FOLLOW_FILES=" + json.dumps(files, ensure_ascii=False, sort_keys=True) + ";"
meta = {}
for pg2 in pages:
    p3b = "%03d" % pg2
    qzn = len((QBANK.get(p3b) or QBANK.get("p%03d" % pg2) or {}).get("quiz", []))
    vq = 1 if glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%03d_*.html" % pg2)) or glob.glob(os.path.join(ROOT, "词汇诊断", "词汇诊断_u*_p%d_*.html" % pg2)) else 0
    meta[str(pg2)] = {"s": len(tj.get("p" + p3b, tj.get("p%03d" % pg2, []))), "q": qzn, "v": vq}
payload += "window.FOLLOW_META=" + json.dumps(meta, ensure_ascii=False, sort_keys=True) + ";"
site = re.sub(r"window\.FOLLOW_META=\{[^}]*\};", "window.FOLLOW_META={};" , site) if "window.FOLLOW_META" in site else site
site2 = re.sub(r"window\.FOLLOW_FILES=\{[^}]*\};", payload, site, count=1)
assert site2 != site or payload in site, "FOLLOW_FILES 块未找到"
open(IDX, "w", encoding="utf-8").write(site2)
print("生成", len(files), "页 →", OUT)
print("FOLLOW_FILES 回写完成")
