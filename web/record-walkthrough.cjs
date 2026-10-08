// Record complete real workflows with deliberate reading time and visible evidence.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const output = path.join(root, 'artifacts', 'walkthrough-v2');
const origin = process.env.APP_URL || 'http://127.0.0.1:8000';
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
const journalText = "Today I celebrated my friend's promotion with her. I felt joyful and grateful for our time together.";
const questions = [
  { text: 'How many annual leave days do Cedar studio employees receive?', number: '23', page: 1 },
  { text: 'What is the equipment reimbursement limit?', number: '420', page: 2 },
];

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const pdf = path.join(output, 'cedar-studio-handbook.pdf');
  const python = process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python';
  const fixture = spawnSync(path.join(root, python), ['-c',
    'from pathlib import Path; from tests.pdf_helpers import make_pdf; from pypdf import PdfWriter; from io import BytesIO; from datetime import datetime, timezone; import sys; target=Path(sys.argv[1]); make_pdf(target, ["Cedar studio employees receive 23 days of annual leave. Leave requests require approval from the studio manager. Contractors receive no annual leave.", "Equipment reimbursement is capped at 420 pounds per year. Receipts must be submitted within 21 days."]); writer=PdfWriter(clone_from=BytesIO(target.read_bytes())); writer.add_metadata({"/CreationDate": datetime.now(timezone.utc).isoformat()}); writer.write(str(target))', pdf],
  { cwd: root, encoding: 'utf8' });
  assert.equal(fixture.status, 0, fixture.stderr);

  const browser = await chromium.launch({ headless: true, channel: 'msedge', args: ['--disable-gpu'] });
  const reports = [];
  let uploadedId;
  try {
    for (const [name, width, height] of [['desktop', 1440, 960], ['mobile', 390, 844]]) {
      const context = await browser.newContext({ viewport: { width, height },
        recordVideo: { dir: output, size: { width, height } } });
      const page = await context.newPage();
      page.setDefaultTimeout(70000);
      const started = Date.now();
      const chapters = [];
      const evidence = [];
      const errors = [];
      const responses = [];
      const seconds = () => Number(((Date.now() - started) / 1000).toFixed(3));
      const chapter = (title, caption) => {
        chapters.push({ start: seconds(), title, caption });
        console.log(`${name} ${seconds()}s: ${title}`);
      };
      page.on('pageerror', error => errors.push(error.message));

      async function frame(selector, title, caption, hold = 10000) {
        const element = page.locator(selector);
        await element.waitFor({ state: 'visible' });
        await element.evaluate(el => el.scrollIntoView({ behavior: 'smooth', block: 'center' }));
        await pause(800);
        const box = await element.boundingBox();
        assert.ok(box && box.y >= -1 && box.y + box.height <= height + 1,
          `${title}: result is not entirely inside the recorded viewport`);
        chapter(title, caption);
        const at = seconds();
        await page.screenshot({ path: path.join(output, `${name}-${evidence.length + 1}.png`) });
        evidence.push({ title, visibleFrom: at, inspectVideoAt: at + hold / 2000, holdSeconds: hold / 1000 });
        await pause(hold);
      }

      async function type(locator, value) {
        await locator.scrollIntoViewIfNeeded();
        await locator.fill('');
        await locator.pressSequentially(value, { delay: 35 });
        await pause(1800);
      }

      async function ask(item) {
        chapter(`Ask: ${item.text}`, 'A real request runs against the selected PDF.');
        await type(page.getByLabel('Question', { exact: true }), item.text);
        const responsePromise = page.waitForResponse(r => r.url().endsWith('/questions') && r.request().method() === 'POST');
        const requestStarted = Date.now();
        await page.getByRole('button', { name: 'Ask document', exact: true }).click();
        const response = await responsePromise;
        assert.equal(response.status(), 200, await response.text());
        const result = await response.json();
        responses.push({ question: item.text, seconds: (Date.now() - requestStarted) / 1000, result });
        await page.locator('.answer p').filter({ hasText: result.answer }).waitFor();
        assert.equal(result.status, 'ANSWERED');
        assert.ok(result.answer.includes(item.number));
        assert.ok(result.citations.some(c => c.document_id === uploadedId && c.page === item.page));
        const citation = page.locator('.answer details').filter({ hasText: `Page ${item.page}` }).first();
        await citation.locator('summary').click();
        await page.locator(`canvas[aria-label="Source document page ${item.page}"][data-rendered=true]`).waitFor();
        await frame('.answer', `Completed answer - page ${item.page}`,
          `Read the answer and expanded source quote.\nCitation points to page ${item.page} of the uploaded PDF.`, 12000);
        await frame('.pdf-preview', `Original PDF - page ${item.page}`,
          'Compare the answer with the original PDF.\nThe cited page is rendered below.', 8000);
        return result;
      }

      try {
        chapter('Start', 'MyManah | Real local-model walkthrough\nJournal analysis and evidence-grounded PDF questions');
        await page.goto(origin, { waitUntil: 'networkidle' });
        await page.getByText('Models ready', { exact: true }).waitFor();
        await pause(3500);
        chapter('Journal request', 'Enter a journal, then run the local models.\nThe recording retains the full processing time.');
        await type(page.getByLabel('Journal entry'), journalText);
        const responsePromise = page.waitForResponse(r => r.url().endsWith('/analyze-journal') && r.request().method() === 'POST');
        const requestStarted = Date.now();
        await page.getByRole('button', { name: 'Analyze', exact: true }).click();
        const response = await responsePromise;
        assert.equal(response.status(), 200, await response.text());
        const journal = await response.json();
        const journalSeconds = (Date.now() - requestStarted) / 1000;
        assert.deepEqual(Object.keys(journal).sort(), ['confidence', 'crisisRisk', 'emotion', 'moodScore', 'sentiment', 'summary']);
        await page.getByText(journal.summary, { exact: true }).waitFor();
        await frame('.journal-results', 'Completed journal analysis',
          'Completed analysis: mood, sentiment, emotion,\nclassification score, screening priority and summary.', 16000);

        chapter('Document upload', name === 'desktop'
          ? 'Upload a two-page policy PDF.\nWait for READY before asking a question.'
          : 'Open the PDF saved by the desktop workflow.\nIts existing index is reused.');
        await page.getByRole('button', { name: 'Documents', exact: true }).click();
        await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
        await pause(2500);
        let upload;
        if (name === 'desktop') {
          const uploading = page.waitForResponse(r => r.url().endsWith('/documents') && r.request().method() === 'POST');
          await page.locator('input[type=file]').setInputFiles(pdf);
          const uploaded = await uploading;
          assert.equal(uploaded.status(), 201, 'Recording requires a new PDF, not a duplicate upload');
          upload = await uploaded.json();
          assert.equal(upload.status, 'READY');
          uploadedId = upload.document.id;
        } else {
          await page.locator('.document-select').filter({ hasText: path.basename(pdf) }).first().click();
        }
        await page.locator('.ready-label').waitFor();
        await frame('.document-question > .section-label', 'PDF ready',
          'READY confirms extraction and indexing completed.\nQuestions can now use this document.', 5000);
        await page.locator('canvas[data-rendered=true]').waitFor();
        await ask(questions[0]);
        await ask(questions[1]);

        chapter('Question outside the document', 'Ask for information the PDF does not contain.');
        const unknownText = "What was Cedar studio's revenue in 2018?";
        await type(page.getByLabel('Question', { exact: true }), unknownText);
        const unsupportedPromise = page.waitForResponse(r => r.url().endsWith('/questions') && r.request().method() === 'POST');
        await page.getByRole('button', { name: 'Ask document', exact: true }).click();
        const unsupportedResponse = await unsupportedPromise;
        assert.equal(unsupportedResponse.status(), 200, await unsupportedResponse.text());
        const unsupported = await unsupportedResponse.json();
        assert.equal(unsupported.status, 'INSUFFICIENT_EVIDENCE');
        assert.deepEqual(unsupported.citations, []);
        await page.locator('.answer-status').filter({ hasText: 'INSUFFICIENT EVIDENCE' }).waitFor();
        await frame('.answer', 'Completed unsupported-question result',
          'INSUFFICIENT EVIDENCE\nThe completed result has no answer claim or citations.', 16000);
        assert.equal(await page.locator('.activity').count(), 0);
        assert.equal(await page.locator('.error').count(), 0);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
        assert.deepEqual(errors, []);
        reports.push({ name, viewport: { width, height }, journalSeconds, journal, upload,
          documentId: uploadedId, responses, unsupported, chapters, evidence,
          errors, end: seconds(), recording: 'Uninterrupted real-time UI capture; every completed result is held visibly.' });
      } finally {
        const video = page.video();
        await context.close();
        await video.saveAs(path.join(output, `${name}.webm`));
        fs.writeFileSync(path.join(output, 'recording-report.json'), JSON.stringify(reports, null, 2));
      }
    }
  } finally {
    await browser.close();
  }
  console.log('Both complete recordings saved, including the final rendered result.');
})().catch(error => { console.error(error); process.exitCode = 1; });
