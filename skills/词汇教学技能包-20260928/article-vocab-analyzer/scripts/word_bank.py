# -*- coding: utf-8 -*-
"""词汇库：SQLite 内核累积 + Excel 视图导出（与 assess_vocab.py --db 配套）。

设计：数据库是"累积的计算层"，Excel 是"人能读的交付层"。
  - words     表：按 (lemma,pos) 主键累积，跨篇聚合频次/归属层热点/例句。
  - word_docs 表：文档维度去重，保证同一文档内某词只计 1 次到 n_doc。
  - docs      表：记录每次入库的文章（source、路径）。
单篇报告仍是主产物；本模块只在传 --db 时把词项级结论 UPSERT 进库。
"""
import json, sqlite3, collections


_SCHEMA = """
CREATE TABLE IF NOT EXISTS words(
    lemma    TEXT NOT NULL,
    pos      TEXT NOT NULL DEFAULT '',
    layer    TEXT NOT NULL DEFAULT '',      -- 归属层(KET<PET<NGSL<NAWL/空)
    n_doc    INTEGER NOT NULL DEFAULT 0,     -- 出现的不同文章数
    freq     INTEGER NOT NULL DEFAULT 0,     -- 累计token频次
    cefr     TEXT NOT NULL DEFAULT '',       -- 难度标注(可选)
    examples TEXT NOT NULL DEFAULT '[]',     -- 累积原文例句(JSON数组, 最多3条)
    PRIMARY KEY(lemma, pos)
);
CREATE TABLE IF NOT EXISTS word_docs(
    lemma TEXT NOT NULL,
    pos   TEXT NOT NULL DEFAULT '',
    doc   TEXT NOT NULL,
    PRIMARY KEY(lemma, pos, doc)
);
CREATE TABLE IF NOT EXISTS docs(
    path   TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    ts     INTEGER NOT NULL
);
"""

_EX_MAX = 3


def _conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA)
    return conn


def _examples_merge(ex_json, new_text):
    if not new_text:
        return ex_json or "[]"
    try:
        arr = json.loads(ex_json) if ex_json else []
        if not isinstance(arr, list):
            arr = []
    except (ValueError, TypeError):
        arr = []
    if new_text not in arr:
        arr.append(new_text)
    return json.dumps(arr[:_EX_MAX], ensure_ascii=False)


def upsert_report(db_path, out_items, source, doc_path):
    """把一次判定的词项级结论 UPSERT 进词库，跨文档去重计数。

    out_items: assess() 的归属分层结果(逐 token 的 dict)。
    doc_path: 唯一文章标识(优先文件路径; 无则用 source+时间戳)。
    返回 (本次出现不同词数, 本次新增词数)。
    """
    conn = _conn(db_path)
    conn.execute("INSERT OR REPLACE INTO docs(path, source, ts) VALUES(?,?,?)",
                 (doc_path, source, int(__import__("time").time())))

    # 聚合每个 (lemma,pos) 在本篇的频次、归属层热点、例句；跨文档去重计数交给 word_docs
    agg = collections.Counter()
    layers = {}
    ex_first = {}
    for it in out_items:
        if it["kind"] != "word":
            continue
        lm = it.get("lemma", "")
        if not lm:
            continue
        pos = it.get("pos", "") or ""
        key = (lm, pos)
        agg[key] += 1
        lc = layers.setdefault(key, collections.Counter())
        lc[it.get("layer", "")] += 1
        exs = it.get("examples") or []
        if exs and it.get("layer") and key not in ex_first:
            ex_first[key] = exs[0]
        if key not in ex_first and exs:
            ex_first[key] = exs[0]

    inserted = 0
    for (lm, pos), freq in agg.items():
        layer = layers[(lm, pos)].most_common(1)[0][0]
        cefr_v = it_c = ""  # 本模块不直接给 cefr，由调用方写入 or 留空
        new_ex = f"[{source}] {ex_first[(lm, pos)]}" if ex_first.get((lm, pos)) else ""

        row = conn.execute("SELECT n_doc, examples FROM words WHERE lemma=? AND pos=?",
                           (lm, pos)).fetchone()
        if row:
            n_doc, ex_json = row
            # 该文档首次遇到此词才 n_doc+1
            has_doc = conn.execute(
                "SELECT 1 FROM word_docs WHERE lemma=? AND pos=? AND doc=?", (lm, pos, doc_path)).fetchone()
            delta_doc = 0 if has_doc else 1
            if not has_doc:
                conn.execute("INSERT OR IGNORE INTO word_docs(lemma,pos,doc) VALUES(?,?,?)",
                             (lm, pos, doc_path))
            conn.execute(
                "UPDATE words SET freq=freq+?, n_doc=n_doc+?, layer=?, examples=? "
                "WHERE lemma=? AND pos=?",
                (freq, delta_doc, layer, _examples_merge(ex_json, new_ex), lm, pos))
        else:
            inserted += 1
            conn.execute(
                "INSERT OR IGNORE INTO word_docs(lemma,pos,doc) VALUES(?,?,?)", (lm, pos, doc_path))
            conn.execute(
                "INSERT OR IGNORE INTO words(lemma,pos,layer,n_doc,freq,cefr,examples) "
                "VALUES(?,?,?,?,?,'',?)",
                (lm, pos, layer, 1, freq, _examples_merge('[]', new_ex)))
    conn.commit()
    conn.close()
    return len(agg), inserted


# ---------------- Excel 视图导出 ----------------
def export_views(db_path, xlsx_path):
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    conn = _conn(db_path)
    rows = conn.execute(
        "SELECT lemma,pos,layer,n_doc,freq,cefr,examples FROM words").fetchall()

    wb = openpyxl.Workbook()
    HDR = Font(bold=True, color="FFFFFF"); FILL = PatternFill("solid", fgColor="2E8B57")
    LW = lambda ws, widths, n: [setattr(ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width, "value", w) or None for i, w in enumerate(widths, 1)]

    # 1) 分层词卡（教学视图）
    ws = wb.active; ws.title = "分层词卡"
    ws.append(["归属层", "词", "词性", "出现文章数", "累计频次", "CEFR", "累积例句"])
    for c in range(1, 8):
        ws.cell(1, c).font = HDR; ws.cell(1, c).fill = FILL
    for lm, pos, layer, nd, fr, cf, ex in sorted(rows, key=lambda r: (-r[4], r[0])):
        ws.append([layer, lm, pos, nd, fr, cf, _pretty_ex(ex)])
    ws.freeze_panes = "A2"
    for i, w in enumerate((10, 22, 12, 12, 10, 8, 90), 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # 2) 补卡清单（out/NAWL 累积视图，按出现文章数排序）
    ws2 = wb.create_sheet("补卡清单")
    ws2.append(["词", "词性", "出现文章数", "累计频次", "CEFR", "累积例句"])
    for c in range(1, 7):
        ws2.cell(1, c).font = HDR; ws2.cell(1, c).fill = FILL
    for lm, pos, layer, nd, fr, cf, ex in sorted(
            (r for r in rows if r[2] in (None, "", "out", "NAWL")), key=lambda r: (-r[3], -r[4])):
        ws2.append([lm, pos, nd, fr, cf, _pretty_ex(ex)])
    ws2.freeze_panes = "A2"
    for i, w in enumerate((22, 12, 12, 10, 8, 90), 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # 3) 研究覆盖视图
    ws3 = wb.create_sheet("研究覆盖")
    ws3.append(["文章路径", "词表来源", "入库时间"])
    for c in range(1, 4):
        ws3.cell(1, c).font = HDR; ws3.cell(1, c).fill = FILL
    for dpath, source, ts in conn.execute("SELECT path,source,ts FROM docs").fetchall():
        from datetime import datetime
        ws3.append([dpath, source, datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")])
    ws3.freeze_panes = "A2"
    for i, w in enumerate((70, 24, 18), 1):
        ws3.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    conn.close()
    wb.save(xlsx_path)
    return xlsx_path


def _pretty_ex(ex_json):
    try:
        arr = json.loads(ex_json) if ex_json else []
        if not isinstance(arr, list):
            return ""
        return "; ".join(str(x) for x in arr if x)
    except (ValueError, TypeError):
        return ""


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else ""
    if q == "exports" and len(sys.argv) >= 4:
        export_views(sys.argv[2], sys.argv[3])
        print("saved views:", sys.argv[3])