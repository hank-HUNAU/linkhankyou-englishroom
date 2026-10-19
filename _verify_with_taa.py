# -*- coding: utf-8 -*-
"""TextAudioAligner 全量句级校验 + SRT/LRC 产出（32 篇）

流程（用户定案）：
  1. 从归档 句级数据_pXXX.json 提取逐句 txt
  2. TextAudioAligner align（自有 ASR + 强制对齐）→ JSON（units/report/words）
  3. 由 units 生成 逐句 SRT + LRC → 归档 Ux/01_正文篇章/pXXX.srt / pXXX.lrc
  4. 双对比：
     a. report.coverage（脚本词 vs ASR 词匹配率）→ 误听/文本错误检测
     b. SRT 起止时间 vs 句级数据 → 时间轴校验（句1 允许报幕并入；|Δ|<=1.8s 判正常=静音吸附差）
  5. 汇总 _taa_work/句级校验报告_全32篇.md

用法：python _verify_with_taa.py            （sys310，需 PATH 可达 taa）
"""
import io, sys, os, json, re, glob, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

REPO = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.abspath(os.path.join(REPO, '..'))
TAA = r'D:\TextAudioAligner-portable-v1.0.1\TextAudioAligner\TextAudioAligner.exe'
WORK = os.path.join(REPO, '_taa_work')
os.makedirs(WORK, exist_ok=True)
ENV = dict(os.environ, HF_HUB_OFFLINE='1')

FOLDERS = {'U5_FreeTime': 5, 'U6_BestFriends': 6, 'U7_LivingForSport': 7, 'U8_FeelTheRhythm': 8,
           'U9_WhosHungry': 9, 'U10_BigSuccesses': 10, 'U11_TheAnimalWorld': 11, 'U12_MovingAbout': 12}

def norm(t):
    return ' '.join(re.sub(r'[^a-z0-9\s]', ' ', t.lower()).split())

def srt_ts(sec):
    ms = int(round(sec * 1000))
    return '%02d:%02d:%02d,%03d' % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)

def lrc_ts(sec):
    return '[%02d:%02d.%02d]' % (int(sec // 60), int(sec % 60), int(sec * 100 % 100))

rows = []
t0 = time.time()
for folder, unit in FOLDERS.items():
    d1 = os.path.join(ARCH, folder, '01_正文篇章')
    for jf in sorted(glob.glob(os.path.join(d1, '句级数据_p*.json'))):
        pg = re.search(r'句级数据_(p\d+)\.json', jf).group(1)
        if os.path.exists(os.path.join(WORK, pg + '.json')):
            print(pg + ' · 已有缓存，跳过'); continue
        j = json.load(open(jf, encoding='utf-8'))
        sents = j['sentences']
        # 1) 逐句 txt
        txt = os.path.join(WORK, pg + '_sents.txt')
        open(txt, 'w', encoding='utf-8').write('\n'.join(s['text'] for s in sents) + '\n')
        # 2) TAA align → JSON
        outj = os.path.join(WORK, pg + '.json')
        mp3 = os.path.join(REPO, 'assets', pg + '.mp3')
        r = subprocess.run([TAA, 'align', mp3, '-t', txt, '-o', outj, '-f', 'json',
                            '--no-line-breaks', '-q'], env=ENV, capture_output=True, text=True, encoding='utf-8')
        if r.returncode != 0 or not os.path.exists(outj):
            rows.append({'pg': pg, 'unit': unit, 'err': (r.stderr or r.stdout or 'fail')[-120:]})
            print('%s ✗ TAA 失败' % pg); continue
        taa = json.load(open(outj, encoding='utf-8'))
        units, rep = taa['units'], taa['report']
        # 3) SRT + LRC 落归档
        with open(os.path.join(d1, pg + '.srt'), 'w', encoding='utf-8') as f:
            for k, u in enumerate(units, 1):
                f.write('%d\n%s --> %s\n%s\n\n' % (k, srt_ts(u['start']), srt_ts(u['end']), u['text']))
        with open(os.path.join(d1, pg + '.lrc'), 'w', encoding='utf-8') as f:
            for u in units:
                f.write('%s%s\n' % (lrc_ts(u['start']), u['text']))
        # 4) 双对比
        n = min(len(units), len(sents))
        text_ok = sum(1 for i in range(n) if norm(units[i]['text']) == norm(sents[i]['text']))
        cov = rep.get('coverage', 0)
        deltas = []
        for i in range(n):
            ds = units[i]['start'] - sents[i]['start_s']
            if i == 0 and units[i]['start'] < 1.0 and sents[i]['start_s'] > 3:
                deltas.append(('报幕', ds)); continue   # 句1 报幕并入（TAA 不剥离报幕）
            deltas.append(('ok' if abs(ds) <= 1.8 else 'FLAG', ds))
        flagged = [d for d in deltas if d[0] == 'FLAG']
        rows.append({'pg': pg, 'unit': unit, 'n': n, 'text_ok': text_ok, 'cov': cov,
                     'maxd': max((abs(d[1]) for d in deltas if d[0] != '报幕'), default=0),
                     'flags': len(flagged), 'dur': j.get('duration_s')})
        print('%s ✓ %d句 文本%d/%d 覆盖率%.1f%% 最大偏差%.2fs%s' % (
            pg, n, text_ok, n, cov * 100,
            rows[-1]['maxd'], ' ⚠%d处' % len(flagged) if flagged else ''))

# 5) 汇总报告
lines = ['# 句级数据 TAA 校验报告（%s）\n' % time.strftime('%Y-%m-%d %H:%M'),
         '工具：TextAudioAligner-portable-v1.0.1（faster-whisper small，独立 ASR + 强制对齐）',
         '判定：覆盖率=脚本词被 ASR 命中比例（误听检测）；|起点差|<=1.8s 判正常（本站静音吸附前拉 vs TAA 词首对齐）；句1 差=报幕并入。\n',
         '| 篇 | 单元 | 句数 | 文本一致 | ASR覆盖率 | 最大起点差 | 待人工 |', '|---|---|---|---|---|---|---|']
tot_flag = 0
for r in rows:
    if 'err' in r:
        lines.append('| %s | U%d | — | ✗ TAA失败 | — | — | %s |' % (r['pg'], r['unit'], r['err'].replace('|', '/')[:40])); continue
    tot_flag += r['flags']
    lines.append('| %s | U%d | %d | %d/%d | %.1f%% | %.2fs | %s |' % (
        r['pg'], r['unit'], r['n'], r['text_ok'], r['n'], r['cov'] * 100, r['maxd'],
        r['flags'] if r['flags'] else '—'))
lines.append('\n合计 %d 篇，待人工 %d 处。SRT/LRC 已按篇落归档 01_正文篇章/。' % (len([r for r in rows if 'err' not in r]), tot_flag))
open(os.path.join(WORK, '句级校验报告_全32篇.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n完成，用时 %.1f 分钟 → _taa_work/句级校验报告_全32篇.md' % ((time.time() - t0) / 60))
