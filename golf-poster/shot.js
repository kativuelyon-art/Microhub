const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:1600},deviceScaleFactor:+process.argv[3]||1});
await p.goto('file://'+process.cwd()+'/poster_preview.html');await p.waitForTimeout(2500);await p.evaluate(()=>document.fonts.ready);
await p.screenshot({path:process.argv[2]});await b.close();})();
