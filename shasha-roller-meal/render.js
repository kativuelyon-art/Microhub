// Render the SVG to a PNG preview and a vector PDF using the pre-installed Chromium.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const dir = __dirname;
  const svg = fs.readFileSync(path.join(dir, 'shasha_roller_meal_10kg.svg'), 'utf8')
    .replace(/width="400mm" height="550mm"/, 'width="800" height="1100"');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 800, height: 1100 }, deviceScaleFactor: 2 });
  await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await page.screenshot({ path: path.join(dir, 'shasha_roller_meal_10kg_preview.png') });
  const raw = fs.readFileSync(path.join(dir, 'shasha_roller_meal_10kg.svg'), 'utf8');
  await page.setContent(`<html><head><style>@page{size:400mm 550mm;margin:0}body{margin:0}</style></head><body>${raw}</body></html>`);
  await page.pdf({ path: path.join(dir, 'shasha_roller_meal_10kg.pdf'), width: '400mm', height: '550mm', printBackground: true });
  await browser.close();
  console.log('rendered');
})();
