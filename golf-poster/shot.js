const { chromium } = require('playwright');
(async()=>{const [,,html,png,scale,pdf]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:1600},deviceScaleFactor:+scale||1});
await p.goto('file://'+process.cwd()+'/'+html);await p.waitForTimeout(2500);await p.evaluate(()=>document.fonts.ready);
await p.screenshot({path:png});
if(pdf) await p.pdf({path:pdf,width:'1200px',height:'1600px',printBackground:true,pageRanges:'1'});
await b.close();})();
