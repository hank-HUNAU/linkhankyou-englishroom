#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""整合输出：把一键管道产出的四份源 xlsx(主报告/学生卡/备课本/语音卡) 按页签抽取，
组装成【教师版】【学生版】两份权威合集。页签级复制，保留列宽/行高/合并/冻结窗格/字体。

用法(在前缀一致的情形下):
  python vocab_merge.py --base london
  python vocab_merge.py --report london_报告.xlsx --cards london_学生卡.xlsx \
                        --prep london_备课本.xlsx --voice london_语音卡.xlsx --out london
自动拼路径: --base 下  <base>_报告 / <base>_学生卡 / <base>_备课本 / <base>_语音卡。
输出: <out>_教师版.xlsx 与 <out>_学生版.xlsx (缺页签自动跳过, 不需四份都在)。
"""
import os, sys, argparse

SRC_SUFFIX = ("_报告", "_学生卡", "_备课本", "_语音卡")
_SFX_MAP = {"报告": "_报告", "学生卡": "_学生卡", "备课本": "_备课本", "语音卡": "_语音卡"}

# 页签归属: (目标版本, [页签名])；页签名若源中不存在则跳过。
# 主报告里"命中-*"为动态前缀, 用前缀捕获(_START/_PREFIX)。
_TEACHER = [
    # 主报告
    "覆盖率", "超纲词", "候选待核短语", "专名词",
    ("HIT", "命中-"),          # 命中-KET/PET/NGSL/NAWL, 命中-PET(排除KET) 一并收入
    # 学生卡
    "学生记忆卡", "实词表", "虚词表",
    # 备课本
    "分层词卡", "考点命题矩阵", "超纲进阶补卡", "单元考点统计",
    # 语音卡
    "原句朗读标注", "单词英式音标", "语音讲授要点",
]
# 学生版: 实词/虚词/专名词表在整合时由 _inject_ipa_into_student 注入"英式音标"列,
# 因此不单列独立音标页——音标跟着词走(教师版仍保留全量音标索引页)。
_STUDENT = [
    # 学生卡
    "学生记忆卡", "实词表", "虚词表", "专名词",
    # 语音卡
    "原句朗读标注",
]


def copy_sheet(src_ws, dst_wb, name):
    """把源 sheet 深拷贝为 dst_wb 的一张新 sheet, 保留值/列宽/行高/合并/冻结/字体。"""
    from openpyxl.utils import get_column_letter
    ws = dst_wb.create_sheet(title=name)
    # 单元格值 + 字体/边框/对齐等样式(共享样式对象)
    ws._cells = {}
    for row in src_ws.iter_rows():
        for cell in row:
            if cell.value is None and cell.style is None:
                continue
            nc = ws.cell(row=cell.row, column=cell.column, value=cell.value)
            try:
                nc._style = cell._style        # 复制样式引用
            except Exception:
                pass
            if cell.has_style:
                pass
    # 列宽 / 行高
    for k, v in src_ws.column_dimensions.items():
        ws.column_dimensions[k] = v
    for k, v in src_ws.row_dimensions.items():
        ws.row_dimensions[k] = v
    # 合并单元格
    for rng in src_ws.merged_cells.ranges:
        ws.merge_cells(str(rng))
    # 冻结窗格
    ws.freeze_panes = src_ws.freeze_panes
    return ws


def collect(targets, wb, name, subs=None):
    """从 wb 收集名为 name(或 subs 中的任一同名 sheet) 的页签到 targets。返回是否拷贝成功。"""
    if name in wb.sheetnames:
        copy_sheet(wb[name], targets["wb"], name)
        return True
    if subs:
        for s in subs:
            if s in wb.sheetnames:
                copy_sheet(wb[s], targets["wb"], s)
                return True
    return False


# 学生版实词/虚词/专名词表注入"英式音标"列。
# 找行: 某行首列=表头关键词, 其下一行为数据. 目标列: 追加到现有列最右。
def _inject_ipa_into_student(dst, books):
    """为学生版实词/虚词/专名词表注入"英式音标"列。
    语源优先级: ①学生记忆卡"音标"列(同源同词形) ②语音卡"单词英式音标"页。
    找不到任何源时静默跳过(列留空)。"""
    ipa_map = {}
    # ① 学生记忆卡: Word列(词目) + 音标列
    for key, wb in books.items():
        if wb and ("学生记忆卡" in wb.sheetnames):
            src = wb["学生记忆卡"]
            header_row = next(rows for rows in src.iter_rows(values_only=True)
                              if rows and any(x == "Word" for x in rows))
            cols = {v: i for i, v in enumerate(header_row) if v is not None}
            wc, ic = cols.get("Word"), cols.get("音标")
            if wc is not None and ic is not None:
                for ridx, row in enumerate(src.iter_rows(values_only=True), 1):
                    if ridx == 1:
                        continue
                    w = row[wc]
                    if w and row[ic]:
                        ipa_map[str(w).strip()] = str(row[ic]).strip()
            break
    # ② 语音卡"单词英式音标"页补缺
    for key, wb in books.items():
        if wb and ("单词英式音标" in wb.sheetnames):
            src = wb["单词英式音标"]
            header_row = next(rows for rows in src.iter_rows(values_only=True)
                              if rows and any(x == "词汇" for x in rows))
            cols = {v: i for i, v in enumerate(header_row) if v is not None}
            wc, ic = cols.get("词汇"), cols.get("英式音标UK")
            if wc is not None and ic is not None:
                for ridx, row in enumerate(src.iter_rows(values_only=True), 1):
                    if ridx == 1:
                        continue
                    w = str(row[wc] or "").strip()
                    if w and row[ic] and w not in ipa_map:
                        ipa_map[w] = str(row[ic]).strip()
            break
    del src
    if not ipa_map:
        return
    target_sheets = dst.sheetnames
    word_col_key = ("词", "专名")
    for sn in ("实词表", "虚词表", "专名词"):
        if sn not in target_sheets:
            continue
        ws = dst[sn]
        hdr_row = None
        for ridx in range(1, ws.max_row + 1):
            vals = [ws.cell(row=ridx, column=c).value for c in range(1, ws.max_column + 1)]
            if any(v in word_col_key for v in vals):
                hdr_row = ridx
                break
        if hdr_row is None:
            continue
        wcol = next(c for c in range(1, ws.max_column + 1)
                    if ws.cell(row=hdr_row, column=c).value in word_col_key)
        col = ws.max_column + 1
        ws.cell(row=hdr_row, column=col, value="英式音标")
        for ridx in range(hdr_row + 1, ws.max_row + 1):
            w = ws.cell(row=ridx, column=wcol).value
            if w and str(w).strip() in ipa_map:
                ws.cell(row=ridx, column=col, value=ipa_map[str(w).strip()])
        print("[学生版] 已注入英式音标 -> %s" % sn)


def main():
    ap = argparse.ArgumentParser(description="整合四份源xlsx -> 教师版/学生版")
    ap.add_argument("--base", default=None,
                    help="统一前缀, 自动定位 <base>_报告/学生卡/备课本/语音卡.xlsx")
    for sfx, key in (("报告", "report"), ("学生卡", "cards"), ("备课本", "prep"), ("语音卡", "voice")):
        ap.add_argument("--" + key, default=None, help="显式指定 <" + key + "> 源 xlsx 路径")
    ap.add_argument("--out", default=None, help="输出前缀(默认同 --base)")
    a = ap.parse_args()

    base = a.out or a.base
    if not base:
        ap.error("需要 --base 或 --out")
    if not a.base and not (a.report or a.cards or a.prep or a.voice):
        ap.error("未指定任何源: 用 --base 自动拼, 或用 --report/--cards/--prep/--voice 显式给出 xlsx 路径")

    # 解析源文件真实路径
    paths = {}
    for sfx, key in (("报告", "report"), ("学生卡", "cards"), ("备课本", "prep"), ("语音卡", "voice")):
        p = getattr(a, key)
        if p is None and a.base:
            cand = a.base + _SFX_MAP[sfx] + ".xlsx"
            if os.path.exists(cand):
                p = cand
        if p:
            paths[key] = p

    import openpyxl
    # 预加载全部源
    books = {}
    for key, p in paths.items():
        try:
            books[key] = openpyxl.load_workbook(p, data_only=False)
        except Exception as ex:
            sys.stderr.write("加载失败 %s: %s\n" % (p, ex))

    spec = {"教师版": _TEACHER, "学生版": _STUDENT}
    for version, seq in spec.items():
        dst = openpyxl.Workbook()
        dst.remove(dst.active)               # 去掉默认空 sheet
        hit_done = False
        for item in seq:
            name, subs = (item, None) if isinstance(item, str) else (None, item[1])
            if item[0] == "HIT":             # "命中-*" 动态前缀吸收
                collected = False
                for key, wb in books.items():
                    for sn in list(wb.sheetnames):
                        if sn.startswith("命中-") and sn not in dst.sheetnames:
                            copy_sheet(wb[sn], dst, sn); collected = True
                if not collected:
                    sys.stderr.write("[%s] 无 '命中-*' 页签, 跳过\n" % version)
                continue
            ok = False
            for key, wb in books.items():
                if collect({"wb": dst}, wb, name, subs):
                    ok = True
                    break
            if not ok:
                sys.stderr.write("[%s] 缺页签 '%s', 跳过\n" % (version, name))
        if version == "学生版":            # 音标跟着词走: 注入实词/虚词/专名词表
            _inject_ipa_into_student(dst, books)
        out = base + "_" + version + ".xlsx"
        dst.save(out)
        print("生成 %s: %d 个页签" % (out, len(dst.sheetnames)))
        dst.close()
        for wb in books.values():
            try:
                wb.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()