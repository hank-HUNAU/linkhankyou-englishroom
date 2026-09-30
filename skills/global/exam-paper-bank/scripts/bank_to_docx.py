# -*- coding: utf-8 -*-
"""题库纯文本 → 导入用 docx（一段一行，格式原样保留）

与 txt 同源：先由 txt 定稿，再由本脚本生成 docx，避免两者分别手写而不一致。
空行不写入 docx；字体 Times New Roman + 中文宋体 10.5pt；单倍行距；段前段后 0。

用法：
  python bank_to_docx.py --txt <题库.txt> --out <输出目录> --name <章>_题库_导入格式
"""
import argparse
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt


def build(txt: str, out_dir: Path, name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir.joinpath(name + ".txt").write_text(txt, encoding="utf-8")

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(10.5)
    try:
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    except AttributeError:
        pass
    st.paragraph_format.space_before = Pt(0)
    st.paragraph_format.space_after = Pt(0)
    st.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    n = 0
    for ln in txt.splitlines():
        if not ln.strip():
            continue
        doc.add_paragraph(ln)
        n += 1

    out = out_dir / (name + ".docx")
    doc.save(out)
    print("段落 %d 行 → %s（%.1f KB）" % (n, out.name, out.stat().st_size / 1024))
    print("同时落盘 %s.txt" % name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt", required=True, help="题库纯文本（一段一行）")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--name", required=True, help="输出文件名，不含扩展名")
    a = ap.parse_args()
    build(Path(a.txt).read_text(encoding="utf-8"), Path(a.out), a.name)


if __name__ == "__main__":
    main()
