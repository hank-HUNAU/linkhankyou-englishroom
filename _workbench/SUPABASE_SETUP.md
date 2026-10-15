# TH!NK 双工作台 · Supabase 后端部署清单（v1.0，2026-10-15）

> 架构定案：**Supabase 后端（数据清空重建，不迁移资料库）+ GitHub 前端**。
> 本清单做到「凭证到位 → 十分钟通线」；所有前置改造已完成。

---

## 0. 现状一览（本轮已完成的前置准备）

| 项 | 状态 | 位置 |
|---|---|---|
| 建表 SQL（5 表，中文列名，RLS anon 全读写） | ✅ 就绪 | `_workbench/supabase_schema.sql` |
| 种子数据 SQL（可选示例：2 班级 / 4 学生 / 2 任务 / 2 记录 / 1 资源） | ✅ 就绪 | `_workbench/supabase_seed.sql` |
| 双端数据层适配器（业务调用点零改动） | ✅ 已植入 | `_workbench/teacher-workbench.html` / `student-workbench.html` |
| 双端 GitHub Pages 部署副本 | ✅ 已入库 | `workbench/teacher.html` / `workbench/student.html` |
| 规格 v1.1 修订（零外链条目解锁） | ✅ 已记录 | `_workbench/TEACHER_WORKBENCH_SPEC.md` / `STUDENT_WORKBENCH_SPEC.md` |
| `SUPA_CONFIG` 启用 | ⏳ 等凭证 | 两份 HTML 顶部，`enabled: false` 占位 |

**数据分层结论（工作区分析 2026-10-15）**

- **GitHub 静态层（已在仓库，无需动）**：`assets/timeline.json` 28 篇 / 687 句（U7–U12 全覆盖）；17 个课文音频；`index.html` 点读平台（篇章元数据当前只接 U7/U12，U8–U11 数据已在 timeline 中待接）；词汇数据在 `Think F 教材资产/*/02_词汇数据/`（24 个词汇 JSON / 5412 词条，含 layer/cefr 标注）——**尚未入库**，见 §4 待办。
- **Supabase 动态层（本清单）**：预习任务 / 学习记录 / 班级 / 学生账户 / 教学资源 5 表。

---

## 1. 创建 Supabase 项目（约 3 分钟）

1. [supabase.com](https://supabase.com) → **Sign up with GitHub**（授权页需本人操作）
2. **New project**：名称随意（如 `think-workbench`）；Region 选 **Singapore** 或 Tokyo；数据库密码自留
3. 等待项目初始化完成（约 1–2 分钟）

## 2. 跑建表 SQL

Dashboard → **SQL Editor** → New query：

1. 粘贴 `supabase_schema.sql` 全文 → **Run** → 期望 `Success`
2. （可选）粘贴 `supabase_seed.sql` 全文 → **Run** → 灌入示例数据

## 3. 凭证回填（交给我或自己改）

**Settings → API** 复制两项，填入两份 HTML 的 `SUPA_CONFIG`：

```js
var SUPA_CONFIG = {
  enabled: true,                      // ← 改 true
  url: 'https://xxxxx.supabase.co',   // ← Project URL
  anonKey: 'eyJhbGciOi...',           // ← anon public key
};
```

> ⚠️ **只要 anon key，绝不要 service_role key**。service_role 绕过一切 RLS，写入公开前端等于数据库裸奔。

**凭证交给我时我会做**：回填双端 + 部署副本共 4 处 → REST 冒烟（建表校验、读写各一次）→ commit + push。

## 4. 冒烟验收（凭证到位后逐条过）

1. `curl https://<PROJECT>.supabase.co/rest/v1/classes?select=*` 带 `apikey` 头 → 返回种子班级
2. 学生端 `workbench/student.html`：学号 `S2026001` 登录 → 完成一项预习 → 学习记录表新增一行
3. 学生端复习三档自评 → 原记录 `掌握度/复习次数/下次复习` 更新
4. 教师端 `workbench/teacher.html`：学情看板可见上述记录；推送新任务 → 学生端可见
5. 教师端撤回该任务 → 学生端即时隐藏

## 5. 上线切换与回滚

- **上线**：把 `workbench/` 两页链接发给学生/自用；GitHub Pages 自动随 push 更新
- **资料库入口并存**：workbuddy.link 双页不受影响（`enabled` 只在 GitHub 副本上改，资料库版本保持回落资料库后端）
- **回滚**：`SUPA_CONFIG.enabled` 改回 `false` → GitHub 副本回到演示模式，零风险
- **免费档提醒**：项目 7 天无活动会暂停，去 Dashboard → Restore 即可；课堂日常使用不会触发

## 6. 安全与升级路径

- 当前 RLS = anon 全读写（与资料库公开页同安全级；数据非敏感：班级/任务/记录，**无密码无身份信息**）
- 学号列已加唯一索引（`idx_stu_sid`），防重复身份
- 升级路径：接入 Supabase Auth 后收紧——教师可写任务/班级/账户，学生仅写自己的记录
- 禁止把 `service_role`、数据库密码写进任何前端文件或提交到仓库

---

## 附：数据边界速查

| 数据 | 去向 | 原因 |
|---|---|---|
| timeline.json（篇章句级）、音频、词汇 JSON | GitHub 静态 | 只读内容，Pages 直接吃 |
| 预习任务、学习记录、班级、学生账户、教学资源 | Supabase | 双端动态读写 |
| 备课本/学生卡 xlsx、词汇诊断 HTML | 本地归档（Think F 教材资产） | 生产中间物，非运行时依赖 |
