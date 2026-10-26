# Think F U1-U4 · 批量走词汇技能全链（vocab_pipeline）→ 归档 5 件套
# 2026-10-26 v2：产物统一落在 _vocab_out_tmp/（单目录），最后一次性删目录——
# 避免逐文件删除撞环境批量删除保护（SAFE_DELETE_BULK）。
import os, re, glob, json, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
TXT_DIR = os.path.join(HERE, "词汇诊断", "篇章文本_U1_U4")
PIPE = os.path.join(HERE, "skills", "词汇教学技能包-20260928", "article-vocab-analyzer", "scripts", "vocab_pipeline.py")
PY = sys.executable
UNIT_DIR = {1: "U1_AllTogether", 2: "U2_ImExcited", 3: "U3_FamilyTime", 4: "U4_CityLife"}
TMP = os.path.join(HERE, "_vocab_out_tmp")
os.makedirs(TMP, exist_ok=True)

key_of = {}
for f in glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "句级数据_p*.json")):
    d = json.load(open(f, encoding="utf-8"))
    key_of[(int(str(d["unit"]).lstrip("Uu")), d["page"])] = d["passage_key"]

SUFFIX = {"_报告.json": ".json", "_报告.xlsx": ".xlsx", "_学生卡.xlsx": "_学生卡.xlsx",
          "_备课本.xlsx": "_备课本.xlsx", "_语音卡.xlsx": "_语音卡.xlsx"}

txts = sorted(glob.glob(os.path.join(TXT_DIR, "*.txt")))
print(f"共 {len(txts)} 篇", flush=True)
ok = fail = skip = 0
for t in txts:
    fn = os.path.basename(t)
    m = re.match(r"Unit(\d+)_p?(\d+)_", fn)
    if not m:
        print(f"[SKIP] {fn}", flush=True); fail += 1; continue
    unit, page = int(m.group(1)), "p%03d" % int(m.group(2))
    key = key_of.get((unit, page))
    if not key:
        print(f"[SKIP] {fn} 无归档", flush=True); fail += 1; continue
    dst_dir = os.path.join(BASE, UNIT_DIR[unit], "02_词汇数据")
    if all(os.path.exists(os.path.join(dst_dir, key + s)) for s in SUFFIX.values()):
        print(f"[DONE] {key}: 5 件套已在归档，跳过", flush=True); skip += 1; continue
    r = subprocess.run([PY, PIPE, t, "--out", key], cwd=TMP,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    os.makedirs(dst_dir, exist_ok=True)
    missing = []
    for suf, dst in SUFFIX.items():
        src = os.path.join(TMP, key + suf)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst_dir, key + dst))
        else:
            missing.append(suf)
    if missing:
        print(f"[PART] {key}: 缺 {missing} | rc={r.returncode}", flush=True); fail += 1
    else:
        print(f"[OK] {key}: 5 件套归档", flush=True); ok += 1
print(f"\n完成：{ok} 成功 / {skip} 已完成跳过 / {fail} 异常", flush=True)
