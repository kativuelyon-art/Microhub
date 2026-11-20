/* Print layout for UCF sample-jar labels.
   Default (no hash)  : A4 landscape, 4 labels per page, 3 mm bleed + crop marks (home/office printers).
   #mode=shop         : one label per page, 106 x 81 mm (100 x 75 trim + 3 mm bleed), for print shops.
   #export            : plain label grid used for PNG export (this script does nothing). */
(function(){
  if (location.hash === '#export') return;
  const mode = new URLSearchParams(location.hash.slice(1)).get('mode') || 'sheet';
  const W = 100, H = 75, B = 3;               // trim size + bleed (mm)
  const labels = [...document.querySelectorAll('.sheet .label')];
  document.querySelector('.sheet').remove();
  document.body.classList.add('print-mode');

  const css = document.createElement('style');
  css.textContent = `
    @page{ size:${mode==='shop' ? `${W+2*B}mm ${H+2*B}mm` : '297mm 210mm'}; margin:0; }
    body.print-mode{ background:#e9edf2; }
    .page{ position:relative; background:#fff; overflow:hidden; page-break-after:always; break-after:page;
           width:${mode==='shop' ? W+2*B : 297}mm; height:${mode==='shop' ? H+2*B : 210}mm; }
    .page:last-child{ page-break-after:auto; break-after:auto; }
    @media screen{ .page{ margin:24px auto; box-shadow:0 6px 30px rgba(0,0,0,.15); } }
    .cell{ position:absolute; width:${W+2*B}mm; height:${H+2*B}mm; overflow:hidden; contain:strict; clip-path:inset(0); }
    .page{ contain:strict; }
    .cell{ background:#fff; }
    .cell .label{ position:absolute; outline:none !important; background:transparent; }
    .crop{ position:absolute; background:#000; }
    .note{ position:absolute; left:0; right:0; bottom:9mm; text-align:center; font:600 2.6mm Montserrat,Arial,sans-serif; color:#8a94a0; }
  `;
  document.head.appendChild(css);

  // A label surrounded by 8 mirrored copies = mirror-edge bleed (art continues seamlessly past the cut line).
  function cell(label){
    const c = document.createElement('div'); c.className = 'cell';
    for (let dy=-1; dy<=1; dy++) for (let dx=-1; dx<=1; dx++){
      const l = (dx||dy) ? label.cloneNode(true) : label;
      if (dx||dy) l.removeAttribute('id'); else l.style.zIndex = 1;
      l.style.left = (B + dx*(W-0.1)) + 'mm'; l.style.top = (B + dy*(H-0.1)) + 'mm';  // 0.1 mm overlap hides seams
      if (dx||dy) l.style.transform = `scale(${dx?-1:1},${dy?-1:1})`;
      c.appendChild(l);
    }
    return c;
  }
  function crop(page, x, y, w, h){ const d=document.createElement('div'); d.className='crop';
    Object.assign(d.style,{left:x+'mm',top:y+'mm',width:w+'mm',height:h+'mm'}); page.appendChild(d); }

  if (mode === 'shop'){
    labels.forEach(l => { const p=document.createElement('div'); p.className='page';
      const c=cell(l); c.style.left='0'; c.style.top='0'; p.appendChild(c); document.body.appendChild(p); });
    return;
  }
  const GAP = 16, X0 = (297 - (2*W+GAP))/2, Y0 = (210 - (2*H+GAP))/2, T = 0.15, OFF = B, LEN = 4;
  for (let i=0; i<labels.length; i+=4){
    const p = document.createElement('div'); p.className='page';
    labels.slice(i,i+4).forEach((l,k)=>{
      const x = X0 + (k%2)*(W+GAP), y = Y0 + Math.floor(k/2)*(H+GAP);
      const c = cell(l); c.style.left=(x-B)+'mm'; c.style.top=(y-B)+'mm'; p.appendChild(c);
      [[x,y,-1,-1],[x+W,y,1,-1],[x,y+H,-1,1],[x+W,y+H,1,1]].forEach(([cx,cy,sx,sy])=>{
        crop(p, sx<0 ? cx-OFF-LEN : cx+OFF, cy-T/2, LEN, T);          // horizontal mark
        crop(p, cx-T/2, sy<0 ? cy-OFF-LEN : cy+OFF, T, LEN);          // vertical mark
      });
    });
    const n=document.createElement('div'); n.className='note';
    n.textContent='Print at 100% / Actual size (no "fit to page") · Cut on the crop marks · Label 100 × 75 mm';
    p.appendChild(n); document.body.appendChild(p);
  }
})();
