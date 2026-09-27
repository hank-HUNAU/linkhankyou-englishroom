/**
 * 批量升级 12 个词汇诊断页的测试引擎（幂等，已打补丁的文件自动跳过）：
 *  1) 干扰项改为「优选 + 确定性」生成，同题选项固定（难度/区分度才可比）
 *  2) 支持人工审校覆盖：词条 dis 字段 或 window.__VQ_DIS__
 *  3) 逐题答题数据补全：itemId / opts / picked
 * 用法：node _patch_vocab.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const DIR = path.join(__dirname, '词汇诊断');
const MARK = '/*VQ-PATCH*/';

const R1_OLD = `const distractors = shuffle(WORDS.filter(x => x.zh !== w.zh && x.en !== w.en)).slice(0, 3);`;
const R1_NEW = `const distractors = pickDistractors(w, 'zh', 3);`;
const R2_OLD = `const distractors = shuffle(WORDS.filter(x => x.en !== w.en && x.pos === w.pos)).slice(0, 3);`;
const R2_NEW = `const distractors = pickDistractors(w, 'en', 3);`;

const SHUFFLE_ANCHOR = `const shuffle = a => { for (let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; };`;
const DIST_BLOCK = SHUFFLE_ANCHOR + `

${MARK} /* ── 干扰项优选：确定性生成，保证同一题的选项集合对所有学生一致（难度/区分度才可比） ──
   优先级：人工审校(w.dis / window.__VQ_DIS__) → 同类+同词性+同层级 → 同类+同词性 → 同词性+同层级 → 同词性 → 全体
   排除：自身、近义释义、同词根(climb/climbing)、重复释义；同层内按词长相近排序，避免靠长度猜答案 */
const VQ_DIS = (typeof window !== 'undefined' && window.__VQ_DIS__) ? window.__VQ_DIS__ : {};
function vqEnStem(s){ return String(s||'').toLowerCase().replace(/[^a-z]/g,'').replace(/(ings|ing|ied|ed|ies|es|s|er|est|ly)$/,''); }
function vqEnClose(a, b){
  const x = vqEnStem(a), y = vqEnStem(b);
  if (!x || !y) return false;
  if (x === y) return true;
  return x.length >= 4 && y.length >= 4 && (x.startsWith(y) || y.startsWith(x));
}
function vqZhClean(s){ return String(s||'').replace(/[（(].*?[)）]/g,'').replace(/[，,、;；。.！!？?\\s]/g,''); }
function vqZhClose(a, b){
  const x = vqZhClean(a), y = vqZhClean(b);
  if (!x || !y) return false;
  return x === y || x.includes(y) || y.includes(x);
}
function pickDistractors(w, field, n){
  n = n || 3;
  const ov = (w && w.dis && typeof w.dis === 'object') ? w.dis : VQ_DIS[String(w.en||'').toLowerCase()];
  if (ov && Array.isArray(ov[field]) && ov[field].length >= n){
    return ov[field].slice(0, n).map(v => field === 'zh' ? { zh: v, en: '' } : { en: v, zh: '' });
  }
  const L = String(w[field] || '').length;
  const usable = x => x !== w
    && String(x[field]||'').toLowerCase() !== String(w[field]||'').toLowerCase()
    && !vqEnClose(x.en, w.en)
    && !(field === 'zh' && vqZhClose(x.zh, w.zh));
  const tiers = [
    x => x.pos === w.pos && x.cat === w.cat && x.level === w.level,
    x => x.pos === w.pos && x.cat === w.cat,
    x => x.pos === w.pos && x.level === w.level,
    x => x.pos === w.pos,
    () => true
  ];
  const picked = [], seen = new Set([String(w[field]||'').toLowerCase()]);
  for (const t of tiers){
    if (picked.length >= n) break;
    const pool = WORDS.filter(x => usable(x) && t(x)).sort((a, b) => {
      const da = Math.abs(String(a[field]||'').length - L), db2 = Math.abs(String(b[field]||'').length - L);
      if (da !== db2) return da - db2;
      return String(a.en).localeCompare(String(b.en));
    });
    for (const c of pool){
      if (picked.length >= n) break;
      const v = String(c[field]||'').toLowerCase();
      if (!v || seen.has(v)) continue;
      seen.add(v); picked.push(c);
    }
  }
  return picked.slice(0, n);
}`;

const R4_OLD = `function renderQuestion(){
  test.answered = false;
  test.questionStartAt = Date.now();`;
const R4_NEW = `function renderQuestion(){
  test.answered = false;
  test.questionStartAt = Date.now();
  test.curOpts = null; test.curPicked = null; ${MARK}`;

const R5_OLD = `    const opts = shuffle([w.zh, ...distractors.map(x => x.zh)]);`;
const R5_NEW = `    const opts = shuffle([w.zh, ...distractors.map(x => x.zh)]);
    test.curOpts = opts.slice(); ${MARK}`;
const R6_OLD = `      const opts = shuffle([w.en, ...distractors.map(x => x.en)]);`;
const R6_NEW = `      const opts = shuffle([w.en, ...distractors.map(x => x.en)]);
      test.curOpts = opts.slice(); ${MARK}`;

const R7_OLD = `        const ok = btn.dataset.zh === w.zh;`;
const R7_NEW = `        test.curPicked = btn.dataset.zh; ${MARK}
        const ok = btn.dataset.zh === w.zh;`;
const R8_OLD = `          const ok = btn.dataset.en === w.en;`;
const R8_NEW = `          test.curPicked = btn.dataset.en; ${MARK}
          const ok = btn.dataset.en === w.en;`;

const R9_OLD = `  const result = applyTestResult(w, ok, { mode: effectiveMode, skipped: !!skipped, timeMs, errorType });`;
const R9_NEW = `  const result = applyTestResult(w, ok, { mode: effectiveMode, skipped: !!skipped, timeMs, errorType,
    opts: test.curOpts || null, picked: test.curPicked || null }); ${MARK}`;

const R10_OLD = `  rec.testHistory.push({
    mode: meta.mode, fromStatus: cur, toStatus: rec.status,
    correct: !!ok, skipped: !!meta.skipped, uncertain: !!meta.uncertain,
    timeMs: meta.timeMs || 0, errorType: meta.errorType || null,
    testedAt: Date.now()
  });`;
const R10_NEW = `  rec.testHistory.push({
    itemId: k, mode: meta.mode, fromStatus: cur, toStatus: rec.status,
    correct: !!ok, skipped: !!meta.skipped, uncertain: !!meta.uncertain,
    timeMs: meta.timeMs || 0, errorType: meta.errorType || null,
    opts: meta.opts || null, picked: meta.picked || null,
    testedAt: Date.now()
  }); ${MARK}`;

const R11_OLD = `const WORDS = RAW.map(r => ({ en:r[0], ipa:r[1], pos:r[2], zh:r[3], level:r[4], cat:r[5], ex:r[6] }));`;
const R11_NEW = `const WORDS = RAW.map(r => ({ en:r[0], ipa:r[1], pos:r[2], zh:r[3], level:r[4], cat:r[5], ex:r[6], dis:r[7] || null })); ${MARK}`;

function rep(s, from, to, label, errs, crlf){
  const f = crlf ? from.replace(/\n/g, '\r\n') : from;
  const t = crlf ? to.replace(/\n/g, '\r\n') : to;
  if(!s.includes(f)){ errs.push(label); return s; }
  return s.replace(f, t);
}

const files = fs.readdirSync(DIR).filter(f => /^词汇诊断.*\.html$/.test(f)).sort();
let done = 0, skip = 0;
for(const f of files){
  const fp = path.join(DIR, f);
  let s = fs.readFileSync(fp, 'utf8');
  if(s.includes(MARK)){ console.log('跳过(已打补丁) ' + f); skip++; continue; }
  const crlf = s.includes('\r\n');
  const errs = [];
  s = rep(s, R1_OLD, R1_NEW, 'unknown干扰项', errs, crlf);
  s = rep(s, R2_OLD, R2_NEW, 'known干扰项', errs, crlf);
  s = rep(s, SHUFFLE_ANCHOR, DIST_BLOCK, '插入pickDistractors', errs, crlf);
  s = rep(s, R4_OLD, R4_NEW, 'renderQuestion重置', errs, crlf);
  s = rep(s, R5_OLD, R5_NEW, 'unknown选项记录', errs, crlf);
  s = rep(s, R6_OLD, R6_NEW, 'known选项记录', errs, crlf);
  s = rep(s, R7_OLD, R7_NEW, 'unknown选择记录', errs, crlf);
  s = rep(s, R8_OLD, R8_NEW, 'known选择记录', errs, crlf);
  s = rep(s, R9_OLD, R9_NEW, 'finishQuestion传参', errs, crlf);
  s = rep(s, R10_OLD, R10_NEW, 'testHistory字段', errs, crlf);
  s = rep(s, R11_OLD, R11_NEW, '词表dis字段', errs, crlf);
  if(errs.length){ console.log('✗ ' + f + ' → 未匹配: ' + errs.join(' / ')); continue; }
  fs.writeFileSync(fp, s, 'utf8');
  console.log('✓ ' + f + (crlf ? ' (CRLF)' : ' (LF)'));
  done++;
}
console.log(`\n完成 ${done} 个，跳过 ${skip} 个，共 ${files.length} 个`);