# -*- coding: utf-8 -*-
"""课程资产 · 课程资源三件套生成器（课文侧 / 词汇侧 / 技术栈侧）。

结构：CSV 为 canonical；MD / HTML 由 CSV 渲染。
用法：python _gen_assets.py  → 课程资产/课程资源.{csv,md,html}
资产变更（课文/词汇/技术栈任一侧）后重跑本脚本即同步。
"""
import csv, io, os

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "课程资产")
CSV_PATH = os.path.join(OUT, "课程资源.csv")
MD_PATH = os.path.join(OUT, "课程资源.md")
HTML_PATH = os.path.join(OUT, "课程资源.html")

# (侧, 类别, 资产名称, 说明, 存放位置, 内容状态, GitHub)
ROWS = [
 # ---------- 课文侧 ----------
 ("课文", "清单", "正课文清单三件套", "48 正课文 + 36 非正文视频映射，课文追踪唯一来源（CSV canonical）", "reports/正课文清单.{csv,md,html}", "就绪", "❌未推送"),
 ("课文", "音频", "课文音频", "16 篇点读/跟读唯一音源", "assets/p*.mp3", "就绪", "✅已推送"),
 ("课文", "时间轴", "句级时间轴", "16 篇 / 418 句，唯一权威源（门禁盯一致性）", "assets/timeline.json", "就绪", "✅已推送"),
 ("课文", "视频", "SB 原版视频", "纪录片 12 + 语法Rap 12 + 播客 6 + 文化视频 6", "../Student's Book Video 原版/", "就绪", "❌未推送"),
 ("课文", "参考", "单元篇章清单", "12 单元篇章标题 / 页码（含 +1 偏移提示）", "单元篇章清单_unit1-12.html", "就绪", "❌未推送"),
 ("课文", "附录", "逐字稿 / 校对 / 结构化笔记", "p067 / p070 逐字稿与校对", "p067_p070_*.md", "就绪", "❌未推送"),
 ("课文", "素材源", "官方 CD 音频（198 轨）", "素材库原始音频（版权，库外）", "003 第三版课程材料/第N单元/第N单元 音频/", "就绪（库外）", "❌未推送"),
 ("课文", "素材源", "课本 / 教师用书 / 练习册 / 试卷 PDF", "词汇·语法·技能·测试卷（版权，库外）", "003 第三版课程材料/第N单元/", "就绪（库外）", "❌未推送"),
 # ---------- 词汇侧 ----------
 ("词汇", "诊断页", "主题词汇页 ×2", "theme_u7 / theme_u12：筛选→学习→测试 + 诊断报告", "词汇诊断/词汇诊断_theme_*.html", "就绪", "❌未推送"),
 ("词汇", "诊断页", "篇章词汇页 ×15", "U7×6（p66/67/69/70/72/73）+ U8×4（p075/077/078/080）+ U12×5（p110/111/113/114/117），九层 level + 不规则词形保留原形式口径", "词汇诊断/词汇诊断_u*_p*.html", "就绪", "❌未推送"),
 ("词汇", "审校", "干扰项审校工作表", "干扰项审校工作表.csv + 干扰项审校.js", "词汇诊断/干扰项审校工作表.csv", "就绪", "❌未推送"),
 ("词汇", "分析产物", "词汇分析中间产物", "vocab_analysis_u7p070_u12p111 / 篇章词汇_产出 / 篇章文本_U7_U12", "词汇诊断/", "就绪", "❌未推送"),
 ("词汇", "词表", "剑桥 Wordlist", "Think Starter Wordlist", "../Think Starter Wordlist.xlsx", "就绪", "❌未推送"),
 ("词汇", "词表", "KET / PET 词表", "KET_PET_总表 + 词表（剑桥官方词表）", "KET_PET_*.xlsx", "就绪", "❌未推送"),
 ("词汇", "词表", "九层分级词表", "少儿 Pre A1/A1/A2（剑桥少儿）+ 考点 KET/PET/FCE/CAE（A2–C1，FCE/CAE 为 CEFR-J/Octanove 替代）+ NGSL/NAWL", "skills/global/article-vocab-analyzer/wordlists/", "就绪", "❌未推送"),
 ("词汇", "分析产物", "U7 篇章词汇资产", "6 篇（p66/67/69/70/72/73）九层分析 + 词汇诊断页 + 备课本", "词汇诊断/（篇章词汇_产出 / 词汇诊断_u7_*.html）", "就绪", "❌未推送"),
 ("词汇", "分析产物", "U8 篇章词汇资产", "4 篇（p075/077/078/080）九层分析 + 词汇诊断页 + 备课本（xlsx+HTML）+ 学生卡 ×4 + 语音卡 ×4（英标 100% 覆盖 + 真人发音 mp3）", "词汇诊断/（篇章词汇_产出 / 词汇诊断_u8_*.html / 篇章文本_U8）", "就绪", "❌未推送"),
 ("词汇", "诊断页", "U8 逐句跟读听写诊断页", "p077 听力篇：逐句跟读（播放/循环/录音 A/B）+ 段落听写（4 段逐句判分）+ 诊断报告，按句 ID u8/p077/sNN 存本机", "词汇诊断/跟读听写_u8_p077_musicians.html（自包含包：词汇诊断/U8_资源包/）", "就绪", "❌未推送"),
 ("词汇", "清单", "U8 资源包", "U8 单元自包含交付包：源清单/篇章文本/九层分析/学生卡/备课本/语音卡/词汇诊断页/跟读听写 + 资源清单 md+html（44 文件）", "词汇诊断/U8_资源包/", "就绪", "❌未推送"),
 ("词汇", "分析产物", "U9 篇章词汇资产", "⚠ 缺：U9 正课文时间轴/词汇页均未做", "—", "待办", "—"),
 ("词汇", "分析产物", "U12 篇章词汇资产", "5 篇（p110/111/113/114/117）九层复跑分析 + 词汇诊断页", "词汇诊断/（篇章词汇_产出 / 词汇诊断_u12_*.html）", "就绪", "❌未推送"),
 ("词汇", "模板", "词汇诊断页模板", "反推自 u7_p67（RAW/PASSAGE/CATS 三数据块置占位）", "词汇诊断/_模板_词汇诊断页.html", "就绪", "❌未推送"),
 ("词汇", "技能", "词汇四技能", "article-vocab-analyzer / teacher-vocab-prep / student-vocab-cards / british-phonetics", "skills/", "就绪", "✅已推送"),
 ("词汇", "工具", "词表加工脚本", "_gen_review_sheet / _patch_vocab / _patch_vqdis", "根目录", "就绪", "✅已推送"),
 # ---------- 技术栈侧 ----------
 ("技术栈", "技能", "全局技能 ×9", "local-mineru / article-vocab-analyzer / cet-cn2en-scholar / british-phonetics / student-vocab-cards / exam-paper-bank / teacher-vocab-prep / sentence-alignment / chunk-splitter", "skills/global/", "就绪", "✅已推送"),
 ("技术栈", "技能", "项目技能 ×1", "sentence-alignment（项目版）", "skills/project/", "就绪", "✅已推送"),
 ("技术栈", "工作流", "句级对齐规约", "方法定案 / 正课文清单 / 坑 / 门禁（权威规约）", "_ALIGNMENT_WORKFLOW.md", "就绪", "✅已推送"),
 ("技术栈", "工作流", "对齐生产入口", "_align_unit.py --unit N（ASR→对齐→合入→同步→门禁）", "_align_unit.py", "就绪", "✅已推送"),
 ("技术栈", "工具链", "音频对齐工具链", "教师用书栏目标题 ↔ 官方 CD 198 轨对齐（产 _alignment.json + 对照表）", "tools/audio-alignment/", "就绪", "✅已推送"),
 ("技术栈", "工具", "词表导入器", "_import_yle.py（剑桥少儿三层）/ _import_fce_cae.py（CEFR-J·Octanove → FCE/CAE）", "skills/global/article-vocab-analyzer/scripts/", "就绪", "❌未推送"),
 ("技术栈", "工具", "词汇技能主脚本", "assess_vocab.py（九层分析）+ vocab_pipeline.py（学生卡/备课本/语音卡）", "skills/global/article-vocab-analyzer/scripts/", "就绪", "✅已推送"),
 ("技术栈", "质量", "回归套件", "核心门禁 7 项 + 端到端 smoke 6 项", "_regress.js / _check*.js / _smoke*", "就绪", "✅已推送"),
 ("技术栈", "应用", "学习平板应用", "server.js + index.html + 教师端 + login + store/ui", "根目录", "就绪", "✅已推送"),
 ("技术栈", "应用", "双工作台源", "资料库在线学生端/教师端页面源", "_workbench/", "就绪", "❌未推送"),
 ("技术栈", "文档", "文件清单（MANIFEST）", "核心/依赖/生产/溯源四级归档 + 弃用记录", "MANIFEST.md", "就绪", "❌未推送"),
 ("技术栈", "文档", "作业与交接指南", "README / AGENTS / HANDOFF / HANDOFF-workbuddy", "根目录", "就绪", "✅已推送"),
 ("技术栈", "参考", "溯源工具", "_source_match / _sents_v2_bounds / _bridge_* / _trace_* / _align_audio", "根目录", "就绪", "✅已推送"),
 ("技术栈", "清单", "课程资源三件套（本表）", "三侧资产可视化核对表", "课程资产/课程资源.{csv,md,html}", "就绪", "❌未推送"),
 ("技术栈", "清单", "课程资产总目录", "三侧索引 + GitHub 推送状态", "课程资产/README.md", "就绪", "❌未推送"),
]

COLS = ["侧", "类别", "资产名称", "说明", "存放位置", "内容状态", "GitHub"]
os.makedirs(OUT, exist_ok=True)

# ---- CSV ----
with io.open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f); w.writerow(COLS); w.writerows(ROWS)

# ---- 由 CSV 渲染 MD / HTML ----
with io.open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
    rdr = list(csv.reader(f))
head, data = rdr[0], rdr[1:]
def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def counts(col_idx, val):
    return sum(1 for r in data if r[col_idx] == val)

# ---- MD ----
md = ["# 课程资源清单 · TH!NK Starter", "",
      "> **三侧资产可视化核对表**（课文侧 / 词汇侧 / 技术栈侧）· CSV 为 canonical，本 MD 由 CSV 渲染。",
      f"> 更新于 2026-10-13 · 共 {len(data)} 项 · 已推送 GitHub {counts(6,'✅已推送')} · 未推送 {counts(6,'❌未推送')}", "",
      "| " + " | ".join(head) + " |", "|" + "|".join(["---"]*len(head)) + "|"]
for r in data:
    md.append("| " + " | ".join(x.replace("|", "\\|") for x in r) + " |")
md += ["", "**说明**：GitHub 推送状态基于当前 `origin/main`；未推送＝未跟踪/被 gitignore/在未推送提交中。资产变更后重跑 `_gen_assets.py` 同步。"]
io.open(MD_PATH, "w", encoding="utf-8").write("\n".join(md))

# ---- HTML ----
def cls(row): return "t-" + {"课文":"text","词汇":"vocab","技术栈":"tech"}[row[0]]
body = []
for r in data:
    tds = [f'<td class="side {cls(r)}">{esc(r[0])}</td>', f'<td>{esc(r[1])}</td>',
           f'<td class="name">{esc(r[2])}</td>', f'<td class="desc">{esc(r[3])}</td>',
           f'<td class="mono">{esc(r[4])}</td>']
    st = r[5]
    stc = "ok" if st == "就绪" else ("todo" if st == "待办" else "ext")
    tds.append(f'<td><span class="{stc}">{esc(st)}</span></td>')
    gh = r[6]
    ghc = "pushed" if gh.startswith("✅") else ("nopush" if gh.startswith("❌") else "na")
    tds.append(f'<td><span class="gh {ghc}">{esc(gh)}</span></td>')
    body.append(f'<tr class="{cls(r)}">' + "".join(tds) + "</tr>")

html = f'''<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>课程资源清单 · TH!NK Starter</title>
<style>
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;margin:0;padding:22px;line-height:1.5;}}
h1{{font-size:20px;margin:0 0 4px;}} .sub{{color:#666;font-size:13px;margin-bottom:12px;}}
.lede{{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 16px;}}
.lede span{{background:#fff;border:1px solid #e3e6ec;padding:6px 13px;border-radius:20px;font-size:12.5px;}}
.lede b{{color:#1565c0;}}
table{{border-collapse:collapse;width:100%;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);}}
td,th{{border-bottom:1px solid #eef0f4;padding:7px 10px;text-align:left;font-size:12.5px;vertical-align:top;}}
th{{background:#eef3fb;color:#1565c0;font-size:12px;white-space:nowrap;}}
tr:last-child td{{border-bottom:none;}}
.side{{font-weight:700;white-space:nowrap;}} .t-text .side,.side.t-text{{color:#1c4fb0;}}
tr.t-text{{background:#f7faff;}} tr.t-vocab{{background:#fbf9ff;}} tr.t-tech{{background:#f7fffb;}}
.name{{font-weight:600;white-space:nowrap;}} .desc{{color:#555;}} .mono{{font-family:Consolas,Menlo,monospace;font-size:11px;color:#666;word-break:break-all;}}
.ok{{color:#1b5e20;background:#e6f4ea;padding:1px 8px;border-radius:10px;font-size:11px;white-space:nowrap;}}
.todo{{color:#8a5a00;background:#fff3d6;padding:1px 8px;border-radius:10px;font-size:11px;white-space:nowrap;}}
.ext{{color:#555;background:#eef0f4;padding:1px 8px;border-radius:10px;font-size:11px;white-space:nowrap;}}
.gh{{padding:1px 8px;border-radius:10px;font-size:11px;white-space:nowrap;}}
.gh.pushed{{color:#1b5e20;background:#e6f4ea;}} .gh.nopush{{color:#8a2b00;background:#fdeee6;}} .gh.na{{color:#777;background:#eef0f4;}}
</style></head><body>
<h1>课程资源清单 · TH!NK Starter</h1>
<div class="sub">三侧资产可视化核对表 · CSV 为 canonical，本页由 CSV 渲染 · 更新于 2026-10-13</div>
<div class="lede">
  <span>共 <b>{len(data)}</b> 项</span>
  <span>课文侧 <b>{counts(0,'课文')}</b></span>
  <span>词汇侧 <b>{counts(0,'词汇')}</b></span>
  <span>技术栈侧 <b>{counts(0,'技术栈')}</b></span>
  <span>✅已推送 <b>{counts(6,'✅已推送')}</b> · ❌未推送 <b>{counts(6,'❌未推送')}</b></span>
</div>
<table>
<tr>{''.join(f'<th>{esc(c)}</th>' for c in head)}</tr>
{chr(10).join(body)}
</table>
</body></html>'''
io.open(HTML_PATH, "w", encoding="utf-8").write(html)

print("CSV :", os.path.getsize(CSV_PATH), "| MD :", os.path.getsize(MD_PATH), "| HTML:", os.path.getsize(HTML_PATH))
print(f"共 {len(data)} 项 · 课文 {counts(0,'课文')} / 词汇 {counts(0,'词汇')} / 技术栈 {counts(0,'技术栈')} · 已推送 {counts(6,'✅已推送')} / 未推送 {counts(6,'❌未推送')}")
