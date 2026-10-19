# -*- coding: utf-8 -*-
"""篇章源文本 × 教师用书 PDF 文字层 覆盖率体检（bag-of-words 包含率）

用途：核查句-音频对齐所用源文本与课本/教师用书印刷文本的一致程度。
  覆盖率 ≥97%  = 与印刷文本同源（阅读类应达到）
  90-97%      = 轻差（听力类 ASR 转写常态，可按教师用书听力原文校对）
  <90%        = 明显不符（优先人工核对）
用法：python _pdf_check.py   （解释器需含 fitz，如 sys310）
数据源：篇章页/复习_*.html 内嵌 arts（U7/U12）+ _book_extra.json（U8-U11）
"""
import json, re, io, sys, os, glob
import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))
PDFBASE = r'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/按单元与课次教师用书_文字层可提取'

def norm(t):
    t = t.lower()
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return t.split()

# 1) U7/U12 arts 来自篇章页内嵌 BOOK 映射；U8-U11 来自 _book_extra.json
srcs = {}
for f in glob.glob(os.path.join(ROOT, '篇章页', '复习_*.html')):
    h = open(f, encoding='utf-8').read()
    for m in re.finditer(r'(\d+):\{u:"(Unit \d+)"[^{}]*?arts:(\[)', h):
        pg = int(m.group(1))
        if pg in srcs: continue
        k = m.start(3); d = 0; inS = None; end = None
        i = k
        while i < len(h):
            c = h[i]
            if inS:
                if c == '\\': i += 1
                elif c == inS: inS = None
            else:
                if c in '"\'': inS = c
                elif c == '[': d += 1
                elif c == ']':
                    d -= 1
                    if d == 0: end = i + 1; break
            i += 1
        if end:
            try:
                arts = json.loads(h[k:end])
                sents = [s for para in arts for s in para]
                srcs[pg] = {'sents': sents, 'text': ' '.join(sents)}
            except Exception:
                pass

be = json.load(open(os.path.join(ROOT, '_book_extra.json'), encoding='utf-8'))
for k, v in be['book'].items():
    pg = int(k)
    sents = [s for para in v['arts'] for s in para]
    srcs[pg] = {'sents': sents, 'text': ' '.join(sents)}

def unit_of(pg):
    return 12 if pg in (110, 111, 113, 114, 117, 202) else 7 if pg <= 73 else 8 if pg <= 80 else 9 if pg <= 90 else 10 if pg <= 99 else 11

# 2) 教师用书 PDF 全文
pdf_text = {}
for u in (7, 8, 9, 10, 11, 12):
    txt = []
    for f in glob.glob(os.path.join(PDFBASE, 'Unit %d 第*课_教师用书.pdf' % u)):
        doc = fitz.open(f)
        for p in doc: txt.append(p.get_text())
    pdf_text[u] = norm(' '.join(txt))

# 3) 逐篇覆盖率
print('%-6s %8s %12s' % ('pg', '句数', 'PDF词覆盖率'))
low = []
for pg in sorted(srcs):
    sw = norm(srcs[pg]['text'])
    if not sw: continue
    pset = set(pdf_text[unit_of(pg)])
    hit = sum(1 for w in sw if w in pset)
    ratio = hit / len(sw)
    flag = 'OK' if ratio >= 0.97 else ('轻差' if ratio >= 0.90 else '明显不符')
    if ratio < 0.97: low.append(pg)
    print('p%03d  %4d句  %8.1f%%  %s' % (pg, len(srcs[pg]['sents']), ratio * 100, flag))
print()
print('覆盖率<97%（需人工核对/听力校对待办）:', low if low else '无')
