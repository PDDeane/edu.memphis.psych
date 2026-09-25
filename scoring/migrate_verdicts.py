#!/usr/bin/env python3
"""Verdict standardisation: move slots onto the canonical vocabulary.

Run twice so far, for the two halves of stage 02.

  1. Retire `verdicts=`. A block could redefine the default verdict list for
     every slot in it that did not spell its own — the override hatch that made
     "the canonical vocabulary" advisory. Every inheriting slot was rewritten to
     state its options, and the attribute deleted.

  2. Shorten what can be shortened. A judgement is `met`, `absent`, then extras,
     so it can be written as just its extras (`key:Label:unclear`) or as nothing
     at all. Anything whose first two options are not met/absent is an identity,
     a count, or a yes/no spelling that has not moved yet, and is left verbatim
     for a later stage — this script only makes changes it can prove are inert.

THE CHECK, which is the reason this is a script at all: parse before, parse
after, and refuse to write unless EVERY slot in every block resolves to the same
option list. A rewrite that would change what the model is asked does not get
written; it gets reported. Idempotent — a second run reports no edits.

    ./migrate_verdicts.py            # report, touch nothing
    ./migrate_verdicts.py --write    # rewrite in place

The vocabulary itself is read out of lo-blocks' slotSheet.ts rather than copied,
for the same reason agreement._ts_literal reads its schema descriptions there: a
copy is the thing that drifts, and this one would drift silently.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import paths

import olx_prompts  # for the vocabulary, read from slotSheet.ts
import paths as _p7   # J-7b: this course's handout file names

# Read, never copied — the same reason olx_prompts reads them.
ENGINE_DEFAULT = olx_prompts.default_verdicts()
EXTRAS = olx_prompts.extra_verdicts()

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
        seg = parts[2] if len(parts) >= 3 else None
        out.append((key, olx_prompts.resolve_options(seg, default)))
    return out


def shorten(opts: list[str]) -> str | None:
    """The concise spelling of an option list, or None to leave it alone.

    A judgement is `met`, `absent`, then extras — so it can be written as just
    its extras, or as nothing at all. Anything else is an identity or count
    vocabulary that has not moved out of `verdict` yet; left verbatim.
    """
    if opts[:2] != ENGINE_DEFAULT:
        return None
    extras = opts[2:]
    if any(e not in EXTRAS for e in extras):
        return None
    return "/".join(extras)


def rewrite_slots(slots_attr: str, default: list[str]) -> str:
    """Rewrite explicit judgement lists in the concise extras form."""
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
        if len(parts) < 3 or not parts[2].strip():
            pieces.append(raw)                       # already bare
            continue
        opts = [o.strip() for o in parts[2].split("/") if o.strip()]
        short = shorten(opts)
        if short is None:
            pieces.append(raw)                       # identity/count — not yet
            continue
        tail = f":{short}" if short else ""
        pieces.append(f"{parts[0]}:{parts[1]}{tail}{pts}")
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
            notes.append(f"  {bid.group(1) if bid else tag}: shortened")
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

    files = sorted((paths.OLX_DIR).glob(_p7.handout_olx_glob()))
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
