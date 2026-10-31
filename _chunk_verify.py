#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_chunk_verify.py —— 语块数据校验

1) **verbatim 命中**：每条语块必须在它标注的句子里按子串出现（归一化后）——防「模型臆造语块」
2) **释义完整**：zh 必须含中文，且不能整条是英文
3) **双写一致**（仅当页面内嵌 CHUNKS 时才检查）：2026-10-31 起语块**不上线**，
   正典只存归档 `语块_pXXX.json`，由 `_gen_teacher_pack.py` 生成教师讲解卡/学生发放页；
   页面无 CHUNKS 属**预期状态**，不是「未接线」。若未来恢复上线，本检查自动恢复效力。

用法：
  python _chunk_verify.py                      # 校验全部已归档语块
  python _chunk_verify.py --page p048
"""
import argparse
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))


def norm(s):
    s = (s or "").replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s.lower())
    return s.strip()


def page_chunks(page):
    """从篇章页取出内嵌 CHUNKS 对象（括号配对，字符串感知）"""
    num = page.lstrip("pP")
    hits = glob.glob(os.path.join(HERE, "篇章页", "读写_%s_*.html" % num))
    if not hits:
        return None, None
    src = open(hits[0], encoding="utf-8").read()
    m = re.search(r"var CHUNKS\s*=", src)
    if not m:
        return hits[0], None
    i = src.index("{", m.end())
    depth, j, instr, esc = 0, i, False, False
    while j < len(src):
        c = src[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
        j += 1
    try:
        return hits[0], json.loads(src[i:j + 1])
    except Exception as e:
        return hits[0], dict(_error=str(e), raw=src[i:j + 1][:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default=None)
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(BASE, "U[0-9]*_*", "02_词汇数据", "语块_p*.json")))
    if args.page:
        files = [f for f in files if args.page in os.path.basename(f)]
    if not files:
        sys.exit("没有找到语块 JSON")

    bad = 0
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        page = d["page"]
        unit = d["unit"]
        ud = [p for p in glob.glob(os.path.join(BASE, "U%d_*" % unit))][0]
        sents = json.load(open(os.path.join(ud, "01_正文篇章", "句级数据_%s.json" % page),
                               encoding="utf-8"))["sentences"]
        print("\n== %s %s｜%d 条 ==" % (page, d.get("key"), len(d["chunks"])))
        for c in d["chunks"]:
            si = c["sent"] - 1
            sent_n = norm(sents[si]["text"]) if 0 <= si < len(sents) else ""
            ok_v = norm(c["text"]) in sent_n
            ok_z = bool(re.search(r"[\u4e00-\u9fff]", c.get("zh") or "")) and \
                len(re.findall(r"[A-Za-z]", c.get("zh") or "")) <= len(c.get("zh") or "") / 2
            flag = "✓" if (ok_v and ok_z) else "✗"
            if not (ok_v and ok_z):
                bad += 1
            print("  %s %-18s 句%-3d verbatim=%s zh=%s" % (
                flag, c["text"][:18], c["sent"], "OK" if ok_v else "MISS", "OK" if ok_z else "BAD"))
            if not ok_v:
                print("      源句：%s" % sents[si]["text"][:90] if 0 <= si < len(sents) else "      句号越界")

        # 双写一致性（仅当页面内嵌 CHUNKS；2026-10-31 起不上线，页面无 CHUNKS 属预期）
        html, emb = page_chunks(page)
        if emb is None:
            print("  语块不上线（本地资源模式），页面无 CHUNKS —— 符合预期")
            continue
        if "_error" in emb:
            print("  ✗ 页面 CHUNKS 解析失败：%s" % emb["_error"]); bad += 1; continue
        a = [(c["text"], c["sent"], c["zh"]) for c in d["chunks"]]
        b = [(c["text"], c["sent"], c["zh"]) for c in emb.get("chunks", [])]
        if a == b:
            print("  双写一致 ✓（页面 %s）" % os.path.basename(html))
        else:
            bad += 1
            print("  ✗ 双写不一致：归档 %d 条 vs 页面 %d 条" % (len(a), len(b)))
            for x, y in zip(a, b):
                if x != y:
                    print("      归档：%s\n      页面：%s" % (x, y))
    print("\n结论：%s（异常 %d）" % ("全部通过" if not bad else "有异常", bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
