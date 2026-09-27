const fs = require('fs');
const path = require('path');
const ROOT = __dirname;
const INJECT = '<script src="/store.js"></script>';
const targets = ['学生端.html','教师端.html','index.html'];
fs.readdirSync(path.join(ROOT,'词汇诊断')).forEach(f => { if(f.endsWith('.html')) targets.push('词汇诊断/'+f); });
let injected = 0;
targets.forEach(rel => {
  const fp = path.join(ROOT, rel);
  if(!fs.existsSync(fp)){ console.log('skip(stat):', rel); return; }
  let s = fs.readFileSync(fp, 'utf8');
  if(s.includes(INJECT)){ console.log('  already:', rel); return; }
  const i = s.lastIndexOf('</body>');
  if(i < 0){ console.log('NOBODY:', rel); return; }
  s = s.slice(0,i) + INJECT + s.slice(i);
  fs.writeFileSync(fp, s);
  injected++;
  console.log('inject:', rel);
});
console.log('total injected:', injected);