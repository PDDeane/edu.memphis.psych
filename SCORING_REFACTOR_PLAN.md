# Moving the course out of `scoring/` — a refactor plan

**Status: FIRST DRAFT, for discussion. Nothing here is decided and no code is to
be written yet.** The entry conditions in §1 are not close to met, and §4 lists
questions the rubric migration has to answer before parts of this can be settled
at all.

---

## 0 · The goal, in one sentence

`scoring/` should contain a scoring **engine** and no psychology: every fact
about this course, its handouts, its items and its rubric moves into a readable
JSON file that lives beside the rubric in the content directory, and every
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

## 1 · Entry conditions — hard, and none of them are met

No code is written for this refactor until **all** of the following hold. They
are listed in the order they can be satisfied.

1. **The re-sweep is finished.** Fifteen items; nine done at the time of
   writing, `1a` in flight, five behind it.
2. **The queued live self-test has run and reported clean**, with its tree
   checksum showing no residue. (There is an open defect here: a self-test run
   leaves `agreement.py` carrying an injected mutation. See §6-T3.)
3. **All current work is committed.**
4. **The rubric migration is complete** through its own stages and gates.
5. **The migration is committed.**

Condition 4 is not merely sequencing. Several decisions below cannot be taken
until the migration has settled how the rubric is read at all — see §4.

---

## 2 · The inventory — what actually has to move

Measured 2026-09-14 on the live tree, not estimated.

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

## 4 · Open decisions, several blocked on the migration

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

Each stage ends with a gate. The shape follows the migration's discipline: no
stage changes behaviour and shape at once, and every stage is verified against
a frozen baseline rather than by inspection.

### 5.1 · Stage A — widen the inventory and freeze a baseline
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

### 5.2 · Stage B — design the schema against the real content
Draft the JSON schema by fitting it to the *hardest* tables first
(`GOLD_DIVERGENCES`, `CORRECTED_GOLD`, `PROSE_ONLY_SLOTS`, `DESIGNED_TEXT`),
not the easiest. Decide the readability conventions and where each table's
rationale prose lands.
**Gate:** every classified table has a named home in the schema and a worked
example; no field is `TBD`; a person can read a sample file and say what it
means.

### 5.3 · Stage C — the reader, and dual-source verification
Build the metadata reader and have every consumer go through one accessor, with
a mode that reads **both** the old table and the new file and asserts they agree
— the migration's `dual` pattern, which is what caught its own gaps.
**Gate:** the reader reproduces every moved table exactly; `dual` runs the whole
suite with zero differences; the audit finding-set is unchanged.

### 5.4 · Stage D — move the tables, engine untouched
Emit the metadata file, flip the accessor to read it, delete the tables. One
group at a time, smallest first.
**Gate:** finding-set identical; no fingerprint moves except where a table is
genuinely inside a scorer's closure — and where it does move, the affected
columns are re-recorded.

### 5.5 · Stage E — `GOALS.md`
Convert to the `goals` key, port `goals.py` and the four other readers, and
**keep a human-editable path** and the ACTIVE line in `--preflight`.
**Gate:** all 112 entries round-trip; `check`, `next_label`, `misfiled_series`
and `stale_slot_claims` behave identically on the same corpus; a person can still
edit the active goal mid-task without tooling.

### 5.6 · Stage F — split `QUALITY_CONTROL.md` in two
Separate the general guide from a course guide. Give the GENERAL guide stable
anchors; move every course-specific passage into the course guide with a
reference back to the principle it applies; teach the nine readers to reach the
course guide through the rubric's metadata.
**Gate:** the general guide names no course, handout or item anywhere — checked
mechanically, the way the migration's C2 scan checks the engine; every anchor the
course guide names resolves; every reader gets its directives via the rubric it
was given; no reader has a hardcoded handout number; and both documents still
read start-to-finish as guides rather than as databases.


### 5.7 · Stage G — generalise the programs
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
