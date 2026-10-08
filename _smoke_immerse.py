# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright
BASE="http://localhost:8000"
def log(*a): print(*a, flush=True); sys.stdout.flush()
with sync_playwright() as p:
    b=p.chromium.launch()
    ctx=b.new_context(); pg=ctx.new_page(); errs=[]
    pg.on("pageerror", lambda e: errs.append(str(e)))
    # 学生端已砍掉登录：预置本地姓名后直开单元 7（任务由匿名只读接口拉取）
    pg.add_init_script("try{localStorage.setItem('tf_current_student','张小美');}catch(e){}")
    pg.goto(BASE+"/index.html?unit=7", wait_until="domcontentloaded")
    pg.wait_for_function("!!document.querySelector('#taskzone .tz-row')", timeout=10000)
    pg.wait_for_timeout(600)
    probe=pg.evaluate("""(function(){
      var z=document.getElementById('taskzone');
      return JSON.stringify({
        hero: !!z.querySelector('.tz-hero'),
        ring: !!z.querySelector('.tz-ring svg'),
        stages: z.querySelectorAll('.tz-stage').length,
        stageRows: [].map.call(z.querySelectorAll('.tz-stage'),function(s){return s.querySelectorAll('.tz-row').length;}).join(','),
        rowsText: z.querySelectorAll('.tz-row .i-tl').length,
        head: (z.querySelector('.tz-title')||{}).textContent||'',
        msg: (z.querySelector('.tz-msg')||{}).textContent||'',
        total: (z.querySelector('.tz-ring text.gm'))? '' : z.querySelectorAll('.tz-ring text')[0]&&z.querySelectorAll('.tz-ring text')[1].textContent
      });
    })();""")
    log("[1] 沉浸式渲染:", probe)
    # 点击任务行 → 触发材料跳转。优先选带 data-mode 的引擎行；只有主题行时退回主题行
    clicked=pg.evaluate("""(function(){
      var z=document.getElementById('taskzone');
      var r=z.querySelector('.tz-row[data-mode]') || z.querySelector('.tz-row');
      if(!r) return "no-row";
      r.click();
      return r.dataset.mode ? ('clicked '+r.dataset.mode) : 'clicked theme-row';
    })();""")
    pg.wait_for_timeout(600)
    log("[2] 点击任务行:", clicked, "| JS错误:", errs)
    b.close()
    log("DONE")
