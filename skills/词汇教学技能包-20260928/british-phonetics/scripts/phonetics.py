# -*- coding: utf-8 -*-
"""英式语音语调软分支·后处理
主技能 article-vocab-analyzer 的任务结果(分层+词性+CEFR+原句) → 逐词联网补**英式音标(UK IPA)+英女真人发音**，
并把原句做成**朗读标注**(意群/强读弱读/重音位置/语调提示)，供教师课堂讲授与学生跟读双用。

与 student-vocab-cards 区分：学生卡偏"词义-记忆"，本分支只取**发音维**，尽量少联网、按需 --limit。

用法:
  python phonetics.py --file 课文.txt --out 英式语音卡
  python phonetics.py --text "..." --out 语音
  python phonetics.py --file 课文.txt --limit 10 --offline   # 少联网/断网快速出静态标注
"""
import os, sys, re, json, io, time, html, subprocess, urllib.parse
import urllib.request, argparse

def _main_dir():
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        cand = os.path.join(d, "skills", "article-vocab-analyzer")
        if os.path.exists(os.path.join(cand, "scripts", "assess_vocab.py")):
            return os.path.abspath(cand)
        d = os.path.dirname(d)
    return None
MAIN = _main_dir() or os.path.abspath("article-vocab-analyzer")
ASSESS = os.path.join(MAIN, "scripts", "assess_vocab.py")
# worktree 平铺优先：本文件同级有 assess_vocab.py 时用它(开发版最新)，否则回退部署位
_flat = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assess_vocab.py")
if os.path.exists(_flat):
    ASSESS = _flat
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "Referer": "https://dict.youdao.com/"}

# ---------- 1. 调主技能：json(lemma/layer/cefr) + report.xlsx(词性/原句) ----------
def run_main(text=None, file=None, stem="ph_tmp"):
    cmd = [sys.executable, ASSESS, "--out", stem]
    cmd += ["--text", text] if text else ["--file", file]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL)
    toks = json.load(io.open(stem + ".json", encoding="utf-8"))["tokens"]
    words = {}
    propers = set()                       # 专名(kind=proper，主技能已按"首字母大写且未收录"分流)
    for t in toks:
        if t.get("kind") == "proper" and t.get("form"):
            propers.add(t["form"].lower())
        if t.get("kind") not in ("word", "out"):
            continue
        lm = t.get("lemma", "")
        if not lm:
            continue
        words.setdefault(lm, {"layer": t.get("layer", ""), "cefr": t.get("cefr", ""), "forms": []})
        f = t.get("form", "")
        if f and f not in words[lm]["forms"]:
            words[lm]["forms"].append(f)
    import openpyxl
    wb = openpyxl.load_workbook(stem + ".xlsx", read_only=True)
    meta = {}
    for sn in wb.sheetnames:
        ws = wb[sn]
        for row in ws.iter_rows(values_only=True):
            if not row or not row[0]:
                continue
            c = list(row)
            if sn.startswith("命中"):
                if len(c) < 7:
                    continue
                w = c[0]
                # 跳过表头/中文标签行(如"词"、"词/短语")——真词必含英文字母
                if not re.search(r"[A-Za-z]", str(w)) or not isinstance(w, str) or len(w) >= 40:
                    continue
                if w not in meta:
                    meta[w] = {"pos": c[1] or "", "type": c[2] or "", "freq": c[3], "cefr": c[5] or "",
                               "example": c[6] or ""}
            elif sn == "超纲词" and len(c) >= 2 and re.search(r"[A-Za-z]", str(c[0])):
                meta.setdefault(c[0], {}).update({"cefr": c[2] if len(c) > 2 else "", "pos": "",
                                                  "example": c[3] if len(c) > 3 else ""})
    wb.close()
    return words, meta, propers

# ---------- 2. 有道：英式音标(ukphone) + 英女真人发音(ukspeech) ----------
def youdao_en(word):
    try:
        url = "https://dict.youdao.com/jsonapi?q=" + urllib.parse.quote(word)
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=12) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        sw = {}
        sim = d.get("simple") or {}
        if isinstance(sim, dict) and isinstance(sim.get("word"), list) and sim.get("word"):
            sw = sim["word"][0]
        ipa = sw.get("ukphone") or ""                      # 英式音标优先(默认英·女)
        au = (sw.get("ukspeech") or "").split("&type=")[0]  # 英音音频
        return ipa, au
    except Exception:
        return "", ""

# ---------- 2b. 剑桥词典(第三方抓取API, 入口见 github hank-HUNAU 词汇查询助手) ----------
def cambridge_en(word):
    """剑桥英汉词典 → (UK音标, UK真人音频url)。有道缺词条时的二级兜底。"""
    try:
        url = "https://dictionary-api.eliaschen.dev/api/dictionary/en-cn/" + urllib.parse.quote(word)
        req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"], "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as r:
            d = json.loads(r.read().decode("utf-8", "ignore"))
        uk = {}
        for p in (d.get("pronunciation") or []):
            if p.get("lang") == "uk":
                uk = p
                break
        # 剑桥 pron 可能形如 "strong /biː/ weak /bɪ/" → 取强读(引读)形式单条
        raw = uk.get("pron") or ""
        chunks = re.findall(r"/[^/]+/", raw)
        ipa = (chunks[0] if chunks else raw).strip("/")   # 剑桥风格: 带音节点/含 r 拼写
        return ipa, uk.get("url") or ""
    except Exception:
        return "", ""

def ph_en(word, cambridge=True):
    """统一取音：剑桥词典API首选 → 有道兜底。返回 (ipa, 音频, 源标识)。"""
    if not cambridge:
        ipa, au = youdao_en(word)
        return ipa, au, "youdao"
    ipa, au = cambridge_en(word)
    if ipa or au:                       # 剑桥命中(含无音标但有音频等边界)
        return ipa, au, "cambridge"
    ipa, au = youdao_en(word)
    return ipa, au, "youdao"

def _au_src(au):
    """给音源列打标签：本地下载的词典真人mp3 / 有道URL / 剑桥URL / 本地edge mp3。"""
    if not au:
        return ""
    if "http://" in au or "https://" in au:
        if "dict.youdao.com" in au:
            return "有道英音(URL)"
        if "cambridge.org" in au:
            return "剑桥真人(URL)"
        return "在线音频(URL)"
    return "本地mp3(真人)"      # 下载到本地的词典真人发音(非URL)

# ---------- 3. 英式音标里的重音位置 ----------
def _stress_mark(ipa):
    """从英式音标提取重音节提示：ˈ 或 ' 后的音节为重音节(返回 主重音/次重音/无)。"""
    if not ipa:
        return ""
    if "ˈ" in ipa or re.search(r"\b'\w", ipa) or re.search(r"(?i)'[aeiou]", ipa):
        return "主重音"
    if "ˌ" in ipa:
        return "次重音"
    return "单音节/重音在首"

# ---------- 4. 虚词弱读表(静态常量，发音教学用) ----------
WEAK = {
    "a": "ə", "an": "ən", "the": "ðə(辅)/ði(元)", "and": "ənd", "of": "əv", "to": "tə",
    "for": "fə", "from": "frəm", "at": "ət", "as": "əz", "but": "bət", "than": "ðən",
    "that": "ðət", "can": "kən", "could": "kəd", "would": "wəd", "should": "ʃəd",
    "must": "məs", "do": "də", "does": "dəz", "have": "həv", "has": "həz", "had": "həd",
    "are": "ə", "was": "wəz", "were": "wə", "is": "z/ɪz", "am": "əm", "not": "nt",
    "us": "əs", "them": "ðəm", "your": "jə", "you": "jə", "him": "ɪm", "her": "ə",
    "some": "səm", "there": "ðə",
}

def _tts_note(word):
    """对虚词给出弱读注释(朗读教学起点)；实词返回空由教师自行决定。"""
    return WEAK.get(word.lower(), "")

# ---------- 3c. 专名音标补全：人工核注表 + 内置常用名读音库 ----------
# 词典类源(有道/剑桥)均收入名词条很少，人名词常用下列两途径补：
#  1) NAMED_IPA：本课文专名人工核注表(教师可随课文在此增补；取音以主流词典姓名条目为准)。
#  2) names_ipa.json：随技能附带的常用英美姓名读音库(skill 数据文件，非具体课文内容)，开箱覆盖常见名。
# 查序：NAMED_IPA(教师核注优先) → names_ipa.json → 联网不足时留待方案A清单核注。
NAMED_IPA = {
    "maureen": "mɔːˈriːn",
}
def _load_names():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "names_ipa.json")
    try:
        if os.path.exists(p):
            return json.load(io.open(p, encoding="utf-8"))
    except Exception:
        pass
    return {}
NAMES_IPA = _load_names()

# ---------- 5. 原句朗读标注：意群切分 + 停顿 + 语调 ----------
def _senti_split(s):
    """按标点把原句切成意群，返回 [ (片段, 末尾语调标记), ... ]。
    语调启发式：句号/句末→降调 ∨；问号→升调 ∧；逗号/连词后→停顿 ⊣。"""
    if not s:
        return None
    parts = re.split(r"([,;:.?!])", s.strip())
    groups, buf = [], ""
    for i in range(0, len(parts)):
        tok = parts[i]
        is_q = parts[i - 1] == "?" and i > 0
        intro = parts[i - 1] and parts[i - 1] not in " ,;:." and parts[i - 1] != " "
        if tok in ",;:":
            groups.append((buf.strip(), "⊣停顿"))
            buf = ""
        elif tok in "!?":
            groups.append((buf.strip(), "∧升调" if is_q or tok == "?" else "∨降调(惊叹)"))
            buf = ""
        elif tok == ".":
            groups.append((buf.strip(), "∨降调"))
            buf = ""
        else:
            buf += tok
    if buf.strip():
        groups.append((buf.strip(), "∨降调"))
    return [g for g in groups if g[0]] or None

# ---------- 5a. 页1·逐词列对齐：上方标音标 + 意群独立合并标记 ----------
def _write_lantsheet(ws, rels, words, ipa_map, offline, cambridge=True, propers=(), missing=None, learned=None):
    """按意群把原句逐词一列铺开：上方一行放英式音标(与词同列对齐)，
    下方一行用合并单元格在意群段中央放 ⊣停连 / ∨降调 / ∧升调。返回去重句数。
    propers: 专名词形集合；missing: 见证 dict{专名: 频次} 收集仍未标出音标的专名(方案A清单)；
    learned: 见证 dict{专名: 音标} 收集已解析但内置库缺的专名(回写更新库)。"""
    from openpyxl.utils import get_column_letter
    # 功能词(虚词)不上方标音标，只标实词——朗读教学惯例：虚词靠弱读表(页3)提示
    FUNCTION = set(WEAK) | set((
        "be am are is was were been being do does did "
        "have has had having will would shall should can could may might must "
        "i you he she it we they me him her us them my your his its our their "
        "this that these those who whom whose which what some any no none all "
        "both each every many much and but or nor yet if when while because "
        "although though since unless until than as that whether "
        "of at in on to for from with without by about into through over under "
        "between among not there").split())
    # 词形→lemma 反查：原句里遇到变形词(如 went)能回到 lemma 的音标
    lem_of = {}
    for lm, rec in words.items():
        lem_of.setdefault(lm.lower(), lm)
        for f in rec["forms"]:
            lem_of.setdefault(f.lower(), lm)
    cache = {k.lower(): v for k, v in ipa_map.items()}   # 复用主循环已取 lemma 音标

    def _fetch(w):
        """联网取一个词形的英式音标(只用音标)。"""
        if offline:
            return ""
        return ph_en(w, cambridge=cambridge)[0]

    def ipa_for(raw):
        t = raw.strip(".,!?;:'\"()[]…")
        if not re.search(r"[A-Za-z]", t):
            return ""
        lc = t.lower()
        if not lc or lc in FUNCTION:            # 虚词不标音标
            if lc:
                cache[lc] = ""
            return ""
        if lc in cache:
            return cache[lc]
        ov = NAMED_IPA.get(lc) or NAMES_IPA.get(lc)   # 专名核注/内置读音库 优先于联网
        if ov:
            cache[lc] = ov
            if learned is not None and lc in propers and NAMED_IPA.get(lc) and lc not in NAMES_IPA:
                learned[lc] = ov   # 教师核注的新专名 → 汇总待回写库
            return ov
        if "-" in t:                             # 连字符复合词：整体优先，失败按段拼
            v = ipa_map.get(t) or _fetch(t)
            if v:
                cache[lc] = v
                return v
            seg = " / ".join(p for p in (_fetch(x) for x in t.split("-")) if p)
            if seg:
                cache[lc] = seg
                return seg
        # 词形自身音标优先：先查词目缓存/直达源；屈折形特殊处理(见下)
        lm = lem_of.get(lc)
        v = ipa_map.get(t) or ipa_map.get(t.capitalize())
        if not v and lm and lm.lower() != lc and not offline:
            # 屈折/派生形：剑桥会归并到词目(如 waited→weɪt)丢表层读音，
            # 改为先取表层精确音(有道覆盖屈折词形: waited→ˈweɪtɪd)
            v, _ = youdao_en(t)
        if not v:
            v = _fetch(t)                       # 词典直查(剑桥首选→有道兜底)
        if not v and lm:                        # 最终回退词目音标
            v = ipa_map.get(lm, "")
        cache[lc] = v
        if not v and missing is not None and lc in propers:
            missing[lc] = missing.get(lc, 0) + 1   # 归档待核注专名(方案A)
        elif v and learned is not None and lc in propers and lc not in NAMES_IPA:
            learned[lc] = v                        # 联网解析出的新专名 → 汇总待回写库
        return v

    ws.append(["★ 原句朗读标注：上方=英式音标(UK)，下方=意群标记  ⊣停连 / ∨降调 / ∧升调 ] 教学分层与词性见页2"])
    seen = set()
    cur = 2
    for w, m in rels:
        ex = m["example"]
        if not ex or ex in seen:
            continue
        grp = _senti_split(ex)
        if not grp:
            continue
        seen.add(ex)
        ipa_c, word_c, tag_c = [], [], []
        col = 1
        for seg, tag in grp:
            toks = re.findall(r"\S+", seg) or [seg]
            gs = col
            for tok in toks:
                ipa_c.append((col, ipa_for(tok)))
                word_c.append((col, tok))
                col += 1
            tag_c.append((gs, col - 1, tag))
        r_ipa, r_w, r_tag = cur, cur + 1, cur + 2
        for c, v in ipa_c:
            ws.cell(r_ipa, c, v)
        for c, v in word_c:
            ws.cell(r_w, c, v)
        for gs, ge, tag in tag_c:
            ws.merge_cells(start_row=r_tag, start_column=gs, end_row=r_tag, end_column=ge)
            ws.cell(r_tag, gs, tag)
        cur += 4                                     # 每句占 音标/原文/标记 + 空行
    # 统一列宽，保证音标与词上下对齐
    for c in range(1, col):
        ws.column_dimensions[get_column_letter(c)].width = 15
    return len(seen)

# ---------- 5b. 性别可控的英式真人发音(微软 edge_tts 神经语音) ----------
# 声线: en-GB-RyanNeural(男) / en-GB-ThomasNeural(男) / en-GB-LibbyNeural(女) / en-GB-SoniaNeural(女)
def _tts_mp3(word, voice, tts_dir):
    """edge_tts 生成一词的英式真人 mp3，返回相对文件名；失败返回空。"""
    import asyncio, edge_tts
    bn = "".join(c for c in word if c.isalnum()) or "w"
    path = os.path.join(tts_dir, bn + ".mp3")
    try:
        asyncio.run(edge_tts.Communicate(word, voice).save(path))
        return bn + ".mp3"
    except Exception as e:
        sys.stderr.write("  [tts跳过] %s : %s\n" % (word, e))
        return ""

# ---------- 5c. 下载词典真人发音到本地mp3(剑桥首选→有道兜底) ----------
def _download_audio(word, url, au_dir):
    """把真人发音音频URL(curl 可得的 mp3)下载到 au_dir 下，返回相对文件名；失败返回空。"""
    if not url:
        return ""
    bn = "".join(c for c in word if c.isalnum()) or "w"
    path = os.path.join(au_dir, bn + ".mp3")
    if os.path.exists(path):
        return bn + ".mp3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA["User-Agent"], "Referer": "https://dictionary.cambridge.org/"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if len(data) < 200:               # 防空mp3/错误页
            return ""
        with open(path, "wb") as f:
            f.write(data)
        return bn + ".mp3"
    except Exception:
        return ""

# ---------- 6. 主流程 ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file"); ap.add_argument("--text")
    ap.add_argument("--out", default="英式语音卡")
    ap.add_argument("--limit", type=int, default=0, help="只对前N词联网取音(调试/防限流)")
    ap.add_argument("--offline", action="store_true", help="断网: 只出静态朗读标注, 不取音标")
    ap.add_argument("--voice", choices=["youdao", "gb-male", "gb-female"], default="youdao",
                    help="英式真人发音来源: youdao(默认)=下载剑桥→有道真人发音到本地mp3 / gb-male=英男edge_tts / gb-female=英女edge_tts")
    ap.add_argument("--no-cambridge", action="store_true", help="关闭剑桥主源，只用有道(缺词条时不转查剑桥)")
    ap.add_argument("--no-tts", action="store_true",
                    help="禁用TTS兜底(通常在管道调用或非交互场景)：剑桥+有道下载不到宁可留空也不触发TTS")
    a = ap.parse_args()
    stem = "__ph_" + a.out
    words, meta, propers = run_main(a.text, a.file, stem)
    # 逐词联网取 英标+英音；顺序稳定
    order = sorted(words)
    ipa_map, au_map = {}, {}
    voice = a.voice
    VN = {"gb-male": "en-GB-RyanNeural", "gb-female": "en-GB-LibbyNeural"}
    tts_dir = a.out + "_tts"
    if not a.offline:
        os.makedirs(tts_dir, exist_ok=True)
    n = len(order)
    tts_missing = []            # 剑桥+有道均下载不到的词 → 需TTS兜底
    if not a.offline:
        for i, w in enumerate(order[:a.limit] if a.limit else order, 1):
            ipa, au, src = ph_en(w, cambridge=not a.no_cambridge)   # 剑桥首选→有道兜底
            if ipa:
                ipa_map[w] = ipa
            if voice == "youdao":
                # 构建下载URL：剑桥为完整官方URL，有道需拼 dictvoice
                url = au if (au and src == "cambridge") else (
                    "https://dict.youdao.com/dictvoice?audio=%s&type=1" % au) if au else ""
                fname = _download_audio(w, url, tts_dir)
                if fname:
                    au_map[w] = fname                                  # 本地mp3文件名
                elif not a.no_tts:
                    tts_missing.append(w)                             # 两源都无 → 待TTS确认
            elif tts_dir:
                mp3 = _tts_mp3(w, VN[voice], tts_dir)
                if mp3:
                    au_map[w] = mp3
            if i % 20 == 0:
                sys.stderr.write("  [%d/%d] %s\n" % (i, n, w))
            time.sleep(0.12)
        # TTS 兜底：仅 youdao 模式、download 失败、且非 --no-tts(非交互/管道) 时，经确认才执行
        if tts_missing and voice == "youdao" and not a.no_tts:
            sys.stderr.write("\n[需要TTS兜底] %d 个词剑桥/有道均无音频(词典源取不到真人发音): %s\n"
                             % (len(tts_missing), ", ".join(tts_missing)))
            if hasattr(sys, "stdin") and sys.stdin and sys.stdin.isatty():
                ans = input("  是否用edge_tts为这些词生成真人发音mp3? [y/N]: ").strip().lower()
                if ans in ("y", "yes"):
                    for w in tts_missing:
                        mp3 = _tts_mp3(w, VN["gb-female"], tts_dir)   # 默认英女
                        if mp3:
                            au_map[w] = mp3
                else:
                    sys.stderr.write("  跳过TTS，这些词音源列留空。\n")
            else:
                sys.stderr.write("  非交互环境(TTS需确认)，已跳过；如需可用 --voice gb-male/gb-female 显式生成。\n")
    # 整句去重(朗读页)
    rels = [(w, m) for w, m in meta.items() if m.get("example")]
    import openpyxl
    wb = openpyxl.Workbook()
    # 页1 朗读标注：逐词列对齐 + 上方音标 + 意群独立合并标记
    ws = wb.active; ws.title = "原句朗读标注"
    missing = {}
    learned = {}
    seen = _write_lantsheet(ws, rels, words, ipa_map, a.offline, cambridge=not a.no_cambridge,
                            propers=propers, missing=missing, learned=learned)
    # 页2 单词音标卡
    ws2 = wb.create_sheet("单词英式音标")
    ws2.append(["词汇", "教学梯度层", "词性", "英式音标UK", "重音提示", "弱读/朗读提示", "英式真人发音", "音源", "原文照搬"])
    BAND = {"KET": "全员(基础)", "PET": "全员(基础)", "NGSL": "中阶", "NAWL": "中强", "out": "中强(超纲/进阶)"}
    for w in order:
        m = meta.get(w, {})
        lay = words[w]["layer"]
        ipa = ipa_map.get(w, "")
        st = _stress_mark(ipa) if ipa else ""
        wk = _tts_note(w)
        au = au_map.get(w, "")
        src = _au_src(au)
        ws2.append([w, BAND.get(lay, lay), m.get("pos", ""), ipa, st, wk, au, src, m.get("example", "")])
    # 页3 语音规则备忘
    ws3 = wb.create_sheet("语音讲授要点")
    ws3.append(["类别", "要点", "示例"])
    ws3.append(["弱读(功能词)", "虚词在句中常弱读为中央元音/缩短，是英式流畅语流关键", "to→tə, of→əv, and→ənd, at→ət"])
    ws3.append(["强读/弱读切换", "句首/重读强调时用强读，句中非重读用弱读", "I can /kæn/ (强调) vs I can /kən/ (常用)"])
    ws3.append(["重音位置", "先看英式音标元音前的 ˈ 符号，落在该音节为重读", "example => eˈxample，重音在第二音节"])
    ws3.append(["读升调", "是非问句(yes/no)句末升调 ∧；陈述句降调 ∨", "Are you ready? ∧ / It's Monday. ∨"])
    ws3.append(["读停顿休息", "逗号/连词后可有气群停顿 ⊣，句点处换气", "I waited, ⊣ and then he came."])
    for w in sorted(WEAK):
        ws3.append(["本课弱读词：" + w, WEAK[w], next((m2.get("example", "") for w2, m2 in meta.items() if w2.lower() == w and m2.get("example")), "")])
    out = a.out + ".xlsx"
    wb.save(out)
    for f in (stem + ".json", stem + ".xlsx"):
        try: os.remove(f)
        except OSError: pass
    have_ipa = sum(1 for w in order if w in ipa_map)
    print("完成: %d 词 / %d 个原句朗读标注 / 英标覆盖 %d 词（限流可用 --limit 分批）→ %s" % (len(order), seen, have_ipa, out))
    if missing:   # 方案A：列出仍未补出音标的专名，教师核注进 NAMED_IPA 后二跑即全绿
        sys.stderr.write("\n[待核注专名清单] 以下专名词典源未收录音标，请在 phonetics.py 的 NAMED_IPA 表按需增补一行后重跑：\n")
        for w, c in sorted(missing.items(), key=lambda x: -x[1]):
            sys.stderr.write("    %s   ×%d   →  \"%s\": \"音标\",\n" % (w, c, w))
        sys.stderr.write("\n")
    if learned and not a.offline:   # 内置库自学习：本次解析出的新专名回写 names_ipa.json
        added = {k: learned[k] for k in learned if k not in NAMES_IPA}
        if added:
            NAMES_IPA.update(added)
            _nsf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "names_ipa.json")
            try:
                io.open(_nsf, "w", encoding="utf-8").write(
                    json.dumps(NAMES_IPA, ensure_ascii=False, indent=1))
                print("已回写内置读音库 names_ipa.json，新增 %d 个专名" % len(added))
            except Exception as e:
                sys.stderr.write("内置库回写失败: %s\n" % e)

if __name__ == "__main__":
    main()