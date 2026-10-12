# -*- coding: utf-8 -*-
"""U8 四篇正课文的全自动句级时间轴产出。

流程（用户定案，全自动、无人耳终审）：
  情况2（p075/p078/p080，有源文本）：faster-whisper 词级时间戳 × 源文本自动校准 + 静音吸附
  情况1（p077 听力，无源文本）：ASR 转写即为源文本，同样走词级时间戳 + 静音吸附

产出：
  _u8_timeline.json   { page: [{i, start_s, end_s, dur_s, text, confidence}] }
"""
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

HERE = os.path.dirname(os.path.abspath(__file__))
ALIGNER_HOME = r"D:\Trae Project\audio-aligner-v4.0.0"
sys.path.insert(0, ALIGNER_HOME)

import aligner  # noqa: E402

PAGES = ["p075", "p077", "p078", "p080"]
SILENCE = {
    "enabled": True,
    "min_silence_duration": 0.3,
    "silence_threshold_db": -40,
    "boundary_tolerance": 0.15,
}


def main():
    src = json.load(open(os.path.join(HERE, "_u8_source.json"), encoding="utf-8"))
    out = {}
    report = []

    words_all = json.load(open(os.path.join(HERE, "_u8_words.json"), encoding="utf-8"))

    for page in PAGES:
        spec = src[page]
        sentences = spec["sentences"]
        text = "\n".join(sentences)
        mp3 = os.path.join(HERE, "assets", page + ".mp3")

        # 复用已算好的词级时间戳（CPU int8），避免 CUDA 检测 / 重复转写
        word_alignments = [
            {"text": w[2].strip(), "start": w[0], "end": w[1]} for w in words_all[page]
        ]

        print("\n=== %s  %s  (%s) ===" % (page, spec["title"], spec["type"]), flush=True)
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
        print("[ok] %s %d 句，低置信 %d，首句起点 %.3fs" % (
            page, len(rows), len(low), rows[0]["start_s"] if rows else -1))
        for r in rows:
            report.append((page, r))

    json.dump(out, open(os.path.join(HERE, "_u8_timeline.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # 人读摘要
    lines = ["# U8 四篇句级时间轴产出摘要", ""]
    for page in PAGES:
        rows = out[page]
        lines.append("## %s  %s" % (page, src[page]["title"]))
        lines.append("- 句数 %d，首句 %.3fs，末句 %.3fs" % (
            len(rows), rows[0]["start_s"], rows[-1]["end_s"]))
        lines.append("")
        for r in rows:
            lines.append("  %2d  %8.3f - %8.3f  %s" % (
                r["i"], r["start_s"], r["end_s"], r["text"]))
        lines.append("")
    open(os.path.join(HERE, "_u8_timeline.txt"), "w", encoding="utf-8").write("\n".join(lines))

    total = sum(len(out[p]) for p in PAGES)
    print("\n完成：4 篇共 %d 句 -> _u8_timeline.json / _u8_timeline.txt" % total)


if __name__ == "__main__":
    main()
