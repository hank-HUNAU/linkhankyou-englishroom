# -*- coding: utf-8 -*-
"""
_pack_landing.py — TH!NK F「Think 0_落地」交付打包器（2026-11-14）

用途：把本轮（2026-11-12 ~ 11-14）产出的文件、它们的依赖文件、以及历史上
与对齐核查 / 语块 / 意群 / p052 处置相关的文件，按 8 类归档到交付文件夹，
并生成可核对清单（MANIFEST.csv / MANIFEST.md）、SHA256SUMS.txt、校验记录与 ZIP。

设计原则：
1. 只复制，不移动、不删除任何源文件；音频文件 md5 前后必须一致。
2. 每个目标文件在 MANIFEST.csv 里恰好出现一次，附「来源 / 类别 / 状态 / 说明」。
3. MANIFEST.csv / MANIFEST.md / SHA256SUMS.txt 属自指产物，排除在校验清单外。
4. 目标文件夹若已存在且非空，默认拒绝覆盖（--force 才允许）。

用法：
  python _pack_landing.py            # 打包（含 ZIP）
  python _pack_landing.py --no-zip   # 只落库，不打 ZIP
"""
from __future__ import unicode_literals

import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import shutil
import sys
import zipfile

# ---------------------------------------------------------------------------
# 路径基线
# ---------------------------------------------------------------------------
WS = r"E:\04 少儿原版课程\03 Think 0 课程制作\Codex 学习中心"
REPO = os.path.join(WS, "Think F 教材资产", "github在线推送")
ARCH = os.path.join(WS, "Think F 教材资产")
MEM = os.path.join(WS, ".workbuddy", "memory")
DEST = os.path.join(WS, "Think 0_落地")
ZIP_BASE = os.path.join(WS, "Think 0_落地_2026-11-14")

ROOTS = {"R": REPO, "A": ARCH, "M": MEM}

CATS = [
    ("01_交付说明", "本轮生成：入口、结论、校验记录"),
    ("02_脚本工具", "本轮新增脚本 + 复现所需依赖脚本"),
    ("03_核查报告", "全站对齐核查 / 诊断 / 方案拍板 / 历史清单"),
    ("04_仓库运行时与正典", "本轮改动的站点运行时数据（保持仓库相对路径）"),
    ("05_归档教学资源", "归档正典：p052 句级/译文/字幕、p048 意群/语块、教师资源"),
    ("06_规约与进度", "五份 WORKFLOW + 资产清单 + 两份进度活文档"),
    ("07_历史关联证据", "U1–U4 支线、词级证据、口径依据"),
    ("08_备份与日志", "处置前备份 + 当日日志 + 项目长期记忆"),
]

# (目标相对路径, 源根, 源相对路径, 状态, 说明)
ITEMS = []


def add(cat, dest_rel, root, src_rel, state="", note=""):
    ITEMS.append((cat + "/" + dest_rel, root, src_rel, state, note))


def add_many(cat, root, pairs, state="", note=""):
    """pairs: [(dest_rel, src_rel), ...]"""
    for d, s in pairs:
        add(cat, d, root, s, state, note)


# ---------------------------------------------------------------------------
# 02_脚本工具
# ---------------------------------------------------------------------------
SCRIPTS_NEW = [
    ("_apply_p052_fix.py", "本轮新增", "方案 A 处置器：--dry-run / --apply，双写 + 6 处下游同步 + 自检"),
    ("_gen_words_cache.py", "本轮新增", "只读音频补 ASR 词级证据（U7/U8/U12 共 12 篇），不碰 timeline"),
    ("_verify_alignment_all.py", "本轮新增", "全站 48 篇可机检核查（只读），出篇章/逐句 CSV + JSON + MD"),
    ("_pack_landing.py", "本轮新增", "本打包器：生成 Think 0_落地 交付包 + 清单 + 校验 + ZIP"),
    ("_align_u14_rerun.py", "11-12 新增", "U1–U4 情况1 六篇按主线口径重跑 aligner"),
    ("_apply_u14_rerun.py", "11-12 新增", "六篇重跑结果双写归档 + timeline"),
    ("_gen_u14_confidence.py", "11-12 新增", "生成 136 句逐句置信度清单"),
]
for fn, st, note in SCRIPTS_NEW:
    add("02_脚本工具", fn, "R", fn, st, note)

SCRIPTS_DEP = [
    ("content_pipeline.py", "五段流水线编排器（align/vocab/zh/chunk/yiqun）+ --audit"),
    ("_gen_teacher_pack.py", "方案 B 后重生成教师讲解卡 / 学生发放页"),
    ("_yiqun_extract.py", "意群候选提取（脚本只出候选，人工定稿是唯一入口）"),
    ("_yiqun_verify.py", "意群六门禁 G1–G6，方案 B 后全过"),
    ("_chunk_extract.py", "语块候选 Lane A / Lane B"),
    ("_chunk_verify.py", "语块校验（页面未内嵌 CHUNKS 属预期）"),
    ("_chunk_master.py", "跨 48 篇生成语块总表候选"),
    ("_gen_and_verify_srt_lrc.py", "SRT / LRC 重派生与校验依赖"),
    ("_verify_srt_lrc_vs_json.py", "字幕与句级正典一致性校验"),
    ("_sync_timeline.js", "timeline.json → index.html DB.TL 同步"),
    ("_timeline_check.js", "时间轴单一数据源门禁"),
    ("_regress.js", "npm test 回归入口"),
    ("package.json", "npm test 脚本定义"),
    ("_align_unit.py", "U5–U12 主线对齐入口"),
    ("_verify_alignment_u14.py", "U1–U4 对齐核查"),
    ("_push_one.js", "Git Data API 兜底推送"),
]
for fn, note in SCRIPTS_DEP:
    add("02_脚本工具", fn, "R", fn, "依赖", note)

# ---------------------------------------------------------------------------
# 03_核查报告
# ---------------------------------------------------------------------------
REPORTS = [
    ("p052_方案A处置与复检_2026-11-14.md", "本轮产出", "方案 A 处置全过程 + 自检/门禁/回归结果"),
    ("意群_p048_方案B定稿_2026-11-14.md", "本轮产出", "方案 B 定稿 + 六门禁 + 教师资源重生成"),
    ("全站对齐质量核查_48篇_2026-11-14.md", "本轮产出", "处置后 48 篇 / 1115 句，A969-B146-C0"),
    ("全站对齐质量核查_48篇_2026-11-14.json", "本轮产出", "处置后机器可读结果"),
    ("全站对齐质量核查_48篇_2026-11-14_篇章.csv", "本轮产出", "处置后逐篇 48 行"),
    ("全站对齐质量核查_48篇_2026-11-14_逐句.csv", "本轮产出", "处置后逐句 1115 行"),
    ("全站对齐质量核查_48篇_2026-11-14_处置前.md", "处置前快照", "48 篇 / 1118 句，A969-B146-C3"),
    ("全站对齐质量核查_48篇_2026-11-14_处置前.json", "处置前快照", "处置前机器可读结果"),
    ("全站对齐质量核查_48篇_2026-11-14_处置前_篇章.csv", "处置前快照", "处置前逐篇 48 行"),
    ("全站对齐质量核查_48篇_2026-11-14_处置前_逐句.csv", "处置前快照", "处置前逐句 1118 行"),
    ("情况2三篇间隙诊断_2026-11-14.md", "本轮产出", "p020/p024/p045 三方对账判非缺陷"),
    ("p052_评分段未朗读诊断_2026-11-14.md", "本轮产出", "发现真缺陷并提出 A/B/C 方案"),
    ("意群_p048_审核意见对照_2026-11-14.md", "本轮产出", "SVC 三种切法对照表，推荐 B"),
    ("对齐准确度核查_U1-U4_vs_U5-U12_2026-11-12.md", "历史相关", "支线 vs 主线口径与证据完备性核查"),
    ("句级对齐置信度_U1-U4_情况1.csv", "历史相关", "136 句 A136/B0/C0 逐句清单"),
    ("句级对齐置信度_U1-U4_情况1.json", "历史相关", "逐句清单 JSON"),
    ("句级对齐置信度_U1-U4_情况1.html", "历史相关", "逐句清单网页版"),
    ("圆桌会议纪要_听写跟读聚焦_2026-10-21.md", "历史相关", "跟读/听写设计依据（仓库内未跟踪旧文件）"),
    ("正课文清单.csv", "历史相关", "48 篇正课文 canonical 清单"),
    ("正课文清单.md", "历史相关", "清单 Markdown 版"),
    ("正课文清单.html", "历史相关", "清单网页版"),
    ("正文篇章清单_U1-U12.md", "历史相关", "归档 × timeline 零差异清单"),
    ("栏目标题与音频对照表.html", "历史相关", "报幕 / 栏目标题对照（三方对账依据）"),
    ("课文音频对照清单.html", "历史相关", "音频序 vs 课本版面序对照"),
]
for fn, st, note in REPORTS:
    add("03_核查报告", fn, "R", "reports/" + fn, st, note)

# ---------------------------------------------------------------------------
# 04_仓库运行时与正典（保持仓库相对路径）
# ---------------------------------------------------------------------------
RUNTIME = [
    ("assets/timeline.json", "49 篇 / 1138 句，单句时间轴唯一正典"),
    ("assets/subtitles/p052.srt", "方案 A 后由新 5 句重派生"),
    ("assets/subtitles/p052.lrc", "方案 A 后由新 5 句重派生"),
    ("assets/p052.mp3", "受审音频；方案 A 前后 md5 未变（69fa7bf91deeb25ca25f7578fa53cb15）"),
    ("index.html", "FOLLOW_META[52].s 8→5；DB.TL 由 _sync_timeline.js 同步"),
    ("_book_extra.json", "删 book[52].arts 第二段 3 句"),
    ("_integrate_u56.js", "生成器内联 BOOK_EXTRA 同步清理"),
    ("_unit_5_source.json", "p052 缩为 5 行；删 3 行原文存 excluded_from_alignment 留痕"),
    ("_unit_5_timeline.json", "U5 历史时间轴产物同步"),
    ("_unit_5_timeline.txt", "U5 历史时间轴文本同步"),
    ("_zh_tables/译文表_p052.json", "删 3 条译文键"),
    ("_unit_7_words.json", "11-14 补：U7 词级证据（旧格式）"),
    ("_unit_7_asr.json", "11-14 补：U7 词级证据（富格式 segments/duration）"),
    ("_unit_8_words.json", "11-14 补：U8 词级证据（旧格式）"),
    ("_unit_8_asr.json", "11-14 补：U8 词级证据（富格式）"),
    ("_unit_12_words.json", "11-14 补：U12 词级证据（旧格式）"),
    ("_unit_12_asr.json", "11-14 补：U12 词级证据（富格式）"),
]
for rel, note in RUNTIME:
    add("04_仓库运行时与正典", rel, "R", rel, "本轮改动", note)

# 33 个篇章页：方案 A 清理内联 BOOK_EXTRA（含紧凑 JSON 补漏 4 页）
PAGE_PREFIXES = [
    "048", "051", "052", "054", "056", "059", "060", "063",
    "067", "069", "070", "072", "075", "077", "078", "080",
    "085", "087", "088", "090", "092", "095", "096", "099",
    "102", "105", "106", "108", "111", "113", "114", "117", "202",
]
for pre in PAGE_PREFIXES:
    matches = [f for f in os.listdir(os.path.join(REPO, "篇章页"))
               if f.startswith("读写_" + pre + "_") and f.endswith(".html")]
    if len(matches) != 1:
        raise RuntimeError("篇章页前缀 %s 命中 %d 个：%s" % (pre, len(matches), matches))
    rel = "篇章页/" + matches[0]
    note = "方案 A 内联 BOOK_EXTRA 清理"
    if pre == "052":
        note = "p052 正文页：DB.ZH 删 3 键 + BOOK_EXTRA 清理"
    elif pre == "048":
        note = "p048 篇章页（意群/语块试点母版）+ 紧凑 JSON 补漏"
    elif pre in ("051", "056", "063"):
        note = "方案 A 内联 BOOK_EXTRA 清理 + 紧凑 JSON 补漏"
    add("04_仓库运行时与正典", rel, "R", rel, "本轮改动", note)

# ---------------------------------------------------------------------------
# 05_归档教学资源（归档正典，与仓库相对独立）
# ---------------------------------------------------------------------------
ARCHIVE_ITEMS = [
    ("U5_FreeTime/01_正文篇章/句级数据_p052.json", "本轮改动", "p052 归档句级正典 8→5 句，与 timeline 双写一致"),
    ("U5_FreeTime/01_正文篇章/p052.srt", "本轮改动", "归档字幕重派生"),
    ("U5_FreeTime/01_正文篇章/p052.lrc", "本轮改动", "归档字幕重派生"),
    ("U5_FreeTime/01_正文篇章/译文_p052.json", "本轮改动", "译文删 3 键"),
    ("U5_FreeTime/01_正文篇章/p052.mp3", "未改动", "归档音频正本；硬规约「音频只增不改」"),
    ("U5_FreeTime/04_意群数据/意群_p048.json", "本轮定稿", "方案 B：22 句 / 57 群，新增 grouping_rule，六门禁全过"),
    ("U5_FreeTime/05_教学资源/教师讲解卡_p048.html", "本轮重生成", "22 句 / 57 意群 / 6 语块，A4 可打印"),
    ("U5_FreeTime/05_教学资源/学生发放页_p048.html", "本轮重生成", "本地发放页，零联网零音频"),
    ("U5_FreeTime/02_词汇数据/语块_p048.json", "历史相关", "p048 语块定稿 6 条（教师卡语块来源）"),
    ("U5_FreeTime/02_词汇数据/u5_p048_robotics_club.json", "依赖", "p048 九层词汇分析"),
    ("U5_FreeTime/02_词汇数据/u5_p052_tech_break.json", "依赖", "p052 九层词汇分析"),
    ("U5_FreeTime/02_词汇数据/u5_p051_favourite_technology.json", "历史相关", "U5 词汇链同构样本"),
    ("U5_FreeTime/02_词汇数据/u5_p054_school_concert.json", "历史相关", "U5 词汇链同构样本"),
    ("00_语块总表/语块总表_候选.csv", "历史相关", "362 候选，只收 disp≥2"),
    ("00_语块总表/语块总表_候选.json", "历史相关", "候选机器可读版"),
    ("00_语块总表/语块总表_候选.html", "历史相关", "候选网页版"),
]
for rel, st, note in ARCHIVE_ITEMS:
    add("05_归档教学资源", rel, "A", rel, st, note)

# ---------------------------------------------------------------------------
# 06_规约与进度
# ---------------------------------------------------------------------------
DOCS = [
    ("_ALIGNMENT_WORKFLOW.md", "本轮改动", "§4 新增「判定漏句前必须三方对账」；§7 状态订正到 1138 句"),
    ("_RELEASE_WORKFLOW.md", "本轮改动", "§7 状态：1153 → 1141 → 1138"),
    ("_VOCAB_WORKFLOW.md", "依赖", "词汇四链规约"),
    ("_CHUNK_WORKFLOW.md", "依赖", "语块两轨定案 / 学术诚实边界 / 三轮 DOI 审核"),
    ("_YIQUN_WORKFLOW.md", "依赖", "意群=句法教学单位，零音频依赖"),
    ("AGENTS.md", "本轮改动", "工具表 +3 脚本；timeline 口径 1138 句"),
    ("MANIFEST.md", "本轮改动", "资产清单句数订正"),
    ("课程资产/README.md", "本轮改动", "正文篇章与 timeline 句数订正"),
    ("项目进度.md", "本轮改动", "整项目活文档；⑪⑫ 已完成、⑬ 落地包交付"),
    ("项目进度_语块意群.md", "本轮改动", "语块+意群专项子文档"),
]
for rel, st, note in DOCS:
    add("06_规约与进度", rel, "R", rel, st, note)

# ---------------------------------------------------------------------------
# 07_历史关联证据
# ---------------------------------------------------------------------------
HISTORY = [
    ("_u14_source.json", "U1–U4 课本源文本正典（三方对账依据）"),
    ("_u14_words.json", "U1–U4 词级证据"),
    ("_u14_report.json", "U1–U4 对齐报告"),
    ("_u14_rerun_result.json", "11-12 六篇拉齐重跑结果"),
    ("_unit_5_words.json", "U5 词级证据（p052 诊断依据）"),
    ("_align_u14.py", "U1–U4 支线对齐脚本"),
    ("_extract_u14_text.py", "U1–U4 文本抽取（BLANKS 回填）"),
    ("_merge_u14.py", "U1–U4 合入脚本"),
    ("_build_u14_pages.py", "U1–U4 篇章页生成（p048 母版）"),
    ("_chunk_cand_p048.json", "p048 语块候选（定稿 6 条的来源）"),
]
for rel, note in HISTORY:
    add("07_历史关联证据", rel, "R", rel, "历史相关", note)

# ---------------------------------------------------------------------------
# 08_备份与日志
# ---------------------------------------------------------------------------
BK11 = "2026-11-14/backup_p052_fix_121855"
BK12 = "2026-11-12/backup_20261112_225019"


def add_tree(cat, root, src_dir, dest_prefix, state, note):
    base = os.path.join(ROOTS[root], src_dir)
    if not os.path.isdir(base):
        raise RuntimeError("备份目录不存在：" + base)
    for dirpath, _dirs, files in os.walk(base):
        for fn in sorted(files):
            full = os.path.join(dirpath, fn)
            rel_in = os.path.relpath(full, base).replace("\\", "/")
            src_rel = src_dir.replace("\\", "/") + "/" + rel_in
            add(cat, dest_prefix + "/" + rel_in, root, src_rel, state, note)


add_tree("08_备份与日志", "M", BK11, "方案A处置前备份", "备份", "47 个被改文件原始副本 + 意群/教师资源备份")
add_tree("08_备份与日志", "M", BK12, "11-12拉齐前备份", "备份", "6 篇归档 + timeline + audio_before.md5")

LOGS = [
    ("2026-11-14/README.md", "当日索引（本轮收尾后需追加）"),
    ("2026-11-14/工作日志.md", "当日详细过程日志（本轮收尾后需追加）"),
    ("2026-11-12/README.md", "11-12 拉齐重跑当日索引"),
    ("2026-11-12/工作日志.md", "11-12 拉齐重跑详程"),
    ("MEMORY.md", "项目长期记忆（9 节硬规约 / 坑位 / 口径）"),
]
for rel, note in LOGS:
    add("08_备份与日志", rel, "M", rel, "日志/记忆", note)

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def put_text(rel, text):
    p = os.path.join(DEST, rel.replace("/", os.sep))
    d = os.path.dirname(p)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return rel


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="目标目录已存在时清空重建")
    ap.add_argument("--no-zip", action="store_true", help="不生成 ZIP")
    args = ap.parse_args()

    if os.path.isdir(DEST) and os.listdir(DEST):
        if not args.force:
            print("[x] 目标目录已存在且非空：%s\n    如确需重建请加 --force" % DEST)
            return 2
        shutil.rmtree(DEST)
    if not os.path.isdir(DEST):
        os.makedirs(DEST)

    for cat, desc in CATS:
        d = os.path.join(DEST, cat)
        if not os.path.isdir(d):
            os.makedirs(d)

    # 1) 复制
    mapping = {}       # dest_rel -> (root_label, src_rel, state, note, src_abs)
    missing = []
    for dest_rel, root, src_rel, state, note in ITEMS:
        src = os.path.join(ROOTS[root], src_rel.replace("/", os.sep))
        if not os.path.isfile(src):
            missing.append((dest_rel, src))
            continue
        dst = os.path.join(DEST, dest_rel.replace("/", os.sep))
        dd = os.path.dirname(dst)
        if not os.path.isdir(dd):
            os.makedirs(dd)
        shutil.copy2(src, dst)
        mapping[dest_rel] = (root, src_rel, state, note, src)

    if missing:
        print("[!] 缺失 %d 个源文件（已跳过，见 校验记录.md）：" % len(missing))
        for d, s in missing:
            print("    %s  <-  %s" % (d, s))

    # 2) 逐文件比对（源 vs 目标）
    verify_rows = []
    bad = []
    for dest_rel, (root, src_rel, state, note, src) in sorted(mapping.items()):
        dst = os.path.join(DEST, dest_rel.replace("/", os.sep))
        s_size, d_size = os.path.getsize(src), os.path.getsize(dst)
        s_md5, d_md5 = md5_of(src), md5_of(dst)
        ok = (s_size == d_size and s_md5 == d_md5)
        if not ok:
            bad.append(dest_rel)
        verify_rows.append((dest_rel, root, src_rel, state, s_size, s_md5, ok))

    audio_repo = os.path.join(REPO, "assets", "p052.mp3")
    audio_arch = os.path.join(ARCH, "U5_FreeTime", "01_正文篇章", "p052.mp3")
    audio_md5_repo = md5_of(audio_repo) if os.path.isfile(audio_repo) else "-"
    audio_md5_arch = md5_of(audio_arch) if os.path.isfile(audio_arch) else "-"

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_bytes = sum(r[4] for r in verify_rows)

    # 3) 生成说明文档
    readme = u"""# Think 0_落地 · 交付包入口

> 用户所称「文件夹【Think 0_落地】」即本文件夹。
> 生成时间：%s　|　生成脚本：`02_脚本工具/_pack_landing.py`（可复现）
> 源工作区：`E:\\04 少儿原版课程\\03 Think 0 课程制作\\Codex 学习中心`

## 这是什么

2026-11-12 ~ 11-14 这一轮的**完整落地快照**：本轮产出 + 复现所需依赖 + 历史上与
「句级对齐核查 / p052 真缺陷处置 / 意群 p048 定稿 / 语块与教师资源」相关的文件。
**只复制、不移动、不删改源文件**；站点与归档正典仍在原位置，本包是交付副本。

## 目录结构

| 目录 | 内容 |
|---|---|
| `01_交付说明/` | 本文件、本轮工作与结论、校验记录 |
| `02_脚本工具/` | 本轮新增 7 个脚本 + 16 个复现依赖脚本（含本打包器） |
| `03_核查报告/` | 处置前/后全站核查四件套、诊断、方案拍板、历史清单共 24 件 |
| `04_仓库运行时与正典/` | 本轮改动的站点数据（保持仓库相对路径，含 33 个篇章页与 p052.mp3） |
| `05_归档教学资源/` | p052 句级/译文/字幕、p048 意群定稿与教师卡/学生页、语块总表 |
| `06_规约与进度/` | 五份 WORKFLOW + AGENTS/MANIFEST + 两份进度活文档 |
| `07_历史关联证据/` | U1–U4 支线、词级证据、p048 语块候选 |
| `08_备份与日志/` | 方案 A 处置前备份、11-12 拉齐前备份、当日日志、项目 MEMORY.md |

根目录三件校验产物：`MANIFEST.csv`（逐文件机器可读清单）、`MANIFEST.md`（分类人读清单）、
`SHA256SUMS.txt`（校验和）。同级另有 `Think 0_落地_2026-11-14.zip` 便于搬运。

## 三条硬规约在本包中的体现

1. **音频只增不改**：`assets/p052.mp3` 仓库副本 md5 `%s`；归档副本 md5 `%s`；方案 A 前后未变。
2. **句级双写**：`04_仓库运行时与正典/assets/timeline.json` 与
   `05_归档教学资源/U5_FreeTime/01_正文篇章/句级数据_p052.json` 的 p052 均为 5 句。
3. **站点禁引库外路径**：本包为交付副本，不参与站点运行时；线上只认原仓库相对路径。

## 一句话结论

p052 方案 A 与意群 p048 方案 B 均已落地；全站 timeline **49 篇 / 1138 句**，
48 篇正课文核查 **A969 / B146 / C0**，C 级清零；音频零改动、门禁与 `npm test` 11/11 全绿。
详见 `01_交付说明/本轮工作与结论_2026-11-14.md`。
""" % (now, audio_md5_repo, audio_md5_arch)
    put_text("01_交付说明/README.md", readme)

    conclusion = u"""# 本轮工作与结论 · 2026-11-12 ~ 11-14

> 用户指令：`按推荐方案！完成后，将所有本轮产出的文件及依赖文件打包、包含历史上与本轮相关的文件落库到文件夹【Think 0_落地】文件夹中`

## 一、拍板与执行

| 项 | 推荐方案 | 执行结果 |
|---|---|---|
| ⑪ p052 评分结果段未朗读 | **方案 A**：删课本印刷但音频未朗读的 3 行 | ✅ 已执行（`_apply_p052_fix.py --apply`） |
| ⑫ 意群 p048 定稿 | **方案 B**：只改 i=3 / i=12，消除整段 SVC | ✅ 已执行（55→57 群） |

## 二、p052 方案 A 改动面（47 个文件）

- 双写：`assets/timeline.json` + `U5_FreeTime/01_正文篇章/句级数据_p052.json`，p052 8→5 句。
- 重派生：仓库 / 归档各 `p052.srt` + `p052.lrc`，均 5 条。
- 译文链：`_zh_tables/译文表_p052.json`、归档 `译文_p052.json`、页面 `DB.ZH` 各删 3 键。
- 课文结构：`_book_extra.json`、`_integrate_u56.js`、**33 个篇章页共 66 处内联 `BOOK_EXTRA`**（含标准 JSON 与紧凑 JSON 两种序列化，后者曾漏 4 页共 6 处，已补清）。
- 元数据 / 生产输入：`index.html` 的 `FOLLOW_META[52].s` 8→5；`_unit_5_source.json` 保留 `excluded_from_alignment` 留痕，防止重跑复活；`_unit_5_timeline.{json,txt}` 同步。
- **音频未动**：`assets/p052.mp3` md5 `%s`。

## 三、意群 p048 方案 B

- 正典 `意群_p048.json`：`n_groups` 55→57；新增 `grouping_rule`；
  i=3 拆为 `it's` / `a club for building robots`，i=12 拆为 `I` / `feel really excited`。
- 六门禁 G1–G6 全过：22 句 / 57 段 / 平均 2.59 段每句。
- 教师讲解卡 `20,797 B`、学生发放页 `13,220 B` 重生成，规模 22 句 / 57 意群 / 6 语块。

## 四、前置工作（本包一并收录）

1. **规程固化**：`_ALIGNMENT_WORKFLOW.md` §4 写入「判定漏句前必须三方对账」（行数对账 / 间隙词归类 / ASR×课本交叉印证），源于两次误判教训。
2. **情况2 三篇判非缺陷**：p020 / p024 / p045 归档行数 == 课本源行数，间隙属报幕、署名、小节题注或音频独有台词，不改数据。
3. **补齐词级证据**：`_gen_words_cache.py` 只读音频补 U7/U8/U12 共 12 篇（words + asr 双格式），全站 48/48 有可机检证据；本机改用本地 CTranslate2 small 模型目录绕开 HF 离线缓存缺 small 的坑。
4. **全站核查**：`_verify_alignment_all.py` 处置前 48 篇 / 1118 句 A969-B146-**C3**；处置后 48 篇 / 1115 句 A969-B146-**C0**；两套四件产物并存（`_处置前` 快照）。
5. **口径订正**：timeline 与译文 **49 篇 / 1138 句**（48 篇 1115 + p202 23）。历史值 1153（报幕清理前）→ 1141 → 1138。7 处主文档同步订正。

## 五、验收记录

```
node _sync_timeline.js            ✓
node _timeline_check.js           OK 时间轴单一数据源一致：49 篇 / 1138 句
npm test                          11 通过 / 0 失败
BOOK_EXTRA 声明                   98 个全可 JSON 解析，含 52 的 66 个 arts 均 5 句
全站运行时残留                    无
音频 md5                          前后一致
```

## 六、口径边界（诚实声明）

- A/B/C 是**可机检分级**（词覆盖率、词数配比、词边界残差），**不是人工听审准确率**。
- aligner 的 `confidence` 是 LCS 词映射率，不是识别概率；情况1 同源时恒 1.000，无鉴别力。
- 9,336 词小语料上 Biber「10 次/百万词」不可达，语块只能称「教材内相对高频 + 教学判断」。

## 七、仍挂起（不在本包处置范围）

- `#51` 等 ima copilot 语块/意群规约到手后合并 → 再谈扩量（U5 余 3 篇 → 48 篇）与语块条数方案。
- 语块总表 / 教师卡的 9,336 词口径待 #51 统一重算（p052 删 3 句后未局部改数）。
- 可选：p020「No problem.」/ p024「Next week? But Ruby…」记入教师资源；教师卡 PDF 导出；自动化巡检脚本。
""" % audio_md5_repo
    put_text("01_交付说明/本轮工作与结论_2026-11-14.md", conclusion)

    # 4) 扫描 DEST 生成清单（排除 3 件自指产物）
    SELF = {"MANIFEST.csv", "MANIFEST.md", "SHA256SUMS.txt"}
    all_files = []
    for dirpath, _dirs, files in os.walk(DEST):
        for fn in files:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, DEST).replace("\\", "/")
            if rel in SELF:
                continue
            all_files.append(rel)
    all_files.sort()

    rows = []
    for rel in all_files:
        full = os.path.join(DEST, rel.replace("/", os.sep))
        meta = mapping.get(rel)
        if meta:
            root, src_rel, state, note, src_abs = meta
            src_disp = {"R": "github在线推送", "A": "Think F 教材资产", "M": ".workbuddy/memory"}[root] + "/" + src_rel
        else:
            root, src_rel, state, note, src_abs = ("-", "-", "本轮生成", "打包器生成的交付说明", None)
            src_disp = "(本轮生成)"
        cat = rel.split("/")[0]
        rows.append({
            "类别": cat,
            "目标相对路径": rel,
            "来源": src_disp,
            "状态": state,
            "说明": note,
            "字节": os.path.getsize(full),
            "md5": md5_of(full),
            "sha256": sha256_of(full),
        })

    csv_path = os.path.join(DEST, "MANIFEST.csv")
    with io.open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["类别", "目标相对路径", "来源", "状态", "说明", "字节", "md5", "sha256"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    sums_path = os.path.join(DEST, "SHA256SUMS.txt")
    with io.open(sums_path, "w", encoding="utf-8", newline="") as f:
        for r in rows:
            f.write("%s  %s\n" % (r["sha256"], r["目标相对路径"]))

    cat_counts = {}
    for r in rows:
        cat_counts[r["类别"]] = cat_counts.get(r["类别"], 0) + 1

    man_md = [u"# MANIFEST · Think 0_落地 交付清单", u"",
              u"> 生成时间：%s　|　逐文件明细见 `MANIFEST.csv`，校验和见 `SHA256SUMS.txt`。" % now,
              u"> 本文件、`MANIFEST.csv`、`SHA256SUMS.txt` 为自指产物，不计入校验清单。", u"",
              u"## 汇总", u"",
              u"| 类别 | 文件数 | 说明 |", u"|---|---:|---|"]
    for cat, desc in CATS:
        man_md.append(u"| `%s/` | %d | %s |" % (cat, cat_counts.get(cat, 0), desc))
    man_md += [u"| **合计** | **%d** | 总字节 %s |" % (len(rows), format(sum(r["字节"] for r in rows), ",")), u"",
               u"## 分类明细", u""]
    for cat, desc in CATS:
        sub = [r for r in rows if r["类别"] == cat]
        man_md += [u"### `%s/`（%d）" % (cat, len(sub)), u"",
                   u"| 文件 | 状态 | 字节 | 说明 |", u"|---|---|---:|---|"]
        for r in sub:
            name = r["目标相对路径"][len(cat) + 1:]
            note = r["说明"].replace("|", "\\|")
            man_md.append(u"| `%s` | %s | %s | %s |" % (name, r["状态"], format(r["字节"], ","), note))
        man_md.append(u"")
    man_md += [u"## 来源根", u"",
               u"- `github在线推送/` = `%s`" % REPO,
               u"- `Think F 教材资产/` = `%s`" % ARCH,
               u"- `.workbuddy/memory/` = `%s`" % MEM, u""]
    put_text("MANIFEST.md", u"\n".join(man_md) + u"\n")

    # 5) 校验记录
    chk = [u"# 校验记录 · Think 0_落地", u"",
           u"> 生成时间：%s" % now, u"",
           u"## 一、复制一致性（源文件 vs 落地副本）", u"",
           u"- 纳入源文件：**%d** 个，逐文件比对「字节数 + md5」。" % len(verify_rows),
           u"- 一致：**%d**；不一致：**%d** %s。" % (
               len(verify_rows) - len(bad), len(bad), ("（" + ", ".join(bad) + "）") if bad else ""),
           u"- 缺失跳过：**%d** %s。" % (len(missing), ("（见下）" if missing else "")), u""]
    if missing:
        chk += [u"| 目标路径 | 期望源文件 |", u"|---|---|"]
        for d, s in missing:
            chk.append(u"| `%s` | `%s` |" % (d, s))
        chk.append(u"")
    chk += [u"## 二、音频只增不改（硬规约）", u"",
            u"| 副本 | md5 |", u"|---|---|",
            u"| `04_仓库运行时与正典/assets/p052.mp3` | `%s` |" % audio_md5_repo,
            u"| `05_归档教学资源/U5_FreeTime/01_正文篇章/p052.mp3` | `%s` |" % audio_md5_arch,
            u"| 方案 A 前后（历史记录） | `69fa7bf91deeb25ca25f7578fa53cb15` |", u"",
            u"结论：%s" % ("一致，音频未被本打包过程改动。" if audio_md5_repo == audio_md5_arch else "两副本 md5 不同，需人工复核！"), u"",
            u"## 三、正典双写（硬规约）", u"",
            u"由 `04_仓库运行时与正典/assets/timeline.json` 与 "
            u"`05_归档教学资源/U5_FreeTime/01_正文篇章/句级数据_p052.json` 现场读取核对：", u""]
    try:
        tl = json.load(io.open(os.path.join(DEST, "04_仓库运行时与正典", "assets", "timeline.json"), "r", encoding="utf-8"))
        arc = json.load(io.open(os.path.join(DEST, "05_归档教学资源", "U5_FreeTime", "01_正文篇章", "句级数据_p052.json"), "r", encoding="utf-8"))
        tl52 = tl.get("p052", [])
        arc52 = arc.get("sentences", arc if isinstance(arc, list) else [])
        chk += [u"- timeline 篇章数 / 总句数：**%d / %d**" % (len(tl), sum(len(v) for v in tl.values())),
                u"- timeline p052：**%d 句**；归档 p052：**%d 句** → %s" % (
                    len(tl52), len(arc52), "一致 ✓" if len(tl52) == len(arc52) == 5 else "不一致，需复核！")]
    except Exception as e:
        chk.append(u"- 现场读取失败：%s（以 `reports/p052_方案A处置与复检_2026-11-14.md` 为准）" % e)
    chk += [u"",
            u"## 四、校验产物自指约定", u"",
            u"`MANIFEST.csv` / `MANIFEST.md` / `SHA256SUMS.txt` 三件为派生清单，",
            u"其自身不列入 SHA256SUMS（避免自指循环）；其余 **%d** 个文件全部列入。" % len(rows), u"",
            u"复核命令（在落地文件夹内，PowerShell）：", u"",
            u"```powershell", u"Get-Content SHA256SUMS.txt | ForEach-Object {",
            u"  $h,$p = $_ -split '  ',2; $a=(Get-FileHash $p -Algorithm SHA256).Hash.ToLower()",
            u"  if ($a -ne $h) { Write-Host \"MISMATCH $p\" }", u"}", u"```", u""]
    put_text("01_交付说明/校验记录.md", u"\n".join(chk) + u"\n")

    # 6) ZIP
    zip_path = None
    if not args.no_zip:
        zip_path = ZIP_BASE + ".zip"
        if os.path.isfile(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for rel in all_files:
                z.write(os.path.join(DEST, rel.replace("/", os.sep)), rel)
            # 三件自指产物也打进 ZIP
            for s in sorted(SELF):
                z.write(os.path.join(DEST, s), s)

    print("=" * 68)
    print("落地包完成：%s" % DEST)
    print("文件 %d 个（含说明 %d 件 + 源文件 %d 件），总字节 %s" % (
        len(rows), len(rows) - len(verify_rows), len(verify_rows), format(sum(r["字节"] for r in rows), ",")))
    for cat, _ in CATS:
        print("  %-26s %3d" % (cat, cat_counts.get(cat, 0)))
    print("复制一致性：%d/%d OK；缺失 %d" % (len(verify_rows) - len(bad), len(verify_rows), len(missing)))
    print("音频 md5：repo=%s arch=%s" % (audio_md5_repo, audio_md5_arch))
    if zip_path:
        print("ZIP：%s（%s 字节）" % (zip_path, format(os.path.getsize(zip_path), ",")))
    print("=" * 68)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
