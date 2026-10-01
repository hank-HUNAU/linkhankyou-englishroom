/**
 * 校验：三页引用的图标 id 必须在 ui.js 的 sprite 中已定义（防止出现空白图标）。
 * 用法：node _check_icons.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = __dirname;

const ui = fs.readFileSync(path.join(ROOT, 'ui.js'), 'utf8');
const defined = new Set();
const re = /^\s*([A-Za-z][\w]*):\s*'/gm;
let m;
while ((m = re.exec(ui))) defined.add(m[1]);

const pages = ['index.html', '教师端.html', 'login.html'];
const used = new Map();
let bad = 0;
for (const p of pages) {
  const s = fs.readFileSync(path.join(ROOT, p), 'utf8');
  for (const mm of s.matchAll(/href="#i-([A-Za-z][\w]*)"/g)) {
    if (!defined.has(mm[1])) { console.log('✗ ' + p + ' 引用了未定义图标: i-' + mm[1]); bad++; }
    used.set(mm[1], (used.get(mm[1]) || 0) + 1);
  }
  for (const mm of s.matchAll(/ICON\('([A-Za-z][\w]*)'/g)) {
    if (!defined.has(mm[1])) { console.log('✗ ' + p + ' ICON() 未定义: ' + mm[1]); bad++; }
    used.set(mm[1], (used.get(mm[1]) || 0) + 1);
  }
  // 动态图标：ICON(isPre?'book':'loop') 之类，单独列出供人工确认
  for (const mm of s.matchAll(/ICON\([^)]*\?[^)]*\)/g)) console.log('· 动态图标（人工确认）: ' + p + ' → ' + mm[0]);
}
console.log('\nsprite 已定义 ' + defined.size + ' 个图标，页面实际引用 ' + used.size + ' 个：');
console.log([...used.keys()].sort().join(', '));
const unused = [...defined].filter(k => !used.has(k));
console.log('\n未被引用（可保留备用）: ' + (unused.join(', ') || '无'));
console.log(bad ? '\n结果：✗ 有 ' + bad + ' 处问题' : '\n结果：✓ 全部图标引用有效');