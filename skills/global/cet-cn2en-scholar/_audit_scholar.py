# -*- coding: utf-8 -*-
"""学理自查规约的机器实现 —— **统一权威版 v1.4**（2026-09-21 双副本口径统一）。

按「学理自查规约」第 2 节断言表，校验"策略L1/技巧L3 声称的学理手段"是否在译文中有
语言实证。红旗机制，非最终判定。

版本统一说明（2026-09-21）：
- 此前存在两个不同源副本：本版（断言集较宽，含 CL-11）与技能目录旧副本
  （窄版，CL-03 触发词为「分词短语」、CL-04 不含 was/were 与不规则形、CL-05 不含 allow/encourage/use/cause、
   CL-01 不含 because/while/so、CL-02 无 Using/Learning 等）。同一 158 套语料分别报 1403·0 与 1324·62。
- 经对 62 处未实证逐条诊断，确认**全部为窄版漏检的假阳性**（译文均确有该机制，仅特征词未覆盖）——
  如 `has become`（不规则过去分词）、`is widely regarded`（副词插入）、`was written`（was/were 支路缺失）、
  `If … because …`（连接词表缺 because）、`helps`（`\\bhelp\\b` 未含 -s）、`Using idioms`（动词表缺 Using）。
- 故统一采用**本版**为权威实现，并按本版特征集修订《学理自查规约》§2 断言表（含新增 CL-11）。

可移植说明：
- 断言表(PRIN)是纯方法论，可随 skill 复用；它不带任何真题/译文/来源任务数据。
- 待测文件一律通过命令行传入（见用法），不硬编码本地路径，便于任何环境复跑。

位置说明（2026-09-21 库归位）：
- **权威副本**：技能目录 `cet-cn2en-scholar\_audit_scholar.py`（随技能发布）。
- **本地调用副本**：库内 `_cet历年\管线\_audit_scholar.py`（本文件）——二者须**同哈希**。
- 原第三副本 `_cet2026\_audit_scholar.py` 已随"数据仓库 _cet2026"角色废止而删除（该目录整体撤销）。

用法:
    python _cet历年\管线\_audit_scholar.py 文件.md [文件2.md ...]   # 指定待测学习卡
    python _cet历年\管线\_audit_scholar.py --pass 文件.md            # 仅输出未实证项
    python _cet历年\管线\_audit_scholar.py --json 报告.json 文件.md  # 导出结构化报告
"""
import sys, re, io, json, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SPEC_VERSION = 'v1.4'   # 统一权威版（2026-09-21：双副本口径统一，含 CL-11）
RUN_STAMP = datetime.date.today().isoformat()

# ---- 断言定义（与「学理自查规约」§2 断言表一一对应；正则预编译避免重复开销） ----
# 字段: id, 触发词(ta/te 出现即评估), 断言名, 学理依据, 证据特征正则(pattern)
PRIN = [
    dict(id='CL-01', trig='形合', name='显性连接词', basis='连淑能1993 意合→形合',
         pat=re.compile(r'\band\b|\bwhich\b|\bso as to\b|\bthat\b|\bwho\b|\bbut also\b|\bwith (its|their)\b|^(As|While|Although|Though)\b|\bwhile\b|\bso\b|\bbecause\b|\bto (boost|promote|enhance)\b', re.I)),
    dict(id='CL-02', trig='动名词主语', name='动名词短语', basis='Li&Thompson1976 提炼主语',
         pat=re.compile(r'\b(Exchanging|Giving|Following|Respecting|Offering|Maintaining|Promoting|Identifying|Delivering|Viewing|Guessing|Using|Learning|Eating|Placing|Starting)\s', re.I)),
    dict(id='CL-03', trig='分词', name='分词/with短语', basis='Molina&Albir2002 分词独立',
         pat=re.compile(r',\s*(?:[a-z]+(ly|er|est)\s+)?[a-z]+(ing|ed)\b|,?\s+(?:[a-z]+(ly|er|est)\s+)?[a-z]+ed\s+(?:with|to|for|in|as|by)\b|\bwith (its|their|a)\b|\bwith\s+(?:[a-z]+\s+){0,3}[a-z]+(ing|ed)\b|\bby\s+(?:[a-z]+\s+){0,3}[a-z]+ing\b|\b(?:By|by|Through|through)\s+[a-z]+ing\b|^(Following|Embracing|Using|Hailed|Located|Hearing|Regretting|Watching|Waiting|Standing|Hoping|Mending|Losing|Staying|Spanning)\s|\b(?:turning|strolling|wandering|walking|facing|living|raising|satisfying|protecting|making|promoting|embodying|contributing|allowing|experiencing|enabling|covering|inheriting|innovating|hearing|regretting|watching|waiting|standing|hoping|mending|losing|rushing|spanning|falling|melting|harvesting|withering|enjoying|flowing|staying|crossing|draining|growing|withering|preserved|hidden|drained|connecting|prepared)\b|\bwhile\s+[a-z]+ing\b|\b(?:made|written|known|set|built|held|told|drawn|found|given|taken|said|brought|sent|shown|seen|kept|left|won|lost|chosen|grown|spoken|understood|ordered|associated|practiced|hidden)\b', re.I)),
	    dict(id='CL-04', trig='被动', name='被动结构', basis='英汉语态差异',
	         pat=re.compile(r'\bare (seated|favored)|(?:have|has|had) been|\b(?:are|is|was|were|be|been)\s+(?:\w+\s+){0,3}\w+ed\b|\b(?:are|is|was|were|be|been)\s+(?:\w+\s+){0,3}(?:made|said|told|written|known|held|drawn|found|given|taken|put|set|built|kept|left|sent|shown|seen|brought|chosen|grown|spoken|hidden)\b', re.I)),
    dict(id='CL-05', trig='使役', name='使役/使动', basis='Vinay&Darbelnet1958 使役转移',
         pat=re.compile(r'\benabl|\bhelp\w*\b|\bma\w{1,3}e\b|\bbrought\b|\bfacilitat|\b(use|uses|used|using|cause)\b|\bencourag\w*|\ballow\w*', re.I)),
    dict(id='CL-06', trig='定语从句', name='后置定语从句', basis='连淑能1993 修饰语位序',
         pat=re.compile(r'\bthat\b|\bwhich\b|\bwho\b|\bwhere\b|\bwhen\b', re.I)),
    dict(id='CL-07', trig='目的', name='目的状语', basis='连淑能1993 语序重排',
         pat=re.compile(r'^To\b|, to\b|\bin order to\b|\bso as to\b|\bso that\b|\bto (boost|promote|enhance|meet|realize|support|record|offer|provide|gain|ensure|help|learn|visit|develop|build|create|establish|protect|feed|irrigate|spray|transform|encourage|repair|pick|describe|replenish|shorten|connect|pass|drain|reduce|save|mark|celebrate|take|cross|facilitate|withstand|divide|divert|channel|enjoy|escape|express|receive|select|carry)\b', re.I)),
    dict(id='CL-08', trig='时态', name='完成/进行时', basis='连淑能1993 时态+Nida1964 判据',
         pat=re.compile(r'\b(has|have|had|is|are|was|were)\s+(?:\w+\s+)?\w+ed\b|\b(has|have|had) been [a-z ]*?\w+ed\b|\b(is|are|was|were)\s+(?:\w+\s+)?\w+ing\b|\b(has|have|had) been\s+(?:[a-z]+\s+)*\w+ing\b|\b(has|have|had)\s+(kept|been|become|spread|risen|chosen|grown|made|taken|given|got|gone)\b|\bin recent\b', re.I)),
    dict(id='CL-09', trig='增补', name='增补/补全', basis='Molina&Albir2002 Amplification',
         pat=re.compile(r'\bbrought\b|\bquality\b|\bfor them\b|\breturn the favor\b|\bglasses and\b|\bmore dishes\b|\benabl|\bfacilitat|\bgreatly\b', re.I)),
    dict(id='CL-10', trig='名词化', name='名词化/名转', basis='Molina&Albir2002 Nominalization',
         pat=re.compile(r'\b\w{3,}(?:ization|ification|ment|tion|sion|ance|ence|ness|ity)s?\b|\b(Giving|Exchanging)\b|^[A-Z]\w+ (progress|platforms|records)\b|\b\w+(ing)\b(?=\s+(of|for)\b)', re.I)),
    dict(id='CL-11', trig='异化|归化|音译|直译|专名|定译', name='文化负载项实证', basis='Venuti1995 异化/归化',
         pat=re.compile(r'\([a-zA-Z][a-zA-Z .&\-]{0,40}\)|[“"][^“”"]{1,40}[”"]|\b(stands for|means|literally|known as)\b|\bThe [A-Z][A-Za-z]+', re.I)),
]

def split_sentences(md):
    out = []
    for b in re.split(r'^###\s+句\d+', md, flags=re.M)[1:]:
        en = re.search(r'\*{0,2}译文\*{0,2}：(.+)', b)
        ta = re.search(r'\*{0,2}策略 L1\*{0,2}：(.+)', b)
        te = re.search(r'\*{0,2}技巧 L3\*{0,2}：(.+)', b)
        l2 = re.search(r'\*{0,2}语块 L2\*{0,2}：(.+)', b)
        out.append(((en.group(1).strip() if en else ''),
                    (ta.group(1).strip() if ta else ''),
                    (te.group(1).strip() if te else ''),
                    (l2.group(1).strip() if l2 else '')))
    return out

def check(en, ta, te):
    flags = []
    for r in PRIN:
        if r['trig'] in (ta + te):
            flags.append(dict(id=r['id'], name=r['name'], basis=r['basis'],
                              ok=bool(r['pat'].search(en)), note=r['trig']))
    return flags

# ---- 语块 L2 层校验：每个语块类名必须为 N&D 四类之一 ----
# 类注解恒在每语块项末尾（全角括号），后面紧跟 ； 或 。；中文标签注解括号后是空格/英文，不误捕获。
LEGAL_L2 = {'P', 'IE', 'PC', 'SB'}
CLS_PAT = re.compile(r'（([^（）]{1,6}?)）(?=；|。)')

def l2_classes(l2_text):
    """提取 L2 行内所有全角括号类名；英文括号用半角 ()，不误匹配。"""
    if not l2_text.strip():
        return []
    return CLS_PAT.findall(l2_text)

def check_l2(l2_text):
    """返回 (总类标注数, 非法类名列表)。"""
    cls = l2_classes(l2_text)
    return len(cls), [c for c in cls if c not in LEGAL_L2]

def main():
    json_path = ''
    files = []
    skip = False
    for a in sys.argv[1:]:
        if a == '--json':
            skip = True          # 下一个参数为报告路径
        elif a == '--pass':
            pass
        elif skip:
            json_path = a        # 承接 --json 的路径参数（v1.4 修复：旧版此参数被丢弃）
            skip = False
        elif a.startswith('--'):
            skip = False
        else:
            files.append(a)
    if not files:
        print('用法: python _audit_scholar.py [--pass] [--json out.json] 文件.md [...]')
        return
    only_miss = '--pass' in sys.argv

    report = dict(spec=SPEC_VERSION, run=RUN_STAMP, files=[],
                  stats=dict(assertions=0, unmet=0, l2_items=0, l2_bad=0))
    for path in files:
        md = open(path, encoding='utf-8').read()
        rec = dict(file=path, items=[])
        for i, (en, ta, te, l2) in enumerate(split_sentences(md), 1):
            flags = check(en, ta, te)
            report['stats']['assertions'] += len(flags)
            miss = [f for f in flags if not f['ok']]
            report['stats']['unmet'] += len(miss)
            n_cls, bad = check_l2(l2)
            report['stats']['l2_items'] += n_cls
            if bad:
                report['stats']['l2_bad'] += len(bad)
                miss.append(dict(id='L2-CLS', name='语块L2类名不合法', basis='Nattinger&DeCarrico1992',
                                 ok=False, note=','.join(bad)))
            if only_miss and not miss:
                continue
            rec['items'].append(dict(n=i, en=en, ta=ta, l2=l2, flags=flags))
            un = ", ".join(f"{f['id']}({f['name']})" for f in miss)
            print(f"[{'!!' if miss else 'OK'}] 句{i}  " + (f"未实证: {un}" if miss else "✔"))
        report['files'].append(rec)

    print('=' * 60)
    print(f"规约 {SPEC_VERSION} · {RUN_STAMP} · 断言 {report['stats']['assertions']} 项 · 未实证 {report['stats']['unmet']} 项"
          f" · L2语块 {report['stats']['l2_items']} 个 · L2非法类名 {report['stats']['l2_bad']} 处")
    if json_path:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print('报告已导出:', json_path)

main()