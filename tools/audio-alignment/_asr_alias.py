# -*- coding: utf-8 -*-
"""对 12 个改名/别名文件做 ASR 验证 → _asr_alias.json"""
import os, json, sys, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from faster_whisper import WhisperModel

base = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"
NAMES = ["109.mp3", "903.mp3", "905.mp3", "Unit 03-1 Reading.mp3",
         "Unit_3_p34_t04[reading].mp3", "Unit4-p38-reading.mp3",
         "Unit4-p41-listening-ex9.ex10.mp3", "4-p42-reading-ex1.mp3",
         "4-p43-functions-ex11.mp3", "4-p45-culture-ex3.mp3",
         "第8单元 阅读1 Music in the Forest 课文音频.mp3",
         "第9单元 第1次课 篇章阅读 音频.mp3"]
targets = []
for n in NAMES:
    for dirpath, dirs, files in os.walk(base):
        if n in files:
            targets.append(os.path.join(dirpath, n))
            break
print("targets:", len(targets), flush=True)
model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
WORK = os.path.dirname(os.path.abspath(__file__))
OUTP = os.path.join(WORK, "_asr_alias.json")
for i, p in enumerate(targets, 1):
    key = os.path.basename(p)
    # 只转写前 30 秒即可拿到公告
    segs, info = model.transcribe(p, language="en", vad_filter=True,
                                  condition_on_previous_text=False)
    head = []
    tspent = 0.0
    for s in segs:
        head.append(s.text.strip())
        tspent = s.end
        if tspent > 28:
            break
    txt = " ".join(head)
    out[key] = dict(path=p, dur=round(info.duration, 1), head=txt)
    print(f"[{i}/{len(targets)}] {key[:44]} -> {txt[:80]}", flush=True)
    json.dump(out, open(OUTP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", flush=True)
