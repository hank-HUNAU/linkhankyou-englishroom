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

## global/ —— 全局技能

| 技能 | 作用 |
|---|---|
| `local-mineru` | 教材 PDF 与图片的本地解析 |
| `article-vocab-analyzer` | 词汇分析主技能，四词表分层、专名分类与 CEFR 标注 |
| `cet-cn2en-scholar` | 中译英学习卡流水线 |
| `british-phonetics` | 英式音标与朗读标注（软分支） |
| `student-vocab-cards` | 学生记忆词卡（软分支） |
| `exam-paper-bank` | 试卷题库包生成 |
| `teacher-vocab-prep` | 教师备课本与考点矩阵（软分支） |
| `sentence-alignment` | 句级对齐 |
| `chunk-splitter` | 句中意群切分 |

## 产出对应关系

词汇分析产出词汇报告与 `词汇诊断/`；句级对齐产出 `assets/timeline.json`；`teacher-vocab-prep`、`student-vocab-cards`、`british-phonetics` 是三个软分支，由 `article-vocab-analyzer/scripts/vocab_pipeline.py` 串联编排。

## 同名技能的状态

`sentence-alignment` 同时出现在 `project/` 与 `global/` 下，两处内容一致。

**`sentence-alignment` 已统一到全局版，且方向与直觉相反。** 全局版（更晚编辑）明确「词级点读（WORDS / `.wd`）下线，本技能只保证句级对齐」，与应用现状一致——`index.html` 中的点读只有句级 `TL` 与 `CHUNKS`，没有任何 `WORDS` 数据结构。`project/` 下曾是更早的副本，仍把词级归属钳制作为管线第 ③ 层。现已用全局版覆盖该陈旧副本，并把项目版独有的「端到端总流程」一节（剔除词级内容后）回灌进全局版，四处内容一致。**不要用旧版项目副本反向覆盖全局版**，那会把已废弃的词级流程重新引入。

## 已退役：text-vocab-coverage

`text-vocab-coverage` 已从 `project/`、`global/`、工作区 `.trae/skills/`、用户 `.trae-cn/skills/` 四处全部删除，能力由 `article-vocab-analyzer` 承接：

- 专名分类 `entity_classify.py` 与词典 `entity_lexicon.json` 已迁入 `article-vocab-analyzer/scripts/`（含项目版新增的姓氏起头识别 `PER_surname` 与多词机构匹配 `ORG_multi`）。
- 词汇分析改用 `article-vocab-analyzer` 版 `assess_vocab.py`（超集）：新增 `AGENT_ER_NOUNS`（阻止 `teacher`→`teach` 这类 -er 名词过度词干化）、弯引号归一与纯引号 token 过滤。`lemma_candidates` 对 -er 名词的候选集因此与旧版不同（如 `owner` 不再归并到 `own`），依赖该函数的词汇分级结果可能微调。
- 两版 `NGSL.json`、`NAWL.json` 词表内容不同，`article-vocab-analyzer` 的是较新快照。
- 删除前四处副本字节一致，内容仍可从仓库 git 历史取回。

引用方已改指新技能：工作区 `tools-whisper/` 下的 `ketpet/build_entities.py`、`ketpet/verify_entities.py`，解析走「工作区 `.trae/skills/` 优先、回落全局 `.trae-cn/skills/`」。原第三个引用方 `tools-whisper/build_page.py` 是遗留脚本（仍生成已下线的词级 `WORDS`，重跑会把 `index.html` 从约 176 KB 回退到约 80 KB），已一并删除；其模板 `index.html.template`（约 55 KB，仓库外未跟踪）也已删除。

## 依赖提示

`local-mineru` 需要独立的 Python 环境，`requirements.txt` 与 `scripts/install-env.ps1` 在包内。其余技能的 Python 脚本依赖 `openpyxl`；`british-phonetics` 下载真人发音需要联网。

## 未收录的内容

`__pycache__/` 与 `*.pyc` 编译产物首次运行自动重建；`local-mineru/tests/` 的测试样例（1.65 MB 的 PDF 与图片）与应用无关；`british-phonetics/攀登者朗读卡.xlsx` 是示例运行产物，不是技能源文件。三者均未入库。
