# -*- coding: utf-8 -*-
"""方案 B 全量：12 篇转写 + 用已知文本顺序匹配反推句边界，与当前时间轴比对。"""
import json
import os
import re
import sys

from faster_whisper import WhisperModel

ROOT = os.path.dirname(os.path.abspath(__file__))
TJ = json.load(open(os.path.join(ROOT, "assets", "timeline.json"), encoding="utf-8"))


def norm(w):
    return re.sub(r"[^a-z0-9']", "", str(w).lower())


def edit1(a, b):
    """允许 1 个编辑距离的宽松相等。"""
    if a == b:
        return True
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b) if x != y) <= 1
    if len(a) > len(b):
        a, b = b, a
    i = j = 0
    diff = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            diff += 1
            j += 1
            if diff > 1:
                return False
    return True


def main():
    print("load faster-whisper small (cpu int8) ...", flush=True)
    model = WhisperModel("small", device="cpu", compute_type="int8")

    order = sorted(TJ.keys(), key=lambda k: int(k.replace("p", "")))
    all_words = {}
    derived = {}
    for key in order:
        audio = os.path.join(ROOT, "assets", key + ".mp3")
        segs, info = model.transcribe(audio, language="en", word_timestamps=True,
                                      beam_size=1, vad_filter=False)
        ws = []
        for seg in segs:
            for w in (seg.words or []):
                n = norm(w.word)
                if n:
                    ws.append((w.start, w.end, n))
        all_words[key] = ws
        print("%s  %.1fs  ->  %d words" % (key, info.duration, len(ws)), flush=True)

        # 顺序匹配：每句的目标词序列在识别词流里依次找
        n = len(TJ[key])
        clean = [[norm(w) for w in re.split(r"\s+", s["text"]) if norm(w)] for s in TJ[key]]
        cursor = 0
        bounds = []          # 每句的 (first_idx, last_idx) 在 ws 中的位置
        for words in clean:
            if not words:
                bounds.append(None)
                continue
            first = last = None
            for tw in words:
                found = None
                for j in range(cursor, min(cursor + 12, len(ws))):
                    if edit1(tw, ws[j][2]):
                        found = j
                        break
                if found is None:
                    break
                cursor = found + 1
                if first is None:
                    first = found
                last = found
            bounds.append((first, last) if first is not None else None)
        derived[key] = bounds

    json.dump(all_words, open(os.path.join(ROOT, "_whisper_all_words.json"), "w", encoding="utf-8"),
              ensure_ascii=False)

    print("")
    print("=" * 78)
    print("B 反推的句边界 vs 当前时间轴")
    print("=" * 78)
    out = {}
    for key in order:
        ws = all_words[key]
        bounds = derived[key]
        n = len(TJ[key])
        got = []
        for k in range(n):
            b = bounds[k]
            if b is None:
                got.append(None)
                continue
            f, l = b
            got.append([round(ws[f][0], 3), round(ws[l][1], 3)])
        out[key] = got
        # 内部边界比对（句 k 的终点）
        miss = sum(1 for g in got if g is None)
        deltas = []
        for k in range(n - 1):
            if got[k] is None or got[k + 1] is None:
                continue
            b_derived = (got[k][1] + got[k + 1][0]) / 2.0
            b_cur = TJ[key][k]["end_s"]
            deltas.append((k, b_cur, b_derived, b_derived - b_cur))
        big = [d for d in deltas if abs(d[3]) > 0.30]
        print("%-6s 句数 %3d  未匹配 %2d  可比边界 %3d  偏差>0.3s 的 %2d 条"
              % (key, n, miss, len(deltas), len(big)), flush=True)
    json.dump(out, open(os.path.join(ROOT, "_whisper_bounds.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("")
    print("=== 偏差最大的 20 条边界 ===")
    rows = []
    for key in order:
        ws = all_words[key]
        got = out[key]
        n = len(TJ[key])
        for k in range(n - 1):
            if got[k] is None or got[k + 1] is None:
                continue
            b_derived = (got[k][1] + got[k + 1][0]) / 2.0
            b_cur = TJ[key][k]["end_s"]
            rows.append((abs(b_derived - b_cur), key, k, b_cur, b_derived,
                         TJ[key][k]["text"][-30:], TJ[key][k + 1]["text"][:30]))
    rows.sort(reverse=True)
    for d, key, k, cur, der, tail, head in rows[:20]:
        print("  %-6s #%-2d  当前 %8.3f  B %8.3f  Δ%+6.3f | …%s | %s…"
              % (key, k, cur, der, der - cur, tail, head))


if __name__ == "__main__":
    main()
