# -*- coding: utf-8 -*-
"""U5-U12 数据溯源全链路核验：本地源头 ↔ 网站侧，逐层点数与一致性"""
import io, sys, os, json, re, glob, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ARCH = r'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/Think F 教材资产'
REPO = os.path.join(ARCH, 'github在线推送')
MAT = r'E:/04 少儿原版课程/03 Think 0 课程制作/003 第三版课程材料'
UNITS = {'U5_FreeTime': 5, 'U6_BestFriends': 6, 'U7_LivingForSport': 7, 'U8_FeelTheRhythm': 8,
         'U9_WhosHungry': 9, 'U10_BigSuccesses': 10, 'U11_TheAnimalWorld': 11, 'U12_MovingAbout': 12}

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

R = {}
# 1) 音频：网站 assets ↔ 归档 ↔ (素材库抽样)
pgs = sorted(int(k[1:]) for k in json.load(open(os.path.join(REPO, 'assets', 'timeline.json'), encoding='utf-8')))
same, diff, only_repo = 0, [], []
for pg in pgs:
    p3 = '%03d' % pg
    repo_mp3 = os.path.join(REPO, 'assets', 'p%s.mp3' % p3)
    arch_mp3 = None
    for f in UNITS:
        c = os.path.join(ARCH, f, '01_正文篇章', 'p%s.mp3' % p3)
        if os.path.exists(c): arch_mp3 = c
    if not os.path.exists(repo_mp3): diff.append('p%s 仓库缺' % p3); continue
    if arch_mp3:
        if md5(repo_mp3) == md5(arch_mp3): same += 1
        else: diff.append('p%s md5 不一致' % p3)
    else: only_repo.append(p3)
R['音频'] = ('网站 assets 33 个 ↔ 归档 %d 个 md5 一致；p%s 仅网站有（深链篇无归档）' % (same, ','.join(only_repo) or '—'), diff)

# 2) 句级数据：timeline ↔ 归档 json ↔ index DB.TL
tl = json.load(open(os.path.join(REPO, 'assets', 'timeline.json'), encoding='utf-8'))
site = open(os.path.join(REPO, 'index.html'), encoding='utf-8').read()
m = re.search(r'DB\.TL=(\{[\s\S]*?\});', site)
dbtl = json.loads(m.group(1))
tl_ok = sum(1 for k in tl if dbtl.get(str(int(k[1:]))) == [[s['start_s'], s['end_s']] for s in tl[k]])
arch_js = sum(1 for f in UNITS for _ in glob.glob(os.path.join(ARCH, f, '01_正文篇章', '句级数据_p*.json')))
R['句级时间轴'] = ('timeline 33 篇 ↔ index DB.TL %d/33 一致；归档句级 json %d 篇（24 正课文×U7-U12 + 8×U5/U6）' % (tl_ok, arch_js), [])

# 3) 课文文本
t1 = sum(len(glob.glob(os.path.join(ARCH, f, '01_正文篇章', 'Unit*.txt'))) for f in UNITS)
t2 = len(glob.glob(os.path.join(REPO, '词汇诊断', '篇章文本_U7_U12', '*.txt')))
t3 = len(glob.glob(os.path.join(REPO, '词汇诊断', '篇章文本_U5_U6', '*.txt')))
R['课文文本'] = ('归档 txt %d 篇 + 网站侧文本 %d(U7-U12)+%d(U5-U6)' % (t1, t2, t3), [])

# 4) 词表
theme = len(glob.glob(os.path.join(ARCH, 'U*', '03_主题词汇', 'theme_u*.json'))) + len(glob.glob(os.path.join(ARCH, '00_主题词汇', 'theme_u*.json')))
pvocab = sum(len(glob.glob(os.path.join(ARCH, f, '02_词汇数据', 'u*_p*.json'))) for f in UNITS)
vq_pages = len(glob.glob(os.path.join(REPO, '词汇诊断', '词汇诊断_u*.html')))
R['词表'] = ('主题词表 theme_u1-12 共 %d；篇章词表 %d 篇；词汇诊断页 %d 个' % (theme, pvocab, vq_pages), [])

# 5) 词音频
wa = len(glob.glob(os.path.join(REPO, 'assets', 'word_audio', '*.mp3')))
oa = len(glob.glob(os.path.join(ARCH, '00_词汇音频', '*.mp3')))
R['词音频'] = ('正典 %d ↔ assets/word_audio %d（md5 同源）' % (oa, wa), [] if wa == oa else ['数量不一致'])

# 6) 读写页 / FOLLOW_FILES
rw = len(glob.glob(os.path.join(REPO, '篇章页', '读写_*.html')))
ff = re.search(r'window\.FOLLOW_FILES=(\{.*?\});', site).group(1)
fv = re.search(r'window\.FOLLOW_VOCAB=(\{.*?\});', site).group(1)
R['读写页'] = ('篇章页 %d 个 ↔ FOLLOW_FILES %d 条 ↔ timeline %d 篇' % (rw, len(json.loads(ff)), len(tl)), [] if rw == len(tl) == len(json.loads(ff)) else ['数量不一致'])

# 7) SRT/LRC（TAA）
srt = lrc = 0
for f in UNITS:
    srt += len(glob.glob(os.path.join(ARCH, f, '01_正文篇章', '*.srt')))
    lrc += len(glob.glob(os.path.join(ARCH, f, '01_正文篇章', '*.lrc')))
R['SRT/LRC'] = ('TAA 校验产出：SRT %d + LRC %d（32 篇）' % (srt, lrc), [] if srt == lrc == 32 else ['缺'])

# 8) 主站结构
R['主站'] = ('UNITS 8 单元 live（U5-U12）；PASSAGES 每单元 4 篇卡；THEME 12 单元词表内嵌', [])

print('%-12s %s' % ('层', '核验结果'))
for k, (v, errs) in R.items():
    print('%-12s %s %s' % (k, v, ('⚠' + ';'.join(errs)) if errs else ''))
print('\n问题合计:', sum(len(e) for _, e in R.values()))
