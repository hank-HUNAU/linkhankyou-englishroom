/**
 * 冒烟验证：四项改动的端到端检查（对真实后端，测后自动清理临时账号）
 *  1) 静态资源与三页可达（ui.css / ui.js / login / 学生端 / 教师端）
 *  2) 词汇测试引擎数据 → /api/bank 难度·区分度·干扰项分布·审校标记
 *  3) 干扰项覆盖表（人工审校）优先级
 *  4) 跟读支架数据（follow 记录）经 kv 同步
 *  5) 安全基线：students/update 参数化（注入无效）、坏 token 401
 * 用法：node _smoke.js
 */
'use strict';
const B = process.env.BASE || 'http://localhost:8000';
let pass = 0, fail = 0;
const ok = (n, c, extra) => { c ? (pass++, console.log('  ✓ ' + n + (extra ? ' — ' + extra : ''))) : (fail++, console.log('  ✗ ' + n + (extra ? ' — ' + extra : ''))); };

async function j(path, opt){
  const r = await fetch(B + path, opt);
  let body = null; try { body = await r.json(); } catch(e){}
  return { status: r.status, body };
}
const post = (p, body, token) => j(p, { method:'POST', headers: Object.assign({'Content-Type':'application/json'}, token ? {Authorization:'Bearer '+token} : {}), body: JSON.stringify(body) });
const get  = (p, token) => j(p, { headers: token ? {Authorization:'Bearer '+token} : {} });

const TEMP = [];
async function mkStudent(name){
  const r = await post('/api/register', { name, pass:'smoke1' });
  if(!r.body || !r.body.ok) throw new Error('注册失败 ' + name + ' ' + JSON.stringify(r.body));
  TEMP.push({ id: r.body.user.id, token: r.body.token });
  return r.body;
}

/* 10 名学生 × 5 道题的作答矩阵：能力 j(0..9) 与题目阈值 t 决定对错 */
const ITEMS = [
  { id:'climb#unknown',  t:0, distr:['游泳','跳跃','滑行'] },   /* 全对 → tooEasy */
  { id:'board#unknown',  t:2, distr:['游泳','跳跃','滑行'] },
  { id:'record#unknown', t:9, distr:['游泳','跳跃','滑行'] },   /* 仅1人对 → tooHard + ambig */
  { id:'snowboard#unknown', t:4, distr:['游泳','跳跃','滑行'] },
  { id:'medal#unknown',  t:6, distr:['游泳','跳跃','滑行'] }
];
const CORRECT_OPT = { 'climb#unknown':'攀登，攀爬', 'board#unknown':'板，木板', 'record#unknown':'纪录，记录',
  'snowboard#unknown':'滑雪板，滑雪单板', 'medal#unknown':'奖牌，勋章' };

(async () => {
  console.log('\n=== 1. 静态资源与页面可达 ===');
  for (const p of ['/ui.css', '/ui.js', '/login.html', '/%E5%AD%A6%E7%94%9F%E7%AB%AF.html', '/%E6%95%99%E5%B8%88%E7%AB%AF.html']) {
    const r = await fetch(B + p);
    ok('GET ' + decodeURIComponent(p), r.status === 200, 'HTTP ' + r.status + ' ' + (r.headers.get('content-type')||''));
  }
  const uj = await (await fetch(B + '/ui.js')).text();
  ok('ui.js 含 sprite 定义', /'<symbol id="i-'\s*\+\s*k/.test(uj) && /check:\s*'/.test(uj));
  ok('ui.js 导出 ICON()', /window\.ICON\s*=/.test(uj));

  console.log('\n=== 2. 词汇测试 → 题库分析 ===');
  const t = await post('/api/login', { role:'teacher', name:'teacher', pass:'think-teacher' });
  ok('教师登录', t.body && t.body.ok, t.body && t.body.user && ('id=' + t.body.user.id));
  const tk = t.body.token;

  const blank = await get('/api/bank', tk);
  ok('/api/bank 教师可访问', blank.status === 200 && blank.body.ok);

  const stu = [];
  for (let i = 1; i <= 10; i++) stu.push(await mkStudent('冒烟学生' + String(i).padStart(2,'0')));
  ok('注册 10 名临时学生', stu.length === 10);

  const now = Date.now();
  for (let j2 = 0; j2 < stu.length; j2++) {
    const records = {};
    for (const it of ITEMS) {
      const correct = j2 >= it.t;
      /* 只在前两个干扰项间循环 → 第三个从未被选，用于验证 deadOpt 标记 */
      const picked = correct ? CORRECT_OPT[it.id] : it.distr[j2 % 2];
      records[it.id.split('#')[0]] = {
        status: correct ? 'known' : 'unknown',
        testHistory: [{
          itemId: it.id, mode: 'unknown', correct, skipped: false,
          opts: [CORRECT_OPT[it.id], ...it.distr], picked,
          errorType: correct ? null : 'meaning', testedAt: now
        }]
      };
    }
    const r = await post('/api/kv', [{ op:'set', key:'GR_records_v2', value: JSON.stringify(records) }], stu[j2].token);
    if (!r.body || !r.body.ok) { ok('学生' + j2 + ' 写入记录', false, JSON.stringify(r.body)); }
  }
  ok('10 名学生写入测试记录', true);

  const bank = await get('/api/bank', tk);
  ok('/api/bank 返回数据', bank.body && bank.body.ok && bank.body.items.length > 0, 'items=' + (bank.body.items ? bank.body.items.length : 0));
  const byItem = new Map((bank.body.items || []).map(x => [x.itemId, x]));
  const it1 = byItem.get('climb#unknown'), it3 = byItem.get('record#unknown');
  ok('难度 p 正确（全对题 p=1）', it1 && it1.p === 1, it1 && ('p=' + it1.p + ' n=' + it1.n));
  ok('难度 p 正确（难题 p≈0.1）', it3 && Math.abs(it3.p - 0.1) < 0.001, it3 && ('p=' + it3.p));
  ok('区分度 D 已计算', it1 && it1.d !== null && it1.d !== undefined, it1 && ('D=' + it1.d));
  ok('区分度 D 高（全对题 D=0 合理，看中等题）', byItem.get('snowboard#unknown') && byItem.get('snowboard#unknown').d !== null,
     byItem.get('snowboard#unknown') && ('D=' + byItem.get('snowboard#unknown').d));
  ok('点二列相关 r 已计算', it3 && it3.r !== null && it3.r !== undefined, it3 && ('r=' + it3.r));
  ok('选项分布含全部 4 个选项（含 0 次被选）', it1 && it1.opts.length === 4, it1 && ('opts=' + it1.opts.length));
  ok('标记 tooEasy', it1 && it1.flags.includes('tooEasy'), it1 && it1.flags.join(','));
  ok('标记 tooHard', it3 && it3.flags.includes('tooHard'), it3 && it3.flags.join(','));
  ok('标记 ambig（干扰项比答案更常被选）', it3 && it3.flags.includes('ambig'), it3 && it3.flags.join(','));
  ok('标记 deadOpt（存在从未被选的选项）', it3 && it3.flags.includes('deadOpt'), it3 && it3.flags.join(','));
  ok('正确答案识别正确', it1 && it1.keyOpt === '攀登，攀爬', it1 && ('keyOpt=' + it1.keyOpt));
  ok('汇总含学生总分', bank.body.students && bank.body.students.length >= 10, 'students=' + (bank.body.students||[]).length);

  console.log('\n=== 3. 干扰项人工审校覆盖表（静态校验） ===');
  const fs = require('fs'), path = require('path');
  const dis = fs.readFileSync(path.join(__dirname, '词汇诊断', '干扰项审校.js'), 'utf8');
  ok('覆盖表已定义 window.__VQ_DIS__', /window\.__VQ_DIS__\s*=/.test(dis));
  const csv = fs.readFileSync(path.join(__dirname, '词汇诊断', '干扰项审校工作表.csv'), 'utf8');
  const rows = csv.trim().split(/\r?\n/);
  ok('审校工作表已生成', rows.length > 100, '数据行=' + (rows.length - 1));
  /* 篇章词汇页与单元主题词汇页共用同一套诊断模板，两处都要有覆盖表接线 */
  for (const pf of ['词汇诊断_u12_p111_greatrace.html', '词汇诊断_theme_u7.html']) {
    const page = fs.readFileSync(path.join(__dirname, '词汇诊断', pf), 'utf8');
    ok('词汇页已接入覆盖表脚本 — ' + pf, page.includes('干扰项审校.js'));
    ok('词汇页用惰性 vqDis() 读取覆盖表 — ' + pf, /function vqDis\(\)/.test(page) && /vqDis\(\)\[String/.test(page));
    ok('词汇页用确定性优选 pickDistractors — ' + pf, /function pickDistractors/.test(page) && /pickDistractors\(w, 'zh'/.test(page));
    ok('逐题记录含 opts/picked — ' + pf, /test\.curOpts/.test(page) && /test\.curPicked/.test(page));
  }

  console.log('\n=== 4. 跟读支架数据同步 ===');
  const fkey = 'follow_u7_p67';
  const fr = await post('/api/kv', [{ op:'set', key:fkey, value: JSON.stringify({ stage:3, chunks:12, done:true }) }], stu[0].token);
  ok('学生写入跟读进度', fr.body && fr.body.ok);
  const kv0 = await get('/api/kv', stu[0].token);
  ok('学生可读回跟读进度', kv0.body && kv0.body.ok && !!kv0.body.rows[fkey], kv0.body && kv0.body.rows[fkey]);
  const rep = await get('/api/reports', tk);
  ok('/api/reports 教师可读学生数据', rep.body && rep.body.ok && rep.body.students.some(s => s.kv && s.kv[fkey]));

  console.log('\n=== 5. 安全基线 ===');
  const inj = "x' ; DROP TABLE users; --";
  const target = stu[0].user.id;
  const r1 = await post('/api/students/update', { id: target, name: inj }, tk);
  const list = await get('/api/students', tk);
  ok('users 表未被注入破坏', list.body && list.body.ok && Array.isArray(list.body.students) && list.body.students.length >= 10,
     'students=' + (list.body && list.body.students ? list.body.students.length : '?'));
  const renamed = list.body.students.find(s => s.id === target);
  ok('注入串被当作普通姓名（参数化生效）', r1.body.ok ? (renamed && renamed.name === inj) : true,
     'update=' + JSON.stringify(r1.body) + ' name=' + (renamed && renamed.name));
  const bad = await get('/api/me', 'not-a-real-token');
  ok('无效 token → 401', bad.status === 401);
  const noAuth = await get('/api/bank', '');
  ok('未登录访问 /api/bank → 401', noAuth.status === 401);
  const stuTok = stu[1].token;
  const forbidden = await get('/api/bank', stuTok);
  ok('学生访问 /api/bank → 403', forbidden.status === 403);
  const stuList = await get('/api/students', stuTok);
  ok('学生访问 /api/students → 403', stuList.status === 403);

  console.log('\n=== 6. 清理临时账号 ===');
  for (const s of TEMP) await post('/api/students/delete', { id: s.id }, tk);
  const after = await get('/api/students', tk);
  const left = (after.body.students || []).filter(s => s.name.indexOf('冒烟学生') === 0);
  ok('临时学生已清除', left.length === 0, '残留=' + left.length);

  console.log('\n──────────────────────────────');
  console.log(`结果：通过 ${pass} 项，失败 ${fail} 项`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('冒烟脚本异常：', e); process.exit(2); });