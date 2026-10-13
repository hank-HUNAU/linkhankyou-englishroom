# AGENTS.md

TH!NK 学习平板原型：课文点读 / 跟读支架化 / 预习复习任务 / 教师学情与题库分析。
后端零 npm 依赖——只用 Node 内建 `http` + `node:sqlite`，复制目录即可运行。

## 环境要求

| 项 | 版本 | 说明 |
|---|---|---|
| Node.js | ≥ 22.5 | `node:sqlite` 的 `DatabaseSync` 自 22.5 起提供，低于此版本启动即失败 |
| Python 3 + Playwright | 可选 | 仅 6 个 `_smoke_*.py` 端到端脚本需要；未安装时用 `npm run test:core` |
| 浏览器 | Chromium / Edge / Safari | 前端是原生 HTML/CSS/JS，无构建步骤 |

## 常用命令

```bash
npm start            # node server.js  → http://localhost:8000
npm run start:http   # 强制 HTTP（已有证书但想走 HTTP 时）
npm run cert         # 生成自签证书到 certs/，重启后自动启用 HTTPS
npm test             # 全量回归：_regress.js 串跑 10 个套件
npm run test:core    # 核心门禁：仅纯 Node 套件，不需要 Python
npm run test:list    # 列出全部套件
```

启动后控制台会打印本机地址与局域网地址，跨设备同步验证要用后者。

不要直接双击 HTML 文件。`store.js` 与 `login.html` 在 `file://` 下会拦截并给出启动指引。

## 目录约定

| 路径 | 作用 |
|---|---|
| `server.js` | 唯一后端：静态服务、账号认证、KV 存储、聚合接口、定时备份、安全响应头 |
| `store.js` | 存储垫层，拦截 `localStorage`；登录后水合，写入自动镜像上云。**学生端已不加载它**（见下），仅教师端与词汇诊断页引用 |
| `ui.css` / `ui.js` | 设计令牌与 SVG sprite 图标系统，三个页面共用 |
| `index.html` | **学生首页**：书架 → 单元页（任务区 + 主题词汇入口卡 + 篇章）；主题词汇跳独立词汇页，篇章跟读同页接入点读 / 跟读 / 听写引擎（深链 `?pg=`） |
| `词汇诊断/词汇诊断_*.html` | 词汇诊断页（三步：筛选→学习→测试 + 诊断报告），键 `u7_*` / `u12_*` 为篇章词汇，`theme_u7` / `theme_u12` 为**单元主题词汇**；由模板生成，`gitignore` 排除 |
| `学生端.html` | 已并入 `index.html`，现为兼容旧链接的跳转壳（`学生端.html?unit=N` → `index.html?unit=N`） |
| `教师端.html` | 班级、学生账号、任务下发、学情汇总、题库分析 |
| `login.html` | 登录 / 注册入口 |
| `assets/p*.mp3` | 课文音频，当前版本唯一的运行时音频依赖 |
| `_align_unit.py` + `_unit_N_source.json` | 正课文句级时间轴**唯一生产入口**（`--unit N` 全自动）；规约 `_ALIGNMENT_WORKFLOW.md` |
| `_regress.js` | 回归入口，套件定义在文件顶部的 `SUITE` 数组 |
| `_check.js` / `_align_check.js` / `_check_icons.js` / `_smoke.js` | 纯 Node 校验，无外部依赖 |
| `_smoke_*.py` | Playwright 端到端，需要 Python 3 + Playwright |
| `skills/` | 内容生产技能文件，详见 `skills/README.md`；应用运行时不加载 |
| `MANIFEST.md` | **文件清单**：核心运行时 / 依赖开发 / 内容生产 / 溯源参考 四级归档 + 弃用候选；文件增删后更新 |

## 架构要点

- 实时同步：`GET /api/events` 是 SSE 事件流（零依赖，`db` 变更后广播）。教师改 `tf_assignments` → `event: assignment` 推全体在线学生；学生写 `*_records_v2`/`tf_reports`/`tf_follow_*` → `event: progress` 推在线教师/助教（限流 3s）。心跳 20s，值未变化不推送。客户端 `store.js` 在页面不可见时断开 SSE、可见时重连并补拉，另有 30s 轮询兜底。
- 数据分桶：`kv` 表按 `uid` 隔离，`uid = -1` 是全局数据（教师下发的 `tf_assignments`，所有学生可见），其余为各账号私有学情。
- 令牌：`tf_token` 默认 7 天有效，剩余不足一半时滑动续期；写接口需 `Authorization: Bearer <token>`。
- 角色：`teacher` 可写，`assistant` 只读，写操作按钮自动置灰。
- 词汇引擎：干扰项走确定性优选 `pickDistractors`（同层同词性、人工审校优先），保证选项集合对所有学生一致，难度与区分度才可比。
- 归属仲裁：词汇分层取最低层、只归一层（KET < PET < NGSL < NAWL），各层覆盖率相加闭环。

## 内容生产工具链

应用运行时只消费产出物，不加载任何技能，所以技能全部缺席也不影响启动，只影响内容能否再生产。技能文件已随仓库提供，落在 `skills/` 下，按去向分两份：

| 仓库路径 | 去向 | 内容 |
|---|---|---|
| `skills/project/` | 新工作区的 `.trae/skills/` | `sentence-alignment` |
| `skills/global/` | 新环境的 `.trae-cn/skills/` | `local-mineru`、`article-vocab-analyzer`、`cet-cn2en-scholar`、`british-phonetics`、`student-vocab-cards`、`exam-paper-bank`、`teacher-vocab-prep`、`sentence-alignment`、`chunk-splitter` |

产出对应关系：`article-vocab-analyzer` 分析课文产出词汇报告与 `词汇诊断/`；`sentence-alignment` 对齐音频产出 `assets/timeline.json`；`teacher-vocab-prep` / `student-vocab-cards` / `british-phonetics` 是三个软分支，由 `article-vocab-analyzer/scripts/vocab_pipeline.py` 串联编排。

### 时间轴是单一数据源（重要）

`assets/timeline.json` 是 **16 篇 / 418 句**的唯一权威时间轴（U7 4 篇 + U8 4 篇 + U12 4 篇正课文 + p066/p073/p110/p202），index.html 里那段带 `==TL-DATA-START==` / `==TL-DATA-END==` 标记的 `DB.TL` 是它的投影。`_timeline_check.js` 会逐条比对两者并已进核心门禁，**不要手改 index.html 里的时间轴**，改 `assets/timeline.json` 后同步内联块。

**新增正课文时间轴的唯一入口是 `_align_unit.py --unit N`**（全自动，无人耳终审），权威规约见 `_ALIGNMENT_WORKFLOW.md`：写 `_unit_N_source.json`（正课文清单 + 源文本 + 音频映射）后一键跑完 ASR→对齐→合入→同步→门禁。

历史教训：这份数据曾经有"两代"——`var DB` 字面量里的旧值，加第 772/773 行一整行 12 KB 的运行时覆盖块。实际生效的是覆盖块，所以改字面量完全不生效；更糟的是它和 `assets/timeline.json`（那份"3 遍人工核查 + ASR 复验通过"的产物）逐条都不一致，真实播放值最大偏差 1.02s，导致被核查过的 p067/p070 反而是切音最严重的两篇。已合并为一份。

句级边界体检与重切工具：`py _align_audio.py check|refine|dump|cmp <timeline.json>`（能量法：边界 ±60ms 内峰值能量 / 全篇峰值，<0.25 正常、0.25~0.50 可疑、≥0.50 切音）。重切清单见 `_align_report.md`：300 条句间边界里，切音/可疑/正常 由 36/43/221 改善为 16/24/260，改动 130 句。

> **2026-10-13 起已废止「人工试听定案」**：句级边界改由 `_align_unit.py --unit N` 全自动产出
> （faster-whisper 词级时间戳 × 源文本校准 + 静音吸附），见 `_ALIGNMENT_WORKFLOW.md`。
> 旧的 `_align_audio.py` 能量法体检与 `_bridge_aligner.py` 交叉验证保留作参考，不再作为生产一环。

`text-vocab-coverage` **已退役**，四处副本（`project/`、`global/`、工作区 `.trae/skills/`、用户 `.trae-cn/skills/`）已全部删除，能力由 `article-vocab-analyzer` 承接：`entity_classify.py` 与 `entity_lexicon.json` 已迁入其 `scripts/`（含项目版的 `PER_surname` / `ORG_multi` 增强）；词汇分析改用其 `assess_vocab.py`（超集，新增 `AGENT_ER_NOUNS`、弯引号归一、纯引号 token 过滤），`lemma_candidates` 对 -er 名词的候选集与旧版不同（如 `owner` 不再归并到 `own`），依赖该函数的词汇分级可能微调。删除前四处副本字节一致，内容仍可从 git 历史取回。

工作区根目录（`xueersi-diancan-原型` 的上一级）的 `tools-whisper/` 是内容生产脚本目录，其中两个脚本原引用该技能，解析路径已改为 `article-vocab-analyzer`（工作区 `.trae/skills/` 优先、回落全局 `.trae-cn/skills/`）：`ketpet/build_entities.py`、`ketpet/verify_entities.py`。改后已复跑验证：`verify_entities.py` 准确率 100%，`build_entities.py` 产物与现网 `entity_tables_lesson.json` / `entity_tables_stage.json` 字节一致。

原第三个引用方 `tools-whisper/build_page.py` 是**遗留脚本，已删除**：它仍输出已下线的词级 `WORDS`，产物约 80 KB，远落后于现网 `index.html`（约 176 KB，只有句级 `TL` / `CHUNKS`），重跑会把页面回退。其模板 `index.html.template`（约 55 KB，仓库外未跟踪）已一并删除。

`sentence-alignment` 也已统一到全局版，方向与直觉相反：全局版更晚编辑、已声明「词级点读（WORDS / `.wd`）下线，只保证句级对齐」，与应用现状一致（`index.html` 只有句级 `TL` 与 `CHUNKS`）；项目级旧副本曾含词级归属钳制，现已用全局版覆盖，并把旧副本独有的「端到端总流程」一节回灌进全局版。**不要用旧版项目副本反向覆盖全局版。** 详见 `skills/README.md`。

### 学生端已砍掉登录（无会话模式）

`index.html` 不再加载 `store.js`：学生直接打开即可用，进度只落本机 `localStorage`，身份由本地姓名闸口（`tf_current_student`）决定。`getStudent()` 特意不再回退读 `tf_user`——否则共用一台平板时，上一位同学的登录名会把新同学的学情算到自己头上（该串号问题已实测复现过）。

代价与补偿：

- 学情不再自动上云，教师端「学情汇总」收不到学生端产生的记录。
- 任务区仍在：`server.js` 的 `GET /api/assignments` 允许匿名只读（下发任务是 `uid=-1` 的全局数据，每名学生本来就看得见），`index.html` 启动时拉取并每 30s 兜底轮询。教师端其余接口照旧要令牌，写操作仍限教师。
- 纯静态托管（不跑 `server.js`）时该请求失败会静默降级，任务区显示「本单元暂无任务」。
- 跟读已由三步（意群 → 跟句 → 影子）收敛为两步（跟句 → 影子），`CHUNKS` 数据与 `folChunks` / `folChunkSlice` / `followPlayChunk` / `followChunkEnd` 全部下线。
- 回归套件同步更新：`_smoke_follow_stage.py` 改为两步且不再登录；`_smoke_immerse.py` / `_smoke_bridge.py` / `_smoke_multi.py` 的学生端改为"预置本地姓名 + 匿名拉任务"。

## 改动后的验证

改任何页面或脚本后至少跑一遍 `npm run test:core`；涉及跟读、题库、跨设备同步时跑 `npm test`。
`_regress.js` 以退出码加关键断言双校验判定结果，不要只看日志输出。

## 不要提交

`think.db` 及 `-wal` / `-shm`、`backups/`、`src/`、`assets/sents/`、`assets/sents_v2/`、`render/`、`词汇诊断/`、`*.xlsx`、`index.backup.html`、`index.before-home-redesign.html`。

这些已在 `.gitignore` 中排除，不要用 `git add -f` 绕过。其中前两类含真实账号与学情，第三至五类含教材版权素材。

## 迁移遗留项

1. Google Fonts 外部依赖 —— `教师端.html`（第 9、11 行）与 `login.html`（第 7、9 行）各引 2 处 `fonts.googleapis.com`，国内与离线环境不可达，Inter 会回退到系统字体。建议本地化字体或改系统字体栈。
2. `/store.js` 绝对路径 —— `index.html:2556`、`教师端.html:1003`（`学生端.html` 已退役，不再引用）。子路径部署会 404，建议改为 `./store.js`。
3. 演示口令写在 `README.md` —— `teacher` / `think-teacher`、`助教` / `think-assist`、学生 `1234`，仓库公开前应改为首次启动随机生成或读环境变量。
4. Python 与 Playwright 未声明 —— 目前只在 README 的可选依赖里，建议补进 `package.json` 或 CI 说明。
5. `node:sqlite` 是实验性 API —— 启动会打印 ExperimentalWarning，升级 Node 前先看发布说明。

## 当前状态与下一步

最近一次提交 `4f37aa7`（`feat: 学生首页整合、主题词汇跳转与跨设备实时同步`）交付了三件事：

1. **学生首页并入 `index.html`** —— 书架 → 单元页（任务区 + 主题词汇入口卡 + 篇章）与点读引擎合并到同一页；原「学习之旅」首页已删除（`#map` / `MAP_BOOKS` / `renderHome` / `openHome`）；篇章跟读由新标签页改为同页切换并保留 `?pg=` 深链；`学生端.html` 退役为跳转壳（`?unit=N` 透传），教师端与登录页学生入口已改指 `index.html`。
2. **单元主题词汇改为跳转** —— 单元页 43 张内嵌词卡换成入口卡，篇章区起点由 1.8 屏提前到 0.9 屏，整页 2212px → 1314px；新增 `词汇诊断_theme_u7` / `theme_u12` 两页，**词表由 `index.html` 的 `THEME` 生成，勿手抄**；任务区主题行按 `theme_u<N>_records_v2` 自动判定完成，与篇章口径一致。
3. **跨设备实时同步** —— `GET /api/events`（SSE，零依赖）+ 30s 轮询兜底；教师改任务秒级推达在线学生端，学生产生学情推达在线教师/助教。

接手时的注意点：

- **新克隆缺 `词汇诊断/`** —— 该目录被 `.gitignore` 排除（版权），克隆后点「单元主题词汇」或「篇章词汇」会 404，需本地按 `skills/README.md` 的 `article-vocab-analyzer` 流水线重新生成。
- **词汇页只能改模板再批量重生成** —— 11 个篇章词汇页 + 2 个主题词汇页是同模板的参数化副本，逐页手改必然漂移。
- **SSE 有两处在自动化下无法复现** —— 真实标签页切换触发的 `visibilitychange`、窗口遮挡导致的 `document.hidden`，在 Playwright 环境里恒为 `false`。验证时改用「覆写 `document.hidden` + 派发事件」，或真机双设备手测。
- **本机到 `github.com` 连接不稳定** —— `git fetch/push` 可能报 `Recv failure: Connection was reset`，重试 2~3 次通常即通；`api.github.com` 一直可用，只读核验优先用 `gh api`。

可复跑的验证结论（本次已通过）：核心门禁 6/6、端到端冒烟 10 项全绿；推送到达 0.03s、断线重连 1.5s 自动补齐、静置 45s 连接存活、静置 20s 无自触发循环。

## 远端

`origin` = `https://github.com/hank-HUNAU/linkhankyou-englishroom`（private），默认分支 `main`。
