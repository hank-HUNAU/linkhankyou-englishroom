/* 全量诊断 v2：感知字符串边界的括号配对（v1 因 arts 文本内含括号误判截断）。
   引擎实际读取 BOOK[PG]（line397: var B=BOOK[PG]）；BOOK_EXTRA 为死代码（无任何引用）。
   逐页解析 var BOOK={...} 中当前页条目，展平 arts 与权威句级数据比对。 */
const fs = require('fs');
const path = require('path');
const PAGE_DIR = path.join(__dirname, '篇章页');
const ARCH = 'E:/04 少儿原版课程/03 Think 0 课程制作/Codex 学习中心/Think F 教材资产';

/* 从 idx 处（应为 '{'）做感知字符串的括号配对，返回结束下标 */
function matchBrace(h, idx) {
  let depth = 0, i = idx, q = null;
  for (; i < h.length; i++) {
    const c = h[i];
    if (q) {
      if (c === '\\') { i++; continue; }
      if (c === q) q = null;
      continue;
    }
    if (c === '"' || c === "'") { q = c; continue; }
    if (c === '{' || c === '[') depth++;
    else if (c === '}' || c === ']') { depth--; if (depth === 0) return i; }
  }
  return -1;
}

function parseBook(h) {
  const m = h.match(/var BOOK=\{/);
  if (!m) return null;
  const start = m.index + m[0].length - 1;
  const end = matchBrace(h, start);
  if (end < 0) return null;
  const dbStub = new Proxy({}, { get: () => new Proxy({}, { get: () => ({}) }) });
  return { obj: (new Function('DB', 'return ' + h.slice(start, end + 1)))(dbStub), start, end };
}

function canonCount(pg) {
  const p3 = String(pg).padStart(3, '0');
  const units = fs.readdirSync(ARCH).filter(d => /^U\d+_/.test(d));
  for (const u of units) {
    const f = path.join(ARCH, u, '01_正文篇章', '句级数据_p' + p3 + '.json');
    if (fs.existsSync(f)) { const j = JSON.parse(fs.readFileSync(f, 'utf8')); return { n: j.sentences.length, unit: u }; }
  }
  return null;
}

const files = fs.readdirSync(PAGE_DIR).filter(f => /^读写_\d+_.*\.html$/.test(f)).sort();
let bad = 0, noCanon = 0;
for (const f of files) {
  const pg = parseInt(f.match(/^读写_(\d+)_/)[1], 10);
  const h = fs.readFileSync(path.join(PAGE_DIR, f), 'utf8');
  const bk = parseBook(h);
  if (!bk) { console.log(`p${pg}: 无 BOOK`); bad++; continue; }
  const entry = bk.obj[String(pg)] || bk.obj[pg];
  const c = canonCount(pg);
  if (!entry) { console.log(`p${pg}: BOOK 无该键`); bad++; continue; }
  const flat = [].concat(...(entry.arts || []));
  if (!c) { console.log(`p${pg}: BOOK展平=${flat.length}（无权威数据，跳过）`); noCanon++; continue; }
  const ok = flat.length === c.n;
  if (!ok) bad++;
  console.log(`p${pg} (${f.replace(/^读写_\d+_|\.html$/g, '')}): BOOK展平=${flat.length} 权威=${c.n} ${ok ? 'OK' : '<<< 错位'} [${c.unit}]`);
}
console.log(`\n共 ${files.length} 页；错位 ${bad} 页；无权威数据 ${noCanon} 页`);
