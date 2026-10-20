/* 单元页实测（2026-10-21 2×2 布局 + 进度徽章 + 存储键修复）：
   场景1：种子数据（p048 词汇 12/17 已掌握、tf_stage_48 听完成、theme_u5 10/17）→ 校验徽章值与网格列数
   场景2：干净存储 → 校验全部「未学/—」兜底且无 JS 报错 */
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8901';
const EXE = 'C:/Users/Thinkpad/AppData/Local/ms-playwright/chromium-1234/chrome-win64/chrome.exe';

function seed(page) {
  return page.addInitScript(() => {
    localStorage.setItem('tf_current_student', '测试学员');
    // p048 词汇：17 词中 12 个 known/mastered（注意：诊断页真实存储键带 slug）
    const rec = {};
    for (let i = 1; i <= 17; i++) rec['w' + i] = { status: i <= 12 ? 'known' : 'unknown' };
    localStorage.setItem('u5_p048_robotics_club_records_v2', JSON.stringify(rec));
    localStorage.setItem('tf_stage_48', JSON.stringify({ listen: true, dictate: false }));
    localStorage.setItem('tf_stage_51', JSON.stringify({ listen: true, dictate: true }));
    const th = {};
    for (let i = 1; i <= 17; i++) th['t' + i] = { status: i <= 10 ? 'known' : 'unknown' };
    localStorage.setItem('theme_u5_records_v2', JSON.stringify(th));
  });
}

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  let fail = 0;

  // ── 场景 1：带种子数据 ──
  {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await seed(page);
    await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(800);
    await page.click('button.book[data-k="5"]');
    await page.waitForTimeout(600);

    const r = await page.evaluate(() => {
      const grid = document.getElementById('pgGrid');
      const cards = [...grid.querySelectorAll('.pg')];
      const cs = getComputedStyle(grid);
      return {
        cols: cs.gridTemplateColumns.split(' ').length,
        cardBgImg: getComputedStyle(cards[0]).backgroundImage,
        cardBgColor: getComputedStyle(cards[0]).backgroundColor,
        n: cards.length,
        badges: cards.map(c => [...c.querySelectorAll('.pg-badges .pbad')].map(b => ({
          t: b.textContent.trim(), ok: b.classList.contains('ok'), v: b.classList.contains('v')
        }))),
        titles: cards.map(c => (c.querySelector('.pt') || {}).textContent),
        themeSub: (document.querySelector('.tv-s') || {}).textContent || '',
        vwCount: (document.getElementById('vwCount') || {}).textContent || '',
        viewOn: document.getElementById('view-unit').classList.contains('on')
      };
    });
    const exp = [
      [{ t: '词汇 12/17', ok: false, v: true }, { t: '听', ok: true, v: false }, { t: '写 —', ok: false, v: false }],
      [{ t: '词汇 未学', ok: false, v: false }, { t: '听', ok: true, v: false }, { t: '写', ok: true, v: false }],
      [{ t: '词汇 未学', ok: false, v: false }, { t: '听 —', ok: false, v: false }, { t: '写 —', ok: false, v: false }],
      [{ t: '词汇 未学', ok: false, v: false }, { t: '听 —', ok: false, v: false }, { t: '写 —', ok: false, v: false }]
    ];
    const checks = [
      ['视图切换到单元页', r.viewOn === true],
      ['网格 2 列', r.cols === 2],
      ['4 张篇章卡', r.n === 4],
      ['卡片不透明白（无背景图）', r.cardBgImg === 'none'],
      ['卡片背景色 #fff', r.cardBgColor === 'rgb(255, 255, 255)'],
      ['徽章序列符合预期', JSON.stringify(r.badges) === JSON.stringify(exp)],
      ['主题卡副标题去重（无「17 词」字样）', !r.themeSub.includes('17 词') && r.themeSub.includes('已掌握') && r.themeSub.includes('10')],
      ['章节头保留 17 词', r.vwCount === '17 词'],
      ['无 JS 报错', errs.length === 0]
    ];
    checks.forEach(([name, ok]) => { if (!ok) fail++; console.log(`${ok ? 'PASS' : 'FAIL'} S1 ${name}`); });
    console.log('   徽章实测: ' + JSON.stringify(r.badges));
    if (errs.length) console.log('   ERR: ' + errs.join(';'));

    // 窄屏 480px → 单列
    await page.setViewportSize({ width: 480, height: 800 });
    await page.waitForTimeout(300);
    const cols2 = await page.evaluate(() => getComputedStyle(document.getElementById('pgGrid')).gridTemplateColumns.split(' ').length);
    const okM = cols2 === 1;
    if (!okM) fail++;
    console.log(`${okM ? 'PASS' : 'FAIL'} S1 窄屏480px 单列（实测 ${cols2} 列）`);
    await page.close();
  }

  // ── 场景 2：干净存储 ──
  {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    // 新 context 无学生名会弹姓名门拦住点击——只设姓名，不设任何进度
    await page.addInitScript(() => { localStorage.setItem('tf_current_student', '测试学员'); });
    await page.goto(BASE + '/index.html', { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(800);
    await page.click('button.book[data-k="5"]');
    await page.waitForTimeout(500);
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#pgGrid .pg')];
      return {
        badges: cards.map(c => [...c.querySelectorAll('.pg-badges .pbad')].map(b => b.textContent.trim())),
        themeSub: (document.querySelector('.tv-s') || {}).textContent || ''
      };
    });
    const allFallback = r.badges.every(bs => bs.length === 3 && bs[0] === '词汇 未学' && bs[1] === '听 —' && bs[2] === '写 —');
    const checks = [
      ['干净存储全部兜底徽章', allFallback],
      ['主题卡无进度时不显示已掌握', !r.themeSub.includes('已掌握')],
      ['无 JS 报错', errs.length === 0]
    ];
    checks.forEach(([name, ok]) => { if (!ok) fail++; console.log(`${ok ? 'PASS' : 'FAIL'} S2 ${name}`); });
    if (errs.length) console.log('   ERR: ' + errs.join(';'));
    await page.close();
  }

  await browser.close();
  console.log(fail === 0 ? 'ALL PASS' : `FAILURES: ${fail}`);
  process.exit(fail === 0 ? 0 : 1);
})().catch(e => { console.error('SCRIPT FAIL:', e.message); process.exit(1); });
