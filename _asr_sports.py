import os, json
os.environ["HF_HUB_OFFLINE"] = "1"
from faster_whisper import WhisperModel
f = r"E:////04 少儿原版课程////03 Think 0 课程制作////003 第三版课程材料////第11单元////第11单元 音频////Thk2e_BE_L0_SB_Unit_11_p108_t07[公众号happyshare2023].mp3"
model = WhisperModel("small", device="cpu", compute_type="int8")
segs, info = model.transcribe(f, language="en", beam_size=1, vad_filter=False)
for seg in segs: print(" ", seg.text.strip(), flush=True)
