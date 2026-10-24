# Think F U1-U4 · 网站接线：FOLLOW_VOCAB / FOLLOW_META / LIVE_VOCAB_RE
import json, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
HTML = os.path.join(HERE, "index.html")

# 从归档取 (page, key, n_sent)
info = {}
for f in glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "句级数据_p*.json")):
    d = json.load(open(f, encoding="utf-8"))
    info[d["page"]] = (d["passage_key"], d["n_sent"])

h = open(HTML, encoding="utf-8").read()

# 1) FOLLOW_VOCAB：在 "48": 前插入 16 项（页码→诊断页文件名）
vocab_new = " ".join('"%d": "词汇诊断_%s.html",' % (int(p[1:]), k)
                     for p, (k, _) in sorted(info.items(), key=lambda x: int(x[0][1:])))
anchor_v = '"48": "词汇诊断_u5_p048_robotics_club.html"'
assert anchor_v in h, "FOLLOW_VOCAB 锚点未找到"
h = h.replace(anchor_v, vocab_new + " " + anchor_v, 1)

# 2) FOLLOW_META：在 "48": {...} 前插入 16 项
meta_new = " ".join('"%d": {"q": 0, "s": %d, "v": 1},' % (int(p[1:]), n)
                    for p, (_, n) in sorted(info.items(), key=lambda x: int(x[0][1:])))
anchor_m = '"48": {"q": 0, "s": 22, "v": 1}'
assert anchor_m in h, "FOLLOW_META 锚点未找到"
h = h.replace(anchor_m, meta_new + " " + anchor_m, 1)

# 3) LIVE_VOCAB_RE 扩容至 U1-U12
old_re = "var LIVE_VOCAB_RE = /^u(5|6|7|8|9|10|11|12)_/;"
new_re = "var LIVE_VOCAB_RE = /^u(1|2|3|4|5|6|7|8|9|10|11|12)_/;"
assert old_re in h, "LIVE_VOCAB_RE 旧值未找到"
h = h.replace(old_re, new_re, 1)

# 注释同步
h = h.replace("词汇 = 诊断页已生成的单元（U5–U12 均已产出 词汇诊断/词汇诊断_<key>.html；U5/U6 于 2062d80 补入时漏改本正则，2026-10-24 修复）",
              "词汇 = 诊断页已生成的单元（U1–U12 均已产出 词汇诊断/词汇诊断_<key>.html；U1–U4 于 2026-10-24  analyzer 全链补入）")

open(HTML, "w", encoding="utf-8").write(h)
print("接线完成：FOLLOW_VOCAB +%d 项，FOLLOW_META +%d 项，正则扩至 U1-U12" % (len(info), len(info)))
for p, (k, n) in sorted(info.items(), key=lambda x: int(x[0][1:])):
    print(f"  p{int(p[1:]):03d} → 词汇诊断_{k}.html（{n} 句, v=1）")
