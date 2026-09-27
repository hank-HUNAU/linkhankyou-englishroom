/* 视觉对齐校验：令牌完整性 + 硬编码残留 + 关键组件取值一致性 */
'use strict';
const fs = require('fs'), path = require('path');
const R = __dirname;
const read = f => fs.readFileSync(path.join(R, f), 'utf8');

const ui = read('ui.css');
const pages = ['login.html', '学生端.html', '教师端.html'];
let bad = 0;

/* 1. ui.css 定义的令牌 */
const defined = new Set();
for (const m of ui.matchAll(/^\s*(--[\w-]+)\s*:/gm)) defined.add(m[1]);
console.log('ui.css 定义令牌 ' + defined.size + ' 个');

/* 2. 每页 var() 引用是否都有定义 */
console.log('\n=== 令牌引用完整性 ===');
for (const p of pages) {
  const src = read(p);
  const local = new Set();
  for (const m of src.matchAll(/(--[\w-]+)\s*:/g)) local.add(m[1]);   // 页面内联自定义（若有）
  const used = new Set();
  for (const m of src.matchAll(/var\(\s*(--[\w-]+)/g)) used.add(m[1]);
  const missing = [...used].filter(t => !defined.has(t) && !local.has(t));
  console.log((missing.length ? '  ✗ ' : '  ✓ ') + p + ' 引用 ' + used.size + ' 个令牌' +
    (missing.length ? '，未定义: ' + missing.join(',') : ''));
  if (missing.length) bad++;
}

/* 3. 硬编码 border-radius 残留（50% 与圆形除外） */
console.log('\n=== 硬编码圆角残留 ===');
for (const p of pages) {
  const src = read(p);
  const hits = [...src.matchAll(/border-radius\s*:\s*(\d+)px/g)];
  console.log((hits.length ? '  ✗ ' : '  ✓ ') + p + ' 硬编码圆角 ' + hits.length + ' 处' +
    (hits.length ? '：' + hits.map(h => h[1] + 'px').join(',') : ''));
  if (hits.length) bad++;
}

/* 4. 关键组件取值对比 */
console.log('\n=== 主按钮 .btn ===');
const pick = (src, re) => { const m = src.match(re); return m ? m[1].replace(/\s+/g, ' ').trim() : '(未找到)'; };
for (const p of pages) {
  const src = read(p);
  const block = pick(src, /\.btn\s*\{([^}]*)\}/);
  console.log('  ' + p + ': ' + block);
}

console.log('\n=== 卡片阴影 ===');
for (const p of pages) {
  const src = read(p);
  const g = sel => { const m = src.match(new RegExp(sel + '[^{]*\\{[^}]*box-shadow\\s*:\\s*([^;}]+)')); return m ? m[1].trim() : '-'; };
  console.log('  ' + p + '  .card=' + g('\\.card') + '   .gate-card=' + g('\\.gate-card'));
}

console.log('\n=== 徽标排版（字号/字重/padding/圆角/字距）===');
const badgeSel = ['\\.tag\\s*\\{', '\\.kind\\s*\\{', '\\.sec-n\\s*\\{', '\\.tz-chip\\s*\\{', '\\.pill\\s*\\{', '\\.fl\\s*\\{'];
for (const p of pages) {
  const src = read(p);
  for (const sel of badgeSel) {
    const re = new RegExp(sel + '([^}]*)');
    const m = src.match(re);
    if (!m) continue;
    const g = k => { const x = m[1].match(new RegExp(k + '\\s*:\\s*([^;}]+)')); return x ? x[1].trim() : '-'; };
    console.log('  ' + p + ' ' + sel.replace(/[\\{}]|\s\*/g, '') + ': fs=' + g('font-size') +
      ' fw=' + g('font-weight') + ' pad=' + g('padding') + ' ls=' + g('letter-spacing'));
  }
}

console.log('\n──────────────────────────────');
console.log(bad ? '结果：发现 ' + bad + ' 项问题' : '结果：✓ 全部通过');
process.exit(bad ? 1 : 0);