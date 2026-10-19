// 线上逐句音频全量核验（node spawn curl，避免 bash fork 问题）
const { execSync } = require('child_process');
const fs = require('fs');
const tl = JSON.parse(fs.readFileSync('assets/timeline.json', 'utf8'));
const pgs = Object.keys(tl).map(k => 'p' + k.slice(1).padStart(3, '0'));
let ok = 0; const bad = [];
for (const p of pgs) {
  let code = '000';
  try {
    code = execSync(`curl -s -o NUL -w "%{http_code}" --max-time 20 "https://hank-hunau.github.io/linkhankyou-englishroom/assets/${p}.mp3"`,
      { encoding: 'utf8', timeout: 30000 }).trim();
  } catch (e) { code = 'ERR'; }
  if (code === '200') ok++; else bad.push(p + '(' + code + ')');
  process.stdout.write(p + ':' + code + ' ');
}
console.log('\nRESULT: 线上逐句音频 200:', ok + '/25', '| 异常:', bad.join(',') || '无');
