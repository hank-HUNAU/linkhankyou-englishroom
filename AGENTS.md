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
| `store.js` | 存储垫层，拦截 `localStorage`；登录后水合，写入自动镜像上云 |
| `ui.css` / `ui.js` | 设计令牌与 SVG sprite 图标系统，三个页面共用 |
| `index.html` | 点读 / 跟读三阶段 / 词汇测试 |
| `学生端.html` | 书架 + 沉浸式任务区 |
| `教师端.html` | 班级、学生账号、任务下发、学情汇总、题库分析 |
| `login.html` | 登录 / 注册入口 |
| `assets/p*.mp3` | 课文音频，当前版本唯一的运行时音频依赖 |
| `_regress.js` | 回归入口，套件定义在文件顶部的 `SUITE` 数组 |
| `_check.js` / `_align_check.js` / `_check_icons.js` / `_smoke.js` | 纯 Node 校验，无外部依赖 |
| `_smoke_*.py` | Playwright 端到端，需要 Python 3 + Playwright |
| `skills/` | 内容生产技能文件，详见 `skills/README.md`；应用运行时不加载 |

## 架构要点

- 数据分桶：`kv` 表按 `uid` 隔离，`uid = -1` 是全局数据（教师下发的 `tf_assignments`，所有学生可见），其余为各账号私有学情。
- 令牌：`tf_token` 默认 7 天有效，剩余不足一半时滑动续期；写接口需 `Authorization: Bearer <token>`。
- 角色：`teacher` 可写，`assistant` 只读，写操作按钮自动置灰。
- 词汇引擎：干扰项走确定性优选 `pickDistractors`（同层同词性、人工审校优先），保证选项集合对所有学生一致，难度与区分度才可比。
- 归属仲裁：词汇分层取最低层、只归一层（KET < PET < NGSL < NAWL），各层覆盖率相加闭环。

## 内容生产工具链

应用运行时只消费产出物，不加载任何技能，所以技能全部缺席也不影响启动，只影响内容能否再生产。技能文件已随仓库提供，落在 `skills/` 下，按去向分两份：

| 仓库路径 | 去向 | 内容 |
|---|---|---|
| `skills/project/` | 新工作区的 `.trae/skills/` | `sentence-alignment`、`text-vocab-coverage` |
| `skills/global/` | 新环境的 `.trae-cn/skills/` | `local-mineru`、`article-vocab-analyzer`、`text-vocab-coverage`、`cet-cn2en-scholar`、`british-phonetics`、`student-vocab-cards`、`exam-paper-bank`、`teacher-vocab-prep`、`sentence-alignment`、`chunk-splitter` |

产出对应关系：`article-vocab-analyzer` / `text-vocab-coverage` 分析课文产出词汇报告与 `词汇诊断/`；`sentence-alignment` 对齐音频产出 `assets/timeline.json`；`teacher-vocab-prep` / `student-vocab-cards` / `british-phonetics` 是三个软分支，由 `article-vocab-analyzer/scripts/vocab_pipeline.py` 串联编排。

`sentence-alignment` 与 `text-vocab-coverage` 在 `project/` 与 `global/` 下内容不完全相同（详见 `skills/README.md`）。迁移前先确定单一权威版本，否则同一份课文在不同环境会算出不同覆盖率。

## 改动后的验证

改任何页面或脚本后至少跑一遍 `npm run test:core`；涉及跟读、题库、跨设备同步时跑 `npm test`。
`_regress.js` 以退出码加关键断言双校验判定结果，不要只看日志输出。

## 不要提交

`think.db` 及 `-wal` / `-shm`、`backups/`、`src/`、`assets/sents/`、`assets/sents_v2/`、`render/`、`词汇诊断/`、`*.xlsx`、`index.backup.html`、`index.before-home-redesign.html`。

这些已在 `.gitignore` 中排除，不要用 `git add -f` 绕过。其中前两类含真实账号与学情，第三至五类含教材版权素材。

## 迁移遗留项

1. Google Fonts 外部依赖 —— `学生端.html`、`教师端.html`、`login.html` 各引 3 处 `fonts.googleapis.com`，国内与离线环境不可达，Inter 会回退到系统字体。建议本地化字体或改系统字体栈。
2. `/store.js` 绝对路径 —— `index.html:1759`、`学生端.html:1057`、`教师端.html:989`。子路径部署会 404，建议改为 `./store.js`。
3. 演示口令写在 `README.md` —— `teacher` / `think-teacher`、`助教` / `think-assist`、学生 `1234`，仓库公开前应改为首次启动随机生成或读环境变量。
4. Python 与 Playwright 未声明 —— 目前只在 README 的可选依赖里，建议补进 `package.json` 或 CI 说明。
5. `node:sqlite` 是实验性 API —— 启动会打印 ExperimentalWarning，升级 Node 前先看发布说明。

## 远端

`origin` = `https://github.com/hank-HUNAU/linkhankyou-englishroom`（private），默认分支 `main`。