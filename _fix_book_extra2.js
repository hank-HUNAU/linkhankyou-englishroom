/* 修复 U5 p048/p051：页面内有两个 var BOOK_EXTRA 声明，行尾各跟
   Object.keys(BOOK_EXTRA).forEach(k=>BOOK[k]=BOOK_EXTRA[k]) 合并进 BOOK。
   第二个声明最后执行、覆盖第一个（deb76cb 只修了第一个=死修改）。
   本脚本把【最后一个】BOOK_EXTRA 声明中当前页条目的 arts 重建为句子级。 */
const fs = require('fs');
const path = require('path');
const PAGE_DIR = path.join(__dirname, '篇章页');
const ARCH = 'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/Think F 教材资产';

function norm(s) { return String(s).replace(/\s+/g, ' ').trim(); }

/* 字符串感知的括号配对：从 idx（'{' 处）返回配对 '}' 的下标 */
function matchBrace(h, idx) {
  let depth = 0, i = idx, q = null;
  for (; i < h.length; i++) {
    const c = h[i];
    if (q) { if (c === '\\') { i++; continue; } if (c === q) q = null; continue; }
    if (c === '"' || c === "'") { q = c; continue; }
    if (c === '{' || c === '[') depth++;
    else if (c === '}' || c === ']') { depth--; if (depth === 0) return i; }
  }
  return -1;
}

/* 找最后一个 var BOOK_EXTRA={ ，返回 {start(对象'{'下标), end(配对'}'下标)} */
function findLastBookExtra(h) {
  let pos = -1;
  const re = /var BOOK_EXTRA=\{/g;
  let m;
  while ((m = re.exec(h)) !== null) { pos = m.index; }
  if (pos < 0) return null;
  const start = pos + 'var BOOK_EXTRA={'.length - 1;
  const end = matchBrace(h, start);
  return end < 0 ? null : { start, end };
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

const pages = [
  { pg: 48, file: '读写_048_robotics_club.html' },
  { pg: 51, file: '读写_051_favourite_technology.html' },
  { pg: 56, file: '读写_056_real_friend.html' },
  { pg: 63, file: '读写_063_welcoming_people.html' },
];

/* 动态定位归档中的句级数据文件 */
function findCanon(pg) {
  const p3 = '句级数据_p' + String(pg).padStart(3, '0') + '.json';
  const units = fs.readdirSync(ARCH).filter(d => /^U\d+_/.test(d));
  for (const u of units) {
    const f = path.join(ARCH, u, '01_正文篇章', p3);
    if (fs.existsSync(f)) return f;
  }
  return null;
}

for (const p of pages) {
  const fp = path.join(PAGE_DIR, p.file);
  const h = fs.readFileSync(fp, 'utf8');
  const canonFile = findCanon(p.pg);
  if (!canonFile) { console.log(p.file, '无归档句级数据，跳过'); continue; }
  const canon = JSON.parse(fs.readFileSync(canonFile, 'utf8'));
  const sents = canon.sentences.map(s => s.text);

  const loc = findLastBookExtra(h);
  if (!loc) { console.log(p.file, '未找到 BOOK_EXTRA'); continue; }
  const dbStub = new Proxy({}, { get: () => new Proxy({}, { get: () => ({}) }) });
  const obj = (new Function('return ' + h.slice(loc.start, loc.end + 1)))(dbStub);
  const key = String(p.pg);
  const entry = obj[key] || obj[p.pg];
  if (!entry) { console.log(p.file, '最后一个 BOOK_EXTRA 无 ' + key + ' 键'); continue; }

  const oldFlat = [].concat(...entry.arts).map(norm);
  const newArts = rebuildArts(entry.arts, sents);
  const newFlat = [].concat(...newArts).map(norm);
  const okCount = newFlat.length === sents.length;
  const okText = JSON.stringify(newFlat) === JSON.stringify(sents.map(norm));
  const repro = newArts.map(x => x.join(' ')).map(norm);
  const orig = entry.arts.map(x => x.join(' ')).map(norm);
  const okRepro = JSON.stringify(repro) === JSON.stringify(orig);

  console.log(`\n${p.file}（最后一个 BOOK_EXTRA 声明）`);
  console.log(`  oldFlat=${oldFlat.length} newFlat=${newFlat.length} canon=${sents.length} okCount=${okCount} okText=${okText} okRepro=${okRepro}`);
  if (!(okCount && okText && okRepro)) { console.log('  !! 校验失败，跳过'); continue; }
  if (JSON.stringify(entry.arts) === JSON.stringify(newArts)) { console.log('  → 已是句子级，无需改动'); continue; }

  entry.arts = newArts;
  const newExpr = JSON.stringify(obj);
  const newH = h.slice(0, loc.start) + newExpr + h.slice(loc.end + 1);
  fs.writeFileSync(fp, newH, 'utf8');
  console.log('  → 已重写（段落分组保留，行尾合并语句不受影响）');
}
console.log('\n完成');
