# -*- coding: utf-8 -*-
"""大间隙段 ASR 反向校验：13 处 >3s 间隙逐段转写，判定内容。"""
import json, os, sys
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills", "global", "article-vocab-analyzer", "scripts"))
from faster_whisper import WhisperModel
tl = json.load(open("../Think F 教材资产/【数据资产】/timeline.json", encoding="utf-8"))
gaps = json.load(open("_gap_check.json", encoding="utf-8"))
model = WhisperModel("small", device="cpu", compute_type="int8")
out = []
cur = None
for k, t_end, t_next in gaps:
    if k != cur:
        cur = k
    seg = []
    def cb(segments, info):
        seg.extend(segments)
    audio = f"assets/{k}.mp3"
    segs, info = model.transcribe(audio, language="en", clip_timestamps=[max(0,t_end-0.3), t_next+0.3], vad_filter=False)
    txt = " ".join(s.text.strip() for s in segs).strip()
    dur = t_next - t_end
    if not txt:
        verdict = "静音/无语音（正常停顿）"
    elif any(w in txt.lower() for w in ["unit", "page", "think", "cambridge"]):
        verdict = "报幕/标题朗读（正确排除）"
    else:
        verdict = "⚠疑似漏句（需人工听）"
    out.append({"p": k, "gap": f"{t_end:.1f}-{t_next:.1f}", "dur": round(dur,1), "asr": txt, "判定": verdict})
    print(f"[{k}] {t_end:.1f}-{t_next:.1f}s ({dur:.1f}s): {txt[:80] or '（空）'} → {verdict}", flush=True)
json.dump(out, open("_gap_asr_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("完成:", len(out))
