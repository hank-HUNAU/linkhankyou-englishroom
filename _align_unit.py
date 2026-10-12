#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""通用句级时间轴产出脚本：_align_unit.py --unit N

把一个单元的正课文（阅读A/听力/阅读B/口语或文化）一键产出句级时间轴并合入
assets/timeline.json。替代早期的 _u8_whisper.py + _u8_align.py（那两个是 U8 首次
跑通的硬编码版，留作留痕，不再维护）。

输入：`_unit_{N}_source.json`（正课文清单 + 源文本 + 音频映射），格式见
      _ALIGNMENT_WORKFLOW.md 第 2 节。
输出：`_unit_{N}_words.json`（词级时间戳）、`_unit_{N}_timeline.json/.txt`（句级
      时间轴），并合入 assets/timeline.json → 同步 index.html → 跑门禁。

用法：
    python _align_unit.py --unit 8
    python _align_unit.py --unit 8 --skip-asr      # 复用已算好的词级时间戳
    python _align_unit.py --unit 8 --no-merge      # 只产出时间轴，不合入/不同步
    python _align_unit.py --unit 8 --page p075     # 只跑一篇（调试）

对齐方法（用户定案，全自动、无人耳终审）：
  情况2（有源文本：阅读A/B、口语、文化）→ ASR 词级时间戳 × 源文本自动校准 + 静音吸附
  情况1（无源文本：听力）→ ASR 转写即为源文本，同样走词级时间戳 + 静音吸附
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

HERE = os.path.dirname(os.path.abspath(__file__))
ALIGNER_HOME = r"D:\Trae Project\audio-aligner-v4.0.0"
MATERIAL_BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"

SILENCE = {
    "enabled": True,
    "min_silence_duration": 0.3,
    "silence_threshold_db": -40,
    "boundary_tolerance": 0.15,
}


# ---------------------------------------------------------------- 输入
def source_path(unit):
    return os.path.join(HERE, "_unit_%d_source.json" % unit)


def words_path(unit):
    return os.path.join(HERE, "_unit_%d_words.json" % unit)


def timeline_path(unit):
    return os.path.join(HERE, "_unit_%d_timeline.json" % unit)


def unit_audio_dir(unit):
    return os.path.join(MATERIAL_BASE, "第%d单元" % unit, "第%d单元 音频" % unit)


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- 音频
def ensure_audio(unit, page, audio_name):
    """从素材库复制音频到 assets/pXXX.mp3（MD5 一致则跳过）。"""
    src = os.path.join(unit_audio_dir(unit), audio_name)
    dst = os.path.join(HERE, "assets", page + ".mp3")
    if not os.path.isfile(src):
        sys.exit("[x] 素材库缺音频：%s" % src)
    if os.path.isfile(dst) and md5(dst) == md5(src):
        print("[=] %s 已就绪（MD5 一致）" % page)
    else:
        shutil.copyfile(src, dst)
        print("[+] %s <- %s" % (page, audio_name))
    return dst


# ---------------------------------------------------------------- ASR
def run_asr(unit, pages):
    from faster_whisper import WhisperModel

    print("加载 faster-whisper small (cpu int8) ...", flush=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")

    words_out = {}
    for page in pages:
        audio = os.path.join(HERE, "assets", page + ".mp3")
        segs, info = model.transcribe(
            audio, language="en", word_timestamps=True,
            beam_size=1, vad_filter=False,
        )
        ws = []
        for seg in segs:
            for w in (seg.words or []):
                # 关键坑：faster-whisper 词文本带前导空格，必须 strip，否则归一化失配
                ws.append([round(w.start, 3), round(w.end, 3), w.word.strip()])
        words_out[page] = ws
        print("[asr] %s %.1fs -> %d 词" % (page, info.duration, len(ws)), flush=True)

    json.dump(words_out, open(words_path(unit), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    return words_out


# ---------------------------------------------------------------- 对齐
def run_align(unit, pages, spec, words_all):
    sys.path.insert(0, ALIGNER_HOME)
    import aligner  # noqa: E402

    out = {}
    for page in pages:
        item = spec["pages"][page]
        text = "\n".join(item["sentences"])
        mp3 = os.path.join(HERE, "assets", page + ".mp3")
        # 复用已算好的词级时间戳，绕过 aligner 的 CUDA 探测（缺 cublas 会崩）
        word_alignments = [
            {"text": w[2].strip(), "start": w[0], "end": w[1]} for w in words_all[page]
        ]
        print("\n=== %s  %s · %s（%s）===" % (
            page, item["section"], item["title"], item["type"]), flush=True)
        a = aligner.AudioTextAligner(mp3, language="en", silence_config=SILENCE, model_size="small")
        aligned = a.align_with_word_alignments(text, word_alignments)

        rows = []
        for i, al in enumerate(aligned):
            rows.append({
                "i": i,
                "start_s": round(al["start"], 3),
                "end_s": round(al["end"], 3),
                "dur_s": round(al["end"] - al["start"], 3),
                "text": al["text"],
                "confidence": al.get("confidence"),
            })
        out[page] = rows
        low = [r for r in rows if r["confidence"] is not None and r["confidence"] < 0.8]
        print("[ok] %s %d 句，低置信 %d，首句 %.3fs" % (
            page, len(rows), len(low), rows[0]["start_s"] if rows else -1))

    json.dump(out, open(timeline_path(unit), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 人读摘要
    lines = ["# Unit %d 句级时间轴产出摘要" % unit, ""]
    for page in pages:
        item = spec["pages"][page]
        rows = out[page]
        lines.append("## %s  %s · %s" % (page, item["section"], item["title"]))
        lines.append("- 句数 %d，首句 %.3fs，末句 %.3fs" % (
            len(rows), rows[0]["start_s"], rows[-1]["end_s"]))
        lines.append("")
        for r in rows:
            lines.append("  %2d  %8.3f - %8.3f  %s" % (
                r["i"], r["start_s"], r["end_s"], r["text"]))
        lines.append("")
    open(os.path.join(HERE, "_unit_%d_timeline.txt" % unit), "w", encoding="utf-8").write("\n".join(lines))
    return out


# ---------------------------------------------------------------- 合入
def merge(unit, out):
    """合入 assets/timeline.json（先备份），格式与现网一致（无 confidence）。"""
    tj_path = os.path.join(HERE, "assets", "timeline.json")
    tl = json.load(open(tj_path, encoding="utf-8"))

    import datetime
    stamp = datetime.date.today().strftime("%Y%m%d")
    bak = tj_path + ".bak-" + stamp
    shutil.copyfile(tj_path, bak)

    for page, rows in out.items():
        tl[page] = [
            {"i": r["i"], "start_s": r["start_s"], "end_s": r["end_s"],
             "dur_s": r["dur_s"], "text": r["text"]}
            for r in rows
        ]
    json.dump(tl, open(tj_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n[merge] 合入 assets/timeline.json：%d 篇 / %d 句（备份 %s）" % (
        len(tl), sum(len(v) for v in tl.values()), os.path.basename(bak)))


def sync_and_check():
    for cmd in (["node", "_sync_timeline.js"], ["node", "_timeline_check.js"]):
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        print(r.stdout.strip())
        if r.returncode != 0:
            sys.exit(r.stderr or ("%s 失败" % " ".join(cmd)))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", type=int, required=True)
    ap.add_argument("--skip-asr", action="store_true")
    ap.add_argument("--no-merge", action="store_true")
    ap.add_argument("--page", help="只跑一篇，如 p075")
    args = ap.parse_args()

    spec = json.load(open(source_path(args.unit), encoding="utf-8"))
    all_pages = list(spec["pages"].keys())
    pages = [args.page] if args.page else all_pages

    print("Unit %d 正课文：%d 篇 -> %s" % (args.unit, len(pages), ", ".join(pages)))

    for page in pages:
        ensure_audio(args.unit, page, spec["pages"][page]["audio"])

    if args.skip_asr and os.path.isfile(words_path(args.unit)):
        words_all = json.load(open(words_path(args.unit), encoding="utf-8"))
        print("[=] 复用词级时间戳 %s" % os.path.basename(words_path(args.unit)))
    else:
        words_all = run_asr(args.unit, pages)

    out = run_align(args.unit, pages, spec, words_all)

    if not args.no_merge:
        merge(args.unit, out)
        sync_and_check()
        print("\n完成：请再跑 `npm test` 做全量回归验收。")


if __name__ == "__main__":
    main()
