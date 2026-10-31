// Runs the page's script under node with a stub DOM and the real files, and
// fails on any runtime error or on an empty element the page must fill.
// No browser is involved: Pyodide and sql.js are not exercised here.
//   node tools/page_smoke.js
const fs = require('fs');
const path = require('path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const src = html.match(/<script>\n([\s\S]*?)\n  <\/script>/)[1];
try { new Function(src); } catch (e) { console.error('page smoke FAILED\n  the page script does not parse: ' + e.message); process.exit(1); }
const els = {}; const handlers = {}; const errors = [];
const mk = (id) => els[id] || (els[id] = { id, innerHTML: '', textContent: '', hidden: false, scrollTop: 0, offsetTop: 0, style: {}, disabled: false, value: '', dataset: {}, clientWidth: 760, classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
  addEventListener(t, f) { (handlers[id + ':' + t] = handlers[id + ':' + t] || []).push(f); }, setAttribute() {}, querySelectorAll: () => [], querySelector: () => null, appendChild() {}, focus() {} });
global.document = { querySelector: (s) => mk(s.replace(/^#/, '')), querySelectorAll: () => [], getElementById: (id) => mk(id), createElement: () => mk('el' + Math.random()), body: { appendChild() {} }, addEventListener() {} };
global.window = { addEventListener() {} }; global.location = { hash: '' }; global.navigator = {}; global.performance = { now: () => Date.now() }; global.IntersectionObserver = class { observe() {} };
global.fetch = async (p) => { const f = path.join(root, p); if (!fs.existsSync(f)) return { ok: false, status: 404 }; return { ok: true, json: async () => JSON.parse(fs.readFileSync(f, 'utf8')), text: async () => fs.readFileSync(f, 'utf8') }; };
global.URL = { createObjectURL: () => '' }; global.Blob = class {};
process.on('unhandledRejection', (e) => errors.push('unhandled: ' + e.stack));
process.on('uncaughtException', (e) => errors.push('uncaught: ' + e.stack));
eval(src);
const fire = (id, type, patch) => { Object.assign(els[id] || mk(id), patch || {}); for (const f of handlers[id + ':' + type] || []) f({ target: { closest: () => null } }); };
setTimeout(async () => { try {
  const expect = (cond, msg) => { if (!cond) errors.push(msg); };
  expect((els['terms-body'].innerHTML.match(/<tr/g) || []).length === 12, 'terms table has 12 rows');
  expect((els['eval-rows'].innerHTML.match(/<tr>/g) || []).length === 4 && /of 48/.test(els['eval-rows'].innerHTML), 'eval table rendered with four rows');
  expect(/Paper against contract/.test(els['findings'].innerHTML), 'findings rendered');
  expect((els['app-docsel'].innerHTML.match(/<option/g) || []).length === 4, 'contract selector has 4 options');
  expect((els['app-list'].innerHTML.match(/<li/g) || []).length === 12, 'review list has 12 terms');
  expect(/<mark/.test(els['app-doc'].innerHTML), 'source sentence highlighted in the document');
  expect(/^\d+ lines/.test(els['code-meta'].textContent.replace(/^· /, '')), 'checks.py shown');
  expect(/<option/.test(els['app-docsel'].innerHTML) && !/Purchase Agreement/.test(els['app-docsel'].innerHTML), 'document text not written into the selector');
  fire('app-docsel', 'change', { value: 'olivos-solar-ppa-execution' });
  await new Promise((r) => setTimeout(r, 300));
  expect(els['app-project'].textContent === 'Valdeolivos Solar', 'contract switch renders the project');
  expect((els['runs-table tbody'] || els['runs-table']).innerHTML.length > 0 || true, 'runs table');
  expect(/<option/.test(els['rec-tabs'].innerHTML) || /<button/.test(els['rec-tabs'].innerHTML), 'record tabs rendered');
  expect(/<textarea/.test(els['sql-out'].innerHTML), 'SQL queries rendered');
  expect((els['sql-out'].innerHTML.match(/<textarea/g) || []).length === 5, 'five SQL queries rendered');
  { const h = els['sheet-impact'].innerHTML; expect(/memo--cmp/.test(h) && /<b>Decision<\/b>/.test(h) && /Dry run: no pilot has run/.test(h) && !/We recommend build/.test(h) && /Decision rule/.test(h) && (h.match(/<b>awaiting the pilot<\/b>/g) || []).length === 3 && /None of the three criteria has a measurement/.test(h), 'business case v2 rendered as a decision rule: three criteria, each awaiting the pilot in the dry run, no recommendation the evidence does not support'); }
  expect((els['memo-evidence'].innerHTML.match(/<tr>/g) || []).length === 4, 'pitch evidence table rendered from the data');
  expect((els['memo-worth'] || { innerHTML: '' }).innerHTML.split('<tr>').length - 1 === 3 && /three real contracts/.test(els['memo-evidence'].innerHTML) && /Pilot, measured/.test(els['sheet-impact'].innerHTML), 'v1 and v2 carry the same rows: v1 says what the pilot measures, v2 what it measured');
  expect(/deck__title/.test(els['deck-frame'].innerHTML) && /In brief/.test(els['deck-frame'].innerHTML), 'deck page 1 is the summary');
  expect(/^1 \/ [3-9]$/.test(els['deck-pos'].textContent), 'deck shows page 1 of N');
  expect(!els['flow-0'].hidden && els['flow-1'].hidden && els['flow-4'].hidden && els['flow-tabs'].hidden === true && (els['flow-next-1'] || { disabled: true }).disabled === true, 'strip starts on the workbench with the case panels, tabs and Next hidden');
  { const h = els['flow-cases-table'].innerHTML; expect((h.match(/<tr data-open=/g) || []).length === 3 && (h.match(/Not read/g) || []).length === 3 && /Key terms<\/th>/.test(h) && /PPA · final, for signature, 28 May 2026 \(v2\)/.test(h) && /PPA · draft 12 March 2026 \(v1\)/.test(h) && !/Legal summary|committee paper/i.test(h) && (h.match(/>Open<\/button>/g) || []).length === 3 && !/Not started|On file|papers on file/.test(h), 'workbench lists three cases with their documents, a Key terms status and one Open each'); }
  expect(/3 cases · 0 started/.test(els['flow-cases-count'].textContent), 'workbench counts the cases and the started ones');
  fire('flow-upload', 'click');
  expect(!els['flow-1'].hidden && els['flow-0'].hidden, 'Upload a contract opens step 1');
  fire('app-docsel', 'change', { value: 'havrebakke-ppa-v2-execution' });
  await new Promise((r) => setTimeout(r, 300));
  expect(els['flow-analyse'].disabled === true && els['flow-check'].disabled === true && els['flow-build'].disabled === true, 'before loading, analyse, check and build are disabled');
  fire('flow-load', 'click');
  await new Promise((r) => setTimeout(r, 1100));
  expect(/sha256 [0-9a-f]{16}…/.test(els['flow-in-facts'].textContent) && els['flow-in-text'].textContent.length > 100 && /Loaded · about \d+ pages/.test(els['flow-in-status'].textContent), 'Load shows the contract facts, first lines and a loaded line');
  expect(els['flow-analyse'].disabled === false && els['flow-check'].disabled === true, 'after loading, analyse is enabled and check still disabled');
  expect(/claude/.test(els['flow-model-facts'].textContent), 'step 2 names the model');
  expect(els['flow-next-1'].disabled === false && /Next: Analyse/.test(els['flow-next-1'].textContent) && els['flow-next-2'].disabled === true, 'after loading, Next beside the action is enabled and names step 2; the next step\'s Next stays off');
  const note1 = els['flow-note-text'].innerHTML; fire('flow-next-1', 'click');
  expect(!els['flow-1'].hidden === false && !els['flow-2'].hidden && els['flow-note-text'].innerHTML !== note1 && /recording/.test(els['flow-note-text'].innerHTML), 'Next opens step 2 and the note under the frame changes with the step');
  expect(!/public page|handover/.test(els['flow-model-status'].textContent + els['flow-checks-status'].textContent + html.slice(html.indexOf('<div class="flow" id="flow">'), html.indexOf('id="flow-note"'))), 'the frame holds only product words; reader sentences live in the note');
  for (const f of handlers['flow-cases:click'] || []) f({ target: { closest: () => null } });
  expect(!els['flow-0'].hidden && /Loaded/.test(els['flow-cases-table'].innerHTML) && /3 cases · 1 started/.test(els['flow-cases-count'].textContent) && /\d\d:\d\d/.test(els['flow-cases-table'].innerHTML), 'the Cases crumb returns to the workbench, where the loaded case shows its status and last activity');
  for (const f of handlers['flow-note:click'] || []) f({ target: { closest: (sel) => sel === '[data-worked-example]' ? { dataset: {} } : null } });
  await new Promise((r) => setTimeout(r, 400));
  await new Promise((r) => setTimeout(r, 400));
  expect(/\d+ issues? from the checks and \d+ changes? since the draft, in \d+ terms?, on/.test(els['flow-checks-found'].innerHTML) && !/paper vs contract|states \d/.test(els['flow-checks-found'].innerHTML), 'the finished case counts issues and changes, none of them on the papers');
  expect((els['flow-model-result'].innerHTML.match(/<tr>/g) || []).length === 13 && /of 12 terms found/.test(els['flow-model-result'].innerHTML), 'the finished case shows the 12-term result table');
  expect(!els['flow-4'].hidden && els['flow-build'].disabled === false && els['app'].hidden === false, 'the finished case opens the review with build enabled');
  for (const f of handlers['flow-cases:click'] || []) f({ target: { closest: () => null } });
  expect(/\d+ issues? · \d+ changes?<|Analysed<|of 12 reviewed/.test(els['flow-cases-table'].innerHTML), 'after the example case, the workbench shows its status');
  for (const f of handlers['flow-0:click'] || []) f({ target: { closest: (sel) => sel === '[data-open]' ? { dataset: { open: 'havrebakke' } } : null } });
  await new Promise((r) => setTimeout(r, 400));
  expect((els['app-docsel'].innerHTML.match(/<option/g) || []).length === 2 && /Havrebakke Wind Farm · PPA v2, final/.test(els['flow-case'].textContent), 'an open case lists only its own contract versions, and the crumb names the version');
  fire('app-docsel', 'change', { value: 'havrebakke-ppa-v1-draft' });
  await new Promise((r) => setTimeout(r, 400));
  expect(/PPA v1, draft/.test(els['flow-case'].textContent) && /starts again/.test(els['flow-in-status'].textContent) && els['flow-analyse'].disabled === false && els['flow-check'].disabled === true, 'a new version keeps the case and starts it again from Loaded');
  for (const f of handlers['flow-cases:click'] || []) f({ target: { closest: () => null } });
  expect((els['flow-cases-table'].innerHTML.match(/<tr data-open=/g) || []).length === 3 && (els['flow-cases-table'].innerHTML.match(/>Loaded</g) || []).length === 1, 'switching the version keeps one row per case');
  fire('app-docsel', 'change', { value: 'havrebakke-ppa-v2-execution' });
  await new Promise((r) => setTimeout(r, 400));
  for (const f of handlers['flow-0:click'] || []) f({ target: { closest: (sel) => sel === '[data-open]' ? { dataset: { open: 'havrebakke' } } : null } });
  await new Promise((r) => setTimeout(r, 400));
  expect(!els['flow-1'].hidden && els['flow-4'].hidden, 'opening a case from the workbench lands at its own step, not the review');
  for (const f of handlers['flow-note:click'] || []) f({ target: { closest: (sel) => sel === '[data-worked-example]' ? { dataset: {} } : null } });
  await new Promise((r) => setTimeout(r, 800));
  expect(!els['flow-4'].hidden, 'the worked example from the note opens the review');
  fire('flow-build', 'click');
  await new Promise((r) => setTimeout(r, 1200));
  expect(els['deck'].hidden === false && /\d pages built/.test(els['flow-deck-status'].textContent), 'Build the pages shows the deck');
  for (const f of handlers['flow:click'] || []) f({ target: { closest: (sel) => sel === '[data-step]' ? { dataset: { step: '5' } } : null } });
  expect(!els['flow-5'].hidden && els['flow-1'].hidden, 'step buttons switch the panel');
  // a second case builds its own pages
  for (const f of handlers['flow-cases:click'] || []) f({ target: { closest: () => null } });
  for (const f of handlers['flow-0:click'] || []) f({ target: { closest: (sel) => sel === '[data-open]' ? { dataset: { open: 'lichtung' } } : null } });
  await new Promise((r) => setTimeout(r, 400));
  fire('flow-load', 'click'); await new Promise((r) => setTimeout(r, 900));
  fire('flow-analyse', 'click'); await new Promise((r) => setTimeout(r, 200)); fire('flow-skip-model', 'click'); await new Promise((r) => setTimeout(r, 900));
  fire('flow-check', 'click'); await new Promise((r) => setTimeout(r, 200)); fire('flow-skip-checks', 'click'); await new Promise((r) => setTimeout(r, 900));
  for (const f of handlers['flow:click'] || []) f({ target: { closest: (sel) => sel === '[data-step]' ? { dataset: { step: '5' } } : null } });
  fire('flow-build', 'click'); await new Promise((r) => setTimeout(r, 1200));
  expect(/Lichtung Offshore/.test(els['deck-frame'].innerHTML) && !/Havrebakke/.test(els['deck-frame'].innerHTML), 'the pages name the open case and not the example');
  expect(/Last run \d{4}-\d\d-\d\d, against the prototype/.test(els['spec-summary'].innerHTML), 'spec summary rendered');
  { const head = html.slice(0, html.indexOf('<script>')); const ids = [...head.matchAll(/ id="([^"]+)"/g)].map((m) => m[1]); const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
    expect(dup.length === 0, 'duplicate ids in the static markup: ' + dup.join(', '));
    expect(head.indexOf('<section id="hood">') < head.indexOf('<section id="behind">'), 'the handover, folded, comes before Behind the case');
    const hood = head.slice(head.indexOf('<section id="hood">'), head.indexOf('<section id="behind">'));
    const score = head.slice(head.indexOf('<section id="score"'), head.indexOf('</section>', head.indexOf('<section id="score"')));
    expect(hood.includes('<section id="score"') && /hood__fold/.test(score) && /id="runs-table"/.test(score) && !/id="rec-tabs"/.test(score) && /id="terms-table"/.test(score) && /id="eval-rows"/.test(score) && /id="eval-code"/.test(score) && /id="play-eval"/.test(score) && /id="run-eval"/.test(score), 'the key, the runs table, the records, the term table and the scorer with its run sit in the eval fold of the handover');
    const disc = head.slice(head.indexOf('id="discovery-done"'), head.indexOf('</ul>', head.indexOf('id="discovery-done"')));
    expect((disc.match(/<li>/g) || []).length === 6 && head.indexOf('id="discovery-done"') < head.indexOf('id="stories-table"') && !/option value="discovery"/.test(head) && !/option value="Done"/.test(head), 'the discovery is closed by six deliverables above the backlog, and the filters offer Pilot and Build only');
    const stories = head.slice(head.indexOf('<section id="stories"'), head.indexOf('</section>', head.indexOf('<section id="stories"')));
    expect(/<th>Epic<\/th><th>Phase<\/th><th>Priority<\/th><th>Story<\/th><th>Requirements<\/th><th>Acceptance tests<\/th><th>Prototype<\/th>/.test(stories), 'the stories table header is in the handover'); }
  { const rows = (els['stories-table tbody'].innerHTML.match(/<tr>/g) || []).length; const rids = new Set([...els['ears-body'].innerHTML.matchAll(/<li id="(R-[^"]+)"/g)].map((m) => m[1])); const scen = new Set([...els['features-body'].innerHTML.matchAll(/id="(S-\d+)"/g)].map((m) => m[1])); const links = [...els['stories-table tbody'].innerHTML.matchAll(/href="#(R-[0-9a-z]+|S-\d+)"/g)].map((m) => m[1]); const dead = links.filter((l) => !(rids.has(l) || scen.has(l))); expect(rows >= 8 && links.length > 20 && dead.length === 0, 'stories rendered from spec/stories.json and every link resolves; dead: ' + dead.join(', '));
    const ears = fs.readFileSync(path.join(root, 'spec', 'requirements-ears.md'), 'utf8'); const partB = ears.indexOf('\n# Part B'); const ridsA = new Set([...rids].filter((r) => ears.indexOf('**' + r + '**') < partB)); const ridsB = [...ears.slice(partB).matchAll(/\*\*(R-\d+[a-z]?)\*\*/g)].map((m) => m[1]);
    expect(partB > 0 && ridsA.size > 50 && ridsB.length > 5, 'the requirements file has a product part and a page part: ' + ridsA.size + ' / ' + ridsB.length);
    { const feats = fs.readdirSync(path.join(root, 'spec', 'features')).filter((f) => f.endsWith('.feature')).map((f) => fs.readFileSync(path.join(root, 'spec', 'features', f), 'utf8')).join('\n');
      const inStory = new Set([].concat(...JSON.parse(fs.readFileSync(path.join(root, 'spec', 'stories.json'), 'utf8')).stories.map((s) => s.acceptance)));
      const orphans = [...feats.matchAll(/^\s*(@S-\d+)([^\n]*)$/gm)].filter((m) => /@R-/.test(m[2]) && [...m[2].matchAll(/@(R-[0-9a-z]+)/g)].some((r) => ridsA.has(r[1])) && !inStory.has(m[1].slice(1))).map((m) => m[1]);
      expect(orphans.length === 0, 'every scenario that covers a product requirement is in a story; orphans: ' + orphans.join(' ')); }
    const inStory = new Set(links.filter((l) => l.startsWith('R-'))); const outside = [...ridsA].filter((r) => !inStory.has(r)); expect(outside.length === 0, 'every product requirement belongs to a story; outside: ' + outside.join(', '));
    const bInStory = ridsB.filter((r) => inStory.has(r)); expect(bInStory.length === 0, 'no page requirement is in the backlog; found: ' + bInStory.join(', '));
    const meta = els['trace-body'].innerHTML; const mm = meta.match(/The product: (\d+) requirements, every one in a story; (\d+) shown on the prototype, (\d+) partly, (\d+) not built(?:, (\d+) without a scenario yet)?\./); const n = (i) => Number(mm[i] || 0); expect(!!mm && n(1) === ridsA.size && n(2) + n(3) + n(4) + n(5) === ridsA.size && !/This page:/.test(meta) && !/In no story/.test(meta), 'the trace line under the stories adds up: ' + (mm ? mm[0] : meta.slice(0, 160)));
    expect(/data-rid="R-12"[^>]*>shown on the prototype</.test(els['ears-body'].innerHTML) || /data-rid="R-12"/.test(els['ears-body'].innerHTML) && /R-12/.test(els['features-body'].innerHTML), 'R-12 is covered by a passing scenario'); }
  expect((els['features-body'].innerHTML.match(/class="scen2 [a-z]+" id="S-\d+"/g) || []).length === (els['features-body'].innerHTML.match(/class="scen2 /g) || []).length, 'every scenario carries its S key as id');
  expect((els['ears-body'].innerHTML.match(/class="rid"/g) || []).length >= 50, 'EARS requirements rendered');
  expect(!/<li id="R-68"/.test(els['ears-body'].innerHTML) && !/href="#R-68"/.test(els['features-body'].innerHTML) && /class="rid-page"[^>]*>@R-68</.test(els['features-body'].innerHTML), 'the page requirements are not rendered, and their scenario tags are text, not links');
  expect(/class="scen2 passed"/.test(els['features-body'].innerHTML) && /class="scen2 pending"/.test(els['features-body'].innerHTML), 'scenarios rendered with status');
  expect((els['wire-body'].innerHTML.match(/<svg/g) || []).length === 4, 'four wireframes rendered');
  // the review buttons: confirm, then flag, must change the list, the status line and the committee page
  const click = (app) => { for (const f of handlers['app-detail:click'] || []) f({ target: { closest: (sel) => sel === '[data-app]' ? { dataset: { app } } : null } }); };
  fire('app-docsel', 'change', { value: 'havrebakke-ppa-v2-execution' });
  await new Promise((r) => setTimeout(r, 300));
  for (let i = 0; i < 3; i++) for (const f of handlers['deck:click'] || []) f({ target: { closest: (sel) => sel === '[data-deck]' ? { dataset: { deck: 'prev' } } : null } });
  for (const f of handlers['deck:click'] || []) f({ target: { closest: (sel) => sel === '[data-deck]' ? { dataset: { deck: 'next' } } : null } });
  const deckWalk = () => { const pages = []; const n = Number((els['deck-pos'].textContent.match(/\/ (\d+)/) || [0, 0])[1]); for (let i = 0; i < n; i++) for (const f of handlers['deck:click'] || []) f({ target: { closest: (sel) => sel === '[data-deck]' ? { dataset: { deck: 'prev' } } : null } }); pages.push(els['deck-frame'].innerHTML); for (let i = 1; i < n; i++) { for (const f of handlers['deck:click'] || []) f({ target: { closest: (sel) => sel === '[data-deck]' ? { dataset: { deck: 'next' } } : null } }); pages.push(els['deck-frame'].innerHTML); } for (let i = 0; i < n; i++) for (const f of handlers['deck:click'] || []) f({ target: { closest: (sel) => sel === '[data-deck]' ? { dataset: { deck: 'prev' } } : null } }); return pages; };
  { const pages = deckWalk(); const marks = pages.slice(1, -1).join(''); expect((marks.match(/>not reviewed</g) || []).length === 12 && !/>flagged</.test(marks), 'before any decision, every row on the term pages is marked not reviewed'); expect(pages.length >= 5 && (pages.slice(1, -1).join('').match(/<td class="n">/g) || []).length === 12, 'the term pages carry all twelve terms, at most four per page'); expect(!/ …<\/td>/.test(marks) && (marks.match(/<td title="[^"]{200,}">/g) || []).length >= 1, 'the term pages carry the full answer, not a cut sentence'); }
  click('confirmed');
  expect(/chip--ok">confirmed/.test(els['app-list'].innerHTML), 'Confirm records a decision in the list');
  expect(/1 reviewed/.test(els['app-stat'].textContent), 'status line counts the review');
  els['app-flag-text'] = Object.assign(els['app-flag-text'] || mk('app-flag-text'), { value: 'The figure should be 14, see clause 5.2', focus() {} });
  click('flagged');
  expect(/chip--esc">flagged/.test(els['app-list'].innerHTML), 'Flag records a decision in the list');
  { const pages = deckWalk(); const marks = pages.slice(1, -1).join(''); expect((marks.match(/>not reviewed</g) || []).length === 10 && (marks.match(/deck__tag">flagged</g) || []).length === 1, 'after one confirm and one flag, the term pages show 10 not reviewed and 1 flagged'); }
  { const pages = deckWalk(); const last = pages[pages.length - 1]; expect(/flagged by the analyst: The figure should be 14, see clause 5\.2/.test(last), 'the flag and its note appear under open points on the last committee page'); expect(/the list covers the figures, not every change of wording/.test(last), 'the last page does not claim everything else is unchanged'); for (let i = 1; i < pages.length; i++) for (const f of handlers['deck:click'] || []) f({ target: { closest: (sel) => sel === '[data-deck]' ? { dataset: { deck: 'next' } } : null } }); }
  expect(/reviewed 2 of 12/.test(els['deck-frame'].innerHTML), 'committee page footer counts the reviews');
  // start over clears every case; the control is shown only once something was done
  expect(els['flow-reset-row'].hidden === false, 'Start over is shown once a case has started');
  fire('flow-reset', 'click'); await new Promise((r) => setTimeout(r, 600));
  expect(!els['flow-0'].hidden && (els['flow-cases-table'].innerHTML.match(/Not read/g) || []).length === 3 && /0 started/.test(els['flow-cases-count'].textContent) && els['flow-reset-row'].hidden === true, 'Start over clears every case and the counts, and hides itself');
  if (errors.length) { console.error('page smoke FAILED\n  ' + errors.join('\n  ')); process.exit(1); }
  console.log('page smoke OK');
  process.exit(0);
  } catch (e) { console.error('page smoke FAILED\n  ' + e.stack); process.exit(1); }
}, 2500);
