#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_chunk_extract.py —— 语块（formulaic sequences）候选提取

方法论依据（全部经三轮审核，见 _CHUNK_WORKFLOW.md）：
  · Simpson-Vlach & Ellis (2010) AFL：频率 × 分布(dispersion) × 教学效用 三指标遴选
    DOI 10.1093/applin/amp058
  · Ellis, Simpson-Vlach & Maynard (2008)：L2 语块加工主要受 phrasal frequency 驱动
    （母语者靠 MI）→ 对 L2 排序以频率为主、MI 作质量过滤
    DOI 10.1002/j.1545-7249.2008.tb00137.x
  · Martinez & Schmitt (2012) PHRASE List：非透明多词表达，receptive 优先
    DOI 10.1093/applin/ams010
  · Conklin & Schmitt (2012)：低水平二语者常逐词加工 → 必须显性教 + 高复现
    DOI 10.1017/S0267190512000074

用法：
  python _chunk_extract.py --page p048            # 该篇候选（带全站指标）
  python _chunk_extract.py --page p048 --min-freq 2 --min-disp 2
  python _chunk_extract.py --report reports/语块候选_U5.md   # 批量写报告

产出：候选表（stdout / markdown），字段
  ngram | freq(全站出现次数) | disp(覆盖篇章数) | units(覆盖单元数) | MI(互信息) |
  hits(本篇句号) | type(whitelist/high-mi/…)
筛选口径（默认）：freq>=2 且 disp>=2（跨篇复现才算语块，单篇一次性搭配不算）。
"""
import argparse
import glob
import io
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))          # Think F 教材资产

# A1–A2 功能/交际语块白名单（正则，句首/句中出现均可）：课标功能大纲级句型
WHITELIST = [
    r"\bcan i\b", r"\bcan you\b", r"\bcould you\b", r"\bwould you like\b",
    r"\bi'?d like\b", r"\bhow much\b", r"\bhow many\b", r"\bhow about\b",
    r"\bwhat about\b", r"\bwhat time\b", r"\bwhere is\b", r"\bwhere are\b",
    r"\bdo you (?:know|like|want|have)\b", r"\bare you\b", r"\bis there\b",
    r"\bthere (?:is|are)\b", r"\bthank you\b", r"\bexcuse me\b",
    r"\bwhat'?s your\b", r"\bhow old\b", r"\bhow often\b", r"\blet'?s\b",
    r"\bi think\b", r"\bi don'?t (?:know|think|like)\b", r"\bit'?s (?:a|an|the|my)\b",
    r"\bgood (?:morning|afternoon|evening|idea|luck)\b", r"\bsee you\b",
    r"\ba lot of\b", r"\blots of\b", r"\bkind of\b", r"\bof course\b",
    r"\bat (?:the )?(?:moment|same time)\b", r"\bin (?:the )?(?:end|morning|evening)\b",
    r"\bthe same as\b", r"\bgood at\b", r"\binterested in\b", r"\bafraid of\b",
    r"\btake (?:a|part in)\b", r"\bhave (?:a|fun|to)\b", r"\bmake (?:a|sure)\b",
    r"\ba (?:great|good|nice) place to\b", r"\bcome and see\b", r"\bhappy to\b",
    r"\bi love\b", r"\bso many\b", r"\bevery (?:day|week|year|monday|sunday)\b",
    r"\bafter school\b", r"\beveryone\b",
]
WL_RE = re.compile("|".join(WHITELIST))

# 悬垂词：语块不该以这些词开头/收尾（否则是切碎的半个短语）；白名单/功能车道豁免
BAD_START = {"and", "but", "us", "it", "that", "is", "are", "was", "were", "to", "of",
             "or", "not", "a", "an", "the"}
BAD_END = {"to", "of", "a", "an", "the", "and", "but", "or", "is", "are", "us", "it",
           "that", "in", "on", "at", "for", "with", "as", "so", "not"}

STOP = {"the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for",
        "with", "is", "are", "was", "were", "it", "this", "that", "i", "you", "he",
        "she", "we", "they", "my", "your", "his", "her", "s", "t", "s", "d", "ll",
        "re", "ve", "m", "not", "there", "some", "any", "so", "as", "be", "have",
        "has", "had", "do", "does", "did", "can", "will", "would", "like"}


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").lower()
    s = re.sub(r"[^a-z0-9'\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_corpus():
    """48 篇正课文：{(unit,page): {key, sents:[str]}}，正典 = 归档句级数据"""
    out = {}
    for f in sorted(glob.glob(os.path.join(BASE, "U[0-9]*_*", "01_正文篇章", "句级数据_p*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        unit = int(str(d.get("unit", "U0")).lstrip("Uu"))
        page = d.get("page")
        sents = [s.get("text", "") for s in d.get("sentences", [])]
        # 词汇 key 反推（旧 schema 无 passage_key）
        key = d.get("passage_key")
        if not key:
            digits = str(page).lstrip("pP")
            vd = os.path.join(os.path.dirname(os.path.dirname(f)), "02_词汇数据")
            import fnmatch
            cands = [p for p in glob.glob(os.path.join(vd, "*.json"))
                     if re.match(r"^u%d_p0*%s_.+$" % (unit, digits), os.path.basename(p))]
            key = os.path.splitext(os.path.basename(cands[0]))[0] if cands else None
        out[(unit, page)] = dict(key=key, sents=sents)
    return out


def build_stats(corpus):
    uni = Counter()          # 词频
    gram = Counter()         # n-gram 频次
    gram_pages = defaultdict(set)
    gram_units = defaultdict(set)
    total_tokens = 0
    for (unit, page), d in corpus.items():
        for sent in d["sents"]:
            toks = norm(sent).split()
            total_tokens += len(toks)
            uni.update(toks)
            for n in range(2, 7):
                for i in range(len(toks) - n + 1):
                    g = " ".join(toks[i:i + n])
                    gram[g] += 1
                    gram_pages[g].add(page)
                    gram_units[g].add(unit)
    return uni, gram, gram_pages, gram_units, total_tokens


def mi(g, uni, total_tokens):
    toks = g.split()
    p_g = 1.0                       # 以「出现过的 n-gram 视为 1 个类型」的近似：用词概率连乘
    for t in toks:
        p_g *= (uni[t] / total_tokens) if t in uni else 1e-9
    # MI = log2( P(g) / ΠP(w) )，P(g) 用出现频次/总 token 近似（n-gram 计数口径）
    return p_g


def score(gram_, gram_units_, uni, total_tokens, n):
    """互信息：log2( P(g) / Π P(w) )，P(g)≈freq/(总词数)；长度归一到单词，便于跨 n 比较"""
    freq = gram_[0]
    toks = gram_[1]
    p_g = max(freq, 1) / max(total_tokens, 1)
    denom = 1.0
    for t in toks:
        denom *= uni[t] / total_tokens
    m = math.log2(p_g / denom) if denom > 0 else 0.0
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", default="p048")
    ap.add_argument("--min-freq", type=int, default=2)
    ap.add_argument("--min-disp", type=int, default=2)
    ap.add_argument("--min-mi", type=float, default=0.0, help="MI 下限（默认不限，仅排序参考）")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--no-lane-b", dest="lane_b", action="store_false",
                    help="关闭功能白名单车道（只出语料统计候选）")
    ap.add_argument("--json", default=None, help="候选落 JSON（供审校）")
    args = ap.parse_args()

    corpus = load_corpus()
    uni, gram, pages, units, total = build_stats(corpus)
    print("语料：%d 篇 / %d tokens / %d 个 2-6 元候选" % (len(corpus), total, len(gram)))

    target = None
    for (u, p), d in corpus.items():
        if p == args.page:
            target = (u, d)
            break
    if not target:
        sys.exit("✗ 找不到 %s" % args.page)
    unit, tdata = target
    key = tdata["key"]

    # 本篇句号索引
    page_grams = defaultdict(set)
    for i, sent in enumerate(tdata["sents"]):
        toks = norm(sent).split()
        for n in range(2, 7):
            for j in range(len(toks) - n + 1):
                page_grams[" ".join(toks[j:j + n])].add(i + 1)

    rows = []
    for g, hits in page_grams.items():
        n = len(g.split())
        freq = gram[g]
        disp = len(pages[g])
        if freq < args.min_freq or disp < args.min_disp:
            continue
        m = score((freq, g.split()), None, uni, total, n)
        if m < args.min_mi:
            continue
        typ = "whitelist" if WL_RE.fullmatch(g) else ("collocation" if m >= 3 else "bundle")
        rows.append(dict(ngram=g, n=n, freq=freq, disp=disp, units=len(units[g]),
                         mi=round(m, 2), hits=sorted(hits), type=typ))

    # 车道B：功能白名单，不受频率门槛限制（单次出现的功能句如 "come and see" 也有教学价值）
    if args.lane_b:
        have = {r["ngram"] for r in rows}
        for g, hits in page_grams.items():
            if g in have or not WL_RE.fullmatch(g):
                continue
            n = len(g.split())
            m = score((gram[g], g.split()), None, uni, total, n)
            rows.append(dict(ngram=g, n=n, freq=gram[g], disp=len(pages[g]),
                             units=len(units[g]), mi=round(m, 2), hits=sorted(hits),
                             type="functional"))

    # 去重 + 悬垂过滤：优先级 = 白名单/功能车道 > 长 > MI 高；重叠只留一条
    def prio(r):
        return (2 if r["type"] in ("whitelist", "functional") else
                (1 if r["mi"] >= 3 else 0), r["n"], r["mi"])
    rows = [r for r in rows
            if r["type"] in ("whitelist", "functional")
            or (r["ngram"].split()[0] not in BAD_START
                and r["ngram"].split()[-1] not in BAD_END)]
    rows.sort(key=prio, reverse=True)
    kept = []
    for r in rows:
        if any(r["ngram"] in k["ngram"] or k["ngram"] in r["ngram"] for k in kept):
            continue
        kept.append(r)
    kept.sort(key=lambda r: (r["type"] not in ("whitelist", "functional"), -r["freq"], -r["mi"]))

    print("\n== %s（U%d %s）候选 %d 条 ==" % (args.page, unit, key, len(kept)))
    print("%-34s %-3s %-4s %-4s %-5s %-6s %-11s %s" % ("ngram", "n", "freq", "disp", "units", "MI", "hit句", "type"))
    for r in kept[:args.top]:
        print("%-34s %-3d %-4d %-4d %-5d %-6.2f %-11s %s" % (
            r["ngram"][:34], r["n"], r["freq"], r["disp"], r["units"], r["mi"],
            ",".join(map(str, r["hits"][:5])), r["type"]))

    if args.json:
        json.dump(dict(page=args.page, unit=unit, key=key, corpus=dict(pages=len(corpus), tokens=total),
                       candidates=kept), open(args.json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\n✓ 候选已写入 %s" % args.json)


if __name__ == "__main__":
    main()
