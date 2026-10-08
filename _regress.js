#!/usr/bin/env node
/**
 * TH!NK 一键回归入口
 *
 *   node _regress.js            全量回归（核心门禁 + 诊断脚本）
 *   node _regress.js --core     只跑核心门禁（断言型，无数据副作用）
 *   node _regress.js --no-server  不自动拉起服务器（默认会自动拉起）
 *   node _regress.js --list     只列出套件清单，不执行
 *
 * 判定规则：退出码为 0 且命中全部 mustMatch、未命中任何 forbid 才算通过。
 * 串行执行——脚本共用同一服务端与数据库，并行会互相污染。
 */
'use strict';
const { spawn, spawnSync } = require('child_process');
const http = require('http');
const https = require('https');
const path = require('path');

const ROOT = __dirname;
const PORT = 8000;
const BASE = `http://localhost:${PORT}`;
const TIMEOUT = 240000;

const argv = process.argv.slice(2);
const has = f => argv.includes(f);
const CORE_ONLY = has('--core');
const NO_SERVER = has('--no-server');
const LIST_ONLY = has('--list');

/* ── 套件清单 ─────────────────────────────────────────────
   kind: 'core' 断言型门禁 / 'diag' 诊断型（会写入演示数据）
   ──────────────────────────────────────────────────────── */
const SUITE = [
  {
    name: '语法检查（JS + HTML 内联脚本）',
    kind: 'core',
    run: 'node',
    args: ['_check.js', 'ui.js', 'store.js', 'server.js', 'index.html', '学生端.html', '教师端.html', 'login.html'],
    forbid: [/^FAIL/m],
    mustMatch: [/^OK {3}/m]
  },
  {
    name: '视觉对齐校验（设计令牌）',
    kind: 'core',
    run: 'node',
    args: ['_align_check.js'],
    mustMatch: [/结果：✓ 全部通过/]
  },
  {
    name: '图标引用校验（SVG sprite）',
    kind: 'core',
    run: 'node',
    args: ['_check_icons.js'],
    mustMatch: [/结果：✓ 全部图标引用有效/]
  },
  {
    name: '时间轴单一数据源（index.html ↔ assets/timeline.json）',
    kind: 'core',
    run: 'node',
    args: ['_timeline_check.js'],
    mustMatch: [/^OK {3}时间轴单一数据源一致/],
    forbid: [/^FAIL/m]
  },
  {
    name: 'API 层冒烟（账号/存储/聚合）',
    kind: 'core',
    run: 'node',
    args: ['_smoke.js'],
    mustMatch: [/结果：通过 \d+ 项，失败 0 项/]
  },
  {
    name: '跟读支架化（跟句→影子，意群已下线）',
    kind: 'core',
    run: 'python',
    args: ['_smoke_follow_stage.py'],
    mustMatch: [/结果：\d+ 通过 \/ 0 失败/]
  },
  {
    name: '题库分析闭环（难度/区分度/待审校）',
    kind: 'core',
    run: 'python',
    args: ['_smoke_bank_ui.py'],
    mustMatch: [/结果：\d+ 通过 \/ 0 失败/, /\[4\] 已清理 \d+ 名临时学生/]
  },
  {
    name: '预习→复习衔接引导',
    kind: 'diag',
    run: 'python',
    args: ['_smoke_bridge.py'],
    mustMatch: [/CTA点击: (guide-cta-clicked|bridge-cta-clicked)/],
    forbid: [/JS错误: \[[^\]]/]
  },
  {
    name: '花名册 / 班级 / 学情 / 助教只读',
    kind: 'diag',
    run: 'python',
    args: ['_smoke_roster.py'],
    mustMatch: [
      /\[1\] 教师登录: ok/,
      /\[3\] 建班后含 冒烟测试班: True/,
      /\[4\] 学生表含 测试学生X: True/,
      /\[7\] 助教只读：新增学生按钮禁用=True/
    ],
    forbid: [/教师端 JS错误: \[[^\]]/]
  },
  {
    name: '学生端沉浸式任务区渲染',
    kind: 'diag',
    run: 'python',
    args: ['_smoke_immerse.py'],
    mustMatch: [/\[1\] 沉浸式渲染: .*"hero":true/, /\[1\] 沉浸式渲染: .*"ring":true/, /\[2\] 点击任务行: clicked/],
    forbid: [/JS错误: \[[^\]]/]
  },
  {
    name: '跨设备同步（教师下发 → 学生端只读拉取）',
    kind: 'diag',
    run: 'python',
    args: ['_smoke_multi.py'],
    mustMatch: [
      /\[2\] 服务器端 tf_assignments\(全局\) 是否已含 p67\+主题: [Tt]rue/,
      /\[3\] 学生端本地姓名: 张小美/,
      /\[3\.5\] 学生端拉取检查: .*"server_has_assign":true/,
      /\[4\] 学生端看到教师下发的任务\+截止: [Tt]rue/
    ]
  }
];

const tasks = CORE_ONLY ? SUITE.filter(t => t.kind === 'core') : SUITE;

/* ── 工具 ─────────────────────────────────────────────── */
const C = {
  d: s => `\x1b[2m${s}\x1b[0m`,
  b: s => `\x1b[1m${s}\x1b[0m`,
  g: s => `\x1b[32m${s}\x1b[0m`,
  r: s => `\x1b[31m${s}\x1b[0m`,
  y: s => `\x1b[33m${s}\x1b[0m`
};
const stamp = () => new Date().toTimeString().slice(0, 8);
const secs = ms => (ms / 1000).toFixed(1) + 's';
const tail = (s, n) => s.trimEnd().split('\n').slice(-n).join('\n');

function resolvePython() {
  for (const [cmd, pre] of [['python', []], ['py', ['-3']]]) {
    const r = spawnSync(cmd, [...pre, '--version'], { encoding: 'utf8' });
    if (!r.error && r.status === 0) return { cmd, pre };
  }
  return null;
}

function probe(proto) {
  return new Promise(resolve => {
    const lib = proto === 'https' ? https : http;
    const req = lib.get({ host: 'localhost', port: PORT, path: '/login.html', rejectUnauthorized: false }, res => {
      res.resume();
      resolve(res.statusCode >= 200 && res.statusCode < 500);
    });
    req.setTimeout(1500, () => { req.destroy(); resolve(false); });
    req.on('error', () => resolve(false));
  });
}

async function waitReady(limitMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < limitMs) {
    if (await probe('http')) return true;
    await new Promise(r => setTimeout(r, 400));
  }
  return false;
}

async function ensureServer() {
  if (await probe('http')) return { proto: 'http', owned: null, note: '复用已运行实例' };
  if (await probe('https')) return { proto: 'https', owned: null, note: '已运行实例仅 HTTPS —— 脚本以 http 为基准，将失败' };
  if (NO_SERVER) return { proto: null, owned: null, note: '--no-server 且无实例在监听' };

  console.log(C.y(`未检测到 ${BASE} 上的服务，正在自动启动（node server.js --http）…`));
  const child = spawn('node', ['server.js', '--http'], { cwd: ROOT, stdio: 'ignore', windowsHide: true });
  const ok = await waitReady(20000);
  if (!ok) { try { child.kill(); } catch {} return { proto: null, owned: null, note: '自动启动超时（20s）' }; }
  return { proto: 'http', owned: child, note: '本次自动启动' };
}

/* ── 单脚本执行 ───────────────────────────────────────── */
function runTask(task, py) {
  let cmd, args;
  if (task.run === 'python') {
    if (!py) return { status: 'skip', ms: 0, out: '', why: '未检测到 python' };
    cmd = py.cmd; args = [...py.pre, ...task.args];
  } else {
    cmd = 'node'; args = task.args;
  }

  const t0 = Date.now();
  const r = spawnSync(cmd, args, {
    cwd: ROOT,
    encoding: 'utf8',
    timeout: TIMEOUT,
    maxBuffer: 32 * 1024 * 1024,
    windowsHide: true,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });
  const ms = Date.now() - t0;
  const out = `${r.stdout || ''}${r.stderr || ''}`;

  if (r.error && r.error.code === 'ENOENT') return { status: 'skip', ms, out, why: `找不到 ${cmd}` };
  if (r.error && r.error.code === 'ETIMEDOUT') return { status: 'fail', ms, out, why: `超时 ${TIMEOUT / 1000}s` };

  const reasons = [];
  if (r.status !== 0) reasons.push(`退出码 ${r.status}`);
  for (const re of task.mustMatch || []) if (!re.test(out)) reasons.push(`缺少断言 ${re}`);
  for (const re of task.forbid || []) if (re.test(out)) reasons.push(`命中禁止项 ${re}`);

  return { status: reasons.length ? 'fail' : 'pass', ms, out, why: reasons.join('；') };
}

/* ── 主流程 ───────────────────────────────────────────── */
(async () => {
  if (LIST_ONLY) {
    console.log(C.b(`\n套件清单（${tasks.length} 项，${CORE_ONLY ? '仅核心' : '全量'}）\n`));
    tasks.forEach((t, i) => console.log(`  ${String(i + 1).padStart(2)}. [${t.kind}] ${t.name}  ${C.d(t.run + ' ' + t.args.join(' '))}`));
    console.log('');
    return;
  }

  const srv = await ensureServer();
  const py = resolvePython();

  console.log('');
  console.log(C.b('═'.repeat(74)));
  console.log(C.b(`  TH!NK 一键回归 · ${new Date().toLocaleString('zh-CN')}`));
  console.log(`  服务器   ${BASE}  ${C.d(srv.note)}`);
  console.log(`  套件     ${tasks.length} 项（${CORE_ONLY ? '仅核心门禁' : '全量：核心 + 诊断'}）`);
  console.log(`  运行环境 node ${process.version} · ${py ? py.cmd : 'python 缺失'}`);
  console.log(C.b('═'.repeat(74)));

  const results = [];
  for (let i = 0; i < tasks.length; i++) {
    const t = tasks[i];
    console.log('');
    console.log(C.b(`▶ [${i + 1}/${tasks.length}] ${t.name}`));
    console.log(C.d(`  $ ${t.run === 'python' ? (py ? py.cmd + ' ' : '') : ''}${t.args.join(' ')}`));

    const res = runTask(t, py);
    res.name = t.name;
    results.push(res);

    if (res.status === 'pass') {
      const key = (t.mustMatch || []).map(re => (res.out.match(re) || [''])[0]).filter(Boolean).pop();
      console.log(C.g(`  ✓ 通过`) + C.d(`  ${secs(res.ms)}`) + (key ? C.d(`  · ${key.trim().slice(0, 60)}`) : ''));
    } else if (res.status === 'skip') {
      console.log(C.y(`  ⏭ 跳过`) + C.d(`  ${res.why}`));
    } else {
      console.log(C.r(`  ✗ 失败`) + C.d(`  ${secs(res.ms)}`) + `  ${res.why}`);
      console.log(C.d('  ── 末尾输出 ──'));
      console.log(tail(res.out, 22).split('\n').map(l => '  ' + l).join('\n'));
    }
  }

  const pass = results.filter(r => r.status === 'pass').length;
  const fail = results.filter(r => r.status === 'fail').length;
  const skip = results.filter(r => r.status === 'skip').length;
  const total = results.reduce((s, r) => s + r.ms, 0);

  console.log('');
  console.log(C.b('─'.repeat(74)));
  console.log(C.b('  结果汇总'));
  results.forEach(r => {
    const mark = r.status === 'pass' ? C.g('✓') : r.status === 'skip' ? C.y('⏭') : C.r('✗');
    console.log(`  ${mark} ${r.name.padEnd(34, ' ')} ${C.d(secs(r.ms).padStart(7))}${r.status === 'fail' ? C.r('  ' + r.why.slice(0, 40)) : ''}`);
  });
  console.log(C.b('─'.repeat(74)));
  console.log(`  通过 ${pass} · 失败 ${fail} · 跳过 ${skip} · 总耗时 ${secs(total)}`);

  if (fail === 0) {
    console.log(C.g(C.b('  ✓ 回归通过')) + (skip ? C.d('（有跳过项）') : ''));
  } else {
    console.log(C.r(C.b(`  ✗ 回归未通过：${results.filter(r => r.status === 'fail').map(r => r.name).join('、')}`)));
    console.log(C.d('    排查顺序：先看失败脚本末尾输出 → 单独重跑该脚本 → 再整轮回归'));
  }

  if (srv.owned) {
    console.log(C.d(`\n  关闭本次自动启动的服务器（pid ${srv.owned.pid}）`));
    try { srv.owned.kill(); } catch {}
  }
  console.log('');
  process.exit(fail ? 1 : 0);
})();
