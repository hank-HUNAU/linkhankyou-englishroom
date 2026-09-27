# -*- coding: utf-8 -*-
"""按句切分教材朗读音频（启发式对齐）。
候选边界=≥150ms 静音的中点；按“字数占比→期望位置”从候选里挑最近切分点。
精度说明：连续朗读无逐句来源，切分可能偶有过/欠切，供逐句点读使用。
"""
import librosa, numpy as np, json, os, wave, math

A = r"C:\Users\Thinkpad\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a963ac655852a745b9b5a45\xueersi-diancan-原型\assets"
OUT = os.path.join(A, "sents")

P67 = [
 "Nikolai Kutsenko, from Ukraine, can do amazing things with a football.",
 "He can kick a ball well ... but he can also keep the ball in the air with his feet, legs and head.",
 "Lots of footballers can do this.",
 "But can they do it for 24 hours and 30 minutes without stopping?",
 "Nikolai can and it's a world record!",
 "Sloan Henderson, from Utah, is a really good snowboarder – and she's only 14 months old!",
 "Her mother and father take her to the mountains, and they put her on a snowboard – and there she goes!",
 "Sloan loves to be on the board.",
 "People are often surprised when they see her because she doesn't fall over!",
 "American rock-climber Maureen 'Mo' Beck was born without her left hand and only part of her left arm, but she can climb really well.",
 "She is the winner of two climbing World Championships for disabled athletes, and five national championships.",
 "She has her own special way of climbing, but Maureen thinks she is just the same as any other climber.",
 "Goatee can't talk or write, but she can surf!",
 "Why is this special?",
 "Because Goatee is a goat!",
 "She surfs with her owner, Dana McGregor.",
 "Dana helps Goatee to stand on the board and together they ride the waves in California.",
 "Goatee wears a yellow life-jacket because she can't swim very well!",
 "And now there is a children's book about her, too – Dana is the author.",
]
P70 = [
 "It's 15th February at Greece Athena High School, New York.",
 "Jason McElwain is an 18-year-old student.",
 "Jason is autistic.",
 "He loves basketball and he helps with the school basketball team.",
 "Jason practises hard every day, but he never plays in the team.",
 "Tonight is the last game of the season.",
 "It's Jason's last chance to play a game with the team, but for 44 minutes, he sits on the bench and watches.",
 "It's four minutes before the end.",
 "The team is winning, so the coach tells Jason to go out and play.",
 "The team and the crowd are very happy, because everyone knows Jason and likes him.",
 "Jason tries to score a basket, but he misses.",
 "But suddenly he hits a 3-point basket.",
 "The crowd goes crazy.",
 "Jason hits another 3-pointer, then another and another – he hits six 3-pointers (it's a record for the team) and scores twenty points altogether.",
 "The team wins, and Jason is a real hero.",
 "It's an amazing night for him!",
 "Soon Jason starts to become famous.",
 "People in his town know who he is.",
 "The US president comes to Jason's town to meet him.",
 "Jason writes a book and some people want to make a film about him.",
 "He becomes assistant coach to the high school basketball team.",
 "Now Jason works hard to help other autistic people.",
 "He travels across the US to help get money for autism research.",
]

def wav16(path, data, sr):
    data = np.clip(data, -1.0, 1.0)
    pcm = (data * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())

def boundaries_for(fn, sentences, tag):
    y, sr = librosa.load(os.path.join(A, fn), sr=None, mono=True)
    hop = 220
    n = len(y)//hop; yc = y[:n*hop].reshape(-1, hop)
    rms = np.sqrt((yc**2).mean(1)); thr = max(np.percentile(rms, 30)*0.10, 0.004)
    act = rms > thr
    speech = []
    i = 0
    while i < len(act):
        if act[i]:
            j = i
            while j < len(act) and act[j]: j += 1
            speech.append((i*hop, j*hop)); i = j
        else: i += 1
    cand = []
    for k in range(len(speech)-1):
        gs, ge = speech[k][1], speech[k+1][0]
        if ge-gs >= 0.15*sr:
            cand.append((gs+ge)//2)
    first_start = speech[0][0]
    last_end = speech[-1][1]
    readdur = last_end - first_start
    L = [len(s) for s in sentences]
    tot = sum(L)
    # ensure strictly increasing candidate picks
    sel = []
    prev = first_start
    cum = 0.0
    for k in range(len(sentences)-1):
        cum += L[k]
        expect = first_start + (cum/tot) * readdur
        # pick candidate >= prev minimizing |c-prev... | to expect
        best = None
        for c in cand:
            if c >= prev + int(0.02*sr):
                d = abs(c - expect)
                if best is None or d < best[1]:
                    best = (c, d)
        if best:
            prev = best[0]; sel.append(best[0])
        else:
            # no candidate ahead: insert expected clamped
            prev = max(prev + int(0.02*sr), expect); sel.append(prev)
    bounds = [first_start] + sel + [last_end]
    # clips: sentence k = [bounds[k]-pad0, bounds[k+1]+pad1]
    pad0 = int(0.03*sr); pad1 = int(0.06*sr)
    clips = []
    for k in range(len(sentences)):
        s = max(0, bounds[k]-pad0)
        e = min(len(y), bounds[k+1]+pad1)
        clips.append((s, e))
    os.makedirs(OUT, exist_ok=True)
    meta = []
    for k,(s,e) in enumerate(clips):
        fp = os.path.join(OUT, f"{tag}__{k:02d}.wav")
        wav16(fp, y[s:e], sr)
        meta.append({"i": k, "start_s": round(s/sr,3), "end_s": round(e/sr,3),
                     "dur_s": round((e-s)/sr,3), "text": sentences[k]})
    return meta, clips

all_meta = {}
for tag, fn, sentences in [("p067", "p067.mp3", P67), ("p070", "p070.mp3", P70)]:
    meta, clips = boundaries_for(fn, sentences, tag)
    all_meta[tag] = meta
    print(f"==== {tag} {len(sentences)} sentences")
    for m in meta:
        flag = "LONG" if m["dur_s"] > 9.0 else ("SHORT" if m["dur_s"] < 0.6 else "")
        print(f"  s{m['i']:02d}  {m['start_s']:7.2f}-{m['end_s']:7.2f} ({m['dur_s']:5.2f}s) {flag} {m['text'][:30]}")

with open(os.path.join(A, "timeline.json"), "w", encoding="utf-8") as f:
    json.dump(all_meta, f, ensure_ascii=False, indent=1)
print("timeline.json written")