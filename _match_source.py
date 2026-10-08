#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_match_source.py —— 用「时长指纹」把 assets/p*.mp3 反向定位到原始素材轨。

背景：assets/ 里 12 篇课文音频质量参差——p066 / p073 / p202 是 22050Hz 单声道
32kbps（听感嘈杂），p110 是 64kbps，其余 8 篇是 44100Hz 立体声 128kbps。
原始素材在 E:\\04 少儿原版课程\\03 Think 0 课程制作\\003 第三版课程材料\\第N单元\\第N单元 音频\\，
共 198 轨、289MB，命名形如 Thk2e_BE_L0_SB_Unit_7_p70_t07.mp3（SB=学生用书，WB=练习册）。

mp3 时长精确到小数点后 6 位，是极强的指纹：未经重编码的复制品会逐位一致，
被重编码过的会有几百毫秒到几秒的偏移（编码器 padding）。所以按容差匹配即可。

用法
----
    python _match_source.py              # 扫描并匹配，输出对照表
    python _match_source.py --tol 0.5    # 收紧容差（默认 2.0s）
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
SRC_ROOT = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"
FFPROBE = r"D:\Trae Project\audio-aligner-v4.0.0\ffmpeg\ffprobe.exe"
OUT = os.path.join(HERE, "_source_match.json")


def probe(path):
    """返回 (时长秒, 采样率, 声道, 码率)。失败返回 None。"""
    try:
        r = subprocess.run(
            [
                FFPROBE, "-v", "error",
                "-show_entries", "stream=sample_rate,channels",
                "-show_entries", "format=duration,bit_rate",
                "-of", "json", path,
            ],
            capture_output=True, timeout=30,
        )
        d = json.loads(r.stdout.decode("utf-8", "replace"))
        st = (d.get("streams") or [{}])[0]
        fm = d.get("format") or {}
        return (
            float(fm.get("duration", 0)),
            int(st.get("sample_rate", 0)),
            int(st.get("channels", 0)),
            int(fm.get("bit_rate", 0)),
        )
    except Exception:
        return None


def scan_sources():
    """扫描原始素材库所有 mp3。"""
    found = []
    if not os.path.isdir(SRC_ROOT):
        sys.exit("原始素材目录不可达：%s" % SRC_ROOT)
    for root, _dirs, files in os.walk(SRC_ROOT):
        for fn in files:
            if fn.lower().endswith(".mp3"):
                found.append(os.path.join(root, fn))
    return sorted(found)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tol", type=float, default=2.0, help="时长匹配容差（秒）")
    ap.add_argument("--src-only", action="store_true", help="只扫描素材库，不做匹配（用于缓存结果）")
    args = ap.parse_args()

    pages = sorted(
        f for f in os.listdir(ASSETS) if f.startswith("p") and f.endswith(".mp3")
    )
    print("assets: %d 篇" % len(pages))
    cur = {}
    for f in pages:
        m = probe(os.path.join(ASSETS, f))
        if m:
            cur[f[:-4]] = m
            print("  %s  %8.3fs  %dHz %dch %dkbps" % (f[:-4], m[0], m[1], m[2], m[3] // 1000))

    print("\n扫描原始素材库…")
    src_files = scan_sources()
    print("  共 %d 个 mp3，逐个探测…" % len(src_files))
    src = []
    for p in src_files:
        m = probe(p)
        if m:
            src.append((p, m))
    print("  探测成功 %d 个" % len(src))

    result = {}
    print("\n=== 匹配结果（容差 %.1fs）===" % args.tol)
    for page in sorted(cur):
        d, sr, ch, br = cur[page]
        cands = [x for x in src if abs(x[1][0] - d) <= args.tol]
        cands.sort(key=lambda x: abs(x[1][0] - d))
        if not cands:
            print("  %s  %8.3fs  ❌ 无匹配（容差内找不到原始轨）" % (page, d))
            result[page] = {"asset": {"dur": d, "sr": sr, "ch": ch, "kbps": br // 1000}, "match": None}
            continue
        best = cands[0]
        bp, bm = best
        bt = "完全一致" if abs(bm[0] - d) < 0.01 else "差 %+.3fs" % (bm[0] - d)
        better = "✅ 更好" if bm[3] > br else "＝ 同级"
        print(
            "  %s  %8.3fs  →  %s  [%dHz %dch %dkbps]  %s %s"
            % (page, d, os.path.basename(bp)[:52], bm[1], bm[2], bm[3] // 1000, bt, better)
        )
        result[page] = {
            "asset": {"dur": d, "sr": sr, "ch": ch, "kbps": br // 1000},
            "match": {
                "path": bp,
                "name": os.path.basename(bp),
                "dur": bm[0],
                "sr": bm[1],
                "ch": bm[2],
                "kbps": bm[3] // 1000,
                "delta": round(bm[0] - d, 3),
                "better": bool(bm[3] > br),
            },
            "alts": [os.path.basename(x[0]) for x in cands[1:4]],
        }

    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n-> %s" % OUT)
    need = [p for p in result if result[p]["match"] and result[p]["match"]["better"]]
    print("可用更高质量原轨替换：%s" % (", ".join(sorted(need)) or "无"))


if __name__ == "__main__":
    main()
