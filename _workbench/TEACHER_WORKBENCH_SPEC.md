# TH!NK 教师端工作台 · 冻结规格（LOCKED v1.0）

> **锁定日期**：2026-10-14（圆桌会议 7 议题收敛 + 视口锁定改造后）
> **状态**：🔒 已锁定。任何修改前必须先由用户明示「解锁」，并记录变更原因。
> **线上地址**：https://workbuddy.link/p/2SypNEMB8U8YXelLsrw5VN（迭代覆盖导入，链接永不变）
> **源文件**：`codex-handoff/_workbench/teacher-workbench.html`（单文件，全内联；外链仅 Supabase JS CDN 一项，见文末 v1.1 修订）
> **数据表绑定**（5 张）：预习任务 `M2BiG1J9hhkYDOcdZFWi3s` · 学习记录 `qKJybtlu4NrEqJ7yUPTduo` · 教学资源 `iRti0RoXNhXFoekVY9y4Cf` · 班级 `PUQ5oUZJNDYWKBBMpIijgw` · 学生账户 `2OjdhXTwUccUa71i4R2wBx`

---

## 一、定位与边界（不得回退）

| 决策 | 冻结值 |
|---|---|
| 模块 | **6 个**：今日关注 / 推送预习 / 班级管理 / 账户管理 / 教学资源 / 学情看板（`state.view`：focus/push/classes/accounts/resources/insight） |
| 布局 | 左导航（224px）+ 顶栏（模块名/副标题 + 班级筛选）+ 视图区；班级/账户/学情为**列表→详情三段分栏** |
| 单教师假设 | 当前**不做**多教师/角色权限；页面无登录（与需要登录的学生端不同） |
| 管理闭环 | 三张清单能力对齐：已推送预习（修改/软撤回/删除）、班级（修改/删除）、账户（修改/停用/删除）、**教学资源（修改/删除）** |
| 软撤回 | 预习任务 `任务状态`（已推送/已撤回），撤回可逆、学生端即时隐藏；撤回/恢复**不写**修改时间（状态徽章自明，避免噪音） |
| 变更痕迹 | 编辑保存写 `修改时间`（date，field_id `SzOPUCkL`），任务列表显示「修改于 X日」；**学生端展示等学生端解锁** |

## 二、视口锁定外壳（2026-10-14 定案，8 条规范）

1. `html,body{height:100%; overflow:hidden; overscroll-behavior:none}`——页面永不出现滚动条
2. `body{height:100vh→100dvh}` 双声明 + 四向 `env(safe-area-inset-*)` 安全区
3. `.app{height:100%}`；`.body` flex 列 + `overflow:hidden`；footer **移出滚动区常驻底栏**（含安全区 padding）
4. `main` 是纯视图容器（flex 列、不滚、padding 0 20px）；**滚动收敛到视图内部**
5. 普通视图 `.view.on{overflow-y:auto; max-width:1280px; margin:0 auto; padding:16px 0 20px}`
6. 分栏视图 `.view.split.on{display:grid; overflow:hidden; grid-template-rows:minmax(0,1fr)}`——pane `height:100%; min-height:0` 内部滚，**禁止**再用 `max-height:calc(100vh - Npx)` 魔法数
7. 切模块复位：`setView` 复位当前视图 `scrollTop`（不用 `window.scrollTo`）
8. 声明顺序注意：`.view.card` 的 `padding:16px` 在 `.view.on` 之后（同特异性后者胜），卡片边框固定、内容内滚

## 三、冻结的关键值（与线上代码对齐）

### 响应式断点
- `≤1400px`：导航 196px，分栏列表 240–290px
- `≤1100px`：`.app` 转 `grid-template-rows:auto minmax(0,1fr)`，导航转顶部横向 tab
- `≤1024px`：推送页双栏折单列（表单在上）
- `≤900px`：分栏列表/详情互换，详情栏出「返回列表」
- `≤620px` KPI 两列；`≤560px` dgrid 单列；`≤520px` f2 单列
- 输入框 ≥16px（防 iOS 放大）；按钮梯度：mini/chipx **36px** → 主按钮/取消 **46px**；列表行 52px；导航项 44px

### 功能行为
- **推送页双栏**：左 5fr 表单｜右 7fr 管理列表（`.push-grid`）；表单限宽 760px
- **班级筛选**：只在 focus / accounts / insight 显示（`renderNav` 按 `state.view` 切 `classSwitch` 显隐）；跳转对齐：goto-acc 时 scope 自动对齐该生班级（未分班回落「全部」，写回 `wb_think_teacher_scope`）
- **今日关注**：每项带「去处理」——学生事项 → 账户详情选中该生（含筛选对齐 + 窄屏 `openDetail`）；任务事项 → 推送页并 `startEditTask` 进编辑态
- **教学资源**：修改回填表单（编辑条 + 取消）+ 两步确认删除；列表全量渲染（原 6 条截断已去）
- **近 7 天节奏**：`miniBars()` 共享助手，注入账户详情与学情详情；按学习记录日期本地窗口统计

### 数据约定
- 预习任务字段含 `推送方式`（全班/按班级/按个人）+ `推送对象`（多选）+ `任务状态` + `修改时间`；旧 `推送班级` 字段弃用保留
- 资源 `链接` 为 url 复合字段 `{text, link}`；编辑时空链接不清除（可接受）
- localStorage 键：`wb_think_teacher_scope` / `wb_think_teacher_view` / `wb_think_teacher_draft_*` / `wb_think_cache_*`

## 四、文案红线（禁止回加）

- 模块名固定「**今日关注**」（2026-10-14 更名，勿写回「今天要关注」）
- 已删且不得恢复：~~推送预习至学生端+sub~~、~~可修改、撤回或删除~~、~~音频/讲义/词汇表，学生端可调用~~（卡头重复）、~~右侧新建一个~~（方位词）
- 总原则：标题不自释、说明不重复按钮、空态不给窄屏不成立的方位词；`focusHint` 是动态计数（「共 N 项待关注」），不是静态副标题

## 五、已明确「不做」清单

- ❌ 通知推送（纯前端无渠道，钉死）
- ❌ 词汇级掌握分析（等词汇本落地有数据）
- ❌ 多教师 / 角色权限
- ❌ 教学资源分栏（资源过 **10 条**再议）
- ❌ 任务撤回/恢复写修改时间
- ❌ 外部 CDN/框架/字体/图标库

## 六、验收门禁（每次改动后全跑）

1. `node --check`（内联脚本抽出）
2. DOM id 交叉校验 0 缺失；标签闭合平衡
3. `lint_schema` / `lint_database_sdk_usage` / `lint_page_quality`（PQ001 用 `--ack` 放行）
4. schema 变更须同步 `gen_schema.py` 并重新生成 canon/merged
5. 发布态复查：5 表绑定、改动项在位、旧模型零残留（**发布态字面量检查会因导入管线注入 `data-page-node-id`/注释而误报，须带上下文正则复查**）

---

## v1.1 修订（2026-10-14，用户解锁「零外链」条款：接入 Supabase 后端）

**变更原因**：用户定案架构——Supabase 后端（数据清空重建，不做资料库迁移）+ GitHub 前端（篇章/词汇静态数据已在仓库 `linkhankyou-englishroom`）。

| 修订项 | 内容 |
|---|---|
| 零外链条目 | 修订为「**全内联，外链仅 `cdn.jsdelivr.net` 的 supabase-js UMD 一项**」；其余 CDN/框架/字体仍禁 |
| 数据层 | 新增 `SUPA_CONFIG`（enabled/url/anonKey 三值）+ `makeSupaAdapter()`；后端选择链：**Supabase（enabled 且 CDN 库加载成功）→ 资料库 SDK → null（演示模式）** |
| 适配器接口 | 与资料库 SDK 同形：`query / getSchema / addRecord / updateRecord / deleteRecord`；**全部业务调用点零改动** |
| 表映射 | 5 张资料库表 ID → Supabase 表：`prep_tasks / learning_records / resources / classes / students`（建表脚本 `supabase_schema.sql`，中文列名与双端字段一致） |
| 属性转换 | 写入 `{text/select/number/date/url:{text,link}}` → 平面值；读出还原扁平行（`_id` + 中文字段），资源 `链接` 列还原为 `[{text,link}]` |
| getSchema | Supabase 无选项枚举 → 返回空 properties，`OPTION_FALLBACK` 兜底 |
| 分页 | Supabase `range(offset)` 模拟游标分页，单页 200，与调用侧 guard 20 页兼容 |
| 页脚文案 | 「数据存于资料库」→「数据云端同步」（双端） |
| 部署 | 目标宿主 GitHub Pages（仓库根或 /workbench/）；资料库页面版本保留可用（自动回落资料库后端） |
| 安全 | anon 全读写 RLS（与公开页同级）；**严禁 service_role key 入前端**；升级路径：接 Supabase Auth 后收紧 RLS |

**验收门禁追加**：`SUPA_CONFIG.enabled=false` 时行为与 v1.0 完全一致（回归基线）；启用后须在 Supabase 建表并冒烟双端读写。
