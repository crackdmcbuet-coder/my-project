const {chromium} = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  const footer = `<div style="width:100%;font-size:8.5px;color:#6b756f;font-family:'Hind Siliguri';padding:0 15mm;display:flex;justify-content:space-between"><span>সকাল-সন্ধ্যা ও রাতের মাসনূন আমল</span><span>পৃষ্ঠা <span class="pageNumber"></span></span></div>`;
  await p.goto('file://' + process.cwd() + '/cover.html', {waitUntil: 'networkidle'});
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({path: 'cover.pdf', format: 'A4', printBackground: true, preferCSSPageSize: true});
  await p.goto('file://' + process.cwd() + '/body.html', {waitUntil: 'networkidle'});
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({path: 'body.pdf', format: 'A4', printBackground: true, preferCSSPageSize: true,
    displayHeaderFooter: true, headerTemplate: '<div></div>', footerTemplate: footer, outline: true, tagged: true});
  await b.close();
})();
