#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键词汇分析：分析 + 入班库 + 导出三视图。防健忘——只传源文件即可。

用法:
  python vocab_run.py 课文.txt                       # 分析+入 vocab.db+导出视图
  python vocab_run.py 课文.txt --bank 班库.db         # 指定班库
  python vocab_run.py 课文.txt --doc "课次A-课文1"     # 指定入库标识(默认用 out 名)
  python vocab_run.py --text "He can kick a ball."   # 直接给文本
  python vocab_run.py 课文.txt --no-bank              # 只出报告，不入库、不导出视图
  python vocab_run.py 课文.txt --no-view              # 入库但不导出Excel视图
"""
import os, sys, subprocess, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
ASSESS = os.path.join(HERE, "assess_vocab.py")


def main():
    ap = argparse.ArgumentParser(description="一键词汇分析 + 入班库 + 导出视图", add_help=True)
    ap.add_argument("source", nargs="?", help="课文文件(.txt/.md/.xlsx)")
    ap.add_argument("--text", default=None, help="或直接给课文文本")
    ap.add_argument("--out", default=None, help="输出名(默认取源文件名/文本次号)")
    ap.add_argument("--bank", default="vocab.db", help="班库SQLite路径(默认当前目录 vocab.db)")
    ap.add_argument("--doc", default=None, help="入库文章标识(默认用 out 名)")
    ap.add_argument("--no-bank", action="store_true", help="不入库、不导出视图")
    ap.add_argument("--no-view", action="store_true", help="入库但不导出Excel视图")
    a = ap.parse_args()

    if not a.text and not a.source:
        ap.error("需要 source 或 --text")
    if a.text:
        out = a.out or ("inline_" + "".join(c for c in a.text[:8] if c.isalnum()))
    else:
        out = a.out or os.path.splitext(os.path.basename(a.source))[0]

    cmd = [sys.executable, ASSESS]
    if a.text:
        cmd += ["--text", a.text]
    else:
        cmd += ["--file", a.source]
    cmd += ["--out", out]
    if not a.no_bank:
        cmd += ["--db", a.bank, "--doc", a.doc or out]
    if not a.no_bank and not a.no_view:
        cmd += ["--db-export", out + "_词库视图.xlsx"]
    print(">>", " ".join(cmd))
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    main()