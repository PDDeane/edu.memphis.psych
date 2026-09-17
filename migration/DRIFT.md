# What changed in live since the dry run, and which stage each change lands on

The dry run forked **2026-09-13 20:50**. Everything below appeared afterwards and
was never exercised by it. A stage that is not adjusted for the rows touching it
will either fail confusingly or — the real risk — pass against the wrong thing.

Re-derive this table before starting; it is a snapshot, not a constant.

## The changes

| # | change | where |
|---|---|---|
| A | **corpus references** replace student text in rubric prose and `.olx` | `rubric_h*.py`, `psychology/*.olx` |
| B | **new machinery the dry run never saw**: `corpus_resolve.py` (361), `corpus_ref.py` (417), `check_ref_grammars.py` (104), `fixture_edits.py` (257), `CONSENSUS_SPANS.json` (875), `STUDENT_TEXT_BUDGET.json` | `scoring/` |
| C | **`olx_prompts.expand_prose` now calls `to_olx`** — it CONVERTS a reference rather than resolving it, so the words never reach the `.olx` | `scoring/olx_prompts.py` |
| D | **a build-time resolver in the engine**: `packages/shared/scripts/resolveCorpusRefs.ts` | `$LO_BLOCKS` |
| E | **three new audit checks** (main-guard reachability, one definition of student text, export-not-for-classification) | `scoring/enforcement.py` |
| F | **`precommit_gate` refuses student text on a ratchet**, budget in `STUDENT_TEXT_BUDGET.json` | `scoring/precommit_gate.py` |
| G | ordinary scoring evolution: `measured.py`, `handouts.py`, `score.py`, `agreement.py`, `probe.py`, `guide.py`, `sweep_*.py`, `MEASURED.json`, `DEFINITIONS.json` | `scoring/` |

## Which stage each one lands on

| stage | affected by | what to adjust |
|---|---|---|
| **00** registry / baseline / oracles | A B C E G | **Re-freeze everything.** The dry run's goldens describe a pre-reference tree. `audit_baseline.json` must be re-captured: the audit has three more checks (E) and one of them currently reports 5 findings (see BACKLOG). |
| **01** coupling recount | E G | The dry run counted **73 of 135** checks coupled; live now has **141**. Recount — do not scale the old ratio. |
| **02** assembler surface (26 bodies byte-exact) | A C | Bodies now contain `{{corpus:…}}` where they used to contain sentences. The hand-built structures must reproduce the REFERENCE, not the text. A structure that emits the resolved words will differ from the file and look like an assembler bug. |
| **03a/b** blocks parse & engine neutral | D | The engine gained a resolver. Confirm it is content-neutral and that `check_ref_grammars.py` (Python vs TypeScript grammar equivalence) passes — it is the only thing stopping the two resolvers from drifting. |
| **04/05** migrate rubric, byte equality, `prompt_sha` | A C | **The central adjustment.** `prompt_sha` hashes a `<Vertical>` slice of the `.olx`, and that slice now holds references. Every family's value therefore differs from any pre-rewrite baseline — not because the migration changed anything, but because the rewrite did. Re-freeze first, then compare; comparing against a pre-rewrite oracle will report a migration defect that does not exist. |
| **06** fingerprint / selftest | E G | `SELFTEST_EXPECTED` was 114 in the dry run against 135 checks. Live's count differs; recompute from the registered injections rather than carrying the constant over. |
| **07** prose mentions | A | Mentions are split by tense over rubric prose that now contains references. A reference is not a mention; make sure the splitter does not count one. |
| **08** acceptance | A C D F | Corpus replay and the served-prompt check must run against a tree whose references RESOLVE — `$CORPUS_REFS` must point at an export containing every span the tree cites. The `idmap` dump must still predate the work. |

## The gate that belongs to (A), and is not optional

The migration lifts rubric prose into the `.olx`. If the prose still holds
student text, the migration moves student text into a new public file, and every
downstream artefact inherits it.

**Before stage 00, `rubric_h1.py`, `rubric_h2.py` and `rubric_h3.py` must scan to
ZERO distinctive student 4-grams** against the whole response space
(`corpus_ref._index()`), with course text subtracted, using
`scripts/history_rewrite/scan_full_corpus.py` and its positive control.

Measured 2026-09-16, before the rewrite was finished:

| tree | distinctive student 4-grams in `rubric_h*.py` |
|---|---|
| live working tree | 7 |
| rewritten HEAD (psych13, incomplete table) | 29 |

Neither is zero, which is why `preflight.py` refuses today. The mechanism is
sound — (C) means references travel into the `.olx` as references — but the
mechanism only protects what the rewrite actually replaced.
