# -*- coding: utf-8 -*-
"""把已知课文词序列与识别词序列做动态规划比对，反推句边界。
复用已存盘的转写结果 _whisper_all_words.json，不重新转写。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(ROOT, "_whisper_all_words.json"), encoding="utf-8"))
TJ = json.load(open(os.path.join(ROOT, "assets", "timeline.json"), encoding="utf-8"))


def norm(w):
    return re.sub(r"[^a-z0-9']", "", str(w).lower())


def target_words(key):
    """把每篇课文摊平成 (词, 句号) 序列。"""
    out = []
    for i, s in enumerate(TJ[key]):
        for w in re.split(r"\s+", s["text"]):
            n = norm(w)
            if n:
                out.append((n, i))
    return out


def align(A, B):
    """Needleman-Wunsch：A=目标词, B=识别词。返回 [(i, j) 匹配对]。"""
    n, m = len(A), len(B)
    MATCH, MIS, GAP = 2, -1, -1
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i * GAP
    for j in range(1, m + 1):
        dp[0][j] = j * GAP
    for i in range(1, n + 1):
        ai = A[i - 1]
        row, prev = dp[i], dp[i - 1]
        for j in range(1, m + 1):
            sc = MATCH if ai == B[j - 1] else MIS
            row[j] = max(prev[j - 1] + sc, prev[j] + GAP, row[j - 1] + GAP)
    i, j, pairs = n, m, []
    while i > 0 and j > 0:
        sc = MATCH if A[i - 1] == B[j - 1] else MIS
        if dp[i][j] == dp[i - 1][j - 1] + sc:
            if A[i - 1] == B[j - 1]:
                pairs.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i - 1][j] + GAP:
            i -= 1
        else:
            j -= 1
    pairs.reverse()
    return pairs


def main():
    order = sorted(TJ.keys(), key=lambda k: int(k.replace("p", "")))
    result = {}
    print("%-6s %5s %5s %6s %9s   %s" % ("page", "词", "匹配", "漏配", "报幕结束", "偏差>0.3s"))
    rows = []
    for key in order:
        T = target_words(key)
        W = [(w[0], w[1], w[2]) for w in WORDS[key]]
        A = [t[0] for t in T]
        B = [w[2] for w in W]
        pairs = align(A, B)
        matched = {i: j for i, j in pairs}
        # 报幕 = 识别流里在第一个匹配词之前的词
        first_j = min(j for i, j in pairs) if pairs else 0
        ann_end = W[first_j - 1][1] if first_j > 0 else None
        # 每句的首末识别词
        per = {}
        for i, j in pairs:
            si = T[i][1]
            if si not in per:
                per[si] = [j, j]
            else:
                per[si][1] = j
        n = len(TJ[key])
        got = []
        for si in range(n):
            if si in per:
                got.append([round(W[per[si][0]][0], 3), round(W[per[si][1]][1], 3)])
            else:
                got.append(None)
        result[key] = {"bounds": got, "announceEnd": ann_end,
                       "missing": [i for i in range(n) if got[i] is None]}
        deltas = []
        for k in range(n - 1):
            if got[k] is None or got[k + 1] is None:
                continue
            der = (got[k][1] + got[k + 1][0]) / 2.0
            cur = TJ[key][k]["end_s"]
            deltas.append((k, cur, der, der - cur))
            rows.append((abs(der - cur), key, k, cur, der, der - cur))
        big = sum(1 for d in deltas if abs(d[3]) > 0.30)
        print("%-6s %5d %5d %6d %9s   %d / %d"
              % (key, len(A), len(pairs), len(A) - len(pairs),
                 ("%.2f" % ann_end) if ann_end else "—", big, len(deltas)))

    json.dump(result, open(os.path.join(ROOT, "_whisper_bounds_dp.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("")
    print("=== 偏差最大的 20 条边界 ===")
    rows.sort(reverse=True)
    for d, key, k, cur, der, delta in rows[:20]:
        print("  %-6s #%-2d  当前 %8.3f   B %8.3f   Δ%+6.3f | …%s | %s…"
              % (key, k, cur, der, delta, TJ[key][k]["text"][-28:], TJ[key][k + 1]["text"][:28]))

    print("")
    print("=== 报幕（首句音频起点）===")
    for key in order:
        a = result[key]["announceEnd"]
        cur0 = TJ[key][0]["start_s"]
        if a:
            print("  %-6s 报幕结束 %7.3f   当前首句起点 %7.3f   Δ%+6.3f"
                  % (key, a, cur0, a - cur0))
        else:
            print("  %-6s 无报幕   当前首句起点 %7.3f" % (key, cur0))


main()
