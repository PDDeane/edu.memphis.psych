# Running the rubric migration for real

The dry run (2026-09-13 → 2026-09-16, `~/code/migration_dryrun`) carried stages
00–08 to their gates on a sandbox copy. This directory is what that produced:
every script, golden, verifier and hand-written product needed to do it again on
the live tree. `RUBRIC_MIGRATION_PLAN.md` is the design and the trap list;
this file is the order of operations.

## What the migration actually does

It **deletes `scoring/rubric_h1.py`, `rubric_h2.py`, `rubric_h3.py`** and
replaces them with `scoring/rubric_reader.py`, which reads the same rubric out of
the `.olx`. `RUBRIC_DECISIONS.md` records every judgement made while moving it.
The `.olx` bodies and all 26 `prompt_sha` values must come out **byte-identical**;
that is the whole acceptance argument, and it is why a sweep is not scheduled.

## THIS IS NOT A REPLAY. Re-baseline first.

The dry run forked on **2026-09-13 20:50**. Since then the live tree has moved:
2 commits and (at the time of writing) 27 uncommitted changes, touching
`rubric_h1.py`, `rubric_h2.py`, `enforcement.py`, `equivalence.py`,
`olx_prompts.py`, `handouts.py`, `measured.py`, `precommit_gate.py` and others.
The rubric files also now carry **corpus references** from the history rewrite,
which did not exist when the dry run read them.

Replaying the dry run's goldens against that tree would migrate a rubric that no
longer exists, and — because the comparison is against *frozen* oracles — it
would do so while reporting everything green. So:

1. **Land the history rewrite first.** The migration edits the same files. Doing
   both at once makes every byte comparison unreadable.
2. **Re-freeze every golden from the CURRENT tree** (`stage00_freeze_oracles.py`,
   `stage00_capture_baseline.py`). The files in `goldens/` are the dry run's and
   are kept for reference and diffing, **not** for acceptance.
3. **Re-run `stage00_registry.py`** — the inventory of consumers. Three empty
   modules were removed during the dry run; confirm that still holds.
4. **Diff the new goldens against the dry run's.** Where they differ, understand
   why before proceeding. A difference is information, not an obstacle.

**`DRIFT.md` is the companion to this file**: what changed in live since the
fork, and which stage each change lands on. Read it before stage 00 and
re-derive it — it is a snapshot, not a constant.

## Preconditions

* `git status` clean, or every pending change understood — the migration deletes
  three files and rewrites several.
* `source migration/env.sh` in every shell. It resolves `MIGRATION_ROOT` from its
  own location and **refuses to run if that resolves to a sandbox**.
* `precommit_gate.py` passes. The tree must not be carrying student text before
  a migration starts moving text around.
* The engine (`$LO_BLOCKS`) builds: `npm run build` green.

## Order of operations

| stage | script | gate |
|---|---|---|
| 00 | `stage00_registry.py`, `stage00_capture_baseline.py`, `stage00_freeze_oracles.py` | inventory enumerates every consumer; baseline finding-set committed |
| 01 | `stage01_recount_coupling.py`, `stage01_gate.py` | count re-measured; every coupled check has a disposition |
| 02 | `stage02_assembler_surface.py`, `stage02_gate.py` | all 26 bodies byte-exact from hand-built structures |
| 03a/b | `stage03a_gate.py`, `stage03b_gate.py` | blocks parse and validate; engine stays content-neutral |
| 04 | `stage04_migrate_rubric.py`, `stage04_gate.py` | all 26 byte-equal; second run reports no edits |
| 05 | `stage05_complete_rubric.py`, `stage05_rubric_equivalence.py`, `stage05_gate.py` | every `.olx` byte identical; all three `prompt_sha` families unchanged |
| 06 | `stage06_freeze_rubric_oracle.py`, `stage06b_*`, `stage06c_*` | `fingerprint_text` unchanged; selftest accounts for exactly `SELFTEST_EXPECTED` |
| 07 | `stage07_prose_mentions.py`, `stage07_gate.py` | prose mentions split by tense; suite green |
| 08 | `stage08_acceptance.py`, `e2e_session.sh`, `student_session.sh` | six rows green |

**Products to install** (`products/`, hand-written — no script regenerates them):
`rubric_reader.py`, `selftest_injections.py`, `RUBRIC_DECISIONS.md`.

## Stage 08 is six rows, and two of them run the release

Four instruments compare bytes: prompt oracles, `fingerprint_text`, the served
`idmap` prompt, corpus replay. **All four pass on a build whose handouts do not
render**, because a page that renders nothing has the same bytes as one that
renders (T21). So two more instruments run it:

* `e2e_session.sh` — one participant through all 26 items, scorer side.
* `student_session.sh` — a student clicking the course and all three handouts in
  a browser, answering every input, pressing every feedback button.

Both report **NOT RUN** rather than PASS when their artefact is missing. The
browser one needs a server, and the client **refuses to boot on a port that is
not in `WS_PORT_MAP`** (T22/T22a) — on an unlisted port every page reads
"Failed to start", while the scorer-side row still passes perfectly.

## Read these before starting

* `RUBRIC_MIGRATION_PLAN.md` §10 — traps T1–T26. T21–T26 are stage 08's.
* `scoring/QUALITY_CONTROL.md` §6a/6b/6c — trusting an instrument; a byte
  comparison cannot tell you the thing runs; a scan only finds what its
  reference set contains.
* `~/code/scripts/history_rewrite/README.md` — a separate workstream, but its
  two lessons generalise: a check whose reference set is its own output proves
  nothing, and always run the positive control.
