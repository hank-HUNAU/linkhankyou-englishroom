#!/usr/bin/env node
/**
 * TH!NK · 多设备/账号后端（零依赖）
 * 内建 http + node:sqlite。用法：node server.js   →  http://localhost:8000
 */
'use strict';
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');
const { DatabaseSync } = require('node:sqlite');

const ROOT = __dirname;
const DBFILE = path.join(ROOT, 'think.db');
const PORT = process.env.PORT || 8000;

/* ── HTTPS：certs/ 下有证书则自动启用；--http 强制回退 ── */
const CERT_KEY = path.join(ROOT, 'certs', 'key.pem');
const CERT_CRT = path.join(ROOT, 'certs', 'cert.pem');
const FORCE_HTTP = process.argv.includes('--http');
const USE_TLS = !FORCE_HTTP && fs.existsSync(CERT_KEY) && fs.existsSync(CERT_CRT);

/* ── 令牌有效期：默认 7 天，滑动续期 ── */
const TOKEN_TTL = (+process.env.TOKEN_TTL_MS) || 7 * 24 * 3600 * 1000;
const TOKEN_RENEW_AT = TOKEN_TTL / 2;   /* 剩余不足一半时续期，避免每请求写库 */

/* ── 定时备份：VACUUM INTO 原子快照，保留最近 N 份 ── */
const BK_DIR = path.join(ROOT, 'backups');
const BK_KEEP = 14;
const BK_EVERY = 6 * 3600 * 1000;

/* ───────────── SQLite ───────────── */
const db = new DatabaseSync(DBFILE);
db.exec('PRAGMA journal_mode=WAL');
db.exec(`CREATE TABLE IF NOT EXISTS users(
  id    INTEGER PRIMARY KEY AUTOINCREMENT,
  role  TEXT NOT NULL,
  name  TEXT NOT NULL UNIQUE,
  salt  TEXT NOT NULL,
  hash  TEXT NOT NULL,
  token TEXT
)`);
db.exec(`CREATE TABLE IF NOT EXISTS classes(
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT NOT NULL UNIQUE,
  teacher_id INTEGER
)`);
db.exec(`CREATE TABLE IF NOT EXISTS kv(
  uid  INTEGER NOT NULL,        /* -1 = 全局(任务) */
  key  TEXT    NOT NULL,
  val  TEXT    NOT NULL,
  PRIMARY KEY(uid,key)
)`);
/* 迁移：为已有 users 表补充 class_id / token_exp 列 */
(function(){
  const cols = db.prepare('PRAGMA table_info(users)').all().map(c => c.name);
  if(!cols.includes('class_id')) db.exec('ALTER TABLE users ADD COLUMN class_id INTEGER');
  if(!cols.includes('token_exp')) db.exec('ALTER TABLE users ADD COLUMN token_exp INTEGER');
})();

/* ───────────── 密码/口令 ───────────── */
function hashPass(pass, salt){
  return crypto.scryptSync(String(pass), salt, 64).toString('hex');
}
function newToken(){ return crypto.randomBytes(24).toString('hex'); }

/* 种子账号 */
function seed(){
  const n = db.prepare('SELECT COUNT(*) c FROM users').get().c;
  if(n) return;
  const mk = (role, name, pass) => {
    const salt = crypto.randomBytes(8).toString('hex');
    db.prepare('INSERT INTO users(role,name,salt,hash) VALUES(?,?,?,?)').run(role, name, salt, hashPass(pass, salt));
  };
  mk('teacher', 'teacher', 'think-teacher');
  mk('assistant', '助教', 'think-assist');
  mk('student', '学生01', '1234');
  mk('student', '学生02', '1234');
  mk('student', '张小美', '1234');
}
seed();
/* 幂等补齐：助教账号 + 班级 + 种子学生分班 */
function ensureSeed(){
  if(!db.prepare("SELECT id FROM users WHERE role='assistant' AND name='助教'").get()){
    const s=crypto.randomBytes(8).toString('hex');
    db.prepare("INSERT INTO users(role,name,salt,hash) VALUES('assistant','助教',?,?)").run(s, hashPass('think-assist', s));
  }
  const tid = db.prepare("SELECT id FROM users WHERE role='teacher'").get()?.id;
  ['秋季一班','秋季二班'].forEach(cn=>{
    if(!db.prepare('SELECT id FROM classes WHERE name=?').get(cn)){
      db.prepare('INSERT INTO classes(name,teacher_id) VALUES(?,?)').run(cn, tid);
    }
  });
  const c1 = db.prepare("SELECT id FROM classes WHERE name='秋季一班'").get();
  if(c1){
    db.prepare('UPDATE users SET class_id=? WHERE role=? AND name=? AND class_id IS NULL').run(c1.id,'student','学生01');
    db.prepare('UPDATE users SET class_id=? WHERE role=? AND name=? AND class_id IS NULL').run(c1.id,'student','学生02');
  }
}
ensureSeed();

/* ───────────── 备份 ───────────── */
function backup(){
  try{
    fs.mkdirSync(BK_DIR, { recursive: true });
    const d = new Date();
    const p2 = n => String(n).padStart(2, '0');
    const ts = `${d.getFullYear()}${p2(d.getMonth()+1)}${p2(d.getDate())}-${p2(d.getHours())}${p2(d.getMinutes())}${p2(d.getSeconds())}`;
    const fp = path.join(BK_DIR, `think-${ts}.db`);
    db.exec(`VACUUM INTO '${fp.replace(/'/g, "''")}'`);
    const files = fs.readdirSync(BK_DIR).filter(f => /^think-\d{8}-\d{6}\.db$/.test(f)).sort();
    while(files.length > BK_KEEP) fs.unlinkSync(path.join(BK_DIR, files.shift()));
    console.log('[backup]', path.basename(fp));
  }catch(e){
    console.error('[backup] 失败:', e.message);
  }
}
backup();
setInterval(backup, BK_EVERY).unref();

/* ───────────── 请求工具 ───────────── */
function parseBody(req){
  return new Promise((res, rej) => {
    let b = '';
    req.on('data', c => { b += c; if(b.length > 2e6){ req.destroy(); rej(new Error('too large')); } });
    req.on('end', () => { try{ res(b ? JSON.parse(b) : {}); }catch(e){ rej(e); } });
    req.on('error', rej);
  });
}
const MIME = {
  '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8',
  '.json':'application/json', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg',
  '.gif':'image/gif', '.svg':'image/svg+xml', '.ico':'image/x-icon', '.mp3':'audio/mpeg',
  '.woff2':'font/woff2', '.webp':'image/webp', '.pdf':'application/pdf'
};
function send(res, code, body, mime){ res.writeHead(code, { 'Content-Type': mime || 'application/json; charset=utf-8' }); res.end(typeof body==='string' ? body : JSON.stringify(body)); }
function sendErr(res, code, msg){ send(res, code, { ok:false, error:msg }); }

/* 静态文件（防目录穿越） */
function serveStatic(req, res, urlPath){
  let p = decodeURIComponent(urlPath.split('?')[0]);
  if(p === '/' ) p = 'index.html';
  const fp = path.normalize(path.join(ROOT, p));
  if(!fp.startsWith(ROOT + path.sep) && fp !== ROOT){
    return sendErr(res, 403, 'forbidden');
  }
  fs.stat(fp, (err, st) => {
    if(err || !st.isFile()) return send(res, 404, 'Not Found', 'text/plain; charset=utf-8');
    const mime = MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': mime, 'Cache-Control': 'no-cache' });
    fs.createReadStream(fp).pipe(res);
  });
}

/* 鉴权：校验令牌 + 有效期（滑动续期） */
function userByToken(tok){
  if(!tok) return null;
  const u = db.prepare('SELECT * FROM users WHERE token=?').get(tok);
  if(!u) return null;
  /* 过期（或历史遗留的无期限令牌）一律作废，需重新登录 */
  if(!u.token_exp || u.token_exp <= Date.now()){
    db.prepare('UPDATE users SET token=NULL, token_exp=NULL WHERE id=?').run(u.id);
    return null;
  }
  if(u.token_exp - Date.now() < TOKEN_RENEW_AT){
    const exp = Date.now() + TOKEN_TTL;
    db.prepare('UPDATE users SET token_exp=? WHERE id=?').run(exp, u.id);
    u.token_exp = exp;
  }
  return u;
}
function authUser(req){
  const h = req.headers.authorization || '';
  if(!/^Bearer /.test(h)) return null;
  return userByToken(h.slice(7).trim());
}
const only = role => user => user && (role==='teacher' ? user.role==='teacher' : user.role===role);
const isTeacher = only('teacher');
const isStaff = user => user && (user.role==='teacher' || user.role==='assistant');
const pubUser = u => ({ id:u.id, role:u.role, name:u.name, classId: u.class_id ?? null });

/* ───────────── 事件推送（SSE，零依赖） ─────────────
   方向一：教师下发/改动任务 → 全体在线学生端秒级更新（event: assignment）
   方向二：学生产生学情写入   → 在线教师/助教刷新学情（event: progress，限流 3s）
   心跳 20s 防中间层断连；断线由浏览器自动重连，重连即刻对齐一次任务。 */
const sseClients = new Set();          /* { res, uid, staff } */
const SSE_HEARTBEAT_MS = 20000;
const PROGRESS_MIN_GAP_MS = 3000;
let lastProgressPush = 0;

function sseSend(c, event, data){
  try{ c.res.write('event: ' + event + '\ndata: ' + JSON.stringify(data) + '\n\n'); }catch(e){}
}
function sseBroadcast(event, data, filter){
  for(const c of sseClients) if(!filter || filter(c)) sseSend(c, event, data);
}
function currentAssignments(){
  const r = db.prepare('SELECT val FROM kv WHERE uid=-1 AND key=?').get('tf_assignments');
  return r ? r.val : '';
}
function pushAssignments(){
  sseBroadcast('assignment', { value: currentAssignments() });
}
function pushProgress(user){
  const now = Date.now();
  if(now - lastProgressPush < PROGRESS_MIN_GAP_MS) return;
  lastProgressPush = now;
  sseBroadcast('progress', { uid:user.id, name:user.name }, c => c.staff);
}

/* ───────────── API 路由 ───────────── */
const routes = {
  async ['POST /api/login'](req, res){
    const b = await parseBody(req);
    const u = db.prepare('SELECT * FROM users WHERE role=? AND name=?').get(b.role, String(b.name||''));
    if(!u || u.hash !== hashPass(b.pass||'', u.salt)) return sendErr(res, 401, '账号或口令不正确');
    const tok = newToken();
    db.prepare('UPDATE users SET token=?, token_exp=? WHERE id=?').run(tok, Date.now()+TOKEN_TTL, u.id);
    send(res, 200, { ok:true, user:pubUser(u), token:tok, expiresIn: TOKEN_TTL });
  },
  async ['POST /api/register'](req, res){
    const b = await parseBody(req);
    const name = String(b.name||'').trim(), pass = String(b.pass||'');
    if(!name || pass.length < 4) return sendErr(res, 400, '姓名与口令（至少4位）必填');
    const dup = db.prepare('SELECT id FROM users WHERE name=?').get(name);
    if(dup) return sendErr(res, 409, '该姓名已被注册');
    const salt = crypto.randomBytes(8).toString('hex');
    const tok = newToken();
    db.prepare('INSERT INTO users(role,name,salt,hash,token,token_exp) VALUES(?,?,?,?,?,?)')
      .run('student', name, salt, hashPass(pass, salt), tok, Date.now()+TOKEN_TTL);
    const u = db.prepare('SELECT * FROM users WHERE name=?').get(name);
    send(res, 200, { ok:true, user:pubUser(u), token:u.token, expiresIn: TOKEN_TTL });
  },
  async ['GET /api/me'](req, res){
    const u = authUser(req);
    if(!u) return sendErr(res, 401, '未登录');
    send(res, 200, { ok:true, user:pubUser(u) });
  },
  async ['POST /api/logout'](req, res){
    const u = authUser(req);
    if(u) db.prepare('UPDATE users SET token=NULL, token_exp=NULL WHERE id=?').run(u.id);
    send(res, 200, { ok:true });
  },
  /* 返回：全局行 + 本人行 合并（uid=-1 全局 + uid=u.id） */
  async ['GET /api/kv'](req, res){
    const u = authUser(req);
    if(!u) return sendErr(res, 401, '未登录');
    const rows = db.prepare('SELECT key,val FROM kv WHERE uid IN (-1, ?) ORDER BY uid DESC').all(u.id);
    const kv = {}; rows.forEach(r => kv[r.key] = r.val);
    send(res, 200, { ok:true, rows: kv });
  },
  /* SSE 事件流。EventSource 无法自定义请求头，故同时允许 ?token= 传令牌 */
  async ['GET /api/events'](req, res){
    const m = /[?&]token=([^&]+)/.exec(req.url || '');
    const u = authUser(req) || (m ? userByToken(decodeURIComponent(m[1])) : null);
    if(!u) return sendErr(res, 401, '未登录');

    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache, no-transform',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no'
    });
    req.socket.setTimeout(0);          /* 长连接不参与空闲超时 */
    req.socket.setNoDelay(true);
    if(typeof res.flushHeaders === 'function') res.flushHeaders();

    const client = { res, uid: u.id, staff: isStaff(u) };
    sseClients.add(client);
    /* 建连即对齐，补上断线期间漏掉的变更 */
    sseSend(client, 'assignment', { value: currentAssignments() });

    const hb = setInterval(function(){ try{ res.write(': ping\n\n'); }catch(e){} }, SSE_HEARTBEAT_MS);
    let done = false;
    const bye = function(){
      if(done) return;
      done = true;
      clearInterval(hb);
      sseClients.delete(client);
      try{ res.end(); }catch(e){}
    };
    req.on('close', bye);
    req.on('error', bye);
    res.on('close', bye);
  },
  /* 轻量轮询专用：只返回教师下发的全局任务，避免每次拉回全部 KV */
  async ['GET /api/assignments'](req, res){
    const u = authUser(req);
    if(!u) return sendErr(res, 401, '未登录');
    const r = db.prepare('SELECT val FROM kv WHERE uid=-1 AND key=?').get('tf_assignments');
    send(res, 200, { ok:true, value: r ? r.val : '' });
  },
  /* 批量写入/删除：body = [{op:'set'|'del', key, value?, scope?}]  scope:'global' 仅限教师 */
  async ['POST /api/kv'](req, res){
    const u = authUser(req);
    if(!u) return sendErr(res, 401, '未登录');
    const batch = await parseBody(req);
    const arr = Array.isArray(batch) ? batch : [batch];
    const ins = db.prepare('INSERT INTO kv(uid,key,val) VALUES(?,?,?) ON CONFLICT(uid,key) DO UPDATE SET val=excluded.val');
    const del = db.prepare('DELETE FROM kv WHERE uid=? AND key=?');
    const prevAssign = db.prepare('SELECT val FROM kv WHERE uid=-1 AND key=?').get('tf_assignments');
    db.exec('BEGIN');
    let touchAssign = false, touchProgress = false;
    try{
      arr.forEach(it => {
        let uid = u.id;
        if(it.scope === 'global'){
          if(!isStaff(u)) return;
          uid = -1;
        }
        const k = String(it.key);
        if(uid === -1){ if(k === 'tf_assignments') touchAssign = true; }
        else if(/_records_v2$/.test(k) || k === 'tf_reports' || /^tf_follow_/.test(k)) touchProgress = true;
        if(it.op === 'del') del.run(uid, k);
        else ins.run(uid, k, it.value===undefined ? '' : String(it.value));
      });
      db.exec('COMMIT');
    }catch(e){ db.exec('ROLLBACK'); return sendErr(res, 500, '存储失败'); }
    /* 推送放在 COMMIT 之后、读库取最新值；值没变就不推，避免客户端回传同值时造成广播噪音 */
    if(touchAssign && currentAssignments() !== (prevAssign ? prevAssign.val : '')) pushAssignments();
    if(touchProgress) pushProgress(u);
    send(res, 200, { ok:true, n:arr.length });
  },
  /* 教师聚合：返回全部学生本人 KV（含 tf_reports / *_records_v2 / tf_follow_*） */
  async ['GET /api/reports'](req, res){
    const u = authUser(req);
    if(!u) return sendErr(res, 401, '未登录');
    if(!isStaff(u)) return sendErr(res, 403, '仅教师/助教可查看学情');
    const students = db.prepare("SELECT id,name,class_id AS classId FROM users WHERE role='student' AND id IN (SELECT DISTINCT uid FROM kv WHERE uid<>-1)").all();
    const rows = db.prepare('SELECT uid,key,val FROM kv WHERE uid<>-1 ORDER BY uid').all();
    const byUid = new Map();
    rows.forEach(r => { if(!byUid.has(r.uid)) byUid.set(r.uid, {}); byUid.get(r.uid)[r.key] = r.val; });
    const clsMap = new Map(db.prepare('SELECT id,name FROM classes').all().map(c => [c.id, c.name]));
    send(res, 200, { ok:true, classes:[...clsMap.entries()].map(([id,name])=>({id,name})), students: students.map(s => ({ uid:s.id, name:s.name, classId:s.classId, className: s.classId!=null ? (clsMap.get(s.classId)||'') : '' , kv: byUid.get(s.id) || {} })) });
  },
  /* 题库分析：聚合全体学生「测试引擎」逐题作答 → 难度 p / 区分度 D·r / 干扰项分布 / 待审校标记 */
  async ['GET /api/bank'](req, res){
    const u = authUser(req);
    if(!u) return sendErr(res, 401, '未登录');
    if(!isStaff(u)) return sendErr(res, 403, '仅教师/助教可查看题库分析');
    /* 注意：SQLite 的 LIKE 里 '_' 是单字符通配符，必须 ESCAPE 才按字面匹配 */
    const rows = db.prepare("SELECT uid,key,val FROM kv WHERE uid<>-1 AND key LIKE '%!_records!_v2' ESCAPE '!'").all()
      .filter(r => String(r.key).endsWith('_records_v2'));
    const names = new Map(db.prepare("SELECT id,name FROM users WHERE role='student'").all().map(s => [s.id, s.name]));
    const score = new Map();   /* uid → 测试作答总数/正确数（区分度的总分基准） */
    const items = new Map();   /* page|itemId|mode → 聚合体 */
    for(const r of rows){
      let obj; try{ obj = JSON.parse(r.val); }catch(e){ continue; }
      if(!obj || typeof obj !== 'object') continue;
      const page = String(r.key).slice(0, -'_records_v2'.length);
      for(const k of Object.keys(obj)){
        const rec = obj[k]; if(!rec || !Array.isArray(rec.testHistory)) continue;
        for(const h of rec.testHistory){
          /* 只统计测试引擎的题（带 itemId）；跳过/不确定不计入难度 */
          if(!h || !h.itemId || h.skipped) continue;
          const ok = !!h.correct, mode = h.mode || 'unknown';
          const sc = score.get(r.uid) || { n:0, ok:0 };
          sc.n++; if(ok) sc.ok++; score.set(r.uid, sc);
          const id = page + '|' + h.itemId + '|' + mode;
          let it = items.get(id);
          if(!it){
            it = { page, itemId: h.itemId, en: String(h.itemId).split('#')[0], mode, n:0, ok:0, rows:[], picks:new Map(), allOpts:new Set(), last:0 };
            items.set(id, it);
          }
          it.n++; if(ok) it.ok++;
          it.rows.push([r.uid, ok ? 1 : 0]);
          if(h.testedAt > it.last) it.last = h.testedAt;
          /* 记录该题出现过的全部选项（含从未被选的），否则「无效干扰项」无法识别 */
          if(Array.isArray(h.opts)) h.opts.forEach(v => { if(v != null && v !== '') it.allOpts.add(String(v)); });
          if(h.picked != null && h.picked !== ''){
            const pv = it.picks.get(String(h.picked)) || { pick:0, ok:0 };
            pv.pick++; if(ok) pv.ok++; it.picks.set(String(h.picked), pv);
          }
        }
      }
    }
    /* 区分度基准：学生测试总分 */
    const uids = [...score.keys()];
    const tot = uids.map(id => score.get(id).ok);
    const mean = tot.length ? tot.reduce((a, b) => a + b, 0) / tot.length : 0;
    const sd = tot.length ? Math.sqrt(tot.reduce((a, b) => a + (b - mean) * (b - mean), 0) / tot.length) : 0;
    const sorted = uids.slice().sort((a, b) => score.get(b).ok - score.get(a).ok);
    const cut = Math.max(1, Math.round(sorted.length * 0.27));
    const hi = new Set(sorted.slice(0, cut)), lo = new Set(sorted.slice(-cut));
    const list = [];
    for(const it of items.values()){
      const p = it.n ? it.ok / it.n : 0;
      /* 点二列相关 r：题目对错 与 学生总分 的相关 */
      let r = null;
      if(it.rows.length >= 4 && sd > 0){
        const o1 = it.rows.filter(x => x[1] === 1), o0 = it.rows.filter(x => x[1] === 0);
        if(o1.length && o0.length){
          const m1 = o1.reduce((a, x) => a + score.get(x[0]).ok, 0) / o1.length;
          const m0 = o0.reduce((a, x) => a + score.get(x[0]).ok, 0) / o0.length;
          r = Math.round((m1 - m0) / sd * Math.sqrt(p * (1 - p)) * 1000) / 1000;
        }
      }
      /* 高低分组 D（上下各 27%） */
      let d = null;
      if(sorted.length >= 6){
        let hn = 0, hc = 0, ln = 0, lc = 0;
        it.rows.forEach(x => { if(hi.has(x[0])){ hn++; hc += x[1]; } if(lo.has(x[0])){ ln++; lc += x[1]; } });
        if(hn && ln) d = Math.round((hc / hn - lc / ln) * 1000) / 1000;
      }
      /* 干扰项分布：优先用「出现过的全部选项」（含 0 次被选），否则退回实际被选集合 */
      const opts = (it.allOpts.size
        ? [...it.allOpts].map(v => { const c = it.picks.get(v) || { pick:0, ok:0 }; return { v, pick:c.pick, ok:c.ok }; })
        : [...it.picks.entries()].map(([v, c]) => ({ v, pick:c.pick, ok:c.ok }))
      ).sort((a, b) => b.pick - a.pick);
      let keyOpt = null, maxOk = 0;
      opts.forEach(o => { if(o.ok > maxOk){ maxOk = o.ok; keyOpt = o.v; } });
      const distr = opts.filter(o => o.v !== keyOpt);
      const flags = [];
      if(keyOpt && it.n >= 8){
        if(distr.length && distr[0].pick > it.ok) flags.push('ambig');        /* 某干扰项比答案更常被选 → 疑似歧义或答案错位 */
        if(distr.some(o => o.pick === 0)) flags.push('deadOpt');              /* 从未被选的干扰项 → 无效选项 */
      }
      if(it.n < 8) flags.push('thin');
      if(it.n >= 8 && p >= 0.95) flags.push('tooEasy');
      if(it.n >= 8 && p <= 0.25) flags.push('tooHard');
      if(it.n >= 8 && d !== null && d < 0.2) flags.push('lowD');
      list.push({ page:it.page, itemId:it.itemId, en:it.en, mode:it.mode, n:it.n, ok:it.ok,
        p: Math.round(p * 1000) / 1000, d, r, keyOpt, opts: opts.slice(0, 8), flags, last: it.last });
    }
    list.sort((a, b) => a.page.localeCompare(b.page) || a.en.localeCompare(b.en) || a.mode.localeCompare(b.mode));
    const students = [...score.entries()].map(([id, v]) => ({ uid:id, name:names.get(id) || ('#' + id), n:v.n, ok:v.ok, pct: v.n ? Math.round(v.ok / v.n * 100) : 0 }))
      .sort((a, b) => b.ok - a.ok);
    send(res, 200, { ok:true, students, items:list,
      summary:{ items:list.length, flagged:list.filter(x => x.flags.length).length, students:students.length,
                answers: list.reduce((a, x) => a + x.n, 0) } });
  },
  /* ─── 班级管理（教师可写，助教只读） ─── */
  async ['GET /api/classes'](req, res){
    const u = authUser(req);
    if(!u) return sendErr(res, 401, '未登录');
    if(!isStaff(u)) return sendErr(res, 403, '仅教师/助教可访问');
    const rows = db.prepare('SELECT c.id,c.name,COUNT(s.id) AS n FROM classes c LEFT JOIN users s ON s.class_id=c.id AND s.role=? GROUP BY c.id ORDER BY c.id').all('student');
    send(res, 200, { ok:true, classes: rows });
  },
  async ['POST /api/classes'](req, res){
    const u = authUser(req); if(!u) return sendErr(res,401,'未登录');
    if(!isTeacher(u)) return sendErr(res,403,'仅教师可建班');
    const name = String((await parseBody(req)).name||'').trim();
    if(!name) return sendErr(res,400,'班级名称不能为空');
    try{ const r=db.prepare('INSERT INTO classes(name,teacher_id) VALUES(?,?)').run(name,u.id); send(res,200,{ok:true,id:r.lastInsertRowid}); }
    catch(e){ sendErr(res,409,'班级名称已存在'); }
  },
  async ['POST /api/classes/update'](req, res){
    const u = authUser(req); if(!u) return sendErr(res,401,'未登录');
    if(!isTeacher(u)) return sendErr(res,403,'仅教师可操作');
    const b = await parseBody(req);
    const name = String(b.name||'').trim();
    if(!name) return sendErr(res,400,'班级名称不能为空');
    try{ db.prepare('UPDATE classes SET name=? WHERE id=?').run(name, +b.id); send(res,200,{ok:true}); }
    catch(e){ sendErr(res,409,'班级名称已存在'); }
  },
  async ['POST /api/classes/delete'](req, res){
    const u = authUser(req); if(!u) return sendErr(res,401,'未登录');
    if(!isTeacher(u)) return sendErr(res,403,'仅教师可操作');
    const id = +(await parseBody(req)).id;
    db.prepare('UPDATE users SET class_id=NULL WHERE class_id=?').run(id);
    db.prepare('DELETE FROM classes WHERE id=?').run(id);
    send(res,200,{ok:true});
  },
  /* ─── 学生账号管理（教师可写，助教只读） ─── */
  async ['GET /api/students'](req, res){
    const u = authUser(req); if(!u) return sendErr(res,401,'未登录');
    if(!isStaff(u)) return sendErr(res,403,'仅教师/助教可访问');
    const clsMap = new Map(db.prepare('SELECT id,name FROM classes').all().map(c=>[c.id,c.name]));
    const st = db.prepare("SELECT id,name,class_id AS classId FROM users WHERE role='student' ORDER BY class_id IS NULL, class_id, id").all();
    send(res, 200, { ok:true, students: st.map(s=>({ id:s.id, name:s.name, classId:s.classId, className: s.classId!=null?(clsMap.get(s.classId)||''):'' })) });
  },
  async ['POST /api/students'](req, res){
    const u = authUser(req); if(!u) return sendErr(res,401,'未登录');
    if(!isTeacher(u)) return sendErr(res,403,'仅教师可建学生账号');
    const b = await parseBody(req);
    const name = String(b.name||'').trim(), pass = String(b.pass||'');
    if(!name || pass.length<4) return sendErr(res,400,'姓名与口令（至少4位）必填');
    const dup = db.prepare('SELECT id FROM users WHERE name=?').get(name);
    if(dup) return sendErr(res,409,'该姓名已被使用');
    const salt = crypto.randomBytes(8).toString('hex');
    const cid = b.class_id ? +b.class_id : null;
    db.prepare('INSERT INTO users(role,name,salt,hash,class_id) VALUES(?,?,?,?,?)').run('student',name,salt,hashPass(pass,salt),cid);
    send(res,200,{ok:true});
  },
  async ['POST /api/students/update'](req, res){
    const u = authUser(req); if(!u) return sendErr(res,401,'未登录');
    if(!isTeacher(u)) return sendErr(res,403,'仅教师可操作');
    const b = await parseBody(req);
    const id = +b.id;
    const cur = db.prepare("SELECT * FROM users WHERE id=? AND role='student'").get(id);
    if(!cur) return sendErr(res,404,'学生不存在');
    /* 逐字段独立参数化更新：SQL 文本固定，杜绝拼接 */
    const updName  = db.prepare('UPDATE users SET name=? WHERE id=?');
    const updAuth  = db.prepare('UPDATE users SET salt=?, hash=? WHERE id=?');
    const updClass = db.prepare('UPDATE users SET class_id=? WHERE id=?');
    db.exec('BEGIN');
    try{
      if(b.name !== undefined){
        const name = String(b.name||'').trim();
        if(!name){ db.exec('ROLLBACK'); return sendErr(res,400,'姓名不能为空'); }
        if(db.prepare('SELECT id FROM users WHERE name=? AND id<>?').get(name, id)){ db.exec('ROLLBACK'); return sendErr(res,409,'该姓名已被使用'); }
        updName.run(name, id);
      }
      if(b.pass !== undefined && b.pass !== ''){
        if(String(b.pass).length < 4){ db.exec('ROLLBACK'); return sendErr(res,400,'口令至少4位'); }
        const salt = crypto.randomBytes(8).toString('hex');
        updAuth.run(salt, hashPass(b.pass, salt), id);
      }
      if(b.class_id !== undefined){
        updClass.run(b.class_id === '' ? null : (+b.class_id), id);
      }
      db.exec('COMMIT');
    }catch(e){ db.exec('ROLLBACK'); return sendErr(res,500,'更新失败'); }
    send(res,200,{ok:true});
  },
  async ['POST /api/students/delete'](req, res){
    const u = authUser(req); if(!u) return sendErr(res,401,'未登录');
    if(!isTeacher(u)) return sendErr(res,403,'仅教师可操作');
    const id = +((await parseBody(req)).id);
    db.prepare('DELETE FROM kv WHERE uid=?').run(id);
    db.prepare("DELETE FROM users WHERE id=? AND role='student'").run(id);
    send(res,200,{ok:true});
  },
};

/* ───────────── 服务器 ───────────── */
const handler = async (req, res) => {
  /* 安全响应头 */
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'SAMEORIGIN');
  res.setHeader('Referrer-Policy', 'same-origin');
  /* CORS：仅回显同源 Origin（跨站不再放行） */
  const origin = req.headers.origin;
  if(origin){
    let same = false;
    try{ same = new URL(origin).host === req.headers.host; }catch(e){}
    if(same){ res.setHeader('Access-Control-Allow-Origin', origin); res.setHeader('Vary', 'Origin'); }
  }
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  if(req.method === 'OPTIONS'){ res.writeHead(204); return res.end(); }

  const url = req.url.split('?')[0];
  if(url.startsWith('/api/')){
    const key = `${req.method} ${url}`;
    const fn = routes[key];
    if(!fn) return sendErr(res, 404, '未知接口');
    try{ await fn(req, res); }
    catch(e){ sendErr(res, 400, '参数错误: ' + (e.message||'')); }
    return;
  }
  serveStatic(req, res, req.url);
};
const server = USE_TLS
  ? https.createServer({ key: fs.readFileSync(CERT_KEY), cert: fs.readFileSync(CERT_CRT) }, handler)
  : http.createServer(handler);

server.listen(PORT, () => {
  const proto = USE_TLS ? 'https' : 'http';
  console.log(`TH!NK server → ${proto}://localhost:${PORT}`);
  if(!USE_TLS){
    console.log('  提示：运行 node gen-cert.js 生成证书后重启，即自动启用 HTTPS；加 --http 可强制 HTTP。');
  } else {
    console.log('  HTTPS 已启用（自签名证书，浏览器首次访问需手动信任）。');
  }
  const nets = os.networkInterfaces();
  const ips = [];
  for(const k of Object.keys(nets)) for(const a of nets[k] || []) if(a.family === 'IPv4' && !a.internal) ips.push(a.address);
  if(ips.length) console.log('  局域网访问（其他设备）：' + ips.map(ip => `${proto}://${ip}:${PORT}`).join('  '));
  console.log(`  令牌有效期 ${Math.round(TOKEN_TTL/864e5*10)/10} 天；数据库备份目录 backups/（保留最近 ${BK_KEEP} 份）`);
  console.log('账号：教师 teacher / think-teacher；助教 助教 / think-assist；学生 学生01、学生02、张小美 / 1234');
});