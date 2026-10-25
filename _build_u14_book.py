# Think F U1-U4 激活 · 构建 BOOK 条目（段落结构）并合入 _book_extra.json
import json, glob, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
BE_PATH = os.path.join(HERE, "_book_extra.json")

# 段落规格：key -> 每段句数（None = 一句一段，对话框式）
PARA = {
    "u1_p12_website": [10, 10, 10, 10],        # 4 位青少年 × 10 行问答
    "u2_p20_messages": [7, 5, 5, 7],           # 4 条短信（Lizzie/Connor/Gemma/Jud）
    "u2_p027_masks": [4, 5, 4, 3, 5],          # 墨西哥/中国/威尼斯/北美/万圣节
    "u3_p30_families": [9, 10],                # Emma / Chris
    "u4_p38_brochure": [9, 8],                 # 伊斯坦布尔 / 奈良
    "u4_p45_parks": [3, 2, 3, 3, 3, 4],        # 6 座公园
}

be = json.load(open(BE_PATH, encoding="utf-8"))
book = be["book"]
added = []
for f in sorted(glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "句级数据_p*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    pg = int(d["page"][1:])
    key = d["passage_key"]
    sents = [s["text"].strip() for s in d["sentences"]]
    spec = PARA.get(key)
    if spec:
        assert sum(spec) == len(sents), f"{key}: 段落规格 {sum(spec)} != 句数 {len(sents)}"
        arts, i = [], 0
        for n in spec:
            arts.append(sents[i:i + n]); i += n
    else:
        arts = [[s] for s in sents]            # 对话：一句一段（每轮一段）
    unit = int(str(d["unit"]).lstrip("Uu"))
    book[str(pg)] = {
        "u": "Unit %d" % unit,
        "audio": "../assets/p%03d.mp3" % pg,
        "title": d["title"],
        "arts": arts,
    }
    added.append((pg, key, len(sents), len(arts)))

json.dump(be, open(BE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("BOOK 新增/更新 %d 篇（book 总条数 %d）" % (len(added), len(book)))
for pg, key, ns, na in added:
    print(f"  p{pg:03d} {key:24s} {ns:2d} 句 → {na:2d} 段")
