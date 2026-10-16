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

### 阶段 3 —— 验收
```bash
npm test          # 全量回归（含时间轴单一数据源门禁）
```

## 5. 坑清单（跨单元通用，务必记住）

1. **faster-whisper 词文本前导空格**：`" I'm"` 不 `.strip()` 则归一化 `" im"`≠`"im"`，全词失配触发 identity 兜底 → 首句起点错到 0.000s。
2. **aligner CUDA 探测**：`_detect_device()` 探到 GPU 用 float16，缺 `cublas64_12.dll` 崩溃。**必须复用词级时间戳走 `align_with_word_alignments()`**，不重新加载模型。
3. **报幕/标题/时间戳吸收**：每轨开头「Unit N, Page X…」报幕、微blog时间戳（17.34 等）、小节标题（"1. The Tango"）被朗读但**排除在句外**（落进句间间隙），首句从内容词锚定。
4. **音频/课本顺序差异**：p080 音频按「Tango→Whirling→Irish」朗读，课本排「Whirling→Irish→Tango」——源文本按**音频顺序**排。
5. **音频省略课本词**：p078 访谈音频不念课本的 "When I'm DJing"——源文本删掉音频没有的词，否则该句起点前移。
6. **页码 +1 偏移**：`单元篇章清单` 的页码可能与教师用书页脚差 1（U8 阅读B/文化即如此），务必教师用书定案。
7. **音频名不统一**：有的带 `[公众号happyshare2023]`，有的单独命名（U8 阅读A），不能纯靠规律拼路径。

## 6. 单一数据源（不可违反）

- 唯一权威：`assets/timeline.json`。`index.html` 里 `==TL-DATA-START/END==` 的 `DB.TL` 是投影。
- 改 timeline 后必须 `node _sync_timeline.js` + `node _timeline_check.js`，`_timeline_check.js` 已进核心门禁。
- **不要手改 index.html 里的时间轴。**

## 7. 当前状态（2026-10-13）

- `assets/timeline.json`：**16 篇 / 418 句**（12 旧篇 + U8 四篇 106 句）。
- 全量回归 `npm test` 11/11 绿。
- 下一步：生成静态 JSON 数据包 `data/u7.json / u8.json / u12.json`（三段式 ID `u8/p078/s03`）供 GitHub Pages 静态站。
