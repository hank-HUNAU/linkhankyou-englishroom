# -*- coding: utf-8 -*-
"""意群数据校验（硬门禁）—— 本地教师资源用，不涉及站点与音频。

用法：
  python _yiqun_verify.py --page p048
  python _yiqun_verify.py --page p048 --quiet

六道门禁：
  G1 源句一致：意群 text 与归档句级数据同 i 的 text 逐字相同（空白归一）
  G2 拼接还原：各群按序以空格拼接 == 源句（空白归一）——**切点必落词边界**
  G3 句覆盖完整：i 从 0 连续、条数 == 句级数据 n_sent
  G4 段数合理：每句 2–4 群（<2 或 >4 报警，不阻断）
  G5 标注完整：每群 fn（句法功能）与 zh（中文片段）非空
  G6 教学点：每句 point 非空
退出码：0 全过；1 有硬失败（G1/G2/G3/G5/G6）；2 仅告警（G4）
"""
import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def norm(s):
    return re.sub(r'\s+', ' ', (s or '')).strip()


def find(pattern):
    for root, dirs, files in os.walk(os.path.join(HERE, '..')):
        for f in files:
            if f == pattern:
                return os.path.join(root, f)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--page', required=True)
    ap.add_argument('--quiet', action='store_true')
    args = ap.parse_args()
    digits = re.sub(r'\D', '', args.page)
    page = 'p%03d' % int(digits)

    yq_path = find('意群_%s.json' % page)
    sj_path = find('句级数据_%s.json' % page)
    if not yq_path:
        sys.exit('未找到 意群_%s.json' % page)
    if not sj_path:
        sys.exit('未找到 句级数据_%s.json' % page)

    yq = json.load(io.open(yq_path, encoding='utf-8'))
    sj = json.load(io.open(sj_path, encoding='utf-8'))
    src = {s['i']: s['text'] for s in sj['sentences']}

    hard, warn = [], []
    sents = yq.get('sentences', [])
    n_groups_total = 0

    # G3 覆盖
    idx = [s['i'] for s in sents]
    if idx != sorted(idx):
        hard.append('G3 句序非升序')
    if len(sents) != len(src):
        hard.append('G3 句数不符：意群 %d vs 句级 %d' % (len(sents), len(src)))
    missing = sorted(set(src) - set(idx))
    if missing:
        hard.append('G3 缺句：%s' % missing)

    for s in sents:
        i = s['i']
        groups = s.get('groups') or []
        n_groups_total += len(groups)

        # G1 源句一致
        if i in src and norm(s.get('text')) != norm(src[i]):
            hard.append('G1 [%02d] text 与句级数据不一致' % i)

        # G2 拼接还原
        joined = norm(' '.join(g.get('t', '') for g in groups))
        if joined != norm(s.get('text')):
            hard.append('G2 [%02d] 拼接不还原' % i)
            if not args.quiet:
                print('  [%02d] 原文：%s' % (i, norm(s.get('text'))))
                print('        拼接：%s' % joined)

        # G4 段数
        if not (2 <= len(groups) <= 4):
            warn.append('G4 [%02d] 段数 %d（建议 2–4）' % (i, len(groups)))

        # G5 标注完整
        for k, g in enumerate(groups):
            if not norm(g.get('fn', '')):
                hard.append('G5 [%02d] 第 %d 群缺 fn' % (i, k + 1))
            if not norm(g.get('zh', '')):
                hard.append('G5 [%02d] 第 %d 群缺 zh' % (i, k + 1))

        # G6 教学点
        if not norm(s.get('point', '')):
            hard.append('G6 [%02d] 缺 point' % i)

    print('=== 意群校验 %s · %s ===' % (page, yq.get('title', '')))
    print('句数 %d / 意群总段数 %d / 平均 %.2f 段每句'
          % (len(sents), n_groups_total, n_groups_total / max(1, len(sents))))
    if warn:
        print('\n[告警 %d]' % len(warn))
        for w in warn:
            print('  !', w)
    if hard:
        print('\n[硬失败 %d]' % len(hard))
        for h in hard:
            print('  x', h)
        sys.exit(1)
    print('\n六道门禁全过：G1 源句一致 · G2 拼接还原 · G3 覆盖完整 · G4 段数 · G5 标注 · G6 教学点')
    sys.exit(2 if warn else 0)


if __name__ == '__main__':
    main()
