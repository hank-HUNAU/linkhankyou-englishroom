import json, glob, os
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
rows = {}
for f in sorted(glob.glob(os.path.join(BASE, "U*", "01_正文篇章", "句级数据_p*.json"))):
    d = json.load(open(f, encoding="utf-8"))
    u = int(str(d["unit"]).lstrip("Uu"))
    rows.setdefault(u, []).append((d["type"], d["title"], d["page"]))
print("ZWK = {")
for u in sorted(rows):
    items = " ".join(f'("{t}","{ti}","{p}","{p}"),' for t, ti, p in sorted(rows[u], key=lambda x: int(x[2][1:])))
    print(f' {u}:[{items}],')
print("}")
