const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  const output = path.resolve(__dirname, '../artifacts/browser');
  fs.mkdirSync(output, { recursive: true });
  const report = [];
  for (const [name, width, height] of [['desktop', 1440, 960], ['mobile', 390, 844]]) {
    const page = await browser.newPage({ viewport: { width, height } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.APP_URL || 'http://127.0.0.1:8000', { waitUntil: 'networkidle' });
    await page.getByRole('heading', { name: 'Journal analysis' }).waitFor();
    await page.screenshot({ path: path.join(output, name + '-journal.png'), fullPage: true });
    const journalOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    await page.getByRole('button', { name: 'Documents', exact: true }).click();
    await page.getByRole('heading', { name: 'Your documents' }).waitFor();
    await page.screenshot({ path: path.join(output, name + '-documents.png'), fullPage: true });
    const documentOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    report.push({ name, errors, journalOverflow, documentOverflow });
    await page.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.some(row => row.errors.length || row.journalOverflow || row.documentOverflow)) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
