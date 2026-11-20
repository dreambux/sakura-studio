'use strict';
/* E2E strony artefaktu: prawdziwy Chromium (Playwright) + prawdziwy serwer MCP (silnik testowy) przez most HTTP.
   Środowisko `window.claude` to atrapa zgodna z typami kontraktu (e2e/claude-mock.js).
   Uruchomienie: PYTHON=/ścieżka/do/python node e2e/run_e2e.cjs */

const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const net = require('node:net');
const zlib = require('node:zlib');

const PYTHON = process.env.PYTHON || 'python3';
const OUT = process.env.E2E_OUT || fs.mkdtempSync(path.join(os.tmpdir(), 'svm-e2e-'));
const BRIDGE = path.join(__dirname, 'bridge.py');

const failures = [];
let passed = 0;
const check = (cond, msg) => { if (cond) { passed++; console.log('  ok    ' + msg); } else { failures.push(msg); console.log('  FAIL  ' + msg); } };
async function step(name, fn) {
  console.log('\n## ' + name);
  try { await fn(); } catch (e) { failures.push(`${name}: ${e && e.stack || e}`); console.log('  ERROR ' + (e && e.message)); }
}

const freePort = () => new Promise((resolve) => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => resolve(p)); }); });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function startBridge(dataDir, env) {
  const port = await freePort();
  const child = spawn(PYTHON, [BRIDGE, '--port', String(port), '--data-dir', dataDir], { env: { ...process.env, ...env }, stdio: ['ignore', 'pipe', 'pipe'] });
  let log = '';
  child.stdout.on('data', (d) => { log += d; }); child.stderr.on('data', (d) => { log += d; });
  for (let i = 0; i < 300; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/health`); if (r.ok) return { port, child, log: () => log }; } catch { /* jeszcze nie wstał */ }
    if (child.exitCode !== null) throw new Error('bridge exited: ' + log);
    await sleep(200);
  }
  throw new Error('bridge did not start: ' + log);
}

function wavBytes({ seconds, rate, channels, freq }) {
  const frames = Math.floor(seconds * rate); const dataLen = frames * channels * 2; const buf = Buffer.alloc(44 + dataLen);
  buf.write('RIFF', 0); buf.writeUInt32LE(36 + dataLen, 4); buf.write('WAVE', 8); buf.write('fmt ', 12); buf.writeUInt32LE(16, 16);
  buf.writeUInt16LE(1, 20); buf.writeUInt16LE(channels, 22); buf.writeUInt32LE(rate, 24); buf.writeUInt32LE(rate * channels * 2, 28);
  buf.writeUInt16LE(channels * 2, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(dataLen, 40);
  for (let i = 0; i < frames; i++) for (let c = 0; c < channels; c++) buf.writeInt16LE(Math.round(Math.sin((2 * Math.PI * freq * (c + 1) * i) / rate) * 0.4 * 32767), 44 + (i * channels + c) * 2);
  return buf;
}

function parseWav(buf) {
  if (buf.toString('ascii', 0, 4) !== 'RIFF' || buf.toString('ascii', 8, 12) !== 'WAVE') throw new Error('not a WAV');
  const channels = buf.readUInt16LE(22); const rate = buf.readUInt32LE(24); const bits = buf.readUInt16LE(34); const dataLen = buf.readUInt32LE(40);
  return { channels, rate, bits, dataLen, seconds: dataLen / (channels * rate * (bits / 8)) };
}

function parseZip(buf) {
  if (buf.readUInt32LE(0) !== 0x04034b50) throw new Error('no local header');
  const method = buf.readUInt16LE(8); const crc = buf.readUInt32LE(14); const csize = buf.readUInt32LE(18); const usize = buf.readUInt32LE(22);
  const nlen = buf.readUInt16LE(26); const elen = buf.readUInt16LE(28);
  const name = buf.toString('utf8', 30, 30 + nlen); const start = 30 + nlen + elen;
  const eocd = buf.readUInt32LE(buf.length - 22) === 0x06054b50 ? { entries: buf.readUInt16LE(buf.length - 14), cdOffset: buf.readUInt32LE(buf.length - 6) } : null;
  const cdSig = eocd ? buf.readUInt32LE(eocd.cdOffset) : 0;
  return { name, method, crc, usize, csize, data: buf.subarray(start, start + csize), eocd, cdSig };
}

async function openPage(browser, port, cfg = {}, viewport = { width: 1280, height: 900 }) {
  const context = await browser.newContext({ viewport });
  const page = await context.newPage();
  const problems = [];
  page.on('pageerror', (e) => problems.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error' && !/fonts\.g/.test(m.location().url || '') && !/fonts\.g/.test(m.text())) problems.push('console: ' + m.text()); });
  await page.goto(`http://127.0.0.1:${port}/page?cfg=${encodeURIComponent(JSON.stringify(cfg))}`);
  return { page, context, problems };
}

const engineReady = (page) => page.waitForFunction(() => /gotowy/.test(document.querySelector('#chip-engine').textContent), null, { timeout: 40000 });
const voiceNames = (page) => page.locator('.voice .name').allTextContents();

(async () => {
  const dataDir = fs.mkdtempSync(path.join(OUT, 'data-'));
  const bridge = await startBridge(dataDir, { SVM_FAKE_LOAD_DELAY: '1.0', SVM_FAKE_SYNTH_DELAY: '0.3', SVM_FAKE_FAIL_ON: 'BOOM' });
  const browser = await chromium.launch();
  console.log('output dir:', OUT);

  await step('A. start, status, preview, generate with a built-in voice, play, save as ZIP', async () => {
    const { page, context, problems } = await openPage(browser, bridge.port);
    const first = await page.locator('#chip-engine').textContent();
    check(/łączenie|ładuje|gotowy/.test(first), `engine chip shows a state at load ("${first}")`);
    check(await page.locator('#add-open').isVisible(), 'the add-friend button is visible from the first moment, before the engine is ready');
    await engineReady(page);
    check(await page.locator('#add-hint').isHidden(), 'the gate hint disappears once the engine is ready');
    check((await page.locator('#add-open').boundingBox()).y < (await page.locator('label.voice', { hasText: 'buttery' }).boundingBox()).y, 'the add button sits above the built-in and Claude voices');
    check(/dostępne/.test(await page.locator('#chip-claude').textContent()), 'Claude voices chip says available');
    check(await page.locator('#setup').isHidden(), 'setup guide is hidden when the host is connected');
    check(/TRYB TESTOWY/.test(await page.locator('#engine-note').textContent()) && await page.locator('#engine-note').isVisible(), 'the fake-engine warning ("tones, not speech") is visible');
    check((await page.locator('label.voice:has(input:checked) .name').textContent()) === 'demo-niski', 'default selection prefers a local voice over Claude voices once the engine is ready');
    check(/Głos: demo-niski/.test(await page.locator('#chosen').textContent()), 'the chosen voice is echoed next to the text box');
    const names = await voiceNames(page);
    check(['demo-niski', 'demo-wysoki', 'buttery', 'airy', 'glassy', 'rounded'].every((n) => names.includes(n)), `voice list has built-in and Claude voices (${names.join(', ')})`);
    await page.waitForSelector('#spoken-box:not([hidden])', { timeout: 10000 });
    const spoken = await page.locator('#spoken').textContent();
    check(spoken.includes('dziewiętnastego listopada dwa tysiące dwudziestego szóstego roku') && spoken.includes('tysiąc dwieście pięćdziesiąt złotych') && spoken.includes('czternastej trzydzieści'), `preview shows the normalised Polish text ("${spoken.slice(0, 80)}…")`);
    check(!/\d/.test(spoken), 'preview has no digits left');
    check(await page.evaluate(() => getComputedStyle(document.querySelector('#add-panel')).display) === 'none', 'hidden panels stay hidden thanks to the page\'s own CSS, not the host reset');
    check(/outputs/.test(await page.locator('#results-empty').textContent()), 'the empty-results text mentions the disk copies because the engine saves them');

    await page.locator('label.voice', { hasText: 'demo-niski' }).click();
    await page.locator('#go').click();
    await page.waitForSelector('#results .result', { timeout: 40000 });
    const msg = await page.locator('#msg').textContent();
    check(/Gotowe/.test(msg), `completion message ("${msg}")`);
    const meta = await page.locator('#results .result .meta').first().textContent();
    check(/\d+,\d s/.test(meta) && /24 kHz/.test(meta), `result meta has duration and rate ("${meta}")`);
    const savedPath = await page.locator('#results .result .path').first().textContent();
    check(/outputs/.test(savedPath) && /\.wav/.test(savedPath), `disk copy path is shown ("${savedPath}")`);
    check(await page.locator('#go').isEnabled(), 'Generate is enabled again after the job');

    await sleep(1800);
    const time = await page.locator('#results .result .time').first().textContent();
    const playing = await page.locator('#results .result [data-play]').first().textContent();
    check(!/^0:00 \//.test(time) || playing === '❚❚', `playback advances through WebAudio (time "${time}", button "${playing}")`);

    await page.locator('#results .result button', { hasText: 'Zapisz (ZIP z WAV)' }).first().click();
    await page.waitForFunction(() => window.__saves.length === 1);
    const save = await page.evaluate(() => window.__saves[0]);
    const zip = parseZip(Buffer.from(save.bytes));
    const wav = parseWav(zip.data);
    check(/^glos-demo-niski-\d{14}\.zip$/.test(save.filename) && /\.wav$/.test(zip.name), `ZIP and entry names are sane (${save.filename} / ${zip.name})`);
    check(zip.method === 0 && zip.usize === zip.csize && zlib.crc32(zip.data) === zip.crc, 'ZIP entry is stored with a correct CRC32');
    check(zip.eocd && zip.eocd.entries === 1 && zip.cdSig === 0x02014b50, 'ZIP has a valid central directory and end record');
    check(wav.channels === 1 && wav.rate === 24000 && wav.bits === 16 && wav.seconds > 3, `WAV inside is mono 24 kHz PCM16, ${wav.seconds.toFixed(1)} s`);

    await page.evaluate(() => { const t = document.querySelector('#text'); t.value = 'Test \uD83D koniec.'; t.dispatchEvent(new Event('input')); });
    await page.locator('#go').click();
    await page.waitForFunction(() => document.querySelectorAll('#results .result').length === 2, null, { timeout: 40000 });
    const sent = await page.evaluate(() => window.__hostCalls.filter((c) => c.tool === 'speak').pop().input.text);
    check(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/.test(sent) && sent.includes('\uFFFD'), 'a lone UTF-16 surrogate is replaced before the call (the stdio transport would drop it silently)');
    const states = await page.locator('#results .result [data-play]').allTextContents();
    check(states.filter((s) => s === '❚❚').length <= 1, `only one clip plays at a time (${states.join(' ')})`);
    await page.screenshot({ path: path.join(OUT, 'desktop-after-generate.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await sleep(300);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    check(overflow <= 1, `no horizontal overflow at 390 px width (overflow ${overflow})`);
    await page.screenshot({ path: path.join(OUT, 'mobile-after-generate.png'), fullPage: true });
    check(problems.length === 0, `no console or page errors${problems.length ? ': ' + problems.join(' | ') : ''}`);
    await context.close();
  });

  await step('B. add a friend voice (stereo 44.1 kHz upload), consent gate, generate, delete', async () => {
    const { page, context, problems } = await openPage(browser, bridge.port);
    await engineReady(page);
    await page.locator('#add-open').click();
    check(await page.locator('#add-panel').isVisible(), 'add panel opens');
    await page.locator('#add-name').fill('Kuba Żółć');
    await page.locator('#add-files').setInputFiles([{ name: 'kuba-stereo.wav', mimeType: 'audio/wav', buffer: wavBytes({ seconds: 8, rate: 44100, channels: 2, freq: 220 }) }]);
    await page.waitForSelector('#filelist li');
    await page.waitForFunction(() => /Razem 8,0 s/.test(document.querySelector('#meter-text').textContent));
    check(/rozsądna długość/.test(await page.locator('#meter-text').textContent()), `file listed and measured ("${await page.locator('#meter-text').textContent()}")`);

    await page.locator('#add-save').click();
    check(/zgod/i.test(await page.locator('#add-msg').textContent()), 'saving without consent is refused with a consent message');
    await page.screenshot({ path: path.join(OUT, 'desktop-add-panel.png'), fullPage: true });
    await page.locator('#add-consent').check();
    await page.locator('#add-save').click();
    await page.waitForSelector('#add-panel[hidden]', { state: 'attached', timeout: 30000 });
    await page.waitForFunction(() => [...document.querySelectorAll('.voice .name')].some((n) => n.textContent === 'Kuba Żółć'));
    check(/Zapisano głos/.test(await page.locator('#msg').textContent()), 'success message after saving');
    check(await page.locator('.voice', { hasText: 'Kuba Żółć' }).locator('.badge').count() === 1, 'friend card shows the consent badge');

    const voicesDir = path.join(dataDir, 'voices');
    const ids = fs.readdirSync(voicesDir).filter((n) => /^v_[0-9a-f]{12}$/.test(n));
    check(ids.length === 1, `exactly one voice directory on disk (${ids.join(',')})`);
    const record = JSON.parse(fs.readFileSync(path.join(voicesDir, ids[0], 'voice.json'), 'utf8'));
    check(record.name === 'Kuba Żółć' && record.consent.confirmed === true && record.consent.statement_version === 1, 'voice.json records name and consent');
    const stored = parseWav(fs.readFileSync(path.join(voicesDir, ids[0], 'samples', 's0.wav')));
    check(stored.channels === 1 && stored.rate === 24000 && stored.bits === 16 && Math.abs(stored.seconds - 8) < 0.05, `stored sample was converted in the browser to mono 24 kHz PCM16 (${stored.seconds.toFixed(2)} s)`);

    await page.locator('label.voice', { hasText: 'Kuba Żółć' }).click();
    await page.locator('#text').fill('Krótki test głosu znajomego.');
    await page.locator('#go').click();
    await page.waitForSelector('#results .result', { timeout: 40000 });
    check((await page.locator('#results .result .who').first().textContent()) === 'Kuba Żółć', 'result is attributed to the friend voice');

    await page.getByRole('button', { name: 'Usuń głos Kuba Żółć' }).click();
    check(/Usunąć głos/.test(await page.locator('.voice.confirming').textContent()), 'delete asks for in-page confirmation');
    await page.locator('.voice.confirming button', { hasText: 'Usuń' }).click();
    await page.waitForFunction(() => ![...document.querySelectorAll('.voice .name')].some((n) => n.textContent === 'Kuba Żółć'));
    await sleep(300);
    check(fs.readdirSync(voicesDir).filter((n) => /^v_/.test(n)).length === 0, 'voice directory is gone after deletion');
    check(problems.length === 0, `no console or page errors${problems.length ? ': ' + problems.join(' | ') : ''}`);
    await context.close();
  });

  await step('C. cancel a running job', async () => {
    const { page, context } = await openPage(browser, bridge.port);
    await engineReady(page);
    await page.locator('label.voice', { hasText: 'demo-wysoki' }).click();
    await page.locator('#text').fill(Array.from({ length: 14 }, (_, i) => `To jest zdanie numer ${i + 1} do wypowiedzenia.`).join(' '));
    const before = await page.locator('#results .result').count();
    await page.locator('#go').click();
    await page.waitForFunction(() => /Generuję fragment/.test(document.querySelector('#msg').textContent), null, { timeout: 15000 });
    await page.locator('#stop').click();
    await page.waitForFunction(() => /Anulowano/.test(document.querySelector('#msg').textContent), null, { timeout: 20000 });
    check(true, 'cancel message appears');
    check((await page.locator('#results .result').count()) === before, 'no result is added for a cancelled job');
    check(await page.locator('#go').isEnabled(), 'Generate is enabled again');
    await context.close();
  });

  await step('D. engine error and length limit are shown in Polish', async () => {
    const { page, context } = await openPage(browser, bridge.port);
    await engineReady(page);
    await page.locator('label.voice', { hasText: 'demo-niski' }).click();
    await page.locator('#text').fill('To jest BOOM test.');
    await page.locator('#go').click();
    await page.waitForSelector('#msg[data-tone="bad"]', { timeout: 20000 });
    check(/Silnik testowy zgłosił błąd/.test(await page.locator('#msg').textContent()), 'engine failure message from the server is shown');
    await page.locator('#text').fill('x'.repeat(2100));
    await page.locator('#go').click();
    check(/za długi/.test(await page.locator('#msg').textContent()), 'over-limit text is refused client-side');
    await context.close();
  });

  await step('E. no local host: setup guide and Claude voices still work', async () => {
    const { page, context, problems } = await openPage(browser, bridge.port, { noHost: true });
    await page.waitForFunction(() => /niepodłączony/.test(document.querySelector('#chip-engine').textContent), null, { timeout: 15000 });
    check(await page.locator('#setup').isVisible(), 'setup guide is visible');
    check((await page.locator('#cfg-snippet').textContent()).includes('"sakura-voice"'), 'config snippet names the server sakura-voice');
    check(await page.locator('#add-open').isVisible(), 'the add-friend button is visible even without a local engine');
    check(/nie jest podłączony/.test(await page.locator('#add-hint').textContent()), 'the hint under the button says why saving is blocked');
    await page.locator('#add-open').click();
    check(await page.locator('#add-panel').isVisible() && await page.locator('#add-gate').isVisible(), 'the panel opens and shows the gate notice');
    await page.locator('#add-name').fill('Kolega');
    await page.locator('#add-files').setInputFiles([{ name: 'kolega.wav', mimeType: 'audio/wav', buffer: wavBytes({ seconds: 10, rate: 44100, channels: 1, freq: 200 }) }]);
    await page.waitForFunction(() => /Razem 10,0 s/.test(document.querySelector('#meter-text').textContent));
    check(true, 'the recording is read and measured before any engine is connected');
    await page.locator('#add-consent').check();
    check(await page.locator('#add-save').isDisabled() && /najpierw podłącz silnik/.test(await page.locator('#add-save').textContent()), 'Save is disabled and says it needs the engine');
    check(await page.locator('#add-gate-setup').isVisible(), 'the gate offers a jump to the setup guide');
    const hostTools = await page.evaluate(() => window.__hostCalls.map((c) => c.tool));
    check(!hostTools.some((t) => t.startsWith('voice_upload')), 'no upload calls are made without an engine');
    await page.screenshot({ path: path.join(OUT, 'desktop-no-host-add.png'), fullPage: true });
    await page.locator('#add-cancel').click();
    await page.locator('#cfg-copy').click();
    await page.locator('#text').fill('Dzień dobry, to głos Claude.');
    await page.locator('#go').click();
    await page.waitForFunction(() => window.__ttsCalls.length === 1);
    const call = await page.evaluate(() => window.__ttsCalls[0]);
    check(call.options.voice === 'buttery' && call.options.language === 'pl' && call.options.rate === 1 && call.what[0].text === 'Dzień dobry, to głos Claude.', `tts.speak called with voice, language, rate and text (${JSON.stringify(call.options)})`);
    check(await page.locator('#speed').getAttribute('min') === '0.7' && await page.locator('#speed').getAttribute('max') === '1.5', 'the tempo slider shows the 0.7-1.5 range that Claude voices accept');
    check(await page.locator('label.consent:has(#normalize)').isHidden() && await page.locator('#spoken-box').isHidden(), 'the normalisation switch and the "how it will be read" box are hidden for Claude voices (they read the raw text)');
    await page.screenshot({ path: path.join(OUT, 'desktop-no-host.png'), fullPage: true });
    check(problems.length === 0, `no console or page errors${problems.length ? ': ' + problems.join(' | ') : ''}`);
    await context.close();
  });

  await step('F. no runtime at all and denied permissions degrade without errors', async () => {
    const bare = await openPage(browser, bridge.port, { noClaude: true });
    await bare.page.waitForFunction(() => /niedostępny/.test(document.querySelector('#chip-engine').textContent), null, { timeout: 15000 });
    check(await bare.page.locator('#go').isDisabled(), 'Generate is disabled when no voice exists');
    check(await bare.page.locator('#add-open').isVisible() && /nie ma dostępu/.test(await bare.page.locator('#add-hint').textContent()), 'add-friend stays visible and explains the missing access without window.claude');
    check(bare.problems.length === 0, `no errors without window.claude${bare.problems.length ? ': ' + bare.problems.join(' | ') : ''}`);
    await bare.context.close();
    const denied = await openPage(browser, bridge.port, { denyCalls: true });
    await denied.page.waitForFunction(() => /brak zgody/.test(document.querySelector('#chip-engine').textContent), null, { timeout: 15000 });
    check(true, 'chip says the local server has no permission');
    check(await denied.page.locator('#setup').isVisible() && /Uprawnienia/.test(await denied.page.locator('#setup-why').textContent()), 'permission explanation is shown instead of the install steps');
    check(await denied.page.locator('#setup-steps').isHidden(), 'install steps are hidden when the cause is a denied permission');
    check(await denied.page.locator('#add-open').isVisible() && /Uprawnienia/.test(await denied.page.locator('#add-hint').textContent()), 'add-friend stays visible and explains the missing permission');
    check(denied.problems.length === 0, `no errors when calls are denied${denied.problems.length ? ': ' + denied.problems.join(' | ') : ''}`);
    await denied.context.close();
  });

  await step('G. engine-driven reference policy: one clip, 4-12 s, transcript required', async () => {
    const strictDir = fs.mkdtempSync(path.join(OUT, 'data-strict-'));
    const strict = await startBridge(strictDir, { SVM_FAKE_LOAD_DELAY: '0.3', SVM_FAKE_REF_MAX_FILES: '1', SVM_FAKE_REF_MIN_SECONDS: '4', SVM_FAKE_REF_MAX_SECONDS: '12', SVM_FAKE_REF_TRANSCRIPT: 'required', SVM_FAKE_NO_CAPS: 'speed,temperature' });
    try {
      const { page, context, problems } = await openPage(browser, strict.port);
      await engineReady(page);
      check(await page.locator('#speed-field').isHidden() && await page.locator('#caps-note').isVisible(), 'tempo is hidden for a model without tempo control, with an explanation');
      check(/tempa ani ekspresji/.test(await page.locator('#caps-note').textContent()), 'the note names both missing controls');
      await page.locator('label.voice', { hasText: 'buttery' }).click();
      check(await page.locator('#speed-field').isVisible() && await page.locator('#caps-note').isHidden(), 'Claude voices keep their own tempo control');
      await page.locator('label.voice', { hasText: 'demo-niski' }).click();
      await page.locator('#add-open').click();
      check(await page.locator('#add-transcript-box').isVisible() && /wymagane/.test(await page.locator('#add-transcript-req').textContent()), 'transcript box is shown and marked required');
      check(/jednego nagrania/.test(await page.locator('#policy-note').textContent()), 'the single-clip policy is explained');
      check((await page.locator('#add-files').evaluate((el) => el.multiple)) === false, 'the file picker is single-file');
      check(/Najlepiej 8 do 20 sekund/.test(await page.locator('#tips-length').textContent()), 'recommended length comes from the engine');
      await page.locator('#add-name').fill('Ola');
      await page.locator('#add-files').setInputFiles([{ name: 'a.wav', mimeType: 'audio/wav', buffer: wavBytes({ seconds: 8, rate: 24000, channels: 1, freq: 200 }) }]);
      await page.waitForSelector('#filelist li');
      await page.locator('#add-files').setInputFiles([{ name: 'b.wav', mimeType: 'audio/wav', buffer: wavBytes({ seconds: 6, rate: 24000, channels: 1, freq: 300 }) }]);
      await page.waitForFunction(() => /jednego nagrania/.test(document.querySelector('#add-msg').textContent));
      check((await page.locator('#filelist li').count()) === 1, 'a second clip is refused');
      await page.locator('#add-consent').check();
      await page.locator('#add-save').click();
      check(/transkrypcji/.test(await page.locator('#add-msg').textContent()), 'saving without the transcript is refused before any upload');
      check(!(await page.evaluate(() => window.__hostCalls.map((c) => c.tool))).some((t) => t.startsWith('voice_upload')), 'no upload call was made');
      await page.locator('#add-transcript').fill('Mam 5 złotych i 12,50 zł.');
      await page.locator('#add-save').click();
      await page.waitForSelector('#add-panel[hidden]', { state: 'attached', timeout: 30000 });
      const ids = fs.readdirSync(path.join(strictDir, 'voices')).filter((n) => /^v_/.test(n));
      const record = JSON.parse(fs.readFileSync(path.join(strictDir, 'voices', ids[0], 'voice.json'), 'utf8'));
      check(record.transcript === 'Mam pięć złotych i dwanaście złotych pięćdziesiąt groszy.', `the transcript is stored normalised ("${record.transcript}")`);
      await page.locator('#add-open').click();
      await page.locator('#add-name').fill('Zbyt długi');
      await page.locator('#add-files').setInputFiles([{ name: 'long.wav', mimeType: 'audio/wav', buffer: wavBytes({ seconds: 14, rate: 24000, channels: 1, freq: 200 }) }]);
      await page.waitForSelector('#filelist li');
      await page.locator('#add-transcript').fill('Coś tam mówię.');
      await page.locator('#add-consent').check();
      await page.locator('#add-save').click();
      check(/maksimum/.test(await page.locator('#add-msg').textContent()), 'a clip over the engine maximum is refused with the limit');
      check(problems.length === 0, `no console or page errors${problems.length ? ': ' + problems.join(' | ') : ''}`);
      await context.close();
    } finally { strict.child.kill(); }
  });

  await step('H. Anuluj during an upload does not save the voice', async () => {
    const { page, context, problems } = await openPage(browser, bridge.port);
    await engineReady(page);
    await page.route('**/call', async (route) => { await sleep(700); await route.continue(); });
    await page.locator('#add-open').click();
    await page.locator('#add-name').fill('Anulowany');
    await page.locator('#add-files').setInputFiles([{ name: 'a.wav', mimeType: 'audio/wav', buffer: wavBytes({ seconds: 10, rate: 44100, channels: 1, freq: 200 }) }]);
    await page.waitForFunction(() => /Razem 10,0 s/.test(document.querySelector('#meter-text').textContent));
    await page.locator('#add-consent').check();
    const before = await page.evaluate(() => window.__hostCalls.length);
    await page.locator('#add-save').click();
    await page.waitForFunction((n) => window.__hostCalls.slice(n).some((c) => c.tool === 'voice_upload_begin'), before);
    await page.locator('#add-cancel').click();
    await sleep(3500);
    const tools = await page.evaluate((n) => window.__hostCalls.slice(n).map((c) => c.tool), before);
    check(!tools.includes('voice_upload_commit'), `no voice is committed after Anuluj (${tools.join(', ')})`);
    check(tools.includes('voice_upload_abort'), 'the open upload session is aborted');
    const names = await page.evaluate(async () => (await (await fetch('/call', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ tool: 'list_voices', input: {} }) })).json()).structuredContent.voices.map((v) => v.name));
    check(!names.includes('Anulowany'), 'the cancelled voice is not stored');
    check(problems.length === 0, `no console or page errors${problems.length ? ': ' + problems.join(' | ') : ''}`);
    await context.close();
  });

  await browser.close();
  bridge.child.kill();
  console.log(`\n${passed} checks passed, ${failures.length} failed`);
  if (failures.length) { console.log('\nFailures:\n - ' + failures.join('\n - ')); console.log('\nbridge log:\n' + bridge.log()); process.exit(1); }
  process.exit(0);
})().catch((e) => { console.error(e); process.exit(2); });
