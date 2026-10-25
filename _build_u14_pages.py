# Think F U1-U4 · 用库内补丁终态页（p048）作母版产出 16 个篇章页
# 背景：_gen_follow_v2.py 直出会被打回未补丁态（aplay 自递归 / 无 SRT 回退），
#       库内 33 页是「生成器 + 补丁」终态；新页必须沿用终态母版。
import re, os, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
OUT = os.path.join(HERE, "篇章页")
MASTER = os.path.join(OUT, "读写_048_robotics_club.html")

master = open(MASTER, encoding="utf-8").read()
be = json.load(open(os.path.join(HERE, "_book_extra.json"), encoding="utf-8"))["book"]
KEYS = {"u1_p12_website": (1, 12), "u1_p15_quiz": (1, 15), "u1_p16_tshirt": (1, 16), "u1_p18_daniela": (1, 18),
        "u2_p20_messages": (2, 20), "u2_p23_dialogues": (2, 23), "u2_p24_birthday": (2, 24), "u2_p027_masks": (2, 27),
        "u3_p30_families": (3, 30), "u3_p33_family": (3, 33), "u3_p34_photo": (3, 34), "u3_p36_photos": (3, 36),
        "u4_p38_brochure": (4, 38), "u4_p41_directions": (4, 41), "u4_p42_shop": (4, 42), "u4_p45_parks": (4, 45)}
SLUG = {"u1_p12_website": "website", "u1_p15_quiz": "quiz", "u1_p16_tshirt": "tshirt", "u1_p18_daniela": "daniela",
        "u2_p20_messages": "messages", "u2_p23_dialogues": "dialogues", "u2_p24_birthday": "birthday",
        "u2_p027_masks": "masks", "u3_p30_families": "families", "u3_p33_family": "family",
        "u3_p34_photo": "photo", "u3_p36_photos": "photos", "u4_p38_brochure": "brochure",
        "u4_p41_directions": "directions", "u4_p42_shop": "shop", "u4_p45_parks": "parks"}

# 归档句级数据 → TL
tl_map = {}
for f in glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "句级数据_p*.json")):
    d = json.load(open(f, encoding="utf-8"))
    tl_map[d["passage_key"]] = [[s["start_s"], s["end_s"]] for s in d["sentences"]]

made = []
for key, (unit, pg) in KEYS.items():
    tl = tl_map[key]
    assert len(tl) == len([s for para in be[str(pg)]["arts"] for s in para]), key
    html = master
    html = html.replace("课文 p048", "课文 p%03d" % pg)
    html = re.sub(r"var PG=48;", "var PG=%d;" % pg, html)
    # TL：母版为 SRT 派生单行；换成该篇 [[start,end],...]
    html = re.sub(r"DB\.TL=\{.*?\};",
                  "DB.TL=" + json.dumps({str(pg): tl}, ensure_ascii=False, separators=(",", ":")) + ";",
                  html, count=1, flags=re.S)
    # BOOK_EXTRA：两处声明都要换（第二处覆盖第一处）
    be_one = json.dumps({str(pg): be[str(pg)]}, ensure_ascii=False, separators=(",", ":"))
    n = len(re.findall(r"var BOOK_EXTRA=\{.*?\};", html, flags=re.S))
    assert n in (1, 2), "BOOK_EXTRA 声明数异常: %d" % n
    html = re.sub(r"var BOOK_EXTRA=\{.*?\};", "var BOOK_EXTRA=" + be_one + ";", html, flags=re.S)
    name = "读写_%03d_%s.html" % (pg, SLUG[key])
    open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n").write(html)
    made.append((pg, name, len(tl), n))
    print(f"  p{pg:03d} → {name}（{len(tl)} 句, BOOK_EXTRA×{n}）")
print(f"\n共 {len(made)} 页 → {OUT}")
