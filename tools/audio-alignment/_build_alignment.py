# -*- coding: utf-8 -*-
"""教师用书栏目标题 ↔ 音频对齐：构建模型 _alignment.json"""
import os, re, json, glob
from collections import defaultdict

base = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"
durs = json.load(open("_durations.json"))
tb = json.load(open("_tb_refs.json", encoding="utf-8"))["tbout"]
pat = re.compile(r"Thk2e_BE_L0_(SB|WB)_Unit_(\d+|W)_p(\d+)_t(\d+)")

SECS = ["READING", "LISTENING", "SPEAKING", "VOCABULARY", "GRAMMAR", "CULTURE", "WRITING", "PRONUNCIATION"]

# 每本教师用书的 spread 页码 + 顺序栏目
fileinfo = {}
for t0 in tb:
    t = open(os.path.join("_tb_cache", t0["file"] + ".txt"), encoding="utf-8").read()
    marks = []
    for line in t.split("\n"):
        ls = line.strip()
        if 3 < len(ls) < 40 and ls.upper() == ls and re.search(r"[A-Z]{4,}", ls):
            for s in SECS:
                if ls.startswith(s):
                    marks.append(s)
                    break
    # 去重保序
    seen = []
    for s in marks:
        if s not in seen:
            seen.append(s)
    fileinfo[t0["file"]] = dict(unit=t0["unit"], pages=t0["pages"], secs=seen)

# (unit,track) -> 引用信息（轨号自带单元前缀，支持 Unit N&M 多单元册）
refmap = {}
for t0 in tb:
    t = open(os.path.join("_tb_cache", t0["file"] + ".txt"), encoding="utf-8").read()
    nm = re.match(r"Unit (\d+)(&(\d+))?", t0["file"])
    if "Welcome" in t0["file"]:
        cands = {"W"}
    elif nm:
        cands = {nm.group(1)}
        if nm.group(3):
            cands.add(nm.group(3))
    else:
        continue
    for m in re.finditer(r"(?:^|\s|\()(\d{1,2}|W)\.(\d{2})\b\s*(.{0,80})", t):
        pu, tr, ctx = m.group(1), int(m.group(2)), re.sub(r"\s+", " ", m.group(3))
        if pu not in cands or not (1 <= tr <= 20):
            continue
        refmap.setdefault((pu, tr), dict(
            sec="", ex="", ctx=ctx,
            lesson=t0["file"].replace("_教师用书", ""), pages=t0["pages"]))
# 补充栏目标题/练习号：用原 tbout 里同一文件的逐条信息
for t0 in tb:
    if not t0["unit"]:
        continue
    for r in t0["refs"]:
        k = (t0["unit"], r["tr"])
        if k in refmap and not refmap[k]["sec"]:
            refmap[k].update(sec=r["sec"], ex=r["ex"], ctx=r["ctx"] or refmap[k]["ctx"])

# 改名文件别名表（依据诊断逐一核对）
ALIAS = {
    "109.mp3": ("1", 9, "文件名=单元1轨09"),
    "903.mp3": ("9", 3, "文件名=单元9轨03"),
    "905.mp3": ("9", 5, "文件名=单元9轨05"),
    "Unit 03-1 Reading.mp3": ("3", 1, "第1次课 Reading"),
    "Unit_3_p34_t04[reading].mp3": ("3", 4, "p34 Reading"),
    "Unit4-p38-reading.mp3": ("4", 1, "p38 Reading"),
    "Unit4-p41-listening-ex9.ex10.mp3": ("4", 3, "p41 ex9-10 发音"),
    "4-p42-reading-ex1.mp3": ("4", 4, "p42 Reading ex1"),
    "4-p43-functions-ex11.mp3": ("4", 11, "p43 ex11"),
    "4-p45-culture-ex3.mp3": ("4", 12, "p45 ex3 推断"),
    "第8单元 阅读1 Music in the Forest 课文音频.mp3": ("8", 1, "第1次课 Reading"),
    "第9单元 第1次课 篇章阅读 音频.mp3": ("9", 1, "第1次课 Reading"),
}

units = defaultdict(lambda: defaultdict(list))

def ulabel(u):
    return "Welcome（第0单元）" if u == "W" else ("Unit " + u if u != "?" else "未归类")

def ukey(u):
    return -1 if u == "W" else (999 if u == "?" else int(u))

std = defaultdict(list)
for p in durs:
    m = pat.search(os.path.basename(p))
    if m and m.group(1) == "SB":
        std[m.group(2)].append((int(m.group(3)), int(m.group(4)), p))

used_alias = set()

# 1) 标准 SB 轨
for u, trks in std.items():
    for pg, tr, p in sorted(trks):
        k = (u, tr)
        if k in refmap:
            r = refmap[k]
            units[u]["sb"].append(dict(pg=pg, tr=tr, sec=r["sec"], ex=r["ex"], ctx=r["ctx"],
                                       f=os.path.basename(p), path=p, dur=durs[p], st="exact"))
        else:
            lesson = ""
            secs = []
            for fn, fi in fileinfo.items():
                if fi["unit"] == u and fi["pages"] and pg and min(fi["pages"]) <= pg <= max(fi["pages"]):
                    lesson = fn.replace("_教师用书", "")
                    secs = fi["secs"]
                    break
            units[u]["sb"].append(dict(pg=pg, tr=tr, sec=" / ".join(secs), ex="", ctx="",
                                       f=os.path.basename(p), path=p, dur=durs[p], st="inferred",
                                       note=lesson))

# 2) TB 引用但标准文件缺失 → 找改名别名
for (u, tr), r in refmap.items():
    if u in std and any(t == tr for _, t, _ in std[u]):
        continue  # 标准文件已存在，第一步已处理
    hit = None
    note = ""
    for b, (au, atr, nt) in ALIAS.items():
        if au == u and atr == tr:
            hit = b
            note = nt
            used_alias.add(b)
            break
    if hit:
        pth = None
        for dirpath, dirs, files in os.walk(base):
            if hit in files:
                pth = os.path.join(dirpath, hit)
                break
        units[u]["sb"].append(dict(pg="", tr=tr, sec=r["sec"], ex=r["ex"], ctx=r["ctx"],
                                   f=hit, path=pth, dur=durs.get(pth), st="alias", note=note))
    else:
        units[u]["miss"].append(dict(tr=tr, sec=r["sec"], ex=r["ex"], ctx=r["ctx"],
                                     lesson=r["lesson"], pages=r["pages"]))

# 3) 其余文件：WB / 技能 / 视频音轨 / 其他
for p in durs:
    b = os.path.basename(p)
    m = pat.search(b)
    if m and m.group(1) == "SB":
        continue
    if b in used_alias:
        continue
    rel = os.path.relpath(p, base)
    um = re.search(r"第(\d+)单元", rel)
    if m and m.group(1) == "WB":
        units[m.group(2)]["wb"].append(dict(pg=int(m.group(3)), tr=int(m.group(4)),
                                            f=b, path=p, dur=durs[p]))
        continue
    u = um.group(1) if um else "?"
    if "技能" in b or "测试" in rel:
        bucket = "skill"
    elif ("纪录片" in b) or ("Rap" in b) or ("Culture.mp3" in b):
        bucket = "video"
    else:
        bucket = "other"
    units[u][bucket].append(dict(f=b, path=p, dur=durs[p]))

out = {u: {k: v for k, v in d0.items()} for u, d0 in units.items()}
json.dump(out, open("_alignment.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

for u in sorted(units, key=ukey):
    d0 = units[u]
    print(ulabel(u), "| SB:", len(d0["sb"]), "| WB:", len(d0["wb"]), "| 缺:",
          len(d0["miss"]), "| 技能:", len(d0["skill"]), "| 视频:", len(d0["video"]),
          "| 其他:", len(d0["other"]))
    for r0 in d0["sb"]:
        if r0["st"] != "exact":
            tag = ("p%st%02d" % (r0["pg"], r0["tr"])) if r0["pg"] else ("t%02d" % r0["tr"])
            print("   ", r0["st"], tag, r0.get("note", ""), r0["sec"][:34])
    for m0 in d0["miss"]:
        print("    MISSING", u + "." + str(m0["tr"]).zfill(2), m0["lesson"][:32], m0["sec"], m0["ctx"][:40])
