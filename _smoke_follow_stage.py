# -*- coding: utf-8 -*-
"""跟读支架化验证：跟句 → 影子跟读（index.html 两步状态机）

学生端已砍掉登录：直接打开 index.html 即可，身份由本地姓名闸口决定。"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
ok = fail = 0
def chk(name, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("  OK  " + name + ("   " + extra if extra else ""))
    else: fail += 1; print("  XX  " + name + "   " + extra)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1300, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))

    # 无登录直开；预先写入本地姓名，避免姓名闸口遮挡交互
    ctx.add_init_script("try{localStorage.setItem('tf_current_student','冒烟同学');}catch(e){}")
    pg.goto(BASE + "/index.html?pg=66", wait_until="domcontentloaded"); pg.wait_for_timeout(1400)
    print("[0] 直开学生端 URL:", pg.url,
          "| 未跳登录页:", "login.html" not in pg.url)

    print("[1] 两阶段入口")
    n = pg.eval_on_selector_all("#fpass .fpc", "es=>es.length")
    chk("步骤芯片共 2 个", n == 2, "实际 %d" % n)
    titles = pg.eval_on_selector_all("#fpass .fpc", "es=>es.map(e=>e.getAttribute('title')||'')")
    chk("芯片语义 = 跟句 / 影子跟读",
        "跟句" in titles[0] and "影子跟读" in titles[1],
        " | ".join(t[:18] for t in titles))

    print("[2] 句级时间轴（意群已下线）")
    tl = pg.evaluate("()=>{var a=TL[state.pg]; return {n:a.length, first:[+a[0][0].toFixed(3),+a[0][1].toFixed(3)]};}")
    chk("pg66 有句级时间轴", tl["n"] > 0, "句数=%s" % tl["n"])
    chk("第 1 句区间有效", tl["first"][0] < tl["first"][1], str(tl["first"]))
    chk("CHUNKS 已移除", pg.evaluate("()=>typeof DB.CHUNKS==='undefined' && typeof CHUNKS==='undefined'"))

    print("[3] 手动切步 + UI 同步")
    for s, lbl, cnt in [(1, "句", None), (2, "全篇", "全文")]:
        pg.click('#fpass .fpc[data-s="%d"]' % s); pg.wait_for_timeout(250)
        st = pg.evaluate("""()=>({
          f: FOL.fstep,
          on: (document.querySelector('#fpass .fpc.on')||{dataset:{}}).dataset.s,
          lbl: (document.querySelector('#dkCntR .lbl')||{}).textContent,
          cnt: (document.getElementById('dkS')||{}).textContent })""")
        chk("切到第 %d 步" % s, st["f"] == s and int(st["on"] or 0) == s, json.dumps(st, ensure_ascii=False))
        chk("  标签为「%s」" % lbl, st["lbl"] == lbl, "实际 %s" % st["lbl"])
        if cnt: chk("  计数为「%s」" % cnt, st["cnt"] == cnt, "实际 %s" % st["cnt"])

    print("[4] 自动进阶")
    pg.evaluate("()=>beginFollowStep2()"); pg.wait_for_timeout(200)
    chk("beginFollowStep2 → 第 2 步（影子）", pg.evaluate("()=>FOL.fstep") == 2)
    chk("第 2 步为全文影子", pg.evaluate("()=>{var t=TL[state.pg];return FOL.start<=t[0][0]+1e-6;}"))

    print("[5] 暂停间隙引导开口")
    pg.evaluate("()=>showGap(2,'该你开口 · 测试',function(){})"); pg.wait_for_timeout(250)
    gap = pg.evaluate("""()=>{var g=document.getElementById('fsGap');
      return {on: !!(g&&g.classList.contains('on')), txt: g? g.innerText.replace(/\\s+/g,' ').trim():null};}""")
    chk("间隙提示层出现", gap["on"], str(gap["txt"])[:60])
    pg.evaluate("()=>cancelGap()"); pg.wait_for_timeout(200)
    chk("间隙提示层可关闭", not pg.evaluate("()=>!!(document.getElementById('fsGap')||{}).classList.contains('on')"))

    print("[6] 两步完成 → 进入听写")
    pg.evaluate("()=>followWholeEnd()"); pg.wait_for_timeout(400)
    fin = pg.evaluate("()=>({follow: !!(typeof PROG!=='undefined' && PROG.follow), stage: (typeof state!=='undefined'&&state.stage)||null})")
    chk("标记跟读完成", fin["follow"], json.dumps(fin, ensure_ascii=False))
    chk("自动进入听写阶段", fin["stage"] == "dictate", "stage=%s" % fin["stage"])

    print("[7] 运行时错误")
    chk("页面无 JS 异常", len(errs) == 0, str(errs[:4]))

    b.close()

print("\n结果：%d 通过 / %d 失败" % (ok, fail))
sys.exit(1 if fail else 0)
