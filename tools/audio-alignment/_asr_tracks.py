# -*- coding: utf-8 -*-
"""对 25 个按页推断轨 + 2-3 个杂项轨做 faster-whisper 转写 → _asr_tracks.json"""
import os, json, sys, io
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from faster_whisper import WhisperModel

WORK = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(WORK, "_alignment.json"), encoding="utf-8"))
targets = []
for u, d0 in A.items():
    for r0 in d0.get("sb", []):
        if r0["st"] == "inferred" and r0.get("path"):
            targets.append((u, "t%02d" % r0["tr"], r0["path"]))
    for r0 in d0.get("other", []):
        if r0.get("path"):
            targets.append((u, "other", r0["path"]))

print("targets:", len(targets), flush=True)
model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
OUTP = os.path.join(WORK, "_asr_tracks.json")
if os.path.exists(OUTP):
    out = json.load(open(OUTP, encoding="utf-8"))
for i, (u, tag, p) in enumerate(targets, 1):
    key = os.path.basename(p)
    if key in out:
        continue
    try:
        segs, info = model.transcribe(p, language="en", vad_filter=True,
                                      condition_on_previous_text=False)
        txt = " ".join(s.text.strip() for s in segs)
        out[key] = dict(unit=u, tag=tag, path=p, dur=round(info.duration, 1), text=txt)
        print(f"[{i}/{len(targets)}] {u}/{tag} {key[:44]} -> {txt[:70]}", flush=True)
    except Exception as e:
        print(f"[{i}/{len(targets)}] ERR {key}: {e}", flush=True)
        out[key] = dict(unit=u, tag=tag, path=p, error=str(e))
    json.dump(out, open(OUTP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", len(out), flush=True)
