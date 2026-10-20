# -*- coding: utf-8 -*-
"""词汇音频拉取器：剑桥真人发音（主）→ 有道（兜底）→ edge_tts（最终兜底，需依赖）。
   词源 = 主题词汇 theme_uN.json（仓库 00_主题词汇/，含全部单元）+ 12 篇篇章词汇产出 json 的 tokens（kind=word 的 lemma）。
   落盘 = 正典 Think F 教材资产/00_词汇音频/<word>.mp3
   索引 = audio_index.json {word: {f, src}}（落归档 00_词汇音频/ 一份）。
   用法：python _gen_vocab_audio.py"""
import json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(ROOT, "skills", "词汇教学技能包-20260928", "british-phonetics", "scripts")
sys.path.insert(0, PH)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
def dictvoice_url(word, t="2"):
    return "https://dict.youdao.com/dictvoice?audio=" + urllib.parse.quote(word) + "&type=" + t  # type=2 英音
AUD = os.path.join(ROOT, "..", "00_词汇音频")  # ROOT=github在线推送; ROOT/.. 即 Think F 教材资产
os.makedirs(AUD, exist_ok=True)

try:
    import edge_tts
    HAVE_TTS = True
except ImportError:
    HAVE_TTS = False

# ── 词集合 ──
words = {}
T00 = os.path.join(ROOT, "00_主题词汇")
for f in sorted(glob_json(T00, "theme_u*.json")) if False else []:
    pass
import glob
for f in glob.glob(os.path.join(T00, "theme_u*.json")):
    for w in json.load(open(f, encoding="utf-8")):
        words.setdefault(w["w"].lower().strip(), "theme")
VD = os.path.join(ROOT, "词汇诊断", "篇章词汇_产出")
for f in glob.glob(os.path.join(VD, "u*.json")):
    if os.path.basename(f).startswith("__") or f.endswith(".vocab.json"):
        continue
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    for t in d.get("tokens", []):
        if t.get("kind") == "word" and t.get("lemma"):
            words.setdefault(t["lemma"].lower().strip(), "passage")
print("词总数:", len(words), flush=True)

# ── 拉取 ──
def dl(url, word):
    bn = "".join(c for c in word if c.isalnum()) or "w"
    path = os.path.join(AUD, bn + ".mp3")
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return os.path.basename(path)
    try:
        req = urllib.request.Request(url, headers={**UA, "Referer": "https://dictionary.cambridge.org/"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if len(data) < 200:
            return ""
        open(path, "wb").write(data)
        return os.path.basename(path)
    except Exception:
        return ""

async def tts(word):
    bn = "".join(c for c in word if c.isalnum()) or "w"
    out = os.path.join(AUD, bn + ".mp3")
    await edge_tts.Communicate(word, "en-GB-LibbyNeural").save(out)
    return os.path.basename(out)

import asyncio
idx = {}
done = 0
for w in sorted(words):
    bn = "".join(c for c in w if c.isalnum()) or "w"
    path = os.path.join(AUD, bn + ".mp3")
    if os.path.exists(path) and os.path.getsize(path) > 200:
        idx[w] = {"f": bn + ".mp3", "src": "cache"}
        done += 1
        continue
    f = dl(dictvoice_url(w), w)
    src = "youdao-uk" if f else "none"""
    if not f and HAVE_TTS:
        try:
            f = asyncio.run(tts(w)); src = "edge_tts"
        except Exception as e:
            print("  tts 失败", w, str(e)[:60], flush=True)
    if f:
        idx[w] = {"f": f, "src": src or ("cambridge" if "cambridge" in (au or "") else "youdao")}
    else:
        idx[w] = {"f": "", "src": "none"}
    done += 1
    if done % 25 == 0:
        print("进度 %d/%d" % (done, len(words)), flush=True)
        json.dump(idx, open(os.path.join(AUD, "audio_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(0.35)

json.dump(idx, open(AUD + "/../audio_index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 索引统一落盘归档 00_词汇音频/audio_index.json（见上），不再写仓库根
ok = sum(1 for v in idx.values() if v["f"])
print("完成: %d/%d 有音频 | src 分布: %s" % (ok, len(idx),
      {s: sum(1 for v in idx.values() if v["src"] == s) for s in set(v["src"] for v in idx.values())}))
