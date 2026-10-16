# -*- coding: utf-8 -*-
import os, json
os.environ["HF_HUB_OFFLINE"] = "1"
from faster_whisper import WhisperModel
BASE = r"E:/04 少儿原版课程/03 Think 0 课程制作/003 第三版课程材料"
FILES = {
 "u9_cooking_p87": os.path.join(BASE, "第9单元", "第9单元 音频", "903.mp3"),
 "u9_restaurant_p88": os.path.join(BASE, "第9单元", "第9单元 音频", "905.mp3"),
 "u9_offering_p90": os.path.join(BASE, "第9单元", "第9单元 音频", "Thk2e_BE_L0_SB_Unit_9_p90_t09[公众号happyshare2023].mp3"),
 "u10_prize_p95": os.path.join(BASE, "第10单元", "第10单元 音频", "Thk2e_BE_L0_SB_Unit_10_p95_t03[公众号happyshare2023].mp3"),
 "u11_josh_p105": os.path.join(BASE, "第11单元", "第11单元 音频", "Thk2e_BE_L0_SB_Unit_11_p105_t02[公众号happyshare2023].mp3"),
}
model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
for k, f in FILES.items():
    segs, info = model.transcribe(f, language="en", beam_size=1, vad_filter=False)
    sents = [seg.text.strip() for seg in segs]
    out[k] = sents
    print("==", k, len(sents), "段", flush=True)
    for s in sents: print("  ", s, flush=True)
json.dump(out, open("_asr_dialogs_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE")
