#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_apply_u14_rerun.py —— 把 _u14_rerun_result.json 双写到归档 + timeline

_RELEASE_WORKFLOW.md 硬规约：
  1) 双写内容一致（归档 01_正文篇章/句级数据_pXXX.json + 仓库 assets/timeline.json）
  2) 音频一个不动（本脚本不触碰任何 mp3）
  3) 文本逐字不变；confidence 不进正典（另存 reports/ 逐句清单）
  4) 改后须跑 node _sync_timeline.js + node _timeline_check.js + npm test

用法：
  .venv-align/Scripts/python.exe _apply_u14_rerun.py --check   # 只报告差异
  .venv-align/Scripts/python.exe _apply_u14_rerun.py           # 执行双写
"""
import argparse
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
RESULT = os.path.join(HERE, "_u14_rerun_result.json")
TIMELINE = os.path.join(HERE, "assets", "timeline.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    R = json.load(io.open(RESULT, encoding="utf-8"))
    tl = json.load(io.open(TIMELINE, encoding="utf-8"))
    changed = []

    for page, r in sorted(R.items()):
        arc = os.path.join(BASE, r["archive"])
        doc = json.load(io.open(arc, encoding="utf-8"))
        old = doc["sentences"]
        rows = r["sentences"]

        # 门禁：句数 / 文本逐字 / 时间轴单调
        assert len(old) == len(rows), "%s 句数不符" % page
        assert all(o["text"] == n["text"] for o, n in zip(old, rows)), \
            "%s 文本被改动" % page
        assert all(rows[i]["start_s"] >= rows[i-1]["end_s"] - 0.001
                   for i in range(1, len(rows))), "%s 时间重叠" % page

        # timeline 里对应条目
        trows = tl.get(page)
        assert trows is not None, "%s 不在 timeline.json" % page
        assert len(trows) == len(rows), "%s timeline 句数不符" % page
        assert all(t["text"] == n["text"] for t, n in zip(trows, rows)), \
            "%s timeline 文本与归档不一致" % page

        moved = [(o["i"], float(o["start_s"]), float(o["end_s"]),
                  n["start_s"], n["end_s"])
                 for o, n in zip(old, rows)
                 if abs(float(o["start_s"]) - n["start_s"]) > 0.01
                 or abs(float(o["end_s"]) - n["end_s"]) > 0.01]
        changed.append((page, len(rows), moved))

        if not args.check:
            # 归档正典：schema 恒为 {i,start_s,end_s,text}
            doc["sentences"] = [
                dict(i=x["i"], start_s=x["start_s"],
                     end_s=x["end_s"], text=x["text"]) for x in rows
            ]
            doc["source"] = (
                "ASR 转写（情况1，无官方稿）× 词级时间戳校准 + 静音吸附"
                "（2026-11-12 拉齐至 U5–U12 主线口径；_align_u14_rerun.py）"
            )
            json.dump(doc, io.open(arc, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

            # timeline：schema 恒为 {i,start_s,end_s,dur_s,text}
            tl[page] = [
                dict(i=x["i"], start_s=x["start_s"], end_s=x["end_s"],
                     dur_s=round(x["end_s"] - x["start_s"], 3),
                     text=x["text"]) for x in rows
            ]

    if not args.check:
        json.dump(tl, io.open(TIMELINE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)

    print("=== %s ===" % ("DRY CHECK" if args.check else "双写完成"))
    for page, n, moved in changed:
        print("  %s  %d 句  时间轴变动 %d 句" % (page, n, len(moved)))
        for i, os_, oe, ns, ne in moved[:6]:
            print("    句%2d  %.2f–%.2f → %.2f–%.2f" % (i, os_, oe, ns, ne))
    print("\n文本逐字守恒 ✓ · 音频未触碰 ✓ · confidence 未写入正典 ✓")
    if not args.check:
        print("\n下一步：node _sync_timeline.js && node _timeline_check.js && npm test")


if __name__ == "__main__":
    main()
