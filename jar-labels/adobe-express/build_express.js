// Turn each label option into a static, self-contained HTML document for Adobe Express import.
// Every label becomes one .slide (378 x 284 px = 100 x 75 mm @ 300 dpi). No JS, no <use>, images inlined.
const { chromium } = require('playwright');
const fs = require('fs');
const dir = require('path').resolve(__dirname, '..');
const PX = 378 / 100;   // px per mm: Express prints 96 px/inch, so 378 x 284 px = 100 x 75 mm
const opts = [['ucf_jar_labels.html','a','Option A'],['ucf_jar_labels_option_b.html','b','Option B'],['ucf_jar_labels_option_c.html','c','Option C']];
const variant = process.argv[2] || 'white';   // 'white' or 'clear'
(async () => {
  const b = await chromium.launch();
  for (const [f,o,title] of opts) {
    const p = await b.newPage();
    await p.goto('file://' + dir + '/' + f + (variant==='clear' ? '#export&clear' : '#export'), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    const out = await p.evaluate(async () => {
      // inline <use> references
      document.querySelectorAll('.label svg use').forEach(u => {
        const id = u.getAttribute('href').slice(1), sym = document.getElementById(id), svg = u.closest('svg');
        svg.setAttribute('viewBox', sym.getAttribute('viewBox'));
        if (sym.getAttribute('preserveAspectRatio')) svg.setAttribute('preserveAspectRatio', sym.getAttribute('preserveAspectRatio'));
        [...sym.childNodes].forEach(n => svg.insertBefore(n.cloneNode(true), u)); u.remove();
      });
      // inline images as data URIs
      // Express doesn't re-wrap text: break names that wrap in the browser onto explicit lines
      document.querySelectorAll('.sheet .label .product').forEach(p => {
        const lh = parseFloat(getComputedStyle(p).fontSize) * 1.3;
        if (p.getBoundingClientRect().height > lh && p.textContent.trim() === 'Agricultural Gypsum') p.innerHTML = 'Agricultural<br>Gypsum';
      });
      // Express can't size images with 'auto' or place boxes measured from right/bottom:
      // pin every image and absolutely-positioned badge to explicit mm boxes measured from the live layout.
      const MM = 96 / 25.4;
      document.querySelectorAll('.sheet .label').forEach(label => {
        const L = label.getBoundingClientRect();
        label.querySelectorAll('img').forEach(img => {
          const r = img.getBoundingClientRect();
          img.style.width = (r.width / MM).toFixed(3) + 'mm'; img.style.height = (r.height / MM).toFixed(3) + 'mm';
          img.style.flex = 'none'; img.style.objectFit = 'contain'; img.style.alignSelf = 'center';
        });
        label.querySelectorAll('.tag, .seal').forEach(el => {
          if (getComputedStyle(el).position !== 'absolute') return;
          const r = el.getBoundingClientRect();
          const pad = el.classList.contains('tag') ? 10 : 0;   // a little slack so text never re-wraps in Express
          if (pad) el.style.whiteSpace = 'nowrap';
          Object.assign(el.style, { left: ((r.left - L.left) / MM - pad).toFixed(3) + 'mm', top: ((r.top - L.top) / MM).toFixed(3) + 'mm',
            width: (r.width / MM + pad).toFixed(3) + 'mm', height: (r.height / MM).toFixed(3) + 'mm', right: 'auto', bottom: 'auto', justifyContent: pad ? 'flex-end' : 'center' });
        });
      });
      const css = [...document.querySelectorAll('style')].map(s => s.textContent).join('\n');
      const labels = [...document.querySelectorAll('.sheet .label')].map(l => ({ id: l.id, html: l.outerHTML }));
      return { css, labels };
    });
    const mm0 = s => s.replace(/(-?\d*\.?\d+)mm/g, (_, n) => (parseFloat(n) * PX).toFixed(2) + 'px');
    const mm = s => mm0(s).replace(/src="(assets\/[^"]+\.png)"/g, (_, pth) => 'src="data:image/png;base64,' + fs.readFileSync(dir + '/' + pth).toString('base64') + '"');
    let css = mm(out.css)
      .replace(/@page\{[^}]*\}/g, '')
      .replace(/\.sheet\{[^}]*\}/g, '')
      .replace(/@media screen\{[^}]*\}\s*\}/g, '');
    const names = { gypsum:'Agricultural Gypsum', 'comp-d':'Compound D', 'comp-c':'Compound C', can:'CAN', lan:'LAN', blank:'Blank' };
    const slides = out.labels.map(l => `<section class="slide" data-canvas-width="378" data-canvas-height="284" aria-label="${names[l.id.replace('label-','')]}">\n${mm(l.html)}\n</section>`).join('\n');
    const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="hz:slide-selector" content=".slide">
<meta name="hz:canvas-width" content="378">
<meta name="hz:canvas-height" content="284">
<title>United Capital Fertilizer – Sample Jar Labels – ${title}${variant==='clear'?' (clear)':''}</title>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800;900&family=Kaushan+Script&family=Tinos:wght@700&display=swap" rel="stylesheet">
<style>
${css}
html,body{ margin:0; padding:0; background:${variant==='clear'?'transparent':'#fff'}; }
.slide{ position:relative; width:378px; height:284px; overflow:hidden; margin:0; ${variant==='clear'?'background:transparent;':'background:#fff;'} }
.slide .label{ outline:none !important; position:absolute; left:0; top:0; }
</style>
</head>
<body${variant==="clear" ? " class=\"export clear\"" : ""}>
${slides}
</body>
</html>`;
    const name = `${dir}/adobe-express/ucf_labels_option_${o}${variant==='clear'?'_clear':''}_express.html`;
    fs.writeFileSync(name, html); console.log(name, (html.length/1024).toFixed(0)+'KB', out.labels.length, 'slides');
    await p.close();
  }
  await b.close();
})();
