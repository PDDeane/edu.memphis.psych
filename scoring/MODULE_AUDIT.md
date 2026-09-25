# Module audit — the precondition for J and K

## Summary

76 modules read. **STATUS 2026-09-24: J's stated blocker is CLEARED and the
detailed work has moved into `RUBRIC_MIGRATION_PLAN.md`.**

This document is the AUDIT -- what was measured, and the corrections to it.
The prepared work it produced (J's six fixes, the 786-reference disposition,
E's plugin design, goal M) now lives with its goals in the migration plan,
because a plan that drifts from the audit behind it is worse than either.

- **K.** The 189 enforcement checks have three fates, not two: port the
  rubric-structural majority (~133) to TS, DELETE the ~8 python-vs-web parity
  checks the change makes vacuous, and LEAVE the ~48 whose subject is the python
  source tree. §2.
- **J.** `scoring/materials/` holds 4.1 MB of this course's handouts, decks,
  dictionaries and the PSYC 1030 syllabus — course content inside the engine
  root, named by four embedded filenames in engine code. §9.
- **One defect fixed.** `goals_restructure.py` resolved GOALS.md by `__file__` and
  so read the 53-line generic stub, reporting "round trip clean" over the wrong
  file. Fixed; it now reads the real 16,774-line document and is still clean. §8.
- **One question for you.** QUALITY_CONTROL.md is declared a split document but
  has no course half, and the project's own prose rule can justify either
  answer. I did not decide it. §6.
- **Two blind spots in the ratchet.** Course content held as DATA in code is
  invisible to every arm of it — vocabulary reads docstrings only (F1), and
  handout filenames in an f-string dict count as nothing (§9).

Measured 2026-09-24 on the dry-run tree. 76 modules, 133 units of course signal
as `tools/course_inventory` counts it (tables 58, literal_ids 27, vocabulary 40,
named 8 — totals reproduced exactly against the ratchet's own run).

## 1. Where the course sits in the engine

| category | modules | loc | course signal |
|---|---:|---:|---:|
| COURSE-CONTENT (`*_source.py` builders) | 5 | 3,547 | 53 |
| SEAM (paths/coursedata/handouts/rubric_*) | 6 | 3,742 | 2 |
| ONE-OFF? (migration + diagnostics, needs triage) | 14 | 3,341 | 4 |
| ENGINE | 51 | 53,268 | 74 |

40% of the course signal is in 5 builder modules holding 4% of the code. Of the
74 left in ENGINE, 43 is in five modules (measured, enforcement, olx_prompts,
equivalence, score), and most of it is `vocabulary` — i.e. docstring prose, not
behaviour.

## 2. Goal K: the 189 enforcement checks have THREE fates, not two

Classified by propagating data-source signals through enforcement.py's internal
call graph, then reading representatives to check the classifier.

- **PORT (~133).** Structural validation over the rubric item data.
  `check_slot_codes_exist(items)` walks `it["deductions"]`, `it["credit"]`,
  `it["counts"]` and reports names that don't resolve. Nothing python-specific:
  a TS test over the rubric component does this natively. This is the bulk of K.
- **RETIRE (~8).** Checks whose subject is python-scorer vs web-scorer
  DIVERGENCE — `check_engines_send_the_same_request`,
  `check_scored_slots_are_answered_by_both_engines`,
  `check_both_engines_compute_the_same_primitives`. If K stops treating python as
  a second engine these have no subject. **They must not be ported**; porting
  them would assert a parity that no longer exists.
- **KEEP IN PYTHON (~48).** Checks whose subject IS the python tree:
  `check_module_has_no_course_data`, `check_filesystem_locations_come_from_paths_py`,
  `check_every_module_is_tracked`, `check_no_definition_vanished`. These cannot
  become TS tests because their subject is python source. They survive as long as
  any python does — and the pipeline, the ledger and the sweeps are all python.

So K is not "reimplement 189 checks in TS". It is: port the rubric-structural
majority, delete the parity checks the change makes vacuous, and leave the
source-hygiene checks where they are.

## 3. Findings raised by the audit

**F1 — the ratchet's vocabulary signal reads DOCSTRINGS ONLY.**
`course_inventory.scan_module` walks Module/FunctionDef/ClassDef and calls
`ast.get_docstring`; string literals in code are never inspected. Proved with a
matched pair: the same three terms score `vocabulary: 3` in a docstring and
`vocabulary: 0` in a module-level list. So course vocabulary held as DATA is
invisible — `oc_grid.GATE_KEYS` (5 slot names, 4 of them live rubric slots),
`prose_vocabulary.EXTRA_TERMS`, `check_slot_grammars.PROBES`.
*Recommendation: document the limit, do not widen the scan.* Widening would
flag `prose_vocabulary.EXTRA_TERMS`, whose whole subject is that vocabulary — a
false positive by construction. This is the "silently under-counting ratchet
reads as a tightening" hazard, so the limit belongs in the module's own comment.

**F2 — `oc_grid.py` is inert and unguarded.** 38 lines, no docstring, no
functions, no `__main__` guard: its whole body runs on import and prints a grid
to stdout. It calls `score.derive_oc_ledger`, so it is a real diagnostic against
current code, but importing it for any reason executes it. QUALITY_CONTROL.md
names oc_grid only as one of four stale SHADOW COPIES in a past incident, not as
a live tool. *Triage with category X; if kept, it needs a `__main__` guard.*

**F3 — `avoidance_frame` is NOT stale.** It is the python-side name; the rubric
calls it `phrased_directly` (`canonicalise_verdicts.py:77`). All five GATE_KEYS
resolve. Recorded because the raw comparison looks like a defect and will be
re-noticed.

## 4. Method corrections (so the numbers are trustworthy)

Three of my own errors, each caught by a total that failed to reconcile:
- `scan_module(path, ids)` takes two required args; calling it with one raised
  `TypeError` into a bare `except`, yielding all-zero scores. **An earlier
  "scores zero" claim about the three vocabulary modules rested on this and was
  invalid** — the conclusion survived re-testing, the evidence did not.
- Key names guessed (`literals`, `named_for`) instead of using the prepared
  `['counts']` dict, losing two of four columns silently.
- The static import graph showed the four `*_source` builders as having no
  importer. They are loaded DYNAMICALLY via `migrated_tables.BUILDERS`. "No
  importer" is not evidence of death in this tree.

## 5. Filed revision task — the handout set is written out 74 times

Third-verdict case: course-specific today, ought to be generic. `handouts.HANDOUTS`
is the declared set (`{1: ..., 2: ..., 3: ...}`), and `baseline.py` already reads
it correctly (`choices=sorted(HANDOUTS)`). Everywhere else the literal `(1, 2, 3)`
is written inline, so a fourth handout means editing 67 sites.

Population enumerated in full and reconciled (74 = 67 + 7):

**FIX SET — 67 sites**
- 59 × `for h|hh|handout in (1, 2, 3)` across enforcement (39), measured (5),
  probe (2), sweep_readout (3), olx_prompts (3), self_graded_misses (2),
  precommit_gate (2), rubric_export, score, leakage, handouts, equivalence
- 3 × a module-level `HANDOUTS = (1, 2, 3)` of its own, in `rubric_export.py:44`,
  `rubric_equivalence.py:42`, `reader_equivalence.py:55`. None of the three
  imports `handouts`, so this is the same fact declared independently four times.
  Not shadowing — duplication.
- 3 × `for hnd|_h in (1, 2, 3)` in enforcement (12454, 12465, 15557)
- 2 × head_to_head (`for _h`, and `("ALL", (1, 2, 3))` in a label table)

**MUST NOT CHANGE — 7 sites.** A blind replacement corrupts these:
- `probe.py:242,243` and `declaration_source.py:651,663` — `for n in (1, 2, 3)`
  is a SENTENCE index (`sentence_{n}`), not a handout
- `measured.py:4615` — `len(a) in (1, 2, 3)` is an argument count
- `rubric_equivalence.py:134`, `reader_equivalence.py:411` — prose in comments

Rule: the set comes from `sorted(handouts.HANDOUTS)`; a literal handout tuple is
a finding. Worth a `check_*` once the sites are converted, otherwise it grows back.

**Not executed.** This is behaviour-neutral and future-facing (it pays off when a
fourth handout arrives), and a 67-site edit would invalidate the certification
being run now. It needs its own certification cycle.

## 6. RESOLVED — QUALITY_CONTROL.md is now split (user's instruction, 2026-09-24)

Of the four `SPLIT_DOCS`, three have both halves. QUALITY_CONTROL.md has only a
generic half, and the composed artifact is BYTE-IDENTICAL to it (md5 bdef1ce6befd).

| doc | generic | course-specific | composed |
|---|---:|---:|---:|
| GOALS.md | 53 | 16,722 | 16,774 |
| QUALITY_CONTROL.md | 2,702 | **MISSING** | 2,702 |
| EQUIVALENCE.md | 877 | 2,199 | 3,063 |
| README.md | 170 | 465 | 632 |

The generic half carries course-specific material: 118 of 2,702 lines hold an
unambiguous item id, including corpus references citing individual students'
spans (`{{corpus:WK1/p17:...}}`, `{{corpus:Q6/p8:...}}`). Course VOCABULARY is
negligible (7 hits in 27,122 words) — the signal is item ids, not psych terms.

**Two readings, and the evidence does not separate them:**
1. The split ran and correctly moved nothing, because the project's own prose
   rule is *"a section MOVES if it is a RECORD; it STAYS if it is a RULE,
   illustrations included"* — and a QC guide is rules, with the item ids
   appearing inside worked illustrations. Under this reading the table above is
   correct and nothing is owed.
2. The split was declared for this document and never performed.

`prose_split.py` (the stage-7 worksheet) classifies 26 vocabulary-carrying
sentences in the composed QC doc as `incident` — i.e. records, which under the
rule would move. But that tool's own docstring says the decision "is not
mechanical" and its module comment says "a word list finds the sentences, it
cannot tell a specification from an incident". **It is a worksheet, not a
verdict**, so I am not making this call unilaterally. It needs the author's.

**What IS a defect regardless of which reading wins:** `compose_docs.missing()`
only checks that the COMPOSED path exists. It never checks the course half, so
"no course half because nothing moved" and "course half lost in a checkout" are
indistinguishable to every reader — the exact failure mode that function's own
docstring says it exists to prevent. Fix in the project's idiom: require a split
doc with no course half to DECLARE that ("DECLARED RATHER THAN SNIFFED", cf.
`migrated_tables.py`), so silence stops being ambiguous.

**Related: `prose_vocabulary.py` is inert.** It reports "Stage 7's split has NOT
run, so there is no general half to check. This is inert by design, not clean" —
it expects `<!-- general -->` markers that no document carries. The T7.3 property
(no course vocabulary in general prose) is therefore UNENFORCED. The module is
honest about it; the property is still unchecked. Note this is a DIFFERENT split
from compose_docs' — two split mechanisms coexist and only one has run.

**RESOLVED.** The user directed the split, with the illustrations becoming the
course-specific part — the opposite of reading (1) above, and their call on their
own rule. Done 2026-09-24:

| | lines |
|---|---:|
| generic half (`scoring/`) | 2,663 |
| course half (`psychology/bmod/`) | 348 |
| composed | 3,005 |

97 course-specific passages across 33 sections moved out; the generic half now
holds **zero** item ids, corpus references, handout numbers or domain vocabulary.
Guards clean (`missing`/`stale`/`duplicated`, 160 anchors resolving, guide
structure). Content verified against a pre-split snapshot — no course fact lost.

**The constraint worth recording**, because it will govern any future split: the
guide's own `check_guide_lessons_are_approved` keys each lesson by the sha of its
prose, so REWRITING a rule to strip course facts out of it lapses that lesson's
approval. A first attempt that reworded three lesson paragraphs was reverted for
exactly this. The finished split therefore comes in two parts — verbatim moves,
which change no sha, and 32 genericised lessons, which changed the ILLUSTRATION
only (`Q4b/p1 improved from 6 of 12` → `A cell that improves from 6 of 12`) and
which the user must approve one sha at a time. Until they do, the audit reads
44 + 32.

**A detector limit this exposed:** the course-reference scan keys on item ids,
corpus references, handout numbers and domain vocabulary. It does NOT catch
project-specific FIGURES — 6c's opening (`915` / `3123` from the history rewrite)
carries none of those markers and was missed; it was caught only by the
content-preservation check against the snapshot, and restored by hand.

## 7. Category X triage (the H remainder) — each one-off run, not guessed

| module | ran? | verdict |
|---|---|---|
| `rubric_equivalence.py` | exit 0 | **KEEP as tombstone.** Self-reports "the rubric modules are gone, so this tool has no oracle... Its last run with one is recorded in STAGE5_LICENCE.md, and that run is what licensed removing them." Deleting it loses the pointer to the licence. |
| `reader_equivalence.py` | exit 0 | **KEEP as tombstone.** Identical self-report. |
| `canonicalise_verdicts.py` | exit 0 | Work complete — "0 slot(s) renamed" on all three handouts. Inert but harmless. |
| `migrate_verdicts.py` | exit 0 | **NOT done.** Reports 2 pending edits on handout 1 (`no_antecedents`, `no_consequences`: "shortened") though its docstring says "Idempotent — a second run reports no edits", so `--write` was never run after those slots appeared. The change is proven-inert by the tool's own before/after parse. **Do not apply now:** it rewrites .olx, which moves prompt_sha and would re-stale the ledger currently being re-recorded. |
| `goals_restructure.py` | exit 0 | **DEFECT — false clean.** See §8. |
| `prose_split.py` | exit 0 | Live tool, not a one-off — still worksheets the composed docs. Reclassify. |
| `stamp_legacy_artifacts.py` | exit 0 | Still finds work (`SKIP nt2_cli/DAY1.runs.json: no sweep log`). Keep. |
| `scrub_metadata.py` | — | Publication utility, not a migration. Reclassify as ENGINE. |
| `oc_grid.py` | runs on import | See F2 — inert, unguarded, triage. |
| `migrated_tables.py`, `property_ratchet.py`, `prose_vocabulary.py`, `structure_kids.py` | — | **Misclassified by me.** All are imported live checks, not one-offs. Reclassify as ENGINE. (prose_vocabulary is live but inert — §6.) |

## 8. DEFECT — `goals_restructure.py` reads a stub and reports it clean

`goals_restructure.py:47` builds `GOALS = os.path.join(HERE, "GOALS.md")` — a
`__file__`-relative path. After the G2 split that file is the 53-line GENERIC
half; the real document is 16,722 lines at `$COURSE_DATA/courses/edu.memphis.psych/`.
So it reports "54 lines, 0 entries, round trip clean" — a **false clean over the
wrong file**.

`goals.py:48` shows the correct form and even warns against this mistake in a
comment: `GOALS = Path(compose_docs.composed_path("GOALS.md"))` — *"THE COMPOSED
DOCUMENT, not the generic half beside this module."* `goals.py` was updated
during the split; `goals_restructure.py` was not.

Population enumerated — exactly **two** modules build a split-document path from
`__file__`, and no others:
- `goals_restructure.py:47` → `GOALS.md` (**broken**, reads a 53-line stub)
- `tools/guide.py:52` → `QUALITY_CONTROL.md` (**works by accident** — that doc has
  no course half, so generic and composed are byte-identical today. It breaks the
  moment QC is split, i.e. exactly when §6 is resolved.)

Fix: both should resolve through `compose_docs.composed_path(...)`. This is the
same property `check_filesystem_locations_come_from_paths_py` already enforces for
filesystem locations, and it wants the document analogue.

## 9. RESOLVED 2026-09-24 — `scoring/materials/` has left the engine root

**Done.** All 11 files (4.2 MB) copied to
`$COURSE_DATA/courses/edu.memphis.psych/materials/`, verified byte-identical,
and the source removed. `scoring/` fell from 11.6 MB to 7.5 MB. `paths.MATERIALS`
now resolves through `$COURSE_DATA` with a `COURSE_MATERIALS` override, and all
four readers (`handouts.py` x3, `score_h1.py`) resolve. Audit re-run after the
move: **44 undeclared + 1 parked, finding set identical to baseline.**

`paths.py`'s comment recorded the argument this superseded rather than deleting
it: the old reasoning was from SENSITIVITY (the templates are blank) and is still
true; it is no longer operative, because goal J makes course materials
inadmissible in engine territory whether or not they are sensitive.

**One hazard found doing it:** defining `MATERIALS` from `DATA`/`NS` before either
existed broke `paths.py`, which broke `editguard` -- which imports `paths`, so the
guard could not repair the file it guards. `paths.py` is the one module where
`editguard` cannot be the safety net; take a backup first.

### The original finding, for the record

`paths.MATERIALS` resolves to `scoring/materials`, which holds **4.1 MB of this
course's authored materials**: the three BMod handouts (.docx), their three
PowerPoint decks, three Scoring & Feedback Dictionaries, and the **PSYC 1030
syllabus and course schedule for Spring 2026**. The syllabus and schedule are
institution- and term-specific; none of it is engine.

When scoring becomes its own repository these cannot travel with it. They belong
under `$COURSE_METADATA` beside `course.json`, by the same argument that moved
course.json there.

The move is not just a directory rename — three literal filenames are embedded in
engine code and must be redirected with it:
- `handouts.py:258` — `BMod Handout #1 - Defining Behaviors, ABCs, and SMART Goals.docx`
- `handouts.py:466` — Handout #2's .docx
- `handouts.py:488` — Handout #3's .docx
- `score_h1.py:43` — Handout #1's .docx again, a SECOND copy of the same literal

Note `score_h1.py:43` duplicates the filename `handouts.py:258` already has, so
the same course fact is written in two places. `enforcement.py:5395` documents
`handouts.MATERIALS` as "where the submission files are".

**The ratchet cannot see any of this.** These are f-strings inside a config dict,
not a module-level table of item ids, so `tables`/`literal_ids` do not count them
and `vocabulary` reads docstrings only (F1). `handouts.py` scores 1 table + 1
named on the inventory while carrying three handout filenames verbatim. This is
the same blind spot as F1, on a different signal: **course content held as DATA
in code is invisible to every arm of the ratchet.**

## 10. Outstanding work — STATUS 2026-09-24

K is DEFERRED by the user; this is no longer a pre-K list. Detail for each
item is in `RUBRIC_MIGRATION_PLAN.md` under its goal.

| item | status |
|---|---|
| QUALITY_CONTROL.md split | **DONE** — 44 lessons approved one at a time; twelve identifier classes at zero; content loss zero; certified 72/72 |
| `scoring/materials/` out of the engine | **DONE** — §9 |
| EXPECT duplication | **DESIGNED** — not redundancy but a migration-verification pair; the stale thing is the CHECK'S PREMISE, since goal C ended OLX generation. Six steps, plan §J |
| `tools/guide.py` under-checks the guide | **NEXT** — split the resolution; do NOT repoint `GUIDE`, which feeds two consumers with opposite needs |
| `compose_docs.missing()` blind to a lost course half | **NEXT** — declare the no-course-half case rather than sniff it |
| 67-site handout-set revision | designed; needs its own certification cycle |
| `migrate_verdicts.py`'s 2 inert edits | unapplied; rewrites .olx so it moves prompt_sha and needs a re-record cycle |
| `_1C_GATE_CEILING` rename | **WITHDRAWN** — it is in `editguard.ITEM_NAMED_BY_DESIGN` with the reasoning recorded, and renaming it would be a data migration on a gold-file key. Folds into J-5 |
| goal J | blocker cleared; six fixes prepared, plan §J |
| goal L | prepared and parked: target chosen, archiving proved at 47.7x, `locking.py` proved on five properties |
| goal M | filed — generalise the criteria scorer |
| goal K | deferred by the user |

### The original list, for the record


**1. The EXPECT duplication** (you asked for this to be listed, not fixed).
The same course fact is authored in two places:
- `rubric_h2_source.py:1191` — `_EXPECT_SHIPPED`, a per-item table applied to
  `ITEMS` in a module-level loop (`_it["expect"] = _EXPECT_SHIPPED[_it["id"]]`)
- `psychology/bmod_rubric.olx` — six `<Expect .../>` elements, four of which are
  the same four entries (`NP`/`NR`/`PP` on `observed_type`, `PR` on `stimulus_move`)

`course.json` carries no `expect` key, so the builder and the rubric are the only
two homes — and goal C's rule says the authored table belongs in the rubric alone.
The OLX has two `<Expect>` elements the builder table does not (including a
`lenient=` form), so **the two are not a straight copy** and reconciling them is a
read, not a delete. `_ONLYIF_SHIPPED` sits directly below `_EXPECT_SHIPPED` and
has the same shape — check whether it duplicates too.

**2. `migrate_verdicts.py` has 2 unapplied inert edits** (§7). Applying them
rewrites .olx and moves prompt_sha, so it needs its own re-record cycle.

**3. §6 — QUALITY_CONTROL.md's split.** DONE; 32 lesson approvals outstanding.

**4. The 67-site handout-set revision** (§5). Needs its own certification cycle.

**5. `compose_docs.missing()` cannot see a lost course half** (§6). Small fix,
in-idiom: make "no course half" a declared fact rather than silence.

**6. `tools/guide.py` now under-checks the guide — LIVE as of the §6 split.**
`GUIDE` resolves to the GENERIC half (`paths.SCORING`), so `check()` validates
§-citations and backticked identifiers over only part of the document. The course
half already carries a `§2k` citation and dozens of backticked identifiers that
nothing validates.

**Do not fix it by repointing `GUIDE`.** That name feeds TWO different consumers
with opposite requirements:

| consumer | needs | why |
|---|---|---|
| `check()` (lines 146, 250, 305) | the **composed** document | it validates what READERS see, and citations can live in either half |
| `unapproved_lessons()` (line 535) | the **generic** half | it diffs against `git show HEAD:./QUALITY_CONTROL.md`, and only the generic half is tracked there |

Repointing `GUIDE` wholesale would make the lesson check compare the composed
document against the HEAD-committed generic half, flagging every course-half
lesson as newly added. The fix is to split the resolution, giving `check()` the
composed path and leaving `unapproved_lessons()` on the generic one.

**Deliberately NOT done yet:** 32 lesson approvals are outstanding against the
current resolution, and changing the approval machinery while the user is acting
on its output is the wrong order. Do it immediately after the approvals land, and
re-run the audit to confirm 44.

Same applies to the two QUALITY_CONTROL.md injection sites in `equivalence.py`:
once `check()` reads the composed document, `_SELFTEST_DOC_HOME` must gain
`"QUALITY_CONTROL.md": "composed"` so injection and check stay in lockstep — the
same alignment the GOALS.md fix established.

## 11. CORRECTION to §8 — the population was five, not two, and one of them was the certifier

§8 claimed "exactly two modules build a split-document path from `__file__`, and
no others." **That was wrong.** The grep covered only the two spellings already
observed (`os.path.join(HERE, "X.md")`, `HERE / "X.md"`). Three more use
`Path(__file__).resolve().parent / "X.md"`:

| site | document | state |
|---|---|---|
| `goals_restructure.py:47` | GOALS.md | fixed (§8) |
| `tools/guide.py:52` | QUALITY_CONTROL.md | CORRECT — see below |
| `equivalence.py:2824` | GOALS.md | **broke the self-test**; fixed |
| `equivalence.py:2842` | QUALITY_CONTROL.md | CORRECT — see below |
| `equivalence.py:2854` | QUALITY_CONTROL.md | CORRECT — see below |

**The self-test breakage.** `equivalence.py:2824` read the 53-line generic stub,
so `re.search(r"^- \[ \] Q\d+\. .*$")` returned None and `m.group(0)` raised
`AttributeError`. That aborts `enforcement_selftest()`, so **the 59 cases after
case 13 never ran** — the run produced 18 lines instead of 95. G2's split caused
it and nothing re-ran the suite afterwards, so it sat undetected. The case was
broken twice over: even on a match it injected into a file the check under test
does not read (enforcement reads `compose_docs.composed_path("GOALS.md")`).

**Not every site should resolve the same way, and that is the real lesson.** The
two split documents are read differently BY DESIGN:
- enforcement's goal checks read the **composed** GOALS.md
- `tools.guide` reads the **generic half** of QUALITY_CONTROL.md (`paths.SCORING`)

So the three QUALITY_CONTROL.md sites are correctly aimed today and redirecting
them would have broken two passing cases. The fix is a resolver with an explicit
map, `_SELFTEST_DOC_HOME = {"GOALS.md": "composed"}`, used by BOTH the injection
site and `_selftest_snapshot` — kept in lockstep because "two places disagree
about where a document lives" is the defect itself.

**Residual hazard, unchanged:** `tools/guide.py:52` and the two QC sites are
correct only because QUALITY_CONTROL.md has no course half. Resolving §6 breaks
all three at once. Fix them in the same change.

## 12. Ledger repairs applied

- **`previous` blocks restored from HEAD** for 78 entries; `previous==live` went
  79/79 → **52/79**, matching HEAD exactly. The restore script refuses any entry
  whose LIVE value moved, so it can only touch history.
- **Q1/olx NOT repaired** — held for the user. Its `out` regressed from
  `q1_render_0914` (HEAD) to `full_0912_olx`. Score is 17/20 either way, so
  restoring it moves no number, but it is a measurement of record.
- **`DEFINITIONS.json` backfill owed** for the two names this fix added
  (`_SELFTEST_DOC_HOME`, `_selftest_doc`) — `tools/editguard.py --backfill`.
  This is why the cold audit read 47 rather than 46.
