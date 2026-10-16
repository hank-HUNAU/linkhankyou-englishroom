# -*- coding: utf-8 -*-
import os, json
os.environ["HF_HUB_OFFLINE"] = "1"
from faster_whisper import WhisperModel
BASE = r"E:/04 少儿原版课程/03 Think 0 课程制作/003 第三版课程材料"
FILES = {
 "u10_statues": os.path.join(BASE, "第10单元", "第10单元 音频", "Thk2e_BE_L0_SB_Unit_10_p99_t09[公众号happyshare2023].mp3"),
 "u11_dolphins": os.path.join(BASE, "第11单元", "第11单元 音频", "Thk2e_BE_L0_SB_Unit_11_p102_t01[公众号happyshare2023].mp3"),
 "u11_extinct": os.path.join(BASE, "第11单元", "第11单元 音频", "Thk2e_BE_L0_SB_Unit_11_p106_t05[公众号happyshare2023].mp3"),
}
model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
for k, f in FILES.items():
    segs, info = model.transcribe(f, language="en", beam_size=1, vad_filter=False)
    sents = []
    for seg in segs:
        sents.append(seg.text.strip())
    out[k] = sents
    print("==", k, len(sents), "段", flush=True)
    for s in sents: print("  ", s, flush=True)
json.dump(out, open("_asr_full_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
