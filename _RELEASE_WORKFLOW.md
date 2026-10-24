# 落库与上线 · 工作流与规约

> 本文是 TH!NK 课程数据「落库 → 上线」的**权威规约**：三条硬规约、落库流程、发布检查单、版本基线、回滚。
> 配套：`_ALIGNMENT_WORKFLOW.md`（篇章对齐）、`_VOCAB_WORKFLOW.md`（词汇四链）。

## 1. 三条硬规约（不可违反）

1. **句级重对齐双写**——产出必须同时落两处且内容一致：
   - 运行时单一数据源：仓库 `assets/timeline.json`（改后跑 `node _sync_timeline.js` 同步 index.html 内联块 + `node _timeline_check.js` 门禁）；
   - 归档正典：`Think F 教材资产/Ux_主题/01_正文篇章/句级数据_pXXX.json`（schema：`{unit, passage_key, page, title, type, n_sent, duration_s, source, sentences:[{i,start_s,end_s,text}]}`；注意 unit/page 是字符串字段）。
2. **音频只增不改**——新增音频以 md5 记录；同一文件 md5 一致才允许推送，**禁止覆盖已推送音频**（学生端可能已缓存/引用）。
3. **网站页面严禁引用仓库外路径**——所有运行时依赖（音频/数据/词音频）必须在仓库 `assets/` 内；库外素材（`003 第三版课程材料/`、`Student's Book Video 原版/` 等）只作生产输入，不进页面引用。

## 2. 落库流程（每批数据）

```
生产（_align_unit.py / _align_u14.py / _gen_*.py / _patch_*.js）
  → 校验（npm test 或该批三重校验：句数对账/区间/质量）
  → 双写归档（timeline + 句级数据_pXXX.json）
  → 音频入库 assets/<page>.mp3（记 md5）
  → commit（小批量入库，message 带期号/轨号/句数）
  → python _gen_assets.py（课程资产三件套同步）
```

- **小批量入库**：一批一 commit，勿攒大提交；message 格式 `feat/fix/docs(范围): 摘要——关键数字`。
- **提交前看一眼 `git status`**：确认没有误扫 gitignore 项（尤其 `*.xlsx`、`词汇诊断/`、`think.db`）；用户有意留在库外的文件（如会议纪要）不要 `git add -A` 扫入。

## 3. 上线流程（发布检查单）

1. **门禁全绿**：`npm test`（或该批对应校验）通过——以退出码 + 关键断言双校验判定，不要只看日志；
2. **推送**：`git push origin main`——本机到 github.com 连接不稳定时重试 2–3 次；只读核验优先 `gh api`（api.github.com 一直可用）；
3. **sha 对齐确认**：`gh api repos/hank-HUNAU/<repo>/commits/main --jq .sha` 与本地 `git rev-parse HEAD` 一致（API 路径推送例外，见 §5）；
4. **Pages 构建**：GitHub Pages built（重大结构变更后抽查线上页面字节数）；
5. **CDN 验证**（改了已上线页面时）：Pages CDN `max-age=600`，`?v=` 不一定绕缓存——**用 `?cb=N` 并核对字节数 + `X-Cache: MISS`** 再下结论；
6. **记基线**：按 §4 格式写入记忆。

## 4. 版本基线记录格式

每次上线后在 `.workbuddy/memory/MEMORY.md`「线上版本基线」节登记：

```
- <日期> 快照：TH!NK 远端 main <sha10>（内容摘要；前值 <sha10>），Pages built；NCE2 echoloop 远端 <sha10>（…），Pages built。
```

查询：`gh api repos/hank-HUNAU/<repo>/commits/main --jq .sha`。

## 5. 推送兜底与已知坑

- **直连优先**：2026-10-23 实测 `git push` 直连可用（think1-echoloop 首推即走直连，sha 无规范化问题）；
- **API 兜底**：代理拦截 github.com TLS 时用 `node _push_one.js`（Git Data API）。注意：
  - API 将提交日期规范化为 UTC → **远端 commit sha 与本地不同（内容一致）**；对齐用 `git fetch origin && git reset --hard origin/main`；
  - **空仓用 API 建 blob 会 409（Git Repository is empty）**——首次提交必须用直连 git push 播种；
- **回滚**：API PATCH refs/heads/main 到目标 sha——
  `gh api -X PATCH repos/hank-HUNAU/<repo>/git/refs/heads/main -f sha=<目标sha> -f force=false`；
- **本地/远端分叉**：长期「同内容不同 sha」时，`git fetch origin && git rebase origin/main` 后推送，可真正对齐历史（2026-10-24 TH!NK 仓库已如此理顺）。

## 6. 各仓库远端

| 仓库 | 远端 | 用途 |
|---|---|---|
| `linkhankyou-englishroom` | hank-HUNAU/linkhankyou-englishroom | TH!NK 主站（Pages） |
| `nce2-echoloop` | hank-HUNAU/nce2-echoloop | 新概念2 听读站（Pages） |
| `think1-echoloop` | hank-HUNAU/think1-echoloop | THiNK 1 听读站数据底座（Pages） |

## 7. 当前状态（2026-10-24）

- TH!NK 远端 main `0e1bece`：U1–U4 定型（每单元恰 4 篇）+ timeline 49 键 / 1153 句 + assets 49 mp3；
- 规约三件套齐备：`_ALIGNMENT_WORKFLOW.md`（篇章）+ `_VOCAB_WORKFLOW.md`（词汇）+ 本文（落库上线）；
- U1–U4 站点激活（UNITS live + 篇章页生成）待用户指令，激活后须按本文 §3 走发布检查单。
