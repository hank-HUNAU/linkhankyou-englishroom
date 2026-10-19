# -*- coding: utf-8 -*-
"""TAA 校验终判：覆盖率（误听）+ 起点差（句界）双指标，输出汇总"""
import io, sys, os, json, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPO = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.abspath(os.path.join(REPO, '..'))
WORK = os.path.join(REPO, '_taa_work')
FOLDERS = {'U5_FreeTime': 5, 'U6_BestFriends': 6, 'U7_LivingForSport': 7, 'U8_FeelTheRhythm': 8,
           'U9_WhosHungry': 9, 'U10_BigSuccesses': 10, 'U11_TheAnimalWorld': 11, 'U12_MovingAbout': 12}

def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', t.lower()).split())

verdicts = []
for folder, unit in FOLDERS.items():
    for jf in sorted(glob.glob(os.path.join(ARCH, folder, '01_正文篇章', '句级数据_p*.json'))):
        pg = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        taaj = os.path.join(WORK, pg + '.json')
        if not os.path.exists(taaj): verdicts.append((pg, unit, '未跑')); continue
        sents = json.load(open(jf, encoding='utf-8'))['sentences']
        taa = json.load(open(taaj, encoding='utf-8'))
        units, rep = taa['units'], taa['report']
        cov = rep.get('coverage', 0) * 100
        # 起点差：每句找锚定 unit 的最小 start（排除句1 报幕）
        anchor = {}
        for u in units:
            nu = norm(u['text'])
            hit = next((s for s in sents if norm(s['text']) == nu), None) or \
                  next((s for s in sents if nu and (nu in norm(s['text']) or norm(s['text']) in nu)), None)
            if hit: anchor.setdefault(hit['i'], []).append(u)
        maxstart, worst_i = 0.0, None
        for s in sents:
            us = anchor.get(s['i'], [])
            if not us: continue
            ds = min(u['start'] for u in us) - s['start_s']
            if s['i'] == 0 and ds < -3: continue
            if abs(ds) > maxstart: maxstart, worst_i = abs(ds), s['i'] + 1
        if cov >= 95 and maxstart <= 2.5: v = '✅ 通过'
        elif cov >= 90 and maxstart <= 2.5: v = '✅ 通过（听力 ASR 上限，覆盖率%.1f%%）' % cov
        else: v = '⚠️ 待人工（句%d 起点差%.1fs）' % (worst_i, maxstart) if maxstart > 2.5 else '⚠️ 待人工（覆盖率%.1f%%）' % cov
        verdicts.append((pg, unit, v, round(cov, 1), round(maxstart, 2)))

lines = ['\n## 终判汇总（双指标：覆盖率=误听检测 / 起点差=句界检测）\n',
         '| 篇 | 单元 | 覆盖率 | 最大起点差 | 判定 |', '|---|---|---|---|---|']
npass = 0
for r in verdicts:
    if len(r) == 3: lines.append('| %s | U%d | — | — | %s |' % (r[0], r[1], r[2])); continue
    if r[2].startswith('✅'): npass += 1
    lines.append('| %s | U%d | %s%% | %ss | %s |' % (r[0], r[1], r[3], r[4], r[2]))
lines.append('\n**通过 %d / 32 篇**' % npass)
rep_path = os.path.join(WORK, '句级校验报告_v3.md')
open(rep_path, 'a', encoding='utf-8').write('\n'.join(lines) + '\n')
for r in verdicts: print(r)
print('\n通过 %d/32' % npass)
