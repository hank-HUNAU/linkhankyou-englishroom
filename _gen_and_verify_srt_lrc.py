# -*- coding: utf-8 -*-
"""步骤1：把 句级数据_pXXX.json 转成 SRT/LRC（覆盖 TAA 产物，旧版改名 .taa 保留）。
步骤2：核查 (a) 新 SRT/LRC 与 JSON 的一致性；(b) 旧 TAA SRT/LRC 与 JSON 的差异（即当初的分叉）。
用法：python _gen_and_verify_srt_lrc.py
"""
import os, re, json, glob
from datetime import timedelta

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
TOL = 0.5

def srt_ts(t):
    ms = int(round(t * 1000))
    td = timedelta(milliseconds=ms)
    h = td.seconds // 3600; m = (td.seconds % 3600) // 60; s = td.seconds % 60
    return "%02d:%02d:%02d,%03d" % (h, m, s, td.microseconds // 1000)

def lrc_ts(t):
    ms = int(round(t * 1000))
    m = ms // 60000; s = (ms % 60000) // 1000; xx = (ms % 1000) // 10
    return "[%02d:%02d.%02d]" % (m, s, xx)

def parse_srt(path):
    txt = open(path, encoding='utf-8').read()
    cues = []
    for b in re.split(r'\n\s*\n', txt.strip()):
        lines = b.split('\n')
        for i, l in enumerate(lines):
            if '-->' in l:
                m = re.findall(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', l)
                if len(m) >= 2:
                    a, b2 = m[0], m[1]
                    start = int(a[0])*3600 + int(a[1])*60 + int(a[2]) + int(a[3])/1000
                    end = int(b2[0])*3600 + int(b2[1])*60 + int(b2[2]) + int(b2[3])/1000
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

def norm(t):
    return ' '.join(t.split())

# ---------- 步骤1：生成 ----------
print("=== 步骤1：JSON → SRT/LRC（旧 TAA 改名 .taa 保留）===")
gen_n = 0
for u in sorted(glob.glob(os.path.join(BASE, 'U*'))):
    for jf in sorted(glob.glob(os.path.join(u, '01_正文篇章', '句级数据_p*.json'))):
        key = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        folder = os.path.dirname(jf)
        srt_path = os.path.join(folder, key + '.srt')
        lrc_path = os.path.join(folder, key + '.lrc')
        taa_srt = os.path.join(folder, key + '.taa.srt')
        taa_lrc = os.path.join(folder, key + '.taa.lrc')
        # 备份旧 TAA 产物（不覆盖已有 .taa，避免误删历史）
        if os.path.exists(srt_path) and not os.path.exists(taa_srt):
            os.rename(srt_path, taa_srt)
        if os.path.exists(lrc_path) and not os.path.exists(taa_lrc):
            os.rename(lrc_path, taa_lrc)
        d = json.load(open(jf, encoding='utf-8'))
        sents = d['sentences']
        srt_blocks = []
        for i, s in enumerate(sents):
            text = norm(s.get('text', ''))
            srt_blocks.append("%d\n%s --> %s\n%s\n" % (i + 1, srt_ts(s['start_s']), srt_ts(s['end_s']), text))
        open(srt_path, 'w', encoding='utf-8').write('\n'.join(srt_blocks) + '\n')
        lrc_lines = ["%s%s" % (lrc_ts(s['start_s']), norm(s.get('text', ''))) for s in sents]
        open(lrc_path, 'w', encoding='utf-8').write('\n'.join(lrc_lines) + '\n')
        gen_n += 1
print("已生成 %d 篇 SRT/LRC；旧 TAA 文件保留为 .taa.srt / .taa.lrc。" % gen_n)

# ---------- 步骤2a：新 SRT/LRC 与 JSON 一致性 ----------
print("\n=== 步骤2a：新 SRT/LRC 与 句级数据 JSON 一致性（应≈0）===")
print("篇章  n  maxStartΔ maxEndΔ  LRCΔ  文本差异")
fid_start_max = fid_end_max = fid_lrc_max = 0.0
fid_text_mis_total = 0
for u in sorted(glob.glob(os.path.join(BASE, 'U*'))):
    for jf in sorted(glob.glob(os.path.join(u, '01_正文篇章', '句级数据_p*.json'))):
        key = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        folder = os.path.dirname(jf)
        sf = os.path.join(folder, key + '.srt'); lf = os.path.join(folder, key + '.lrc')
        d = json.load(open(jf, encoding='utf-8')); sents = d['sentences']
        cues = parse_srt(sf); lrc = parse_lrc(lf); n = len(sents)
        common = min(n, len(cues), len(lrc))
        sd = [abs(sents[i]['start_s'] - cues[i][0]) for i in range(common)]
        ed = [abs(sents[i]['end_s'] - cues[i][1]) for i in range(common)]
        ld = [abs(sents[i]['start_s'] - lrc[i][0]) for i in range(common)]
        tmis = sum(1 for i in range(common) if norm(sents[i].get('text', '')) != cues[i][2])
        maxsd = max(sd) if sd else 0; maxed = max(ed) if ed else 0; maxld = max(ld) if ld else 0
        fid_start_max = max(fid_start_max, maxsd); fid_end_max = max(fid_end_max, maxed)
        fid_lrc_max = max(fid_lrc_max, maxld); fid_text_mis_total += tmis
        flag = '⚠️' if (maxsd > TOL or maxed > TOL or maxld > TOL or tmis) else '✅'
        print("%s %s %3d  %6.4f  %6.4f  %6.4f  %3d" % (flag, key, n, maxsd, maxed, maxld, tmis))
print("新 SRT/LRC 与 JSON 最大偏差：start=%.4fs end=%.4fs lrc=%.4fs；文本差异累计=%d"
      % (fid_start_max, fid_end_max, fid_lrc_max, fid_text_mis_total))

# ---------- 步骤2b：旧 TAA SRT/LRC 与 JSON 差异（当初分叉）----------
print("\n=== 步骤2b：旧 TAA SRT/LRC 与 句级数据 JSON 差异（核查当初分叉）===")
print("篇章  n  maxStartΔ maxEndΔ  LRCΔ  文本差异  startWithin endWithin lrcWithin")
taa_total = 0; issues = []
sw_all = ew_all = lw_all = cmp_all = 0
for u in sorted(glob.glob(os.path.join(BASE, 'U*'))):
    for jf in sorted(glob.glob(os.path.join(u, '01_正文篇章', '句级数据_p*.json'))):
        key = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        folder = os.path.dirname(jf)
        taa_srt = os.path.join(folder, key + '.taa.srt')
        taa_lrc = os.path.join(folder, key + '.taa.lrc')
        if not (os.path.exists(taa_srt) and os.path.exists(taa_lrc)):
            issues.append((key, '无 TAA 备份')); continue
        d = json.load(open(jf, encoding='utf-8')); sents = d['sentences']
        cues = parse_srt(taa_srt); lrc = parse_lrc(taa_lrc); n = len(sents)
        common = min(n, len(cues), len(lrc)); taa_total += 1
        sd = [abs(sents[i]['start_s'] - cues[i][0]) for i in range(common)]
        ed = [abs(sents[i]['end_s'] - cues[i][1]) for i in range(common)]
        ld = [abs(sents[i]['start_s'] - lrc[i][0]) for i in range(common)]
        tmis = sum(1 for i in range(common) if norm(sents[i].get('text', '')) != cues[i][2])
        maxsd = max(sd) if sd else 0; maxed = max(ed) if ed else 0; maxld = max(ld) if ld else 0
        sw = sum(1 for x in sd if x <= TOL); ew = sum(1 for x in ed if x <= TOL); lw = sum(1 for x in ld if x <= TOL)
        sw_all += sw; ew_all += ew; lw_all += lw; cmp_all += common
        flag = '⚠️' if (maxsd > TOL or maxed > TOL or maxld > TOL or tmis) else '✅'
        print("%s %s %3d  %6.2f  %6.2f  %6.2f  %3d    %d/%d     %d/%d    %d/%d"
              % (flag, key, n, maxsd, maxed, maxld, tmis, sw, common, ew, common, lw, common))
        if maxsd > TOL or maxed > TOL or maxld > TOL or tmis:
            issues.append((key, 'startΔmax=%.2f endΔmax=%.2f lrcΔmax=%.2f textMis=%d' % (maxsd, maxed, maxld, tmis)))
print('\n=== 步骤2b 总计 ===')
print('篇章数:', taa_total, '| 比对句对:', cmp_all)
print('start 在 %.2fs 内: %d/%d (%.1f%%)' % (TOL, sw_all, cmp_all, 100*sw_all/cmp_all))
print('end   在 %.2fs 内: %d/%d (%.1f%%)' % (TOL, ew_all, cmp_all, 100*ew_all/cmp_all))
print('lrc   在 %.2fs 内: %d/%d (%.1f%%)' % (TOL, lw_all, cmp_all, 100*lw_all/cmp_all))
print('问题篇章:', len(issues))
for k, v in issues[:20]:
    print('  ', k, v)
