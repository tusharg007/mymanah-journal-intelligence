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
  const report = { context: 'Fresh anonymous non-persistent Edge context; no imported cookies or credentials',
    checked_at: new Date().toISOString(), checked_commit: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    repository: base, documents: [], links: [] };
  try {
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
      report.documents.push({ file, source, status: response.status(), link_count: links.length });
      // GitHub inserts heading-permalink anchors; only the actual Markdown links are submission targets.
      for (const link of links.filter(link => !link.url.includes('#'))) {
        await page.goto(source, { waitUntil: 'domcontentloaded', timeout: 60000 });
        const anchor = page.locator('article.markdown-body a').filter({ hasText: link.text }).first();
        await anchor.waitFor({ timeout: 30000 });
        await Promise.all([page.waitForURL(link.url, { timeout: 60000 }), anchor.click()]);
        await page.waitForLoadState('domcontentloaded');
        const destination = await context.request.get(page.url(), { timeout: 60000 });
        const row = { document: file, text: link.text, url: link.url, final_url: page.url(), status: destination.status() };
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
      }
    }
    report.success = true;
    fs.writeFileSync(output, JSON.stringify(report, null, 2));
  } finally {
    await context.close();
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
