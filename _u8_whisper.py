# -*- coding: utf-8 -*-
"""U8 四篇音频的 faster-whisper 转写（词级时间戳 + 分段文本），供定稿源文本前核验。

产出：
  _u8_words.json    { page: [[start, end, word], ...] }
  _u8_transcript.txt  每篇的分段文本（含段起止时间），人读
"""
import json
import os

# 模型已缓存在本地，强制离线，避免代理 502
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGES = ["p075", "p077", "p078", "p080"]


def main():
    print("load faster-whisper small (cpu int8) ...", flush=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")

    words_out = {}
    lines = []
    for key in PAGES:
        audio = os.path.join(ROOT, "assets", key + ".mp3")
        segs, info = model.transcribe(
            audio, language="en", word_timestamps=True,
            beam_size=1, vad_filter=False,
        )
        ws = []
        lines.append("\n" + "=" * 78)
        lines.append("PAGE %s  (duration %.1fs)" % (key, info.duration))
        lines.append("=" * 78)
        for seg in segs:
            lines.append("[%6.2f - %6.2f] %s" % (seg.start, seg.end, seg.text.strip()))
            for w in (seg.words or []):
                ws.append([round(w.start, 3), round(w.end, 3), w.word])
        words_out[key] = ws
        print("%s  %.1fs -> %d words" % (key, info.duration, len(ws)), flush=True)

    json.dump(words_out, open(os.path.join(ROOT, "_u8_words.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    open(os.path.join(ROOT, "_u8_transcript.txt"), "w", encoding="utf-8").write("\n".join(lines))
    print("done -> _u8_words.json, _u8_transcript.txt")


if __name__ == "__main__":
    main()
