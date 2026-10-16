---
name: "british-phonetics"
description: "英式语音语调·软分支技能。把 article-vocab-analyzer 的分析结果（分层+词性+CEFR+原句）逐词联网补英式音标(UK IPA)+英式真人发音音频，并把原句做成朗读标注（意群切分/停连/降升调/弱读提示），输出 Excel 三页签供教师课堂讲授与学生跟读双用。当用户要'英式发音、语音语调、朗读标注、英音音标、英男/英女发音、跟读材料、弱读'时触发。"
---

# 英式语音语调（British Phonetics）

复用 **article-vocab-analyzer 主技能**的静态结果（分层+词性+CEFR+原句），逐词联网补**英式音标（UK IPA）+ 英式真人发音音频**，并把原句做成**朗读标注**，产出一份师生可用的**发音 / 跟读**材料。

**定位**：与 student-vocab-cards 分工——学生卡偏"词义记忆"，本分支只取**发音维度**。发音默认英式发音。

## 输出（Excel 三页签）

| 页签 | 内容 | 用途 |
|---|---|---|
| 原句朗读标注 | 按意群切分原句，标注停连 ⊣ / 降调 ∨ / 升调 ∧ | 教师领读、学生跟读节奏 |
| 单词英式音标 | 词/教学梯度/词性/UK音标/重音位置/弱读提示/英式真人发音(url或mp3)/音源/原句 | 逐词正音、听音跟读 |
| 语音讲授要点 | 弱读规则、重音规律、升降调、停连示范 + 本课弱读词表 | 课堂讲授提纲 |

## 用法

```bash
python scripts/phonetics.py --file 课文.txt --out 英式语音卡
python scripts/phonetics.py --text "..." --out 语音
python scripts/phonetics.py --file 课文.txt --limit 20        # 只对前20词联网取音(防限流/快速)
python scripts/phonetics.py --file 课文.txt --offline         # 断网: 只出静态朗读标注, 不取音标
python scripts/phonetics.py --file 课文.txt --voice gb-male   # 英男真人发音(edge_tts, 生成本地mp3)
python scripts/phonetics.py --file 课文.txt --voice gb-female # 英女真人发音(edge_tts, 生成本地mp3)
python scripts/phonetics.py --file 课文.txt --no-cambridge  # 关闭剑桥主源, 只用有道
python scripts/phonetics.py --file 课文.txt --no-tts         # 禁用TTS兜底(词典下载不到即留空, 非交互/管道)
```

> **推荐**：经主技能一键管道调用——`python scripts/vocab_pipeline.py 课文.txt`（默认含语音卡；`--steps 主,语音` 只出这步；`--voice gb-male/gb-female` 出性别真人发音）。

`--voice` 取值：
- `youdao`（默认）→ **下载剑桥真人发音到本地 mp3**；剑桥下载不到自动兜底有道下载；两源都无则提示并**经确认才用 edge_tts 生成**
- `gb-male` → 英式**男声**（edge_tts en-GB-RyanNeural / ThomasNeural），直接生成本地 mp3
- `gb-female` → 英式**女声**（edge_tts en-GB-LibbyNeural / SoniaNeural），直接生成本地 mp3

## 发音与音标来源

- **英式音标（UK IPA，首选）**：剑桥词典抓取 API（dictionary-api.eliaschen.dev，Cambridge en-cn 分音节式 RP 音标）+ 官方真人音频 URL；**缺词条/404 时自动回退有道** `ukphone`。`--no-cambridge` 关闭剑桥、只用有道。
- **专名补音（A+B）**：人名等词典不收的专名，采用两级方案——
  1) **内置常用名读音库** `scripts/names_ipa.json`：随技能附带约 180 个常用英美名/姓的英式 IPA，开箱覆盖常见名；
  2) **人工核注表** `NAMED_IPA`（脚本顶部）：本课文特有专名在此核注一行即自动标音（取音以主流词典姓名条目为准，如 Maureen=mɔːˈriːn）。
  3) **库自学习回写**：凡新解析出音标但库中缺的专名（含教师核注的新专名），运行结束自动回写进 `names_ipa.json`，下次开箱即命中，库随使用持续增补。
  运行结束若仍有专名**未能补出音标**，会打印「待核注专名清单（原文+频次）」到控制台，教师按提示核注进 `NAMED_IPA` 后重跑即全绿。
- **英式真人发音（默认下载）**：**首选剑桥真人音频并下载为本地 mp3**；剑桥下载不到自动回退有道 `dict.youdao.com/dictvoice?audio=<词>&type=1`（type=1=英式）下载；两源均为真人录音、**均不区分男女声**。若两源都取不到音频，默认**提示并须确认**才走 edge_tts（TTS 仅作备用）。页2「音源」列区分 本地mp3(真人·下载) / 剑桥真人(URL) / 有道英音(URL)。
- **英男/英女性别可控发音**：微软 `edge_tts` 神经语音（en-GB 声线），`--voice gb-male/gb-female` 时逐词生成本地 `mp3`（真实自然语音，可指定性别）。需在线访问微软语音服务。

## 学理 / 规则口径

- **重音位置**：从英式音标提取 `ˈ`（主重音）`ˌ`（次重音）标记，提示重读节。
- **弱读表（静态常量）**：常见虚词（a/the/of/to/and/can 等）的弱读形式，朗读教学起点。
- **语调（启发式）**：句号→降调∨、是非问号→升调∧、逗号/连词→停连⊣。仅为朗读起点，实读须结合语境由教师把握。

## 边界

1. **联网依赖**：音标与发音音频需在线（剑桥/有道/微软），断网用 `--offline` 只出静态朗读标注。
2. **限流**：全量逐词联网可能触发限流，建议 `--limit` 分批处理。
3. **默认全部本地 mp3**：默认即把**每个词的剑桥/有道真人发音下载为本地 mp3**，生成 `→<out>_tts/` 目录，需随 xlsx 一起转移；`--voice gb-*` 同为本地 mp3。断网/离线无下载。若下载不到且非交互（如管道），音源列留空——需 TTS 时用 `--voice gb-*` 显式指定。
4. **启发式不等于答案**：语调/停连/重音为自动化建议，是讲授起点，请结合教材原声音频与真人示范复核。
5. 弱读表为常见功能词，个别词因语境强读需教师取舍。