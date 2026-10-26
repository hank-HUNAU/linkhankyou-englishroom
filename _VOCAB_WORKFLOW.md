# 词汇数据处理 · 工作流与规约

> 本文是 TH!NK 课程「词汇」数据产出的**权威规约**。跑词汇链路前先读本文。
> 配套：`_ALIGNMENT_WORKFLOW.md`（篇章句级对齐）、`_RELEASE_WORKFLOW.md`（落库与上线）。
> 词汇分四链，各有正典源与生成物；**任一侧资产变更后重跑 `_gen_assets.py` 同步课程资产三件套**。

## 1. 四链总览

| 链 | 正典源（canonical） | 生成物 | 工具 | 入库 git？ |
|---|---|---|---|---|
| ① 篇章词表 | 归档 `Ux_主题/02_词汇数据/uN_pXXX_<key>.json` | 词汇分析报告 + 诊断页词源 | `article-vocab-analyzer`（`vocab_pipeline.py` 编排） | 词表 JSON 入库 |
| ② 主题词表 | 归档 `Ux_主题/03_主题词汇/theme_uN.json`（U5–U12）+ `00_主题词汇/theme_uN.json`（U1–U4） | `index.html` 的 `THEME`/`THEME_TITLE` 内联 + theme 诊断页 | `_gen_theme.py` | theme JSON 入库 |
| ③ 词音频 | 归档 `00_词汇音频/<word>.mp3` + `audio_index.json` | 仓库 `assets/word_audio/` | `_gen_vocab_audio.py` | mp3 入库（只增不改） |
| ④ 词汇诊断页 | 模板 `词汇诊断/_模板_词汇诊断页.html` | `词汇诊断/词汇诊断_<key>.html` / `词汇诊断_theme_uN.html` | `_gen_vqdis.py` / `_gen_theme.py` | **不入库**（gitignore，版权）；归档 `00_主题词汇/` 保留 theme 页副本 |

数据流：课文文本 → ① 篇章词表（九层分析）→ ④ 诊断页；Wordlist.xlsx + 课文 → ② 主题词表 → ④ theme 页；② + ① 的 word 类 lemma → ③ 词音频。

## 2. 分链规约

### 2.1 篇章词表（analyzer 链）

- **交付口径 = 5 件套/篇**（与 U9–U12 同构）：`<key>.json`（九层分析）+ `<key>.xlsx`（分析报告）+ `<key>_学生卡.xlsx` + `<key>_备课本.xlsx` + `<key>_语音卡.xlsx`，全部落 `Ux_主题/02_词汇数据/`。
- **一键全链（唯一正确入口）**：
  ```bash
  # 单篇
  python skills/词汇教学技能包-20260928/article-vocab-analyzer/scripts/vocab_pipeline.py <课文.txt> --out <key>
  # 批量（U1–U4 用）
  python _vocab_pipeline_u14.py      # 产物落 _vocab_out_tmp/（gitignore），5 件套自动归档
  ```
  五步：主（assess_vocab 九层）+ 学生卡 + 备课 + 语音（british-phonetics）+ 整合。
- **只跑 `assess_vocab.py` 是不够的**（2026-10-26 教训）：U1–U4 首版只跑了主分析，缺学生卡/备课本/语音卡，等于没走技能全链。
- **九层标注**：`A1_Starters → A1_Movers → A2_Flyers → KET → PET → FCE → CAE → NGSL → NAWL`。
- **schema**：`{source, total, numbers, proper, tokens:[{kind, form, lemma, hit}]}`；`kind ∈ {word, proper}`，`hit` 为出现句序号。
- **CEFR 取值顺序**（硬规约，跨项目生效）：Oxford → CEFR-J v1.6 → Octanove C1/C2 → EFLLex（峰值）；主标注遇 Oxford 即定；冲突只在 {Oxford, CEFR-J, Octanove} 间判定，**冲突保留双标注 + 列出，禁止静默覆盖**；EFLLex 属频率分布构念，只补缺不参与冲突。
- **坑**：
  1. `lemma` 归一默认**关闭**，须 `--strict-lemma` 才生效（会改 lemma → 覆盖率/词库主键变，历史项目需重跑）；
  2. 不规则词保留原形（children/feet 不折算为 child/foot）；
  3. analyzer 对过去式动词有 lemma 缺陷（如 `added→ad`），**每次运行后必须人工复核**；
  4. 第三方词表源数据不打包进技能，只发下载脚本 `scripts/fetch_cefr_sources.py` → 落 `wordlists/cefr_sources/`；Cambridge PDF 受版权，脚本不代下载，只做本地核验；
  5. Cambridge 官方直链会 301 改版（YLE 2018 单册曾跳到绘本而非词表）——下载后必须「页数 + 唯一词形 + 交叉覆盖率」三重校验。

### 2.2 主题词表

- **源**：`Think Starter Wordlist.xlsx`（636 词 × WORD/UNIT/PAGE/DEF/POS/IPA/EXAMPLE）+ 课文补充词。
- **schema**：`[{w, ipa, pos, zh, en, ex}]`（中文释义 `zh`、英英 `en`、例句 `ex`）。
- **工具**：`python _gen_theme.py [--offline]`；中文释义走 `_dict_cache.json` 命中即用，缺失联网查（有道）并写回缓存——**断网用 `--offline`**。
- **例外**：U7 / U12 保留现有手输版，`_gen_theme.py` 不回写这两单元。
- **落站**：生成结果回写 `index.html` 的 `THEME` / `THEME_TITLE`，**勿手抄**（手抄必漂移）。

### 2.3 词音频

- **工具**：`python _gen_vocab_audio.py [--upgrade-youdao]`；三级音源 = 剑桥真人（主）→ 有道英音（兜底）→ edge_tts（最终兜底）。
- **实测结论（2026-10-26，重要）**：**剑桥媒体 URL 有防盗链，带浏览器头也 403**，程序抓不到；脚本内置熔断（首次 403 后本轮直接走有道）。
  → **真人音频实际来源 = 有道英女（`youdao-uk`）**；**剑桥稳定提供的是音标**（`dictionary-api.eliaschen.dev`，语音卡里 `ˈɔː.səm` 这种带音节点的写法即剑桥风格）。
  → `audio_index.json` 的 `src` 如实标注 `cambridge` / `youdao-uk` / `edge_tts`，不得谎报。
- **词源** = 全部单元 `theme_uN.json` + 篇章词汇产出的 `tokens`（`kind=word` 的 lemma）。
- **落盘**：正典 `Think F 教材资产/00_词汇音频/<word>.mp3` + 索引 `audio_index.json`（归档内存一份）。
- **硬规约**：音频**只增不改**（md5 一致才推送，见 `_RELEASE_WORKFLOW.md` §1）；`--upgrade-youdao` 属有意的音源升级，须在日志注明。

### 2.4 词汇诊断页

- **模板**：`词汇诊断/_模板_词汇诊断页.html`（RAW / PASSAGE / CATS 占位）。**只能改模板再批量重生成，逐页手改必然漂移**（11 个篇章页 + theme 页是同模板的参数化副本）。
- **生成**：`python _gen_vqdis.py <key...>`（分析 JSON + 有道词典音标/义项 + 反推模板 → 单页 HTML）。
- **存储键坑（2026-10-21 修，重要）**：诊断页 localStorage 键取页内 `PASSAGE.key`——篇章页是带 slug 的 `u5_p048_robotics_club_records_v2`，而主站 PASSAGES 数据键是 `u5_48`，长期失配致篇章词汇进度从不显示；`index.html` 已用 `vocabStoreCandidates()` 按 FOLLOW_VOCAB 文件名反解引擎键（新旧候选都试）。主题页键 `theme_uN` 本就一致。
- **新克隆注意**：`词汇诊断/` 被 gitignore 排除（版权），克隆后点「单元主题词汇」或「篇章词汇」会 404，需按本规约重新生成。

## 3. 引擎规则（改动前须先解锁）

- **干扰项确定性优选**：`pickDistractors(w, field, n)`（模板内，同层同词性、人工审校优先）——保证选项集合对所有学生一致，难度与区分度才可比。人工审校走 `干扰项审校工作表.csv` → `_patch_vqdis.js` 写回词表 `dis` 字段。
- **归属仲裁**：词汇分层取**最低层、只归一层**（KET < PET < NGSL < NAWL），各层覆盖率相加闭环（`assess_vocab.py` 九层分析 + `cefr.json`）。
- **不规则词**：保留原形，不折算 lemma。

## 4. 验收

| 项 | 命令 / 方式 |
|---|---|
| 全站回归 | `npm test`（退出码 + 关键断言双校验，不要只看日志） |
| 核心门禁 | `npm run test:core`（纯 Node 套件，不需要 Python） |
| 页面语法 | `node _check.js`（HTML 内联脚本 + JS 语法） |
| 模板重生成后 | 抽样 2–3 页核对词条数/层级分布与源 JSON 一致 |
| 课程资产同步 | `python _gen_assets.py`（三件套：`课程资源.{csv,md,html}`） |

## 5. 坑清单（跨链通用）

1. **诊断页只能模板化重生**——手改单页 = 制造漂移；
2. **存储键 slug 失配**——已修（`vocabStoreCandidates()`），新页面务必用同一反解；
3. **lemma 归一与过去式缺陷**——运行后人工复核；
4. **Cambridge 源会 301 改版**——下载后三重校验（页数/唯一词形/交叉覆盖率）；
5. **联网依赖**——`_gen_theme.py` / `_gen_vqdis.py` 的有道查询走 `_dict_cache.json` 缓存，断网场景用 `--offline` 或接受缺释义；
6. **双位置**——theme 诊断页在归档 `00_主题词汇/` 有副本、仓库 `词汇诊断/` 是 gitignore 工作区，改模板后两处都要重生。

## 6. 技能包环境（跑之前必看，2026-10-26 补齐）

- **仓库内 `skills/词汇教学技能包-20260928/` 曾长期是旧副本**：缺 `A1_Starters/A1_Movers/A2_Flyers/CAE/FCE/lemma_supplement` 六个词表 + `cefr_layers.py`/`entity_classify.py`/`entity_lexicon.json` 三个依赖脚本 → 只能出 KET/PET/NGSL，A1 三层全丢。已从用户级技能 `C:\Users\Thinkpad\.workbuddy\skills\article-vocab-analyzer\` 同步补齐，**两处现已一致**。
- **三个子分支的 `_main_dir()` 已兼容两种布局**（`<root>/skills/article-vocab-analyzer` 与包内 `<root>/article-vocab-analyzer`），此前包内布局解析失败会静默落到 CWD 相对路径 → 报 `article-vocab-analyzer/scripts/assess_vocab.py` 找不到。
- **`--out` 只能是裸词干，不能带路径**（`student_cards.py` 会拼 `__sb_` 前缀，带盘符会非法）。
- **批量请用 `_vocab_pipeline_u14.py`**：产物统一落 `_vocab_out_tmp/`（gitignore），最后一次性删目录——**不要逐文件删临时产物**，单轮 ≥50 个删除会触发环境批量删除保护（`SAFE_DELETE_BULK_CONFIRM_REQUIRED`）而中断。

## 7. 当前状态（2026-10-26）

- **九层分析必须用用户级技能**：`C:\Users\Thinkpad\.workbuddy\skills\article-vocab-analyzer\`（完整版，含 A1_Starters/Movers/Flyers 三层）。仓库内 `skills/词汇教学技能包-20260928/` 已于 2026-10-26 同步补齐（见 §6），两处一致。
- 篇章词表：**U1–U12 全部 48 篇**已分析入库；**U1–U4 十六篇已补齐 5 件套**（分析 json/xlsx + 学生卡 + 备课本 + 语音卡，走 `vocab_pipeline.py` 全链）。
- **诊断页音标 = 剑桥分音节记法**（有语音卡时优先，`_gen_vqdis.card_ipa()`）；与语音卡逐词比对 425/425 一致。
- 词音频：`00_词汇音频/` 1210 mp3 + `audio_index.json`（src 如实标注；真人音频实为有道英女，剑桥媒体 403）。
- 诊断页：48 篇章页 + 12 theme 页，全部在库并 git 跟踪。
- 站点接线：`FOLLOW_VOCAB` / `FOLLOW_META` 各 49 篇；`LIVE_VOCAB_RE` 覆盖 U1–U12；全 12 单元 live。
