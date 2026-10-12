# -*- coding: utf-8 -*-
"""生成《GitHub 仓库文件清单 × 已完成功能清单》HTML"""
import subprocess, os, re
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def git(*args):
    return subprocess.run(["git", "-C", REPO] + list(args), capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout

files = sorted(git("ls-files").splitlines())
last_commit_for = {}
for line in git("ls-files", "-format=%H%x09%p").splitlines():
    if "\t" in line:
        h, p = line.split("\t", 1)
        last_commit_for[p] = h[:7]
log = git("log", "--oneline", "-n", "20").splitlines()
status = git("status", "-sb").splitlines()

CATS = [
    ("前端页面与交互", lambda p: p.endswith((".html", ".js", ".css")) and "/" not in p and p != "server.js" and not p.startswith("_")),
    ("后端与部署", lambda p: p in ("server.js", "package.json", "LICENSE", ".gitignore")),
    ("数据资产", lambda p: p.startswith("assets/")),
    ("音频对齐工具链", lambda p: p.startswith(("_align", "_bridge", "_match", "_pilot", "_ab_", "split_audio", "scan_")) or p in ("_bridge_bounds.json", "_source_match.json")),
    ("门禁 · 回归 · 冒烟", lambda p: p.startswith(("_timeline_check", "_sync_timeline", "_regress", "_smoke", "_check", "_gen_review", "_inject", "_patch", "shot_", "gen-cert")) or p.endswith("_report.md")),
    ("文档", lambda p: p in ("README.md", "AGENTS.md", "HANDOFF.md", "HANDOFF-workbuddy.md")),
    ("配套技能包 skills/", lambda p: p.startswith("skills/")),
]

FEATURES = [
    ("平板原型 · 首发", "72f8195", ["学生端 / 教师端 / 点读页三端页面", "零依赖后端（内建 http + node:sqlite，无 npm 依赖）"]),
    ("学生端", "4f37aa7", ["免登录（匿名拉任务）", "首页整合 + 主题词汇跳转", "跟读两步制（跟句→影子），意群 CHUNKS 已下线"]),
    ("实时同步", "4f37aa7", ["SSE 双向：教师发任务 event:assignment 秒级下发", "学生学情 event:progress 回传（3s 限流）"]),
    ("API 面", "72f8195", ["login/register/me/logout · kv · assignments · reports · bank · classes · events"]),
    ("时间轴单一数据源", "28afc6f", ["assets/timeline.json 权威（12 篇/312 句）→ _sync_timeline.js 投影 index.html", "_timeline_check.js 门禁：当前「12 篇 / 312 句一致」全绿"]),
    ("课文音频入库", "28afc6f", ["12 篇 pNNN.mp3 与官方 CD 源 MD5 逐字节一致（换源无意义已定案）"]),
    ("句边界人工定案", "e9faca8", ["p067 #2/#3（28afc6f）", "p069/p072 共 7 处（cb32ba4）", "p069 #5 回退至耳定 26.70 + #4 回退原值（e9faca8）", "p072 噪声定案「用原版不降噪」（8f9ebd7，§2.7.1）"]),
    ("音频对齐工具链", "28afc6f", ["_bridge_aligner.py：faster-whisper 词级时间戳 + 序列匹配 → 句边界候选", "_ab_candidates.py：多候选起点试听页（应对 Whisper 词起点失准）", "_match_source.py：时长指纹反查官方源轨 + MD5 验证"]),
    ("质量门禁", "72f8195", ["test:core 7/7 · npm test 11/11", "7 个冒烟脚本（bridge/follow_stage/immerse/multi/bank_ui/roster/主流程）"]),
    ("纯静态版部署", "4f37aa7", ["U7+U12 先行上线验证（免后端形态）"]),
    ("配套技能包", "39edd4f", ["9 个技能入库：article-vocab-analyzer / british-phonetics / cet-cn2en-scholar / chunk-splitter / exam-paper-bank / local-mineru / sentence-alignment×2 / student-vocab-cards / teacher-vocab-prep"]),
]

rows_by_cat = {}
assigned = set()
for cname, pred in CATS:
    rows = []
    for p in files:
        if p in assigned:
            continue
        if pred(p):
            rows.append((p, last_commit_for.get(p, "")))
            assigned.add(p)
    rows_by_cat[cname] = rows
leftover = [(p, last_commit_for.get(p, "")) for p in files if p not in assigned]

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")

cats_html = ""
for cname, _ in CATS:
    rows = rows_by_cat.get(cname) or []
    if not rows:
        continue
    items = "".join(
        f"<tr><td class='fp'>{esc(p)}</td><td class='cm'>{h}</td></tr>" for p, h in rows)
    cats_html += f"<tr class='uh'><td colspan='2'>{cname}（{len(rows)}）</td></tr>{items}"
if leftover:
    items = "".join(f"<tr><td class='fp'>{esc(p)}</td><td class='cm'>{h}</td></tr>" for p, h in leftover)
    cats_html += f"<tr class='uh'><td colspan='2'>其他（{len(leftover)}）</td></tr>{items}"

feat_html = ""
for name, commit, items in FEATURES:
    lis = "".join(f"<li>{i}</li>" for i in items)
    feat_html += (f"<tr><td class='fn'>{name}</td><td class='cm'>{commit}</td>"
                  f"<td><ul>{lis}</ul></td></tr>")

ahead = re.search(r"ahead (\d+)", status[0]) if status else None
ahead_n = ahead.group(1) if ahead else "0"
untracked = [l for l in status[1:] if l.strip()]

html = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GitHub 仓库文件清单 × 已完成功能</title>
<style>
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;margin:0;padding:24px;line-height:1.7;}
h1{font-size:21px;margin:0 0 4px;} .sub{color:#666;font-size:13px;margin-bottom:14px;}
.note{padding:9px 14px;border-radius:8px;font-size:13px;margin:8px 0;}
.warn{background:#fff7e0;border:1px solid #f0d488;color:#7a5b00;}
.ok{background:#e6f4ea;border:1px solid #bfe3cc;color:#1b5e20;}
h2{font-size:17px;color:#1565c0;margin:26px 0 8px;border-left:4px solid #1565c0;padding-left:10px;}
table{border-collapse:collapse;width:100@PCT@;background:#fff;font-size:12.5px;margin:8px 0;box-shadow:0 1px 3px rgba(0,0,0,.08);}
th,td{border-bottom:1px solid #eee;padding:6px 10px;text-align:left;vertical-align:top;}
th{background:#eef3fb;color:#1565c0;font-size:12px;}
tr.uh td{background:#1565c0;color:#fff;font-weight:700;font-size:13px;}
.fp{font-family:Consolas,monospace;font-size:12px;} .cm{font-family:Consolas,monospace;color:#888;white-space:nowrap;}
.fn{font-weight:700;white-space:nowrap;}
ul{margin:2px 0 2px 16px;padding:0;} li{margin:2px 0;}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0;}
.kpi div{background:#fff;border-radius:8px;padding:8px 14px;font-size:13px;box-shadow:0 1px 3px rgba(0,0,0,.08);}
.kpi b{font-size:17px;color:#1565c0;display:block;}
</style></head><body>
<h1>GitHub 仓库清单：linkhankyou-englishroom</h1>
<div class="sub">github.com/hank-HUNAU/linkhankyou-englishroom（private · main）· 本地 D:/codex交接/codex-handoff · 生成于 @D1@</div>
<div class="kpi">
<div><b>@NFILES@</b>跟踪文件</div>
<div><b>@NFEAT@</b>大类功能模块</div>
<div><b>@AHEAD@</b>提交未推送 ⚠</div>
<div><b>@NDIRTY@</b>未提交改动</div>
</div>
<div class="note warn">⚠ 本地领先 origin/main <b>@AHEAD@ 个提交</b>（音频对齐工具链 + 三批句边界定案 + p072 定案文档均在其中），建议尽快推送备份。未提交改动：@DIRTY@</div>

<h2>一、已完成功能清单（按提交足迹）</h2>
<table>
<tr><th>功能模块</th><th>落地提交</th><th>明细</th></tr>
@FEATROWS@
</table>
<div class="note ok">另：会话内新完成的「教师用书×ASR 轨内公告」全书 198 轨对齐（125/126 精确到练习号）当前在
<b>工作区 C:/Users/Thinkpad/WorkBuddy/2026-10-08-22-28-29/</b> 的 ASR/TB 对齐链与交付物已于 2026-10-12 交接入库（<code>tools/audio-alignment/</code> + <code>reports/</code>）。</div>

<h2>二、仓库文件清单（@NFILES@ 个跟踪文件，按类分组）</h2>
<table>
<tr><th>文件</th><th>最近提交</th></tr>
@FILEROWS@
</table>
</body></html>"""

html = (html.replace("@PCT@", "%")
            .replace("@D1@", date.today().isoformat())
            .replace("@NFILES@", str(len(files)))
            .replace("@NFEAT@", str(len(FEATURES)))
            .replace("@AHEAD@", ahead_n)
            .replace("@NDIRTY@", "; ".join(untracked) or "无")
            .replace("@FEATROWS@", feat_html)
            .replace("@FILEROWS@", cats_html))

out = os.path.join(REPO, "reports", "GitHub仓库清单与功能清单.html")
open(out, "w", encoding="utf-8").write(html)
print("written:", out, "| files:", len(files), "| ahead:", ahead_n, "| dirty:", len(untracked))
