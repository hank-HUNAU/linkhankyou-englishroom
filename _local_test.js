/* 本地实测：修复后的 p048/p051 渲染句数与点击播放 */
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8901';
const pages = [
  ['p048', '读写_048_robotics_club.html', 22],
  ['p051', '读写_051_favourite_technology.html', 20]
];
(async () => {
  const browser = await chromium.launch({
    executablePath: 'C:/Users/Thinkpad/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe',
    args: ['--no-sandbox', '--disable-dev-shm-usage']
  });
  for (const [tag, file, want] of pages) {
    const page = await browser.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    const url = BASE + '/%E7%AF%87%E7%AB%A0%E9%A1%B5/' + encodeURIComponent(file);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2500);
    const info = await page.evaluate(() => ({
      cards: document.querySelectorAll('.sent').length,
      tl: (window.TLx || []).length,
      sub: (document.getElementById('tSub') || {}).textContent || '',
      first: (document.querySelector('.sent .en') || {}).textContent || '',
      last: [...document.querySelectorAll('.sent .en')].pop() || {}
    }));
    await page.click('.sent').catch(() => {});
    await page.waitForTimeout(1800);
    const play = await page.evaluate(() => {
      const a = window.audio;
      return a ? { paused: a.paused, t: +a.currentTime.toFixed(2), e: a.error ? a.error.code : null } : null;
    });
    const ok = info.cards === want && info.tl === want && play && play.paused === false && !errs.length;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${tag}: cards=${info.cards}(期望${want}) TLx=${info.tl} | ${info.sub}`);
    console.log(`   首句: ${String(info.first).slice(0, 60)}`);
    console.log(`   末句: ${String(info.last.textContent || '').slice(0, 60)}`);
    console.log(`   点击播放: ${JSON.stringify(play)}${errs.length ? ' ERR:' + errs.join(';') : ''}`);
    await page.close();
  }
  await browser.close();
})().catch(e => { console.error('SCRIPT FAIL:', e.message); process.exit(1); });
