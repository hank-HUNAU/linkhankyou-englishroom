# -*- coding: utf-8 -*-
"""方案 A 试点：用 torchaudio 的 MMS_FA（CTC 强制对齐）把已知文本钉到音频上。

用法：
  py -3 -m venv .venv-align            # 已建
  .venv-align\\Scripts\\python.exe _align_forced.py --probe p067
  .venv-align\\Scripts\\python.exe _align_forced.py --page p067 --out _forced_067.json

与能量法的区别：能量法只找静音；强制对齐是拿已知文本去配准音频，输出词级时间戳。
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import soundfile as sf
import torch
import torchaudio
from torchaudio.pipelines import MMS_FA as BUNDLE

ROOT = os.path.dirname(os.path.abspath(__file__))
SR = BUNDLE.sample_rate


def load_wav(path):
    """读任意音频 → 16k 单声道 float32。soundfile 自带 libsndfile，支持 mp3。"""
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    wav = torch.from_numpy(data.mean(axis=1))
    if sr != SR:
        wav = torchaudio.functional.resample(wav, sr, SR)
    return wav


def normalize(text):
    """课文书写形式 → 朗读形式。这一步做不干净，对齐一定错。"""
    t = text
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u201c", '"').replace("\u201d", '"')
    t = t.replace("\u2014", " ").replace("\u2013", " ")
    t = re.sub(r"\.\.\.+", " ", t)              # 省略号
    t = t.replace("–", " ")
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe")
    ap.add_argument("--page")
    ap.add_argument("--out")
    args = ap.parse_args()

    print("加载 MMS_FA 模型（首次会下载，约 1GB）…", flush=True)
    model = BUNDLE.get_model()
    model.eval()
    tokenizer = BUNDLE.get_tokenizer()
    aligner = BUNDLE.get_aligner()
    print("模型就绪；采样率", SR, "词表", len(BUNDLE.get_dict()), "词", flush=True)

    tj = json.load(open(os.path.join(ROOT, "assets", "timeline.json"), encoding="utf-8"))
    pages = [args.probe or args.page]
    for pid in pages:
        key = "p" + pid
        wav = load_wav(os.path.join(ROOT, "assets", pid + ".mp3"))
        print("%s 音频 %d 采样点 = %.2fs" % (key, len(wav), len(wav) / SR), flush=True)
        norm_wav = torchaudio.functional.preemphasis(wav)  # MMS_FA 建议做 preemphasis? 先不做
        with torch.inference_mode():
            emission, _ = model(wav.unsqueeze(0))
        print("  发射矩阵:", tuple(emission.shape), flush=True)
        sents = [s["text"] for s in tj[key]]
        # 先只对第一句做，验证链路
        txt = normalize(sents[0])
        print("  第一句:", txt[:70], flush=True)
        try:
            tokens = tokenizer(txt)
            print("  音素数:", len(tokens), flush=True)
            spans = aligner(emission[0], tokens)
            sec = spans[0].start / emission.shape[1] * (len(wav) / SR)
            end = spans[-1].end / emission.shape[1] * (len(wav) / SR)
            print("  对齐结果: %.3fs ~ %.3fs （原 TL: %.3f ~ %.3f）"
                  % (sec, end, tj[key][0]["start_s"], tj[key][0]["end_s"]), flush=True)
        except Exception as e:
            print("  对齐失败:", type(e).__name__, e, flush=True)
        break


if __name__ == "__main__":
    main()
