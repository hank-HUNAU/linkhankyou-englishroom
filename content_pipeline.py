#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""content_pipeline.py —— TH!NK F 篇章内容三段流水线（对齐 → 词汇 → 译文）

把三套既有工作流串成一条按篇章调度的流水线，逐段「缺才跑、齐即跳」，
最后输出一页汇总（各阶段 OK/跳过/待办/失败 + 校验数字）。缺什么跑什么，
已完成的段落一律跳过（幂等），保证重复执行安全。

  ① 对齐  ：归档 句级数据_pXXX.json + assets/timeline.json 条目，缺则跑
            _align_unit.py --unit N --page pXXX（.venv-align 环境，U5–U12）
            U1–U4 走 _align_u14.py（整批+词级缓存，无单篇开关）
  ② 词汇  ：归档 02_词汇数据/<key>.json（九层分析）+ 词汇诊断/词汇诊断_<key>.html
            缺则跑用户级技能 article-vocab-analyzer 的 vocab_pipeline 全链（5 件套）。
            **默认不自动执行**（联网 + 有 lemma 缺陷须人工复核，见 _VOCAB_WORKFLOW.md
            §2.1 坑3），加 --do-vocab 才放行。
  ③ 译文  ：归档 01_正文篇章/译文_pXXX.json，且 R2（zh_check）/ R3（zh_r3）双门禁通过。
            R1（翻译本身）是会话内工作，脚本不代译：
            - 有批次表 _zh_tables/译文表_pXXX.json → 落库 + R2 + R3
            - 只有译文 JSON → 只复跑 R2 + R3 复检
            - 两者皆无 → 标「R1待」，不算失败
  ④ 语块  ：归档 02_词汇数据/语块_pXXX.json（每篇 3–6 条，试点 2026-10-28 起）。
            执行 = 跑 _chunk_extract.py 出候选（车道A 频率×分布×MI + 车道B 功能白名单），
            **人工审校定稿后写归档**（脚本不代选），再 _chunk_verify.py 三道校验
  ⑤ 意群  ：归档 04_意群数据/意群_pXXX.json（2026-10-31 起；句法教学单位，纯文本、零音频）。
            执行 = 跑 _yiqun_extract.py 出候选 → 人工定稿写归档 → _yiqun_verify.py 六道门禁。
            **意群与语块均不上线**：由 _gen_teacher_pack.py 生成教师讲解卡/学生发放页（本地资源）
            （verbatim 命中 / 释义完整 / 页面双写一致）。

用法：
    python content_pipeline.py --unit 5                     # 单元 4 篇：检查 + 按需执行
    python content_pipeline.py --unit 5 --page p048         # 单篇
    python content_pipeline.py --unit 5 --from vocab        # 从词汇段开始（跳过对齐）
    python content_pipeline.py --unit 5 --page p048 --force # 忽略完成态强制重跑
    python content_pipeline.py --unit 5 --page p048 --do-vocab  # 允许词汇段联网执行
    python content_pipeline.py --audit                      # 全站 49 篇体检（只检查不执行）

规约配套：_ALIGNMENT_WORKFLOW.md / _VOCAB_WORKFLOW.md / _RELEASE_WORKFLOW.md
"""
import argparse
import csv
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))                    # Think F 教材资产
TIMELINE = os.path.join(HERE, "assets", "timeline.json")
CSV_LIST = os.path.join(HERE, "reports", "正课文清单.csv")
VENV_PY = os.path.join(HERE, ".venv-align", "Scripts", "python.exe")
ALIGN_UNIT = os.path.join(HERE, "_align_unit.py")                   # U5–U12 单篇对齐
ALIGN_U14 = os.path.join(HERE, "_align_u14.py")                     # U1–U4 整批对齐
SKILL_ZH = r"C:\Users\Thinkpad\.workbuddy\skills\course-sentence-translation\scripts"
SKILL_VOCAB = r"C:\Users\Thinkpad\.workbuddy\skills\article-vocab-analyzer\scripts"
VOCAB_PIPE = os.path.join(SKILL_VOCAB, "vocab_pipeline.py")
TXT_SUBDIRS = ("篇章文本_U1_U4", "篇章文本_U5_U6", "篇章文本_U8", "篇章文本_U7_U12")
VOCAB_SUFFIX = {"_报告.json": ".json", "_报告.xlsx": ".xlsx",
                "_学生卡.xlsx": "_学生卡.xlsx", "_备课本.xlsx": "_备课本.xlsx",
                "_语音卡.xlsx": "_语音卡.xlsx"}
PY = sys.executable


# ---------------------------------------------------------------- 清单
def load_catalog():
    """正课文清单（canonical，CSV 为准）：[(unit, page, 板块, 篇名, 状态)]
    只取 类型=正课文（48 篇）；单元开篇/Grammar Rap/文学/p202 深链等「非正文」行
    不在流水线调度范围。"""
    rows = []
    with open(CSV_LIST, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["类型"].strip() != "正课文":
                continue
            rows.append(dict(unit=int(r["单元"].lstrip("Uu")),
                             page=r["页码"].strip(),
                             kind=r["板块"].strip(),
                             title=r["篇名"].strip(),
                             csv_sent=int(r["句数"]) if r["句数"].strip().isdigit() else None,
                             status=r["状态"].strip()))
    return rows


def unit_dir(unit):
    hits = sorted(glob.glob(os.path.join(BASE, "U%d_*" % unit)))
    return hits[0] if hits else None


# ---------------------------------------------------------------- 阶段① 对齐
def check_align(c):
    """返回 (done: bool, detail: str)"""
    ud = unit_dir(c["unit"])
    arc = os.path.join(ud, "01_正文篇章", "句级数据_%s.json" % c["page"]) if ud else None
    if not arc or not os.path.exists(arc):
        return False, "缺归档 句级数据_%s.json" % c["page"]
    tl = json.load(open(TIMELINE, encoding="utf-8"))
    if c["page"] not in tl:
        return False, "归档在库，timeline.json 无 %s 条目" % c["page"]
    d = json.load(open(arc, encoding="utf-8"))
    n_arc, n_tl = len(d.get("sentences", [])), len(tl[c["page"]])
    if n_arc != n_tl:
        return False, "句数漂移：归档 %d vs timeline %d" % (n_arc, n_tl)
    return True, "OK %d 句（归档=timeline）" % n_tl


def run_align(c):
    if c["unit"] <= 4:
        print("  ⚠ U1–U4 对齐脚本 _align_u14.py 无单篇开关，整批重跑（词级缓存命中，ASR 不重算）")
        cmd = [VENV_PY, ALIGN_U14]
    else:
        cmd = [VENV_PY, ALIGN_UNIT, "--unit", str(c["unit"]), "--page", c["page"]]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (r.stdout or "").strip().splitlines()
    for line in tail[-3:]:
        print("    | " + line[:120])
    if r.returncode:
        print("    | stderr: " + (r.stderr or "")[-200:].replace("\n", " "))
    return r.returncode == 0


# ---------------------------------------------------------------- 阶段② 词汇
def vocab_key(c):
    """篇章词汇 key（u5_p048_robotics_club 式）。
    优先取归档句级数据的 passage_key（U1–U4 新 schema 有）；
    U5–U12 旧 schema 无此字段 → 回退到 02_词汇数据 九层 JSON 文件名反推
    （兼容 p 补零 u4_p042_shop 与不补零 u2_p20_messages 两种命名）。"""
    ud = unit_dir(c["unit"])
    arc = os.path.join(ud, "01_正文篇章", "句级数据_%s.json" % c["page"]) if ud else None
    if arc and os.path.exists(arc):
        k = json.load(open(arc, encoding="utf-8")).get("passage_key")
        if k:
            return k
    digits = c["page"].lstrip("pP")
    pat = re.compile(r"^u%d_p0*%s_.+$" % (c["unit"], digits))
    for f in sorted(glob.glob(os.path.join(ud or "", "02_词汇数据", "*.json"))):
        stem = os.path.splitext(os.path.basename(f))[0]
        if pat.match(stem):
            return stem
    return None


def check_vocab(c):
    key = vocab_key(c)
    if not key:
        return False, None, "无归档句级数据，取不到词汇 key（先跑对齐）"
    vd = os.path.join(unit_dir(c["unit"]), "02_词汇数据")
    five = [s for s in VOCAB_SUFFIX.values() if os.path.exists(os.path.join(vd, key + s))]
    dis = os.path.join(HERE, "词汇诊断", "词汇诊断_%s.html" % key)
    have_json = os.path.exists(os.path.join(vd, key + ".json"))
    have_dis = os.path.exists(dis)
    detail = "%s %d/5 诊断页%s" % (key, len(five), "✓" if have_dis else "✗")
    if have_json and have_dis:
        return True, len(five), detail
    miss = []
    if not have_json:
        miss.append("九层JSON")
    if not have_dis:
        miss.append("诊断页")
    return False, len(five), "缺 %s（%s）" % ("/".join(miss), detail)


def run_vocab(c):
    """vocab_pipeline 全链 → 5 件套归档（须 --do-vocab；产出后须人工复核 lemma）"""
    key = vocab_key(c)
    txt = find_passage_text(c["page"])
    if not key or not txt:
        print("  ✗ 词汇执行缺前置：key=%s 课文txt=%s" % (key or "无", txt or "无"))
        return False
    tmp = os.path.join(HERE, "_vocab_out_tmp")
    os.makedirs(tmp, exist_ok=True)
    r = subprocess.run([PY, VOCAB_PIPE, txt, "--out", key], cwd=tmp,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print("  ✗ vocab_pipeline rc=%d\n    %s" % (r.returncode, (r.stderr or r.stdout)[-300:]))
        return False
    dst_dir = os.path.join(unit_dir(c["unit"]), "02_词汇数据")
    os.makedirs(dst_dir, exist_ok=True)
    missing = []
    for suf, dst in VOCAB_SUFFIX.items():
        src = os.path.join(tmp, key + suf)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst_dir, key + dst))
        else:
            missing.append(suf)
    # 诊断页
    r2 = subprocess.run([PY, os.path.join(HERE, "_gen_vqdis.py"), key],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    if missing or r2.returncode:
        print("  ✗ 5 件套缺 %s；诊断页 rc=%d" % (missing or "无", r2.returncode))
        return False
    print("  ✓ 5 件套 + 诊断页归档（%s）→ 务必人工复核 lemma 缺陷" % key)
    return True


def find_passage_text(page):
    """按 _gen_vqdis.text_of 同款规则找课文 txt（p 补零/不补零两命名都试）"""
    digits = page.lstrip("pP")
    cands = [page, "p" + digits, "p%03d" % int(digits)] if digits.isdigit() else [digits]
    seen, ordered = set(), []
    for x in cands:
        if x not in seen:
            seen.add(x); ordered.append(x)
    for sub in TXT_SUBDIRS:
        for cand in ordered:
            hits = glob.glob(os.path.join(HERE, "词汇诊断", sub, "*" + cand + "*.txt"))
            if hits:
                return hits[0]
    return None


# ---------------------------------------------------------------- 阶段③ 译文
def page_html(c):
    num = c["page"].lstrip("pP")
    hits = glob.glob(os.path.join(HERE, "篇章页", "读写_%s_*.html" % num))
    return hits[0] if hits else None


def check_zh(c):
    """译文 JSON 在库 + 条目数与句级数据对账 + R2/R3 双门禁"""
    ud = unit_dir(c["unit"])
    arc = os.path.join(ud, "01_正文篇章", "译文_%s.json" % c["page"]) if ud else None
    if not arc or not os.path.exists(arc):
        return None, "无译文 JSON（R1待，会话内翻译）"
    sent_arc = os.path.join(ud, "01_正文篇章", "句级数据_%s.json" % c["page"])
    n_sent = None
    if os.path.exists(sent_arc):
        n_sent = len(json.load(open(sent_arc, encoding="utf-8")).get("sentences", []))
    d = json.load(open(arc, encoding="utf-8"))
    n_en = len(d.get("entries", d.get("zh", [])))
    drift = "" if (n_sent is None or n_en == n_sent) else " ⚠句数漂移 %d≠%d" % (n_en, n_sent)
    html = page_html(c)
    if not html:
        return None, "译文在库（%d 句%s）但找不到篇章页，无法跑 R2/R3" % (n_en, drift)
    r2 = subprocess.run([PY, os.path.join(SKILL_ZH, "zh_check.py"), "--page", html, "--json", arc],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    r3 = subprocess.run([PY, os.path.join(SKILL_ZH, "zh_r3.py"), "--page", html],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok2 = "结论：通过" in (r2.stdout or "")
    ok3 = r3.returncode == 0
    if ok2 and ok3:
        return True, "OK %d 句 R2✓ R3✓%s" % (n_en, drift)
    return False, "R2%s R3%s（%d 句%s）" % ("✓" if ok2 else "✗", "✓" if ok3 else "疑点", n_en, drift)


def run_zh(c):
    """有批次表则落库+双门禁；否则只复跑双门禁。"""
    html = page_html(c)
    if not html:
        print("  ✗ 找不到篇章页"); return False
    tbl = os.path.join(HERE, "_zh_tables", "译文表_%s.json" % c["page"])
    ud = unit_dir(c["unit"])
    arc = os.path.join(ud, "01_正文篇章", "译文_%s.json" % c["page"])
    if os.path.exists(tbl):
        r = subprocess.run([PY, os.path.join(SKILL_ZH, "zh_apply.py"), "--page", html,
                            "--src", tbl, "--out", arc],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print("  ✗ zh_apply 失败：%s" % (r.stderr or r.stdout)[-200:]); return False
        print("  ✓ 已从批次表落库")
    r2 = subprocess.run([PY, os.path.join(SKILL_ZH, "zh_check.py"), "--page", html, "--json", arc],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    r3 = subprocess.run([PY, os.path.join(SKILL_ZH, "zh_r3.py"), "--page", html],
                        capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok2, ok3 = "结论：通过" in (r2.stdout or ""), r3.returncode == 0
    if not ok2:
        for line in (r2.stdout or "").splitlines():
            if line.startswith(("FAIL", "R2-")):
                print("    | " + line[:110])
    if not ok3:
        for line in (r3.stdout or "").splitlines()[1:4]:
            print("    | " + line[:110])
    print("  %s R2 %s · R3 %s" % ("✓" if (ok2 and ok3) else "✗",
                                  "通过" if ok2 else "FAIL", "通过" if ok3 else "疑点"))
    return ok2 and ok3


# ---------------------------------------------------------------- 阶段④ 语块
def check_chunk(c):
    """归档语块 JSON 在库 + 三道校验（verbatim/释义/双写）"""
    arc = os.path.join(unit_dir(c["unit"]), "02_词汇数据", "语块_%s.json" % c["page"])
    if not os.path.exists(arc):
        return False, "无语块 JSON（先跑候选提取 + 人工审校）"
    r = subprocess.run([PY, os.path.join(HERE, "_chunk_verify.py"), "--page", c["page"]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    n = len(json.load(open(arc, encoding="utf-8")).get("chunks", []))
    if r.returncode == 0:
        return True, "OK %d 条（三道校验过）" % n
    return False, "%d 条但校验失败" % n


def run_chunk(c):
    """产出候选供人工审校（不代选、不落归档）"""
    out = os.path.join(HERE, "_chunk_cand_%s.json" % c["page"])
    r = subprocess.run([PY, os.path.join(HERE, "_chunk_extract.py"),
                        "--page", c["page"], "--json", out],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout or "")[-600:])
    if r.returncode == 0 and os.path.exists(out):
        print("  ✓ 候选已写入 %s → 人工审校选 3–6 条写 语块_%s.json（归档 02_词汇数据）→ _chunk_verify.py"
              % (os.path.basename(out), c["page"]))
        print("    提醒：语块不上线（2026-10-31 定案）——审校定稿后跑 _gen_teacher_pack.py --page %s 生成教师卡/学生页"
              % c["page"])
        return True
    print("  ✗ 候选提取失败：%s" % (r.stderr or r.stdout)[-200:])
    return False


# ---------------------------------------------------------------- 阶段⑤ 意群
def check_yiqun(c):
    """归档意群 JSON 在库 + 六道门禁（源句/拼接/覆盖/段数/标注/教学点）"""
    arc = os.path.join(unit_dir(c["unit"]), "04_意群数据", "意群_%s.json" % c["page"])
    if not os.path.exists(arc):
        return False, "无意群 JSON（先跑 _yiqun_extract.py + 人工定稿）"
    r = subprocess.run([PY, os.path.join(HERE, "_yiqun_verify.py"), "--page", c["page"]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode not in (0, 2):  # 2 = 仅段数告警，放行
        return False, "意群门禁未过：%s" % ((r.stdout or r.stderr or "")[-120:].replace("\n", " "))
    return True, "OK"


def run_yiqun(c):
    """产出意群候选供人工定稿（不代切、不落归档）"""
    r = subprocess.run([PY, os.path.join(HERE, "_yiqun_extract.py"), "--page", c["page"]],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print((r.stdout or "")[-600:])
    if r.returncode == 0:
        print("  ✓ 候选已打印 → 人工按句法定稿写 04_意群数据/意群_%s.json → _yiqun_verify.py" % c["page"])
        print("    提醒：意群不上线（2026-10-31 定案）——定稿后跑 _gen_teacher_pack.py --page %s 生成教师卡/学生页"
              % c["page"])
        return True
    print("  ✗ 候选提取失败：%s" % (r.stderr or r.stdout)[-200:])
    return False


# ---------------------------------------------------------------- 主流程
STAGES = ["align", "vocab", "zh", "chunk", "yiqun"]
STAGE_CN = {"align": "对齐", "vocab": "词汇", "zh": "译文", "chunk": "语块", "yiqun": "意群"}


def process(c, args, results):
    print("\n== U%d %s %s（%s）==" % (c["unit"], c["page"], c["title"], c["kind"]))
    row = dict(unit=c["unit"], page=c["page"], title=c["title"])
    start = STAGES.index(args["from_stage"])
    for si, st in enumerate(STAGES):
        tag = "%s·%s" % (STAGE_CN[st], st)
        if si < start:
            row[st] = "跳过(--from)"
            continue
        if st == "align":
            done, detail = check_align(c)
        elif st == "vocab":
            done, five, detail = check_vocab(c)
            row["five"] = five
        elif st == "chunk":
            done, detail = check_chunk(c)
        elif st == "yiqun":
            done, detail = check_yiqun(c)
        else:
            done, detail = check_zh(c)
        if done and not args["force"]:
            row[st] = "OK·跳"
            print("  [%s] 已完成，跳过｜%s" % (tag, detail))
            continue
        if st == "zh" and done is None:
            # 无译文：有批次表可落库，否则 R1 待办
            if os.path.exists(os.path.join(HERE, "_zh_tables", "译文表_%s.json" % c["page"])):
                ok = run_zh(c)
                row[st] = "落库+" + ("OK" if ok else "FAIL")
            else:
                row[st] = "R1待"
                print("  [%s] %s" % (tag, detail))
            continue
        # 需要执行
        print("  [%s] %s｜%s" % (tag, "已完成，--force 强制重跑" if done else "未完成", detail))
        if st == "vocab" and not args["do_vocab"]:
            row[st] = "待执行(--do-vocab)"
            print("      联网执行须加 --do-vocab（跑完须人工复核 lemma）；确认后重跑")
            continue
        print("  [%s] 执行中…" % tag)
        ok = {"align": run_align, "vocab": run_vocab, "zh": run_zh,
              "chunk": run_chunk, "yiqun": run_yiqun}[st](c)
        row[st] = ("执行" + ("OK" if ok else "FAIL"))
        if not ok and not args["keep_going"]:
            row["_abort"] = True
            results.append(row)
            return
    results.append(row)


def audit(catalog, results):
    """全站体检：只检查不执行、不问网络。"""
    print("全站体检（%d 篇，只检查不执行）\n" % len(catalog))
    print("%-4s %-6s %-22s %-8s %-8s %-14s %-6s %-6s %s" % (
        "单元", "页", "key/篇名", "对齐", "词汇", "译文", "语块", "意群", "备注"))
    stats = {k: 0 for k in ("align_ok", "vocab_ok", "zh_ok", "chunk_ok", "yiqun_ok", "zh_r1")}
    for c in catalog:
        a_ok, a_det = check_align(c)
        v_ok, five, v_det = check_vocab(c)
        z_ok, z_det = check_zh(c)
        k_ok, k_det = check_chunk(c)
        y_ok, y_det = check_yiqun(c)
        key = vocab_key(c) or c["title"][:14]
        def m(x): return "✓" if x else ("—" if x is None else "✗")
        note = []
        if not a_ok: note.append(a_det)
        if not v_ok: note.append(v_det)
        if z_ok is None: note.append(z_det); stats["zh_r1"] += 1
        stats["align_ok"] += bool(a_ok)
        stats["vocab_ok"] += bool(v_ok)
        stats["zh_ok"] += bool(z_ok)
        stats["chunk_ok"] += bool(k_ok)
        stats["yiqun_ok"] += bool(y_ok)
        print("%-4d %-6s %-22s %-8s %-8s %-14s %-6s %-6s %s" % (
            c["unit"], c["page"], key[:22], m(a_ok),
            ("✓" if v_ok else "✗") + ("(%s/5)" % five if five is not None else ""),
            m(z_ok), m(k_ok), m(y_ok), "；".join(note)[:60]))
        results.append(dict(unit=c["unit"], page=c["page"], title=c["title"],
                            align="OK·跳" if a_ok else "缺", vocab="OK·跳" if v_ok else "缺",
                            zh=("OK·跳" if z_ok else ("R1待" if z_ok is None else "缺")),
                            chunk="OK·跳" if k_ok else "缺",
                            yiqun="OK·跳" if y_ok else "缺"))
    print("\n汇总：对齐 %d/%d · 词汇 %d/%d · 译文 %d/%d（另有 %d 篇 R1待）· 语块 %d/%d · 意群 %d/%d" % (
        stats["align_ok"], len(catalog), stats["vocab_ok"], len(catalog),
        stats["zh_ok"], len(catalog), stats["zh_r1"], stats["chunk_ok"], len(catalog),
        stats["yiqun_ok"], len(catalog)))


def main():
    ap = argparse.ArgumentParser(description="TH!NK F 篇章内容三段流水线（对齐→词汇→译文）")
    ap.add_argument("--unit", type=int, help="单元号 1–12")
    ap.add_argument("--page", help="页号 p048 式（缺省=该单元全部）")
    ap.add_argument("--from", dest="from_stage", choices=STAGES, default="align",
                    help="起始阶段（跳过之前的阶段）")
    ap.add_argument("--force", action="store_true", help="已完成也强制重跑")
    ap.add_argument("--do-vocab", action="store_true",
                    help="允许词汇段联网执行 vocab_pipeline（跑完须人工复核 lemma）")
    ap.add_argument("--keep-going", action="store_true", help="某篇失败后继续下一篇（默认 fail-fast）")
    ap.add_argument("--audit", action="store_true", help="全站 49 篇体检（只检查不执行）")
    args = vars(ap.parse_args())

    catalog = load_catalog()
    results = []
    if args["audit"]:
        audit(catalog, results)
    else:
        if not args["unit"]:
            ap.error("缺 --unit N（或用 --audit 全站体检）")
        sel = [c for c in catalog if c["unit"] == args["unit"]]
        if args["page"]:
            sel = [c for c in sel if c["page"] == args["page"]]
        if not sel:
            sys.exit("✗ 清单里找不到 U%d%s" % (args["unit"], " " + args["page"] if args["page"] else ""))
        flags = ("｜force" if args["force"] else "") + ("｜do-vocab" if args["do_vocab"] else "")
        print("流水线：对齐 → 词汇 → 译文｜%d 篇｜起始=%s%s" % (len(sel), args["from_stage"], flags))
        for c in sel:
            process(c, args, results)

    # 一页汇总
    print("\n" + "=" * 72)
    print("%-4s %-6s %-24s %-10s %-12s %-12s %-8s" % ("单元", "页", "篇名", "对齐", "词汇", "译文", "语块"))
    n_fail = 0
    for r in results:
        if r.get("_abort"):
            n_fail += 1
        print("%-4d %-6s %-24s %-10s %-12s %-12s %-8s" % (
            r["unit"], r["page"], (r["title"] or "")[:24],
            r.get("align", "-"), r.get("vocab", "-"), r.get("zh", "-"), r.get("chunk", "-")))
    print("=" * 72)
    if n_fail:
        print("✗ %d 篇中途失败（fail-fast 中止）" % n_fail)
        sys.exit(1)
    print("完成。")


if __name__ == "__main__":
    main()
