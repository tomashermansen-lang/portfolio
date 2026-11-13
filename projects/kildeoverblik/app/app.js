// Kildeoverblik: kobler siden til core.js. Henter extractions/app-data.json og afspiller morgenen.
(function () {
  "use strict";
  const core = window.KildeCore;
  const $ = (id) => document.getElementById(id);
  const toMin = (t) => { const [h, m] = t.split(".").map(Number); return h * 60 + m; };
  const toTime = (n) => String(Math.floor(n / 60)).padStart(2, "0") + "." + String(n % 60).padStart(2, "0");
  let data = null, timer = null, origin = null;
  const state = { desk: "F", role: "vagtchef", view: "prio", t: "09.00", sel: null, doc: null, filter: "alle", mark: null, flash: false, spot: false, cue: null, tamper: false };

  // Appen er bygget til 1200 px. På en smallere skærm skaleres den ned, så hele skærmbilledet kan ses.
  const BASE_W = 1200, SMALL_H = 760;
  function fit() {
    const box = $("appfit"), app = $("app");
    if (!box.clientWidth) return;
    const s = core.fitScale(box.clientWidth, BASE_W);
    const small = s < 1;
    app.style.width = small ? BASE_W + "px" : "";
    app.style.height = small ? SMALL_H + "px" : "";
    app.style.transformOrigin = small ? "top left" : "";
    app.style.transform = small ? `scale(${s})` : "";
    box.style.height = small ? Math.ceil(SMALL_H * s) + "px" : "";
    $("smallnote").hidden = !small;
  }

  function draw() {
    $("app").innerHTML = core.renderApp(data, state);
    $("clock").textContent = state.t;
    $("range").value = toMin(state.t);
    $("play").textContent = timer ? "❚❚ Pause" : "▶ Afspil morgenen";
  }

  let cycler = null;
  function stopCycle() { if (cycler) { clearInterval(cycler); cycler = null; } state.flash = false; }
  // Viser redaktionerne efter tur med et par sekunders mellemrum og ender på den første.
  function cycleDesks() {
    const ids = data.world.desks.map((d) => d.id);
    const order = ids.slice(1).concat(ids[0]);
    state.flash = true;
    draw();
    cycler = setInterval(() => {
      state.desk = order.shift();
      state.sel = null;
      draw();
      if (!order.length) { clearInterval(cycler); cycler = null; setTimeout(() => { if (!cycler) { state.flash = false; draw(); } }, 1500); }
    }, 1500);
  }

  // Vejen til udkastet i tre trin: forslaget i listen, knappen "Åbn udkast" nederst i højre rude, udkastet.
  let tour = [];
  function stopTour() { tour.forEach(clearTimeout); tour = []; state.cue = null; }
  function tourToDraft() {
    tour.push(setTimeout(() => {
      state.spot = false; state.cue = "draft"; draw();
      const pane = document.querySelector("#app .det .scroll");
      if (pane) pane.scrollTo({ top: pane.scrollHeight, behavior: "smooth" });
    }, 1500));
    tour.push(setTimeout(() => { state.cue = null; state.view = "udkast"; state.spot = true; draw(); tour = []; }, 3200));
  }

  // Mål-skærmen rulles langsomt igennem fra top til bund. Den stopper, når læseren selv ruller, klikker eller trykker.
  let roll = null;
  function stopRoll() { if (roll) { cancelAnimationFrame(roll); roll = null; } }
  function rollGoals() {
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    tour.push(setTimeout(() => {
      const pane = document.querySelector("#app .main");
      if (!pane) return;
      const max = pane.scrollHeight - pane.clientHeight;
      let start = null;
      const step = (now) => {
        if (start === null) start = now;
        if (!pane.isConnected) { roll = null; return; }
        pane.scrollTop = core.scrollAt(now - start, max);
        roll = core.scrollDone(now - start, max) ? null : requestAnimationFrame(step);
      };
      roll = requestAnimationFrame(step);
    }, 1200));
  }

  function stop() { stopTour(); stopRoll(); stopCycle(); if (timer) { clearInterval(timer); timer = null; } }

  function play() {
    if (timer) { stop(); draw(); return; }
    const end = toMin(data.world.window.to);
    if (toMin(state.t) >= end) state.t = data.world.window.from;
    timer = setInterval(() => {
      const next = toMin(state.t) + 1;
      state.t = toTime(Math.min(next, end));
      if (next >= end) stop();
      draw();
    }, 220);
    draw();
  }

  function onClick(ev) {
    const el = ev.target.closest("[data-act]");
    if (!el) return;
    const act = el.dataset.act, id = el.dataset.id;
    if (act !== "noop") state.mark = null;
    state.spot = false;
    stopCycle();
    stopTour();
    stopRoll();
    if (act !== "tamper") state.tamper = false;
    if (act === "desk") { state.desk = id; state.sel = null; state.doc = null; }
    else if (act === "role") state.role = id;
    else if (act === "view") { state.view = id; state.doc = null; }
    else if (act === "sel") { state.sel = id; state.doc = null; if (state.view !== "udkast") state.view = "prio"; }
    else if (act === "doc") state.doc = id;
    else if (act === "closedoc") state.doc = null;
    else if (act === "tamper") state.tamper = !state.tamper;
    else return;
    ev.stopPropagation();
    draw();
  }

  fetch("extractions/app-data.json", { cache: "no-store" }).then((r) => r.json()).then((d) => {
    data = d;
    state.t = d.world.window.to;
    $("range").min = toMin(d.world.window.from); $("range").max = toMin(d.world.window.to);
    $("from").textContent = d.world.window.from; $("to").textContent = d.world.window.to;
    $("recnote").textContent = `Optagelse af en modelkørsel på ${d.meta.documents} syntetiske kilder`;
    $("result").textContent = core.resultLine(d);
    document.querySelectorAll("[data-go]").forEach((el) => el.addEventListener("click", () => {
      stop();
      Object.assign(state, core.go(data, state, el.dataset.go));
      if (el.dataset.go.includes("play=1")) play(); else draw();
      if (el.dataset.go.includes("cycle=1")) cycleDesks();
      if (el.dataset.go.includes("tour=udkast")) tourToDraft();
      if (el.dataset.go.includes("tour=maal")) rollGoals();
      $("stage").scrollIntoView({ behavior: "smooth", block: "start" });
      origin = el;
    }));
    // Vejen tilbage: en knap i hjørnet, så længe den knap, læseren trykkede på, er ude af syne.
    const showBack = () => { $("back").hidden = !(origin && core.outOfView(origin.getBoundingClientRect(), window.innerHeight)); };
    window.addEventListener("scroll", showBack, { passive: true });
    $("back").addEventListener("click", () => {
      if (origin) origin.scrollIntoView({ behavior: "smooth", block: "center" });
      origin = null;
      $("back").hidden = true;
    });
    $("app").addEventListener("click", onClick);
    ["wheel", "touchstart", "pointerdown"].forEach((name) => $("app").addEventListener(name, stopRoll, { passive: true }));
    $("play").addEventListener("click", play);
    $("end").addEventListener("click", () => { stop(); state.t = d.world.window.to; draw(); });
    $("range").addEventListener("input", (ev) => { stop(); state.t = toTime(Number(ev.target.value)); draw(); });
    window.addEventListener("resize", fit);
    draw();
    fit();
  }).catch((err) => { $("app").textContent = "Kunne ikke hente data: " + err; });
})();
