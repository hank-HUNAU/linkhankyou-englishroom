# -*- coding: utf-8 -*-
"""试卷题库自检（通用版，任意章节可用）

八组校验：题量与编号 / 客观题格式 / 答案位置分布 / 知识点唯一 /
课后习题全覆盖 / 交付卫生 / 练习答案词落地 / 盘点与说明一致性。

用法：
  python bank_qc.py --spec spec.json
  python bank_qc.py --bank <题库.txt> [--data <chapterN_data.js>] [--explain <说明.md>]

spec.json 字段（除 bank 外均可省略，省略即用默认值/跳过相关组）：
  {
    "bank": "题库 txt 路径",
    "data": "chapterN_data.js 路径",
    "explain": "命题说明与覆盖对照.md 路径",
    "expect": {"单选题": 25, "多选题": 10, "匹配题": 1, "翻译题": 5, "作文题": 1},
    "keyword_map": {"组1-1": "先秦子学四大家", ...},
    "answer_tokens": [["组1 填空1", 4, ["Confucianism", "Legalism", "Mohism"]], ...],
    "min_essay_words": 200
  }
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_EXPECT = {"单选题": 25, "多选题": 10, "匹配题": 1, "翻译题": 5, "作文题": 1}
SINGLE, MULTI = "单选题", "多选题"
MATCH, TRANS, ESSAY = "匹配题", "翻译题", "作文题"
FIELDS = ("难易程度：", "答案解析：", "知识点：", "课程目标：")

OPT = re.compile(r"^([A-H])\.(.+)$")
HEAD = re.compile(r"^(\d+)\.(?:\{\{)?【(.+?)】(.*)$")
SUB = re.compile(r"^(\d+)\.(.+?)（）答案：([A-H])$")

OK, BAD = [], []


def chk(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print("   %s %s%s" % ("✓" if cond else "✗", name, (" " + str(detail)) if detail else ""))


def parse_bank(text):
    items, cur = [], None
    for ln in text.split("\n"):
        m = HEAD.match(ln)
        if m:
            cur = {"no": int(m.group(1)), "type": m.group(2), "stem": m.group(3),
                   "body": [], "brace": ln.startswith("%s.{{" % m.group(1))}
            items.append(cur)
        elif cur is not None and ln.strip():
            cur["body"].append(ln)
    return items


def field(it, key):
    pre = key + "："
    return next((b.split("：", 1)[1].strip() for b in it["body"] if b.startswith(pre)), None)


def options(it):
    op = {}
    for b in it["body"]:
        m = OPT.match(b)
        if m:
            op[m.group(1)] = m.group(2).strip()
    return op


def correct_text(it):
    op = options(it)
    ans = field(it, "答案") or ""
    return " ".join(op.get(a, "") for a in ans)


def load_data(p):
    t = Path(p).read_text(encoding="utf-8")
    obj, _ = json.JSONDecoder().raw_decode(t[t.find("{"):])
    return obj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec")
    ap.add_argument("--bank")
    ap.add_argument("--data")
    ap.add_argument("--explain")
    a = ap.parse_args()

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8")) if a.spec else {}
    bank_p = a.bank or spec.get("bank")
    if not bank_p:
        sys.exit("需要 --bank 或在 spec 里给 bank")
    data_p = a.data or spec.get("data")
    explain_p = a.explain or spec.get("explain")
    expect = spec.get("expect") or DEFAULT_EXPECT
    kmap = spec.get("keyword_map") or {}
    tokens = spec.get("answer_tokens") or []
    min_essay = spec.get("min_essay_words", 200)

    bank = Path(bank_p).read_text(encoding="utf-8")
    lines = bank.split("\n")
    items = parse_bank(bank)
    singles = [i for i in items if i["type"] == SINGLE]
    multis = [i for i in items if i["type"] == MULTI]
    matches = [i for i in items if i["type"] == MATCH]
    trans = [i for i in items if i["type"] == TRANS]
    essays = [i for i in items if i["type"] == ESSAY]

    print("【① 题量与题型】")
    cnt = {}
    for it in items:
        cnt[it["type"]] = cnt.get(it["type"], 0) + 1
    print("   " + " ｜ ".join("%s %d" % kv for kv in cnt.items()))
    for t, n in expect.items():
        chk("%s %d 道" % (t, n), cnt.get(t) == n, cnt.get(t))
    total = sum(expect.values())
    chk("共 %d 道" % total, len(items) == total, len(items))
    nos = [i["no"] for i in items]
    chk("编号 1—%d 连续无缺" % total, nos == list(range(1, total + 1)), nos[:6])

    print("\n【② 客观题格式】")
    for it in singles + multis:
        body = it["body"]
        op = options(it)
        ans = field(it, "答案") or ""
        idx = [j for j, b in enumerate(body) if OPT.match(b)]
        tight = bool(idx) and all(OPT.match(body[j]) for j in range(idx[0], idx[0] + len(op)))
        chk("%2d 四个选项且字母齐备" % it["no"], len(op) == 4 and set(op) == set("ABCD"), sorted(op))
        chk("%2d 选项内容互不重复" % it["no"], len(set(op.values())) == len(op))
        chk("%2d 选项之间无空行" % it["no"], tight)
        if it["type"] == SINGLE:
            chk("%2d 答案为单个字母且在选项中" % it["no"], ans in op, ans)
        else:
            chk("%2d 答案为 2—4 个字母且在选项中且升序" % it["no"],
                2 <= len(ans) <= 4 and all(c in op for c in ans) and ans == "".join(sorted(ans)), ans)
        for f in FIELDS:
            chk("%2d 含 %s" % (it["no"], f.rstrip("：")), any(b.startswith(f) for b in body))

    print("\n【③ 答案位置分布】")
    dist = {k: sum(1 for i in singles if field(i, "答案") == k) for k in "ABCD"}
    print("   单选答案分布：%s" % dist)
    chk("单选答案无位置偏向（各字母 3—8 次）", all(3 <= v <= 8 for v in dist.values()), dist)
    mcomb = sorted({field(i, "答案") or "" for i in multis})
    print("   多选答案集合：%s" % mcomb)
    chk("多选答案集合不少于 4 种", len(mcomb) >= 4, len(mcomb))

    print("\n【④ 知识点唯一性】")
    kps = [field(i, "知识点") for i in items]
    chk("每道题都有知识点", all(kps), [i["no"] for i, k in zip(items, kps) if not k])
    dup = sorted({k for k in kps if k and kps.count(k) > 1})
    chk("知识点两两不重复", not dup, dup[:3] or "%d 个各不相同" % len(kps))

    src = None
    if data_p:
        print("\n【⑤ 课后习题全覆盖】")
        try:
            src = load_data(data_p)
            ex = src["exercises"]
            g1 = [q["q"] for q in ex[0]["qs"]]
            g2 = ex[1]["table"]["rows"]
            g3 = ex[2]
            print("   组1 %d 小题 ｜ 组2 术语 %d 条 ｜ 组3 段落翻译 ｜ 组4 思辨 ｜ 组5 口语"
                  % (len(g1), len(g2)))
        except Exception as e:
            chk("读取 exercises 五组", False, repr(e))
            ex = None

        if ex:
            allkp = " ".join(k for k in kps if k)
            for k, v in kmap.items():
                chk("%s → 有对应题目（关键词「%s」）" % (k, v), v in allkp,
                    "命中题号 %s" % [i["no"] for i, kp in zip(items, kps) if kp and v in kp])

            if matches:
                mt = matches[0]
                mopts = {}
                for b in mt["body"]:
                    m = re.match(r"^([A-H])\.(.+)$", b)
                    if m:
                        mopts[m.group(1)] = m.group(2).strip()
                msub = [m for m in (SUB.match(b) for b in mt["body"]) if m]
                letters = sorted(m.group(3) for m in msub)
                chk("匹配题 %d 个小题" % len(g2), len(msub) == len(g2), len(msub))
                chk("匹配题 {{ }} 包裹", mt.get("brace") and mt["body"][-1].strip() == "}}",
                    "前缀=%s ｜ 末行=%s" % (mt.get("brace"), mt["body"][-1].strip()))
                chk("匹配题答案字母互补且各用一次", letters == sorted(mopts), letters)
                corpus2 = {r[0]: r[1] for r in g2}
                for m in msub:
                    term = m.group(2).strip()
                    got = mopts.get(m.group(3), "")
                    chk("组2「%s」英译与课后习题一致" % term,
                        term in corpus2 and got == corpus2[term],
                        "" if got == corpus2.get(term) else "稿=%s ｜ 料=%s" % (got[:40], corpus2.get(term, "无")[:40]))

            if trans and "ans" in g3:
                mine = " ".join(field(i, "答案") or "" for i in trans)
                norm = lambda s: re.sub(r"\s+", " ", s).strip()
                chk("组3 各句参考译文拼回原答案逐字一致", norm(mine) == norm(g3["ans"]),
                    "" if norm(mine) == norm(g3["ans"]) else "差在：%s" % norm(g3["ans"])[:60])
                chk("组3 每句都带中文原句",
                    all(re.search(r"[\u4e00-\u9fff]{6,}", i["stem"]) for i in trans))
                chk("组3 拆句顺序与原文一致", [i["no"] for i in trans] == sorted(i["no"] for i in trans))

            if essays:
                comp = essays[0]
                whole = comp["stem"] + "\n" + "\n".join(comp["body"])
                chk("组4 已改编为写作题（含写作要求与范文）",
                    "Write an essay" in comp["stem"] and "参考答案（范文）" in whole)
                chk("组4 含评分要点", "评分要点" in whole)
                m = re.search(r"参考答案（范文）：(.+?)难易程度", whole, re.S)
                chk("作文范文不少于 %d 词" % min_essay,
                    bool(m) and len(m.group(1).split()) >= min_essay,
                    "%d 词" % (len(m.group(1).split()) if m else 0))
    else:
        print("\n【⑤ 课后习题全覆盖】 跳过（未提供 --data）")

    print("\n【⑥ 交付卫生】")
    chk("无残留占位/待补标记", not re.search(r"TODO|待补|xxx|XXX", bank))

    if tokens:
        print("\n【⑦ 练习答案词逐项落地】")
        for name, no, toks in tokens:
            it = next((x for x in items if x["no"] == no), None)
            if not it:
                chk("%s → 第 %d 题存在" % (name, no), False, "题号缺失")
                continue
            t = correct_text(it)
            miss = [k for k in toks if k.lower() not in t.lower()]
            chk("%s → 第 %d 题正确答案落地" % (name, no), not miss,
                "缺 %s" % miss if miss else t[:52])
    else:
        print("\n【⑦ 练习答案词逐项落地】 跳过（spec 未给 answer_tokens）")

    if explain_p and Path(explain_p).exists():
        print("\n【⑧ 盘点与说明一致性】")
        dt = Path(explain_p).read_text(encoding="utf-8")
        inv = len(items)
        chk("说明文档已登记题量盘点", ("%d 道" % inv) in dt or ("共 %d" % inv) in dt)
        if src is not None:
            try:
                n_ex = (len(ex[0]["qs"]) + len(ex[1]["table"]["rows"]) + 1
                        + len(ex[3]["qs"]) + len(ex[4]["qs"]))
                chk("说明文档登记的课后习题条目数与数据一致（%d 条）" % n_ex,
                    ("%d 个条目" % n_ex) in dt or ("共 %d" % n_ex) in dt, n_ex)
            except Exception:
                pass
        chk("说明文档已登记未入卷条目", "未入卷" in dt or "未进卷" in dt)
    else:
        print("\n【⑧ 盘点与说明一致性】 跳过（未提供 --explain）")

    print("\n" + "=" * 84)
    print("通过 %d ｜ 失败 %d" % (len(OK), len(BAD)))
    for x in BAD:
        print("   ✗ %s" % x)
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
