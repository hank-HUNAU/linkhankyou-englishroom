# -*- coding: utf-8 -*-
"""导入 FCE / CAE 考点层词表（剑桥官方不公布，改用 CEFR 分级替代源）。

来源：
  FCE(B2) ← CEFR-J Vocabulary Profile 1.5（Tono Lab, TUFS；免费可商用需引用）
  CAE(C1) ← Octanove Vocabulary Profile C1/C2 v1.0（CC BY-SA 4.0）
用法：python _import_fce_cae.py <cefrj-1.5.csv> <octanove-c1c2.csv> [输出目录]
产出：wordlists/FCE.json（CEFR-J B2）、wordlists/CAE.json（Octanove C1）
"""
import csv, io, os, sys, json

POS_MAP = {
 "noun": "n", "verb": "v", "adjective": "adj", "adverb": "adv", "determiner": "det",
 "preposition": "prep", "conjunction": "conj", "pronoun": "pron", "interjection": "excl",
 "modal verb": "v", "auxiliary verb": "v", "number": "num", "ordinal": "num",
 "article": "det", "possessive": "poss", "predeterminer": "det", "exclamation": "excl",
}

def short_pos(p):
    p = (p or "").strip().lower()
    if p in POS_MAP: return POS_MAP[p]
    return p.split()[0][:4] if p else ""

def read_rows(path):
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def build(rows, level, src, head_col="headword", pos_col="pos", lv_col="CEFR"):
    entries, seen = [], set()
    for r in rows:
        if (r.get(lv_col, "").strip().upper() != level): continue
        head = (r.get(head_col) or "").strip()
        if not head or head.lower() in seen: continue
        seen.add(head.lower())
        pos = short_pos(r.get(pos_col, ""))
        entries.append({"head": head, "pos": pos, "raw": f"{head} ({pos})" if pos else head})
    return {"source": src, "entries": entries, "forms": []}

def main():
    cefrj_csv, oct_csv = sys.argv[1], sys.argv[2]
    outdir = os.path.abspath(sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wordlists"))
    fce = build(read_rows(cefrj_csv), "B2", "CEFR-J Vocabulary Profile 1.5 (B2) · Tono Lab, TUFS")
    cae = build(read_rows(oct_csv), "C1", "Octanove Vocabulary Profile C1/C2 v1.0 (C1) · CC BY-SA 4.0")
    for name, d in [("FCE", fce), ("CAE", cae)]:
        p = os.path.join(outdir, name + ".json")
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[{name}] {len(d['entries'])} 条 ← {d['source']}")

if __name__ == "__main__":
    main()
