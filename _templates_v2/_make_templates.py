# -*- coding: utf-8 -*-
"""三模板拆分脚本：_legacy_follow_v1/_模板_跟读页.html → _templates_v2/{预习,复习,听写}_模板.html

拆分原则（2026-10-16 定案）：
- 全量内联数据块（DB.ZH/DB.TL/DB.ENTITY/.../BOOK/BOOKU12）、TYPES/UNIT_GROUPS、
  听写词性表 FUNCTION/NUMB、pickCustom 长内联 HTML：一律从 v1 原文按标记提取，逐字保留。
- JS 逻辑按环节重组：预习=聆听+盲听答题板；复习=逐句跟读+间隙生词提示；听写=抽句三方式。
- 补齐 v1 缺失的 escQ 定义与 .blind/.quiz-banner/.quiz-opt/.nb-* 样式（差异清单已记录）。
- 新增 __SIBLINGS__ 注入点：本篇三页互链（预习↔复习↔听写）。
用法：python _make_templates.py
"""
import os, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # codex-handoff
V1 = os.path.join(ROOT, "_legacy_follow_v1", "_模板_跟读页.html")
src = open(V1, encoding="utf-8").read()
lines = src.split("\n")                            # 0-based

def find_line(pred, desc, start=0):
    for i in range(start, len(lines)):
        if pred(lines[i]):
            return i
    raise SystemExit("未找到标记行: " + desc)

def extract(pred_start, pred_end, desc):
    a = find_line(pred_start, desc + " 起始")
    b = find_line(pred_end, desc + " 结束", start=a)
    assert b >= a, desc
    return "\n".join(lines[a:b+1])

# ---- 从 v1 逐字提取的共用块 ----
CSS = extract(lambda l: l.strip() == "<style>", lambda l: l.startswith(".qz-submit:disabled"), "CSS")
assert CSS.startswith("<style>") and ":root" in CSS and ".qz-submit:disabled" in CSS

DATA = extract(lambda l: l.startswith('var DB={"ZH"'), lambda l: l.strip() == "Object.assign(BOOK, BOOKU12);", "全量数据块")
assert "DB.TL=" in DATA and "Object.assign(BOOK, BOOKU12);" in DATA

FUNC_NUMB = extract(lambda l: "听写：全句挖空逐词填" in l, lambda l: l.startswith("var NUMB={};"), "FUNCTION/NUMB 词表")
assert FUNC_NUMB.count("var FUNCTION") == 1 and FUNC_NUMB.rstrip().endswith("NUMB[w]=1;});")

PICKCUSTOM = extract(lambda l: l.startswith("function pickCustom(){"), lambda l: l.strip() == 'pc.classList.add("on");', "pickCustom")
assert PICKCUSTOM.rstrip().endswith('pc.classList.add("on");')

TYPES = extract(lambda l: l.strip() == "var TYPES={", lambda l: l.strip() == "};", "TYPES")
assert "rt:{n:" in TYPES and "pd:{n:" in TYPES

UG = extract(lambda l: l.startswith("var UNIT_GROUPS={"), lambda l: l.strip() == "};", "UNIT_GROUPS")
assert '7:{label:"Unit 7"' in UG

# ---- v2 新增补齐样式（v1 缺失：盲听遮罩/答题横幅/答题选项/听写本浮层） ----
CSS_EXTRA = """
/* == v2 补齐（v1 缺失样式）：盲听遮罩 / 答题横幅 / 答题选项 / 听写本浮层 == */
#body.blind{filter:blur(9px);pointer-events:none;user-select:none;transition:filter .3s}
.quiz-banner{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 16px;margin:0 0 12px;background:#fff8e6;border:1.5px solid #f2c94c;border-radius:14px;font-size:13.5px;font-weight:700;color:#7a5800}
.quiz-banner button{border:none;background:#f2b706;color:#fff;font-weight:800;font-size:13px;padding:7px 16px;border-radius:16px;cursor:pointer;font-family:var(--font)}
.quiz-banner.hide{display:none}
.quiz-prog{font-size:12.5px;font-weight:700;color:var(--ink-3);margin-bottom:8px}
.quiz-opts{display:flex;gap:8px;flex-wrap:wrap}
.quiz-opt{border:1.5px solid var(--line);background:var(--card);border-radius:10px;padding:9px 14px;font-size:14px;font-weight:600;cursor:pointer;font-family:var(--font);color:var(--ink);text-align:left}
.quiz-opt:hover{border-color:var(--blue)}
.quiz-opt.ok{border-color:var(--green);background:var(--green-bg);color:var(--green-deep);font-weight:800}
.quiz-opt.no{border-color:var(--red);background:var(--red-bg);color:var(--red);font-weight:700}
.nb-ov{position:fixed;inset:0;z-index:1500;background:rgba(15,18,34,.55);display:none;align-items:flex-start;justify-content:center;padding:16px;overflow:auto}
.nb-ov.on{display:flex}
.nb-card{background:#fff;border-radius:20px;max-width:640px;width:100%;padding:18px}
.nb-words{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 12px}
.nb-w{border:1.5px solid var(--line);border-radius:9px;padding:5px 11px;font-size:14px;cursor:pointer;user-select:none;background:var(--bg-soft)}
.nb-w.mark{background:var(--red-bg);border-color:var(--red);color:#c2261c;text-decoration:line-through;font-weight:700}
.nb-tip{font-size:13px;line-height:1.75;color:var(--ink-2);background:var(--bg-soft);border-radius:10px;padding:10px 12px;margin:10px 0}
.nb-audio{display:flex;gap:8px;margin:8px 0}
"""

# ---- HTML 骨架 ----
def head_top(subtitle, bodyclass):
    return ("""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>__TITLE__ · """ + subtitle + """</title>
<link rel="stylesheet" href="../ui.css">
<script src="../ui.js"></script>
""" + CSS + CSS_EXTRA + """
</style></head>
<body class=\"""" + bodyclass + """\">
<div class="app">
""")

HEADER = """
  <header class="top">
    <div class="meta"><span class="t" id="headline">Unit 7</span><span class="tchip" id="timerChip" title="本次练习时长">00:00</span></div>
    <button class="tbtn" id="rateBtn" title="播放速度">1x</button>
    <button class="tbtn" id="loopBtn" title="循环次数（聆听整篇 / 跟读单句）">↻1</button>
    <div class="sp"></div>
    <nav class="tabs" id="tabs">
      <button class="tbtn" id="mapBtn" title="返回书架">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14M15 6v14"/></svg>
      </button>
      <button class="curtab" id="curTab" title="当前篇章"><span class="tty" id="curTty">阅读</span><i class="tsep">·</i><span class="curTt" id="curTitle"></span><i class="curArr">▾</i></button>
      <button class="tbtn" id="openDir" title="目录">
        <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="4" cy="6" r="1.5" fill="currentColor" stroke="none"/><line x1="9" y1="6" x2="20" y2="6"/><circle cx="4" cy="12" r="1.5" fill="currentColor" stroke="none"/><line x1="9" y1="12" x2="20" y2="12"/><circle cx="4" cy="18" r="1.5" fill="currentColor" stroke="none"/><line x1="9" y1="18" x2="20" y2="18"/></svg>
      </button>
    </nav>
  </header>
"""

READER = """
  <main class="stage">
    <div class="reader" id="reader">
      <div class="head-wrap">
        <h1 class="headline" id="paperTitle"></h1>
      </div>
      <div class="body" id="body"></div>
    </div>
"""

FSTAGE = """
    <div class="fstage" id="fstage">
      <div class="fs-card" id="fsCard">
        <div class="fs-txt" id="fsTxt"></div>
        <div class="fs-hint" id="fsHint"></div>
      </div>
      <div class="fs-gap" id="fsGap">
        <div class="fs-ring" id="fsRing"></div>
        <div class="fs-gap-msg" id="fsGapMsg">该你开口 · 跟读这段</div>
        <div id="fsGapWords" style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:8px"></div>
        <div class="fs-gapbar"><div class="fs-gapbar-i" id="fsGapBar"></div></div>
      </div>
    </div>
"""

WAYPICKS = """
    <div class="waypick" id="pickpick" aria-hidden="true">
      <div class="way-card">
        <div class="w-head">选择听写抽句</div>
        <p class="w-sub">从本篇句子中挑"最能练到重点词"的句来听写，每句精听 4 遍（第1、4遍 1.0×，第2、3遍 0.85×）。</p>
        <button class="way-btn" type="button" onclick="pickCount(3)">
          <span class="wb-ic">✳</span>
          <span class="wb-t"><b>抽 3 句</b><i>覆盖本篇重点词的精听，适合快速巩固</i></span>
        </button>
        <button class="way-btn" type="button" onclick="pickCount(5)">
          <span class="wb-ic">✳✳</span>
          <span class="wb-t"><b>抽 5 句</b><i>更充分的听写覆盖</i></span>
        </button>
        <button class="way-btn" type="button" onclick="pickCustom()">
          <span class="wb-ic">☰</span>
          <span class="wb-t"><b>自定义选段落</b><i>勾选若干段，在该段内听写全部句子</i></span>
        </button>
        <div id="pcustom" class="wx"></div>
      </div>
    </div>

    <div class="waypick" id="waypick" aria-hidden="true">
      <div class="way-card">
        <div class="w-head">选择听写方式</div>
        <p class="w-sub">选定后本课全程使用，两种方式都按抽句四遍精听。</p>
        <button class="way-btn" type="button" onclick="pickWay('key')">
          <span class="wb-ic">⌨</span>
          <span class="wb-t"><b>键盘输入听写</b><i>在原位下划线处打字，写完自动判分</i></span>
        </button>
        <button class="way-btn" type="button" onclick="pickWay('paper')">
          <span class="wb-ic">✎</span>
          <span class="wb-t"><b>稿纸听写</b><i>屏幕显示下划线占位，用你自己的纸笔写，点「核对答案」对照</i></span>
        </button>
        <button class="way-btn" type="button" onclick="pickWay('nb')">
          <span class="wb-ic">📔</span>
          <span class="wb-t"><b>听写本模式</b><i>拿出听写本逐句写，写完看原文点错词自评（拍照发微信群）</i></span>
        </button>
      </div>
    </div>
"""

DICT_PANEL = """
    <div class="dict" id="dict">
      <div class="dict-head">
        <div style="display:flex;flex-direction:column;gap:2px">
          <span class="dict-tag">听写 · 抽句四遍精听</span>
          <span class="dict-sub" id="dt-count"></span>
        </div>
        <span class="dict-pass" id="dt-pass">第 1/4 遍 · 1.0× 常速</span>
      </div>
      <div class="dict-card">
        <div class="dt-line" id="dt-sheet"></div>
      </div>
      <div class="dict-zh" id="dt-zh"></div>
      <div class="dict-desc" id="dt-desc"></div>
      <div class="dict-act">
        <button class="chip" id="dtRelisten"><span class="dot"></span>重听本句</button>
        <span class="dict-score" id="dt-score"></span>
      </div>
      <div class="dict-diag" id="dt-diag"></div>
    </div>
  </main>
"""

NBOV = """
<div class="nb-ov" id="nbOv"><div class="nb-card" id="nbCard"></div></div>
"""

QUIZOV = """
<div class="qzboard" id="quizOv"><div class="qz-card">
  <div class="qz-head">
    <span class="qz-tip" id="qzTip">📖 阅读题目 · 听后做题</span>
    <span class="qz-tools">
      <button class="qz-tool" id="mkU" onclick="mkMode('u')">下划线</button>
      <button class="qz-tool" id="mkC" onclick="mkMode('c')">画圈</button>
      <button class="qz-tool" onclick="mkClear()">清除</button>
    </span>
  </div>
  <div class="qz-sec" id="qzSec"><canvas class="qz-canvas" id="qzCanvas"></canvas><div id="qzBody"></div></div>
  <button class="qz-submit" id="qzSubmit" disabled>🔊 听后作答（播放中…）</button>
</div></div>
"""

def dock(mid, cta):
    return """
  <footer class="dock">
    <div class="dgroup">
      <button class="tbtn" id="prev" title="上一条"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m11 17-5-5 5-5M18 17l-5-5 5-5"></path></svg></button>
      <button class="big" id="play"><svg id="playIc" width="26" height="26" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="7 4 20 12 7 20 7 4"/></svg></button>
      <button class="tbtn" id="next" title="下一条"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 17 5-5-5-5M12 17l5-5-5-5"></path></svg></button>
    </div>
    <div class="dmid">
""" + mid + """
    </div>
    <button class="cta" id="nextStage">""" + cta + """</button>
  </footer>
"""

MID_LISTEN = """      <span class="di-dots" id="dkDots"></span>
      <button class="chip" id="cnToggle">译文</button>"""

MID_FOLLOW = """      <span class="di" id="dkCntR"><span class="lbl">句</span><span class="num" id="dkS">1/1</span></span>
      <span class="di-dots" id="dkDots"></span>
      <button class="chip" id="cnToggle">译文</button>
      <span class="dlp">
        <span class="dlp-t">步骤</span>
        <span class="fpass" id="fpass">
        <span class="fpc on" data-s="1" title="逐句跟读：边听边读 → 播完一句看生词提示 → 开口跟读">跟读</span>
        </span>
      </span>"""

MID_DICTATE = """      <button class="chip" id="cnToggle">译文</button>"""

DIR_PANEL = """
<!-- 分组目录面板（v2：只列本篇三环节互链，由 __SIBLINGS__ 注入） -->
<div class="dir" id="dir">
  <div class="dir-panel">
    <div class="dir-head">
      <b>目录</b>
      <span class="du" id="dirUnit">Unit 7</span>
      <button class="x" id="dirClose" type="button" title="关闭" aria-label="关闭">✕</button>
    </div>
    <div class="dir-body" id="dirGroups"></div>
  </div>
</div>
"""

AUDIO = """
<audio id="audio" preload="metadata"></audio>
"""

# ---- 共用 JS（数据块之后） ----
SHARED_JS = r"""
var $=id=>document.getElementById(id);
var audio=$("audio");
var TL, ZH, TITLE_START, ENTITY, ENTITYMULTI, LEVEL, TOPIC, BASE, TRAP;
function initDB(){ TL=DB.TL; ZH=DB.ZH||{}; TITLE_START=DB.TITLE_START;
  ENTITY=DB.ENTITY||{}; ENTITYMULTI=DB.ENTITYMULTI||{}; LEVEL=DB.LEVEL||{}; TOPIC=DB.TOPIC||{}; BASE=DB.BASE||{}; TRAP=DB.TRAP||{}; }

/* == 三页互链注入点（_gen_follow_v2.py 注入本篇 预习/复习/听写 文件名） == */
var SIBLINGS=__SIBLINGS__;
var CUR="__CUR__";
var QUIZ = __QDATA__;
var TASKS = (function(){ var m=(location.search||"").match(/[?&]tasks=([\w,]+)/); return m ? m[1].split(",") : null; })();
function tasksAllow(k){ return !TASKS || TASKS.indexOf(k) >= 0; }

/* ---------- state ---------- */
var state={ pg:__PG__, stage:CUR, mode:"whole", cn:false, idx:0, flow:"read", loopN:1, loopLeft:0, rate:1 };
var PROG={ listen:false, follow:false, dictate:false };
var SEGS=[], sentEls=[];
var seeking=false;

/* ---------- 进度落盘：三页共用 tf_follow_<pg>，主站任务判定读 follow 键 ---------- */
var FK='tf_follow_';
function loadFollow(pg){ try{ var o=JSON.parse(localStorage.getItem(FK+pg)); return (o&&typeof o==='object')?o:null; }catch(e){ return null; } }
function saveFollow(){ try{ localStorage.setItem(FK+state.pg, JSON.stringify({ listen:PROG.listen, follow:PROG.follow, dictate:PROG.dictate, updatedAt:Date.now() })); }catch(e){} }

function partsOf(s){
  var re=/([A-Za-z']+|[0-9]+)|([^\s])/g, m, o=[], i=0;
  while((m=re.exec(s))){
    if(m.index>i) o.push({t:s.slice(i,m.index),w:-1});
    o.push(m[1]? {t:m[1],w:1} : {t:m[2],w:0});
    i=m.index+m[0].length;
  }
  if(i<s.length) o.push({t:s.slice(i),w:-1});
  return o;
}
function wrapWords(s){ var h=""; partsOf(s).forEach(function(p){ h+= p.t; }); return h; }
function normTok(t){ return (t||"").toLowerCase().replace(/[.,;'!?]+$/,''); }
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }
function escQ(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
let tt; function toast(m){ var t=$("toast"); t.textContent=m; t.classList.add("show"); clearTimeout(tt); tt=setTimeout(()=>t.classList.remove("show"),2200); }

function render(pg){
  state.pg=pg; state.idx=0;
  var B=BOOK[pg], body=$("body"), seg=0, spk=B.spk||null;
  state.dialog = !!(spk && spk.length>1);
  body.innerHTML="";
  SEGS=[]; sentEls=[];
  PROG={ listen:false, follow:false, dictate:false };
  var _saved=loadFollow(pg);
  if(_saved){ PROG.listen=!!_saved.listen; PROG.follow=!!_saved.follow; PROG.dictate=!!_saved.dictate; }
  B.arts.forEach(function(ar){
    var p=document.createElement("div"); p.className="para";
    ar.forEach(function(s){
      var sent=document.createElement("span");
      sent.className="sent"; sent.dataset.i=seg;
      if(spk){ sent.dataset.spk=spk[seg]; sent.innerHTML='<b class="spk">'+(spk[seg]==="julia"?"Julia":"Mike")+'</b>'+wrapWords(s)+`<span class="zh ${state.cn?"":"hide"}">${ZH[s]||""}</span>`; }
      else sent.innerHTML=wrapWords(s)+`<span class="zh ${state.cn?"":"hide"}">${ZH[s]||""}</span>`;
      p.appendChild(sent); p.appendChild(document.createTextNode(" "));
      SEGS.push(s); sentEls.push(sent);
      seg++;
    });
    body.appendChild(p);
  });
  $("paperTitle").textContent=B.title;
  $("headline").textContent=B.u;
  audio.pause();
  audio.src=B.audio;
  setStage(state.stage);
}

/* ---------- transport ---------- */
function jump(sec, fromPlay){
  var d=audio.duration;
  var t=Math.max(0, Math.min(sec, isFinite(d)?d: sec));
  if(Math.abs(audio.currentTime-t)<0.04 && !audio.paused) return;
  audio.pause(); seeking=true;
  try{ audio.currentTime=t; }catch(e){}
  audio.addEventListener("seeked", function h(){ seeking=false; audio.play(); audio.removeEventListener("seeked",h); });
  setPlayIc(true);
}
function startFrom(){
  var k=state.pg; var start=(TITLE_START["p"+String(k).padStart(3,"0")]||0);
  jump(start, true);
}
audio.addEventListener("play", function(){ setPlayIc(true); });
audio.addEventListener("pause", function(){ setPlayIc(false); });

/* ---------- highlight ---------- */
function highlightAt(t){
  var tls=TL[state.pg]; var si=0;
  for(var i=0;i<tls.length;i++){ if(t>=tls[i][0]-0.01) si=i; else break; }
  setActiveSentence(si);
}
function setActiveSentence(si){
  for(var i=0;i<sentEls.length;i++) sentEls[i].classList.toggle("on", i===si);
  autoScroll(si);
}
function autoScroll(si){
  var el=sentEls[si]; if(!el) return;
  var body=$("body");
  var er=el.getBoundingClientRect(), br=body.getBoundingClientRect();
  if(er.top<br.top+4 || er.bottom>br.bottom-8){
    el.scrollIntoView({block:"center",behavior:"smooth"});
  }
}
function setPlayIc(on){
  $("playIc").outerHTML = on
    ? '<svg id="playIc" width="26" height="26" viewBox="0 0 24 24" fill="currentColor" stroke="none"><rect x="7" y="5" width="4" height="14" rx="1"/><rect x="13" y="5" width="4" height="14" rx="1"/></svg>'
    : '<svg id="playIc" width="26" height="26" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="7 4 20 12 7 20 7 4"/></svg>';
}

/* == 跟读间隙生词提示（方案A：unknown 优先，fuzzy 补位）+ 听写本错词入待复习（v1 全量保留） == */
var VQKEY = "__VQKEY__";
function vqRecords(){ try{ return JSON.parse(localStorage.getItem(VQKEY + "_records_v2")) || {}; }catch(e){ return {}; } }
function vqMark(word, status){
  if(!VQKEY) return;
  var R = vqRecords(); var w = word.toLowerCase();
  R[w] = R[w] || { status:"none", filterTime:0, filterChanges:0, isPriority:false, listenCount:0, studyTime:0,
    studyRounds:0, lastStudyAt:0, spellChecked:false, spellResult:null, consecCorrect:0, nearMissCount:0,
    reviewCount:0, lastReviewAt:0, nextReviewAt:0, testHistory:[], testCount:0, correctCount:0, wrongCount:0, uncertainCount:0 };
  R[w].status = status;
  if(status==="unknown"){ R[w].lastReviewAt = Date.now(); R[w].reviewCount = 0; R[w].nextReviewAt = Date.now() + 864e5; }
  try{ localStorage.setItem(VQKEY + "_records_v2", JSON.stringify(R)); }catch(e){}
}
function speakW(w){ try{ var u=new SpeechSynthesisUtterance(w); u.lang="en-GB"; u.rate=0.85; speechSynthesis.cancel(); speechSynthesis.speak(u); }catch(e){} }
function vqWordsFor(seg){
  if(!VQKEY) return [];
  var R = vqRecords(), unk = [], fz = [];
  for(var w in R){ if(R[w].status==="unknown") unk.push(w); else if(R[w].status==="fuzzy") fz.push(w); }
  if(!unk.length && !fz.length) return [];
  var toks = partsOf(seg).map(function(p){ return (p.t||"").toLowerCase().replace(/[^a-z']/g,""); }).filter(Boolean);
  var hitU = [], hitF = [];
  toks.forEach(function(t){
    unk.forEach(function(w){ if(t.indexOf(w)===0 || w.indexOf(t)===0) hitU.push(w); });
    fz.forEach(function(w){ if(t.indexOf(w)===0 || w.indexOf(t)===0) hitF.push(w); });
  });
  var seen = {}; var out = [];
  unk.concat(fz).forEach(function(w){ if(hitU.indexOf(w)>=0 && !seen[w]){ out.push([w,"u"]); seen[w]=1; } });
  hitF.forEach(function(w){ if(!seen[w]){ out.push([w,"f"]); seen[w]=1; } });
  return out;
}
function renderGapWords(si){
  var box = $("fsGapWords"); if(!box) return;
  var list = vqWordsFor(SEGS[si]);
  if(!list.length){ box.innerHTML = '<span style="font-size:12px;color:#8a8a92">本句无生词，直接跟读</span>'; return; }
  box.innerHTML = list.map(function(p){
    var lab = p[1]==="u" ? "不会" : "模糊";
    return '<span class="gapw" onclick="speakW(\''+p[0]+'\')">'+escQ(p[0])+'<i>'+lab+' 🔊</i></span>';
  }).join("") + '<span style="font-size:11.5px;color:#8a8a92;align-self:center">跟着读音开口</span>';
}

/* ---------- binds (script runs at end of body, DOM present) ---------- */
document.addEventListener("DOMContentLoaded", function(){
  initDB();
  bindSentClicks();
  render(__PG__);
  $("play").onclick=togglePlay;
  document.addEventListener("keydown",function(e){
    if(e.code!=="Space") return;
    var el=document.activeElement;
    if(el && (el.tagName==="INPUT"||el.tagName==="TEXTAREA")) return;
    e.preventDefault(); togglePlay();
  });
  $("prev").onclick=()=>nxt(-1);
  $("next").onclick=()=>nxt(1);
  $("cnToggle").onclick=function(){
    state.cn=!state.cn; syncCnUI(); toast(state.cn?"译文：显示":"译文：隐藏");
  };
});
"""

DIR_JS_HEAD = """</script>
<script>
(function(){
var ID=function(o){return document.getElementById(o);};
/* 类型视觉编码：图标 + 颜色（阅读/听力/口语/文化/纪录片/播客 六类，v1 全量保留） */
"""

DIR_JS_MID = """
/* U8-U11 扩展条目（_gen_follow_v2.py 注入） */
__BOOK_EXTRA__

/* 单元目录配置：按单元分组，组内按页码数字升序；新增篇章只需在此追加 [pg, 类型key, 题名] */
"""

DIR_JS_TAIL = r"""
__UG_EXTRA__

function unitOf(pg){ return (pg===110||pg===111||pg===113||pg===114||pg===117||pg===202)?12:7; }
function meta(pg){
  var items=UNIT_GROUPS[unitOf(pg)].items;
  for(var i=0;i<items.length;i++)
    if(items[i][0]===pg)return {pg:pg,ty:items[i][1],tt:items[i][2]};
  return null;
}
function paint(){
  var cur=meta(state.pg)||meta(67); if(!cur)return;
  var ty=TYPES[cur.ty];
  var tty=ID("curTty"); tty.textContent=ty.n; tty.style.background=ty.c+"1a"; tty.style.color=ty.c;
  ID("curTitle").textContent=cur.tt;
  ID("curTab").title="当前："+cur.tt;
}
/* v2 目录：只列本篇三环节互链（预习↔复习↔听写），由 SIBLINGS 提供文件名 */
var STEP_NAMES={listen:"预习（聆听）",follow:"复习（跟读）",dictate:"听写"};
function build(){
  var g=UNIT_GROUPS[unitOf(state.pg)];
  var body=ID("dirGroups"); body.innerHTML="";
  ID("dirUnit").textContent=g.label;
  var lab=document.createElement("div"); lab.className="grp-label"; lab.textContent=g.label; body.appendChild(lab);
  var m=meta(state.pg)||{ty:"rt",tt:BOOK[state.pg].title};
  var ty=TYPES[m.ty];
  ["listen","follow","dictate"].forEach(function(k){
    var b=document.createElement("button"); b.type="button"; b.className="grp-item"; b.dataset.k=k;
    b.innerHTML='<span class="gi-ic" style="background:'+ty.c+'1a;color:'+ty.c+'">'+ty.ic+'</span>'
      +'<span class="gi-t"><span class="gi-pg">'+("000"+state.pg).slice(-3)+'</span>'
      +'<span class="gi-tt">'+(k===CUR?"当前 · ":"")+STEP_NAMES[k]+'</span></span>';
    b.addEventListener("click",function(){ closeDir(); if(k!==CUR) location.href=SIBLINGS[k]; });
    body.appendChild(b);
  });
}
function markOn(){
  var items=ID("dirGroups").querySelectorAll(".grp-item");
  for(var i=0;i<items.length;i++){
    var on=items[i].dataset.k===CUR;
    items[i].classList.toggle("on",on);
    if(on)items[i].scrollIntoView({block:"nearest"});
  }
}
function openDir(){ build(); ID("dir").classList.add("on"); markOn(); }
function closeDir(){ ID("dir").classList.remove("on"); }
document.addEventListener("DOMContentLoaded",function(){
  var mb=ID("mapBtn"); if(mb) mb.onclick=function(){ location.href="../index.html"; };
  var RATES=[1,0.75,1.25], RI=0;
  ID("rateBtn").onclick=function(){ RI=(RI+1)%3; state.rate=RATES[RI]; audio.playbackRate=state.rate; ID("rateBtn").textContent=state.rate+"x"; toast("播放速度 "+state.rate+"x"); };
  ID("loopBtn").onclick=function(){ var N=[1,2,3,5], I=N.indexOf(state.loopN); state.loopN=N[(I+1)%4]; state.loopLeft=state.loopN-1; ID("loopBtn").textContent="↻"+state.loopN; toast(state.loopN>1?("循环 "+state.loopN+" 次（跟读=每句，聆听=整篇）"):"循环关闭"); };
  var t0=Date.now(); setInterval(function(){ var s=Math.floor((Date.now()-t0)/1000); ID("timerChip").textContent=("0"+Math.floor(s/60)).slice(-2)+":"+("0"+s%60).slice(-2); },1000);
  build(); paint();
  __STAGE_DIR_BINDS__
  ID("openDir").addEventListener("click",function(e){ e.stopPropagation(); openDir(); });
  ID("curTab").addEventListener("click",openDir);
  ID("curTab").addEventListener("keydown",function(e){ if(e.key==="Enter"||e.key===" "){e.preventDefault();openDir();} });
  ID("dirClose").addEventListener("click",closeDir);
  ID("dir").addEventListener("click",function(e){ if(e.target.id==="dir")closeDir(); });
  document.addEventListener("keydown",function(e){ if(e.key==="Escape")closeDir(); });
  /* 暴露给宿主脚本复用（头部类型标注） */
  window.paint=paint; window.meta=meta; window.TYPES=TYPES;
  window.currentUnit=function(){ return unitOf(state.pg); };
});
})();
</script>
"""

LISTEN_DIR_BINDS = r"""  applyBlind();
  var qc = ID("qzCanvas");
  ["mousedown","touchstart"].forEach(function(ev){ qc.addEventListener(ev, mkStart, {passive:false}); });
  ["mousemove","touchmove"].forEach(function(ev){ qc.addEventListener(ev, mkMove, {passive:false}); });
  ["mouseup","mouseleave","touchend","touchcancel"].forEach(function(ev){ qc.addEventListener(ev, mkEnd); });
  ID("qzSubmit").addEventListener("click", function(){ if(QZB.submitted) closeQuiz(); });
  window.addEventListener("resize", function(){ if($("quizOv").classList.contains("on")) resizeCanvas(); });"""

PLAIN_DIR_BINDS = r"""  /* 本环节无答题板绑定 */"""

# ---- 环节 JS：预习 ----
LISTEN_JS = r"""
/* ========== 预习（聆听）：整篇循环 + 盲听答题（v1 功能全量保留） ========== */
var QZ = {done:false};
function quizDone(){ return QZ.done || PROG.listen; }
var LCOUNT={ n:0, p:0 };
function setListenN(n){
  var dots=$("dkDots"); if(dots){ dots.innerHTML=""; for(var i=0;i<3;i++){ var d=document.createElement("span"); d.className="lp-dot"+((i<n)?" on":""); dots.appendChild(d); } }
}
function listenLoop(){
  if(LCOUNT.p!==state.pg) return;
  LCOUNT.n++;
  PROG.listen=true; saveFollow();
  if(LCOUNT.n>=3){ setListenN(0); toast("聆听 3 遍完成，进入复习跟读"); setTimeout(function(){ location.href=SIBLINGS.follow; }, 900); }
  else { setListenN(LCOUNT.n); startFrom(); }
}
audio.addEventListener("ended", function(){
  if(!seeking){
    if(QUIZ.length && !quizDone()){ showQuiz(); return; }
    listenLoop();
  }
});

/* 盲听：答题（≥75% 记完成）前隐去原文 */
function applyBlind(){
  var b = $("body");
  if(!b) return;
  if(QUIZ.length && !quizDone()){ b.classList.add("blind"); showQuizBanner(); }
  else { b.classList.remove("blind"); var bn=$("quizBanner"); if(bn) bn.classList.add("hide"); }
}
function showQuizBanner(){
  var bn = $("quizBanner");
  if(!bn){
    bn = document.createElement("div"); bn.id="quizBanner"; bn.className="quiz-banner";
    bn.innerHTML = '<span>📖 预习（聆听）：全文整体听 · 阅读题目 —— 听后做题</span><button onclick="showQuiz()">答题</button>';
    var reader = $("reader") || document.body;
    reader.parentNode.insertBefore(bn, reader);
  }
  bn.classList.remove("hide");
}
var QZB = {answered:false, submitted:false};
var MK = {mode:null, down:false, sx:0, sy:0, ctx:null};
function showQuiz(){
  audio.pause(); setPlayIc(false);
  QZB.answered=false; QZB.submitted=false;
  $("quizOv").classList.add("on");
  $("qzSubmit").disabled = true; $("qzSubmit").textContent = "🔊 全文整体听 · 听后作答";
  $("qzTip").textContent = "📖 阅读题目 · 听后做题（可用下划线/画圈标记）";
  var html = QUIZ.map(function(q,i){
    var inner = "";
    if(q.t==="tf") inner = ["T","F","DS"].map(function(o){ return '<button class="quiz-opt dis" data-qi="'+i+'" data-ans="'+o+'">'+(o==="T"?"✓ T":(o==="F"?"✗ F":"? DS"))+'</button>'; }).join("");
    else inner = q.opts.map(function(o,oi){ return '<button class="quiz-opt dis" data-qi="'+i+'" data-ans="'+oi+'">'+escQ(o)+'</button>'; }).join("");
    return '<div class="qz-q">'+(i+1)+'. '+escQ(q.q)+'</div><div class="quiz-opts">'+inner+'</div>';
  }).join("");
  $("qzBody").innerHTML = html;
  $("qzBody").querySelectorAll(".quiz-opt").forEach(function(b){
    b.addEventListener("click", function(){
      var q = QUIZ[+b.dataset.qi];
      var ok = (q.t==="tf") ? (b.dataset.ans===q.a) : (+b.dataset.ans===q.a);
      b.parentNode.querySelectorAll(".quiz-opt").forEach(function(x){ x.classList.remove("ok","no"); });
      b.classList.add(ok ? "ok" : "no");
      if(!ok){ b.parentNode.querySelectorAll(".quiz-opt")[q.t==="tf" ? ["T","F","DS"].indexOf(q.a) : q.a].classList.add("ok"); }
      checkAllAnswered();
    });
  });
  resizeCanvas(); mkMode(null);
}
function checkAllAnswered(){
  var btns = $("qzBody").querySelectorAll(".quiz-opt.ok,.quiz-opt.no");
  var need = 0; QUIZ.forEach(function(q){ need++; });
  if(btns.length >= need && !QZB.submitted){ QZB.submitted = true; submitQuiz(); }
}
function submitQuiz(){
  var score = 0;
  QUIZ.forEach(function(q,i){
    var sel = $("qzBody").querySelector('.quiz-opt.ok[data-qi="'+i+'"]');
    var ans = sel ? sel.dataset.ans : null;
    var ok = q.t==="tf" ? (ans===q.a) : (+ans===q.a);
    if(ok) score++;
  });
  var pass = score >= Math.ceil(QUIZ.length*0.75);
  $("qzSubmit").textContent = "得分 " + score + " / " + QUIZ.length + (pass ? " · 🎉 预习完成，正文已解锁" : " · 再听一遍试试");
  $("qzSubmit").disabled = false;
  $("qzSubmit").onclick = function(){ closeQuiz(); };
  if(pass){ QZ.done=true; PROG.listen=true; saveFollow(); applyBlind(); }
}
function closeQuiz(){ $("quizOv").classList.remove("on"); applyBlind(); }
/* 标记：下划线/画圈（鼠标+触摸手势） */
function mkMode(m){
  MK.mode = (MK.mode===m) ? null : m;
  $("mkU").classList.toggle("on", MK.mode==="u");
  $("mkC").classList.toggle("on", MK.mode==="c");
  var c = $("qzCanvas"); c.classList.toggle("on", !!MK.mode);
  if(MK.mode) resizeCanvas();
}
function mkClear(){ var c=$("qzCanvas"); c.getContext("2d").clearRect(0,0,c.width,c.height); }
function resizeCanvas(){
  var sec = $("qzSec"), c = $("qzCanvas");
  c.width = sec.clientWidth; c.height = sec.scrollHeight;
}
function mkPos(e){
  var r = $("qzCanvas").getBoundingClientRect();
  var t = e.touches ? e.touches[0] : e;
  return {x:t.clientX-r.left, y:t.clientY-r.top};
}
function mkStart(e){
  if(!MK.mode) return; e.preventDefault();
  MK.down = true; var p = mkPos(e); MK.sx = p.x; MK.sy = p.y;
  MK.ctx = $("qzCanvas").getContext("2d");
  MK.ctx.strokeStyle = "#f2b706"; MK.ctx.lineWidth = MK.mode==="u" ? 2.5 : 3; MK.ctx.lineCap = "round";
  if(MK.mode==="c") MK.ctx.beginPath(), MK.ctx.moveTo(p.x,p.y);
}
function mkMove(e){
  if(!MK.down || !MK.mode) return; e.preventDefault();
  var p = mkPos(e), ctx = MK.ctx;
  if(MK.mode==="u"){ ctx.clearRect(MK.sx-1, MK.sy-9, p.x-MK.sx+2, 18); ctx.beginPath(); ctx.moveTo(MK.sx, MK.sy); ctx.lineTo(p.x, p.y); ctx.stroke(); }
  else { ctx.lineTo(p.x, p.y); ctx.stroke(); }
}
function mkEnd(){ MK.down = false; }

/* ---------- 单环节状态机（预习） ---------- */
function setStage(s){
  document.body.className = "listen" + (state.dialog?" dialog":"");
  syncCnUI();
  LCOUNT={ n:0, p:state.pg }; setListenN(0);
  applyBlind();
}
function syncCnUI(){
  var t=$("cnToggle"); if(!t) return;
  t.classList.toggle("on", state.cn);
  document.querySelectorAll(".sent .zh").forEach(function(z){ z.classList.toggle("hide",!state.cn); });
}
function bindSentClicks(){
  $("body").addEventListener("click",function(e){
    var sent=e.target.closest(".sent"); if(!sent) return;
    state.idx=+sent.dataset.i;
    jump(TL[state.pg][state.idx][0], false);
  });
}
function togglePlay(){
  if(audio.paused){ if(audio.ended || audio.currentTime===0){ startFrom(); } else audio.play(); }
  else audio.pause();
}
function nxt(d){ var L=SEGS.length; var i=Math.max(0,Math.min(L-1,state.idx+d));
  state.idx=i; jump(TL[state.pg][i][0], false); }
audio.addEventListener("timeupdate", function(){
  var t=audio.currentTime; if(!isFinite(t)) return;
  var tls=TL[state.pg], lastI=tls.length-1, wholeEnd=tls[lastI][1];
  if(!seeking && t>=wholeEnd){
    if(state.loopLeft>0){ state.loopLeft--; jump(tls[0][0], true); toast("整篇循环 · 剩 "+state.loopLeft+" 遍"); return; }
    audio.pause(); return;
  }
  highlightAt(t);
});
$("nextStage").onclick=function(){ location.href=SIBLINGS.follow; };
"""

# ---- 环节 JS：复习 ----
FOLLOW_JS = r"""
/* ========== 复习（跟读）：听句 → 间隙生词提示（方案A） → 开口（v1 第1步全量保留，影子已下线） ========== */
var FOL={ fstep:1, idx:0, ci:0, start:0, end:0, gap:false, next:null, timer:null, track:[], _cur:-1 };
var FOL_HINT='第 1 步 · 跟句：听完整一句 → 暂停 → 开口跟读整句（注意停顿与语调）';
function folTokens(s){
  var parts=[], re=/([A-Za-z']+|\d+)|([^A-Za-z'0-9]+)/g, m;
  while((m=re.exec(s))){ if(m[1]!==undefined) parts.push({word:m[1]}); else parts.push({p:m[2]}); }
  return parts;
}
/* 按词长把句段时间分摊到每个词 → 词级时间轴（无词级标注时的近似） */
function folWordTimes(s, st, en){
  var toks=folTokens(s), total=0;
  toks.forEach(function(t){ if(t.word!==undefined) total+=t.word.length; });
  if(!total){ toks.forEach(function(t){ if(t.word!==undefined){ t.st=st; t.en=en; } }); return toks; }
  var t=st;
  toks.forEach(function(tok){
    if(tok.word===undefined) return;
    var d=(en-st)*tok.word.length/total;
    tok.st=t; tok.en=t+d; t+=d;
  });
  return toks;
}
function renderTokenSpans(toks){
  var box=$("fsTxt"); box.innerHTML="";
  FOL.track.length=0; FOL._cur=-1;
  toks.forEach(function(tok){
    if(tok.p!==undefined){ box.appendChild(document.createTextNode(tok.p)); return; }
    var sp=document.createElement("span"); sp.className="fol-w"; sp.textContent=tok.word;
    box.appendChild(sp); FOL.track.push({el:sp, st:tok.st, en:tok.en});
  });
}
function wordAt(ts){
  var tr=FOL.track, res=-1;
  for(var i=0;i<tr.length;i++){ if(ts>=tr[i].st-0.012){ res=i; } else break; }
  return res;
}
function maybeScrollWord(el){
  var card=$("fsCard"), cr=card.getBoundingClientRect(), er=el.getBoundingClientRect();
  if(er.top<cr.top+8 || er.bottom>cr.bottom-8){ el.scrollIntoView({block:"center",behavior:"smooth"}); }
}
function updateShadowCursors(t){
  var tr=FOL.track; if(!tr.length) return;
  var c=wordAt(t);
  if(c!==FOL._cur){ if(FOL._cur>=0&&FOL._cur<tr.length) tr[FOL._cur].el.classList.remove("cur"); FOL._cur=c; if(c>=0&&c<tr.length){ tr[c].el.classList.add("cur"); maybeScrollWord(tr[c].el); } }
}
function setFollowHint(){
  $("fsHint").innerHTML='<div class="fol-legend"><i><span class="k k1"></span>音频正在这里</i></div>' + FOL_HINT;
}
function followPlaySentence(i){
  cancelGap();
  state.idx=i; FOL.ci=0; setActiveSentence(i);
  var tl=TL[state.pg][i];
  FOL.start=tl[0]; FOL.end=tl[1];
  renderTokenSpans(folWordTimes(SEGS[i], tl[0], tl[1]));
  $("fsCard").classList.remove("whole");
  setFollowHint();
  setFollowUI();
  jump(tl[0], true);
}
/* ---------- 「该你开口」间隙：暂停 + 倒计时条，走完自动进入下一段 ---------- */
function showGap(dur, msg, next){
  FOL.gap=true; FOL.next=next;
  audio.pause(); setPlayIc(false);
  var g=$("fsGap"), bar=$("fsGapBar"), m=$("fsGapMsg");
  if(m) m.textContent=msg;
  if(g) g.classList.add("on");
  if(bar) bar.style.width="0%";
  var t0=Date.now(), ms=Math.max(700, dur*1000);
  if(FOL.timer) clearInterval(FOL.timer);
  FOL.timer=setInterval(function(){
    var p=(Date.now()-t0)/ms; if(p>1) p=1;
    if(bar) bar.style.width=(p*100).toFixed(1)+"%";
    if(p>=1){
      clearInterval(FOL.timer); FOL.timer=null;
      var nx=FOL.next; FOL.next=null; hideGap();
      if(nx) nx();
    }
  }, 40);
}
function hideGap(){ FOL.gap=false; var g=$("fsGap"); if(g) g.classList.remove("on"); }
function resumeGap(){  /* 间隙里按播放：不等倒计时，立刻进入下一段 */
  if(FOL.timer){ clearInterval(FOL.timer); FOL.timer=null; }
  var nx=FOL.next; FOL.next=null; hideGap();
  if(nx) nx();
}
function cancelGap(){
  FOL.gap=false; FOL.next=null;
  if(FOL.timer){ clearInterval(FOL.timer); clearTimeout(FOL.timer); FOL.timer=null; }
  var g=$("fsGap"); if(g) g.classList.remove("on");
}
/* 第1步：一句播完 → 让出跟读时间 → 下一句；末句 → 跟读完成 */
function followSentenceEnd(){
  var si=state.idx, lastSent=si>=SEGS.length-1;
  showGap(Math.min(5.5, Math.max(1.8, (FOL.end-FOL.start)*0.8)), '该你开口 · 跟读整句', function(){
    if(!lastSent) return followPlaySentence(si+1);
    finishFollow();
  });
  renderGapWords(si);
}
function finishFollow(){
  PROG.follow=true; audio.pause(); setPlayIc(false); setFollowUI(); saveFollow();
  toast("逐句跟读完成 ✓ 进入听写");
  setTimeout(function(){ location.href=SIBLINGS.dictate; }, 900);
}
function enterFollow(){
  cancelGap();
  FOL.idx=0; FOL._cur=-1;
  setFollowUI();
  followPlaySentence(0);
}
function setFollowUI(){
  var ct=$("dkS");
  if(ct) ct.textContent=(state.idx+1)+"/"+SEGS.length;
  var cnt=$("dkCntR"); if(cnt) cnt.style.display="";
  var dots=$("dkDots"); if(dots) dots.innerHTML="";
}

/* ---------- 单环节状态机（复习） ---------- */
function setStage(s){
  document.body.className = "follow" + (state.dialog?" dialog":"");
  syncCnUI();
  enterFollow();
}
function syncCnUI(){
  var t=$("cnToggle"); if(!t) return;
  t.classList.remove("on");
  t.classList.add("off");
  t.disabled = true;
  document.querySelectorAll(".sent .zh").forEach(function(z){ z.classList.add("hide"); });
}
function bindSentClicks(){
  $("body").addEventListener("click",function(e){
    var sent=e.target.closest(".sent"); if(!sent) return;
    playSentence(+sent.dataset.i);
  });
}
function playSentence(i){
  cancelGap();
  state.idx=i; setActiveSentence(i);
  followPlaySentence(i);
}
function togglePlay(){
  if(audio.paused){ if(FOL.gap){ resumeGap(); } else followPlaySentence(state.idx); }
  else audio.pause();
}
function nxt(d){ var L=SEGS.length; var i=Math.max(0,Math.min(L-1,state.idx+d));
  playSentence(i); }
audio.addEventListener("timeupdate", function(){
  var t=audio.currentTime; if(!isFinite(t)) return;
  updateShadowCursors(t);
  if(seeking || FOL.gap) return;
  if(t>=TL[state.pg][state.idx][1]){
    if(state.loopLeft>0){ state.loopLeft--; jump(TL[state.pg][state.idx][0], true); return; }
    followSentenceEnd();
  }
});
$("fsCard").addEventListener("click",function(){
  if(FOL.gap){ resumeGap(); return; }
  followPlaySentence(state.idx);
});
$("nextStage").onclick=function(){ location.href=SIBLINGS.dictate; };
"""

# ---- 环节 JS：听写 ----
DICTATE_JS = r"""
/* ========== 听写：抽句四遍精听 · 三方式（键盘/稿纸/听写本，v1 全量保留） ========== */
var DT={ density:"mid", spell:false, hint:false, pass:0, way:"key", askedWay:false,
          list:[], qi:0, spech:false };
var NB = {i:0};
/* 听写四遍变速：第1遍常速建立整体 → 第2、3遍慢速聚焦拼写 → 第4遍回常速末遍判分 */
var PASS=[
  { d:"mid", spell:false, hint:false, rate:1.0,  label:"1.0× 常速 · 整体预听"},
  { d:"mid", spell:false, hint:false, rate:0.85, label:"0.85× 慢速 · 主词听写"},
  { d:"mid", spell:false, hint:false, rate:0.85, label:"0.85× 慢速 · 补全漏空"},
  { d:"mid", spell:false, hint:false, rate:1.0,  label:"1.0× 常速 · 末遍校验"}
];
function splitSent(s){
  var parts=[], re=/([A-Za-z']+|\d+)|([^A-Za-z'0-9]+)/g, m;
  while((m=re.exec(s))){ if(m[1]!==undefined) parts.push({w:m[1]}); else parts.push({p:m[2]}); }
  var out=[], i=0;
  while(i<parts.length){
    var it=parts[i];
    if(it.p!==undefined){
      if(/^(?:-+|\u2013+)$/.test(it.p) && !/\s/.test(it.p) && out.length && i+1<parts.length &&
         out[out.length-1].w!==undefined && parts[i+1].w!==undefined){
        out[out.length-1].w += "-" + parts[i+1].w; i+=2; continue;
      }
      out.push({p:it.p}); i++; continue;
    }
    out.push({w:it.w}); i++;
  }
  return out;
}
function dtBlankByDensity(lo){
  var d=DT.density;
  if(d==="easy") return BASE[lo]===1;        // 全员：基础高频词
  if(d==="mid")  return TOPIC[lo]===1;       // 中：主题核心词
  return TOPIC[lo]===1 || TRAP[lo]===1;      // 中强：主题 ∪ 拼写难点词
}
function dtBuild(s, pg){
  var toks=splitSent(s), words=[], wmap=[];
  toks.forEach(function(t,i){ if(t.w!==undefined){wmap[i]=words.length; words.push(t.w);} else wmap[i]=-1; });
  var n=words.length, used=new Array(n).fill(false), entT=new Array(n).fill(""), entS=new Array(n).fill(0);
  var cs=ENTITYMULTI[pg]||[];
  for(var k=0;k<cs.length;k++){
    var ts=cs[k][0], meta=cs[k][1], L=ts.length;
    for(var i=0;i+L<=n;i++){
      var ok=true;
      for(var u=0;u<L;u++){ if(used[i+u] || words[i+u].toLowerCase().replace(/'+$/,'')!==ts[u]){ok=false;break;} }
      if(ok){ for(var u=0;u<L;u++){ used[i+u]=true; entT[i+u]=meta.t; entS[i+u]=meta.s; } }
    }
  }
  var sing=ENTITY[pg]||{};
  for(var i=0;i<n;i++){ if(!used[i]){ var lo=words[i].toLowerCase().replace(/'+$/,''); if(sing[lo]){ used[i]=true; entT[i]=sing[lo].t; entS[i]=sing[lo].s; } } }
  var wds=[];
  for(var i=0;i<n;i++){
    var w=words[i], lo=w.toLowerCase();
    var kind;
    if(used[i]) kind = (DT.spell && entS[i]) ? "blankE" : "anchor";
    else if(/^\d/.test(lo) || NUMB[lo]) kind="hint";
    else if(FUNCTION[lo]) kind="hint";
    else kind = dtBlankByDensity(lo) ? "blank" : "hint";
    wds.push({w:w, full:lo, kind:kind, etype:entT[i], espell:entS[i], wi:i});
  }
  var cells=[], wi=-1;
  toks.forEach(function(t){
    if(t.w!==undefined){ wi++; cells.push({kind:"wd", o:wds[wi]}); }
    else cells.push({kind:"sep", s:t.p});
  });
  return {wds:wds, cells:cells};
}
function dtGroups(rec){
  var blanks=[];
  rec.wds.forEach(function(x){ if(x.kind==="blank"||x.kind==="blankE") blanks.push(x); });
  if(DT.density==="hard"){
    var gs=[]; for(var i=0;i<blanks.length;i+=2) gs.push(blanks.slice(i,i+2)); return gs.length?gs:[[]];
  }
  if(blanks.length<=6) return [blanks.slice()];
  var h=Math.ceil(blanks.length/2); return [blanks.slice(0,h), blanks.slice(h)];
}
function renderDictatePass(p){
  if(!(DT.list && DT.list.length)) return;
  DT.qi=Math.max(0, Math.min(DT.qi, DT.list.length-1));
  DT.pass=p;
  var i=DT.list[DT.qi]; state.idx=i;
  var P=PASS[p];
  DT.density=P.d; DT.spell=P.spell; DT.hint=P.hint; DT.rate=P.rate;
  dtRenderSentence(i);
  $("dt-pass").textContent="第 "+(p+1)+"/4 遍 · "+P.label;
  replayCurrentSentence();   // 每遍都播整句(按当前语速)
}
function nextDictatePass(){ if(DT.pass<3){ renderDictatePass(DT.pass+1); } }
function dtRenderSentence(i){
  var s=SEGS[i]; if(!s) return;
  var rec=dtBuild(s, state.pg);
  DT.rec=rec; DT.groups=dtGroups(rec); DT.g=0; DT.playEnd=null;
  audio.pause(); setPlayIc(false);
  var sheet=$("dt-sheet"); sheet.innerHTML="";
  var groupOf={}; rec.wds.forEach(function(x){ groupOf[x.wi]=-1; });
  DT.groups.forEach(function(g, gi){ g.forEach(function(b){ b.gi=gi; groupOf[b.wi]=gi; }); });
  var starts={}; DT.groups.forEach(function(g, gi){ for(var b of g){ if(!(b.wi in starts)) starts[b.wi]=gi; } });
  rec.cells.forEach(function(c){
    if(c.kind==="sep"){ var t=c.s.replace(/\s/g,""); if(t) sheet.appendChild(document.createTextNode(t)); return; }
    var o=c.o;
    var wrap=document.createElement("span");
    if(o.kind==="anchor"){ wrap.className="dt-w dt-anchor"; wrap.title="免写锚词 · 实体已给出"; wrap.textContent=o.w; sheet.appendChild(wrap); return; }
    if(o.kind==="hint"){ wrap.className="dt-w dt-hint"; wrap.textContent=o.w; sheet.appendChild(wrap); return; }
    if((o.wi in starts) && DT.groups.length>1 && starts[o.wi]>0){
      var sep=document.createElement("span"); sep.className="dt-gsep"; sep.textContent="\u23d0"; sheet.appendChild(sep);
    }
    if(DT.way==="paper"){
      var pp=document.createElement("span"); pp.className="dt-w dt-blank paper";
      var pf=(DT.hint && o.full.length>1) ? o.full[0] : "";
      var n=Math.max(o.full.length-pf.length,3);
      var pb = pf ? '<b class="fst">'+esc(pf)+'</b>' : "";
      pp.innerHTML = pb + '<span class="ul">'+new Array(n+1).join("_")+'</span>';
      pp.dataset.full=o.full; pp.dataset.wi=o.wi;
      sheet.appendChild(pp); return;
    }
    var bl=document.createElement("span"); bl.className="dt-w dt-blank";
    var first = (DT.hint && o.full.length>1) ? o.full[0] : "";
    o.fst=first; o.gi=starts[o.wi];
    var body = first ? '<b class="fst">'+esc(first)+'</b>' : "";
    var rest = o.full.slice(first.length);
    var il=Math.max(rest.length,3);
    body += '<input class="dt-in" size="'+il+'" maxlength="'+il+'" autocomplete="off" autocapitalize="off" spellcheck="false" value="">';
    bl.innerHTML=body;
    bl.dataset.full=o.full; bl.dataset.gi=o.gi; bl.dataset.wi=o.wi;
    sheet.appendChild(bl);
  });
  document.querySelectorAll("#dt-sheet .dt-blank").forEach(function(el){
    var gi=+el.dataset.gi;
    var inp=el.querySelector("input"); if(inp) inp.disabled = gi!==DT.g;
    el.classList.toggle("is-on", gi===DT.g);
  });
  DT.blankEls=[].slice.call(document.querySelectorAll("#dt-sheet .dt-blank"));
  DT.blankEls.forEach(bindBlank);
  $("dt-count").textContent="第 "+(DT.qi+1)+" / "+DT.list.length+" 句 · 遍 "+(DT.pass+1)+"/4 · 挖空 "+rec.wds.filter(function(x){return x.kind==="blank"||x.kind==="blankE";}).length+" 词 · 分 "+DT.groups.length+" 段";
  $("dt-zh").textContent=ZH[s]||""; $("dt-zh").classList.toggle("hide", !state.cn);
  $("dt-desc").textContent = DT.way==="paper"
    ? "稿纸听写：下划线处用你自己的纸笔听写，写完点下方「核对答案」对照。"
    : "绿色词＝已给出(免写锚词)；灰词＝提示词已给出；下划线＝本段要写的词，写完本段自动判分。";
  $("dt-diag").classList.remove("on"); $("dt-diag").innerHTML="";
  $("dt-score").textContent="";
  var inp0=DT.blankEls[0]&&DT.blankEls[0].querySelector("input");
  if(DT.way==="key"&&inp0&&!inp0.disabled) setTimeout(function(){ try{inp0.focus();}catch(e){} },80);
  // 本遍无填空：整句试听，直接给推进入口
  if(!DT.blankEls.length){
    $("dt-score").textContent="本句无填空词 · 完整试听";
    var nb = DT.pass<3
      ? '<button class="cta" onclick="nextDictatePass()">进入第 '+(DT.pass+2)+' 遍 · '+PASS[DT.pass+1].label+' →</button>'
      : '<button class="cta" onclick="dictNext()">下一句 →</button>';
    $("dt-diag").innerHTML='<div class="ddq-row" style="margin-bottom:12px">本句没有需要填空的词，先完整听一遍。</div><div style="display:flex;gap:8px;flex-wrap:wrap">'+nb+'</div>';
    $("dt-diag").classList.add("on");
  } else if(DT.way==="paper"){
    $("dt-diag").innerHTML='<div style="display:flex;gap:8px;flex-wrap:wrap"><button class="chip" onclick="dtRelisten()">重听本句</button><button class="cta" onclick="dtCheckAnswer()">核对答案</button></div>';
    $("dt-diag").classList.add("on");
    $("dt-score").textContent="";
  }
}
function dtCheckAnswer(){
  document.querySelectorAll('#dt-sheet .dt-blank.paper').forEach(function(el){
    el.classList.add("revealed");
    var ul=el.querySelector(".ul"); if(ul) ul.outerHTML='<span class="ans">'+esc(el.dataset.full)+'</span>';
  });
  var nb = DT.pass<3
    ? '<button class="cta" onclick="nextDictatePass()">进入第 '+(DT.pass+2)+' 遍 · '+PASS[DT.pass+1].label+' →</button>'
    : '<button class="cta" onclick="dictNext()">下一句 →</button>';
  $("dt-diag").innerHTML='<div class="ddq-row" style="margin-bottom:12px">已展示答案，对照你纸上的写法查漏补缺。</div><div style="display:flex;gap:8px;flex-wrap:wrap"><button class="chip" onclick="dtRelisten()">重听本句</button>'+nb+'</div>';
  DT.g=1; toast("已核对答案");
}
function bindBlank(el){
  var inp=el.querySelector("input"); if(!inp) return;
  var full=el.dataset.full, gi=+el.dataset.gi, wi=+el.dataset.wi;
  var fst=(el.querySelector(".fst")||{}).textContent||"";
  var rest=full.length-fst.length;
  inp.addEventListener("input", function(){
    if(inp.value.length<rest) return;
    var grp=DT.groups[gi];
    var idx=grp.findIndex(function(b){return b.wi===wi;});
    if(idx<grp.length-1){ focusBlank(grp[idx+1]); }
    else dtSubmitGroup(gi);
  });
  inp.addEventListener("keydown", function(e){
    if(e.key==="Enter"){ e.preventDefault(); dtSubmitGroup(gi); }
    else if(e.key==="Tab"){ e.preventDefault(); nxtToBlank(el,1,gi); }
  });
}
function focusBlank(b){
  var inp=document.querySelector('#dt-sheet [data-wi="'+b.wi+'"] input');
  if(inp&&!inp.disabled){ try{inp.focus();}catch(e){} }
}
function nxtToBlank(el,dir,gi){
  var grp=DT.groups[gi], i=grp.findIndex(function(b){return b.wi===+el.dataset.wi;});
  if(i<0) return;
  var j=i+dir;
  if(j>=0 && j<grp.length) focusBlank(grp[j]);
}
function dtSubmitGroup(gi){
  if(gi!==DT.g) return;
  var grp=DT.groups[gi], judge=(DT.pass>=3);   // 仅第4遍末判分
  grp.forEach(function(b){
    var el=document.querySelector('#dt-sheet [data-wi="'+b.wi+'"]'); if(!el) return;
    var inp=el.querySelector("input"); if(!inp) return;
    var fst=(el.querySelector(".fst")||{}).textContent||"";
    var typed=(fst+inp.value).trim().toLowerCase();
    if(!judge){ b.typed=typed; return; }        // 前3遍只记不判
    var ok=typed===b.full;
    var html= ok ? '<b class="dt-r-ok">'+esc(b.full)+'</b>'
                 : '<b class="dt-r-bad">'+esc(b.full)+'</b><span class="dt-r-tip">你写: '+esc(typed||"—")+'</span>';
    el.innerHTML=html;
    b.ok=ok; b.typed=typed;
  });
  DT.g++;
  if(DT.g>=DT.groups.length){
    if(judge){ dtFinish(); return; }
    nextDictatePass(); return;                  // 慢速试写两遍不计分 → 自动进下一遍
  }
  DT.groups[DT.g].forEach(function(b){
    var el=document.querySelector('#dt-sheet [data-wi="'+b.wi+'"]');
    var inp=el&&el.querySelector("input"); if(inp){ inp.disabled=false; }
  });
  focusBlank(DT.groups[DT.g][0]);
  audio.pause(); setPlayIc(false);
}
function dtFinish(){                            // 仅第4遍(末遍)调用
  var tot=0,cor=0,wrong=[];
  DT.groups.forEach(function(g){ g.forEach(function(b){ tot++; if(b.ok)cor++; else wrong.push(b); }); });
  var first=wrong.length===0;
  $("dt-score").textContent=cor+"/"+tot+" 词正确"+(first?"　太棒了！":"");
  var diag=$("dt-diag");
  var h='<div class="ddq-row"><span class="lbl">末尾校验结果：</span><b>'+cor+'</b> / '+tot+' 词正确</div>';
  if(wrong.length){
    h+='<div class="ddq-row" style="margin-top:6px"><span class="lbl">看看正确的拼写：</span></div>';
    wrong.forEach(function(b){ h+='<div class="ddq-row"><span class="em1">'+esc(b.full)+'</span>　你写：'+esc(b.typed||"—")+'</div>'; });
  } else {
    h+='<div class="ddq-row">末遍全对，真棒！</div>';
  }
  h+='<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap"><button class="chip" onclick="dtRelisten()">重听本句</button><button class="cta" onclick="dictNext()">下一句 →</button></div>';
  diag.innerHTML=h; diag.classList.add("on");
  audio.pause(); setPlayIc(false);
  toast(first?"末遍全对，继续加油！":"末遍听写完成，看看需要巩固的词吧");
}
function seekSpec(st,en){ DT.playEnd=en; seeking=true; audio.pause();
  try{audio.currentTime=st;}catch(e){}
  audio.addEventListener("seeked",function h(){seeking=false; audio.play(); audio.removeEventListener("seeked",h); });
  setPlayIc(true);
}
function replayCurrentSentence(){
  var i=state.idx; if(!(TL[state.pg]&&TL[state.pg][i])) return;
  if(DT.rate!=null){ try{ audio.playbackRate=DT.rate; }catch(e){} }
  var st=TL[state.pg][i][0], en=TL[state.pg][i][1];
  seekSpec(st,en);
}
function dtRelisten(){ replayCurrentSentence(); }
function dtTimeupdate(t){ if(DT.playEnd!=null && t>=DT.playEnd){ DT.playEnd=null; audio.pause(); setPlayIc(false); } }
function dictNext(){ /* 清单下一句；无则完成 */
  if(DT.qi < DT.list.length-1){ DT.qi++; renderDictatePass(0); }
  else { PROG.dictate=true; audio.pause(); setPlayIc(false);
    $("dt-score").textContent="本次听写全部完成！";
    saveFollow();
    $("dt-diag").innerHTML='<div class="ddq-row">你已完成抽句四遍听写。可回预习页重温整篇，或到复习页再练跟读。</div><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:12px"><button class="chip" onclick="location.href=SIBLINGS.listen">返回预习 →</button><button class="cta" onclick="location.href=SIBLINGS.follow">再练跟读 →</button></div>';
    $("dt-diag").classList.add("on");
  }
}
function showPick(){ $("pickpick").classList.add("on"); }
function closePick(){ $("pickpick").classList.remove("on"); }
/* 每段句索引区间 [start,end] */
function buildParas(){
  var B=BOOK[state.pg], s=0, out=[];
  B.arts.forEach(function(ar){ out.push([s, s+ar.length-1]); s+=ar.length; });
  return out;
}
function sentScore(segIdx){
  var m=(SEGS[segIdx]||"").match(/[A-Za-z']+/g); if(!m) return 0;
  var sc=0;
  for(var i=0;i<m.length;i++){
    var lo=m[i].toLowerCase().replace(/[.,'!?]+$/,'');
    if(LEVEL[lo]==="X") sc+=4; else if(TRAP[lo]) sc+=3;
    else if(TOPIC[lo])  sc+=2; else if(BASE[lo]) sc+=1;
  }
  return sc;
}
function pickCount(k){
  var cand=[];
  for(var i=0;i<SEGS.length;i++) cand.push(i);
  cand.sort(function(a,b){ return sentScore(b)-sentScore(a); });
  var list=cand.slice(0,k).sort(function(a,b){return a-b;});   // 分值Top-K，按原文顺序
  startPick(list);
}
function confirmCustom(){
  var paras=buildParas(), list=[], chs=document.querySelectorAll(".pc-check:checked");
  if(!chs.length){ toast("请至少勾选一个段落"); return; }
  chs.forEach(function(ch){ var i=+ch.dataset.i; for(var s=paras[i][0];s<=paras[i][1];s++) list.push(s); });
  list.sort(function(a,b){return a-b;});
  startPick(list);
}
function startPick(list){
  DT.list=list; DT.qi=0; DT.askedWay=false; DT.g=0; DT.groups=[];
  $("pickpick").classList.remove("on"); $("pcustom").classList.remove("on");
  showWayPick();
  toast("已选 "+list.length+" 句 · 开始后可重选");
}
function showWayPick(){ $("waypick").classList.add("on"); }
function pickWay(w){
  if(w==="nb"){ pickWayNb(); return; }
  DT.way=w; DT.askedWay=true;
  $("waypick").classList.remove("on");
  toast(w==="paper" ? "稿纸听写：屏幕只显示下划线，用纸笔写，每遍点「核对答案」对照" : "键盘输入听写：在划线处打字，四遍听完末遍判分");
  renderDictatePass(0);
}
function pickWayNb(){ DT.way="nb"; DT.askedWay=true; $("waypick").classList.remove("on"); NB.i=0; $("nbOv").classList.add("on"); nbShow(); }
function nbShow(){
  var si=DT.list[NB.i], seg=SEGS[si];
  var words = partsOf(seg).filter(function(p){ return p.t.trim(); }).map(function(p){ return p.t.trim(); });
  var c = $("nbCard");
  c.innerHTML = '<div class="quiz-prog">听写本 · 第 '+(NB.i+1)+' / '+DT.list.length+' 句</div>'
    + '<div class="nb-audio"><button class="quiz-opt" style="flex:1;text-align:center" onclick="playSentence('+si+')">▶ 播放本句</button>'
    + '<button class="quiz-opt" style="text-align:center" onclick="playSentence('+si+')">↻ 再听</button></div>'
    + '<div class="nb-tip">✍️ 请拿出<b>听写本</b>，把听到的句子写下来。写完后点「看原文核对」，<b>点出你写错的词</b>——特别注意<b>动词的形式变化</b>（-ed / -ing / 三单 -s / 不规则变形）！写完记得拍照发到微信群。</div>'
    + '<div style="display:flex;gap:8px"><button class="quiz-opt" style="flex:1;text-align:center;border-color:#5a76d8" id="nbReveal">看原文核对 →</button></div>'
    + '<div id="nbCheckZone"></div>';
  $("nbReveal").onclick = function(){ nbReveal(words); };
}
function nbReveal(words){
  var zone = $("nbCheckZone");
  zone.innerHTML = '<div class="quiz-prog" style="margin-top:12px">点出你写错的词（没错就点完成）：</div>'
    + '<div class="nb-words">' + words.map(function(w,i){ return '<span class="nb-w" data-i="'+i+'" onclick="this.classList.toggle(\'mark\')">'+escQ(w)+'</span>'; }).join("") + '</div>'
    + '<div style="display:flex;gap:8px"><button class="quiz-opt" style="flex:1;text-align:center" onclick="nbNext()">'+(NB.i+1<DT.list.length?"下一句 →":"完成听写 ✓")+'</button></div>';
  zone.scrollIntoView({block:"nearest"});
}
function nbNext(){
  document.querySelectorAll("#nbCheckZone .nb-w.mark").forEach(function(el){
    var w = el.textContent.trim(); if(w) vqMark(w, "unknown");
  });
  NB.i++;
  if(NB.i<DT.list.length){ nbShow(); return; }
  if(VQKEY) toast("错词已记入待复习词汇 ✓");
  PROG.dictate=true; saveFollow();
  $("nbOv").classList.remove("on");
  toast("听写本模式完成 ✓ 记得拍照发微信群！");
}

/* ---------- 单环节状态机（听写） ---------- */
function setStage(s){
  document.body.className = "dictate" + (state.dialog?" dialog":"");
  $("reader").style.display = "none";
  syncCnUI();
  audio.pause();
  $("pickpick").classList.remove("on");
  $("waypick").classList.remove("on");
  if(!(DT.list && DT.list.length)){ showPick(); return; }  // 先选抽句
  if(!DT.askedWay){ showWayPick(); return; }               // 再选方式
  renderDictatePass(0);
}
function syncCnUI(){
  var t=$("cnToggle"); if(!t) return;
  t.classList.toggle("on", state.cn);
  document.querySelectorAll(".sent .zh").forEach(function(z){ z.classList.toggle("hide",!state.cn); });
  if($("dt-zh")) $("dt-zh").classList.toggle("hide",!state.cn);
}
function bindSentClicks(){
  $("body").addEventListener("click",function(e){
    var sent=e.target.closest(".sent"); if(!sent) return;
    var i=+sent.dataset.i; state.idx=i;
    var at=DT.list.indexOf(i); if(at>=0){ DT.qi=at; renderDictatePass(0); } else replayCurrentSentence();
  });
}
function playSentence(i){
  state.idx=i; setActiveSentence(i);
  var at=DT.list.indexOf(i); if(at>=0){ DT.qi=at; renderDictatePass(0); } else replayCurrentSentence();
}
function togglePlay(){ replayCurrentSentence(); }
function nxt(d){ var L=SEGS.length; var i=Math.max(0,Math.min(L-1,state.idx+d));
  state.idx=i;
  var at=DT.list.indexOf(i); if(at>=0){ DT.qi=at; renderDictatePass(0); } }
audio.addEventListener("timeupdate", function(){
  var t=audio.currentTime; if(!isFinite(t)) return;
  dtTimeupdate(t);
});
$("dtRelisten").onclick=dtRelisten;
$("nextStage").onclick=function(){ location.href="../index.html"; };
"""

# ---- 组装 ----
def steps_one(num, key, label):
    return '      <div class="step on" data-s="%s"><b>%d</b><span>%s</span></div>' % (key, num, label)

def build(stage, subtitle, bodyclass, step_html, main_html, dock_mid, dock_cta, stage_js, stage_dir_binds, tail_html):
    head = (head_top(subtitle, bodyclass) + HEADER
            + '\n  <div class="flowbar">\n    <nav class="steps" id="steps">\n' + step_html + '\n    </nav>\n  </div>\n'
            + main_html + dock(dock_mid, dock_cta)
            + '\n</div>\n<div class="toast" id="toast"></div>\n'
            + AUDIO + '\n<script>\n' + DATA + '\n</script>\n<script>')
    core = stage_js + "\n</script>"
    dirjs = DIR_JS_HEAD + TYPES + "\n" + DIR_JS_MID + UG + DIR_JS_TAIL.replace("__STAGE_DIR_BINDS__", stage_dir_binds)
    tail = DIR_PANEL + tail_html + "\n</body></html>\n"
    doc = head + SHARED_JS + core + dirjs + tail
    assert doc.count("__CUR__") == 1
    return doc.replace("__CUR__", stage)

def build_listen():
    main = READER + "\n  </main>"
    return build("listen", "课文预习（聆听）", "listen", steps_one(1, "listen", "预习（聆听）"),
                 main, MID_LISTEN, "进入 复习 →", LISTEN_JS, LISTEN_DIR_BINDS, QUIZOV)

def build_follow():
    main = READER + FSTAGE + "\n  </main>"
    return build("follow", "课文复习（跟读）", "follow", steps_one(2, "follow", "跟读"),
                 main, MID_FOLLOW, "进入 听写 →", FOLLOW_JS, PLAIN_DIR_BINDS, "")

def build_dictate():
    main = READER + WAYPICKS + DICT_PANEL
    js = DICTATE_JS + "\n" + FUNC_NUMB + "\n" \
         + "\nfunction pickCustom(){" + PICKCUSTOM[len("function pickCustom(){"):] + "\n}\n"
    return build("dictate", "课文听写", "dictate", steps_one(3, "dictate", "听写"),
                 main, MID_DICTATE, "完成本课", js, PLAIN_DIR_BINDS, NBOV)

def write(name, content):
    p = os.path.join(HERE, name)
    open(p, "w", encoding="utf-8", newline="\n").write(content)
    print("写出", name, len(content), "chars")

write("预习_模板.html", build_listen())
write("复习_模板.html", build_follow())
write("听写_模板.html", build_dictate())

# 自检：占位符齐全、环节互斥（不含他环节函数/面板）
for fn, must, mustnot in [
    ("预习_模板.html", ["__PG__", "__TITLE__", "__QDATA__", "__VQKEY__", "__BOOK_EXTRA__", "__UG_EXTRA__", "__SIBLINGS__",
                    "showQuiz", "mkMode", "applyBlind", "listenLoop", 'var DB={"ZH"', 'id="quizOv"', "setListenN"],
     ["followPlaySentence", "renderDictatePass", "pickWay", "nbShow", "dtRenderSentence", "id=\"fstage\"", "id=\"nbOv\""]),
    ("复习_模板.html", ["__PG__", "__TITLE__", "__QDATA__", "__VQKEY__", "__BOOK_EXTRA__", "__UG_EXTRA__", "__SIBLINGS__",
                    "followPlaySentence", "vqWordsFor", "renderGapWords", "showGap", 'var DB={"ZH"', 'id="fstage"', 'id="fpass"'],
     ["showQuiz", "renderDictatePass", "pickWay", "nbShow", "applyBlind", 'id="quizOv"', 'id="nbOv"', "listenLoop"]),
    ("听写_模板.html", ["__PG__", "__TITLE__", "__QDATA__", "__VQKEY__", "__BOOK_EXTRA__", "__UG_EXTRA__", "__SIBLINGS__",
                    "renderDictatePass", "pickCount", "pickWay", "nbShow", "vqMark", "var FUNCTION", 'var DB={"ZH"', 'id="waypick"', 'id="nbOv"'],
     ["showQuiz", "followPlaySentence", "applyBlind", "listenLoop", 'id="quizOv"', 'id="fstage"']),
]:
    t = open(os.path.join(HERE, fn), encoding="utf-8").read()
    for m in must:
        assert m in t, fn + " 缺少 " + m
    for m in mustnot:
        assert m not in t, fn + " 不应含 " + m
print("三模板自检通过")
