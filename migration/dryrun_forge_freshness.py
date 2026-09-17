import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
#!/usr/bin/env python3
"""DRY RUN ONLY — stamp current shas onto stale columns WITHOUT measuring them.

WHAT THIS DOES, IN PLAIN WORDS: it makes the ledger LIE. It writes today's
`prompt_sha` onto runs that answered a question which no longer ships, so a
column reports fresh when nothing re-measured it. §7a names this exact act as
the thing that "destroys the evidence that a sweep was owed", and it is right.

WHY IT EXISTS ANYWAY: the migration dry run has to exercise stages 01-08 against
a ledger that satisfies stage 00's entry condition. Really satisfying it costs
~120 calls per column per side. In a THROWAWAY COPY, buying that with real money
proves nothing the later stages need -- what they need is a ledger shaped like a
fresh one, so the scripts, gates and ordering can be tested end to end.

WHY IT IS SAFE ONLY HERE, and the guards that keep it that way:

  1. It REFUSES to touch anything outside the dry-run sandbox. The path is
     resolved and must sit under DRYRUN_ROOT; a ledger under
     `edu.memphis.psych` is refused by name as well, so a wrong argument cannot
     reach the real one even if someone moves the sandbox.
  2. Every entry it touches is marked `dryrun_fabricated`, with the reason and
     the sha it displaced. The lie is written down INSIDE the lie.
  3. The ledger gains a top-level `DRYRUN_FABRICATED_LEDGER` banner, so anything
     reading it can tell in one key that these numbers are not measurements.
  4. It writes `FABRICATED.txt` beside the ledger, because a marker inside a
     JSON file is easy to miss when someone copies the file somewhere else.
  5. It backs the ledger up first and prints how to undo it.

NOTHING PRODUCED DOWNSTREAM OF THIS IS EVIDENCE. Not a rate, not a band, not a
median, not a "wrong cell". If a dry-run figure is ever quoted about the real
corpus, that is this script's failure and the banner exists to prevent it.
"""
import argparse, json, shutil, sys
from pathlib import Path

DRYRUN_ROOT = MP.ROOT
BANNER = "DRYRUN_FABRICATED_LEDGER"
FORBIDDEN = ("edu.memphis.psych",)


def refuse_unless_sandbox(ledger: Path) -> None:
    r = ledger.resolve()
    for bad in FORBIDDEN:
        if bad in r.parts:
            raise SystemExit(f"REFUSED: {r} is the REAL repository. This script "
                             f"fabricates freshness and must never touch it.")
    if DRYRUN_ROOT not in r.parents:
        raise SystemExit(f"REFUSED: {r} is not under {DRYRUN_ROOT}. This script "
                         f"runs only inside the dry-run sandbox.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--sides", default="paper")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    scoring = Path(a.scoring)
    ledger = scoring / "MEASURED.json"
    refuse_unless_sandbox(ledger)
    sys.path.insert(0, str(scoring.resolve()))
    import measured as M

    plan = []
    for side in a.sides.split(","):
        for item, msg in M.status(side):
            if msg.startswith("ok"):
                continue
            plan.append((item, side, msg.split("—")[0].strip(), msg))
    if not plan:
        print("nothing stale — the ledger already satisfies the entry condition")
        return 0

    print(f"WOULD FABRICATE FRESHNESS for {len(plan)} column(s):")
    for item, side, kind, msg in plan:
        print(f"   {item}/{side}: {msg[:88]}")
    if not a.apply:
        print("\n(dry list only — pass --apply to write it)")
        return 0

    shutil.copy2(ledger, ledger.with_suffix(".json.pre_fabrication"))
    doc = json.loads(ledger.read_text())
    touched = 0
    for item, side, kind, msg in plan:
        # LAYOUT IS items[item][side], not [side][item]. The first version
        # assumed the latter, found nothing, and cheerfully reported "fabricated
        # freshness on 0 column(s)" while writing the banner — a no-op that
        # announced success. A writer that cannot find its target must say so.
        entry = ((doc.get("items") or {}).get(item) or {}).get(side)
        if entry is None:
            print(f"   ! {item}/{side}: no ledger entry to stamp — skipped")
            continue
        was_p, was_s = entry.get("prompt_sha"), entry.get("scorer_sha")
        entry["prompt_sha"] = M.prompt_sha(item, side)
        entry["scorer_sha"] = M.scorer_sha(item, side)
        ask = M.ask_sha(item, side)
        if ask:
            entry["ask_sha"] = ask
        entry["dryrun_fabricated"] = {
            "why": "DRY RUN ONLY. No sweep was run. Today's shas were stamped "
                   "onto runs measured under an older prompt so the migration "
                   "dry run could exercise stages 01-08 without spending calls.",
            "displaced_prompt_sha": was_p,
            "displaced_scorer_sha": was_s,
            "was": msg,
            "not_evidence": "No figure derived from this column describes the "
                            "real corpus.",
        }
        touched += 1
    doc[BANNER] = (
        "THIS LEDGER CONTAINS FABRICATED FRESHNESS. One or more columns carry "
        "today's prompt_sha over runs that were never re-measured. It exists to "
        "exercise the migration dry run without spending a sweep. NOTHING in it "
        "is evidence about the real corpus, and it must never be copied into "
        "edu.memphis.psych. See the per-entry `dryrun_fabricated` keys."
    )
    if not touched:
        raise SystemExit("REFUSED: nothing was stamped, so the ledger is "
                         "unchanged and the banner would be a lie about a lie. "
                         "Check the layout before re-running.")
    ledger.write_text(json.dumps(doc, indent=1, sort_keys=True))
    (scoring / "FABRICATED.txt").write_text(
        "This scoring tree's MEASURED.json carries FABRICATED freshness.\n"
        f"{touched} column(s) were stamped with today's shas WITHOUT a sweep.\n"
        "It is a migration dry-run sandbox. Nothing here is evidence.\n"
        f"Undo: mv MEASURED.json.pre_fabrication MEASURED.json\n")
    print(f"\nfabricated freshness on {touched} column(s)")
    print(f"  banner key   : {BANNER}")
    print(f"  backup       : {ledger.name}.pre_fabrication")
    print(f"  undo         : mv {ledger}.pre_fabrication {ledger}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
