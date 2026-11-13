#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_gen_words_cache.py —— 为早期单元补 ASR 词级证据（只读音频，不碰时间轴）

背景：U5–U12 中 U7 / U8 / U12 是早期由硬编码脚本产出的，没有 `_unit_N_words.json`，
      导致全站「可机检对齐质量」核查缺 12 篇证据。本脚本只跑 faster-whisper 词级
      转写，**绝不**重跑 aligner、绝不写 timeline.json / 归档 JSON / SRT / 音频
      （守 `_RELEASE_WORKFLOW.md` 三条硬规约；音频前后 md5 会断言一致）。

产出（与既有链路同构）：
  `_unit_N_words.json`  {page: [[start, end, word], ...]}
      —— 旧格式，供 `_align_unit.py --unit N --skip-asr` 直接复用。
  `_unit_N_asr.json`    {page: {words, segments, duration}}
      —— 富格式，与 `_u14_words.json` 同构，供回溯验证 / 三方对账拿 segments 与时长。

用法：
  .venv-align/Scripts/python.exe _gen_words_cache.py --unit 7
  .venv-align/Scripts/python.exe _gen_words_cache.py --unit 7,8,12
  .venv-align/Scripts/python.exe _gen_words_cache.py --unit 8 --page p075   # 单篇试点
"""
import argparse
import hashlib
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

HERE = os.path.dirname(os.path.abspath(__file__))

# 本机 CTranslate2 small 模型目录（aligner 自带；HF 缓存里只有 medium，
# 且 HF_HUB_OFFLINE=1 下 snapshot_download 会报 LocalEntryNotFound → 直接传本地路径）
MODEL_DIR = r"D:\我的文档\audio-aligner-v4.0.0\dist\AudioAlignerVIP ver4.0.0\models\faster-whisper-small"

# 单元 → 4 篇正课文的 timeline 键（以 _ALIGNMENT_WORKFLOW.md §3 映射表为准）
PAGES = {
    7: ["p067", "p069", "p070", "p072"],
    8: ["p075", "p077", "p078", "p080"],
    12: ["p111", "p113", "p114", "p117"],
}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def words_path(unit):
    return os.path.join(HERE, "_unit_%d_words.json" % unit)


def asr_path(unit):
    return os.path.join(HERE, "_unit_%d_asr.json" % unit)


def run_unit(unit, model, only=None):
    tl = json.load(open(os.path.join(HERE, "assets", "timeline.json"), encoding="utf-8"))
    pages = only or PAGES[unit]

    # 前置校验：timeline 键存在、音频存在、音频未与 timeline 脱节
    audio_md5_before = {}
    for page in pages:
        if page not in tl:
            sys.exit("[x] timeline.json 缺 %s（U%d）" % (page, unit))
        mp3 = os.path.join(HERE, "assets", page + ".mp3")
        if not os.path.isfile(mp3):
            sys.exit("[x] 缺音频：%s" % mp3)
        audio_md5_before[page] = md5(mp3)

    words_out, asr_out = {}, {}
    for page in pages:
        mp3 = os.path.join(HERE, "assets", page + ".mp3")
        segs, info = model.transcribe(
            mp3, language="en", word_timestamps=True,
            beam_size=1, vad_filter=False,
        )
        words, segments = [], []
        for seg in segs:
            segments.append([round(seg.start, 3), round(seg.end, 3), (seg.text or "").strip()])
            for w in (seg.words or []):
                # 关键坑：faster-whisper 词文本带前导空格，必须 strip
                words.append([round(w.start, 3), round(w.end, 3), (w.word or "").strip()])
        words = [w for w in words if w[2]]
        if not words:
            sys.exit("[x] %s ASR 零词，疑似音频损坏或模型异常" % page)

        words_out[page] = words
        asr_out[page] = {
            "words": words,
            "segments": segments,
            "duration": round(float(info.duration), 3),
        }
        print("[asr] %s  %.2fs -> %d 词 / %d 段  (timeline %d 句)" % (
            page, info.duration, len(words), len(segments), len(tl[page])), flush=True)

    # 音频只增不改：断言 md5 未变
    for page in pages:
        mp3 = os.path.join(HERE, "assets", page + ".mp3")
        if md5(mp3) != audio_md5_before[page]:
            sys.exit("[x] 音频被改动：%s（违反硬规约）" % mp3)

    # 单篇试点时合并进已有缓存，避免覆盖另外 3 篇
    wp, ap = words_path(unit), asr_path(unit)
    if only:
        if os.path.isfile(wp):
            old = json.load(open(wp, encoding="utf-8"))
            old.update(words_out)
            words_out = old
        if os.path.isfile(ap):
            old = json.load(open(ap, encoding="utf-8"))
            old.update(asr_out)
            asr_out = old

    json.dump(words_out, open(wp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(asr_out, open(ap, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[ok] U%d 写入 %s (%d 篇) + %s；音频 md5 全一致" % (
        unit, os.path.basename(wp), len(words_out), os.path.basename(ap)), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", required=True, help="逗号分隔，如 7,8,12")
    ap.add_argument("--page", help="只跑一篇，如 p075")
    args = ap.parse_args()

    units = [int(x) for x in args.unit.split(",")]
    for u in units:
        if u not in PAGES:
            sys.exit("[x] 仅支持 U7/U8/U12（其余单元已有词级缓存）")

    if not os.path.isfile(os.path.join(MODEL_DIR, "model.bin")):
        sys.exit("[x] 本地 small 模型缺失：%s" % MODEL_DIR)
    print("加载 faster-whisper small (cpu int8) · 本地模型 %s" % MODEL_DIR, flush=True)
    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL_DIR, device="cpu", compute_type="int8")

    for u in units:
        run_unit(u, model, only=[args.page] if args.page else None)


if __name__ == "__main__":
    main()
