const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.HATTI_TEST_URL || 'http://127.0.0.1:8765';
(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.CHROME_EXECUTABLE ? {executablePath: process.env.CHROME_EXECUTABLE} : {})});
  const page = await browser.newPage({viewport:{width:1440,height:1100}});
  const errors=[];
  page.on('pageerror', e=>errors.push(e.message));
  await page.goto(base);
  await page.locator('.quest-node').first().waitFor();
  await page.locator('#story-theme').selectOption('detective');
  const responsePromise=page.waitForResponse(r=>r.url().endsWith('/api/ai/story') && r.status()===200);
  await page.locator('#create-story').click();
  const payload=await (await responsePromise).json();
  await page.locator('.story-scene').last().waitFor();
  assert.equal(await page.locator('.story-scene').count(),3);
  const sourceWords=await (await page.request.get(base+'/api/content')).json();
  for (const s of payload.scenes) assert.equal(s.word.badaga,sourceWords.words.find(w=>w.id===s.word.id).badaga);
  await page.locator('.story-challenge').first().locator('summary').click();
  const first=payload.scenes[0];
  await page.locator('.story-challenge').first().getByRole('button',{name:first.word.badaga,exact:true}).click();
  await page.locator('.story-challenge .quiz-feedback').first().waitFor();
  assert.ok(JSON.parse(await page.evaluate(()=>localStorage.getItem('hatti-quest-progress-v1'))).learned.includes(first.word.id));
  const output=path.join(__dirname,'..','docs','screenshots');fs.mkdirSync(output,{recursive:true});
  await page.locator('#studio-heading').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(output,'story-studio.png'),fullPage:false});
  for(const width of [375,320]){
    await page.setViewportSize({width,height:900});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  }
  await page.setViewportSize({width:1440,height:1100});
  await page.goto(base+'/lab');
  await page.locator('.service-chip').first().waitFor();
  assert.equal(await page.locator('.service-chip').count(),3);
  await page.getByRole('button',{name:'Inspect ↗'}).first().click();
  assert.ok(await page.locator('.detail-word').count()>=3);
  await page.screenshot({path:path.join(output,'ai-evidence.png'),fullPage:true});
  for(const width of [375,320]){
    await page.setViewportSize({width,height:900});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  }
  assert.deepEqual(errors,[]);
  await browser.close();
  console.log('Story Studio, source grounding, quiz progress, operations ledger and mobile layout passed.');
})().catch(e=>{console.error(e);process.exit(1);});
