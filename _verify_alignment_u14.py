# Think F U1-U4 · 音频↔文本 回溯验证（词数配比 + 覆盖率 + 间隙漏检）
# 原理：ASR 专名会错，但**词数大体守恒**。若某句窗口内 ASR 词数远小于该句词数 → 音频没落在这个窗口（错位）；
#       若窗口内词数远大于句词数 → 抢了邻句；若大间隙里还有成串 ASR 词 → 漏句。
import json, os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
W = json.load(open(os.path.join(HERE, "_u14_words.json"), encoding="utf-8"))

def wc(s):
    return len(re.findall(r"[A-Za-z'’]+", s or ""))

def check(key, verbose=False):
    d = None
    for f in glob.glob(os.path.join(BASE, "U[1-4]_*", "01_正文篇章", "句级数据_p*.json")):
        dd = json.load(open(f, encoding="utf-8"))
        if dd["passage_key"] == key:
            d = dd; break
    if d is None:
        return None
    words = [(float(a), float(b), c) for a, b, c in W[key]["words"] if isinstance(c, str) and c.strip()]
    dur = float(W[key]["duration"])
    sents = d["sentences"]
    used = [0] * len(sents)
    for a, b, _t in words:
        mid = (a + b) / 2
        for i, s in enumerate(sents):
            if float(s["start_s"]) - 0.2 <= mid <= float(s["end_s"]) + 0.2:
                used[i] += 1
                break
    rows = []
    for i, s in enumerate(sents):
        st, en = float(s["start_s"]), float(s["end_s"])
        n_text = wc(s["text"])
        rows.append((i, s["text"], st, en, n_text, used[i]))
    # 覆盖率 & 间隙漏检
    covered = sum(used)
    gaps = []
    prev_end = 0.0
    for s in sents:
        st, en = float(s["start_s"]), float(s["end_s"])
        if st - prev_end > 2.0:
            gwords = [t for a, b, t in words if prev_end <= (a + b) / 2 < st]
            gaps.append((prev_end, st, len(gwords), " ".join(gwords[:10])))
        prev_end = en
    if dur - prev_end > 2.0:
        gwords = [t for a, b, t in words if (a + b) / 2 >= prev_end]
        gaps.append((prev_end, dur, len(gwords), " ".join(gwords[:10])))
    return rows, covered, len(words), dur, gaps

def main():
    keys = sys.argv[1:] or sorted(W.keys())
    bad_total = 0
    for key in keys:
        r = check(key)
        if r is None:
            print(f"[{key}] 无归档"); continue
        rows, covered, total, dur, gaps = r
        # 判据：窗内词数 / 句词数 < 0.5 → 疑似错位；> 2.5 且差>8 → 疑似抢句
        bad = [(i, t, st, en, nt, nu) for i, t, st, en, nt, nu in rows
               if nt >= 2 and (nu < max(1, nt) * 0.5 or (nu > nt * 2.5 and nu - nt > 8))]
        gg = [g for g in gaps if g[2] >= 3]
        print(f"\n=== {key}: {len(rows)} 句 | 词数异常 {len(bad)} | 覆盖率 {covered}/{total} ({covered/max(1,total):.0%}) | 有词间隙 {len(gg)} ===")
        for i, t, st, en, nt, nu in bad[:6]:
            print(f"   句{i} [{st:.1f}-{en:.1f}] 句词数{nt} 窗内{nu} | {t[:50]}")
        for a, b, n, txt in gg[:3]:
            print(f"   间隙 {a:.1f}-{b:.1f}（{b-a:.1f}s）含 {n} 词: {txt}")
        bad_total += len(bad) + len(gg)
    print(f"\n合计异常：{bad_total}")

if __name__ == "__main__":
    main()
