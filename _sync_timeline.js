#!/usr/bin/env node
// 把 assets/timeline.json 同步进 index.html 的 ==TL-DATA-START/END== 块。
// 时间轴的唯一权威源是 assets/timeline.json；index.html 里那段是它的投影。
// 改完 timeline.json 跑一次本脚本，再用 _timeline_check.js 验收。
//
// 用法：node _sync_timeline.js [--check]
//   --check  只报告差异，不写盘
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = __dirname;
const HTML = path.join(ROOT, 'index.html');
const TJ = path.join(ROOT, 'assets', 'timeline.json');
const CHECK_ONLY = process.argv.includes('--check');

const START = '/* ==TL-DATA-START==';
const END = '/* ==TL-DATA-END== */';

const tj = JSON.parse(fs.readFileSync(TJ, 'utf8'));
const pids = Object.keys(tj).sort((a, b) => parseInt(a.replace(/\D/g, ''), 10) - parseInt(b.replace(/\D/g, ''), 10));
const parts = pids.map(pid => {
  const num = String(parseInt(pid.replace(/\D/g, ''), 10));
  const arr = tj[pid].map(p => '[' + p.start_s + ',' + p.end_s + ']').join(',');
  return '"' + num + '":[' + arr + ']';
});
const block = [
  '/* ==TL-DATA-START== 由 assets/timeline.json 生成（_sync_timeline.js）；请勿手改这一块 == */',
  'DB.TL={' + parts.join(',') + '};',
  '/* ==TL-DATA-END== */'
].join('\n');

const html = fs.readFileSync(HTML, 'utf8');
const a = html.indexOf(START);
const b = html.indexOf(END);
if (a < 0 || b < 0) {
  console.error('✗ index.html 里找不到 TL-DATA 标记块');
  process.exit(1);
}
const oldBlock = html.slice(a, b + END.length);
if (oldBlock === block) {
  console.log('OK   已是最新，无需同步');
  process.exit(0);
}
if (CHECK_ONLY) {
  console.log('DIFF index.html 的内联时间轴与 assets/timeline.json 不一致（跑一次不带 --check 即可同步）');
  process.exit(1);
}
fs.writeFileSync(HTML, html.slice(0, a) + block + html.slice(b + END.length), 'utf8');
console.log('✓ 已把 assets/timeline.json（' + pids.length + ' 篇）同步进 index.html');
