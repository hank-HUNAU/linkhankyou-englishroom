/* 重建 U5 四篇 BOOK_EXTRA.arts 为句子级，与句级音频/SRT 严格 1:1。
   段落分组沿用当前 arts 的段落结构（每个段落块拆成其包含的权威句子）。
   校验：①展平句数 == 权威句数 ②展平文本 == 权威文本 ③重建段落拼接 == 原段落拼接。 */
const fs = require('fs');
const path = require('path');
const PAGE_DIR = path.join(__dirname, '篇章页');
const ARCHIVE = path.join(__dirname, '..', 'U5_FreeTime', '01_正文篇章');

const pages = [
  { pg: 48, file: '读写_048_robotics_club.html' },
  { pg: 51, file: '读写_051_favourite_technology.html' },
  { pg: 52, file: '读写_052_tech_break.html' },
  { pg: 54, file: '读写_054_school_concert.html' },
];

function norm(s) { return String(s).replace(/\s+/g, ' ').trim(); }

function evalBookExtra(h) {
  const idx = h.indexOf('var BOOK_EXTRA=');
  if (idx < 0) throw new Error('BOOK_EXTRA not found');
  let i = idx + 'var BOOK_EXTRA='.length;
  while (i < h.length && /\s/.test(h[i])) i++;
  let depth = 0, start = i, end = -1;
  for (; i < h.length; i++) {
    const c = h[i];
    if (c === '{' || c === '[') depth++;
    else if (c === '}' || c === ']') { depth--; if (depth === 0) { end = i; break; } }
  }
  if (end < 0) throw new Error('unbalanced BOOK_EXTRA');
  const expr = h.slice(start, end + 1);
  const obj = (new Function('return ' + expr))();
  return { obj, start, end };
}

function rebuildArts(blobs, sents) {
  const arts = []; let si = 0;
  for (const blob of blobs) {
    let para = [], acc = '';
    while (si < sents.length) {
      const cand = para.length ? acc + ' ' + sents[si] : sents[si];
      if (norm(blob).startsWith(norm(cand))) {
        para.push(sents[si]); acc = cand; si++;
        if (norm(blob) === norm(cand)) break;
      } else break;
    }
    arts.push(para);
  }
  if (si < sents.length) arts.push(sents.slice(si));
  return arts;
}

let changed = 0;
for (const p of pages) {
  const h = fs.readFileSync(path.join(PAGE_DIR, p.file), 'utf8');
  const canonFile = path.join(ARCHIVE, '句级数据_p' + String(p.pg).padStart(3, '0') + '.json');
  const canon = JSON.parse(fs.readFileSync(canonFile, 'utf8'));
  const sents = canon.sentences.map(s => s.text);
  const { obj, start, end } = evalBookExtra(h);
  const key = String(p.pg);
  const entry = obj[key] || obj[p.pg];
  if (!entry) { console.log(p.file, '→ 无 ENTRY，跳过'); continue; }
  const oldBlobs = entry.arts;
  const oldFlat = [].concat(...oldBlobs).map(norm);
  const newArts = rebuildArts(oldBlobs, sents);
  const newFlat = [].concat(...newArts).map(norm);
  const okCount = newFlat.length === sents.length;
  const okText = JSON.stringify(newFlat) === JSON.stringify(sents.map(norm));
  const repro = newArts.map(par => par.join(' ')).map(norm);
  const orig = oldBlobs.map(par => par.join(' ')).map(norm);
  const okRepro = JSON.stringify(repro) === JSON.stringify(orig);
  console.log(`\n${p.file}`);
  console.log(`  oldFlat=${oldFlat.length} newFlat=${newFlat.length} canon=${sents.length}`);
  console.log(`  okCount=${okCount} okText=${okText} okRepro=${okRepro}`);
  if (!(okCount && okText && okRepro)) {
    console.log('  !! 校验失败，跳过（未改动文件）');
    continue;
  }
  if (JSON.stringify(oldBlobs) === JSON.stringify(newArts)) {
    console.log('  → 已是句子级，无需改动');
  } else {
    entry.arts = newArts;
    const newExpr = JSON.stringify(obj);
    const newH = h.slice(0, start) + newExpr + h.slice(end + 1);
    fs.writeFileSync(path.join(PAGE_DIR, p.file), newH, 'utf8');
    console.log('  → 已重写 arts（段落分组保留）');
    changed++;
  }
}
console.log(`\n完成。共重写 ${changed} 个页面。`);
