# -*- coding: utf-8 -*-
"""生成《站点与数据接入需求 × 工具链处理报告》HTML"""
import os, json
from datetime import date

WORK = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(os.path.dirname(os.path.dirname(WORK)), "reports")
A = json.load(open(os.path.join(WORK, "_alignment.json"), encoding="utf-8"))
n_sb = sum(len(d0.get("sb", [])) for d0 in A.values())
n_wb = sum(len(d0.get("wb", [])) for d0 in A.values())
n_other = sum(len(d0.get("other", [])) + len(d0.get("skill", [])) + len(d0.get("video", []))
              for d0 in A.values())

html = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>站点与数据接入需求报告 × 工具链数据处理</title>
<style>
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;margin:0;padding:24px;line-height:1.75;}
.wrap{max-width:960px;margin:0 auto;}
h1{font-size:22px;margin:0 0 4px;} h2{font-size:17px;color:#1565c0;margin:30px 0 8px;border-left:4px solid #1565c0;padding-left:10px;}
h3{font-size:14.5px;margin:16px 0 6px;color:#37474f;}
.sub{color:#666;font-size:13px;margin-bottom:16px;}
.card{background:#fff;border-radius:10px;padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,.08);margin-bottom:14px;}
table{border-collapse:collapse;width:100@PCT@;background:#fff;font-size:13px;margin:8px 0;}
th,td{border:1px solid #e5e9ef;padding:6px 10px;text-align:left;vertical-align:top;}
th{background:#eef3fb;color:#1565c0;}
code{background:#f0f2f5;border-radius:4px;padding:1px 6px;font-size:12.5px;}
.mono{font-family:Consolas,monospace;font-size:12.5px;}
.ok{color:#1b5e20;font-weight:700;} .warn{color:#b53f00;font-weight:700;} .mid{color:#7a5b00;font-weight:700;}
.flow{background:#0d1b2a;color:#dbe7f3;border-radius:10px;padding:14px 18px;font-family:Consolas,monospace;font-size:12.5px;line-height:1.9;overflow-x:auto;}
.flow b{color:#7fd1ff;} .flow i{color:#9ef0a0;font-style:normal;}
ul{margin:6px 0 6px 20px;padding:0;} li{margin:3px 0;}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0;}
.kpi div{background:#eef3fb;border-radius:8px;padding:8px 14px;font-size:13px;}
.kpi b{font-size:18px;color:#1565c0;display:block;}
</style></head><body><div class="wrap">
<h1>TH!NK 学习平板：站点与数据接入需求报告</h1>
<div class="sub">范围：站点现状 · 数据接入需求盘点 · 本次工具链如何处理现有数据 · 资产清单与路线图 · 生成于 @D1@</div>

<div class="kpi">
<div><b>12 篇 / 312 句</b>已上线（时间轴）</div>
<div><b>198 轨</b>官方音频全部对齐</div>
<div><b>125 / 126</b>课本轨精确到练习号</div>
<div><b>门禁 7/7</b> 全绿</div>
</div>

<h2>一、站点现状与数据流</h2>
<div class="card">
<p><b>架构</b>：零依赖 Node（内建 http + <code>node:sqlite</code>），单进程 <code>server.js</code>（端口 8000）。
存储三张表：<code>users / classes / kv</code>；实时通道 SSE 双向（教师发任务 <code>event:assignment</code> →
学生端秒级更新；学生写学情 <code>event:progress</code> → 教师端刷新，3s 限流）。</p>
<p><b>API 面</b>：<code>login / register / me / logout / kv(GET,POST) / events / assignments / reports / bank / classes(GET,POST)</code>。
学生端免登录（匿名拉任务），教师端 token 鉴权。</p>
<p><b>数据单一源</b>：<code>assets/timeline.json</code>（12 篇/312 句的权威时间轴）→
<code>node _sync_timeline.js</code> 投影进 <code>index.html</code> 的 <code>==TL-DATA-START/END==</code> 块 →
<code>node _timeline_check.js</code> 门禁校验（当前「12 篇 / 312 句一致」）。
课文音频 <code>assets/pNNN.mp3</code> 12 个，由前端按句边界 <code>start_s/end_s</code> 播放。</p>
</div>

<h2>二、数据接入需求盘点</h2>
<div class="card">
<h3>① 音频数据（核心缺口）</h3>
<table>
<tr><th>需求</th><th>现状</th><th>缺口 / 所需接入</th></tr>
<tr><td>课文音频源</td><td class="ok">12 篇已入库且与官方 CD 轨逐字节一致</td><td>全书 13 单元 114 条课本轨已就位（素材库），<b>需批量入库 + 命名规范化</b></td></tr>
<tr><td>句级时间轴</td><td class="mid">12 篇 312 句已人工耳校；其余 0</td><td>全书约 1000+ 句：用已验证的「词级时间戳→序列匹配→A/B 试听→人耳定案」流水线批量生产</td></tr>
<tr><td>1 句 1 音频切片</td><td class="warn">无（前端按 start/end 播放整轨）</td><td>两种路线：A. 维持整轨+时间轴（现状，零存储成本）；B. ffmpeg 预切逐句 mp3（离线批量，需按本报告管道先修边界）</td></tr>
<tr><td>轨↔课文练习映射</td><td class="ok">198 轨已全部对齐栏目标题/练习号</td><td>无缺口；新批次音频按同一管道即可自动对齐</td></tr>
</table>
<h3>② 结构化内容</h3>
<table>
<tr><th>需求</th><th>现状</th><th>缺口</th></tr>
<tr><td>课文文本</td><td>timeline.json 内嵌句文本（12 篇）</td><td>全书文本：教师用书 PDF 文本层可直接提取（已验证可提取率 100@PCT@），或从音频 ASR 反向校对</td></tr>
<tr><td>词汇/语法点</td><td>词汇学习中心独立成站</td><td>与平板站以 <code>/api/bank</code> 打通即可</td></tr>
<tr><td>教师用书元数据</td><td class="ok">67 册 PDF → 67 份文本缓存 + 轨号/栏目/练习号结构化（_tb_refs.json）</td><td>无缺口，可复用</td></tr>
</table>
<h3>③ 运行时数据（站点自身）</h3>
<table>
<tr><th>需求</th><th>现状</th><th>缺口</th></tr>
<tr><td>任务下发</td><td class="ok">/api/assignments（kv 存储 + SSE 推送）</td><td>任务需引用「单元/页/句」ID——扩展到全书后 ID 规范要先行（建议 <code>u7/p66/s03</code> 三段式）</td></tr>
<tr><td>学情回传</td><td class="ok">kv + progress 事件（教师端实时）</td><td>学情明细表（跟读评分、时长）目前走 kv 快照，量大后建议独立表</td></tr>
<tr><td>用户/班级</td><td class="ok">users/classes 表</td><td>无</td></tr>
<tr><td>部署形态</td><td class="mid">本机 node server.js</td><td>纯静态版已具备（U7+U12 先行上线过）；全静态化需把 /api 换成只读 JSON 或保留本地服务</td></tr>
</table>
</div>

<h2>三、本次创建的工具链：如何处理现有数据</h2>
<div class="card">
<div class="flow">
<b>原始素材（E: 198 轨 + 67 册教师用书 PDF）</b>
  ├─ <i>_match_source.py</i> ……时长指纹反查 → <b>_source_match.json</b>（资产↔源轨）
  ├─ <i>MD5 逐字节比对</i> …………资产↔源一致性（12 篇全验证，防"换源"误判）
  ├─ <i>_bridge_aligner.py</i> ……faster-whisper 词级时间戳 + 序列匹配 → <b>_bridge_bounds.json</b>（句边界候选）
  │    └─ <i>_ab_candidates.py / _ab_p*.html</i> → 多候选试听页 → <b>人耳定案</b> → 改 timeline.json
  ├─ <i>_build_alignment.py</i> ……教师用书文本层轨号解析 → <b>_alignment.json</b>（轨↔栏目/练习）
  ├─ <i>_asr_tracks.py / _asr_alias.py</i> → faster-whisper 转写 → <b>轨内公告解析</b>（Unit/P/Section/Exercise）
  │    └─ <i>_asr_apply.py</i> → 公告写回 _alignment.json（🛡 三重证据互锁）
  └─ <i>_make_html.py</i> …………………→ <b>栏目标题与音频对照表.html</b>（198 轨可点击清单）
</div>
<h3>每个工具的输入 → 输出 → 精度</h3>
<table>
<tr><th>工具</th><th>输入</th><th>输出</th><th>实测精度 / 用途</th></tr>
<tr><td class="mono">_bridge_aligner.py</td><td>_whisper_all_words.json + timeline.json</td><td>_bridge_bounds.json、A/B 试听页</td><td>confidence=1.0；199/312 句暴露真分歧 → 交给耳朵裁决</td></tr>
<tr><td class="mono">_ab_candidates.py</td><td>候选起点列表</td><td>多候选试听 HTML</td><td>解决 Whisper 词起点落在上一词尾音的问题（p067#3、p069#5 两例均由人耳终审）</td></tr>
<tr><td class="mono">_build_alignment.py</td><td>67 份 TB 文本 + 198 轨文件名</td><td>_alignment.json</td><td>轨号主键精确匹配 89 轨；别名规则 12 轨；页码推断 25 轨（后经 ASR 收敛）</td></tr>
<tr><td class="mono">_asr_*.py 链</td><td>27+12 轨音频</td><td>_asr_tracks/_asr_alias.json</td><td><b>轨内公告</b>「Unit 7. Page 68. Pronunciation. Exercise 1.」→ 36 轨直接精确到练习号；2m43s 跑完</td></tr>
<tr><td class="mono">_make_html.py</td><td>_alignment.json</td><td>对照表 HTML</td><td>198 轨 / 13 单元 / 0 缺失</td></tr>
</table>
<h3>三重证据质量模型（本管道的护城河）</h3>
<ul>
<li><b>证据一 · 教师用书文本层</b>：官方轨号（如 7.01）印在 PDF 里 → 主键</li>
<li><b>证据二 · 音频轨内公告</b>：CD 人声自报页码/栏目/练习号 → 独立复核，还纠正了 3 处 TB 解析偏差</li>
<li><b>证据三 · 人耳终审</b>：句边界争议一律 A/B 试听由你拍板（p067#3、p069#5、p072 全套）</li>
</ul>
</div>

<h2>四、数据资产清单</h2>
<div class="card">
<table>
<tr><th>资产</th><th>内容</th><th>可再生</th></tr>
<tr><td class="mono">assets/timeline.json</td><td>12 篇 312 句权威时间轴（git 已入库）</td><td>否（人工定案值）</td></tr>
<tr><td class="mono">assets/p*.mp3 ×12</td><td>课文音频（与官方源逐字节一致）</td><td>是（源在 E:）</td></tr>
<tr><td class="mono">_whisper_all_words.json</td><td>12 篇词级时间戳</td><td>是（重跑 ~10min）</td></tr>
<tr><td class="mono">_source_match.json</td><td>资产↔源轨映射 + MD5 验证</td><td>是</td></tr>
<tr><td class="mono">_tb_cache/ (67 txt) + _tb_refs.json</td><td>教师用书文本层 + 轨号/栏目结构化</td><td>是（~2min）</td></tr>
<tr><td class="mono">_durations.json / _alignment.json</td><td>198 轨时长 / 最终对齐模型</td><td>是</td></tr>
<tr><td class="mono">_asr_tracks.json / _asr_alias.json</td><td>39 轨转写与轨内公告</td><td>是</td></tr>
<tr><td class="mono">3 份 HTML 清单</td><td>视频 36 / 音频 198 / 对照表</td><td>是（脚本在）</td></tr>
</table>
</div>

<h2>五、风险与建议路线图</h2>
<div class="card">
<ul>
<li><span class="warn">P1 · ID 规范先行</span>：全书扩展前先定「单元/页/句」三段式 ID，任务、学情、时间轴共用，避免 12 篇时代的临时编号固化。</li>
<li><span class="warn">P1 · 时间轴批量生产</span>：用已验证管道（词级时间戳 → 候选 → 试听）处理剩余 ~100 单元页；发音/朗读类短轨公告已自带定位，成本远低于首批。</li>
<li><span class="mid">P2 · 逐句音频决策</span>：先按路线 A（整轨+时间轴）扩量；确有性能/离线需求再启用 ffmpeg 预切（切分精度依赖已修好的边界）。</li>
<li><span class="mid">P2 · 学情明细表</span>：kv 快照够用当前规模；跟读评分上线后建 <code>progress_log</code> 表。</li>
<li><span class="ok">低风险项</span>：素材库齐全（视频 36、音频 198、教师用书 67 册文本层可提取），扩展不存在素材障碍。</li>
</ul>
</div>
<div class="sub" style="margin-top:14px">报告基于 2026-10-08 ~ 10-12 会话实测数据；所有工具脚本与中间产物均在 D:/codex交接/codex-handoff 与本工作区，可随时复跑。</div>
</div></body></html>"""

html = (html.replace("@PCT@", "%").replace("@D1@", date.today().isoformat()))
out = os.path.join(REPORTS, "站点与数据接入需求报告.html")
open(out, "w", encoding="utf-8").write(html)
print("written:", out)
