/**
 * 为 12 个词汇诊断页接入「干扰项人工审校覆盖表」（幂等）：
 *  1) 把 VQ_DIS 改为惰性读取 → 覆盖表加载顺序不再敏感
 *  2) 在主脚本前注入 <script src="干扰项审校.js"></script>
 * 用法：node _patch_vqdis.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const DIR = path.join(__dirname, '词汇诊断');
const MARK = '/*VQ-DIS*/';
const TAG = '<script src="干扰项审校.js"></script>';

const OLD = `const VQ_DIS = (typeof window !== 'undefined' && window.__VQ_DIS__) ? window.__VQ_DIS__ : {};`;
const NEW = `function vqDis(){ return (typeof window !== 'undefined' && window.__VQ_DIS__) ? window.__VQ_DIS__ : {}; } ${MARK}`;
const OLD_USE = `: VQ_DIS[String(w.en||'').toLowerCase()];`;
const NEW_USE = `: vqDis()[String(w.en||'').toLowerCase()];`;

const files = fs.readdirSync(DIR).filter(f => /^词汇诊断.*\.html$/.test(f)).sort();
let done = 0, skip = 0;
for(const f of files){
  const fp = path.join(DIR, f);
  let s = fs.readFileSync(fp, 'utf8');
  if(s.includes(MARK)){ console.log('跳过(已处理) ' + f); skip++; continue; }
  if(!s.includes(OLD) || !s.includes(OLD_USE)){ console.log('✗ ' + f + ' → 未找到 VQ_DIS 锚点'); continue; }
  s = s.replace(OLD, NEW).replace(OLD_USE, NEW_USE);
  const i = s.indexOf('<script>');
  if(i < 0){ console.log('✗ ' + f + ' → 未找到主脚本'); continue; }
  s = s.slice(0, i) + TAG + '\n' + s.slice(i);
  fs.writeFileSync(fp, s, 'utf8');
  console.log('✓ ' + f);
  done++;
}
console.log(`\n完成 ${done} 个，跳过 ${skip} 个，共 ${files.length} 个`);