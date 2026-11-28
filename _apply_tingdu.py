# -*- coding: utf-8 -*-
"""两站篇章听读改造（2026-11-28 用户令）：
① Think F 49 个篇章页：移植 Think 1 已验证的 strip_dictate_page（删逐句听写 tab/UI/CSS/引擎）；
② 91 个篇章页（TF 49 + TK 42）：<title> 与页头 <h1> 改为课本标题名（PASSAGES.title，TF p202 补
   「Ways to Get Around」，来源 reports/正课文清单.csv）；
③ 页内可见文案「逐句听已完成」→「篇章听读已完成」（其余逐句听均为 JS 注释，不动）；
④ 全量断言：TF 零 tabDictate/viewDictate/逐句听写/dictate；TK 零 dictate；title 覆盖 91/91。
页面已入 git，可直接回滚，不做额外备份。
"""
import io, os, re, json, glob, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
TF_HTML = os.path.join(BASE, "index.html")
TK_HTML = os.path.join(BASE, "tk1", "index.html")


def extract_objects(s):
    """提取 var PASSAGES={...}; 与所有 Object.assign(PASSAGES,{...}); 的对象字面量（跳过字符串内花括号）。"""
    out = []
    for m in re.finditer(r'var PASSAGES\s*=\s*\{|Object\.assign\(PASSAGES\s*,\s*\{', s):
        i = m.end() - 1
        depth, instr, k = 0, None, i
        while k < len(s):
            c = s[k]
            if instr:
                if c == '\\':
                    k += 2; continue
                if c == instr: instr = None
            else:
                if c in '\'"`': instr = c
                elif c == '{': depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0: break
            k += 1
        out.append(s[i:k + 1])
    return out


def passages_map(html_path, tmp_tag):
    """node 求值 PASSAGES → {页码int: title}。"""
    s = io.open(html_path, encoding="utf-8").read()
    segs = extract_objects(s)
    assert segs, "PASSAGES 提取失败: " + html_path
    js = ['var PASSAGES = ' + segs[0][segs[0].find('{'):] + ';']
    for seg in segs[1:]:
        js.append('Object.assign(PASSAGES, ' + seg[seg.find('{'):] + ' );')
    js.append('console.log(JSON.stringify(PASSAGES));')
    tmp = os.path.join(BASE, '_tmp_passages_%s.js' % tmp_tag)
    io.open(tmp, 'w', encoding='utf-8').write('\n'.join(js))
    r = subprocess.run(['node', tmp], capture_output=True, text=True, encoding='utf-8')
    os.remove(tmp)
    assert r.returncode == 0, 'PASSAGES 求值失败: ' + r.stderr[:300]
    d = json.loads(r.stdout)
    out = {}
    for _u, lst in d.items():
        for p in lst:
            n = int(str(p.get('p', '')).lstrip('p'))
            out[n] = p.get('title', '')
    return out


def cut_between(t, start, end, label):
    s = t.find(start)
    assert s >= 0, "起点缺失: " + label
    e = t.find(end, s + len(start))
    assert e >= 0, "终点缺失: " + label
    return t[:s] + t[e:]


def replace_once(t, old, new, label):
    assert t.count(old) == 1, "锚点不唯一或缺失: %s (%d)" % (label, t.count(old))
    return t.replace(old, new, 1)


def strip_dictate_page(t, fname):
    """独立篇章页：删除逐句听写 tab、UI、CSS 与引擎，仅保留逐句听。（移植自 _gen_tk1_pages.py）"""
    t = cut_between(t, "/* ── 流程② 逐句听写 ── */", "#toast{", "听写 CSS")
    t = cut_between(t, '    <div class="tabs">', "  </header>", "顶部 tab")
    t = cut_between(t, '    <section id="viewDictate" class="hide">',
                    "  </div></main>", "听写 UI")
    t = replace_once(t,
        "/* ============ 读写单页引擎：流程① 逐句听（纯听+看，中文默认关） · 流程② 逐句听写（随机N句/按段落） ============ */",
        "/* ============ 逐句听单页引擎（听写已移除，中文默认关） ============ */",
        "引擎注释")
    t = replace_once(t,
        "    if(lg&&typeof lg==='object') o={listen:!!lg.listen, dictate:!!lg.dictate};\n"
        "  }\n"
        "  return {listen:!!(o&&o.listen), dictate:!!(o&&o.dictate), lastPct:(o&&o.lastPct)||null};",
        "    if(lg&&typeof lg==='object') o={listen:!!lg.listen};\n"
        "  }\n"
        "  return {listen:!!(o&&o.listen), lastPct:(o&&o.lastPct)||null};",
        "stageLoad")
    s = t.find("/* ── 流程切换 ── */")
    e = t.find("/* ═══════════ 流程① 逐句听 ═══════════ */", s)
    assert s >= 0 and e > s, "流程切换块缺失: " + fname
    t = (t[:s] +
         "/* ── 单流程：逐句听（听写入口已移除） ── */\n"
         "var state={ flow:'listen', idx:0, auto:false, zh:false, played:{} };\n"
         "$('backBtn').onclick=function(){ location.href='../index.html'; };\n\n\n" +
         t[e:])
    t = cut_between(t, "/* ═══════════ 流程② 逐句听写 ═══════════ */",
                    "/* ── 启动 ── */", "听写 JS")
    t = replace_once(t,
        "    renderSents(); setIdx(0); updatePos(); renderParaChips();",
        "    renderSents(); setIdx(0); updatePos();",
        "boot render")
    t = replace_once(t,
        "    var m=(location.search||'').match(/[?&]flow=(listen|dictate)/);\n"
        "    if(m&&m[1]==='dictate') setFlow('dictate'); else setFlow('listen');\n",
        "    /* 单流程：逐句听 */\n",
        "boot flow")
    assert "逐句听写" not in t, "残留逐句听写文案: " + fname
    assert "dictate" not in t, "残留 dictate 标识: " + fname
    return t


def page_no(fname):
    m = re.search(r'(\d{2,3})', fname)
    return int(m.group(1)) if m else None


def set_title_h1(t, title, fname):
    t2, n = re.subn(r'<title>[^<]*</title>', '<title>%s</title>' % title, t, count=1)
    assert n == 1, "title 替换失败: " + fname
    t2, n = re.subn(r'<h1 id="tTitle">[^<]*</h1>', '<h1 id="tTitle">%s</h1>' % title, t2, count=1)
    assert n == 1, "h1 替换失败: " + fname
    return t2


PILL_OLD = "✓ 逐句听已完成（进度已记录）"
PILL_NEW = "✓ 篇章听读已完成（进度已记录）"


def assert_only_comment_zh(t, fname):
    """处理后「逐句听」仅允许出现在注释行。"""
    bad = []
    for i, ln in enumerate(t.splitlines(), 1):
        if '逐句听' in ln:
            st = ln.strip()
            if not (st.startswith('/*') or st.startswith('*') or st.startswith('//')):
                bad.append((i, st[:80]))
    assert not bad, "可见「逐句听」残留: %s %s" % (fname, bad[:3])


def main():
    tf_map = passages_map(TF_HTML, 'TF')
    tk_map = passages_map(TK_HTML, 'TK')
    tf_map[202] = 'Ways to Get Around'   # p202 深链篇，PASSAGES 无条目；来源 reports/正课文清单.csv
    print('TF title 映射:', len(tf_map), '| TK:', len(tk_map))

    ok, fail = [], []
    # ── Think F 49 页：strip + title/h1 + done-pill ──
    for f in sorted(glob.glob(os.path.join(BASE, '篇章页', '*.html'))):
        fname = os.path.basename(f)
        n = page_no(fname)
        title = tf_map.get(n)
        if not title:
            fail.append((fname, '无 title 映射')); continue
        try:
            t = io.open(f, encoding='utf-8').read()
            # 先改 title/h1（消除 strip 断言命中的旧 title 文案），再做 strip
            t = set_title_h1(t, title, fname)
            t = strip_dictate_page(t, fname)
            assert t.count(PILL_OLD) <= 1
            t = t.replace(PILL_OLD, PILL_NEW)
            assert_only_comment_zh(t, fname)
            io.open(f, 'w', encoding='utf-8', newline='\n').write(t)
            ok.append(fname)
        except AssertionError as ex:
            fail.append((fname, str(ex)[:120]))
    # ── Think 1 42 页：title/h1 + done-pill ──
    ok_tk, fail_tk = [], []
    for f in sorted(glob.glob(os.path.join(BASE, 'tk1', '篇章页', '*.html'))):
        fname = os.path.basename(f)
        n = page_no(fname)
        title = tk_map.get(n)
        if not title:
            fail_tk.append((fname, '无 title 映射')); continue
        try:
            t = io.open(f, encoding='utf-8').read()
            t = set_title_h1(t, title, fname)
            t = t.replace(PILL_OLD, PILL_NEW)
            assert 'dictate' not in t, 'TK 残留 dictate: ' + fname
            assert_only_comment_zh(t, fname)
            io.open(f, 'w', encoding='utf-8', newline='\n').write(t)
            ok_tk.append(fname)
        except AssertionError as ex:
            fail_tk.append((fname, str(ex)[:120]))

    print('TF 处理成功 %d / 失败 %d' % (len(ok), len(fail)))
    for x in fail[:10]: print('  FAIL', x)
    print('TK 处理成功 %d / 失败 %d' % (len(ok_tk), len(fail_tk)))
    for x in fail_tk[:10]: print('  FAIL', x)
    if fail or fail_tk:
        sys.exit(1)
    print('PASS：TF %d 页 strip+改名，TK %d 页改名；91/91 title=课本标题，可见文案=篇章听读'
          % (len(ok), len(ok_tk)))


if __name__ == '__main__':
    main()
