#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_verify_alignment_all.py —— TH!NK F 全站 48 篇「可机检对齐质量」核查

产物（reports/，前缀 `全站对齐质量核查_48篇_2026-11-14`）：
  _篇章.csv  48 行，篇章级汇总（canonical 摘要）
  _逐句.csv  1118 行（48 篇实测），逐句指标（延续「按篇章、句子罗列」口径）
  .json      机器可读全量 + 口径说明
  .md        人读报告（结论 / 口径 / 篇章表 / 线索清单）

证据来源（三类格式自动适配）：
  U1–U4      `_u14_words.json`            {passage_key: {words, segments, duration}}
  U5/6/9/10/11 `_unit_N_words.json`       {page: [[start,end,word], ...]}（旧格式）
  U7/8/12    `_unit_N_asr.json`           {page: {words, segments, duration}}（2026-11-14 补）
             回退 `_unit_N_words.json`

口径（**诚实声明，勿称「准确率」**）：
  - 词数配比 = 落在句窗（±0.2s）内的实录 ASR 词数 / 该句词数；<0.5 或 >2.5 且差>8 → C。
  - 起点/终点残差 = 句边界到最近 ASR 词边界的距离（秒）。
  - 分级 A 贴合（配比正常且双残差 ≤0.30s）/ B 可用（配比正常但边界偏）/ C 需复核（配比异常）。
    **全部是可机检判定，非人工听审结论。**
  - aligner 的 confidence（LCS 词映射率）情况1 恒 1.000、无鉴别力，本核查不采用。
  - **有词间隙只列为「线索」**，按 `_ALIGNMENT_WORKFLOW.md` §4 的强制前置，
    判定漏句前必须三方对账（归档句数==课本源行数 + 间隙词归类 + ASR/源文本交叉印证）。
    本脚本不自动下「漏句」结论。
  - 双写一致性：归档 `句级数据_pXXX.json` × `assets/timeline.json` 逐句核对句数/文本/起止。

本脚本**只读**，不改任何正典数据。
"""
import csv
import glob
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心\Think F 教材资产"
REPORTS = os.path.join(HERE, "reports")
STEM = "全站对齐质量核查_48篇_2026-11-14"


def wc(s):
    return len(re.findall(r"[A-Za-z'’]+", s or ""))


def jload(path):
    return json.load(io.open(path, encoding="utf-8"))


def norm_words(raw):
    """把富格式 / 旧格式统一成 (words, segments, duration)。"""
    if isinstance(raw, dict):
        ws = raw.get("words", [])
        segments = raw.get("segments")
        dur = raw.get("duration")
    else:
        ws = raw
        segments = None
        dur = None
    words = [(float(a), float(b), str(t).strip()) for a, b, t in ws
             if isinstance(t, str) and t.strip()]
    if not dur:
        dur = max((b for a, b, t in words), default=0.0)
    return words, segments or [], float(dur)


def load_evidence():
    """返回 {page: {words, segments, duration, src}}。"""
    ev = {}
    u14 = os.path.join(HERE, "_u14_words.json")
    if os.path.isfile(u14):
        for key, raw in jload(u14).items():
            w, s, d = norm_words(raw)
            ev[key] = dict(words=w, segments=s, duration=d,
                           src="_u14_words.json:" + key)
    for f in sorted(glob.glob(os.path.join(HERE, "_unit_*_asr.json"))) + \
             sorted(glob.glob(os.path.join(HERE, "_unit_*_words.json"))):
        name = os.path.basename(f)
        for page, raw in jload(f).items():
            if page in ev:      # 富格式优先，旧格式不覆盖
                continue
            w, s, d = norm_words(raw)
            ev[page] = dict(words=w, segments=s, duration=d, src=name + ":" + page)
    return ev


def grade_of(n_text, n_win, d_start, d_end):
    bad = n_text >= 2 and (n_win < max(1, n_text) * 0.5
                           or (n_win > n_text * 2.5 and n_win - n_text > 8))
    if bad:
        return "C"
    if d_start <= 0.30 and d_end <= 0.30:
        return "A"
    return "B"


def nearest(xs, x):
    return min((abs(x - v) for v in xs), default=9.99)


def main():
    tl = jload(os.path.join(HERE, "assets", "timeline.json"))
    ev = load_evidence()
    archives = sorted(glob.glob(os.path.join(BASE, "U*", "01_正文篇章", "句级数据_p*.json")))

    units, sent_rows = [], []
    for f in archives:
        doc = jload(f)
        page = doc["page"]
        unit = doc.get("unit", "?")
        key = doc.get("passage_key") or ""
        rows = tl.get(page)
        if rows is None:
            print("[!] %s 归档有、timeline 无 → 跳过" % page)
            continue

        # 双写一致性（硬规约①）
        arc = doc["sentences"]
        dw_ok = (len(arc) == len(rows))
        if dw_ok:
            for a, b in zip(arc, rows):
                if a["text"] != b["text"] or abs(float(a["start_s"]) - float(b["start_s"])) > 0.001 \
                        or abs(float(a["end_s"]) - float(b["end_s"])) > 0.001:
                    dw_ok = False
                    break

        # 找词级证据：U1–U4 用 passage_key，其余用 page
        e = ev.get(key) or ev.get(page)
        if e is None:
            units.append(dict(unit=unit, page=page, key=key, title=doc.get("title", ""),
                              type=doc.get("type", ""), n_sent=len(rows), evidence="MISSING",
                              grade="N/A", double_write="OK" if dw_ok else "MISMATCH"))
            print("[!] %s 无词级证据" % page)
            continue

        words = e["words"]
        starts = sorted(a for a, b, t in words)
        ends = sorted(b for a, b, t in words)
        dur = e["duration"]
        covered = 0
        srows = []
        for s in rows:
            st, en = float(s["start_s"]), float(s["end_s"])
            n_text = wc(s["text"])
            n_win = sum(1 for a, b, t in words if st - 0.2 <= (a + b) / 2 <= en + 0.2)
            covered += n_win
            d_start = round(nearest(starts, st), 3)
            d_end = round(nearest(ends, en), 3)
            g = grade_of(n_text, n_win, d_start, d_end)
            srows.append(dict(
                unit=unit, page=page, key=key, title=doc.get("title", ""),
                sent=int(s["i"]) + 1, start_s=st, end_s=en,
                dur_s=round(en - st, 3), text=s["text"],
                n_text=n_text, n_win=n_win,
                ratio=round(n_win / max(1, n_text), 3),
                d_start=d_start, d_end=d_end, grade=g))
        sent_rows.extend(srows)

        # 间隙：只记线索，不判漏句（§4 强制三方对账）
        gaps, prev_end = [], 0.0
        for s in rows:
            st, en = float(s["start_s"]), float(s["end_s"])
            if st - prev_end > 2.0:
                gw = [t for a, b, t in words if prev_end <= (a + b) / 2 < st]
                if len(gw) >= 3:
                    gaps.append(dict(a=round(prev_end, 2), b=round(st, 2),
                                     n=len(gw), sample=" ".join(gw[:10])))
            prev_end = en
        tail_words = 0
        if dur - prev_end > 2.0:
            tail_words = sum(1 for a, b, t in words if (a + b) / 2 >= prev_end)

        grades = [r["grade"] for r in srows]
        pg = "C" if "C" in grades else ("B" if "B" in grades else "A")
        units.append(dict(
            unit=unit, page=page, key=key, title=doc.get("title", ""),
            type=doc.get("type", ""), n_sent=len(rows),
            n_words=len(words), coverage=round(covered / max(1, len(words)), 3),
            n_A=grades.count("A"), n_B=grades.count("B"), n_C=grades.count("C"),
            d_start_max=max((r["d_start"] for r in srows), default=0),
            d_end_max=max((r["d_end"] for r in srows), default=0),
            ratio_min=min((r["ratio"] for r in srows), default=0),
            ratio_max=max((r["ratio"] for r in srows), default=0),
            n_gaps_with_words=len(gaps), gap_words=sum(g["n"] for g in gaps),
            tail_words=tail_words, double_write="OK" if dw_ok else "MISMATCH",
            evidence=e["src"], grade=pg, gaps=gaps, duration=round(dur, 2)))

    # ---------------- 输出 ----------------
    os.makedirs(REPORTS, exist_ok=True)
    unit_fields = ["unit", "page", "key", "title", "type", "n_sent", "n_words",
                   "coverage", "n_A", "n_B", "n_C", "d_start_max", "d_end_max",
                   "ratio_min", "ratio_max", "n_gaps_with_words", "gap_words",
                   "tail_words", "double_write", "evidence", "grade", "duration"]
    sent_fields = ["unit", "page", "key", "title", "sent", "start_s", "end_s",
                   "dur_s", "text", "n_text", "n_win", "ratio", "d_start", "d_end", "grade"]

    def dump_csv(path, fields, rows):
        with io.open(path, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)

    dump_csv(os.path.join(REPORTS, STEM + "_篇章.csv"), unit_fields, units)
    dump_csv(os.path.join(REPORTS, STEM + "_逐句.csv"), sent_fields, sent_rows)

    payload = dict(
        date="2026-11-14",
        scope="U1–U12 共 48 篇正课文（p202 深链篇无归档，不在核查范围）",
        disclaimer="全部指标为可机检判定，非人工听审准确率；"
                   "有词间隙仅列线索，须按 _ALIGNMENT_WORKFLOW.md §4 三方对账后才可定性",
        confidence="aligner 的 LCS 词映射率情况1 恒 1.000、无鉴别力，本核查不采用",
        n_units=len(units), n_sentences=len(sent_rows),
        n_with_evidence=sum(1 for u in units if u.get("evidence") not in (None, "MISSING")),
        n_double_write_ok=sum(1 for u in units if u.get("double_write") == "OK"),
        grade_counts={g: sum(1 for r in sent_rows if r["grade"] == g) for g in "ABC"},
        units=units, sentences=sent_rows)
    json.dump(payload, io.open(os.path.join(REPORTS, STEM + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ---------------- 人读报告 ----------------
    L = ["# 全站句级对齐质量核查 · 48 篇 / %d 句" % len(sent_rows), "",
         "> 日期：2026-11-14。数据：`assets/timeline.json` × 归档 `句级数据_pXXX.json` × ASR 词级证据。",
         "> 脚本：`_verify_alignment_all.py`（只读，不改任何正典）。", "",
         "## 一、结论", "",
         "- 证据覆盖：**%d / %d 篇**有词级缓存（U7/U8/U12 共 12 篇于当日补齐）。" % (
             payload["n_with_evidence"], len(units)),
         "- 双写一致性：**%d / %d 篇**归档 × timeline 逐句同文本同时间。" % (
             payload["n_double_write_ok"], len(units)),
         "- 逐句分级：A %d / B %d / C %d（可机检判定，非听审准确率）。" % (
             payload["grade_counts"]["A"], payload["grade_counts"]["B"], payload["grade_counts"]["C"]),
         "- p202 深链篇无归档，不在 48 篇核查范围；timeline 共 49 篇。", "",
         "## 二、口径与边界（勿误读）", "",
         "1. 词数配比 = 句窗（±0.2s）内实录 ASR 词数 / 句词数；<0.5 或 >2.5 且差>8 → C。",
         "2. 起点/终点残差 = 句边界到最近 ASR 词边界距离；双残差 ≤0.30s → A，否则 B。",
         "3. **aligner 的 `confidence`（LCS 词映射率）情况1 恒 1.000、无鉴别力，本核查不采用。**",
         "4. **有词间隙只列为线索**：按 `_ALIGNMENT_WORKFLOW.md` §4，判定漏句前必须做",
         "   「归档句数 == 课本源行数」+「间隙词归类」+「ASR/源文本交叉印证」三方对账。",
         "   2026-11-12 尾部空隙、2026-11-14 情况2 三篇中段间隙，两次误判皆因跳过此步。",
         "5. 覆盖率 <85% 不等于缺陷：报幕、署名、小节题注、音频独有台词都会拉低覆盖率。", "",
         "## 三、篇章汇总", "",
         "| 单元 | 页 | 类型 | 句数 | ASR词 | 覆盖率 | A/B/C | 间隙线索(词) | 尾隙词 | 双写 | 证据 | 级 |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for u in units:
        if u.get("evidence") == "MISSING":
            L.append("| %s | %s | %s | %s | — | — | — | — | — | %s | **缺失** | N/A |" % (
                u["unit"], u["page"], u.get("type", ""), u["n_sent"], u.get("double_write", "")))
            continue
        L.append("| %s | %s | %s | %d | %d | %.0f%% | %d/%d/%d | %d(%d) | %d | %s | %s | %s |" % (
            u["unit"], u["page"], u.get("type", ""), u["n_sent"], u["n_words"],
            u["coverage"] * 100, u["n_A"], u["n_B"], u["n_C"],
            u["n_gaps_with_words"], u["gap_words"], u["tail_words"],
            u["double_write"], u["evidence"].split(":")[0], u["grade"]))
    L += ["", "## 四、需复核线索（不自动定性）", ""]
    cs = [r for r in sent_rows if r["grade"] == "C"]
    if cs:
        L.append("**C 级句 %d 条**（配比异常，需按源文本三方对账）：" % len(cs))
        L += ["| 单元 | 页 | 句 | 时间 | 句词/窗内 | 文本 |", "|---|---|---|---|---|---|"]
        for r in cs[:40]:
            L.append("| %s | %s | %d | %.2f–%.2f | %d/%d | %s |" % (
                r["unit"], r["page"], r["sent"], r["start_s"], r["end_s"],
                r["n_text"], r["n_win"], r["text"][:60].replace("|", "\\|")))
    else:
        L.append("无 C 级句。")
    dw = [u for u in units if u.get("double_write") == "MISMATCH"]
    if dw:
        L += ["", "**双写不一致 %d 篇**：%s" % (len(dw), ", ".join(u["page"] for u in dw))]
    else:
        L += ["", "双写一致性：全部 OK。"]
    low = [u for u in units if u.get("coverage", 1) < 0.85 and u.get("evidence") != "MISSING"]
    if low:
        L += ["", "**覆盖率 <85%% 的 %d 篇**（多为版面元素被朗读，需查证非缺陷）：%s" % (
            len(low), ", ".join("%s(%.0f%%)" % (u["page"], u["coverage"] * 100) for u in low))]
    L += ["", "## 五、产物", "",
          "- `%s_篇章.csv`（48 行，canonical 摘要）" % STEM,
          "- `%s_逐句.csv`（%d 行，按篇章·句子罗列）" % (STEM, len(sent_rows)),
          "- `%s.json`（全量机器可读 + 口径说明）" % STEM,
          "- 本报告 `.md`", ""]
    io.open(os.path.join(REPORTS, STEM + ".md"), "w", encoding="utf-8").write("\n".join(L))

    print("核查完成：%d 篇 / %d 句；有证据 %d/%d；双写 OK %d/%d；A/B/C = %d/%d/%d" % (
        len(units), len(sent_rows), payload["n_with_evidence"], len(units),
        payload["n_double_write_ok"], len(units),
        payload["grade_counts"]["A"], payload["grade_counts"]["B"], payload["grade_counts"]["C"]))
    for u in units:
        if u.get("evidence") == "MISSING" or u.get("double_write") == "MISMATCH" or u.get("grade") == "C":
            print("  [!] %s %s evidence=%s dw=%s grade=%s" % (
                u["unit"], u["page"], u.get("evidence"), u.get("double_write"), u.get("grade")))
    print("输出 → reports/%s*" % STEM)


if __name__ == "__main__":
    main()
