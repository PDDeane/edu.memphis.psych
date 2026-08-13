#!/usr/bin/env python3
"""Verdict standardisation, step 1: make every slot's verdicts explicit.

WHAT THIS DOES. Each sheet-bearing block may carry a `verdicts=` attribute that
redefines the default verdict list for every slot in it that does not spell its
own. That is the override hatch the standardisation exists to close: while it
is there, "the canonical vocabulary" is advisory. This rewrites every slot that
was relying on a default — the block's or the engine's — to state its options
itself, then deletes the attribute.

WHY THIS STEP IS SEPARATE. It is provably score-neutral, and the proof is cheap:
the RESOLVED option list of every slot is identical before and after, so nothing
the model is asked or the grader computes can have moved. Concision comes next,
in the step that introduces the extras form (`key:Label:unclear`) and flips the
engine default; keeping the two apart means the risky half is a one-line default
change with no content in flight, rather than 182 rewrites and a default change
landing together across two repositories.

    ./migrate_verdicts.py --check    # report, touch nothing
    ./migrate_verdicts.py --write    # rewrite in place

The check the whole thing rests on runs either way: parse before, parse after,
and refuse to write unless every slot in every block resolves to the same list.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import paths

ENGINE_DEFAULT = ["met", "absent", "unclear"]  # lib/llm/slotSheet.ts:DEFAULT_VERDICTS

BLOCK_RE = re.compile(r"<(LLMAction|DerivedChecks)\b(.*?)(/?)>", re.S)
SLOTS_RE = re.compile(r'slots="([^"]*)"', re.S)
VERDICTS_RE = re.compile(r'\s*verdicts="([^"]*)"', re.S)
PTS_RE = re.compile(r"@(-?\d+(?:\.\d+)?)\s*$")


def resolve(slots_attr: str, default: list[str]) -> list[tuple[str, list[str]]]:
    """(key, resolved options) for each slot — the engine's own parseSlots rule."""
    out = []
    for entry in slots_attr.split("|"):
        e = entry.strip()
        if not e:
            continue
        e = PTS_RE.sub("", e).strip()
        parts = e.split(":")
        key = parts[0].strip()
        if len(parts) >= 3 and parts[2].strip():
            opts = [o.strip() for o in parts[2].split("/") if o.strip()]
        else:
            opts = list(default)
        out.append((key, opts))
    return out


def rewrite_slots(slots_attr: str, default: list[str]) -> str:
    """Spell out the options of any slot that was inheriting them."""
    pieces = []
    for entry in slots_attr.split("|"):
        raw = entry
        e = entry.strip()
        if not e:
            pieces.append(raw)
            continue
        m = PTS_RE.search(e)
        pts = m.group(0) if m else ""
        body = PTS_RE.sub("", e).strip()
        parts = body.split(":")
        if len(parts) >= 3 and parts[2].strip():
            pieces.append(raw)                       # already explicit
            continue
        # key:Label (or a bare key) — append the list it was inheriting.
        if len(parts) == 1:
            parts.append(parts[0])                   # label defaults to the key
        pieces.append(f"{parts[0]}:{parts[1]}:{'/'.join(default)}{pts}")
    return "|".join(pieces)


def process(src: str) -> tuple[str, list[str]]:
    notes: list[str] = []

    def one(m: re.Match) -> str:
        tag, attrs, close = m.group(1), m.group(2), m.group(3)
        sm = SLOTS_RE.search(attrs)
        if not sm:
            return m.group(0)
        vm = VERDICTS_RE.search(attrs)
        default = ([v.strip() for v in vm.group(1).split(",") if v.strip()]
                   if vm else list(ENGINE_DEFAULT))
        bid = re.search(r'id="([^"]+)"', attrs)
        new_slots = rewrite_slots(sm.group(1), default)
        if new_slots != sm.group(1):
            notes.append(f"  {bid.group(1) if bid else tag}: spelled out "
                         f"{'/'.join(default)}")
        attrs2 = attrs[:sm.start(1)] + new_slots + attrs[sm.end(1):]
        if vm:
            # Recompute the span against the rewritten string.
            vm2 = VERDICTS_RE.search(attrs2)
            attrs2 = attrs2[:vm2.start()] + attrs2[vm2.end():]
            notes.append(f"  {bid.group(1) if bid else tag}: dropped verdicts=")
        return f"<{tag}{attrs2}{close}>"

    return BLOCK_RE.sub(one, src), notes


def slot_table(src: str) -> dict[str, list[str]]:
    """Every slot's resolved options, keyed block-wise — the neutrality witness."""
    table: dict[str, list[str]] = {}
    for m in BLOCK_RE.finditer(src):
        attrs = m.group(2)
        sm = SLOTS_RE.search(attrs)
        if not sm:
            continue
        vm = VERDICTS_RE.search(attrs)
        default = ([v.strip() for v in vm.group(1).split(",") if v.strip()]
                   if vm else list(ENGINE_DEFAULT))
        bid = re.search(r'id="([^"]+)"', attrs)
        blk = bid.group(1) if bid else f"?{m.start()}"
        for key, opts in resolve(sm.group(1), default):
            table[f"{blk}.{key}"] = opts
    return table


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="rewrite in place")
    args = ap.parse_args()

    files = sorted((paths.OLX_DIR).glob("bmod_handout*.olx"))
    if not files:
        print(f"no handouts under {paths.OLX_DIR}", file=sys.stderr)
        return 2

    total_slots = changed_blocks = 0
    for f in files:
        src = f.read_text()
        before = slot_table(src)
        out, notes = process(src)
        after = slot_table(out)

        # THE CHECK. Not "looks right" — every slot resolves to the same list, or
        # nothing is written.
        if before != after:
            drift = [k for k in sorted(set(before) | set(after))
                     if before.get(k) != after.get(k)]
            print(f"REFUSING TO WRITE — {f.name}: {len(drift)} slot(s) changed "
                  f"their resolved verdicts:", file=sys.stderr)
            for k in drift[:10]:
                print(f"    {k}: {before.get(k)} -> {after.get(k)}", file=sys.stderr)
            return 1

        total_slots += len(before)
        changed_blocks += len(notes)
        print(f"{f.name}: {len(before)} slots, {len(notes)} edit(s)")
        for n in notes:
            print(n)
        if args.write and out != src:
            f.write_text(out)

    print(f"\n{total_slots} slots checked, {changed_blocks} edits, "
          f"resolved verdicts identical{'' if args.write else ' (dry run)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
