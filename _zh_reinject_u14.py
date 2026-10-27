# -*- coding: utf-8 -*-
"""重建页面后回注 16 篇译文：按 en 精确查旧译文 JSON，缺的用 OVERRIDE 补，再调用 zh_apply 逻辑写回。"""
import json, os, re, glob, subprocess, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
SKILL = r"C:\Users\Thinkpad\.workbuddy\skills\course-sentence-translation\scripts"
PY = sys.executable
UNIT = {"U1_AllTogether": 1, "U2_ImExcited": 2, "U3_FamilyTime": 3, "U4_CityLife": 4}

# 因数据层修复而新增/变更的句子（本轮补译）
OVERRIDE = {
    "u3_p34_photo": {
        "Oh, just a minute, Anna. There’s a nice photograph. Over there, next to the bed.":
            "哦，等一下，安娜。有张好看的照片。就在那儿，床边。",
    },
    "u4_p42_shop": {
        "Hello. How much is a ticket?": "你好。一张票多少钱？",
        "Yes, you’re right. OK, I’ll take them.": "你说得对。好，我买了。",
        "Um, yes. Can I have one, please?": "嗯，要。能给我一个吗？",
        "Sure. Put it in the machine, please. Thank you. OK, bye – have a nice day.":
            "好的。请插到机器里。谢谢。好，再见——祝你今天愉快！",
    },
}

pages = sorted(glob.glob(os.path.join(HERE, "篇章页", "读写_0*.html")))
ok = miss_total = 0
for f in pages:
    html = open(f, encoding="utf-8").read()
    mp = re.search(r"var PG=(\d+);", html)
    mb = re.search(r"var BOOK_EXTRA=(\{.*?\});", html, re.S)
    if not (mp and mb):
        continue
    pg = int(mp.group(1))
    if pg not in (12, 15, 16, 18, 20, 23, 24, 27, 30, 33, 34, 36, 38, 41, 42, 45):
        continue
    book = json.loads(mb.group(1))[str(pg)]
    sents = [s for p in book["arts"] for s in p]
    # 找该篇 key 与旧译文
    key, old, out, unit = None, {}, None, None
    for d in glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "译文_p%03d.json" % pg)):
        j = json.load(open(d, encoding="utf-8"))
        key, unit = j["passage_key"], j.get("unit")
        old = {e["en"]: e["zh"] for e in j["entries"]}
        out = d
    if not key:
        print("缺译文正典：p%03d" % pg)
        continue
    ov = OVERRIDE.get(key, {})
    zh, missing = [], []
    for s in sents:
        v = old.get(s) or ov.get(s)
        if not v:
            missing.append(s)
        zh.append(v or "")
    if missing:
        miss_total += len(missing)
        print("p%03d %s 缺 %d 句：" % (pg, key, len(missing)))
        for m in missing[:3]:
            print("    ", m[:70])
        continue
    tbl = os.path.join(HERE, "_zh_tables", "译文表_p%03d.json" % pg)
    json.dump({"passage_key": key, "page": "p%03d" % pg, "unit": unit, "zh": zh},
              open(tbl, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r = subprocess.run([PY, os.path.join(SKILL, "zh_apply.py"), "--page", f, "--src", tbl, "--out", out],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        ok += 1
        print("  OK p%03d %s（%d 句）" % (pg, key, len(zh)))
    else:
        print("  FAIL p%03d：%s" % (pg, (r.stderr or r.stdout)[-160:]))
print("\n回注：%d 篇成功 / 缺译 %d 句" % (ok, miss_total))
