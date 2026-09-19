# Moving the course out of `scoring/` — a refactor plan

**Status: FIRST DRAFT, for discussion. Nothing here is decided and no code is to
be written yet.** The entry conditions in §1 are not close to met, and §4 lists
questions the rubric migration has to answer before parts of this can be settled
at all.

---

## 0 · The goal, in one sentence

`scoring/` should contain a scoring **engine** and no psychology: every fact
about this course, its handouts, its items and its rubric moves into a readable
JSON file that lives in `courses/<course-id>/` (AMENDED 2026-09-18 by §10.5,
which supersedes the original "beside the rubric in the content directory"), and every
program reads those facts from that file instead of from a table in its own
source.

Two identifiers tie it together:

* the metadata file carries an **id naming the rubric it describes**, and
* the rubric carries an **attribute naming its metadata file**.

So either artifact can be found from the other, and neither is guessed by
convention or by filename arithmetic.

### The governing principle: specific points at general

**Every reference in this refactor points FROM the course-specific artifact TO
the general one. Nothing general points at anything specific.**

That holds for the guide (3.4), for goals (3.3), and for any artifact this
refactor splits later. The test is simple and worth applying to every design
decision below: *could this shared artifact be read, in full, by someone who has
never heard of this psychology course?* If a pointer, a name or an example in it
would puzzle them, the reference is pointing the wrong way.

The failure mode it prevents is not caught by tests. Point the references
inward - shared file holding the passages, course metadata pointing in - and the
system works perfectly for one course. Add a second and every course's passages
must live in the shared file for their pointers to resolve, so the shared file
becomes the union of every course that ever used it. It degrades by accumulation,
silently, and each individual addition looks reasonable.

It is the same rule the rubric migration enforces as C2, one level up: there, the
ENGINE must not learn subject vocabulary; here, the shared DOCUMENTS must not.

### The second governing principle: the JSON is machine-owned, the `.md` files are ours

**Decided by the user, 2026-09-14.** The metadata file is **entirely machine
owned**. No one hand-edits it, ever. **Only `.md` files are human-edited.**

That draws the ownership line cleanly through every artifact this refactor
touches:

| artifact | written by | edited by a person |
|---|---|---|
| `bmod_rubric.meta.json` | programs only | **never** |
| the general guide, the general goals file | people | yes |
| the course guide, the course goals narrative | people | yes |
| the rubric `.olx` | the build | no (it is generated) |

**This resolves the format tension that 3.3 could not.** "Readable JSON" and
"hand-editable JSON" were pulling against each other, and 16,650 lines of goal
prose is exactly where that tears. It is now settled: the JSON must be
**readable** - a person reads it to see what a program decided - and it does not
need to be **editable**, because a person never edits it. Stable key order, one
fact per line, arrays of lines for prose: still required. Comment syntax,
merge-friendliness, hand-editing ergonomics: not required.

**The consequence, which is the part to design for.** Anything a human authors
lives in a `.md` and the JSON is DERIVED from it; anything a machine measures is
written to the JSON directly and has no `.md` source. So the goals key is not a
place people type into - it is the structured form of what the goals `.md` says,
plus the measurements programs recorded against it.

*The risk this creates, stated now rather than discovered:* `GOALS.md` exists so
that a person rewrites the plan mid-task, and `measured.py --preflight` puts the
ACTIVE line in front of whoever is working. If that now requires a tool, the tool
must exist and be pleasant **before** the practice depends on it. A generation
step that makes restating the objective slower will kill the habit while every
test still passes.

### What this is NOT

**It is not the rubric migration.** That one moves the rubric ITSELF — the
items, slots, credit, deductions, guidance — out of `rubric_hN.py` and into
`bmod_hN_rubric.olx`. This one moves the **metadata about the rubric and about
the scoring analysis that produced it**: gold divergences, exclusions,
declarations, designed text, probe limits, goals, and the course-specific half
of the quality-control guide.

The boundary matters because the two can be told apart by a single question:
*would a grader need this to score an answer?* If yes it is rubric content and
belongs to the migration. If it only records what WE decided, measured, declared
or excluded while building the rubric, it is metadata and belongs here.

---

## 1 · Entry conditions — hard

*Revised 2026-09-18. The migration conditions are gone: the migration was
completed in full in the dry run and is not being redone here, so gating this
refactor on its stages gated it on work that will not happen. What the migration
leaves behind is not a stage list but a tree — see condition 3.*

No code is written for this refactor until **all** of the following hold. They
are listed in the order they can be satisfied.

1. **The re-sweep is finished.** — **MET as of 2026-09-18.** All 26 ledger items
   read `ok` in `measured.py --status`, 5-6 runs each, nothing stale. (The
   original text here said "fifteen items; nine done, `1a` in flight, five behind
   it"; that was true when written and is not now.)
2. **The live self-test has run and reported clean**, with its tree checksum
   showing no residue.
3. **The work this refactor will measure is committed.** Not "all current work" —
   that is too vague to gate on, and the answer differs per repository.

   As measured 2026-09-18:

   * `edu.memphis.psych` — clean apart from this document.
   * `molly_scoring` — **not a git repository at all**; it is a directory of
     handout `.docx`/`.pptx` source material. It cannot be "committed" and does
     not belong in this condition. (Recorded because an earlier reading of this
     plan reported it clean, which was a `git status` failing and its empty
     output being counted as a pass.)
   * `update/lo-blocks` — **38 uncommitted paths** (22 tracked-modified, 16
     untracked) on `pdeane/content-8-26`, whose HEAD is `44d5a818` of 2026-09-09.
     The reflog confirms HEAD has not moved since and no branch carries later
     work.

   **What those 38 are — and are not.** They are the continuation of the slot-sheet
   engine line already committed on this branch: `forbid` (2026-08-25), a computed
   rule naming its verdict (08-28), `maps` (08-28), `LLMAction: declare forbid and
   maps` (08-29), `contains` (09-01), `buildSlotSchema` (09-09). The working tree
   carries the next increment — `slotSheet.ts` +179 lines, plus `maps`, `equals`,
   `runner` and round-trip tests. **This is not "the rubric migration": the
   migration has not been performed on the live tree and is not planned until
   after this refactor.** An earlier revision of this section called them "the
   migration's engine", which was wrong.

   Three of the 38 are not that work either, and belong to the history-rewrite and
   simulation of 2026-09-17/18: `SelfMonitorPlot/legendRender.test.ts` (the p20
   student-data scrub), `packages/shared/lib/testing/` (a `preloadBlocks` helper),
   and `packages/shared/scripts/resolveCorpusRefs.ts`. They should be separated
   from the engine increment rather than swept into one commit.

   Why this gates the refactor at all: on 2026-09-18 a historical student
   simulation failed with `Invalid attributes for <LLMAction>: 'free'` against the
   COMMITTED engine and passed against the working tree. The engine the refactor
   reads is therefore not the engine in git, and §2's inventory must be
   re-measured against whichever tree it will actually read.

4. **The self-test refuses to run while another self-test is running.**
   — **MET 2026-09-18, the same day it was added.** `enforcement_selftest` now
   calls `refuse_if_selftest_running` before the fingerprint and before any
   injection; a second run exits 1 naming the first. The detector was also fixed:
   it matched a wrapper process (`timeout ... python3 ... equivalence.py
   --selftest`), so a single run under `timeout` would have refused ITSELF.
   ADDED 2026-09-18, and it is not a theoretical hardening: two self-tests were
   started on the live tree that day and **both ran**, neither refusing. Neither
   the live tree nor the dry run contains a locking primitive (`flock`, `O_EXCL`
   or a pid file), so §11.11's claim that this was "fixed in the dry run" does
   not hold — this is code to be written, not ported. Until it exists, condition
   2's gate is unfalsifiable in the way §11.11 describes: a run can damage the
   tree and still report success.

---

## 2 · The inventory — what actually has to move

Measured 2026-09-14 on the live tree, not estimated.

> **RE-MEASURE BEFORE USING THESE NUMBERS (noted 2026-09-18).** This inventory
> was taken against a tree that does not contain lo-blocks' 38 uncommitted
> migration paths (condition 3). Whether those land or are declared out of scope
> changes what "the engine" is, and therefore what has to move out of it. No
> table below should be acted on until it has been recounted against the tree
> this refactor will actually read.

### 2.1 Item-bearing tables in the engine's own source

Module-level tables whose literals name this course's item ids:

| file | tables | lines |
|---|---|---|
| `handouts.py` | 5 | **1,908** |
| `enforcement.py` | 18 | 808 |
| `measured.py` | 7 | 519 |
| `olx_prompts.py` | 11 | 454 |
| `goals.py` | 1 | 234 |
| `score.py` | 2 | 44 |
| `probe.py` | 1 | 18 |
| `leakage.py` | 1 | 1 |
| **total** | **46** | **3,986** |

The largest single ones are `handouts.GOLD_DIVERGENCES` (784 lines),
`handouts.CORRECTED_GOLD` (522), `handouts.HANDOUTS` (281), `goals.CLOSURES_APPROVED`
(234), `handouts.GOLD_CEILINGS` (210), `enforcement.PROSE_ONLY_SLOTS` (201),
`measured.GOLD_SLOT_DISAGREEMENTS_KNOWN` (152) and `enforcement.MULTI_BLOCK_DECLARED`
(134).

**This count is a floor, not a ceiling.** It finds tables whose literals contain
an item id. It will miss course-specific content keyed by slot name, by code, by
handout number, or by prose alone — and `handouts.HANDOUTS` shows why that
matters: it scores only 1 item id while being almost entirely course content
(blurbs, submission paths, gold wiring). An early stage has to widen this scan;
see §5.1.

### 2.2 Whole files that are course data

| file | lines | nature |
|---|---|---|
| `GOALS.md` | 16,650 | 112 entries, prose + structure, machine-parsed |
| `OVERRIDES.md` | 257,216 (49 MB) | machine-written gate log, "do not edit by hand" |
| `MEASURED.json` | 5,622 | already JSON — the ledger |
| `EQUIVALENCE.md` | 3,050 | read by 6 modules |
| `QUALITY_CONTROL.md` | 2,448 | mixed: general method + course specifics |
| `BACKLOG.md` | 1,706 | read by 8 modules |
| `LEAKAGE_REVIEWED.json` | 272 | already JSON |
| `rubric_h{1,2,3}.py` | 5,156 | **the migration's, not ours** |

### 2.3 Coupling

* `GOALS.md` is read or written by **5** modules: `goals.py`, `enforcement.py`,
  `measured.py`, `equivalence.py`, `olx_prompts.py`.
* `QUALITY_CONTROL.md` is read by **9**: the five above plus `compare_runs.py`,
  `editguard.py`, `guide.py`, `handouts.py`, `sweep_gate.py`.
* `BACKLOG.md` by 8, `EQUIVALENCE.md` by 6, `OVERRIDES.md` by 3.

---

## 3 · The target shape

### 3.1 ONE file, for the whole rubric, at course level - SETTLED

**Decided by the user, 2026-09-14.** Not one file per handout. The rubric is a
course-level object and its metadata is one file.

```
psychology/
  bmod_h1_rubric.olx          \
  bmod_h2_rubric.olx           >  the rubric       (migration's output)
  bmod_h3_rubric.olx          /
  bmod_rubric.meta.json           everything about it  (this refactor's output)
```

The metadata file names the rubric it describes; the rubric names its metadata
file:

```xml
<Rubric id="bmod_rubric" metadata="bmod_rubric.meta.json">
```

```json
{ "rubric": "bmod_rubric",
  "handouts": { "1": {...}, "2": {...}, "3": {...} },
  "gold": {...}, "declarations": {...}, "goals": {...},
  "quality_control": {...}, "overrides": {...} }
```

This settles what was an open question. Corpus-wide facts (goals, neutrality
pairs, the ledger) and per-handout facts (gold, exclusions, item notes) live in
ONE file, the per-handout ones under a `handouts` key. Nothing has to be
apportioned between files and no file is incomplete on its own.

*Consequence to watch:* one file holding ~4,000 lines of tables plus 112 goal
entries is a large artifact, and the editability requirement in 3.3 applies to
all of it. Size is a reason to design the layout carefully in stage B, not a
reason to split.

### 3.2 Readability is a requirement, not a preference

The user's word is "readable". That rules out a dump: it wants stable key order,
one fact per line where possible, comments preserved as fields rather than
discarded, and a layout a person can diff. Several of these tables currently
carry their rationale in Python comments that a naive conversion would delete —
and in this project the comment above a rule usually holds the measured work
that produced it. **Every table's prose has to land in a field, not on the
floor.**

### 3.3 `GOALS.md` splits the same way, and must stay hand-editable

**Two requirements from the user, and the second constrains the format.**

1. `GOALS.md` splits like the guide does: a **general file** keeping the process
   rules that are true of any scoring project, and **rubric-specific details**
   moving into the metadata file under a `goals` key.
2. Both halves must be **human readable and human editable**.

The grammar is already regular - `goals.py` parses entries with
`^- \[([ x])\] ([A-Z]+)(\d+)\. (.*)$` and citations with
`\b(?:sub)?goal ([A-Z]+)(\d+)\b`. 112 entries across three series (`Q` 63,
`E` 49, `WK` 1).

What is general (stays in the file a person reads):

* one ACTIVE goal, subgoals in order, the reason each closed;
* **"NEVER CLOSE A GOAL WITHOUT ASKING THE USER FIRST"** and why;
* the rule that a superseded goal moves to DONE *with the measurement that
  closed it*, because a goal closed without a number gets reopened.

What is rubric-specific (moves to `goals`): the 112 entries themselves, their
findings, their cited measurements, and `goals.CLOSURES_APPROVED` (234 lines).

#### The format tension - RESOLVED by the ownership rule

**The JSON does not need to be hand-editable, because no one edits it** (§0's
second principle). What follows is kept because the reasoning still governs
WHERE each thing lives, not because the tension is open.



**JSON is a poor container for long prose and this is 16,650 lines of it.** A
multi-line goal entry becomes one string with `\n` escapes: unreadable in a
diff and impossible to comment. Since nobody edits the file, the editing half of
that objection falls away and the READING half does not - so the layout still
has to be chosen deliberately. What stage B settles is which of these applies to
which content:

* **Arrays of lines** - `"body": ["line one", "line two"]`. Diffs cleanly, edits
  reasonably, still JSON. Costs a join on read.
* **Prose stays in Markdown, JSON holds structure** - the entry's id, state,
  citations and closing measurement in `goals`, its narrative in a COURSE-level
  goals document that anchor-references the general process rules. Same
  direction as 3.4: the general rules file never points at a course's goals.
* **Generate it from the `.md`** - the human writes the goals narrative in
  Markdown, a program derives the structured form. This is the default under the
  ownership rule: the `.md` is the source, the JSON is the product, and the two
  cannot disagree because one is computed from the other.

*Whatever is chosen must keep the practice alive:* `measured.py --preflight`
prints the ACTIVE line so the objective is in front of whoever is working. A
format that makes it awkward to restate the objective mid-task kills that, and
every test can still pass while it dies.

Everything that reads or writes `GOALS.md` changes: `goals.py` (949 lines - the
parser, `next_label`, `check`, `misfiled_series`, `stale_slot_claims`, `rank`)
plus `enforcement.py`, `measured.py`, `equivalence.py` and `olx_prompts.py`.

### 3.4 `QUALITY_CONTROL.md` splits into a general guide and a course guide

Functionality does not change. What changes is that there come to be TWO
documents, and one of them is allowed to know about psychology.

* **The general guide** - "probe before you sweep", "try the structural fix
  first", "profile the errors by slot after every sweep", "use the prepared
  classifier". True of any scoring model. **It never names a course, a handout
  or an item.**
* **The course guide** - this course's application of those rules: the worked
  examples naming `Q6`, `NR/p14`, `1c`; the primitive choices as they apply to
  these items; the thresholds tuned on this corpus. It lives with the course,
  and the metadata file names it the same way the rubric names its metadata.

#### References point FROM the specific TO the general, never the reverse

**Decided by the user, 2026-09-14, and it is the load-bearing decision in this
section.** The course guide carries anchor references INTO the general guide.
The general guide holds no references out.

An **anchor** is a stable named marker on a passage - much like the `#id` a web
page heading carries - so another document can point at that place in the prose
instead of copying it. In the general guide, a passage carries a name:

```markdown
## 2a. PROBE BEFORE YOU SWEEP   <!-- qc:probe-before-sweep -->
```

and the COURSE guide points at it while adding what is true here:

```markdown
### Probing on this corpus   <!-- see: qc:probe-before-sweep -->

Six runs, not two. Q1's two-cell probe reported "better [17], worse none"; the
20-cell version reported 3 better, 6 worse.
```

**Why this direction and not the other.** The first draft had it backwards: the
prose staying in the shared guide with the metadata pointing in. That works for
exactly one course. The moment a second course exists, every course's passages
have to live in the shared file for their pointers to resolve - so the general
guide accumulates course-specific material and stops being general. The failure
is not a bug that shows up in a test; it is the shared artifact slowly becoming
a union of every course that ever used it.

Pointing the other way, the general guide is **closed**: complete and readable
without knowing that any course exists. Adding a course adds a file and changes
nothing shared. This is the same rule the rubric migration enforces as C2, where
the engine must not learn subject vocabulary - here the shared GUIDE must not.

*It also simplifies the integrity check to one direction.* Every anchor a course
guide names must exist in the general guide - a dangling reference is an error.
There is no reverse check, because the general guide has nothing to point back
at and should not know what is pointing at it.

#### What the metadata file holds

Numbers and structure, not prose: thresholds, minimum run counts, which
directives apply, and the name of the course guide.

```json
"quality_control": {
  "guide": "bmod_quality_control.md",
  "probe": { "min_runs": 6 }
}
```

So a program that needs a directive is given a rubric, finds the metadata, finds
the course guide, and resolves any general principle from there. It never has to
know which course it is working on as a fact about itself.

## 4 · Open decisions

*Revised 2026-09-18: the heading used to read "several blocked on the
migration". With the migration finished in the dry run, nothing here is blocked
on it any more — but nothing is automatically answered either. Every decision
below that cites a migration stage as its blocker must be RE-EXAMINED against
what the dry run actually settled, and answered or restated. Treating "the
migration is done" as "the decision is made" would be the same mistake as
treating a tree diff as proof a fix works.*

**4.1 · Does the rubric attribute naming the metadata file fit C2?**
The migration's constraint C2 forbids course vocabulary in lo-blocks. An
attribute called `metadata` is neutral; what it points at is not the engine's
business. But the migration's decision 11.4 already had to rename an attribute
(`rubric` → `rubricDef`) because the name reached a shared registry and
`sheetAttributes` is corpus-wide. **The same check is owed here before any name
is chosen**, and the migration's block-registry work should settle it.

**4.2 · What reads the metadata file — Python, lo-blocks, or both?**
The migration settled (11.2, 11.6) that Python reads the rubric object directly
with its own reader. If the metadata file is Python-only, it need not be a
lo-blocks block at all and the `metadata` attribute is an inert string. If the
app ever needs it, it becomes a registered attribute with a resolver.
**Blocked on the migration's stage 08.**

**4.3 · Leak-checking gold content - REQUIRED, not a question.**
`edu.memphis.psych` is PUBLIC and nothing derived from student submissions may
enter it. `GOLD_DIVERGENCES` (784 lines) and `CORRECTED_GOLD` (522) are about
graded student work. They are already in this repo, so they are presumably
already clean — but **moving them must re-run the leak gate**, which the
migration already exercises ("no 40-char window unique to one submission appears
in a frozen string without also appearing in an authored source"). Treat a leak
finding here as a stop, not a warning.

**4.4 · One metadata file per rubric, or per course? CLOSED 2026-09-14: ONE, at
course level.** See §3.1. Per-handout facts live under a `handouts` key in the
same file; nothing is apportioned between files.

**4.5 · Extract the QC specifics, or anchor-reference them? CLOSED 2026-09-14.**
See §3.4. A course guide carries the course-specific prose and
**anchor-references the general guide**; the direction is specific -> general and
never the reverse, because the other direction turns the shared guide into the
union of every course that ever used it.

**4.7 · WHICH rubric object is "the rubric"? BLOCKING, and it is the migration's
to answer.** §3.1 assumes a course-level rubric that IS the rubric and can carry
a `metadata` attribute. Measured in the dry run on 2026-09-14, that is not yet
what exists:

* `bmod_rubric.olx` declares `id="bmod_rubric"` and is **34 lines** - a
  `<Verdicts>` and an `<ItemTemplate>`, no items.
* `bmod_h{1,2,3}_rubric.olx` hold all 845 lines of actual rubric content - 26
  items - and **nothing references them**. `<Course>` uses `bmod_rubric` alone.
* `bmod_rubric_pr.olx` **also** declares `id="bmod_rubric"`. Two files, one id,
  and nothing references the `_pr` variant.

So "the rubric at course level" is presently a shell, the rubric is three
unreferenced files, and the id the metadata would name is claimed twice. **This
refactor cannot attach a metadata file to "the rubric" until the migration says
what the rubric IS**: whether the three per-handout files become children of
`bmod_rubric`, or the course references all four, and which file keeps the id.
Nothing in §3 is buildable before that.

**4.8 · Who writes the metadata file, given that several of these tables are
machine-written today?** The ownership rule (§0) says programs only. But the
rule alone does not settle the shape: `DESIGNED_TEXT` is written by
`measured.py --accept-design-change`, `CLOSURES_APPROVED` by the goals tooling,
and goal entries by whatever replaces `goals.py`'s writers. Several writers into
one file is how T5 - one artifact, one writer - gets violated by a design that
was told about T5.

*The question to settle in stage B:* is the file assembled by ONE generator from
declared sources, with every other program writing to its own source and never
to the file? Or does each program own a region? The first is the migration's
answer (one emitter, and a patcher that added fields it did not know about was
erased silently). The second is easier and is how the file acquires two writers
that disagree about key order.

**4.9 · Where does `MEASURED.json` go?** 5,622 lines, already JSON, entirely
course-specific, and rewritten by `--record` after every sweep. Folding a ledger
that changes on every measurement into the same file as declarations that change
rarely makes every recording a diff against the whole artifact. *Recommendation:
it stays a separate file and is NAMED by the metadata rather than absorbed into
it* - but the plan should say so rather than leave it listed in §2.2 with no
destination.

**4.10 · `EQUIVALENCE.md` and `BACKLOG.md` - classified 2026-09-14, and the
measurement corrected my own inventory.** §2.3 said EQUIVALENCE was "read by 6
modules" and BACKLOG "by 8". **That was wrong.** It counted every file that
MENTIONS the name - and almost every mention is a comment, "see EQUIVALENCE.md".
Counting mentions rather than reads is the same error as scanning for attribute
access and missing `from X import` (T26 in the migration). What the tree
actually does:

| file | machine readers | what reads it |
|---|---|---|
| `EQUIVALENCE.md` | **none** | nothing binds its path at all |
| `BACKLOG.md` | 1 | `olx_prompts` greps it for lines naming an item, beside `drafts/` and `GOALS.md` |
| both | +1 generic | `measured` globs `SCORING/*.md` (excluding `OVERRIDES.md`) for the prose-number check |

Course-specificity, measured at the heading level - the unit that actually
splits - rather than by line:

| file | lines | headings | headings naming an item |
|---|---|---|---|
| `EQUIVALENCE.md` | 3,050 | 88 | 25 (**28%**) |
| `BACKLOG.md` | 1,706 | 52 | 17 (**32%**) |

So the proportions are nearly the same, and the split is **not** by volume. It is
by KIND, and the two files are siblings of two different things:

* **`EQUIVALENCE.md` is a sibling of `QUALITY_CONTROL.md`.** Its spine is
  general - "why this file exists", "three scorers, and what python means here",
  what equivalence IS and what the contract requires. Its item-named sections are
  per-item divergence FINDINGS hung off that spine. **Treat it exactly as 3.4
  treats the guide:** a general document that never names a course, plus a course
  document carrying the divergence findings and anchor-referencing the general
  one. Since nothing machine-reads it, the split costs no reader changes - the
  cheapest of the four prose moves, and the one whose general half is most
  reusable by a second course.
* **`BACKLOG.md` is a sibling of `GOALS.md`.** "Jobs we need to do" is a work
  list about this course, and it is grepped by the same mechanism that greps
  `GOALS.md`. **Treat it exactly as 3.3 treats goals:** the narrative in a
  course-level `.md` a person edits, the structure derived into the metadata
  file, and `olx_prompts`' record-scan re-pointed to find it through the rubric
  rather than by filename.

*One consequence for stage F that applies to all four prose files:* `measured`
globs `SCORING/*.md`. After the split, the general documents no longer live
beside the course ones, so that glob has to learn the difference - or it will
either miss the course files or scan general prose for numbers that describe a
corpus it knows nothing about.

**4.6 · `OVERRIDES.md` IS IN SCOPE - settled, with one complication.**
The user's test is whether it records decisions about rubric content. Measured,
it does: 660 of its findings name gold cells, slot-set disagreements or item
decisions, and the reasons given are substantive judgements about this rubric
("p6 is right by two errors cancelling"). One entry even carries an appended
**CORRECTION** reversing its own reasoning. That is exactly the record this
refactor exists to make first-class, so it moves.

*The complication is that 95.6% of the file is not that.* Measured 2026-09-14:

| | |
|---|---|
| entries | 49 |
| total lines | 257,216 |
| **largest single entry** (2026-09-05 09:41:26) | **245,791 lines** |
| median entry | 68 lines |

That one entry waved through 245,782 findings, of which **245,751 are
`PROSE NUMBER CONTRADICTS THE LEDGER OVERRIDES`** - the prose-number check
reading `OVERRIDES.md` itself. It was a feedback loop: the log grew, the check
found more contradictions inside it, the next override recorded all of them, the
log grew again.

**The loop is no longer live** - `check_prose_numbers_match_the_ledger()` now
returns 0 findings - so this is historical damage, not an active defect. But the
file still carries the output.

*Consequence for this refactor:* do not migrate 245,791 lines of a check reading
its own log. The decision content is the ~11,400 lines in the other 48 entries
plus that entry's genuine 31. **Open question for the user: is the giant entry
pruned, kept verbatim for provenance, or summarised to its reason plus a note of
what it contained?** Pruning a gate log is not a thing to do silently, which is
why it is a question rather than a plan.

## 5 · Stages

> **RENUMBERED 2026-09-18.** These were Stages A-G. §9 and §10 then introduced
> GOALS A-I, and "Stage G" and "Goal G" meant different things on the same page —
> a reader could not tell whether a cross-reference meant the prose artifacts or
> generalising the programs. Stages are now NUMBERED, goals stay lettered.

Each stage ends with a gate. The shape follows the migration's discipline: no
stage changes behaviour and shape at once, and every stage is verified against
a frozen baseline rather than by inspection.

### 5.1 · Stage 1 — widen the inventory and freeze a baseline
Write the scan that finds course-specific content by **all** its markers, not
only item ids: item ids, slot keys, deduction codes, handout numbers, and
per-file prose review for the stragglers. Produce a reviewed list, table by
table, classified as: *rubric content (migration's)*, *metadata (moves)*,
*engine (stays)*, or *undecided*.
Two measurements belong here rather than at the stage that trips over them:

* **Which moved tables are inside a scorer's closure.** Deleting a table changes
  its module's source, and `scorer_sha` hashes the closure of the scoring roots.
  Knowing up front which moves cost a re-record - and which cost nothing - is the
  difference between a priced stage and a surprise. The migration measured this
  at 05 and found the answer was "none"; at 06 it was "eight columns". Both were
  knowable before the edit.
* **The definition drops.** Removing ~46 module-level tables removes ~46 names,
  and `editguard.safe_write` refuses an undeclared drop. Every stage-D commit
  carries a declared `dropping=[...]` list, and `DEFINITIONS.json` must be
  updated one name at a time - never by bulk regenerate, which is the thing that
  inventory exists to prevent.

**Gate:** every one of the 46 known tables classified, plus whatever the wider
scan adds; zero tables left `undecided`; **the four instruments frozen as a
baseline** the way stage 00 of the migration froze its own - the audit's RAW
finding-set as a MULTISET, the self-test case count, `prompt_sha` per item per
side, and `scorer_sha` per item per side; and the closure/definition inventory
above produced and reviewed.

### 5.2 · Stage 2 — design the schema against the real content
Draft the JSON schema by fitting it to the *hardest* tables first
(`GOLD_DIVERGENCES`, `CORRECTED_GOLD`, `PROSE_ONLY_SLOTS`, `DESIGNED_TEXT`),
not the easiest. Decide the readability conventions and where each table's
rationale prose lands.
**Gate:** every classified table has a named home in the schema and a worked
example; no field is `TBD`; a person can read a sample file and say what it
means.

### 5.3 · Stage 3 — the reader, and dual-source verification
Build the metadata reader and have every consumer go through one accessor, with
a mode that reads **both** the old table and the new file and asserts they agree
— the migration's `dual` pattern, which is what caught its own gaps.
**Gate:** the reader reproduces every moved table exactly; `dual` runs the whole
suite with zero differences; the audit finding-set is unchanged.

### 5.4 · Stage 4 — move the tables, engine untouched
Emit the metadata file, flip the accessor to read it, delete the tables. One
group at a time, smallest first.
**Gate:** finding-set identical; no fingerprint moves except where a table is
genuinely inside a scorer's closure — and where it does move, the affected
columns are re-recorded.

### 5.5 · Stage 5 — `GOALS.md`

> **CORRECTED 2026-09-18.** This stage said "convert to the `goals` key", which was
> §3.3's plan: the specific half moving INTO the metadata JSON. §10.4 supersedes
> both — each prose artifact becomes a GENERAL file and a COURSE-SPECIFIC PROSE
> file that incorporates the general one by reference (G1c), and neither half
> becomes a JSON key. §3.3's second requirement stands and is the reason: both
> halves must remain human-readable and human-editable.
>
> **This stage is also blocked** by §10.4.1: `GOALS.md` has 9 headings across
> 16,516 lines and must be RESTRUCTURED into anchorable sections first.

Split `GOALS.md` general/specific per §10.4, port `goals.py` and the four other
readers, and **keep a human-editable path** and the ACTIVE line in `--preflight`.
**Gate:** all 112 entries round-trip; `check`, `next_label`, `misfiled_series`
and `stale_slot_claims` behave identically on the same corpus; a person can still
edit the active goal mid-task without tooling.

### 5.6 · Stage 6 — split `QUALITY_CONTROL.md` in two
Separate the general guide from a course guide. Give the GENERAL guide stable
anchors; move every course-specific passage into the course guide with a
reference back to the principle it applies; teach the nine readers to reach the
course guide through the rubric's metadata.
**Gate:** the general guide names no course, handout or item anywhere — checked
mechanically, the way the migration's C2 scan checks the engine; every anchor the
course guide names resolves; every reader gets its directives via the rubric it
was given; no reader has a hardcoded handout number; and both documents still
read start-to-finish as guides rather than as databases.


### 5.7 · Stage 7 — generalise the programs
The remaining pass: every program that touches the rubric, `GOALS.md` or
`QUALITY_CONTROL.md` takes the rubric as an input rather than assuming this
course.
**The acceptance test, concretely.** "Runs against a rubric it has never seen" is
the only real proof the course is out, and it is worth nothing if it is not
specified. The synthetic rubric is designed in stage B and must:

* be a DIFFERENT subject with different item ids, slot keys and deduction codes -
  not psychology renamed, which would pass on vocabulary the engine had merely
  stopped hard-coding;
* exercise at least one of every primitive the real rubric uses, so the test
  fails on a missing capability rather than on absence;
* carry its own metadata file and course guide, built by the same generator.

And the programs that must run against it, named rather than implied: the
generator (`olx_prompts --check`), the paper scorer's `fingerprint_text`, the
full enforcement audit, the self-test, and `measured.py --preflight`.

**Gate:** all five run to completion against the synthetic rubric with no
psychology checked out at all; **the audit reports findings about the SYNTHETIC
rubric** rather than silence - a check that has stopped looking returns `[]` and
reports success (T4), so a quiet audit here is a failure, not a pass.

---

### 5.8 Rollback, and what a stage IS

**Each stage is one commit, and the commit is the rollback unit.** A stage that
cannot be reverted cleanly was not a stage; it was two. The migration's commit
discipline (§7b there) applies unchanged: the audit runs as a per-stage test, the
finding-set is compared as a multiset before and after, and a stage whose
finding-set moved does not land until every difference is attributed to that
stage's own work.

**A removal is attributed, not welcomed** (T4). The dangerous direction is a
finding that disappears, because a check whose source has vanished returns `[]`
and reports success.

---

## 6 · Traps carried in from the migration

These are not hypothetical; each was paid for during the rubric migration and
every one of them applies again here.

**T1 · Prompt-complete is not scorer-complete.** The migration proved 23/23
generated bodies byte-equal and still had 107 omissions in 18 fields, because
byte-equality only exercises what the prompt reads. The analogue: a metadata
file that satisfies every program you remembered to run is not complete. Walk
the structure and compare, one name at a time.

**T2 · A table that looks derivable may not be.** `EXPECT` read exactly like the
inverse index of a per-item field and was a partial authoring table merged from
two sources. Ten names were mapped on the family resemblance; three were real.
**Verify each moved table against its original, individually.**

**T3 · A verification that runs while something else writes is not a
verification.** Two self-tests overlapping left `agreement.py` carrying an
injected mutation that parses, imports and passes every audit. Worse, an audit
taken during a self-test reported the right number for the wrong reason. Any
gate here must refuse to run while anything else is mutating the tree.

**T4 · A removed finding is the dangerous direction.** When a batch rewrite
broke an import, the audit's finding-set moved by −1 and it read like an
improvement. A check whose source vanished returns `[]` and reports success.

**T5 · One artifact, one writer.** A patcher that adds fields the emitter does
not know about is erased the next time the emitter runs, silently, with the gate
still green.

**T6 · Check the whole string, not a prefix.** A 60-character prefix match led to
a proposed change to shipped bytes that was not needed at all.

---

## 7 · What must not change

* **No scoring number moves** without being re-measured and re-recorded.
* **The audit's finding-set is the invariant** at every gate, compared as a
  multiset.
* **The leak gate stays clean.** This repo is public.
* **`GOALS.md`'s practice survives its format.** The file exists to keep the
  objective in front of whoever is working; a format that makes it harder to
  edit mid-task defeats the point even if every test passes.
* **`QUALITY_CONTROL.md` keeps working as a guide** that a person reads
  start-to-finish, not a database that happens to render.

---

## 8 · Sizing

Roughly 4,000 lines of tables in 8 files, two large prose files to restructure,
and ~14 modules to generalise — against an engine whose own audit is 140 checks.
The migration is the closest comparable: it took eight stages, and its cheapest
stages were the ones where a baseline was frozen first and the hardest case was
designed against before any code was written.

**Next action when the entry conditions are met:** stage A's widened inventory.
Nothing before that.

---

## 9 · One JSON file, generic code — the goal stated in terms of DATA and PROCEDURE

*Added 2026-09-18 on the user's instruction. The goals below are DECIDED, and as
of the same day so are all eight implementation choices — A1c, A2a, A3a, B1a,
B2a, C1b, C2a, C3c. The options NOT taken are kept under each decision rather
than deleted: a choice whose alternatives have been erased cannot be re-argued
when the reason for it stops holding.*

**The shape these eight decisions add up to:**

* One JSON file for the course (A3a), holding only authored data — every derived
  value is recomputed by the reader (A2a).
* `rubric_h2`'s builders survive as an AUTHORING tool that generates the expanded,
  canonical JSON; no reader ever instantiates a template (A1c).
* Everything an item needs, including what the prompt generator needs, lives on
  that item's entry (B2a), reached through one module that owns the file (B1a).
* Gold lives in a SECOND file by the same mechanism (C1b), so the rubric file
  carries no student-derived content and needs no per-read leak judgement.
* Migration proceeds module by module, each step proved by its table count
  reaching zero (C2a), measured by grep and gated by an enforcement check (C3c).

**One consequence of B2a to hold on to.** Folding the generator's tables into each
item's entry means an item entry carries rubric facts AND generator hints in the
same object. That is the price of "everything about Q1 in one place", and it was
chosen knowingly. The reader (B1a) must therefore expose them through SEPARATE
accessors — `rubric_for(item)` and `slot_notes(item, slot)` — so that a consumer
of the rubric never has to know the generator's fields exist, even though they
sit in the same entry. If that discipline slips, the two concerns will grow into
each other and B2b becomes the repair.

### 9.0 · What was measured first

Measured on the live tree, 2026-09-18, by AST parse rather than by reading:

| module | lines | functions | what they are |
|---|---|---|---|
| `rubric_h1.py` | 2,949 | **0** | pure data |
| `rubric_h3.py` | 830 | **0** | pure data |
| `rubric_h2.py` | 1,362 | 4 (650 lines, 47%) | **data builders**, not scoring rules |

`rubric_h2`'s four functions — `_example_item`, `_type_item`, `_definition_item`,
`_example_use_item` — are parameterised templates for repeated item shapes. They
run at import and return plain dicts.

**The consequence that matters: all three rubrics' `ITEMS` are ALREADY
JSON-serialisable.** 26 items, ~171,000 characters (h1 62k, h2 86k, h3 23k). The
builders are not an obstacle to serialisation; they are a question about the
FORM of the file, not its feasibility.

Beyond `ITEMS`, each module exports more names. Sorted by whether they can be
recomputed:

* **Derived** — `BY_ID`, `TOTAL`, `SLOT_SPEC` (h1, h2), `OC_GATES`, `FORBID`,
  `SLOT_OPTIONS`, the `*_ITEMS` index lists, `_MOVE_RULE`, `_EXAMPLE_RULES`.
* **Independent, and therefore authored data that must be carried** — `MAPS`
  (h1, h3), `READS_UTB_CHOICE`, `REQUIRED_MOVE`, `_OC_FRAME`, `_EXPECTS_RULE`,
  `_AUTHORED_RULE`, `_RESTRICTS_RULE`, `_HELD_BACK_RULE`, `AVOIDANCE_SCORES`,
  `_BARRIER_CONDS`, `EXPECT`, `_EXPECT_SHIPPED`, `_ONLYIF_SHIPPED`, `SLOT_SPEC`
  (h3).

*That split was made by a crude test (does the assignment mention `ITEMS`, a
loop, `sum(` or `BY_ID`) and is a starting point, not a finding. Each name must be
confirmed by hand before anything is dropped as derivable.*

### 9.1 · GOAL A — the rubric is data in JSON; the code that applies it is generic

**DECIDED.** `rubric_h1.py`, `rubric_h2.py` and `rubric_h3.py` stop being Python.
The facts they carry — form, item, and rubric points — move into the one JSON
file. What remains is generic code that reads that file and does what those three
modules do today, so the same processes can be applied to new content without
writing a new `rubric_hN.py`.

The test of success is not that the file exists. It is that **a new handout, or a
new course, can be scored by adding data and changing no Python.**

**DECIDED A1 (A1c) — what happens to `rubric_h2`'s builders.**

* **A1a · Expand them.** Serialise the built items. The file carries every item in
  full; the 405-line `_example_use_item` becomes four near-identical blocks.
  Simplest reader, largest and most repetitive file, and an edit to a shared shape
  must be made four times.
* **A1b · A template mechanism in the schema.** The file carries a template and
  its instantiations. Keeps the factoring that made the builders worth writing,
  but adds an instantiation step to every reader and a second thing to validate.
* **A1c · CHOSEN — Expand, and keep the builders as an authoring tool.** The JSON is
  expanded and canonical; the builders survive outside the pipeline to GENERATE
  that JSON when a new item of the same shape is added. Readers stay simple, the
  factoring stays available, and the generated file is checked in.

**DECIDED A2 (A2a) — derived values.**

* **A2a · CHOSEN — Store only authored data; recompute `BY_ID`, `TOTAL`, `SLOT_SPEC` etc.
  in the reader.** Smaller file, no chance of a stale derived value, and the
  reader owns the derivation rules.
* **A2b · Store everything, derived included.** The file is a complete picture
  and needs no reader logic, but every derived value is a thing that can go stale
  against the data it came from.
* **A2c · Store derived values AND verify them on load.** Complete file, stale
  values caught at read time rather than at use; costs a validation pass on every
  read.

**DECIDED A3 (A3a) — one file or one per handout.**

* **A3a · CHOSEN — One file for the whole course** (as §3.1 settled for the rubric).
* **A3b · One file per handout, plus a course file naming them.** Smaller diffs
  and fewer merge conflicts; more files to keep in step.

### 9.2 · GOAL B — the prompt generator's course tables move to the same file

**DECIDED, with a constraint the user set: those tables live in the SAME JSON file
as the rubric, and `olx_prompts.py` reaches them through functions rather than
reading the file itself.**

`olx_prompts.py` exists to turn the rubric into prompts and should need no course
knowledge. Measured 2026-09-18, it holds **12 module-level tables naming this
course's items**:

| table | lines | item ids |
|---|---|---|
| `SLOT_NOTES` | 396 | 16 |
| `REF_IDS` | 164 | **190** |
| `SCORING_DIVERGENCES` | 130 | 6 |
| `ITEM_NOTES` | 98 | 2 |
| `RESPONSE` | 49 | 63 |
| `PROBE_REACH_LIMITS` | 45 | 4 |
| *(6 smaller)* | | |

**DECIDED B1 (B1a) — where the accessors live.**

* **B1a · CHOSEN — A single `coursedata.py` module** that owns the file and exposes
  `slot_notes(item, slot)`, `ref_ids(item)`, and so on. One reader, one place to
  change, one import for every consumer.
* **B1b · Accessors on a loaded object** — `course = load_course(); course.ref_ids(...)`.
  Testable with a fixture course and no module-level state, but every caller must
  be handed the object.
* **B1c · Accessors beside the data they serve**, one module per concern. Keeps
  each accessor near its schema section; multiplies the modules that own the file.

**DECIDED B2 (B2a) — how the tables are keyed in the file.**

* **B2a · CHOSEN — By item id, folded INTO each item's entry.** `SLOT_NOTES` for `Q1`
  becomes a field on `Q1`. Everything about an item is in one place; the item
  entry grows and mixes rubric with generator hints.
* **B2b · As sibling sections keyed by item id**, parallel to `items`. The rubric
  stays exactly what it is; a reader must join two sections.
* **B2c · By PURPOSE, not by item** — a `prompts` section holding what the
  generator needs. Matches who consumes it; splits an item's facts across sections.

### 9.3 · GOAL C — the remaining tables and modules

**DECIDED in direction: all psychology-, course-, handout- and question-specific
data ends up in the one JSON file, and the modules that use it become generic.**
The route is OPEN pending A and B, because C is large enough that the shape
chosen there decides most of it.

Measured scope (plan §2.1, and a floor rather than a ceiling): **46 tables,
3,986 lines, across 8 modules**, and **15 modules import a rubric**. The largest
are `handouts.GOLD_DIVERGENCES` (784 lines), `handouts.CORRECTED_GOLD` (522),
`handouts.HANDOUTS` (281), `goals.CLOSURES_APPROVED` (234),
`handouts.GOLD_CEILINGS` (210), `enforcement.PROSE_ONLY_SLOTS` (201).

### 9.2a · B2a's enforcement obligation — REQUIRED, not a convention

B2a puts rubric facts and prompt-generator hints in the same item entry. The only
thing keeping them apart is then the accessor boundary, and a boundary that is
merely documented is a boundary that erodes: the first caller that reaches past
`rubric_for(item)` into `item["slot_notes"]` because it is right there will not be
noticed, and the second will cite the first.

**So the separation is enforced, in the same framework as the other 135 checks
(this is what C3c's "gate" half means for B2a).** Three obligations:

1. **The schema declares which group each field belongs to.** Every field on an
   item entry is either RUBRIC or GENERATOR — no field is unclassified, and a new
   field that names no group fails validation rather than defaulting. Without the
   declaration the check below has nothing to check against.

2. **`coursedata.py` exposes each group only through its own accessors.**
   `rubric_for(item)` returns the rubric fields and NOT the generator fields;
   `slot_notes(item, slot)`, `ref_ids(item)` and their kin return generator fields
   and NOT the rubric. Neither returns the raw entry. An accessor that hands back
   the whole dict defeats the boundary while appearing to honour it, and is the
   most likely way this fails.

3. **An enforcement check fails the gate when a module crosses the boundary.**
   Its subject is every module except `coursedata.py`: no other module may index a
   generator field off a rubric entry, or a rubric field off a generator result.
   It must also fail on the raw-entry escape — a module obtaining an item entry
   from anything other than an accessor.

**What failure should look like.** The check names the module, the field and the
group it belongs to, so the fix is obvious: use the other accessor, or declare the
field in the group it actually belongs to. A check that reports only "boundary
violated" would send the reader back to this section to work out what that means.

**The repair if it erodes anyway.** If the check has to be suppressed for a real
case, that is evidence the two concerns do not in fact separate at the field
level, and B2b — sibling sections keyed by item id — is the designed fallback. It
is kept above for exactly this reason.

**DECIDED C1 (C1b) — does gold belong in this file at all?**

* **C1a · Yes, one file holds everything.** One place to look, one schema.
  But `GOLD_DIVERGENCES` and `CORRECTED_GOLD` are about student submissions in a
  PUBLIC repository (§4.3), and merging them into the shipped rubric file puts
  that judgement on the critical path of every read.
* **C1b · CHOSEN — No — gold is a second file**, same mechanism, different file, and the
  leak rules apply to it alone. The rubric file can then be public without a
  per-read judgement.
* **C1c · One file, with gold in a section that is stripped on publication.**
  One authoring artifact; a build step that can fail open.

**DECIDED C2 (C2a) — order of migration.**

* **C2a · CHOSEN — By module** — take `olx_prompts.py` to zero course tables, then the
  next module. Each step is provable: the module's table count reaches zero.
* **C2b · By table kind** — move all gold, then all slot metadata, then all notes.
  Each step gives one schema section its final shape across every consumer.
* **C2d · By handout** — everything for handout 1, then 2, then 3. A whole handout
  is scorable from the file early, which is the closest thing to an end-to-end
  proof; but every module is touched three times.

**DECIDED C3 (C3c) — how a module is proved free of course data.**

* **C3a · A test that greps the module for item ids** — cheap, and it is the
  measurement §2.1 already uses, so the number is comparable over time.
* **C3b · An enforcement check** in the existing framework, so a new course table
  fails the gate rather than being noticed later.
* **C3c · CHOSEN — Both** — the grep as the metric, the check as the gate.

---

## 10 · What §9 does not reach — the other three kinds of embedding, and the proof

*Added 2026-09-18 after a review of §9 against the tree. §9 moves TABLES. Measured
below: tables are one of four ways psychology is embedded in `scoring/`, and the
goal — "generic code, applicable to other datasets" — has no test at all. Goals D-I
are DECIDED in direction; the choices under each are OPEN unless marked otherwise.*

### 10.0 · What was measured, 2026-09-18, by AST parse over 50 modules

| embedding | measure | where it is worst |
|---|---|---|
| tables (§9) | 46 tables, 3,986 lines | `handouts.py`, `enforcement.py` |
| **literal item ids in CODE** | **53** comparisons/lookups | `equivalence.py` 28, `measured.py` 7, `agreement.py` 3 |
| **course vocabulary in DOCSTRINGS** | ~**30** words (a first count of 188 was inflated — see 10.3.0) | `operant`, `utb`, `behavior_1`, `reinforcement` |
| **modules named for a course artifact** | **9** | `gold_slots_q6.py`, `baseline_h1.py`, `score_h1.py`, `simulate_h3.py`, `rubric_h{1,2,3}.py`, `handouts.py`, `gold.py` |
| **prose artifacts** | ~24,000 lines | `GOALS.md` 16,516 · `EQUIVALENCE.md` 3,036 · `QUALITY_CONTROL.md` 2,674 · `BACKLOG.md` 1,840 |

**Why this matters to C2a.** C2a proves a module clean when its table count reaches
zero. A module can reach zero and still compare against `"Q6"`, still be named
`gold_slots_q6.py`, and still explain behaviour modification in its docstring. The
per-module proof must therefore be widened — see 10.6 — or the migration will
report success against a definition that does not mean what it says.

### 10.1 · GOAL D — the 53 literal item ids in code

**DECIDED:** every one is either expressed as data or declared to be engine
behaviour. None may remain as an unexplained literal.

#### 10.1.0 · The 53 are four unrelated populations, not one

Measured 2026-09-18 by AST, after an earlier reading of this section treated them
as a single problem:

| group | count | where | what it actually is |
|---|---|---|---|
| self-test fixtures | **28** | `equivalence.py`, all inside `enforcement_selftest` | fault injection naming an item to damage — **D2, not D1** |
| **item `1c`** | **13** | `measured`, `agreement`, `agreement_app`, `olx_prompts`, `enforcement`, `compare_runs` | one item with a genuinely different shape, asserted in six modules |
| builder conditionals | **5** | `rubric_h2.py`, `if item_id == "DAY2"` | data variation inside a data builder — **dissolved by A1c** |
| item `Q6` | **4** | `gold_slots_q6.py`, `q6_consensus.py` | modules that exist for one question — **E1** |

**Three of the four groups are already answered by decisions taken elsewhere.**
Expanding the builders (A1c) turns `if item_id == "DAY2"` into the DAY2 entry
simply carrying that text. The `Q6` references belong to modules named for Q6 and
move with them (E1). The 28 are self-test fixtures (D2).

**So D's real scope is `1c`** — handout 3's graph item: eight boxes rather than
prose, a `rebuild_1c` gold path, a `series_box_holds` check, a
`GRAPH_UNREACHABLE_1C` exclusion list. Not a scattering of quirks; one item whose
shape differs, asserted in six places.

#### 10.1.1 · DECIDED D1 — the rule: properties become flags, behaviour becomes named strategies

The sites are not all asking the same kind of question, so one mechanism fits them
badly. `PER_ITEM_EXCLUDE["1c"]` asks about a PROPERTY of the item; `rebuild_1c`
selects a BEHAVIOUR. The rule is therefore:

1. **A property of the item becomes a declared field on the item.**
   `boxes: 8`, `derives_from_series: true`. The code asks the item what it is,
   never what it is called. No interpreter, greppable, testable.
2. **A choice of behaviour becomes a NAMED STRATEGY the item selects**, with the
   implementations held in an engine registry — `gold: "rebuild_series"`. The
   file says WHICH, never HOW, so the behaviour stays in Python where it can be
   tested, and a new course selects from what exists or adds an implementation.
3. **Anything that is neither is DECLARED ENGINE BEHAVIOUR**, in a table the gate
   reads, with a reason. A site that cannot be stated as a property or a strategy
   is a fact about the engine, and saying so is better than inventing a flag to
   hide it.

*Rejected, and why:* a **predicate language in the file** (the former D1b) was
considered and rejected as clearly disproportionate — designing, testing and
securing an evaluator for thirteen references to one item is a fixed large cost
against a variety that does not exist. **Flags alone** (former D1a) would wrap
`rebuild_1c` in a boolean the engine must still branch on, moving the branch
rather than removing it. **Strategies alone** (former D1c) would produce
single-member strategies wrapping what is only a property. **Open-ended
case-by-case** (former D1d) is what this rule replaces: the same freedom, but with
a stated test, so "what should this be?" has an answer rather than a discussion.

#### 10.1.2 · DECIDED D1x (D1x-c) — who decides property vs behaviour, and when

The rule has one soft edge: a site can often be argued either way
(`series_box_holds` is a check the engine runs, but "this item's boxes hold a
series" is also a property).

* **D1x-a · At migration time, by whoever moves the site**, recorded in the
  declaration table. Fastest; the boundary drifts with whoever is working.
* **D1x-b · Property first, strategy only when a property cannot express it.**
  A default that resolves most arguments without discussion, and biases toward the
  simpler mechanism. Risks flags that are really behaviour in disguise.
* **D1x-c · CHOSEN — Strategy first, property only for values the engine never
  branches on.** The sharper test — if the engine branches on it, it is behaviour
  and belongs in a registry — and it keeps branches out of the engine by
  construction. Produces more strategies, some of them thin.

**What choosing D1x-c commits us to.** The test is mechanical rather than a
judgement call: *does any engine code branch on this value?* If yes it is a
strategy, whatever it looks like. So `series_box_holds` is a strategy, because the
engine branches on it; `boxes: 8` stays a property, because nothing branches on
the number — it is read and used.

This is the strictest of the three and it was chosen for a reason worth keeping:
the whole goal of Goal D is that the engine stops deciding things by item
identity. A rule that lets a branch survive as a flag reaches the letter of that
goal while missing it, and the flag vocabulary then becomes the place where course
shape accumulates — which is precisely the weakness recorded against flags-alone
above.

**The cost, accepted knowingly:** more strategies than the other two rules would
produce, and some of them thin — a registry entry wrapping a few lines. A thin
strategy is the price of a branch-free engine, and it is preferred to a flag that
the engine must branch on anyway.

**The check this implies** (it belongs with 10.7's widened per-module proof): a
declared PROPERTY that appears in an engine branch is a rule violation, and the
gate should say so. Without that, D1x-c is a convention and drifts back to D1x-b
the first time a property is convenient.

#### 10.1.3 · DECIDED D2 (D2d) — the 28 self-test fixtures

All 28 sit inside `enforcement_selftest` (1,360 lines, 27 case functions). Each
case wraps a real function, mutates the data for ONE named item, and asserts that
a particular enforcement check fires. The item choices are not arbitrary but
neither are they declared: `_drop_counts` needs an item that HAS a `counts` field
(it uses Q1), `_drop_dealt` needs a job that is `dealt` (2a), `_filling` needs a
box that gold records as EMPTY and therefore a specific cell (Q6/p9).

* **D2a · Generic fixture selection.** Fixtures pick by shape — the first item
  with `counts`, the first `dealt` job. The only option under which the self-test
  runs against the Goal I fixture course, and it turns each case's precondition
  into code rather than leaving it implicit in a literal. But it is the most work;
  several cases need a conjunction (item AND participant AND an empty box) that is
  real query code living inside the instrument that tests everything else; and it
  makes COVERAGE DRIFT SILENTLY — damaging "the first item with counts" is Q1
  today and Q2 after a content edit, so a regression that only reproduces on Q1
  stops being caught with nobody noticing.
* **D2b · Fixtures declared in the course file.** Explicit, reviewable, pinned,
  cheap. Rejected on the governing principle: it would make the ENGINE's self-test
  require a section in every COURSE file, so a course omitting it could not run
  the self-test — general pointing at specific, which §0 forbids. It also puts
  test scaffolding into the shipped course artifact, and still never says WHY Q1.
* **D2c · Exempt the self-test.** Free, and honest that a fixture naming its
  target is not the sin an engine branching on identity is. But it leaves 28 of
  the 53 permanently course-bound and the self-test unable to run against the
  fixture course — the acceptance test for genericity would exclude the module
  that verifies the checks.
* **D2d · CHOSEN — D2c now, D2a as the destination, in that order.** The
  self-test is exempted from the gate FOR NOW, and made generic AFTER its own
  defects are fixed.

**Why the sequence rather than either end of it.** §11.11 records two open defects
in this instrument: a case that does not restore its own injection, and guards
that do not stop two self-tests running at once — the second confirmed on
2026-09-18 by starting two on the live tree and watching both proceed. This is the
instrument every gate depends on. Making its fixtures query-based while it is
known untrustworthy adds a NEW way for it to be quietly wrong — a query silently
selecting a different target — to a component that already has two. Fix what is
broken, then generalise.

**What this commits us to, so "for now" does not become "forever":**

1. The exemption is NAMED and SCOPED — `enforcement_selftest` only, never
   `equivalence.py` as a whole — and the gate REPORTS the exemption rather than
   passing in silence, so the 28 stay visible in the count.
2. The exemption is CONDITIONAL on entry condition 4 (the concurrency guard) and
   on the self-test's restore defect. When both close, the exemption expires and
   D2a is the work that replaces it. **BOTH CLOSED 2026-09-18**, and T4.1's
   `check_module_has_no_course_data` detected it the day it was written. The
   finding is PARKED with its reason and D2a is owed — see T4.1's record. (The
   cross-reference above read "§11.11's restore defect"; that section was
   renumbered to Stage 10 and the pointer was stale.)
3. D2a's coverage-drift weakness is answered when it is done, not deferred: a
   shape-selected fixture must REPORT the target it chose, so a silent change of
   target appears in the run's own output.
4. Until D2a lands, Goal I's fixture course is NOT expected to run the enforcement
   self-test, and 10.6 must say so rather than appearing to cover it.

### 10.2 · GOAL E — modules named for a course artifact

**DECIDED:** a generic engine contains no module named for a question, a handout
or a course.

#### 10.2.0 · The nine are four different problems

Measured 2026-09-18 (lines, share of lines inside defs, and how many modules
import it):

| module | lines | code | importers | what it is |
|---|---|---|---|---|
| `gold_slots_q6.py` | 276 | 72% | **0** | reads Q6's per-slot gold out of grader comments |
| `q6_consensus.py` | 241 | 53% | **0** | CLI — one stable parse of each Q6 answer |
| `baseline_h1.py` | 218 | 83% | **0** | CLI — scorer vs the 20 gold rows for handout 1 |
| `score_h1.py` | 507 | 72% | **0** | CLI — score handout 1, one item at a time |
| `simulate_h3.py` | 452 | 61% | 2 | reconstruct a handout 3 session from paper |
| `rubric_h1.py` | 2,949 | **0%** | 6 | pure data |
| `rubric_h3.py` | 830 | **0%** | 3 | pure data |
| `rubric_h2.py` | 1,362 | 47% | 7 | data + builders |
| `gold.py` | 176 | 44% | 6 | gold access |
| `handouts.py` | 2,354 | **10%** | **21** | the hub: 1,875 lines of constants |

Two facts drive the decision. **Four modules have no importers at all** — they are
command-line tools, not library code, so nothing is coupled to them and a rename
cannot break a caller. And **`handouts.py` is 90% data with 21 importers**, its
bulk being `GOLD_DIVERGENCES` (771), `CORRECTED_GOLD` (503), `HANDOUTS` (281) and
`GOLD_CEILINGS` (206) — all of which leave for the gold file under C1b anyway.

#### 10.2.1 · DECIDED E1 — per group, not one treatment

A single option fits none of these well, so the decision is made per group. The
three mechanisms (E1a rename-and-parameterise, E1b merge-per-kind, E1c
split-engine-from-data) are kept as the vocabulary.

| group | modules | decision | why |
|---|---|---|---|
| **rubrics** | `rubric_h{1,2,3}.py` | **already A1c** | they become the course JSON; no E decision is owed |
| **the hub** | `handouts.py`, `gold.py` | **E1c** | the only option that addresses 1,875 lines of constants behind 21 importers — and largely free, since C1b moves the gold tables out regardless |
| **item-shaped reader** | `gold_slots_q6.py` | **E1c** | 72% code, but the SHAPE it parses is Q6's: split into a generic grader-comment reader plus Q6's shape as data |
| **CLI tools** | `q6_consensus.py`, `baseline_h1.py`, `score_h1.py` | **E1a** | zero importers, so a rename cannot break a caller and a split buys nothing; parameterise by handout/item |
| **genuinely specific** | `simulate_h3.py` | **E1a, or left alone with a declaration** | reconstructing seven daily numbers and three axis labels from a paper chart IS handout-3-shaped work; a generic name would be a lie |

**Why not E1b anywhere.** Merging per kind was rejected on the measurement: the
four CLI tools have NO importers, so merging them yields no dependency
simplification while carrying the largest merge risk — the biggest change for the
smallest structural gain. If `baseline_h1` and `score_h1` turn out to share real
logic, that is a refactor to make on its merits, not a reason to merge modules
nothing depends on.

**The trap E1a carries, and the check for it.** Renaming `score_h1.py` to
`score_handout.py` while it still assumes handout 1's item shapes satisfies Goal E
and defeats it. So a module renamed under E1a is not "done" until it runs against
a SECOND handout — which is what Goal I's fixture course is for. Until then it is
renamed, not generalised, and the plan should not count it.

**`simulate_h3.py` is the one place a course-shaped module may survive**, because
its subject matter is a specific artifact. If it is left, it carries a written
declaration saying so — an undeclared exception is how "no course-named modules"
quietly becomes "no course-named modules except the ones we kept".

### 10.3 · GOAL F — course vocabulary in engine docstrings

**DECIDED:** engine documentation explains the ENGINE. Course facts cited as
illustration are marked as illustrations; course facts that are really
specification move to the course prose.

#### 10.3.0 · The number was wrong, and correcting it changes the goal

An earlier revision of this section said **188 course-vocabulary words in
docstrings** and listed `enforcement.py` 44, `measured.py` 19 and so on. That
count came from a regex, and the regex was wrong in two ways. Re-measured
2026-09-18:

| word | count | verdict |
|---|---|---|
| `handout` | **127** | **NOT course vocabulary.** A handout is a STRUCTURAL unit the engine will have whatever the course is, and most uses are usage documentation — `python3 agreement.py --handout 1`. Counting it made the problem look five times bigger than it is. |
| `behaviour` | 35 | **mostly ordinary software English.** `_behaviour_src` is "a function's source with its prose removed, so only behaviour is hashed"; "the caller keeps its existing behaviour". Nothing to do with behaviour modification. |
| `operant` | 9 | real |
| `utb` | 8 | real |
| `behavior_1`, `behavior_n` | 7 | real — course slot names |
| `reinforcement`, `psychology`, others | ~6 | real |

**The genuine population is on the order of 30 words, not 188.** Recorded because
the inflated figure would have justified a far larger intervention than the
evidence supports — and because the same regex is the one C3a would use as a
metric, so it has to be fixed there too or the gate inherits the error.

#### 10.3.1 · The mechanisms, named by WHICH WAY THEY POINT

An earlier revision of this section said F1c was "move the explanation to the
course file and leave the engine docstring pointing at it". **That violates §0** —
it is a general artifact pointing at a specific one, and it fails §0's own test:
a reader who has never heard of this psychology course would hit a pointer they
cannot resolve. It is retracted.

The mechanisms are therefore distinguished by direction of reference, not by kind
of sentence:

1. **Concept naming — the engine names VOCABULARY, never a course.** The docstring
   names the field or strategy it consumes: *"Gate on the criteria the item
   declares in `oc_definition`, then classify by type."* General, complete, and no
   reference leaves the engine. This is what F1c should have said.
2. **Generic incident — the engine may record WHAT WENT WRONG, stated without the
   course.** See 10.3.2.
3. **Anchor include — the course file incorporates general sections by
   reference** (Goal G). Points the right way by construction.
4. **The course JSON** — machine-readable facts, reached only through
   `coursedata.py` accessors (B1a).

#### 10.3.2 · DECIDED F1 — no course-derived sentence survives in general prose

**Course-derived illustrations are FORBIDDEN in engine prose, marked or not.** The
`e.g. (psych):` marker considered above is rejected: a convention that permits
course content in a general artifact decays into a rubber stamp, and §0's failure
mode is accumulation that "looks reasonable" one addition at a time.

Each sentence is therefore handled by what it is:

* **Specification** — the contract the code implements. The docstring names the
  concept (mechanism 1); the content lives in the course JSON and is explained in
  the course prose. Example: `score.derive_oc_ledger`'s "criteria 1-3 of the
  definition (an operant, a contingency, correct temporal order) ... only if it
  passes do we ask which of the four types it is" becomes a docstring about
  gating on declared criteria, with the criteria themselves course-side.
* **Incident and history** — moves to **the project changelog**, which is where a
  record of what happened belongs and which no general artifact points at.
  Example: `measured.report`'s "Handout 1's items were once reported as 12/14 and
  14/15 while their denominators were 19 and 20."
* **SPLIT, where the incident is the argument for the code.** Some incidents are
  not decoration — they are why the function is written as it is, and deleting
  them loses the reason. In that case the sentence is split: **a GENERIC statement
  of the failure stays in the engine prose, and the course-specific instance goes
  to the changelog.** `measured.report` keeps *"a reported figure is most easily
  wrong in two ways: the best run quoted instead of the median, and a denominator
  that has since grown"* — which is true of any course, justifies the median, and
  names nothing. The 12/14 instance goes to the changelog.

**The test for whether a split is owed:** *does the generic statement still
justify the code?* If yes, split and keep the generic half. If the sentence only
persuades because of its specific numbers, it is history and belongs wholly in the
changelog.

**F1a (rewrite everything generically) remains rejected** where it would destroy a
contract — a reader who cannot see WHICH definition the code implements cannot
check the implementation. Under the rule above that case does not arise: the
contract is not rewritten, it MOVES, and the docstring names the concept instead.

### 10.4 · GOAL G — the prose artifacts, GENERAL and COURSE-SPECIFIC

**DECIDED, and the shape is the user's, 2026-09-18:** each of these files becomes
**two** files — a GENERAL file holding the structure that should always be there,
and a COURSE-SPECIFIC file holding what comes from this course, its handouts, its
items and its student responses. **The course-specific file incorporates the
general file in pieces, BY REFERENCE** — it does not copy it, and it does not
replace it.

This supersedes §3.3 and §3.4, which proposed a split for `GOALS.md` and
`QUALITY_CONTROL.md` alone and did not say how the halves relate. The same
treatment now applies to `EQUIVALENCE.md` and `BACKLOG.md`.

**DECIDED G1 (G1c) — what "by reference" is, mechanically.**

* **G1a · Anchor include** — the course file names a section of the general file
  by a stable anchor. No build step; the reader follows the pointer. *An earlier
  revision called this "a convention this repo already uses". It is not: measured
  2026-09-18, exactly ONE anchor pair exists, and both halves sit in this plan six
  lines apart. It is a demonstration, never a working cross-file mechanism.*
* **G1b · Transclusion at build time** — a generated combined document, with the
  two sources authoritative. Readers see one document; there is a build to run and
  a generated artifact that can go stale.
* **G1c · CHOSEN — Reference with a checked contract** — anchors as in G1a, plus
  a gate that fails when a referenced anchor does not exist or a general section is
  orphaned. Same authoring cost as G1a; the pointers cannot rot silently.

**Why, and what the gate is for.** G1a's only fatal weakness is silent rot across
four files and ~24,000 lines, and there is no evidence the bare convention
survives use — it has never been used. The check is cheap (a few lines: collect
`qc:` definitions, collect `see: qc:` references, diff the two sets) and it fits
C3c's decided shape, where a rule that matters gets a gate rather than a
convention.

**The orphan half is the valuable half.** A dangling reference is an ordinary
broken link. An ORPHANED general section — one no course file points at — is the
signal that something placed in the general file is not actually general, which is
the failure §0 describes and the one no test otherwise catches.

**The gate's known soft edge:** a general section legitimately used by no course
YET is not wrong. So orphans WARN and danglers FAIL, and an orphan that is
deliberate carries a declaration rather than an exemption list — exemption lists
erode, and §0's failure mode is precisely erosion that looks reasonable one entry
at a time.

**What G1c does NOT fix:** the reading experience. Following a pointer into a
16,516-line file is still that, which is why 10.4.1 is a prerequisite rather than
a nicety.

#### 10.4.1 · PREREQUISITE — `GOALS.md` has no structure to anchor to

Measured 2026-09-18:

| file | lines | headings | lines per section |
|---|---|---|---|
| `GOALS.md` | 16,516 | **9** | ~1,800 |
| `EQUIVALENCE.md` | 3,036 | 88 | ~35 |
| `BACKLOG.md` | 1,840 | 56 | ~33 |
| `QUALITY_CONTROL.md` | 2,674 | 52 | ~51 |

Three of the four are already finely structured and can be split and anchored as
they stand. **`GOALS.md` cannot**: nine headings across 16,516 lines means there is
almost nothing to anchor TO, and a pointer into a 1,800-line section is not a
reference, it is a direction to go looking.

**So restructuring `GOALS.md` is a PREREQUISITE of Goal G, not a consequence of
it** — and on the measurement it is the larger job. It must be done before the
general/specific split, because the split has to cut along section boundaries that
do not currently exist, and inventing them during the split would mean deciding
what is general and where the seams are at the same time.

It is also the file where the split matters most: `GOALS.md` is 112 entries of
prose + structure, machine-parsed, read or written by five modules (§2.2, §2.3).

**Sequencing this adds to Goal G:**

1. Restructure `GOALS.md` into sections at a granularity a pointer can usefully
   name, with its machine-parsed contract unchanged — the five modules that read
   it must not notice.
2. Then split each of the four files general/specific.
3. Then place anchors and turn on the G1c gate.

Doing 3 before 1 would gate a mechanism that cannot yet be used on the file that
needs it most.

**DECIDED G2 (G2c) — the machine-written log becomes structured data, LATE.**

Measured 2026-09-18: `OVERRIDES.md` is 48 MB / 257,216 lines, TRACKED in git,
append-only, written by the pre-commit gate and read by five modules
(`precommit_gate`, `goals`, `enforcement`, `equivalence`, `measured`). Each entry
is a commit that used `ALLOW_UNDECLARED`, the findings it waved through, and the
reason given.

*Checked first, because this repository is public: **zero** lines carry
student-style first-person phrasing across all 257,216. The 333 quoted runs of 80+
characters are finding text — check names, slot sets, goal titles. G2 is a
structure question, not a leak question.*

* **G2a · Leave it entirely course-side.** Simplest, and defensible on content —
  every line names this course's findings. But it makes the course directory the
  home of a 48 MB machine artifact sitting beside a hand-authored rubric, and it
  leaves the FORMAT undocumented anywhere general, so a second course's gate would
  re-derive it from this file.
* **G2b · A general format description, log stays course-side.** Separates format
  (engine) from entries (course). Rejected as likely decorative: a documented
  format that drifts from what `precommit_gate.py` actually writes is worse than
  none, and nothing would hold the two together.
* **G2c · CHOSEN — it is not prose.** 48 MB of Markdown that is machine-written,
  machine-read by five modules and never read end-to-end by a person is a database
  in a document's clothes. The record becomes structured data (JSONL, appended);
  the `.md` becomes a RENDERING produced on demand.

**Why G2c.** It is what §0's second governing principle already says — *the JSON
is machine-owned, the `.md` files are ours* — applied to a file that is machine-
owned and in the wrong format for that rule. It also achieves G2b's aim in a form
that CANNOT drift: the format becomes a schema the writer and all five readers
share, rather than a description beside them. And it removes prose-parsing from
five modules.

**Sequenced LATE, and this is part of the decision.** G2c modifies the pre-commit
gate — the thing standing between this PUBLIC repository and a student-text leak.
Breaking it is the worst failure available in this refactor: not a wrong number,
but student text in a public repo. So:

1. **Not part of Goal G's main sequence.** G proceeds on the four prose files
   without it.
2. **Not started until the fixture course (Goal I) exists**, so the converted gate
   can be exercised against a second dataset before it is trusted with the first.
3. **The gate's leak check is not touched by this work.** The conversion changes
   how the RECORD is written, never what the gate refuses. If a step requires
   changing the refusal logic, that step is out of scope and stops.
4. **The 48 MB stays readable throughout.** The renderer lands before the old file
   is retired, so there is never a window where the audit record exists only in a
   form nobody can open — an audit log whose value is partly that anyone can read
   it should not become tool-only even briefly.

### 10.5 · GOAL H — the course files get their own directory

**DECIDED, the user's instruction:** the JSON file and the course-specific prose
files live together in their own directory, separate from the engine.

**DECIDED H1 (H1c) — `courses/<course-id>/`, and gold OUTSIDE the repository.**

* **H1a · Beside the content, in `psychology/`.** What §0 currently says. Keeps
  rubric and metadata together, and lo-blocks already mounts that directory. But it
  makes a content directory the home of scoring configuration, and gives no home to
  the four course-specific `.md` files from Goal G, which are not content lo-blocks
  renders.
* **H1b · A sibling of `scoring/`, e.g. `course/`.** Easy to find and obviously
  separate from the engine. Rejected for its name: a directory called `course/` in
  a repo holding one course works until there are two, which is §0's accumulation
  trap with a different shape.
* **H1c · CHOSEN — `courses/<course-id>/`**, e.g. `courses/edu.memphis.psych/`.

**Why.** A second course becomes a new DIRECTORY rather than a new convention,
which is precisely Goal I's acceptance test — the fixture course is
`courses/fixture/` and needs no structural argument. It makes the course id, which
§0 already uses to tie rubric and metadata together, the organising principle of
the filesystem too. And it is the only layout that FAILS visibly if someone
assumes a single course, rather than working fine until the second one arrives.

**Its cost, accepted:** it builds for a plurality that does not exist yet, and it
changes how lo-blocks mounts content — `content-sources.local.yaml` currently
points at a root containing `psychology/`.

#### 10.5.1 · §0 is AMENDED, not silently contradicted

§0 says the metadata file "lives beside the rubric in the content directory". H1c
supersedes that. The two identifiers in §0 are untouched and do the work they
always did — the metadata names its rubric, the rubric names its metadata — so
neither artifact is found by filename arithmetic and the pair may now live in
different directories without weakening anything. **§0 must be edited to say so.**
A plan that contradicts its own opening section in section 10 is a plan whose
reader cannot tell which part is current.

#### 10.5.2 · Two locations, not one — gold lives OUTSIDE the repository

The course data does not all live in one place, and the plan should stop implying
it does:

| artifact | location | why |
|---|---|---|
| course JSON (rubric, item data, generator fields) | `courses/<id>/` **in the repo** | publishable; it is the thing the engine reads |
| course prose, general/specific split (Goal G) | `courses/<id>/` **in the repo** | publishable |
| **gold, divergences, corrected gold (C1b)** | **`$COURSE_DATA/courses/<id>/`, outside the repo** | derived from student submissions; this repository is PUBLIC |

This is not a new rule, it is the existing one: `.gitignore` states that nothing
derived from student submissions belongs in this repo, and `migration_goldens` was
already moved out of it after being found to hold 433 student spans. C1b's gold
file inherits that, and putting it under the same `courses/<id>/` name OUTSIDE the
repo keeps the two halves legible as one course without putting either in the
wrong place.

#### 10.5.3 · `COURSE_DATA` should be renamed `COURSE_DATA`

**DECIDED.** The variable is named after one course's data set; under H1c it holds
`courses/<id>/` for any number of them, so the name becomes wrong exactly when the
refactor succeeds. `COURSE_DATA` says what it is.

The rename is mechanical but not free — `COURSE_DATA` appears in `paths.py`, in
runbooks, in shell environments and in this plan — so:

* it is a SEPARATE step, not folded into another goal, because a rename touching
  environment variables fails in ways that look like missing data;
* `COURSE_DATA` is honoured as a fallback for a declared period, with the reader
  preferring `COURSE_DATA` and warning when it finds only the old name — an
  environment variable that silently stops being read gives an empty result
  rather than an error, and empty results here look like a clean pass;
* `COURSE_OUT` and any other `MOLLY_*` names are renamed in the same step, so the
  repo does not end up with both vocabularies.

### 10.6 · GOAL I — the proof: a second dataset

**DECIDED, and this is the gap that matters most.** The success test in §9.1 is
*"a new handout, or a new course, can be scored by adding data and changing no
Python."* There is exactly ONE course in this repository and no fixture course
anywhere. **Genericity cannot be demonstrated against a single instance**: every
abstraction fits the dataset that shaped it, and the assumptions that were never
parameterised are found by the SECOND course, not the first. Every stage in §5 and
§9 is provable except the goal itself.

*Scope note, from D2d: until the self-test's fixtures are made generic, the
fixture course is NOT expected to run `enforcement_selftest`. The acceptance test
therefore covers scoring end-to-end but not the enforcement self-test, and says so
rather than appearing to cover it.*

**DECIDED I1 (I1a, sized by shape coverage) and I2 (I2c for stage one, I1b later).**

#### What the fixture must cover, and why "minimal" is the wrong size

Measured 2026-09-18: the 26 items produce **19 distinct key-shapes**. Seven fields
are universal (`id`, `label`, `max`, `increment`, `question`, `credit`,
`deductions`); after that it fragments — `guidance` on 25 items, `context` 23,
`derive_from_credit` 18, `blank_code` 11, `derive_from_criteria` 8.

**A two-item fixture would cover 2 of 19 shapes and prove almost nothing.** So the
fixture is sized by SHAPE COVERAGE, not by item count: it carries at least one
item of every key-shape the engine claims to handle, and the coverage is
measured and reported rather than asserted. An engine change that introduces a
shape the fixture does not cover is an engine change that has not been tested.

* **I1a · CHOSEN for stage one — a fixture course, invented content, sized by
  shape coverage.** Available now: no checkout, no PAT, no content negotiation, no
  leak surface. Its known weakness is recorded rather than wished away: **it is
  written by the same hand that abstracts the engine, at the same time, so it will
  encode some of the assumptions it exists to test.** Shape coverage narrows that
  but does not remove it. A fixture that passes proves the engine handles the
  fixture.
* **I1b · NO LONGER DEFERRED — THREE real courses are checked out. See §10.6.2.**
  The text below was written when none was known to be available; it is kept
  because its reasoning still holds, but its premise is false.
* **I1b · (as written) DEFERRED, not rejected — a real second course, when one is available.**
  Two exist as declared content sources in lo-blocks: `edu.memphis.writing`
  (public) and `edu.gsu.interdisciplinary` (non-public, needs a PAT). Neither is
  checked out here and neither is known to carry a scored assignment. A real course
  is the only thing that can FALSIFY the abstraction, because its shapes were not
  chosen by us — so it is scheduled as a second acceptance round when one becomes
  available, not dropped.
* **I1c · REJECTED — a fixture stripped from the psych course.** It inherits
  exactly the assumptions it exists to test: psych's item shapes, field vocabulary
  and gating structure, so the engine fits it by construction. It also carries a
  live leak risk the invented fixture does not — stripping and renaming
  student-derived gold is how partially-scrubbed data reaches a public repo, and
  that has happened in this project once already.

#### 10.6.1 · What "a fixture course" actually has to be — the INTAKE is the hard part

*Added 2026-09-18 on the user's correction, and it resizes I1a.*

The existing fixture is not the starting point it looks like. It is the **output
of a process that already happened**: the class materials were read, and the
forms, items, keys, gold scores and grader comments were found in them by hand.
The fixture *program* was then written **once the format of THIS example was
understood** — so it is fitted to one course's shapes, and the understanding it
encodes is not written down anywhere the engine can read.

That means "build a fixture course" is not one job but two, and the second is the
one that carries the generality:

1. **An inventory of the shapes an item can take.** The space is not open — it is
   **defined by lo-blocks' components, especially the input and grader
   components**. That inventory is what "sized by shape coverage" above has to be
   measured against; without it, "every key-shape the engine claims to handle" has
   no denominator and the coverage number means nothing.

2. **A program that INFERS the course from unstructured material.** Real intake is
   not a format. It is ordinary teacher-editable documents and spreadsheets —
   handouts, answer keys, grading sheets — with no fixed structure, from which the
   **course, its forms, its items, their keys and/or rubrics, and the gold scores
   and comments** must be inferred, and then **mapped onto the space of
   possibilities lo-blocks defines**.

##### The shape space, MEASURED — and how little of it we have touched

*Added 2026-09-18 on the user's second correction, with the counts taken from the
tree rather than estimated.*

lo-blocks ships **sixteen grader components**, counted by registered name —
eight built through `createGrader` (`CorrectGrader`, `CustomGrader`,
`DefaultGrader`, `FormulaGrader`, `NumericalGrader`, `RatioGrader`,
**`SlotSheetGrader`**, `StringGrader`) and eight declared directly
(`CheckboxGrader`, `KeyGrader`, `LLMGrader`, `MatchingGrader`, `RulesGrader`,
`SortableGrader`, `TabularMCQGrader`, `TextSelectionGrader`) — plus a generated
`*Match` rule-variant per grader for use inside `RulesGrader`.

It ships **fourteen gradable inputs**: `CheckboxInput`, `ChoiceInput`,
`CodeInput`, `ComplexInput`, `DropdownInput`, `FormulaInput`, `Freewrite`,
`LineInput`, `MatchingInput`, `NumberInput`, `SortableInput`, `TabularMCQ`,
`TextArea`, `TextSelectionInput` — and **`CapaProblem` and `MarkupProblem`**,
two self-contained gradable problem families carrying their own grading.

**A first count of this missed most of it**, and the way it missed is worth
keeping: it read the `grading/` directory and the `input/` directory as though
they were the population. `SortableGrader`, `MatchingGrader`, `TabularMCQGrader`
and `CheckboxGrader` live beside their inputs, not in `grading/`;
`TextSelectionInput` and `Freewrite` live under `language-arts/`; `CodeInput`
lives under `authoring/`; and the eight `createGrader` graders register under a
`base:` name that the grep for `name: '...Grader'` never sees. Directory
structure is not a census.

##### Only ONE of the sixteen is what this project has been about

`SlotSheetGrader`, fed by `LLMAction`, scores constructed response. Everything
built here — the rubric modules, `olx_prompts.py`'s generated prompts, the
agreement sweeps, the gold comparison, all 152 enforcement checks — addresses
items of that one shape. Measured against this repository:

| | |
|---|---|
| grader components in lo-blocks | **16** |
| graders the psych course uses | **7** — `CheckboxGrader`, `CorrectGrader`, `KeyGrader`, `MatchingGrader`, `SlotSheetGrader`, `SortableGrader`, `TabularMCQGrader` (an earlier count of 2 tested only ten grader names and missed five) |
| gradable inputs in lo-blocks | **14** (+ CapaProblem, MarkupProblem) |
| inputs the psych course uses | **7** of 15 — CheckboxInput, ChoiceInput, LineInput, MatchingInput, SortableInput, TabularMCQ, TextArea |
| **scored items, all handouts** | **26** |
| **of those, slot-sheet shaped** | **26 — every one** |

Eleven files in the course carry a `ChoiceInput` and **not one of those items is
scored by this engine**.

##### The exhaustive census — 122 blocks, and the scoring ones are a quarter of it

*Taken 2026-09-18 over every block declaration in
`packages/shared/components/blocks`. **Caveat, stated rather than hidden:** the
authoritative registry is `blockMetadataAutogen.json`, generated at build time and
not committed, and the generator will not run in a clone without installed
dependencies. This census reads the source declarations instead — `core({name:})`
and `createGrader({base:})` — and should be re-confirmed against a built tree
before anything depends on the exact number.*

| | count |
|---|---|
| block definitions (PascalCase) | **122** |
| graders | 16 |
| gradable inputs | 14 |
| **everything else** | **95** |

##### The other 95 are the course's STRUCTURE, and items are encountered INSIDE them

*Recorded on the user's third correction, and it is the largest of the three.*

A scoring-only census reads the 95 as irrelevant. They are not: **they are how an
item is reached.** An item does not appear bare — it sits inside a `Sequential`,
behind a `NextReveal`, on a `Tabs` page, in a `Carousel`, inside a `Collapsible`,
gated by an `IntakeGate`, ordered by a `Navigator`, or inside a `MasteryBank` that
repeats it until mastery. The intake program must infer **which of these to use**
from teacher materials, exactly as it must infer which grader to use.

| category | n | what it carries |
|---|---|---|
| `layout` | 20 | `Carousel`, `Collapsible`, `CompactPopout`, `DynamicList`, `Hidden`, `IntakeGate`, `Navigator` (+4 detail/preview variants), `Noop`, `Sequential`, `SideBarPanel`, `SplitPanel`, `SplitTest`, `Tabs`, `TimedContainer`, `Vertical` |
| `display` | 16 | prose, math, media and feedback surfaces items are explained by |
| `action` | 10 | `LLMAction`, `LLMFeedback`, `ActionButton`, `HintButton`, `ShowAnswerButton`, `SetFieldAction`, `CopyFieldAction`, `PrintAction`, `Flash` — item BEHAVIOUR, and the path by which `SlotSheetGrader` is fed |
| `scenario` | 6 | `Chat`, `Cast`, `CastEditor`, `CharacterBuilder`, `AvatarEditor`, `NextReveal` |
| `reference` | 5 | `AggregatedInputs`, `AnswerDistribution`, `Ref`, `UseDynamic`, `UseHistory` — cross-item and cross-student structure |
| `grading` | 5 | `Correctness`, `DerivedChecks`, `Rule`, `ScoreTable`, `SheetValue` — grading machinery that is not itself a grader |
| `input` | 4 | `Key`, `Distractor`, `SimpleMatching`, `SimpleSortable` — the PARTS an item is built from |
| `language-arts` | 4 | `Annotate`, `SimpleTextSelection`, `WordUsage`, `WritingRhythmPlot` |
| `specialized` | 4 | `MasteryBank`, `DigitSpanTask`, `LiquidTemplate`, `PEGDevBlock` |
| `media` | 3 | `Video`, `VideoPlayer`, `Transcript` |
| `CapaProblem`/`MarkupProblem` | 3 | two self-contained gradable problem families |
| `utility` | 2 | `ErrorNode`, `Spinner` |
| `authoring` | 10 | **not intake targets** — `Studio`, `Catalog`, `BlockDoc`, `DocsBrowser` and friends are the authoring environment, not course content |
| `_test` | 3 | **not intake targets** |

So the intake program's target space is roughly **109 blocks**, not the 30 that
score. Subtracting the 13 authoring and test blocks is itself an inference the
program will have to encode, since nothing in a teacher's document says which
blocks are course content.

**This is what makes the intake program hard, and it is not a scoring problem.**
Choosing `MatchingGrader` over `CheckboxGrader` is a local decision about one
item. Choosing `Sequential` over `Tabs` over `MasteryBank`, or deciding that a
worksheet's three parts are one `Carousel` and not three pages, is a decision
about the SHAPE OF THE COURSE, inferred from documents that never mention any of
it. The shape inventory (item 1) therefore has to cover the structural space as
well as the scoring space, or the intake program has a target for its items and
none for the course that holds them.

##### TAKEN 2026-09-18 — `shape_inventory.py` → `SHAPE_INVENTORY.json`

`134 blocks registered. 121 intake targets. The psych course exercises 50 of them
— 41%.` `--self-test`: 6/6 failure modes caught.

**The registry is the population, not the directory tree.** The hand census two
sections up got 122 and missed twelve, `Course` and `SlotSheetGrader` among them.
This reads `blockMetadataAutogen.json`, which the lo-blocks build generates — so
the tool also refuses (`--check-fresh`) when any component source is newer than
the registry describing it, because a stale build artifact has cost this project
19 observations once already.

| role | n | intake target? |
|---|---|---|
| `structure` | 37 | yes — an item is reached THROUGH these |
| `display` | 26 | yes |
| `grader` | 16 | yes |
| `gradable_input` | 15 | yes |
| `action` | 14 | yes — `LLMAction` feeds `SlotSheetGrader` by this path |
| `item_part` | 6 | yes — `Key`, `Distractor`, the `Simple*` shorthands |
| `grading_support` | 5 | yes |
| `gradable_item_family` | 2 | yes — `CapaProblem`, `MarkupProblem` |
| `not_intake` | 13 | **no** — the authoring studio and test blocks |

An `UNCLASSIFIED` block is a **refusal, not a bucket**: a classifier that bins the
unknown reports coverage of a space it never saw. That refusal fired on the first
run and was right — `TabularMCQ` writes `...blocks.input({`, namespaced, and the
input detector was anchored on the bare spelling.

##### What one course does NOT reach

The course we have exercises 7 of 16 graders and 7 of 15 gradable inputs. Never
used, and therefore never tested by anything in this repo:

* **graders** — `CustomGrader`, `DefaultGrader`, `FormulaGrader`, `LLMGrader`,
  `NumericalGrader`, `RatioGrader`, `RulesGrader`, `StringGrader`,
  `TextSelectionGrader`
* **inputs** — `Annotate`, `CodeInput`, `ComplexInput`, `DropdownInput`,
  `FormulaInput`, `Freewrite`, `NumberInput`, `TextSelectionInput`
* **24 of 37 structural blocks**, including `Carousel`, `NextReveal`,
  `Navigator` (and its four detail/preview variants), `DynamicList`, `SplitTest`,
  `TimedContainer`, `Hidden`, `CompactPopout`, `SharedNotes`, `MasteryBank`'s
  neighbours `DigitSpanTask` and `PEGDevBlock`, and the whole `Cast`/`AvatarEditor`
  character-building family

**This is the denominator I1a lacked.** "Sized by shape coverage" can now be
stated as a number, and the number says a fixture modelled on what we have seen
would cover 41% of the intake space and report itself complete.

##### The pairing is NOT declared, and the tool refuses to invent it

No grader declares which inputs it pairs with. A grader declares `inputType`
(`single`/`list`) or `slots` (dict mode) and whether it `infer`s its inputs from
its children; compatibility with a given input is a value-schema question plus
authoring convention, and the convention lives in prose and READMEs. The inventory
records both sides' schemas and stops there.

That is a finding, not a gap in the tool: **the intake program's hardest decision
— which grader this item becomes — cannot be read off the declarations**, so it
will have to be made from convention, from the READMEs, or from examples. 154
declared attributes were extracted across 64 blocks; the other 70 declare none
this reader can see, which bounds how much of the shape space is machine-readable
at all.

##### DECLARED 2026-09-18 — `grader_inputs.py`, and it is gated

*On the user's instruction: "determine which graders can go with which inputs and
create a hard declaration of that, because it will guide almost everything else."*

`16 graders declared, 20 nested pairings, 20 response sources (14 constructed, 6
selected). 319 .olx scanned. The declaration and the evidence agree, both ways.`
Gated by `check_grader_input_pairings_are_declared`.

**Three mechanisms, and the third is the one a nesting-shaped reading misses:**

1. **nested** — the grader WRAPS the input and infers it from its children
   (`infer: true`). All 24 demonstrated nestings are of this kind.
2. **targeted** — the grader names its source by id (`infer: false`).
   `SlotSheetGrader target=` points at an `LLMFeedback`, which is not a student
   input at all.
3. **referenced** — the input is read by an `LLMAction` through
   `<Ref target="...">` **inside the prompt body**. Nothing links input to grader
   by attribute; the link is a reference embedded in prose. **This is how all 26
   scored psych items are reached**, and a reader looking only for nesting sees
   none of it.

##### There are TWO LLM graders, and they are not interchangeable

* **`LLMGrader`** — nested, async, wraps one constructed response and judges it
  against `question` + `rubric` (+ optional `answer`), returning **one**
  correctness verdict. Declared in the `org.mitros.dev` namespace, which is a
  namespace and not a gate.
* **`SlotSheetGrader`** — targeted; scores the **structured** sheet of slots and
  counts an `LLMAction` produced. Multi-slot and point-weighted, which is what a
  rubric needs and what a single verdict cannot express.

So the simple path exists and is much cheaper to author: for an item that needs
one holistic judgement, `LLMGrader` is the answer and the whole `LLMAction →
LLMFeedback → SlotSheetGrader` chain is unnecessary.

##### "Could be scored by an LLM" is not "should be"

*On the user's correction.* A `<Ref target= field=>` renders any component's
value into a prompt, so nearly everything **could** be handed to a model. The
table records that as `llm_fallback` and never as a preference: **asking a model
to score a `ChoiceInput` is strictly worse than `KeyGrader`** — slower, costlier,
non-deterministic, and wrong sometimes — when the answer is a set the author
already enumerated. Nine of the twenty sources carry `llm_fallback: True` and
prefer a deterministic grader; an intake program that read the capability as a
recommendation would route an entire course through a model.

Equally, **short is not selected**: a `LineInput` is constructed response. It
prefers `StringGrader`/`RulesGrader`/`NumericalGrader` when the expected answer
is fixed, and the LLM path when the line is open-ended.

##### Not every response source is named `*Input`

A census keyed on the name — or even on the `...input(` declaration — misses
**`Chat`, `Annotate`, `AvatarEditor`, `CastEditor`, `CharacterBuilder`,
`DigitSpanTask`** and `SimpleTextSelection`. They collect student work through
ordinary state dispatch. **A conversation is constructed response**, and scoring
annotations written onto a text is judgement by nature. All are declared, with
the LLM chain as their preferred path and `ungraded`/`self-measuring` where that
is the honest answer.

##### The evidence classes are kept apart

`LLMGrader ← TextArea` is declared and appears in no `.olx`; the both-ways check
reported it and was right to. Its evidence is the block's **own usage note**, so
it is declared as `doc_only` with the source named, rather than waved through.
One pairing of twenty rests on documentation rather than on a shipped example,
and the run says so.

##### THE STRUCTURAL HALF — `structure_kids.py`, also gated

`26 containers declared, 11 leaves. 319 .olx scanned: 215 nesting edges, 81
reference edges. The containment declaration and the evidence agree.`
Gated by `check_container_contents_are_declared`.

**No block declares what it may contain.** There is no `childTags`, no
`allowedChildren`, no schema of permitted kids anywhere in lo-blocks —
containment is decided by each block's parser and its runtime. So the same
approach as the pairings: declare by hand, mine the corpora, and gate both.

**Four mechanisms, and three are invisible to a nesting scan:**

1. **nested** — children are nested tags. `Vertical`, `Sequential`,
   `Collapsible`, `Hidden`, `NextReveal`, `TimedContainer`, `DynamicList`,
   `Tabs`, `Course`.
2. **slotted** — nested into NAMED REGIONS marked by stub blocks: `SideBarPanel`
   takes `MainPane` and `Sidebar`, which the parent parses rather than rendering
   as components.
3. **referenced-body** — the body is a LIST OF IDS:
   `<Carousel wrap="true">ctt, irt, rasch</Carousel>`,
   `<MasteryBank goal="3">demo_q1 demo_q2 demo_q3</MasteryBank>`. These contain
   nothing syntactically, and a first pass here reported `Carousel` and
   `MasteryBank` as "never seen as a parent" while they appear in twelve files.
4. **referenced-attribute** — attributes name blocks by id: `Navigator preview=
   detail=`, `AggregatedInputs`, `AnswerDistribution`, `UseHistory`, and every
   grader's `target=`.

##### The decision an intake program actually faces

| relation | containers |
|---|---|
| **NESTS an item** | `Collapsible`, `DynamicList`, `Hidden`, `NextReveal`, `Sequential`, `TimedContainer`, `Vertical` |
| **REFERENCES an item** | `AggregatedInputs`, `AnswerDistribution`, `Chat`, `MasteryBank`, `Ref`, `UseDynamic`, `UseHistory` |

**Choosing the container decides the shape of the document, not an attribute of
it.** A `Sequential` of three items and a `MasteryBank` of the same three are
different files: in the first the items are written inside, in the second they
are written separately and named. That is the second-order choice §10.6.1
predicts will often be indeterminate, and it is not a formatting decision.

`Vertical` is the general-purpose body — it nests every role there is, including
`grading_support` and `item_part` — and is what an intake program should default
to when nothing more specific is implied.

##### REFERENCE IS NOT CONTAINMENT

Conflating them made `Ref` the largest container in the corpus: **431 `TextArea`s
"inside" a block that holds nothing and points at everything.** The two relations
are declared and checked separately. This is the same distinction the grader
table draws between a nested grader and a targeted one, and it keeps reappearing
because it is how lo-blocks is built: *structure is expressed by naming at least
as often as by nesting.*

Four containers are declared and **undemonstrated** — `SharedNotes`,
`SideBarPanel`, `SplitPanel`, `SplitTest` — with `SplitTest` appearing in no
`.olx` at all. They are recorded as declared-without-evidence rather than
dropped, because absence from one corpus is not absence from the engine.

##### CORRECTED 2026-09-18 — the corpus was wrong three ways, and the docs declare what I said nothing declares

*On the user's questions: "have you looked at all the tasks in edu.memphis.psych?"
and "double check all your mapping assumptions against the data provided there and
in the demo content directory" and "look for useful info in the documentation."
The honest answer to the first was no, and checking found four errors.*

**1. A build artifact was counted as evidence.** `lo-blocks/.stage/content` holds
**29 staged copies of the psych course, of which only 20 still match** — so the
course was mined TWICE and a STALE copy contributed as though it were independent
evidence. Every edge count involving psych content was inflated. The corpus is now
chosen in `olx_corpus.py`, once, with `.stage`/`dist`/`build` excluded by name.
**A corpus is a decision, not a glob.**

**2. The documentation was ignored, and it is the largest evidence source there
is.** 68 block readmes carry **295 fenced OLX examples** — a corpus the size of
the standalone files, authored by the people who wrote the blocks. Mining it
immediately produced five containment facts and two pairings no `.olx` shows,
including **`Course` nests `Sequential`**, which this plan's own authored reason
had asserted while the evidence-derived table said `display` only.

**3. "No grader declares which inputs it pairs with" was too strong.** It is not
declared in CODE, but it IS documented: `CorrectGrader.md` says outright *"is
input-agnostic. It works with CheckboxInput, ChoiceInput, LineInput, TextArea,
or…"*, and `NumericalGrader.md` says *"works with any input that outputs a
number"*. The declaration now carries four inputs for `CorrectGrader` instead of
two, and the claim is restated: **the pairing is not machine-readable, but it is
authored prose, and prose written by the block's authors is evidence.**

**4. `SimpleMatching`, `SimpleSortable` and `SimpleTextSelection` were
misclassified as item PARTS.** Each is *"a terse one-tag PEG syntax that expands
to a CapaProblem"* — whole items in a compact spelling, not pieces of one. Their
own descriptions say so. They are now `gradable_item_family` and declared
self-grading.

After the corrections: **575 sources scanned** (280 files + 295 documented
examples), 23 nested pairings, 27 containers, 242 nesting and 94 reference edges,
all three gates clean.

##### The repository holds far more than the three handouts

`psychology/` carries a whole **SBA course** — parts 1–4 with activities, quizzes
and auto variants — alongside the three `bmod_` handouts: 29 `.olx` in all, plus
`function-questions` and `operant-questions` banks and an `operant-mastery` bank.

##### A FIFTH authoring surface: the PEG formats

And the course is not written only in OLX. It carries **`.chatpeg` (13),
`.textSelectionpeg` (5), `.textHighlightpeg` (3), `.cast` (2), `.liquid` (2)** —
compact, teacher-writable source formats that expand into blocks. lo-blocks
defines the grammars behind them: `chat.pegjs`, `textSelection.pegjs`,
`matching.pegjs`, `sort.pegjs`, `dropdown.pegjs`, `idlist.pegjs`, `capa.pegjs`,
`dnd.pegjs`, `clip.pegjs`.

A `.textSelectionpeg` is prose with the answers in brackets:

```
Look at each scenario below and highlight the examples that show [reinforcement].
1. [A child receives a sticker for completing homework on time].
```

**This matters more to the intake program than anything else in this section.**
The question "how does a teacher write an item without writing XML" already has
answers in this engine, and they were built for exactly the materials the intake
program will be reading. An intake program that emits OLX when a `.textSelectionpeg`
would do is producing something no teacher can edit afterwards.

They are deliberately NOT mined as OLX — `olx_corpus.SEPARATE_SURFACES` names
them — because attributing a grammar's constructs to its expansion would put
shapes in the inventory that no block declares. They need their own pass, and
that is now owed.

##### 10.6.2 · FOUR courses exist, and the corpus is now declared

*On the user's corrections, arriving one at a time: `edu.memphis.writing`,
`edu.mtsu.transitional-reading`, and `~/code/interdisciplinary`.*

**I1b said a real second course was "not available". Three are, and all three are
checked out.** That premise was wrong for the whole of this work, and every
coverage number taken before now was quietly about one course while claiming to
be about the engine.

| course | intake shapes used, of 121 |
|---|---|
| psych | 50 |
| edu.memphis.writing | 35 |
| interdisciplinary | 35 |
| edu.mtsu.transitional-reading | 20 |
| **all four together** | **67 (55%)** |

The four courses **overlap heavily**: 140 course-shape uses collapse to 67
distinct shapes. And **54 intake shapes are used by no course at all**, including
nine of the sixteen graders — `RulesGrader`, `NumericalGrader`, `StringGrader`,
`FormulaGrader`, `RatioGrader`, `DefaultGrader`, `CustomGrader`, `LLMGrader`,
`TextSelectionGrader` — which exist, are documented, and appear in no course
anyone has written.

##### A corpus is a decision, and three attempts to avoid making it failed

Each failed differently and the sequence is the lesson:

1. **`*.olx` under two roots** swept in `lo-blocks/.stage/content`, a staging
   COPY of the psych course: mined twice, nine files stale, counted as
   independent evidence.
2. **Sibling directories named `edu.*`** found two of the three new courses and
   missed `interdisciplinary`, which is neither named `edu.*` nor beside the
   engine.
3. **"Any directory containing OLX"** — evidence-based, and *worse*: nine roots
   including three parallel checkouts of trees already listed, reporting **1171
   files and 1155 documented examples where there are about 300 and 295
   distinct.** Counting a second checkout as a second course is the `.stage`
   error again, at repository scale.

**Auto-discovery is a glob with extra steps.** Which trees are DISTINCT evidence
is a judgement nothing in the filesystem encodes, so `olx_corpus.DECLARED_ROOTS`
names five with a reason each, `COURSE_ROOTS` overrides, and **a declared root
that is not present is a FINDING** — a corpus that silently shrinks reports
smaller coverage and calls it a result.

##### What the new courses changed in the declarations

The pairing table survived all four courses unchanged, which is some evidence it
is right. The containment table did not: `Cast` turns out to nest `Sequential`,
`Tabs`, `SplitPanel` and `Vertical` — a real container, not the leaf it was
declared; `Carousel` both NESTS and REFERENCES; `Ref` and `UseHistory` nest
`IntakeGate`; and `Navigator` REFERENCES an `Annotate`, an item. Widened against
evidence, gate clean.

##### 10.6.3 · THE PEG AUTHORING FORMATS — `peg_formats.py`, gated

*The surface a teacher actually writes in, and the closest thing in this engine
to the intake program's intended output.*

`13 PEG formats registered, 7 creatable by an author. All 7 are used by the
courses.` Gated by `check_peg_authoring_formats_are_declared`.

**This mapping IS declared**, unlike the grader and containment tables.
`packages/shared/generated/parserRegistry.ts` gives every extension its grammar,
its directory, a display name and a **`creatable`** flag — whether an author may
make a file of that type. So `peg_formats.py` READS the registry rather than
inventing a mapping, and declares only what the registry does not carry: **what
the teacher writes**.

| creatable format | block | what the teacher writes | files |
|---|---|---|---|
| `textSelectionpeg` | SimpleTextSelection | prose with the answers in `[brackets]` | 5 |
| `matchingpeg` | Matching | two columns, one pair per line | 2 |
| `sortpeg` | Sort | items in their correct order | 3 |
| `dropdownpeg` | Dropdown | options in a list, the key marked | 2 |
| `chatpeg` | Chat | a dialogue script, `::id [attrs]` turn markers | 22 |
| `idlistpeg` | MasteryBank | a list of OLX ids — an item bank | 2 |
| `capapeg` | Capa | an Open edX-style markdown problem | 12 |

Six more are registered and **not** author-creatable — `clippeg`, `demopeg`,
`dndpeg`, `exprpeg`, `grammarpeg`, `templatepeg` — engine internals and
prototypes. That flag is the engine telling an intake program which formats are
fair game, and it should be obeyed rather than re-derived.

##### A SIXTH reference mechanism: a block naming a FILE

`<Chat src="psych_sba_part2.chatpeg" cast="characters.cast" />`. The five
mechanisms recorded so far relate blocks to blocks; this one relates a block to a
FILE. Peg content is absent from `manifest.yaml`, reached only by `src=`, and
**invisible to every block-level scan** — including all three of the earlier
declarations, which is why this pass was owed.

##### What the pass found

* **`.textHighlightpeg` is registered NOWHERE.** Three psych files use it, and
  each is **byte-identical** to a `.textSelectionpeg` beside it — a renamed
  grammar whose old files were left behind. The check caught it on its first run.
* **Six authored psych files are reached by nothing.** The three
  `.textHighlightpeg` dead twins *and* their three live `.textSelectionpeg`
  originals: three highlighting quizzes, written, parseable, routed nowhere.
  Declared in `ORPHANED_CONTENT` with reasons so a NEW orphan fails rather than
  hiding among them, and so a declaration about a deleted file is itself
  reported.
* **Orphans are a course question, not an engine one.** lo-blocks carries twelve
  unreferenced `test-*.capapeg` fixtures and demo scripts, which is what they are
  for. Counting them buried the six real ones among twenty-six.

##### Why this matters more than the OLX tables

An intake program that emits OLX where a `.textSelectionpeg` would do has
produced something **the teacher cannot edit afterwards**. The bracketed-prose
quiz above is one file, readable by anyone; the OLX it expands into is not. The
`creatable` flag, the seven formats and their authored shapes are therefore the
intake program's preferred output space, and the OLX tables describe the
fallback for everything those seven cannot express.

##### 10.6.4 · THE INPUT SIDE — what teacher materials actually look like

*On the user's pointer to `~/code/activities_materials`: "very partial, not as
complete as what's in molly_data, but helpful. A few will partly match existing
activities."*

Everything in §10.6 so far describes the intake program's OUTPUT — the blocks,
the pairings, the containers, the PEG formats. This is the first look at its
INPUT, and it changes what the program has to be able to do. **17 files, `.docx`
and `.pptx`, no other format.**

**They span all four courses**, and the correspondence is measurable where the
material carries text — keyword overlap against each course's OLX:

| material | course | overlap |
|---|---|---|
| Psych SBA FBA2 prototype (×2 versions) | psych | 60/60 |
| REVISIONS … SBA Interdisciplinary Reasoning Prototype | interdisciplinary | 59/60 |
| Psych_SleepScenario_Draft2 | psych | 57/60 |
| SBA FBA prototype DRAFT 11.26.24 | psych | 56/60 |
| DCA SBA 1 | writing | 49/60 |
| IRP SBA_ | interdisciplinary | 49/60 |

The method discriminates well for the prototypes and **not at all** for the
generic concept documents — `SBA concept` scores psych 48 / writing 48, which is
a tie, not a match. Shared SBA vocabulary is most of the signal. So: filename and
provenance carry information the text does not, and an intake program should not
pretend otherwise.

##### THREE KINDS OF MATERIAL, and only one is text

1. **Prototype decks** — 255 to 1,731 text runs. Authorable: the items, prompts
   and structure are in the text.
2. **Plan documents** — `DCA SBA 1.docx` has a table of contents (Overview,
   Scenario Outline, Graphic Organizer, Questions, Key Terms), **20 headings, 42
   questions and 45 fill-in blanks**. The structure of a form, written as prose.
3. **Screenshot decks** — `Survey 1`, `Survey 2`, `Writing Process Journal 1`:
   **28 images and TWO text runs across 29 slides.** The activity is in the
   pixels.

**The third kind settles an open design question.** §10.6.1 says the intake
program "will almost certainly have to use LLMs extensively, often using tools" —
this is why. A third of the sample carries its content as images, and no parser,
however good, will read it. Vision is not an enhancement here; without it the
program cannot see the material at all.

##### Versions, not duplicates

`3 Psych SBA FBA2 prototype Share 10-7-25 (1).pptx` and
`Psych SBA FBA2 prototype Share 10-7-25.pptx` differ by 121 KB of embedded media
and are **textually identical** — a download duplicate. `SBA Final Feedback(1)`
and `SBA Final Feedback` are **98.6% similar and not identical** — a genuine
revision. And `SBA FBA prototype DRAFT 11.26.24` is an earlier dated version of
the `Share 10-7-25` deck.

So the input carries **three different same-ish relationships** — a byte-level
duplicate, a near-identical revision, and a dated earlier draft — and they need
different answers. Deciding which version is current is part of intake, not a
preliminary to it, and nothing in the filenames reliably says.

##### What this sample does NOT contain

No gold scores, no grading sheets, no completed student work. `molly_data` holds
the fuller materials (see `$COURSE_DATA`), and this set is explicitly partial. So
it exercises **items, prompts and structure** and says nothing yet about how the
intake program is to recover **gold and rubrics** — which §10.6.1 lists as part
of its job and which remains unexamined.

##### 10.6.5 · GOLD AND SCORING MATERIALS — the other half of intake

*On the user's pointer to `molly_data`. §10.6.4's sample carried no gold; this is
where it lives. **Structure only below** — the workbooks sit beside student
submissions whose participant ids are the key that identifies them, and nothing
derived from them belongs in this public repository.*

**The shape is uniform and simple.** Three handouts, each a directory of **20
`.docx` submissions and ONE `.xlsx`** named `Handout N - Scoring & Feedback`. One
sheet, one row per participant, and per item a **pair** of columns:

```
Participant ID | <item> Score | <item> Feedback | <item> Score | <item> Feedback | ...
```

20 data rows per sheet, 26 items across the three, 52 score/feedback columns.

##### The column heading IS the rubric's `label`, and that is the join

Three handouts use three different naming conventions — h1 `Question 4a`, h3
`1a`, and h2 in **prose**: `First Type Definition`, `Second Weekly Example`. Not
one of them is the item id (`Q4a`, `1a`, `D1`, `WK2`).

**Measured: 52 of 52.** For every one of the 26 items, `label + " Score"` and
`label + " Feedback"` are columns in that handout's sheet. The rubric's `label`
field is not decoration — **it is the join key to the teacher's spreadsheet**,
and it is the reason a grader's column can be found at all.

That answers a question §10.6.1 left open. Recovering gold from teacher materials
is not free-text inference: the correspondence is carried by a field the rubric
already has. **An intake program producing a rubric must emit a `label` that
matches the teacher's column heading, or the gold it recovers joins to nothing.**

##### A duplicate declaration, now gated

`gold.HN_HEADER_TO_ITEM` states the same correspondence a SECOND time, as three
hardcoded header→id tables. They agree with the labels today, in both directions,
and nothing made them agree.

A label edited for wording would leave the gold join reading the old heading —
and the scores would still load, against the item that heading used to describe.
`check_gold_columns_are_the_item_labels` now holds the copy to the original.
**Under A2a the header map is derivable and should not be a stored table at
all**, which makes it a concrete Stage 4 deletion candidate the plan did not
previously name.

The check reads **headers only** and no data row.

##### What is still unexamined

The `.docx` submissions themselves — how a student's answer is located inside a
handout document — and `molly_data`'s wider contents (`migration_reference`,
`handsplit`, `out`, and roughly 8,900 JSON artifacts). This pass covers where
gold lives and how it binds to items, not how a response is found in a document.

##### 10.6.6 · LOCATING A STUDENT ANSWER, AND FINDING THE KEY

*Two questions that look alike and are not. **Structure only** — no submission
text appears below.*

###### Inside a submission: subtract the template, then match a marker per item

`segment.py` already solves this, and its method is general. **Every submission
is the blank handout with answers typed into it**, so the reliable way to isolate
student text is to SUBTRACT THE TEMPLATE. Its docstring names the failure that
forces this: Handout 1's template carries a worked "fruit-flavored water"
example and Handout 3's carries an example data table AND an example graph — *"a
scorer that reads those as student work scores them."*

Subtraction alone gives undifferentiated text, so each item is then located by a
**regex marker matching the handout's own printed prose**: 10 markers for h1, 14
for h2, 10 for h3. They are of two kinds, and the difference matters:

* **prose markers** — h1's `Define your unwanted target behavior and explain WHY`,
  h2's `Example of Positive Reinforcement`. The question text IS the locator.
* **positional markers** — h3's `^\W*1\W?a\b`: a numbered slot, no prose at all.

Per-handout flags follow from the layout: h2 needs `capture_tail` because its
answers are written **inline after the label**, and h1 must not use it because its
marker lines carry only question prose.

**What this costs an intake program.** The locator is the printed question, so
*rewording the handout breaks the segmenter* — the module says so about its own
section headings: "Reword either and the segmenter stops finding the section it
names." A generated course avoids this entirely, because each response has an
input with an id; the marker machinery exists only to read documents authored
before any of that. It is **intake of legacy submissions**, not part of the
engine, and should not be generalised — it should be made unnecessary.

###### In the teacher materials: keys sit WITH the item, in no convention

*On the user's note that answers appear "as keys with the items in various ways,
not as gold sets".* Measured across the 17 materials: **no `(x)` markers, no
`ANSWER:`/`KEY:` labels, nothing the engine's formats would recognise.** What is
there instead:

* **A parenthetical in prose.** The sleep-scenario deck writes the key directly
  after the scenario: `… when he goes to bed when asked (correct answer is
  positive reinforcement)`. Three such, one per scenario. The key is a sentence,
  not a marker.
* **Nothing at all**, for most items — they rely on the separate gold workbook
  (§10.6.5).

###### The bracket trap

The FBA2 prototype uses `[...]` for **authoring notes**: `[insert new updated
plan here]`, `[say something here about …]`, `[Carry over highlighted
strategies…]`.

In `.textSelectionpeg` the identical syntax means **the answer**:
`[A child receives a sticker for completing homework on time]`.

**The same bracket convention means opposite things in the two places an intake
program will read.** A program keying on brackets would import a teacher's
reminders-to-self as the answer key. This is the sharpest instance so far of
§10.6.1's warning that the second-order decision is indeterminate: the syntax
carries no signal, and only the surrounding document says which reading applies.

##### 10.6.7 · WHAT `$COURSE_DATA` ACTUALLY IS — four stores in one root

*Surveying the rest of `molly_data`. This bears directly on **H1c**, which puts
gold under `$COURSE_DATA` and renames the variable: the name says "course data",
and 97% of the directory by size is something else.*

**1.6 GB, and gold is 11 MB of it.**

| store | size | what it is |
|---|---|---|
| `out/` | **1.6 G** | the run artifact store: **553 run directories, 1,010 `*.runs.json`, 8,821 JSON**, spanning 2026-07-30 to 09-15, plus 156 `idmap_*.json` and 107 logs at its top level |
| `migration_reference/` | 18 M | dry-run material preserved when the sandbox was deleted — an engine half that "existed nowhere else" |
| `Handout Submissions…/` | 11 M | **the actual course data**: 60 submissions and 3 gold workbooks |
| `pre_scrub_backup_…/` | 7.3 M | a pre-scrub source backup |
| `retired_artifacts/` | 2.8 M | artifacts deliberately moved OUT of the scanned tree |
| `migration_goldens/` | 2.1 M | golden outputs for the migration verifiers |

**The consequence for H1c.** `$COURSE_DATA` for a NEW course means the 11 MB —
submissions and gold. The other 1.59 GB is this project's measurement history and
migration archaeology, which no second course would have or want. The rename is
right, but the directory it renames is **not a course-data directory today**, and
the plan should say which part a new course is expected to provide.

##### The data root holds copies of the SOURCE — a third instance of one mistake

`$COURSE_DATA` carries **63 `.py` files and six `.olx`**. `migration_reference/`
preserves a whole engine half plus three rubric `.olx`; `pre_scrub_backup_…/`
holds three course `.olx` and a **partial, stale copy of `scoring/` — 20 files
identical to the live tree and five differing**.

Nothing reads them today: every walk into the data store is scoped to `out/` with
an explicit `*.runs.json` or `*.json` pattern, and `DECLARED_ROOTS` does not name
it. But this is the third appearance of one mistake — `.stage/content` counted as
a second course, three parallel checkouts counted as three more — so it is now
**prevented rather than diagnosed**: `olx_corpus.roots_inside_the_data_store()`
refuses any declared corpus root inside `$COURSE_DATA`, and both corpus gates
carry it. Verified firing: pointed at a parent of three roots, it returns three
refusals.

##### Two stores are properly governed, and say so

`retired_artifacts/README.md` is a model of the thing: superseded sweep artifacts
moved out of the scanned tree, **kept not deleted** because "a fault superseded by
a later sweep stays true of what was recorded"; it records that live-ledger
sources were checked for and three were left in place; and it states the reversal
— *"Move a file back into out/ to put it under the audit again."*
`migration_reference/README.md` likewise says why each part cannot live in the
public repo.

##### And two accumulations that nobody governs

**Ten `corpus_refs.json` variants** (`.bak`, `.pre_merge`, `.pre_seamsplit`,
`.pre_residue`, `.pre_union`, `.pre_unwrap`, `.pre_unanchored`, `.pre_worktree`,
`.with_first`) and **156 `idmap_*.json`**. Both are inert — nothing selects among
them, the canonical `corpus_refs.json` is named exactly and an idmap is passed
explicitly by `--idmap` — so this is dead weight, not a hazard. Worth noting only
because the difference between the governed stores above and these is a README.

##### The intake program: an LLM reading materials onto ROLES, then components

*Recorded on the user's architecture note.*

The program that reads teacher materials will **use LLMs extensively** — Claude
first, but the design stays model-general — and will need **tools**, because
interpreting handouts, keys and grading spreadsheets is not a parse.

**Its first decision is a correspondence between parts of the teacher material
and the ROLES** in the shape inventory: this chunk is an item stem, this column
is gold, this table is an answer key, this sequence is the structure of a form.
Roles are a small, stable vocabulary — `grader`, `gradable_input`, `item_part`,
`structure`, `action`, `display` — and that is what makes them a tractable first
pass.

**Choosing the specific component that fills a role is a SECOND-ORDER task, and
will often be indeterminate.** Nothing in a worksheet says whether three parts
are one `Carousel` or three pages, whether a list is a `Sortable` or a
`Matching`, or whether an open line wants `StringGrader` or judgement. The
pairing table above constrains the second pass — it says which components can
fill a role and which grader each response source is FOR — but it cannot remove
the indeterminacy, and the design should expect that decision to be provisional,
revisable, and worth surfacing to the teacher rather than guessed silently.

##### SCORING WITHOUT THIS ENGINE IS FINE — the intake program is what must be general

*Recorded on the user's correction, and it decides the scope of everything above.*

The python scorer handling only `SlotSheetGrader` is **not a gap to close**. An
item graded natively by `CheckboxGrader`, `MatchingGrader`, `NumericalGrader` or
a `RulesGrader` rule is scored by lo-blocks itself and never needs this engine at
all. The engine's narrow scope is a legitimate, permanent boundary, not a
shortfall — and widening it is NOT implied by any of the above.

What must be general is the **intake program** (item 2). Its output space is the
whole of the sixteen graders, the fourteen inputs and the two problem families:
reading teacher-editable documents and spreadsheets, it has to decide which
scoring mechanism each item becomes — a `CheckboxGrader` here, a `MatchingGrader`
there, a `SlotSheetGrader` with an `LLMAction` only where the response is
genuinely constructed — and emit it. **Most of what it emits will never touch the
python scorer.**

So the shape inventory (item 1) is **a specification of the intake program's
target space, not a to-do list for the scoring engine**. That is the sense in
which "sized by shape coverage" has to be read, and it is why the inventory is
worth taking early: it bounds a program that has not been written, rather than
auditing one that has.


**Why this belongs to the refactor and not beside it.** I1a's recorded weakness is
that the fixture is "written by the same hand that abstracts the engine, at the
same time, so it will encode some of the assumptions it exists to test". An
inferred fixture weakens that in a way an invented one cannot: the inference
program is written against the **component space**, which nobody in this project
chose, rather than against psychology's shapes. It does not reach I1b's standard —
only a real course whose shapes were not chosen by us can falsify the abstraction
— but it is the difference between a fixture that encodes our assumptions and one
that encodes lo-blocks'.

**Consequences for the sequence.** The shape inventory (1) is a measurement and
can be taken early — it needs lo-blocks, not the migration, and it is a
prerequisite for claiming any coverage number at all. The inference program (2) is
substantial and is properly its own piece of work, not a step inside Stage 11. I2c
still holds — the fixture is built LAST as acceptance — but what is being built
last is now understood to include an intake program, and the plan should not let
"invent a fixture course" stand in for it.

#### I2 — when

* **I2c · CHOSEN for stage one — the fixture is built LAST, as acceptance**, with
  I1a as the baseline the stage is measured against.
* **A second acceptance round with I1b** follows when a real alternative course
  becomes available. The first round establishes that the engine is course-shaped
  no longer; the second establishes that it is course-INDEPENDENT. They are
  different claims and the plan should not let the first stand for the second.
* I2a (first) and I2b (at the first module boundary) are not taken: designing the
  fixture before any migration means guessing where the seams are, and the fixture
  would then encode today's shape as the target.

#### What now depends on the fixture, and therefore lands after stage one

I2c puts the fixture at the END of stage one, so everything sequenced after it
moves with it. Recorded here because these dependencies were agreed separately and
would otherwise look independent:

* **G2c** (`OVERRIDES.md` to structured data) — explicitly "not started until the
  fixture course exists", because it modifies the pre-commit gate.
* **E1a's renamed modules** — renamed is not generalised until one runs against a
  second handout; until then the plan counts them as renamed.
* **D2a** (generic self-test fixtures) — already sequenced behind the self-test's
  own defects, and the fixture course is what it would finally run against.

**The risk I2c carries, stated plainly:** the expensive discovery — that something
migrated early was never general — arrives at the end. That is the price of not
guessing the seams in advance, and it is mitigated only by C2a's per-module proof
and C3c's gate catching the cheap failures as they happen.

### 10.7 · The per-module proof, widened

**DECIDED:** C2a's "clean" is redefined. A module is clean when **all** hold:

1. no course table (§2.1's measure, C3a's grep),
2. **no literal course id in code** (the 53),
3. **no unmarked course vocabulary in docstrings** (the 188),
4. **no course artifact in its own name** (the 9),

and C3c's enforcement check gates all four, not just the first. A definition of
"clean" that stops at tables would let every module pass while the engine stayed
a psychology program.

---

## 11 · The order of work

*Added 2026-09-18. §5 listed stages and §§9-10 took fourteen decisions, but nothing
said which happens when, and several decisions created dependencies on each other
that are invisible from where they are written. This is the single ordering; where
it disagrees with a stage description, this section is current.*

### 11.0 · Before anything

| # | gate | status |
|---|---|---|
| E1 | re-sweep finished | **MET** — 26 items `ok` |
| E2 | live self-test clean, no residue | **run in flight**; the last full run left the tree clean but reported 1 failed case and 1 skipped, both since repaired |
| E3 | lo-blocks engine increment committed | **MET** — `59d64720`, `92d6ab30` |
| E4 | self-test refuses a concurrent run | **MET** — guard added and verified |

**E2 is the only open gate**, and it now means something narrower than "the
self-test passes": the two defective cases (a vacuous neutrality fixture, a
skipped inverted case) must be repaired and the suite re-run clean.

### 11.1 · Stage 0 — repair the instrument (IN PROGRESS)

1. ~~concurrency guard~~ **done**
2. ~~neutrality case builds its own pair~~ **done, verified firing**
3. **count-scaffold case builds its own precondition** — writes a synthetic
   `*.runs.json` with an impossible triple, confirms the finding fires, blinds the
   check, confirms it stops. Must carry `web_score_sha` or the check's own
   attributability filter skips it and the case is vacuous for a new reason.
4. **T0.1, the vacancy report** — BUILT 2026-09-18. §12 assigned it to Stage 0
   and this list omitted it, so the sequence disagreed with the tooling section
   about what Stage 0 contains.
5. **full self-test re-run, clean** — closes E2.

*Nothing else starts until Stage 0 closes. Every later stage is verified by this
instrument; repairing it afterwards would invalidate whatever it had already
certified.*

### 11.2 · Stage 1 — widen the inventory, freeze a baseline

Re-measure §2.1 against the tree that now includes the committed engine increment
(§1 condition 3 requires it). The scan must count all four embeddings from §10.7,
not tables alone: **tables, literal ids, unmarked course vocabulary, course-named
modules.** §10.3.0's correction is part of this — the vocabulary regex counted
`handout` (127) and software-sense `behaviour` (35) and made the problem look five
times larger than it is.

### 11.2a · STAGES 2 AND 3 CYCLE — they are not sequential

*Added 2026-09-18, on the user's observation, after T2.1 was built.*

The order in §11 reads as Stage 2 then Stage 3. **It is a loop**, and pretending
otherwise would have the schema settled before anything proved where the data can
live.

T2.1 drops a value only when it can recompute it. A2a says the READER recomputes.
So each derivation written in the reader lets the export drop one more value, which
changes the file, which changes what the schema has to describe — and `SLOT_SPEC`
alone is 78 source lines in h1 and 149 in h2, so this is a dozen iterations, not a
formality.

The cycle, with its proof at every turn:

1. the reader gains a derivation;
2. `DERIVATIONS` (which lives in the reader from Stage 3) gains an entry;
3. the export drops that value on its next run;
4. **T5.1 proves the JSON still reproduces the modules** — so a wrong derivation
   is caught the moment it is written, not when something downstream misreads it;
5. repeat until every value is either authored or rebuilt.

**A2a's progress is therefore countable** — and it was counted on 2026-09-18: of
the twelve names §9.0 called derived, TWO are derivable, sixteen candidates are
authored literals, and one derives from another literal. **The cycle is short, not
a dozen turns**, because there are no outstanding values provably derivable from
items. The schema is finished when that number stops moving, not before —
and a schema declared final while the reader is still learning to rebuild things
would have to be reopened, which is the state §5.2's gate ("no field is `TBD`")
exists to prevent.

### 11.3 · Stage 2 — schema, against the hardest tables first

Fit the schema to `GOLD_DIVERGENCES`, `CORRECTED_GOLD`, `PROSE_ONLY_SLOTS`,
`DESIGNED_TEXT`. Decisions already binding on it: **A2a** (authored data only,
derived recomputed), **A3a** (one file per course), **B2a** (generator fields on the
item entry), **§9.2a** (every field declares RUBRIC or GENERATOR, unclassified
fails), **C1b** (gold is a SECOND file), **H1c** (`courses/<id>/`).

### 11.4 · Stage 3 — the reader

`coursedata.py` (**B1a**), with per-group accessors and **no accessor returning a
raw entry** (§9.2a). Dual-source verification: the reader and the existing modules
must agree on the live course before anything is deleted.

### 11.5 · Stage 4 — move the tables, module by module (**C2a**)

`olx_prompts.py` first — 12 tables, 190 ids. A module is done when §10.7's four
counts reach zero, gated by **C3c** (grep as metric, enforcement check as gate),
including D1x-c's rule that **a declared property appearing in an engine branch is
a violation**.

Goal D's real scope is `1c` (13 references, six modules) — properties become
fields, behaviour becomes named strategies. The other three groups are handled
elsewhere: `rubric_h2`'s 5 dissolve under **A1c**, `Q6`'s 4 move under **E1**, and
the 28 self-test fixtures are exempt under **D2d** until Stage 8.

#### STAGE 4 BEGUN 2026-09-19 — `olx_prompts.py`: 11 tables → 0, prompts byte-identical

The first module through C2a, and the test that settles it is not a count: **the
23 generated web prompts hash the same before and after** — `e814c89b50e6fe88`.
A migration that changes what ships is not a migration.

| | before | after |
|---|---|---|
| `olx_prompts.py` tables | 11 | **0** |
| items carrying generator fields | 0 | **26 of 26** |
| course-level generator values | — | 3 |

**How the data moved.** Nine item-keyed tables became generator fields on the
item entry (B2a), each prefixed `prompt_` — `CONTEXT` would otherwise land as
`context`, which the rubric already uses for something else, and §9.2a forbids a
field naming two groups. Two tables are lists about the course, not about any
item, and are carried at course level: putting a course-wide list on 26 items
would be 26 copies of one fact.

**The names stay, the data leaves.** Eight modules reference `ACTION`,
`RESPONSE`, `ITEM_NOTES` and the rest. They are now built by reading the course
file, so every consumer keeps working and the move can be judged by output alone.

**`generator_source.py` — a builder outside the pipeline.** The export must read
the authored tables from somewhere, and reading them from `olx_prompts` would
make regenerating the course file depend on the file being regenerated. Stage 5
already anticipated this: *"Builders survive OUTSIDE the pipeline as the tool
that generates the expanded canonical JSON."* Nothing in the scoring path imports
it. The tables are carried VERBATIM, comments included, because a comment saying
why an item is in a table is part of the authored record.

##### Three guards caught three real things, none of them anticipated

1. **editguard refused the write** and listed 76 vanishing table entries —
   among them `CONTEXT['_utb']` and `CONTEXT['_wgb']`, the only two keys that are
   **not item ids**. They are handout 2's section headings, and folding the table
   onto item entries would have dropped both silently. They are now carried as a
   declared residue, and an UNDECLARED non-item key is a REFUSAL, so the next
   table to arrive with one must be decided rather than truncated.
2. **`check_course_schema_is_complete` caught me on its first real use.** The new
   `_generator_value` read `coursedata._load()["generator"]` — the raw-entry
   escape its own Part B was written to find, committed by the first module to
   try it. Fixed with a `generator_value()` accessor: a caller holding the whole
   document can read anything in it, so the group boundary stops meaning anything
   while the code still looks like it goes through the reader.
3. **The ratchet refused a tightening** — `enforcement.py: 30 → 31` — and was
   right to, which exposed a defect in T1.1.

##### T1.1 counted integers as item ids: 106 literal ids → 57

`str(c.value) in ids` rendered the **integer** `3` as `"3"` and matched handout
3's item `3`. So **every `handout == 3` and every `{1: …, 2: …, 3: …}` counted as
a course id embedded in engine code.** `enforcement.py` carried six of them;
`olx_prompts` three.

Item ids are strings and are compared and subscripted as strings; a bare integer
is a handout number, an index or a count. Matching `isinstance(value, str)` takes
the repo-wide count from **106 to 57**, and `enforcement.py` from 7 to 1.

This is the third measurement in this plan to shrink sharply under scrutiny (53
branches → ~13, 188 docstring words → ~30), and the second defect of exactly this
shape today: **the property ratchet matched a name where a property was meant,
and this matched a rendering where a value was meant.** Both were found by
reading the hits rather than trusting the number.

#### `segment.py`: 6 tables → 0, segmentation of all 60 submissions unchanged

The second module through C2a, verified the same way: **all 60 submissions
segment to the same hashes** — `5732df7063d35f9d` before and after.

Two different migrations in one module, and the difference is A2a:

* **`H1/H2/H3_MARKERS` are course CONTENT** — an ordered list of `(key, regex)`
  matching the handout's own printed prose. They moved to the course file whole.
  **Not folded onto item entries**, for two reasons: the order is load-bearing
  (the segmenter walks them in sequence), and the lists carry keys that are not
  items — `preamble` and `_q4_intro` in handout 1, `_utb` and `_wgb` in handout
  2. An item entry cannot hold a position in a sequence it shares with non-items.
* **`H1/H2/H3_ITEMS` are DERIVED and are now stored nowhere.** `H1_ITEMS` was the
  literal `["Q1", "Q2", …]`; it is exactly handout 1's item ids in rubric order.
  Verified equal for all three handouts, then deleted. That is A2a doing what it
  is for.

#### The ratchet refused the migration it exists to enable

`generator_source.py: 11 -> 14` — because three marker tables arrived there FROM
`segment.py`, which is the work succeeding. A count that rises in the DESTINATION
is not a regression.

So `DATA_MODULES` is declared: `rubric_h{1,2,3}.py` and `generator_source.py` are
authored course data by design, and the ratchet exists to stop course content
accumulating in ENGINE code. **Their contents are still counted and recorded** —
the budget carries `data_modules: {generator_source.py: 14, rubric_h2.py: 21, …}`
and a change there is reported — because the point is to see how much course data
exists and where it sits, not to pretend a data module holds none.

The writer had to learn the same rule: `--tighten` kept refusing after the gate
stopped complaining, because its own growth check still counted data modules. **A
gate and its writer that disagree make a budget that can never be written again.**

#### `agreement.py`: 6 tables → 3, and the rest of Stage 4 is BLOCKED ON GOLD

The three per-handout reference maps moved — `_H1_CTX`, `_H2_CTX`, `_H3_CTX`,
component id → the context handed to the grader. Carried course-level, **keyed by
component and not by item**: one component is context for several items and one
item draws on several components, so there is no item entry for such a map to
live on. `BLOCKS` reassembles identically from the course file.

##### What remains in Stage 4 is almost entirely GOLD, and gold cannot move tonight

Ranked by what each module still carries, the remainder is dominated by gold
declarations: `CORRECTED_GOLD`, `GOLD_DIVERGENCES`, `GOLD_CEILINGS`,
`PER_ITEM_EXCLUDE` (handouts.py); `GOLD_SLOT_CHARGES`, `GOLD_CODE_KNOWN`,
`GOLD_SLOT_BOUNDS_KNOWN`, `GOLD_SLOT_UNMAPPABLE`,
`GOLD_SLOT_DISAGREEMENTS_KNOWN`, `SILENT_GOLD_DIVERGENCES`,
`DECLARED_CEILING_CELLS` (measured.py); `GRAPH_UNREACHABLE_1C`,
`UNSCORED_GOLD_CRITERIA` (agreement.py).

**C1b puts gold in a SECOND file under `$COURSE_DATA`, outside this repository**,
and that is exactly right for these: several are keyed by PARTICIPANT —
`CORRECTED_GOLD[("NR", 4)]`, `GRAPH_UNREACHABLE_1C = (4, 19, 20)` — which is the
kind of key the repository's own rule says makes a participant id meaningful.
They should not move into `course.json`; they belong in the gold file.

So this work is **put to one side, for a stated reason**: writing that file means
writing under `$COURSE_DATA`, and the 2026-09-18 write-scope restriction makes
everything outside the dry run read-only. The migration is designed and the
destination is decided; only the write is deferred.

**Two consequences worth holding on to.** First, C1b's second file is not a
convenience — it is the only correct home for a table keyed by participant, and
these tables currently sit in a PUBLIC repository. Second, Stage 4 cannot reach
"all four counts zero" for `handouts.py`, `measured.py` or `agreement.py` until
the gold file exists, so **Stage 5's deletion of the rubric modules is gated on
C1b**, which the sequence in §11 does not currently say.

#### The audit's verdict on tonight's work, and three findings it returned

A full `enforcement_audit()` over the dry run after Stages 4, 7 and 9: **10
findings, 1 parked, 9 live** — and seven of the nine were mine.

1. **`DATA_MODULES` and `OLD_ENV_NAMES_ALLOWED` were declaration-shaped tables
   with no verifier named.** The same check caught `MIGRATED_MODULES` and
   `D2D_EXEMPTION` the day they were added. Registered.
2. **`olx_corpus.DECLARED_ROOTS` spelled four absolute paths.**
   `check_filesystem_locations_come_from_paths_py` was right, and its own
   docstring says why: *a literal path does not fail on the wrong tree, it
   SUCCEEDS on it.* The answer was in the check's name — `paths.py` is where
   locations are resolved — so the corpus roots moved there as
   `paths.CORPUS_ROOTS`, resolved, with `$CODE_HOME` and `$COURSE_ROOTS`
   overriding. The *declaration* of which trees count stays in `olx_corpus`,
   where the reasoning lives; only the resolving moved.
3. **`check_no_old_environment_names` fired on this plan** — which documents the
   rename and therefore has to name what was renamed. **The same shape as the
   anchor gate failing on the plan's own `see: qc:NAME` example**: a convention's
   specification uses the convention. Both plan files are declared, with that
   reason.

The two remaining live findings are stale build artifacts in lo-blocks
(`.stage/content` 40h older than its source), which predate tonight.

#### The 13 enforcement declaration tables: analysed, and NOT moved — for want of a test

`enforcement.py` holds **17 tables, 16 of them non-gold**, and §11.3 names two of
them — `PROSE_ONLY_SLOTS`, `DESIGNED_TEXT` — among the hardest tables the schema
must fit. They are course-specific scoring declarations and they belong in the
course file. 682 lines across 13 tables were located and ready to move.

**They were not moved, and the reason is the method rather than the hour.**

Each of tonight's three completed migrations rested on a decisive equivalence
test: `olx_prompts` on the 23 generated prompts hashing identically, `segment.py`
on all 60 submissions segmenting identically, `agreement.py` on `BLOCKS`
reassembling identically. **There is no such test for these thirteen.** They feed
enforcement checks, and the audit currently returns **4 findings** — so a table
silently emptied would produce the same 4 findings whenever the checks it feeds
are already passing. That is T0.1's vacancy problem one level up: *4 findings
cannot distinguish 13 faithful moves from 13 losses.*

What the move needs first is a test that would fail if it went wrong — for
instance, asserting each check's finding count against a deliberately emptied
table, per table, before the move rather than after.

**One further consequence found while preparing it.** `DESIGNED_TEXT` has a
documented human procedure: `measured.py --accept-design-change ITEM SLOT FIELD`,
which writes `DESIGNED_TEXT_SHA.json` while the table itself is hand-edited under
the "register only with the build" rule. Moving the table relocates that
authoring step into the builder, which is the Stage 5 model and correct — but it
changes a procedure a person follows, and that is not a thing to change
unreviewed overnight.

#### `table_sensitivity.py` — the test a move needs BEFORE it happens

Built 2026-09-19 to answer the question that stopped the enforcement migration:
**would we notice if it went wrong?** For each table it empties the table,
re-runs only the checks that consume it, and reports whether any of them moved.

`8 of 13 tables are SENSITIVE.`

| sensitive — safe to migrate, the loss would be reported | |
|---|---|
| `PROSE_ONLY_SLOTS` (27), `PROSE_ONLY_JUDGED_AGAINST` (27), `MULTI_BLOCK_DECLARED` (11), `DESIGNED_TEXT` (6), `DECOMPOSITION_DIVERGENCES` (12), `CONSENSUS_OVERLAP_BACKLOG` (2), `UNCHARGED_VERDICTS` (1), `APP_ONLY_SLOTS` (1) | |

| NOT sensitive — nothing would report the loss | |
|---|---|
| `SLOT_STRUCTURE_FAMILIES`, `HAND_AUTHORED_ATTRS`, `COUNTABLE_EXEMPT`, `PROBE_UNREACHABLE_PAIRS`, `PROBE_PROVOCATIONS` | |

**A "not sensitive" result is not one thing**, and the tool refuses to guess
between the two: the table may be genuinely inert — every entry describing a
condition that no longer arises, which makes it a candidate for DELETION rather
than migration — or it is load-bearing and the check that reads it is passing for
unrelated reasons, which makes the CHECK the weak instrument. Either way it may
not be migrated on the strength of a check that would not notice its loss.

##### The scan reported a false discovery first

Looking only inside each `check_*` body, it found `SLOT_STRUCTURE_FAMILIES` and
`PROBE_PROVOCATIONS` read by **no check at all** — which reads as a finding about
two dead tables. Both are read by module-level HELPERS that checks call, and both
are registered with the table watcher. Following one hop through helpers corrects
it, and the remaining bound is stated rather than hidden: a table reached through
two helpers would still be reported as unconsumed.

`check_engines_send_the_same_request` is excluded — it caches a 672 KB capture
under `$COURSE_DATA/out`, and nothing here is worth a write outside the tree
being worked on.

#### `enforcement.py`: 17 tables → 10, once there was a test to move them by

`12 of 12 consuming checks IDENTICAL after the migration`, and
`table_sensitivity.py` re-run afterwards shows the moved tables are **still
sensitive** — so the test that licensed the move is still live against the
course-file-backed version.

Seven moved. **Six did not, for two different reasons, and the difference is the
point:**

* **`CONSENSUS_OVERLAP_BACKLOG` is keyed by PARTICIPANT** — `('2a', 18, 'how1',
  'verdict')`, participants 18 and 20. C1b puts anything keyed by a participant
  in the gold file, outside this public repository. Found by checking every key
  for integer parts before exporting, not after.
* **Five are NOT SENSITIVE** — `SLOT_STRUCTURE_FAMILIES`, `HAND_AUTHORED_ATTRS`,
  `COUNTABLE_EXEMPT`, `PROBE_UNREACHABLE_PAIRS`, `PROBE_PROVOCATIONS`. Emptying
  them moves no check, so nothing would report the loss. They stay until
  something would.

##### Tuple keys, and why not a separator

Six of the seven are keyed by tuples — `("Q4a", "antecedent_kind_1",
"rule_addition")` — and JSON has string keys only. **Joining the parts with a
separator would be lossless only until a part contained the separator**, and
would then stop round-tripping silently. The file holds `[[key, value], …]`, so
a key stored as a LIST comes back as the tuple it was. The round trip is asserted
on all seven, not assumed.

##### The same dependency mistake, a second time

Extracting the tables left `_PRIMS_2026_08_29` behind and
`DECOMPOSITION_DIVERGENCES` is built from it — a `NameError` on first import.
**That is exactly what happened moving `MATCH_DEF` out of `olx_prompts`**, where
`EQUIVALENCE_DEF` was left behind. A table is not self-contained just because it
is a table, and the loud failure is the good case: the quiet one is a table that
imports and is subtly wrong.

#### The five insensitive tables, resolved into three different things

Chasing them found a defect in the harness, a stale-looking declaration, and a
category the harness cannot test at all.

##### 1. The harness was reporting on itself — `COUNTABLE_EXEMPT`

`check_countable_families_converted(items)` **takes an argument**, so calling it
bare raised `TypeError` before AND after emptying the table. Identical results,
scored as "not sensitive". That was the harness, not the table.

Uncallable checks are now named and excluded from the verdict — the same
distinction the self-test draws between a SKIP and a vacuous case, and the same
mistake in a new place. One of the five was this.

##### 2. An exemption nothing exempts — `HAND_AUTHORED_ATTRS`

`check_generated_attributes_have_a_declaration` reports an attribute present in
the `.olx` with **no rubric rule and no exemption**. Emptying the exemption
therefore ought to make its four entries fail. It changes nothing — and all four
now carry a rubric `expect`:

| entry | rubric rule present |
|---|---|
| `PR.expect`, `NR.expect`, `PP.expect`, `NP.expect` | **yes, all four** |

They have rules because `rubric_h2._EXPECT_SHIPPED` sets `_it["expect"]` at
import time — the import-time scaffolding found earlier today while censusing
module-level names. So the four are not orphans, with or without the exemption.

**Whether that makes the exemption stale is a scoring judgement, not a mechanical
one**, and it is left open: it turns on whether scaffolding that assigns `expect`
counts as *the rubric declaring a rule*. If it does, the table has outlived its
reason and should go the way the PEG orphan declarations went. If it does not,
the CHECK is looking in the wrong place. **Either answer is a finding; guessing
between them is not.**

##### 3. A table that IS its check's input domain — `SLOT_STRUCTURE_FAMILIES`

One entry, `h2-cadence-and-type`, consumed by
`check_sibling_slots_share_their_structure`. Emptying it removes the check's
SUBJECT rather than causing a failure: no families declared, nothing to compare,
zero findings either way.

**Such a table cannot be tested by emptying at all.** The test it needs is
CORRUPTION — change a member so the family stops being consistent — which is a
different harness and is not built. `PROBE_UNREACHABLE_PAIRS` and
`PROBE_PROVOCATIONS` look like the same shape and are unexamined.

That is the real limit of `table_sensitivity.py`, and it is now stated: **it can
prove a table load-bearing, and it cannot distinguish "inert" from "declares the
work itself".**

#### Corruption testing: 11 of 13 declaration tables could hold WRONG VALUES unnoticed

`table_sensitivity.py` now asks two questions instead of one, because they are
different questions and a table can answer one and not the other:

* **emptying** asks whether the table's PRESENCE is checked;
* **corrupting one value** asks whether its CONTENT is checked.

| | presence checked | content checked |
|---|---|---|
| `PROSE_ONLY_JUDGED_AGAINST`, `DESIGNED_TEXT` | yes | **yes** |
| `PROSE_ONLY_SLOTS`, `MULTI_BLOCK_DECLARED`, `DECOMPOSITION_DIVERGENCES`, `CONSENSUS_OVERLAP_BACKLOG`, `UNCHARGED_VERDICTS`, `APP_ONLY_SLOTS` | yes | no |
| `SLOT_STRUCTURE_FAMILIES`, `HAND_AUTHORED_ATTRS`, `PROBE_UNREACHABLE_PAIRS`, `PROBE_PROVOCATIONS` | **no** | **no** |
| `COUNTABLE_EXEMPT` | its check cannot be called bare | — |

**Only two of thirteen have their contents verified.** For the other eleven a
wrong value passes: the check notices that the table is THERE and not what it
says. That is a fact about the enforcement framework, not about the migration,
and it is worth more than the migration that found it.

##### The prediction I made last hour was wrong

§ above argued `SLOT_STRUCTURE_FAMILIES` "cannot be tested by emptying at all"
and needs corruption — the implication being that corruption would resolve it.
**It does not.** Corrupting it moves nothing either. Four tables are verified by
NEITHER test: their presence is not checked and their contents are not checked.

##### What this does and does not prove

The corruption is crude by design — reverse a string, increment a number, drop a
set member — so a check may legitimately not care about the particular value
mangled. **"Content not checked" is therefore suggestive and not proof**, and the
honest reading is: *no evidence was found that anything validates these contents*,
which is a reason to look, not a verdict.

What it does prove is the positive direction. Where corruption DOES move a check,
that table's contents are verified, and `DESIGNED_TEXT` — the table governing
what prompt text ships — is one of the two.

#### `check_declaration_tables_are_verified` — the finding turned into a gate

162 checks. `VERIFICATION_BUDGET.json` records the four tables nothing
validates — `HAND_AUTHORED_ATTRS`, `PROBE_PROVOCATIONS`,
`PROBE_UNREACHABLE_PAIRS`, `SLOT_STRUCTURE_FAMILIES` — plus the one whose check
cannot be called bare, `COUNTABLE_EXEMPT`.

**It gates the direction, not the state.** The set may shrink and may not grow,
so a NEW declaration table has to be checkable by something before it is added,
and a table that becomes unverifiable is reported. Fixing the existing four is
separate work; stopping a fifth is not.

##### The expensive half is deliberately not in the gate

Measuring sensitivity re-runs every consuming check **twice per table**. Inside
an audit that already runs 160 checks, that would add minutes to every commit.
So `table_sensitivity.py --tighten` measures and records; the check only
compares — the same split T4.1 uses, and for the same reason: **a gate that can
lower its own bar is not a ratchet.**

`--tighten` refuses if a table has BECOME unverified, because *a table nothing
checks is not a baseline to record*.

Both halves of the gate were exercised: a recorded table that no longer exists is
caught, and a missing budget file fails rather than passing — *nothing recording
which tables are verified is not the same as all of them being verified*.

#### What is left in Stage 4, specified precisely

##### The participant-key rule, corrected

"Any integer in the key" flagged `handouts.HANDOUTS` as participant-keyed. Its
keys are **1, 2, 3 — handout numbers**. That is the same crude-heuristic mistake
T1.1 made counting the integer `3` as item `"3"`, in a second place.

The sound rule is structural: **a participant id is an integer in a TUPLE key
whose first element is an item id.** `DECLARED_CEILING_CELLS[("1c", 12)]` is
participant 12; `HANDOUTS[2]` is handout 2. Both cases are now distinguished by
shape rather than by type.

##### `HANDOUTS` is FIVE different things in one table — split 2026-09-19

| part | what it is | destination |
|---|---|---|
| `blurb`, `template`, `submissions`, `outdir`, `capture_tail`, `exemplar_items` | course data | the course file |
| `gold` (a **function**), `rubric` (a **module**) | WIRING — not data at all, and not serialisable | stays in the engine |
| `cited_participants`, `exemplar_participants` | participant references | the gold file, under C1b |

So the table needs a three-way split before any of it moves, and the export would
refuse it today: `_jsonable` raises on a function or a module, which is the right
behaviour — *a field quietly dropped here is a field lost*.

##### The rest, and why each is where it is

* `score.PAPER_ITEM_NOTES`, `PAPER_ITEM_NOTES_WHY` — one entry each, keyed by
  item. Movable, small, and needing only an equivalence test on the paper
  scorer's output.
* `agreement_app.JOBS` (26, item-keyed) and `CONTEXT_SOURCE` (17, component-keyed)
  — movable; `CONTEXT_SOURCE` is the same shape as the `_H*_CTX` maps already
  moved.
* `measured.DECLARED_CEILING_CELLS`, `_1C_GATE_CEILING`, and the seven
  `GOLD_SLOT_*` tables — gold or participant-keyed, so C1b's file, so blocked.

#### Three more tables moved — and the behavioural test did not catch the defect

`score.PAPER_ITEM_NOTES`, `score.PAPER_ITEM_NOTES_WHY`,
`agreement_app.CONTEXT_SOURCE`. All 26 paper prompts hash identically.

##### JSON has no tuple, and the VALUES were tuples too

`CONTEXT_SOURCE` holds `("section", "Q1")` and came back `["section", "Q1"]`.
The KEYS round-trip — `coursedata.declaration` restores those — but the values do
not, and nothing in the file records that they were tuples.

**The behavioural test passed anyway.** 26 paper prompts built identically while
this table's shape had quietly changed, because no paper prompt reads it. The
defect was found by comparing each table against its authored copy — a check
added out of habit, not because the plan asked for it.

**The lesson is about test SCOPE, not about tuples.** One behavioural test was
used for three tables from two modules, and it exercised one of them. A migration
needs a test per table, or a test that demonstrably covers every table it claims
to.

The module that knows the contract restores it: `agreement_app` converts its
values back, because it is the module that unpacks them positionally and it is
where the knowledge that they are pairs lives.

`declaration_source.py` also had to join `DATA_MODULES` — the ratchet refused
`7 -> 10` on the builder that exists to receive exactly that growth, the same
lesson `generator_source.py` taught two stages earlier.

#### `migrated_tables.py` — and it found four more silent shape changes at once

163 checks. `check_migrated_tables_match_their_source` compares **all 27 migrated
tables** against the authored copies they came from, and it found **four** that
nothing had noticed: `olx_prompts.CONTEXT`, `RESPONSE`, `EVIDENCE` and
`PROBE_REACH_LIMITS` had all turned tuples into lists.

**Every behavioural test still passed while those four were wrong** — 23 web
prompts, 26 paper prompts and 60 segmentations all hashed identically, because
rendering a list and rendering a tuple produce the same text. A shape change that
does not alter output is exactly what a behavioural test cannot see.

##### The fix belonged in the encoding, not in each consumer

The first repair converted values back inside `agreement_app`, which works for
one table and asks every future consumer to remember its own shapes. Tuples are
now **TAGGED** on export — `{"__tuple__": [...]}` — and untagged by the reader, so
the round trip is exact **by construction** at any depth: a tuple inside a list
inside a dict comes back a tuple. The per-consumer conversion is gone.

##### The pairs are discovered, not listed

A migrated table is an assignment whose value calls a reader helper
(`_declaration`, `_generator_table`, `_generator_value`, `_markers`,
`_context_refs`), so the 27 pairs come from an AST scan and a table moved
tomorrow is covered tomorrow without editing anything. A hand list would drift
from the migrations it describes — which is the failure this whole section keeps
finding in other tables.

**What it cannot see**, stated rather than left to be discovered: a table read
through a wrapper it does not recognise, and an authored copy edited to match a
bad migration. It compares the two sides; it does not know which is right.

#### The format change broke both equivalence proofs, and both were right to break

Tagging tuples altered the file, and the two tools whose whole job is to police
the file noticed within minutes.

**T3.2** reported four handout-2 tables as `module ['DAY1', …] != reader
{'__tuple__': ['DAY1', …]}`. `_group`, `declaration` and `generator_value` all
untag; **`derived()`'s authored branch did not**, and it was the one path nothing
had exercised since the change.

**T5.1** reported 82 differences — every `prompt_*` field as `ONLY IN FILE`. That
was not the tagging; it was **Stage 4**. T5.1 proves "the file reproduces the
AUTHORED modules", and since Stage 4 the authored modules include the builders.
It now checks the 74 generator fields against `generator_source`, which is the
claim it was always making, correctly scoped.

It names the builder's tables itself rather than importing
`coursedata.GENERATOR_FIELDS` — **a proof that borrowed the reader would not be
independent of it**, which is the rule T5.1 was designed around.

It also had to learn to decode the tagging, and that is NOT the same borrowing:
a tool that reads the file directly has to understand the file's format. It
implements the decoding rather than importing it, for the reason it has its own
canonicaliser — a shared decoding bug would cancel out on both sides.

All four of T5.1's negative controls still fire, including two new ones: a
generator field altered, and a generator field removed.

#### `agreement_app.JOBS` — the last clean non-gold table. 28 tables migrated.

`agreement_app.py`: 2 tables → **0**. 26 job definitions, structure identical,
and the per-table gate now covers **28** tables.

##### A move and a reshape are separate changes

`JOBS` composes its screen ids from `paths.NS`, so every one embeds the course
id — `edu.memphis.psych/bmod_h1_q1` — which the course file **already carries in
its own `course` field**. De-namespacing them is a real Goal-D improvement: a
course id sitting inside a value is exactly what Goal D is about.

It was NOT done here. A move and a reshape performed together cannot be
attributed when one of them breaks, and the move had a test while the reshape
would need its own. It is recorded as owed.

##### Import order is part of the migration

`JOBS` is defined at line 98 and the `_declaration` helper had been added further
down when `CONTEXT_SOURCE` moved. Python runs top-down, so the module raised
`NameError` on import — loudly, immediately, and before any test could report
something subtler. The helper now sits above its first use.

Worth noting because it is the third time tonight that **extraction left
something behind**: `EQUIVALENCE_DEF` from `olx_prompts`, `_PRIMS_2026_08_29`
from `enforcement`, and now a helper that existed but too late. Each failed
loudly, which is the good case.

#### `handouts.HANDOUTS` split — nine fields moved, and four kinds stayed

`handouts.config()` returns identically for all three handouts, and all 60
submissions still segment to the same hashes.

| kind | fields | where it went |
|---|---|---|
| course data | `blurb`, `capture_tail`, `exemplar_items`, `repair_orphans`, `join_aware` | the course file (9 values) |
| resolved path | `template`, `submissions`, `outdir` | **stay computed** — storing a resolved path bakes in one machine |
| shared reference | `markers` | **unchanged** — see below |
| wiring | `gold` (a function), `rubric` (a module) | stays; not data at all |
| participants | `cited_participants`, `exemplar_participants`, `suspect_participants` | the gold file, C1b |

##### The three handouts do not share a schema

Reading h1 and assuming the others matched would have left two course-data flags
behind: **`repair_orphans` is h2 only, `join_aware` is h3 only, `exemplar_items`
is h1 only.** Each handout was read rather than one being taken as the pattern.

##### A "duplicate" that was a shared reference

`markers` looked like a duplicate of the course file's `SEGMENT_MARKERS` and was
verified identical to it — so the plan was to derive it. Checking how it arrives
showed `handouts` imports `H1_MARKERS` **from `segment`**, which already reads the
course file. The two were never separate copies; they are the same object.

**Rewriting it would have added a second read path to replace a working one.**
The check that established this is worth as much as the change it prevented.

##### `gold` is a function, and a function's repr contains its address

The verification reported all three handouts differing at `gold` — until the
memory address was normalised, after which they were identical. **A baseline that
captures `str(a_function)` compares addresses**, and addresses change every run,
so that field could never have matched. The fix is in the test, not the code.

#### The JOBS reshape — the course id now appears ONCE in the course file

`"edu.memphis.psych" occurrences in course.json: 1` — its own `course` field,
down from 27. Runtime `JOBS` identical, and all 28 migrated tables still match
their authored copies.

Every job stored `screen` as `edu.memphis.psych/bmod_h1_q1` **and** carried `ns`
with the same course id — twice over, in a file whose own `course` field already
says it. And `measured.py` does `job["screen"].split("/")[-1]`, **stripping back
off what was put on.**

The file now holds the bare id and no `ns`; the reader recomposes both. This is a
change to what is STORED, not to what is read, which is why it could be verified
against the same baseline the move used.

**Done as its own change, deliberately.** JOBS moved first with a test, and this
reshaped it with another. Together they would have been one diff in which a
failure could not be attributed to either.

##### The raw-entry escape, caught a third time

Recomposing the namespace needed the course id, and the obvious way to get it is
`coursedata._load()["course"]` — which `check_course_schema_is_complete` flagged
immediately, as it did for `olx_prompts` and for the generator-value path before
that.

**It keeps recurring because `_load()` is right there and returns everything**,
which is precisely why the check exists. `coursedata.course_id()` is the third
accessor added in response, and each one narrows the boundary the check is
defending.

#### C1b's gold exporter — built, verified, and NOT installed

`gold_export.py`: **16 gold declaration tables, 77 entries, 6 per-handout
participant fields. Every table round-trips exactly.** Tested to a scratch path;
the install under `$COURSE_DATA` waits for the write-scope restriction to lift.

These are not the graders' marks — those are in the three workbooks and `gold.py`
reads them. These are the **declarations ABOUT gold**: which cells are corrected
and why, which diverge, which ceilings are unreachable, which slots cannot be
mapped. They are participant-keyed because a judgement is about one person's
answer, and that is exactly why C1b puts them outside a public repository.

##### The round-trip assertion earned itself immediately

`PER_ITEM_EXCLUDE` is `{item: {16: {...}}}` — **integer keys two levels down**.
JSON has string keys only, so `16` came back `"16"`: a silent type change in the
one field that identifies a person. Dicts with non-string keys are now tagged
`{"__dict__": [[k, v], …]}` and rebuild exactly.

##### A refusal that could not fire, and the write it failed to stop

The first guard refused when there was no course-data root. **That is
unreachable** — `data_root()` falls back to `paths.DATA`, which always has a
value — so it was a sentence, not a protection.

While replacing it, `editguard` rejected the edit and the test ran anyway:
`--out ../courses/<id>/gold.json` **wrote 97 KB of participant-keyed declarations
into the repository.** It was deleted immediately, unstaged, uncommitted, never
in the index — verified all three ways.

The guard is now by **PATH**, not by intention: any destination inside the repo
is refused, and the exact command that succeeded before now exits 2. *A
'Participant ID NNN' filename is not de-identification* is this repository's own
rule, and the check enforces it rather than restating it.

**`gold.json` is also not in `.gitignore`.** Adding it is owed — a guard in one
tool does not protect against a file arriving by another route.

### 11.6 · Stage 5 — the rubric becomes data (**A1c**)

`rubric_h{1,2,3}.py` retire. Builders survive OUTSIDE the pipeline as the tool that
generates the expanded canonical JSON.

### 11.7 · Stage 6 — modules (**E1**, per group)

`handouts.py` and `gold.py` split (**E1c**) — cheap once C1b has taken the gold
tables. `gold_slots_q6.py` splits. The three CLI tools rename (**E1a**).
`simulate_h3.py` may stay, with a written declaration.

### 11.8 · Stage 7 — prose (**Goal G**)

**Blocked on restructuring `GOALS.md`** (§10.4.1): 9 headings over 16,516 lines,
nothing to anchor to. Then split all four files general/specific, then place
anchors and turn on the **G1c** gate — danglers fail, orphans warn.
Docstrings under **F1**: no course-derived sentence survives in general prose;
incidents split, generic half stays, specific half to the changelog.

#### Stage 7's split is MEASURED and deliberately not done: 3,832 sentences

`prose_split.py` prepares the split as a worksheet — `PROSE_SPLIT_WORKSHEET.json`
— and moves nothing.

| file | sentences carrying course vocabulary |
|---|---|
| `GOALS.md` | **2,937** |
| `EQUIVALENCE.md` | 341 |
| `BACKLOG.md` | 313 |
| `QUALITY_CONTROL.md` | 241 |
| **total** | **3,832** |

**All 31 sections of `QUALITY_CONTROL.md` carry course vocabulary**, so the split
is a sentence-level rewrite of every section rather than a move of a few. That is
the failure T7.1's design names — *a diff that touches every line cannot be
reviewed* — and these files are read by five modules and by people. §10.3.2's
three outcomes cannot be chosen by a word list; T7.3 says as much about itself.
So the worksheet gathers the evidence for each decision and leaves the decision.

Each row carries the terms that flagged the sentence and a SUGGESTION with its
reason: a date or two measured numbers reads as an *incident*, because that is
what the changelog keeps; an item or slot named without numbers reads as a
*specification*; anything else is left **unclassified**, which is the honest
answer — 166 of the 3,832 are.

##### The first count was 956, and it was wrong by 93% of one file

The worksheet skipped any line indented four spaces, on the usual Markdown
convention that indentation means code. **`GOALS.md`'s prose is indented under
its entries**: 15,640 of its 16,762 lines were discarded, 690 were examined, and
the file reported 89 sentences. Fenced blocks are now tracked properly and
indentation is not treated as code.

The lesson is the one this plan keeps meeting: **a convention that holds
everywhere else is still a measurement assumption**, and 89 sentences for a
17,000-line prose file was the number that should have looked wrong immediately.

### 11.9 · Stage 8 — the fixture course (**I1a**, **I2c**)

Sized by SHAPE COVERAGE — at least one item of each of the 19 key-shapes, coverage
measured and reported. This is the acceptance test for stage one, and it unblocks
three things deliberately parked behind it: **G2c** (`OVERRIDES.md` to structured
data, because it touches the pre-commit gate), **D2a** (generic self-test
fixtures, which retires D2d's exemption), and **E1a's renamed modules**, which are
renamed and not generalised until one runs against a second handout.

### 11.10 · Stage 9 — the rename

`COURSE_DATA` → `COURSE_DATA` (§10.5.3), separately from everything else, with the
old name honoured and warned about for a declared period.

### 11.11 · Stage 10 — the second course (**I1b**), when one exists

`edu.memphis.writing` or `edu.gsu.interdisciplinary`. Stage 8 establishes the
engine is course-SHAPED no longer; only this establishes it is course-INDEPENDENT.
Not scheduled — it waits on availability, and the plan should not pretend
otherwise.

### 11.12 · What the order is protecting

* **The instrument before the work.** Stage 0 first, because everything later is
  certified by it.
* **Measure before design.** Stage 1 before Stage 2, because the schema is fitted
  to what is actually there — and two of this plan's own measurements shrank
  sharply under scrutiny (53 branches to ~13, 188 docstring words to ~30).
* **The reader before the deletions.** Stage 3 before Stage 4: dual-source
  verification needs both sources.
* **The proof last, knowingly.** I2c puts the fixture at the end, so the expensive
  discovery — something migrated early was never general — arrives late. That was
  chosen over designing the fixture against seams that did not exist yet.

---

## 12 · The tooling, keyed to the stage that needs it

*Added 2026-09-18. One design per tool, to be reviewed one at a time.*

**The governing constraint, established before designing any of them:** this repo
already has `enforcement.py` with **149 registered checks**, `guide.py` doing
structural checks on `QUALITY_CONTROL.md`, `sweep_gate.py` gating sweeps, and
`editguard.py` guarding writes. **A gate belongs in that machinery, not in a new
script.** A new script is warranted only for work that produces or transforms an
artifact. Eleven tools follow: four scripts, four checks, two converters, one
module.

### 12.0 · THE RULE FOR EVERY GATE DISCOVERED LATER

**A gate found during the work goes into the existing enforcement mechanism. It is
never a one-off.** This list is not expected to be complete — the work will turn up
rules that need enforcing, exactly as it already has: §9.2a's accessor boundary,
D1x-c's property-not-branched-on rule and G1c's anchor contract were all discovered
while deciding something else, and each became a check rather than a note.

Concretely, a new gate is registered as:

* a `check_*` function in `enforcement.py`, so it runs with the other 149 and fails
  a commit rather than being remembered; or
* an addition to `guide.py` when it is a structural rule about the prose artifacts;
  or
* an addition to `sweep_gate.py` when it must hold before a sweep spends calls.

**Why this is a rule and not a preference.** A one-off script is run by whoever
remembers it, and this project has the evidence: §11.11's self-test defects went
unnoticed because nothing gated them; the enforcement self-test itself contained a
case that had silently stopped testing anything; and the convention "do not start a
sweep while the self-test is running" was a thing a person had to remember until
`refuse_if_selftest_running` made it a refusal. A check that lives outside the gate
is a convention with a filename.

**What that requires of each gate:** it must be cheap enough to run every time
(the audit already runs 149), it must name the module, the field and the rule when
it fails, and it must be tested by a self-test case that proves it fires — which,
per T0.1, must not be vacuous.

---

### T0.1 · the self-test's own vacancy report — NOT a script — STAGE 0

*Revised on review, 2026-09-18. First designed as a standalone
`selftest_case_audit.py`; three objections retired that shape — see "why not a
script" below.*

**Why.** On 2026-09-18 one case failed with `NOTHING FIRED` because the table it
mutated was empty (`dict(SCORER_NEUTRAL)` had no entries, so the comprehension
iterated zero times and the injection injected nothing), and a second was SKIPPED
because the finding it blinds was not firing. Both had been testing nothing for an
unknown period while the suite reported `72 of 72 expected`.

**What it is.** A report the SELF-TEST emits, from data it already has. Each case
already computes the findings before and after its injection in order to assert the
right one fired; the report records that delta per case and fails the run when any
case could not have tested anything.

**Two failure states, not one.**

1. **Zero delta** — the injection changed no finding. The neutrality case.
2. **SKIPPED** — the case's precondition was absent, so no comparison happened at
   all. The count-scaffold case. *A skip never reaches a before/after comparison,
   so a design that only compared deltas would have caught the first failure and
   missed the second — which is half the evidence that motivated this.*

Both are vacancy. Both fail the run.

**Output.** Per case: `name, findings before, findings after, delta, verdict`, and
a summary line of the form `N cases, M vacuous` — with a non-zero exit when M > 0.
The existing `70 detected, 1 failed, 1 skipped, 72 of 72 expected` line stays; this
sits beside it and answers a different question, which is not "did the right thing
fire" but "could anything have fired at all".

**Why not a script (§12.0, and two practical objections).**

* §12.0 says a gate belongs in the existing machinery, not in a one-off run by
  whoever remembers it. An `enforcement.py` check is the usual home, but this one
  audits the SELF-TEST, so making it a check means the audit checking its own
  self-test — and proving that check fires would require deliberately making a case
  vacuous. Emitting it FROM the self-test keeps §12.0's intent without the
  circularity.
* **Cost.** A standalone auditor would re-run `enforcement_audit()` before and
  after every case. The audit takes minutes alone and the suite is ~3 hours over 72
  cases; re-running it per case could double or triple that. The self-test already
  has these findings in hand, so consuming them is free.

**The failure it must not have.** It must not depend on the tree's incidental
state, or it acquires the disease it diagnoses. It asserts a DIFFERENCE, never a
specific finding.

**Verification.** Both known-vacuous cases must be flagged BEFORE they are
repaired — the neutrality case by zero delta, the count-scaffold case by skip. A
tool for finding vacuous tests that has never caught one is not known to work.

#### BUILT 2026-09-18 — what writing it changed

* **The baseline was a COUNT, not a set.** `_selftest_baseline = len(...)`, so a
  delta computed from it cannot tell a case that changed nothing from one that
  added a finding and removed another — it would have reported a WORKING case as
  vacuous. `_baseline_keys` now captures the set alongside the count. Third time in
  this work that a measurement was weaker than it looked.
* **Verification needed no 3-hour run.** The agreed approach was to check out the
  pre-repair code and run it. Unnecessary: the defective run's OUTPUT is recorded,
  and both rules are decidable from it — the neutrality case reported
  `NOTHING FIRED` against `baseline 0`, so its delta was provably zero, and the
  count-scaffold case is in the `SKIP` list verbatim. Verifying against what
  happened beats re-enacting it.
* **`_vacancy_report` is a PURE FUNCTION** taking records and skips. That was the
  point of emitting a per-case record, and it paid immediately: every behaviour
  here was tested in seconds, against a suite that takes three hours.
* **DECIDED: a RATCHET, not a hard fail** (`SELFTEST_VACANT_MAX`, same idiom as
  `SELFTEST_EXPECTED` and `HANDCODED_BUDGET`). A hard fail would make the suite
  permanently red for a reason nobody can fix: the `plain-path computed check`
  case SKIPS by design when the corpus holds no item outside the derive-path
  branch, and a corpus is not a defect. Growth is what actually goes wrong — a
  case quietly stopping testing — and the ratchet catches exactly that, while
  falling freely so repairing a case never requires editing a budget.

#### The defect T0.1's first real run exposed — a RATCHET COUNTING ITSELF WRONG

Repairing the two cases made the suite report `71 of 72 expected` and
`*** THE SUITE LOST 1 CASE`. Nothing was lost. `total = built + len(skips)` where
`built = len(cases)` — and an inverted case whose precondition is absent is
appended to `cases` with `found=None` AND added to `skips`, so the same case was
counted twice.

**`SELFTEST_EXPECTED` has therefore been one too high since 2026-09-05**, when it
was raised 64 -> 65 "for subgoal E43's INVERTED case": that raise added one for a
case `len(cases)` was already counting.

Why it matters beyond the number: this constant is a TWO-SIDED ratchet whose
stated purpose is that *fewer means a case was lost*. An arithmetic that can
quietly add one masks exactly the loss it exists to catch — **and it did**, for
the whole period the neutrality case was injecting nothing while the suite printed
`72 of 72 expected`.

Fixed by correcting the arithmetic rather than lowering the constant to match:
conditional skips (`plain`, `_site`) are counted because they are NOT in `cases`;
inverted skips are printed but not re-counted. `SELFTEST_EXPECTED` is now 71.

*The general lesson, and it is the fourth of its kind in this work: a count that
looks right and measures the wrong thing is the recurring defect here — the
baseline that was a length not a set, the 53 branches that were 13, the 188 words
that were 30, and now a ratchet that counted one case twice.*

#### The artifact it leaves

`$COURSE_OUT/selftest_cases.json` — per case: label, want, item, inverted, baseline
and found counts, and the findings added and removed. Written every run, consumed
by the report, and reusable by anything later that wants to know what a case
actually did.

---

### T1.1 · `course_inventory.py` — the four-embedding scan — STAGE 1

*Revised on review, 2026-09-18: four objections, recorded below with the design
they produced.*

**Why.** §2.1 counted tables and called itself a floor. §10.7 redefined "clean" as
four counts. Nothing measures all four, and two ad-hoc measurements made for this
plan were WRONG IN THE SAME DIRECTION: 53 "branches" were really 13 plus three
other populations, and 188 "course words" were ~30 once `handout` (127) and
software-sense `behaviour` (35) came out.

**What it does.** Per module, by AST: (1) module-level tables whose literals name
course items; (2) literal course ids in code; (3) unmarked course vocabulary in
docstrings; (4) course artifacts in the module's own name.

#### The item ids come from DATA, never from a pattern in this tool

**The objection that reshaped it.** To find `Q1`, `WK2`, `1c`, the scan needs this
course's item ids. The ad-hoc version hard-coded
`Q\d+[a-c]?|WK[12]|DAY[12]|PR|NR|...` — which is EXACTLY the embedding the tool
exists to detect. A scan that hard-codes this course's identifiers to find this
course's identifiers passes its own test forever and finds NOTHING in a second
course.

So the id list is an INPUT: read from the course file once it exists, from the
rubric modules until then, and **the tool carries no id pattern of its own**. The
same rule governs the vocabulary list: every term carries a one-line justification
in the source, and a term without one fails the tool's self-test. `handout` and
software-sense `behaviour` are excluded BY DECLARATION, with their counts (127, 35)
recorded as the reason.

#### It reports populations; it does not guess them

Today's decomposition — 28 self-test fixtures, 13 for `1c`, 5 builder
conditionals, 4 for `Q6` — was done BY HAND, by reading enclosing functions and
modules. Some of that automates ("is this inside `enforcement_selftest`?") and some
does not ("is this a data builder or an engine branch?").

**Where it cannot decide, it reports the raw hit with its enclosing function and
leaves the classification to a person.** A wrong split is worse than none: C2a's
per-module proof would then count the wrong things and report clean modules that
are not.

#### Its JSON is an INTERFACE, not a report

T4.1 reads this output to gate Stage 4, so the shape is a contract: it carries a
`schema_version`, and the gate REFUSES an unknown version rather than reading it.
A gate that reads a changed shape may report zero findings, and zero findings looks
exactly like success.

**Output.** The versioned JSON, plus a readable table for a person to classify each
finding per §5.1: *rubric content*, *metadata (moves)*, *engine (stays)*,
*undecided*.

**Verification — exact numbers, not approximations.** The first run fixes an
expected count per category, and the tool is tested against those exact figures
thereafter. Today's hand counts are the starting point but are NOT the assertion:
46 tables, 9 course-named modules, and id/vocabulary figures that the first run
must establish precisely. **Where the tool disagrees with the hand count, that is a
finding to resolve, not a tolerance to widen** — one of the two hand counts this
plan already corrected was out by a factor of six.

### T2.1 · `rubric_export.py` — builders to canonical JSON — STAGE 2, used at 5

*Revised on review, 2026-09-18: four objections, recorded with the design they
produced.*

**Why.** A1c: `rubric_h2`'s four builders survive as an AUTHORING tool that
generates the expanded canonical JSON; no reader ever instantiates a template.

**What it does.** Imports the three rubric modules, expands `ITEMS`, decides what is
derived by MEASUREMENT rather than by the list in §9.0, and writes
`courses/<id>/course.json`.

#### Derived-or-authored is decided by recomputation, not by the §9.0 list

§9.0 sorted the module exports into "derived" and "independent" using a substring
test — does the assignment mention `ITEMS`, a loop, `sum(` or `BY_ID` — and says in
as many words that it is "a starting point, not a finding".

**An export that acts on that list can silently LOSE data**: drop something that is
not in fact derivable and the value is gone, and T5.1 would only catch it if the
reader's recomputation happened to differ from the original.

So for each candidate the export **recomputes the value and compares it to the
module's**. It drops only what recomputation reproduces EXACTLY; anything else is
carried as authored data regardless of what §9.0 guessed. The comparison is
reported, so the §9.0 list is corrected by this run rather than left standing.

#### BUILT 2026-09-18 — and what it showed about A2a

The export works and is deterministic (byte-identical on re-run; keys sorted
within an entry, items in rubric order). 26 items, 223,680 bytes.

**But §9.0 called TWELVE names derived and this tool can prove TWO.** It drops only
what a known derivation reproduces exactly — `BY_ID` and `TOTAL` — and CARRIES the
other ten (`SLOT_SPEC`, `OC_GATES`, `FORBID`, `SLOT_OPTIONS` and the six `*_ITEMS`
index lists), because refusing to drop what it cannot recompute is the whole point
of deciding by recomputation.

So **A2a is two-twelfths honoured today**, and the file is larger than A2a intends.
That is not a defect in the export; it is where the derivations actually live. Each
one is 78 source lines in h1 and 149 in h2 for `SLOT_SPEC` alone, implicit inside
the rubric modules, and writing them is Stage 3's work — the READER is where a
derivation belongs.

**DECIDED 2026-09-18: `DERIVATIONS` moves into `coursedata.py` at Stage 3 and lives
there alone.** The export decides what to drop; the reader rebuilds it. Those are
one question asked from two sides, and two implementations that must agree is
exactly the defect T5.1 had to be redesigned to avoid. From Stage 3 the export
imports the table from the reader and drops precisely what the reader can rebuild.

The sequence this implies, and it should be read as A2a's progress meter:

1. **now** — 18 values carried, 2 proven derivable;
2. **Stage 3** — each derivation written in the reader; as it lands, `DERIVATIONS`
   gains an entry and that value leaves the file;
3. **T5.1 throughout** — so a wrong derivation is caught when it is written, not
   when something downstream misreads it.

#### MEASURED 2026-09-18 — §9.0's "derived" list was wrong about ten of twelve

Every candidate was classified by HOW IT IS DEFINED, by AST:

| | count | which |
|---|---|---|
| derivable from `ITEMS` | **2** | `BY_ID`, `TOTAL` |
| **authored literals** | **16** | `SLOT_SPEC`×3, `MAPS`×2, `OC_GATES`, `FORBID`, `SLOT_OPTIONS`, `EXPECT`, `REQUIRED_MOVE`, `AVOIDANCE_SCORES`, `READS_UTB_CHOICE`, and the `*_ITEMS` index tuples |
| derived from another AUTHORED literal | 1 | `BARRIER_PICK_ITEMS = CADENCE_BARRIER_ITEMS + ('NR',)` |

**Why §9.0 got it wrong**, which is worth knowing because the same test would
misfire again: it searched the assignment's source for `ITEMS`, `for `, `sum(` or
`BY_ID`. It matched `"for "` inside PROSE LABELS —
`'Realistic — why it is achievable for you'` — and `ITEMS` inside the variable's
OWN NAME, `CADENCE_BARRIER_ITEMS`. Neither is a computation.

**`SLOT_SPEC` is the sharpest case and settles it.** All three are plain literals,
and **47 of its 52 labels appear nowhere in `ITEMS`** — `"Says whether it is a good
choice to modify"` exists only there. No derivation can invent authored prose. Had
the export acted on §9.0's list it would have dropped 269 source lines including 47
unrecoverable labels, and the loss would have surfaced only when something tried to
render a slot sheet.

**What this does and does not change.** A2a's DECISION stands — do not store what
can be recomputed. A2a's EXPECTATION was wrong: almost nothing can be. The course
file is therefore about the size the rubric modules are, and that is correct rather
than a shortfall. The Stage 2/3 cycle (§11.2a) is accordingly SHORT — there are not
a dozen derivations to write, there are none outstanding that are provably
derivable from items.

*This is the recomputation design paying for itself twice: once by refusing to act
on a wrong list, and once by producing the measurement that showed the list was
wrong.*

#### The tagging is applied at STAGE 4, not here

The rubric modules hold no GENERATOR fields — those are `olx_prompts.py`'s 12
tables, which move under B2a in Stage 4, after this. If T2.1 tagged fields at Stage
2, every field would be RUBRIC, the tagging would be trivially uniform, and
**T2.2's check would pass vacuously** — the exact failure T0.1 exists to catch,
reproduced in a new place. The schema declares the two groups from the start; the
interesting classifications arrive with the generator fields.

#### Deterministic means an ORDER that is pinned

"Byte-identical on re-run" is not free: Python dicts are insertion-ordered and the
builders construct in loops, so a refactor that changes iteration order changes the
file without changing its meaning — a large diff with no content, which reviewers
learn to skim. The export emits **sorted keys within an entry, and items in RUBRIC
order** (not alphabetical: rubric order is how a person reads them).

#### What expansion makes permanent

Expanding the builders bakes in their conditionals — the 5 `if item_id == "DAY2"`
cases become DAY2's text and nothing else. That is the intent. It also means **a
bug in a builder becomes permanent data** once the modules retire. Two consequences:
T5.1 runs while the modules still exist (already required), and the modules are
retired by DELETION IN GIT, never by rewriting in place, so the oracle stays
readable in history.

**Output.** One file, ~171KB expanded, deterministic under the pinned order.

**The failure it must not have.** Silently dropping a field it does not recognise.
Anything neither reproduced by recomputation nor classifiable is an ERROR, never an
omission.

**Verification.** T5.1's equivalence proof, plus the recomputation report above —
which is itself a correction of §9.0 and should be read as one.

### T2.2 · `check_course_schema_is_complete` — an enforcement check — STAGE 2

*Revised on review, 2026-09-18. Grown to cover §9.2a's obligation 3, which had
fallen between two designs.*

**Why.** §9.2a sets three obligations and the first draft of this section covered
only the first. Obligation 2 (accessors expose each group separately) belongs to
T3.1, which is a module and cannot gate itself. Obligation 3 (no module crosses the
boundary) was assigned to nothing: T4.1 gates course DATA sitting in a module,
which is a different thing from a module reaching across the accessor boundary.
**A rule with no tool is a comment.** This check now carries both 1 and 3.

#### Part A — the declaration (obligation 1), reported in BOTH directions

* **An undeclared field is a VIOLATION.** A field on an item entry that no group
  names fails the check. This is the rule: §9.2a says a new field naming no group
  fails validation rather than defaulting.
* **A stale declaration is a CLEANUP.** A group naming a field that does not exist
  is reported separately and does not fail by itself.

They are reported apart because they mean different things, and merging them would
let a real violation hide in a list of tidying.

#### Part B — the boundary (obligation 3)

By AST over every module except `coursedata.py`: no module may index a GENERATOR
field off a rubric result, or a RUBRIC field off a generator result, and none may
obtain a raw item entry from anything other than an accessor. The raw-entry escape
is the one to watch — it defeats the boundary while appearing to honour it.

**Failure message names the module, the field, and the group it belongs to**, so
the fix is either "use the other accessor" or "declare the field where it actually
belongs". "Boundary violated" would send the reader back to §9.2a to decode it.

#### BUILT 2026-09-18 as `course_schema.py` — clean, and honest that it proves nothing yet

`30 fields declared (0 generator), 0 violations, 0 cleanups.` `--self-test`: 4/4
conditions caught. Gated by `check_course_schema_is_complete` (158 checks).

Every item field is already in a declared group and no declaration is stale, so
**Part A passes on real data by having nothing to find**, and Part B has no
cross-group field to look for while `GENERATOR_FIELDS` is empty. The run says so
in its own output rather than reporting a clean bill:

> `NOTE: GENERATOR_FIELDS is empty, so Part A cannot yet fail on real data and
> Part B has no cross-group field to find. The self-test is what exercises this
> check until Stage 4.`

All four conditions are therefore constructed and injected by the check itself —
including two that need a module on disk, so it writes a probe module, scans it,
and removes it in a `finally`.

##### A defect found on the way: `gold_path()` was silently relative

`coursedata.gold_path()` read `$COURSE_DATA`/`$COURSE_DATA` directly and fell back
to `""`, so with the variable unset it returned **`courses/<id>/gold.json`** — a
relative path resolving against whatever the working directory happened to be.
It would have reported "gold is not available" while never having looked in the
right place, and would have FOUND a file if one ever sat beside the caller.

`paths.DATA` already carries the default and every other reader goes through it.
`coursedata.data_root()` now does too, and with no root at all the path is
returned named (`<COURSE_DATA-unset>/…`) rather than silently relative.

##### Where the alarm sits, and where it does not

A missing `$COURSE_DATA` is a **failure**, in the project's own idiom — *a check
that cannot run is not a check that passed*. But `$COURSE_DATA` present with
**no gold file yet** is NOT a failure: C1b's export is Stage 5 work, and failing
here would gate Stage 2 on a later stage's output. The distinction is in the code
with the reason attached.

#### The self-test case, and why it needs writing now

At Stage 2 there are no GENERATOR fields, so Part A is satisfied by tagging
everything RUBRIC and **the check passes while proving nothing** until Stage 4 —
a check whose first real exercise is two stages away is one nobody has watched
fail.

So it ships with self-test cases that construct their own conditions, per T0.1:

1. add a field in NEITHER group → Part A must fire;
2. declare a group member that does not exist → the cleanup report must list it,
   and the check must NOT fail on it alone;
3. make a module read a GENERATOR field off a rubric result → Part B must fire;
4. make a module take a raw entry → Part B must fire.

Each is injected and restored by the case itself. None depends on the tree
containing a suitable example, which is how the neutrality case became vacuous.

#### Gold is in scope, and a missing `$COURSE_DATA` is an ALARM

C1b puts gold in a second file, under `$COURSE_DATA/courses/<id>/`, outside this
public repository. **This check validates that file too** — an ungated schema is an
ungated schema wherever it lives.

That means the check assumes `$COURSE_DATA` exists. **When it does not, the check
FAILS LOUDLY — it does not skip and it does not pass.** The message says the
variable is unset or the path is absent, and that gold could not be validated.

This is deliberate and it is the project's own rule: a check that cannot run is not
the same as a check that passed. `check_count_scaffolds_are_arithmetic` already
says exactly that when its output root is missing — *"this check cannot run, which
is NOT the same as passing"* — and this follows it. The cost is that anyone with
the repo and not the data gets a failure; that is the intended signal, because
scoring without the gold data is not a state to proceed quietly from.

**Why a check and not a script.** §12.0: it runs with the other 149, so an
unclassified field or a boundary crossing fails a commit rather than being noticed
later.

### T3.1 · `coursedata.py` — the reader — STAGE 3

*Revised on review, 2026-09-18: five objections, recorded with the design they
produced.*

**Why.** B1a: a single module owns the file.

**What it does.** Loads `courses/<id>/course.json` and, lazily, the separate gold
file (C1b); recomputes what is genuinely derivable (A2a); and exposes SEPARATE
accessors per group — `rubric_for(item)`, `slot_notes(item, slot)`, `ref_ids(item)`
(§9.2a obligation 2).

#### BUILT 2026-09-18 — and the cycle proved safe

The reader works: 26 items, `rubric_for("Q1")` returns 14 RUBRIC fields and no
generator fields, `TOTAL` for handout 1 rebuilds to 45.0 (matching the module's own
comment), `BY_ID` to 8 keys for handout 1's 8 items.

**Nested mutation was the test that mattered.** A shallow copy would pass
"mutating the returned dict does not leak" and fail on
`rubric_for("Q1")["credit"][0]["pts"] = -999`, which reaches into the loaded
document through a shared inner object. Both are tested; both hold.

**Gold is genuinely independent.** With `COURSE_DATA` and `COURSE_DATA` both unset,
`gold()` refuses with the variable and path it tried while `items()` still returns
all 26 — which is the split T3.1's review asked for and T2.2 deliberately does not
make.

**The cycle with T2.1 is safe against a WRONG derivation.** `DERIVATIONS` now lives
here and the export imports it. Adding a deliberately incorrect derivation for
`MAPS` (returning `{}`) did NOT cause the export to drop it: recomputation
differed, so the value was carried, and the report said why. A bad derivation in
the reader cannot lose data in the file — it can only fail to save space.

That is the property that makes the Stage 2/3 loop (§11.2a) safe to run a dozen
times: each pass can only move a value from "carried" to "dropped" when the reader
demonstrably rebuilds it.

#### The boundary is a MECHANISM, not a rule

"No accessor returns a raw entry" is not enforceable by intention: Python has no
private data, so an accessor returning the inner dict hands the caller everything,
and `rubric_for(item)["slot_notes"]` then works. **T2.2's AST check would not
necessarily see it** — that is a runtime subscript on a returned value, not a
declared field access — so the boundary would hold only by convention, which is
what §9.2a exists to avoid.

Therefore every accessor returns **a copy, or a read-only view, containing only the
fields of the requested group**. A caller cannot reach a field of the other group
because it is not in what they were handed.

#### Copies are required because the code MUTATES

This is not hygiene. The existing code mutates these structures in place:
`enforcement_selftest` does `rubric_h1.BY_ID["Q6"].pop("cover")` and restores it;
`_drop_dealt` pops from `JOBS`. If the reader hands out shared dicts, one caller's
mutation corrupts every later reader in the same process — and the self-test is
BUILT on doing exactly that.

#### A2a's recomputation hides a port, and one value that cannot be recomputed

The reader recomputes `BY_ID`, `TOTAL`, `SLOT_SPEC` and the `*_ITEMS` index lists.
Those derivations currently live in the rubric modules — `SLOT_SPEC` is 78 source
lines in h1 and 149 in h2 — so "the reader recomputes" is a real port, not a
one-liner.

**And h3's `SLOT_SPEC` is INDEPENDENT, not derived** (§9.0). It must be carried as
authored data. T2.1's recomputation test is what will confirm that, and this design
states the expectation now so it arrives as a confirmation rather than a surprise.

#### Load once per process, and do not watch the file

149 enforcement checks plus a sweep call these accessors constantly; re-reading and
re-deriving a ~171KB file per call is not viable, and a cache that watches for
changes reintroduces the staleness this project has already been bitten by (a
long-lived dev server serving fresh content from stale code cost 19 observations).

So: **loaded once per process, never re-read.** A process that outlives an edit to
the course file is a process to restart, and that is the documented expectation
rather than something clever.

#### Gold loads LAZILY; only gold accessors fail without it

T2.2 fails loudly when `$COURSE_DATA` is missing, because validating gold is its
job. The READER must be subtler: the rubric lives in the repo and `rubric_for()`
has no reason to need gold.

So gold is loaded on first use by a gold accessor. Someone with the repo and not
the data keeps the whole rubric side of the reader; only a gold call fails, and it
fails saying which variable is unset and which path was tried.

**The failure it must not have.** An accessor handing back the whole entry. It
defeats the boundary while appearing to honour it, and is the most likely way B2a
fails.

### T3.2 · `dual_source_verify.py` — reader vs incumbent — STAGE 3

*Revised on review, 2026-09-18: five objections, recorded with the design they
produced.*

**What it does.** Compares what `coursedata.py` returns against what the existing
modules return TODAY, in both directions, and reports how much it actually
compared. Runs before any table is deleted.

**Why it matters.** Stage 4 deletes tables. A reader that agrees on 99% of keys
looks right and silently changes 1% of scores.

#### The key inventory comes from T1.1, not from this tool

"Every item, slot and gold row" is not an enumeration. The incumbent side is 46
tables across 8 modules with incompatible key shapes — `GOLD_DIVERGENCES` keyed one
way, `PER_ITEM_EXCLUDE["Q4c"][16]` another, `CORRECTED_GOLD[("NR", 4)]` another —
and no single iteration reaches them all.

Enumerating them is exactly T1.1's job, so **this tool consumes T1.1's output**
rather than re-deriving it. Two inventories would eventually disagree about what
exists, and the disagreement would appear as a verification result.

#### BOTH directions, because the dangerous gap is the reader's

Comparing only "for each key the reader knows, does the incumbent agree?" **passes
when the reader is missing keys entirely** — and Stage 4 then deletes a table whose
contents were never carried across.

So: keys the incumbent has and the reader lacks are reported as a FAILURE, not an
absence. Keys the reader has and the incumbent lacks are reported too; they are
usually a migration in progress, but they are never silent.

#### Coverage is reported, and zero coverage cannot exit 0

At the start of Stage 4 almost nothing is in the JSON. A run comparing zero keys
and exiting 0 reads as "verified" — T0.1's vacancy problem in a new tool.

Output therefore leads with **`N keys compared, M tables not yet migrated`**, and
the tool REFUSES to exit 0 when coverage is zero. A partial run is a legitimate
state during Stage 4; a partial run that looks complete is not.

#### BUILT 2026-09-18 as `reader_equivalence.py` — and the inventory source above is WRONG

`50 values compared through the reader, 65 tables not yet migrated — EQUIVALENT.`
`--self-test`: **9 of 9 failure modes caught.**

**The design's key-inventory rule was corrected before the tool was written**
(approved 2026-09-18). "Consume T1.1's output rather than re-deriving it" has the
right reasoning and the wrong source. T1.1 answers *which tables embed course
ids* — an **embedding** census, sized to bound the renaming work. This tool needs
*what does the module hold that must be carried* — a **completeness** census.
Measured, they differ: handout 2 holds 27 module-level names where T1.1 lists 15.
`SLOT_OPTIONS` is absent from T1.1 **and is carried by the export**; `BY_ID` and
`TOTAL` are absent and are the two values the reader rebuilds. All three would
have gone unverified while the run printed success.

It does not borrow the export's rule either (`isupper() and not startswith("_")`),
which would agree with the export by construction and go blind wherever the
export is blind. Instead **every module-level name is enumerated by reflection and
every one must be accounted for** — compared through the reader, or carrying a
written justification keyed by `(handout, name)` so a new private table in a new
module cannot inherit a justification written for a different one. Unaccounted is
a FAILURE.

T1.1 is still consumed — for the `65 tables not yet migrated` line, which is
exactly the question an embedding census answers.

##### What the completeness census found immediately

`rubric_h2._HELD_BACK_RULE` is **dead**: 686 characters of authored scoring
prose, defined at `rubric_h2.py:155`, referenced nowhere, absent from every
item's text, and written for a `held_back_is` slot that no item uses. T1.1's
inventory would never have looked at it — it names no course ids.

It is reported and left in place. **A migration tool is the wrong place to decide
that authored scoring text is dead**, so this is owed as a content decision:
delete it, or find the item whose guidance lost it. It ships nowhere today either
way, so no measured result depends on the answer.

##### `handout` is invented by the export, so it is declared and checked

No module item records its handout — the module it is written in *is* the
handout, and that fact is lost the moment the items are pooled. The export
synthesises the field. `EXPORT_ADDED` names it rather than quietly ignoring it,
and the tool checks it holds the RIGHT value, because an invented field deserves
more scrutiny than a carried one, not less.

##### Three of the nine controls caught defects in the TOOL, not the data

This is the argument for negative controls stated as a measurement:

1. **A check that could never fire.** The `handout` check was unreachable: the
   served items were *filtered* by handout, so a wrong value removed the item
   instead of mismatching it. It reported "missing" and never compared the value.
2. **Coverage that could never reach zero.** `BY_ID` and `TOTAL` rebuild happily
   from an empty pool — `{}` and `0` — so a file with nothing migrated still
   reported "2 values compared" per handout and the refusal was unreachable.
   **T0.1's vacancy defect, reappearing inside the guard written against it.**
   Rebuilding a value from no inputs proves nothing.
3. **The same bug twice.** The empty-pool guard was first gated on the *module's*
   items, which are never empty. The pool that matters is the *reader's*.

The controls live in the tool as `--self-test`, not in a scratch file, because
controls kept outside the tool rot the moment the tool changes.

#### Comparison is by VALUE, in the pinned order

T3.1 returns copies rather than the incumbent's own objects, so identity
comparison is meaningless. Values are compared after normalising to T2.1's pinned
order (sorted keys within an entry, items in rubric order), so the two tools cannot
disagree about what "the same" means.

#### Gold is in scope and its absence is LOUD

`GOLD_DIVERGENCES` (771 lines) and `CORRECTED_GOLD` (503) are where a silent 1%
difference actually changes scores, so they are the most important half to verify —
and they live under `$COURSE_DATA`, outside the repo.

**If the gold data is absent this tool FAILS; it does not verify the repo half and
report success.** Unlike T2.2, where a missing `$COURSE_DATA` is obviously fatal to
the check's purpose, the danger here is that comparing only the repo half still
produces a plausible green result — which is precisely the shape of failure this
tool exists to prevent.

### T4.1 · `check_module_has_no_course_data` — an enforcement check — STAGE 4

*Revised on review, 2026-09-18: five objections, recorded with the design they
produced.*

**What it does.** C3c's gate half: a module declared MIGRATED must have zero count
in §10.7's categories. T1.1 is the metric half.

#### It RUNS the scan; it does not read yesterday's answer

The first draft had the check read T1.1's JSON. **A gate reading a cached
measurement passes while the thing it measures changes underneath** — edit a module
to add a course table and the JSON, written earlier, still says zero.

This project has already paid for that shape once: a dev server reloading CONTENT
but not CODE mis-scored every mapped slot for 19 observations while looking healthy.

So **T1.1 is an importable module** and the check calls it; the CLI is a thin
wrapper over the same code. The scan is AST work over ~50 files and is cheap enough
to run in the gate that already runs 149 checks. T1.1's versioned JSON remains the
interface for humans and for T3.2 — but the gate never trusts it.

#### The MIGRATED list lives in the engine

Which modules are migrated is state: a list updated as Stage 4 proceeds. It is
course-INDEPENDENT — a fact about the engine, not about psychology — so it lives in
the engine beside the check, never in the course file. §0's rule decides this: the
course file may not be where the engine records its own progress.

#### A ratchet as well as a whitelist

A list of migrated modules is a whitelist, and whitelists rot: a module can be
migrated and never declared, and nothing notices. So the check ALSO carries a
ratchet on the total counts across all modules, in the idiom this repo already uses
for `STUDENT_TEXT_BUDGET.json` — the totals may fall and may not rise.

The two catch different failures. The whitelist proves a specific module is done;
the ratchet catches a regression anywhere, including in modules nobody has declared
yet, which is most of them for most of Stage 4.

#### The D2d exemption expires by MECHANISM

"Expiring when D2a lands" is a sentence, and sentences do not expire. D2d makes the
exemption conditional on two things: the concurrency guard (MET 2026-09-18) and
§11.11's restore defect.

So the check names those conditions and **fails when they are satisfied while the
exemption is still present**. An exemption that outlives its reason is how "for
now" becomes "forever", which §12.0 and this project's own history both say is the
default outcome.

#### BUILT 2026-09-18 — three checks, a ratchet file, and an exemption that expired on contact

`152 checks registered (was 149). 55 modules, 200 embeddings baselined. 11/11
negative controls caught. Scan cost 2s` — cheap enough for the gate, as assumed.

| check | what it gates |
|---|---|
| `check_module_has_no_course_data` | whitelist + ratchet over §10.7 categories 1–3 |
| `check_no_module_is_named_for_a_course_artifact` | category 4, ratcheted at today's 9 |
| `check_every_enforcement_check_is_registered` | **unplanned** — see below |

##### The registration check was not in the design, and should have been

149 checks were defined and 149 were called, matched **by discipline alone** —
nothing enforced it. This tool added three checks, any one of which could have
been left unwired with nothing to notice, and a check nobody calls is worse than
no check: it reads as coverage, passes review, and never runs. Run before wiring,
it named all three, including itself.

##### Two bugs, both found by refusing a first clean number

1. **`_exempt` excused 117 of 230 embeddings.** It compared `entry.get("in")`
   against `D2D_EXEMPTION.get(module)`; for any module *not* in the exemption both
   sides are `None`, so every module-level embedding in every module compared
   equal and was excused. **A `None == None` is how a narrow exemption becomes a
   general one.** Caught only because the printed totals refused to reconcile with
   the budget's sum — 230 against 113.
2. **The expiry predicate was keyed on the wrong name.** It looked for
   `_selftest_in_flight`, which is the helper *inside* `olx_prompts`; the call in
   `equivalence.py` is `refuse_if_selftest_running`, and the helper's name appears
   there only in a comment. The condition read False, the exemption looked alive,
   and the expiry silently did not fire — a false negative in exactly the place
   the predicate's own docstring warns a structural test can have one.

##### The name check had to be ratcheted, or it could never have been added

Unratcheted it fails from the moment it exists, since the nine modules are still
named for questions and handouts today. That would mean adding it only *after*
the GOAL E work it gates — a gate that gates nothing. Baselined instead:
`named_modules` may shrink and may not grow, and a stale entry is reported so a
reduction cannot be quietly undone.

##### The writer is in T1.1, the gate is in enforcement — deliberately

`course_inventory.py --tighten` writes `COURSE_DATA_BUDGET.json`; the check only
ever reads it. **A gate that can lower its own bar is not a ratchet.** `--tighten`
refuses a count that rose, because baselining a regression turns a ratchet into a
record of whatever happened to be true.

#### The D2d exemption EXPIRED on the day this check was written

Both conditions are closed, and the check says so:

```
True  enforcement_selftest calls refuse_if_selftest_running
True  snapshot/repair net installed and a moved source FAILS
→ the D2d exemption has OUTLIVED ITS REASON
```

**Decided 2026-09-18: parked, not declared, and D2a is owed and scheduled.**
`PARKED_UNDECLARED[("-", "MIGRATED MODULE HOLDS COURSE DATA")]` carries the reason
and `PARKED_BUDGET` goes 0 → 1. The finding stays computed and printed; what the
park silences is the commit gate, not the measurement. The difference from a
declaration is the claim: a declaration would say the 30 course-bound fixtures are
right, and they are not — they are wrong and D2a is what fixes them.

`check_parked_entries_still_apply` reports the park if the finding ever disappears
first, so the park cannot outlive its own reason the way the exemption did.

**D2a, now owed:** each of the 30 fixtures in `enforcement_selftest` selects its
target BY SHAPE — the first item with `counts`, the first `dealt` job — and
**reports the target it chose**, so D2a's coverage-drift weakness shows up in the
run's own output instead of silently. The park goes when D2a lands.

#### The module-NAME category is a separate check

§10.7's fourth category — no course artifact in the module's own name — cannot be
gated from a module's contents: renaming `gold_slots_q6.py` changes the file's
identity, so the rule is about the repository's file list, not about any one
module.

It is therefore its own small check over the module names, not a category folded in
here. Folding it in would mean a per-module check that fails for a reason the
module's own contents cannot fix.

### T4.2 · the property ratchet — a narrower check than first designed — STAGE 4

*Rewritten on review, 2026-09-18. The first design said it would search engine code
for any branch on a declared PROPERTY. Reconsidering the scope changed what it is
for, and shrank it.*

#### What reconsidering found: a single branch on a property is NOT a genericity defect

`if caps.boxes == 8:` is fine. A second course with six boxes works — the branch
reads the value and behaves correctly, and nothing is course-bound. Contrast
`if item == "1c":`, which a second course can never satisfy — and **T4.1 already
catches that**, because it is a literal course id in code.

So D1x-c is not protecting against any individual branch. The harm §10.1.1 actually
names is different and narrower:

> the flag vocabulary then becomes the place where course shape accumulates

The failure is **ACCUMULATION**. One flag is harmless; forty narrow booleans —
`derives_from_series`, `needs_utb_gate`, `blank_code_applies` — mean the engine is
psychology-shaped again in a new vocabulary, and a second course must set flags it
cannot interpret.

#### Part A — the ratchet, which is the part that matters

A count of DECLARED PROPERTIES that appear in any branch anywhere. **It may fall.
It may not rise without a declaration naming the new property and why a strategy
would not do.**

This targets accumulation rather than instances, is completely decidable (it is a
syntactic question, not a dataflow one), and uses the idiom already in this repo:
`STUDENT_TEXT_BUDGET.json`, and T4.1's own ratchet.

#### Part B — a narrow, SOUND check, advertised as narrow

Direct forms only: an attribute access or subscript of a declared property inside a
branch condition. It must cover **truthiness**, which is the most natural way to
write the violation and which a comparison-only check would miss entirely:

    if item.derives_from_series:          # caught
    if not caps.blank_code:               # caught
    if caps.boxes == 8:                   # caught
    n = caps.boxes; ...; if n == 8:       # NOT caught — indirection

`coursedata.py` is exempt: the reader MUST branch on properties to recompute
derived values and choose accessor paths, so gating it would fail the one module
that has to do this.

#### It does NOT claim completeness, and that is deliberate

Indirection through a local is undecidable without dataflow analysis. The first
design said it "searches engine code for a branch on it", which reads as coverage
it cannot have.

**A gate that catches only naive violations while announcing the rule enforced is
worse than no gate**, because it converts "be careful here" into "the check
passed". So the known blind spots are listed in the check's own failure output, and
the rule stays in §10.1.2 as a design principle that a reviewer applies — the gate
enforces the enforceable part and says so.

#### BUILT 2026-09-18 as `property_ratchet.py` — 11 of 30, and one defect caught by reading the hits

`30 properties declared, 11 reached in a branch, across 55 modules.`
`--self-test`: 10/10 forms behave as documented. Gated by
`check_property_vocabulary_has_not_grown` (157 checks now).

| property | sites |
|---|---|
| `id` | 23 |
| `max` | 9 |
| `credit` | 5 |
| `handout` | 4 |
| `question`, `cadence`, `cover`, `deductions`, `equals`, `expected_type`, … | 1–2 each |

##### It matched the NAME, not the property — 11 of 44 hits were noise

The first version matched attribute access as well as subscripts, and **every
attribute hit was a false positive**: `args.handout` (7 sites — an argparse flag,
not an item) and `node.value.id` / `t.id` (4 sites — Python's own AST API, where
`.id` is a `Name` node's identifier). A quarter of the measurement was the check
matching a *name*.

That is not a cosmetic error in a ratchet. **Baselining noise lets real growth
hide inside its churn**: a genuinely new property branch could arrive while an
argparse flag was renamed away, and the count would not move.

The fix is a rule with a premise rather than a convenience: **subscripts only,
because `coursedata` returns dicts.** `items()` and `rubric_for()` hand back
`_group(...)`, a dict copy, so a course property is read as `item["credit"]` and
never as `item.credit`. `premise_holds()` checks that on every run and REFUSES if
the reader ever starts returning objects — at which point attribute access
becomes how properties are read and this check would have gone silently blind.

##### The self-test asserts the blind spots too

Ten forms, including **two that must NOT fire**: `n = c["boxes"]` (an assignment
is not a branch) and `n = c["boxes"]; if n == 8:` (indirection through a local).
A check that quietly caught the second would mean the docstring's claim of
narrowness is wrong — so the blind spot is tested as a blind spot, and the three
known ones are printed with every failure.

#### Its self-test cases exercise what it claims

Per §12.0 and T0.1, each case constructs its own condition and exercises a form the
check CLAIMS to catch — comparison, truthiness, negation, subscript. A case using
only the `==` form would pass while the check stayed blind to the others, which is
the vacancy T0.1 exists to prevent, one level up.

### T5.1 · `rubric_equivalence.py` — the JSON reproduces the modules — STAGE 5

*Revised on review, 2026-09-18: four objections, one of them a contradiction
between this design's stated purpose and its stated mechanism.*

**What it does.** Loads `ITEMS` from `rubric_h{1,2,3}.py`, loads
`courses/<id>/course.json` **directly with `json.load`**, and asserts the authored
fields match in T2.1's canonical form.

#### It must NOT read through `coursedata.py` — the first draft did, and that broke its own purpose

The design says this tool compares DATA against the modules while T3.2 compares the
READER against the modules, "because a reader bug and an export bug produce the same
symptom, and the two proofs separate them" — and then specified loading the JSON
*via `coursedata.py`*.

**That defeats the separation entirely.** Both tools would run through the reader, a
reader bug would fail both identically, and the thing the second proof exists to
isolate would be invisible. The JSON is loaded directly. No reader.

*(This is the same class of error as an accessor returning a raw entry: a stated
boundary and an implementation that quietly disagree with each other.)*

#### Deep equality is impossible, because A2a removes fields ON PURPOSE

The JSON omits derived values by decision, so module `ITEMS` and JSON items will
differ — the modules carry fields the file does not. A "deep equality" assertion
would fail on every item for a designed reason.

Recomputing the missing values here would mean either duplicating the reader's
derivation rules (which drift) or calling the reader (which is objection 1). So the
scopes are split and do not overlap:

* **T5.1 compares the AUTHORED fields**, JSON against modules, directly.
* **T3.2 covers the DERIVED values**, through the reader, where the derivation
  rules actually live.

Between them every field is proved once, by the tool that can prove it without
borrowing the thing under test.

#### It asserts T2.1's canonical form, not a looser normalisation

"Normalising only key order" would let it pass on data that is not byte-
reproducible, so a later re-export produces a diff nobody expects. It asserts
exactly what T2.1 emits: sorted keys within an entry, items in rubric order.

#### BUILT 2026-09-18 — equivalent, and proven capable of failing

`26 items, 333 item fields, 18 module-level authored values — EQUIVALENT.`

**A proof that passes on its first run is exactly when to distrust it**, so each
failure mode was induced on a copy of the file. All seven are caught, each naming
the path:

| induced | reported |
|---|---|
| an item deleted from the file | `item Q1: IN MODULE, ABSENT FROM FILE` |
| a changed scalar | `item Q1.max: module 5.0 != file 99.0` |
| a changed NESTED value | `item Q1.credit[0].pts: module 2.0 != file -1` |
| a field dropped from an item | `item Q1.guidance: ONLY IN MODULE -- the export lost it` |
| an authored value not carried | `h1 MAPS: IN MODULE, ABSENT FROM FILE` |
| a DERIVED value wrongly stored | `h1 TOTAL: stored ... A2a says do not store it` |
| an item in the file but not the modules | `item ZZ9: IN FILE, ABSENT FROM MODULES` |

The nested case is the one a shallow comparison would miss, and the "derived value
wrongly stored" case is the one that enforces A2a from the other direction — the
file must not carry what the reader rebuilds.

It names `DERIVED_BY_DESIGN` itself rather than importing the reader's
`DERIVATIONS`. That duplication is deliberate and is the point of the tool: this
proof must not borrow the thing it is proving the file against.

#### Not a per-commit check — an acceptance step and a pre-deletion gate

It imports all three rubric modules, which means RUNNING `rubric_h2`'s builders,
on every invocation. The gate already runs 149 checks and this answers a question
that changes only when the export or the modules change.

So it runs: at Stage 5 acceptance, and again as the gate immediately before the
modules are deleted. **Until they are deleted the modules are the oracle**, and the
last run of this tool is what licenses removing them.

### T7.1 · `goals_restructure.py` — make `GOALS.md` anchorable — STAGE 7

*Revised on review, 2026-09-18. The first draft rested on a FALSE PREMISE, found by
reading the parser rather than the plan.*

**Why.** §10.4.1: 9 headings across 16,516 lines. A pointer into an 1,800-line
section is a direction to go looking, not a reference.

#### The false premise: `goals.py` DOES parse headings

The first draft said the tool "moves and adds headings" while the machine-parsed
contract stays unchanged, and named that contract as the `ENTRY` regex
`^- \[([ x])\] ([A-Z]+)(\d+)\. (.*)$`.

**`goals.py` also parses `^## `.** `misfiled_series()` tracks the current section
from `## ` lines and checks each entry's label series against `SERIES_SECTION`,
reporting an entry filed under the wrong section. So:

* **adding a `##` heading changes SECTION MEMBERSHIP** for every entry beneath it —
  insert one mid-section and the entries after it are suddenly filed under a new
  name, and `misfiled_series()` fires on entries nobody moved;
* **the contract is `ENTRY` + `^## ` + `SERIES_SECTION`'s series-to-section map**,
  not the entry regex alone.

#### Therefore: new granularity is `###`, never `##`

`misfiled_series()` matches `^## ` only, so `###` sub-headings are invisible to it.
The nine top-level sections STAY AS THEY ARE, and the anchorable granularity
arrives beneath them.

That is a constraint on the result, not a preference: a restructuring that adds
`##` headings would be correct-looking and would break a check that has nothing to
do with it.

#### The proof is on (entry, section) PAIRS, not on entries or on return values

"All 112 entries parse identically" is necessary and weak — `ENTRY` captures state,
series, number and text, so an entry can keep all four while moving between
sections.

Equally, asserting `misfiled_series()` returns the same list is weak: it could
return empty before and after while entries moved, because the move happened to
stay consistent with `SERIES_SECTION`.

So the round-trip proof asserts **the (entry, section) pair for all 112 entries is
unchanged**, and separately that `check`, `next_label`, `misfiled_series` and
`stale_slot_claims` return identical results on the same corpus.

#### BUILT AND APPLIED 2026-09-19 — 112 anchors, and the net reverted it twice

`16,516 lines -> 16,761. 112 ### headings + 112 <!-- qc:LABEL --> anchors added.
6 ## sections unchanged. 245 lines inserted, 0 altered.` Idempotent: a second run
adds nothing. `goals.py` after: `check` 0, `misfiled_series` 0, `next_label` Q69.

Granularity is one heading per ENTRY, and the entry's own label is the anchor
name — it is already the stable alias G1c wants, so nothing had to be invented.

##### The tool reverted its own work twice, and was right both times

It writes, re-runs `goals.py`, and restores the original if any result moves.

1. **Headings carried the entry's bolded title** — which reads better and
   duplicated prose into the file. `stale_slot_claims()` scans open entries'
   prose for slot-level figures, so the duplication created new prose for it to
   read. Headings now carry **the label and nothing else**; the human-readable
   title is on the entry line immediately below, so only the duplication is lost.
2. **The net's own criterion was wrong.** After the fix it still reverted, and the
   diff showed why: 14 claims before, 14 after, with `GOALS.md:5747` become
   `GOALS.md:5856`. Inserting lines moves every line below them. What must not
   change is WHICH claims are reported, so line numbers are normalised and
   everything else compared exactly.

The second is the more useful lesson. **A net that fires is not the same as a net
that is right**, and the way to tell is to read what moved rather than to weaken
the net until it passes. Had I loosened the comparison at step 1, step 1's real
defect would have shipped.

##### What the round trip actually asserts

Four things, because the obvious three are each insufficient alone: every
`(entry, SECTION)` pair unchanged — an entry can keep state, series, number and
text while moving between sections; the `## ` count unchanged, since
`misfiled_series()` reads those; every original line still present **in order, as
a subsequence**, which is what "inserts only, never rewrites" means mechanically;
and `check`, `next_label`, `misfiled_series`, `stale_slot_claims` identical
modulo line numbers.

#### It places the anchors, because otherwise this is two passes

G1c needs `<!-- qc:NAME -->` on the sections a course file will reference. If this
tool only restructures, anchoring is a second pass over the same 16,516 lines by
someone who has to re-derive where the seams are.

**Output.** The restructured file with anchors placed, plus the round-trip proof
above.

**The failure it must not have.** Reflowing prose. It moves lines and adds headings
and anchors; it does not rewrite lines, because a diff that touches every line
cannot be reviewed — and this file is read by five modules and by people.

### T7.2 · the anchor gate — anchors as STABLE ALIASES — STAGE 7

*Revised on review, 2026-09-18. The first draft proposed a referencing scheme
alongside one that already exists and is maintained.*

#### What already exists, and why it is not enough

`guide.py` maintains NUMERIC SECTION LABELS on `QUALITY_CONTROL.md` — `## 0. The
order of operations`, `## 1. Fixture first` — with `headings()` parsing
`(label, title, hashes)`, `renumber()` deriving labels from document order and
rewriting both headings and citations, and `_cited_by()` scanning every `.py`,
`.md` and `.olx` for references.

That is a working, machine-checked citation mechanism over this exact file. The
`<!-- qc:NAME -->` convention proposed by G1c has **one instance, both halves in
this plan, six lines apart.**

**Two schemes over one file would be the worst outcome**: a section carrying both a
number and an anchor, `renumber()` maintaining one of them, references free to use
either, and no answer to which is authoritative when they disagree.

#### Why an anchor is still needed: `renumber()` rewrites labels

`renumber()` derives labels FROM DOCUMENT ORDER, so inserting a section renumbers
everything after it and every citation must be rewritten in the same pass. Inside
one repo that is fine — `_cited_by()` can find every citer and fix it.

It is NOT fine across directories. A course file in `courses/<id>/` pointing at the
general guide is a citer `renumber()` cannot see, so a renumber silently
invalidates pointers — and G1c's dangling check would then fire on work that was
correct when it was written.

#### The design: numbers for structure, anchors for cross-file references

* **Numeric labels stay** as the human-facing structure `guide.py` already
  maintains. In-file citations keep using them.
* **An anchor is added only to a section a course file actually references.** It is
  a stable alias, immune to renumbering.
* **`renumber()` must PRESERVE anchors** — it rewrites labels and citations today,
  and would otherwise destroy the aliases on its next run. This is the change most
  likely to be missed, because `renumber()` looks unrelated to anchoring.
* **Cross-file references use anchors, never numbers.**

The gate then means: a `see: qc:NAME` with no matching `qc:NAME` FAILS; an anchor
nothing points at WARNS, since an unused alias is a section someone thought was
general and no course needed. A deliberate orphan carries a declaration, never an
exemption list.

#### BUILT 2026-09-19 as `anchors.py`, gated — and two of its own rules were wrong first

`112 anchors across 1 prose file, 0 cross-file references, every reference
resolves.` Gated by `check_cross_file_anchors_resolve` (159 checks).

##### A citation form has to be writable ABOUT

Matching a bare `qc:NAME` made every sentence DESCRIBING the convention into a
live pointer. On its first run the gate failed on **this plan's own text** and on
the tool's own docstring. Requiring `see: qc:NAME` was not enough either, because
the plan specifies the form *using* the form — "a `see: qc:NAME` with no matching
anchor FAILS" is documentation, not a reference.

The resolution is the design's own: **citers are course files**, under
`courses/<id>/`. That is not a convenience — it is exactly the set `_cited_by()`
cannot see, which is the entire reason anchors exist. Scoping to it removes the
specification-text problem by construction rather than by exception.

##### A check satisfied by writing prose about the thing it checks

The renumber-safety check first grepped `guide.py` for `qc:` and reported that
renumbering had no anchor-preserving rule. **Adding a docstring to `renumber()`
made it pass.** Nothing about the code had changed.

What can be verified is not a promise about `renumber()` but **where the anchors
are**: every anchor sits on its own line, so a heading rewrite cannot reach one.
`anchors_are_renumber_safe()` checks that, and it demonstrably fires on an anchor
sharing a heading line. The property is now structural instead of promised, and
the promise is not needed.

##### Unused aliases are summarised, not listed

T7.1 anchors every GOALS.md entry so that any of them CAN be pointed at, which
makes "pointed at by nothing yet" the normal state until courses exist to do the
pointing. 112 identical warnings would bury the danglers that matter, so the
count is reported per file and only danglers fail.

#### The scope question: `guide.py` is built for ONE file

`HEAD`, `_cited_by` and `renumber` are all shaped around `QUALITY_CONTROL.md`. Goal
G covers four, and they are not alike: `GOALS.md` is parsed by a DIFFERENT module
whose heading sensitivity T7.1 had to discover, and `BACKLOG.md` and
`EQUIVALENCE.md` have their own structures.

So the work splits:

* **the anchor gate is its own check**, reading all four files, because it is one
  rule over four documents;
* **`guide.py` keeps its numbering job** for `QUALITY_CONTROL.md` and gains only
  the requirement to preserve anchors;
* generalising `guide.py`'s numbering to the other three is NOT part of this and
  should not be attempted while proving the anchor mechanism.

### T7.3 · `check_general_prose_has_no_course_vocabulary` — a check — STAGE 7

*Revised on review, 2026-09-18: four gaps, including a destination that did not
exist.*

**What it does.** Enforces F1's PRECONDITION: no course vocabulary appears in
general prose.

#### What counts as "general prose"

Defined, because after G's split the course halves are SUPPOSED to be full of
psychology and a gate that read them would fire on correct work:

* the GENERAL half of each of the four split files, and
* every module docstring outside `courses/`.

It therefore runs **after** Stage 7's split, not alongside it — before the split
there is no general half to check.

#### It enforces the precondition, not the decision

§10.3.2 sorts a sentence into *specification* (moves to the course file),
*incident* (moves to the changelog) or *split* (generic half stays). **A word list
cannot tell those apart.** This check says only "a course word appears here"; which
of the three remedies applies is a human decision.

Stated because the first draft read as though the check enforced F1. It enforces
the condition that makes F1 checkable, and the plan should not claim more.

#### `behaviour` must be phrased unambiguously — DECIDED

T1.1 excludes software-sense `behaviour` by WORD, not by sense. In a measurement
that is acceptable; in a GATE it is a false negative on the single most likely
course word to appear — "the student's target behaviour" would pass.

**So surviving uses must be unambiguous: `code behaviour`, `runtime behaviour`, a
function's behaviour.** A bare `behaviour` in general prose fails the check and is
rephrased. This costs a small rewording in ~35 places and removes a blind spot
that would otherwise sit exactly where the risk is highest.

#### BUILT 2026-09-19 as `prose_vocabulary.py`, with the changelog it required

`160 checks registered.` The changelog exists at
`courses/edu.memphis.psych/CHANGELOG.md`, created FIRST because this check
refuses to run without it — a gate that strips sentences while their destination
is undefined produces deletions, not moves.

The check is **inert until Stage 7's split, and says so**:

> `Stage 7's split has NOT run, so there is no general half to check. This is
> inert by design, not clean: GOALS.md carries no <!-- general --> marker ...`

That is the same shape T2.2 has, for the same reason: a check whose first real
exercise is a stage away is one nobody has watched work, so it is exercised now
on constructed input. Five controls, all behaving:

| input | verdict |
|---|---|
| "the student's target **behaviour** is recorded" | fails — unqualified |
| "the **parser's behaviour** is unchanged" | passes — software sense |
| "scores **handout** 1 item **Q4b**" | fails — `handout`, `q4b` |
| "the reader returns a copy of each entry" | passes |
| "**reinforcement** and **punishment** are scored" | fails |

The vocabulary is read FROM THE COURSE — item ids and label words out of
`course.json` — plus a small declared set of psychology terms. A hand-written
list would drift from the course it describes.

##### The changelog's rules, written before it has entries

Keep the date and the numbers, because a generic retelling loses the evidence
that made the sentence worth moving. Name the cell, item or slot, so the entry is
findable by someone looking at that cell. Say what was believed, what was true
and how the gap closed — an incident with no resolution is an open defect and
belongs in `GOALS.md`. One entry per incident, cross-referenced rather than
merged.

It lives under `courses/<course-id>/` because an incident in THIS course's
scoring is course-specific by construction: another course would have its own,
and the engine should carry neither.

#### The changelog is CREATED in Stage 7 — DECIDED

F1 sends incidents to "the project changelog". **No such file exists** — nothing in
the repo carries one and the plan named no path. A gate that strips sentences from
docstrings while their destination is undefined produces DELETIONS, not moves, and
the evidence in those sentences is the thing most worth keeping: *"Handout 1's
items were once reported as 12/14 and 14/15 while their denominators were 19 and
20"* is a recorded defect, not decoration.

So Stage 7 creates it, and it is a prerequisite of this check rather than a
consequence:

* it lives with the course material it describes (`courses/<id>/`), because an
  incident in this course's scoring is course-specific by construction;
* each entry keeps the date and the numbers, since a generic retelling loses the
  evidence;
* the generic half of a SPLIT sentence stays in the engine prose and the changelog
  carries the instance — per §10.3.2's split rule.

**No sentence is removed from general prose until the changelog exists to receive
it.**

### T8.1 · the fixture course — STAGE 8

*Revised on review, 2026-09-18. The first draft sized the fixture against the PSYCH
course's shapes, which is the criticism that rejected I1c, arriving by another
route.*

**Why.** I1a: the acceptance test for stage one. Sized by shape coverage, because
26 items produce 19 distinct key-shapes and a two-item fixture would cover 2.

#### The shapes come from the SCHEMA, not from the psych items

The "19 key-shapes" were derived by looking at which optional fields the 26 psych
items happen to use. **A fixture covering those 19 proves the engine handles
PSYCHOLOGY's shapes** — which is exactly why I1c (a fixture stripped from the psych
course) was rejected: it inherits the assumptions it exists to test. Sizing against
the same 19 arrives at the same failure by another route.

So coverage is measured against **what the SCHEMA declares the engine accepts**.
The difference between the two sets is itself a finding, and the fixture reports
both:

* a schema field **no psych item uses** is untested today, and the fixture is the
  first thing that exercises it;
* a psych shape **the schema cannot express** is a migration bug, found before the
  rubric modules are deleted rather than after.

#### A fixture is a course AND submissions AND gold

Items alone score nothing. Exercising `agreement.py`, the graders and the gold path
that C1b split into a second file requires invented **submissions** and an invented
**gold set** as well as the course.

That is materially more work than "generate a course file", and it is stated here
so Stage 8 is planned for what it is.

#### Invented gold must be DERIVABLE BY INSPECTION

Gold is what the scorer is measured against. Invented answers with invented scores
make every disagreement meaningless — a scorer bug and a badly-chosen gold row look
identical.

So the fixture's items carry scoring rules simple enough that **the correct score
is obvious to a reader**, and a disagreement is therefore unambiguously the
engine's fault. A fixture whose gold requires judgement has recreated the problem
the real corpus already has.

#### CHECKED IN, with the generator kept for deliberate regeneration

A generator that runs on every use drifts with the code it tests — the fixture
adapts to the bug and the test keeps passing. The same argument as A1c: the
expanded artifact is canonical and checked in, the generator is an authoring tool.

#### Scoreable WITHOUT live LLM calls

If fixture items carry `LLMAction` prompts, an end-to-end run costs real Azure
calls — the historical student simulation made 73+ per state, which is why it was
replaced by a fast variant.

**An acceptance test too expensive to run often becomes a test run once, at the
end** — which is the risk I2c already carries and should not have doubled. So the
fixture scores against stubbed or recorded responses by default, with the live-LLM
path a deliberate, occasional variant.

**What it must say out loud.** Which schema shapes it does NOT cover. A fixture
reporting full coverage while the schema has grown a field is the failure mode.

### T9.1 · the `MOLLY_*` rename — a fallback, a sed pass, and a check — STAGE 9

*Revised on review, 2026-09-18. Designed as a script; measuring the scope showed
the script is the trivial part and the real work is elsewhere.*

**Scope, measured 2026-09-18:** 16 files, 67 references — `COURSE_DATA` 48,
`COURSE_OUT` 18, and **`COURSE_MEDIA` 1**, which the first design did not know
existed. A pass that renames two of the three creates exactly the mixed vocabulary
it exists to prevent, and the single occurrence is the easiest to miss.

#### Part 1 — the fallback in `paths.py`, which is the actual deliverable

`COURSE_DATA` preferred; `COURSE_DATA` honoured when it is the only one set;
**a warning emitted ONCE PER PROCESS**, not per read — `paths.DATA` is read
constantly and a per-read warning produces thousands of lines that get filtered,
which is the same as no warning.

**This is the deliverable, not a transition courtesy**, because the variables live
where a repo-wide rename cannot reach: shells, runbooks, cron entries, and the
command lines of background jobs. Renaming 67 references in the repo does not
change a single one of those.

#### Part 2 — the rename itself is a `sed` pass with review

67 mechanical replacements across 16 files, every one visible in a diff. This does
not want a program. All three names go in ONE pass — `COURSE_DATA`, `COURSE_OUT`,
`COURSE_MEDIA` — so the repo never holds both vocabularies even briefly.

#### Part 3 — a check, so the old name cannot come back

Per §12.0: after the rename, a check fails on any new `MOLLY_*` in the repo.
Without it the old name returns by copy-paste from a runbook and nobody notices
until the fallback is removed — at which point the failure is an empty result, and
**empty results in this project look like clean passes.**

#### DONE 2026-09-19 — 79 replacements, one pass, fallback verified four ways

`MOLLY_DATA` → `COURSE_DATA`, `MOLLY_OUT` → `COURSE_OUT`, `MOLLY_MEDIA` →
`COURSE_MEDIA`. **79 replacements across 18 files in ONE pass**, so the repo never
held both vocabularies. Gated by `check_no_old_environment_names` (161 checks).

**The fallback, verified on all four combinations** rather than asserted:

| environment | result | warns |
|---|---|---|
| neither set | default `~/molly_data` | no |
| old name only | honoured | **yes** |
| new name only | used | no |
| both set | **new wins** | no |

The warning fires once per process by construction — `paths.DATA` is computed at
import — which is what the design asked for and what a per-read warning could
never deliver: thousands of filtered lines are the same as no warning.

One place still knows the old names and must: `paths._RENAMED`, the table that
honours them. It is declared in `OLD_ENV_NAMES_ALLOWED`, and the sed pass
rewrote it along with everything else before it was restored — a table whose job
is to remember the old name is exactly the thing a blanket rename destroys.

The check demonstrably fires: a probe file containing `export MOLLY_DATA=…` is
caught by name and path.

##### The vocabulary gate caught its own author

Re-tightening after the rename refused: `enforcement.py: 25 -> 26`. The new
embedding was the word *psychology* — in the docstring of
`check_general_prose_has_no_course_vocabulary` ("the course halves are supposed
to be full of psychology") and in `check_property_vocabulary_has_not_grown`
("the engine is psychology-shaped again in a new vocabulary").

**The check that forbids course vocabulary in general prose used course
vocabulary to explain itself**, and the ratchet noticed. Rephrased to
*course-shaped* and *full of course vocabulary*, which is what T7.3 asks of
everyone else and is more accurate besides: the point was never psychology
specifically.

`editguard` refused two attempts at that rephrasing before allowing it, both
times correctly. Declaring `prose:psychology` as removed was false — the word
survives elsewhere in the file — and a declaration that does not come true is
exactly what its stale-declaration rule is for.

#### The expiry needs a criterion, not a date

"Honoured for a declared period" expires the way §10.1.2's and D2d's sentences
would have: not at all. The fallback is removed when the WARNING HAS NOT FIRED in
normal use for a stated stretch of work — evidence that nothing is still setting
the old name — and not on a date that passes unnoticed.

### T10.1 / T10.2 · the `OVERRIDES.md` converters — G2c, AFTER STAGE 8

*Revised on review, 2026-09-18: five objections, three of them couplings found by
reading the file's consumers rather than the design.*

**What they do.** Convert the 48 MB `OVERRIDES.md` to appended JSONL, and render
JSONL back to a readable document on demand.

**The constraints from G2c, not negotiable:** the renderer lands BEFORE the old
file retires, so the audit record is never tool-only; the pre-commit gate's REFUSAL
logic is untouched — this changes how the record is WRITTEN, never what the gate
REFUSES; and if a step requires touching the refusal logic, the step stops.

#### `git log -p` is the audit trail, and same-commit staging must survive

`precommit_gate.py` states that the record is "STAGED INTO THE SAME COMMIT", so
`git log -p OVERRIDES.md` reads as the history of what the audit was told to
ignore. That is what makes the log evidence rather than a file.

JSONL improves it — one line per entry diffs better than a prose block — but the
staging behaviour is a property to PRESERVE explicitly, not a detail to
reimplement.

#### Three modules special-case this file, and conversion changes what they see

* `equivalence.py:1152` — `_SELFTEST_REPAIR_MAX = 4_000_000  # bytes; OVERRIDES.md
  is ~50MB`: the self-test's snapshot-and-repair net is bounded because of this
  file.
* `measured.py:3561` — globs `*.md` and excludes `OVERRIDES.md` BY NAME, with a
  comment that the exclusion exists because of a defect that check caught.

**After conversion a `.jsonl` is not matched by `*.md` at all**, so that exclusion
becomes silently redundant and the check's scope changes without anyone editing it.
A check written because of a defect must not have its scope changed by a file
rename happening elsewhere.

So the conversion carries an explicit pass over these three consumers, each
re-decided rather than left to fall out: the repair bound, the glob exclusion, and
any other reader the pass finds.

#### The converter needs a COUNT-PRESERVATION proof

257,216 lines of markdown written by an appender over months, in a format that has
probably drifted since the first entry, parsed by something written afterwards. A
converter can silently drop or merge entries and the result still looks like a log.

So: **entries in equals entries out**, and every original block reconstructable
from its record. The raw `.md` stays in git history — it will be there regardless —
and is the oracle for that proof.

#### G2c does not shrink the repository

The 48 MB remains in git history forever. Conversion stops the file GROWING as
markdown; it recovers nothing already committed. Stated so no one expects a size
win and is surprised.

#### The rendered document is NOT committed

Rendering to a committed file would leave the repo carrying both representations —
96 MB and two artifacts to keep in step, which is the state G2c exists to leave.
Render on demand, to a gitignored path.

