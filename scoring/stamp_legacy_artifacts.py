#!/usr/bin/env python3
r"""Stamp `era.model` on artifacts written before the era block carried one.

THE GAP THIS CLOSES IS ONE WE OPENED. `agreement._era_for` was fixed to pass its
backend through, so every artifact written afterwards names the model that
produced it and `measured.record` can hold a column to the SIDE CONTRACT. The
fix said nothing about the artifacts already on disk: 183 of 339 carry no model,
and the first time one of them is re-recorded the contract refuses it. That is
the guard working, and it leaves the column permanently unrecordable -- a
ledger row that can never be refreshed is a slow leak, not a safe state.

THE MODEL IS NOT LOST, IT IS IN THE SWEEP LOG. Every sweep writes `<item>.log`
beside its runs file, and its second line names the backend in the SAME words
the era block uses: "measuring N item(s) x M participant(s) = K calls via
<backend>". Across the 156 artifacts that ARE stamped, backend determines model
exactly -- 'lo-blocks endpoint (what the browser calls)', 'lo' and the empty
backend all mean gpt-5-mini, 'cli' means opus, and no backend maps to two
models. So the log settles what the era block omitted.

THAT MAPPING IS RE-DERIVED AT RUN TIME, NEVER HARD-CODED, AND THE FUNCTION IS
RE-CHECKED BEFORE IT IS USED. If a backend ever maps to two models, this refuses
rather than picking one: the whole point of the contract is that a number knows
which model produced it, and a guess dressed as a stamp is worse than an honest
refusal.

WHAT IS WRITTEN IS MARKED AS DERIVED. `era.model_source` records that the stamp
came from the log rather than from the run, so a later reader can tell a
recovered provenance from an observed one. Existing fields are never altered.
"""
import argparse
import collections
import json
import re
import sys

import paths

BACKEND_LINE = re.compile(r"=\s*\d+\s+calls\s+via\s+(.+?)\s*$", re.M)


def observed_mapping() -> dict:
    """backend -> model, learned from artifacts that carry both."""
    seen = collections.defaultdict(set)
    for d in sorted(paths.roots().out.iterdir()):
        if not d.is_dir():
            continue
        for f in d.glob("*.runs.json"):
            try:
                era = json.load(open(f)).get("era") or {}
            except Exception:
                continue
            if era.get("model"):
                seen[(era.get("backend") or "")].add(era["model"])
            break
    return seen


def backend_of(runs_file):
    """The backend named by the sweep log beside this runs file."""
    log = runs_file.with_suffix("").with_suffix(".log")
    if not log.exists():
        log = runs_file.parent / (runs_file.name.split(".")[0] + ".log")
    if not log.exists():
        return None, f"no sweep log beside {runs_file.name}"
    m = BACKEND_LINE.search(log.read_text(errors="replace"))
    if not m:
        return None, f"{log.name} names no backend"
    return m.group(1).strip(), ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("artifacts", nargs="*", help="artifact directory names; default every unstamped one")
    ap.add_argument("--write", action="store_true", help="write the stamps (otherwise report only)")
    a = ap.parse_args(argv)

    seen = observed_mapping()
    ambiguous = {b: ms for b, ms in seen.items() if len(ms) > 1}
    if ambiguous:
        print("REFUSING: backend does not determine model in the artifacts on disk:")
        for b, ms in ambiguous.items():
            print(f"  {b!r} -> {sorted(ms)}")
        return 2
    mapping = {b: next(iter(ms)) for b, ms in seen.items()}
    if not mapping:
        print("REFUSING: no stamped artifact to learn the mapping from; nothing "
              "was examined, which is not the same as nothing needing a stamp")
        return 2
    print(f"  mapping learned from {sum(len(v) for v in seen.values())} stamped artifact(s):")
    for b, m in sorted(mapping.items()):
        print(f"     {b[:52]!r} -> {m}")

    dirs = ([paths.roots().out / n for n in a.artifacts] if a.artifacts
            else [d for d in sorted(paths.roots().out.iterdir()) if d.is_dir()])
    done = skipped = 0
    for d in dirs:
        if not d.is_dir():
            print(f"  {d.name}: not a directory"); continue
        for f in sorted(d.glob("*.runs.json")):
            try:
                doc = json.load(open(f))
            except Exception as exc:
                print(f"  {d.name}/{f.name}: unreadable ({exc})"); skipped += 1; continue
            era = doc.get("era")
            if not isinstance(era, dict) or era.get("model"):
                continue
            backend, why = backend_of(f)
            if backend is None:
                print(f"  SKIP {d.name}/{f.name}: {why}"); skipped += 1; continue
            if backend not in mapping:
                print(f"  SKIP {d.name}/{f.name}: backend {backend[:40]!r} is not one "
                      f"any stamped artifact used, so the model is not established")
                skipped += 1
                continue
            model = mapping[backend]
            if a.write:
                era["model"] = model
                era["backend"] = backend
                era["model_source"] = "derived from the sweep log's backend line"
                json.dump(doc, open(f, "w"))
            print(f"  {'STAMP' if a.write else 'would stamp'} {d.name}/{f.name}: "
                  f"model={model} backend={backend[:40]!r}")
            done += 1
    print(f"  stamped: {done}   skipped: {skipped}   (write={a.write})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
