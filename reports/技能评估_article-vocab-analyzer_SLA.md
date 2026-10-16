# 技能评估：`article-vocab-analyzer`

> **评估视角**：二语习得（SLA）理论层 × 教学实践层
> **评估对象**：`skills/global/article-vocab-analyzer`（SKILL.md / USAGE.md / 词汇分析技术文档.md + 实现 `assess_vocab.py` + 四词表）
> **评估用途**：在用它为 TH!NK U8 生成篇章词汇页**之前**的准入判断
> 评估人：WorkBuddy · 2026-10-13

---

## 结论速览

**这是一份学理意识罕见的词汇分析工具**——它主动区分了「频率 vs 难度 vs 考试构念」三正交轴，并正确地声明 NGSL/NAWL 是频率/语体轴而非难度轴、CEFR 是有序分类轴不可当连续变量。这在同类工具里属上乘。

但用在 **TH!NK Starter（少儿入门）** 这一具体语境前，有三类系统性问题需要校正：

| 维度 | 评级 | 一句话 |
|---|---|---|
| 学理根基（引用是否成立） | **A** | 引文基本准确，正交构念处理专业 |
| 学理完整性（框架是否齐全） | **B−** | 缺任务负荷（ILH）、四股绳、词汇深度三大块 |
| 实现质量 | **B** | 规则式 lemma 归一，无 POS/语境消歧（自制补丁） |
| 实践可用性 | **A−** | 输入多源、输出三层 + JSON，离线自包含 |
| **本语境适配（TH!NK 少儿）** | **C+** | 无 A1 底表 · 频率表成人化 · 覆盖≠学习者已知 |
| **综合** | **B+ / A−** | 工具可用；用前须做 3 处校正 |

**主判断**：可以用于 U8，但**不能直接采信其"覆盖百分比"与"层归属"作为教学结论**，须叠加人工校正（见 §4）。若目标班为入门级，建议先补 A1/小学底表。

---

## 一、理论层评估（SLA）

### 1.1 站得住的学理（优点，逐条核）

| # | 技能主张 | 核验 | 评点 |
|---|---|---|---|
| 1 | 覆盖率 → 可读性（Hu & Nation 2000） | ✅ 成立 | 引用正确；但阈值口径须修正（见 1.2-①） |
| 2 | 频率假说（Ellis 2002；Nation 2001） | ✅ 成立 | 且**正确声明 NGSL 是频率表非难度表**——极克制 |
| 3 | 形式–意义–使用（Nation 2001） | ✅ 成立 | 学生视角数据表与 Nation 框架对齐 |
| 4 | CEFR 有序轴、统计须非参数（CEFR 2001） | ✅ 成立 | **罕见**：多数工具把 CEFR 当连续变量加总 |
| 5 | 多词语块 / 短语优先（Wray 2002；MI） | ✅ 方向正确 | 短语先于单词 + 互信息提取 + 教师核注入库 |
| 6 | 构念效度 / 测试规范（Read 2000；Messick 1989） | ✅ 成立 | 明确"词表 ≠ 完整命题逻辑" |
| 7 | 语体多维（Biber 1988） | ✅ 成立 | 明确 NAWL 只是"学术化程度"代理、非充分判据 |

> 单看这一节，该技能的学理素养高于市面多数词汇分析脚本（如通用 VocabProfile 变体）。它把"考试构念 / 频率 / 难度"三轴分开，避免了最典型的循环论证。

### 1.2 学理缺口与偏弱处（问题，逐条）

**① 覆盖阈值口径偏低。** 技能写"≥95% token 方具'可独立阅读'前提"。但 Hu & Nation (2000) 的核心结论是 **98%** 才足以支持无辅助的阅读愉悦（95% 是勉强线、理解仍受损）；Kremmel et al. (2023) 的复现研究亦支持高阈值。且该阈值源自**书面阅读**，听力/口语输入的适宜覆盖不同。
→ *修正*：报告口径应为「95% 最低 / 98% 充分」，并**按模态标注**。

**② `i+1` 的操作化有循环性。** 技能用「文本 CEFR 分布落在学习者级 +1」来落实 Krashen (1985) 的 i+1。问题有二：(a) **i 本身不可直接测量**，用 CEFR 级当 i 只是代理；(b) 输入假说/`i+1` 长期受**输出假说**（Swain 1985）与**互动假说**（Long 1996）挑战，"输入恰在 i+1"既非必要也非充分。把"覆盖率落在某级"直接等同"该级适读"，会把**学习者已知词汇量**（真正的 i）漏掉。
→ *修正*：把 CEFR 剖面当"文本难度坐标"，与"学习者已知词汇量"并列，不由文本侧单独下"适读"结论。

**③ 缺「任务诱发负荷」框架（Laufer & Hulstijn 2001）。** 这是词汇教学设计最常用的标准工具：任务的**需要 / 搜索 / 评价**三要素决定保持率。技能能回答"学哪些词"，但**不回答"用多高负荷的任务去学"**。从分析到练习之间缺这一环，直接生成词汇页易退化为"低负荷的认词"。
→ *修正*：词汇页设计显式标注每个词的 ILH 负荷意图（如"看英文猜义=高负荷"vs"给义连线=低负荷"）。

**④ 缺「四股绳」坐标（Nation 2007）。** 意义聚焦输入 / 意义聚焦输出 / 语言聚焦学习 / 流利度发展——四股须均衡。本技能的分析产物只喂**"语言聚焦学习"**一股；用于跟读/听写（属流利度 + 意义输入）时，词汇侧与另三股的接口无定义。
→ *修正*：在技能或下游资料层，给每次输出标注它服务哪一股，避免词汇教学吃掉其余三股。

**⑤ 只测广度，缺深度（Qian 1999；Schmitt 2014）。** coverage / 分层测的是**词汇广度**（是否认得该词形），不测**深度**（义项数、搭配、语域、产出性知识）。对"跟读 / 听写"够用；对"能用起来"（输出）不足。技能文档的"学生数据表"里要求了搭配与派生——**但那要靠下游补齐，技能本身不产出**。
→ *修正*：把技能定位明确写为"广度侧工具"，深度需求单列。

**⑥ 频率表的语料偏差。** 技能正确区分频率/难度，但 NGSL 来自**成人通用书面语料**；**少儿教材（child-directed, 教材复现）的频率剖面显著不同**。用 NGSL 判 TH!NK Starter 的"高频词"会有系统偏差（如教材强复现的 *rhythm / tango / vlog* 在 NGSL 里并不"高频"）。
→ *修正*：本语境下"高频=重点"的推论须打折，改用**本套教材跨单元复现频次**作补充信号。

**⑦ 加工深度论（Craik & Lockhart 1972）提了但未落地。** 文档引用它佐证"多通道触达"，但工具本身不设计多通道任务，这一引用对**本工具**是外挂的（对下游资料成立）。
→ *修正*：要么落到输出（生成多通道任务），要么降为下游原则、不在技能层声称。

### 1.3 一处引用建议补充

技能未提**测试效应/检索练习**（Roediger & Karpicke 2006）——而 TH!NK 内置**词汇测试引擎**，正是检索练习的载体。把"测试即学习（不止测量）"写进学理支撑，能让"词汇测试"环节的理论根基闭合。

---

## 二、实践层评估（教学可用性）

### 2.1 可操作性（优点）

- **输入多源**：文本 / 文件 / xlsx 列 / 管道——适配"句库一列喂全篇"。
- **输出三层**：覆盖率报告 + 逐词条明细（词性/频次/Range/例句/CEFR）+ 超纲清单；另有逐 token JSON 供界面消费。
- **归属闭环**：「最低层只归一层」使各层覆盖相加不重叠——会计干净、可解释（代价：丢失"又高频又学术"的跨层信息，但 JSON `hit` 保留）。
- **离线自包含**：无联网依赖，适合课堂/内网。
- **词表可插拔**：`registry.json` 声明层级，放新词表即并行生效（可接中高考平行探针）。

### 2.2 实践风险（须防）

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| 1 | **lemma 归一规则式**（无 POS/形态分析） | 过切/欠切直接影响覆盖数字 | 抽样复核；技能已自陈为风险 6 |
| 2 | **同形异义未消歧**（found/left/rose/wound） | 层判定、练习选词可能错 | 人工复核上下文 |
| 3 | **无 A1/pre-A1 底表** | 最低层＝KET(A2)；少儿入门"KET 层"非真底 | 补 A1/小学底表，或映射到班级真实水平 |
| 4 | **覆盖≠学习者已知** | 工具测"文本 vs A2/B1 锚"，非"文本 vs 这个班" | 人工叠加班级已知词汇画像 |
| 5 | **短语种子库极小**（`phrase_extra.json` 仅 3 条） | 少儿教材高频语块（have got / would like）靠官方表 | 对 U8 语块人工补入 |
| 6 | **CEFR 仅 4954 词**（Oxford 3000/5000 子集） | 留空多；B2–C2 近似 | 接受留空；别对空值下结论 |
| 7 | **阈值不区分模态** | 阅读阈值套用于听力/口语 | 按模态标注（同 1.2-①） |

### 2.3 版权与合规

技能**主动提醒**"KET/PET 真题受版权、只做同构仿真题"，并在 §8 标注词表来源——合规意识好。用于 TH!NK（含剑桥教材内容）时保持一致口径即可。

---

## 三、对 TH!NK 语境的专门判断

1. **锚点匹配度**：TH!NK Starter 面向小学高年级、目标约 A1–A2；KET(A2)/PET(B1) 双锚**大体匹配**，作为"考点层"探针合理。
2. **真正的错配**：教材为**少儿入门**，而工具的最底层是 A2。对 pre-A1 教学，"KET 层词"仍需再分（哪些是本课新授、哪些已会）。**这是本技能最大的语境缺口。**
3. **U8 四篇的适配**：`#Music in the forest`（微博客）/ 广播 / 访谈 / 文化文章——专名多（国名/人名）、口语语块多、复现词多。工具的 `proper` 分流与 Range 指标正好用得上；但**语块与专名的边界要靠人工**。

---

## 四、用前必做的 3 处校正（U8 准入条件）

1. **抽检 lemma 归一**：对 U8 四篇的少儿高频不规则形（*got/has got*、*'s*、*children*、*-ing* 词）抽样比对，确认无过切/漏归。
2. **底表校正 + 班级映射**：把输出"KET 层"当 **A2 锚**，再人工映射到班级真实水平；若班级为入门，先补 A1/primary 底表。
3. **语块与阈值**：把 U8 的固定语块（have got / would like / a lot of …）人工补入 `phrase_extra.json`；报告口径改为「95% 最低 / 98% 独立阅读，按模态」。

**结论：准予使用，但产出的"覆盖率数字 / 层归属 / 适读判断"三项须经上述校正后方可进入教学结论。**

---

## 五、给技能本身的改进建议（后续）

1. 接入 **ILH / Technique Feature Analysis**（Laufer & Hulstijn 2001；Nation & Webb 2011），从"分析"延伸到"任务负荷标注"。
2. 增 **四股绳** 坐标（Nation 2007），标注每次输出服务哪一股。
3. 增 **A1 / 小学底表** 与"学习者已知词汇"接口，闭合 i+1 的另一半。
4. **语境消歧**：至少在报告里对同形异义词给出上下文提示。
5. **阈值按模态参数化**（阅读/听力/口语）。
6. 补 **检索练习** 学理条目，使词汇测试引擎理论闭合。

---

## 六、文献依据（3 轮核验 · 含 DOI）

> 核验方式：检索初筛 → 原文/权威源核对题名、卷期页 → 二次复核 DOI 可解析。书目类无 DOI 者按规范标注。

| 主题 | 文献 | 类型 | DOI / 来源 |
|---|---|---|---|
| 词汇覆盖→可读性（阈值） | Hu, M. & Nation, P. (2000). Unknown vocabulary density and reading comprehension. *Reading in a Foreign Language*, 13(1), 403–430. | 期刊论文 | https://doi.org/10.64152/10125/66973 |
| 覆盖阈值复现 | Kremmel, B., Indrarathne, B., Kormos, J. & Suzuki, S. (2023). Replicating Hu and Nation (2000). *Language Learning*, 73(4). | 期刊论文 | https://doi.org/10.1111/lang.12622 |
| 词法阈值再探 | Laufer, B. & Ravenhorst-Kalovski, G. C. (2010). Lexical threshold revisited. *Reading in a Foreign Language*, 22(1), 15–30. | 期刊论文 | https://doi.org/10.64152/10125/66648 |
| 任务负荷假说（ILH） | Laufer, B. & Hulstijn, J. (2001). Incidental vocabulary acquisition… involvement load. *Applied Linguistics*, 22(1), 1–26. | 期刊论文 | https://doi.org/10.1093/applin/22.1.1 |
| ILH 实证 | Hulstijn, J. & Laufer, B. (2001). Some empirical evidence for the involvement load hypothesis. *Language Learning*, 51(3), 539–558. | 期刊论文 | https://doi.org/10.1111/0023-8333.00164 |
| 四股绳 | Nation, I. S. P. (2007). The four strands. *Innovation in Language Learning and Teaching*, 1(1), 2–13. | 期刊论文 | https://doi.org/10.2167/illt039.0 |
| 频率效应 | Ellis, N. C. (2002). Frequency effects in language processing. *Studies in Second Language Acquisition*, 24(2), 143–188. | 期刊论文 | https://doi.org/10.1017/S0272263102002024 |
| 学术词表 AWL | Coxhead, A. (2000). A new academic word list. *TESOL Quarterly*, 34(2), 213–238. | 期刊论文 | https://doi.org/10.2307/3587951 |
| 加工深度 | Craik, F. I. M. & Lockhart, R. S. (1972). Levels of processing. *Journal of Verbal Learning and Verbal Behavior*, 11(6), 671–684. | 期刊论文 | https://doi.org/10.1016/S0022-5371(72)80001-X |
| 测试效应/检索练习 | Roediger, H. L. & Karpicke, J. D. (2006). Test-enhanced learning. *Psychological Science*, 17(3), 249–255. | 期刊论文 | https://doi.org/10.1111/j.1467-9280.2006.01693.x |
| 重复对词汇知识的作用 | Webb, S. (2007). The effects of repetition on vocabulary knowledge. *Applied Linguistics*, 28(1), 46–65. | 期刊论文 | https://doi.org/10.1093/applin/aml048 |
| 练习测试元分析 | Adesope, O. O., Trevisan, D. A. & Sundararajan, N. (2017). Rethinking the use of tests. *Review of Educational Research*, 87(3). | 期刊论文 | https://doi.org/10.3102/0034654316689306 |

**书目类（无 DOI，按规范标注）**：

| 文献 | 类型 | 来源 |
|---|---|---|
| Krashen, S. D. (1985). *The Input Hypothesis: Issues and Implications*. London: Longman. | 学术专著 | 无 DOI（专著） |
| Biber, D. (1988). *Variation across Speech and Writing*. Cambridge: CUP. | 学术专著 | 无 DOI（专著） |
| Nation, I. S. P. (2001). *Learning Vocabulary in Another Language*. Cambridge: CUP. | 学术专著 | 无 DOI（专著） |
| Read, J. (2000). *Assessing Vocabulary*. Cambridge: CUP. | 学术专著 | 无 DOI（专著） |
| Wray, A. (2002). *Formulaic Language and the Lexicon*. Cambridge: CUP. | 学术专著 | 无 DOI（专著） |
| Qian, D. D. (1999). Assessing the roles of depth and breadth of vocabulary knowledge in reading comprehension. *Canadian Modern Language Review*, 56(2), 282–308. | 期刊论文 | 未在本轮核验，**DOI 待补** |
| Schmitt, N. (2014). Size and depth of vocabulary knowledge. *Language Learning*, 64(4), 913–951. | 期刊论文 | 未在本轮核验，**DOI 待补** |

> 说明：上表期刊项均经本轮核验；两个标「DOI 待补」项为评估中引用但**尚未核验**，落地材料引用前应先补核，勿直接用。
