#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_apply_p052_fix.py —— p052「评分结果段音频未朗读」处置方案 A（用户 2026-11-14 拍板）

从正典中删掉课本印刷但**音频未朗读**的 3 行评分结果（i=5/6/7），使归档/timeline/字幕/
译文/页面段落结构与音频一致。全站句数 1141 → 1138（48 篇 1118 → 1115）。

    .venv-align/Scripts/python.exe _apply_p052_fix.py --dry-run   # 只预览将改哪些文件
    .venv-align/Scripts/python.exe _apply_p052_fix.py --apply      # 备份 + 执行 + 自检

**不改**：音频（md5 前后断言）、教师用书/课本原文 txt、TAA 旧工具产物（`p052.taa.*`、
`_taa_work/*`）、语块总表（篇章级引用，待 #51 规约合并后统一重算）、历史诊断报告。
改完必须外部再跑：node _sync_timeline.js → node _timeline_check.js → npm test。
"""
import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)  # Think F 教材资产/
MEM = os.path.join(os.path.dirname(BASE), ".workbuddy", "memory", "2026-11-14")

PAGE = "p052"
KEEP = 5
CUT_TEXTS = [
    "5 to 9 – No, you don't need a break! You use it well.",
    "10 to 12 – You're not too bad, but be careful!",
    "13 to 15 – Yes, you do. You need a break from tech! Do something different!",
]

F = {
    "timeline": os.path.join(HERE, "assets", "timeline.json"),
    "srt": os.path.join(HERE, "assets", "subtitles", "p052.srt"),
    "lrc": os.path.join(HERE, "assets", "subtitles", "p052.lrc"),
    "index": os.path.join(HERE, "index.html"),
    "book_extra": os.path.join(HERE, "_book_extra.json"),
    "integrate": os.path.join(HERE, "_integrate_u56.js"),
    "source": os.path.join(HERE, "_unit_5_source.json"),
    "unit_tl_json": os.path.join(HERE, "_unit_5_timeline.json"),
    "unit_tl_txt": os.path.join(HERE, "_unit_5_timeline.txt"),
    "zh_table": os.path.join(HERE, "_zh_tables", "译文表_p052.json"),
    "archive_sent": os.path.join(BASE, "U5_FreeTime", "01_正文篇章", "句级数据_p052.json"),
    "archive_zh": os.path.join(BASE, "U5_FreeTime", "01_正文篇章", "译文_p052.json"),
    "archive_srt": os.path.join(BASE, "U5_FreeTime", "01_正文篇章", "p052.srt"),
    "archive_lrc": os.path.join(BASE, "U5_FreeTime", "01_正文篇章", "p052.lrc"),
}


def jload(p):
    return json.load(io.open(p, encoding="utf-8"))


def text(p):
    # newline="" 保留原始 CRLF/LF，避免批量改页时产生整文件换行 diff
    return io.open(p, encoding="utf-8", newline="").read()


def put(p, s):
    """写回时沿用该文件原有的换行风格（CRLF / LF），避免整文件 diff。"""
    crlf = b"\r\n" in open(p, "rb").read()
    s = s.replace("\r\n", "\n")
    if crlf:
        s = s.replace("\n", "\r\n")
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def jdump(p, d, indent=1):
    put(p, json.dumps(d, ensure_ascii=False, indent=indent) + "\n")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def ts_srt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def ts_lrc(t):
    m = int(t // 60)
    s = t - m * 60
    return "[%02d:%05.2f]" % (m, s)


def make_srt(rows):
    out = []
    for i, r in enumerate(rows, 1):
        out.append("%d\n%s --> %s\n%s\n" % (
            i, ts_srt(r["start_s"]), ts_srt(r["end_s"]), r["text"]))
    return "\n".join(out)


def make_lrc(rows):
    return "\n".join(ts_lrc(r["start_s"]) + r["text"] for r in rows) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.dry_run or args.apply):
        sys.exit("请指定 --dry-run 或 --apply")

    tl = jload(F["timeline"])
    rows = tl[PAGE]
    assert len(rows) == 8, "p052 应为 8 句，实为 %d（脚本可能已跑过）" % len(rows)
    assert all(r["text"] == t for r, t in zip(rows[5:], CUT_TEXTS)), "末 3 句文本不符，终止"
    kept = [dict(i=r["i"], start_s=r["start_s"], end_s=r["end_s"],
                 dur_s=r["dur_s"], text=r["text"]) for r in rows[:KEEP]]

    # 待改文件清单（用于备份）
    pages = [p for p in sorted(__import__("glob").glob(
        os.path.join(HERE, "篇章页", "读写_*.html"))) if '"52":' in text(p)]
    zh_page = os.path.join(HERE, "篇章页", "读写_052_tech_break.html")
    targets = [v for k, v in F.items()] + pages
    targets = list(dict.fromkeys(targets))

    audio = os.path.join(HERE, "assets", "p052.mp3")
    audio_before = md5(audio)
    print("=== p052 方案 A · %s ===" % ("DRY-RUN" if args.dry_run else "APPLY"))
    print("将删 i=5/6/7 三句（课本印刷、音频未朗读），保留 5 句")
    print("涉及文件 %d 个（其中篇章页 %d 个）" % (len(targets), len(pages)))
    print("音频 md5 前：", audio_before)
    if args.dry_run:
        for f in targets:
            print("  ·", os.path.relpath(f, BASE))
        print("\nDRY-RUN 结束，未写盘。")
        return

    # ---------------- 备份 ----------------
    stamp = datetime.now().strftime("%H%M%S")
    bdir = os.path.join(MEM, "backup_p052_fix_" + stamp)
    os.makedirs(bdir, exist_ok=True)
    for f in targets:
        rel = os.path.relpath(f, BASE).replace("..", "_UP")
        dst = os.path.join(bdir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(f, dst)
    print("备份 →", bdir)

    # ---------------- 1. 正典双写 ----------------
    tl[PAGE] = kept
    jdump(F["timeline"], tl)
    doc = jload(F["archive_sent"])
    doc["sentences"] = [dict(i=r["i"], start_s=r["start_s"],
                             end_s=r["end_s"], text=r["text"]) for r in kept]
    doc["n_sent"] = KEEP
    jdump(F["archive_sent"], doc)
    print("[1] 双写完成：timeline + 归档 各 5 句")

    # ---------------- 2. 字幕重派生（仓库 + 归档） ----------------
    srt, lrc = make_srt(kept), make_lrc(kept)
    for k in ("srt", "lrc", "archive_srt", "archive_lrc"):
        put(F[k], srt if k in ("srt", "archive_srt") else lrc)
    print("[2] SRT/LRC 重派生：各 5 条（仓库 + 归档）")

    # ---------------- 3. 译文 ----------------
    z = jload(F["zh_table"])
    z["zh"] = z["zh"][:KEEP]
    jdump(F["zh_table"], z)
    az = jload(F["archive_zh"])
    az["entries"] = [e for e in az["entries"] if e["i"] < KEEP]
    az["n_sent"] = az["n_unique_keys"] = KEEP
    jdump(F["archive_zh"], az)
    # 页面 DB.ZH 删 3 键（中文释义从备份读，因为 zh_table 刚被截断）
    orig_zh = jload(os.path.join(bdir, os.path.relpath(F["zh_table"], BASE).replace("..", "_UP")))["zh"][5:]
    pairs = ['"%s":"%s"' % (en, zz) for en, zz in zip(CUT_TEXTS, orig_zh)]
    s = text(zh_page)
    for p in pairs:
        n = s.count("," + p)
        assert n == 1, "DB.ZH 键值命中异常(%d)：%s" % (n, p[:40])
        s = s.replace("," + p, "")
    put(zh_page, s)
    print("[3] 译文：译文表/归档译文/页面 DB.ZH 各删 3 条")

    # ---------------- 4. BOOK_EXTRA（源头 + 生成器 + 全站内联） ----------------
    be = jload(F["book_extra"])
    a2 = be["book"]["52"]["arts"][1]
    assert a2 == CUT_TEXTS, "book['52'].arts[1] 与预期不符"
    be["book"]["52"]["arts"] = [be["book"]["52"]["arts"][0]]
    jdump(F["book_extra"], be)
    # 两种内联序列化都要清：标准 `, ["...", "..."]` 与早期紧凑 `,["...","..."]`
    art_json = json.dumps(CUT_TEXTS, ensure_ascii=False)
    art_json_tight = json.dumps(CUT_TEXTS, ensure_ascii=False, separators=(",", ":"))
    pat = re.compile(r",\s*(?:" + re.escape(art_json) + "|" + re.escape(art_json_tight) + ")")
    n_pages = n_hits = 0
    for p in pages:
        s = text(p)
        s2, c = pat.subn("", s)
        if c:
            put(p, s2)
            n_pages += 1
            n_hits += c
    s = text(F["integrate"])
    s2, c = pat.subn("", s)
    put(F["integrate"], s2)
    print("[4] BOOK_EXTRA：源头删第 2 段；%d 个页面共 %d 处内联清除；生成器 %d 处" % (
        n_pages, n_hits, c))

    # ---------------- 5. 主站元数据 ----------------
    s = text(F["index"])
    old, new = '"52": {"q": 0, "s": 8, "v": 1}', '"52": {"q": 0, "s": 5, "v": 1}'
    assert s.count(old) == 1, "FOLLOW_META 52 命中异常"
    put(F["index"], s.replace(old, new))
    print("[5] index.html FOLLOW_META 52.s: 8 → 5")

    # ---------------- 6. 生产输入 / 历史产出同步 ----------------
    src = jload(F["source"])
    sp = src["pages"][PAGE]
    assert len(sp["sentences"]) == 8
    sp["excluded_from_alignment"] = {
        "reason": "课本印刷的评分结果段，音频未朗读（三方对账 2026-11-14）；按「源文本以音频为准」不进句级正典",
        "lines": sp["sentences"][5:],
        "report": "reports/p052_评分段未朗读诊断_2026-11-14.md",
    }
    sp["sentences"] = sp["sentences"][:KEEP]
    jdump(F["source"], src)
    u = jload(F["unit_tl_json"])
    u[PAGE] = u[PAGE][:KEEP]
    jdump(F["unit_tl_json"], u)
    lines = [ln for ln in text(F["unit_tl_txt"]).split("\n")
             if not any(t in ln for t in CUT_TEXTS)]
    put(F["unit_tl_txt"], "\n".join(lines))
    print("[6] _unit_5_source/timeline 同步：源文本 5 句 + 保留 3 行原文于 excluded_from_alignment")

    # ---------------- 7. 自检 ----------------
    print("\n=== 自检 ===")
    tl2 = jload(F["timeline"])
    print("timeline 篇数 %d / 总句数 %d / p052 %d 句" % (
        len(tl2), sum(len(v) for v in tl2.values()), len(tl2[PAGE])))
    assert len(tl2[PAGE]) == KEEP
    assert sum(len(v) for v in tl2.values()) == 1138
    assert all(t not in text(F["srt"]) and t not in text(F["lrc"]) for t in CUT_TEXTS)
    assert all(t not in text(zh_page) for t in CUT_TEXTS)
    assert all(t not in text(F["book_extra"]) for t in CUT_TEXTS)
    assert md5(audio) == audio_before, "音频被改动，违反硬规约"
    print("音频 md5 后：", md5(audio), "（未改动 ✓）")
    print("✓ 自检通过。接下来必须跑：node _sync_timeline.js && node _timeline_check.js && npm test")


if __name__ == "__main__":
    main()
