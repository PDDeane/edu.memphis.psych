#!/usr/bin/env python3
"""Verdict standardisation, stage 03: rename onto the canonical vocabulary.

Three renames, all of which preserve WHICH value means satisfied:

  1. yes/no -> met/absent.  60 slots spell the same judgement with different
     words. `yes` is their satisfied value, so it becomes `met`.

  2. `uncertain` -> `confident`, INVERTED.  Its options are `no/yes` with `no`
     first: the satisfied state is "not unsure". Mapping yes->met would make the
     good state `absent`, so this one maps no->met, yes->absent, and the check is
     renamed and relabelled to match — "All judgments confident".

     Two other checks are also written backwards, `thin_reason` and
     `avoidance_frame`. Un-inverting one means restating its label so that `met`
     is the good state, and `thin_reason`'s label currently describes the BAD
     state ("Either reason is present but weak"). That is student-facing wording
     rather than a mechanical edit, so both are reported and left alone until it
     is decided. Polarity-by-ordering is therefore reduced, not yet eliminated.

  3. Item-local failure reasons onto the canonical six.  not_antecedent,
     not_active, not_consequence and not_reason all say "the content is not the
     kind of thing asked for" and become `wrong_kind`; `not_described` becomes
     `incomplete`.

THE CHECK is necessarily different from the earlier pass, which asserted the
resolved options were IDENTICAL — a rename changes them by construction. What is
asserted instead, per slot:

  * points unchanged;
  * the option COUNT unchanged, so nothing gained an escape hatch or lost a
    diagnosis;
  * the old satisfied value (index 0) maps to the new satisfied value;
  * every renamed judgement ends up satisfied-by `met`.

Structurally that makes the rename score-neutral. It is NOT behaviour-neutral:
the generated checklist lists each check's verdicts, so every one of these
prompts changes, and only the 3-run sweep can speak to what the model does with
them.

    ./canonicalise_verdicts.py            # report, touch nothing
    ./canonicalise_verdicts.py --write    # rewrite in place
"""
from __future__ import annotations

import argparse
import re
import sys

import olx_prompts
import paths

MET, ABSENT = "met", "absent"

# Reasons that mean the same thing across items, and the canonical name.
REASON_RENAME = {
    "not_antecedent": "wrong_kind",
    "not_active": "wrong_kind",
    "not_consequence": "wrong_kind",
    "not_reason": "wrong_kind",
    "not_described": "incomplete",
}

# Checks whose satisfied value is `no`, i.e. whose meaning is written backwards.
# Un-inverting one means restating its label so that `met` is the good state, and
# that is student-facing wording, not a mechanical edit. Only the check whose
# wording has been decided is listed; the others are reported and left alone
# rather than having a label invented for them.
INVERTED = {
    "uncertain": ("confident", "All judgments confident"),
    # Advisory flags: `yes` meant "a remark is warranted", so the good state was
    # `no`. Relabelled so `met` is the good state. `phrased_directly` keeps its
    # label, which already described the good state — only its KEY named the bad
    # one. The python still calls that input `avoidance_frame`; enforcement.ALIAS
    # carries the correspondence, which is what that table is for.
    "thin_reason": ("reasons_substantial", "Both reasons are substantial"),
    "avoidance_frame": ("phrased_directly",
                        "Phrased directly rather than by what is avoided"),
}

BLOCK_RE = re.compile(r"<(LLMAction|DerivedChecks)\b(.*?)(/?)>", re.S)
SLOTS_RE = re.compile(r'slots="([^"]*)"', re.S)
PTS_RE = re.compile(r"@(-?\d+(?:\.\d+)?)\s*$")


def split_slot(entry: str):
    """(key, gates, label, options, pts_suffix) for one authored slot."""
    m = PTS_RE.search(entry)
    pts = m.group(0) if m else ""
    body = PTS_RE.sub("", entry).strip()
    parts = body.split(":")
    raw_key = parts[0].strip()
    label = parts[1].strip() if len(parts) > 1 else raw_key
    seg = parts[2].strip() if len(parts) > 2 and parts[2].strip() else None
    opts = olx_prompts.resolve_options(seg, olx_prompts.default_verdicts())
    return raw_key.lstrip("!"), raw_key.startswith("!"), label, opts, pts


def is_count(opts: list[str]) -> bool:
    """A verdict list that is really a measurement: every option a digit."""
    return len(opts) > 1 and all(o.isdigit() for o in opts)


def rename_options(key: str, opts: list[str]) -> tuple[str, str | None, list[str]]:
    """New (key, label-or-None, options) for a slot."""
    if is_count(opts):
        return key, None, list(opts)          # handled by the count branch
    # 2. A backwards-written check, if its replacement wording is settled.
    if opts and opts[0] == "no":
        if key not in INVERTED:
            return key, None, list(opts)          # left alone; reported below
        new_key, new_label = INVERTED[key]
        return new_key, new_label, [MET if o == "no" else ABSENT for o in opts]

    new = []
    for o in opts:
        if o == "yes":
            new.append(MET)                  # 1. yes/no -> met/absent
        elif o == "no":
            new.append(ABSENT)
        else:
            new.append(REASON_RENAME.get(o, o))   # 3. canonical reasons
    return key, None, new


def concise(opts: list[str]) -> str:
    """Write a judgement as its extras; anything else verbatim."""
    default = olx_prompts.default_verdicts()
    extras = olx_prompts.extra_verdicts()
    if opts[:2] == default and all(o in extras for o in opts[2:]):
        return "/".join(opts[2:])
    return "/".join(opts)


def process(src: str) -> tuple[str, list[str], list[str]]:
    notes: list[str] = []
    problems: list[str] = []
    deferred: set[str] = set()

    def one(m: re.Match) -> str:
        tag, attrs, close = m.group(1), m.group(2), m.group(3)
        sm = SLOTS_RE.search(attrs)
        if not sm:
            return m.group(0)
        bid = re.search(r'id="([^"]+)"', attrs)
        blk = bid.group(1) if bid else tag

        pieces = []
        for entry in sm.group(1).split("|"):
            e = entry.strip()
            if not e:
                pieces.append(entry)
                continue
            key, gates, label, opts, pts = split_slot(e)
            new_key, new_label, new_opts = rename_options(key, opts)

            # ---- the per-slot check -------------------------------------
            if len(new_opts) != len(opts):
                problems.append(f"{blk}.{key}: option count {len(opts)} -> {len(new_opts)}")
            if new_opts and opts and new_opts[0] != rename_options(key, [opts[0]])[2][0]:
                problems.append(f"{blk}.{key}: satisfied value moved")
            if new_opts != opts and not is_count(opts) and new_opts[0] != MET:
                problems.append(f"{blk}.{key}: renamed but not satisfied-by met "
                                f"({'/'.join(new_opts)})")

            if opts and opts[0] == "no" and key not in INVERTED:
                deferred.add(f"{key} ({'/'.join(opts)}) — {label}")
            if new_opts == opts and new_key == key and not is_count(opts):
                pieces.append(entry)                       # untouched
                continue

            if is_count(opts):
                # 3/2/1/0, 2/1/0 and 0/1/2/3 all mean 0..max; the direction they
                # were written in never meant anything the engine read.
                tail = f"count({max(int(o) for o in opts)})"
            else:
                tail = concise(new_opts)
            bang = "!" if gates else ""
            pieces.append(f"{bang}{new_key}:{new_label or label}"
                          + (f":{tail}" if tail else "") + pts)
            notes.append(f"  {blk}.{key}: {'/'.join(opts)} -> "
                         f"{tail if is_count(opts) else '/'.join(new_opts)}"
                         + (f"  (key -> {new_key})" if new_key != key else ""))

        new_slots = "|".join(pieces)
        attrs2 = attrs[:sm.start(1)] + new_slots + attrs[sm.end(1):]
        return f"<{tag}{attrs2}{close}>"

    return BLOCK_RE.sub(one, src), notes, problems, deferred


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    total = 0
    for f in sorted(paths.OLX_DIR.glob("bmod_handout*.olx")):
        src = f.read_text()
        out, notes, problems, deferred = process(src)
        if problems:
            print(f"REFUSING TO WRITE — {f.name}:", file=sys.stderr)
            for p in problems[:12]:
                print(f"    {p}", file=sys.stderr)
            return 1
        total += len(notes)
        print(f"{f.name}: {len(notes)} slot(s) renamed")
        for d in sorted(deferred):
            print(f"  DEFERRED — backwards-written, needs label wording: {d}")
        if args.verbose:
            for n in notes:
                print(n)
        if args.write and out != src:
            f.write_text(out)

    print(f"\n{total} slots renamed, satisfied value preserved on every one"
          f"{'' if args.write else ' (dry run)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
