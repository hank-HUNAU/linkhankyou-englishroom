# -*- coding: utf-8 -*-
"""U9-11 候选音频头 15s ASR 探针：识别内容用于音轨配对。"""
import os, sys, glob, json
BASE = r"E:/04 少儿原版课程/03 Think 0 课程制作/003 第三版课程材料"
os.environ["HF_HUB_OFFLINE"] = "1"
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
for u in (9, 10, 11):
    d = os.path.join(BASE, "第%d单元" % u, "第%d单元 音频" % u)
    for f in sorted(glob.glob(os.path.join(d, "*.mp3"))):
        name = os.path.basename(f)
        try:
            segs, info = model.transcribe(f, language="en", beam_size=1, vad_filter=False)
            text = []
            for seg in segs:
                if seg.end > 18: 
                    text.append(seg.text.strip())
                    break
                text.append(seg.text.strip())
            out[name] = {"dur": round(info.duration,1), "head": " ".join(text)[:160]}
        except Exception as e:
            out[name] = {"err": str(e)[:100]}
        print(name[:52], "->", out[name].get("head", out[name].get("err"))[:100], flush=True)
json.dump(out, open("_probe_audio_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
