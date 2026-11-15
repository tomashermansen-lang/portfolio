"""A small Gherkin reader and step runner, standard library only.

Reads .feature files (Feature, Background, Scenario, Given/When/Then/And/But,
@tags), binds steps to functions by regular expression, runs every scenario
with its background, and returns one result per scenario. Used by
tools/spec_runner.py; tools/spec_runner.js does the same for the UI features.
"""
from __future__ import annotations

import re
import traceback
from pathlib import Path

STEP_WORDS = ("Given", "When", "Then", "And", "But")


def parse(path: Path) -> dict:
    feature = {"file": path.name, "name": "", "background": [], "scenarios": []}
    tags: list[str] = []
    current = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            tags = line.split()
            continue
        if line.startswith("Feature:"):
            feature["name"] = line[len("Feature:"):].strip(); current = None; continue
        if line.startswith("Background:"):
            current = feature["background"]; continue
        if line.startswith("Scenario:"):
            sc = {"name": line[len("Scenario:"):].strip(), "tags": tags, "steps": []}
            tags = []
            feature["scenarios"].append(sc); current = sc["steps"]; continue
        word = line.split(" ", 1)[0]
        if word in STEP_WORDS and current is not None:
            current.append(line.split(" ", 1)[1].strip())
    return feature


class Steps:
    def __init__(self):
        self.table: list[tuple[re.Pattern, object]] = []

    def __call__(self, pattern: str):
        def deco(fn):
            self.table.append((re.compile("^" + pattern + "$"), fn)); return fn
        return deco

    def find(self, text: str):
        for rx, fn in self.table:
            m = rx.match(text)
            if m:
                return fn, m.groups()
        raise KeyError(f"no step matches: {text}")


def run(features: list[Path], steps: Steps) -> list[dict]:
    results = []
    for path in features:
        f = parse(path)
        for sc in f["scenarios"]:
            ctx: dict = {}
            status, failed, error = "passed", None, None
            if "@pending" in sc["tags"]:
                results.append({"feature": f["name"], "file": f["file"], "scenario": sc["name"], "tags": sc["tags"],
                                "steps": len(f["background"]) + len(sc["steps"]), "status": "pending", "failed_step": None, "error": None})
                continue
            for text in f["background"] + sc["steps"]:
                try:
                    fn, groups = steps.find(text)
                    fn(ctx, *groups)
                except Exception as e:  # noqa: BLE001
                    status, failed, error = "failed", text, f"{type(e).__name__}: {e}"
                    if not isinstance(e, (AssertionError, KeyError)):
                        error += "\n" + traceback.format_exc(limit=2)
                    break
            results.append({"feature": f["name"], "file": f["file"], "scenario": sc["name"], "tags": sc["tags"],
                            "steps": len(f["background"]) + len(sc["steps"]), "status": status, "failed_step": failed, "error": error})
    return results
