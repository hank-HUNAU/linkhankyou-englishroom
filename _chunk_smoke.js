/* _chunk_smoke.js —— 语块 tab 真浏览器验收（零依赖：Node 22 内置 WebSocket 走 CDP）
 * 用法：先起本地服务 python -m http.server 8901，再 node _chunk_smoke.js [page]
 * 校验：①tab 存在且可切 ②渲染条数与正典一致 ③点「听这句」真的播放该句区间
 *       ④遮中文开关生效 ⑤无 JS 运行时报错
 */
const { spawn } = require('child_process');
const http = require('http');

const CHROME = 'C:/Users/Thinkpad/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
const PORT = 9333;
const PAGE = process.argv[2] || '读写_048_robotics_club.html';
const URL = 'http://127.0.0.1:8901/' + encodeURIComponent('篇章页') + '/' + encodeURIComponent(PAGE);

const get = (p) => new Promise((res, rej) => {
  http.get({ host: '127.0.0.1', port: PORT, path: p }, r => {
    let b = ''; r.on('data', d => b += d); r.on('end', () => res(JSON.parse(b)));
  }).on('error', rej);
});
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const chrome = spawn(CHROME, [
    '--headless=new', '--remote-debugging-port=' + PORT,
    '--user-data-dir=' + require('os').tmpdir() + '/cdp-chunk-profile',
    '--autoplay-policy=no-user-gesture-required', '--no-sandbox',
    '--disable-dev-shm-usage', '--mute-audio', 'about:blank'
  ], { stdio: 'ignore' });

  let ver = null;
  for (let i = 0; i < 40 && !ver; i++) {
    try { ver = await get('/json/version'); } catch (e) { await sleep(250); }
  }
  if (!ver) { console.log('✗ 浏览器没起来'); chrome.kill(); process.exit(1); }

  const tgt = await get('/json/list');
  let wsUrl = tgt.find(t => t.type === 'page').webSocketDebuggerUrl;
  const ws = new WebSocket(wsUrl);
  let id = 0; const pend = new Map(); const errors = [];
  const send = (method, params) => new Promise((res) => {
    const mid = ++id; pend.set(mid, res);
    ws.send(JSON.stringify({ id: mid, method, params: params || {} }));
  });
  ws.onmessage = (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m.result); pend.delete(m.id); }
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error'
        && !/favicon/i.test((m.params.entry.url || '') + ' ' + m.params.entry.text)) {
      errors.push((m.params.entry.url || '') + ' | ' + m.params.entry.text);
    }
    if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.text + ' ' + (m.params.exceptionDetails.exception || {}).description);
  };
  await new Promise(r => ws.onopen = r);
  await send('Runtime.enable'); await send('Log.enable'); await send('Page.enable');
  await send('Page.navigate', { url: URL });
  await sleep(3000);

  const ev = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) return { __err: r.exceptionDetails.text };
    return r.result.value;
  };

  const out = {};
  out.tabExists = await ev(`!!document.getElementById('tabChunk')`);
  out.rowsBeforeClick = await ev(`document.querySelectorAll('#chunkList .chk').length`);
  await ev(`document.getElementById('tabChunk').click()`);
  await sleep(300);
  out.chunkVisible = await ev(`!document.getElementById('viewChunk').classList.contains('hide')`);
  out.listenHidden = await ev(`document.getElementById('viewListen').classList.contains('hide')`);
  out.rows = await ev(`document.querySelectorAll('#chunkList .chk').length`);
  out.texts = await ev(`[...document.querySelectorAll('#chunkList .chk .en')].map(e=>e.textContent)`);
  out.badges = await ev(`[...document.querySelectorAll('#chunkList .chk .badge')].map(e=>e.textContent).slice(0,4)`);
  out.hlOK = await ev(`(document.querySelector('#chunkList .chk .ex b')||{}).textContent||''`);

  // 点第一条「听这句」→ 应播该句区间
  const firstSentIdx = await ev(`Number(document.querySelector('#chunkList .chk').dataset.sent)`);
  const iv = await ev(`JSON.stringify((window.TLx||[])[${firstSentIdx}]||null)`);
  if (typeof iv !== 'string') { console.log('调试：firstSentIdx=', JSON.stringify(firstSentIdx), ' iv=', JSON.stringify(iv)); }
  await ev(`document.querySelector('#chunkList .chk [data-play]').click()`);
  await sleep(1200);
  out.audioSrc = await ev(`(document.getElementById('audio').currentSrc||'').split('/').pop()`);
  out.currentTime = await ev(`+document.getElementById('audio').currentTime.toFixed(2)`);
  out.paused = await ev(`document.getElementById('audio').paused`);
  out.tlRange = (typeof iv === 'string' ? JSON.parse(iv || 'null') : null) || [0, 0];
  out.playedClass = await ev(`document.querySelector('#chunkList .chk').classList.contains('played')`);

  // 遮中文
  await ev(`document.getElementById('chkZhTog').click()`);
  await sleep(150);
  out.zhHidden = await ev(`document.body.classList.contains('chk-hide-zh')`);

  const shot = await send('Page.captureScreenshot', { format: 'png' });
  if (shot && shot.data) {
    require('fs').writeFileSync('_chunk_shot.png', Buffer.from(shot.data, 'base64'));
    console.log('截图：_chunk_shot.png');
  }
  console.log(JSON.stringify(out, null, 1));
  if (errors.length) console.log('JS 报错：\n' + errors.slice(0, 5).join('\n'));
  else console.log('JS 报错：无');

  const okAll = out.tabExists && out.rows === 6 && out.chunkVisible && out.listenHidden
    && out.audioSrc === 'p048.mp3' && out.currentTime >= out.tlRange[0] - 0.5
    && out.currentTime < out.tlRange[1] + 0.5 && out.playedClass && out.zhHidden && !errors.length;
  console.log(okAll ? '\n✓ 语块 tab 验收通过' : '\n✗ 验收未通过');
  ws.close(); chrome.kill();
  process.exit(okAll ? 0 : 1);
})();
