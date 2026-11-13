"""Tæl en kørsel mod facit: extractions/runs/<N>/eval.json.

Kørsel: python3 -I tools/evaluate.py [--run N]

Tællingen er en test, ikke en del af produktet: en redaktion har intet facit. Pr. redaktion tælles
historier, der stod blandt forslagene (found), historier, der ikke gjorde (missed, med grund), og
forslag, der ikke var historier for den redaktion (noise). Sammenhænge tælles for sig og kun ét sted.
Et forslag er en gruppe af læste fund, hvor mindst ét fund har værdi på grænsen eller over for redaktionen.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def _value(reads: dict, fid: str, desk: str) -> float:
    return ((reads.get(fid) or {}).get("values") or {}).get(desk, {}).get("value") or 0


def proposals(run: dict, desk: str) -> list[dict]:
    out = []
    for g in run["groups"]:
        members = [f for f in g.get("finds", []) if f in run["reads"]]
        # Ubekræftet materiale går til verifikation og er ikke et forslag (samme regel som i appen).
        verified = [f for f in members if not (run["coarse"].get(f) or {}).get("unverified")]
        value = max([_value(run["reads"], f, desk) for f in verified] or [0])
        if members and value >= run["threshold"]:
            out.append({"finds": members, "label": g.get("label", ""), "value": value})
    return out


def evaluate(key: dict, run: dict, desks: list[str]) -> dict:
    event_of = {fid: entry.get("event") for fid, entry in key["finds"].items()}
    finds_of: dict[str, list[str]] = {}
    for fid, ev in event_of.items():
        if ev:
            finds_of.setdefault(ev, []).append(fid)
    result: dict = {"desks": {}, "titles": {ev["id"]: ev["title"] for ev in key["events"]}}

    judged = run.get("links", {})
    related = {tuple(name.split("__")) for name, rec in judged.items() if rec.get("related")}
    found_links, missed_links, matched, pairs_of = [], [], set(), {}
    for link in key.get("links", []):
        hits = {(f, t) for f, t in related if t == link["to"] and event_of.get(f) == link.get("event", event_of.get(link["from"]))}
        if hits:
            found_links.append(link["id"])
            matched |= hits
            pairs_of[link["id"]] = hits
            continue
        if link["from"] not in run["reads"]:
            why = "dagens fund blev aldrig læst i fuld tekst"
        elif f"{link['from']}__{link['to']}" not in judged:
            why = "koden fandt ingen kandidat"
        else:
            why = "modellen sagde nej"
        missed_links.append({"link": link["id"], "why": why})
    wrong = [{"from": f, "to": t} for f, t in sorted(related - matched)]
    result["links"] = {"found": found_links, "missed": missed_links, "wrong": wrong,
                       "counts": {"planted": len(key.get("links", [])), "found": len(found_links),
                                  "missed": len(missed_links), "wrong": len(wrong), "judged": len(judged)}}

    for desk in desks:
        props = proposals(run, desk)
        proposed_finds = {f for p in props for f in p["finds"]}
        stories = [ev["id"] for ev in key["events"] if ev["story_for"].get(desk)]
        via = {ev["id"]: ev.get("via_links") or [] for ev in key["events"]}

        def is_found(ev: str) -> bool:
            if via[ev]:
                return any(f in proposed_finds for lid in via[ev] for f, _ in pairs_of.get(lid, ()))
            return bool(proposed_finds & set(finds_of.get(ev, [])))

        found = [ev for ev in stories if is_found(ev)]
        missed = []
        for ev in stories:
            if ev in found:
                continue
            if via[ev]:
                missed.append({"event": ev, "why": "sammenhængen blev ikke fundet"})
                continue
            read = [f for f in finds_of.get(ev, []) if f in run["reads"]]
            if read and all((run["coarse"].get(f) or {}).get("unverified") for f in read):
                why = "ubekræftet kilde; ligger til verifikation"
            else:
                why = "læst, men under grænsen for redaktionen" if read else "aldrig læst i fuld tekst"
            missed.append({"event": ev, "why": why})
        noise = [p for p in props if not any(event_of.get(f) in stories for f in p["finds"])]
        result["desks"][desk] = {
            "found": found, "missed": missed, "noise": noise, "proposals": props,
            "counts": {"stories": len(stories), "proposed": len(props), "found": len(props) - len(noise),
                       "missed": len(missed), "noise": len(noise)}}
        # "found" i counts er forslag, der er historier (found + noise = proposed);
        # antallet af facits historier, der blev fundet, står i stories_found.
        result["desks"][desk]["stories_found"] = len(found)


    differs = {d: sum(1 for fid in run["reads"]
                      if _value(run["reads"], fid, d) != ((run["coarse"].get(fid) or {}).get("scores") or {}).get(d))
               for d in desks}
    result["reading"] = {"documents": len([f for f in key["finds"]]), "read": len(run["reads"]),
                         "value_differs_from_coarse": differs}
    return result


def load_run(folder: Path, threshold: int) -> dict:
    def parsed(sub: str) -> dict:
        return {p.stem: (json.loads(p.read_text(encoding="utf-8")).get("parsed") or {}) for p in sorted((folder / sub).glob("*.json"))}
    groups = (json.loads((folder / "groups.json").read_text(encoding="utf-8")).get("parsed") or {}).get("groups") or [] \
        if (folder / "groups.json").exists() else []
    return {"threshold": threshold, "coarse": parsed("coarse"), "reads": parsed("read"), "groups": groups, "links": parsed("links")}


def main() -> int:
    import casefiles
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int)
    args = ap.parse_args()
    data = casefiles.load()
    runs = ROOT / "extractions" / "runs"
    n = args.run or max(int(p.name) for p in runs.glob("[0-9]*"))
    run = load_run(runs / str(n), data["world"]["threshold"])
    result = evaluate(data["key"], run, [d["id"] for d in data["world"]["desks"]])
    (runs / str(n) / "eval.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for desk, r in result["desks"].items():
        c = r["counts"]
        print(f"{desk}: {r['stories_found']} af {c['stories']} historier stod blandt {c['proposed']} forslag; "
              f"{c['missed']} overset, {c['noise']} støj")
    print("sammenhænge:", result["links"]["counts"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
