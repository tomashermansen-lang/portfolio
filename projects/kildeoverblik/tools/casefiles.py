"""Indlæsning af testdata. Ét sted, så værktøjer og test læser det samme."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(root: Path = ROOT) -> dict:
    room = root / "dataroom"
    finds: list[dict] = []
    for name in ("designed.json", "noise.json"):
        path = room / "finds" / name
        if path.exists():
            finds.extend(_load(path))
    finds.sort(key=lambda f: (f.get("time", ""), f.get("id", "")))
    archive: list[dict] = []
    for name in ("archive.json", "archive_more.json"):
        path = room / "finds" / name
        if path.exists():
            archive.extend(_load(path))
    key = _load(room / "key.json") if (room / "key.json").exists() else {"events": [], "finds": {}, "links": []}
    return {"world": _load(room / "world.json"), "finds": finds, "archive": archive, "key": key}
