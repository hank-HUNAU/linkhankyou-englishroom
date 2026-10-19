# -*- coding: utf-8 -*-
"""用现行首句内容词定位教师用书中的听力原文块"""
import fitz, io, sys, os, glob, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))
PDFBASE = r'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/按单元与课次教师用书_文字层可提取'

def unit_of(pg):
    return 12 if pg in (110, 111, 113, 114, 117, 202) else 7 if pg <= 73 else 8 if pg <= 80 else 9 if pg <= 90 else 10 if pg <= 99 else 11

LISTEN = [69, 77, 87, 95, 105, 113]
be = json.load(open(os.path.join(ROOT, '_book_extra.json'), encoding='utf-8'))

def arts_of(pg):
    if str(pg) in be['book']:
        return [s for p in be['book'][str(pg)]['arts'] for s in p]
    for f in glob.glob(os.path.join(ROOT, '篇章页', '复习_%03d_*.html' % pg)):
        h = open(f, encoding='utf-8').read()
        marker = '%d:{u:"Unit ' % pg
        i = h.find(marker)
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

for pg in LISTEN:
    sents = arts_of(pg)
    first = sents[0]
    words = [w for w in re.sub(r'[^a-zA-Z\s]', ' ', first).split() if len(w) > 3][:4]
    print('=' * 90)
    print('p%03d 首句: %s' % (pg, first[:90]))
    print('锚词: %s' % words)
    u = unit_of(pg)
    for f in sorted(glob.glob(os.path.join(PDFBASE, 'Unit %d 第*课_教师用书.pdf' % u))):
        doc = fitz.open(f)
        for pi in range(len(doc)):
            t = doc[pi].get_text()
            tl = t.lower()
            hit = sum(1 for w in words if w.lower() in tl)
            if hit >= 3:
                i = tl.find(words[0].lower())
                while i >= 0 and not all(w.lower() in tl[max(0, i - 400):i + 400].lower() for w in words[:2]):
                    i = tl.find(words[0].lower(), i + 1)
                j = i if i >= 0 else tl.find(words[0].lower())
                print('--- %s p%d (命中%d/4) ---' % (os.path.basename(f), pi + 1, hit))
                print(t[max(0, j - 200):j + 2500])
                break
        else:
            continue
        break
