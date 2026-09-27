# -*- coding: utf-8 -*-
"""跟读支架化验证：跟意群 → 跟句 → 影子跟读（index.html 三步状态机）"""
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

    # 先登录（真实会话），再进点读页
    pg.goto(BASE + "/login.html", wait_until="domcontentloaded"); pg.wait_for_timeout(500)
    pg.fill("#name", "张小美"); pg.fill("#pass", "1234"); pg.click("#loginBtn")
    pg.wait_for_timeout(2000)
    print("[0] 登录后 URL:", pg.url,
          "| 提示:", pg.evaluate("()=>(document.getElementById('err')||{}).textContent||''"),
          "| 已拿令牌:", pg.evaluate("()=>!!localStorage.getItem('tf_token')"))
    pg.goto(BASE + "/index.html?pg=66", wait_until="domcontentloaded"); pg.wait_for_timeout(1400)

    print("[1] 三阶段入口")
    n = pg.eval_on_selector_all("#fpass .fpc", "es=>es.length")
    chk("步骤芯片共 3 个", n == 3, "实际 %d" % n)
    titles = pg.eval_on_selector_all("#fpass .fpc", "es=>es.map(e=>e.getAttribute('title')||'')")
    chk("芯片语义 = 跟意群 / 跟句 / 影子跟读",
        "跟意群" in titles[0] and "跟句" in titles[1] and "影子跟读" in titles[2],
        " | ".join(t[:18] for t in titles))

    print("[2] 意群切分数据")
    ch = pg.evaluate("()=>{var c=(DB.CHUNKS||{})['66']; return c? c.map(x=>x.length): null;}")
    chk("pg66 存在 CHUNKS", bool(ch), "句数=%s" % (len(ch) if ch else 0))
    fc = pg.evaluate("()=>{var a=folChunks(0); return a? a.map(x=>[+x[0].toFixed(2),+x[1].toFixed(2)]): null;}")
    chk("第 1 句可切出意群块", bool(fc) and len(fc) >= 1, "第1句意群=%s" % json.dumps(fc))

    print("[3] 手动切步 + UI 同步")
    for s, lbl, cnt in [(1, "意群", None), (2, "句", None), (3, "全篇", "全文")]:
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
    chk("beginFollowStep2 → 第 2 步", pg.evaluate("()=>FOL.fstep") == 2)
    pg.evaluate("()=>beginFollowStep3()"); pg.wait_for_timeout(200)
    chk("beginFollowStep3 → 第 3 步", pg.evaluate("()=>FOL.fstep") == 3)

    print("[5] 暂停间隙引导开口")
    pg.evaluate("()=>showGap(2,'该你开口 · 测试',function(){})"); pg.wait_for_timeout(250)
    gap = pg.evaluate("""()=>{var g=document.getElementById('fsGap');
      return {on: !!(g&&g.classList.contains('on')), txt: g? g.innerText.replace(/\\s+/g,' ').trim():null};}""")
    chk("间隙提示层出现", gap["on"], str(gap["txt"])[:60])
    pg.evaluate("()=>cancelGap()"); pg.wait_for_timeout(200)
    chk("间隙提示层可关闭", not pg.evaluate("()=>!!(document.getElementById('fsGap')||{}).classList.contains('on')"))

    print("[6] 三步完成 → 进入听写")
    pg.evaluate("()=>followWholeEnd()"); pg.wait_for_timeout(400)
    fin = pg.evaluate("()=>({follow: !!(typeof PROG!=='undefined' && PROG.follow), stage: (typeof state!=='undefined'&&state.stage)||null})")
    chk("标记跟读完成", fin["follow"], json.dumps(fin, ensure_ascii=False))
    chk("自动进入听写阶段", fin["stage"] == "dictate", "stage=%s" % fin["stage"])

    print("[7] 运行时错误")
    chk("页面无 JS 异常", len(errs) == 0, str(errs[:4]))

    b.close()

print("\n结果：%d 通过 / %d 失败" % (ok, fail))
sys.exit(1 if fail else 0)