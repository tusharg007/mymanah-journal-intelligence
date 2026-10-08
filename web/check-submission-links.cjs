const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');

(async () => {
  const root = path.resolve(__dirname, '..');
  const base = 'https://github.com/tusharg007/mymanah-journal-intelligence';
  const browser = await chromium.launch({ headless: true, channel: 'msedge', args: ['--disable-gpu'] });
  // Fresh, non-persistent context: no user profile, credentials or saved browsing data.
  const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
  const page = await context.newPage();
  const output = path.join(root, 'reports', 'submission-link-check.json');
  let report = { context: 'Fresh anonymous non-persistent Edge context; no imported cookies or credentials',
    checked_at: new Date().toISOString(), checked_commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    repository: base, documents: [], links: [] };
  try {
    if (process.argv.includes('--resume') && fs.existsSync(output)) {
      const prior = JSON.parse(fs.readFileSync(output, 'utf8'));
      if (prior.checked_commit !== report.checked_commit) throw new Error('Resume only against the same committed submission');
      report = { ...prior, resumed_at: new Date().toISOString(), resume_context: report.context };
    }
    const repository = await page.goto(base, { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (repository.status() !== 200) throw new Error(`Public repository: HTTP ${repository.status()}`);
    report.repository_status = repository.status();
    for (const file of ['SUBMISSION.md', 'WALKTHROUGH.md']) {
      const source = `${base}/blob/main/docs/${file}`;
      const response = await page.goto(source, { waitUntil: 'domcontentloaded', timeout: 60000 });
      if (response.status() !== 200) throw new Error(`${file}: HTTP ${response.status()}`);
      const article = page.locator('article.markdown-body');
      await article.waitFor({ timeout: 30000 });
      const links = await article.locator('a[href]').evaluateAll(elements => elements.map(a => ({ text: a.textContent, url: a.href })));
      if (!report.documents.some(row => row.file === file)) report.documents.push({ file, source, status: response.status(), link_count: links.length });
      // GitHub inserts heading-permalink anchors; only the actual Markdown links are submission targets.
      for (const link of links.filter(link => !link.url.includes('#'))) {
        if (report.links.some(row => row.document === file && row.url === link.url && row.status === 200)) continue;
        const anchor = page.locator('article.markdown-body a').filter({ hasText: link.text }).first();
        await anchor.waitFor({ timeout: 30000 });
        const popup = context.waitForEvent('page', { timeout: 60000 });
        await anchor.click({ modifiers: ['Control'] });
        const target = await popup;
        await target.waitForLoadState('domcontentloaded');
        const previous = report.links.find(row => row.url === target.url() && row.status === 200);
        let destination = previous ? null : await context.request.get(target.url(), { timeout: 60000, maxRetries: 2 });
        const row = { document: file, text: link.text, url: link.url, final_url: target.url(), status: previous ? 200 : destination.status() };
        if (previous) row.status_verified_on_prior_click = true;
        if (row.status === 429) {
          const retryAfter = Number(destination.headers()['retry-after']) || 60;
          row.initial_status = 429;
          row.retry_wait_seconds = Math.min(180, Math.max(60, retryAfter));
          await new Promise(resolve => setTimeout(resolve, row.retry_wait_seconds * 1000));
          destination = await context.request.get(target.url(), { timeout: 60000, maxRetries: 2 });
          row.status = destination.status();
        }
        if (row.status !== 200) throw new Error(`Link failed: ${JSON.stringify(row)}`);
        const marker = '/blob/main/';
        if (link.url.startsWith(base + marker)) {
          const relative = decodeURIComponent(link.url.slice((base + marker).length));
          const local = path.resolve(root, relative);
          if (!local.startsWith(root + path.sep) || !fs.existsSync(local)) throw new Error(`Missing local asset: ${relative}`);
          row.local_bytes = fs.statSync(local).size;
          if (/\.(mp4|pdf)$/.test(relative)) {
            const media = await context.request.get(`https://raw.githubusercontent.com/tusharg007/mymanah-journal-intelligence/main/${relative}`, {
              headers: { Range: 'bytes=0-31' }, timeout: 60000 });
            const bytes = await media.body();
            row.media_status = media.status();
            row.media_content_type = media.headers()['content-type'];
            const range = media.headers()['content-range'];
            row.remote_total_bytes = range ? Number(range.match(/\/(\d+)$/)[1]) : bytes.length;
            row.media_signature_matches = relative.endsWith('.pdf') ? bytes.subarray(0, 5).toString() === '%PDF-' : bytes.subarray(4, 8).toString() === 'ftyp';
            if (![200, 206].includes(media.status()) || !row.media_signature_matches) throw new Error(`Unavailable media: ${relative}`);
            if (row.remote_total_bytes !== row.local_bytes) throw new Error(`Published media size mismatch: ${relative}`);
            if (relative.endsWith('.mp4')) row.below_100_mib = row.local_bytes < 100 * 1024 * 1024;
          }
        }
        report.links.push(row);
        fs.writeFileSync(output, JSON.stringify(report, null, 2));
        console.log(JSON.stringify(row));
        await target.close();
        await new Promise(resolve => setTimeout(resolve, 5000));
      }
    }
    report.success = true;
    fs.writeFileSync(output, JSON.stringify(report, null, 2));
  } finally {
    await context.close();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
