---
name: "article-vocab-analyzer"
description: "对任意英文文章做九词表（Pre A1 Starters / A1 Movers / A2 Flyers / KET / PET / FCE / CAE / NGSL / NAWL）词汇分析：分词+lemma归一+短语先查+专名/数字分流+最小层归属分层+超纲检测，并内置 CEFR 难度标签（Oxford 3000/5000，A1–C1 自动标注、无需联网），输出覆盖率/Range/超纲/难度等级报告。当用户提供文章并要统计某词汇表命中率、词汇覆盖、难度测绘、标 CEFR、难度等级、超纲词、分层词汇卡时调用。"
---

# 一篇文章词汇分析（Article Vocabulary Analyzer）

把任意英文文章切词后，按 **九词表** 判定每个词属于哪一层，输出 **命中覆盖率**、**归属分层**（最低层只归一层，闭环不重叠）、每词条的 **Range（跨句广度）/频次/原文例句**、**内置 CEFR 难度标签**（Oxford 3000/5000，A1–C1 自动标注、无需联网，查不出的规范留空）、以及 **超纲词清单**。用于评估课文难度、选取听写目标词、划分层重点词卡、学术测覆盖率等。

**定位**：本技能是通用的英文课文词汇分析工具——分析**任意英文课文**，交付分层/覆盖率/超纲/CEFR 等结构化结果，供编写教学资料与学习资料使用。技能本身不预设任何资料版式、界面或视觉偏好；具体材料如何编写由使用方决定。

## 学理定位（三正交构念 · 九词表）

| 词表 | 层位 | 回答的问题 | 属性 | 学理 / 来源 |
|---|---|---|---|---|
| A1_Starters / A1_Movers / A2_Flyers | Pre A1–A2 | 是不是**少儿入门词** | **少儿底表** | 剑桥少儿官方词表（2018）；补 pre-A1/A1 断层 |
| KET / PET | A2 / B1 | 考不考 / 属哪个考点层 | **考试考察** | 覆盖→可读性（Hu & Nation 2000）；剑桥官方锚定 |
| FCE / CAE | B2 / C1 | 高段考不考 | **考试考察（高段）** | 剑桥**不公布** FCE/CAE 词表 → CEFR-J B2 / Octanove C1 替代 |
| NGSL / NAWL | 频率 / 语体 | 是不是高频 / 是否学术 | **频率与语体** | 频率假说（Ellis 2002）；通用→学术覆盖阶梯（Browne 2013） |
| CEFR（可选） | A1–C1 | 读起来有多难 | **难度坐标** | 熟练度阶段（CEFR 2001）；i+1（Krashen 1985） |

**关键约定**：前七层（少儿底表 + 考点阶梯）由 `registry.json` 顺序决定「最低层只归一层」；KET≈A2、PET≈B1、FCE≈B2、CAE≈C1 由 CEFR 锚定，NGSL/NAWL 是频率/语体轴（非难度轴）。CEFR 仅作为一篇文章难度剖面的**独立正交模块**，来源优先级 EVP → 词典星标 → **留空不猜**。**注意**：FCE/CAE 为 CEFR 分级**替代源**（非剑桥官方构念），语义上是 B2/C1 词表而非严格考试词表。

## 目录结构

```
article-vocab-analyzer/                  # 技能根目录(全局装于 <用户>/.trae-cn/skills/, 项目级则位于 <项目>/.trae/skills/)
├── SKILL.md
├── USAGE.md                             # 使用说明(触发信号/工作流/速查)
├── 词汇分析技术文档.md                     # 学理与技术实现文档
├── scripts/
│   ├── assess_vocab.py                  # 主脚本(自包含, 无需第三方依赖除 openpyxl)
│   ├── word_bank.py                     # 词汇库(SQLite累积+Excel视图导出), 被 --db 按需加载
│   ├── vocab_run.py                     # 一键: 分析 + 入班库 + 导出三视图
│   ├── vocab_pipeline.py                # 一键: 主技能 + 三个软分支(学生卡/备课本/语音卡)
│   └── vocab_merge.py                   # 整合各源 xlsx 为教师版/学生版
└── wordlists/
    ├── registry.json                    # 词表注册与顺序(九层, 见下)
    ├── A1_Starters.json                 # 剑桥少儿 Pre A1(入门底表)
    ├── A1_Movers.json                   # 剑桥少儿 A1
    ├── A2_Flyers.json                   # 剑桥少儿 A2
    ├── KET.json                         # 官方KET(A2)基表, 含词性 raw
    ├── PET.json                         # 官方PET(B1)基表, 含词性 raw
    ├── FCE.json                         # FCE(B2)替代源 = CEFR-J B2
    ├── CAE.json                         # CAE(C1)替代源 = Octanove C1
    ├── NGSL.json                        # NGSL通用高频(无词性, 含全屈折 forms)
    ├── NAWL.json                        # NAWL学术层(无词性, 含全屈折 forms)
    ├── cefr.json                        # CEFR标签(A1–C1), 缺省自动加载, 无需联网
    └── phrase_extra.json                # 教学扩展短语种子库(教师自增), 自动加载
```

**九层归属顺序**（`registry.json`）：`A1_Starters < A1_Movers < A2_Flyers < KET < PET < FCE < CAE < NGSL < NAWL`。前七层为「少儿底表 + 考点阶梯」，后两层为频率/语体轴。导入脚本：`_import_yle.py`（少儿三层）、`_import_fce_cae.py`（FCE/CAE）。

> 说明：`registry.json` 只声明**分层词表**（决定九层归属顺序，见上）；`cefr.json`、`phrase_extra.json`、`registry.json` 自身属辅助文件，脚本按名显式排除，不进词表循环。

## 词表统一格式

每个词表文件均为 JSON：

```json
{"entries": [{"head": "...", "pos": "...", "raw": "..."}],
 "forms": ["form1", "form2", ...]}
```

- `head` 支持斜杠合并形式（`a/an`、`centre/center`）与多词短语（`a lot of`）。
- `forms` 为研究版全部屈折词形，用于**覆盖/Range 统计兜底**（NGSL/NAWL 提供；KET/PET 无则忽略）。
- KET/PET 由官方 PDF 解析得到（含词性 raw 可支撑例句回查）；NGSL/NAWL 来自三件套 research 版。词性在 KET/PET 中有、NGSL/NAWL 为空——命中明细里 NGSL/NAWL 词性列留空属正常。

`registry.json` 声明顺序。**把任意词表（含未来中高考词表）做成同格式 json 放入 `wordlists/` 即自动并行纳入，无需改脚本**——支持 KET/PET/中高考平行探针的考试适配度推断。

## 判定流水线（优先级从高到低）

对每个 token 按序分流：

1. **数字**（阿拉伯/拼写数字，如 `5`、`five`）→ `num`。
2. **专名**（首字母大写——**跳过前导引号/撇号后判定**，如 `'Mo'`→`Mo`，且 lemma 未被任何词表收录）→ `proper`；入库时剥两侧引号存干净词形。
3. **多词短语**各词表整词匹配（最长 5→2 词优先，避免短短语拆长短语；如 `a lot of` 不被拆成 `a lot`+`of`）→ 命中对应层。
4. **单词** lemma 候选归一（表面→不规则→ing/双写/加 e 变体）+ **研究版屈折词形兜底**，逐词表判断 → 命中一个或多个（允许跨表重叠）。
5. 未命中任何词表 → **超纲** `out`。

**归属仲裁**：一个 token 命中多个词表时，按 **`A1_Starters < A1_Movers < A2_Flyers < KET < PET < FCE < CAE < NGSL < NAWL` 取最低层只归一层**，保证各层覆盖率相加闭环、不重叠、可解释。

词形归一要点（含已踩坑结论）：
- 缩写/所有格剥离：`can't→can`、`Jake's→Jake`、`children's→children`、`kids'→kids`.
- 判定集/基表一律存 **原形词头**，屈折归一交给 lemma 候选匹配，切勿对词头预做过度剥离（会误伤 `thing`→`th` 这类以 ing 结尾的非分词词）.
- lemma 候选是**候选取优**而不是一步式剥后缀，故 `practises→practise`、`stopping→stop`、`things→thing` 都能正确落到词表词目.

## 用法

```bash
# 直接给课文文本
python assess_vocab.py --text "He can kick a ball. She can't swim."

# 读文件(.txt/.md)
python assess_vocab.py --file 课文.txt

# 从 xlsx 某列读句子(如句库工作表, col 为 0 基列号)
python assess_vocab.py --xlsx 教学.xlsx --sheet "C4 句库时间轴" --col 2

# 管道输入
cat 课文.txt | python assess_vocab.py --stdin

# 附加 CEFR 难度标注 (cefr.json: {"words": {"head": "A2", ...}})
python assess_vocab.py --file 课文.txt --cefr cefr.json

# 自定义输出名(默认 vocab_report)
python assess_vocab.py --file 课文.txt --out my_report

# 一键: 分析 + 入班库 + 导出三视图 (只传源即可, 默认入 vocab.db)
python vocab_run.py 课文.txt
python vocab_run.py 课文.txt --bank 班库.db --doc "课次A-课文1"
```

### 一键调用主技能+全部分支（vocab_pipeline.py）

只传源文件即串联落地 **主技能分析 + 三个软分支**（学生记忆卡 / 教师备课本 / 英式语音卡），防健忘——说意图即可，无需记各分支参数：

```bash
# 默认一条命令出齐：分析报告 + 学生卡 + 备课本 + 语音卡
python scripts/vocab_pipeline.py 课文.txt

# 常用开关（按需追加）
python scripts/vocab_pipeline.py 课文.txt --out 课次A_阅读1   # 自定义前缀
python scripts/vocab_pipeline.py 课文.txt --steps 主,学生卡     # 只跑指定步
python scripts/vocab_pipeline.py 课文.txt --no-cambridge        # 语音只用有道
python scripts/vocab_pipeline.py 课文.txt --voice gb-female     # 语音出英女真人发音(local mp3)
python scripts/vocab_pipeline.py 课文.txt --limit 20            # 学生卡/语音防限流缓冲
python scripts/vocab_pipeline.py 课文.txt --bank 班库.db --doc "课次A-1"  # 主步并入班库+导视图
python scripts/vocab_pipeline.py --text "直接给文本"              # 也可直接给文本
```

默认 `--steps` 全跑会在最后自动整合出 **`<out>_教师版.xlsx`（权威合集）** 与 **`<out>_学生版.xlsx`（学习向5页签）**；也可显式 `--steps 整合` 单独重整合已生成的各源 xlsx。

调用话术（用户说一句即可，由助手组装命令）：
- "分析这篇课文并出齐学生卡/备课本/语音卡" → `python scripts/vocab_pipeline.py <文>`
- "只出学生卡和语音" → 追加 `--steps 学生卡,语音`
- "语音要英女/英男真人发音" → 追加 `--voice gb-female/gb-male`

### 词汇库累积与视图导出（--db）

单篇报告是主产物；传 `--db` 时把本篇词项级结论 UPSERT 进 SQLite 词库，实现跨文章累积（频次、不同文章数 n_doc、归属层热点、累积例句、可选 CEFR），再导出教学/研究用的 Excel 视图。

```bash
# 把本报告 UPSERT 入库；--doc 指定文章标识(缺省用文件路径/时间戳)
python assess_vocab.py --file 课文.txt --db vocab.db --doc "高考阅读1"

# 从 SQLite 词库导出 Excel 视图(分层词卡/补卡清单/研究覆盖)
python assess_vocab.py --file 课文.txt --db vocab.db --db-export bank_views.xlsx
```

- `--db vocab.db`：词库 SQLite 路径，传则累计入库。按 `(lemma,pos)` 主键跨篇聚合，`word_docs` 表保证同一文章内某词只计 1 次到 `n_doc`，`docs` 表记录每次入库来源。
- `--doc "标识"`：入库时的文章标识（优先使用；缺省回退为输入文件绝对路径，文本输入用 `inline-<时间戳>`）。
- `--db-export bank_views.xlsx`：从词库导出 Excel 视图——Sheet「分层词卡」(隶属层+教学分卡)、「补卡清单」(out/NAWL 累积、按 n_doc 排序定补卡优先级)、「研究覆盖」(文章×词表来源×入库时间)。可单跑，也可与 `--db` 同传。

输出写到当前目录：
- `vocab_report.xlsx` — Sheet「覆盖率」：各层命中token数/占比、**归属分层闭环**、专名/数字、超纲；每词表一个「命中-词表」明细Sheet（词/短语、词性、频次、跨句Range、CEFR、原文例句）；Sheet「超纲词」（词/频次/CEFR/**原文例句**）；**Sheet「专名词」**：识别出的地名/机构/物名等首字母大写专名单词，列为「专名\|频次」，作为认识清单，零联网。
  - `--mwe` 时另出 **Sheet「候选待核短语」**：N-gram 滑动窗口(2~4词)提取+互信息(MI)打分、排除已在词表的词组，列为「待核短语\|词数\|频次\|互信息MI」，供教师核注后写入 `wordlists/phrase_extra.json`。
- `vocab_report.json` — 结构化逐 token 判定结果（`kind/lemma/hit/layer/cefr`），供后续程序/听写界面消费。

## 基表生成与新词表接入

- KET/PET 官方 A2/B1 词表为多栏 PDF：PyMuPDF `dict` 结构化行，按 `x0` 聚类分栏、`y` 容差聚类成行；词头行判定=左缘缩进浅+含 POS 括号+非句读整句；例句缩进更深剔除。产出 `{head,pos,raw}` 序列。
- NGSL/NAWL 由三件套 `*_for_research.csv` 生成：第一列 head 为 entries，其余列并入 `forms`。CSV 可能非 UTF-8（NAWL 为 latin-1），读取需做编码探测。
- **接入新词表（如中高考）**：转成 `{"entries":[{head,pos,raw}],"forms":[...]}` 放入 `wordlists/`，在 `registry.json` 的顺序里显式声明层级位置，重启即生效。中高考词表可与现有九层并行，实现中国课标段适配度推断。

## 边界与学理提醒（教学/科研）

1. **版权**：KET/PET/中高考真题受版权保护，可参考词表**自创同构仿真题**，不可照搬真题。
2. **词表 ≠ 完整命题逻辑**：完整出卷还需语法梯度、难度校准（IRT/Rasch）、信效度检验。
3. **覆盖阈值**：学术共识 ≥95% token 覆盖才具备"可独立阅读"前提，不只报百分比还要判断够不够。
4. **同形异义词（homograph）**：NGSL 官方标注了 found/left/rose/wound 等问题，自动分析需人工复核或上下文消歧。
5. **短语优先**：命中顺序上多词单元先于单词，否则被拆碎误判超纲。
6. **lemma 归一化质量**：直接影响覆盖率数字，须固定归一策略（研究版 forms 正好支撑）。
7. **CEFR 统计口径**：CEFR 是有序分类轴（ordinal），统计须用有序/非参数方法（秩相关、有序分类回归），不可把 B1=2、B2=3 当连续变量做普通回归或加总。
8. **CEFR 数据获取**：官方 EVP 不提供整表下载；可落地来源为 CEFR-J（可下载）+ 词典 CEFR 星标（Oxford 3000/5000）。

## 与既有项目的衔接约定

- 输出 `vocab_report.json` 的 `tokens[]` 已含 `kind/lemma/hit/layer/cefr`。`layer` 字段给出归属层，可对接分层教学（全员=KET/PET 不足，中/中强=NGSL/NAWL/超纲）；`proper`/`num` 为免写锚词；带例句的 teaching 口径可支撑学生记忆词卡（原句照搬）。
- 新增课文时：把其句库（篇/序号/文本）增补到 xlsx 列，重跑本脚本即刷新全部命中标注，无需改动代码。