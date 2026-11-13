# 句级音频对齐 · 工作流与规格

> 本文是 TH!NK 课程「正课文」句级时间轴产出的**唯一权威规约**。跑新单元前先读本文。
> 配套：可执行脚本 `_align_unit.py --unit N`、源文本模板 `_unit_N_source.json`、
> 技能 `think-course-audio-alignment`（`~/.workbuddy/skills/`）。

## 1. 方法定案（2026-10-13，用户拍板）

**全自动，无人耳 A/B 终审。** 两类情况：

| 情况 | 适用篇章 | 做法 |
|---|---|---|
| **情况2（有源文本）** | 阅读A、阅读B、口语、文化 | faster-whisper 词级时间戳 × **源文本自动校准**，静音吸附微调起止 |
| **情况1（无源文本）** | 听力（学生课本不印原文） | ASR 转写即为源文本，同样走词级时间戳 + 静音吸附 |

> 历史：早期 `_bridge_aligner.py` + `_ab_candidates.py` 的「人耳 A/B 终审」已**废止**，
> 不再作为流程一环。`_bridge_aligner.py` 保留作实现层交叉验证，非生产必需。

## 2. 正课文清单（每单元 4 篇）

- **单数单元**（1/3/5/7/9/11）：阅读A + 听力 + 阅读B + **口语**。
- **双数单元**（2/4/6/8/10/12）：阅读A + 听力 + 阅读B + **文化**。
- 纪录片（`.1 Documentary`）、播客/文化视频（`.3`）**不算正课文**。

## 3. 已确认映射（U7 / U8 / U12）

### Unit 7（单数 · p66）

| page | 板块 | 篇名 | 音频源（第7单元 音频） | 句数 |
|---|---|---|---|---|
| p067 | 阅读A | Sport wonders! | `Thk2e_BE_L0_SB_Unit_7_p66_t01[公众号happyshare2023].mp3` | 19 |
| p069 | 听力 | Making arrangements | `Thk2e_BE_L0_SB_Unit_7_p69_t06[公众号happyshare2023].mp3` | 21 |
| p070 | 阅读B | An amazing last four minutes | `Thk2e_BE_L0_SB_Unit_7_p70_t07[公众号happyshare2023].mp3` | 23 |
| p072 | 口语 | Making suggestions | `Thk2e_BE_L0_SB_Unit_7_p72_t11[公众号happyshare2023].mp3` | 15 |

### Unit 8（双数 · p74）

| page | 板块 | 篇名 | 音频源（第8单元 音频） | 句数 |
|---|---|---|---|---|
| p075 | 阅读A | #Music in the forest | `第8单元 阅读1 Music in the Forest 课文音频.mp3`（非标准名） | 32 |
| p077 | 听力 | Musicians around the world | `Thk2e_BE_L0_SB_Unit_8_p77_t02[公众号happyshare2023].mp3` | 27 |
| p078 | 阅读B | A teenage DJ | `Thk2e_BE_L0_SB_Unit_8_p78_t03[公众号happyshare2023].mp3` | 25 |
| p080 | 文化 | Dances around the world | `Thk2e_BE_L0_SB_Unit_8_p81_t07[公众号happyshare2023].mp3` | 22 |

> 页码定案：阅读B 在 **p78**、文化在 **p80**（`单元篇章清单_unit1-12.html` 整体 +1 偏移，
> 已用教师用书页脚 + 轨号 8.03=访谈 / 8.07=Dances 交叉纠正）。

### Unit 12（双数 · p110）

| page | 板块 | 篇名 | 音频源（第12单元 音频） | 句数 |
|---|---|---|---|---|
| p111 | 阅读A | The great race | `Thk2e_BE_L0_SB_Unit_12_p110_t01[公众号happyshare2023].mp3` | 24 |
| p113 | 听力 | At the train station | `Thk2e_BE_L0_SB_Unit_12_p113_t05[公众号happyshare2023].mp3` | 42 |
| p114 | 阅读B | My favourite journey | `Thk2e_BE_L0_SB_Unit_12_p114_t06[公众号happyshare2023].mp3` | 33 |
| p117 | 文化 | Transport around the world | `Thk2e_BE_L0_SB_Unit_12_p117_t07[公众号happyshare2023].mp3` | 30 |

> 轨号规律（U7/U12 印证）：阅读A = `t01`，文件名用**单元首页页码**（`p66_t01` / `p110_t01`），
> 不是课文页页码。U8 阅读A 例外（素材库单独命名）。**新单元务必显式核对文件名，不臆断。**

## 4. 分阶段 SOP

### 阶段 0 —— 定清单（半自动，每单元一次）
1. 从 `单元篇章清单_unit1-12.html` 读该单元正课文（4 篇）。
2. 用教师用书页脚（`tools/audio-alignment/_tb_cache/*.txt`）+ 音频轨号交叉定案**真实页码**（清单可能偏移）。
3. 到素材库 `第N单元/第N单元 音频/` 找对应 mp3，**逐条确认文件名**（含 `[公众号happyshare2023]` 后缀、非标准名）。

### 阶段 1 —— 源文本（半自动，每单元一次）
- 情况2：从教师用书文本层抄出课文正文，**按句拆行**（脚本按换行切句），去掉习题号/答案/Unicode 残迹（`/uni00A0`→空格）。
- 情况1（听力）：跑 ASR 后用转写作源文本，去报幕、按语义断句。
- **以音频为准**校准课本差异（见 §5 坑 4/5）。

### 阶段 2 —— 一键产出（全自动）
```bash
.venv-align/Scripts/python.exe _align_unit.py --unit 8              # 完整跑
.venv-align/Scripts/python.exe _align_unit.py --unit 8 --skip-asr   # 复用词级时间戳
.venv-align/Scripts/python.exe _align_unit.py --unit 8 --no-merge   # 只产出，不合入
```
脚本自动完成：复制音频（MD5 去重）→ ASR 词级时间戳 → 源文本校准 + 静音吸附 →
合入 `assets/timeline.json`（先备份）→ `node _sync_timeline.js` → `node _timeline_check.js`。

### 阶段 3 —— 验收（**必跑回溯验证**）

```bash
npm run test:core          # 门禁（含时间轴单一数据源）
python _verify_alignment_u14.py            # 回溯验证：全篇
python _verify_alignment_u14.py u1_p12_website   # 单篇
```

**回溯验证三判据**（`_verify_alignment_u14.py`，对 ASR 专名误识免疫）：
1. **词数配比**——每句窗内 ASR 词数 vs 该句词数；< 50% 疑似错位，> 2.5 倍且差 >8 疑似抢邻句；
2. **覆盖率**——落在句窗内的 ASR 词 / 全轨词数，正常 ≥ 85%（其余应为报幕/栏目标题）；
3. **间隙漏词**——>2s 的间隙里若还有 ≥3 个词 → **只是线索，不是结论**（见下方强制前置）。

### 判据 3 的强制前置：三方对账（2026-11-14 定，必做）

间隙里出现词，**不等于漏句**。下结论前必须逐项核验：

1. **行数对账**：归档句数 == 课本源文本行数（情况2 查 `_unit_N_source.json` / `_u14_source.json` 的 `lines`；情况1 查 ASR segments 断句数）。行数一致 → 归档未漏抄，间隙词在正典之外。
2. **间隙词归类**：把间隙内 ASR 词逐条归入 ①报幕/栏目名 ②署名/时间戳/小节题注（`A. Villa Borghese…`、`1. The Tango`） ③城市／人名名头 ④**音频独有台词**（音频念了、课本未印）。四类都属规约允许剥离或课本正典之外，**不补进句级归档**。
3. **交叉印证**：ASR segments 原文 × 课本源文本双向核对，确认该词确实不在源文本里，而不是被错位挤进邻句。

- 三项都过 → 判「**非缺陷**」，不改 timeline / 归档 / SRT / 音频（守 `_RELEASE_WORKFLOW.md` 三条硬规约），只在诊断报告留痕。
- 任一不过（行数不符，或实词在源文本内却落入间隙）→ 才是真错位，按坑 #4 重排文本块序后重对齐。
- **历史教训**：2026-11-12 把 U1–U4 情况1 的**尾部空隙**（实为片尾静音、内含 0 词）误判为漏检；2026-11-14 把情况2 三篇**中段有词间隙**误判为漏句。根因相同：把回放验证的间隙直接当成漏句，未与课本源文本对账。详见 `reports/对齐准确度核查_U1-U4_vs_U5-U12_2026-11-12.md` §7、`reports/情况2三篇间隙诊断_2026-11-14.md`。

> **2026-10-26 实战**：p012（U1 All together）回溯验证抓到 **33.5s 内容整段落进间隙 + 7 句被压成 0.1s 微窗**。
> 根因是 TB 版面顺序（Flavia 起头）≠ 音频顺序（Cenc→Jess→Flavia→Li Jun），违反下面坑 #4。
> 修正后：词数异常 0，覆盖率 96%（剩余 4% = 片头报幕）。**结论：情况2 也必须先按音频顺序核一遍文本块序，不能默认时书版面序就是音频序。**

## 5. 坑清单（跨单元通用，务必记住）

1. **faster-whisper 词文本前导空格**：`" I'm"` 不 `.strip()` 则归一化 `" im"`≠`"im"`，全词失配触发 identity 兜底 → 首句起点错到 0.000s。
2. **aligner CUDA 探测**：`_detect_device()` 探到 GPU 用 float16，缺 `cublas64_12.dll` 崩溃。**必须复用词级时间戳走 `align_with_word_alignments()`**，不重新加载模型。
3. **报幕/标题/时间戳吸收**：每轨开头「Unit N, Page X…」报幕、微blog时间戳（17.34 等）、小节标题（"1. The Tango"）被朗读但**排除在句外**（落进句间间隙），首句从内容词锚定。
4. **音频/课本顺序差异**：p080 音频按「Tango→Whirling→Irish」朗读，课本排「Whirling→Irish→Tango」——源文本按**音频顺序**排。
   **同型重犯（2026-10-26）**：p012 四段采访（Cenc 土耳其 / Jess 英国 / Flavia 巴西 / Li Jun 印尼）音频序与 TB 版面序不同，按版面序对齐直接把整段压进间隙。**多块同构篇章（采访/短信/多对话）必须逐块核音频序。**
5. **填空式对话的空号（2026-10-27 新增，最隐蔽）**：Think Starter 的「完成对话」练习在 TB 正文里**用数字化替答案词**
   （`Hello. 1` / `I'll 3` / `bye – have 5`），抽取时数字被剥离 → 原文留下空洞（`Hello. is a ticket?`），
   而 ASR 侧听到的是完整句。表现为「句数对、时间轴对、内容缺词」，**任何结构性校验都发现不了**。
   - 检测：逐句比对「源文本词集」vs「该句窗内 ASR 词集」，源缺而 ASR 多出的实词 → 疑似空号（归一化必须先统一 `’`→`'`，否则全是假阳性）。
   - 回填：`_extract_u14_text.py` 的 `BLANKS` 表（键=篇章+空号，答案以**音频 ASR 逐条核对**）；**裸数字行（题号）不参与回填**，否则会把答案词塞到下一句（p042 首版即踩此坑，出现 `pay. take`）。
   - 已知受影响的篇：`u3_p34_photo`（空号 3=There）、`u4_p42_shop`（1=How much / 3=take / 4=Can I / 5=a nice day）。
6. **报幕变体**：`Developing Speaking` 一类「栏目名+动名词」不在原过滤式内（原式只认 `Speaking`/`Listening`/`Reading` 单词形式）→ p036 首句残留。已补 `Developing\s+(Listening|Reading|Speaking|Writing)`。**新单元开工时先跑一次「首句是不是栏目名」检查。**
5. **音频省略课本词**：p078 访谈音频不念课本的 "When I'm DJing"——源文本删掉音频没有的词，否则该句起点前移。
6. **页码 +1 偏移**：`单元篇章清单` 的页码可能与教师用书页脚差 1（U8 阅读B/文化即如此），务必教师用书定案。
7. **音频名不统一**：有的带 `[公众号happyshare2023]`，有的单独命名（U8 阅读A），不能纯靠规律拼路径。

## 6. 单一数据源（不可违反）

- 唯一权威：`assets/timeline.json`。`index.html` 里 `==TL-DATA-START/END==` 的 `DB.TL` 是投影。
- 改 timeline 后必须 `node _sync_timeline.js` + `node _timeline_check.js`，`_timeline_check.js` 已进核心门禁。
- **不要手改 index.html 里的时间轴。**

## 7. 当前状态（2026-11-14 更新）

- `assets/timeline.json`：**49 篇 / 1141 句**（48 篇 1118 + p202 23；2026-11-14 实测订正，旧值 1153 为报幕清理前历史快照）；译文 49 篇 / 1141 句，两者句数一致。
- **两套生产工具**（同一方法论，输入排版不同）：
  - **U5–U12**：`_align_unit.py --unit N`（读 `_unit_N_source.json`，从整册教师用书抄文本）；
  - **U1–U4**：`_extract_u14_text.py`（从**按课次**教师用书 `Think F 教材资产/00 按单元与课次教师用书_文字层可提取/` 提取+拼行+说话轮次+填空回填）→ `_align_u14.py`（同一 ASR/校准管线）→ `_merge_u14.py`（校验+音频入库+timeline 合入）。
- 情况分布：U1–U4 为 10 篇情况2（TB 官方文本）+ 6 篇情况1（ASR）；U5–U12 以情况2 为主。
- U1–U4 站点已激活（2026-10-25，UNITS `live:true` + 16 篇章页）。全量回归 `npm run test:core` 11/11 绿（2026-11-12 快照）。
- **2026-11-12 拉齐**：6 篇情况1（p015/p018/p023/p033/p036/p041，136 句）按主线口径重跑，`_align_u14_rerun.py` → `_apply_u14_rerun.py` 双写；文本逐字守恒、音频 md5 全一致。逐句置信度清单 `reports/句级对齐置信度_U1-U4_情况1.{csv,json,html}`（A136/B0/C0）。**`confidence` 是 LCS 词映射率，情况1 同源恒 1.000，无鉴别力**；可判别指标须另取词边界残差／词数配比。
- **2026-11-14 诊断**：情况2 三篇（p020/p024/p045）中段有词间隙经三方对账判「非缺陷」，不改任何数据；规程已固化到 §4。
- 下一步：补 U7/U8/U12 共 12 篇词级缓存，使全站 48/48 具备可机检对齐证据（当前主线 20/32 有缓存）。
