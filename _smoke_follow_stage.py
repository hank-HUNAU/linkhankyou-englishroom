# -*- coding: utf-8 -*-
"""篇章读写单页验证（每篇 1 个 HTML · 两流程）

覆盖（2026-10-19 单页化定案）：
- 主站深链 ?pg=85 → 篇章页/读写单页（flow=listen）
- 流程①逐句听 p067：句子渲染数=时间轴句数、中文默认关、行点击定位、播完记 tf_stage.listen
- 流程②逐句听写 p067：随机抽 5 句 → 逐句提交（含全对样本）→ 汇总页 → tf_stage.dictate 落盘
- 深链 ?flow=dictate 直接落在流程②
- 每个页面零 JS 异常

用法：python _smoke_follow_stage.py [BASE]   （BASE 默认 http://localhost:8000）
"""
import io, sys, json, time
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

    # ── [A] 主站深链 ?pg=85 → 篇章读写单页 ──
    print("[A] 主站深链 ?pg= → 篇章读写单页")
    errs = []
    ctx, pg = new_page(b, errs)
    ctx.add_init_script("try{localStorage.setItem('tf_current_student','冒烟同学');}catch(e){}")
    pg.goto(BASE + "/index.html", wait_until="domcontentloaded")
    pg.evaluate("location.href = '" + BASE + "/index.html?pg=85'")
    pg.wait_for_timeout(1500)
    chk("深链落在篇章读写单页", "/篇章页/读写_085_" in unquote(pg.url) and "flow=listen" in unquote(pg.url), unquote(pg.url))
    chk("深链页无 JS 异常", len(errs) == 0, str(errs[:3]))
    ctx.close()

    # ── [B] 流程①逐句听 p067 ──
    print("[B] 逐句听 p067（纯听+看，中文默认关）")
    errs = []
    ctx, pg = new_page(b, errs)
    pg.goto(BASE + "/篇章页/读写_067_sportwonders.html", wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    n_segs = pg.evaluate("()=>SEGS.length")
    n_tl = pg.evaluate("()=>(TL[PG]||TL[String(PG)]).length")
    chk("句子渲染数=时间轴句数", pg.eval_on_selector_all("#sentList .sent", "es=>es.length") == n_tl and n_tl > 0, "SEGS=%s TL=%s" % (n_segs, n_tl))
    chk("中文默认关闭", pg.evaluate("()=>!document.body.classList.contains('zh-on')") and pg.evaluate("()=>getComputedStyle(document.querySelector('#sentList .sent .zh')).display") == 'none')
    pg.click("#zhTog")
    pg.wait_for_timeout(150)
    chk("中文开关打开后显示译文", pg.evaluate("()=>document.body.classList.contains('zh-on')"))
    pg.click("#zhTog")
    pg.eval_on_selector_all("#sentList .sent", "es=>es[2].click()")
    pg.wait_for_timeout(150)
    chk("点击句子行定位当前句", pg.evaluate("()=>state.idx===2"))
    pg.evaluate("()=>{ for(var i=0;i<SEGS.length;i++) markPlayed(i); }")
    pg.wait_for_timeout(200)
    chk("播完全篇出现完成标记", pg.eval_on_selector_all("#listenDone .done-pill", "es=>es.length") == 1)
    chk("tf_stage_67.listen 落盘", pg.evaluate("()=>JSON.parse(localStorage.getItem('tf_stage_67')).listen") == True)
    chk('audio.src 已挂载本篇音频', pg.evaluate("()=>audio.src.indexOf('assets/p067.mp3')>=0"))
    pg.evaluate("()=>playCur()")
    pg.wait_for_timeout(1500)
    chk('真实播放出声（currentTime 前进）', pg.evaluate("()=>audio.currentTime>0.2"), 'currentTime=' + str(pg.evaluate("()=>audio.currentTime.toFixed(2)")))
    try:
        pg.evaluate("()=>audio.pause()")
    except Exception:
        pass
    chk("流程①无 JS 异常", len(errs) == 0, str(errs[:3]))
    ctx.close()

    # ── [C] 流程②逐句听写 p067（随机 5 句全对样本） ──
    print("[C] 逐句听写 p067（随机抽句 + 逐词判分）")
    errs = []
    ctx, pg = new_page(b, errs)
    pg.goto(BASE + "/篇章页/读写_067_sportwonders.html", wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    pg.click("#tabDictate")
    pg.wait_for_timeout(150)
    chk("切到流程②", pg.evaluate("()=>state.flow==='dictate'") and not pg.eval_on_selector("#viewDictate", "e=>e.classList.contains('hide')"))
    pg.select_option("#countSel", "5")
    pg.click("#startBtn")
    pg.wait_for_timeout(200)
    chk("听写运行器出现（5 句队列）", not pg.eval_on_selector("#dRunner", "e=>e.classList.contains('hide')") and "5" in (pg.eval_on_selector("#dPos", "e=>e.textContent") or ""))
    all_right = True
    for k in range(5):
        sent = pg.evaluate("()=>SEGS[D.queue[D.qi]].t")
        pg.fill("#dInput", sent)
        pg.click("#dSubmit")
        pg.wait_for_timeout(150)
        verdict = pg.eval_on_selector("#dVerdict", "e=>e.textContent")
        if "完全正确" not in verdict: all_right = False
        pg.click("#dNext"); pg.wait_for_timeout(150)
    chk("5 句全对判分", all_right)
    chk("汇总页出现 100%", not pg.eval_on_selector("#dSummary", "e=>e.classList.contains('hide')") and "100%" in pg.eval_on_selector("#sumPct", "e=>e.textContent"))
    chk("tf_stage_67.dictate 落盘", pg.evaluate("()=>JSON.parse(localStorage.getItem('tf_stage_67')).dictate") == True)
    chk("流程②无 JS 异常", len(errs) == 0, str(errs[:3]))
    ctx.close()

    # ── [D] 深链 ?flow=dictate 直接落流程② ──
    print("[D] 深链 ?flow=dictate")
    errs = []
    ctx, pg = new_page(b, errs)
    pg.goto(BASE + "/篇章页/读写_096_sportsachievers.html?flow=dictate", wait_until="domcontentloaded")
    pg.wait_for_timeout(800)
    chk("落在流程②设置面板", pg.evaluate("()=>state.flow==='dictate'") and not pg.eval_on_selector("#dSetup", "e=>e.classList.contains('hide')"))
    chk("p096 段落芯片=5 段", pg.eval_on_selector_all("#paraChips .chip", "es=>es.length") == 5)
    chk("流程②深链无 JS 异常", len(errs) == 0, str(errs[:3]))
    ctx.close()

    b.close()

print("结果：%d 通过 / %d 失败" % (ok, fail))
sys.exit(0 if fail == 0 else 1)
