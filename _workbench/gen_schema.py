# -*- coding: utf-8 -*-
"""生成两个工作台页面的合并 schema（供 SDK lint）与 canonical schema（供 schema lint）。"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

def sel(name):  # 展示/表单 selector（形态合法即可，R10 不启用）
    return '[data-field="%s"]' % name

OPTS = {
    "内容类型": ["词汇", "阅读", "听力", "口语", "语法", "文化"],
    "推送班级": ["全班", "A组", "B组"],
    "推送方式": ["全班", "按班级", "按个人"],
    "任务状态": ["已推送", "已撤回"],
    "记录类型": ["预习", "复习", "跟读", "听写", "测验"],
    "掌握度": ["陌生", "模糊", "熟悉", "掌握"],
    "类型": ["音频", "视频", "PDF讲义", "词汇表", "练习题", "图片"],
    "班级状态": ["进行中", "筹备中", "已结课"],
    "账户状态": ["在读", "停用"],
}

PREP = ["任务标题", "单元", "内容类型", "推送班级", "推送方式", "推送对象", "任务状态", "预计用时", "推送时间", "修改时间", "截止日期", "任务说明"]
REC = ["学生", "记录类型", "学习内容", "单元", "用时分钟", "正确率", "掌握度", "复习次数", "日期", "下次复习", "备注"]
RES = ["资源名称", "类型", "单元", "标签", "链接", "上传时间"]
CLASS = ["班级名称", "学段", "授课教师", "计划人数", "班级状态", "创建时间", "备注"]
ACCT = ["姓名", "学号", "所属班级", "账户状态", "加入时间", "备注"]

WRITE_FIELDS = {"学生", "记录类型", "学习内容", "单元", "用时分钟", "掌握度", "复习次数", "日期", "下次复习",
                "任务标题", "推送班级", "推送方式", "推送对象", "任务状态", "预计用时", "推送时间", "修改时间", "截止日期", "任务说明",
                "资源名称", "类型", "标签", "链接", "上传时间",
                "班级名称", "学段", "授课教师", "计划人数", "班级状态", "创建时间",
                "姓名", "学号", "所属班级", "账户状态", "加入时间"}


def prop_config(name):
    if name in OPTS:
        return {"select": {"options": [{"text": t, "id": "opt-%s-%d" % (name, i)} for i, t in enumerate(OPTS[name])]}}
    if name in ("预计用时", "用时分钟", "正确率", "复习次数", "计划人数"):
        return {"number": {"decimalPlaces": 0, "useSeparate": False}}
    if name in ("推送时间", "修改时间", "截止日期", "日期", "下次复习", "上传时间", "创建时间", "加入时间"):
        return {"date": "yyyy-mm-dd"}
    if name == "链接":
        return {"url": {"text": "", "link": ""}}
    return {"text": ""}


def value_type(cfg):
    return list(cfg.keys())[0]


def canonical(title, fields, dbs):
    properties, field_mapping, options_map = {}, {}, {}
    for f in fields:
        cfg = prop_config(f)
        properties[f] = cfg
        vt = value_type(cfg)
        entry = {
            "value_type": vt,
            "form_input": ('[name="%s"]' % f) if f in WRITE_FIELDS else None,
            "display_selector": sel(f),
            "render_signal": "label:contains('%s')" % f,
        }
        if vt in ("select", "multi_select"):
            entry["options_value_key"] = "value"
            options_map[f] = {o["id"]: {"text": o["text"], "id": o["id"]} for o in cfg["select"]["options"]}
        field_mapping[f] = entry
    return {"title": title, "page_type": "mixed", "properties": properties,
            "field_mapping": field_mapping, "options_map": options_map,
            "source": "agent_analysis", "sdk_calls_found": True,
            "existing_databases": dbs, "confidence": "high"}


def merged(fields):
    seen, out = set(), {}
    for f in fields:
        if f in seen:
            continue
        seen.add(f)
        out[f] = {}
    return {"properties": out}


student_fields = PREP + REC + ACCT
teacher_fields = PREP + RES + CLASS + ACCT + REC

DB_PREP = "M2BiG1J9hhkYDOcdZFWi3s"
DB_REC = "qKJybtlu4NrEqJ7yUPTduo"
DB_RES = "iRti0RoXNhXFoekVY9y4Cf"
DB_CLASS = "PUQ5oUZJNDYWKBBMpIijgw"
DB_ACCT = "2OjdhXTwUccUa71i4R2wBx"

jobs = [
    ("merged_student.json", merged(student_fields)),
    ("canon_student.json", canonical("学生学习工作台", student_fields, [DB_PREP, DB_REC, DB_ACCT])),
    ("merged_teacher.json", merged(teacher_fields)),
    ("canon_teacher.json", canonical("教师教学工作台", teacher_fields, [DB_PREP, DB_RES, DB_CLASS, DB_ACCT, DB_REC])),
]
for fn, obj in jobs:
    with open(os.path.join(HERE, fn), "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    print("wrote", fn)
