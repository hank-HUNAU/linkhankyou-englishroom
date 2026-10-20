/* 线上篇章播放冒烟测试（供"音频不播放"类报障复验）
   用法：NODE_PATH=<playwright所在node_modules> node _smoke_live.js [baseURL]
   逐篇加载线上篇章页 → 点第一句 → 断言 audio 进入播放态且定位到该句起点。
   通过条件：cards==TLx 且 paused==false 且无 pageerror。 */
const { chromium } = require('playwright');
const BASE = process.argv[2] || 'https://hank-hunau.github.io/linkhankyou-englishroom';
const PAGES = [
  ['p048(U5)', '读写_048_robotics_club.html'],
  ['p060(U6)', '读写_060_new_teacher.html'],
  ['p067(U7)', '读写_067_sportwonders.html'],
  ['p090(U9)', '读写_090_offeringhelp.html'],
  ['p108(U11)', '读写_108_sequencing.html'],
  ['p114(U12)', '读写_114_favjourney.html']
];
const EXE = process.env.PLAYWRIGHT_EXECUTABLE ||
  'C:/Users/Thinkpad/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';

(async () => {
  let launchOpts = { args: ['--no-sandbox', '--disable-dev-shm-usage'] };
  try { await chromium.launch(launchOpts); await new Promise(r => setTimeout(r, 1)); } catch (e) { launchOpts.executablePath = EXE; }
  const browser = await chromium.launch(launchOpts);
  let fail = 0;
  for (const [tag, file] of PAGES) {
    const page = await browser.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    const url = BASE + '/%E7%AF%87%E7%AB%A0%E9%A1%B5/' + encodeURIComponent(file);
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(e => errs.push('GOTO:' + e.message));
    await page.waitForTimeout(3000);
    const info = await page.evaluate(() => ({
      cards: document.querySelectorAll('.sent').length,
      tl: (window.TLx || []).length
    }));
    await page.click('.sent').catch(() => {});
    await page.waitForTimeout(2000);
    const play = await page.evaluate(() => {
      const a = window.audio;
      return a ? { paused: a.paused, t: +a.currentTime.toFixed(2), e: a.error ? a.error.code : null } : null;
    });
    const ok = info.cards === info.tl && play && play.paused === false && play.e === null && !errs.length;
    if (!ok) fail++;
    console.log(`${ok ? 'PASS' : 'FAIL'} ${tag}: cards=${info.cards} TLx=${info.tl} click=${JSON.stringify(play)}${errs.length ? ' ERR:' + errs.join(';') : ''}`);
    await page.close();
  }
  await browser.close();
  console.log(fail ? `\n${fail} 篇未通过` : '\n全部通过');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error('SCRIPT FAIL:', e.message); process.exit(1); });
