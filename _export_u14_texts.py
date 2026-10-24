# Think F U1-U4 · 课文文本导出（analyzer 输入，格式对标 U5-U12）
# 情况2（10 篇）= _u14_source.json 的 TB 官方文本；情况1（6 篇）= ASR 转写（滤报幕）
import json, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "词汇诊断", "篇章文本_U1_U4")
SRC = json.load(open(os.path.join(HERE, "_u14_source.json"), encoding="utf-8"))
WORDS = json.load(open(os.path.join(HERE, "_u14_words.json"), encoding="utf-8"))

# 情况1 六篇的 ASR 文本源（轨号→key）
ASR_KEYS = {
    "u1_p15_quiz": "u1_p15_quiz", "u1_p18_daniela": "u1_p18_daniela",
    "u2_p23_dialogues": "u2_p23_dialogues", "u3_p33_family": "u3_p33_family",
    "u3_p36_photos": "u3_p36_photos", "u4_p41_directions": "u4_p41_directions",
}
TITLE_FIX = {
    "u1_p12_website": "All together (website)", "u2_p20_messages": "Text messages",
    "u2_p027_masks": "Masks from around the world", "u3_p30_families": "Famous families",
    "u4_p38_brochure": "Great cities", "u4_p45_parks": "Parks around the world",
}

def asr_text(key):
    segs = []
    for s in WORDS[key]["segments"]:
        tx = s[2].strip()
        # 滤指令性前缀：报幕/Listening/Exercises/Example/裸编号
        if re.match(r"^Units? \d", tx) or re.match(r"^(Listening|Reading|Speaking)", tx, re.I) \
           or re.match(r"^Exercises?\b", tx, re.I) or re.match(r"^Example\b", tx, re.I) \
           or re.fullmatch(r"\d{1,2}\.?", tx):
            continue
        segs.append(tx)
    return " ".join(segs)

def safe_fn(s):
    return re.sub(r'[?():*"<>|]', "", s).replace("  ", " ").strip()

os.makedirs(OUTDIR, exist_ok=True)
made = []
for p in SRC:
    key, unit, page = p["key"], p["unit"], p["page"]
    title = TITLE_FIX.get(key, p["title"])
    lines = [l.strip() for l in p["lines"] if l.strip()]
    # 对话轮次已是句子行；文章按行即句。组装为段落流（标题 + 全文）
    body = " ".join(lines)
    body = re.sub(r"\s{2,}", " ", body)
    # 命名统一 p%03d 补零约定（与篇章文本_U7_U12 一致，保证 _gen_vqdis.text_of 能按 p\d+ 命中）
    fn = safe_fn(f"Unit{unit}_{page}_{title}.txt")
    with open(os.path.join(OUTDIR, fn), "w", encoding="utf-8") as f:
        f.write(title + "\n" + body + "\n")
    made.append((fn, len(body), len(lines)))

# 情况1 六篇
ASR_TITLES = {
    "u1_p15_quiz": ("Unit1", "One-Minute Challenge"), "u1_p18_daniela": ("Unit1", "Where is Daniela from"),
    "u2_p23_dialogues": ("Unit2", "Four dialogues"), "u3_p33_family": ("Unit3", "Three people talking"),
    "u3_p36_photos": ("Unit3", "Paul and Carla"), "u4_p41_directions": ("Unit4", "Asking for directions"),
}
PAGE_OF = {"u1_p15_quiz": "p015", "u1_p18_daniela": "p018", "u2_p23_dialogues": "p023",
           "u3_p33_family": "p033", "u3_p36_photos": "p036", "u4_p41_directions": "p041"}
for key, (stem, title) in ASR_TITLES.items():
    body = asr_text(key)
    body = re.sub(r"\s{2,}", " ", body)
    fn = safe_fn(f"{stem}_{PAGE_OF[key]}_{title}.txt")
    with open(os.path.join(OUTDIR, fn), "w", encoding="utf-8") as f:
        f.write(title + "\n" + body + "\n")
    made.append((fn, len(body), -1))

for fn, n, nl in made:
    print(f"  {fn[:52]:54s} {n:5d} 字符" + (f"（{nl} 源行）" if nl >= 0 else "（ASR）"))
print(f"\n共 {len(made)} 个输入文件 → {OUTDIR}")
