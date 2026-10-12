# -*- coding: utf-8 -*-
"""ASR 转写 × 教师用书练习块 匹配器 → _asr_match_report.json"""
import os, re, json, glob

WORK = os.path.dirname(os.path.abspath(__file__))
asr = json.load(open(os.path.join(WORK, "_asr_tracks.json"), encoding="utf-8"))
A = json.load(open(os.path.join(WORK, "_alignment.json"), encoding="utf-8"))

def norm(s):
    return re.sub(r"[^a-z]", "", s.lower())

def ngrams(s, n=4):
    return set(s[i:i + n] for i in range(max(0, len(s) - n + 1)))

def contain_score(tr_ns, block_ns):
    g = ngrams(tr_ns)
    if not g or len(tr_ns) < 12:
        return 0.0
    b = ngrams(block_ns)
    return len(g & b) / len(g)

def split_blocks(text):
    """把 spread 文本切成块：以 栏目大写标题 或 练习号行 为界"""
    lines = text.split("\n")
    marks = []  # (line_idx, label)
    for i, l in enumerate(lines):
        ls = l.strip()
        if 2 < len(ls) < 40 and ls.upper() == ls and re.search(r"[A-Z]{4,}", ls):
            marks.append((i, ls))
        elif re.match(r"^\d{1,2}\s+[A-Za-z(]", ls):
            ex = ls.split()[0]
            marks.append((i, "ex" + ex))
    blocks = []
    for j, (i, lab) in enumerate(marks):
        end = marks[j + 1][0] if j + 1 < len(marks) else len(lines)
        body = " ".join(lines[i:end])
        blocks.append((lab, body))
    if not blocks:
        blocks.append(("ALL", text))
    return blocks

out = []
for key, e in asr.items():
    if "error" in e or not e.get("text"):
        out.append(dict(file=key, err="no transcript"))
        continue
    tr_ns = norm(e["text"])
    # 页码：标准文件名优先；other 文件用 tag/unit 推
    m = re.search(r"_p(\d+)_t(\d+)", key)
    pg = int(m.group(1)) if m else None
    u = e["unit"]
    # 候选教师用书 spread：同单元且页码落在其页码范围内（Welcome 单文件全含）
    cands = []
    for f in glob.glob(os.path.join(WORK, "_tb_cache", "*.txt")):
        bn = os.path.basename(f)[:-4]
        um = re.match(r"Unit (\d+)", bn)
        fu = "W" if "Welcome" in bn else (um.group(1) if um else None)
        if fu != u:
            continue
        t = open(f, encoding="utf-8").read()
        pgs = sorted(set(int(x) for x in re.findall(r"T(\d{2,3})\b", t)))
        if pg and pgs and not (min(pgs) <= pg <= max(pgs)):
            continue
        cands.append((bn, t))
    scored = []
    for bn, t in cands:
        for lab, body in split_blocks(t):
            s = contain_score(tr_ns, norm(body))
            if s > 0.05:
                scored.append((round(s, 3), bn, lab, body[:150]))
    scored.sort(reverse=True)
    out.append(dict(file=key, unit=u, page=pg, dur=e.get("dur"),
                    transcript=e["text"][:200],
                    top=[dict(score=s, lesson=b, block=a, sample=c) for s, b, a, c in scored[:4]]))

json.dump(out, open(os.path.join(WORK, "_asr_match_report.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for r0 in out:
    if r0.get("err"):
        print("ERR", r0["file"])
        continue
    print("=" * 100)
    print(f"{r0['file'][:52]}  u{r0['unit']} p{r0['page']} {r0['dur']}s")
    print("  TR:", r0["transcript"][:120])
    for t0 in r0["top"]:
        print(f"   {t0['score']:.2f}  {t0['lesson'][:28]} | {t0['block'][:24]} | {t0['sample'][:80]}")
