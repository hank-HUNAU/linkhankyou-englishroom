# -*- coding: utf-8 -*-
import os, json, sys, time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
def log(*a): print(*a, flush=True); sys.stdout.flush()

def do_login(page, role, name, pwd):
    page.goto(BASE + "/login.html", wait_until="domcontentloaded")
    page.wait_for_timeout(300)
    if role == "teacher":
        page.evaluate("document.getElementById('roleTeacher').click()")
    page.fill("#name", name)
    page.fill("#pass", pwd)
    page.click("#loginBtn")
    selector = "document.getElementById('app') || document.getElementById('shelf')"
    page.wait_for_function(selector, timeout=6000)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctxTeacher = b.new_context()   # 设备A：教师机
    ctxStudent = b.new_context()   # 设备B：学生机（独立 localStorage → 模拟换设备）

    t = ctxTeacher.new_page()
    do_login(t, "teacher", "teacher", "think-teacher")
    t.wait_for_timeout(700)
    log("[1] 教师端已登录；当前账号:", t.evaluate("JSON.parse(localStorage.getItem('tf_user')).name"))

    # 教师分配任务：Unit7 预习含 主题词汇 + p67(词汇+跟读)，设截止时间并保存
    t.click("#preAddTheme")
    t.evaluate("""(function(){
      var b=document.querySelector('#pickerHost [data-k="u7_p67_sportwonders"][data-tb="preview"]');
      if(b) b.click();
    })();""")
    t.fill("#preDeadline", "2026-10-01T18:00")
    t.click("#saveAssign")
    t.wait_for_timeout(900)   # 等 store.js flush(fetch到服务器, scope=global)
    saved = t.evaluate("fetch('/api/kv',{headers:{Authorization:'Bearer '+localStorage.getItem('tf_token')}}).then(r=>r.json()).then(o=>JSON.stringify(o.rows['tf_assignments']))")
    log("[2] 服务器端 tf_assignments(全局) 是否已含 p67+主题:", saved and "u7_p67_sportwonders" in saved)

    # 学生登录（另一台设备）
    s = ctxStudent.new_page()
    do_login(s, "student", "张小美", "1234")
    s.wait_for_timeout(900)
    log("[3] 学生端已登录:", s.evaluate("JSON.parse(localStorage.getItem('tf_user')).name"))

    # 学生端书架是否已水合到全局任务
    s.wait_for_timeout(300)
    dbg = s.evaluate("""(async function(){
      var tok = localStorage.getItem('tf_token');
      var kv = await fetch('/api/kv',{headers:{Authorization:'Bearer '+tok}}).then(r=>r.json());
      return JSON.stringify({
        local_tf: !!localStorage.getItem('tf_assignments'),
        server_has_assign: !!(kv.rows && kv.rows['tf_assignments'])
      });
    })();""")
    log("[3.5] 学生端水合检查:", dbg)
    s.evaluate("""(function(){var c=document.querySelectorAll('#shelf .book');for(var i=0;i<c.length;i++){if(c[i].dataset.k==='7'){c[i].click();return;}}})();""")
    s.wait_for_timeout(600)
    dbg2 = s.evaluate("""(function(){
      var A = JSON.parse(localStorage.getItem('tf_assignments')||'{}');
      var p = (A['7']&&A['7']['preview'])||{};
      var zone = document.getElementById('taskzone');
      return JSON.stringify({items:p.items, deadline:p.deadline, zoneHtml:(zone?zone.innerHTML:'').slice(0,200)});
    })();""")
    log("[3.6] 解析任务+任务区:", dbg2)
    tz = s.evaluate("document.getElementById('taskzone').innerText")
    log("[4] 学生端看到教师下发的任务+截止:", ("预习任务" in tz) and ("10-01" in tz))
    log(tz[:120])

    # 学生打开 p67 词汇 → 上报 started；再标记完成
    s.evaluate("""(function(){var it=document.querySelector('#taskzone [data-id="u7_p67_sportwonders"][data-mode="vocab"]');if(it)it.click();})();""")
    s.wait_for_timeout(300)
    s.evaluate("""(function(){var mk=document.querySelector('[data-id="u7_p67_sportwonders"][data-mark="1"]');if(mk)mk.click();})();""")
    s.wait_for_timeout(900)   # flush 上报
    log("[5] 学生已上报 started+done")

    # 教师（不同设备）查学情
    t.bring_to_front()
    t.click(".tab[data-p='data']")
    t.wait_for_timeout(800)
    t.evaluate("""(function(){var b=document.querySelector("#dataTypeTabs .tab[data-t='preview']");if(b)b.click();})();""")
    t.wait_for_timeout(800)
    tbl = t.evaluate("document.getElementById('dataTable').innerText")
    log("[6] 教师端(另一台设备)汇总学生学情:")
    log(tbl)

    b.close()
    log("DONE")