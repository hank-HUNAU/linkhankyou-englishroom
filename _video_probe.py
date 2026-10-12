# -*- coding: utf-8 -*-
"""探测 Student's Book Video 原版 下各 mp4 的音轨时长/采样率/声道。

用途：assets/ 里 p066(176.15s) 与 p073(163.82s) 两篇在 198 轨 SB 音频里找不到来源
（_source_match.json 里 p073 的 match 为 null、p066 是假匹配），怀疑来自视频音轨。
本脚本扫全部视频，用时长指纹定位候选。

解码走 PyAV（自带 ffmpeg，无需系统 ffmpeg/ffprobe）。

用法：
    .venv-align/Scripts/python.exe _video_probe.py
    .venv-align/Scripts/python.exe _video_probe.py --target 176.15,163.82
"""
import argparse
import glob
import os

import av

VIDEO_ROOT = "E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/Student's Book Video 原版"


def probe(path):
    with av.open(path) as c:
        dur = (c.duration or 0) / 1_000_000.0
        a = next((s for s in c.streams if s.type == 'audio'), None)
        sr = a.codec_context.sample_rate if a else None
        ch = a.codec_context.channels if a else None
    return dur, sr, ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', default='', help='待匹配的目标时长，逗号分隔，如 176.15,163.82')
    args = ap.parse_args()
    targets = [float(t) for t in args.target.split(',') if t.strip()]

    files = sorted(glob.glob(os.path.join(VIDEO_ROOT, '**', '*.mp4'), recursive=True))
    print(f'扫描到 {len(files)} 个 mp4\n')
    print(f"{'文件':<44}{'时长':>10}{'采样率':>8}{'声道':>6}")
    rows = []
    for p in files:
        try:
            dur, sr, ch = probe(p)
        except Exception as e:
            print(f'{os.path.basename(p):<44}  读取失败 {e}')
            continue
        name = os.path.relpath(p, VIDEO_ROOT)
        rows.append((name, dur, sr, ch))
        print(f'{name:<44}{dur:>10.3f}{str(sr):>8}{str(ch):>6}')

    if targets:
        print('\n══ 时长指纹匹配（容差 ±2.0s）══')
        for t in targets:
            hits = [(n, d) for n, d, _, _ in rows if abs(d - t) <= 2.0]
            print(f'\n目标 {t}s：')
            if hits:
                for n, d in sorted(hits, key=lambda x: abs(x[1] - t)):
                    print(f'   ✓ {n}   dur={d:.3f}  Δ={d - t:+.3f}')
            else:
                print('   ✗ 无命中')


if __name__ == '__main__':
    main()
