# -*- coding: utf-8 -*-
"""TH!NK F 48 篇「语块 / 意群」机器候选层批量产出器（2026-11-15）

背景：#51 规约合并判定后（见 reports/语块意群规约合并判定_NCE2技能比对_2026-11-15.md），
吸收 NCE2「句法-语块积木」技能的**流程工程化方法**（P1 状态机 / P2 草案不填中文 /
P3 PASS≠正确），为全站 48 篇产出可批量、可机检、可复现的**机器候选层**。

硬边界（不可绕过）：
1. 只出 `auto` / `pending` 草案层，**绝不写中文**（意群 groups 只有 t，无 fn/zh/point）；
2. **不进归档正典**（不改 Ux_*/02_词汇数据/语块_pXXX.json、04_意群数据/意群_pXXX.json）；
3. **不上线、不碰音频、不碰 timeline、不改站点页面**；
4. 产物只落分支目录 `Think 0_分支项目/语块意群_48篇候选/`，**不入库 git**（技能 §9 目录规约）；
5. 算法单一真相源：直接调用既有权威 CLI `_chunk_extract.py --page` / `_yiqun_extract.py --page`，
   **不复制、不改写**候选逻辑，避免两份代码漂移。

用法：
  python _gen_candidate_pack.py                    # 全 48 篇
  python _gen_candidate_pack.py --pages p048,p052  # 指定篇（调试）
  python _gen_candidate_pack.py --no-write         # 只算不写
"""
from __future__ import unicode_literals

import argparse
import csv
import datetime
import glob
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(WS, "Think 0_分支项目", "语块意群_48篇候选")
sys.path.insert(0, HERE)
import _chunk_extract as ce  # noqa: E402  （只用于取 48 篇页清单，不改其算法）

PY = sys.executable
WS_NORM = lambda s: re.sub(r"\s+", " ", s).strip()  # noqa: E731


def page_list():
    """48 篇正课文，顺序与 _chunk_extract.load_corpus() 一致"""
    return [p for (_u, p) in sorted(ce.load_corpus().keys(), key=lambda k: (k[0], str(k[1])))]


def run_cli(script, page, json_path):
    """调用既有权威候选器，产物写 json_path；stdout/stderr 全部捕获不打印"""
    cmd = [PY, os.path.join(HERE, script), "--page", page, "--json", json_path]
    r = subprocess.run(cmd, cwd=HERE, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    if r.returncode != 0 or not os.path.isfile(json_path):
        raise RuntimeError("%s %s 失败(rc=%s): %s" % (
            script, page, r.returncode, (r.stderr or r.stdout or "")[-400:]))
    return json.load(io.open(json_path, "r", encoding="utf-8"))


def build_yiqun(page, raw):
    """把候选器输出重组成 P1/P2 合规的草案：groups 只有 t，无 fn/zh/point"""
    rows = []
    n_groups = 0
    restore_bad = []
    for c in raw.get("candidates", []):
        groups = [{"t": g} for g in c.get("cand", []) if g]
        n_groups += len(groups)
        joined = WS_NORM(" ".join(g["t"] for g in groups))
        src = WS_NORM(c.get("text", ""))
        if joined != src:
            restore_bad.append({"i": c.get("i"), "text": src, "joined": joined})
        rows.append({"i": c.get("i"), "text": c.get("text"), "groups": groups})
    return {
        "page": page,
        "cutSource": "auto",
        "reviewStatus": "pending",
        "level": "草案层（非正典）",
        "note": "P2：机器草案不填中文；fn/zh/point 须人工按译文_pXXX.json 逐句定稿后才可进归档",
        "n_sent": len(rows),
        "n_groups": n_groups,
        "sentences": rows,
    }, restore_bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default=None, help="逗号分隔页号，默认全 48 篇")
    ap.add_argument("--no-write", action="store_true")
    args = ap.parse_args()

    pages = page_list()
    if args.pages:
        want = set(x.strip() for x in args.pages.split(",") if x.strip())
        pages = [p for p in pages if p in want]
        if not pages:
            sys.exit("✗ --pages 未命中任何正课文")
    print("目标篇章：%d 篇" % len(pages))

    tmp = os.path.join(OUT, "_tmp")
    if not args.no_write and not os.path.isdir(tmp):
        os.makedirs(tmp)

    chunk_rows, yiqun_rows, summary = [], [], []
    total_bad = 0
    corpus_tokens = None

    for idx, page in enumerate(pages, 1):
        cj = os.path.join(tmp, "chunk_%s.json" % page)
        yj = os.path.join(tmp, "yiqun_%s.json" % page)
        craw = run_cli("_chunk_extract.py", page, cj) if not args.no_write else {}
        yraw = run_cli("_yiqun_extract.py", page, yj) if not args.no_write else {}
        if args.no_write:
            print("  [%02d/%02d] %s （--no-write，跳过 CLI）" % (idx, len(pages), page))
            continue

        if corpus_tokens is None:
            corpus_tokens = craw.get("corpus", {}).get("tokens")

        # 语块草案
        cd = {
            "page": page,
            "unit": craw.get("unit"),
            "key": craw.get("key"),
            "cutSource": "auto",
            "reviewStatus": "pending",
            "level": "草案层（非正典）",
            "corpus": craw.get("corpus"),
            "n_candidates": len(craw.get("candidates", [])),
            "note": "P2：候选不含 zh/exZh；人工审选定稿 3–6 条后才可写 02_词汇数据/语块_pXXX.json",
            "candidates": craw.get("candidates", []),
        }
        for rank, r in enumerate(craw.get("candidates", []), 1):
            chunk_rows.append({
                "page": page, "rank": rank, "ngram": r.get("ngram"), "n": r.get("n"),
                "freq": r.get("freq"), "disp": r.get("disp"), "units": r.get("units"),
                "mi": r.get("mi"), "type": r.get("type"),
                "hits": ",".join(map(str, r.get("hits", []))),
            })

        # 意群草案
        yd, bad = build_yiqun(page, yraw)
        total_bad += len(bad)
        for s in yd["sentences"]:
            yiqun_rows.append({
                "page": page, "i": s["i"], "n_groups": len(s["groups"]),
                "text": s["text"],
                "groups": " | ".join(g["t"] for g in s["groups"]),
                "restore_ok": 1 if WS_NORM(" ".join(g["t"] for g in s["groups"])) == WS_NORM(s["text"]) else 0,
            })

        if not args.no_write:
            d1 = os.path.join(OUT, "语块候选", "逐篇")
            d2 = os.path.join(OUT, "意群候选", "逐篇")
            for d in (d1, d2):
                if not os.path.isdir(d):
                    os.makedirs(d)
            json.dump(cd, io.open(os.path.join(d1, page + ".json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            json.dump(yd, io.open(os.path.join(d2, page + ".json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

        summary.append({
            "page": page,
            "语块候选": cd["n_candidates"],
            "意群句数": yd["n_sent"],
            "意群段数": yd["n_groups"],
            "均段每句": round(yd["n_groups"] / max(1, yd["n_sent"]), 2),
            "拼接不一致": len(bad),
        })
        print("  [%02d/%02d] %s  语块 %2d 条 / 意群 %2d 句 %3d 段 / 拼接不一致 %d" % (
            idx, len(pages), page, cd["n_candidates"], yd["n_sent"], yd["n_groups"], len(bad)))

        os.remove(cj)
        os.remove(yj)

    if args.no_write:
        return 0
    try:
        os.rmdir(tmp)
    except OSError:
        pass

    # ---- 汇总 CSV ----
    with io.open(os.path.join(OUT, "语块候选", "全站_逐篇候选.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["page", "rank", "ngram", "n", "freq", "disp",
                                          "units", "mi", "type", "hits"])
        w.writeheader()
        w.writerows(chunk_rows)
    with io.open(os.path.join(OUT, "意群候选", "全站_逐句候选.csv"), "w",
                 encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["page", "i", "n_groups", "text", "groups", "restore_ok"])
        w.writeheader()
        w.writerows(yiqun_rows)

    # ---- 核验结果 JSON ----
    total_sent = sum(r["意群句数"] for r in summary)
    total_group = sum(r["意群段数"] for r in summary)
    total_chunk = sum(r["语块候选"] for r in summary)
    restore_ok = sum(x["restore_ok"] for x in yiqun_rows)
    result = {
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "corpus": {"passages": len(summary), "tokens": corpus_tokens, "sentences": total_sent},
        "levels": {"cutSource": "auto", "reviewStatus": "pending"},
        "counts": {
            "语块候选条数": total_chunk,
            "意群句数": total_sent,
            "意群段数": total_group,
            "均段每句": round(total_group / max(1, total_sent), 2),
        },
        "check_G2_拼接还原": {"ok": restore_ok, "total": total_sent,
                             "bad": total_sent - restore_ok,
                             "pass": total_bad == 0},
        "per_page": summary,
        "boundary": "PASS≠正确：拼接还原只证明形式合法，不证明句法切分或教学判断正确。",
    }
    json.dump(result, io.open(os.path.join(OUT, "核验结果.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ---- 核验报告 ----
    lines = [
        "# 48 篇语块 / 意群机器候选层 · 核验报告", "",
        "> 生成：%s　|　生成器：`github在线推送/_gen_candidate_pack.py`（可复现）" % result["generated_at"],
        "> 语料：**%d 篇 / %d 句 / %s 词**（p052 方案 A 后现行口径）" % (
            len(summary), total_sent, format(corpus_tokens or 0, ",")),
        "> 层级：`cutSource=auto` / `reviewStatus=pending` —— **草案层，非正典**", "",
        "## 一、汇总", "",
        "| 指标 | 值 |", "|---|---:|",
        "| 篇章 | %d |" % len(summary),
        "| 语块候选条数 | %d |" % total_chunk,
        "| 意群句数 | %d |" % total_sent,
        "| 意群段数 | %d |" % total_group,
        "| 均段每句 | %.2f |" % (total_group / max(1, total_sent)),
        "| G2 拼接还原 OK | %d / %d（不一致 %d） |" % (restore_ok, total_sent, total_sent - restore_ok), "",
        "## 二、逐篇", "",
        "| 篇 | 语块候选 | 意群句数 | 意群段数 | 均段每句 | 拼接不一致 |", "|---|---:|---:|---:|---:|---:|",
    ]
    for r in summary:
        lines.append("| %s | %d | %d | %d | %.2f | %d |" % (
            r["page"], r["语块候选"], r["意群句数"], r["意群段数"], r["均段每句"], r["拼接不一致"]))
    lines += [
        "", "## 三、硬边界（随产出留痕）", "",
        "1. **P2 草案不填中文**：意群 `groups` 只有 `t`，没有 `fn` / `zh` / `point`；语块候选没有 `zh` / `exZh`。",
        "2. **不进归档正典**：`Ux_*/02_词汇数据/语块_pXXX.json`、`04_意群数据/意群_pXXX.json` 一字未改（仍各仅 p048 一篇）。",
        "3. **不上线 / 不碰音频 / 不碰 timeline / 不改站点页面**；产物只落本分支目录，不入库 git。",
        "4. **不换轨**：本候选层沿用 TH!NK F「意群＝句法教学单位」构念，**不是** NCE2 的 Quirk 七型句法积木；",
        "   技能可执行入口 `run_full.py` 未被调用（产物目录硬约束 + spaCy 标注层缺失），属借鉴方法原则。",
        "5. **PASS ≠ 正确**：G2 拼接还原只证明「段能拼回原句、切点落词边界」，",
        "   不证明句法功能判得对、切分符合教学需要。人工定稿（`revised`）仍是正典唯一入口。",
        "6. **算法单一真相源**：逐篇候选由既有权威 CLI `_chunk_extract.py --page` / `_yiqun_extract.py --page` 产出，",
        "   本脚本只做重组、状态标记、汇总与机检，**未复制或改写任何候选算法**。", "",
        "## 四、下一步（需用户发令）", "",
        "- 语块：从 `语块候选/逐篇/pXXX.json` 人工审选 3–6 条 → 写归档正典（带 `zh`/`exZh`）。",
        "- 意群：从 `意群候选/逐篇/pXXX.json` 人工按句法合并/拆分 + 填 `fn`/`zh`/`point` → `_yiqun_verify.py` 六门禁 → 归档。",
        "- 条数方案 A/B/C 待拍板；**不存在一键批量产出正典的合规路径**。", "",
    ]
    io.open(os.path.join(OUT, "核验报告.md"), "w", encoding="utf-8", newline="").write("\n".join(lines))

    # ---- 入口 README ----
    readme = u"""# Think 0 · 语块 / 意群机器候选层（48 篇）

> 用户所称「用 nce2-syntax-chunk-blocks 处理 think 0 的语块与意群」的**数据层交付**。
> 规约层交付见 `github在线推送/reports/语块意群规约合并判定_NCE2技能比对_2026-11-15.md`。
> 生成：%s

## 这是什么

按 #51 合并判定吸收的三条方法原则，为全站 48 篇产出**可批量、可机检、可复现的机器候选层**：

| 原则 | 本包如何体现 |
|---|---|
| P1 状态机 | 每个 JSON 顶层 `cutSource=auto` / `reviewStatus=pending` / `level=草案层（非正典）` |
| P2 草案不填中文 | 意群 `groups` 只有 `t`；语块候选只有统计字段，无 `zh` / `exZh` |
| P3 PASS≠正确 | `核验报告.md` 第三条硬边界明示「拼接还原 ≠ 切分正确」 |

**不是正典**：归档 `Ux_*/02_词汇数据/语块_pXXX.json`、`04_意群数据/意群_pXXX.json` 一字未改，仍各仅 p048 一篇定稿。

## 目录

```
语块候选/逐篇/pXXX.json        48 个，逐篇候选（含 freq/disp/units/MI/hits/type）
语块候选/全站_逐篇候选.csv      汇总 %d 行
意群候选/逐篇/pXXX.json        48 个，逐句机器切分（groups 只有 t）
意群候选/全站_逐句候选.csv      汇总 %d 行（含 restore_ok 列）
核验报告.md                    汇总 + 逐篇 + 六条硬边界
核验结果.json                  机读结果
```

## 关键数字

语料 **%d 篇 / %d 句 / %s 词**；语块候选 **%d 条**；意群 **%d 段**（均 %.2f 段每句）；
G2 拼接还原 **%d / %d**%s。

## 边界（必须随包带走）

1. 产物只落本分支目录，**不入库 git、不上线、不碰音频 / timeline / 站点页面**。
2. 沿用 TH!NK F「意群＝句法教学单位」构念，**不是** NCE2 的 Quirk 七型句法积木；技能 `run_full.py` 未调用。
3. 候选算法来自既有权威 CLI `_chunk_extract.py` / `_yiqun_extract.py`，本包未复制算法。
4. **人工定稿（`revised`）是正典唯一入口**；不存在一键批量产出正典的合规路径。
""" % (result["generated_at"], len(chunk_rows), len(yiqun_rows),
       len(summary), total_sent, format(corpus_tokens or 0, ","),
       total_chunk, total_group, total_group / max(1, total_sent),
       restore_ok, total_sent,
       "" if total_bad == 0 else "（**不一致 %d，见核验报告**）" % total_bad)
    io.open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="").write(readme)

    print("=" * 68)
    print("候选层完成：%s" % OUT)
    print("语块 %d 条 / 意群 %d 句 %d 段 / G2 还原 %d/%d / 不一致 %d" % (
        total_chunk, total_sent, total_group, restore_ok, total_sent, total_bad))
    print("=" * 68)
    return 0 if total_bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
