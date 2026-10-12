# -*- coding: utf-8 -*-
"""把 assets/sents_v2/ 的句切片反算回原音频的绝对边界，并落盘保全。

背景
────
sents_v2 是人工核查结果的**唯一载体**：它里头的 wav 只带时长、不携带在原音频里的
绝对位置，而核查报告只记录了其中 3 处。一旦 sents/ 与 sents_v2/ 被清理，其余几处
人工修正就再也找不回来了。所以必须在清理之前，用互相关把每个切片匹配回整篇音频，
反算出 start/end 落盘。

实测结论（2026-10-12）
────────────────────
sents/ 与 sents_v2/ 各 42 个 wav，只覆盖 p067(19) + p070(23)。
逐文件比对：仅 8 个不同（p067__02/03/17/18、p070__19~22），其余 34 个 v2 与 v1 完全相同
→ v2 不是「全篇人工核查版」，而是「v1 + 8 处人工修正」。

用法
────
    .venv-align/Scripts/python.exe _sents_bounds.py              # 全量反算 + 比对
    .venv-align/Scripts/python.exe _sents_bounds.py --only p067  # 只跑一篇

产出：_sents_v2_bounds.json
"""
import argparse
import json
import os
import sys

import numpy as np
import soundfile as sf
import torch
import torchaudio

ROOT = os.path.dirname(os.path.abspath(__file__))
SENTS_V2 = os.path.join(ROOT, 'assets', 'sents_v2')
SENTS_V1 = os.path.join(ROOT, 'assets', 'sents')
TIMELINE = os.path.join(ROOT, 'assets', 'timeline.json')
OUT = os.path.join(ROOT, '_sents_v2_bounds.json')


def load_mono(path, target_sr):
    """读音频 → 单声道 → 重采样到 target_sr，返回 float32 一维数组。"""
    data, sr = sf.read(path, dtype='float32', always_2d=True)
    data = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
    t = torch.from_numpy(np.ascontiguousarray(data)).unsqueeze(0)
    if sr != target_sr:
        t = torchaudio.functional.resample(t, sr, target_sr)
    return t.squeeze(0).numpy().astype(np.float32)


def find_offset(full, seg):
    """用 FFT 互相关定位 seg 在 full 中的起始样本索引。

    返回 (offset, score)：score 为该处的归一化相关系数，越接近 1 越可靠。
    """
    n = 1 << (len(full) + len(seg) - 1).bit_length()
    corr = np.fft.irfft(np.fft.rfft(full, n) * np.conj(np.fft.rfft(seg, n)), n)
    valid = corr[: len(full) - len(seg) + 1]
    k = int(np.argmax(valid))
    seg_n = seg - seg.mean()
    win = full[k:k + len(seg)]
    win_n = win - win.mean()
    denom = np.linalg.norm(win_n) * np.linalg.norm(seg_n)
    score = float(win_n @ seg_n / denom) if denom > 0 else 0.0
    return k, score


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', help='只处理指定篇，如 p067')
    args = ap.parse_args()

    tl = json.load(open(TIMELINE, encoding='utf-8'))
    pages = sorted({f.split('__')[0] for f in os.listdir(SENTS_V2)})
    if args.only:
        pages = [p for p in pages if p == args.only]

    result = {}
    for page in pages:
        mp3 = os.path.join(ROOT, 'assets', f'{page}.mp3')
        if not os.path.exists(mp3):
            print(f'[跳过] 缺 {page}.mp3')
            continue
        segs = sorted(f for f in os.listdir(SENTS_V2) if f.startswith(page + '__'))
        # 以 wav 的采样率为基准准备整篇音频，避免重采样口径不一致
        probe_sr = sf.info(os.path.join(SENTS_V2, segs[0])).samplerate
        print(f'── {page}：{len(segs)} 个切片，整篇重采样至 {probe_sr}Hz …')
        full = load_mono(mp3, probe_sr)
        tl_map = {s['i']: s for s in tl.get(page, [])}

        rows = []
        for fn in segs:
            idx = int(fn.split('__')[1].split('.')[0])
            p_v2 = os.path.join(SENTS_V2, fn)
            p_v1 = os.path.join(SENTS_V1, fn)
            seg, sr = sf.read(p_v2, dtype='float32', always_2d=True)
            seg = seg.mean(axis=1) if seg.shape[1] > 1 else seg[:, 0]
            dur = len(seg) / sr

            off, score = find_offset(full, seg)
            start = off / sr
            end = start + dur

            v1_dur = None
            if os.path.exists(p_v1):
                d1, sr1 = sf.read(p_v1, dtype='float32', always_2d=True)
                v1_dur = len(d1) / sr1

            t = tl_map.get(idx, {})
            rows.append({
                'i': idx,
                'text': t.get('text', ''),
                'v2_start': round(start, 3),
                'v2_end': round(end, 3),
                'v2_dur': round(dur, 3),
                'v1_dur': round(v1_dur, 3) if v1_dur else None,
                'tl_start': t.get('start_s'),
                'tl_end': t.get('end_s'),
                'tl_dur': t.get('dur_s'),
                'd_start': round(start - t['start_s'], 3) if 'start_s' in t else None,
                'd_end': round(end - t['end_s'], 3) if 'end_s' in t else None,
                'v2_eq_v1': bool(v1_dur and abs(v1_dur - dur) < 0.001),
                'match_score': round(score, 4),
            })
        result[page] = rows

    json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f'\n已落盘：{OUT}')

    # 汇总：只报真正的人工修正点（v2 与 v1 不同）+ 匹配质量可疑的
    print('\n══ 人工修正点（v2 ≠ v1，即核查动过的切片）══')
    print(f"{'篇/句':<10}{'v2_start':>9}{'v2_end':>9}{'tl_start':>9}{'tl_end':>9}{'Δstart':>8}{'Δend':>8}{'score':>7}")
    for page, rows in result.items():
        for r in rows:
            if not r['v2_eq_v1']:
                print(f"{page}#{r['i']:<3}{r['v2_start']:>9.3f}{r['v2_end']:>9.3f}"
                      f"{r['tl_start']:>9.3f}{r['tl_end']:>9.3f}{r['d_start']:>8.3f}{r['d_end']:>8.3f}"
                      f"{r['match_score']:>7.3f}")

    bad = [(p, r) for p, rows in result.items() for r in rows if r['match_score'] < 0.9]
    if bad:
        print('\n⚠ 匹配质量偏低（score<0.9，边界可能不可靠）：')
        for p, r in bad:
            print(f"   {p}#{r['i']}  score={r['match_score']}")
    else:
        print('\n匹配质量：全部 score ≥ 0.9')


if __name__ == '__main__':
    sys.exit(main())
