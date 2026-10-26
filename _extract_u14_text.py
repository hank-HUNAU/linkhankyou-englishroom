# Think F U1-U4 · 有稿课文提取 v2（情况2：9 篇）
import fitz, warnings, os, re, json
warnings.filterwarnings("ignore")

LESSON = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产\00 按单元与课次教师用书_文字层可提取"
OUT = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产\github在线推送\_u14_source.json"

def load_lines(fn):
    d = fitz.open(os.path.join(LESSON, fn))
    t = "".join(p.get_text() for p in d)
    d.close()
    return [l.strip() for l in t.split("\n") if l.strip()]

def span(lines, start_kw, end_kw):
    si = next((i for i, l in enumerate(lines) if start_kw in l), None)
    if si is None:
        raise ValueError("起点未找到: " + start_kw)
    ei = next((j for j in range(si + 1, len(lines)) if end_kw in lines[j]), len(lines) - 1)
    return lines[si:ei + 1]

def join_wrapped(lines, speaker_aware=False):
    out = []
    for l in lines:
        if (out and not re.search(r"[.?!…\"”]$", out[-1])
                and not (speaker_aware and re.match(r"^[A-Z][a-z]+(\s[A-Z][a-z]+)?\s", l))):
            out[-1] = out[-1] + " " + l
        else:
            out.append(l)
    return out

def clean_turn(text):
    """说话轮次清洗：姓名/单数字填空（a/an 后的数字保留，如 A 5 Seconds）/标点间距"""
    m = re.match(r"^(Steve|Camila|Ruby|Ben|Lottie|Anna|Man|Girl|Woman)\b[ \t]*(.*)$", text)
    if m:
        text = m.group(2)
    toks = text.split()
    keep = []
    for i, t in enumerate(toks):
        if re.fullmatch(r"[0-9]", t):
            prev = toks[i-1].lower() if i else ""
            nxt = toks[i+1] if i + 1 < len(toks) else ""
            if prev in ("a", "an"):
                keep.append(t)          # A 5 Seconds of Summer
            elif nxt and nxt[0].isupper():
                keep.append(t)
            # 其余：纯填空编号，丢弃
            continue
        keep.append(t)
    s = " ".join(keep)
    s = re.sub(r"\s+([,.?!;:])", r"\1", s)
    s = re.sub(r"(\d)\s+([ap]\.?m\.?)\b", r"\1\2", s)
    return s.strip()

def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'‘“])", text)
    return [p.strip() for p in parts if p.strip()]

def dialogue_turns(seg, names):
    """说话轮次组装：'Name text' 或 Name 独占行"""
    turns, cur = [], None
    pat = re.compile(r"^(" + "|".join(names) + r")\b[ \t]*(.*)$")
    for l in seg:
        m = pat.match(l)
        if m:
            if cur is not None:
                turns.append(cur)
            cur = m.group(2)
        elif l in names:
            if cur is not None:
                turns.append(cur)
            cur = ""
        elif cur is not None:
            cur += " " + l
    if cur:
        turns.append(cur)
    return [clean_turn(t) for t in turns if t.strip()]

def article_sents(seg, headers=()):
    joined = join_wrapped(seg, speaker_aware=False)
    sents = []
    for l in joined:
        if l in headers or re.fullmatch(r"[A-F]", l):
            sents.append(l)
        else:
            sents.extend(split_sentences(l))
    return sents

P = []

# ============ U1 ============
lines = load_lines("Unit 1 第1次课_教师用书.pdf")
seg = span(lines, "CRAZY ABOUT", "Because he’s great!")
qa = []
for l in join_wrapped(seg, speaker_aware=False):
    l = re.sub(r"^(CRAZY ABOUT|FAVOURITE MUSICIAN!)\s*", "", l).strip()
    if l and not l.startswith(("H O M E", "A B O U T", "N E W S", "C O N T A C T", "tell us")):
        qa.append(l)
# 四段采访（每段 10 行，以 "What's your name?" 起）按**音频顺序**重排：
# 音频实际播 Cenc(土耳其/Izmir) → Jess(英国/Newcastle) → Flavia(巴西) → Li Jun(印尼)；
# TB 版面顺序是 Flavia 起头 —— 不对齐会把整段压进间隙（2026-10-26 回溯验证抓获）
_blocks, _cur = [], []
for _l in qa:
    if _l.lower().startswith("what’s your name") and _cur:
        _blocks.append(_cur); _cur = []
    _cur.append(_l)
if _cur:
    _blocks.append(_cur)
def _bid(b):
    t = " ".join(b).lower()
    if "izmir" in t: return 0      # 音频第 1 位
    if "newcastle" in t: return 1
    if "brazil" in t or "flavia" in t: return 2
    return 3                       # Li Jun（印尼/雅加达）
_blocks.sort(key=_bid)
assert len(_blocks) == 4, "u1_p12 采访段数异常: %d" % len(_blocks)
qa = [l for b in _blocks for l in b]
P.append(dict(key="u1_p12_website", unit=1, page="p012", title="All together (website)", type="阅读A",
              track="1.01", audio="Thk2e_BE_L0_SB_Unit_1_p12_t01.mp3", src="tb", lines=qa))

lines = load_lines("Unit 1 第3次课_教师用书.pdf")
seg = span(lines, "Steve Nice T-shirt.", "Steve Oh, OK! Bye!")
P.append(dict(key="u1_p16_tshirt", unit=1, page="p016", title="Nice T-shirt", type="阅读B",
              track="1.06", audio="Thk2e_BE_L0_SB_Unit_1_p16_t06.mp3", src="tb",
              lines=dialogue_turns(seg, ["Steve", "Camila"])))

# ============ U2 ============
lines = load_lines("Unit 2 第1次课_教师用书.pdf")
# 音频播送顺序 = Lizzie → Connor → Gemma → Jud（课本页序不同，坑#4：以音频顺序为准）
# thought bubble（warmer 图片心声）不在音频中，不取
seg = span(lines, "I’m at the cinema", "Where are my friends?")  # 整块消息区（含气泡，由块边界排除）
body = [l for l in seg if not re.fullmatch(r"(Gemma|Jud|Conner|Lizzie|No problem!)", l)
        and not re.fullmatch(r"\d{1,2}\.\d{2}", l)]
body = [re.sub(r"\s+\d{1,2}\.\d{2}(\s|$)", r"\1", l) for l in body]
flat = []
for l in join_wrapped(body, speaker_aware=False):
    flat.extend(split_sentences(l))

def block(flat, start_kw, end_kw):
    si = next(i for i, l in enumerate(flat) if start_kw in l)
    ei = next((j for j in range(si + 1, len(flat)) if end_kw in flat[j]), len(flat) - 1)
    return flat[si:ei + 1]

msgs = (block(flat, "Hi there, I’m at a party", "I’m sad.")
        + block(flat, "I’m at the computer shop", "cool things here!")
        + block(flat, "I’m at the cinema", "hungry and thirsty.")
        + block(flat, "We’re at the station", "six weeks!!!!!"))
P.append(dict(key="u2_p20_messages", unit=2, page="p020", title="Text messages", type="阅读A",
              track="2.01", audio="Thk2e_BE_L0_SB_Unit_2_p20_t01.mp3", src="tb", lines=msgs))

lines = load_lines("Unit 2 第3次课_教师用书.pdf")
seg = span(lines, "Ruby Hi, Ben", "It’s next week.")
P.append(dict(key="u2_p24_birthday", unit=2, page="p024", title="Ruby's birthday", type="阅读B",
              track="2.06", audio="Thk2e_BE_L0_SB_Unit_2_p24_t06.mp3", src="tb",
              lines=dialogue_turns(seg, ["Ruby", "Ben"])))

# 2.07 文化篇 Masks from around the world（第4次课 TB；音频顺序≠课本页序：墨西哥→中国→威尼斯→北美→万圣节，坑#4）
lines = load_lines("Unit 2 第4次课_教师用书.pdf")

def mask_block(start_kw, end_kw, keep_end=False):
    seg = span(lines, start_kw, end_kw)
    if not keep_end and end_kw in seg[-1]:
        seg = seg[:-1]  # 终点行属于下一块，丢弃
    out = []
    for l in join_wrapped(seg, speaker_aware=False):
        if l in ("Masks from around the world", "FROM AROUND THE WORLD", "sks.") or re.fullmatch(r"\d{1,2}", l):
            continue
        out.extend(split_sentences(l))
    return out

b_halloween = mask_block("These are Halloween masks.", "This mask is from Mexico.")
b_mexico = mask_block("This mask is from Mexico.", "Masks are an")
b_venice = mask_block("Masks are an", "This is a lion mask from China.")
b_china = mask_block("This is a lion mask from China.", "This mask is from North")
b_na = mask_block("This mask is from North", "for the medicine man.", keep_end=True)
masks = b_mexico + b_china + b_venice + b_na + b_halloween  # 按音频播送序
P.append(dict(key="u2_p027_masks", unit=2, page="p027", title="Masks from around the world", type="文化",
              track="2.07", audio="Thk2e_BE_L0_SB_Unit_2_p27_t07.mp3", src="tb", lines=masks))

# ============ U3 ============
lines = load_lines("Unit 3 第1次课_教师用书.pdf")
# 音频顺序 = Emma 先于 Chris（课本页序相反，坑#4）
emma = article_sents(span(lines, "Emma Watson is a famous", "Goodwill Ambassador."))
chris = article_sents(span(lines, "Chris Hemsworth is a famous", "India Rose."))
P.append(dict(key="u3_p30_families", unit=3, page="p030", title="Famous families", type="阅读A",
              track="3.01", audio="Unit 03-1 Reading.mp3", src="tb", lines=emma + chris))

lines = load_lines("Unit 3 第3次课_教师用书.pdf")
seg = span(lines, "Lottie So, is", "English teachers.")
P.append(dict(key="u3_p34_photo", unit=3, page="p034", title="Ellie's photo", type="阅读B",
              track="3.04", audio="Unit_3_p34_t04[reading].mp3", src="tb",
              lines=dialogue_turns(seg, ["Lottie", "Anna"])))

# ============ U4 ============
lines = load_lines("Unit 4 第1次课_教师用书.pdf")
seg = span(lines, "Istanbul, Turkey", "they love it!")
# 城市名头被朗读但不属正文句 —— 剥掉（Nara 的 "N" 在文字层丢失，一并修）
_bro = [l.replace("ara, Japan", "Nara, Japan") for l in article_sents(seg)]
for _i, _s in enumerate(_bro):
    for _h in ("Istanbul, Turkey", "Nara, Japan"):
        _s = re.sub(r"^" + re.escape(_h) + r"\s+", "", _s)
    _bro[_i] = _s
P.append(dict(key="u4_p38_brochure", unit=4, page="p038", title="Great cities", type="阅读A",
              track="4.01", audio="Unit4-p38-reading.mp3", src="tb", lines=_bro))

lines = load_lines("Unit 4 第3次课_教师用书.pdf")
i0 = next(i for i, l in enumerate(lines) if "Morning. Can I" in l)
seg = lines[i0 - 1:]  # 回退一行带上「Man」说话人标记
ei = next(j for j in range(1, len(seg)) if "You, too. Bye!" in seg[j])
seg = seg[:ei + 1]
P.append(dict(key="u4_p42_shop", unit=4, page="p042", title="Buying in a shop", type="阅读B",
              track="4.04", audio="4-p42-reading-ex1.mp3", src="tb",
              lines=dialogue_turns(seg, ["Man", "Girl", "Woman"])))

lines = load_lines("Unit 4 第4次课_教师用书.pdf")
seg = span(lines, "Villa Borghese is a big public park", "view of the city.")
# 6 座公园：题图标签 A-F + 城市名头被朗读但不属正文句 —— 从句首剥掉（只留正文）
PARK_HDR = ["Golden Gate Park, San Francisco, US", "Chapultepec Park, Mexico City, Mexico",
            "El Parque del Buen Retiro, Madrid, Spain", "The Iguana Park, Guayaquil, Ecuador",
            "Mount Faber Park, Singapore"]
park_sents = article_sents(seg)
for _i, _s in enumerate(park_sents):
    for _h in PARK_HDR:
        _s = re.sub(r"^[A-F]\s+" + re.escape(_h) + r"\s+", "", _s)
    park_sents[_i] = _s
P.append(dict(key="u4_p45_parks", unit=4, page="p045", title="Parks around the world", type="文化",
              track="4.12", audio="4-p45-culture-ex3.mp3", src="tb", lines=park_sents))

json.dump(P, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for p in P:
    print(f"{p['key']:18s} {p['type']:4s} {len(p['lines']):3d} 行 | 首: {p['lines'][0][:52]}")
    print(f"{'':18s}      末: {p['lines'][-1][:52]}")
