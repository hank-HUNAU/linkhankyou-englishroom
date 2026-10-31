# -*- coding: utf-8 -*-
"""意群（thought groups）候选切分器 —— 句法规则版（本地教师资源用，非上线）

用法：
  python _yiqun_extract.py --page p048
  python _yiqun_extract.py --page p048 --json _yiqun_cand_p048.json

设计口径（用户 2026-10-31 拍板）：
  意群 = **句法教学单位**（主语群/谓语群/宾语群/状语群/从句），
  不是停顿提示，**不碰音频**（零音频依赖）。
  脚本只出候选，**人工审校才是定稿唯一入口**（同语块轨，参见 _CHUNK_WORKFLOW.md）。

规则（启发式，按优先级）：
  R1 逗号 / 破折号 / 分号 / 冒号 后切
  R2 并列连词 and/but/or/so 前切（若前面不是逗号已切）
  R3 从属连词 when/because/if/after/before/while/that 前切
  R4 关系代词 who/which/that 前切（有限支持）
  R5 过长的段（>=8 词）在介词短语前二次切（in/on/at/for/to/with/from）
已知局限：不做完整句法分析，候选常需人工合并/拆分——这是设计如此，不是缺陷。
"""
import argparse
import json
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

CUT_AFTER = re.compile(r'(?<=[,;:–—])\s+')
CONJ = re.compile(r'\b(and|but|or|so)\b', re.I)
SUBCONJ = re.compile(r'\b(when|because|if|after|before|while|although|though|that|unless|since)\b', re.I)
PREP = re.compile(r'\b(in|on|at|for|to|with|from|of|about)\b', re.I)

# 「so」作连词时后面通常接小句主语；否则（so many/so much）是限定词，不是连词
CLAUSE_SUBJ = set('i we you they he she it the this that there these those everybody everyone someone'.split())


def find_sentences(page):
    """从归档句级数据读句；找不到则报错（不猜路径）。"""
    digits = re.sub(r'\D', '', page)
    # 归档位置：U*/01_正文篇章/句级数据_pXXX.json
    for root, dirs, files in os.walk(os.path.join(HERE, '..')):
        for f in files:
            if f == '句级数据_p%s.json' % digits:
                with io.open(os.path.join(root, f), encoding='utf-8') as fh:
                    return json.load(fh)
    raise SystemExit('未找到 句级数据_p%s.json（请在 教材资产 内运行）' % digits)


def _depths(text):
    """每个字符位置的括号深度；用于禁止在括号内部切分。"""
    d, out = 0, []
    for ch in text:
        if ch in '([':
            out.append(d)
            d += 1
        elif ch in ')]':
            d = max(0, d - 1)
            out.append(d)
        else:
            out.append(d)
    return out


def split_candidates(text):
    """返回候选切分段列表（可能不理想，交人工）。

    切点只落在**词边界且括号深度为 0**处：括号内是插入语/同位语，整块不切。
    """
    dep = _depths(text)
    words = [(m.start(), m.end(), m.group()) for m in re.finditer(r'\S+', text)]
    if not words:
        return []

    cuts = [words[0][0]]
    for k, (st, en, w) in enumerate(words):
        if k == 0:
            continue
        bare = re.sub(r'[^A-Za-z]', '', w)
        prev = words[k - 1][2]
        r1 = bool(re.search(r'[,;:–—]$', prev))          # R1 标点后切
        r2 = bool(CONJ.fullmatch(bare) or SUBCONJ.fullmatch(bare))  # R2/R3 连词前切
        if r2 and bare.lower() == 'so':
            # 「so」既可是连词也可是限定词（so many / so much）——只有后面接小句主语才算连词
            nxt = re.sub(r'[^A-Za-z]', '', words[k + 1][2]) if k + 1 < len(words) else ''
            r2 = nxt.lower() in CLAUSE_SUBJ
        if (r1 or r2) and dep[st] == 0:
            cuts.append(st)

    cuts.append(len(text))
    segs = []
    for a, b in zip(cuts, cuts[1:]):
        seg = text[a:b].strip()
        if seg:
            segs.append(seg)

    # R5：过长段（>=8 词）在介词短语前二次切，同样避开括号内
    final = []
    for seg in segs:
        ws = [(m.start(), m.end(), m.group()) for m in re.finditer(r'\S+', seg)]
        if len(ws) < 8:
            final.append(seg)
            continue
        dseg = _depths(seg)
        cut = None
        for i, (st, en, w) in enumerate(ws):
            if i >= 3 and dseg[st] == 0 and PREP.fullmatch(re.sub(r'[^A-Za-z]', '', w)):
                cut = i
                break
        if cut:
            final.append(seg[:ws[cut][0]].strip())
            final.append(seg[ws[cut][0]:].strip())
        else:
            final.append(seg)
    return [f for f in final if f]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page', required=True)
    ap.add_argument('--json', default=None)
    args = ap.parse_args()

    data = find_sentences(args.page)
    rows = []
    print('=== %s %s · %d 句 ===' % (data.get('page'), data.get('title'), len(data['sentences'])))
    total_g = 0
    for s in data['sentences']:
        groups = split_candidates(s['text'])
        total_g += len(groups)
        rows.append({'i': s['i'], 'text': s['text'], 'cand': groups})
        print('\n[%02d] %s' % (s['i'], s['text']))
        for g in groups:
            print('     / %s' % g)

    avg = total_g / max(1, len(data['sentences']))
    print('\n候选：%d 句 / %d 段 / 均长 %.2f 段每句' % (len(rows), total_g, avg))
    print('提示：以上只是候选。意群定稿须人工按句法功能合并/拆分（主语群·谓语群·宾语群·状语群·从句），')
    print('      并写 04_意群数据/意群_pXXX.json；校验用 _yiqun_verify.py。')

    if args.json:
        with io.open(os.path.join(HERE, args.json), 'w', encoding='utf-8') as fh:
            json.dump({'page': data.get('page'), 'candidates': rows}, fh, ensure_ascii=False, indent=1)
        print('候选已写：%s' % args.json)


if __name__ == '__main__':
    main()
