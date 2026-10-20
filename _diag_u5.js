'use strict';
const fs = require('fs');
const path = require('path');
const ROOT = __dirname;
const PAGE_DIR = path.join(ROOT, '篇章页');
const SUB_DIR = path.join(ROOT, 'assets', 'subtitles');

function parseSRT(text) {
  const cues = [];
  const raw = String(text).replace(/\r/g, '');
  const blocks = raw.split(/\n\s*\n/);
  const re = /(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/;
  for (const b of blocks) {
    const lines = b.split('\n');
    for (const l of lines) {
      const m = l.match(re);
      if (m) { cues.push([+m[1]*3600+ +m[2]*60+ +m[3]+ +m[4]/1000, +m[5]*3600+ +m[6]*60+ +m[7]+ +m[8]/1000]); break; }
    }
  }
  return cues;
}

// 抽取某页 BOOK[PG].arts 扁平句列表
function getArts(pageFile, pg) {
  const h = fs.readFileSync(path.join(PAGE_DIR, pageFile), 'utf8');
  const m = h.match(/var BOOK_EXTRA=(\{[\s\S]*?\});/);
  if (!m) return null;
  const be = JSON.parse(m[1]);
  const entry = be[String(pg)] || be[pg];
  if (!entry) return null;
  const arts = entry.arts || [];
  const flat = [];
  arts.forEach((para, pi) => para.forEach((s, si) => flat.push({ p: pi, t: s })));
  return { title: entry.title, nSeg: flat.length, paras: arts.length, flat };
}

const U5 = [
  { pg: 48, f: '读写_048_robotics_club.html' },
  { pg: 51, f: '读写_051_favourite_technology.html' },
  { pg: 52, f: '读写_052_tech_break.html' },
  { pg: 54, f: '读写_054_school_concert.html' },
];

for (const { pg, f } of U5) {
  const a = getArts(f, pg);
  const srt = parseSRT(fs.readFileSync(path.join(SUB_DIR, 'p' + String(pg).padStart(3,'0') + '.srt'), 'utf8'));
  console.log('\n========== p' + pg + ' (' + f + ') ==========');
  if (!a) { console.log('  !! 未找到 arts'); continue; }
  console.log('  文本句数(arts 扁平):', a.nSeg, '| 段落数:', a.paras, '| SRT 时间轴句数:', srt.length);
  console.log('  标题:', a.title);
  console.log('  --- 文本逐句 ---');
  a.flat.forEach((s, i) => console.log('   [' + i + '] ' + s.t));
  console.log('  --- SRT 时间轴 (start->end) ---');
  srt.forEach((c, i) => console.log('   [' + i + '] ' + c[0].toFixed(2) + ' -> ' + c[1].toFixed(2)));
}
