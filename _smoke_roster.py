# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright
BASE="http://localhost:8000"
def log(*a): print(*a, flush=True); sys.stdout.flush()

def gate_login(pg, role, name, pwd):
    pg.goto(BASE+"/教师端.html", wait_until="domcontentloaded")
    pg.wait_for_timeout(400)
    pg.select_option("#roleSel", role)
    if role=="assistant":
        pg.fill("#name","助教")
    else:
        pg.fill("#name", name)
    pg.fill("#pass", pwd)
    pg.click("#loginBtn")
    try:
        pg.wait_for_function("document.getElementById('gate').className.indexOf('hide')>=0 && !!document.getElementById('accountBar') && document.getElementById('accountBar').style.display!=='none'", timeout=8000)
    except Exception as e:
        return "LOGIN_FAILED:"+pg.evaluate("document.getElementById('lErr').textContent")
    pg.wait_for_function("document.getElementById('unitPick') && document.getElementById('unitPick').children.length>0", timeout=8000)
    return "ok"

with sync_playwright() as p:
    b=p.chromium.launch()
    ctxT=b.new_context()
    t=ctxT.new_page(); errs=[]
    t.on("pageerror", lambda e: errs.append(str(e)))
    st = gate_login(t,"teacher","teacher","think-teacher")
    log("[1] 教师登录:", st)
    if st!="ok":
        log("[!] 教师端登录失败，JS错误:", errs); b.close(); sys.exit(2)

    # 切换班级与学生页
    t.click(".tab[data-p='roster']")
    t.wait_for_timeout(900)
    log("[2] 班级列表:", t.evaluate("document.getElementById('classTable').innerText").replace(chr(10),' | '))

    # 建班
    t.fill("#newClass","冒烟测试班")
    t.click("#addClassBtn")
    t.wait_for_timeout(600)
    cls_txt=t.evaluate("document.getElementById('classTable').innerText")
    log("[3] 建班后含 冒烟测试班:", "冒烟测试班" in cls_txt)

    # 新增学生并分班
    t.select_option("#newStuClass", label="冒烟测试班")
    t.fill("#newStuName","测试学生X"); t.fill("#newStuPass","abcd")
    t.click("#addStuBtn")
    t.wait_for_timeout(700)
    stu_txt=t.evaluate("document.getElementById('stuTable').innerText")
    log("[4] 学生表含 测试学生X:", "测试学生X" in stu_txt and "冒烟测试班" in stu_txt)

    # 单元预览：新标签页打开学生端
    with ctxT.new_page() as prev:
        prev.goto(BASE+"/学生端.html?unit=7", wait_until="domcontentloaded")
        prev.wait_for_timeout(1200)
        un=prev.evaluate("document.getElementById('unitName').textContent")
        apps=prev.evaluate("!!document.getElementById('vwGrid').children.length && !!document.getElementById('pgGrid').children.length")
        log("[5] 单元预览打开的单元:", un, "| 主题词+篇章已渲染:", apps)

    # 学情按班筛选（切换到学情页，选冒烟测试班，不报错）
    t.click(".tab[data-p='data']")
    t.wait_for_timeout(700)
    opts=t.evaluate("Array.from(document.getElementById('dataClassFilter').options).map(o=>o.text)")
    log("[6] 学情班级筛选选项:", opts)

    # 清理：删除本轮夹具（班级名/学生名唯一，不清理会让下一轮的新建路径形同虚设）
    cleaned = t.evaluate("""(async function(){
      var H={'Authorization':'Bearer '+localStorage.getItem('tf_token'),'Content-Type':'application/json'};
      var n=0;
      var st=await fetch('/api/students',{headers:H}).then(r=>r.json());
      var sids=(st.students||[]).filter(s=>s.name==='测试学生X').map(s=>s.id);
      for(var i=0;i<sids.length;i++){ await fetch('/api/students/delete',{method:'POST',headers:H,body:JSON.stringify({id:sids[i]})}); n++; }
      var cs=await fetch('/api/classes',{headers:H}).then(r=>r.json());
      var cids=(cs.classes||[]).filter(c=>c.name==='冒烟测试班').map(c=>c.id);
      for(var j=0;j<cids.length;j++){ await fetch('/api/classes/delete',{method:'POST',headers:H,body:JSON.stringify({id:cids[j]})}); n++; }
      return n;
    })();""")
    log("[8] 已清理夹具:", cleaned, "项")

    b.close()

    # 助教：只读
    b2=p.chromium.launch(); ctxA=b2.new_context(); a=ctxA.new_page()
    gate_login(a,"assistant","助教","think-assist")
    a.wait_for_timeout(800)
    a.click(".tab[data-p='roster']")
    a.wait_for_timeout(800)
    disabled=a.evaluate("!!(document.getElementById('addStuBtn').disabled)")
    has_del=a.evaluate("document.getElementById('classTable').innerText.includes('删除')")
    has_studel=a.evaluate("document.getElementById('stuTable').innerText.includes('重置口令')")
    log("[7] 助教只读：新增学生按钮禁用=%s, 班级删除按钮=%s, 学生重置按钮=%s" % (disabled, has_del, has_studel))
    b2.close()

    log("教师端 JS错误:", errs)
    log("DONE")