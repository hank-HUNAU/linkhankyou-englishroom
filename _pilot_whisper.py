# -*- coding: utf-8 -*-
"""方案 B 试点：faster-whisper 取词级时间戳，测量与人工核查标尺点的偏差。"""
import json
import os
import sys

from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.abspath(__file__))
PID = sys.argv[1] if len(sys.argv) > 1 else "067"
if not PID.startswith("p"):
    PID = "p" + PID

print("load faster-whisper small (cpu int8) ...", flush=True)
model = WhisperModel("small", device="cpu", compute_type="int8")

audio = os.path.join(ROOT, "assets", PID + ".mp3")
print("transcribe", audio, flush=True)
segments, info = model.transcribe(audio, language="en", word_timestamps=True,
                                  beam_size=1, vad_filter=False)

words = []
for seg in segments:
    for w in (seg.words or []):
        words.append((w.start, w.end, w.word.strip()))
print("words=%d  duration=%.1fs" % (len(words), info.duration), flush=True)

json.dump(words, open(os.path.join(ROOT, "_whisper_words_%s.json" % PID), "w", encoding="utf-8"),
          ensure_ascii=False)

print("")
print("=== B 在人工标尺点附近给出的词边界 ===")
probes = [(2, "end", 28.500), (3, "start", 28.560), (17, "end", 139.420), (18, "start", 139.488)]
for idx, which, human in probes:
    lo = human - 1.2
    hi = human + 1.2
    print("")
    print("p%s #%d %s   human=%.3f" % (PID, idx, which, human))
    hit = False
    for st, en, w in words:
        mid = (st + en) / 2.0
        if mid < lo or mid > hi:
            continue
        hit = True
        cross = "   <== 跨越人工边界" if (st < human and en > human) else ""
        print("   %8.3f - %8.3f  %-18s%s" % (st, en, w, cross))
    if not hit:
        print("   (no words in range)")
