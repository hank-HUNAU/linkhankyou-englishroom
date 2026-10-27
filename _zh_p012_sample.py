# -*- coding: utf-8 -*-
"""p012 样张：按「音译专名 + 自然意译」标准产出 40 句译文
键不手写——从页面 BOOK 的原串按索引取，保证 DB.ZH 逐字命中。
"""
import re, json, os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "篇章页", "读写_012_website.html")
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
KEY, PG = "u1_p12_website", 12

# 逐句译文（索引 = BOOK 展开顺序）
ZH = {
0:  "你叫什么名字？",
1:  "詹奇。",
2:  "你来自哪里？",
3:  "我是土耳其人。我来自一座叫伊兹密尔的城市。",
4:  "你多大了？",
5:  "我十岁。",
6:  "你最喜欢的音乐人是谁？",
7:  "艾德·希兰。他是一名歌手，也会弹吉他。",
8:  "他为什么是你最喜欢的音乐人？",
9:  "因为他太棒了！",
10: "你叫什么名字？",
11: "我叫杰丝。",
12: "你来自哪里？",
13: "我是英国人。我来自纽卡斯尔。",
14: "你多大了？",
15: "我十二岁。",
16: "你最喜欢的音乐人是谁？",
17: "布鲁诺·马尔斯。他是一位来自美国的歌手。",
18: "他为什么是你最喜欢的音乐人？",
19: "因为他超棒的！",
20: "你叫什么名字？",
21: "我是弗拉维娅。",
22: "你来自哪里？",
23: "我来自巴西。我住在福塔莱萨。",
24: "你多大了？",
25: "我十一岁。",
26: "你最喜欢哪些音乐人？",
27: "BLACKPINK。她们是来自韩国的一个女子组合。",
28: "她们为什么是你最喜欢的音乐人？",
29: "因为她们太棒了！",
30: "你叫什么名字？",
31: "我叫李俊。",
32: "你来自哪里？",
33: "我来自印度尼西亚。我住在雅加达。",
34: "你多大了？",
35: "我十一岁。",
36: "你最喜欢的音乐人是谁？",
37: "王羽佳。她是一位来自中国的钢琴家。",
38: "她为什么是你最喜欢的音乐人？",
39: "因为她超酷！",
}

html = open(PAGE, encoding="utf-8").read()
book = json.loads(re.search(r"var BOOK_EXTRA=(\{.*?\});", html, re.S).group(1))[str(PG)]
sents = [s for para in book["arts"] for s in para]
assert len(sents) == len(ZH) == 40, (len(sents), len(ZH))

entries = [{"i": i, "en": sents[i], "zh": ZH[i]} for i in range(40)]
# 去重后的映射（同一英文串只保留一条，译文须一致）
seen, dupdiff = {}, []
for e in entries:
    if e["en"] in seen and seen[e["en"]] != e["zh"]:
        dupdiff.append(e["en"])
    seen[e["en"]] = e["zh"]
assert not dupdiff, "重复英文串译文不一致: %s" % dupdiff

# 1) 正典 JSON
out = os.path.join(BASE, "U1_AllTogether", "01_正文篇章", "译文_p012.json")
json.dump({"passage_key": KEY, "page": "p012", "unit": 1,
           "standard": "音译专名全站统一 + 自然意译；一句一译；键取自 BOOK 原串",
           "n_sent": 40, "n_unique_keys": len(seen),
           "entries": entries},
          open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("正典：", out, "| 句", len(entries), "| 唯一键", len(seen))

# 2) 注入页面 DB.ZH（只放本篇，替换母版那 252 条无关条目）
new_block = "DB.ZH = Object.assign(DB.ZH||{}, " + json.dumps(seen, ensure_ascii=False, separators=(",", ":")) + ");"
pat = re.compile(r"DB\.ZH\s*=\s*Object\.assign\(DB\.ZH\|\|\{\},\s*\{.*?\}\);", re.S)
assert pat.search(html), "页面未找到 DB.ZH 赋值"
html2, n = pat.subn(lambda m: new_block, html, count=1)
open(PAGE, "w", encoding="utf-8", newline="\n").write(html2)
print("注入：替换 DB.ZH 块", n, "处 → 条目", len(seen), "（原母版 252 条已移除）")
