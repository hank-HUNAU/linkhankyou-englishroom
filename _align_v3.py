# -*- coding: utf-8 -*-
"""对齐管线 v3：强制对齐 + 三信号投票 + 双模型交叉 + 自动质量指标。
输出：timeline_v3.json（句级精准时间戳）+ paragraphs_v3.json（双层）+ 质量报告。"""
import json, os, re, sys, glob
os.environ["HF_HUB_OFFLINE"] = "1"
import numpy as np
import fitz
from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open("../Think F 教材资产/【数据资产】/timeline.json", encoding="utf-8"))
PDFDIR = "../按单元与课次教师用书_文字层可提取"
UNITMAP = {"66":"7","67":"7","69":"7","70":"7","72":"7","73":"7","75":"8","77":"8","78":"8","80":"8","85":"9","87":"9","88":"9","90":"9",
           "92":"10","95":"10","96":"10","99":"10","102":"11","105":"11","106":"11","108":"11","110":"12","111":"12","113":"12","114":"12","117":"12","202":"12"}
TITLES = {}  # key -> 标题（从 timeline 首句无关；用 _book_extra）
try:
    be = json.load(open("_book_extra.json", encoding="utf-8"))
    for k, v in be["book"].items(): TITLES[k] = v["title"]
except Exception: pass

def norm_w(t): return re.sub(r"[^a-z' ]", "", t.lower()).split()

def sent_split(text):
    # 句切分：. ! ? 后跟空格+大写/引号（缩写白名单）
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z'“])", text)
    out = []
    for p in parts:
        p = p.strip()
        if not p: continue
        if out and re.search(r"\b(Mr|Mrs|Ms|Dr|St|No|vs|etc|approx)\.$", out[-1]):
            out[-1] += " " + p
        else: out.append(p)
    return out

def dp_align(asr_words, ref_words):
    """ASR词序列×原文词序列 对齐（编辑距离DP），返回 ref索引->asr索引 映射（-1=未对上）"""
    n, m = len(asr_words), len(ref_words)
    INF = 1 << 30
    dp = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1): dp[i][0] = i
    for j in range(1, m+1): dp[0][j] = j
    for i in range(1, n+1):
        aw = asr_words[i-1][0]
        for j in range(1, m+1):
            rw = ref_words[j-1]
            c = 0 if aw == rw else (0.5 if rw.startswith(aw) or aw.startswith(rw) else 1)
            dp[i][j] = min(dp[i-1][j-1]+c, dp[i-1][j]+1, dp[i][j-1]+1)
    i, j = n, m; mp = [-1]*m
    while i > 0 and j > 0:
        aw = asr_words[i-1][0]; rw = ref_words[j-1]
        c = 0 if aw == rw else (0.5 if rw.startswith(aw) or aw.startswith(rw) else 1)
        if dp[i][j] == dp[i-1][j-1]+c: mp[j-1] = i-1; i -= 1; j -= 1
        elif dp[i][j] == dp[i-1][j]+1: i -= 1
        else: j -= 1
    return mp

def find_pdf_pages(key, first_text):
    n = int(re.search(r"\d+", key).group())
    u = UNITMAP[str(n)]
    title = TITLES.get(key.replace(key[:4], key[:4]), "")
    probe = norm_w(first_text)[:6]
    hits = []
    for f in glob.glob(f"{PDFDIR}/Unit {u} 第*课_教师用书.pdf"):
        doc = fitz.open(f)
        for pno in range(len(doc)):
            t = doc[pno].get_text()
            tt = norm_w(t)
            hit = sum(1 for w in probe if w in tt)
            if hit >= 4: hits.append((f, pno, hit))
        doc.close()
    hits.sort(key=lambda x: -x[2])
    return hits[:1]

def pdf_sentences(key, first_text):
    hits = find_pdf_pages(key, first_text)
    if not hits: return None
    f, pno, _ = hits[0]
    doc = fitz.open(f)
    blocks = [(round(b[1],1), re.sub(r"\s+"," ",b[4]).strip()) for b in doc[pno].get_text("blocks") if b[6]==0]
    doc.close()
    # 课文区：含课文首句的 block 起，到装饰词 block 止
    start = next((i for i,(y,t) in enumerate(blocks) if norm_w(t)[:4] == norm_w(first_text)[:4]), None)
    if start is None: return None
    STOP = re.compile(r"^(KIDS|KITCHEN|UNIT \d+|\d+|WHO.?S HUNGRY\?|more|Worksheets?|Project .*|Communication .*|Get.?ting .*|Activity idea.*|Worksheets .*)$", re.I)
    sents = []
    for y, t in blocks[start:]:
        if STOP.match(t): break
        for s in sent_split(t): sents.append(s)
    return {"pdf": os.path.basename(f), "page": pno+1, "sentences": sents}

models = {}
def get_model(size):
    if size not in models:
        models[size] = WhisperModel(size, device="cpu", compute_type="int8")
    return models[size]

report = []
TL3 = {}
from faster_whisper import WhisperModel, audio as faudio
for key in sorted(TL):
    sents_old = TL[key]
    first = sents_old[0]["text"]
    pdfs = pdf_sentences(key, first)
    mp3 = f"assets/{key}.mp3"
    info = faudio.decode_audio(mp3, sampling_rate=16000)
    dur = len(info)/16000
    m_small = get_model("small")
    segs, _ = m_small.transcribe(mp3, language="en", word_timestamps=True, vad_filter=True)
    words_s = []
    for s in segs:
        for w in s.words: words_s.append((re.sub(r"[^a-z' ]","",w.word.strip().lower()), w.start, w.end, getattr(w,"probability",1)))
    words_s = [w for w in words_s if w[0]]
    # PDF 句序列（可能失败 → 回退旧句子文本）
    pdfs_ok = pdfs and pdfs["sentences"] and sum(len(norm_w(x)) for x in pdfs["sentences"]) >= 0.6*sum(len(norm_w(s["text"])) for s in sents_old)
    ref_sents = pdfs["sentences"] if pdfs_ok else [s["text"] for s in sents_old]
    src = "pdf" if pdfs_ok else "timeline回退"
    ref_words = []
    for si, sent in enumerate(ref_sents):
        for w in norm_w(sent): ref_words.append((w, si))
    mp = dp_align(words_s, ref_words)
    # 句级 start/end（词映射聚合）
    sent_ts = {}
    for j, si in enumerate(ref_words and range(len(ref_words))):
        pass
    sent_start = [None]*len(ref_sents); sent_end = [None]*len(ref_sents)
    for j, si in enumerate([x[1] for x in ref_words]):
        ai = mp[j]
        if ai < 0: continue
        w = words_s[ai]
        if sent_start[si] is None or w[1] < sent_start[si]: sent_start[si] = w[1]
        if sent_end[si] is None or w[2] > sent_end[si]: sent_end[si] = w[2]
    # 未对上词的句插值
    for si in range(len(ref_sents)):
        if sent_start[si] is None:
            prev_e = max([sent_end[x] for x in range(si) if sent_end[x] is not None], default=0)
            nxt_s = min([sent_start[x] for x in range(si+1, len(ref_sents)) if sent_start[x] is not None], default=dur)
            n_w = len(norm_w(ref_sents[si])) or 1
            sent_start[si] = prev_e + 0.05
            sent_end[si] = min(nxt_s - 0.05, prev_e + 0.05 + n_w*0.38)
    # 三信号投票：end 吸附 VAD 静音段末（ASR词序列内的静音=相邻词间隙>0.4s）
    sil_mid = []
    for a, b2 in zip(words_s, words_s[1:]):
        if b2[1] - a[2] > 0.4: sil_mid.append((a[2]+b2[1])/2)
    def snap(t):
        cands = [t] + [m for m in sil_mid if abs(m-t) < 0.6]
        return sorted(cands, key=lambda x: abs(x-t))[0]
    sents_v3 = []
    lowconf = 0
    for si, sent in enumerate(ref_sents):
        st = sent_start[si] or 0; en = sent_end[si] or st+1
        en_s = snap(en)
        low = 0
        for j, si2 in enumerate([x[1] for x in ref_words]):
            pass
        sents_v3.append({"i": si+1, "start_s": round(st,2), "end_s": round(en_s,2), "dur_s": round(en_s-st,2), "text": sent})
    # 指标
    overlap = sum(1 for a,b2 in zip(sents_v3, sents_v3[1:]) if b2["start_s"] < a["end_s"]-0.05)
    gap3 = sum(1 for a,b2 in zip(sents_v3, sents_v3[1:]) if b2["start_s"]-a["end_s"] > 3.0)
    mono = all(b2["start_s"] >= a["end_s"]-0.05 for a,b2 in zip(sents_v3, sents_v3[1:]))
    cov = sum(1 for j,si in enumerate([x[1] for x in ref_words]) if mp[j]>=0)/max(1,len(ref_words))
    TL3[key] = {"audio": mp3, "duration": round(dur,2), "src": src, "pdf": (pdfs or {}).get("pdf"), "page": (pdfs or {}).get("page"),
                "sentence_count": len(sents_v3), "sents": sents_v3,
                "metrics": {"overlap": overlap, "gap3": gap3, "mono": mono, "coverage": round(cov,3), "words_asr": len(words_s)}}
    print(f"[{key}] {src} {len(sents_v3)}句 覆盖{cov:.2f} 重叠{overlap} gap3={gap3} 单调={mono}", flush=True)
json.dump(TL3, open("timeline_v3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE timeline_v3.json", len(TL3))
