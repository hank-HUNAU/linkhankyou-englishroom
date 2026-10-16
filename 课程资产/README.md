# 课程资产 · 总目录（TH!NK Starter 学习平板）

> 课程资产的**唯一入口**。三侧资产（课文侧 / 词汇侧 / 技术栈侧）的核查表见 [`课程资源.csv`](课程资源.csv) · [`课程资源.md`](课程资源.md) · [`课程资源.html`](课程资源.html)。
> 生成器：`../_gen_assets.py`（**任一侧资产变更后重跑即同步三件套**）。更新于 2026-10-13。

---

## 📁 本目录

| 文件 | 作用 |
|---|---|
| `README.md` | 本总目录（三侧索引 + 推送状态 + 未纳入清单） |
| `课程资源.csv` | **canonical 数据源**（30 项三侧资产） |
| `课程资源.md` | 可视化核对表（Markdown） |
| `课程资源.html` | 可视化核对表（网页，按侧配色 + 状态徽标） |

---

## ① 课文侧

| 资产 | 位置 | GitHub |
|---|---|---|
| **正课文清单三件套**（48 正课文 + 36 非正文视频） | [`../reports/正课文清单.csv`](../reports/正课文清单.csv) · [`.md`](../reports/正课文清单.md) · [`.html`](../reports/正课文清单.html) | ❌未推送 |
| 句级时间轴（16 篇 / 418 句，唯一权威） | [`../assets/timeline.json`](../assets/timeline.json) | ✅已推送 |
| 课文音频（16 篇 p*.mp3） | [`../assets/`](../assets/) | ✅已推送 |
| SB 原版视频（纪录片/语法Rap/播客/文化视频，36 mp4） | `../../Student's Book Video 原版/`（库外） | ❌未推送 |
| 单元篇章清单（12 单元标题/页码） | [`../单元篇章清单_unit1-12.html`](../单元篇章清单_unit1-12.html) | ❌未推送 |
| 逐字稿 / 校对 / 结构化笔记 | [`../p067_p070_逐字稿与校对.md`](../p067_p070_逐字稿与校对.md) 等 | ❌未推送 |
| 素材源（198 轨音频·课本/教师用书/练习册/试卷） | `003 第三版课程材料/第N单元/`（库外） | ❌未推送 |

## ② 词汇侧

| 资产 | 位置 | GitHub |
|---|---|---|
| 主题词汇页 ×2（theme_u7 / theme_u12） | [`../词汇诊断/`](../词汇诊断/) | ❌未推送 |
| 篇章词汇页 ×11（U7×6 + U12×5） | [`../词汇诊断/`](../词汇诊断/) | ❌未推送 |
| 干扰项审校工作表（+ 审校 js） | [`../词汇诊断/干扰项审校工作表.csv`](../词汇诊断/干扰项审校工作表.csv) | ❌未推送 |
| 词汇分析中间产物 | [`../词汇诊断/`](../词汇诊断/)（vocab_analysis / 篇章词汇_产出） | ❌未推送 |
| **U8 篇章词汇分析**（4 篇覆盖率/分层/超纲 + 逐词判定） | [`../词汇诊断/篇章词汇_产出/`](../词汇诊断/篇章词汇_产出/)（`u8_p*`） | ❌未推送 |
| **九层分级词表**（少儿 Pre A1–A2 + 考点 KET/PET/FCE/CAE + NGSL/NAWL） | [`../skills/global/article-vocab-analyzer/wordlists/`](../skills/global/article-vocab-analyzer/wordlists/) | ❌未推送 |
| 剑桥 Wordlist | `../../Think Starter Wordlist.xlsx`（库外） | ❌未推送 |
| KET / PET 词表 | [`../KET_PET_总表.xlsx`](../KET_PET_总表.xlsx) · `词表.xlsx` | ❌未推送 |
| 词汇四技能 | [`../skills/global/`](../skills/global/)（article-vocab-analyzer / teacher-vocab-prep / student-vocab-cards / british-phonetics） | ✅已推送 |
| 词表加工脚本 | `../_gen_review_sheet.js` · `_patch_vocab.js` · `_patch_vqdis.js` | ✅已推送 |

## ③ 技术栈侧

| 资产 | 位置 | GitHub |
|---|---|---|
| 句级对齐规约（权威） | [`../_ALIGNMENT_WORKFLOW.md`](../_ALIGNMENT_WORKFLOW.md) | ✅已推送 |
| 对齐生产入口 `_align_unit.py --unit N` | [`../_align_unit.py`](../_align_unit.py) | ✅已推送 |
| 音频对齐工具链（198 轨 ↔ 教师用书栏目） | [`../tools/audio-alignment/`](../tools/audio-alignment/) | ✅已推送 |
| **词表导入器**（`_import_yle.py` / `_import_fce_cae.py`）· **九层词汇库** | [`../skills/global/article-vocab-analyzer/`](../skills/global/article-vocab-analyzer/) | ❌未推送 |
| 技能库（全局 9 + 项目 1） | [`../skills/`](../skills/) | ✅已推送 |
| 回归套件（核心 7 + smoke 6） | [`../_regress.js`](../_regress.js) | ✅已推送 |
| 学习平板应用本体 | `../server.js` · `../index.html` · `../教师端.html` · `../ui.*` · `../store.js` | ✅已推送 |
| 双工作台源 | [`../_workbench/`](../_workbench/) | ❌未推送 |
| 文件清单 MANIFEST | [`../MANIFEST.md`](../MANIFEST.md) | ❌未推送 |
| 作业与交接指南 | `../README.md` · `../AGENTS.md` · `../HANDOFF*.md` | ✅已推送 |

---

## 🔄 自动更新约定

> **凡涉及资产（课文 / 词汇 / 技术栈任一侧）的变更，均须同步更新本目录。**

1. 在 `../_gen_assets.py` 的 `ROWS` 增删/修改对应行；
2. 重跑 `python ../_gen_assets.py` → 三件套自动同步；
3. 课文侧底层（正课文/句数）另见 `../reports/正课文清单.*` 三件套（生成器 `../_gen_zwk_list.py`）；
4. 技术栈文件增删后同步 `../MANIFEST.md`。

---

## ❓ 尚未纳入的课程资产（待建/待补）

| # | 缺口 | 说明 | 建议 |
|---|---|---|---|
| 1 | **U8 篇章词汇页** | U8 四篇**分析已完成**（覆盖率/分层/超纲 → `篇章词汇_产出/u8_*`），但 `词汇诊断/` 仍是 U7/U12（共 13 页），**缺 U8 词汇页 HTML** | 反推模板生成 U8 四页 |
| 2 | **U1–U6 / U9–U11 篇章词汇页** | 同上，仅有 U7/U12 | 按需批量生成 |
| 3 | **全 12 单元正课文** | 时间轴仅 U7/U8/U12（12/48 正课文已制作） | 跑 `_align_unit.py --unit N` |
| 4 | **官方 CD 198 轨音频入库** | 素材库有 198 轨，仓库仅 16 篇（其余为版权未入库） | 保持库外 |
| 5 | **练习册 / 测试卷 / 语法·词汇卷** | 素材库每单元含技能/测试/词汇/语法卷（PDF/DOCX），未纳入本目录 | 按教学需要单列 |
| 6 | **双工作台页面发布态** | `_workbench/` 源已备，但与资料库在线页面对应关系未记录 | 补发布链接与页面 ID |
| 7 | **`词汇教学技能包-20260928`** | 未跟踪的 4 技能包（与 `skills/global/` 重复） | 去重后删或入库 |
| 8 | **讲义 / 课件 xlsx** | `C阶段_教学用扩展.xlsx` 等教学产出物未单列 | 按需纳入 |
| 9 | **FCE/CAE 词表授权** | `CAE.json` 源自 Octanove（**CC BY-SA 4.0**），仓库已 public | 派生文件须同协议共享 |

---

## GitHub 推送状态速览

- **已推送** 13 项：应用本体、时间轴、课文音频、技能库、对齐工作流与工具链、回归套件、指南文档等。
- **未推送** 16 项：正课文清单三件套、词汇诊断页与词表、SB 原版视频、单元篇章清单、`_workbench/`、`MANIFEST.md`、本目录三件套等（多为 gitignore / 库外 / 版权素材 / 未提交新成果）。
- 让「正课文清单三件套 / `_gen_*.py` / `_workbench/` / 课程资产」入库并推送，可显著提升「已推送」占比。
