const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
for (const name of ['cmaps', 'standard_fonts', 'wasm', 'iccs']) {
  fs.cpSync(path.join(root, 'node_modules/pdfjs-dist', name), path.join(root, 'public/pdfjs', name), { recursive: true });
}
