/* 线上单元页截图：核对主题词汇卡真实外观（白底 vs 用户截图中的紫粉渐变卡） */
const { chromium } = require('playwright');
const EXE = 'C:/Users/Thinkpad/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';
(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  await page.addInitScript(() => localStorage.setItem('tf_current_student', '截图核对'));
  await page.goto('https://hank-hunau.github.io/linkhankyou-englishroom/index.html?cb=shotcheck', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(1500);
  await page.click('button.book[data-k="5"]');
  await page.waitForTimeout(800);
  await page.screenshot({ path: '_live_unit_check.png', fullPage: false });
  const tv = await page.evaluate(() => {
    const t = document.querySelector('.tv');
    if (!t) return null;
    const cs = getComputedStyle(t);
    return { bg: cs.backgroundImage.slice(0, 80), bgColor: cs.backgroundColor, border: cs.borderLeftColor + ' ' + cs.borderLeftWidth };
  });
  console.log('tv 计算样式:', JSON.stringify(tv));
  await browser.close();
})().catch(e => { console.error('FAIL:', e.message); process.exit(1); });
