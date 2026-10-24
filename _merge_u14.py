# Think F U1-U4 · 归档校验 + 音频入库 + timeline 合入
import json, os, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
AUDIO_BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"
REPO = HERE

UNIT_DIR = {1: "U1_AllTogether", 2: "U2_ImExcited", 3: "U3_FamilyTime", 4: "U4_CityLife"}
AUDIO = {  # page -> (unit, filename)
    "p012": (1, "Thk2e_BE_L0_SB_Unit_1_p12_t01.mp3"), "p015": (1, "Thk2e_BE_L0_SB_Unit_1_p15_t05.mp3"),
    "p016": (1, "Thk2e_BE_L0_SB_Unit_1_p16_t06.mp3"), "p018": (1, "109.mp3"),
    "p020": (2, "Thk2e_BE_L0_SB_Unit_2_p20_t01.mp3"), "p023": (2, "Thk2e_BE_L0_SB_Unit_2_p23_t05.mp3"),
    "p024": (2, "Thk2e_BE_L0_SB_Unit_2_p24_t06.mp3"), "p027": (2, "Thk2e_BE_L0_SB_Unit_2_p27_t07.mp3"),
    "p028": (2, "Thk2e_BE_L0_SB_Unit_2_p28_t08.mp3"),
    "p030": (3, "Unit 03-1 Reading.mp3"), "p033": (3, "Thk2e_BE_L0_SB_Unit_3_p33_t03.mp3"),
    "p034": (3, "Unit_3_p34_t04[reading].mp3"), "p036": (3, "Thk2e_BE_L0_SB_Unit_3_p36_t09.mp3"),
    "p038": (4, "Unit4-p38-reading.mp3"), "p041": (4, "Unit4-p41-listening-ex9.ex10.mp3"),
    "p042": (4, "4-p42-reading-ex1.mp3"), "p043": (4, "4-p43-functions-ex11.mp3"),
    "p045": (4, "4-p45-culture-ex3.mp3"),
}

# （旧误映射 p043 的一次性清理已于 2026-10-24 完成并移除；p043 现为 4.11 functions 篇）

def resolve_audio(unit, fname):
    d = os.path.join(AUDIO_BASE, f"第{unit}单元", f"第{unit}单元 音频")
    p = os.path.join(d, fname)
    if os.path.exists(p):
        return p
    stem, ext = os.path.splitext(fname)
    for suf in ["[公众号happyshare2023]", "[公众号竹清童育]"]:
        q = os.path.join(d, stem + suf + ext)
        if os.path.exists(q):
            return q
    raise FileNotFoundError(fname)

# 1) 校验 16 个归档文件
print("=== 归档校验 ===")
files = []
for u in (1, 2, 3, 4):
    files += sorted(glob.glob(os.path.join(BASE, UNIT_DIR[u], "01_正文篇章", "句级数据_p*.json")))
print(f"归档文件 {len(files)} 个")
ok = True
tot_sent = 0
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    ss = d["sentences"]
    tot_sent += len(ss)
    errs = []
    if d["n_sent"] != len(ss):
        errs.append(f"n_sent={d['n_sent']}!={len(ss)}")
    prev = 0.0
    for s in ss:
        if not (0 <= s["start_s"] < s["end_s"] <= d["duration_s"] + 1.0):
            errs.append(f"句{s['i']}越界")
        if s["start_s"] < prev - 0.05:
            errs.append(f"句{s['i']}重叠")
        prev = s["end_s"]
        if not s["text"].strip():
            errs.append(f"句{s['i']}空文本")
    if errs:
        ok = False
        print(f"  [FAIL] {os.path.basename(f)}: {errs[:3]}")
    else:
        print(f"  [PASS] {os.path.basename(f)} {d['passage_key']} {len(ss)}句")
print(f"总句数 {tot_sent} | 总体: {'PASS' if ok else 'FAIL'}")

# 2) 音频入库 assets/{page}.mp3
print("\n=== 音频入库 ===")
os.makedirs(os.path.join(REPO, "assets"), exist_ok=True)
total_mb = 0
for page, (unit, fname) in sorted(AUDIO.items()):
    src = resolve_audio(unit, fname)
    dst = os.path.join(REPO, "assets", page + ".mp3")
    shutil.copy2(src, dst)
    total_mb += os.path.getsize(dst) / 1048576
print(f"16 个音频已入 assets/，合计 {total_mb:.1f} MB")

# 3) 合入 timeline.json
print("\n=== timeline 合入 ===")
tl_path = os.path.join(REPO, "assets", "timeline.json")
tl = json.load(open(tl_path, encoding="utf-8"))
shutil.copy2(tl_path, tl_path + ".bak_u14")
added = 0
U14_PAGES = set(AUDIO.keys())
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    page = d["page"]
    if page in tl and page not in U14_PAGES:
        print(f"  ! {page} 已存在（非本期范围），跳过")
        continue
    if page in tl:
        print(f"  ~ {page} 覆盖更新")
    tl[page] = [dict(i=s["i"], start_s=s["start_s"], end_s=s["end_s"],
                     dur_s=round(s["end_s"] - s["start_s"], 3), text=s["text"])
                for s in d["sentences"]]
    added += 1
tl.pop("p043", None) if False else None  # p043 现为 4.11 functions 篇，保留
tl = {k: tl[k] for k in sorted(tl, key=lambda x: int(x[1:]))}
json.dump(tl, open(tl_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"新增 {added} 键，timeline 总键数 {len(tl)}")
