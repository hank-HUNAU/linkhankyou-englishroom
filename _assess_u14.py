# Think F U1-U4 · 批量九层分析 → 02_词汇数据 归档
import os, re, json, glob, subprocess, sys, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
TXT_DIR = os.path.join(HERE, "词汇诊断", "篇章文本_U1_U4")
# 用户级技能根 = 完整九词表版（A1_Starters/Movers/Flyers 齐全；仓库内技能包是旧副本，缺 YLE 数据）
# U5-U12 的词表即由用户级技能产出，U1-U4 必须同源
SKILL = r"C:\Users\Thinkpad\.workbuddy\skills\article-vocab-analyzer"
ASSESS = os.path.join(SKILL, "scripts", "assess_vocab.py")
CEFR = os.path.join(SKILL, "wordlists", "cefr.json")
PY = sys.executable
TMP = os.path.join(HERE, "_u14_assess_tmp")
UNIT_DIR = {1: "U1_AllTogether", 2: "U2_ImExcited", 3: "U3_FamilyTime", 4: "U4_CityLife"}

# (unit, page) -> passage_key，从归档句级数据反查
key_of = {}
for f in glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "句级数据_p*.json")):
    d = json.load(open(f, encoding="utf-8"))
    key_of[(int(str(d["unit"]).lstrip("Uu")), d["page"])] = d["passage_key"]

os.makedirs(TMP, exist_ok=True)
txts = sorted(glob.glob(os.path.join(TXT_DIR, "*.txt")))
print(f"输入 {len(txts)} 个课文文本")
ok, fail = 0, 0
for t in txts:
    fn = os.path.basename(t)
    m = re.match(r"Unit(\d+)_p?(\d+)_", fn)
    if not m:
        print(f"  [SKIP] {fn} 文件名不符"); fail += 1; continue
    unit, page = int(m.group(1)), "p%03d" % int(m.group(2))
    key = key_of.get((unit, page))
    if not key:
        print(f"  [SKIP] {fn} 无对应归档（U{unit} {page}）"); fail += 1; continue
    out_stem = os.path.join(TMP, key)
    r = subprocess.run([PY, ASSESS, "--file", t, "--out", out_stem, "--cefr", CEFR],
                       capture_output=True, text=True, encoding="utf-8")
    jpath = out_stem + ".json"
    if r.returncode != 0 or not os.path.exists(jpath):
        print(f"  [FAIL] {key}: {(r.stderr or r.stdout)[-200:]}"); fail += 1; continue
    d = json.load(open(jpath, encoding="utf-8"))
    dst_dir = os.path.join(BASE, UNIT_DIR[unit], "02_词汇数据")
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(jpath, os.path.join(dst_dir, key + ".json"))
    n_word = sum(1 for x in d["tokens"] if x["kind"] == "word")
    print(f"  [OK] {key}: total={d['total']} 词条={len(d['tokens'])} word={n_word} proper={d['proper']}")
    ok += 1
shutil.rmtree(TMP, ignore_errors=True)
print(f"\n完成：{ok} 成功 / {fail} 失败")
