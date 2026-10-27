# -*- coding: utf-8 -*-
"""_zh_batch.py —— 多篇译文一次落库并质检
用法：python _zh_batch.py 批次表.json
批次表 = {"passages": [{"page":"p048","key":"u5_48","unit":5,"zh":[...]}, ...]}
自动解析：篇章页 HTML、归档路径（Ux_*/01_正文篇章/译文_pXXX.json），然后跑 zh_apply + zh_check + zh_r3。
"""
import json, os, re, glob, subprocess, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))
SKILL = r"C:\Users\Thinkpad\.workbuddy\skills\course-sentence-translation\scripts"
PY = sys.executable


def find_unit_dir(unit):
    hits = sorted(glob.glob(os.path.join(BASE, "U%d_*" % unit)))
    return hits[0] if hits else None


def main():
    batch = json.load(open(sys.argv[1], encoding="utf-8"))
    ok = bad = 0
    for p in batch["passages"]:
        pg, key, unit, zh = p["page"], p["key"], p.get("unit"), p["zh"]
        num = pg.lstrip("pP")                                   # 页面名用纯数字：读写_048_*.html
        pages = glob.glob(os.path.join(HERE, "篇章页", "读写_%s_*.html" % num))
        if not pages:
            print("✗ %s 找不到篇章页" % pg); bad += 1; continue
        ud = find_unit_dir(unit) if unit else None
        out = os.path.join(ud, "01_正文篇章", "译文_%s.json" % pg) if ud else os.path.join(HERE, "译文_%s.json" % pg)
        tbl = os.path.join(HERE, "_zh_tables", "译文表_%s.json" % pg)
        os.makedirs(os.path.dirname(tbl), exist_ok=True)
        json.dump({"passage_key": key, "page": pg, "unit": unit, "zh": zh},
                  open(tbl, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        r = subprocess.run([PY, os.path.join(SKILL, "zh_apply.py"), "--page", pages[0],
                            "--src", tbl, "--out", out],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print("✗ %s apply 失败：%s" % (pg, (r.stderr or r.stdout)[-140:])); bad += 1; continue
        c = subprocess.run([PY, os.path.join(SKILL, "zh_check.py"), "--page", pages[0], "--json", out],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        r3 = subprocess.run([PY, os.path.join(SKILL, "zh_r3.py"), "--page", pages[0]],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
        c_ok = "结论：通过" in c.stdout
        r3_ok = r3.returncode == 0
        flag = "✓" if (c_ok and r3_ok) else "!"
        print("%s %s %-18s %s | R2 %s · R3 %s" % (
            flag, pg, key, r.stdout.strip().split("：", 1)[-1][:34],
            "OK" if c_ok else "FAIL", "OK" if r3_ok else "疑点"))
        if not c_ok:
            for line in c.stdout.splitlines():
                if line.startswith(("FAIL", "R2-2", "R2-3", "R2-4")):
                    print("    " + line[:110])
        if not r3_ok:
            for line in r3.stdout.splitlines()[1:4]:
                print("    " + line[:110])
        ok += (c_ok and r3_ok); bad += (not (c_ok and r3_ok))
    print("\n批次结果：通过 %d / 异常 %d" % (ok, bad))


if __name__ == "__main__":
    main()
