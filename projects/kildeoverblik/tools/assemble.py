"""Saml data, kørsel, tælling og redaktionens handlinger til den ene fil, appen læser: extractions/app-data.json.

Kørsel: python3 -I tools/assemble.py [--run N]

Appen tegner alt ud fra denne fil. Ingen tal, tider eller titler i appen er skrevet i hånden.
Her regnes det, kode kan regne: hvornår en gruppe opstår, værdien pr. redaktion, om hvert citat står
ordret i sin kilde, og om hver sætning i et udkast kun bruger tal, der står i citaterne bag den.
En sammenhæng til arkivet bliver tilgængelig ét minut efter det fund, der udløste den.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_model  # noqa: E402
import validate_data  # noqa: E402


def plus_minutes(hhmm: str, minutes: int) -> str:
    h, m = (int(x) for x in hhmm.split("."))
    total = h * 60 + m + minutes
    return f"{total // 60:02d}.{total % 60:02d}"


def _clean_fact(f: dict, find: str, docs: dict) -> dict:
    return {"text": f.get("text", ""), "quote": f.get("quote", ""), "statement": bool(f.get("statement")),
            "speaker": f.get("speaker"), "accuses": f.get("accuses"), "find": find,
            "quote_ok": bool(f.get("quote")) and any(f.get("quote", "") in docs[find].get(k, "") for k in ("text", "title"))}


def build_groups(run: dict, docs: dict, world: dict) -> list[dict]:
    shared = {(c["from"], c["to"]): c["shared"] for c in run.get("candidates", [])}
    out = []
    for n, g in enumerate(run["groups"], 1):
        members = sorted([f for f in g.get("finds", []) if f in run["reads"] and f in docs], key=lambda f: docs[f]["time"])
        if not members:
            continue
        facts, links = [], []
        for fid in members:
            for f in run["reads"][fid].get("facts") or []:
                facts.append(_clean_fact(f, fid, docs))
        for name, rec in sorted(run.get("links", {}).items()):
            frm, to = name.split("__")
            if frm not in members or to not in docs:
                continue
            when = plus_minutes(docs[frm]["time"], 1)
            links.append({"from": frm, "to": to, "shared": shared.get((frm, to), ""), "related": bool(rec.get("related")),
                          "why": rec.get("why", ""), "time": when})
            if rec.get("related"):
                for f in rec.get("facts") or []:
                    facts.append({**_clean_fact(f, to, docs), "via_link": name, "available_from": when})
        # Modellen læser et arkivdokument én gang pr. fund, der peger på det. Samme citat fra samme dokument er
        # samme faktum: det første beholdes, og udkastenes henvisninger flyttes med (renumber: gammelt nr. -> nyt).
        # Et citat, der står inde i et andet, er samme sted i dokumentet; det længste citat beholdes.
        kept, renumber = [], {}
        for old, f in enumerate(facts, 1):
            same = next((k for k in kept if f.get("via_link") and k.get("via_link") and k["find"] == f["find"] and f["quote"]
                         and k["quote"] and (f["quote"] in k["quote"] or k["quote"] in f["quote"])), None)
            if same:
                same["quote"] = max(same["quote"], f["quote"], key=len)
                renumber[old] = same["no"]
                continue
            kept.append(f)
            f["no"] = renumber[old] = len(kept)
        facts = kept
        values = {d["id"]: max([((run["reads"][f].get("values") or {}).get(d["id"]) or {}).get("value") or 0 for f in members])
                  for d in world["desks"]}
        out.append({"gid": f"G{n:02d}", "label": g.get("label", ""), "finds": members,
                    "first_time": docs[members[0]]["time"], "values": values, "facts": facts, "links": links,
                    "renumber": renumber})
    return out


def build_drafts(run: dict, groups: list[dict]) -> dict:
    by_gid = {g["gid"]: g for g in groups}
    out = {}
    for name, d in sorted(run.get("drafts", {}).items()):
        gid = name.split("_", 1)[1]
        if gid not in by_gid or not d:
            continue
        facts = {f["no"]: f for f in by_gid[gid]["facts"]}
        renumber = by_gid[gid].get("renumber") or {}

        def checked(s: dict) -> dict:
            nos = list(dict.fromkeys(renumber.get(n, n) for n in s.get("facts") or []))
            return {"s": s.get("s", ""), "facts": nos, "problems": run_model.sentence_problems({**s, "facts": nos}, facts)}

        note = checked(d.get("notification") or {})
        note["length"] = len(note["s"])
        out[name] = {"angle": d.get("angle", ""), "web": [checked(s) for s in d.get("web") or []],
                     "notification": note, "audio": [checked(s) for s in d.get("audio") or []]}
    return out


def load_run(folder: Path, threshold: int) -> dict:
    def parsed(sub: str) -> dict:
        return {p.stem: (json.loads(p.read_text(encoding="utf-8")).get("parsed") or {}) for p in sorted((folder / sub).glob("*.json"))}

    def one(name: str, default):
        path = folder / name
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    return {"threshold": threshold, "coarse": parsed("coarse"), "reads": parsed("read"),
            "groups": (one("groups.json", {}).get("parsed") or {}).get("groups") or [],
            "links": parsed("links"), "candidates": one("link-candidates.json", []), "drafts": parsed("drafts"),
            "meta": one("run.json", {}), "eval": one("eval.json", None)}


def main() -> int:
    import casefiles
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int)
    args = ap.parse_args()
    data = casefiles.load()
    world = data["world"]
    runs = ROOT / "extractions" / "runs"
    n = args.run or max(int(p.name) for p in runs.glob("[0-9]*"))
    run = load_run(runs / str(n), world["threshold"])
    docs = {}
    for d in data["finds"]:
        docs[d["id"]] = {**d, "excerpt": validate_data.excerpt(d), "archive": False}
    for d in data["archive"]:
        docs[d["id"]] = {**d, "excerpt": validate_data.excerpt(d), "archive": True}
    groups = build_groups(run, docs, world)
    actions_path = ROOT / "dataroom" / "actions.json"
    out = {"meta": {**run["meta"], "documents": len(data["finds"]), "archive": len(data["archive"]), "read": len(run["reads"])},
           "world": {k: world[k] for k in ("date", "weekday", "window", "desks", "fixed_considerations", "threshold", "scope",
                                           "coverage", "note", "time_note", "rules_note", "roles", "users",
                                           "channel_methods", "mock_trends") if k in world},
           "docs": docs, "coarse": run["coarse"],
           "reads": {fid: {"summary": r.get("summary", ""), "values": r.get("values") or {}} for fid, r in run["reads"].items()},
           "groups": [{k: v for k, v in g.items() if k != "renumber"} for g in groups], "drafts": build_drafts(run, groups),
           "actions": json.loads(actions_path.read_text(encoding="utf-8")) if actions_path.exists() else [],
           "eval": run["eval"]}
    target = ROOT / "extractions" / "app-data.json"
    target.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    bad_quotes = sum(1 for g in groups for f in g["facts"] if not f["quote_ok"])
    bad_sentences = sum(1 for d in out["drafts"].values() for s in d["web"] + d["audio"] + [d["notification"]] if s["problems"])
    print(f"{target}: {len(groups)} grupper, {len(out['drafts'])} udkast, {bad_quotes} citater uden dækning, "
          f"{bad_sentences} sætninger med anmærkning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
