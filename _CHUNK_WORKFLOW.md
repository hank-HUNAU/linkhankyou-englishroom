# 语块（Formulaic Chunks）· 工作流与规约

> 本文是 TH!NK 课程「语块」数据产出的**权威规约**。跑语块链路前先读本文。
> 配套：`_ALIGNMENT_WORKFLOW.md`（句级对齐）、`_VOCAB_WORKFLOW.md`（词汇四链）、
> `_RELEASE_WORKFLOW.md`（落库与上线）。2026-10-28 首版（p048 试点）。

## 1. 定位与教学口径

- 语块 = formulaic sequences（整体存储、整体提取的多词单位）。
- **口径（按证据边界定死，不得放宽）**：
  1. **透明语块 + 功能句型优先，习语降权**——低水平二语者对 figurative 义加工困难
     （Conklin & Schmitt 2012，DOI 10.1017/S0267190512000074）；
  2. **每篇 3–6 条，宁少勿多**——显性教学 + 高复现才有效，堆量无效（同上；Miller 1956
     DOI 10.1037/h0043158 组块容量约束）；
  3. **接受性定位**：「听得懂 + 认得出 + 跟读得上」三件套；产出性测试弱化
     （Martinez & Schmitt 2012 自称 PHRASE List receptive 优先）；
  4. **频率优先排序**：L2 语块加工主要受 phrasal frequency 驱动（Ellis, Simpson-Vlach &
     Maynard 2008，DOI 10.1002/j.1545-7249.2008.tb00137.x）→ 复现设计（连读/七轮间隔）
     是语块学习的主引擎。
- **诚实声明（须随产出留痕）**：现有实证多为成人/学术 EAP 场景，向少儿 A1–A2 外推须谨慎；
  处理优势的元分析（Yi & Zhong 2024，DOI 10.1017/S0272263123000542，作者非英美，作补充证据）
  效应量为小到中等，不是「包治」。

## 2. 文献依据（三轮审核通过，DOI 均经 Crossref 复核，2026-10-28）

| 文献 | DOI | 用途 |
|---|---|---|
| Conklin & Schmitt 2008, *Applied Linguistics* 29(1):72–89 | 10.1093/applin/amm022 | 加工优势实证（母语+非母语，字面/习语均成立） |
| Simpson-Vlach & Ellis 2010 (AFL), *Applied Linguistics* 31(4):487–512 | 10.1093/applin/amp058 | 提取方法论：频率×分布×教学效用 + 语用功能分类 |
| Ellis, Simpson-Vlach & Maynard 2008, *TESOL Quarterly* 42(3):375–396 | 10.1002/j.1545-7249.2008.tb00137.x | L2 排序以 frequency 为主、MI 作质量过滤 |
| Conklin & Schmitt 2012, *ARAL* 32:45–61 | 10.1017/S0267190512000074 | 边界：低水平逐词加工；习语更难 |
| Wray & Perkins 2000, *Language & Communication* 20(1):1–28 | 10.1016/S0271-5309(99)00015-4 | 整存/分析加工选择模型（理论框架） |
| Martinez & Schmitt 2012 (PHRASE List), *Applied Linguistics* 33(3):299–320 | 10.1093/applin/ams010 | 现成词典匹配源；receptive 定位 |
| Ellis 1996, *SSLA* 18(1):91–126 | 10.1017/S0272263100014698 | chunking 在 SLA 的机制地位 |
| Miller 1956, *Psychological Review* 63(2):81–97 | 10.1037/h0043158 | 组块概念认知基础 |
| Yi & Zhong 2024, *SSLA* 46(2):427–452（**作者非英美，补充证据**） | 10.1017/S0272263123000542 | 元分析：优势确认，小-中等效应；任务显性度调节 |

> 教训留痕：Wray & Perkins 的 DOI 极易误写为 (00)00015-7（实为 (99)00015-4）；
> Conklin & Schmitt 2008 极易误写为 amn022→实为 amm022。**引用一律以 Crossref 复核为准。**

## 3. 数据链（与词汇四链同构）

| 链 | 正典源 | 生成物 | 工具 | 入库 git？ |
|---|---|---|---|---|
| 语块候选 | 48 篇归档句级数据（语料 9.3k 词） | 候选 JSON `_chunk_cand_pXXX.json` | `_chunk_extract.py` | 不入库（工作件） |
| 语块正典 | **人工审校定稿** | `Ux_*/02_词汇数据/语块_pXXX.json` | 本规约 §4 schema | 入库 |
| 站点呈现 | 语块正典 | 篇章页第三 tab「语块」（内嵌 CHUNKS） | 手工接线（试点）；批量阶段再考虑生成器 | 入库 |
| 校验 | 正典 + 页面 | 三道校验报告 | `_chunk_verify.py`；浏览器验收 `_chunk_smoke.js` | 入库 |

### 两车道提取（_chunk_extract.py）

- **车道A（语料统计）**：n-gram(2–6) 不跨句；`freq≥2 且 disp≥2`（语料只有 9.3k 词，
  阈值比 AFL 的百万词级下沉是**有意的**，规约即此）；MI 只作排序与质量参考。
  悬垂过滤：非白名单语块不得以 BAD_START 词开头 / BAD_END 词收尾。
- **车道B（功能白名单）**：A1–A2 功能句型整串匹配（`fullmatch`），**不受频率门槛限制**——
  `come and see` 这类单次出现的课堂高频句靠它收录。白名单在脚本 `WHITELIST`，扩条目改那里。
- **人工审校是第三车道，也是定稿的唯一入口**：脚本不代选、不写归档。

## 4. 归档 schema（语块_pXXX.json）

```json
{
 "page": "p048", "key": "u5_p048_robotics_club", "unit": 5,
 "n_chunks": 6,
 "standard": "A1-A2 透明语块优先、每篇 3-6 条、逐条 verbatim 命中源句；习语降权",
 "evidence": ["…5 条 DOI 引用…"],
 "corpus": {"passages": 48, "tokens": 9336},
 "chunks": [{
   "id": "c1", "text": "there is", "zh": "有（存在句框架：…）",
   "type": "句型框架", "func": "描述存在", "sent": 12,
   "ex": "原句英文（取自句级数据）", "exZh": "原句中文（取自译文_pXXX.json，保持一致）",
   "freq": 15, "disp": 10, "mi": 3.45, "lane": "A+whitelist", "note": "…"
 }]
}
```

- `sent` 为 **1 基**（页面里转 0 基下标）；`type ∈ {句型框架, 固定搭配, 时间短语, 功能句}`。
- `ex/exZh` 直接取自归档句级数据与译文，**不得另写**（一致性）。

## 5. 三道校验（_chunk_verify.py，硬规约）

1. **verbatim 命中**：每条 `text` 必须在标注句子里按归一化子串出现——防臆造语块；
2. **释义完整**：`zh` 必须含中文；允许内嵌英文框架（如 “There is / There are …”）但中文须占主体；
3. **双写一致**：篇章页内嵌 `CHUNKS` 必须与归档正典逐条一致（文本/句号/中文）——
   同 timeline 双写硬规约，**改归档必须同步页面，反之亦然**。

浏览器验收：`_chunk_smoke.js`（先 `python -m http.server 8901`）——tab 渲染条数、
点「听这句」落在正确时间区间、遮中文开关、无 JS 报错。

## 6. 已知坑（试点实测）

1. **功能车道曾用 `search` 匹配** → 任意含白名单词的长串全被收（如 “in the school hall every
   monday…”）——必须 `fullmatch` 整串匹配；
2. **去重优先级**：白名单/功能 > 长 > MI 高，重叠只留一条——否则 “there is a” 被短串压掉；
3. **元数据未就绪时 seek 丢失**：`audio.currentTime=st` 在 `readyState<1` 时会被忽略，
   播放从 0 开始——必须 `loadedmetadata` 后再 seek（`seekPlayChunk`）；
4. 语料小 → 全站 freq=1 的好语块不少（after school 等），**不要硬凑**，如实标 freq/disp，
   靠车道B与人工审校兜底；
5. `favicon.ico` 404 是站点既有现象（根目录无 favicon），验收脚本须过滤，勿误判为本次回归。

## 7. 验收清单（新篇接线时）

- [ ] `_chunk_extract.py --page pXXX --json _chunk_cand_pXXX.json` 出候选
- [ ] 人工审选定稿 3–6 条 → `02_词汇数据/语块_pXXX.json`（schema 见 §4）
- [ ] 篇章页：tab 按钮 + `#viewChunk` 区块 + CSS + 内嵌 CHUNKS + setFlow 接线
- [ ] `python _chunk_verify.py --page pXXX` → 三道校验全过
- [ ] `node _check.js 篇章页/读写_XXX_*.html` → 语法全过
- [ ] `node _chunk_smoke.js 篇章页文件名` → 真浏览器验收通过（先起 8901 服务）
- [ ] `python content_pipeline.py --unit N --page pXXX` → 四段全 OK·跳
