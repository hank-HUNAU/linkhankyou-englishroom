# -*- coding: utf-8 -*-
"""比对 正文篇章 句级数据 json 与同目录 SRT/LRC 的时间戳/文本一致性。
JSON = 句级(源文本强制对齐)；SRT/LRC = TAA 段落级重对齐。两者可能不同。
用法：python _verify_srt_lrc_vs_json.py
"""
import os, re, json, glob

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def parse_srt(path):
    txt = open(path, encoding='utf-8').read()
    cues = []
    for b in re.split(r'\n\s*\n', txt.strip()):
        lines = b.split('\n')
        for i, l in enumerate(lines):
            if '-->' in l:
                m = re.findall(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', l)
                if len(m) >= 2:
                    h1, m1, s1, ms1 = map(int, m[0]); h2, m2, s2, ms2 = map(int, m[1])
                    start = h1*3600 + m1*60 + s1 + ms1/1000
                    end = h2*3600 + m2*60 + s2 + ms2/1000
                    text = '\n'.join(lines[i+1:]).strip()
                    cues.append((start, end, text))
                break
    return cues

def parse_lrc(path):
    out = []
    for l in open(path, encoding='utf-8').read().split('\n'):
        m = re.match(r'\[(\d{2}):(\d{2})\.(\d{2})\](.*)', l)
        if m:
            mm, ss, xx, text = m.groups()
            out.append((int(mm)*60 + int(ss) + int(xx)/100, text.strip()))
    return out

TOL = 0.5
units = sorted(glob.glob(os.path.join(BASE, 'U*')))
total = 0; issues = []; start_within_all = 0; end_within_all = 0; lrc_within_all = 0; cmp_pairs = 0
print('篇章  n  maxStartΔ maxEndΔ  LRCΔ  文本差异  startWithin endWithin lrcWithin')
for u in units:
    for jf in sorted(glob.glob(os.path.join(u, '01_正文篇章', '句级数据_p*.json'))):
        key = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        folder = os.path.dirname(jf)
        sf = os.path.join(folder, key + '.srt'); lf = os.path.join(folder, key + '.lrc')
        if not (os.path.exists(sf) and os.path.exists(lf)):
            issues.append((key, '缺 srt/lrc')); continue
        d = json.load(open(jf, encoding='utf-8')); sents = d['sentences']
        cues = parse_srt(sf); lrc = parse_lrc(lf); n = len(sents); total += 1
        common = min(n, len(cues), len(lrc))
        sd = [abs(sents[i]['start_s'] - cues[i][0]) for i in range(common)]
        ed = [abs(sents[i]['end_s'] - cues[i][1]) for i in range(common)]
        ld = [abs(sents[i]['start_s'] - lrc[i][0]) for i in range(common)]
        tmis = sum(1 for i in range(common) if sents[i].get('text', '').strip() != cues[i][2].strip())
        maxsd = max(sd) if sd else 0; maxed = max(ed) if ed else 0; maxld = max(ld) if ld else 0
        sw = sum(1 for x in sd if x <= TOL); ew = sum(1 for x in ed if x <= TOL); lw = sum(1 for x in ld if x <= TOL)
        start_within_all += sw; end_within_all += ew; lrc_within_all += lw; cmp_pairs += common
        flag = '⚠️' if (maxsd > TOL or maxed > TOL or maxld > TOL or tmis) else '✅'
        print('%s %s %3d  %6.2f  %6.2f  %6.2f  %3d    %d/%d     %d/%d    %d/%d' %
              (flag, key, n, maxsd, maxed, maxld, tmis, sw, common, ew, common, lw, common))
        if maxsd > TOL or maxed > TOL or maxld > TOL or tmis:
            issues.append((key, 'startΔmax=%.2f endΔmax=%.2f lrcΔmax=%.2f textMis=%d' % (maxsd, maxed, maxld, tmis)))

print('\n=== 总计 ===')
print('篇章数:', total, '| 比对句对:', cmp_pairs)
print('start 在 %.2fs 内: %d/%d (%.1f%%)' % (TOL, start_within_all, cmp_pairs, 100*start_within_all/cmp_pairs))
print('end   在 %.2fs 内: %d/%d (%.1f%%)' % (TOL, end_within_all, cmp_pairs, 100*end_within_all/cmp_pairs))
print('lrc   在 %.2fs 内: %d/%d (%.1f%%)' % (TOL, lrc_within_all, cmp_pairs, 100*lrc_within_all/cmp_pairs))
print('问题篇章:', len(issues))
for k, v in issues[:20]:
    print('  ', k, v)
