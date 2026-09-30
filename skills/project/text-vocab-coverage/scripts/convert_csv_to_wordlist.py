#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 Newman/NGSL 这类 "lemmatized for teaching" CSV 词表转成技能统一 JSON 格式.
CSV 规格: 每行一个词族 = 逗号分隔(首字段为 headword, 其余为屈折形式; 允许空列占位与 '##' 注释行)。
输出: {"label":..., "entries":[{"head","pos","raw","forms"}]}
用法:
  python convert_csv_to_wordlist.py NGSL.csv NGSL.json --label "NGSL(New General Service List)"
"""
import io, json, os, argparse

def convert(csv_path, label):
    raw_b = open(csv_path, "rb").read()
    text = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = raw_b.decode(enc); break
        except UnicodeDecodeError:
            pass
    entries = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", "##")):
            continue
        cells = [c.strip() for c in line.split(",")]
        cells = [c for c in cells if c]
        if not cells:
            continue
        entries.append({"head": cells[0], "pos": "", "raw": line, "forms": cells})
    return {"label": label, "entries": entries}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv"); ap.add_argument("out")
    ap.add_argument("--label", default=None)
    ap.add_argument("--key", default=None)   # 可选: 一并写 registry 用, 若只转文件则略
    a = ap.parse_args()
    label = a.label or os.path.splitext(os.path.basename(a.csv))[0]
    d = convert(a.csv, label)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=0)
    # 统计词族/总形式/短语
    words = set(); phrs = set()
    for e in d["entries"]:
        for f in e["forms"]:
            (phrs if " " in f else words).add(f)
    print("saved:", a.out)
    print("词族=%d 词形=%d 短语=%d 样例=%s" % (len(d["entries"]), len(words) + len(phrs), len(phrs),
          ", ".join(list(words)[:5])))

if __name__ == "__main__":
    main()