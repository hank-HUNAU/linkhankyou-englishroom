# -*- coding: utf-8 -*-
import sys, json
from playwright.sync_api import sync_playwright
BASE="http://localhost:8000"
def log(*a): print(*a, flush=True); sys.stdout.flush()
with sync_playwright() as p:
    b=p.chromium.launch()
    # ── 教师端：确保单元7有复习任务 ──
    t=b.new_context(); tp=t.new_page(); terr=[]
    tp.on("pageerror", lambda e: terr.append(str(e)))
    tp.goto(BASE+"/教师端.html", wait_until="domcontentloaded"); tp.wait_for_timeout(600)
    if tp.query_selector("#gate"):
        tp.fill("#name","teacher"); tp.fill("#pass","think-teacher"); tp.click("#loginBtn")
        tp.wait_for_function("!!localStorage.getItem('tf_token')", timeout=10000)
    tp.wait_for_timeout(900)
    saw = tp.evaluate("""(function(){
      var A=JSON.parse(localStorage.getItem('tf_assignments')||'{}');
      var u=A['7']||{}; // 学生端单元 key
      return JSON.stringify(u);
    })();""")
    log("[教师] tf_assignments[unit7] 当前(本地):", saw)
    written = tp.evaluate("""(async function(){
      var tok=localStorage.getItem('tf_token');
      var r=await fetch('/api/kv',{headers:{Authorization:'Bearer '+tok}});
      var d=await r.json();
      var A=JSON.parse(d.rows['tf_assignments']||'{}');
      var u=A['7']||{};
      if(!u.preview) u.preview={items:[],deadline:'2026-10-01T18:00'};
      if(!u.preview.items||!u.preview.items.length) u.preview.items=[{id:'theme',kind:'theme',passageKey:null,engines:[]}];
      if(!u.review) u.review={items:[],deadline:'2026-10-01T18:00'};
      if(!u.review.items||!u.review.items.length) u.review.items=[{id:'theme',kind:'theme',passageKey:null,engines:[]}];
      A['7']=u;
      await fetch('/api/kv',{method:'POST',headers:{Authorization:'Bearer '+tok,'Content-Type':'application/json'},
        body:JSON.stringify([{op:'set',scope:'global',key:'tf_assignments',value:JSON.stringify(A)}])});
      return 'ok preview='+JSON.stringify(u.preview.items)+' review='+JSON.stringify(u.review.items);
    })();""")
    tp.wait_for_timeout(400)
    log("[教师] 写回全局:", written, "| JS错误:", terr)
    t.close()

    # ── 学生端：张小美 打开单元7，完成预习全部 → 验证衔接条 ──
    s=b.new_context(); sp=s.new_page(); serr=[]
    sp.on("pageerror", lambda e: serr.append(str(e)))
    sp.goto(BASE+"/login.html", wait_until="domcontentloaded"); sp.wait_for_timeout(300)
    sp.fill("#name","张小美"); sp.fill("#pass","1234"); sp.click("#loginBtn")
    sp.wait_for_function("location.pathname.indexOf('学生端')>=0 || !!document.getElementById('shelf')", timeout=8000)
    sp.wait_for_timeout(900)
    sp.goto(BASE+"/学生端.html?unit=7", wait_until="domcontentloaded"); sp.wait_for_timeout(1300)
    # 打印当前任务结构
    pre0=sp.evaluate("""(function(){
      var A=JSON.parse(localStorage.getItem('tf_assignments')||'{}');
      var u=A['7']||{};
      return JSON.stringify({preview:(u.preview||{}).items, review:(u.review||{}).items});
    })();""")
    log("[学生] 水合后任务: ", pre0)
    # 完成预习：点主题词汇的√（若未完成）
    sp.evaluate("""(function(){
      var m=document.querySelector('#taskzone .tre .tz-mark');
      var txt=m.closest('.tz-row').querySelector('.i-cta').textContent;
      if(m && txt.trim()!=='已完成'){ m.click(); }
    })();""")
    sp.wait_for_timeout(600)
    st=sp.evaluate("""(function(){
      var z=document.getElementById('taskzone');
      var g=document.getElementById('tzGuide');
      return JSON.stringify({
        hero: !!z.querySelector('.tz-hero'),
        previewStageDoneBadge: (z.querySelector('.tre .tz-sh-t b')||{}).textContent||'',
        guideOn: !!g,
        guideGo: !!(g&&g.querySelector('#tzGuideGo')),
        guideLater: !!(g&&g.querySelector('#tzGuideLater')),
        bridge: z.querySelector('.bridge') ? z.querySelector('.bridge').innerText : null,
        hasReview: !!z.querySelector('#tzReview'),
        reviewRows: z.querySelectorAll('#tzReview .tz-row').length,
        ringTotal: z.querySelectorAll('.tz-ring text')[1] && z.querySelectorAll('.tz-ring text')[1].textContent
      });
    })();""")
    log("[学生] 衔接状态:", st)
    clickRes=sp.evaluate("""(function(){
      var g=document.getElementById('tzGuide');
      var go=g&&g.querySelector('#tzGuideGo');
      if(go){ go.click(); return 'guide-cta-clicked'; }
      var b=document.getElementById('tzBridgeGo');
      if(b){ b.click(); return 'bridge-cta-clicked'; }
      return 'no-cta';
    })();""")
    sp.wait_for_timeout(900)
    jump=sp.evaluate("""(function(){
      var g=document.getElementById('tzGuide');
      var r=document.getElementById('tzReview');
      return JSON.stringify({
        guideClosed: !g || !g.classList.contains('on'),
        guideRemoved: !document.getElementById('tzGuide'),
        reviewJumped: r ? r.classList.contains('jump') : false,
        seenFlag: sessionStorage.getItem('tf_guide_7')||''
      });
    })();""")
    log("[学生] CTA点击:", clickRes, "| 点击后:", jump, "| JS错误:", serr)
    b.close()
    log("DONE")