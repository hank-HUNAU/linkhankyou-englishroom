# -*- coding: utf-8 -*-
"""课文部分追踪 · 唯一来源生成器。

结构：CSV 为 canonical 数据源（可直接编辑）；MD / HTML 均由 CSV 渲染。
用法：python _gen_zwk_list.py
产出：reports/正课文清单.csv / .md / .html
数据源：assets/timeline.json（句数）、_ALIGNMENT_WORKFLOW.md（映射）、
       _source_match.json（源轨/质量）、单元篇章清单_unit1-12.html（全书标题/页码）、
       Student's Book Video 原版/（纪录片 / 语法Rap / 播客 / 文化视频 的本地 mp4）。
"""
import csv, io, json, os
from urllib.parse import quote, unquote

ROOT = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(ROOT, "reports")
CSV_PATH = os.path.join(REPORTS, "正课文清单.csv")
MD_PATH = os.path.join(REPORTS, "正课文清单.md")
HTML_PATH = os.path.join(REPORTS, "正课文清单.html")

VIDEO_BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Student's Book Video 原版"

# ---------------- 句子数（已制作页） ----------------
tl = json.load(open(os.path.join(ROOT, "assets", "timeline.json"), encoding="utf-8"))
sents = {k: len(v) for k, v in tl.items()}

# ---------------- 单元元数据 ----------------
UNITS = {
 1: "All together", 2: "I'm excited", 3: "Family time", 4: "City life",
 5: "Free time", 6: "Best friends", 7: "Living for sport", 8: "Feel the rhythm",
 9: "Who's hungry?", 10: "Big successes", 11: "The animal world", 12: "Moving about",
}

# 正课文（每单元 4）：(板块, 篇名, 页码, 制作页 or None)
ZWK = {
 1:[("阅读A","All together (website)","p012","p012"), ("听力","One-Minute Challenge","p015","p015"), ("阅读B","Nice T-shirt","p016","p016"), ("口语","Where is Daniela from?","p018","p018")],
 2:[("阅读A","Text messages","p020","p020"), ("听力","Four dialogues","p023","p023"), ("阅读B","Ruby's birthday","p024","p024"), ("文化","Masks from around the world","p027","p027")],
 3:[("阅读A","Famous families","p030","p030"), ("听力","Three people talking","p033","p033"), ("阅读B","Ellie's photo","p034","p034"), ("口语","Paul and Carla","p036","p036")],
 4:[("阅读A","Great cities","p038","p038"), ("听力","Asking for directions","p041","p041"), ("阅读B","Buying in a shop","p042","p042"), ("文化","Parks around the world","p045","p045")],
 5:[("阅读A","Robotics Club is cool!","p048","p048"), ("听力","Favourite technology","p051","p051"), ("阅读B","Do you need a tech break?","p052","p052"), ("口语","The school concert","p054","p054")],
 6:[("阅读A","A real friend","p056","p056"), ("听力","A present for Annie","p059","p059"), ("口语对话","The new teacher","p060","p060"), ("文化","Welcoming people around the world","p063","p063")],
 7:[("阅读A","Sport wonders!","p067","p067"), ("听力","Making arrangements","p069","p069"), ("阅读B","An amazing last four minutes","p070","p070"), ("口语","Making suggestions","p072","p072")],
 8:[("阅读A","#Music in the forest","p075","p075"), ("听力","Musicians around the world","p077","p077"), ("阅读B","A teenage DJ","p078","p078"), ("文化","Dances around the world","p080","p080")],
 9:[("阅读A","Kitchen Kids","p085","p085"), ("听力","Cooking","p087","p087"), ("阅读B","In a restaurant","p088","p088"), ("口语","Offering and asking for help","p090","p090")],
 10:[("阅读A","She was the first woman in space","p092","p092"), ("听力","A prize-giving at school","p095","p095"), ("阅读B","Sports achievers","p096","p096"), ("文化","Statues around the world","p099","p099")],
 11:[("阅读A","Dolphins to the rescue","p102","p102"), ("听力","Josh's holiday","p105","p105"), ("阅读B","Extinct animals","p106","p106"), ("口语","Sequencing a story","p108","p108")],
 12:[("阅读A","The great race","p111","p111"), ("听力","At the train station","p113","p113"), ("阅读B","My favourite journey","p114","p114"), ("文化","Transport around the world","p117","p117")],
}

# 已制作页的源轨（素材库）+ 备注
SRC = {
 "p048":"Thk2e_BE_L0_SB_Unit_5_p54_t09","p051":"Thk2e_BE_L0_SB_Unit_5_p54_t10",
 "p052":"Thk2e_BE_L0_SB_Unit_5_p55_t11","p054":"Thk2e_BE_L0_SB_Unit_5_p56_t12",
 "p056":"Thk2e_BE_L0_SB_Unit_6_p57_t01","p059":"Thk2e_BE_L0_SB_Unit_6_p60_t02",
 "p060":"Thk2e_BE_L0_SB_Unit_6_p61_t03","p063":"Thk2e_BE_L0_SB_Unit_6_p64_t04",
 "p085":"Thk2e_BE_L0_SB_Unit_9_p84_t01","p087":"Thk2e_BE_L0_SB_Unit_9_p86_t02",
 "p088":"Thk2e_BE_L0_SB_Unit_9_p88_t03","p090":"Thk2e_BE_L0_SB_Unit_9_p90_t04",
 "p092":"Thk2e_BE_L0_SB_Unit_10_p92_t01","p095":"Thk2e_BE_L0_SB_Unit_10_p95_t02",
 "p096":"Thk2e_BE_L0_SB_Unit_10_p96_t03","p099":"Thk2e_BE_L0_SB_Unit_10_p100_t04",
 "p102":"Thk2e_BE_L0_SB_Unit_11_p102_t01","p105":"Thk2e_BE_L0_SB_Unit_11_p105_t02",
 "p106":"Thk2e_BE_L0_SB_Unit_11_p106_t03","p108":"Thk2e_BE_L0_SB_Unit_11_p108_t04",
 "p012":"Thk2e_BE_L0_SB_Unit_1_p12_t01","p015":"Thk2e_BE_L0_SB_Unit_1_p15_t05",
 "p016":"Thk2e_BE_L0_SB_Unit_1_p16_t06","p018":"109.mp3",
 "p020":"Thk2e_BE_L0_SB_Unit_2_p20_t01","p023":"Thk2e_BE_L0_SB_Unit_2_p23_t05",
 "p024":"Thk2e_BE_L0_SB_Unit_2_p24_t06","p027":"Thk2e_BE_L0_SB_Unit_2_p27_t07",
 "p030":"Unit 03-1 Reading.mp3","p033":"Thk2e_BE_L0_SB_Unit_3_p33_t03",
 "p034":"Unit_3_p34_t04[reading].mp3","p036":"Thk2e_BE_L0_SB_Unit_3_p36_t09",
 "p038":"Unit4-p38-reading.mp3","p041":"Unit4-p41-listening-ex9.ex10.mp3",
 "p042":"4-p42-reading-ex1.mp3","p045":"4-p45-culture-ex3.mp3",
 "p067":"Thk2e_BE_L0_SB_Unit_7_p66_t01","p069":"Thk2e_BE_L0_SB_Unit_7_p69_t06",
 "p070":"Thk2e_BE_L0_SB_Unit_7_p70_t07","p072":"Thk2e_BE_L0_SB_Unit_7_p72_t11",
 "p075":"第8单元 阅读1 Music in the Forest 课文音频.mp3","p077":"Thk2e_BE_L0_SB_Unit_8_p77_t02",
 "p078":"Thk2e_BE_L0_SB_Unit_8_p78_t03","p080":"Thk2e_BE_L0_SB_Unit_8_p81_t07",
 "p111":"Thk2e_BE_L0_SB_Unit_12_p110_t01","p113":"Thk2e_BE_L0_SB_Unit_12_p113_t05",
 "p114":"Thk2e_BE_L0_SB_Unit_12_p114_t06","p117":"Thk2e_BE_L0_SB_Unit_12_p117_t07",
}
NOTE = {"p075":"素材库非标准名", "p080":"页码定案 p80（清单页 p81）"}

# ---------------- 非正文：视频（纪录片 / 语法Rap / 播客 / 文化视频） ----------------
VID_APP = {("doc",7):"p066", ("vlog",7):"p073", ("doc",12):"p110", ("culture",12):"p202"}
VID_SRC_NOTE = {"p066":"无精确源（32kbps 嘈杂档）","p073":"无精确源（32kbps 嘈杂档）",
                "p110":"无精确源（64kbps；曾误配 Unit_1_p12_t01）","p202":"官方轨待核（曾误配 Grammar Rap）"}
VLOG_TITLE = {1:"Being patient",3:"Good manners",5:"Being supportive",
              7:"Being positive",9:"Thinking about other people",11:"Facing our fears"}
CULTURE_TITLE = {2:"Masks from around the world",4:"Parks around the world",
                 6:"Welcoming people around the world",8:"Dances around the world",
                 10:"Statues around the world",12:"Ways to Get Around"}

def vfile(u, slot):
    if slot == "doc":   f = f"Unit_{u:02d}.1_Documentary.mp4"
    elif slot == "rap": f = f"Unit_{u:02d}.2_Grammar_Rap.mp4"
    else:               f = (f"Unit_{u:02d}.3_vlg.mp4" if u % 2 == 1 else f"Unit_{u:02d}.3_Culture.mp4")
    if u == 1 and slot == "third": f = "Unit_01.3_video blog.mp4"   # L1 非标准名
    rel = f"L{u}_视频/{f}"
    return rel, os.path.join(VIDEO_BASE, rel)

def file_url(abs_path): return "file:///" + quote(abs_path.replace("\\", "/"), safe="/:")

video_rows, missing = [], []
for u in range(1, 13):
    kinds = [("doc","纪录片", UNITS[u], "doc"),
             ("rap","语法Rap", "Grammar Rap", "rap")]
    kinds.append(("vlog","播客", VLOG_TITLE[u], "third") if u % 2 == 1
                 else ("culture","文化视频", CULTURE_TITLE[u], "third"))
    for key, sec, title, slot in kinds:
        rel, ap = vfile(u, slot)
        if not os.path.exists(ap): missing.append(ap)
        mpg = VID_APP.get((key, u))
        if mpg:
            proj_a, proj_l, src = f"assets/{mpg}.mp3", f"index.html?pg={int(mpg[1:])}", VID_SRC_NOTE.get(mpg,"")
            n, st, pg, note = sents.get(mpg,""), "已制作", mpg, f"非正文·音频已入 App（{mpg}.mp3）"
        else:
            proj_a, proj_l, src, n, st, pg, note = "—","—","","","待制作","—","非正文·源已备，未入 App"
        video_rows.append([f"U{u}", UNITS[u], "非正文", sec, title, pg,
                           proj_a, proj_l, src, file_url(ap), n, st, note])

# ---------------- 组装全表（正课文在前，非正文在后，按单元） ----------------
COLS = ["单元","单元名","类型","板块","篇名","页码","项目音频","项目深链","源轨","本地视频","句数","状态","备注"]
rows = []
for u in range(1, 13):
    for sec, title, page, mpg in ZWK[u]:
        if mpg:
            rows.append([f"U{u}", UNITS[u], "正课文", sec, title, mpg, f"assets/{mpg}.mp3",
                f"index.html?pg={int(mpg[1:])}", SRC.get(mpg,""), "", sents.get(mpg,""), "已制作", NOTE.get(mpg,"")])
        else:
            rows.append([f"U{u}", UNITS[u], "正课文", sec, title, page, "—","—","","","","待制作","页码待教师用书核定"])
    rows += [r for r in video_rows if r[0] == f"U{u}"]

zwk_total = sum(len(ZWK[u]) for u in range(1,13))
zwk_done = sum(1 for r in rows if r[2]=="正课文" and r[11]=="已制作")
vid_total = sum(1 for r in rows if r[2]=="非正文")
vid_done  = sum(1 for r in rows if r[2]=="非正文" and r[11]=="已制作")
tot_sent = sum(sents.values())

# ---------------- 写 CSV（canonical） ----------------
os.makedirs(REPORTS, exist_ok=True)
with io.open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(COLS); w.writerows(rows)

# ---------------- 由 CSV 渲染 MD / HTML ----------------
with io.open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rdr = list(csv.reader(f))
head, data = rdr[0], rdr[1:]
def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def fname(url): return unquote(str(url).split("/")[-1])

# ---- MD ----
md = ["# 正课文清单 · TH!NK Starter 学习平板", "",
      "> **课文部分追踪唯一来源**（CSV 为 canonical 数据源，本 MD 由 CSV 渲染）。",
      f"> 更新于 2026-10-24 · 正课文 {zwk_done}/{zwk_total} 已制作 · 非正文视频 {vid_done}/{vid_total} 已入 App · 时间轴 {len(tl)} 篇 / {tot_sent} 句", "",
      "| " + " | ".join(head) + " |", "|" + "|".join(["---"]*len(head)) + "|"]
for r in data:
    cells = []
    for i, x in enumerate(r):
        if i == 9 and x.startswith("file:"):
            cells.append(f"[{fname(x)}]({x})")
        else:
            cells.append(x.replace("|", "\\|"))
    md.append("| " + " | ".join(cells) + " |")
md += ["",
  "**说明**：类型「正课文」＝单数单元 阅读A+听力+阅读B+口语 / 双数单元 阅读A+听力+阅读B+文化（每单元 4 篇）；「非正文」＝纪录片 / 语法Rap / 播客(vlog) / 文化视频，**不计入正课文**。",
  "**项目音频**＝`assets/p*.mp3`；**项目深链**＝`index.html?pg=NN`；**本地视频**＝`Student's Book Video 原版/` 原版 mp4（file:// 链接，点击播放）。未制作页页码取自《单元篇章清单》，可能需按教师用书 +1 校正。"]
io.open(MD_PATH, "w", encoding="utf-8").write("\n".join(md))

# ---- HTML ----
def cls(row): return "type-vid" if row[2]=="非正文" else ("type-done" if row[11]=="已制作" else "type-todo")
body = []
for r in data:
    tds = []
    for i, c in enumerate(r):
        if i == 0:   tds.append(f'<td class="un">{esc(c)}</td>')
        elif i == 2:
            b = "vid" if c=="非正文" else "zwk"
            tds.append(f'<td><span class="tb {b}">{esc(c)}</span></td>')
        elif i == 5: tds.append(f'<td class="pg">{esc(c)}</td>')
        elif i in (6,7,8): tds.append(f'<td class="mono small">{esc(c)}</td>')
        elif i == 9:
            if str(c).startswith("file:"):
                tds.append(f'<td class="mono small"><a href="{esc(c)}" title="{esc(c)}">{esc(fname(c))}</a></td>')
            else:
                tds.append('<td></td>')
        elif i == 10: tds.append(f'<td class="num">{esc(c)}</td>')
        elif i == 11:
            b = "ok" if c=="已制作" else "todo"
            tds.append(f'<td><span class="{b}">{esc(c)}</span></td>')
        else: tds.append(f'<td>{esc(c)}</td>')
    body.append(f'<tr class="{cls(r)}">' + "".join(tds) + "</tr>")

html = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>正课文清单 · TH!NK Starter 学习平板</title>
<style>
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;margin:0;padding:22px;line-height:1.5;}}
h1{{font-size:20px;margin:0 0 4px;}} .sub{{color:#666;font-size:13px;margin-bottom:10px;}}
.lede{{display:flex;gap:14px;flex-wrap:wrap;margin:10px 0 14px;}}
.lede span{{background:#fff;border:1px solid #e3e6ec;padding:5px 12px;border-radius:20px;font-size:12.5px;}}
.lede b{{color:#1565c0;}}
table{{border-collapse:collapse;width:100%;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);}}
td,th{{border-bottom:1px solid #eef0f4;padding:6px 9px;text-align:left;font-size:12.5px;vertical-align:top;}}
th{{background:#eef3fb;color:#1565c0;font-size:12px;white-space:nowrap;position:sticky;top:0;}}
tr:last-child td{{border-bottom:none;}}
tr.type-vid{{background:#fbf7ff;}}
.un{{font-weight:700;white-space:nowrap;color:#2a3550;}}
.pg{{font-weight:700;color:#1565c0;white-space:nowrap;}}
.mono{{font-family:Consolas,Menlo,monospace;word-break:break-all;}} .small{{font-size:11px;color:#666;}}
.num{{text-align:right;font-variant-numeric:tabular-nums;font-weight:600;}}
a{{color:#1565c0;text-decoration:none;}} a:hover{{text-decoration:underline;}}
.ok{{color:#1b5e20;background:#e6f4ea;padding:1px 8px;border-radius:10px;font-size:11px;white-space:nowrap;}}
.todo{{color:#8a5a00;background:#fff3d6;padding:1px 8px;border-radius:10px;font-size:11px;white-space:nowrap;}}
.tb{{padding:1px 7px;border-radius:10px;font-size:11px;white-space:nowrap;}}
.tb.zwk{{background:#e7eefb;color:#1c4fb0;}} .tb.vid{{background:#f0e6fb;color:#6a2fb0;}}
.note{{background:#fff8ea;border:1px solid #f0dcb6;border-radius:10px;padding:12px 16px;margin-top:16px;font-size:12.5px;line-height:1.7;}}
</style></head><body>
<h1>正课文清单 · TH!NK Starter 学习平板</h1>
<div class="sub">课文部分追踪<b>唯一来源</b> · CSV 为 canonical 数据源，本页由 CSV 渲染 · 更新于 2026-10-24</div>
<div class="lede">
  <span>正课文 <b>{zwk_done} / {zwk_total}</b> 已制作</span>
  <span>非正文视频 <b>{vid_done} / {vid_total}</b> 已入 App</span>
  <span>时间轴 <b>{len(tl)} 篇 / {tot_sent} 句</b></span>
</div>
<table>
<tr>{''.join(f'<th>{esc(c)}</th>' for c in head)}</tr>
{chr(10).join(body)}
</table>
<div class="note">
<b>说明：</b>类型「正课文」＝单数单元 阅读A+听力+阅读B+口语 / 双数单元 阅读A+听力+阅读B+文化（每单元 4 篇）；「非正文」＝纪录片 / 语法Rap / 播客(vlog) / 文化视频，<b>不计入正课文</b>。<br>
<b>项目音频</b>＝<span class="mono">assets/p*.mp3</span>；<b>项目深链</b>＝<span class="mono">index.html?pg=NN</span>；<b>本地视频</b>＝<span class="mono">Student's Book Video 原版/</span> 原版 mp4（点击播放，file:// 需本机可访问该盘）。<br>
未制作页<b>页码</b>取自《单元篇章清单》，可能需按教师用书 +1 校正。<b>维护</b>：改 <span class="mono">正课文清单.csv</span> 后重跑 <span class="mono">_gen_zwk_list.py</span>。
</div>
</body></html>'''
io.open(HTML_PATH, "w", encoding="utf-8").write(html)

print("CSV :", os.path.getsize(CSV_PATH), "| MD :", os.path.getsize(MD_PATH), "| HTML:", os.path.getsize(HTML_PATH))
print(f"rows={len(data)}  正课文 {zwk_done}/{zwk_total}  非正文视频 {vid_done}/{vid_total}  时间轴 {len(tl)}篇/{tot_sent}句")
print(("!! 缺失视频 %d 个:" % len(missing)) if missing else "✔ 所有 36 个本地视频文件均已核实存在")
for m in missing: print("   ", m)
