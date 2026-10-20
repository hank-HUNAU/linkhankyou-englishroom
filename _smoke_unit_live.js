/* 线上冒烟：单元页 2×2 + 徽章（CDN 缓存用 ?cb= 绕过） */
const { chromium } = require('playwright');
const URL = 'https://hank-hunau.github.io/linkhankyou-englishroom/index.html?cb=unit2x2live';
const EXE = 'C:/Users/Thinkpad/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  await page.addInitScript(() => localStorage.setItem('tf_current_student', '线上冒烟'));
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.click('button.book[data-k="5"]');
  await page.waitForTimeout(800);
  const r = await page.evaluate(() => {
    const grid = document.getElementById('pgGrid');
    const cards = [...grid.querySelectorAll('.pg')];
    return {
      cols: getComputedStyle(grid).gridTemplateColumns.split(' ').length,
      n: cards.length,
      badges: cards.map(c => [...c.querySelectorAll('.pg-badges .pbad')].map(b => b.textContent.trim())),
      bg: getComputedStyle(cards[0]).backgroundColor
    };
  });
  const ok = r.cols === 2 && r.n === 4 && r.badges.every(b => b.length === 3) && r.bg === 'rgb(255, 255, 255)' && !errs.length;
  console.log(`${ok ? 'PASS' : 'FAIL'} 线上单元页: cols=${r.cols} cards=${r.n} bg=${r.bg}`);
  console.log('   徽章: ' + JSON.stringify(r.badges));
  if (errs.length) console.log('   ERR: ' + errs.join(';'));
  await browser.close();
  process.exit(ok ? 0 : 1);
})().catch(e => { console.error('SCRIPT FAIL:', e.message); process.exit(1); });
