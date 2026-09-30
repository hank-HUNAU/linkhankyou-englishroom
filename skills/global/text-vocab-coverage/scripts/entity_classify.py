# -*- coding: utf-8 -*-
"""实体专名分类模块: 把"大写且未命中词表"的 token 归类为 PER/GPE/ORG/OTH/SYM。

词表: entity_lexicon.json (与本模块同目录, 用户可编辑)。
分类规则 (按优先级):
  1. SYM  符号专名(月份/星期/节日/居民词), 仅标注、不进实体表;
  2. PER  已知名/宠物名, 顺延收集后续大写"姓";    # 如 Sloan Henderson = PER
  3. ORG  校名/机构: 词内[0,+4)出现机构后缀词则整段为机构;  # Greece Athena High School = ORG
  4. GPE  前向多词 -> 后向多词(New York 的 York) -> 单国家/州/城市;
  5. OTH  其他专名 + 兜底。

token 归一: 判定前先剥除包裹引号/撇号并去掉属格/缩略后的词干(core), 保留原形用于展示。
"""
import os, json

LEX_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entity_lexicon.json")


def load_lexicon(path=None):
    """载入实体词典(缺失时返回空结构)。"""
    p = path or LEX_FILE
    empty = {"SYM": set(), "PER_given": set(), "PER_pet": set(),
             "GPE": set(), "GPE_multi": [], "ORG_suffix": set(), "OTH": set()}
    if not os.path.exists(p):
        return empty
    raw = json.load(open(p, encoding="utf-8"))
    sym = set()
    for k in ("months", "weekdays", "holidays", "demonyms"):
        sym |= {w for w in raw.get("SYM", {}).get(k, [])}
    per = raw.get("PER", {})
    gpe_word = {}
    for k in ("country", "state", "city", "region"):
        gpe_word.update({w: k for w in raw.get("GPE", {}).get(k, [])})
    multi = [tuple(w.split()) for w in raw.get("GPE", {}).get("multi", [])]
    return {
        "SYM": sym,
        "PER_given": set(per.get("given", [])),
        "PER_pet": set(per.get("pet", [])),
        "GPE": set(gpe_word),
        "GPE_multi": sorted(multi, key=len, reverse=True),
        "ORG_suffix": set(raw.get("ORG", {}).get("suffix", [])),
        "OTH": set(raw.get("OTH", {}).get("single", [])),
    }


def _disp(tok):
    """去除包裹引号/撇号后的可读原形。"""
    return tok.strip("'\"").strip("'")


def _cname(tok):
    """规范展示形: 去除包裹字符, 并去掉属格(如 Jason's -> Jason)。"""
    s = _disp(tok)
    low = s.lower()
    if low.endswith("'s"):
        s = s[:-2]
    elif low.endswith("s'"):
        s = s[:-2]
    return s


def _core(tok):
    """判定用词干: 剥包裹字符 -> 属格/缩略 -> 小写。"""
    w = _disp(tok).lower()
    if w.endswith("'s"):
        w = w[:-2]
    elif w.endswith("s'"):
        w = w[:-2]
    elif "'" in w:
        w = w.split("'", 1)[0]
    return w


def classify_proper(toks, i, lex):
    """判定 toks[i] (大写且未命中词表的 token) 的实体类型。
    返回 (type, canon, end); end 为下一不消费的下标(可跳过 [i, end) 段)。"""
    n = len(toks)
    c = _core(toks[i])

    # 1) 符号专名
    if c in lex["SYM"]:
        return ("SYM", _cname(toks[i]), i + 1)

    # 2) 人名: 已知名/宠物名, 顺延收集后续大写"姓"
    if c in lex["PER_given"] or c in lex["PER_pet"]:
        lead = _cname(toks[i])
        j = i + 1
        while j < n:
            o = _disp(toks[j])
            if o and o[0].isupper() and o.isalpha() and len(o) > 1:
                lead = lead + " " + o
                j += 1
            else:
                break
        return ("PER", lead, j)

    # 3) 机构: [i, i+4) 内出现机构后缀词 -> 整段归机构
    for j in range(i, min(n, i + 4)):
        if _core(toks[j]) in lex["ORG_suffix"]:
            return ("ORG", " ".join(_cname(t) for t in toks[i:j + 1]), j + 1)

    # 4) 地名: 前向多词
    for words in lex["GPE_multi"]:
        wl = len(words)
        if i + wl <= n and [_core(t) for t in toks[i:i + wl]] == list(words):
            return ("GPE", " ".join(_cname(t) for t in toks[i:i + wl]), i + wl)
    #    后向多词 (如 "New York" 中的 York)
    for words in lex["GPE_multi"]:
        wl = len(words)
        if i + 1 >= wl and [_core(t) for t in toks[i + 1 - wl:i + 1]] == list(words):
            return ("GPE", " ".join(_cname(t) for t in toks[i + 1 - wl:i + 1]), i + 1)
    #    单国家/州/城市
    if c in lex["GPE"]:
        return ("GPE", _cname(toks[i]), i + 1)

    # 5) 其他专名 + 兜底
    if c in lex["OTH"]:
        return ("OTH", _cname(toks[i]), i + 1)
    return ("OTH", _cname(toks[i]), i + 1)