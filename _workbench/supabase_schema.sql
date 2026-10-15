-- =====================================================================
-- TH!NK 双工作台 · Supabase 建表脚本（v1.0，2026-10-14）
-- 对应资料库 5 张表 → Supabase Postgres，字段名保持中文与双端一致
-- 执行方式：Supabase Dashboard → SQL Editor → 粘贴运行
-- 安全模型：anon 可读写（与当前资料库公开页面同一安全级别）
--          后续升级路径：接入 Supabase Auth 后收紧 RLS
-- =====================================================================

-- 1. 预习任务
create table if not exists public.prep_tasks (
  id uuid primary key default gen_random_uuid(),
  "任务标题" text not null,
  "单元" text default '',
  "内容类型" text default '阅读',
  "推送班级" text default '',            -- 旧字段，弃用保留
  "推送方式" text default '全班',
  "推送对象" text default '',
  "任务状态" text default '已推送',       -- 已推送 / 已撤回
  "预计用时" int default 0,
  "推送时间" date default current_date,
  "修改时间" date,
  "截止日期" date default current_date + 1,
  "任务说明" text default '',
  created_at timestamptz not null default now()
);

-- 2. 班级
create table if not exists public.classes (
  id uuid primary key default gen_random_uuid(),
  "班级名称" text not null,
  "学段" text default '',
  "授课教师" text default '',
  "计划人数" int default 0,
  "班级状态" text default '筹备中',
  "创建时间" date default current_date,
  "备注" text default '',
  created_at timestamptz not null default now()
);

-- 3. 学生账户
create table if not exists public.students (
  id uuid primary key default gen_random_uuid(),
  "姓名" text not null,
  "学号" text,
  "所属班级" text default '',
  "账户状态" text default '在读',         -- 在读 / 停用
  "加入时间" date default current_date,
  "备注" text default '',
  created_at timestamptz not null default now()
);

-- 4. 学习记录
create table if not exists public.learning_records (
  id uuid primary key default gen_random_uuid(),
  "学生" text not null,
  "记录类型" text default '预习',
  "学习内容" text default '',
  "单元" text default '',
  "用时分钟" int default 0,
  "正确率" numeric,
  "掌握度" text,                          -- 陌生 / 模糊 / 熟悉 / 掌握
  "复习次数" int default 0,
  "日期" date default current_date,
  "下次复习" date,
  "备注" text default '',
  created_at timestamptz not null default now()
);

-- 5. 教学资源
create table if not exists public.resources (
  id uuid primary key default gen_random_uuid(),
  "资源名称" text not null,
  "类型" text default '音频',
  "单元" text default '',
  "标签" text default '',
  "链接" text default '',
  "上传时间" date default current_date,
  created_at timestamptz not null default now()
);

-- =====================================================================
-- 行级安全（RLS）：当前与资料库公开页同级——anon 全可读写
-- 升级 Supabase Auth 后：教师角色可写任务/班级/账户，学生仅读写自己的记录
-- =====================================================================
alter table public.prep_tasks        enable row level security;
alter table public.classes           enable row level security;
alter table public.students          enable row level security;
alter table public.learning_records  enable row level security;
alter table public.resources         enable row level security;

create policy "anon_all_prep_tasks"       on public.prep_tasks        for all to anon using (true) with check (true);
create policy "anon_all_classes"          on public.classes           for all to anon using (true) with check (true);
create policy "anon_all_students"         on public.students          for all to anon using (true) with check (true);
create policy "anon_all_learning_records" on public.learning_records  for all to anon using (true) with check (true);
create policy "anon_all_resources"        on public.resources         for all to anon using (true) with check (true);

-- 常用索引
create index if not exists idx_prep_status   on public.prep_tasks("任务状态");
create index if not exists idx_rec_student   on public.learning_records("学生");
create index if not exists idx_rec_next      on public.learning_records("下次复习");
create index if not exists idx_stu_class     on public.students("所属班级");
-- 学号唯一（学生端凭学号登录，防重复身份；学号可空，多个 NULL 在 PG 中不冲突）
create unique index if not exists idx_stu_sid on public.students("学号");
