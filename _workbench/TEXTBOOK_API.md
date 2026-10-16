# 教材管理 · 数据层接口规格（v1.0，2026-10-17）

> 面向前端教材管理模块的 REST 规格。项目 `think-workbench`，与双工作台 5 表同库。

## 表结构

| 表 | 字段 | 说明 |
|---|---|---|
| `textbooks` | 教材名称*、系列、级别、当前状态、封面链接、备注 | *唯一索引；状态：在用/筹备中/已归档 |
| `textbook_units` | 教材*、单元号、单元主题、备注 | 教材=教材名称（名称引用，与学习记录.学生同风格） |
| `textbook_passages` | 教材*、单元、页码、篇章类型、标题、在线链接、音频链接、数据状态、备注 | 数据状态：已上线/句级对齐中/未录入 |

RLS：anon 全读写（与其余 5 表同级）。索引：units(教材)、passages(教材)、passages(数据状态)、textbooks(教材名称 唯一)。

## REST 示例（apikey 头 = publishable key）

**教材树一次拉取（教材管理主视图）**
```
GET /rest/v1/textbooks?select=*&order=教材名称.asc
GET /rest/v1/textbook_units?select=*&教材=eq.TH!NK F&order=单元号.asc
GET /rest/v1/textbook_passages?select=*&教材=eq.TH!NK F&order=单元号.asc,页码.asc
```

**录入进度看板（哪本教材缺什么）**
```
GET /rest/v1/textbook_passages?select=教材,数据状态,count
  &数据状态=neq.已上线&groupby=教材,数据状态   ← PostgREST 语法，或前端聚合
```

**任务布置联动（推送预习的三级下拉数据源）**
```
GET /rest/v1/textbook_passages?select=教材,单元,页码,标题,在线链接,音频链接
  &教材=eq.TH!NK F&数据状态=eq.已上线&order=单元.asc,页码.asc
```
选中篇章后写 `prep_tasks`：任务标题=标题、单元=单元、任务说明可拼在线链接。

## 导入规约（后续按本导入）

- 单元/篇章一律以「教材名称」挂靠，导入前先 `delete from textbook_units where 教材=eq.X` 清旧（篇章同理），保证幂等重灌
- TH!NK F 篇章 meta 来源：`index.html` PASSAGES + `assets/timeline.json`（篇数/句数核对）
- 每本教材导入后核对：篇数 = 预期篇章数；数据状态逐条确认
