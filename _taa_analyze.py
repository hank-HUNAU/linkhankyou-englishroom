# -*- coding: utf-8 -*-
"""TAA 缓存 JSON 离线重分析（文本锚定对比，不消耗试用次数）

对 _taa_work/pXXX.json（TAA align 输出）vs 归档 句级数据_pXXX.json：
  a. 覆盖率（report.coverage）：脚本词被 ASR 命中 → 误听检测
  b. 文本锚定：每个 TAA unit 在句库中找同文句（norm 相等/包含），只对锚定上的句子比时间
  c. 起点差 |Δ|<=1.8s 正常（静音吸附差）；句1 报幕并入单列
  d. 未锚定 unit（合并/换行）与未覆盖句单列
输出：_taa_work/句级校验报告_精析.md
"""
import io, sys, os, json, re, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPO = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.abspath(os.path.join(REPO, '..'))
WORK = os.path.join(REPO, '_taa_work')

def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', t.lower()).split())

FOLDERS = {'U5_FreeTime': 5, 'U6_BestFriends': 6, 'U7_LivingForSport': 7, 'U8_FeelTheRhythm': 8}

rows = []
for folder, unit in FOLDERS.items():
    for jf in sorted(glob.glob(os.path.join(ARCH, folder, '01_正文篇章', '句级数据_p*.json'))):
        pg = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        taaj = os.path.join(WORK, pg + '.json')
        if not os.path.exists(taaj):
            rows.append({'pg': pg, 'unit': unit, 'err': 'TAA未跑（试用次数耗尽）'}); continue
        sents = json.load(open(jf, encoding='utf-8'))['sentences']
        taa = json.load(open(taaj, encoding='utf-8'))
        units, rep = taa['units'], taa['report']
        # 句库文本索引（norm → 句）
        lib = {}
        for s in sents:
            lib.setdefault(norm(s['text']), s)
        libc = [s for s in sents]  # 包含匹配用
        matched, unanchored, covered = [], [], set()
        for u in units:
            nu = norm(u['text'])
            hit = lib.get(nu)
            if not hit:
                cand = [s for s in libc if nu and (nu in norm(s['text']) or norm(s['text']) in nu)]
                hit = cand[0] if cand else None
            if hit:
                ds = u['start'] - hit['start_s']
                kind = '报幕' if (u['start'] < 1.0 and hit['start_s'] > 3) else ('ok' if abs(ds) <= 1.8 else 'FLAG')
                matched.append((u, hit, ds, kind))
                covered.add(hit['i'])
            else:
                unanchored.append(u)
        miss = [s for s in sents if s['i'] not in covered]
        flags = [m for m in matched if m[3] == 'FLAG']
        maxd = max((abs(m[2]) for m in matched if m[3] != '报幕'), default=0)
        rows.append({'pg': pg, 'unit': unit, 'n_u': len(units), 'n_s': len(sents),
                     'anchored': len(matched), 'cov': rep.get('coverage', 0),
                     'flags': len(flags), 'unanchored': len(unanchored), 'miss': len(miss), 'maxd': maxd,
                     'detail': (unanchored[:2], miss[:2], flags[:3])})
        print('%s U%-2d units%2d/句%2d 锚定%2d 覆盖率%.1f%% 偏差%.2fs 未锚定%d 未覆盖%d%s' % (
            pg, unit, len(units), len(sents), len(matched), rep.get('coverage', 0) * 100, maxd,
            len(unanchored), len(miss), ' ⚠%d' % len(flags) if flags else ''))

lines = ['# 句级校验精析报告（TAA 缓存离线重分析）\n',
         '口径：覆盖率=脚本词被 TAA 自有 ASR 命中比例；锚定=unit 与句库文本匹配成功后比时间；|Δ|<=1.8s 正常；句1 报幕并入单列。\n',
         '| 篇 | 单元 | TAA句 | 本站句 | 锚定 | 覆盖率 | 最大偏差 | 待人工 | 未锚定 | 未覆盖 |', '|---|---|---|---|---|---|---|---|---|---|']
for r in rows:
    if 'err' in r:
        lines.append('| %s | U%d | — | — | — | — | — | — | — | %s |' % (r['pg'], r['unit'], r['err'])); continue
    lines.append('| %s | U%d | %d | %d | %d | %.1f%% | %.2fs | %s | %d | %d |' % (
        r['pg'], r['unit'], r['n_u'], r['n_s'], r['anchored'], r['cov'] * 100, r['maxd'],
        r['flags'] if r['flags'] else '—', r['unanchored'], r['miss']))
open(os.path.join(WORK, '句级校验报告_精析.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n→ _taa_work/句级校验报告_精析.md')
