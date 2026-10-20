/* 单提交推送：远端 main 已被上次 API 推送改为内容等价的另一条链（sha 不同，
   因 GitHub API 将日期规范为 UTC）。本次把本地 main 的树作为一次新提交 X
   叠到远端头之上，然后本地重建 X 的 commit 对象并对齐 refs，使本地=远端。
   前置：远端头树 == 本地 96b2d73 树（内容等价验证）。 */
const { execSync } = require('child_process');

const TOKEN = execSync('gh auth token').toString().trim();
const OWNER = 'hank-HUNAU', REPO = 'linkhankyou-englishroom';
const API = `https://api.github.com/repos/${OWNER}/${REPO}`;
const H = { Authorization: 'token ' + TOKEN, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json' };

function git(a) { return execSync('git ' + a, { encoding: 'utf8', maxBuffer: 1 << 30 }); }
function gitBuf(a) { return execSync('git ' + a, { maxBuffer: 1 << 30 }); }

async function api(path, method, body, tries) {
  tries = tries || 3;
  for (let i = 1; i <= tries; i++) {
    try {
      const r = await fetch(API + path, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
      const j = await r.json().catch(() => null);
      if (!r.ok) throw new Error(r.status + ' ' + JSON.stringify(j).slice(0, 300));
      return j;
    } catch (e) {
      if (i === tries) throw e;
      console.log(`  retry ${i}/${tries - 1} (${e.message.slice(0, 80)})`);
      await new Promise(r => setTimeout(r, 1500 * i));
    }
  }
}

function matchBrace(h, idx) {
  let depth = 0, i = idx, q = null;
  for (; i < h.length; i++) {
    const c = h[i];
    if (q) { if (c === '\\') { i++; continue; } if (c === q) q = null; continue; }
    if (c === '"' || c === "'") { q = c; continue; }
    if (c === '{' || c === '[') depth++;
    else if (c === '}' || c === ']') { depth--; if (depth === 0) return i; }
  }
  return -1;
}

function lsTree(rev) {
  const out = git('-c core.quotePath=false ls-tree -r -t ' + rev);
  const files = new Map(), trees = new Map();
  for (const line of out.split('\n')) {
    if (!line) continue;
    const t = line.indexOf('\t');
    const parts = line.slice(0, t).split(/\s+/);
    const p = line.slice(t + 1);
    if (parts[1] === 'blob') files.set(p, { sha: parts[2], mode: parts[0] });
    else if (parts[1] === 'tree') trees.set(p, parts[2]);
  }
  return { files, trees };
}

function toGitDate(iso) {
  const d = new Date(iso);
  const unix = Math.floor(d.getTime() / 1000);
  const m = iso.match(/([+-]\d{2}):?(\d{2})$/);
  return unix + ' ' + (m ? m[1] + m[2] : '+0000');
}

(async () => {
  const HEAD = git('rev-parse main').trim();
  const BASE = git('log -1 --format=%P main').trim().split(/\s+/)[0];
  console.log('本地 main:', HEAD.slice(0, 10), '| 内容父基点:', BASE);

  const ref = await api('/git/refs/heads/main', 'GET');
  const remoteSha = ref.object.sha;
  const rc = await api('/git/commits/' + remoteSha, 'GET');
  const baseTree = git('log -1 --format=%T ' + BASE).trim();
  console.log('远端 main:', remoteSha.slice(0, 10), '| 远端树:', (rc.tree ? rc.tree.sha : '?').slice(0, 10));
  if (!rc.tree || rc.tree.sha !== baseTree) { console.error('!! 远端树与本地基点树不一致，终止'); process.exit(1); }

  const { files: newFiles, trees: newTrees } = lsTree(HEAD);
  const { files: oldFiles, trees: oldTrees } = lsTree(BASE);
  const changed = new Set();
  for (const [p, v] of newFiles) { const o = oldFiles.get(p); if (!o || o.sha !== v.sha || o.mode !== v.mode) changed.add(p); }
  for (const p of oldFiles.keys()) if (!newFiles.has(p)) changed.add(p);
  console.log('变更文件数:', changed.size, [...changed].map(x => x.split('/').pop()).join(', '));

  for (const p of changed) {
    const nf = newFiles.get(p);
    if (!nf) continue;
    const b64 = gitBuf('cat-file blob ' + nf.sha).toString('base64');
    const j = await api('/git/blobs', 'POST', { content: b64, encoding: 'base64' });
    if (j.sha !== nf.sha) throw new Error('blob sha 不符: ' + p);
  }
  console.log('blobs 就绪');

  const dirs = new Set();
  for (const p of changed) {
    const parts = p.split('/');
    for (let i = 1; i < parts.length; i++) dirs.add(parts.slice(0, i).join('/'));
  }
  const ordered = [...dirs].sort((a, b) => b.split('/').length - a.split('/').length);
  const newTreeSha = new Map();
  for (const dir of ordered) {
    const prefix = dir + '/';
    const entries = [], childDirs = new Set();
    for (const [p, v] of newFiles) {
      if (!p.startsWith(prefix)) continue;
      const rest = p.slice(prefix.length);
      const slash = rest.indexOf('/');
      if (slash < 0) entries.push({ path: rest, mode: v.mode, type: 'blob', sha: v.sha });
      else childDirs.add(rest.slice(0, slash));
    }
    for (const cd of childDirs) {
      const sha = newTreeSha.get(dir + '/' + cd) || oldTrees.get(dir + '/' + cd);
      if (!sha) throw new Error('缺子树 sha: ' + dir + '/' + cd);
      entries.push({ path: cd, mode: '040000', type: 'tree', sha });
    }
    const j = await api('/git/trees', 'POST', { tree: entries });
    newTreeSha.set(dir, j.sha);
  }

  const entries = [], childDirs = new Set();
  for (const [p, v] of newFiles) {
    const slash = p.indexOf('/');
    if (slash < 0) entries.push({ path: p, mode: v.mode, type: 'blob', sha: v.sha });
    else childDirs.add(p.slice(0, slash));
  }
  for (const cd of childDirs) {
    const sha = newTreeSha.get(cd) || oldTrees.get(cd);
    if (!sha) throw new Error('缺根子树 sha: ' + cd);
    entries.push({ path: cd, mode: '040000', type: 'tree', sha });
  }
  const rt = await api('/git/trees', 'POST', { tree: entries });
  const rootSha = rt.sha;
  const headTree = git('log -1 --format=%T ' + HEAD).trim();
  if (rootSha !== headTree) throw new Error('树 sha 不符: ' + rootSha + ' != ' + headTree);
  console.log('树就绪:', rootSha.slice(0, 10), '（与本地 HEAD 树一致）');

  const am = git('log -1 --format=%an%x00%ae%x00%aI ' + HEAD).trim().split('\0');
  const cm = git('log -1 --format=%cn%x00%ce%x00%cI ' + HEAD).trim().split('\0');
  const message = git('log -1 --format=%B ' + HEAD);
  const j = await api('/git/commits', 'POST', {
    message, tree: rootSha, parents: [remoteSha],
    author: { name: am[0], email: am[1], date: am[2] },
    committer: { name: cm[0], email: cm[1], date: cm[2] }
  });
  const X = j.sha;
  console.log('远端新提交 X:', X);

  await api('/git/refs/heads/main', 'PATCH', { sha: X, force: false });
  console.log('✓ 远端 main 已更新到 X');

  // 本地重建 X 并对齐 ref
  const stored = await api('/git/commits/' + X, 'GET');
  const a = stored.author, c = stored.committer;
  const raw = 'tree ' + stored.tree.sha + '\n' +
    'parent ' + stored.parents[0].sha + '\n' +
    'author ' + a.name + ' <' + a.email + '> ' + toGitDate(a.date) + '\n' +
    'committer ' + c.name + ' <' + c.email + '> ' + toGitDate(c.date) + '\n\n' +
    stored.message;
  const localSha = execSync('git hash-object -w -t commit --stdin', { input: raw, encoding: 'utf8' }).trim();
  console.log('本地重建 sha:', localSha, localSha === X ? '（与 X 一致 ✓）' : '（与 X 不一致 ✗）');
  if (localSha === X) {
    execSync(`git update-ref refs/heads/main ${X}`);
    execSync(`git update-ref refs/remotes/origin/main ${X}`);
    console.log('✓ 本地 main 与 origin/main 已对齐到 X，工作区不变');
  } else {
    console.log('⚠ 本地无法逐字节重建 X（GitHub 元数据规范化差异）。');
    console.log('⚠ 请在本机执行一次：git fetch origin && git reset --hard origin/main');
  }
  console.log('\n完成。当前 git 状态：');
  console.log(git('--no-pager log --oneline -2'));
  console.log(git('status --short').trim() || '(工作区干净)');
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
