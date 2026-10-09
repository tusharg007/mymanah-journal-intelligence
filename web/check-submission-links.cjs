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
  const outputIndex = process.argv.indexOf('--output');
  if (outputIndex !== -1 && !process.argv[outputIndex + 1]) throw new Error('--output requires a project-relative path');
  const output = path.resolve(root, outputIndex === -1 ? 'reports/submission-link-check.json' : process.argv[outputIndex + 1]);
  if (!output.startsWith(root + path.sep)) throw new Error('Link-check output must stay inside the project');
  fs.mkdirSync(path.dirname(output), { recursive: true });
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
    const documents = ['SUBMISSION.md', 'WALKTHROUGH.md'];
    if (process.argv.includes('--include-email')) documents.push('COVER_EMAIL.md');
    for (const file of documents) {
      const source = `${base}/blob/main/docs/${file}`;
      const response = await page.goto(source, { waitUntil: 'domcontentloaded', timeout: 60000 });
      if (response.status() !== 200) throw new Error(`${file}: HTTP ${response.status()}`);
      const article = page.locator('article.markdown-body');
      await article.waitFor({ timeout: 30000 });
      const links = await article.locator('a[href]').evaluateAll(elements => elements.map(a => ({ text: a.textContent, url: a.href, href: a.getAttribute('href') })));
      if (!report.documents.some(row => row.file === file)) report.documents.push({ file, source, status: response.status(), link_count: links.length });
      // GitHub inserts heading-permalink anchors; only the actual Markdown links are submission targets.
      for (const link of links.filter(link => !link.url.includes('#'))) {
        if (report.links.some(row => row.document === file && row.url === link.url && row.status === 200)) continue;
        const anchor = article.locator(`a[href=${JSON.stringify(link.href)}]`).first();
        await anchor.waitFor({ timeout: 30000 });
        const popup = context.waitForEvent('page', { timeout: 60000 });
        await anchor.click({ modifiers: ['Control'] });
        const target = await popup;
        await target.waitForLoadState('domcontentloaded');
        if (target.url() !== link.url) throw new Error(`Wrong link destination: expected ${link.url}, opened ${target.url()}`);
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
        const reference = ['main', 'submission-v1', 'submission-v2'].find(ref => link.url.startsWith(`${base}/blob/${ref}/`));
        if (reference) {
          const marker = `/blob/${reference}/`;
          const relative = decodeURIComponent(link.url.slice((base + marker).length));
          const local = path.resolve(root, relative);
          if (!local.startsWith(root + path.sep) || !fs.existsSync(local)) throw new Error(`Missing local asset: ${relative}`);
          row.local_bytes = fs.statSync(local).size;
          if (/\.(mp4|pdf)$/.test(relative)) {
            row.media_reference = reference;
            row.expected_bytes = Number(execFileSync('git', ['cat-file', '-s', `${reference}:${relative}`], { cwd: root, encoding: 'utf8' }).trim());
            const media = await context.request.get(`https://raw.githubusercontent.com/tusharg007/mymanah-journal-intelligence/${reference}/${relative}`, {
              headers: { Range: 'bytes=0-31' }, timeout: 60000 });
            const bytes = await media.body();
            row.media_status = media.status();
            row.media_content_type = media.headers()['content-type'];
            const range = media.headers()['content-range'];
            row.remote_total_bytes = range ? Number(range.match(/\/(\d+)$/)[1]) : bytes.length;
            row.media_signature_matches = relative.endsWith('.pdf') ? bytes.subarray(0, 5).toString() === '%PDF-' : bytes.subarray(4, 8).toString() === 'ftyp';
            if (![200, 206].includes(media.status()) || !row.media_signature_matches) throw new Error(`Unavailable media: ${relative}`);
            if (row.remote_total_bytes !== row.expected_bytes) throw new Error(`Published media size mismatch: ${reference}:${relative}`);
            if (relative.endsWith('.mp4')) row.below_100_mib = row.remote_total_bytes < 100 * 1024 * 1024;
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
