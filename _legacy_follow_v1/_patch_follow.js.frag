/* == 三环节拆分 + 聆听预习答题卡 + 听写本逐词自评（2026-10-15） == */
var QUIZ = __QDATA__;
var TASKS = (function(){ var m=(location.search||"").match(/[?&]tasks=([\w,]+)/); return m ? m[1].split(",") : null; })();
var QZ = {i:0, picks:[], done:false, score:0};
var NB = {i:0};
function tasksAllow(k){ return !TASKS || TASKS.indexOf(k) >= 0; }
function quizDone(){ return QZ.done || PROG.listen; }
function applyBlind(){
  var b = $("body");
  if(!b) return;
  if(QUIZ.length && !quizDone() && state.stage==="listen"){ b.classList.add("blind"); showQuizBanner(); }
  else { b.classList.remove("blind"); var bn=$("quizBanner"); if(bn) bn.classList.add("hide"); }
}
function showQuizBanner(){
  var bn = $("quizBanner");
  if(!bn){
    bn = document.createElement("div"); bn.id="quizBanner"; bn.className="quiz-banner";
    bn.innerHTML = '<span>🔊 预习：先盲听整篇，别看原文！听完点这里答题</span><button onclick="showQuiz()">答题</button>';
    var reader = $("reader") || document.body;
    reader.parentNode.insertBefore(bn, reader);
  }
  bn.classList.remove("hide");
}
function showQuiz(){ audio.pause(); setPlayIc(false); QZ.i=0; QZ.picks=[]; QZ.score=0; $("quizOv").classList.add("on"); renderQz(); }
function escQ(s){ return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }
function renderQz(){
  var c = $("quizCard"), q = QUIZ[QZ.i];
  var head = '<div class="quiz-prog">预习答题 · 第 ' + (QZ.i+1) + ' / ' + QUIZ.length + ' 题</div>';
  var body = "";
  if(q.t === "tf"){
    body = '<div class="quiz-q">' + escQ(q.q) + '</div><div class="quiz-opts">'
      + ["T","F","DS"].map(function(o){ return '<button class="quiz-opt big" onclick="answerTf(\''+o+'\')">'+(o==="T"?"✓ T 对":(o==="F"?"✗ F 错":"? DS 没说"))+'</button>'; }).join("") + "</div>";
  } else if(q.t === "choice"){
    body = '<div class="quiz-q">' + escQ(q.q) + '</div><div class="quiz-opts">'
      + q.opts.map(function(o,i){ return '<button class="quiz-opt" onclick="answerChoice('+i+')">'+escQ(o)+'</button>'; }).join("") + "</div>";
  } else if(q.t === "order"){
    body = '<div class="quiz-q">' + escQ(q.q) + '</div><div class="quiz-items">'
      + q.items.map(function(it,i){ var pi=QZ.picks.indexOf(i);
          return '<div class="quiz-it'+(pi>=0?" picked":"")+'" onclick="toggleOrder('+i+')"><span class="qn">'+(pi>=0?(pi+1)+"":"·")+'</span><span>'+escQ(it.txt)+'</span></div>'; }).join("")
      + '</div><div style="display:flex;gap:8px"><button class="quiz-opt" style="text-align:center" onclick="QZ.picks=[];renderQz()">重排</button>'
      + '<button class="quiz-opt" style="text-align:center;flex:1;border-color:#5a76d8" onclick="answerOrder()">提交顺序</button></div>';
  }
  c.innerHTML = head + body;
}
function toggleOrder(i){ var at=QZ.picks.indexOf(i); if(at>=0) QZ.picks.splice(at,1); else QZ.picks.push(i); renderQz(); }
function answerTf(v){ var q=QUIZ[QZ.i], ok=(v===q.a); qzFeedback(ok, q.a==="DS"?"正确答案：DS（原文没说）":"正确答案："+(q.a==="T"?"T 对":"F 错")); }
function answerChoice(i){ var q=QUIZ[QZ.i], ok=(i===q.a); qzFeedback(ok, "正确答案："+escQ(q.opts[q.a])); }
function answerOrder(){
  var q=QUIZ[QZ.i];
  if(QZ.picks.length!==q.items.length){ toast("请给全部 "+q.items.length+" 张卡片编号"); return; }
  var got=QZ.picks.map(function(i){ return q.items[i].k; });
  qzFeedback(got.join(",")===q.a.join(","), "正确顺序："+q.a.join(" → "));
}
function qzFeedback(ok, correct){
  var q=QUIZ[QZ.i];
  if(ok) QZ.score++;
  $("quizCard").innerHTML = '<div class="quiz-prog">第 '+(QZ.i+1)+' / '+QUIZ.length+' 题</div>'
    + '<div class="quiz-q">'+escQ(q.q)+'</div>'
    + '<div class="quiz-fb '+(ok?"ok":"no")+'">'+(ok?"✓ 答对了！":"✗ 不对哦。")+' '+correct+'</div>'
    + '<div style="margin-top:16px"><button class="quiz-opt" style="text-align:center;border-color:#5a76d8" onclick="qzNext()">'+(QZ.i+1<QUIZ.length?"下一题 →":"看结果 →")+'</button></div>';
}
function qzNext(){
  QZ.i++;
  if(QZ.i<QUIZ.length){ renderQz(); return; }
  var pass = QZ.score >= Math.ceil(QUIZ.length*0.75);
  $("quizCard").innerHTML = '<div class="quiz-done"><div class="quiz-score">'+QZ.score+' / '+QUIZ.length+'</div>'
    + '<div style="font-weight:800;font-size:15px;margin:10px 0">'+(pass?"🎉 预习完成！正文已解锁，去跟读吧":"再听一遍，重新答一次")+'</div>'
    + '<div style="display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap">'
    + (pass?'':'<button class="quiz-opt" style="text-align:center" onclick="showQuiz()">重答</button>')
    + '<button class="quiz-opt" style="text-align:center;border-color:#5a76d8" onclick="closeQuiz()">'+(pass?"开始看原文 →":"先看原文")+'</button></div></div>';
  if(pass){ QZ.done=true; PROG.listen=true; saveFollow(); if(typeof setStageBadges==="function") setStageBadges(); }
}
function closeQuiz(){ $("quizOv").classList.remove("on"); applyBlind(); if(typeof paint==="function") paint(); }
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
  NB.i++;
  if(NB.i<DT.list.length){ nbShow(); return; }
  PROG.dictate=true; saveFollow();
  $("nbOv").classList.remove("on");
  toast("听写本模式完成 ✓ 记得拍照发微信群！");
  if(typeof setStageBadges==="function") setStageBadges();
}
