
var $=id=>document.getElementById(id);
var audio=$("audio");
var TL, ZH, TITLE_START, ENTITY, ENTITYMULTI, LEVEL, TOPIC, BASE, TRAP;
function initDB(){ TL=DB.TL; ZH=DB.ZH||{}; TITLE_START=DB.TITLE_START;
  ENTITY=DB.ENTITY||{}; ENTITYMULTI=DB.ENTITYMULTI||{}; LEVEL=DB.LEVEL||{}; TOPIC=DB.TOPIC||{}; BASE=DB.BASE||{}; TRAP=DB.TRAP||{}; }

/* == 三页互链注入点（_gen_follow_v2.py 注入本篇 预习/复习/听写 文件名） == */
var SIBLINGS=__SIBLINGS__;
var CUR="dictate";
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

/* ============ 听写：全句挖空逐词填 · 三遍 ============ */
var FUNCTION={}; [
  "a","an","the","this","that","these","those","some","any","every","each","no","another","other","others",
  "of","to","in","on","at","by","for","with","from","into","onto","about","over","under","across","before","after","without","between","through","around","along","above",
  "and","but","or","so","because","if","then","than","when","while","as","although","until","since","nor","yet",
  "i","you","he","she","it","we","they","me","him","her","us","them","my","your","his","its","our","their",
  "mine","yours","hers","ours","theirs","who","what","whose","whom","which","someone","everyone","nobody","anyone","anybody","everybody","somebody","nothing",
  "am","is","are","was","were","be","been","being","have","has","had","do","does","did","can","could","will","would","shall","should","may","might","must",
  "not","don't","doesn't","didn't","can't","couldn't","won't","wouldn't","isn't","aren't","wasn't","weren't","haven't","hasn't","hadn't","i'm","you're","we're","they're","he's","she's","it's","that's","what's","who's","there's","here's","i've","you've","we've","they've","i'll","you'll","he'll","she'll","we'll","they'll","let's","need","needs",
  "very","really","so","too","also","still","only","just","here","there","then","now","again","never","often","always","already","sometimes","once","twice","ever","even",
  "up","down","out","off","back","on","away"
].forEach(function(w){ FUNCTION[w]=1; });
var NUMB={}; ["zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety","hundred","thousand"].forEach(function(w){NUMB[w]=1;});

function pickCustom(){
  var pc=$("pcustom"), paras=buildParas();
  if(!pc.dataset.built){
    pc.dataset.built=1;
    pc.innerHTML='<div class="w-sub" style="margin:12px 0 6px">勾选要听写的段落（段内全部句都会进入听写）：</div>'+
      paras.map(function(r,i){ return '<label style="display:flex;gap:9px;align-items:center;padding:9px 11px;border:1px solid var(--line);border-radius:10px;margin-bottom:6px;cursor:pointer;font-size:13px"><input type="checkbox" class="pc-check" data-i="'+i+'"><span>段落 '+(i+1)+' · '+((r[1]-r[0]+1)+' 句')+'</span></label>'; }).join('')+
      '<div style="display:flex;gap:8px;margin-top:10px"><button class="cta" onclick="confirmCustom()">确定</button></div>';
  }
  pc.classList.add("on");

