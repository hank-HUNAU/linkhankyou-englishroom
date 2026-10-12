# -*- coding: utf-8 -*-
"""生成 栏目标题↔音频对照表 HTML"""
import os, json, re
from urllib.parse import quote
from datetime import date

WORK = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(os.path.dirname(os.path.dirname(WORK)), "reports")
A = json.load(open(os.path.join(WORK, "_alignment.json"), encoding="utf-8"))

def link(p):
    return "file:///" + quote(p.replace("\\", "/"), safe="/:")

def fsize(p):
    try:
        n = os.path.getsize(p)
    except OSError:
        return "—"
    return (f"{n/1e6:.2f} MB" if n >= 1e6 else f"{n/1e3:.0f} KB")

def ulabel(u):
    return "Welcome（第0单元）" if u == "W" else "Unit " + u

def ukey(u):
    return -1 if u == "W" else int(u)

ST = {
    "exact": '<span class="ok">✅ 精确</span>',
    "asr": '<span class="as">🎙 轨内公告</span>',
    "alias": '<span class="al">🔁 改名对齐</span>',
    "inferred": '<span class="inf">🔶 按页推断</span>',
}

def sb_row(r0):
    pt = ("p%s · t%02d" % (r0["pg"], r0["tr"])) if r0["pg"] else ("t%02d（页码见文件名）" % r0["tr"])
    ex = ("ex" + str(r0["ex"])) if r0.get("ex") else ""
    sec = r0.get("sec") or "—"
    ctx = r0.get("ctx") or ""
    note = r0.get("note") or ""
    extra = ('<span class="nt">%s</span>' % note) if note else ""
    return ("<tr><td class='pt'>%s</td><td class='sec'>%s</td><td class='ex'>%s</td>"
            "<td class='ctx'>%s%s</td><td class='fn'><a href=\"%s\">%s</a><span class='m'>%s · %ss</span></td>"
            "<td class='st'>%s</td></tr>"
            % (pt, sec.title(), ex, ctx, extra, link(r0["path"]), r0["f"], fsize(r0["path"]),
               int(round(r0["dur"])) if r0.get("dur") else "?", ST[r0["st"]]))

def simple_row(cat, f, path, d, note=""):
    pass
    return ("<tr><td class='pt'>%s</td><td class='sec'>—</td><td class='ex'></td><td class='ctx'>%s</td>"
            "<td class='fn'><a href=\"%s\">%s</a><span class='m'>%s · %ss</span></td><td class='st'></td></tr>"
            % (cat, note, link(path), f, fsize(path), int(round(d)) if d else "?"))

blocks = []
tot_exact = tot_alias = tot_inf = tot_asr = 0
for u in sorted(A.keys(), key=ukey):
    d0 = A[u]
    for k in ("sb", "wb", "skill", "video", "other", "miss"):
        d0.setdefault(k, [])
    rows = []
    sb = sorted(d0["sb"], key=lambda r: (r["pg"] if r["pg"] else 9999, r["tr"]))
    for r0 in sb:
        rows.append(sb_row(r0))
        tot_exact += r0["st"] == "exact"
        tot_alias += r0["st"] == "alias"
        tot_inf += r0["st"] == "inferred"
        tot_asr += r0["st"] == "asr"
    for r0 in sorted(d0["wb"], key=lambda r: (r["pg"], r["tr"])):
        rows.append(simple_row("练习册", r0["f"], r0["path"], r0.get("dur"),
                               "WB p%s · t%02d" % (r0["pg"], r0["tr"])))
    for r0 in d0["skill"]:
        rows.append(simple_row("技能测试", r0["f"], r0["path"], r0.get("dur"), "Test Yourself / 技能测试听力"))
    for r0 in d0["video"]:
        rows.append(simple_row("视频音轨", r0["f"], r0["path"], r0.get("dur"), "官方视频（纪录片/说唱/文化）音轨"))
    for r0 in d0["other"]:
        rows.append(simple_row("其他", r0["f"], r0["path"], r0.get("dur"),
                               r0.get("note") or "自制/未归类"))
    blocks.append("<tr class='uh'><td colspan='6'>%s</td></tr>%s" % (ulabel(u), "".join(rows)))

html = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>栏目标题 ↔ 音频对照表（教师用书版）</title>
<style>
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;margin:0;padding:20px;}
h1{font-size:20px;margin:0 0 4px;} .sub{color:#666;font-size:13px;margin-bottom:12px;}
.note{padding:8px 12px;border-radius:6px;font-size:13px;margin:8px 0;line-height:1.8;background:#eef3fb;border:1px solid #cdddf0;color:#333;}
.ok{color:#1b5e20;font-weight:700;} .as{color:#0b6fa4;font-weight:700;} .al{color:#7a5b00;font-weight:700;} .inf{color:#b53f00;font-weight:700;}
table{border-collapse:collapse;width:100@PCT@;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:14px;}
td,th{border-bottom:1px solid #eee;padding:6px 10px;text-align:left;font-size:12.5px;vertical-align:top;}
th{background:#eef3fb;color:#1565c0;font-size:12px;white-space:nowrap;position:sticky;top:0;}
tr:last-child td{border-bottom:none;}
tr.uh td{background:#1565c0;color:#fff;font-weight:700;font-size:14px;padding:8px 12px;}
.pt{white-space:nowrap;color:#1565c0;font-weight:700;}
.sec{white-space:nowrap;font-weight:600;color:#37474f;}
.ex{color:#888;white-space:nowrap;}
.ctx{color:#555;max-width:340px;}
.nt{display:block;color:#b53f00;font-size:11px;}
.fn{word-break:break-all;max-width:300px;}
.fn a{color:#1565c0;text-decoration:none;font-weight:600;}
.fn a:hover{text-decoration:underline;}
.m{display:block;color:#888;font-size:11px;}
.st{white-space:nowrap;}
.total{font-size:13px;color:#555;margin-top:6px;}
</style></head><body>
<h1>栏目标题 ↔ 音频对照表（按教师用书 · 全书 13 单元）</h1>
<div class="sub">依据：Codex 学习中心\\按单元与课次教师用书_文字层可提取（67 册 PDF 文本层）× 003 第三版课程材料 198 轨 mp3 · 生成于 @D1@</div>
<div class="note">
<b>对齐方法</b>：教师用书每课次 = 课本一个对开页，正文练习带轨号（如 <b>7.01</b>、Welcome 用 <b>W.01</b>）；
轨号 + 单元即唯一锁定一条 CD 音轨（文件名 p=页码、t=轨号）。<br>
<b>状态图例</b>：<span class="ok">✅ 精确</span>＝教师用书文本层明确写出该轨号（含栏目、练习号、指令原文）；
<span class="al">🔁 改名对齐</span>＝你改过名的文件，按文件名/页码/轨号规则对回教师用书引用；
<span class="as">🎙 轨内公告</span>＝官方 CD 每轨开头有人声公告（"Unit 7. Page 68. Pronunciation. Exercise 1."），ASR 转写后直接精确到练习号——这是最硬的证据；<span class="inf">🔶 按页推断</span>＝仅剩按页归位（页码准确，练习号不保证）。<br>
<b>合计</b>：课本轨 @N1@（✅ @N2@ · 🎙 @N5@ · 🔁 @N3@ · 🔶 @N4@）＋ 练习册 55 ＋ 技能测试 13 ＋ 视频音轨 3 ＋ 其他 3 ＝ 198 轨。
</div>
<table>
<tr><th>页·轨</th><th>栏目</th><th>练习</th><th>指令摘录 / 备注</th><th>音频文件（点开播放）</th><th>状态</th></tr>
@ROWS@
</table>
<div class="total">改名文件对齐依据：109/903/905＝单元+轨号；Unit 03-1 Reading、Unit_3_p34_t04、Unit4-pXX-*、第8/9单元“阅读1/篇章阅读”＝页码+栏目+教师用书轨号三方互证；“第N单元 技能 音频”＝各单元 Test Yourself 测试听力；纪录片/Rap/Culture＝官方视频音轨。</div>
</body></html>"""
html = html.replace("@PCT@", "%")
html = (html.replace("@D1@", date.today().isoformat())
            .replace("@N1@", str(tot_exact + tot_asr + tot_alias + tot_inf))
            .replace("@N2@", str(tot_exact))
            .replace("@N3@", str(tot_alias))
            .replace("@N4@", str(tot_inf))
            .replace("@N5@", str(tot_asr))
            .replace("@ROWS@", "".join(blocks))
            .replace("@PCT@", "%"))

out = os.path.join(REPORTS, "栏目标题与音频对照表.html")
open(out, "w", encoding="utf-8").write(html)
print("written:", out)
print("exact:", tot_exact, "alias:", tot_alias, "inferred:", tot_inf)
