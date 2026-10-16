# -*- coding: utf-8 -*-
"""句级对齐质量全量核查：每篇完整 ASR → 与 timeline.text 归一化比对 → 逐篇一致率报告。
判定：ASR 文本（小写去标点）与原文句 tokens 的匹配率；输出 _align_audit_out.json"""
import os, json, re
os.environ["HF_HUB_OFFLINE"] = "1"
from faster_whisper import WhisperModel
BASE = r"E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/codex-handoff"
tl = json.load(open(BASE + "/assets/timeline.json", encoding="utf-8"))
AUDIO_DIR = BASE + "/assets"

def norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

model = WhisperModel("small", device="cpu", compute_type="int8")
out = {}
for pid in sorted(tl.keys(), key=lambda x: int(x.replace("p",""))):
    ref = [norm(x["text"]) for x in tl[pid]]
    try:
        segs, info = model.transcribe(os.path.join(AUDIO_DIR, pid + ".mp3"),
                                      language="en", beam_size=1, vad_filter=False)
        hyp_all = norm(" ".join(seg.text for seg in segs))
    except Exception as e:
        out[pid] = {"err": str(e)[:120]}; print(pid, "ERR", e); continue
    ref_join = " ".join(ref)
    # 词级召回：原文词在 ASR 中的覆盖
    rw, hw = ref_join.split(), hyp_all.split()
    from collections import Counter
    hc = Counter(hw)
    hit = sum(min(hc[w], 1) for w in set(rw) if hc.get(w))
    uniq = len(set(rw))
    cover = round(hit / max(uniq,1) * 100, 1)
    # 句首匹配：每句前 3 词是否出现在 ASR 中
    first3 = sum(1 for r in ref if (" ".join(r.split()[:3]) in hyp_all) if len(r.split())>=3)
    sent_start = round(first3 / max(sum(1 for r in ref if len(r.split())>=3),1) * 100, 1)
    out[pid] = {"n_sent": len(ref), "word_cover": cover, "sent_start_hit": sent_start,
                "dur": round(info.duration,1), "ref_nwords": len(rw), "asr_nwords": len(hw)}
    print(pid, "词覆盖%".ljust(4), cover, "| 句首命中", sent_start, "|", len(ref), "句", flush=True)
json.dump(out, open(BASE + "/_align_audit_out.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("AUDIT_DONE")
