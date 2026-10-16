#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键管道：主技能分析 + 三个软分支（学生课卡 / 教师备课 / 英式语音）串联落地。防健忘——
只传源文件即一键出齐 分析报告 + 学生记忆卡 + 教师备课本 + 英式语音卡。

用法:
  python vocab_pipeline.py 课文.txt
  python vocab_pipeline.py 课文.txt --out 课次A_阅读1
  python vocab_pipeline.py 课文.txt --steps 主,学生卡        # 只跑指定步(逗号分隔)
  python vocab_pipeline.py 课文.txt --no-语音                # 关掉某分支
  python vocab_pipeline.py --text "He can kick a ball." --limit 20
"""
import os, sys, subprocess, argparse

# 各技能脚本位置（分支脚本自带 _main_dir 定位主技能，无需改动）
_SKILLS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # skills 根
_PATH = {
    "主":     os.path.join(_SKILLS, "article-vocab-analyzer", "scripts", "assess_vocab.py"),
    "学生卡": os.path.join(_SKILLS, "student-vocab-cards", "scripts", "student_cards.py"),
    "备课":   os.path.join(_SKILLS, "teacher-vocab-prep", "scripts", "teacher_prep.py"),
    "语音":   os.path.join(_SKILLS, "british-phonetics", "scripts", "phonetics.py"),
    "整合":   os.path.join(_SKILLS, "article-vocab-analyzer", "scripts", "vocab_merge.py"),
}
_ALL = ["主", "学生卡", "备课", "语音", "整合"]
_VOICE = {"youdao", "gb-male", "gb-female"}


def main():
    ap = argparse.ArgumentParser(description="一键 主技能+三分支 落地管道", add_help=True)
    ap.add_argument("source", nargs="?", help="课文文件(.txt/.md/.xlsx)")
    ap.add_argument("--text", default=None, help="或直接给课文文本")
    ap.add_argument("--out", default=None, help="输出前缀(默认取源文件名/文本前8字；各步产生 -报告/-学生卡/-备课本/-语音卡 ...)")
    ap.add_argument("--steps", default=None, help="只跑指定步，逗号分隔(默认全跑)；可含 主/学生卡/备课/语音")
    ap.add_argument("--bank", default=None, help="[主] 班库SQLite路径(默认不传，主步仅出报告)")
    ap.add_argument("--doc", default=None, help="[主] 入库文章标识")
    ap.add_argument("--voice", default="youdao", choices=sorted(_VOICE), help="[语音] 发音来源 youdao/gb-male/gb-female")
    ap.add_argument("--limit", type=int, default=0, help="[学生卡/语音] 只对前N个词联网(防限流)")
    ap.add_argument("--no-cambridge", action="store_true", help="[语音] 关闭剑桥主源，只用有道")
    ap.add_argument("--offline", action="store_true", help="[语音] 断开联网(只出静态朗读标注)")
    ap.add_argument("--no-tts", action="store_true", help="[语音] 禁用TTS兜底(词典下载不到即留空)")
    a = ap.parse_args()

    if not a.text and not a.source:
        ap.error("需要 source 或 --text")
    base = a.out or (
        ("inline_" + "".join(c for c in a.text[:10] if c.isalnum()) if a.text
         else os.path.splitext(os.path.basename(a.source))[0]))

    steps = _ALL if not a.steps else [s for s in (x.strip() for x in a.steps.split(",")) if s]
    bad = [s for s in steps if s not in _ALL]
    if bad:
        sys.exit("未知步骤: %s (可选 %s)" % (", ".join(bad), "/".join(_ALL)))

    src = ["--text", a.text] if a.text else ["--file", a.source]

    def run(name, extra):
        path = _PATH[name]
        if not os.path.exists(path):
            print("!! 跳过 %s：缺少脚本 %s" % (name, path)); return
        cmd = [sys.executable, path] + src + extra
        print("\n===>>> 步骤[%s]: %s" % (name, " ".join(cmd)))
        subprocess.check_call(cmd)

    if "主" in steps:
        extra = ["--out", base + "_报告"]
        if a.bank and a.doc:
            extra += ["--db", a.bank, "--doc", a.doc, "--db-export", base + "_词库视图.xlsx"]
        run("主", extra)
    if "学生卡" in steps:
        run("学生卡", ["--out", base + "_学生卡"] + (["--limit", str(a.limit)] if a.limit else []))
    if "备课" in steps:
        run("备课", ["--out", base + "_备课本"])
    if "语音" in steps:
        extra = ["--out", base + "_语音卡", "--voice", a.voice]
        if a.limit:
            extra += ["--limit", str(a.limit)]
        if a.no_cambridge:
            extra.append("--no-cambridge")
        if a.offline:
            extra.append("--offline")
        else:
            extra.append("--no-tts")       # 管道/自动化一律非交互：禁用需确认的TTS兜底(词典下载不到即留空)
        run("语音", extra)
        if not a.offline:
            tts_dir = base + "_语音卡_tts"
            print("\n[提示] 真人发音已下载为本地 mp3 → 已生成在当前目录: %s/  请随 xlsx 一起拷贝，否则含本地文件名无法播放。" % tts_dir)
    if "整合" in steps:                        # 整合只读已生成的各源 xlsx, 不接收 --text/--file
        cmd = [sys.executable, _PATH["整合"], "--base", base, "--out", base]
        print("\n===>>> 步骤[整合]: %s" % " ".join(cmd))
        subprocess.check_call(cmd)

    print("\n完成。产出：%s_报告 / %s_学生卡 / %s_备课本 / %s_语音卡(*.xlsx) → 已整合为 %s_教师版 / %s_学生版"
          % ((base,) * 4 + (base, base)))


if __name__ == "__main__":
    main()