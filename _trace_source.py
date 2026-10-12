# -*- coding: utf-8 -*-
"""全库溯源：扫描课程素材目录下所有音频/视频，用时长指纹定位 assets/ 里来路不明的篇目。

背景
────
_source_match.json 里 p073 的 match 为 null、p066 只有一处假匹配（Unit_12_p117_t07，
真主人是 p117）。两者都是 32kbps/22050Hz/单声道的低质量副本，怀疑来自视频音轨或拼接产物。
本脚本把整个素材树的时长都扫出来做指纹比对，回答「高质量源到底存不存在」。

用法
────
    .venv-align/Scripts/python.exe _trace_source.py                      # 默认追 p066/p073
    .venv-align/Scripts/python.exe _trace_source.py --target 176.151,163.816
    .venv-align/Scripts/python.exe _trace_source.py --tol 3.0            # 放宽容差

说明：mp3 走 soundfile（读 header，极快）；mp4 走 PyAV（自带 ffmpeg，无需系统 ffmpeg）。
"""
import argparse
import glob
import os

import av
import soundfile as sf

SCAN_ROOT = "E:/04 少儿原版课程/03 Think 0 课程制作"
EXTS = ('*.mp3', '*.mp4', '*.m4a', '*.wav', '*.flac')

# 待溯源的 assets 篇目时长（来自 _source_match.json 的 asset.dur）
KNOWN = {'p066': 176.151, 'p073': 163.816}


def probe(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.mp4':
        with av.open(path) as c:
            dur = (c.duration or 0) / 1_000_000.0
            a = next((s for s in c.streams if s.type == 'audio'), None)
            sr = a.codec_context.sample_rate if a else None
            ch = a.codec_context.channels if a else None
        return dur, sr, ch
    i = sf.info(path)
    return i.duration, i.samplerate, i.channels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', default='', help='目标时长，逗号分隔；缺省用 p066/p073')
    ap.add_argument('--tol', type=float, default=2.0, help='容差（秒），默认 2.0')
    args = ap.parse_args()

    if args.target:
        targets = {t.strip(): float(t) for t in args.target.split(',')}
    else:
        targets = dict(KNOWN)

    files = []
    for e in EXTS:
        files += glob.glob(os.path.join(SCAN_ROOT, '**', e), recursive=True)
    print(f'扫描根目录：{SCAN_ROOT}')
    print(f'共 {len(files)} 个媒体文件\n')

    rows = []
    for p in files:
        try:
            dur, sr, ch = probe(p)
        except Exception:
            continue
        rows.append((os.path.relpath(p, SCAN_ROOT), dur, sr, ch))

    print(f'成功探测 {len(rows)} 个\n')
    for name, t in targets.items():
        hits = [(n, d, sr, ch) for n, d, sr, ch in rows if abs(d - t) <= args.tol]
        print(f'══ 目标 {name}  {t}s  （容差 ±{args.tol}s）══')
        if hits:
            for n, d, sr, ch in sorted(hits, key=lambda x: abs(x[1] - t)):
                print(f'   ✓ {n}')
                print(f'       dur={d:.3f}  Δ={d - t:+.3f}  sr={sr} ch={ch}')
        else:
            print('   ✗ 无命中 —— 全库不存在等长音频')
        print()

    # 顺带列出最长的一批，人工判断是否有拼接可能
    print('══ 全库最长的 12 个音频（拼接候选）══')
    for n, d, sr, ch in sorted(rows, key=lambda x: -x[1])[:12]:
        print(f'   {d:8.3f}s  {n}')


if __name__ == '__main__':
    main()
