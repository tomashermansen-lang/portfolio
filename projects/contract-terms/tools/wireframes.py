"""Low-fidelity wireframes of the prototype's four screens, as SVG, written to spec/wireframes/.

Usage: python3 -I tools/wireframes.py
Drawn from the same layout the page implements (the workbench, a step panel,
the review screen, a committee page), so the page and the wireframe can be
compared; they carry no data. Files not in SCREENS are removed, so the folder
holds exactly what the page shows.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "spec" / "wireframes"
FONT = "Inter, -apple-system, sans-serif"
MONO = "'JetBrains Mono', Menlo, monospace"
G = {"line": "#8C8478", "fill": "#F2EDE8", "fill2": "#EBE4DB", "text": "#2C2825", "muted": "#6B6560", "accent": "#A2543A", "bg": "#FFFFFF", "dark": "#2C2825", "tint": "#FBEDE6", "grey": "#F3F1EE"}


def box(x, y, w, h, label=None, fill=None, dashed=False, accent=False, small=False, stroke=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill or G["fill"]}" stroke="{stroke or (G["accent"] if accent else G["line"])}" stroke-width="{1.5 if accent else 1}"{" stroke-dasharray=\"4 3\"" if dashed else ""}/>'
    if label:
        s += f'<text x="{x + 8}" y="{y + (14 if small else 18)}" font-family="{FONT}" font-size="{10 if small else 12}" fill="{G["text"]}">{label}</text>'
    return s


def btn(x, y, w, label, primary=False, disabled=False):
    fill = G["dark"] if primary else G["bg"]
    ink = "#FAF8F5" if primary else G["text"]
    op = ' opacity="0.45"' if disabled else ""
    return (f'<g{op}><rect x="{x}" y="{y}" width="{w}" height="24" rx="4" fill="{fill}" stroke="{G["line"]}"/>'
            f'<text x="{x + w / 2}" y="{y + 16}" font-family="{FONT}" font-size="10" fill="{ink}" text-anchor="middle">{label}</text></g>')


def pill(x, y, label, on=False, accent=False, w=None):
    w = w or (len(label) * 5.6 + 14)
    fill = "#B8C4A8" if on else (G["bg"] if not accent else G["tint"])
    stroke = "#B8C4A8" if on else (G["accent"] if accent else G["line"])
    ink = G["accent"] if accent else G["text"]
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="14" rx="7" fill="{fill}" stroke="{stroke}"/>'
            f'<text x="{x + w / 2:.0f}" y="{y + 10}" font-family="{MONO}" font-size="8" fill="{ink}" text-anchor="middle">{label}</text>')


def text(x, y, t, size=11, muted=True, anchor="start", bold=False, mono=False, ink=None):
    fill = ink or (G["muted"] if muted else G["text"])
    return f'<text x="{x}" y="{y}" font-family="{MONO if mono else FONT}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{" font-weight=\"600\"" if bold else ""}>{t}</text>'


def lines(x, y, w, n, gap=7):
    return "".join(f'<rect x="{x}" y="{y + i * gap}" width="{w * (0.9 if i % 2 else 1)}" height="3" fill="{G["fill2"]}"/>' for i in range(n))


def svg(w, h, body, label):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{label}"><rect width="{w}" height="{h}" fill="{G["bg"]}"/>{body}</svg>'


def bar(w, crumb, pills=True):
    """The dark app bar: kicker, breadcrumb, and the five status pills inside a case."""
    b = f'<rect x="0" y="0" width="{w}" height="56" fill="{G["dark"]}"/>'
    b += text(14, 16, "KEY TERMS", 8, mono=True, ink="#B9B2A8") + text(14, 36, crumb, 13, bold=True, ink="#FAF8F5")
    if pills:
        x = 14
        for lab, on in (("Loaded", True), ("Analysed", True), ("N findings", True), ("0 of 12 reviewed", False), ("No pages", False)):
            w2 = len(lab) * 5.6 + 14
            fill = "#B8C4A8" if on else "none"; stroke = "#B8C4A8" if on else "#8C8478"
            b += f'<rect x="{x}" y="42" width="{w2:.0f}" height="12" rx="6" fill="{fill}" stroke="{stroke}"/>'
            b += f'<text x="{x + w2 / 2:.0f}" y="51" font-family="{MONO}" font-size="7" fill="{"#2C2825" if on else "#B9B2A8"}" text-anchor="middle">{lab}</text>'
            x += w2 + 6
    return b


def tabs(w, current):
    """The five step tabs under the bar."""
    b = f'<rect x="0" y="56" width="{w}" height="30" fill="{G["fill"]}"/>'
    names = ["Load", "Analyse", "Check", "Review", "Committee pages"]
    tw = w / 5
    for i, n in enumerate(names):
        x = i * tw
        if i == current:
            b += f'<rect x="{x}" y="56" width="{tw}" height="30" fill="{G["bg"]}"/><rect x="{x}" y="84" width="{tw}" height="2" fill="{G["dark"]}"/>'
        b += f'<circle cx="{x + 16}" cy="71" r="7" fill="{G["dark"] if i <= current else "none"}" stroke="{G["line"]}"/>'
        b += text(x + 16, 74, str(i + 1), 8, anchor="middle", ink="#FAF8F5" if i <= current else G["muted"])
        b += text(x + 30, 75, n, 10, muted=i > current, bold=i == current)
    return b


def workbench():
    w = 820; b = bar(w, "Cases", pills=False)
    b += btn(14, 70, 120, "Upload a contract", primary=True) + text(146, 86, "3 cases · 0 started", 11)
    cols = [(14, "Project"), (190, "Documents"), (470, "Key terms"), (600, "Last activity")]
    for x, lab in cols: b += text(x, 118, lab, 10, bold=True)
    b += f'<line x1="14" y1="124" x2="{w - 14}" y2="124" stroke="{G["line"]}"/>'
    rows = [("Project A", ["PPA · final, for signature, date (v2)", "PPA · draft date (v1)"]), ("Project B", ["PPA · final, for signature, date"]), ("Project C", ["PPA · final, for signature, date"])]
    y = 134
    for name, docs in rows:
        h = 14 + 13 * len(docs)
        b += text(14, y + 14, name, 11, muted=False)
        for i, d in enumerate(docs): b += text(190, y + 14 + i * 13, d, 9)
        b += pill(470, y + 3, "Not read") + text(600, y + 14, "—", 10) + btn(740, y + 1, 66, "Open")
        y += h + 8
        b += f'<line x1="14" y1="{y - 4}" x2="{w - 14}" y2="{y - 4}" stroke="{G["fill2"]}"/>'
    b += text(14, y + 16, "one row per project · the contract in its versions · status of the key terms, not of the contract", 9)
    return svg(w, y + 30, b, "Wireframe of the workbench: dark bar with the crumb Cases, an upload button and the count, then one row per project with its contract versions, the key-terms status pill, the last activity and an Open button.")


def step():
    w = 820; b = bar(w, "Cases › Project A · PPA v2, final") + tabs(w, 1)
    b += btn(14, 100, 130, "Analyse the contract", primary=True) + btn(150, 100, 100, "Next: Check", disabled=True)
    b += text(14, 142, "Not analysed yet.", 11, muted=False)
    b += text(14, 160, "run n of n · model · date · about USD x per run at list price", 9, mono=True)
    b += box(14, 170, w - 28, 90, fill=G["dark"], stroke=G["dark"])
    b += text(24, 186, "Activity log · replay of run n · model · date", 8, mono=True, ink="#B9B2A8")
    for i in range(4): b += f'<rect x="24" y="{196 + i * 14}" width="{(w - 60) * (0.5 + 0.1 * i)}" height="5" fill="#4A443E"/>'
    b += text(24, 254, "Done. 12 of 12 terms found.", 8, mono=True, ink="#B8C4A8")
    b += text(14, 282, "12 of 12 terms found. Each with the sentence it rests on; the full answers are in the review.", 10, muted=False)
    for x, lab in ((14, "Term"), (260, "Answer"), (640, "Clause")): b += text(x, 302, lab, 9, bold=True)
    b += f'<line x1="14" y1="308" x2="{w - 14}" y2="308" stroke="{G["line"]}"/>'
    for i in range(4):
        y = 314 + i * 22
        b += text(14, y + 12, f"Term {i + 1}", 10, muted=False) + lines(260, y + 6, 360, 1) + lines(640, y + 6, 140, 1)
        b += f'<line x1="14" y1="{y + 20}" x2="{w - 14}" y2="{y + 20}" stroke="{G["fill2"]}"/>'
    b += text(14, 414, "⋮ twelve rows", 9)
    b += f'<line x1="0" y1="426" x2="{w}" y2="426" stroke="{G["line"]}"/>'
    b += text(14, 444, "ABOUT THIS STEP", 8, mono=True) + text(110, 444, "the page's note to its reader, outside the frame: what you see is a recording; no model is called here", 9)
    return svg(w, 456, b, "Wireframe of a step panel: the bar with the crumb and status pills, the five step tabs, the action button with Next beside it, the status line, the activity log, the result table, and the page's note under the frame. Load, Analyse and Check share this shape.")


def review():
    w = 820; b = bar(w, "Cases › Project A · PPA v2, final") + tabs(w, 3)
    b += btn(14, 94, 130, "Next: Committee pages", disabled=False)
    # app bar
    b += box(14, 126, w - 28, 28, fill=G["fill2"])
    b += text(22, 144, "KEY TERMS  Project A", 10, muted=False, bold=True) + text(400, 144, "12 terms · n findings · 2 reviewed, 1 flagged · 1 min", 9) + btn(726, 128, 72, "Export CSV")
    # list
    y0 = 154
    for i in range(6):
        y = y0 + i * 38
        b += box(14, y, 236, 36, fill=G["fill2"] if i == 2 else G["bg"])
        b += text(22, y + 14, f"Term {i + 1}", 10, muted=False, bold=True)
        chips = [("finding", True), ("changed", False)] if i == 0 else ([("flagged", True)] if i == 1 else ([("confirmed", False)] if i in (2, 3) else []))
        x = 22
        for lab, acc in chips:
            b += pill(x, y + 19, lab, accent=acc); x += len(lab) * 5.6 + 20
    b += text(22, y0 + 6 * 38 + 12, "⋮ all twelve, findings first", 9)
    # detail
    dx = 262
    b += text(dx, y0 + 12, "the term's definition", 9)
    b += text(dx, y0 + 32, "Term label", 15, muted=False, bold=True)
    b += lines(dx, y0 + 42, w - dx - 14, 2, 8)
    b += box(dx, y0 + 62, w - dx - 14, 34, fill=G["fill2"]); b += text(dx + 8, y0 + 76, "Source: “the sentence copied from the contract”", 9) + text(dx + 8, y0 + 90, "clause · Part II s. 9.1 · Annex 2  (citations are links; a missing one is marked)", 8)
    b += box(dx, y0 + 102, w - dx - 14, 22, accent=True, fill=G["tint"]); b += text(dx + 8, y0 + 116, "finding · citation not in the document", 9)
    b += text(dx, y0 + 140, "version ▾  dataroom/contract.md", 8, mono=True) + text(w - 14, y0 + 140, "source at about 61 % of the document", 8, anchor="end", mono=True)
    b += box(dx, y0 + 146, w - dx - 14, 70, fill=G["fill2"]); b += lines(dx + 10, y0 + 158, w - dx - 34, 4, 9)
    b += f'<rect x="{dx + 10}" y="{y0 + 175}" width="{w - dx - 80}" height="9" fill="#F3DFA0"/>'
    b += btn(dx, y0 + 226, 70, "Confirm", primary=True) + btn(dx + 78, y0 + 226, 100, "Flag for review")
    b += text(dx, y0 + 268, "What is wrong, and where", 9) + box(dx, y0 + 274, w - dx - 14, 28, fill=G["bg"], dashed=True) + text(dx + 8, y0 + 292, "the analyst's note; a flag needs one", 8)
    b += btn(dx, y0 + 312, 90, "Save the flag", primary=True)
    b += text(w - 14, y0 + 328, "← Previous   3 of 12   Next →", 9, anchor="end")
    return svg(w, y0 + 344, b, "Wireframe of the review screen: the bar and tabs, Next to the committee pages, the app bar with the status line and export, the term list with chips on the left, and on the right the answer, the source sentence with its clause, a finding, the contract text with the sentence highlighted, the two decisions Confirm and Flag for review, and the note field a flag needs.")


def committee():
    w, h = 820, 400; b = box(0, 0, w, h, fill=G["bg"])
    b += text(30, 30, "COMMITTEE PAPER · SECTION: KEY TERMS · follows the decision requested, the thesis and the financial case", 8, mono=True)
    b += text(30, 60, "Project · Power Purchase Agreement", 16, muted=False) + text(790, 52, "version, date", 9, anchor="end") + text(790, 64, "fictional project", 9, anchor="end")
    b += f'<line x1="30" y1="72" x2="790" y2="72" stroke="{G["text"]}" stroke-width="1.5"/>'
    b += text(60, 90, "TERM", 8) + text(250, 90, "FIGURE, AS THE CONTRACT STATES IT", 8) + text(640, 90, "CLAUSE", 8)
    states = [None, None, "flagged", None, "not reviewed", None]
    for i, st in enumerate(states):
        y = 100 + i * 42
        if st == "flagged": b += f'<rect x="30" y="{y}" width="760" height="40" fill="{G["tint"]}"/>'
        if st == "not reviewed": b += f'<rect x="30" y="{y}" width="760" height="40" fill="{G["grey"]}"/>'
        b += text(36, y + 14, str(i + 1), 9) + text(60, y + 14, f"Term {i + 1}", 10, muted=False, bold=True)
        if st: b += pill(60, y + 20, st.upper(), accent=st == "flagged")
        b += lines(250, y + 6, 360, 2, 9) + lines(640, y + 6, 130, 2, 9)
        b += f'<line x1="30" y1="{y + 40}" x2="790" y2="{y + 40}" stroke="{G["fill2"]}"/>'
    b += text(30, 370, "Extracted by model, run n, date · reviewed n of 12 · every figure can be followed to its sentence", 8) + text(790, 370, "2 / 4", 8, anchor="end")
    b += text(30, 388, "page 1: six headline figures and what needs attention · page 3: terms 7–12 · page 4: open points with the analyst's notes, changed since the draft", 8)
    return svg(w, h, b, "Wireframe of a committee page in landscape: kicker, title with version, a table of six terms with lead figure and clause, a flagged row with a tint and pill, a not-reviewed row in grey, provenance footer and page number; the other three pages named below.")


SCREENS = (("workbench", workbench), ("step", step), ("review", review), ("committee", committee))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in SCREENS:
        (OUT / f"{name}.svg").write_text(fn())
    for p in OUT.glob("*.svg"):
        if p.stem not in {n for n, _ in SCREENS}:
            p.unlink()
    print("wrote", ", ".join(f"spec/wireframes/{n}.svg" for n, _ in SCREENS))


if __name__ == "__main__":
    main()
