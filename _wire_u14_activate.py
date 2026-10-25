# Think F U1-U4 激活 · PASSAGES 补登 + UNITS 开放
import json, glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
IDX = os.path.join(HERE, "index.html")

KIND = {"阅读A": "阅读 A", "阅读B": "阅读 B", "听力": "听力", "口语": "口语", "文化": "文化"}
INTRO = {
    "u1_p12_website": "网站问答：四位青少年的自我介绍",
    "u1_p15_quiz": "一分钟挑战：广播竞答",
    "u1_p16_tshirt": "T 恤搭话，聊偶像歌手",
    "u1_p18_daniela": "Daniela 从哪儿来",
    "u2_p20_messages": "四条手机短信，各自的兴奋与烦恼",
    "u2_p23_dialogues": "四段邀请与提议对话",
    "u2_p24_birthday": "Ruby 的生日，Ben 记错了日子",
    "u2_p027_masks": "世界各地的面具文化",
    "u3_p30_families": "明星家庭：Emma Watson 与 Chris Hemsworth",
    "u3_p33_family": "三个人聊各自的家庭",
    "u3_p34_photo": "Ellie 的卧室与那张全家合影",
    "u3_p36_photos": "Paul 和 Carla 看照片",
    "u4_p38_brochure": "城市手册：伊斯坦布尔与奈良",
    "u4_p41_directions": "问路与指路",
    "u4_p42_shop": "四段购物对话：买票·运动鞋·土豆·结账",
    "u4_p45_parks": "世界各地的公园",
}

units = {}
for f in sorted(glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "句级数据_p*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    u = int(str(d["unit"]).lstrip("Uu"))
    units.setdefault(u, []).append(d)

def jstr(s):
    return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"

lines = []
for u in sorted(units):
    items = []
    for d in sorted(units[u], key=lambda x: int(x["page"][1:])):
        pg = int(d["page"][1:])
        items.append("{'key':'u%d_%d','p':'%d','kind':%s,'title':%s,'intro':%s,'demo':false}" % (
            u, pg, pg, jstr(KIND.get(d["type"], d["type"])), jstr(d["title"]), jstr(INTRO.get(d["passage_key"], ""))))
    lines.append("Object.assign(PASSAGES, {'%d':[%s]});" % (u, ",".join(items)))

h = open(IDX, encoding="utf-8").read()
anchor = "Object.assign(PASSAGES, {'5':["
assert anchor in h, "U5 PASSAGES 锚点未找到"
h = h.replace(anchor, "\n".join(lines) + "\n" + anchor, 1)

# UNITS：U1-U4 live:false -> true
for n in (1, 2, 3, 4):
    h = re.sub(r"(\{ key:'%d',\s*n:%d,\s*title:[^\n]*?)live:false" % (n, n), r"\1live:true ", h, count=1)

open(IDX, "w", encoding="utf-8", newline="\n").write(h)
print("PASSAGES 补登 4 单元 16 篇；UNITS U1-U4 → live:true")
for l in lines:
    print("  " + l[:120] + "…")
