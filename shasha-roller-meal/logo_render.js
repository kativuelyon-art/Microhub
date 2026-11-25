// Render the standalone logo SVG to a PNG preview (on the bag's navy for contrast).
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1248, height: 800 }, deviceScaleFactor: 1 });
  const svg = fs.readFileSync(path.join(__dirname, 'central_millers_logo.svg'), 'utf8')
    .replace('width="156mm" height="100mm"', 'width="1248" height="800"');
  await p.setContent(`<body style="margin:0;background:#2B2670">${svg}</body>`);
  await p.screenshot({ path: path.join(__dirname, 'central_millers_logo_preview.png') });
  await b.close();
})();
