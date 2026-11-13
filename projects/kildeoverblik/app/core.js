// Kildeoverblik: appens logik og tegning, uden browser. Alt kommer fra extractions/app-data.json.
// Tider er "HH.MM" og kan sammenlignes som tekst. Intet tal, klokkeslæt eller navn står skrevet her.
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.KildeCore = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const deskIds = (data) => data.world.desks.map((d) => d.id);
  const score = (data, id, desk) => { const s = ((data.coarse[id] || {}).scores || {})[desk]; return typeof s === "number" ? s : 0; };
  const value = (data, id, desk) => { const v = ((((data.reads[id] || {}).values || {})[desk]) || {}).value; return typeof v === "number" ? v : 0; };
  const unverified = (data, id) => Boolean((data.coarse[id] || {}).unverified);
  const today = (data) => Object.values(data.docs).filter((d) => !d.archive);
  const arrived = (data, t) => today(data).filter((d) => d.time <= t).sort((a, b) => (a.time < b.time ? 1 : a.time > b.time ? -1 : 0));
  const roleLabel = (data, role) => ((data.world.roles || {})[role]) || (role === "journalist" ? "Journalist" : "Vagthavende redaktør");
  const user = (data, desk, role) => (((data.world.users || {})[desk] || {})[role]) || "";
  const initials = (name) => name.split(/[ .]+/).filter(Boolean).map((x) => x[0]).join("").toUpperCase().slice(0, 2);
  // Vagthavende ser alt. Journalisten ser sine egne og de ledige; kollegers forslag tælles kun.
  function visibleTo(data, props, desk, role) {
    if (role !== "journalist") return { shown: props, hidden: 0 };
    const me = user(data, desk, role);
    const shown = props.filter((p) => p.status.kind === "foreslået" || (p.status.kind === "taget" && p.status.assign === me));
    return { shown, hidden: props.filter((p) => p.status.kind === "taget" && p.status.assign !== me).length };
  }
  const groupOf = (data, id) => data.groups.find((g) => g.finds.includes(id));

  function feed(data, desk, t) {
    const thr = data.world.threshold;
    const docs = arrived(data, t);
    const pulled = new Set();
    data.groups.forEach((g) => (g.links || []).forEach((l) => { if (l.related && l.time <= t && l.from in data.docs && data.docs[l.from].time <= t) pulled.add(l.to); }));
    return {
      above: docs.filter((d) => score(data, d.id, desk) >= thr),
      below: docs.filter((d) => score(data, d.id, desk) < thr),
      archive: [...pulled].map((id) => data.docs[id]).filter(Boolean),
    };
  }

  function toVerify(data, desk, t) {
    const rejected = new Set(data.actions.filter((a) => a.action === "verify_reject" && a.time <= t).map((a) => a.find));
    return arrived(data, t).filter((d) => unverified(data, d.id) && score(data, d.id, desk) >= data.world.threshold && !rejected.has(d.id));
  }

  function statusOf(data, finds, desk, t) {
    const acts = data.actions.filter((a) => a.desk === desk && a.time <= t && finds.includes(a.find) && (a.action === "take" || a.action === "dismiss"))
      .sort((a, b) => (a.time < b.time ? -1 : 1));
    const last = acts[acts.length - 1];
    if (!last) return { kind: "foreslået" };
    if (last.action === "dismiss") return { kind: "fravalgt", who: last.who, time: last.time, why: last.why || "" };
    return { kind: "taget", who: last.who, time: last.time, assign: last.assign || last.who, note: last.note || "" };
  }

  function linkState(data, group, link, desk, t) {
    const acts = data.actions.filter((a) => a.desk === desk && a.time <= t && a.to === link.to && group.finds.includes(a.find));
    if (acts.some((a) => a.action === "reject_link")) return "afvist";
    const ok = acts.find((a) => a.action === "approve_link");
    return ok ? "godkendt" : "foreslået";
  }

  function groupAt(data, g, desk, t) {
    const finds = g.finds.filter((id) => data.docs[id] && data.docs[id].time <= t);
    if (!finds.length) return null;
    const verified = finds.filter((id) => !unverified(data, id));
    const val = Math.max(0, ...verified.map((id) => value(data, id, desk)));
    const links = (g.links || []).filter((l) => l.related && l.time <= t && finds.includes(l.from)).map((l) => {
      const act = data.actions.find((a) => a.desk === desk && a.time <= t && a.to === l.to && a.action === "approve_link" && g.finds.includes(a.find));
      return Object.assign({}, l, { state: linkState(data, g, l, desk, t), by: act ? act.who : "", at: act ? act.time : "" });
    });
    const liveLinks = new Set(links.filter((l) => l.state !== "afvist").map((l) => l.from + "__" + l.to));
    const facts = (g.facts || []).filter((f) => (f.via_link ? liveLinks.has(f.via_link) && f.available_from <= t : finds.includes(f.find)));
    const research = data.actions.filter((a) => a.desk === desk && a.time <= t && a.action === "research" && g.finds.includes(a.find));
    return { gid: g.gid, label: g.label, finds, value: val, facts, links, research, first_time: g.first_time,
             top: verified.slice().sort((a, b) => value(data, b, desk) - value(data, a, desk))[0] || finds[0] };
  }

  function proposals(data, desk, t) {
    const thr = data.world.threshold;
    const at = (d) => data.groups.map((g) => groupAt(data, g, d, t)).filter((p) => p && p.value >= thr);
    const others = {};
    deskIds(data).filter((d) => d !== desk).forEach((d) => { others[d] = new Set(at(d).map((p) => p.gid)); });
    return at(desk).map((p) => Object.assign(p, {
      status: statusOf(data, p.finds, desk, t),
      also: Object.keys(others).filter((d) => others[d].has(p.gid)),
      draft: (data.drafts || {})[desk + "_" + p.gid] || null,
    })).sort((a, b) => (b.value - a.value) || (a.first_time < b.first_time ? -1 : 1));
  }

  function feedback(data, desk, t) {
    const props = new Set(proposals(data, desk, t).flatMap((p) => p.finds));
    return data.actions.filter((a) => a.desk === desk && a.time <= t && ["dismiss", "verify_reject", "missing", "reject_link"].includes(a.action))
      .filter((a) => a.action !== "missing" || !props.has(a.find))
      .sort((a, b) => (a.time < b.time ? -1 : 1));
  }

  function readAt(data, desk, threshold) {
    const docs = today(data);
    return { read: docs.filter((d) => score(data, d.id, desk) >= threshold).length, of: docs.length };
  }

  // Testens samlede tal for siden under appen. Regnes fra tællingen mod facit; tom, hvis kørslen ikke er talt.
  function resultLine(data) {
    const desks = Object.values((data.eval || {}).desks || {});
    if (!desks.length) return "";
    const sum = (k) => desks.reduce((n, d) => n + (d[k] || []).length, 0);
    const found = sum("found"), missed = sum("missed"), noise = sum("noise");
    const again = sum("proposals") - found - noise;
    return `Tilsammen skulle redaktionerne have haft ${found + missed} historier foreslået. Sprogmodellen fandt ${found} af dem og overså ${missed}. Den foreslog også ${noise}, som ikke var ${noise === 1 ? "en historie" : "historier"}.`
      + (again > 0 ? ` ${again} forslag handlede om en historie, der allerede var foreslået.` : "");
  }

  // En genvej fra siden uden om appen ("desk=F&doc=D-004"): slutningen af morgenen (eller begyndelsen, når den skal afspilles), vagthavende, og det, genvejen nævner.
  function go(data, state, spec) {
    const want = Object.fromEntries(spec.split("&").map((part) => part.split("=")));
    return Object.assign({}, state, { desk: want.desk || state.desk, role: "vagtchef", view: want.view || "prio", t: want.play ? data.world.window.from : data.world.window.to, sel: want.sel || null, doc: want.doc || null, mark: want.mark ? want.mark.split(",") : null, spot: !want.play && !want.cycle, cue: want.cue || null });
  }

  // Hvor meget appen skal skaleres for at passe i den bredde, der er. Aldrig op, og 1, når bredden ikke kendes.
  const fitScale = (available, base) => (available > 0 && available < base ? available / base : 1);

  const toMin = (t) => { const [h, m] = t.split(".").map(Number); return h * 60 + m; };

  // Kildekanaler: hvor morgenens kildemateriale kom fra, regnet fra de kilder, der er kommet ind.
  function channels(data, desk, t) {
    const by = new Map();
    arrived(data, t).forEach((d) => {
      const c = by.get(d.sender) || { name: d.sender, type: d.source_type, method: (data.world.channel_methods || {})[d.source_type] || "", count: 0, last: d.time, above: 0 };
      c.count += 1;
      if (d.time > c.last) c.last = d.time;
      if (score(data, d.id, desk) >= data.world.threshold) c.above += 1;
      by.set(d.sender, c);
    });
    return [...by.values()].sort((a, b) => (b.count - a.count) || a.name.localeCompare(b.name, "da"));
  }

  // Dagens mål for en redaktion, regnet fra forslagene og redaktionens handlinger op til klokkeslættet.
  function goals(data, desk, t) {
    const props = proposals(data, desk, t);
    const acts = data.actions.filter((a) => a.desk === desk && a.time <= t);
    const taken = props.filter((p) => p.status.kind === "taget");
    const mins = taken.map((p) => toMin(p.status.time) - toMin(p.first_time)).sort((a, b) => a - b);
    const mid = Math.floor(mins.length / 2);
    return { users: new Set(acts.map((a) => a.who)).size, taken: taken.length, proposals: props.length,
             dismissed: props.filter((p) => p.status.kind === "fravalgt").length,
             missing: acts.filter((a) => a.action === "missing").length,
             published: taken.filter((p) => /\bude\b/.test(p.status.note || "")).length,
             minutes: mins.length ? (mins.length % 2 ? mins[mid] : Math.round((mins[mid - 1] + mins[mid]) / 2)) : null };
  }

  // Langsom rulning gennem en skærm: hvor langt nede den er efter et antal millisekunder, når der er max px at rulle.
  const SCROLL_PX_PER_S = 70;
  const scrollAt = (ms, max) => Math.max(0, Math.min(max, Math.floor((ms / 1000) * SCROLL_PX_PER_S)));
  const scrollDone = (ms, max) => scrollAt(ms, max) >= max;

  // Er et element (dets rektangel i vinduet) helt ude af syne i et vindue med den højde?
  const outOfView = (rect, height) => rect.bottom < 0 || rect.top > height;

  // Samme tjek som i kørslen (tools/run_model.py, sentence_problems): hvert tal i sætningen skal stå i citaterne bag den.
  function numberProblems(sentence, factsByNo) {
    const quotes = (sentence.facts || []).map((n) => (factsByNo.get(n) || {}).quote || "").join(" ");
    return (String(sentence.s || "").match(/\d+(?:[.,]\d+)?/g) || []).filter((num) => !quotes.includes(num)).map((num) => `tallet ${num} står ikke i citaterne bag sætningen`);
  }

  // Afprøvning af tjekket: det første tal i udkastets korte tekst ændres med vilje (300 -> 900).
  function tampered(sentences) {
    const i = sentences.findIndex((x) => /\d+/.test(x.s));
    if (i < 0) return null;
    const from = sentences[i].s.match(/\d+/)[0];
    const to = String(Number(from) * 3);
    const list = sentences.slice();
    list[i] = Object.assign({}, sentences[i], { s: sentences[i].s.replace(from, to) });
    return { list, i, from, to };
  }

  const notPresented = (p) => p.facts.filter((f) => f.accuses);

  // ---------------------------------------------------------------- tegning

  // En knap uden funktion i prototypen: stiplet kant og en forklaring, når musen holdes over den.
  const noop = (cls, label, would) => `<span class="${cls} noop" data-act="noop" title="Virker ikke i prototypen. I drift: ${esc(would)}">${esc(label)}</span>`;
  const tip = (cls, text, title) => `<span class="chip ${cls}" title="${esc(title)}">${esc(text)}</span>`;
  const stmt = (f) => (f.statement ? tip("warn", "Udsagn" + (f.speaker ? ": " + f.speaker : ""), "Noget, nogen siger eller skønner, ikke noget kilden selv slår fast. I en artikel tilskrives det den, der siger det. Mærket er sat af modellen.") : "");
  const accused = (f) => (f.accuses ? tip("warn", "Ikke forelagt: " + f.accuses, "Oplysningen lægger et ansvar eller en forsømmelse på en part, som ikke er blevet spurgt. Kritik forelægges den, den rammer, før den udgives. Mærket er sat af modellen.") : "");
  const chip = (cls, text) => `<span class="chip ${cls}">${esc(text)}</span>`;
  const srcChip = (d) => chip("src", d.source_type);
  const deskName = (data, id) => (data.world.desks.find((d) => d.id === id) || { name: id }).name;
  const also = (data, ids) => (ids.length ? tip("also", "Også hos " + ids.map((id) => deskName(data, id)).join(", "), "Kilden eller forslaget står også hos den redaktion. Hver redaktion vurderer det efter sine egne kriterier.") : "");
  const rejected = (data, id, t) => data.actions.some((a) => a.action === "verify_reject" && a.find === id && a.time <= t);
  const st = (s) => `<span class="st ${{ foreslået: "f", taget: "t", fravalgt: "x" }[s.kind]}">${esc(s.kind.charAt(0).toUpperCase() + s.kind.slice(1))}</span>`;

  function renderFeed(data, s) {
    const f = feed(data, s.desk, s.t);
    const thr = data.world.threshold;
    const item = (d, low) => {
      const g = groupOf(data, d.id);
      const others = deskIds(data).filter((x) => x !== s.desk && score(data, d.id, x) >= thr);
      const marks = [srcChip(d), unverified(data, d.id) ? (rejected(data, d.id, s.t) ? chip("out", "Afvist ved verifikation") : chip("warn", "Til verifikation")) : "", g && g.finds.length > 1 && g.finds[0] !== d.id ? chip("join", "Hører til " + data.docs[g.finds[0]].time) : "", also(data, others)].join("");
      return `<div class="fi ${low ? "low" : ""}" data-act="doc" data-id="${esc(d.id)}"><span class="tm">${esc(d.time || d.date)}</span><span class="tx"><b>${esc(d.title)}</b>${marks}</span><span class="gro ${low ? "l" : ""}">${score(data, d.id, s.desk)}</span></div>`;
    };
    const total = f.above.length + f.below.length;
    return `<div class="pane feed"><div class="ph"><b>Kildemateriale</b><small>${total} kilder siden ${esc(data.world.window.from)}</small></div>
      <p class="thr first">Tal = groft skøn 1-10 ud fra et uddrag. Værdien i listen sættes efter fuld læsning.</p>
      <p class="thr head"><b>${f.above.length} kilder på ${thr} eller over</b> · læst i fuld tekst</p>
      <div class="scroll">${f.above.map((d) => item(d, false)).join("")}
      <p class="thr"><b>${f.below.length} kilder under ${thr}</b> · ikke læst i fuld tekst</p>
      ${f.below.map((d) => item(d, true)).join("")}
      ${f.archive.length ? `<p class="thr"><b>Fra arkivet</b> · hentet frem af en ny kilde</p>` + f.archive.map((d) => `<div class="fi low" data-act="doc" data-id="${esc(d.id)}"><span class="tm">${esc(d.date)}</span><span class="tx"><b>${esc(d.title)}</b>${srcChip(d)}${chip("link", "Fundet via sammenhæng")}</span><span class="gro l">${score(data, d.id, s.desk)}</span></div>`).join("") : ""}
      </div></div>`;
  }

  function renderList(data, s, allProps) {
    const me = user(data, s.desk, s.role);
    const vis = visibleTo(data, allProps, s.desk, s.role);
    const props = vis.shown;
    const cur = current(data, s, allProps);
    const curGid = cur ? cur.gid : null;
    const row = (p, i) => {
      const who = p.status.kind === "taget" ? esc(p.status.assign) + (s.role === "journalist" && p.status.assign === me ? " (mig)" : "") : p.status.kind === "foreslået"
        ? (s.role === "journalist" ? noop("asg", "Jeg tager den", "forslaget står som taget af dig, og de andre på redaktionen kan se det.")
          : noop("asg", "Tag og tildel ▾", "du vælger en journalist; forslaget står som taget og forsvinder fra de andres liste over ledige.")) : "–";
      const kan = p.status.kind === "taget" ? `${esc(p.status.note || "ikke valgt")} ${noop("asg", "Ret ▾", "du ændrer, hvor og hvornår historien udgives (web, app, lyd); ændringen kan ses af hele redaktionen.")}`
        : p.status.kind === "foreslået" ? noop("asg", "Vælg udgivelse ▾", "du vælger, hvor historien skal ud (web, app, lyd) og hvornår; valget følger med, når historien tildeles.") : "–";
      const why = p.status.kind === "fravalgt" ? `<div class="small">Fravalgt af ${esc(p.status.who)} kl. ${esc(p.status.time)}${p.status.why ? ": " + esc(p.status.why) : "."}</div>` : "";
      const marks = [chip(p.finds.length > 1 ? "join" : "src", p.finds.length + (p.finds.length > 1 ? " kilder samlet" : " kilde")),
        archiveLinks(p).filter((l) => l.state !== "afvist").length ? chip("link", "+ " + archiveLinks(p).filter((l) => l.state !== "afvist").length + " fra arkivet") : "",
        also(data, p.also), notPresented(p).length ? chip("warn", "Ikke forelagt") : ""].join("");
      const title = titleOf(p);
      return `<tr class="${p.gid === curGid ? (s.spot ? "sel spot" : "sel") : ""} ${p.status.kind === "fravalgt" ? "off" : ""}" data-act="sel" data-id="${esc(p.gid)}"><td class="n">${p.status.kind === "fravalgt" ? "" : i + 1}</td><td><span class="ti">${esc(title)}</span>${marks}${why}</td><td><span class="val ${p.value >= 8 ? "" : "m"}">${p.value}</span></td><td>${st(p.status)}</td><td>${who}</td><td>${kan}</td></tr>`;
    };
    const active = props.filter((p) => p.status.kind !== "fravalgt");
    const off = props.filter((p) => p.status.kind === "fravalgt");
    const f = feed(data, s.desk, s.t);
    return `<div class="pane prio${s.flash ? " pulse" : ""}"><div class="ph"><b>Prioritering</b><small>${active.length} forslag · værdi 1-10 efter fuld læsning</small><span class="sp"></span>${tip(s.role === "journalist" ? "also" : "src", s.role === "journalist" ? "Viser: mine og ledige" : "Viser: alle", "Følger rollen øverst: den vagthavende ser alle forslag, journalisten sine egne og de ledige.")}</div>
      <div class="scroll"><table class="props"><colgroup><col class="c-n"><col><col class="c-val"><col class="c-st"><col class="c-who"><col class="c-out"></colgroup><tr><th></th><th>Forslag</th><th>Værdi</th><th>Status</th><th>Journalist</th><th title="Hvor og hvornår historien udgives: web, app eller lyd.">Udgivelse</th></tr>
      ${active.map(row).join("") || `<tr><td colspan="6" class="empty">Ingen forslag endnu.</td></tr>`}${off.map(row).join("")}</table>
      <div class="under">${vis.hidden ? `<b>${vis.hidden} forslag er taget af kolleger</b> og vises ikke her. ` : ""}Under grænsen: <b>${f.below.length} kilder</b> er ikke læst i fuld tekst. Redaktionens egne historier står ikke her; listen viser kun det, Kildeoverblik har fundet.</div></div></div>`;
  }

  // De forslag, der kan åbnes: dem brugeren ser, uden de fravalgte. Højre rude og udkastet viser det samme.
  const open = (data, s, allProps) => visibleTo(data, allProps, s.desk, s.role).shown.filter((x) => x.status.kind !== "fravalgt");
  const current = (data, s, allProps) => { const props = open(data, s, allProps); return props.find((x) => x.gid === s.sel) || props[0]; };
  const titleOf = (p) => (p.draft && p.draft.angle ? p.draft.angle : p.label);

  // Et arkivdokument står én gang pr. forslag, også når flere fund peger på det: den tidligste sammenhæng, der ikke er afvist.
  function archiveLinks(p) {
    const by = new Map();
    p.links.forEach((l) => {
      const first = by.get(l.to);
      if (!first) by.set(l.to, Object.assign({}, l));
      else if (first.state === "afvist" && l.state !== "afvist") by.set(l.to, Object.assign({}, l));
      else if (l.state === "godkendt" && first.state !== "godkendt") Object.assign(first, { state: l.state, by: l.by, at: l.at });
    });
    return [...by.values()];
  }

  function renderDetail(data, s, allProps) {
    const p = current(data, s, allProps);
    if (!p) return `<div class="pane det"><div class="ph"><b>Forslag</b></div><div class="dsec muted">Der er ingen forslag på dette tidspunkt.</div></div>`;
    const top = data.reads[p.top] || {};
    const why = ((top.values || {})[s.desk] || {}).why || "";
    const fact = (f) => `<div class="fact"><span class="no">${f.no}</span><span class="ft">${esc(f.text)} <span class="chip src" data-act="doc" data-id="${esc(f.find)}">${esc(data.docs[f.find].sender)}${f.via_link ? " · arkiv" : ""}</span>${stmt(f)}${accused(f)}${f.quote_ok ? "" : tip("out", "Citatet står ikke i kilden", "Modellens citat findes ikke tegn for tegn i kildens tekst. Fundet af kode.")}</span></div>`;
    const links = archiveLinks(p).map((l) => `<div class="kv"><span>${esc(data.docs[l.to].title)}</span><b>${l.state === "godkendt" ? `godkendt af ${esc(l.by)} ${esc(l.at)}` : l.state === "afvist" ? "afvist" : "foreslået sammenhæng"}</b></div><div class="small">Deler ${esc(l.shared)}. ${esc(l.why)}</div>`).join("");
    const np = notPresented(p);
    return `<div class="pane det${s.spot ? " spot" : ""}"><div class="ph"><b>Valgt forslag</b><span class="sp"></span>${st(p.status)}</div><div class="scroll">
      <div class="dsec"><h4>Forslag til vinkel</h4><div class="dt">${esc(titleOf(p))}</div>${also(data, p.also)}</div>
      ${p.status.kind === "taget" ? `<div class="dsec"><h4>Tildeling og udgivelse</h4><div class="kv"><span>Journalist</span><b>${esc(p.status.assign)}</b></div><div class="kv"><span>Udgivelse</span><b>${esc(p.status.note || "ikke valgt")}</b></div><div class="small">Tildelt af ${esc(p.status.who)} kl. ${esc(p.status.time)}.</div><div class="btnrow in">${noop("b", "Ret tildeling", "du skifter journalist eller ændrer, hvor og hvornår historien udgives; ændringen kan ses af hele redaktionen.")}</div></div>` : ""}
      ${p.links.length ? `<div class="dsec arch${s.spot ? " spot" : ""}"><h4>Sammenhæng med arkivet</h4>${links}<div class="btnrow in">${noop("b", "Godkend sammenhæng", "sammenhængen står som godkendt med dit navn og tidspunkt, og dens fakta kan bruges i udkastet.")}${noop("b", "Forkert sammenhæng", "arkivdokumentet og dets fakta fjernes fra forslaget, og meldingen gemmes under Tilbagemelding.")}</div></div>` : ""}
      <div class="dsec"><h4>Fakta og kilder</h4>${p.facts.map(fact).join("") || `<span class="muted">Ingen fakta trukket ud.</span>`}</div>
      <div class="dsec"><h4>Hvorfor denne værdi</h4><div>${esc(why) || `<span class="muted">Ingen begrundelse i kørslen.</span>`}</div></div>
      ${np.length ? `<div class="dsec"><h4>Ikke forelagt</h4><div>Faktum ${np.map((f) => f.no).join(", ")} lægger et ansvar på ${esc([...new Set(np.map((f) => f.accuses))].join(" og "))}. ${esc(roleLabel(data, "vagtchef"))} afgør, om det udgives, før parten er hørt.</div>${p.research.map((r) => `<div class="small">${esc(r.text)}</div>`).join("")}<div class="btnrow in">${noop("b", "Markér som forelagt", "parten står som forelagt med tidspunkt, og sætningerne i udkastet skifter fra rød til gul, mens svaret afventes.")}${noop("b", "Svar indhentet", "du skriver partens svar; mærket forsvinder, og svaret ligger klar til udkastet.")}${noop("b", "Lægger ikke ansvar på nogen", "modellens mærke fjernes fra dette faktum, og rettelsen gemmes som tilbagemelding.")}</div></div>` : ""}
      <div class="dsec"><h4>Kilder i forslaget</h4>${p.finds.map((id) => `<div class="kv" data-act="doc" data-id="${esc(id)}"><span>${esc(data.docs[id].time)} · ${esc(data.docs[id].title)}</span><b>${value(data, id, s.desk)}</b></div>`).join("")}</div>
      <div class="btnrow"><span class="b p${s.cue === "draft" ? " cue" : ""}" data-act="view" data-id="udkast">Åbn udkast</span><span class="b" data-act="doc" data-id="${esc(p.top)}">Åbn kilde</span>${noop("b", "Fravælg: ikke en historie", "du skriver kort hvorfor; forslaget flyttes ned i listen, og fravalget gemmes under Tilbagemelding.")}</div></div></div>`;
  }

  // Markér citater i kildens rå tekst. Citater, der overlapper, slås sammen til ét stykke med alle numre.
  function markQuotes(text, facts) {
    const ranges = [];
    facts.forEach((f) => { const i = text.indexOf(f.quote); if (i >= 0 && f.quote) ranges.push({ a: i, b: i + f.quote.length, nos: [f.no] }); });
    ranges.sort((x, y) => x.a - y.a || y.b - x.b);
    const merged = [];
    ranges.forEach((r) => {
      const last = merged[merged.length - 1];
      if (last && r.a < last.b) { last.b = Math.max(last.b, r.b); last.nos = last.nos.concat(r.nos); } else merged.push(r);
    });
    let out = "", at = 0;
    merged.forEach((r) => {
      out += esc(text.slice(at, r.a)) + `<mark><b>${[...new Set(r.nos)].sort((x, y) => x - y).join(", ")}</b>${esc(text.slice(r.a, r.b))}</mark>`;
      at = r.b;
    });
    return out + esc(text.slice(at));
  }

  function renderDoc(data, s, props) {
    const d = data.docs[s.doc];
    const facts = data.groups.flatMap((g) => g.facts.filter((f) => f.find === d.id && f.quote_ok));
    const html = markQuotes(d.text, facts);
    const c = data.coarse[d.id] || {};
    const g = groupOf(data, d.id);
    const link = data.groups.flatMap((x) => (x.links || []).filter((l) => l.to === d.id && l.related))[0];
    return `<div class="main"><div class="colx wide"><p class="crumb"><span data-act="closedoc">← Tilbage</span></p><div class="card doc"><h3>${esc(d.title)} <small>${esc(d.source_type)} · ${esc(d.sender)} · ${d.archive ? esc(d.date) : "hentet " + esc(d.time)} · opdigtet til prototypen</small></h3><div class="doctext">${html.replace(/\n/g, "</p><p>").replace(/^/, "<p>") + "</p>"}</div></div></div>
      <div class="colx side"><div class="card"><h4>Uddraget, den grove filtrering så</h4><p>${esc(d.excerpt)}</p><div class="kv"><span>Groft tal for ${esc(deskName(data, s.desk))}</span><b>${score(data, d.id, s.desk)}</b></div><div class="small">${esc((c.why || {})[s.desk] || "")}</div></div>
      ${data.reads[d.id] ? `<div class="card"><h4>Efter fuld læsning</h4><p>${esc(data.reads[d.id].summary)}</p><div class="kv"><span>Værdi for ${esc(deskName(data, s.desk))}</span><b>${value(data, d.id, s.desk)}</b></div></div>` : d.archive ? "" : `<div class="card"><h4>Ikke læst i fuld tekst</h4><p class="muted">Ingen redaktion nåede grænsen på ${data.world.threshold} ud fra uddraget.</p></div>`}
      ${link ? `<div class="card"><h4>Sådan blev dokumentet hentet frem</h4><p>${esc(data.docs[link.from].time)}: ${esc(data.docs[link.from].title)} nævner ${esc(link.shared)}. ${esc(link.why)}</p></div>` : ""}
      ${facts.length ? `<div class="card"><h4>Fakta fra denne kilde</h4>${facts.map((f) => `<div class="fact"><span class="no">${f.no}</span><span class="ft">${esc(f.text)}</span></div>`).join("")}</div>` : ""}
      ${d.archive ? "" : `<div class="card"><h4>Giv en tilbagemelding</h4><div class="btnrow in">${noop("b", "Den manglede som forslag", "du skriver, hvad historien er; meldingen gemmes under Tilbagemelding, og kilden bliver et nyt eksempel i eval-suiten.")}${unverified(data, d.id) && !rejected(data, d.id, s.t) ? noop("b", "Afvis ved verifikation", "du skriver, hvad der er galt med materialet; kilden mærkes som afvist og bruges ikke i forslag.") : ""}</div></div>`}
      ${g ? `<div class="card"><h4>Indgår i</h4><div class="kv" data-act="sel" data-id="${esc(g.gid)}"><span>${esc(titleOf(props.find((p) => p.gid === g.gid) || g))}</span><b>${g.finds.length} ${g.finds.length === 1 ? "kilde" : "kilder"}</b></div></div>` : ""}</div></div>`;
  }

  function renderDraft(data, s, allProps) {
    const p = current(data, s, allProps);
    if (!p) return `<div class="main"><div class="colx"><div class="card muted">Der er ingen forslag på dette tidspunkt.</div></div></div>`;
    const d = p.draft;
    const out = outlets(p.status.kind === "taget" ? p.status.note : "");
    const outChip = (key, name) => (out[key] ? `<span class="chip link out">${name}: ${esc(out[key])}</span>` : `<span class="chip src out">Ikke valgt til udgivelse</span>`);
    const blocked = new Set(notPresented(p).map((f) => f.no));
    const tam = s.tamper && d ? tampered(d.web) : null;
    const web = !d ? [] : tam ? tam.list.map((x, i) => (i === tam.i ? Object.assign({}, x, { problems: numberProblems(x, new Map(p.facts.map((f) => [f.no, f]))) }) : x)) : d.web;
    const tryCard = d && tampered(d.web) ? `<div class="card${s.cue === "check" ? " spot" : ""}"><h4>Afprøv kodens tjek</h4><p>Kode holder hvert tal i en sætning op mod citaterne bag den. I kørslen fandt tjekket ingen afvigelser. Her kan du se det virke.</p>${tam ? `<p class="notice"><b>Tallet ${esc(tam.from)} er ændret til ${esc(tam.to)} med vilje.</b> Tjekket har fundet det: sætningen er understreget med rødt i udkastet.</p>` : ""}<div class="btnrow in"><span class="b${tam ? "" : " p"}" data-act="tamper">${tam ? "Sæt tallet tilbage" : "Afprøv tjekket: ret et tal"}</span></div></div>` : "";
    const byNo = new Map(p.facts.map((f) => [f.no, f]));
    const ref = (n) => { const f = byNo.get(n); return f ? `<span data-act="doc" data-id="${esc(f.find)}" title="Åbn kilden: ${esc(data.docs[f.find].title)}">${n}</span>` : String(n); };
    const sent = (x) => { const hold = x.facts.some((n) => blocked.has(n)); return `<span class="sent ${hold ? "hold" : ""} ${x.problems.length ? "bad" : ""}">${esc(x.s)}<sup>${x.facts.map(ref).join(", ")}</sup>${hold ? ` <small>ikke forelagt</small>` : ""}${x.problems.length ? ` <small>${esc(x.problems.join("; "))}</small>` : ""}</span> `; };
    const facts = `<div class="card"><h4>Fakta og kilder</h4>${p.facts.map((f) => `<div class="fact"><span class="no">${f.no}</span><span class="ft">${esc(f.text)} <span class="chip src" data-act="doc" data-id="${esc(f.find)}" title="Åbn kilden: ${esc(data.docs[f.find].title)}">${esc(data.docs[f.find].sender)}${f.via_link ? " · arkiv" : ""}</span>${stmt(f)}${accused(f)}</span></div>`).join("")}</div>
      <div class="card"><h4>Regler for alle udgaver</h4><p>Hver sætning viser de fakta, den hviler på. Klik på et tal eller en kilde for at åbne kilden med stedet markeret. Kode tjekker, at tal i sætningen står i citaterne bag den.</p><p>Udsagn tilskrives den, der siger dem.</p><p>Sætninger på fakta, der ikke er forelagt, er mærket. ${esc(roleLabel(data, "vagtchef"))} afgør.</p><p class="muted">Tonen er neutral. Mediets stemme er redaktionens.</p></div>`;
    const rest = open(data, s, allProps).filter((x) => x.draft && x.gid !== p.gid);
    const others = rest.length ? `<div class="card"><h4>Andre udkast</h4>${rest.map((x) => `<div class="kv" data-act="sel" data-id="${esc(x.gid)}"><span>${esc(titleOf(x))}</span></div>`).join("")}</div>` : "";
    if (!d) return `<div class="main"><div class="colx narrow"><div class="card"><h3>${esc(p.label)}</h3></div>${facts}${others}</div><div class="colx wide"><div class="card muted">Kørslen har ikke lavet et udkast til dette forslag for ${esc(s.desk)}.</div></div></div>`;
    return `<div class="main"><div class="colx narrow"><div class="card"><h3>${esc(d.angle || p.label)}</h3><div class="kv"><span>Journalist</span><b>${p.status.kind === "taget" ? esc(p.status.assign) : "ikke tildelt"}</b></div><div class="kv"><span>Udgivelse</span><b>${esc(p.status.note || "ikke valgt")}</b></div><div class="btnrow in">${noop("b", "Ret udgivelse", "du vælger, hvilke udgaver der skal ud (web, app, lyd) og hvornår; det samme valg står i prioriteringslisten.")}</div></div>${tryCard}${facts}${others}</div>
      <div class="colx wide"><div class="card tall${s.spot && s.cue !== "check" ? " spot" : ""}"><h3>Kort tekst <small>udkast til journalisten</small>${outChip("web", "Web")}</h3><p>${web.map(sent).join("")}</p><p class="muted">[Plads til journalistens egen research: svar, citater, baggrund]</p><div class="btnrow">${noop("b p", "Godkend uden mærkede sætninger", "udkastet sendes til redaktionssystemet uden de sætninger, der ikke er forelagt.")}${noop("b", "Ret", "du redigerer teksten; hver sætning skal stadig pege på sine fakta.")}${noop("b", "Kassér", "udkastet fjernes, og forslaget står tilbage med fakta og kilder.")}</div></div></div>
      <div class="colx side"><div class="card"><h3>Notifikation <small>${d.notification.length} tegn</small>${outChip("app", "App")}</h3><p>${sent(d.notification)}</p></div><div class="card"><h3>Lydmanuskript${outChip("lyd", "Lyd")}</h3><p>${d.audio.map(sent).join("")}</p></div><div class="card"><h3>Billede <small>ikke med i prototypen</small></h3><p class="muted">Kræver redaktionens billedpolitik.</p></div></div></div>`;
  }

  function renderFeedback(data, s) {
    const fb = feedback(data, s.desk, s.t);
    const label = { missing: "Den manglede", dismiss: "Ikke en historie", verify_reject: "Afvist ved verifikation", reject_link: "Forkert sammenhæng" };
    const group = (kind) => { const xs = fb.filter((a) => a.action === kind); return `<h4>${label[kind]} · ${xs.length}</h4>` + (xs.map((a) => `<div class="fi${(s.mark || []).includes(a.find) ? " hl" : ""}" data-act="doc" data-id="${esc(a.find)}"><span class="tm">meldt ${esc(a.time)}</span><span class="tx"><b>${esc(data.docs[a.find].title)}</b>${srcChip(data.docs[a.find])}<div class="small">${esc(a.why || "")} Meldt af ${esc(a.who)}.</div></span><span class="gro l">${score(data, a.find, s.desk)}</span></div>`).join("") || `<p class="muted">Ingen.</p>`); };
    return `<div class="main"><div class="colx wide"><div class="card"><h3>Meldt i dag <small>af redaktionen, ikke af systemet</small></h3>${["missing", "dismiss", "verify_reject", "reject_link"].map(group).join("")}</div></div>
      <div class="colx side"><div class="card"><h4>Sådan gives en tilbagemelding</h4><p>En melding gives der, hvor fejlen ses:</p><p><b>Ved et forslag:</b> "Fravælg: ikke en historie" i højre rude under Prioritering.</p><p><b>Ved en kilde:</b> "Den manglede som forslag" eller "Afvis ved verifikation", når kilden er åbnet.</p><p><b>Ved en sammenhæng med arkivet:</b> "Forkert sammenhæng" i forslaget.</p><p class="muted">Knapperne er stiplede og virker ikke i prototypen. Meldingerne her er skrevet i hånden til afspilningen.</p></div>
      <div class="card"><h4>Hvad meldingerne bruges til</h4><p>Hver melding er et eksempel på noget, sprogmodellen vurderede forkert for denne redaktion. Meldingerne samles og bruges til at forbedre systemet på to måder:</p><p><b>Konfigurering:</b> redaktionens kriterier ændres.</p><p><b>Udvikling:</b> systemet ændres, for eksempel hvor meget af en tekst sprogmodellen ser.</p><p class="notice"><b>Ingen ændring gælder med det samme.</b> Den prøves først mod en omfattende eval-suite og de seneste ugers kildemateriale og godkendes af redaktionen og platformejeren, før den gælder.</p><p>En overset historie bliver et nyt eksempel i eval-suiten.</p></div>
      <div class="card"><h4>Hvad denne skærm ikke kan vise</h4><p>Redaktionen ser kun det, nogen melder. Hvor mange historier der aldrig blev opdaget, kan kun måles med en eval-suite, hvor de rigtige historier er skrevet ned på forhånd.</p></div></div></div>`;
  }

  function renderCriteria(data, s) {
    const desk = data.world.desks.find((d) => d.id === s.desk);
    const thr = data.world.threshold;
    const at = (n) => readAt(data, s.desk, n);
    return `<div class="main"><div class="colx wide">${mock("Skærmen er en skitse af, hvordan den kunne se ud. Reglerne og grænsen er dem, sprogmodellen fik i kørslen, men intet kan ændres her.")}<div class="card"><h3>Redaktionens regler <small>skrevet af redaktionen, gælder fra første dag</small></h3>${desk.rules.map((r) => `<div class="rule"><div class="rt">${esc(r)}</div>${noop("b", "Ret", "redaktøren foreslår en ny ordlyd; ændringen prøves mod en omfattende eval-suite og de seneste ugers kildemateriale og godkendes af redaktionen og platformejeren, før den gælder.")}</div>`).join("")}<p class="muted">${esc(data.world.rules_note || "")}</p><p class="notice"><b>En ændring af en regel gælder ikke med det samme.</b> Den prøves først mod en omfattende eval-suite og de seneste ugers kildemateriale, så redaktionen kan se, hvilke forslag der ville komme til, og hvilke der ville forsvinde. Herefter skal ændringen godkendes af redaktionen og platformejeren, før den gælder.</p></div>
      <div class="card"><h3>Faste hensyn <small>ens for alle redaktioner</small></h3>${data.world.fixed_considerations.map((r) => `<div class="kv"><span>${esc(r)}</span></div>`).join("")}</div></div>
      <div class="colx side"><div class="card"><h3>Grænsen <small>hvor meget læses i fuld tekst?</small></h3><div class="kv"><span>Læs kilder med groft tal på mindst</span><b>${thr}</b></div><div class="kv"><span>Læst for denne redaktion i dag</span><b>${at(thr).read} af ${at(thr).of}</b></div><h4>Hvis grænsen flyttes</h4><div class="kv"><span>Til ${thr + 2}</span><b>${at(thr + 2).read} læst</b></div><div class="kv"><span>Til ${thr - 2}</span><b>${at(thr - 2).read} læst</b></div></div>
      <div class="card"><h4>Hvorfor to trin</h4><p>Første trin er billigt og sorterer alt. Andet trin er dyrt og læser kun det lovende. Med ${at(thr).of} kilder kunne alt læses helt; en rigtig redaktion får tusinder.</p><p>I kørslen så første trin kun et uddrag. Det kostede historier, der stod længere nede i teksten.</p></div></div></div>`;
  }

  // "Web ude 06.20 · app 06.21" -> { web: "ude 06.20", app: "06.21" }: hvor og hvornår hver udgave udgives.
  function outlets(note) {
    const out = {};
    String(note || "").split("·").forEach((part) => { const m = part.trim().match(/^(web|app|lyd)\s+(.+)$/i); if (m) out[m[1].toLowerCase()] = m[2].trim(); });
    return out;
  }

  // En lille kurve til mål-skærmen: én serie, 2 px streg, sidste punkt mærket med sin værdi, hvert punkt med værdi ved musen.
  function lineChart(values, labels, unit) {
    const W = 320, H = 96, L = 8, Rr = 44, T = 12, B = 22;
    const lo = Math.min(0, ...values), hi = Math.max(...values), span = hi - lo || 1;
    const x = (i) => L + (values.length > 1 ? (i * (W - L - Rr)) / (values.length - 1) : 0);
    const y = (v) => T + (1 - (v - lo) / span) * (H - T - B);
    const pts = values.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
    const last = values.length - 1;
    const da = (v) => String(v).replace(".", ",");
    return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(labels[0])} til ${esc(labels[last])}: fra ${da(values[0])} til ${da(values[last])} ${esc(unit)}">
      <line x1="${L}" y1="${H - B}" x2="${W - Rr}" y2="${H - B}" class="axis"/>
      <polyline points="${pts}" class="line"/>
      <circle cx="${x(last).toFixed(1)}" cy="${y(values[last]).toFixed(1)}" r="4" class="dot"/>
      <text x="${(x(last) + 8).toFixed(1)}" y="${(y(values[last]) + 4).toFixed(1)}" class="val">${da(values[last])} ${esc(unit)}</text>
      <text x="${L}" y="${H - 6}" class="tick">${esc(labels[0])}</text><text x="${W - Rr}" y="${H - 6}" class="tick" text-anchor="end">${esc(labels[last])}</text>
      ${values.map((v, i) => `<circle cx="${x(i).toFixed(1)}" cy="${y(v).toFixed(1)}" r="9" class="hit"><title>${esc(labels[i])}: ${da(v)} ${esc(unit)}</title></circle>`).join("")}</svg>`;
  }

  const mock = (text) => `<div class="mock"><b>Mock-up.</b> ${esc(text)}</div>`;

  function renderChannels(data, s) {
    const rows = channels(data, s.desk, s.t);
    const desk = deskName(data, s.desk);
    return `<div class="main mockview"><div class="colx wide">${mock("Skærmen er en skitse af, hvordan den kunne se ud. Tallene er regnet fra morgenens kildemateriale, men intet kan ændres her.")}
      <div class="card"><h3>Kildekanaler <small>hvor kildematerialet hentes fra</small></h3>
      <table class="plain"><tr><th>Kanal</th><th>Materialetype</th><th>Kildetype</th><th>Kilder i dag</th><th>Senest</th><th>Nåede grænsen hos ${esc(desk)}</th><th></th></tr>
      ${rows.map((c) => `<tr><td><b>${esc(c.name)}</b></td><td>${chip("src", c.type)}</td><td>${c.method ? chip("also", c.method) : "–"}</td><td>${c.count}</td><td>${esc(c.last)}</td><td>${c.above}</td><td>${noop("b", "Sæt på pause", "kanalen hentes ikke, før den startes igen; det, der allerede er hentet, bliver stående.")}</td></tr>`).join("") || `<tr><td colspan="7" class="empty">Intet er kommet ind endnu.</td></tr>`}</table>
      <div class="btnrow">${noop("b p", "Tilføj kanal", "du vælger en ny kanal at hente fra, for eksempel en kommunes dagsordener eller et bureau, og hvor ofte den hentes.")}</div></div></div>
      <div class="colx side"><div class="card"><h4>To typer</h4><p><b>Materialetype</b> siger, hvad der kommer ind: en pressemeddelelse, et telegram, et offentligt dokument.</p><p><b>Kildetype</b> siger, hvordan det hentes: gennem et API, fra en hjemmeside (webscrape), fra en postkasse eller et RSS-feed. Den afgør, hvor hurtigt og hvor stabilt kanalen leverer.</p></div>
      <div class="card"><h4>Hvem styrer kanalerne</h4><p>Kanalerne er fælles for alle redaktioner på platformen. En ny kanal koster drift og kan give mere støj, så den tilføjes af platformejeren efter ønske fra en redaktion.</p></div>
      <div class="card"><h4>Hvad tallene bruges til</h4><p>En kanal, der giver meget kildemateriale, men næsten aldrig når grænsen hos nogen redaktion, er en kandidat til at blive fjernet.</p></div></div></div>`;
  }

  function renderGoals(data, s) {
    const g = goals(data, s.desk, s.t);
    const kv = (label, val) => `<div class="kv"><span>${esc(label)}</span><b>${esc(String(val))}</b></div>`;
    const tr = data.world.mock_trends || {};
    const meta = data.meta || {};
    const filter = `<div class="filter">Filter ${noop("asg", "Sprogmodel: " + (meta.model || "alle") + " ▾", "du vælger, hvilken sprogmodel tallene skal gælde for, så to modeller kan sammenlignes på de samme mål.")}${noop("asg", "Udgave af instruksen: " + (meta.prompt_version === undefined ? "alle" : meta.prompt_version) + " ▾", "du vælger en udgave af instruksen til sprogmodellen, så en ændring i kvalitet kan føres tilbage til en ændring i systemet.")}${noop("asg", "Periode: 8 uger ▾", "du vælger, hvor langt tilbage kurverne går.")}</div>`;
    // Kurverne for et kort: hver med titel, mærket "eksempeltal" og en linje om, hvorfor tallet er værd at følge.
    const trend = (card) => { const list = (tr.cards || {})[card] || []; return list.length && tr.weeks ? `<div class="trends">${list.map((c) => `<div class="trend"><div class="tt">${esc(c.title)} <small>Eksempeltal, ikke målt</small></div>${lineChart(c.values, tr.weeks, c.unit)}<p class="why">${esc(c.why)}</p></div>`).join("")}</div>` : ""; };
    return `<div class="main mockview"><div class="colx wide">${mock("Skærmen er en skitse af, hvordan den kunne se ud. Dagens tal er regnet fra prototypens data. Kurverne er eksempeltal, fordi prototypen kun dækker én morgen.")}${filter}
      <div class="card"><h3>Anvendelse <small>bliver værktøjet brugt?</small></h3><p class="desc">Værktøjet giver først værdi, når det bruges fast. Spredt brug giver hverken gevinst eller tilbagemeldinger nok til at kalibrere efter.</p>${kv("Medarbejdere, der har brugt værktøjet i dag", g.users)}${kv("Forslag taget", g.taken + " af " + g.proposals)}${trend("use")}</div>
      <div class="card"><h3>Kvalitet <small>rammer forslagene?</small></h3><p class="desc">En stigende andel fravalg viser ofte, at modellen er skredet, før en formel test gør det.</p>${kv("Forslag fravalgt af redaktionen", g.dismissed + " af " + g.proposals)}${kv("Historier meldt som oversete", g.missing)}${trend("quality")}</div>
      <div class="card"><h3>Effekt <small>ændrer det arbejdet?</small></h3><p class="desc">Målet er kortere vej fra kilde til historie. Sparet tid alene siger ikke, om journalistikken blev bedre.</p>${kv("Udgivne historier, der begyndte som forslag", g.published)}${kv("Minutter fra første kilde til taget historie (median)", g.minutes === null ? "–" : g.minutes)}${trend("effect")}</div>
      <div class="card"><h3>Drift og omkostning <small>hvad koster det at køre?</small></h3><p class="desc">Prisen pr. taget forslag siger, om platformen kan betale sig. Med filteret øverst kan to sprogmodeller sammenlignes på både pris og kvalitet.</p>
      ${trend("ops")}</div>
      <div class="btnrow">${noop("b", "Sammenlign med en anden periode", "du vælger to perioder og ser de samme tal side om side.")}</div></div>
      <div class="colx side"><div class="card"><h4>Hvem sætter målene</h4><p>Målene aftales med redaktionen, før værktøjet tages i brug, og følges af redaktionen og platformejeren sammen.</p></div>
      <div class="card"><h4>Mål, der kræver mere end prototypen</h4><p><b>Hvor meget af et udkast journalisten ændrer</b>, før det udgives. Kræver kobling til redaktionssystemet.</p><p><b>Rettelser efter udgivelse</b> i historier, der begyndte som forslag, sammenlignet med andre historier.</p><p><b>Hvad den sparede tid bruges til.</b> Sparet tid alene siger ikke, om journalistikken blev bedre.</p><p><b>Journalisternes egen vurdering</b>, spurgt med faste mellemrum.</p></div>
      <div class="card"><h4>Hvad tallene ikke siger</h4><p>Om journalisterne oplever, at værktøjet hjælper, kan ikke læses i en log. Det spørger man dem om.</p></div></div></div>`;
  }

  function renderApp(data, s) {
    const props = proposals(data, s.desk, s.t);
    const desk = data.world.desks.find((d) => d.id === s.desk);
    const item = (id, name, n) => `<div class="${s.view === id && !s.doc ? "on" : ""}" data-act="view" data-id="${id}">${name}${n !== "" ? ` <small>${n}</small>` : ""}</div>`;
    const navHtml = item("prio", "Prioritering", visibleTo(data, props, s.desk, s.role).shown.filter((p) => p.status.kind !== "fravalgt").length)
      + item("udkast", "Udkast", open(data, s, props).filter((p) => p.draft).length)
      + `<div class="sep"></div><div class="grp">Opsætning</div>` + item("kriterier", "Kriterier", "mock-up")
      + item("kanaler", "Kildekanaler", "mock-up")
      + `<div class="sep"></div><div class="grp">Opfølgning</div>` + item("feedback", "Tilbagemelding", feedback(data, s.desk, s.t).length)
      + item("maal", "Mål", "mock-up");
    const body = s.doc && data.docs[s.doc] ? renderDoc(data, s, props)
      : s.view === "udkast" ? renderDraft(data, s, props)
      : s.view === "feedback" ? renderFeedback(data, s)
      : s.view === "kriterier" ? renderCriteria(data, s)
      : s.view === "kanaler" ? renderChannels(data, s)
      : s.view === "maal" ? renderGoals(data, s)
      : renderFeed(data, s) + renderList(data, s, props) + renderDetail(data, s, props);
    return `<div class="top"><span class="logo">Kilde<span>overblik</span></span>
      <span class="seg">${data.world.desks.map((d) => `<span class="${d.id === s.desk ? (s.flash ? "on pulse" : "on") : ""}" data-act="desk" data-id="${d.id}">${esc(d.name)}</span>`).join("")}</span>
      <span class="seg">${["vagtchef", "journalist"].map((r) => `<span class="${r === s.role ? "on" : ""}" data-act="role" data-id="${r}">${esc(roleLabel(data, r))}</span>`).join("")}</span>
      <span class="sp"></span><span class="clock">${esc(data.world.weekday.charAt(0).toUpperCase() + data.world.weekday.slice(1))} · ${esc(s.t)}</span>
      <span class="who"><b>${esc(user(data, s.desk, s.role))}</b><small>${esc(roleLabel(data, s.role))} · ${esc(desk.name)}</small></span><span class="ava">${esc(initials(user(data, s.desk, s.role)))}</span></div>
      <div class="body"><div class="anav">${navHtml}</div>${body}</div>`;
  }

  return { esc, user, visibleTo, feed, toVerify, proposals, feedback, readAt, notPresented, renderApp, roleLabel, resultLine, go, fitScale, channels, goals, outlets, outOfView, numberProblems, scrollAt, scrollDone };
});
