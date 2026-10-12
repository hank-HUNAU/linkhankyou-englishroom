# -*- coding: utf-8 -*-
"""逐课《标题-音频对应表》：按教师用书课次组织，含栏目、内容简述、音频映射"""
import os, re, json, glob
from urllib.parse import quote
from datetime import date

WORK = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(os.path.dirname(os.path.dirname(WORK)), "reports")
A = json.load(open(os.path.join(WORK, "_alignment.json"), encoding="utf-8"))

SECS = ["READING", "LISTENING", "SPEAKING", "VOCABULARY", "GRAMMAR", "CULTURE",
        "WRITING", "PRONUNCIATION", "FUNCTIONS", "REVIEW", "DEVELOPING SPEAKING"]

def link(p):
    return "file:///" + quote(p.replace("\\", "/"), safe="/:")

def secs_of(text):
    out = []
    for s in SECS:
        if re.search(r"\b" + s.replace(" ", r"\s+") + r"\b", text):
            out.append(s)
    return out

def objectives(text):
    """从 SB 面板提 FUNCTIONS/GRAMMAR/VOCABULARY"""
    o = {}
    i = text.find("FUNCTIONS:")
    if i < 0:
        return o
    j = text.find("GRAMMAR:", i)
    k = text.find("VOCABULARY:", i)
    if j > i:
        o["功能"] = re.sub(r"\s+", " ", text[i + 10:j]).strip()[:110]
    if k > j:
        o["语法"] = re.sub(r"\s+", " ", text[j + 8:k]).strip()[:90]
        o["词汇"] = re.split(r"\s(?=[A-Z]{4,})", re.sub(r"\s+", " ", text[k + 11:k + 240]).strip())[0][:110]
    return o

def topic(text, fallback):
    m = re.search(r"([A-Z][A-Za-z'’\- ]{3,42}?)\s*\|\s*Unit\s+\d+", text)
    if m:
        return m.group(1).strip()
    m = re.search(r"Unit\s+\d+\s*\|\s*([A-Z][A-Za-z'’\- ]{3,42}?)\s*T\d", text)
    if m:
        return m.group(1).strip()
    return fallback

# ---- 重建 refmap（与 _build_alignment 同逻辑：轨号自带单元前缀）----
refmap = {}
for f in sorted(glob.glob(os.path.join(WORK, "_tb_cache", "*.txt"))):
    name = os.path.basename(f)[:-4]
    nm = re.match(r"Unit (\d+)(&(\d+))?", name)
    if "Welcome" in name:
        cands = {"W"}
    elif nm:
        cands = {nm.group(1)}
        if nm.group(3):
            cands.add(nm.group(3))
    else:
        continue
    t = open(f, encoding="utf-8").read()
    for m in re.finditer(r"(?:^|\s|\()(\d{1,2}|W)\.(\d{2})\b\s*(.{0,80})", t):
        pu, tr = m.group(1), int(m.group(2))
        if pu in cands and 1 <= tr <= 20:
            refmap.setdefault((pu, tr), dict(lesson=name, sec="", ex="", ctx=""))
            r0 = refmap[(pu, tr)]
            if not r0["sec"]:
                mm = re.search(r"\b" + ("W" if pu == "W" else pu) + r"\." + str(tr).zfill(2) + r"\b", t)
                pos = mm.start() if mm else 0
                best = ""
                for line in t.split("\n"):
                    ls = line.strip()
                    if 2 < len(ls) < 40 and ls.upper() == ls and re.search(r"[A-Z]{4,}", ls):
                        for s in SECS:
                            if ls.startswith(s) and t.find(line) < pos:
                                best = s
                r0["sec"] = best

def lesson_key(name):
    m = re.search(r"第(\d+)次课", name)
    if m:
        return int(m.group(1))
    if "Test Yourself" in name:
        return 90
    if "Towards" in name:
        return 91
    return 0

def lesson_pages(name):
    t = open(os.path.join(WORK, "_tb_cache", name + ".txt"), encoding="utf-8").read()
    pgs = sorted(set(int(x) for x in re.findall(r"T(\d{2,3})\b", t)))
    return pgs, t

# ---- 组装单元 → 课次列表 ----
def ulabel(u):
    return "Welcome（第0单元）" if u == "W" else "Unit " + u

def ukey(u):
    return -1 if u == "W" else int(u)

units_out = []
for u in sorted(A.keys(), key=ukey):
    d0 = A[u]
    lessons = {}
    if u == "W":
        lessons = {"Unit 0_Welcome_教师用书": dict(pages=[], forced=True)}
    else:
        for f in glob.glob(os.path.join(WORK, "_tb_cache", "*.txt")):
            nm = os.path.basename(f)[:-4]
            nm2 = re.match(r"Unit (\d+)(&(\d+))? ", nm + " ")
            if not nm2:
                continue
            us = {nm2.group(1)}
            if nm2.group(3):
                us.add(nm2.group(3))
            if u in us:
                lessons[nm] = dict(pages=lesson_pages(nm)[0], forced=False)
    # 音频分配到课次
    rows = sorted(d0.get("sb", []), key=lambda r: (r["pg"] if r["pg"] else 9999, r["tr"]))
    per = {k: [] for k in lessons}
    unassigned = []
    for r0 in rows:
        tgt = None
        ref = refmap.get((u, r0["tr"]))
        if ref and ref["lesson"] in lessons:
            tgt = ref["lesson"]
        elif r0["pg"]:
            for k, v in lessons.items():
                pgs = v["pages"]
                if pgs and min(pgs) <= r0["pg"] <= max(pgs):
                    tgt = k
                    break
        if tgt is None and "Unit 0_Welcome_教师用书" in lessons and u == "W":
            tgt = "Unit 0_Welcome_教师用书"
        if tgt:
            per[tgt].append(r0)
        else:
            unassigned.append(r0)
    # 课次卡片
    cards = []
    for nm in sorted(lessons, key=lesson_key):
        pgs, t = lesson_pages(nm)
        o = objectives(t)
        secs = secs_of(t)
        tp = topic(t, ulabel(u))
        desc = " · ".join(f"{k}：{v}" for k, v in o.items()) if o else ""
        if tp and tp != ulabel(u):
            desc = ("主题：" + tp + ("　" + desc if desc else ""))
        short = nm.replace("_教师用书", "")
        label = short if u == "W" else short.replace("Unit " + u + " ", "").replace("Unit " + u, "Unit " + u)
        audio = []
        for r0 in per[nm]:
            st = {"exact": "✅", "asr": "🎙", "alias": "🔁", "inferred": "🔶"}.get(r0["st"], "")
            pt = ("p%s·t%02d" % (r0["pg"], r0["tr"])) if r0["pg"] else ("t%02d" % r0["tr"])
            ex = ("ex" + r0["ex"]) if r0.get("ex") else ""
            sec = r0.get("sec") or (refmap.get((u, r0["tr"]), {}).get("sec") or "")
            ctx = (r0.get("ctx") or refmap.get((u, r0["tr"]), {}).get("ctx") or "")[:70]
            audio.append(f'<tr><td class="pt">{st} {pt}</td><td class="sec">{sec.title() if sec else "—"}</td>'
                         f'<td class="ex">{ex}</td><td class="ctx">{ctx}</td>'
                         f'<td class="fn"><a href="{link(r0["path"])}">{r0["f"]}</a></td></tr>')
        chips = "".join(f'<span class="chip">{s.title()}</span>' for s in secs) or '<span class="chip dim">（无大栏目）</span>'
        pgstr = (f"SB p{min(pgs)}–{max(pgs)}" if pgs and max(pgs) - min(pgs) >= 1
                 else (f"SB p{pgs[0]}" if pgs else ""))
        cards.append(f'''<div class="lesson">
<div class="lh"><b>{label}</b> <span class="pg">{pgstr}</span>{chips}</div>
{f'<div class="desc">{desc}</div>' if desc else ''}
{'<table><tr><th>音频（轨）</th><th>栏目</th><th>练习</th><th>指令 / 公告摘录</th><th>文件</th></tr>' + "".join(audio) + '</table>' if audio else '<div class="noaudio">本课次无配套课本音频</div>'}
</div>''')
    appendix = []
    if d0.get("wb"):
        appendix.append(f"练习册音频 {len(d0['wb'])} 轨（WB p{min(x['pg'] for x in d0['wb'])}–{max(x['pg'] for x in d0['wb'])}）")
    if d0.get("skill"):
        appendix.append("技能/测试 " + str(len(d0["skill"])) + " 轨（Test Yourself 听力）")
    if d0.get("video"):
        appendix.append("官方视频音轨 " + str(len(d0["video"])) + " 轨")
    if d0.get("other"):
        names = "、".join(x["f"] for x in d0["other"])
        appendix.append("其他 " + str(len(d0["other"])) + " 轨：" + names[:80])
    units_out.append(f'''<tr class="uh"><td colspan="2">{ulabel(u)}</td></tr>
<tr><td colspan="2">{''.join(cards)}
{'<div class="apx">📎 ' + "｜".join(appendix) + "</div>" if appendix else ""}</td></tr>''')

html = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>教师用书逐课 标题-音频对应表</title>
<style>
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;margin:0;padding:22px;line-height:1.7;}
h1{font-size:21px;margin:0 0 4px;} .sub{color:#666;font-size:13px;margin-bottom:12px;}
table.u{border-collapse:separate;border-spacing:0 10px;width:100@PCT@;}
tr.uh td{background:#1565c0;color:#fff;font-weight:700;font-size:15px;padding:9px 14px;border-radius:8px 8px 0 0;}
td{background:#fff;padding:0;}
.lesson{background:#fff;border-radius:8px;padding:12px 16px;margin:0 0 10px;box-shadow:0 1px 3px rgba(0,0,0,.06);}
.lh{font-size:14px;margin-bottom:4px;} .pg{color:#888;font-size:12px;margin:0 8px;}
.chip{display:inline-block;font-size:11px;background:#eef3fb;color:#1565c0;border-radius:4px;padding:1px 8px;margin-left:4px;}
.chip.dim{color:#999;background:#f0f2f5;}
.desc{font-size:12.5px;color:#555;background:#f7f9fc;border-radius:6px;padding:5px 10px;margin:4px 0 6px;}
table{border-collapse:collapse;width:100@PCT@;font-size:12.5px;margin-top:4px;}
th,td{border-bottom:1px solid #eee;padding:4px 8px;text-align:left;}
th{background:#f2f6fc;color:#1565c0;font-size:11.5px;}
.pt{white-space:nowrap;font-family:Consolas,monospace;} .sec{white-space:nowrap;font-weight:600;color:#37474f;}
.ex{color:#888;white-space:nowrap;} .ctx{color:#555;}
.fn{word-break:break-all;max-width:280px;} .fn a{color:#1565c0;text-decoration:none;font-weight:600;}
.noaudio{color:#999;font-size:12px;} .apx{background:#f0f2f5;border-radius:6px;padding:6px 10px;font-size:12px;color:#555;margin-top:4px;}
</style></head><body>
<h1>教师用书逐课：标题 ↔ 音频对应表（含内容与模块类型）</h1>
<div class="sub">严格依据 E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/按单元与课次教师用书_文字层可提取（67 册）· 音频 198 轨 · 生成于 @D1@<br>
图例：✅ 教师用书文本轨号 · 🎙 CD 轨内公告（ASR）· 🔁 改名文件对齐 · 🔶 按页推断</div>
<table class="u">
@ROWS@
</table>
</body></html>"""

html = html.replace("@PCT@", "%").replace("@D1@", date.today().isoformat()).replace("@ROWS@", "\n".join(units_out))
out = os.path.join(REPORTS, "教师用书逐课标题-音频对应表.html")
open(out, "w", encoding="utf-8").write(html)
n_rows = sum(len(d0.get("sb", [])) for d0 in A.values())
print("written:", out, "| lessons:", sum(len(units_out) and 1 for _ in [0]), "| sb rows:", n_rows)
