# Think F U1-U4 · 16 篇句级对齐（统一标准至 U5-U12）
# 情况2（9 篇，TB 源文本）：ASR 词级 × aligner 校准
# 情况1（7 篇，无稿听力）：ASR 段界即句界（Think F 情况1 方法论）
import os, re, json, glob

os.environ.setdefault("HF_HUB_OFFLINE", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
AUDIO_BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\003 第三版课程材料"
ALIGNER_HOME = r"D:\Trae Project\audio-aligner-v4.0.0"
SILENCE = {"enabled": True, "min_silence_duration": 0.3,
           "silence_threshold_db": -40, "boundary_tolerance": 0.15}
WORDS_CACHE = os.path.join(HERE, "_u14_words.json")

UNIT_DIR = {1: "U1_AllTogether", 2: "U2_ImExcited", 3: "U3_FamilyTime", 4: "U4_CityLife"}

# 情况1（无稿）6 篇规格（每单元恰 4 篇，与 U5-U12 同构；备考听力 2.08 按用户令移除）
ASR_ONLY = [
    dict(key="u1_p15_quiz", unit=1, page="p015", title="One-Minute Challenge", type="听力",
         track="1.05", audio="Thk2e_BE_L0_SB_Unit_1_p15_t05.mp3"),
    dict(key="u1_p18_daniela", unit=1, page="p018", title="Where is Daniela from?", type="口语",
         track="1.09", audio="109.mp3"),
    dict(key="u2_p23_dialogues", unit=2, page="p023", title="Four dialogues", type="听力",
         track="2.05", audio="Thk2e_BE_L0_SB_Unit_2_p23_t05.mp3"),
    dict(key="u3_p33_family", unit=3, page="p033", title="Three people talking", type="听力",
         track="3.03", audio="Thk2e_BE_L0_SB_Unit_3_p33_t03.mp3"),
    dict(key="u3_p36_photos", unit=3, page="p036", title="Paul and Carla", type="口语",
         track="3.09", audio="Thk2e_BE_L0_SB_Unit_3_p36_t09.mp3"),
    dict(key="u4_p41_directions", unit=4, page="p041", title="Asking for directions", type="听力",
         track="4.03", audio="Unit4-p41-listening-ex9.ex10.mp3"),
]

def resolve_audio(unit, fname):
    d = os.path.join(AUDIO_BASE, f"第{unit}单元", f"第{unit}单元 音频")
    p = os.path.join(d, fname)
    if os.path.exists(p):
        return p
    # 水印后缀变体
    for suf in ["[公众号happyshare2023]", "[公众号竹清童育]"]:
        stem, ext = os.path.splitext(fname)
        q = os.path.join(d, stem + suf + ext)
        if os.path.exists(q):
            return q
    raise FileNotFoundError(fname)

def run_asr(jobs):
    from faster_whisper import WhisperModel
    print("加载 faster-whisper small (cpu int8) ...", flush=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")
    out = {}
    for key, mp3 in jobs:
        segs, info = model.transcribe(mp3, language="en", word_timestamps=True,
                                      beam_size=1, vad_filter=False)
        words, seglist = [], []
        for s in segs:
            for w in (s.words or []):
                words.append([round(w.start, 3), round(w.end, 3), w.word.strip()])
            txt = re.sub(r"\s+", " ", s.text).strip()
            if txt:
                seglist.append([round(s.start, 3), round(s.end, 3), txt])
        out[key] = dict(words=words, segments=seglist, duration=round(info.duration, 2))
        print(f"[asr] {key} {info.duration:.1f}s -> {len(words)} 词 / {len(seglist)} 段", flush=True)
    return out

def segs_to_sentences(seglist, min_dur=0.8):
    """情况1：ASR 段界即句界；过短段与后续合并；滤除轨头报幕/栏目名/裸编号（坑#3）"""
    BAD = re.compile(
        r"^(Units? \d"                                                    # 报幕
        r"|(Listening|Reading|Speaking)\s*[.,]?(\s+[Ee]xercises?.*)?$"    # 栏目名 / 栏目+练习
        r"|Exercises?\b.*"                                                # Exercises 9 and 10
        r"|Example\b.*"                                                   # Example
        r"|\d{1,2}\.?\s*$"                                                # 裸编号
        r")")
    seglist = [s for s in seglist if not BAD.match(s[2].strip())]
    merged = []
    for st, en, tx in seglist:
        if merged and (en - st) < min_dur:
            merged[-1][1] = en
            merged[-1][2] = (merged[-1][2] + " " + tx).strip()
        else:
            merged.append([st, en, tx])
    return [dict(i=i, start_s=st, end_s=en, text=tx) for i, (st, en, tx) in enumerate(merged)]

def main():
    src = {p["key"]: p for p in json.load(open(os.path.join(HERE, "_u14_source.json"), encoding="utf-8"))}
    specs = []
    for p in src.values():
        specs.append(dict(p, case=2))
    for p in ASR_ONLY:
        specs.append(dict(p, case=1, lines=None, src="asr"))
    specs.sort(key=lambda s: (s["unit"], s["page"]))

    jobs = [(s["key"], resolve_audio(s["unit"], s["audio"])) for s in specs]
    if os.path.exists(WORDS_CACHE):
        cache = json.load(open(WORDS_CACHE, encoding="utf-8"))
        missing = [(k, p) for k, p in jobs if k not in cache]
        if missing:
            print(f"[asr] 补跑 {len(missing)} 个缺失轨: {[k for k, _ in missing]}")
            cache.update(run_asr(missing))
            json.dump(cache, open(WORDS_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        words_all = cache
    else:
        words_all = run_asr(jobs)
        json.dump(words_all, open(WORDS_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    sys_path = list(__import__("sys").path)
    __import__("sys").path.insert(0, ALIGNER_HOME)
    import aligner  # noqa: E402

    report = []
    for s in specs:
        key, unit, page = s["key"], s["unit"], s["page"]
        wa = words_all[key]
        mp3 = resolve_audio(unit, s["audio"])
        dur = wa["duration"]
        if s["case"] == 2:
            word_alignments = [{"text": w[2].strip(), "start": w[0], "end": w[1]} for w in wa["words"]]
            a = aligner.AudioTextAligner(mp3, language="en", silence_config=SILENCE, model_size="small")
            aligned = a.align_with_word_alignments("\n".join(s["lines"]), word_alignments)
            rows = [dict(i=i, start_s=round(x["start"], 3), end_s=round(x["end"], 3),
                         text=x["text"]) for i, x in enumerate(aligned)]
            low = sum(1 for x in aligned if (x.get("confidence") or 0) < 0.8)
            src_n = len(s["lines"])
        else:
            rows = segs_to_sentences(wa["segments"])
            low = -1
            src_n = len(rows)
        # 单调钳制
        prev = 0.0
        for r in rows:
            if r["start_s"] < prev:
                r["start_s"] = prev
            prev = r["end_s"]
        # 归档 JSON（Think F schema）
        doc = dict(unit=f"U{unit}", passage_key=key, page=page, title=s["title"],
                   type=s["type"], n_sent=len(rows), duration_s=dur,
                   source=("按课次教师用书文字层 × 句级音频对齐（情况2）" if s["case"] == 2
                           else "ASR 转写（情况1，无官方稿）"),
                   sentences=[dict(i=r["i"], start_s=r["start_s"], end_s=r["end_s"], text=r["text"])
                              for r in rows])
        outdir = os.path.join(BASE, UNIT_DIR[unit], "01_正文篇章")
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, f"句级数据_{page}.json"), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        report.append((key, s["case"], src_n, len(rows), low, rows[0]["start_s"] if rows else -1,
                       rows[-1]["end_s"] if rows else -1, dur))
        print(f"[ok] {key} 情况{s['case']} 源{src_n} -> {len(rows)} 句 低置信{low} "
              f"首{rows[0]['start_s'] if rows else -1}s 末{rows[-1]['end_s'] if rows else -1}s / {dur}s", flush=True)

    with open(os.path.join(HERE, "_u14_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
