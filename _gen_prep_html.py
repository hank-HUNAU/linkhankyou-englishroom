# -*- coding: utf-8 -*-
"""备课本 HTML 可视化生成器：备课本 xlsx → 单文件 HTML（四页签）。

用法：python _gen_prep_html.py 词汇诊断/篇章词汇_产出/u8_p075_备课本.xlsx [更多.xlsx ...]
产出：词汇诊断/备课本_<名>.html（与 xlsx 同目录同名）
"""
import os, sys, html, json, re
import openpyxl

TABS = [("分层词卡", "word"), ("考点命题矩阵", "exam"), ("超纲进阶补卡", "gap"), ("单元考点统计", "stat")]
STYLE = """
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#f5f6f8;color:#222;margin:0;padding:20px;line-height:1.55}
h1{font-size:19px;margin:0 0 2px}.sub{color:#666;font-size:12.5px;margin-bottom:14px}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.tabs button{border:1px solid #d7dce6;background:#fff;color:#3c4356;padding:7px 16px;border-radius:20px;font-size:13px;cursor:pointer}
.tabs button.on{background:#185FA5;color:#fff;border-color:#185FA5}
.panel{display:none;background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:auto;max-height:78vh}
.panel.on{display:block}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid #eef0f4;padding:7px 10px;text-align:left;font-size:12.5px;vertical-align:top}
th{position:sticky;top:0;background:#eef3fb;color:#1565c0;white-space:nowrap;font-size:12px}
tr:last-child td{border-bottom:none}
td.mono{font-family:Consolas,Menlo,monospace;font-size:11.5px;color:#555;max-width:340px;white-space:pre-wrap}
td.c{text-align:center;font-variant-numeric:tabular-nums}
.layer{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px;background:#e7eefb;color:#1c4fb0;white-space:nowrap}
.gap td.mono,.exam td.mono{max-width:420px}
.stat td.c{font-weight:600}
.foot{color:#888;font-size:11.5px;margin-top:12px}
"""

def cell(v):
    return html.escape("" if v is None else str(v))

def is_num(v):
    return bool(re.fullmatch(r"-?\d+(\.\d+)?", str(v or "").strip()))

def render_sheet(name, rows):
    if not rows:
        return "<p style='color:#888;padding:14px'>（空）</p>"
    head = rows[0]
    body = rows[1:]
    out = ["<table><thead><tr>" + "".join(f"<th>{cell(h)}</th>" for h in head) + "</tr></thead><tbody>"]
    for r in body:
        tds = []
        for i, v in enumerate(r):
            s = str(v or "")
            if s.startswith(("分层|", "|")) or "layer" in str(head[i]).lower():
                tds.append(f'<td class="layer">{cell(v)}</td>')
            elif i == 0 and len(s) <= 14 and "-" not in s:
                tds.append(f'<td class="layer">{cell(v)}</td>')
            elif i in (4, 5) and is_num(v) or str(head[i]) in ("频次", "跨句Range", "词条数"):
                tds.append(f'<td class="c">{cell(v)}</td>')
            elif len(s) > 24:
                tds.append(f'<td class="mono">{cell(v)}</td>')
            else:
                tds.append(f"<td>{cell(v)}</td>")
        out.append("<tr>" + "".join(tds) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)

def main():
    for path in sys.argv[1:]:
        wb = openpyxl.load_workbook(path, read_only=True)
        sheets = {}
        for sn in wb.sheetnames:
            sheets[sn] = [list(r) for r in wb[sn].iter_rows(values_only=True)]
        title = os.path.basename(path).replace("_备课本.xlsx", "")
        m = re.search(r"u(\d+)_p(\d+)", title)
        head_title = f"Unit {m.group(1)} · p{m.group(2)} · 备课本" if m else title
        tabs_html, panels = [], []
        for i, (label, _) in enumerate(TABS):
            sn = next((s for s in wb.sheetnames if label in s), wb.sheetnames[i])
            cls = "on" if i == 0 else ""
            tabs_html.append(f'<button class="{cls}" data-i="{i}">{label}</button>')
            panels.append(f'<div class="panel {cls}" id="p{i}">{render_sheet(sn, sheets.get(sn, []))}</div>')
        doc = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(head_title)}</title>
<style>{STYLE}</style></head><body>
<h1>{html.escape(head_title)}</h1>
<div class="sub">九层词表 · 备课本可视化 · 由 xlsx 渲染</div>
<div class="tabs">{''.join(tabs_html)}</div>
{''.join(panels)}
<div class="foot">数据源：{html.escape(os.path.basename(path))} · 生成于 {__import__('datetime').date.today()}</div>
<script>
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{{
  document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); document.getElementById('p'+b.dataset.i).classList.add('on');
}});
</script></body></html>"""
        out = os.path.join(os.path.dirname(path), "备课本_" + os.path.basename(path).replace("_备课本.xlsx", "") + ".html")
        open(out, "w", encoding="utf-8").write(doc)
        print(f"[{title}] → {os.path.basename(out)} ({os.path.getsize(out)} B)")

if __name__ == "__main__":
    main()
