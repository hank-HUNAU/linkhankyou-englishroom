#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_align_u14_rerun.py —— U1–U4 情况1 六篇「拉齐」重跑（2026-11-12 用户令）

背景：_align_u14.py 的情况1 走 segs_to_sentences()，ASR 段界直接当句界，
      未调用 aligner、无 confidence。本脚本按主线 _align_unit.py::run_align()
      口径补齐：ASR 词级时间戳 × 源文本校准（LCS 映射）+ 静音吸附，
      并产出每句 confidence。

硬规约（_RELEASE_WORKFLOW.md）：
  - 音频一个不动（只读 assets/<page>.mp3 做静音检测）
  - 句子文本逐字不变（译文 DB.ZH / 词汇诊断页 / 语块 sent 索引都取原串）
  - 只重算 start_s / end_s；双写由 _apply_u14_rerun.py 执行
  - 归档 schema 保持 {i,start_s,end_s,text}，confidence 另存逐句清单，不进正典

用法：
  .venv-align/Scripts/python.exe _align_u14_rerun.py            # 全 6 篇
  .venv-align/Scripts/python.exe _align_u14_rerun.py --page p018 # 单篇调试
  .venv-align/Scripts/python.exe _align_u14_rerun.py --dry       # 只比对不写
"""
import argparse
import glob
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
ALIGNER_HOME = r"D:\我的文档\audio-aligner-v4.0.0"
FFMPEG_DIR = os.path.join(ALIGNER_HOME, "ffmpeg")
SILENCE = {"enabled": True, "min_silence_duration": 0.3,
           "silence_threshold_db": -40, "boundary_tolerance": 0.15}
WORDS_CACHE = os.path.join(HERE, "_u14_words.json")
OUT = os.path.join(HERE, "_u14_rerun_result.json")

# key -> (page, 归档单元目录)
SIX = [
    ("u1_p15_quiz",       "p015", "U1_AllTogether"),
    ("u1_p18_daniela",    "p018", "U1_AllTogether"),
    ("u2_p23_dialogues",  "p023", "U2_ImExcited"),
    ("u3_p33_family",     "p033", "U3_FamilyTime"),
    ("u3_p36_photos",     "p036", "U3_FamilyTime"),
    ("u4_p41_directions", "p041", "U4_CityLife"),
]
PAGE2KEY = {p: (k, d) for k, p, d in SIX}


def setup_env():
    """pydub 需要显式 converter/ffprobe；aligner __init__ 不加载 whisper 模型。"""
    from pydub import AudioSegment
    AudioSegment.converter = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
    AudioSegment.ffprobe = os.path.join(FFMPEG_DIR, "ffprobe.exe")
    os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    sys.path.insert(0, ALIGNER_HOME)
    import aligner  # noqa: E402
    return aligner


def archive_path(page, unit_dir):
    fs = glob.glob(os.path.join(BASE, unit_dir, "01_正文篇章",
                                "句级数据_%s.json" % page))
    assert len(fs) == 1, (page, fs)
    return fs[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", help="只跑单篇 pXXX")
    ap.add_argument("--dry", action="store_true", help="不写结果文件")
    args = ap.parse_args()

    aligner = setup_env()
    W = json.load(io.open(WORDS_CACHE, encoding="utf-8"))
    targets = [x for x in SIX if not args.page or x[1] == args.page]
    assert targets, "无匹配页面"
    results = {}

    for key, page, unit_dir in targets:
        arc = archive_path(page, unit_dir)
        doc = json.load(io.open(arc, encoding="utf-8"))
        old = doc["sentences"]
        # 源文本 = 现有归档句子（逐字不改），按换行切 —— aligner 的
        # _split_text_by_punctuation 优先按换行，故一换行=一句
        src_lines = [s["text"] for s in old]
        text = "\n".join(src_lines)

        wa = W[key]
        word_alignments = [
            {"text": w[2].strip(), "start": float(w[0]), "end": float(w[1])}
            for w in wa["words"] if isinstance(w[2], str) and w[2].strip()
        ]
        mp3 = os.path.join(HERE, "assets", page + ".mp3")
        a = aligner.AudioTextAligner(
            mp3, language="en", silence_config=SILENCE, model_size="small")
        aligned = a.align_with_word_alignments(text, word_alignments)

        print("\n=== %s (%s) 源 %d 句 → aligner %d 句 ===" %
              (key, page, len(src_lines), len(aligned)), flush=True)
        if len(aligned) != len(src_lines):
            print("  ⚠ 句数不符，跳过该篇（不写结果）", flush=True)
            continue

        rows = []
        for i, al in enumerate(aligned):
            # 文本一律取原串，绝不采用 aligner 回传的 text
            rows.append(dict(
                i=i,
                start_s=round(float(al["start"]), 3),
                end_s=round(float(al["end"]), 3),
                text=src_lines[i],
                confidence=round(float(al.get("confidence") or 0.0), 3),
            ))

        # 单调钳制（沿用 _align_u14.py::main，消静音吸附微叠）
        prev = 0.0
        for r in rows:
            if r["start_s"] < prev:
                r["start_s"] = prev
            if r["end_s"] < r["start_s"]:
                r["end_s"] = r["start_s"]
            prev = r["end_s"]

        conf = [r["confidence"] for r in rows]
        dur = float(wa["duration"])
        moved = sum(1 for o, n in zip(old, rows)
                    if abs(float(o["start_s"]) - n["start_s"]) > 0.01
                    or abs(float(o["end_s"]) - n["end_s"]) > 0.01)
        results[page] = dict(
            key=key, unit_dir=unit_dir, archive=os.path.relpath(arc, BASE),
            duration_s=dur, n_sent=len(rows), sentences=rows,
            conf_mean=round(sum(conf) / len(conf), 3), conf_min=min(conf),
            conf_low=sum(1 for c in conf if c < 0.8),
            tail_gap=round(dur - rows[-1]["end_s"], 3),
            moved=moved,
        )
        print("  confidence 均 %.3f / min %.3f / <0.8 共 %d 句" %
              (results[page]["conf_mean"], results[page]["conf_min"],
               results[page]["conf_low"]), flush=True)
        print("  尾部空隙 %.2fs（原 %.2fs）· 时间轴变动 %d/%d 句" %
              (results[page]["tail_gap"],
               dur - float(old[-1]["end_s"]), moved, len(rows)), flush=True)

        # 文本逐字守恒断言（硬门禁）
        assert all(o["text"] == n["text"] for o, n in zip(old, rows)), \
            "%s 句子文本被改动，违反硬规约" % page
        assert all(n["end_s"] >= n["start_s"] for n in rows), "负时长"
        assert all(rows[i]["start_s"] >= rows[i-1]["end_s"] - 0.001
                   for i in range(1, len(rows))), "时间重叠"

    if not args.dry:
        json.dump(results, io.open(OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\n结果已写入 %s（%d 篇）" % (os.path.basename(OUT), len(results)))
    print("\n注意：confidence = aligner 的 LCS 词映射率（映射词数/该句词数），"
          "是「文本×词级时间戳一致性」，不是音频识别概率。")


if __name__ == "__main__":
    main()
