# -*- coding: utf-8 -*-
"""篇章三页拆分 v2 验证（预习/复习/听写 84 页）

覆盖（2026-10-16 定案）：
- 复习页 p066：逐句跟读 + 间隙生词提示 + 完成落盘 + 三页互链
- 预习页 p085：盲听 + 常驻答题板（4 题）+ 下划线/画圈标记工具 + ≥75% 记完成
- 复习页 p113：句级时间轴与原文句子数一致 + 间隙可用
- 听写页 p088：抽句（3/5/段落）+ 三方式入口（键盘/稿纸/听写本）
- 主站深链 ?pg=85 → 篇章页/复习页
- 每个页面零 JS 异常

用法：python _smoke_follow_stage.py [BASE]   （BASE 默认 http://localhost:8000）
"""
import io, sys, json
from urllib.parse import unquote
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
ok = fail = 0
def chk(name, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("  OK  " + name + ("   " + extra if extra else ""))
    else: fail += 1; print("  XX  " + name + "   " + extra)

def new_page(b, errs):
    ctx = b.new_context(viewport={"width": 1300, "height": 900})
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    return ctx, pg

with sync_playwright() as p:
    b = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])

    # ── [A] 主站深链 ?pg=85 → 篇章页/复习页 ──
    print("[A] 主站深链 ?pg= → 篇章页三页结构")
    errs = []
    ctx, pg = new_page(b, errs)
    ctx.add_init_script("try{localStorage.setItem('tf_current_student','冒烟同学');}catch(e){}")
    pg.goto(BASE + "/index.html", wait_until="domcontentloaded")
    pg.evaluate("location.href = '" + BASE + "/index.html?pg=85'")
    pg.wait_for_timeout(1500)
    chk("深链落在篇章页/复习页", "/篇章页/复习_085_" in unquote(pg.url), unquote(pg.url))
    chk("深链页无 JS 异常", len(errs) == 0, str(errs[:3]))
    ctx.close()

    # ── [B] 复习页 p066：逐句跟读 + 间隙生词提示 ──
    print("[B] 复习页 p066（逐句跟读流程）")
    errs = []
    ctx, pg = new_page(b, errs)
    pg.goto(BASE + "/篇章页/复习_066_livingforsport.html", wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    print("[B0] 直开复习页 URL:", pg.url)
    n = pg.eval_on_selector_all("#fpass .fpc", "es=>es.length")
    chk("步骤芯片共 1 个", n == 1, "实际 %d" % n)
    titles = pg.eval_on_selector_all("#fpass .fpc", "es=>es.map(e=>e.getAttribute('title')||'')")
    chk("芯片语义 = 逐句跟读", "逐句跟读" in (titles[0] if titles else ""), " | ".join(t[:18] for t in titles))
    tl = pg.evaluate("()=>{var a=TL[state.pg]; return {n:a.length, first:[+a[0][0].toFixed(3),+a[0][1].toFixed(3)]};}")
    chk("pg66 有句级时间轴", tl["n"] > 0, "句数=%s" % tl["n"])
    chk("第 1 句区间有效", tl["first"][0] < tl["first"][1], str(tl["first"]))
    chk("句数与原文一致", pg.evaluate("()=>SEGS.length===TL[state.pg].length"))
    chk("三页互链注入", pg.evaluate("()=>SIBLINGS.listen.indexOf('预习_066_')===0 && SIBLINGS.follow.indexOf('复习_066_')===0 && SIBLINGS.dictate.indexOf('听写_066_')===0"),
        json.dumps(pg.evaluate("()=>SIBLINGS"), ensure_ascii=False))

    print("[B1] 间隙生词提示（方案A）")
    pg.evaluate("()=>{ enterFollow(); followSentenceEnd(); }"); pg.wait_for_timeout(300)
    gapOn = pg.evaluate("()=>document.getElementById('fsGap').classList.contains('on')")
    gw = pg.evaluate("()=>document.getElementById('fsGapWords').textContent")
    chk("间隙卡弹出", gapOn, "")
    chk("生词提示区渲染（无生词走兜底文案）", ("无生词" in gw) or gw.strip() != "", gw[:30])

    print("[B2] 末句完成 → finishFollow + 互链听写页")
    pg.evaluate("()=>{ state.idx = SEGS.length-1; followSentenceEnd(); }"); pg.wait_for_timeout(300)
    pg.evaluate("()=>finishFollow()"); pg.wait_for_timeout(300)
    chk("PROG.follow 置位", pg.evaluate("()=>PROG.follow") == True, "")
    chk("落盘含 follow 键", pg.evaluate("()=>JSON.parse(localStorage.getItem('tf_follow_'+state.pg)).follow") == True, "")
    chk("互链指向听写页", pg.evaluate("()=>SIBLINGS.dictate.indexOf('听写_')===0"),
        str(pg.evaluate("()=>SIBLINGS.dictate")))

    print("[B3] 暂停间隙引导开口")
    pg.evaluate("()=>showGap(2,'该你开口 · 测试',function(){})"); pg.wait_for_timeout(250)
    gap = pg.evaluate("""()=>{var g=document.getElementById('fsGap');
      return {on: !!(g&&g.classList.contains('on')), txt: g? g.innerText.replace(/\\s+/g,' ').trim():null};}""")
    chk("间隙提示层出现", gap["on"], str(gap["txt"])[:60])
    pg.evaluate("()=>cancelGap()"); pg.wait_for_timeout(200)
    chk("间隙提示层可关闭", not pg.evaluate("()=>!!(document.getElementById('fsGap')||{}).classList.contains('on')"))
    chk("复习页无 JS 异常", len(errs) == 0, str(errs[:4]))
    ctx.close()

    # ── [C] 预习页 p085：盲听 + 答题板 + 标记工具 ──
    print("[C] 预习页 p085（盲听 + 4 题 + 标记工具）")
    errs = []
    ctx, pg = new_page(b, errs)
    pg.goto(BASE + "/篇章页/预习_085_kitchenkids.html", wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    chk("题库注入 4 题", pg.evaluate("()=>QUIZ.length") == 4, "实际 %s" % pg.evaluate("()=>QUIZ.length"))
    chk("盲听生效（原文模糊）", pg.evaluate("()=>document.getElementById('body').classList.contains('blind')"), "")
    chk("答题横幅出现", pg.evaluate("()=>!!document.getElementById('quizBanner')"), "")
    pg.evaluate("()=>showQuiz()"); pg.wait_for_timeout(300)
    chk("答题板弹出", pg.evaluate("()=>document.getElementById('quizOv').classList.contains('on')"), "")
    chk("题面渲染 4 题", pg.eval_on_selector_all("#qzBody .qz-q", "es=>es.length") == 4, "")
    chk("听前作答禁用", pg.evaluate("()=>document.getElementById('qzSubmit').disabled"), "")
    pg.evaluate("()=>mkMode('u')"); pg.wait_for_timeout(150)
    chk("下划线标记工具启用", pg.evaluate("()=>document.getElementById('qzCanvas').classList.contains('on')"), "")
    pg.evaluate("()=>mkMode(null)")
    # 逐题答对 → 自动整卷批改
    pg.evaluate("""()=>{ document.querySelectorAll('#qzBody .quiz-opt').forEach(function(b){
        var q=QUIZ[+b.dataset.qi];
        var hit=(q.t==='tf') ? (b.dataset.ans===q.a) : (+b.dataset.ans===q.a);
        if(hit) b.click(); }); }""")
    pg.wait_for_timeout(400)
    scoreTxt = pg.evaluate("()=>document.getElementById('qzSubmit').textContent")
    chk("整卷批改 ≥75% 通过", "得分 4 / 4" in scoreTxt, scoreTxt)
    chk("PROG.listen 记完成", pg.evaluate("()=>PROG.listen") == True, "")
    chk("批改后盲听解除", pg.evaluate("()=>!document.getElementById('body').classList.contains('blind')"), "")
    chk("预习页无 JS 异常", len(errs) == 0, str(errs[:4]))
    ctx.close()

    # ── [D] 复习页 p113：句级时间轴 + 间隙 ──
    print("[D] 复习页 p113（句级时间轴一致性）")
    errs = []
    ctx, pg = new_page(b, errs)
    pg.goto(BASE + "/篇章页/复习_113_trainstation.html", wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    info = pg.evaluate("()=>({segs:SEGS.length, tl:TL[state.pg].length, sib:SIBLINGS.follow})")
    chk("p113 句数与时间轴一致", info["segs"] == info["tl"] and info["tl"] > 0,
        "SEGS=%s TL=%s" % (info["segs"], info["tl"]))
    pg.evaluate("()=>{ enterFollow(); followSentenceEnd(); }"); pg.wait_for_timeout(300)
    chk("p113 间隙卡可用", pg.evaluate("()=>document.getElementById('fsGap').classList.contains('on')"), "")
    pg.evaluate("()=>cancelGap()")
    chk("p113 页无 JS 异常", len(errs) == 0, str(errs[:4]))
    ctx.close()

    # ── [E] 听写页 p088：抽句 + 三方式 ──
    print("[E] 听写页 p088（抽句 + 三方式入口）")
    errs = []
    ctx, pg = new_page(b, errs)
    pg.goto(BASE + "/篇章页/听写_088_inarestaurant.html", wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    chk("抽句面板弹出", pg.evaluate("()=>document.getElementById('pickpick').classList.contains('on')"), "")
    ways = pg.eval_on_selector_all("#pickpick .way-btn, #waypick .way-btn", "es=>es.length")
    chk("抽句 3 入口 + 方式 3 入口", ways == 6, "实际 %d" % ways)
    pg.evaluate("()=>pickCount(3)"); pg.wait_for_timeout(300)
    chk("抽 3 句后进入方式选择", pg.evaluate("()=>document.getElementById('waypick').classList.contains('on')"), "")
    pg.evaluate("()=>pickWay('key')"); pg.wait_for_timeout(400)
    chk("键盘听写渲染填空", pg.eval_on_selector_all("#dt-sheet .dt-blank", "es=>es.length") > 0, "")
    chk("四遍精听标签", "第 1/4 遍" in pg.evaluate("()=>document.getElementById('dt-pass').textContent"),
        pg.evaluate("()=>document.getElementById('dt-pass').textContent"))
    pg.evaluate("()=>pickWayNb()"); pg.wait_for_timeout(300)
    chk("听写本模式浮层弹出", pg.evaluate("()=>document.getElementById('nbOv').classList.contains('on')"), "")
    chk("听写本卡片渲染", pg.evaluate("()=>document.getElementById('nbCard').textContent.indexOf('听写本 · 第 1')===0"), "")
    chk("听写页无 JS 异常", len(errs) == 0, str(errs[:4]))
    ctx.close()

    b.close()

print("\n结果：%d 通过 / %d 失败" % (ok, fail))
sys.exit(1 if fail else 0)
