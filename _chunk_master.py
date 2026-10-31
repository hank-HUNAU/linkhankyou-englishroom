# -*- coding: utf-8 -*-
"""Think F 语块总表（全语料候选）—— 跨 48 篇聚合，不是单篇候选

用途：给教师/教研一个**全书俯瞰**：哪些表达在多篇里反复出现、值得做成长期复现内容。
性质：**候选表，未定稿**。定稿仍按篇走 语块_pXXX.json（人工审校是唯一入口）。

排序口径（2026-10-31 定）：**disp（覆盖篇数）优先**，其次 freq、MI。
理由：各单元词数从 522 递增到 1,106，freq 受体量影响不可跨单元比；disp 不受体量影响。

用法：
  python _chunk_master.py                    # 默认 top=300，写 CSV/JSON/HTML
  python _chunk_master.py --top 120 --min-disp 3
  python _chunk_master.py --no-write         # 只看终端输出
"""
import argparse
import csv
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _chunk_extract as ce  # 复用语料加载/统计/MI/白名单/悬垂词表

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))
OUT_DIR = os.path.join(BASE, "00_语块总表")


def load_finalized():
    """已定稿语块：{ngram: [page,...]}，用于在总表上标注「已定稿」"""
    out = {}
    for f in glob.glob(os.path.join(BASE, "U[0-9]*_*", "02_词汇数据", "语块_p*.json")):
        d = json.load(io.open(f, encoding="utf-8"))
        for c in d.get("chunks", []):
            out.setdefault(ce.norm(c["text"]), []).append(d["page"])
    return out


def build(min_freq, min_disp, use_lane_b=True):
    corpus = ce.load_corpus()
    uni, gram, pages, units, total = ce.build_stats(corpus)

    rows = []
    for g, freq in gram.items():
        n = len(g.split())
        if n < 2 or n > 6:
            continue
        disp = len(pages[g])
        if freq < min_freq or disp < min_disp:
            continue
        is_wl = bool(ce.WL_RE.fullmatch(g))
        toks = g.split()
        if not is_wl and (toks[0] in ce.BAD_START or toks[-1] in ce.BAD_END):
            continue
        m = ce.score((freq, toks), None, uni, total, n)
        typ = ("whitelist" if is_wl else ("collocation" if m >= 3 else "bundle"))
        rows.append(dict(ngram=g, n=n, freq=freq, disp=disp, units=len(units[g]),
                         mi=round(m, 2), type=typ,
                         pages=sorted(pages[g])))
    if not use_lane_b:
        rows = [r for r in rows if r["type"] != "whitelist"]

    # 去重：白名单/功能 > 长 > MI（与 _chunk_extract 同优先级），重叠只留一条
    def prio(r):
        return (2 if r["type"] in ("whitelist", "functional") else
                (1 if r["mi"] >= 3 else 0), r["n"], r["mi"])
    rows.sort(key=prio, reverse=True)
    kept = []
    for r in rows:
        if any(r["ngram"] in k["ngram"] or k["ngram"] in r["ngram"] for k in kept):
            continue
        kept.append(r)

    # 排序：disp 优先（可跨单元比较），再 freq，再 MI
    kept.sort(key=lambda r: (-r["disp"], -r["freq"], -r["mi"]))
    return kept, dict(pages=len(corpus), tokens=total)


def write_outputs(rows, meta, min_freq, min_disp, finalized):
    os.makedirs(OUT_DIR, exist_ok=True)
    payload = dict(
        title="Think F 语块总表（候选·未定稿）",
        standard="候选性质：全语料 n-gram 统计 + 功能白名单；disp(覆盖篇数) 优先排序；非 Biber 式 lexical bundle",
        corpus=meta, min_freq=min_freq, min_disp=min_disp, n=len(rows),
        note="定稿仍按篇（语块_pXXX.json，人工审校为唯一入口）；本表供教师/教研俯瞰与选题。总表只收 disp≥2（至少两篇出现）；单次出现的功能句（如 come and see）不入总表，只在篇级定稿收录",
        chunks=[dict(rank=i + 1, **r,
                     finalized=finalized.get(r["ngram"], []))
                for i, r in enumerate(rows)])

    jp = os.path.join(OUT_DIR, "语块总表_候选.json")
    with io.open(jp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    cp = os.path.join(OUT_DIR, "语块总表_候选.csv")
    with io.open(cp, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["排名", "语块", "词数", "复现次数freq", "覆盖篇数disp", "覆盖单元units",
                    "MI", "类型", "已定稿篇", "出现页"])
        for i, r in enumerate(rows):
            w.writerow([i + 1, r["ngram"], r["n"], r["freq"], r["disp"], r["units"], r["mi"],
                        r["type"], "/".join(finalized.get(r["ngram"], [])) or "—",
                        ",".join(r["pages"])])

    hp = os.path.join(OUT_DIR, "语块总表_候选.html")
    with io.open(hp, "w", encoding="utf-8") as fh:
        fh.write(html(rows, meta, min_freq, min_disp, finalized))
    return cp, jp, hp


TN = {"whitelist": "功能句", "functional": "功能句", "collocation": "搭配", "bundle": "词串"}


def html(rows, meta, min_freq, min_disp, finalized):
    trs = []
    for i, r in enumerate(rows):
        fin = finalized.get(r["ngram"], [])
        mark = ('<span class="fin">已定稿 %s</span>' % "/".join(fin)) if fin else ""
        trs.append(
            '<tr><td class="n">%d</td><td class="ck">%s %s</td><td>%d</td><td>%d</td><td>%d</td>'
            '<td>%d</td><td class="mi">%.2f</td><td><span class="ty t-%s">%s</span></td>'
            '<td class="pg">%s</td></tr>'
            % (i + 1, r["ngram"], mark, r["n"], r["freq"], r["disp"], r["units"], r["mi"],
               r["type"], TN.get(r["type"], r["type"]),
               "、".join(p.lstrip("p").lstrip("0") for p in r["pages"][:8])
               + ("…" if len(r["pages"]) > 8 else "")))
    return """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>Think F 语块总表（候选）</title><style>
:root{--green:#10B981;--green-bg:#E8F8F1;--purple:#7C3AED;--purple-bg:#F2EDFE;
--ink:#1C1C1E;--ink2:#3A3A3C;--ink3:#8E8E93;--line:#E5E5EA}
*{box-sizing:border-box}body{margin:0;background:#F7F7F9;color:var(--ink);
font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;font-size:13px;line-height:1.6}
.page{max-width:1000px;margin:0 auto;background:#fff;padding:26px 30px 40px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.brand{font-size:10.5px;font-weight:800;letter-spacing:.14em;color:var(--purple)}
h1{font-size:22px;margin:4px 0 6px}
.sub{color:var(--ink3);font-size:12px}
.meta{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0 4px}
.pill{font-size:11px;font-weight:800;padding:2px 9px;border-radius:999px;background:#F2F2F7;color:var(--ink2)}
.pill.g{background:var(--green-bg);color:#1F6B2E}
.note{background:var(--green-bg);border-left:3px solid var(--green);padding:9px 13px;border-radius:0 8px 8px 0;
font-size:11.5px;color:#1F6B2E;margin:12px 0}
table{width:100%%;border-collapse:collapse;font-size:12.5px;margin-top:10px}
th,td{border-bottom:1px solid var(--line);padding:6px 7px;text-align:left}
th{font-size:10.5px;color:var(--ink3);font-weight:800;text-transform:uppercase;letter-spacing:.06em;
position:sticky;top:0;background:#fff}
td.n{color:var(--ink3);width:38px;font-family:ui-monospace,monospace;font-size:10.5px}
td.ck{font-weight:700;font-size:13px}
td.mi{color:var(--ink3);font-family:ui-monospace,monospace;font-size:11px}
td.pg{color:var(--ink3);font-size:11px}
.ty{font-size:10px;font-weight:800;padding:1px 7px;border-radius:999px;background:#F2F2F7;color:var(--ink2)}
.ty.t-whitelist,.ty.t-functional{background:var(--purple-bg);color:var(--purple)}
.ty.t-collocation{background:var(--green-bg);color:#1F6B2E}
.fin{font-size:9.5px;font-weight:800;color:#1F6B2E;background:var(--green-bg);
border-radius:999px;padding:1px 6px;margin-left:4px}
.foot{margin-top:18px;padding-top:10px;border-top:1px solid var(--line);color:var(--ink3);font-size:10.5px}
@media print{body{background:#fff}.page{box-shadow:none;padding:0}th{position:static}}
</style></head><body><div class="page">
<div class="brand">TH!NK · 语块总表</div>
<h1>Think F 语块总表（候选 · 未定稿）</h1>
<div class="sub">全语料聚合 · disp（覆盖篇数）优先排序 · 供教师/教研俯瞰</div>
<div class="meta">
  <span class="pill g">%(pages)d 篇</span>
  <span class="pill g">%(tokens)d 词</span>
  <span class="pill">候选 %(n)d 条</span>
  <span class="pill">门槛 freq≥%(mf)d · disp≥%(md)d</span>
</div>
<div class="note"><b>这是候选表，不是定稿表</b>。定稿仍按篇走（<code>语块_pXXX.json</code>，人工审校为唯一入口）。
排序用 <b>disp（覆盖篇数）</b>而非 freq：各单元词数从 522 递增到 1,106，freq 不可跨单元比较。
门槛为 9.3k 词语料缩尺设定，<b>不是</b> Biber 的「10 次/百万词」（该标准在本语料折合 0.093 次、不可达）。总表只收 <b>disp≥2</b>（至少两篇出现）；单次出现的功能句（如 <i>come and see</i>）不入总表，只在篇级定稿收录。</div>
<table><thead><tr><th>#</th><th>语块</th><th>词数</th><th>freq</th><th>disp</th><th>units</th>
<th>MI</th><th>类型</th><th>出现页</th></tr></thead><tbody>
%(rows)s
</tbody></table>
<div class="foot">生成：<code>_chunk_master.py</code> · 数据源：48 篇归档句级数据 · 同目录另有 CSV（可 Excel 打开）与 JSON（含完整出现页列表）</div>
</div></body></html>""" % dict(pages=meta["pages"], tokens=meta["tokens"], n=len(rows),
                            mf=min_freq, md=min_disp, rows="\n".join(trs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=300)
    ap.add_argument("--min-freq", type=int, default=2)
    ap.add_argument("--min-disp", type=int, default=2)
    ap.add_argument("--no-lane-b", dest="lane_b", action="store_false")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    rows, meta = build(args.min_freq, args.min_disp, args.lane_b)
    fin = load_finalized()
    print("语料：%d 篇 / %d 词｜候选 %d 条（freq≥%d, disp≥%d）"
          % (meta["pages"], meta["tokens"], len(rows), args.min_freq, args.min_disp))
    print("%-32s %-4s %-5s %-5s %-6s %-6s %s" % ("语块", "n", "freq", "disp", "units", "MI", "类型"))
    for r in rows[:min(args.top, 30)]:
        print("%-32s %-4d %-5d %-5d %-6d %-6.2f %s%s"
              % (r["ngram"][:32], r["n"], r["freq"], r["disp"], r["units"], r["mi"],
                 r["type"], "  ← 已定稿" if r["ngram"] in fin else ""))

    if not args.no_write:
        cp, jp, hp = write_outputs(rows[:args.top], meta, args.min_freq, args.min_disp, fin)
        print("\n已写：")
        for p in (cp, jp, hp):
            print("  " + p)


if __name__ == "__main__":
    main()
