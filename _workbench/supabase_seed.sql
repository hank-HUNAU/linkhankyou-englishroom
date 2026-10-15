-- =====================================================================
-- TH!NK 双工作台 · Supabase 种子数据（可选，v1.0，2026-10-14）
-- 用途：建表后快速灌入示例班级/学生/任务，用于冒烟验证与演示
-- 执行方式：SQL Editor，在 supabase_schema.sql 运行成功之后再执行
-- 注意：均为示例占位数据，正式启用前可整表清空重建：
--       truncate table public.prep_tasks, public.classes, public.students,
--         public.learning_records, public.resources;
-- =====================================================================

-- 示例班级
insert into public.classes ("班级名称","学段","授课教师","计划人数","班级状态","备注") values
  ('TH!NK Starter A班','Starter','Hank',12,'进行中','示例班级 · 周一/周三 19:00–20:30'),
  ('TH!NK Starter B班','Starter','Hank',12,'进行中','示例班级 · 周二/周四 19:00–20:30');

-- 示例学生（学号唯一；所属班级须与上表班级名称完全一致）
insert into public.students ("姓名","学号","所属班级","账户状态","备注") values
  ('李思远','S2026001','TH!NK Starter A班','在读',''),
  ('王雨桐','S2026002','TH!NK Starter A班','在读',''),
  ('陈嘉禾','S2026003','TH!NK Starter B班','在读',''),
  ('林子墨','S2026004','TH!NK Starter B班','停用','示例：已转线上班');

-- 示例预习任务（推送方式：全班/按班级/按个人；推送对象=班级名或学生名、顿号分隔）
insert into public.prep_tasks
  ("任务标题","单元","内容类型","推送方式","推送对象","任务状态","预计用时","推送时间","截止日期","任务说明") values
  ('Unit 8 · 阅读A《Music in the Forest》精读','Unit 8','阅读','全班','',  '已推送',20,current_date,current_date+1,'点读课文，圈出 5 个生词，跟读 3 遍。'),
  ('Unit 8 · 听力 Musicians around the world','Unit 8','听力','按班级','TH!NK Starter A班','已推送',18,current_date-2,current_date,'精听两遍，写下 3 个听到的乐器名。');

-- 示例学习记录（学生端冒烟：登录 → 预习 → 复习三档会自动写入同类行）
insert into public.learning_records
  ("学生","记录类型","学习内容","单元","用时分钟","正确率","掌握度","复习次数","日期","下次复习") values
  ('李思远','复习','Unit 7 · 阅读A 关键词','Unit 7',10,80,'熟悉',2,current_date-3,current_date),
  ('陈嘉禾','预习','预习：Unit 8 · 阅读B《A teenage DJ》词汇预习','Unit 8',15,90,'熟悉',1,current_date-1,current_date+4);

-- 示例教学资源（链接为纯文本 URL，页面端自动还原为可点链接）
insert into public.resources ("资源名称","类型","单元","标签","链接","上传时间") values
  ('Unit 8 阅读A Music in the Forest 课文音频','音频','Unit 8','阅读A · 精听','https://hank-hunau.github.io/linkhankyou-englishroom/assets/p075.mp3',current_date);
