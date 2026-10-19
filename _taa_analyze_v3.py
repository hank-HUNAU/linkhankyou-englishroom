# -*- coding: utf-8 -*-
"""v3 跨度分析：每本站句聚合其 TAA 子 unit，比较 [span] vs [句区间]（免 Trial）"""
import io, sys, os, json, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPO = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.abspath(os.path.join(REPO, '..'))
WORK = os.path.join(REPO, '_taa_work')

def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', t.lower()).split())

FOLDERS = {'U5_FreeTime': 5, 'U6_BestFriends': 6, 'U7_LivingForSport': 7, 'U8_FeelTheRhythm': 8}
TOL = 1.8

rows = []
for folder, unit in FOLDERS.items():
    for jf in sorted(glob.glob(os.path.join(ARCH, folder, '01_正文篇章', '句级数据_p*.json'))):
        pg = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        taaj = os.path.join(WORK, pg + '.json')
        if not os.path.exists(taaj): continue
        sents = json.load(open(jf, encoding='utf-8'))['sentences']
        taa = json.load(open(taaj, encoding='utf-8'))
        units, rep = taa['units'], taa['report']
        # 每个 unit 锚定到句库句（norm 相等优先，包含次之）
        anchor = {}
        for k, u in enumerate(units):
            nu = norm(u['text'])
            hit = next((s for s in sents if norm(s['text']) == nu), None)
            if not hit:
                hit = next((s for s in sents if nu and (nu in norm(s['text']) or norm(s['text']) in nu)), None)
            if hit: anchor.setdefault(hit['i'], []).append(k)
        flags, checked, nover = [], 0, []
        for s in sents:
            ks = anchor.get(s['i'], [])
            if not ks: nover.append(s['i']); continue
            checked += 1
            span_s = min(units[k]['start'] for k in ks)
            span_e = max(units[k]['end'] for k in ks)
            ds, de = span_s - s['start_s'], span_e - s['end_s']
            first = (s['i'] == 0 and span_s < 1.0 and s['start_s'] > 3)
            if not first and (abs(ds) > TOL or abs(de) > TOL):
                flags.append((s['i'] + 1, round(ds, 2), round(de, 2)))
        maxd = 0
        for s in sents:
            ks = anchor.get(s['i'], [])
            if ks:
                ds = min(units[k]['start'] for k in ks) - s['start_s']
                if not (s['i'] == 0 and ds < -3): maxd = max(maxd, abs(ds))
        rows.append({'pg': pg, 'unit': unit, 'n_s': len(sents), 'n_u': len(units),
                     'cov': rep.get('coverage', 0), 'checked': checked,
                     'flags': len(flags), 'nover': len(nover), 'maxd': maxd, 'detail': flags[:4]})
        print('%s U%-2d 句%2d/unit%2d 覆盖%.1f%% 跨度校验%2d 待人工%s 未覆盖%s 最大偏差%.2fs' % (
            pg, unit, len(sents), len(units), rep.get('coverage', 0) * 100, checked,
            flags or '—', nover or '—', maxd))

lines = ['# 句级校验 v3（跨度口径，TAA 缓存离线）\n',
         '口径：TAA 子 unit 按文本锚定聚合回本站句；span.start/end vs 句 start/end；容差 1.8s（静音吸附 vs 词首对齐）；句1 报幕单列。\n',
         '| 篇 | 单元 | 句数 | TAA unit | 覆盖率 | 跨度校验 | 待人工 | 未覆盖 | 最大偏差 |', '|---|---|---|---|---|---|---|---|---|']
for r in rows:
    lines.append('| %s | U%d | %d | %d | %.1f%% | %d | %s | %s | %.2fs |' % (
        r['pg'], r['unit'], r['n_s'], r['n_u'], r['cov'] * 100, r['checked'],
        r['flags'] if r['flags'] else '—', r['nover'] if r['nover'] else '—', r['maxd']))
open(os.path.join(WORK, '句级校验报告_v3.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
ok = sum(1 for r in rows if r['flags'] == 0 and r['nover'] == 0)
print('\n通过 %d/16（零待人工+零未覆盖）；详情 → _taa_work/句级校验报告_v3.md' % ok)
