# -*- coding: utf-8 -*-
"""内容级溯源：用互相关在 Unit 7 全部候选音频里搜索 p066 / p073 的片段。

时长指纹已经失效（_trace_source.py 扫 450 个文件无真命中），所以改用内容匹配，
回答最后一个问题：这两篇究竟是不是 Unit 7 音频轨 / 视频音轨的**拼接或重编码产物**？

做法：从待溯源篇目里取若干 15 秒片段，在候选音频里做 FFT 互相关，
score 接近 1 即说明该片段确实出自这条候选。

用法：
    .venv-align/Scripts/python.exe _trace_content.py
"""
import glob
import os

import av
import numpy as np
import soundfile as sf
import torch
import torchaudio

ROOT = os.path.dirname(os.path.abspath(__file__))
SR = 16000  # 统一到 16k，够用且快
SEG = 15.0  # 片段长度（秒）

UNIT7_AUDIO = "E:/04 少儿原版课程/03 Think 0 课程制作/003 第三版课程材料/第7单元/第7单元 音频"
UNIT7_VIDEO = "E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/Student's Book Video 原版/L7_视频"


def to_mono_16k(path):
    if path.lower().endswith('.mp4'):
        with av.open(path) as c:
            st = next(s for s in c.streams if s.type == 'audio')
            sr = st.codec_context.sample_rate
            chunks = []
            for frame in c.decode(st):
                arr = frame.to_ndarray()  # (ch, n) float32
                chunks.append(arr)
            data = np.concatenate(chunks, axis=1)
        data = data.mean(axis=0) if data.shape[0] > 1 else data[0]
    else:
        data, sr = sf.read(path, dtype='float32', always_2d=True)
        data = data.mean(axis=1) if data.shape[1] > 1 else data[:, 0]
    t = torch.from_numpy(np.ascontiguousarray(data)).unsqueeze(0)
    if sr != SR:
        t = torchaudio.functional.resample(t, sr, SR)
    return t.squeeze(0).numpy().astype(np.float32)


def best_match(full, seg):
    """返回 (score, offset_sec)。full/seg 已同采样率。"""
    if len(seg) > len(full):
        return 0.0, -1
    n = 1 << (len(full) + len(seg) - 1).bit_length()
    corr = np.fft.irfft(np.fft.rfft(full, n) * np.conj(np.fft.rfft(seg, n)), n)
    valid = corr[: len(full) - len(seg) + 1]
    k = int(np.argmax(valid))
    win = full[k:k + len(seg)]
    wn, sn = win - win.mean(), seg - seg.mean()
    den = np.linalg.norm(wn) * np.linalg.norm(sn)
    score = float(wn @ sn / den) if den > 0 else 0.0
    return score, k / SR


def main():
    targets = {}
    for page in ('p066', 'p073'):
        p = os.path.join(ROOT, 'assets', f'{page}.mp3')
        a = to_mono_16k(p)
        # 取 3 个片段：25%、50%、75% 处
        segs = {}
        for tag, frac in (('25%', 0.25), ('50%', 0.50), ('75%', 0.75)):
            s = int(len(a) * frac)
            segs[tag] = a[s:s + int(SEG * SR)]
        targets[page] = (a, segs)
        print(f'{page}: 全长 {len(a)/SR:.2f}s')

    cands = [(os.path.basename(p), p) for p in sorted(glob.glob(os.path.join(UNIT7_AUDIO, '*.mp3')))]
    cands += [(os.path.basename(p), p) for p in sorted(glob.glob(os.path.join(UNIT7_VIDEO, '*.mp4')))]
    print(f'\n候选 {len(cands)} 条，加载中…\n')
    loaded = []
    for name, p in cands:
        try:
            loaded.append((name, to_mono_16k(p)))
        except Exception as e:
            print(f'  [跳过] {name}: {e}')

    print('\n══ 片段互相关结果（score≥0.9 = 内容确实出自该候选）══\n')
    for page, (a, segs) in targets.items():
        print(f'── {page} ──')
        for tag, seg in segs.items():
            hits = []
            for name, full in loaded:
                sc, off = best_match(full, seg)
                hits.append((sc, name, off))
            hits.sort(reverse=True)
            top = hits[0]
            mark = '✓ 命中' if top[0] >= 0.9 else '✗ 无'
            print(f'  片段@{tag}: {mark}  best={top[1][:44]}  score={top[0]:.3f} @ {top[2]:.1f}s')
            if top[0] < 0.9:
                for sc, name, off in hits[1:3]:
                    print(f'             次选 {name[:44]}  score={sc:.3f} @ {off:.1f}s')
        print()


if __name__ == '__main__':
    main()
