// Appens logik uden browser: hvad der kan ses hvornår, for hvem. Kørsel: node --test app/tests/
const test = require("node:test");
const assert = require("node:assert/strict");
const core = require("../core.js");

const DATA = {
  world: { threshold: 5, channel_methods: { Telegram: "API", Pressemeddelelse: "E-mail", "Offentligt dokument": "Webscrape" }, mock_trends: { weeks: ["uge 45", "uge 46"], cards: { use: [{ title: "Andel taget", unit: "%", why: "Fordi brug.", values: [20, 30] }], quality: [{ title: "Andel fravalgt", unit: "%", why: "Fordi kvalitet.", values: [40, 30] }], effect: [{ title: "Minutter", unit: "min.", why: "Fordi effekt.", values: [15, 9] }] } }, users: { F: { vagtchef: "R. Kjær", journalist: "M. Holm" }, M: { vagtchef: "H. Bay", journalist: "K. Friis" }, E: { vagtchef: "T. Skaarup", journalist: "L. Winther" } }, weekday: "onsdag", window: { from: "06.00", to: "09.00" }, desks: [{ id: "F", name: "Formiddagsblad", rules: ["r1"] }, { id: "M", name: "Morgenavis", rules: [] }, { id: "E", name: "Erhvervsmedie", rules: [] }], fixed_considerations: [], scope: [] },
  docs: {
    D1: { id: "D1", time: "06.05", source_type: "Telegram", sender: "Bureau", title: "Varsel", text: "Varslet er hævet.", excerpt: "Varslet er hævet.", archive: false },
    D2: { id: "D2", time: "06.45", source_type: "Telegram", sender: "Bureau", title: "Beredskab frygter digebrud", text: "Beredskabet frygter digebrud.", excerpt: "Beredskabet frygter digebrud.", archive: false },
    D3: { id: "D3", time: "07.10", source_type: "Pressemeddelelse", sender: "Lotteri", title: "Gevinst ikke hentet", text: "42 mio.", excerpt: "42 mio.", archive: false },
    D4: { id: "D4", time: "06.31", source_type: "Offentligt dokument", sender: "Kommune", title: "Information om bygningsforhold", text: "Skolen lukker.", excerpt: "Information.", archive: false },
    D5: { id: "D5", time: "07.25", source_type: "Sociale medier", sender: "Profil", title: "Video", text: "Video.", excerpt: "Video.", archive: false },
    A1: { id: "A1", date: "2026-11-06", source_type: "Offentligt dokument", sender: "Kommune", title: "Dagsorden", text: "Tre påbud om diget.", excerpt: "Dagsorden.", archive: true },
  },
  coarse: {
    D1: { scores: { F: 9, M: 8, E: 4 }, why: { F: "rammer mange" }, unverified: false },
    D2: { scores: { F: 8, M: 7, E: 3 }, why: {}, unverified: false },
    D3: { scores: { F: 6, M: 2, E: 1 }, why: {}, unverified: false },
    D4: { scores: { F: 4, M: 4, E: 1 }, why: {}, unverified: false },
    D5: { scores: { F: 6, M: 3, E: 1 }, why: {}, unverified: true },
    A1: { scores: { F: 2, M: 3, E: 1 }, why: {}, unverified: false },
  },
  reads: {
    D1: { summary: "Varsel hævet", values: { F: { value: 9, why: "rammer mange" }, M: { value: 9 }, E: { value: 3 } } },
    D2: { summary: "Frygt for digebrud", values: { F: { value: 8 }, M: { value: 8 }, E: { value: 2 } } },
    D3: { summary: "Gevinst", values: { F: { value: 7 }, M: { value: 2 }, E: { value: 1 } } },
    D5: { summary: "Video", values: { F: { value: 6 }, M: { value: 2 }, E: { value: 1 } } },
  },
  groups: [
    { gid: "G01", label: "Stormflod", finds: ["D1", "D2"], first_time: "06.05", values: { F: 9, M: 9, E: 3 },
      facts: [{ no: 1, text: "Varslet er hævet.", quote: "Varslet er hævet", find: "D1", quote_ok: true },
              { no: 2, text: "Beredskabet frygter digebrud.", quote: "frygter digebrud", find: "D2", statement: true, speaker: "Beredskabet", quote_ok: true },
              { no: 3, text: "Tre påbud om diget.", quote: "Tre påbud om diget", find: "A1", via_link: "D2__A1", available_from: "06.46", accuses: "Kommunen", quote_ok: true }],
      links: [{ from: "D2", to: "A1", shared: "Nørrevang Strand", related: true, why: "Samme dige.", time: "06.46" }] },
    { gid: "G02", label: "Lotto", finds: ["D3"], first_time: "07.10", values: { F: 7, M: 2, E: 1 }, facts: [], links: [] },
    { gid: "G03", label: "Video", finds: ["D5"], first_time: "07.25", values: { F: 6, M: 2, E: 1 }, facts: [], links: [] },
  ],
  drafts: { F_G01: { angle: "Stormflod i nat", web: [{ s: "Varslet er hævet.", facts: [1], problems: [] }, { s: "Kommunen har fået tre påbud.", facts: [3], problems: [] }],
                     notification: { s: "Varslet er hævet.", facts: [1], problems: [], length: 17 }, audio: [{ s: "Varslet er hævet.", facts: [1], problems: [] }] } },
  actions: [
    { time: "06.12", desk: "F", who: "R. Kjær", action: "take", find: "D1", assign: "M. Holm", note: "Web ude 06.20" },
    { time: "06.50", desk: "F", who: "R. Kjær", action: "approve_link", find: "D2", to: "A1" },
    { time: "07.15", desk: "F", who: "R. Kjær", action: "take", find: "D3", assign: "S. Krag" },
    { time: "08.10", desk: "F", who: "M. Holm", action: "verify_reject", find: "D5", why: "Anden storm." },
    { time: "08.40", desk: "F", who: "S. Krag", action: "missing", find: "D4", why: "Skolen lukker." },
  ],
  eval: null, meta: { model: "m", run: 1 },
};

test("feedet viser kun det, der er kommet, nyeste først, delt ved grænsen", () => {
  const f = core.feed(DATA, "F", "06.50");
  assert.deepEqual(f.above.map((d) => d.id), ["D2", "D1"]);
  assert.deepEqual(f.below.map((d) => d.id), ["D4"]);
});

test("samme fund har et andet tal på en anden redaktion", () => {
  assert.deepEqual(core.feed(DATA, "E", "09.00").above.map((d) => d.id), []);
});

test("et forslag opstår med sit første fund og vokser, når flere kommer", () => {
  assert.deepEqual(core.proposals(DATA, "F", "06.10").map((p) => [p.gid, p.finds.length, p.value]), [["G01", 1, 9]]);
  assert.deepEqual(core.proposals(DATA, "F", "06.50").map((p) => [p.gid, p.finds.length]), [["G01", 2]]);
});

test("forslag står efter værdi, og under grænsen er de ikke forslag", () => {
  assert.deepEqual(core.proposals(DATA, "F", "09.00").map((p) => p.gid), ["G01", "G02"]);
  assert.deepEqual(core.proposals(DATA, "M", "09.00").map((p) => p.gid), ["G01"]);
  assert.deepEqual(core.proposals(DATA, "E", "09.00"), []);
});

test("ubekræftet materiale går til verifikation og er ikke et forslag", () => {
  assert.ok(!core.proposals(DATA, "F", "09.00").some((p) => p.gid === "G03"));
  assert.deepEqual(core.toVerify(DATA, "F", "07.30").map((d) => d.id), ["D5"]);
});

test("et faktum fra arkivet findes først, når sammenhængen er fundet, og er foreslået, til et menneske godkender", () => {
  assert.deepEqual(core.proposals(DATA, "F", "06.45")[0].facts.map((f) => f.no), [1, 2]);
  const at0647 = core.proposals(DATA, "F", "06.47")[0];
  assert.deepEqual(at0647.facts.map((f) => f.no), [1, 2, 3]);
  assert.equal(at0647.links[0].state, "foreslået");
  assert.equal(core.proposals(DATA, "F", "06.50")[0].links[0].state, "godkendt");
  assert.equal(core.proposals(DATA, "M", "09.00")[0].links[0].state, "foreslået");
});

test("status følger redaktionens handlinger op til klokkeslættet", () => {
  assert.equal(core.proposals(DATA, "F", "06.10")[0].status.kind, "foreslået");
  const taken = core.proposals(DATA, "F", "06.12")[0].status;
  assert.deepEqual([taken.kind, taken.assign, taken.note], ["taget", "M. Holm", "Web ude 06.20"]);
  assert.equal(core.proposals(DATA, "M", "09.00")[0].status.kind, "foreslået");
});

test("et forslag viser, hvilke andre redaktioner der også har det", () => {
  assert.deepEqual(core.proposals(DATA, "F", "09.00")[0].also, ["M"]);
  assert.deepEqual(core.proposals(DATA, "F", "09.00")[1].also, []);
});

test("tilbagemeldingen viser det, redaktionen selv har meldt, op til klokkeslættet", () => {
  assert.deepEqual(core.feedback(DATA, "F", "08.00").map((a) => a.action), []);
  assert.deepEqual(core.feedback(DATA, "F", "09.00").map((a) => a.action), ["verify_reject", "missing"]);
  assert.deepEqual(core.feedback(DATA, "M", "09.00"), []);
});

test("grænsens pris kan regnes: hvor mange fund læses ved en anden grænse", () => {
  assert.deepEqual(core.readAt(DATA, "F", 5), { read: 4, of: 5 });
  assert.deepEqual(core.readAt(DATA, "F", 4), { read: 5, of: 5 });
  assert.deepEqual(core.readAt(DATA, "F", 7), { read: 2, of: 5 });
});

test("et faktum, der lægger et ansvar på nogen, er ikke forelagt, før det er noteret", () => {
  const p = core.proposals(DATA, "F", "09.00")[0];
  assert.deepEqual(core.notPresented(p).map((f) => f.no), [3]);
});

test("hele appen kan tegnes for hver redaktion, rolle, visning og klokkeslæt uden fejl", () => {
  for (const desk of ["F", "M", "E"]) for (const role of ["vagtchef", "journalist"]) for (const view of ["prio", "udkast", "feedback", "kriterier", "kanaler", "maal"]) for (const t of ["06.00", "06.47", "09.00"]) {
    const html = core.renderApp(DATA, { desk, role, view, t, sel: "G01", doc: null, filter: "alle" });
    assert.ok(html.includes('class="top"') && html.includes('class="anav"'), `${desk} ${role} ${view} ${t}`);
    assert.ok(!html.includes("undefined") && !html.includes("NaN") && !html.includes("[object"), `${desk} ${role} ${view} ${t}`);
  }
});

test("kilden åbnes i fuld tekst med de steder, fakta bygger på", () => {
  const html = core.renderApp(DATA, { desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: "G01", doc: "A1", filter: "alle" });
  assert.ok(html.includes("<mark"));
  assert.ok(html.includes("Tre påbud om diget"));
});

test("tekst fra en kilde kan ikke blive til HTML", () => {
  const data = JSON.parse(JSON.stringify(DATA));
  data.docs.D1.title = "<img src=x onerror=alert(1)>";
  const html = core.renderApp(data, { desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: null, doc: null, filter: "alle" });
  assert.ok(!html.includes("<img src=x"));
});

test("journalisten ser 'Jeg tager den', vagtchefen 'Tag og tildel'", () => {
  const j = core.renderApp(DATA, { desk: "F", role: "journalist", view: "prio", t: "07.12", sel: null, doc: null, filter: "alle" });
  const v = core.renderApp(DATA, { desk: "F", role: "vagtchef", view: "prio", t: "07.12", sel: null, doc: null, filter: "alle" });
  assert.ok(j.includes("Jeg tager den") && !j.includes("Tag og tildel"));
  assert.ok(v.includes("Tag og tildel") && !v.includes("Jeg tager den"));
});

test("to citater, der overlapper i kilden, bliver begge markeret", () => {
  const data = JSON.parse(JSON.stringify(DATA));
  data.docs.D1.text = "Lukningen af fabrikken er et hårdt slag for 240 kolleger og for hele byen.";
  data.groups[0].facts = [
    { no: 6, text: "Fabrikken lukkes.", quote: "Lukningen af fabrikken", find: "D1", quote_ok: true },
    { no: 8, text: "Et hårdt slag.", quote: "Lukningen af fabrikken er et hårdt slag for 240 kolleger", find: "D1", quote_ok: true },
    { no: 9, text: "Hele byen.", quote: "for hele byen", find: "D1", quote_ok: true },
  ];
  const html = core.renderApp(data, { desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: null, doc: "D1", filter: "alle" });
  const marks = [...html.matchAll(/<mark><b>([^<]*)<\/b>([^<]*)<\/mark>/g)].map((m) => [m[1], m[2]]);
  assert.deepEqual(marks, [["6, 8", "Lukningen af fabrikken er et hårdt slag for 240 kolleger"], ["9", "for hele byen"]]);
});

test("et citat med tegn, der skal omskrives i HTML, bliver stadig markeret", () => {
  const data = JSON.parse(JSON.stringify(DATA));
  data.docs.D1.text = 'Direktøren siger: "Vi står stærkt" & mere.';
  data.groups[0].facts = [{ no: 1, text: "Citat.", quote: '"Vi står stærkt" & mere', find: "D1", quote_ok: true }];
  const html = core.renderApp(data, { desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: null, doc: "D1", filter: "alle" });
  assert.ok(html.includes("<mark><b>1</b>&quot;Vi står stærkt&quot; &amp; mere</mark>"));
});

test("den, der er logget ind, står øverst med navn, rolle og redaktion", () => {
  const html = core.renderApp(DATA, { desk: "F", role: "journalist", view: "prio", t: "09.00", sel: null, doc: null, filter: "alle" });
  assert.ok(html.includes("M. Holm") && html.includes("Journalist") && html.includes(">MH<"));
  assert.equal(core.user(DATA, "E", "vagtchef"), "T. Skaarup");
});

test("journalisten ser sine egne og de ledige forslag; kollegers står som et antal", () => {
  const mine = core.visibleTo(DATA, core.proposals(DATA, "F", "09.00"), "F", "journalist");
  assert.deepEqual(mine.shown.map((p) => p.gid), ["G01"]);
  assert.equal(mine.hidden, 1);
  const all = core.visibleTo(DATA, core.proposals(DATA, "F", "09.00"), "F", "vagtchef");
  assert.deepEqual([all.shown.length, all.hidden], [2, 0]);
});

test("journalistens eget forslag er mærket som hendes", () => {
  const html = core.renderApp(DATA, { desk: "F", role: "journalist", view: "prio", t: "09.00", sel: null, doc: null, filter: "alle" });
  assert.ok(html.includes("M. Holm (mig)"));
  assert.ok(html.includes("1 forslag er taget af kolleger"));
});

test("hver knap uden funktion siger det og fortæller, hvad den ville gøre i drift", () => {
  let seen = 0;
  for (const desk of ["F", "M", "E"]) for (const role of ["vagtchef", "journalist"]) for (const view of ["prio", "udkast", "kriterier"]) for (const t of ["07.12", "09.00"]) {
    const html = core.renderApp(DATA, { desk, role, view, t, sel: "G01", doc: null, filter: "alle" });
    for (const m of html.matchAll(/<span[^>]*data-act="noop"[^>]*>/g)) {
      seen += 1;
      assert.match(m[0], /title="Virker ikke i prototypen\. I drift: [^"]{15,}"/, m[0]);
      assert.match(m[0], /class="[^"]*\bnoop\b/, m[0]);
    }
  }
  assert.ok(seen > 10);
});

test("den, der ikke er forelagt, kan i drift mærkes som forelagt eller med svar", () => {
  const html = core.renderApp(DATA, { desk: "F", role: "journalist", view: "prio", t: "09.00", sel: "G01", doc: null, filter: "alle" });
  assert.ok(html.includes("Markér som forelagt") && html.includes("Svar indhentet"));
});

test("Kildekanaler og Mål kan åbnes som mock-up: de siger tydeligt, at de er det, og intet i dem kan ændres", () => {
  for (const [view, name] of [["kanaler", "Kildekanaler"], ["maal", "Mål"]]) {
    const html = draw(DATA, { view });
    assert.match(html, new RegExp(`data-act="view" data-id="${view}">${name} <small>mock-up</small>`));
    assert.match(html, /<div class="mock"><b>Mock-up\.<\/b> [^<]{40,}<\/div>/);
    const body = html.slice(html.indexOf('<div class="main mockview">'));
    const acts = [...body.matchAll(/data-act="([a-z]+)"/g)].map((m) => m[1]);
    assert.ok(acts.length > 0 && acts.every((a) => a === "noop"), view + ": " + acts.join(","));
  }
  assert.ok(draw(DATA, {}).includes("Opsætning") && draw(DATA, {}).includes("Opfølgning"));
});

test("kildekanalerne er regnet fra morgenens kildemateriale: hvor meget hver har givet, hvornår sidst, og hvor meget der nåede grænsen", () => {
  assert.deepEqual(core.channels(DATA, "F", "09.00"), [
    { name: "Bureau", type: "Telegram", method: "API", count: 2, last: "06.45", above: 2 },
    { name: "Kommune", type: "Offentligt dokument", method: "Webscrape", count: 1, last: "06.31", above: 0 },
    { name: "Lotteri", type: "Pressemeddelelse", method: "E-mail", count: 1, last: "07.10", above: 1 },
    { name: "Profil", type: "Sociale medier", method: "", count: 1, last: "07.25", above: 1 },
  ]);
  assert.deepEqual(core.channels(DATA, "F", "06.10").map((c) => [c.name, c.count]), [["Bureau", 1]]);
});

test("dagens mål er regnet fra redaktionens handlinger: anvendelse, kvalitet og effekt", () => {
  assert.deepEqual(core.goals(DATA, "F", "09.00"), { users: 3, taken: 2, proposals: 2, dismissed: 0, missing: 1, published: 1, minutes: 6 });
  assert.deepEqual(core.goals(DATA, "E", "09.00"), { users: 0, taken: 0, proposals: 0, dismissed: 0, missing: 0, published: 0, minutes: null });
});

test("mærkerne på et faktum siger, hvem der taler, hvem ansvaret lægges på, og hvad mærket betyder", () => {
  const html = core.renderApp(DATA, { desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: "G01", doc: null, filter: "alle" });
  assert.match(html, /title="[^"]*tilskrives[^"]*">Udsagn: Beredskabet</);
  assert.match(html, /title="[^"]*ikke er blevet spurgt[^"]*">Ikke forelagt: Kommunen</);
});

const copy = () => JSON.parse(JSON.stringify(DATA));
const draftOf = (angle) => ({ angle, web: [{ s: "Tekst.", facts: [], problems: [] }], notification: { s: "Tekst.", facts: [], problems: [], length: 6 }, audio: [] });
const draw = (data, over) => core.renderApp(data, Object.assign({ desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: null, doc: null, filter: "alle" }, over));

test("udkastet, der åbnes uden valg, hører til det forslag, højre rude viser, også når det øverste er fravalgt", () => {
  const data = copy();
  data.drafts.F_G02 = draftOf("Lotto-udkast");
  data.actions.push({ time: "06.20", desk: "F", who: "R. Kjær", action: "dismiss", find: "D1", why: "Ikke for os." });
  assert.ok(draw(data, {}).includes('<div class="dt">Lotto-udkast</div>'));
  const html = draw(data, { view: "udkast" });
  assert.ok(html.includes("<h3>Lotto-udkast</h3>"));
  assert.match(html, /data-id="udkast">Udkast <small>1<\/small>/);
});

test("udkastskærmen viser de andre udkast, så tallet i menuen kan findes", () => {
  const data = copy();
  data.drafts.F_G02 = draftOf("Lotto-udkast");
  const html = draw(data, { view: "udkast", sel: "G01" });
  assert.match(html, /data-act="sel" data-id="G02"><span>Lotto-udkast/);
});

test("et arkivdokument, som to fund i samme forslag peger på, står én gang og tæller én gang", () => {
  const data = copy();
  data.groups[0].links.unshift({ from: "D1", to: "A1", shared: "diget", related: true, why: "Tidlig.", time: "06.06" });
  const html = draw(data, { sel: "G01" });
  assert.ok(html.includes("+ 1 fra arkivet"));
  assert.equal(html.split('<div class="kv"><span>Dagsorden</span>').length - 1, 1);
  assert.ok(html.includes("godkendt af R. Kjær 06.50"));
});

test("andre redaktioner står med navn, ikke bogstav", () => {
  assert.ok(draw(DATA, {}).includes("Også hos Morgenavis"));
  assert.ok(draw(DATA, { doc: "D1" }).includes("Groft tal for Formiddagsblad"));
});

test("materiale, der er afvist ved verifikation, står ikke længere som til verifikation", () => {
  assert.ok(draw(DATA, { t: "07.30" }).includes("Til verifikation"));
  const html = draw(DATA, { t: "09.00" });
  assert.ok(!html.includes("Til verifikation"));
  assert.ok(html.includes("Afvist ved verifikation"));
});

test("tilbagemeldingen siger, at klokkeslættet er, hvornår der blev meldt", () => {
  assert.ok(draw(DATA, { view: "feedback" }).includes("meldt 08.40"));
});

test("alle fund under grænsen står i listen", () => {
  const data = copy();
  for (let i = 0; i < 45; i += 1) {
    data.docs["N" + i] = { id: "N" + i, time: "06.30", source_type: "Telegram", sender: "Bureau", title: "Rutine " + i, text: "x", excerpt: "x", archive: false };
    data.coarse["N" + i] = { scores: { F: 1, M: 1, E: 1 }, why: {}, unverified: false };
  }
  const html = draw(data, {});
  for (let i = 0; i < 45; i += 1) assert.ok(html.includes(">Rutine " + i + "<"), "Rutine " + i);
});

test("kilden viser forslaget med samme titel som listen", () => {
  assert.match(draw(DATA, { doc: "D1" }), /data-act="sel" data-id="G01"><span>Stormflod i nat<\/span>/);
});

test("testens samlede tal regnes fra kørslen: fundne og oversete historier og forslag, der ikke var historier", () => {
  const data = copy();
  data.eval = { desks: { F: { found: ["E1", "E2"], missed: [{ event: "E3" }], noise: [{}], proposals: [{}, {}, {}] }, M: { found: ["E1"], missed: [], noise: [], proposals: [{}] } } };
  assert.equal(core.resultLine(data), "Tilsammen skulle redaktionerne have haft 4 historier foreslået. Sprogmodellen fandt 3 af dem og overså 1. Den foreslog også 1, som ikke var en historie.");
  assert.equal(core.resultLine(DATA), "");
});

test("en genvej fra siden sætter appen i den tilstand, den lover", () => {
  const s = { desk: "M", role: "journalist", view: "kriterier", t: "07.00", sel: "G02", doc: null, filter: "alle" };
  assert.deepEqual(core.go(DATA, s, "desk=F&doc=D4"), { desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: null, doc: "D4", filter: "alle", mark: null, spot: true, cue: null });
  assert.deepEqual(core.go(DATA, s, "desk=E"), { desk: "E", role: "vagtchef", view: "prio", t: "09.00", sel: null, doc: null, filter: "alle", mark: null, spot: true, cue: null });
  assert.equal(core.go(DATA, s, "desk=F&view=udkast").view, "udkast");
  assert.equal(core.go(DATA, s, "desk=F&sel=G01").sel, "G01");
  assert.equal(core.go(DATA, s, "desk=F&play=1").t, "06.00");
});

test("i udkastet fører hvert faktum og hvert tal efter en sætning til kilden", () => {
  const html = draw(DATA, { view: "udkast", sel: "G01" });
  assert.match(html, /<div class="fact"><span class="no">1<\/span><span class="ft">Varslet er hævet\. <span class="chip src" data-act="doc" data-id="D1"[^>]*>Bureau<\/span>/);
  assert.match(html, /<sup><span data-act="doc" data-id="A1" title="[^"]*Dagsorden[^"]*">3<\/span><\/sup>/);
});

test("sammenhængen med arkivet står over faktalisten, så den ses uden at rulle", () => {
  const html = draw(DATA, { sel: "G01" });
  assert.ok(html.indexOf("Sammenhæng med arkivet") > 0);
  assert.ok(html.indexOf("Sammenhæng med arkivet") < html.indexOf("Fakta og kilder"));
});

test("rækken for det forslag, højre rude viser, er markeret, også før man har klikket", () => {
  assert.match(draw(DATA, { sel: null }), /<tr class="sel\s*" data-act="sel" data-id="G01">/);
});

test("hvor og hvornår en historie udgives, vælges i listen: kolonnen hedder Udgivelse og har en knap i hver række", () => {
  const proposed = draw(DATA, { desk: "M", sel: "G01" });
  assert.ok(proposed.includes(">Udgivelse</th>") && !proposed.includes(">Kanaler</th>"));
  assert.match(proposed, /<td><span class="asg noop" data-act="noop" title="Virker ikke i prototypen\. I drift: [^"]*web, app[^"]*">Vælg udgivelse ▾<\/span><\/td><\/tr>/);
  const taken = draw(DATA, { sel: "G01" });
  assert.match(taken, /<td>Web ude 06\.20 <span class="asg noop" data-act="noop" title="[^"]*">Ret ▾<\/span><\/td><\/tr>/);
  assert.match(taken, /<h4>Tildeling og udgivelse<\/h4>[\s\S]*M\. Holm[\s\S]*Web ude 06\.20[\s\S]*Ret tildeling/);
});

test("grunden til et fravalg står ved forslaget, ikke i kolonnen Udgivelse", () => {
  const data = copy();
  data.actions.push({ time: "07.20", desk: "F", who: "R. Kjær", action: "dismiss", find: "D3", why: "Ikke en historie." });
  const row = draw(data, {}).match(/<tr class="[^"]*off[^"]*" data-act="sel" data-id="G02">.*?<\/tr>/s)[0];
  assert.match(row, /<div class="small">Fravalgt af R\. Kjær kl\. 07\.20: Ikke en historie\.<\/div><\/td>/);
  assert.match(row, /<td>–<\/td><td>–<\/td><\/tr>$/);
});

test("det, der kommer ind, hedder kildemateriale og tælles som kilder; ordet fund bruges ikke", () => {
  for (const view of ["prio", "udkast", "feedback", "kriterier"]) for (const doc of [null, "D1"]) {
    assert.ok(!/\bfund\b/i.test(draw(DATA, { view, doc, sel: "G01" })), view);
  }
  const html = draw(DATA, { sel: "G01" });
  assert.ok(html.includes("<b>Kildemateriale</b>"));
  assert.ok(html.includes("2 kilder samlet") && html.includes(">1 kilde<"));
});

test("under reglerne står synligt, at en ændring prøves, før den gælder", () => {
  const data = copy();
  data.world.rules_note = "Reglerne er antagelser.";
  const html = draw(data, { view: "kriterier" });
  assert.match(html, /<p class="muted">Reglerne er antagelser\.<\/p><p class="notice"><b>En ændring af en regel gælder ikke med det samme\.<\/b>[^<]*eval-suite[^<]*godkendes af redaktionen og platformejeren, før den gælder\.<\/p>/);
});

test("tilbagemeldingsskærmen siger det samme som siden: meldinger bruges til konfigurering eller udvikling og prøves først", () => {
  const html = draw(DATA, { view: "feedback" });
  assert.ok(html.includes("Konfigurering:") && html.includes("Udvikling:") && html.includes("eval-suite"));
  assert.ok(!/facit|filteret|flytter de rangeringen/.test(html));
});

test("på en smal skærm skaleres appen ned til den plads, der er; på en bred står den i fuld størrelse", () => {
  assert.equal(core.fitScale(1400, 1200), 1);
  assert.equal(core.fitScale(1200, 1200), 1);
  assert.equal(core.fitScale(600, 1200), 0.5);
  assert.equal(core.fitScale(0, 1200), 1);
});

test("kildekanalerne viser to typer: materialetype og kildetype", () => {
  const html = draw(DATA, { view: "kanaler" });
  assert.ok(html.includes("<th>Materialetype</th><th>Kildetype</th>"));
  assert.match(html, /<td><b>Bureau<\/b><\/td><td><span class="chip src">Telegram<\/span><\/td><td><span class="chip also">API<\/span><\/td>/);
});

test("udkastet viser for hver udgave, hvor og hvornår den udgives, som i listen", () => {
  assert.deepEqual(core.outlets("Web ude 06.20 · app 06.21"), { web: "ude 06.20", app: "06.21" });
  assert.deepEqual(core.outlets(""), {});
  const data = copy();
  data.actions[0].note = "Web ude 06.20 · app 06.21";
  const html = draw(data, { view: "udkast", sel: "G01" });
  assert.match(html, /<h3>Kort tekst <small>udkast til journalisten<\/small><span class="chip link out">Web: ude 06\.20<\/span>/);
  assert.match(html, /<h3>Notifikation <small>\d+ tegn<\/small><span class="chip link out">App: 06\.21<\/span>/);
  assert.match(html, /<h3>Lydmanuskript<span class="chip src out">Ikke valgt til udgivelse<\/span>/);
  assert.match(html, /<span>Udgivelse<\/span><b>Web ude 06\.20 · app 06\.21<\/b>/);
});

test("mål-skærmen har en kurve pr. mål, mærket som eksempeltal, med værdien ved hvert punkt", () => {
  const html = draw(DATA, { view: "maal" });
  assert.equal(html.split("<svg").length - 1, 3);
  assert.equal(html.split("Eksempeltal, ikke målt").length - 1, 3);
  assert.ok(html.includes("<title>uge 46: 30 %</title>") && html.includes("<title>uge 46: 9 min.</title>"));
  assert.equal(html.split('<p class="why">').length - 1, 3);
  assert.ok(html.includes('<p class="why">Fordi kvalitet.</p>'));
  assert.ok(html.includes("Mål, der kræver mere end prototypen"));
});

test("hvert mål har en linje om, hvorfor det følges", () => {
  const html = draw(DATA, { view: "maal" });
  assert.equal(html.split('<p class="desc">').length - 1, 4);
  assert.ok(html.includes("En stigende andel fravalg viser ofte, at modellen er skredet, før en formel test gør det."));
});

test("Kriterier er også en mock-up og siger det", () => {
  const html = draw(DATA, { view: "kriterier" });
  assert.match(html, /data-act="view" data-id="kriterier">Kriterier <small>mock-up<\/small>/);
  assert.match(html, /<div class="mock"><b>Mock-up\.<\/b> [^<]{40,}<\/div>/);
});

test("man kan se, hvor en tilbagemelding gives: ved forslaget, ved sammenhængen og ved kilden", () => {
  const prio = draw(DATA, { desk: "M", sel: "G01" });
  assert.match(prio, /title="Virker ikke i prototypen\. I drift: [^"]*Tilbagemelding[^"]*">Fravælg: ikke en historie<\/span>/);
  assert.match(prio, /title="Virker ikke i prototypen\. I drift: [^"]*">Forkert sammenhæng<\/span>/);
  const doc = draw(DATA, { doc: "D4" });
  assert.match(doc, /<h4>Giv en tilbagemelding<\/h4>[\s\S]*title="Virker ikke i prototypen\. I drift: [^"]*">Den manglede som forslag<\/span>/);
  assert.match(draw(DATA, { doc: "D5", t: "07.30" }), /">Afvis ved verifikation<\/span>/);
  assert.ok(draw(DATA, { view: "feedback" }).includes("<h4>Sådan gives en tilbagemelding</h4>"));
});

test("knapperne til eksemplerne farver de meldinger, de fører hen til", () => {
  const s = core.go(DATA, { desk: "M", role: "journalist", view: "prio", t: "07.00", sel: null, doc: null }, "desk=F&view=feedback&mark=D4");
  assert.deepEqual(s.mark, ["D4"]);
  const html = core.renderApp(DATA, s);
  assert.match(html, /<div class="fi hl" data-act="doc" data-id="D4">/);
  assert.match(html, /<div class="fi" data-act="doc" data-id="D5">/);
  assert.equal(core.go(DATA, s, "desk=F").mark, null);
});

test("når redaktionerne vises efter tur, er den aktuelle redaktion og dens liste fremhævet", () => {
  const on = draw(DATA, { desk: "M", flash: true });
  assert.match(on, /<span class="on pulse" data-act="desk" data-id="M">Morgenavis<\/span>/);
  assert.ok(on.includes('<div class="pane prio pulse">'));
  const off = draw(DATA, { desk: "M" });
  assert.ok(!off.includes("pulse"));
});

test("en genvej fra siden fremhæver det sted, den fører hen til: forslaget, udkastet eller meldingen", () => {
  const base = { desk: "M", role: "journalist", view: "prio", t: "07.00", sel: null, doc: null };
  const prop = core.renderApp(DATA, core.go(DATA, base, "desk=F&sel=G01"));
  assert.match(prop, /<tr class="sel spot\s*" data-act="sel" data-id="G01">/);
  assert.ok(prop.includes('<div class="pane det spot">'));
  assert.ok(core.renderApp(DATA, core.go(DATA, base, "desk=F&view=udkast")).includes('<div class="card tall spot">'));
  assert.ok(!draw(DATA, { sel: "G01" }).includes("spot"));
  assert.equal(core.go(DATA, base, "desk=F&play=1").spot, false);
  assert.equal(core.go(DATA, base, "desk=F&cycle=1").spot, false);
});

test("på vej til udkastet fremhæves knappen Åbn udkast i det valgte forslag", () => {
  assert.match(draw(DATA, { sel: "G01", cue: "draft" }), /<span class="b p cue" data-act="view" data-id="udkast">Åbn udkast<\/span>/);
  assert.ok(!draw(DATA, { sel: "G01" }).includes(" cue"));
});

test("genvejen til et forslag fremhæver også sammenhængen med arkivet", () => {
  const base = { desk: "M", role: "journalist", view: "prio", t: "07.00", sel: null, doc: null };
  assert.ok(core.renderApp(DATA, core.go(DATA, base, "desk=F&sel=G01")).includes('<div class="dsec arch spot">'));
  assert.ok(draw(DATA, { sel: "G01" }).includes('<div class="dsec arch">'));
});

test("drift og omkostning viser kun kurver; sprogmodel og udgave af instruksen er et filter øverst", () => {
  const data = copy();
  data.meta = { model: "model-x", prompt_version: 2 };
  data.world.mock_trends.cards.ops = [{ title: "Pris pr. dag", unit: "kr.", why: "Fordi pris.", values: [900, 700] }];
  const html = draw(data, { view: "maal" });
  const ops = html.slice(html.indexOf("<h3>Drift og omkostning"));
  const card = ops.slice(0, ops.indexOf("</div></div>"));
  assert.ok(!card.includes('class="kv"') && !html.includes("ikke målt i prototypen"));
  assert.match(html, /<div class="filter">Filter[\s\S]*title="Virker ikke i prototypen\. I drift: [^"]*">Sprogmodel: model-x ▾<\/span>[\s\S]*">Udgave af instruksen: 2 ▾<\/span>/);
  assert.ok(!draw(DATA, { view: "maal" }).includes("undefined"));
});

test("drift og omkostning har også kurver med eksempeltal: pris pr. taget forslag og svartid", () => {
  const data = copy();
  data.world.mock_trends.cards.ops = [{ title: "Pris", unit: "kr.", why: "Fordi pris.", values: [12, 8] }, { title: "Svartid", unit: "min.", why: "Fordi tid.", values: [6, 3] }];
  const html = draw(data, { view: "maal" });
  assert.equal(html.split("<svg").length - 1, 5);
  assert.ok(html.includes("<title>uge 46: 8 kr.</title>") && html.includes("<title>uge 46: 3 min.</title>"));
  assert.equal(html.split("Eksempeltal, ikke målt").length - 1, 5);
});

test("decimaltal i en kurve skrives med komma", () => {
  const data = copy();
  data.world.mock_trends.cards.ops = [{ title: "Kald pr. kilde", unit: "", why: "Fordi.", values: [1.9, 2.1] }];
  const html = draw(data, { view: "maal" });
  assert.ok(html.includes("<title>uge 46: 2,1 </title>") && !html.includes("2.1 "));
});

test("kurvens akse begynder ved nul, så et lille udsving ikke ligner et stort", () => {
  const data = copy();
  data.world.mock_trends.cards = { ops: [{ title: "Halv og hel", unit: "", why: "Fordi.", values: [10, 20] }] };
  const pts = draw(data, { view: "maal" }).match(/<polyline points="([^"]+)"/)[1].split(" ");
  assert.equal(pts[0].split(",")[1], "43.0");
  assert.equal(pts[1].split(",")[1], "12.0");
});

test("vejen tilbage til teksten vises kun, når knappen, læseren trykkede på, er ude af syne", () => {
  assert.equal(core.outOfView({ top: -300, bottom: -260 }, 800), true);
  assert.equal(core.outOfView({ top: 900, bottom: 940 }, 800), true);
  assert.equal(core.outOfView({ top: 200, bottom: 240 }, 800), false);
});

test("tallene går op: forslag om en historie, der allerede er foreslået, tælles for sig", () => {
  const data = copy();
  data.eval = { desks: { F: { found: ["E1", "E2"], missed: [{ event: "E3" }], noise: [{}], proposals: [{}, {}, {}, {}, {}] } } };
  assert.equal(core.resultLine(data), "Tilsammen skulle redaktionerne have haft 3 historier foreslået. Sprogmodellen fandt 2 af dem og overså 1. Den foreslog også 1, som ikke var en historie. 2 forslag handlede om en historie, der allerede var foreslået.");
});

test("koden holder en sætnings tal op mod citaterne bag den, på samme måde som i kørslen", () => {
  const facts = new Map([[1, { quote: "omkring 300 boliger bag diget" }]]);
  assert.deepEqual(core.numberProblems({ s: "300 boliger ligger bag diget.", facts: [1] }, facts), []);
  assert.deepEqual(core.numberProblems({ s: "900 boliger ligger bag diget.", facts: [1] }, facts), ["tallet 900 står ikke i citaterne bag sætningen"]);
});

test("kodetjekket kan afprøves: et tal i udkastet ændres med vilje, og tjekket finder det", () => {
  const data = copy();
  data.groups[0].facts[0].quote = "Varslet er hævet for 300 boliger";
  data.docs.D1.text = "Varslet er hævet for 300 boliger.";
  data.drafts.F_G01.web[0] = { s: "Varslet gælder 300 boliger.", facts: [1], problems: [] };
  const before = draw(data, { view: "udkast", sel: "G01" });
  assert.match(before, /data-act="tamper"[^>]*>Afprøv tjekket: ret et tal<\/span>/);
  assert.ok(!before.includes('class="sent  bad"') && !before.includes("står ikke i citaterne"));
  const after = draw(data, { view: "udkast", sel: "G01", tamper: true });
  assert.ok(after.includes("Varslet gælder 900 boliger."));
  assert.ok(after.includes("tallet 900 står ikke i citaterne bag sætningen"));
  assert.match(after, /<p class="notice"><b>Tallet 300 er ændret til 900 med vilje\.<\/b>/);
  assert.match(after, /data-act="tamper"[^>]*>Sæt tallet tilbage<\/span>/);
});

test("genvejen til kodens tjek åbner et udkast og fremhæver kortet, hvor tjekket kan afprøves", () => {
  const data = copy();
  data.groups[0].facts[0].quote = "Varslet er hævet for 300 boliger";
  data.drafts.F_G01.web[0] = { s: "Varslet gælder 300 boliger.", facts: [1], problems: [] };
  const s = core.go(data, { desk: "M", role: "journalist", view: "prio", t: "07.00", sel: null, doc: null }, "desk=F&view=udkast&cue=check");
  assert.equal(s.cue, "check");
  assert.ok(core.renderApp(data, s).includes('<div class="card spot"><h4>Afprøv kodens tjek</h4>'));
  assert.ok(draw(data, { view: "udkast", sel: "G01" }).includes('<div class="card"><h4>Afprøv kodens tjek</h4>'));
});

test("prioriteringslisten har faste kolonnebredder, så sidste kolonne ikke kan blive skåret af", () => {
  const html = draw(DATA, {});
  assert.match(html, /<table class="props"><colgroup><col class="c-n"><col><col class="c-val"><col class="c-st"><col class="c-who"><col class="c-out"><\/colgroup>/);
});

test("mål-knappen ruller skærmen langsomt fra top til bund og bliver stående der", () => {
  // 70 px i sekundet: 1400 px tager 20 sekunder.
  assert.equal(core.scrollAt(0, 1400), 0);
  assert.equal(core.scrollAt(10000, 1400), 700);
  assert.equal(core.scrollAt(20000, 1400), 1400);
  assert.equal(core.scrollAt(60000, 1400), 1400, "den bliver stående i bunden");
  assert.equal(core.scrollAt(5000, 0), 0, "en skærm uden noget at rulle står stille");
  assert.equal(core.scrollDone(19999, 1400), false);
  assert.equal(core.scrollDone(20000, 1400), true);
  assert.equal(core.scrollDone(0, 0), true);
});
