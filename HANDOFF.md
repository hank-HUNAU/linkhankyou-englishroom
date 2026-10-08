# HANDOFF · 交给 Codex 接手

本目录是 `xueersi-diancan-原型`（TH!NK 学习平板原型）的**完整工作副本**，用于交给 Codex 继续开发。

> 给 Codex 的权威说明在 **`AGENTS.md`**（Codex 会自动读取）。本文件只补充「这个包里有什么、怎么跑起来、和 GitHub 仓库有什么不同」。

## 怎么开始

1. 用 Codex 打开**本目录**作为工作区。
2. 先读 `AGENTS.md` 的「当前状态与下一步」一节，那里写着最近一次交付的内容、接手注意点和可复跑的验证结论。
3. 想跑起来：`npm start` → `http://localhost:8000`（若走 HTTPS 提示，加 `--http` 强制 HTTP：`node server.js --http`）。
4. 改完代码先跑 `npm run test:core`（纯 Node，约 18 秒，无需 Python）。

| 命令 | 作用 |
|---|---|
| `npm start` | 启动服务（`node server.js`），默认 `http://localhost:8000` |
| `npm run test:core` | 核心门禁：6 个套件，纯 Node + 2 个 Playwright 套件 |
| `npm test` | 全量回归：10 个套件（含 4 个诊断型） |
| `npm run test:list` | 列出全部套件 |

环境要求：Node.js **≥ 22.5**（`node:sqlite` 的 `DatabaseSync` 自 22.5 起提供）；Python 3 + Playwright 仅 4 个 `_smoke_*.py` 需要。项目**零 npm 依赖**，无 `node_modules`，无构建步骤。

演示账号：教师 `teacher` / `think-teacher`；助教 `助教` / `think-assist`；学生 `学生01`、`学生02`、`张小美` / `1234`。

## 本包已验证

打包后在**本目录内独立跑过** `npm run test:core`，结果 **6 套件全通过**（语法检查、视觉对齐、图标引用、API 冒烟 44 项、跟读支架 18 项、题库闭环）。所以这不是一份「只是复制过来」的包，而是确认可运行的工作副本。

包内 `think.db` 保留了三名学生账号与既有学情进度，开箱即可用；`students` 表里没有测试夹具残留。

## 包含 / 排除

**包含**（498 个文件，约 100 MB）：

| 内容 | 说明 |
|---|---|
| `index.html` / `教师端.html` / `login.html` / `学生端.html` | 四个页面（`学生端.html` 已是跳转壳） |
| `server.js` / `store.js` / `ui.css` / `ui.js` | 后端、存储垫层、设计令牌、图标系统 |
| `词汇诊断/` | **15 个文件，全部词汇诊断页**（11 篇章 + 2 主题词汇 + 审校表） |
| `assets/` | 课文音频 `p*.mp3`、`timeline.json`、句级切片 `sents/`、`sents_v2/` |
| `skills/` | **技能文件 71 个**：`skills/global/` 9 个 + `skills/project/` 1 个 |
| `src/` | 教材原始 PDF / MP3（内容再生产用） |
| `render/` | 18 张开发期渲染图 |
| `.git/` | 完整 git 历史与 `origin` 远端配置 |
| `think.db` 及 `-wal` / `-shm`、`*.xlsx` | 数据库与词表数据 |

**排除**（均为可再生的运行时产物）：

- `backups/` —— 14 份数据库定时快照
- `server.log` / `server.err` —— 运行日志
- `index.backup.html` / `index.before-home-redesign.html` —— `index.html` 的旧版本快照（git 历史里没有，属本地临时备份）
- `__pycache__/` —— Python 字节码缓存

技能文件做过逐字节比对：`skills/global/` 与全局安装目录 `~/.trae-cn/skills/` 的**同名文件内容完全一致**，全局目录只多出 `__pycache__` 缓存、`local-mineru/tests/` 样例文件和一份生成的 xlsx，因此本包只保留仓库版本，未重复收录。

## 与 GitHub 仓库的三点不同

1. **本包有 `词汇诊断/`，GitHub 仓库没有。** 该目录被 `.gitignore` 排除（版权），克隆仓库后会点不到词汇页（404）；本包已包含，功能完整。
2. **本包含 `src/` 原始教材与 `think.db`。** 同样被 `.gitignore` 排除，仅本地保留。
3. **`.git` 的 `origin` 指向同一个远端** `https://github.com/hank-HUNAU/linkhankyou-englishroom`。若原工作副本与本包都提交推送，会产生分叉——**建议只保留一个工作副本负责推送**。

另外，本机到 `github.com` 的连接不稳定，`git fetch/push` 可能报 `Recv failure: Connection was reset`，重试 2~3 次通常即通；`api.github.com` 一直可用，只读核验优先用 `gh api`。

## 接手前务必知道的四个坑

1. **词汇页只能改模板再批量重生成** —— 11 个篇章词汇页 + 2 个主题词汇页是同一套模板的参数化副本，逐页手改必然漂移。主题词汇页的词表由 `index.html` 的 `THEME` 生成，勿手抄。
2. **SSE 有两处在自动化下无法复现** —— 真实标签页切换触发的 `visibilitychange`、窗口遮挡导致的 `document.hidden`，在 Playwright 环境里恒为 `false`。验证时改用「覆写 `document.hidden` + 派发事件」，或真机双设备手测。
3. **不要用 `git add -f` 绕过 `.gitignore`** —— 前三类排除项含真实账号数据，后几类含教材版权素材。
4. **`node:sqlite` 是实验性 API** —— 启动会打印 ExperimentalWarning，升级 Node 前先看发布说明。
