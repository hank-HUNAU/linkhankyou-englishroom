# 技能文件（内容生产工具链）

这里是 TH!NK 学习平板应用的配套技能文件。**应用运行时不需要它们**——应用只消费技能产出的内容（词汇报告、`词汇诊断/`、`timeline.json`、朗读卡等），不加载技能本身。技能全部缺席时应用照常启动，只是内容无法再生产。

按来源与目的地分两份，**解压/复制时请勿合并到同一目录**：

| 目录 | 来源 | 去向 |
|---|---|---|
| `project/` | `<工作区>/.trae/skills/` | 新工作区的 `.trae/skills/` |
| `global/` | `<用户>/.trae-cn/skills/` | 新环境的 `.trae-cn/skills/`（跨项目共享） |

## project/ —— 项目级技能

| 技能 | 作用 |
|---|---|
| `sentence-alignment` | 句级音频与文本对齐，产出 `assets/timeline.json` |
| `text-vocab-coverage` | 多词表词汇命中率检测，产出 `词汇诊断/` 与词表 xlsx |

## global/ —— 全局技能

| 技能 | 作用 |
|---|---|
| `local-mineru` | 教材 PDF 与图片的本地解析 |
| `article-vocab-analyzer` | 词汇分析主技能，四词表分层与 CEFR 标注 |
| `text-vocab-coverage` | 词汇覆盖检测 |
| `cet-cn2en-scholar` | 中译英学习卡流水线 |
| `british-phonetics` | 英式音标与朗读标注（软分支） |
| `student-vocab-cards` | 学生记忆词卡（软分支） |
| `exam-paper-bank` | 试卷题库包生成 |
| `teacher-vocab-prep` | 教师备课本与考点矩阵（软分支） |
| `sentence-alignment` | 句级对齐 |
| `chunk-splitter` | 句中意群切分 |

## 产出对应关系

词汇分析产出词汇报告与 `词汇诊断/`；句级对齐产出 `assets/timeline.json`；`teacher-vocab-prep`、`student-vocab-cards`、`british-phonetics` 是三个软分支，由 `article-vocab-analyzer/scripts/vocab_pipeline.py` 串联编排。

## 同名技能的两处状态

`sentence-alignment` 与 `text-vocab-coverage` 同时出现在 `project/` 与 `global/` 下。两者的处置状态不同：

**`text-vocab-coverage` 已统一为单一版本。** 项目版新增了姓氏起头识别（`PER_surname`）与多词机构匹配（`ORG_multi`），全局版此前是更早的快照。已把项目版的 `entity_classify.py` 与 `entity_lexicon.json` 合并回全局，现两处内容一致，其余文件本就相同。

**`sentence-alignment` 已统一到全局版，且方向与直觉相反。** 全局版（更晚编辑）明确「词级点读（WORDS / `.wd`）下线，本技能只保证句级对齐」，与应用现状一致——`index.html` 中的点读只有句级 `TL` 与 `CHUNKS`，没有任何 `WORDS` 数据结构。`project/` 下曾是更早的副本，仍把词级归属钳制作为管线第 ③ 层。现已用全局版覆盖该陈旧副本，并把项目版独有的「端到端总流程」一节（剔除词级内容后）回灌进全局版，四处内容一致。**不要用旧版项目副本反向覆盖全局版**，那会把已废弃的词级流程重新引入。

另注：全局的 `article-vocab-analyzer` 与 `text-vocab-coverage` 各装一套分析能力，`assess_vocab.py` 分别是 29,559 B 与 14,969 B，`NGSL.json`、`NAWL.json` 两份词表也不同。

## 依赖提示

`local-mineru` 需要独立的 Python 环境，`requirements.txt` 与 `scripts/install-env.ps1` 在包内。其余技能的 Python 脚本依赖 `openpyxl`；`british-phonetics` 下载真人发音需要联网。

## 未收录的内容

`__pycache__/` 与 `*.pyc` 编译产物首次运行自动重建；`local-mineru/tests/` 的测试样例（1.65 MB 的 PDF 与图片）与应用无关；`british-phonetics/攀登者朗读卡.xlsx` 是示例运行产物，不是技能源文件。三者均未入库。
