# -*- coding: utf-8 -*-
"""本地教学资源生成器：教师讲解卡 + 学生发放页（HTML，A4 可打印，零联网、零音频）

用户口径（2026-10-31 拍板）：
  **意群与语块都不上线**，只作为本地资源；由教师课堂讲解、打印发放。
  意群 = 句法教学单位；语块 = 预制语块（高频复现表达）。音频不参与本链路。

用法：
  python _gen_teacher_pack.py --page p048
  python _gen_teacher_pack.py --page p048 --out-dir "…/05_教学资源"

产出：
  教师讲解卡_pXXX.html  —— 意群切分+句法功能+教学点；语块释义+教学提示；课堂流程；依据与边界
  学生发放页_pXXX.html  —— 课文意群版；划意群练习；语块卡（可裁剪）；造句
"""
import argparse
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# ── 句法功能 → 颜色族（教学设计：主语绿 / 谓语紫 / 宾语表语蓝 / 状语从句橙 / 连接插入灰）
FAMILY = [
    ('主语', 'g'), ('谓语', 'p'), ('系', 'p'), ('表语', 'b'), ('宾语', 'b'),
    ('状语', 'o'), ('从句', 'o'), ('定语', 'b'), ('插入语', 'n'), ('连接', 'n'),
    ('祈使', 'p'), ('省略', 'n'), ('疑问', 'b'), ('存在句', 'p'), ('并列', 'n'),
]


def fam(fn):
    for key, cls in FAMILY:
        if key in fn:
            return cls
    return 'n'


def esc(s):
    return (str(s or '').replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def find(pattern):
    for root, dirs, files in os.walk(os.path.join(HERE, '..')):
        for f in files:
            if f == pattern:
                return os.path.join(root, f)
    return None


def load(page):
    digits = re.sub(r'\D', '', page)
    page = 'p%03d' % int(digits)
    paths = {
        'yq': find('意群_%s.json' % page),
        'ck': find('语块_%s.json' % page),
        'sj': find('句级数据_%s.json' % page),
        'zh': find('译文_%s.json' % page),
    }
    missing = [k for k, v in paths.items() if not v]
    if missing:
        raise SystemExit('缺少数据：%s' % missing)
    yq = json.load(io.open(paths['yq'], encoding='utf-8'))
    ck = json.load(io.open(paths['ck'], encoding='utf-8'))
    sj = json.load(io.open(paths['sj'], encoding='utf-8'))
    zh = json.load(io.open(paths['zh'], encoding='utf-8'))
    zhm = {e['i']: e.get('zh', '') for e in zh.get('entries', [])}
    out_dir = os.path.join(os.path.dirname(paths['yq']), '..', '05_教学资源')
    return page, yq, ck, sj, zhm, os.path.normpath(out_dir)


CSS = """
:root{--green:#10B981;--green-bg:#E8F8F1;--purple:#7C3AED;--purple-bg:#F2EDFE;--blue:#1A4FA0;--blue-bg:#EEF3FF;
--orange:#B45309;--orange-bg:#FEF3E2;--ink:#1C1C1E;--ink2:#3A3A3C;--ink3:#8E8E93;--line:#E5E5EA;--rad:10px}
*{box-sizing:border-box}
body{margin:0;background:#F7F7F9;color:var(--ink);
font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,-apple-system,sans-serif;
font-size:13px;line-height:1.65;-webkit-font-smoothing:antialiased}
.page{width:210mm;min-height:297mm;margin:0 auto 10mm;background:#fff;padding:14mm 15mm;
box-shadow:0 1px 3px rgba(0,0,0,.08)}
h1{font-size:19px;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:14px;margin:22px 0 8px;padding-bottom:6px;border-bottom:2px solid var(--green);display:flex;
align-items:center;gap:8px}
h2 .num{background:var(--green);color:#fff;border-radius:6px;width:20px;height:20px;display:inline-flex;
align-items:center;justify-content:center;font-size:11.5px;font-weight:800;flex:none}
h3{font-size:12.5px;margin:14px 0 6px;color:var(--ink2)}
.hd{border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:4px}
.hd .brand{font-size:10.5px;font-weight:800;letter-spacing:.14em;color:var(--purple);text-transform:uppercase}
.hd .sub{font-size:11.5px;color:var(--ink3);margin-top:3px}
.meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.pill{font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:999px;background:#F2F2F7;color:var(--ink2)}
.pill.g{background:var(--green-bg);color:#1F6B2E}.pill.p{background:var(--purple-bg);color:#4C1D95}
.note{background:var(--green-bg);border-left:3px solid var(--green);padding:8px 12px;border-radius:0 8px 8px 0;
font-size:11.5px;color:#1F6B2E;margin:10px 0}
.warn{background:var(--orange-bg);border-left:3px solid var(--orange);padding:8px 12px;border-radius:0 8px 8px 0;
font-size:11px;color:#7C2D12;margin:10px 0}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{border-bottom:1px solid var(--line);padding:7px 6px;vertical-align:top;text-align:left}
th{font-size:10.5px;color:var(--ink3);font-weight:800;letter-spacing:.06em;text-transform:uppercase}
td.n{color:var(--ink3);font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px;width:26px}
td.zh{color:var(--ink2);width:26%;font-size:11.5px}
td.pt{color:var(--ink2);width:26%;font-size:11px}
.seg{line-height:2.6}
.seg .g{display:inline-block;border-bottom:2px solid transparent;padding:0 1px}
.seg .g i{display:inline-block;font-style:normal;font-size:9px;font-weight:800;line-height:1.5;
padding:0 5px;border-radius:999px;margin-left:5px;vertical-align:2px;background:#F2F2F7;color:var(--ink2)}
.seg .g.g{border-color:var(--green)}.seg .g.g i{background:var(--green-bg);color:#0E8A62}
.seg .g.p{border-color:var(--purple)}.seg .g.p i{background:var(--purple-bg);color:var(--purple)}
.seg .g.b{border-color:var(--blue)}.seg .g.b i{background:var(--blue-bg);color:var(--blue)}
.seg .g.o{border-color:var(--orange)}.seg .g.o i{background:var(--orange-bg);color:var(--orange)}
.seg .g.n{border-color:#C7C7CC}.seg .g.n i{background:#F2F2F7;color:var(--ink3)}
.seg .sl{color:var(--ink3);font-weight:800;margin:0 6px;font-size:15px}
.ck{border:1px solid var(--line);border-radius:var(--rad);padding:9px 12px;margin-bottom:7px;
break-inside:avoid}
.ck .top{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}
.ck .en{font-size:14.5px;font-weight:800}
.ck .badge{font-size:9.5px;font-weight:800;padding:1px 7px;border-radius:999px;background:var(--blue-bg);color:var(--blue)}
.ck .badge.f{background:var(--green-bg);color:#1F6B2E}
.ck .zh{font-size:11.5px;color:var(--ink2);margin-top:3px}
.ck .ex{font-size:11px;color:var(--ink3);margin-top:5px;padding-top:5px;border-top:1px dashed var(--line)}
.ck .ex b{color:var(--blue);background:rgba(26,79,160,.09);border-radius:3px;padding:0 2px}
.ck .tip{font-size:10.5px;color:var(--ink3);margin-top:4px}
.ck .tip b{color:var(--purple)}
ol,ul{margin:6px 0 6px 18px;padding:0}
li{margin:3px 0}
.foot{margin-top:20px;padding-top:10px;border-top:1px solid var(--line);font-size:10px;color:var(--ink3);line-height:1.7}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.blank{border-bottom:1px solid #C7C7CC;height:26px;margin-top:6px}
.line{border-bottom:1px solid var(--line);height:22px}
.cut{border:1px dashed #C7C7CC}
@page{size:A4;margin:12mm}
@media print{
  body{background:#fff;font-size:11.5px}
  .page{width:auto;min-height:0;margin:0;padding:0;box-shadow:none}
  .page+.page{page-break-before:always}
  h2{page-break-after:avoid}
  .noprint{display:none}
}
"""


def seg_html(groups, show_fn=True):
    out = []
    for g in groups:
        c = fam(g['fn'])
        label = '<i>%s</i>' % esc(g['fn']) if show_fn else ''
        out.append('<span class="g %s">%s%s</span>' % (c, esc(g['t']), label))
    return '<span class="sl">/</span>'.join(out)


def teacher_html(page, yq, ck, zhm):
    rows = []
    for s in yq['sentences']:
        rows.append(
            '<tr><td class="n">%02d</td><td><div class="seg">%s</div></td><td class="zh">%s</td><td class="pt">%s</td></tr>'
            % (s['i'] + 1, seg_html(s['groups']), esc(zhm.get(s['i'], '')), esc(s.get('point', ''))))

    chunks = []
    for c in ck['chunks']:
        chunks.append(
            '<div class="ck"><div class="top"><span class="en">%s</span>'
            '<span class="badge%s">%s</span><span class="badge">%s</span></div>'
            '<div class="zh">%s</div>'
            '<div class="ex">%s<br>%s</div>'
            '<div class="tip"><b>教学提示</b>：%s　<span style="color:#C7C7CC">｜</span>　'
            '复现 %s 次 / %s 篇　MI %s</div></div>'
            % (esc(c['text']), ' f' if c.get('type') == '功能句' else '', esc(c.get('type', '')),
               esc(c.get('func', '')), esc(c.get('zh', '')),
               esc(c.get('ex', '')), esc(c.get('exZh', '')),
               esc(c.get('note', '')), c.get('freq', '-'), c.get('disp', '-'), c.get('mi', '-')))

    n = len(yq['sentences'])
    g = yq.get('n_groups', sum(len(s['groups']) for s in yq['sentences']))
    title = yq.get('title', '')

    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>教师讲解卡 · %(page)s %(title)s</title><style>%(css)s</style></head><body>
<div class="page">
<div class="hd">
  <div class="brand">TH!NK · 教师讲解卡</div>
  <h1>%(title)s</h1>
  <div class="sub">Unit %(unit)s · %(page)s · %(type)s · 本地教师资源（不上线）</div>
  <div class="meta">
    <span class="pill g">%(n)d 句</span>
    <span class="pill g">%(g)d 个意群</span>
    <span class="pill p">%(nc)d 条预制语块</span>
  </div>
</div>

<div class="note"><b>怎么用</b>：① 先用第一部分讲<b>句子骨架</b>（谁 + 做什么 + 什么），每句只讲一个语法点；
② 再用第二部分讲<b>预制语块</b>，整块听、整块说，不要逐词拼；
③ 最后让学生用发放页把意群「划」出来，再挑 3 个语块造句。全程不需要放音频——音频走主站逐句听即可。</div>

<h2><span class="num">1</span>句子骨架（意群切分 · 句法功能）</h2>
<table>
<thead><tr><th>#</th><th>意群切分（组后标签=句法功能）</th><th>中文</th><th>本句教学点</th></tr></thead>
<tbody>
%(rows)s
</tbody></table>
<div class="warn"><b>诚实边界</b>：意群切分没有国际量化标准（ToBI 是描述性标注体系，其断点标注信度实测也只在「±1 级以内」达 92%%）。本表是<b>按句法功能做的教学切分</b>，教师在课堂上可按学生水平合并相邻两群；不要把它当作唯一正确答案。</div>

<h2><span class="num">2</span>预制语块（整体记忆 · 高频复现）</h2>
%(chunks)s
<div class="warn"><b>诚实边界</b>：本项目语料仅 9,336 词（48 篇正课文=12 单元×4 篇，平均 195 词/篇），Biber 的「10 次/百万词」在本语料上折合 0.093 次、<b>不可达</b>。因此这些语块不是 Biber 式 lexical bundle，而是<b>「教材内相对高频 + 教学判断」</b>的 A1–A2 语块表；「每篇 3–6 条」是教学配额，无文献依据。</div>

<h2><span class="num">3</span>课堂流程建议（约 15 分钟）</h2>
<ol>
<li><b>骨架速读（4′）</b>：教师指意群、学生跟读；只讲每句「教学点」那一行，其余不展开。</li>
<li><b>语块整块记（6′）</b>：读语块 → 读整句 → 学生整块跟说（不逐词）。挑 2 条做「快问快答」。</li>
<li><b>学生动手（5′）</b>：发发放页，学生划意群（先主语、再连词/从句前）→ 同桌互查 → 教师点评 2 例。</li>
</ol>

<div class="foot">
数据来源：意群 <code>04_意群数据/意群_%(page)s.json</code>（人工定稿，六道门禁：源句一致/拼接还原/覆盖/段数/标注/教学点）·
语块 <code>02_词汇数据/语块_%(page)s.json</code>（归档正典）· 中文口径取自 <code>译文_%(page)s.json</code>。<br>
本文件为本地资源：不上线、不含音频、不依赖网络。生成器 <code>_gen_teacher_pack.py</code>。
</div>
</div></body></html>""" % dict(page=page, title=esc(title), unit=yq.get('unit', ''), type=esc(yq.get('type', '')),
                                 n=n, g=g, nc=len(ck['chunks']), rows='\n'.join(rows),
                                 chunks='\n'.join(chunks), css=CSS)


def student_html(page, yq, ck, zhm):
    # 课文（意群版，带编号，不显示功能标签）
    body = []
    for s in yq['sentences']:
        body.append(
            '<div style="margin:0 0 7px"><span class="n" style="color:#8E8E93;font-size:10px">%02d</span> '
            '%s</div>' % (s['i'] + 1, seg_html(s['groups'], show_fn=False)))

    # 划意群练习：挑 4 句短的
    pick = [s for s in yq['sentences'] if 4 <= len(s['text'].split()) <= 9][:4]
    if len(pick) < 4:
        pick = yq['sentences'][:4]
    drills = ''.join(
        '<div style="margin:0 0 12px"><div style="font-size:12.5px">%s</div>'
        '<div class="blank"></div></div>' % esc(s['text']) for s in pick)

    cards = []
    for c in ck['chunks']:
        cards.append(
            '<div class="ck cut"><div class="top"><span class="en">%s</span></div>'
            '<div class="zh">%s</div></div>' % (esc(c['text']), esc(c.get('zh', ''))))

    return """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>学生发放页 · %(page)s %(title)s</title><style>%(css)s</style></head><body>
<div class="page">
<div class="hd">
  <div class="brand">TH!NK · 学生练习页</div>
  <h1>%(title)s</h1>
  <div class="sub">Unit %(unit)s · %(page)s</div>
  <div class="meta" style="font-size:11.5px;color:#8E8E93;margin-top:10px">
    姓名 ____________　班级 ____________　日期 ____________
  </div>
</div>

<h2><span class="num">1</span>读一读：跟着斜线读</h2>
<div style="font-size:13.5px;line-height:2.2">%(body)s</div>
<div class="note">斜线「/」是意群：斜线前面可以稍微停一下，斜线里面要连起来读。</div>

<h2><span class="num">2</span>划一划：给句子划意群</h2>
<div style="font-size:11.5px;color:#8E8E93;margin-bottom:8px">提示：先找<b>主语</b>（谁），再在 <b>and / but / because / when</b> 前面划一道斜线。</div>
%(drills)s

<h2><span class="num">3</span>语块卡（剪下来，随身记）</h2>
<div style="font-size:11.5px;color:#8E8E93;margin-bottom:8px">整块记，不要一个词一个词拼。遮住中文，看英文说意思；遮住英文，看中文说英文。</div>
<div class="grid2">%(cards)s</div>

<h2><span class="num">4</span>说一说：用 3 个语块造句</h2>
<div style="margin-top:6px">
  <div class="line"></div><div class="line"></div><div class="line"></div>
</div>

<div class="foot">本页为课堂发放材料，不上线、无音频。文本与音频对齐以主站逐句听为准。</div>
</div></body></html>""" % dict(page=page, title=esc(yq.get('title', '')), unit=yq.get('unit', ''),
                                 body='\n'.join(body), drills=drills,
                                 cards='\n'.join(cards), css=CSS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page', required=True)
    ap.add_argument('--out-dir', default=None)
    args = ap.parse_args()

    page, yq, ck, sj, zhm, out_dir = load(args.page)
    if args.out_dir:
        out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)

    t_path = os.path.join(out_dir, '教师讲解卡_%s.html' % page)
    s_path = os.path.join(out_dir, '学生发放页_%s.html' % page)
    with io.open(t_path, 'w', encoding='utf-8') as fh:
        fh.write(teacher_html(page, yq, ck, zhm))
    with io.open(s_path, 'w', encoding='utf-8') as fh:
        fh.write(student_html(page, yq, ck, zhm))

    print('已生成：')
    print('  教师讲解卡：%s' % t_path)
    print('  学生发放页：%s' % s_path)
    print('  规模：%d 句 / %d 意群 / %d 语块'
          % (len(yq['sentences']), yq.get('n_groups', 0), len(ck['chunks'])))


if __name__ == '__main__':
    main()
