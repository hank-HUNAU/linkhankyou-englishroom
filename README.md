# TH!NK 学习平板 · 课文点读与预习复习

面向小学高年级英语课堂的学习应用原型：**学生预习/复习 → 课文点读与跟读 → 词汇测试**，教师端配套**班级与学生账号管理、任务下发、学情汇总、题库质量分析**。

后端**零 npm 依赖**——只用 Node 内建 `http` + `node:sqlite`，克隆即跑，无需 `npm install`。

---

## 一、功能总览

### 1. 学生端（`学生端.html`）
- **书架 → 单元 → 材料**三级导航，深链直达：`学生端.html?unit=7`
- **只接收预习与复习两类材料**，不暴露教师备课视角（无考点徽标、无命题矩阵）
- **沉浸式任务区**：今日学习卡（单元/日期）+ 进度环（`已完成/总数`）+ 预习组 / 复习组 + 任务行
- 任务行三态：未开始 / 已完成；打开材料**自动记录 started**，也可手动勾选完成
- **预习→复习衔接引导**：预习项全部完成时弹出全屏引导层，提供「进入复习」与「稍后再说」

### 2. 点读页（`index.html`）
- 深链直达某页：`index.html?pg=66`
- **课文三步流程**：`1 聆听 → 2 跟读 → 3 听写`
- **点读**：句级时间轴（`TL`）+ 句内意群（`CHUNKS`），逐句高亮、点句即播
- **跟读支架化三阶段**（解决「不敢开口 / 跟不上」）：
  - 第 1 步 **意群**：听一个意群 → 暂停 → 开口跟读这一小段
  - 第 2 步 **跟句**：听完整一句 → 暂停 → 跟读整句
  - 第 3 步 **影子**：落后音频半拍，从头到尾不停
  - 阶段自动衔接，暂停间隙提示「该你开口 · 跟读这段」
- 对话课文自动切气泡样式（`body.dialog`）；中文对照可开关，跟读环节禁用译文
- **词汇测试引擎**：确定性干扰项优选（同层同词性、人工审校优先），逐题记录选项 / 正误 / 错误类型

### 3. 教师端（`教师端.html`）
- **角色门禁**：教师可写，助教只读（写操作按钮自动置灰）
- **班级管理**：建班 / 改名 / 删除
- **学生账号**：新增 / 改名 / 重置口令 / 分班 / 删除
- **任务下发**：按单元选材料（主题词汇 / 篇章词汇 / 跟读），设截止时间，一键保存
- **学情汇总**：按班筛选，查看每个学生各任务的完成状态与完成时间
- **题库分析**：由学生作答数据聚合 **难度（正确率 p）** 与 **区分度（高低分组 D / 点二列相关 r）**，并标记 **待人工审校的干扰项**（歧义 / 无效选项 / 偏难偏易）

### 4. 账号与跨设备同步
- `store.js` 是**存储垫层**：拦截 `localStorage`，登录后从服务端水合，本地写入自动镜像上云——原引擎代码零改动即完成上云
- 数据按 `uid` 分桶：**教师任务标记为全局**（`scope=global`，所有学生可见），**学生学习数据按账号隔离**
- 令牌（`tf_token`）默认 **7 天**有效，剩余不足一半时**滑动续期**

### 5. 安全基线
| 项 | 实现 |
|---|---|
| HTTPS | `certs/` 下存在证书则自动启用；`--http` 强制回退 |
| 口令存储 | 随机盐 + 哈希，不存明文 |
| SQL 注入 | 全部**参数化查询**，`students/update` 逐字段独立语句，无字符串拼接 |
| 响应头 | `X-Content-Type-Options: nosniff`、`X-Frame-Options: SAMEORIGIN`、`Referrer-Policy: same-origin` |
| CORS | 仅放行**同源**请求，不再 `*` |
| 备份 | 每 **6 小时**自动备份 `think.db` 到 `backups/`，保留最近 **14** 份 |

---

## 二、快速开始

### 环境要求
- **Node.js ≥ 22.5**（`node:sqlite` 的 `DatabaseSync` 自 22.5 起提供）
- 现代浏览器（Chromium / Edge / Safari）
- 可选：Python 3 + Playwright（仅跑端到端回归时需要）

### 启动
```bash
node server.js            # → http://localhost:8000
node server.js --http     # 强制 HTTP（已有证书但想用 HTTP 时）
npm start                 # 等价于 node server.js
```
启动后控制台会打印**本机地址**与**局域网地址**（如 `http://192.168.3.115:8000`）——用后者可在第二台设备上验证跨设备同步。

> **不要直接双击 HTML 文件。** 这是带后端的应用，`file://` 下无法登录与同步；`store.js` / `login.html` 会拦截并给出启动指引。

### 启用 HTTPS（可选）
```bash
node gen-cert.js          # 生成自签证书到 certs/
node server.js            # 自动识别并启用 HTTPS
```

### 默认账号

| 角色 | 账号 | 口令 |
|---|---|---|
| 教师 | `teacher` | `think-teacher` |
| 助教（只读） | `助教` | `think-assist` |
| 学生 | `张小美` / `学生01` / `学生02` | `1234` |

首次启动会自动建库并写入上述演示账号；学生也可在登录页自行注册。

### 操作路径

**学生**：`login.html` 选「学生」登录 → 书架点单元 → 沉浸式任务区 → 点任务行打开材料 → 走完三步流程 → 回任务区勾完成 → 预习全完成后按引导进入复习

**教师**：`login.html` 选「教师」登录 → **班级/学生**建班加人 → **任务下发**选材料设截止 → **学情**看完成情况 → **题库分析**看待审校干扰项

**跨设备**：教师机下发任务 → 另一台设备用局域网地址 + 学生账号登录 → 应看到同一份任务与截止时间

---

## 三、目录结构

```
xueersi-diancan-原型/
├── server.js                  后端：静态服务 + 账号 + KV 存储 + 聚合接口 + 备份
├── store.js                   localStorage → 云同步 垫层
├── ui.css                     设计令牌（颜色 / 圆角 / 阴影）
├── ui.js                      SVG sprite 图标系统
├── login.html                 登录 / 注册入口
├── 学生端.html                 学生书架 + 沉浸式任务区
├── 教师端.html                 教师工作台
├── index.html                 课文点读 / 跟读 / 词汇测试
├── gen-cert.js                生成 HTTPS 自签证书
├── assets/                    课文音频 p*.mp3（12 个）
├── package.json               脚本与 Node 版本要求
├── _regress.js                一键回归入口
├── _check.js / _align_check.js / _check_icons.js / _smoke.js
├── _smoke_follow_stage.py / _smoke_bank_ui.py / _smoke_bridge.py
├── _smoke_roster.py / _smoke_immerse.py / _smoke_multi.py
└── （一次性内容生产工具，见下表）
```

运行时自动生成、**不入库**：`think.db`（及 `-shm`/`-wal`）、`backups/`、`certs/`、`server.log`。

---

## 四、依赖文件清单

### A. 运行时必需（应用本体，9 个文件 / 约 345 KB）

| 文件 | 大小 | 作用 |
|---|---|---|
| `server.js` | 25 KB | 后端：静态服务、账号认证、KV 存储、聚合接口、定时备份、安全响应头 |
| `store.js` | 4 KB | 存储垫层，`localStorage` 透明上云 |
| `ui.css` | 4 KB | 设计令牌：主色/辅色、圆角刻度 `--r-xs…--r-2xl`、阴影刻度、组件契约 |
| `ui.js` | 5 KB | SVG sprite 图标系统，三页共用 |
| `login.html` | 7 KB | 登录 / 注册（角色切换、`file://` 拦截提示） |
| `学生端.html` | 70 KB | 学生书架、单元页、沉浸式任务区、预习→复习引导层 |
| `教师端.html` | 55 KB | 教师工作台：班级 / 学生 / 任务 / 学情 / 题库分析 |
| `index.html` | 172 KB | 点读页：内嵌课文数据、句级时间轴、CHUNKS、词汇测试引擎 |
| `gen-cert.js` | 2 KB | 生成自签证书到 `certs/`，用于启用 HTTPS |
| `assets/p*.mp3` | **20 MB**（12 个） | 课文音频，点读与跟读的音源 |

### B. 开发与验证（回归套件，11 个文件 / 约 51 KB）

| 文件 | 大小 | 覆盖内容 |
|---|---|---|
| `_regress.js` | 11 KB | **一键回归入口**，串跑下列脚本并汇总 |
| `_check.js` | 0.8 KB | HTML 内联脚本 + JS 语法检查 |
| `_align_check.js` | 3 KB | 设计令牌完整性、硬编码圆角残留、三页关键组件取值一致 |
| `_check_icons.js` | 2 KB | 三页引用的图标 id 是否都在 sprite 中定义 |
| `_smoke.js` | 10 KB | API 层冒烟 40 项（账号 / 存储 / 聚合 / 权限） |
| `_smoke_follow_stage.py` | 4 KB | 跟读三阶段（意群 → 跟句 → 影子）UI 与状态机 |
| `_smoke_bank_ui.py` | 5 KB | 题库分析闭环：播种作答 → 难度/区分度/待审校 → 清理 |
| `_smoke_bridge.py` | 5 KB | 预习→复习衔接引导 |
| `_smoke_roster.py` | 5 KB | 花名册 / 班级 / 学情筛选 / 助教只读 |
| `_smoke_immerse.py` | 2 KB | 学生端沉浸式任务区渲染与点击跳转 |
| `_smoke_multi.py` | 4 KB | 跨设备同步（教师机 ↔ 学生机） |

用法见「六、回归测试」。

### C. 内容生产工具（一次性，应用运行**不需要**，8 个文件 / 约 23 KB）

| 文件 | 作用 |
|---|---|
| `_gen_review_sheet.js` | 由篇章数据生成「干扰项审校工作表」CSV，供人工审校 |
| `_patch_vqdis.js` | 把人工审校后的干扰项写入词表 `dis` 字段 |
| `_patch_vocab.js` | 批量修订词表字段 |
| `_inject.js` | 批量注入片段到页面 |
| `scan_index.py` / `scan_tl.py` / `shot_unit.py` | 索引 / 时间轴 / 单元页的扫描与截图 |
| `split_audio.py` | 音频按句切分，产出句级 wav |

### D. 配套技能包（**位于仓库外**，内容生产流水线）

以下 8 个技能位于 `~/.trae-cn/skills/`，用于**生产**本应用所需的教学内容（词汇分层、音标、朗读标注、意群切分、句级对齐），**不是应用运行时依赖**，随仓库发布时按需单独同步。

| 技能 | 规模 | 作用 |
|---|---|---|
| `article-vocab-analyzer` | 15 文件 / 820 KB | **主技能**：KET/PET/NGSL/NAWL 四词表分层 + lemma 归一 + 短语优先 + CEFR 难度标签 + 覆盖率/Range/超纲报告 |
| `text-vocab-coverage` | 12 文件 / 785 KB | 多词表命中率与覆盖面检测（轻量版） |
| `british-phonetics` | 6 文件 / 73 KB | 英式音标（UK IPA）+ 英式真人发音 + 朗读标注（意群切分/停连/降升调/弱读） |
| `student-vocab-cards` | 4 文件 / 61 KB | 学生记忆词卡：本义/音标/发音/派生/双语例句 |
| `teacher-vocab-prep` | 3 文件 / 17 KB | 教师备课本：分层词卡 + 考点命题矩阵 + 超纲补卡 + 单元统计 |
| `cet-cn2en-scholar` | 11 文件 / 432 KB | 四六级汉译英「原文先行」三规约闭环 |
| `chunk-splitter` | 1 文件 / 4 KB | 句中意群（呼吸群）人工切分，产出 CHUNKS |
| `sentence-alignment` | 1 文件 / 6 KB | 句级音频↔文本对齐（ASR 粗锚 + 声学能量精修） |

### E. 不应入库（已在 `.gitignore` 中排除）

| 内容 | 大小 | 原因 |
|---|---|---|
| `think.db` + `-shm` + `-wal` | 4.1 MB | 运行时数据库，**含真实账号与学生学情** |
| `backups/` | 416 KB | 数据库自动备份 |
| `certs/` | — | HTTPS 自签证书私钥 |
| `server.log` / `server.err` | — | 运行日志 |
| `src/` | 11 MB | 教材原始 PDF 与音频（**版权**） |
| `assets/sents/`、`assets/sents_v2/` | 21.7 MB | 句级切分中间产物，当前版本未引用 |
| `assets/timeline.json`、`assets/vocab_youdao.json` | 440 KB | 当前版本未引用的旧资源 |
| `render/`、根目录 `*.png` | 16.9 MB | 渲染与调试截图 |
| `词汇诊断/` | 1.9 MB | 含课文原文的诊断页与审校工作表（**版权**） |
| `*.xlsx`、`p067_p070_*.md`、`单元篇章清单_unit1-12.html` | 252 KB | 教学产出物（含课文原文/译文） |
| `index.backup.html`、`index.before-home-redesign.html` | 436 KB | 历史快照 |

入库体积约 **20.6 MB**，其中 20 MB 是课文音频。

---

## 五、接口一览

后端共 16 个接口，均返回 JSON；除登录/注册外都需要 `Authorization: Bearer <token>`。

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/login` | 公开 | 登录，返回用户与令牌 |
| POST | `/api/register` | 公开 | 学生自助注册 |
| GET | `/api/me` | 登录 | 当前用户信息 |
| POST | `/api/logout` | 登录 | 注销并失效令牌 |
| GET | `/api/kv` | 登录 | 拉取该用户的全部键值数据（含全局桶） |
| POST | `/api/kv` | 登录 | 写入键值（`scope=global` 仅教师可写） |
| GET | `/api/reports` | 教师/助教 | 学情聚合 |
| GET | `/api/bank` | 教师/助教 | 题库分析：难度 / 区分度 / 待审校干扰项 |
| GET | `/api/classes` | 教师/助教 | 班级列表（含人数） |
| POST | `/api/classes` | 教师 | 建班 |
| POST | `/api/classes/update` | 教师 | 班级改名 |
| POST | `/api/classes/delete` | 教师 | 删班（成员自动解除归属） |
| GET | `/api/students` | 教师/助教 | 学生列表（含班级） |
| POST | `/api/students` | 教师 | 新增学生 |
| POST | `/api/students/update` | 教师 | 改名 / 重置口令 / 分班 |
| POST | `/api/students/delete` | 教师 | 删除学生及其数据 |

---

## 六、回归测试

```bash
npm test                  # 全量 10 项（核心门禁 + 诊断），约 50s
npm run test:core         # 只跑核心 6 项，约 17s，无数据副作用
npm run test:list         # 只列套件清单
node _regress.js --no-server   # 不自动拉起服务器
```

`_regress.js` 的行为：
- **自动起服务**：探测 `localhost:8000`，没在跑就用 `node server.js --http` 拉起，跑完自动回收；复用已运行的实例时不动它
- **双校验判定**：退出码为 0 **且**命中全部关键断言、未命中禁止项才算通过（部分脚本只打印不返回退出码，单看退出码会漏判）
- **串行执行**：脚本共用同一服务端与数据库，并行会互相污染
- 失败时打印该脚本末尾输出并给出非零退出码，可直接接 CI

前置：Python 3 + `playwright`（`pip install playwright && playwright install chromium`）。缺 Python 时相关项会标记为「跳过」而非失败。

> 诊断型脚本（`_smoke_bridge.py` / `_smoke_roster.py` / `_smoke_multi.py`）会写入单元 7 的任务夹具与临时班级/学生，脚本结束时会自行清理。

---

## 七、部署建议

1. **进程守护**：`node server.js` 交给 `pm2` / `systemd` / Windows 服务托管；改端口用环境变量 `PORT`
2. **必须启用 HTTPS**：`node gen-cert.js` 生成自签证书仅适合内网；公网请换正式证书（反向代理 Nginx/Caddy 终止 TLS 亦可）
3. **改默认口令**：`teacher` / `助教` 的默认口令是演示值，上线前必须改
4. **令牌有效期**：默认 7 天，可用环境变量 `TOKEN_TTL_MS` 覆盖
5. **备份**：`backups/` 默认保留 14 份、每 6 小时一次；如需异地备份请另行挂载
6. **数据卷**：`think.db` 与 `backups/` 需挂到持久化磁盘

---

## 八、版权与合规（发布前务必确认）

本原型内含**剑桥《Think》第二版教材**的课文文本与音频（`src/` 中的原始 PDF/MP3，以及由它派生的 `assets/p*.mp3`、`index.html` 内嵌课文、`词汇诊断/` 诊断页、`p067_p070_*.md` 译文与逐字稿）。这些内容**受版权保护**，仓库已通过 `.gitignore` 排除原始素材与含原文的产出物。

发布到 GitHub 前请确认：
- **建议设为 Private 仓库**；若必须 Public，请进一步排除 `assets/*.mp3` 与 `index.html` 中的课文数据（会同时失去点读/跟读的可运行性）
- 或**替换为你自行录制/获授权的音频与文本**后再公开
- `KET/PET` 词表来自剑桥官方词表，商用前请核对其使用条款
- 仓库默认 `license` 为 `UNLICENSED`（保留所有权利）；如需开源请自行选定许可证并同步修改 `package.json`