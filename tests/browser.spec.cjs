/* Optional real-browser checks. Requires Playwright and a running Python app. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const baseURL = process.env.HATTI_TEST_URL || 'http://127.0.0.1:8765';
const output = path.join(__dirname, '..', 'docs', 'screenshots');

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.CHROME_EXECUTABLE ? {executablePath: process.env.CHROME_EXECUTABLE} : {}),
    args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream']});
  const context = await browser.newContext({viewport: {width: 1440, height: 1100}, permissions: ['microphone']});
  const page = await context.newPage();
  const errors = [], posts = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('request', r => {if (r.method() === 'POST') posts.push({url: r.url(), type: r.headers()['content-type'], body: r.postData()});});
  page.on('dialog', d => d.accept());
  fs.mkdirSync(output, {recursive: true});
  await page.goto(baseURL);
  await page.locator('.quest-node').first().waitFor();
  assert.equal(await page.locator('.quest-node').count(), 5);
  await page.screenshot({path: path.join(output, 'adventure-desktop.png'), fullPage: true});

  // A complete lesson: study, recognise, finish, persist and revisit.
  await page.locator('#start-quest').click();
  await page.locator('#quest-dialog').waitFor({state: 'visible'});
  for (let i = 0; i < 4; i++) await page.getByRole('button', {name: 'Next word →', exact: true}).click();
  await page.getByRole('button', {name: 'Let’s play →', exact: true}).click();
  const lesson = await (await page.request.get(`${baseURL}/api/lessons/hello`)).json();
  for (const [i, challenge] of lesson.challenges.entries()) {
    await page.locator(`.quiz-choice[data-word="${challenge.word_id}"]`).click();
    await page.getByRole('button', {name: i === 4 ? 'Finish →' : 'Keep going →', exact: true}).click();
  }
  assert.equal(await page.locator('#badge-count').innerText(), '1');
  assert.equal(await page.locator('#learned-count').innerText(), '5');
  await page.getByRole('button', {name: 'Back to the hills →', exact: true}).click();
  await page.reload(); await page.locator('.quest-node.done').waitFor();
  assert.equal(await page.locator('#learned-count').innerText(), '5');

  // Family task, source guide, actual MediaRecorder with synthetic test device.
  await page.getByRole('button', {name: 'Family corner', exact: true}).click();
  await page.getByRole('button', {name: 'We tried this together ✓', exact: true}).click();
  assert.equal(await page.locator('#family-count').innerText(), '1');
  await page.getByRole('button', {name: 'We say it differently', exact: true}).click();
  await page.locator('.guide-mode').waitFor();
  assert.match(await page.locator('#guide-response').innerText(), /Source guide/);
  await page.locator('#voice-word').selectOption('milk');
  await page.locator('#speaker-label').fill('Test family voice');
  await page.locator('#record-voice').click();
  await page.locator('#record-status').filter({hasText: 'Recording…'}).waitFor();
  await page.waitForTimeout(1100);
  await page.locator('#record-voice').click();
  await page.locator('.saved-voice[data-word-id="milk"]').waitFor();
  await page.getByRole('button', {name: '▶ Hear the saved voice', exact: true}).click();
  await page.reload(); await page.locator('.saved-voice[data-word-id="milk"]').waitFor();
  assert.equal(await page.locator('#voice-count').innerText(), '1');

  // Search plus recording attached to the right word.
  await page.getByRole('button', {name: 'Word basket', exact: true}).click();
  await page.locator('#word-search').fill('Haalu');
  await page.locator('#word-results .word-card').first().waitFor();
  await page.waitForFunction(() => document.querySelector('#search-summary').textContent.includes('matches in source words'));
  const milkCard = page.locator('#word-results .word-card[data-word-id="milk"]');
  await milkCard.waitFor();
  assert.equal(await milkCard.locator('h3').innerText(), 'Haalu');
  await milkCard.locator('.voice-button').click();
  await page.locator('#word-search').fill('xyzxyzxyz');
  await page.locator('.empty-results').waitFor();

  // Export/import validation; resetting progress preserves voices.
  await page.getByRole('button', {name: 'Family corner', exact: true}).click();
  await page.locator('.parent-details summary').click();
  const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#export-progress').click()]);
  const backup = JSON.parse(fs.readFileSync(await download.path(), 'utf8'));
  assert.equal(backup.learned.length, 5); assert.equal(backup.moments.length, 1);
  await page.locator('#import-progress').setInputFiles({name: 'invalid.json', mimeType: 'application/json', buffer: Buffer.from('{"version":1}')});
  await page.locator('#backup-status').filter({hasText: 'No progress changed'}).waitFor();
  await page.locator('#reset-progress').click();
  assert.equal(await page.locator('#learned-count').innerText(), '0');
  assert.equal(await page.locator('#voice-count').innerText(), '1');
  await page.locator('#import-progress').setInputFiles({name: 'progress.json', mimeType: 'application/json', buffer: Buffer.from(JSON.stringify(backup))});
  await page.locator('#backup-status').filter({hasText: 'Progress imported'}).waitFor();
  assert.equal(await page.locator('#learned-count').innerText(), '5');
  await page.locator('.saved-voice[data-word-id="milk"] .danger').click();
  await page.waitForFunction(() => document.querySelector('#voice-count').textContent === '0');

  // Due review on a later local day, including gentle correction.
  await page.evaluate(() => {
    const key = 'hatti-quest-progress-v1'; const s = JSON.parse(localStorage.getItem(key));
    for (const r of Object.values(s.recall)) r.due = '2020-01-01';
    localStorage.setItem(key, JSON.stringify(s));
  });
  await page.getByRole('button', {name: 'Adventure', exact: true}).click();
  await page.reload(); await page.locator('#start-review:enabled').waitFor();
  await page.locator('#start-review').click();
  for (let i = 0; i < 5; i++) {
    await page.locator('.quiz-choice').first().click();
    await page.locator('.quiz-feedback').waitFor();
    await page.getByRole('button', {name: i === 4 ? 'Finish →' : 'Keep going →', exact: true}).click();
  }
  await page.getByRole('button', {name: 'Back to the hills →', exact: true}).click();
  assert.equal(await page.locator('#start-review').isDisabled(), true);

  // Real renders at small sizes; check every view for horizontal overflow.
  for (const width of [375, 320]) {
    await page.setViewportSize({width, height: 812});
    for (const name of ['Adventure', 'Word basket', 'Family corner', 'Our story']) {
      await page.getByRole('button', {name, exact: true}).click();
      const fits = await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);
      if (!fits) {
        const overflow = await page.evaluate(() => [...document.querySelectorAll('body *')].map(el => ({tag: el.tagName, id: el.id, class: el.className, right: el.getBoundingClientRect().right})).filter(el => el.right > innerWidth + 0.5));
        console.error(JSON.stringify({view:name, width, overflow}));
      }
      assert(fits, `${name} should fit a ${width}px screen`);
    }
  }
  await page.setViewportSize({width:375,height:812});
  await page.getByRole('button', {name: 'Adventure', exact: true}).click();
  await page.screenshot({path: path.join(output, 'adventure-mobile.png'), fullPage: true});
  await page.setViewportSize({width:1440,height:1100});
  await page.getByRole('button', {name: 'Our story', exact: true}).click();
  await page.screenshot({path: path.join(output, 'founder-story-page.png'), fullPage: true});
  assert.deepEqual(errors, []);
  assert(posts.length > 10 && posts.every(p => p.url.startsWith(baseURL) && p.type === 'application/json'));
  assert(posts.every(p => !p.body?.includes('Test family voice')));
  console.log(JSON.stringify({status:'passed', checks:['lesson completion','progress persistence','family mission','source guide','microphone recording','local audio persistence and playback','search','backup and invalid import','reset retains voices','due review','mobile 375/320','no audio uploads','no page errors'], requests:posts.length}));
  await browser.close();
})().catch(error => {console.error(error);process.exit(1);});
