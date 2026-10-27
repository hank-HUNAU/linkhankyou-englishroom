# -*- coding: utf-8 -*-
"""_split_arts_sentences.py —— 把段落级 arts 拆成句级（按时间轴句子序列），并处理双 BOOK_EXTRA 声明

用法：python _split_arts_sentences.py 56 63
规则：
  · 页面可能有多处 `var BOOK_EXTRA={...};`（后一处覆盖前一处）——先合并全部，再只重写**最后**一处的本篇条目
  · 段落文本 = 若干连续时间轴句子的拼接 → 按前缀贪心匹配还原段落切分
"""
import re, json, sys, glob, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, "assets/timeline.json"), encoding="utf-8"))
PAT = re.compile(r"var BOOK_EXTRA=(\{.*?\});", re.S)


def norm(s):
    return re.sub(r"\s+", " ", s.replace("’", "'").replace("‘", "'")).strip()


def main():
    pages = [int(x) for x in sys.argv[1:]]
    for pg in pages:
        f = glob.glob(os.path.join(HERE, "篇章页", "读写_%03d_*.html" % pg))[0]
        html = open(f, encoding="utf-8").read()
        blocks = list(PAT.finditer(html))
        merged = {}
        for m in blocks:
            try:
                merged.update(json.loads(m.group(1)))
            except Exception:
                pass
        key = str(pg)
        if key not in merged:
            print("✗ p%03d 无 BOOK 条目" % pg); continue
        sents = [s["text"] for s in TL["p%03d" % pg]]
        arts = merged[key]["arts"]
        total = sum(len(p) for p in arts)
        if total == len(sents):
            print("= p%03d 已是句级（%d 句），跳过" % (pg, total)); continue

        # 段落 → 句序列（前缀贪心）
        new_arts, si, bad = [], 0, []
        for para in arts:
            ptxt = norm(" ".join(para))
            group, acc = [], ""
            while si < len(sents):
                cand = norm((acc + " " + sents[si]).strip())
                if ptxt.startswith(cand) or cand in ptxt:
                    group.append(sents[si]); acc = cand; si += 1
                    if cand == ptxt:
                        break
                else:
                    break
            if not group:
                bad.append(ptxt[:40])
                group = list(para)          # 还原失败 → 原样保留（后面会报）
            new_arts.append(group)
        ok = (si == len(sents))
        merged[key]["arts"] = new_arts
        payload = json.dumps({key: merged[key]}, ensure_ascii=False, separators=(",", ":"))
        # 只重写最后一处声明里的本篇条目：把最后一处整体换成合并后的全量（最稳）
        last = blocks[-1]
        full = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
        html2 = html[:last.start()] + "var BOOK_EXTRA=" + full + ";" + html[last.end():]
        open(f, "w", encoding="utf-8", newline="\n").write(html2)
        print("%s p%03d：%d 段/%d 句 → 句级 %d 段/%d 句（消化 %d 句）%s"
              % ("✓" if ok else "!", pg, len(arts), total, len(new_arts),
                 sum(len(g) for g in new_arts), si, "" if ok else " 未完全对上：" + str(bad[:2])))


if __name__ == "__main__":
    main()
