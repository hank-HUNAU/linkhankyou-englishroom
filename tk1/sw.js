/* TH!NK 站点 Service Worker —— 离线可用 + 本地缓存
 *
 * 策略总览
 *   页面导航(navigate)  → 网络优先，失败回落缓存（并在后台更新）；离线时任何页面回落 index.html
 *   /api/ 请求          → 完全不接管（账号/进度写入必须实时）
 *   音频 mp3/m4a        → 缓存优先（**带 Range 切片**，保证 <audio> 拖动/续播正常）；首播落盘，离线可重放
 *   其余同源静态资源    → stale-while-revalidate（先给缓存，后台静默更新）
 *
 * 版本：改动缓存清单或策略时**必须**改 V（activate 会清掉旧版本缓存）。
 */
const V = '2026-10-26.1';
const SHELL = 'think-shell-' + V;      // 应用外壳（预缓存）
const RUNTIME = 'think-pages-' + V;    // 页面/静态资源运行时缓存
const MEDIA = 'think-media-' + V;      // 音频

/* 预缓存：首访即离线可用的最小集合（不含音频，避免首次就下几十 MB） */
const PRECACHE = [
  './',
  './index.html',
  './login.html',
  './ui.css',
  './ui.js',
  './manifest.webmanifest',
  './assets/timeline.json',
  './assets/icon-192.png',
  './assets/icon-512.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    // 逐个 add：任一 404 不拖垮整体安装
    await Promise.all(PRECACHE.map((u) => c.add(new Request(u, { cache: 'reload' })).catch(() => {})));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keep = new Set([SHELL, RUNTIME, MEDIA]);
    const names = await caches.keys();
    await Promise.all(names.filter((n) => !keep.has(n)).map((n) => caches.delete(n)));
    await self.clients.claim();
  })());
});

/* ── 工具 ── */
async function put(cacheName, req, resp) {
  try {
    if (!resp || !resp.ok || resp.status !== 200) return;
    const c = await caches.open(cacheName);
    await c.put(req, resp);
  } catch (_) { /* 配额满等：静默放弃缓存，不影响播放 */ }
}

async function hasRoom(bytes) {
  try {
    if (!navigator.storage || !navigator.storage.estimate) return true;
    const { usage = 0, quota = 0 } = await navigator.storage.estimate();
    if (!quota) return true;
    return usage + bytes < quota * 0.7;      // 用量超 70% 就不再往里塞
  } catch (_) { return true; }
}

function isAudio(url) { return /\.(mp3|m4a|wav|ogg|aac)$/i.test(url.pathname); }
function isApi(url) { return /\/api\//.test(url.pathname); }

/* Range 切片：把整段缓存裁成 206，供 <audio> 拖动/续播 */
async function sliceRange(resp, rangeHeader) {
  const buf = await resp.arrayBuffer();
  const total = buf.byteLength;
  const m = /bytes=(\d*)-(\d*)/.exec(rangeHeader || '');
  let start = m && m[1] ? parseInt(m[1], 10) : 0;
  let end = m && m[2] ? parseInt(m[2], 10) : total - 1;
  if (!(start >= 0)) start = 0;
  if (!(end >= start)) end = total - 1;
  end = Math.min(end, total - 1);
  return new Response(buf.slice(start, end + 1), {
    status: 206,
    statusText: 'Partial Content',
    headers: {
      'Content-Type': resp.headers.get('Content-Type') || 'audio/mpeg',
      'Content-Range': 'bytes ' + start + '-' + end + '/' + total,
      'Content-Length': String(end - start + 1),
      'Accept-Ranges': 'bytes',
      'Cache-Control': 'public, max-age=31536000, immutable'
    }
  });
}

/* 页面：网络优先（保证能拿到新版），失败回落缓存 */
async function netFirst(req) {
  try {
    const resp = await fetch(req);
    if (resp && resp.ok) {
      const copy = resp.clone();
      put(RUNTIME, req, copy);
    }
    return resp;
  } catch (_) {
    const hit = await caches.match(req, { ignoreSearch: true });
    if (hit) return hit;
    const shell = await caches.match('./index.html', { ignoreSearch: true });
    if (shell) return shell;
    return new Response('<h1>离线</h1><p>本页尚未缓存，请联网后再试。</p>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }
}

/* 音频：缓存优先；命中→按 Range 切片；未命中→整段取回（去掉 Range 头）再落盘 */
async function mediaFirst(req) {
  const range = req.headers.get('range');
  const hit = await caches.match(req, { ignoreSearch: true });
  if (hit) return range ? sliceRange(hit, range) : hit;

  // 未命中：请求整段（避免只拿到分片就落盘导致残缺）
  const full = new Request(req.url, { method: 'GET', credentials: 'same-origin' });
  try {
    const resp = await fetch(full);
    if (resp && resp.ok) {
      const len = parseInt(resp.headers.get('Content-Length') || '0', 10);
      if (await hasRoom(len + 1024 * 512)) put(MEDIA, full, resp.clone());
      return range ? sliceRange(resp, range) : resp;
    }
    // 整段取失败（例如仅支持 Range 的服务）→ 退回原始请求
    return await fetch(req);
  } catch (_) {
    return new Response('', { status: 504, statusText: 'Offline and not cached' });
  }
}

/* 其他静态资源：先给缓存，后台更新 */
async function staleWhileRevalidate(req) {
  const hit = await caches.match(req, { ignoreSearch: false });
  const net = fetch(req).then((resp) => {
    if (resp && resp.ok) put(RUNTIME, req, resp.clone());
    return resp;
  }).catch(() => null);
  return hit || (await net) || new Response('', { status: 504 });
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch (_) { return; }
  if (url.origin !== self.location.origin) return;   // 跨域（Supabase 等）一律不接管
  if (isApi(url)) return;                            // 本地服务 API 直连

  if (req.mode === 'navigate') { e.respondWith(netFirst(req)); return; }
  if (isAudio(url)) { e.respondWith(mediaFirst(req)); return; }
  e.respondWith(staleWhileRevalidate(req));
});

/* 供页面查询缓存状态（诊断用，非必需） */
self.addEventListener('message', (e) => {
  if (e.data === 'cache-info') {
    e.waitUntil((async () => {
      const out = {};
      for (const name of [SHELL, RUNTIME, MEDIA]) {
        const c = await caches.open(name);
        out[name] = (await c.keys()).length;
      }
      e.source && e.source.postMessage({ type: 'cache-info', version: V, counts: out });
    })());
  }
});
