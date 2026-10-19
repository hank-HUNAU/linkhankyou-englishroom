# -*- coding: utf-8 -*-
"""U5/U6 关键音频轨内容确认（快速 ASR，非词级）"""
import io, sys, os, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.environ.setdefault("HF_HUB_OFFLINE", "1")
from faster_whisper import WhisperModel
BASE = r'E:/04 少儿原版课程/03 Think 0 课程制作/003 第三版课程材料'

TRACKS = [
    ('U5 p48_t01 (阅读A newsletter?)', '第5单元/第5单元 音频/Thk2e_BE_L0_SB_Unit_5_p48_t01[公众号happyshare2023].mp3'),
    ('U5 p50_t02 (?)', '第5单元/第5单元 音频/Thk2e_BE_L0_SB_Unit_5_p50_t02[公众号happyshare2023].mp3'),
    ('U5 p53_t07 (?)', '第5单元/第5单元 音频/Thk2e_BE_L0_SB_Unit_5_p53_t07[公众号happyshare2023].mp3'),
    ('U5 p54_t09 (口语对话?)', '第5单元/第5单元 音频/Thk2e_BE_L0_SB_Unit_5_p54_t09[公众号happyshare2023].mp3'),
    ('U6 p58_t02 (阅读A?)', '第6单元/第6单元 音频/Thk2e_BE_L0_SB_Unit_6_p58_t02[公众号happyshare2023].mp3'),
    ('U6 p63_t10 (文化?)', '第6单元/第6单元 音频/Thk2e_BE_L0_SB_Unit_6_p63_t10[公众号happyshare2023].mp3'),
    ('U6 p64_t11 (文化?)', '第6单元/第6单元 音频/Thk2e_BE_L0_SB_Unit_6_p64_t11[公众号happyshare2023].mp3'),
]

model = WhisperModel('small', device='cpu', compute_type='int8')
for label, rel in TRACKS:
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        print('[缺失]', label); continue
    segs, info = model.transcribe(p, language='en', beam_size=1)
    text = ' '.join(s.text.strip() for s in segs)
    print('=' * 70)
    print(label, '| 时长 %.0fs' % info.duration)
    print(text[:420])
