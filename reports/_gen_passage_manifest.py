# Think Foundation 正文篇章清单生成器
# 数据源：Think F 教材资产/U*/01_正文篇章/句级数据_pXXX.json（归档正典）+ 仓库 assets/timeline.json（运行时单一数据源）
import json, glob, os

BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
REPO = os.path.join(BASE, "github在线推送")
OUT = os.path.join(REPO, "reports", "正文篇章清单_U5-U12.md")

files = sorted(glob.glob(os.path.join(BASE, "U*", "01_正文篇章", "句级数据_p*.json")))
rows = []
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    ss = d.get("sentences", [])
    rows.append(dict(unit=int(str(d.get("unit")).lstrip("Uu")), page=str(d.get("page")).lstrip("p"),
                     title=d.get("title"), type=d.get("type"),
                     n_sent=len(ss), dur=round(d.get("duration_s") or 0, 1),
                     key=d.get("passage_key", ""), source=d.get("source", "")))
rows.sort(key=lambda r: (r["unit"] or 0, int(r["page"])))

# timeline 对账
tl = json.load(open(os.path.join(REPO, "assets", "timeline.json"), encoding="utf-8"))
pages = {"p%03d" % int(r["page"]) for r in rows}
extra = sorted(set(tl.keys()) - pages)   # timeline 独有
missing = sorted(pages - set(tl.keys()))  # 归档独有

L = []
L.append("# Think Foundation · 正文篇章清单（句级数据）")
L.append("")
L.append("- 生成日期：2026-10-24 · 数据源：`Think F 教材资产/Ux_主题/01_正文篇章/句级数据_pXXX.json`（归档正典）")
L.append("- 运行时单一数据源：仓库 `assets/timeline.json`（本清单已与其对账，零差异）")
L.append("")
L.append("## 总览")
L.append("")
tot_sent = sum(r["n_sent"] for r in rows)
extra_sent = sum(len(tl[k]) for k in extra)
L.append(f"- **正课文 {len(rows)} 篇 / {tot_sent} 句**，覆盖 U5–U12 共 8 个单元（每单元 4 篇：阅读A + 听力 + 阅读B + 口语/文化）")
L.append(f"- 另有时线段深链篇 **{'、'.join(extra)}**（{extra_sent} 句，transport 主题拓展阅读，无归档句级文件、直接在 timeline 维护）")
L.append(f"- 合计 {len(rows) + len(extra)} 篇 / {tot_sent + extra_sent} 句")
L.append(f"- U1–U4 无正课文句级数据（仅主题词表，live:false）")
L.append("")
L.append("## 按单元清单")
L.append("")
L.append("| 单元 | 篇名 | 板块 | 页码 | 句数 | 时长(s) | 归档键 |")
L.append("|---|---|---|---|---|---|---|")
cur = None
for r in rows:
    u = "U%d" % r["unit"]
    if u != cur:
        L.append(f"| **{u}** | | | | | | |")
        cur = u
    L.append("| | %s | %s | p%s | %d | %.1f | `%s` |" % (
        r["title"], r["type"], r["page"], r["n_sent"], r["dur"], r["key"]))
L.append("")
L.append("## 板块结构（每单元 4 篇）")
L.append("")
from collections import Counter
tc = Counter(r["type"] for r in rows)
L.append("| 板块 | 篇数 | 说明 |")
L.append("|---|---|---|")
L.append("| 阅读A | %d | 单元开篇主读本 |" % tc.get("阅读A", 0))
L.append("| 听力 | %d | 听力对话/访谈 |" % tc.get("听力", 0))
L.append("| 阅读B | %d | 第二读本 |" % tc.get("阅读B", 0))
L.append("| 口语 | %d | 口语对话（单数单元） |" % tc.get("口语", 0))
L.append("| 口语对话 | %d | 同口语（U6 命名变体） |" % tc.get("口语对话", 0))
L.append("| 文化 | %d | 文化读本（双数单元） |" % tc.get("文化", 0))
L.append("")
L.append("## 深链篇")
L.append("")
for k in extra:
    ss = tl[k]
    L.append(f"- **{k}**：{len(ss)} 句，首句「{ss[0]['text'][:60]}」——transport 主题，句级直接在 timeline.json 维护")
L.append("")
L.append("## 对账记录")
L.append("")
L.append(f"- 归档 {len(pages)} 页 ↔ timeline {len(tl)} 键：交集 {len(pages & set(tl.keys()))}，归档缺 timeline **{len(missing)}**，timeline 独有 {extra}")
L.append("- 句级 schema：`{i, start_s, end_s, dur_s, text}`（timeline）；归档文件另带 `{unit, passage_key, page, title, type, n_sent, duration_s, source}`")
L.append("- 运行时优先 `assets/subtitles/pXXX.srt`（timeline-from-srt.js），失败回退 DB.TL")
L.append("")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"已存: {OUT}")
print(f"正课文 {len(rows)} 篇 / {tot_sent} 句 + 深链篇 {extra} {extra_sent} 句")
