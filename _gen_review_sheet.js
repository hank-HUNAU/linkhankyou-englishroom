/**
 * 生成「干扰项审校工作表.csv」：把每个词条当前生效的自动干扰项导出，供教研人工审校。
 * 与页面内 pickDistractors 同源同逻辑，保证工作表内容 = 学生实际看到的选项。
 * 用法：node _gen_review_sheet.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const DIR = path.join(__dirname, '词汇诊断');

/* ── 与 _patch_vocab.js 完全一致的优选逻辑 ── */
function vqEnStem(s){ return String(s||'').toLowerCase().replace(/[^a-z]/g,'').replace(/(ings|ing|ied|ed|ies|es|s|er|est|ly)$/,''); }
function vqEnClose(a, b){
  const x = vqEnStem(a), y = vqEnStem(b);
  if (!x || !y) return false;
  if (x === y) return true;
  return x.length >= 4 && y.length >= 4 && (x.startsWith(y) || y.startsWith(x));
}
function vqZhClean(s){ return String(s||'').replace(/[（(].*?[)）]/g,'').replace(/[，,、;；。.！!？?\s]/g,''); }
function vqZhClose(a, b){
  const x = vqZhClean(a), y = vqZhClean(b);
  if (!x || !y) return false;
  return x === y || x.includes(y) || y.includes(x);
}
function pickDistractors(WORDS, w, field, n){
  n = n || 3;
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
      const da = Math.abs(String(a[field]||'').length - L), db = Math.abs(String(b[field]||'').length - L);
      if (da !== db) return da - db;
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
}

/* ── 从页面提取 RAW 数组（括号计数，稳健） ── */
function extractRaw(html){
  const i = html.indexOf('const RAW');
  if (i < 0) return null;
  const s = html.indexOf('[', i);
  let d = 0, j = s, inStr = false, esc = false;
  for (; j < html.length; j++){
    const ch = html[j];
    if (inStr){
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === '"') inStr = false;
      continue;
    }
    if (ch === '"') inStr = true;
    else if (ch === '[') d++;
    else if (ch === ']'){ d--; if (d === 0){ j++; break; } }
  }
  return JSON.parse(html.slice(s, j));
}

/* 干扰项脱离「同词性+同词类」= 语义跑题，最需要人工审校 */
function offCat(w, dis){ return dis.filter(x => x.pos !== w.pos || x.cat !== w.cat).length; }
function risk(WORDS, w, zhDis, enDis){
  const r = [];
  if (zhDis.length < 3) r.push('看词选义干扰项不足3');
  if (enDis.length < 3) r.push('选词填空干扰项不足3');
  const zc = offCat(w, zhDis), ec = offCat(w, enDis);
  if (zc) r.push('看词选义脱离词类×' + zc);
  if (ec) r.push('选词填空脱离词类×' + ec);
  const near = zhDis.filter(x => vqZhClose(x.zh, w.zh)).length;
  if (near) r.push('释义过近×' + near);
  const lens = zhDis.map(x => String(x.zh||'').length);
  if (lens.length && Math.max(...lens) - Math.min(...lens) >= 4) r.push('释义长度差异大');
  return r.join('；');
}

const esc = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
const files = fs.readdirSync(DIR).filter(f => /^词汇诊断.*\.html$/.test(f)).sort();
const rows = [['篇章','单词','词性','词类','层级','释义',
  '自动干扰项·看词选义','自动干扰项·选词填空','风险提示',
  '人工结论(保留/替换)','替换干扰项·zh(顿号分隔)','替换干扰项·en(顿号分隔)']];
let n = 0;
for (const f of files){
  const html = fs.readFileSync(path.join(DIR, f), 'utf8');
  const raw = extractRaw(html);
  if (!raw){ console.log('✗ 无法解析 ' + f); continue; }
  const WORDS = raw.map(r => ({ en:r[0], ipa:r[1], pos:r[2], zh:r[3], level:r[4], cat:r[5], ex:r[6], dis:r[7] || null }));
  const pg = f.replace(/^词汇诊断_/, '').replace(/\.html$/, '');
  for (const w of WORDS){
    const zhDis = pickDistractors(WORDS, w, 'zh', 3);
    const enDis = pickDistractors(WORDS, w, 'en', 3);
    rows.push([pg, w.en, w.pos, w.cat, w.level, w.zh,
      zhDis.map(x => x.zh).join('、'), enDis.map(x => x.en).join('、'),
      risk(WORDS, w, zhDis, enDis), '', '', '']);
    n++;
  }
}
const out = path.join(DIR, '干扰项审校工作表.csv');
fs.writeFileSync(out, '\ufeff' + rows.map(r => r.map(esc).join(',')).join('\r\n'), 'utf8');
const flagged = rows.slice(1).filter(r => r[8]).length;
console.log(`✓ 已生成 ${out}（${files.length} 篇章，${n} 词条，其中 ${flagged} 条带风险提示需优先审校）`);