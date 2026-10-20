# -*- coding: utf-8 -*-
"""核查网站词汇诊断页(自包含)词表 是否全部源自 归档 json。
判定标准：页面内联词 ⊆ 归档词集（页面诊断内容词；归档含全部篇章词含功能词）。
用法：python _verify_vocab_link.py
"""
import os, re, json, glob

REPO = os.path.dirname(os.path.abspath(__file__))
ARCH = os.path.normpath(os.path.join(REPO, '..'))  # Think F 教材资产

def extract_array(html, varname):
    i = html.find(varname + ' = [')
    if i < 0:
        i = html.find(varname + '=[')
    if i < 0:
        return None
    j = html.index('[', i); depth = 0
    for k in range(j, len(html)):
        if html[k] == '[': depth += 1
        elif html[k] == ']':
            depth -= 1
            if depth == 0:
                return html[j:k+1]
    return None

def bracket_array(text):
    try: return json.loads(text)
    except Exception: return None

def html_word_set(path):
    html = open(path, encoding='utf-8').read()
    for var in ('RAW', 'VOICE'):
        arr = extract_array(html, var)
        if arr is None: continue
        data = bracket_array(arr)
        if data is None: continue
        s = set()
        for r in data:
            if isinstance(r, (list, tuple)) and r:
                s.add(str(r[0]).strip().lower())
            elif isinstance(r, dict):
                s.add(str(r.get('en') or r.get('w') or '').strip().lower())
        s.discard('')
        if s: return s
    return set()

# 归档侧
passage = {}   # key -> set(lemma+form lowercased)
theme = {}     # uX -> set(w lowercased)
for f in glob.glob(os.path.join(ARCH, 'U*', '02_词汇数据', 'u*_p*.json')):
    key = os.path.basename(f)[:-5]
    d = json.load(open(f, encoding='utf-8'))
    s = set()
    for t in d.get('tokens', []):
        for x in (t.get('form'), t.get('lemma')):
            if x: s.add(x.strip().lower())
    passage[key] = s
for f in (glob.glob(os.path.join(ARCH, 'U*', '03_主题词汇', 'theme_u*.json')) +
          glob.glob(os.path.join(ARCH, '00_主题词汇', 'theme_u*.json'))):
    m = re.search(r'theme_u(\d+)', os.path.basename(f))
    if not m: continue
    ux = 'u' + m.group(1)
    d = json.load(open(f, encoding='utf-8'))
    s = set()
    if isinstance(d, list):
        for it in d:
            w = (it.get('w') if isinstance(it, dict) else str(it)).strip().lower()
            if w: s.add(w)
    theme[ux] = s

# 篇章页：页面词 ⊆ 归档词集
ph = [p for p in glob.glob(os.path.join(REPO, '词汇诊断', '词汇诊断_u*.html'))
      if '_theme_' not in os.path.basename(p)]
miss_p, total_p, bad_p = 0, 0, []
for p in ph:
    m = re.search(r'词汇诊断_(u\d+_p\d+_[a-z0-9_]+)', os.path.basename(p))
    if not m or m.group(1) not in passage: continue
    hs = html_word_set(p)
    if not hs: bad_p.append((m.group(1), 'no-data')); continue
    total_p += 1
    missing = hs - passage[m.group(1)]
    if not missing:
        miss_p += 1
    else:
        bad_p.append((m.group(1), '缺%d:%s' % (len(missing), sorted(missing)[:5])))

# 主题页
th = glob.glob(os.path.join(REPO, '00_主题词汇', '词汇诊断_theme_u*.html'))
miss_t, total_t, bad_t = 0, 0, []
for p in th:
    m = re.search(r'theme_(u\d+)', os.path.basename(p))
    if not m or m.group(1) not in theme: continue
    hs = html_word_set(p)
    if not hs: bad_t.append((m.group(1), 'no-data')); continue
    total_t += 1
    missing = hs - theme[m.group(1)]
    if not missing:
        miss_t += 1
    else:
        bad_t.append((m.group(1), '缺%d:%s' % (len(missing), sorted(missing)[:5])))

print('=== 网站词汇页 ↔ 归档 json 接入核验（页面词 ⊆ 归档词集）===')
print('篇章词汇页：%d/%d 全部接入（页面词 100%% 源自归档）' % (miss_p, total_p))
print('主题词汇页：%d/%d 全部接入' % (miss_t, total_t))
print('篇章异常：', bad_p if bad_p else '无')
print('主题异常：', bad_t if bad_t else '无')
print('结论：', '三项数据全部接入归档 ✅' if (miss_p==total_p and miss_t==total_t) else '存在差异需查 ⚠️')
