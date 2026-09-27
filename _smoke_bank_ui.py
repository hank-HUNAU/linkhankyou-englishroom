# -*- coding: utf-8 -*-
"""题库分析闭环验证：播种学生作答 → 教师端「题库分析」页签渲染难度/区分度/待审校 → 清理"""
import io, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000"
ok = fail = 0
def chk(name, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("  OK  " + name + ("   " + extra if extra else ""))
    else: fail += 1; print("  XX  " + name + "   " + extra)

# 3 道题 × 10 名学生：climb 全对(偏易) / board 8 对 / record 仅 1 对(偏难+歧义)
ITEMS = [("climb", 0, ["游泳", "跳跃", "滑行"]), ("board", 2, ["游泳", "跳跃", "滑行"]), ("record", 9, ["游泳", "跳跃", "滑行"])]
CORRECT = {"climb": "攀登，攀爬", "board": "登上（交通工具）", "record": "记录；纪录"}

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1400, "height": 950})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))

    # ── 1) 播种：注册临时学生 + 写 GR_records_v2 ──
    pg.goto(BASE + "/login.html", wait_until="domcontentloaded"); pg.wait_for_timeout(300)
    temp = pg.evaluate("""(async (payload)=>{
      var items=payload.items, correct=payload.correct;
      var made=[];
      for(var j=0;j<10;j++){
        var nm='题库冒烟'+Date.now().toString().slice(-6)+'_'+j;
        var r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({name:nm,pass:'bank1234'})});
        var d=await r.json(); if(!d.ok) return {err:'注册失败 '+JSON.stringify(d)};
        var tok=d.token, rec={};
        items.forEach(function(it){
          var id=it[0], t=it[1], distr=it[2];
          var c = j>=t;
          var picked = c ? correct[id] : distr[j%2];      // 只用前 2 个干扰项 → 第 3 个从未被选(deadOpt)
          rec[id]={ status:'unknown', testHistory:[{ itemId:id+'#unknown', mode:'unknown',
            correct:c, skipped:false, opts:[correct[id]].concat(distr), picked:picked,
            errorType: c?null:'meaning', testedAt:Date.now() }] };
        });
        await fetch('/api/kv',{method:'POST',headers:{'Authorization':'Bearer '+tok,'Content-Type':'application/json'},
          body:JSON.stringify([{op:'set',key:'GR_records_v2',value:JSON.stringify(rec)}])});
        made.push({id:d.user.id, name:nm});
      }
      return {made:made};
    })""", {"items": ITEMS, "correct": CORRECT})
    if temp.get("err"):
        print("播种失败:", temp["err"]); b.close(); sys.exit(2)
    made = temp["made"]
    print("[1] 播种 10 名学生作答: %d 名" % len(made))

    # ── 2) 教师端：切到题库分析 ──
    pg.goto(BASE + "/login.html", wait_until="domcontentloaded"); pg.wait_for_timeout(300)
    pg.click("#roleTeacher")
    pg.fill("#name", "teacher"); pg.fill("#pass", "think-teacher"); pg.click("#loginBtn")
    pg.wait_for_timeout(2200)
    print("[2] 教师登录后 URL:", pg.url.split("/")[-1], "| 提示:", pg.evaluate("()=>(document.getElementById('err')||{}).textContent||''"))
    pg.click('.tab[data-p="bank"]')
    pg.wait_for_timeout(2500)

    st = pg.evaluate("""()=>{
      var pane=document.getElementById('panel-bank');
      var sum=document.getElementById('bankSummary');
      var tbl=document.querySelector('#bankTable table.bank-tbl');
      return {
        on: !!(pane&&pane.classList.contains('on')),
        tabOn: !!document.querySelector('.tab.on[data-p="bank"]'),
        sumCards: sum? sum.querySelectorAll('.bs-card').length : 0,
        sumText: sum? sum.innerText.replace(/\\s+/g,' ').trim().slice(0,160):'',
        rows: tbl? tbl.querySelectorAll('tbody tr').length : 0,
        head: tbl? [].map.call(tbl.querySelectorAll('thead th'),function(t){return t.textContent.trim();}) : [],
        flaggedCells: tbl? tbl.querySelectorAll('.fl.warn').length : 0
      };
    }""")
    print("[3] 页签状态:", json.dumps({k: st[k] for k in ["on", "tabOn", "sumCards", "rows", "flaggedCells"]}, ensure_ascii=False))
    print("    表头:", " | ".join(st["head"]))
    print("    汇总:", st["sumText"])

    chk("题库分析页签已激活", st["on"] and st["tabOn"])
    chk("汇总卡片已渲染", st["sumCards"] >= 3, "卡片数=%d" % st["sumCards"])
    chk("难度/区分度表格有数据行", st["rows"] >= 3, "行数=%d" % st["rows"])
    chk("存在待审校标记", st["flaggedCells"] >= 1, "标记数=%d" % st["flaggedCells"])
    chk("表头含难度与区分度", any("难度" in h for h in st["head"]) and any("区分度" in h for h in st["head"]), " | ".join(st["head"]))
    chk("教师端无 JS 异常", len(errs) == 0, str(errs[:3]))

    # ── 3) 清理 ──
    pg.evaluate("""(async (ids)=>{
      var tok=localStorage.getItem('tf_token');
      for(var i=0;i<ids.length;i++){
        await fetch('/api/students/delete',{method:'POST',headers:{'Authorization':'Bearer '+tok,'Content-Type':'application/json'},
          body:JSON.stringify({id:ids[i]})});
      }
    })""", [m["id"] for m in made])
    print("[4] 已清理 %d 名临时学生" % len(made))
    b.close()

print("\n结果：%d 通过 / %d 失败" % (ok, fail))
sys.exit(1 if fail else 0)