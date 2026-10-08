#!/usr/bin/env node
// 单一数据源校验：index.html 内联的 DB.TL 必须与 assets/timeline.json 完全一致。
//
// 背景：这份时间轴曾经有"两代"——var DB 里的旧字面量，加若干运行时覆盖块；
// 实际生效的是后者，改前者不生效，而且真实播放值还与 assets/timeline.json 不一致。
// 现在只剩 index.html 里由 assets/timeline.json 生成的一段，本脚本负责盯住它别漂。
//
// 用法：node _timeline_check.js
'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = __dirname;

const START = '==TL-DATA-START==';
const END = '==TL-DATA-END==';

const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const tjPath = path.join(ROOT, 'assets', 'timeline.json');
if (!fs.existsSync(tjPath)) {
  console.log('FAIL  缺少 assets/timeline.json（它是句级时间轴的唯一权威源，须随仓库发布）');
  process.exit(1);
}
const tj = JSON.parse(fs.readFileSync(tjPath, 'utf8'));

const a = html.indexOf(START);
const b = html.indexOf(END);
if (a < 0 || b < 0 || b < a) {
  console.log('FAIL  index.html 里找不到 TL-DATA 标记块');
  process.exit(1);
}
const body = html.slice(a, b);
const m = /DB\.TL\s*=\s*(\{[\s\S]*?\});/.exec(body);
if (!m) {
  console.log('FAIL  TL-DATA 块里没有 DB.TL={...}; 赋值');
  process.exit(1);
}
let inline;
try {
  inline = JSON.parse(m[1]);
} catch (e) {
  console.log('FAIL  内联 DB.TL 不是合法 JSON：' + e.message);
  process.exit(1);
}

const num = s => String(parseInt(String(s).replace(/\D/g, ''), 10));
const kIn = Object.keys(inline).map(num).sort((x, y) => x - y);
const kTj = Object.keys(tj).map(num).sort((x, y) => x - y);
let bad = 0;
const problems = [];

if (kIn.join(',') !== kTj.join(',')) {
  problems.push('篇目不一致：index=' + kIn.join(',') + ' / timeline=' + kTj.join(','));
  bad++;
}

let sentTotal = 0;
for (const pid of kIn) {
  const src = tj['p' + String(pid).padStart(3, '0')] || tj['p' + pid];
  if (!src) { problems.push('timeline.json 缺少 p' + pid); bad++; continue; }
  const want = src.map(s => [s.start_s, s.end_s]);
  const have = inline[pid];
  if (want.length !== have.length) {
    problems.push('p' + pid + ' 条数 ' + have.length + ' 不等于 ' + want.length);
    bad++;
    continue;
  }
  sentTotal += want.length;
  for (let i = 0; i < want.length; i++) {
    if (Math.abs(want[i][0] - have[i][0]) > 1e-6 || Math.abs(want[i][1] - have[i][1]) > 1e-6) {
      problems.push('p' + pid + ' #' + i + ' 内联 [' + have[i] + '] 不等于 timeline [' + want[i] + ']');
      bad++;
    }
  }
}

for (const pid of kIn) {
  const arr = inline[pid];
  for (let i = 0; i < arr.length; i++) {
    if (!(arr[i][0] < arr[i][1])) { problems.push('p' + pid + ' #' + i + ' 起点不小于终点'); bad++; }
    if (i + 1 < arr.length && !(arr[i][1] <= arr[i + 1][0])) {
      problems.push('p' + pid + ' #' + i + ' 与下一句重叠'); bad++;
    }
  }
}

const extra = html.match(/DB\.TL\[/g);
if (extra) { problems.push('index.html 仍有 ' + extra.length + ' 处 DB.TL[...] 覆盖赋值'); bad++; }
if (/DB\.CHUNKS/.test(html)) { problems.push('index.html 仍残留 DB.CHUNKS'); bad++; }

if (bad === 0) {
  console.log('OK   时间轴单一数据源一致：' + kIn.length + ' 篇 / ' + sentTotal + ' 句');
} else {
  console.log('FAIL  单一数据源校验未通过：');
  problems.slice(0, 12).forEach(p => console.log('      - ' + p));
}
process.exit(bad ? 1 : 0);
