const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { spawnSync } = require('node:child_process');

(async () => {
  const root = path.resolve(__dirname, '..');
  const output = path.join(root, 'artifacts', 'live-browser');
  fs.mkdirSync(output, { recursive: true });
  const pdf = path.join(output, 'delta-workshop-policy.pdf');
  const fixture = spawnSync(path.join(root, '.venv', 'Scripts', 'python.exe'), ['-c',
    'from pathlib import Path; from tests.pdf_helpers import make_pdf; import sys; make_pdf(Path(sys.argv[1]), ["Delta workshop employees receive 18 days of annual leave. Leave requests require approval from the workshop manager. Contractors receive no annual leave.", "Equipment reimbursement is capped at 317 pounds per year. Receipts must be submitted within 14 days."])', pdf], { cwd: root, encoding: 'utf8' });
  assert.equal(fixture.status, 0, fixture.stderr);
  const browser = await chromium.launch({ headless: true, channel: 'msedge', args: ['--disable-gpu'] });
  const report = [];
  let documentId;
  try {
  for (const [name, width, height] of [['desktop', 1440, 960], ['mobile', 390, 844]]) {
    const context = await browser.newContext({ viewport: { width, height },
      ...(process.env.RECORD_VIDEO === '1' ? { recordVideo: { dir: output, size: { width, height } } } : {}) });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.APP_URL || 'http://127.0.0.1:8000', { waitUntil: 'networkidle' });
    await page.getByText('Models ready', { exact: true }).waitFor({ timeout: 160000 });
    await page.getByLabel('Journal entry').fill('Today I celebrated my friend\'s promotion with her. I felt joyful and grateful for our time together.');
    const started = Date.now();
    const analysisResponse = page.waitForResponse(r => r.url().endsWith('/analyze-journal') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Analyze', exact: true }).click();
    const analysis = await analysisResponse;
    assert.equal(analysis.status(), 200, await analysis.text());
    const journal = await analysis.json();
    assert.deepEqual(Object.keys(journal).sort(), ['confidence', 'crisisRisk', 'emotion', 'moodScore', 'sentiment', 'summary']);
    await page.getByText(journal.summary, { exact: true }).waitFor();
    await page.screenshot({ path: path.join(output, name + '-journal-result.png'), fullPage: true });
    const journalSeconds = (Date.now() - started) / 1000;
    await page.getByRole('button', { name: 'Documents', exact: true }).click();
    if (name === 'desktop') {
      const uploaded = page.waitForResponse(r => r.url().endsWith('/documents') && r.request().method() === 'POST');
      await page.locator('input[type=file]').setInputFiles(pdf);
      const response = await uploaded;
      assert.ok([200, 201].includes(response.status()), await response.text());
      const body = await response.json();
      assert.equal(body.status, 'READY');
      documentId = body.document.id;
    } else {
      await page.locator('.document-select').filter({ hasText: 'delta-workshop-policy.pdf' }).click();
    }
    await page.getByLabel('Question', { exact: true }).fill('How many annual leave days do Delta workshop employees receive?');
    const answered = page.waitForResponse(r => r.url().endsWith('/questions') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Ask document', exact: true }).click();
    const response = await answered;
    assert.equal(response.status(), 200, await response.text());
    const answer = await response.json();
    assert.equal(answer.status, 'ANSWERED');
    assert.ok(answer.answer.includes('18'));
    assert.ok(answer.citations.some(c => c.page === 1 && c.document_id === documentId));
    await page.locator('.answer details').first().locator('summary').click();
    const canvas = page.locator('canvas[data-rendered=true]');
    await canvas.waitFor();
    const pixels = await canvas.evaluate(element => {
      const data = element.getContext('2d').getImageData(0, 0, element.width, element.height).data;
      let dark = 0;
      for (let i = 0; i < data.length; i += 16) if (data[i + 3] && data[i] < 180 && data[i + 1] < 180 && data[i + 2] < 180) dark++;
      return dark;
    });
    assert.ok(pixels > 50, 'Source PDF canvas is blank');
    const preview = await context.request.get(`/documents/${documentId}/file`.replace(/^/, process.env.APP_URL || 'http://127.0.0.1:8000'));
    assert.equal(preview.status(), 200);
    assert.ok((await preview.body()).subarray(0, 5).toString() === '%PDF-');
    await page.screenshot({ path: path.join(output, name + '-document-answer.png'), fullPage: true });
    await page.getByRole('button', { name: 'Next page', exact: true }).click();
    await page.locator('canvas[aria-label="Source document page 2"][data-rendered=true]').waitFor();
    assert.equal(await page.getByLabel('Source page', { exact: true }).inputValue(), '2');
    await page.getByRole('button', { name: 'Previous page', exact: true }).click();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    await page.getByLabel('Question', { exact: true }).fill('What was Delta workshop revenue in 2018?');
    const unknown = page.waitForResponse(r => r.url().endsWith('/questions') && r.request().method() === 'POST');
    await page.getByRole('button', { name: 'Ask document', exact: true }).click();
    const unsupported = await unknown;
    assert.equal(unsupported.status(), 200, await unsupported.text());
    const unsupportedBody = await unsupported.json();
    assert.equal(unsupportedBody.status, 'INSUFFICIENT_EVIDENCE');
    assert.deepEqual(unsupportedBody.citations, []);
    const video = page.video();
    await context.close();
    if (video) await video.saveAs(path.join(output, name + '-walkthrough.webm'));
    report.push({ name, errors, overflow, sourceCanvasDarkSamples: pixels, pageNavigation: true,
      journalSeconds, journal, answer, unsupported: unsupportedBody });
  }
  } finally {
  await browser.close();
  }
  fs.writeFileSync(path.join(root, 'reports', 'live-browser.json'), JSON.stringify(report, null, 2));
  assert.ok(report.every(r => !r.errors.length && !r.overflow));
  console.log(JSON.stringify(report.map(r => ({ name: r.name, errors: r.errors, overflow: r.overflow, journalSeconds: r.journalSeconds })), null, 2));
})().catch(error => { console.error(error); process.exitCode = 1; });
