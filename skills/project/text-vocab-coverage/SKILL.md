---
name: "text-vocab-coverage"
description: "对任意课文做多词表（KET/PET/NGSL/NAWL）词汇命中率检测：分词+lemma归一+短语先查+专名/数字分流，输出覆盖率与 Range/超纲报告。当用户提供课文并要求统计某词汇表(如KET/PET/NGSL/NAWL)命中率、超纲词、词汇覆盖面时调用。"
---

# 课文词汇命中率检测（Multi-wordlist Coverage）

把任意英语课文切词后，按给定词表（默认 **KET/PET/NGSL/NAWL** 四表并行，可插拔增删）判定每个词属于哪一层，输出 **命中覆盖率**、每词条的 **Range（跨句广度）/频次/原文例句**、以及 **超纲词清单**。用于评估课文难度、选取听写目标词、划重点词卡等。

## 目录结构

```
.trae/skills/text-vocab-coverage/
├── SKILL.md
├── scripts/
│   ├── assess_vocab.py            # 主脚本(自包含, 仅依赖openpyxl)
│   ├── entity_classify.py         # 专名→实体类型分类(PER/GPE/ORG/OTH/SYM)
│   ├── entity_lexicon.json        # 实体词根词典(用户可编辑, 人名/地名/国家/机构后缀/符号专名)
│   └── convert_csv_to_wordlist.py # 把 NGSL/NAWL 类 lemmatized CSV 转成词表json
└── wordlists/
    ├── registry.json              # 词表注册与顺序
    ├── KET.json                   # 官方KET(A2)规范化基表
    ├── PET.json                   # 官方PET(B1)规范化基表
    ├── NGSL.json                  # NGSL 1.2 教学版 (从用户CSV转换)
    └── NAWL.json                  # NAWL 1.2 教学版 (从用户CSV转换)
```

## 词表统一格式

每个词表文件均为 JSON：`{"entries": [{"head": "...", "pos": "...", "raw": "..."}]}`。
- `head` 支持斜杠合并形式（`a/an`、`centre/center`）与多词短语（`a lot of`）；单条可有可选的 `forms`（词族全部屈折形式，一并并入词集，命中最稳）.
- 官方 A2/B1 词表由 PDF 解析得到（见下"基表生成"）；NGSL/NAWL 等 lemmatized 教学词表用 `convert_csv_to_wordlist.py` 转成同格式放入 `wordlists/` 即自动并行加载.

`registry.json` 里声明 KET/PET/NGSL/NAWL 的判定顺序；若要增删词表，改该文件的数组 + 把对应 json 放/移出 `wordlists/` 即可，无需改脚本.

## 判定流水线

对每个 token 按序分流：

1. **数字**（阿拉伯/拼写数字，如 `5`、`five`）→ 记为 `num`.
2. **专名**（首字母大写且其 lemma 未被任何词表收录）→ 归为**实体类型** `ent`：`PER`(人名·角色) / `GPE`(地名·国家) / `ORG`(机构·品牌) / `OTH`(其他专名) / `SYM`(符号专名, 月份/星期/节日/居民词)。判据来自 `entity_lexicon.json` + 上下文规则，支持多词专名合并（`Sloan Henderson`→PER、`New York`→GPE、`Greece Athena High School`→ORG）。其中 SYM 只做标注、不进实体表。
3. **多词短语**各词表整词匹配（最长 5→2 词优先，避免短短语拆长短语；如 `a lot of` 不被拆成 `a lot`+`of`）→ 命中对应词表.
4. **单词** lemma 候选归一（表面→不规则→ing/双写/加 e 变体），逐词表判断该词是否被收录 → 命中一个或多个词表（允许跨表重叠）.
5. 未命中任何词表 → **超纲** `out`.

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
python assess_vocab.py --xlsx 教学.xlsx --sheet "句库时间轴" --col 2

# 管道输入
cat 课文.txt | python assess_vocab.py --stdin

# 自定义输出名(默认 vocab_report)
python assess_vocab.py --file 课文.txt --out my_report
```

输出写到当前目录：
- `vocab_report.xlsx` — Sheet「覆盖率」：各词表命中token数/占比、合并命中、超纲、专名/数字；每词表一个「命中-词表」明细Sheet（词/短语、词性、频次、跨句Range、原文例句）；Sheet「超纲词」.
- `vocab_report.json` — 结构化逐 token 判定结果（供后续程序/听写界面消费）.

## 基表生成

**KET/PET (官方 A2/B1 多栏 PDF)**：用 PyMuPDF `dict` 结构化行，按 `x0` 聚类分栏、`y` 容差(≤4px)聚类成行（词头与 POS 括号常因 y 差 1-2px 拆行）；词头行=左缘缩进浅 + 含 POS 括号 + 非句读整句，例句行因缩进更深剔除；产出 `{head,pos,raw}`.

**NGSL/NAWL (lemmatized 教学 CSV)**：跑 `convert_csv_to_wordlist.py NGSL.csv NGSL.json --label "NGSL 1.2"`，脚本自动识别编码(utf-8/latin-1)、跳 `#` 注释行、收整行词族为 `forms`。教学版 CSV 无词性列，`pos` 置空。

## 与既有项目的衔接约定

- 本技能输出 `vocab_report.json` 的 `tokens[]` 已含 `kind/lemma/hit`，可继续对接听写模式的 T1 核心词（KET/PET 命中词）挖空；`kind=="ent"` 的 token 其 `hit` 为实体类型（PER/GPE/ORG/OTH/SYM），`num` 为数字——PER/GPE 等作为免写锚词，`spell` 开关开启后才进入"专名练拼写".
- 专名细分如需扩展，编辑 `scripts/entity_lexicon.json`（人名/地名/国家/机构后缀/符号专名），新课文自动套用；首次遇到无法判定的专名会落到 `OTH`，可一次性人工校对后回填词典。
- 新增课文时：把其句库（篇/序号/文本）增补到 `C4 句库时间轴` 或换成任意 xlsx 列，重跑本技能即刷新全部命中标注，无需改动代码。