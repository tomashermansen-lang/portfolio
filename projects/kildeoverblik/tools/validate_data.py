"""Reglerne for testdata, tjekket af kode før en model ser noget.

Kørsel: python3 -I tools/validate_data.py   (exit 1 ved fejl)

Uddraget er det, den grove filtrering ser. Det regnes af `excerpt` og skrives aldrig i hånden,
så en historie, der står langt nede i en kilde, faktisk er skjult for første trin.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import casefiles  # noqa: E402

EXCERPT_LIMIT = 240
TIME = re.compile(r"^\d\d\.\d\d$")


def excerpt(find: dict, limit: int = EXCERPT_LIMIT) -> str:
    text = find["text"].strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if not text[limit].isspace():
        cut = cut[:cut.rfind(" ")] if " " in cut else cut
    return cut.rstrip()


def problems(data: dict) -> list[str]:
    world, key = data["world"], data["key"]
    out: list[str] = []
    lo, hi = world["window"]["from"], world["window"]["to"]
    desks = [d["id"] for d in world["desks"]]
    seen: dict[str, dict] = {}

    for doc in list(data["finds"]) + list(data["archive"]):
        fid = doc.get("id", "?")
        if fid in seen:
            out.append(f"{fid}: id'et findes to gange")
        seen[fid] = doc
        if doc.get("source_type") not in world["source_types"]:
            out.append(f"{fid}: ukendt kildetype {doc.get('source_type')!r}")
        for field in ("title", "text", "sender"):
            if not str(doc.get(field, "")).strip():
                out.append(f"{fid}: tom {'tekst' if field == 'text' else field}")

    for f in data["finds"]:
        t = f.get("time", "")
        if not TIME.match(t) or not (lo <= t <= hi):
            out.append(f"{f.get('id')}: tidspunktet {t!r} er ikke HH.MM mellem {lo} og {hi}")
        if f.get("id") not in key["finds"]:
            out.append(f"{f.get('id')}: står ikke i facit")
    for a in data["archive"]:
        if not a.get("date") or a["date"] >= world["date"]:
            out.append(f"{a.get('id')}: arkivets dato {a.get('date')!r} skal ligge før {world['date']}")

    events = {e["id"]: e for e in key["events"]}
    used: set[str] = set()
    for fid, entry in key["finds"].items():
        if fid not in seen:
            out.append(f"facit nævner {fid}, som ikke findes")
            continue
        ev = entry.get("event")
        if ev is not None:
            if ev not in events:
                out.append(f"{fid}: facit peger på begivenheden {ev}, som ikke findes")
            used.add(ev)
        phrase = entry.get("buried")
        if phrase:
            if phrase not in seen[fid]["text"]:
                out.append(f"{fid}: den skjulte sætning {phrase!r} står ikke i teksten")
            elif phrase in excerpt(seen[fid]):
                out.append(f"{fid}: den skjulte sætning {phrase!r} står i uddraget og er ikke skjult")

    for eid, e in events.items():
        for d in desks:
            if not isinstance(e.get("story_for", {}).get(d), bool):
                out.append(f"{eid}: mangler ja eller nej for redaktionen {d}")
        link_ids = {l.get("id") for l in key.get("links", [])}
        for lid in e.get("via_links", []):
            if lid not in link_ids:
                out.append(f"{eid}: hviler på sammenhængen {lid}, som ikke findes")
        if eid not in used and not e.get("via_links"):
            out.append(f"{eid}: ingen fund hører til begivenheden")
        for fact in e.get("facts", []):
            src = seen.get(fact.get("find"))
            if src is None:
                out.append(f"{eid}: faktum {fact.get('no')} peger på {fact.get('find')}, som ikke findes")
            elif fact.get("quote", "") not in src["text"]:
                out.append(f"{eid}: citatet {fact.get('quote')!r} står ikke ordret i {fact['find']}")

    for link in key.get("links", []):
        for end in ("from", "to"):
            if link.get(end) not in seen:
                out.append(f"sammenhængen {link.get('id')}: {link.get(end)} findes ikke")
    return out


def main() -> int:
    data = casefiles.load()
    found = problems(data)
    for p in found:
        print("FEJL", p)
    stories = {d["id"]: sum(1 for e in data["key"]["events"] if e["story_for"].get(d["id"])) for d in data["world"]["desks"]}
    print(f"{len(data['finds'])} fund, {len(data['archive'])} i arkivet, {len(data['key']['events'])} begivenheder, "
          f"historier pr. redaktion {stories}, {len(data['key'].get('links', []))} sammenhænge, {len(found)} fejl")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
