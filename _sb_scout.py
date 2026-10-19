# -*- coding: utf-8 -*-
"""L5/L6 课本结构侦察：定位 LISTENING/READING/SPEAKING/CULTURE 页码"""
import io, sys, os, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import fitz
BASE = r'E:/04 少儿原版课程/03 Think 0 课程制作/003 第三版课程材料'
for pdf, unit in [(os.path.join(BASE, '第5单元', 'L5_Free Time_课本.pdf'), 'U5'),
                  (os.path.join(BASE, '第6单元', 'L6_Best Friends_课本.pdf'), 'U6')]:
    doc = fitz.open(pdf)
    print('=' * 80)
    print(unit, pdf, '| 页数:', len(doc))
    for pi in range(len(doc)):
        t = doc[pi].get_text()
        # 找标题行
        heads = re.findall(r'^(LISTENING|READING|SPEAKING|CULTURE|VOCABULARY|GRAMMAR|FUNCTIONS)\s*$', t, re.M)
        # 书页码（页面上通常有大数字）
        pn = re.findall(r'^\s*(\d{2})\s*$', t, re.M)
        title = ''
        m = re.search(r'\n([A-Z][A-Za-z0-9 !?,\'&\-]{6,60})\n', t)
        if heads or pn:
            print('  PDF页%d: 页码=%s 栏目=%s' % (pi + 1, pn[:2], heads))
