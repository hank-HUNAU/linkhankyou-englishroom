#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_gen_u14_confidence.py —— U1–U4 情况1 六篇「句级文本×音频对齐置信度」逐句清单

产出（reports/）：
  句级对齐置信度_U1-U4_情况1.csv   （Excel 可开，canonical）
  句级对齐置信度_U1-U4_情况1.json  （含完整指标与口径说明）
  句级对齐置信度_U1-U4_情况1.html  （按篇章分组、逐句罗列、A4 可打印）

指标口径（诚实声明，勿对外称「准确率」）：
  - conf_lcs      = aligner 的 LCS 词映射率（映射词数/该句词数）。情况1 文本本就是
                    ASR 转写、与词级时间戳同源，故恒为 1.000，**无鉴别力**，仅作口径留痕。
  - 词数配比       = 落在句时间窗（±0.2s）内的实录 ASR 词数 / 该句词数。
                    <0.5 疑似错位，>2.5 且差>8 疑似抢邻句（_verify_alignment_u14.py 判据）。
  - 起点/终点残差 = 句边界到最近 ASR 词边界的距离（秒）；越小说明时间轴越贴实际发音。
  - 分级           A 贴合（配比正常且双残差 ≤0.30s）／B 可用（配比正常但边界偏）
                    ／C 需复核（配比异常）。这是**可机检判定**，非人工听审结论。
"""
import csv
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
REPORTS = os.path.join(HERE, "reports")
RESULT = os.path.join(HERE, "_u14_rerun_result.json")
WORDS = os.path.join(HERE, "_u14_words.json")
STEM = "句级对齐置信度_U1-U4_情况1"

ORDER = ["p015", "p018", "p023", "p033", "p036", "p041"]


def wc(s):
    return len(re.findall(r"[A-Za-z'’]+", s or ""))


def main():
    R = json.load(io.open(RESULT, encoding="utf-8"))
    W = json.load(io.open(WORDS, encoding="utf-8"))
    os.makedirs(REPORTS, exist_ok=True)

    units = []
    all_rows = []

    for page in ORDER:
        r = R[page]
        words = [(float(a), float(b), t) for a, b, t in W[r["key"]]["words"]
                 if isinstance(t, str) and t.strip()]
        starts = sorted(a for a, b, t in words)
        ends = sorted(b for a, b, t in words)

        arc = os.path.join(BASE, r["archive"])
        doc = json.load(io.open(arc, encoding="utf-8"))

        srows = []
        for n, s in zip(r["sentences"], doc["sentences"]):
            st, en = n["start_s"], n["end_s"]
            n_text = wc(s["text"])
            n_win = sum(1 for a, b, t in words if st - 0.2 <= (a + b) / 2 <= en + 0.2)
            ratio = round(n_win / max(1, n_text), 3)
            # 到最近词边界的距离
            d_start = min((abs(st - x) for x in starts), default=9.99)
            d_end = min((abs(en - x) for x in ends), default=9.99)
            d_start, d_end = round(d_start, 3), round(d_end, 3)
            bad_ratio = n_text >= 2 and (n_win < max(1, n_text) * 0.5
                                         or (n_win > n_text * 2.5 and n_win - n_text > 8))
            if bad_ratio:
                grade = "C"
            elif d_start <= 0.30 and d_end <= 0.30:
                grade = "A"
            else:
                grade = "B"
            row = dict(
                unit=doc["unit"], page=page, key=r["key"], title=doc["title"],
                sent=int(s["i"]) + 1, start_s=st, end_s=en,
                dur_s=round(en - st, 3), text=s["text"],
                n_text=n_text, n_win=n_win, ratio=ratio,
                conf_lcs=n["confidence"],
                d_start=d_start, d_end=d_end, grade=grade,
            )
            srows.append(row)
            all_rows.append(row)

        grades = {g: sum(1 for x in srows if x["grade"] == g) for g in "ABC"}
        units.append(dict(page=page, key=r["key"], title=doc["title"],
                          unit=doc["unit"], n_sent=len(srows),
                          duration_s=r["duration_s"],
                          conf_lcs_mean=r["conf_mean"],
                          conf_lcs_min=r["conf_min"],
                          ratio_mean=round(sum(x["ratio"] for x in srows) / len(srows), 3),
                          d_start_mean=round(sum(x["d_start"] for x in srows) / len(srows), 3),
                          d_end_mean=round(sum(x["d_end"] for x in srows) / len(srows), 3),
                          grades=grades, rows=srows))

    meta = dict(
        scope="TH!NK F U1–U4 情况1（无官方稿）六篇，2026-11-12 拉齐至 U5–U12 主线口径",
        method="faster-whisper small/cpu/int8 词级时间戳 × ASR 转写文本校准（LCS）"
               " + 静音吸附（0.3s/-40dB/0.15）+ 单调钳制；文本逐字不变",
        conf_lcs_note="LCS 词映射率；情况1 文本与词级时间戳同源故恒 1.000，无鉴别力，仅作口径留痕",
        ratio_note="句时间窗内实录 ASR 词数 / 句词数；<0.5 疑似错位，>2.5且差>8 疑似抢邻句",
        grade_note="A 贴合（配比正常且双残差≤0.30s）/ B 可用（配比正常但边界偏）/ C 需复核（配比异常）",
        honest="以上均为可机检指标，非人工听审准确率；按 _ALIGNMENT_WORKFLOW.md 定案为全自动无人耳终审",
        total_sent=len(all_rows),
        grades={g: sum(1 for x in all_rows if x["grade"] == g) for g in "ABC"},
    )

    # CSV（canonical）
    cols = ["unit", "page", "title", "sent", "start_s", "end_s", "dur_s",
            "text", "n_text", "n_win", "ratio", "conf_lcs",
            "d_start", "d_end", "grade"]
    head = ["单元", "页", "篇名", "句序", "起点s", "终点s", "时长s",
            "英文句子", "句词数", "窗内ASR词数", "词数配比", "LCS置信度",
            "起点残差s", "终点残差s", "分级"]
    with io.open(os.path.join(REPORTS, STEM + ".csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        for x in all_rows:
            w.writerow([x[c] for c in cols])

    json.dump(dict(meta=meta, units=units),
              io.open(os.path.join(REPORTS, STEM + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # HTML（普通字符串常量，避免 CSS 的 % 撞格式化）
    CSS = """
:root{--green:#10B981;--purple:#7C3AED;--ink:#1c1c1e;--ink2:#3a3a3c;--ink3:#6e6e73;--line:#e5e5ea;--bg:#fff}
*{box-sizing:border-box}
body{margin:0;padding:28px 30px;background:var(--bg);color:var(--ink);
 font-family:'Noto Sans SC','PingFang SC','Microsoft YaHei',sans-serif;font-size:13px;line-height:1.6}
h1{font-size:20px;font-weight:800;margin:0 0 6px}
.sub{color:var(--ink3);font-size:12px;margin-bottom:18px}
.note{background:#f7f7fa;border-left:3px solid var(--purple);padding:10px 14px;margin:14px 0 22px;font-size:12px;color:var(--ink2)}
.note b{color:var(--purple)}
.sum{width:100%;border-collapse:collapse;margin-bottom:26px;font-size:12px}
.sum th{background:#f7f7fa;text-align:left;padding:8px 10px;border:1px solid var(--line);font-weight:700}
.sum td{padding:8px 10px;border:1px solid var(--line)}
.unit{margin:26px 0 0;break-inside:avoid}
.uh{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid var(--green);padding-bottom:7px;margin-bottom:10px}
.uh .pg{font-size:16px;font-weight:800;color:var(--green)}
.uh .ti{font-size:14px;font-weight:700}
.uh .mt{margin-left:auto;font-size:11.5px;color:var(--ink3)}
table.d{width:100%;border-collapse:collapse;font-size:12px}
table.d th{background:#fafafa;text-align:left;padding:6px 8px;border:1px solid var(--line);font-weight:700;font-size:11.5px}
table.d td{padding:6px 8px;border:1px solid var(--line);vertical-align:top}
td.n{font-family:ui-monospace,monospace;color:var(--ink3);white-space:nowrap}
td.t{width:44%;line-height:1.5}
td.g{text-align:center;font-weight:800}
.gA{color:#0E8A62}.gB{color:#B26A00}.gC{color:#C0392B}
.pill{display:inline-block;background:#eef3ff;color:#1a4fa0;border-radius:999px;padding:1px 7px;font-size:11px;font-weight:700}
.foot{margin-top:24px;font-size:11.5px;color:var(--ink3);border-top:1px solid var(--line);padding-top:10px}
@media print{body{padding:0;font-size:11px}.unit{break-inside:auto}table.d{font-size:10.5px}}
"""
    parts = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>句级对齐置信度 · U1–U4 情况1 六篇</title>',
             '<style>' + CSS + '</style></head><body>',
             '<h1>句级文本 × 音频对齐置信度 · U1–U4 情况1 六篇</h1>',
             '<div class="sub">TH!NK F ｜ 2026-11-12 拉齐至 U5–U12 主线口径 ｜ '
             '共 ' + str(meta["total_sent"]) + ' 句 ｜ A ' + str(meta["grades"]["A"]) +
             ' · B ' + str(meta["grades"]["B"]) + ' · C ' + str(meta["grades"]["C"]) + '</div>',
             '<div class="note"><b>口径（必读）</b>：'
             '① <b>LCS置信度</b>＝aligner 的词映射率；情况1 文本本就是 ASR 转写、与词级时间戳同源，'
             '故恒为 1.000，<b>无鉴别力</b>，仅留痕。'
             '② <b>词数配比</b>＝句时间窗内实录 ASR 词数 / 句词数，是真正有判别力的指标。'
             '③ <b>起点/终点残差</b>＝句边界到最近词边界的距离（秒），越小越贴实际发音。'
             '④ 分级 A 贴合／B 可用／C 需复核，均为<b>可机检判定，非人工听审准确率</b>。</div>',
             '<table class="sum"><tr><th>页</th><th>篇名</th><th>句数</th><th>音频时长</th>'
             '<th>LCS 均/最低</th><th>词数配比均</th><th>起点残差均</th><th>终点残差均</th>'
             '<th>A / B / C</th></tr>']
    for u in units:
        g = u["grades"]
        parts.append('<tr><td>' + u["page"] + '</td><td>' + u["title"] + '</td><td>' +
                     str(u["n_sent"]) + '</td><td>' + str(u["duration_s"]) + 's</td><td>' +
                     str(u["conf_lcs_mean"]) + ' / ' + str(u["conf_lcs_min"]) +
                     '</td><td>' + str(u["ratio_mean"]) + '</td><td>' + str(u["d_start_mean"]) +
                     's</td><td>' + str(u["d_end_mean"]) + 's</td><td>' +
                     str(g["A"]) + ' / ' + str(g["B"]) + ' / ' + str(g["C"]) + '</td></tr>')
    parts.append('</table>')

    for u in units:
        parts.append('<div class="unit"><div class="uh"><span class="pg">' + u["page"] +
                     '</span><span class="ti">' + u["title"] + '</span>' +
                     '<span class="mt">' + u["unit"] + ' · ' + u["key"] + ' · ' +
                     str(u["n_sent"]) + ' 句</span></div>')
        parts.append('<table class="d"><tr><th>句</th><th>起点</th><th>终点</th>'
                     '<th>英文句子</th><th>句词数</th><th>窗内词</th><th>配比</th>'
                     '<th>LCS</th><th>起残差</th><th>终残差</th><th>分级</th></tr>')
        for x in u["rows"]:
            import html as _h
            parts.append('<tr><td class="n">' + str(x["sent"]) + '</td>' +
                         '<td class="n">' + str(x["start_s"]) + '</td>' +
                         '<td class="n">' + str(x["end_s"]) + '</td>' +
                         '<td class="t">' + _h.escape(x["text"]) + '</td>' +
                         '<td class="n">' + str(x["n_text"]) + '</td>' +
                         '<td class="n">' + str(x["n_win"]) + '</td>' +
                         '<td class="n">' + str(x["ratio"]) + '</td>' +
                         '<td class="n">' + str(x["conf_lcs"]) + '</td>' +
                         '<td class="n">' + str(x["d_start"]) + '</td>' +
                         '<td class="n">' + str(x["d_end"]) + '</td>' +
                         '<td class="g g' + x["grade"] + '">' + x["grade"] + '</td></tr>')
        parts.append('</table></div>')
    parts.append('<div class="foot">生成：_gen_u14_confidence.py ｜ 数据源：'
                 '归档 句级数据_pXXX.json + _u14_words.json + _u14_rerun_result.json ｜ '
                 '按 _ALIGNMENT_WORKFLOW.md 定案为全自动无人耳终审，本报告不作准确率宣称。</div>')
    parts.append('</body></html>')
    io.open(os.path.join(REPORTS, STEM + ".html"), "w", encoding="utf-8").write("".join(parts))

    print("=== 逐句置信度清单已生成 ===")
    print("总句数 %d ｜ A %d · B %d · C %d" %
          (meta["total_sent"], meta["grades"]["A"], meta["grades"]["B"], meta["grades"]["C"]))
    for u in units:
        g = u["grades"]
        print("  %s %-26s %2d 句  配比均 %.3f  残差 起%.3f/终%.3f  A%2d B%2d C%2d" %
              (u["page"], u["title"][:26], u["n_sent"], u["ratio_mean"],
               u["d_start_mean"], u["d_end_mean"], g["A"], g["B"], g["C"]))
    print("\n产出：reports/%s.{csv,json,html}" % STEM)


if __name__ == "__main__":
    main()
