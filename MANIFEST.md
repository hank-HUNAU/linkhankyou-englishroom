# 文件清单（MANIFEST）· TH!NK 学习平板原型

> 本清单把仓库文件按**职责**归类：核心运行时 / 依赖开发 / 内容生产 / 溯源参考 / 文档 / 弃用候选 / 运行时不入库。
> 更新于 2026-10-24 · 基准：`git ls-files` 3696 个已跟踪文件 + 未跟踪/忽略项。
> 维护：文件增删后更新本表。删除任何文件前先确认是否在上文引用。

---

## A. 核心运行时（应用本体 · 缺一不可）

后端零 npm 依赖，只用 Node 内建 `http` + `node:sqlite`（Node ≥ 22.5）。

| 文件 | 体积 | 作用 |
|---|---|---|
| `server.js` | 29 KB | 唯一后端：静态服务、账号认证、KV 存储、聚合接口、定时备份、安全响应头 |
| `store.js` | 7 KB | localStorage → 云同步垫层（教师端/词汇页引用；**学生端已不加载**） |
| `ui.css` | 4 KB | 设计令牌：主色/圆角刻度/阴影/组件契约 |
| `ui.js` | 5 KB | SVG sprite 图标系统，三页共用 |
| `index.html` | 213 KB | **学生首页** + 点读页：内嵌课文、句级时间轴（`==TL-DATA-*==`）、词汇测试引擎 |
| `login.html` | 7.6 KB | 登录 / 注册入口 |
| `教师端.html` | 58 KB | 教师工作台：班级 / 学生 / 任务 / 学情 / 题库分析 |
| `学生端.html` | 1.3 KB | 已退役为跳转壳（旧链接兼容） |
| `gen-cert.js` | 2 KB | 生成 HTTPS 自签证书到 `certs/` |
| `package.json` | 0.6 KB | 脚本与 Node 版本要求 |
| `.nojekyll` | 0 | 禁用 Jekyll，GitHub Pages 按原样伺服 |
| `assets/p*.mp3` | 49 个 / 62 MB | 课文音频（U1–U12 每单元 4 篇 + p202），点读/跟读唯一音源 |
| `assets/word_audio/` | 1057 个 / 17 MB | 词汇音频（正典归档 `00_词汇音频/`），规约 `_VOCAB_WORKFLOW.md` §2.3 |
| `assets/timeline.json` | 164 KB | **句级时间轴唯一权威源**（49 篇 / 1153 句），`_timeline_check.js` 盯一致性 |

## B. 依赖 / 开发（回归门禁 · 构建）

| 文件 | 体积 | 作用 |
|---|---|---|
| `_regress.js` | 12 KB | **一键回归入口**（套件定义在顶部 `SUITE` 数组），双校验判定 |
| `_check.js` | 0.8 KB | HTML 内联脚本 + JS 语法检查 |
| `_align_check.js` | 3 KB | 设计令牌完整性、硬编码圆角残留、三页组件取值一致 |
| `_check_icons.js` | 2 KB | 三页引用图标 id 是否都在 sprite 中定义 |
| `_smoke.js` | 10 KB | API 层冒烟 40 项（账号/存储/聚合/权限） |
| `_smoke_follow_stage.py` | 4 KB | 跟读两步（跟句→影子）UI 与状态机 |
| `_smoke_bank_ui.py` | 5 KB | 题库分析闭环 |
| `_smoke_bridge.py` | 5 KB | 预习→复习衔接引导 |
| `_smoke_roster.py` | 5 KB | 花名册 / 班级 / 学情 / 助教只读 |
| `_smoke_immerse.py` | 2 KB | 学生端沉浸式任务区渲染与跳转 |
| `_smoke_multi.py` | 4 KB | 跨设备同步 |
| `_sync_timeline.js` | 2 KB | `timeline.json` → `index.html` 内联块同步 |
| `_timeline_check.js` | 3.5 KB | 单一数据源门禁（timeline.json ↔ index.html 逐条比对） |
| `.venv-align/` | gitignored | 对齐脚本的本地 Python 虚拟环境（torch/faster-whisper/PyAV） |

## C. 内容生产（句级对齐 · 词汇 · 生产工具链）

| 文件/目录 | 体积 | 作用 |
|---|---|---|
| `_align_unit.py` | 8.9 KB | **正课文句级时间轴唯一生产入口**（`--unit N` 全自动） |
| `_unit_8_source.json` | 6.5 KB | 源文本模板（新单元照此写 `_unit_N_source.json`） |
| `_ALIGNMENT_WORKFLOW.md` | 6.9 KB | **句级对齐权威规约**（方法/清单/坑/门禁） |
| `_VOCAB_WORKFLOW.md` | 新增 2026-10-24 | **词汇四链权威规约**（篇章词表/主题词表/词音频/诊断页 + 引擎规则 + 坑） |
| `_RELEASE_WORKFLOW.md` | 新增 2026-10-24 | **落库与上线权威规约**（三条硬规约/发布检查单/基线记录/回滚/API 兜底） |
| `_extract_u14_text.py` + `_align_u14.py` + `_merge_u14.py` | 新增 2026-10-24 | U1–U4 正课文三件套（TB 提取 → 对齐 → 校验/音频/timeline 合入）；中间产物 `_u14_source.json` / `_u14_words.json` / `_u14_report.json` |
| `tools/audio-alignment/` | 16 文件 + `_tb_cache/`67 txt | 教师用书栏目标题 ↔ 官方 CD 198 轨对齐工具链（产 `_alignment.json` 与 `reports/` 对照表） |
| `skills/global/` | 9 技能 | `local-mineru` `article-vocab-analyzer` `cet-cn2en-scholar` `british-phonetics` `student-vocab-cards` `exam-paper-bank` `teacher-vocab-prep` `sentence-alignment` `chunk-splitter` |
| `skills/project/` | 1 技能 | `sentence-alignment`（项目版去向 `.trae/skills/`） |
| `skills/README.md` | 4.5 KB | 技能分发与退役说明 |
| `_gen_review_sheet.js` | 5 KB | 生成干扰项审校工作表 CSV |
| `_patch_vqdis.js` | 1.6 KB | 把人工审校的干扰项写入词表 `dis` 字段 |
| `_patch_vocab.js` | 7.5 KB | 批量修订词表字段 |
| `_inject.js` | 0.8 KB | 批量注入片段到页面 |
| `scan_index.py` / `scan_tl.py` / `shot_unit.py` | <1 KB each | 索引 / 时间轴 / 单元页扫描与截图 |
| `split_audio.py` | 6 KB | 音频按句切分（产句级 wav） |
| `_gen_zwk_list.py` | 14.6 KB | 生成 `reports/正课文清单.{csv,md,html}` 追踪三件套 |

## D. 溯源 / 参考工具（HANDOFF §7.5 点名「入库别删」）

| 文件 | 体积 | 作用 |
|---|---|---|
| `_align_audio.py` | 15 KB | 句级边界能量法体检（`check\|refine\|dump\|cmp`） |
| `_align_report.md` | 20 KB | 重切清单与体检结论 |
| `_bridge_aligner.py` | 25 KB | 交叉验证器（TB 文本 ↔ ASR 双证据） |
| `_bridge_bounds.json` / `_bridge_report.md` | 105 KB / 11 KB | 交叉验证产物 |
| `_match_source.py` | 5 KB | 时长指纹溯源 |
| `_sents_bounds.py` | 6 KB | 切片边界反算（互相关） |
| `_sents_v2_bounds.json` | 16 KB | **人工核查结果保全载体**（42 句全量） |
| `_source_match.json` | 11 KB | 项目音频 ↔ 素材库源轨匹配（12 篇） |
| `_trace_source.py` / `_trace_content.py` | 3.3 / 4.2 KB | 全库时长指纹 / 内容互相关溯源 |
| `_video_probe.py` | 2.3 KB | 视频音轨时长探测（PyAV） |
| `_boundary_diag.txt` | 1.2 KB | 边界诊断输出 |

## E. 文档

| 文件 | 体积 | 作用 |
|---|---|---|
| `README.md` | 15.5 KB | 项目总览 / 快速开始 / 目录结构 / 接口一览 / 回归 / 版权合规 |
| `AGENTS.md` | 14 KB | 智能体作业指南（环境/约定/架构/验证/迁移遗留） |
| `HANDOFF.md` | 5 KB | 交接说明（早期） |
| `HANDOFF-workbuddy.md` | 30 KB | 交接说明（2026-10-12，含 §7 溯源与清理指引） |
| `LICENSE` | 1 KB | UNLICENSED（保留所有权利） |

---

## F. ✅ 已弃用文件（**已于 2026-10-13 全清** · 下表为清理记录）

> 依据：`AGENTS.md`「2026-10-13 起已废止人工试听定案」、`_ALIGNMENT_WORKFLOW.md` §1、`HANDOFF-workbuddy.md` §7.6。
> 以下均已删除：**跟踪文件 15 个**可 `git checkout <删除前commit>^ -- <文件>` 恢复；**忽略项为永久删除**（`assets/sents*` 边界已保全于 `_sents_v2_bounds.json`，截图可重生成）。

### F1 — 高置信弃用（旧工作流产物，已被 `_align_unit.py` 全自动取代）

| 文件 | 体积 | 状态 | 依据 |
|---|---|---|---|
| `_ab_candidates.py` | 6.3 KB | 跟踪 | 人耳 A/B 终审**已废止** |
| `_ab_cand_p069.html` `_ab_cand_p072.html` `_ab_p066/067/069/072.html` | 6 个 / 42 KB | 忽略 | A/B 试听页，一次性 |
| `_pilot_whisper.py` `_pilot_whisper_all.py` `_pilot_match_dp.py` | 3 个 / 11 KB | 跟踪 | 早期 ASR pilot，已被生产脚本取代 |
| `_whisper_all_words.json` `_whisper_bounds.json` `_whisper_bounds_dp.json` `_whisper_words_p067.json` | 4 个 / 96 KB | 忽略 | whisper 中间产物 |
| `_u8_align.py` `_u8_source.json` `_u8_timeline.json` `_u8_timeline.txt` `_u8_transcript.txt` `_u8_whisper.py` `_u8_words.json` | 7 个 / 79 KB | 跟踪 | U8 **首次硬编码跑**留痕（已被参数化 `_align_unit.py` 取代） |
| `_unit_8_timeline.json` `_unit_8_timeline.txt` `_unit_8_words.json` | 3 个 / 64 KB | 跟踪 | U8 参数化跑中间产物（终值已在 `assets/timeline.json`） |
| `_align_forced.py` | 3.3 KB | 跟踪 | 强制对齐一次性脚本 |
| `sentence_audio_check_report.html` | 11 KB | 忽略 | 旧句音频检查报告 |
| `_preview_home.png` | 0.75 MB | 忽略 | 旧首页预览截图 |
| `assets/timeline.json.bak-20261009` `-20261009b` `-20261012-u8` `-20261013` | 4 个 / 210 KB | 忽略 | 时间轴改前备份（终版已入库，旧备份可清） |

### F2 — 大体积中间产物（HANDOFF §7.6「可安全清理」）

| 文件/目录 | 体积 | 状态 | 依据 |
|---|---|---|---|
| `assets/sents/` + `assets/sents_v2/` | ~22 MB | 忽略 | 句级切分 wav；**边界已落盘 `_sents_v2_bounds.json`（§7.2）**，可清 |
| `assets/vocab_youdao.json` | 428 KB | 忽略 | README 标「当前版本未引用的旧资源」 |

### F3 — 调试产物（可选）

| 文件/目录 | 体积 | 状态 |
|---|---|---|
| `render/` | 15 MB | 忽略（渲染截图） |
| 根目录 `*.png`（`书架首页` `单元页*` `主题词汇页*` `深链_*` `篇章跟读引擎` `shot_*` `学生端_单元页`） | 11 张 / ~6 MB | 忽略（调试截图） |

---

## G. 运行时生成 / 不入库（`.gitignore` 已排除 · **勿按弃用删**）

| 内容 | 体积 | 说明 |
|---|---|---|
| `think.db` + `-wal` + `-shm` | 4.1 MB | **含真实账号与学生学情** |
| `backups/` | 452 KB | 数据库自动备份（保留 14 份） |
| `src/` | 12 MB | 教材原始 PDF / 音频（**版权**） |
| `词汇诊断/` | 14 MB | 词汇诊断页与审校表（含课文原文，**版权**） |
| `*.xlsx`（`KET_PET_总表/词表`、`C阶段_教学用扩展`） | 250 KB | 教学产出物 |
| `p067_p070_结构化笔记.md` `p067_p070_逐字稿与校对.md` | 12.6 KB | 含课文原文/译文 |
| `单元篇章清单_unit1-12.html` | 12 KB | 含课文标题 |
| `certs/` `server.log` `server.err` | — | 证书 / 日志（运行时生成） |

---

## H. 未跟踪待入库（新成果，**非弃用**）

| 文件/目录 | 体积 | 建议 |
|---|---|---|
| `reports/正课文清单.csv` / `.md` / `.html` | 20 / 24 / 58 KB | **入库**（课文追踪唯一来源三件套） |
| `_gen_zwk_list.py` | 14.6 KB | **入库**（三件套生成器） |
| `_workbench/` | 275 KB | **入库**（双工作台源：HTML + schema/seed JSON） |
| `skills/词汇教学技能包-20260928/` | 966 KB | **入库**（4 技能包） |
| `skills/词汇教学技能包-20260928.zip` | 188 KB | 与解压目录重复，**可只留其一** |

---

## 汇总

| 类别 | 数量/体积 |
|---|---|
| A 核心运行时 | 12 文件 + 17 资源 |
| B 依赖/开发 | 13 文件 + `.venv-align/` |
| C 内容生产 | 8 脚本 + `tools/`(16) + `skills/`(10) |
| D 溯源/参考 | 12 文件 |
| E 文档 | 5 文件 |
| F 弃用文件（已清） | F1 ~0.6 MB · F2 ~22 MB · F3 ~16 MB · **共约 38 MB 已删除** |
| G 运行时不入库 | ~30 MB（版权/学情/备份） |

> **注意**：F 类文件已于 2026-10-13 全清；清理后核心门禁 `npm run test:core` 7/7 通过。跟踪文件可通过 `git checkout <删除前 commit>^ -- <文件>` 恢复。
