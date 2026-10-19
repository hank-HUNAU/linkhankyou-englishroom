# -*- coding: utf-8 -*-
"""听力 6 篇：现行句子被教师用书文字层整句包含的验证（fitz 侧）"""
import io, sys, os, json, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
ROOT = os.path.dirname(os.path.abspath(__file__))
PDFBASE = r'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/按单元与课次教师用书_文字层可提取'

def unit_of(pg):
    return 12 if pg in (110, 111, 113, 114, 117, 202) else 7 if pg <= 73 else 8 if pg <= 80 else 9 if pg <= 90 else 10 if pg <= 99 else 11

def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', t.lower()).split())

be = json.load(open(os.path.join(ROOT, '_book_extra.json'), encoding='utf-8'))

def arts_of(pg):
    if str(pg) in be['book']:
        return [s for p in be['book'][str(pg)]['arts'] for s in p]
    for f in glob.glob(os.path.join(ROOT, '篇章页', '复习_%03d_*.html' % pg)):
        h = open(f, encoding='utf-8').read()
        i = h.find('%d:{u:"Unit ' % pg)
        a = h.find('arts:[', i)
        d = 0; inS = None
        for k in range(a + 5, len(h)):
            c = h[k]
            if inS:
                if c == '\\': continue
                elif c == inS: inS = None
            else:
                if c in '"\'': inS = c
                elif c == '[': d += 1
                elif c == ']':
                    d -= 1
                    if d == 0: return [s for p in json.loads(h[a + 5:k + 1]) for s in p]
    return []

for pg in [69, 77, 87, 95, 105, 113]:
    sents = arts_of(pg)
    pdfn = set()
    for f in glob.glob(os.path.join(PDFBASE, 'Unit %d 第*课_教师用书.pdf' % unit_of(pg))):
        doc = fitz.open(f)
        for p in doc: pdfn.add(norm(p.get_text()))
    blob = ' || '.join(pdfn)
    ver = [s for s in sents if len(norm(s).split()) >= 3 and norm(s) in blob]
    print('p%03d: %d/%d 句整句见于教师用书文字层' % (pg, len(ver), len(sents)))
    for s in ver[:6]: print('   ✓', s[:70])
