# One Rubric, Two Scorers

*lo-blocks · edu.memphis.psych · migration plan — rev. 2026-09-11*

Move the rubric out of Python and into the OLX as a **first-class rubric object**, generate each
item's prompt **at build time**, and keep the paper scorer honest as an independent second
implementation — without disturbing any part of the audit, enforcement and declaration machinery
that has grown up around the current arrangement.

> 70 `LLMAction`s · 23 sheet-bearing · **47 handcrafted** — 26 scored items · 3 handouts
> 3 scorer columns (olx, python, paper) + paper_opus
> 135 enforcement checks · 54 registered declaration tables · 44 modules in `scoring/`
> goal: provably byte-neutral prompts **and** provably unchanged enforcement

### Baseline numbers — re-derive, never quote from memory

Every figure below was re-measured on **2026-09-22** and each carries the command that reproduces it.
The audit rows moved for reasons that are NOT the migration: the 28 findings frozen at stage 00 were
scoring-agreement defects and the agreement work closed every one of them, while the history rewrite
added a concession ledger of references into the `.olx`. The two sets are nearly disjoint, so the
difference is not a regression and not migration drift -- see the freeze commit for the accounting.
They are the migration's control: stage 00 freezes them, and every later stage's gate is stated
against them. A stale number here is worse than no number, because a gate written against it
passes for the wrong reason.

| figure | value | how to re-derive |
|---|---|---|
| audit, undeclared | **45** | `python3 equivalence.py --enforcement \| grep UNDECLARED` |
| audit, raw finding set | **46** | `enforcement_audit()[0]` — the frozen set in `goldens/audit_baseline.json` |
| declared in `SCORING_DIVERGENCES` | 6 | same headline line |
| documented recording gaps | 3 | same headline line |
| `SELFTEST_EXPECTED` | **72** | `grep SELFTEST_EXPECTED equivalence.py` |
| enforcement checks | 172 | `grep -c '^def check_' enforcement.py` |
| registered declaration tables | 63 | `len(enforcement.DECLARATION_TABLES)` |
| `enforcement.py` lines | 13,351 | `wc -l enforcement.py` |

**The raw set and the headline differ, and gates must say which they mean.** The printed line
reports 27 UNDECLARED; `enforcement_audit()[0]` returns 32, because the selftest needs to see
findings the headline filters out — a case that blinds a check must be able to watch its finding
disappear. "Finding-set identical" in a stage gate means **the raw 32**, not the headline 27.

**Maintenance rule.** Any stage that changes what the audit reports — adding or retiring a check,
declaring or dropping a table entry, clearing a finding — **updates this table in the same
commit**, and says in the stage's own entry which figures moved and why. The same applies to
`SELFTEST_EXPECTED`, which is two-sided (C1): adding a case without raising it fails the gate, and
raising it without adding a case leaves slack a later loss can hide in. Measured on 2026-09-12:
three cases were added for the checks of that day and the constant went **66 → 69**.

---

## 0a · THE END STATE, decided 2026-09-22

The rubric lives IN the content, as a `<Rubric>` component the course links beside
the three handouts:

```
<Course id="bmod_course" title="Behaviour Modification" launchable="course">
  <Use ref="bmod_rubric"/>
  <Use ref="bmod_handout1"/>
  <Use ref="bmod_handout2"/>
  <Use ref="bmod_handout3"/>
</Course>
```

`bmod_rubric.olx` is GENERATED today and becomes HAND-AUTHORED, with handout 2's
four factories becoming `<ItemTemplate>` elements and the Python builders retiring.
Generation is scaffolding; `check_the_rubric_component_is_current` retires in the
same commit that stops generating, and says so in its own docstring.

**What moves into the OLX.** The rubric and everything genuinely about it: items,
slots, credit, deductions, guidance, the scoring primitives, the per-handout
`authored` tables, and the criteria frame that is still inside `olx_prompts.py`.
The carried notes (`item_notes`, `handout_notes`, `item_note_runs`) become OLX
COMMENTS -- they were comments in the Python modules and were carried as data only
because there was nowhere else to put them, so they stop being data at all.

**What does NOT move, and why it is not an exception to the goal.** Three kinds of
thing survive as instrument configuration, because none of them is about this
course:

* **Measurement bookkeeping** -- `ASK_EQUIVALENT_PROMPTS` and its kin are
  `prompt_sha` and `ask_sha` values. They record THIS repository's measurement
  history. Copy the rubric to a new course and they are meaningless hashes.
* **Submission parsing** -- `SEGMENT_MARKERS`, `CONTEXT_REFS`, `TABLE_ORDER`
  describe the shape of the .docx students typed into, which is upstream of
  anything the rubric says. `segment.py` reads the markers long before a rubric is
  consulted, and two corrupted marker entries silently broke handout 2's box split
  on 2026-09-22.
* **Gold** -- the graders' scores live outside the repository on purpose.
  Declarations ABOUT gold may move; gold itself does not, and keeping that
  boundary visible is the point.

The residue has no course in it, which is the goal stated from the other side.

**Reading it.** `coursedata` keeps serving `config(h)["rubric"]`, so all 102 call
sites across 18 modules keep their spelling -- the channel is converted, not the
callers, exactly as when the modules went at Stage 5.

**CORRECTED 2026-09-22, after measuring.** This section said the reader takes the
build's staged, EXPANDED copy, on the reasoning that a reader which understood the
template grammar would be the second implementation expansion exists to prevent.
That reasoning still holds, but the staged copy cannot be the source: its corpus
references are RESOLVED, and `olx_prompts` writes this prose back into the shipped
`.olx`. Pointing `coursedata.items()` at it made all three handouts read OUT OF
DATE, and the diff was every `{{corpus:...}}` replaced by the span it protects --
which would have undone the scrub in a public repository, silently. So the reader
takes the AUTHORED file.

**The third artifact now EXISTS** (2026-09-22). `npm run build:expand-rubrics`
writes `.stage/expanded` -- templates expanded, `{{corpus:...}}` intact -- and
`coursedata` reads it through `rubric_component.expanded_path()`. Expansion runs
BEFORE resolution because expansion is structural and resolution textual; one
pass would make the only artifact that can safely be read the one that cannot
exist. It does not reformat: a file with no template is copied byte for byte, and
in a file with one, every unchanged element is emitted from its own SOURCE SPAN,
identified by the identity `materialiseRubric` preserves when it passes a node
through.

`check_the_expanded_rubric_is_current` watches the link, and REFUSES rather than
answers once an `<ItemTemplate>` appears: it compares bytes, exact only while
nothing expands, and would otherwise call every correct expansion stale. The
refusal is what makes the upgrade unavoidable instead of merely noted.

One staging rule, not two: `resolveCorpusRefs` already staged the MOUNTED
sources, so that loop was extracted as `stageSources()` and both steps call it.
Without it the new step saw 12 `.olx` instead of 44 and reported a clean zero --
which is what a tree with no templates also looks like.

**The consequence to accept.** Once that artifact exists, scoring depends on a
build having run -- today `score.py` needs no npm -- and a stale build silently
means a stale rubric, so it needs a freshness check with the same teeth as the
idmap's.

## 0b · Steps 3d and 4 — what inspection found before either was written

Both were inspected on 2026-09-22 while step 3c's certification ran. Each turned
out to be larger than its one-line description, and each carries a defect that is
harmless today and wrong the moment the step lands. Remediation is part of the
step, not follow-up work.

### Step 3d — delete the rubric fields from `course.json`

**It is 28 fields, not 30.** `RUBRIC_FIELDS` has 30 members and all 30 are on
`items[]`, but two must SURVIVE: `id`, the join key, and `handout`, which is
course structure the `<Item>` schema refuses and `handouts.config` selects on.
Deleting either breaks the join step 3c just built.

**Four readers do not follow the component and will go quiet, not loud:**

1. `coursedata.rubric_for(item_id)` still reads `_load()["items"]` through
   `_group(RUBRIC_FIELDS)`. After 3d it returns `{}` for every item, silently.
   It must follow `items()` to the component or be retired.
2. `coursedata.py`'s pool `_group(...)` at the same shape. Same fix.
3. `course_schema.py` declares `{"rubric": RUBRIC_FIELDS}`. With the fields gone
   these become "declared member that does not exist" -- CLEANUP findings, not
   violations. Either trim the declaration or expect the cleanup lines, but say
   which BEFORE the run, because a changed finding count that nobody predicted is
   indistinguishable from a regression.
4. `reader_equivalence.py` and `property_ratchet.py` both build comparison sets
   from `RUBRIC_FIELDS | GENERATOR_FIELDS`. Check each for vacuity: a comparison
   over an empty set passes.

**The fallback must RAISE, not return an empty list.** `items()` currently falls
back to the course file. Its own docstring says the fallback ceasing to find
anything "is the point at which the component is the only source". An empty
fallback is the vacuity trap this project has hit before -- prove the raise by
moving the `.olx` aside, not by reading the code.

**Retire in the same commit:** `rubric_export --olx`,
`check_the_rubric_component_is_current`, and
`check_the_component_reproduces_the_view` with `rubric_equivalence.py`'s course-file
read. That last one compares the component against `items[]`; after 3d there is
nothing on the course side to compare against, so leaving it PASSING would be
leaving a check that tests nothing.

### Step 4 — move the criteria prose into the rubric

**Half of it is already staged, and the direction is backwards.**
`<Frame name="oc_criteria">` is in the built rubric with three segments -- a base,
`ifDeclared="cadence_daily"` and `ifDeclared="cadence_weekly"` -- but
`rubric_olx.frame_text()` BUILDS them by calling `olx_prompts._criteria_section()`.
The prose still lives in Python and the `.olx` is derived from it.
`frame_text()`'s own docstring says what step 4 is: "When the prose moves out,
this function is what changes." So: the segments become authored text,
`_criteria_section` reads them back through `rubric_component`, and `rubric_olx`
stops emitting the Frame.

**A defect that is latent now and live the moment the reader flips.**
`_criteria_section` SUPPRESSES one sentence of criterion 7 when `avoidance_scores`
holds -- "This never changes the score; it flags the answer for a phrasing
comment. " The web call site passes it from the item; `frame_text()` does not pass
it at all, so every emitted segment is the `avoidance_scores=False` variant.
**DAY1 is `derive_from_criteria` AND `avoidance_scores=True`, the only one of the
eight**, so the shipped `oc_criteria` base does not reproduce DAY1's real prompt.
Harmless while nothing reads the frame. Wrong as soon as something does.

Remediation: that sentence becomes its own segment carrying
`ifDeclared="!avoidance_scores"`. Negation is implemented on both sides
(`itemTemplate.ts:77`, `promptAssembler.ts:319`), and `Segment`'s RAW text parser
preserves the leading space that joins it to the sentence in front -- which is the
reason that parser was chosen. Confirm the item declares `avoidance_scores` as a
CONDITION name: a segment matches `conditions=`, not an arbitrary rubric field.

**Two branches cannot move, and the decision must be explicit.** `score.py` passes
`trigger_slot` and `consequence_slot` derived from the CLI's ANSWER SHEET, not from
the item. `ifDeclared` matches names the ITEM declares, so side-conditioned prose
has no expression in a Frame. Either a second frame or those two stay in Python --
decide it in the open rather than letting the keyboard settle it. The CLI's
`_BOX_WORD.sub(_as_answer, ...)` post-transform is an adapter concern and stays.

**The web does not read the frame, and nothing here changes that.**
`promptAssembler.renderFrame` implements exactly this rule, but nothing builds its
`FrameSegment[]` from a parsed `<Frame>`, and `materialiseRubric.ts` -- the only
rubric-OLX consumer -- never touches Frame. Step 4's reader is the PYTHON one.
Written down so nobody later concludes the web already consumes it.

**Naming is settled: the attribute is `ifDeclared`, not `when`.** `Segment.ts`
records why -- `when` is a BASE attribute that gates RENDERING by expression, and
reusing it would make one attribute mean two things depending on the tag it sits
on. `renderFrame`'s `when` is an internal TS field name, not the OLX attribute.
(`Item.md` gets this wrong in the same table that miscalls `scores` as `ref`;
both are tracked in lo-blocks' `DOCUMENTATION_PLAN.md`.)

### What 3d actually turned out to be — three corrections to the above

1. **The builder would have put the fields back.** `rubric_export.build()` reads
   handout 2 from `rubric_h2_source.py`, which is still present, so a plain
   rebuild would have restored twelve items' worth of rubric silently and the
   deletion would have lasted until someone rebuilt. `build()` now projects every
   item to `id + handout + GENERATOR_FIELDS`. **This was not predicted here, and
   without it 3d does not hold.**
2. **`reader_equivalence` needed nothing.** `_modules_present()` looks for
   `rubric_h{h}.py` and only `rubric_h2_source.py` exists, so it has had no
   oracle since Stage 5: its `RUBRIC_FIELDS` use is dead, not vacuous.
3. **`RUBRIC_FIELDS` is kept WHOLE**, against the "trim it or expect the cleanup
   lines" above. Trimming would have shrunk `property_ratchet`'s scanning
   vocabulary and let real growth hide inside it. What made the cleanups zero is
   `course_schema` comparing against BOTH sides of the split.

### Step 4, measured — and one correction to the fix

Measured at the last moment the generator still existed (it retired in the 3d
commit): all three `oc_criteria` segments are byte-identical to what
`_criteria_section` returns -- base 2410, daily 1662, weekly 1665 -- and the
prefix split is still exact. **Step 4 may treat the shipped segments as
authoritative and need not re-render before authoring them.**

The fix above says the `avoidance_scores` sentence "becomes its own segment".
Measured, the split is **inside** the base segment rather than at its edge: 74
characters at offset 2248 of 2410. So the base becomes THREE segments --
`[0:2248]`, the 74 characters under `ifDeclared="!avoidance_scores"`, and
`[2322:2410]` -- and `Segment`'s RAW text parser is what makes that legal, since
the sentence carries its own trailing space and a trimming parser would close the
gap on both sides. That is the reason `Segment.ts` gives for choosing
`parsers.text.raw()`, and this is the sentence it was chosen for.

### A discipline note, written from getting it wrong

The first 3d certification was **VOID**: *"THE SOURCE MOVED UNDER THIS RUN --
changed: `coursedata.py`"*. The tree had been declared frozen and was then edited
forty minutes into a sixty-five minute run, so the baseline and the restored
state were never comparable and the 72/72 it printed certified nothing. **A
certifying run owns the tree until it returns.** Fingerprint before launching and
after finishing; "one small comment" is exactly the edit that reads as innocuous
and is not.

### OWED, and named as wrong: the derivation loop in `olx_prompts`

`SLOT_NOTES` moved into the rubric as `<Frame name="note:KEY">` and every prompt
stayed byte-identical. One thing did NOT move, and keeping it was a mistake worth
stating plainly rather than filing as a nicety:

```python
for _it in config(2)["rubric"].ITEMS:
    if _it.get("avoidance_scores"):
        SLOT_NOTES[f"{_it['id']}:consequence_asserted"] = (
            SLOT_NOTES["consequence_asserted"].replace(
                ", and it never changes the score", ""))
```

This DERIVES one piece of course text from another, in engine code. That is the
shape this migration exists to end, and it is no better for being five lines: the
text moved and the rule that edits the text stayed, which is a half-move, and a
half-move is the state most likely to be mistaken for a finished one.

**The fix needs nothing new.** The store is a `<Frame>`; frames carry conditional
segments; `ifDeclared="!avoidance_scores"` is already the mechanism `oc_criteria`
uses for the SAME suppression on criterion 7. The note becomes two segments and
the loop is deleted. The only real work is that the note lookup then needs the
item's conditions at read time, where today it needs nothing.

**Why it was not done in the same round.** It is a prompt-affecting edit and this
round is already one, and two unmeasured changes inside one certification cannot
be told apart afterwards. It is the FIRST thing after this round, not a backlog
entry.

### The same fix owes a second thing: `oc_criteria` RESTATES two notes

`<Frame name="oc_criteria">`'s `criterion_10_trigger` and criterion-11 segments
hold text that is also in `note:trigger_behavior` and `note:consequence_asserted`.
Before this round one was DERIVED from the other at import
(`_C10_TRIGGER = "10. ..." + _as_criterion(SLOT_NOTES["trigger_behavior"])`); now
both are literal, so the derivation was replaced by a copy.

It is better than it was -- both copies are course content in one file of record,
rather than one in a module and one in content -- but two copies of a rule are two
rules, and this file's own history says what happens next: they agree until one is
edited.

**The fix is the same shape as the loop's.** A segment should REFERENCE the note
store rather than restate it, which is what `@name` already means everywhere else
in this rubric. What makes it more than a rename is the transform: the criteria
form differs from the checklist form by `_as_criterion` (`\`yes\`` becomes `true`,
`evidence` becomes `behavior`) and by the numbering prefix, so the reference has
to carry that or the two forms have to converge. Decide which BEFORE writing it;
converging them is a prompt change and carrying the transform is not.

### Verification both steps share

* cold audit back to the frozen **45**, re-derived, never quoted from memory
* `enforcement_selftest` 72/72, 0 vacuous
* `ask_sha` unchanged; `prompt_sha` moving is EXPECTED wherever a tag changed
* for 3d, prove the missing-component raise by moving the file aside
* for 4, DAY1's prompt reproduced exactly, with the sentence suppressed


## 0 · What changed since the first draft

The original plan (2026-08-14, executed: none of it) described a codebase that no longer exists in
the relevant respects. Three changes matter enough to rewrite around.

**The audit complex did not exist and now dominates.** `enforcement.py` is 11,870 lines holding
135 `check_*` functions and 54 registered declaration tables, with gates in `precommit_gate.py`,
`editguard.py`, `leakage.py`, `probe.py`, `goals.py` and `sweep_gate.py`, and prose hook-ins to
`EQUIVALENCE.md`, `GOALS.md`, `QUALITY_CONTROL.md` and `OVERRIDES.md`. Measured coupling of those
135 checks:

| reads | checks |
|---|---|
| `olx_prompts` (notes, builders, registries) | 46 |
| the rubric modules (`rubric_hN.py`, `SLOT_SPEC`, `all_items`) | 31 |
| the `.olx` bytes (`_olx`, `prompt_sha`, section bounds) | 21 |
| the designed-text registry | 7 |
| recorded artifacts | 8 |
| **none of the above — safe by construction** | **62** |

*Re-measured 2026-09-13 over 135 checks (the table above previously read 54/29/20/9/6/53 over
125). A check may read more than one source, so the rows over-count; the union is what matters.
Per the §0 maintenance rule, any stage that adds or retires a check re-runs this.*

**RE-DERIVED 2026-09-14 BY SCRIPT, and the method needed two corrections. Run
`stage01_recount_coupling.py`; do not scan by hand.**

| source | **code** | text | 2026-09-13 |
|---|---|---|---|
| `olx_prompts` (notes, builders, registries) | **44** | 49 | 46 |
| the rubric modules (`rubric_hN.py`, `SLOT_SPEC`, `all_items`) | **30** | 32 | 31 |
| the `.olx` bytes (`_olx`, `prompt_sha`, section bounds) | **17** | 24 | 21 |
| the designed-text registry | **4** | 7 | 7 |
| recorded artifacts | **9** | 9 | 8 |
| **union — reads something this migration moves** | **69 of 140** | 76 of 140 | 73 of 135 |
| **union after correction 3 — what stage 01 actually dispositions** | **62 of 140** | — | — |

**Correction 1 — a needle in a comment is not a read.** Seven checks name a moving source only in
prose and touch none of it in code; `check_no_module_shadow_in_scratchpad` is one. Counting them
inflates the `.olx` row 17 → 24 and the designed-text row 7 → 4 the other way, which means the
2026-09-13 figures of 21 and 7 were almost certainly inflated the same way and **the migration's
real size has been over-stated since the first measurement**. The script now strips docstrings and
reports both numbers: the CODE union is what stage 01 dispositions, the TEXT union is kept beside
it so this series stays comparable rather than silently redefined. The seven are listed by name in
its output — a check that needs no disposition must be visible as such, or "not dispositioned"
hides among "not coupled", which is C1's failure one level up.

**Correction 2 — this instruction used to say "the needles named in each row", and never named
them.** They dominate the answer: the `.olx` row yields 0, 7, 12 or 24 depending on whether the
needle is `_olx(`, `_olx`, `_olx`+`prompt_sha`, or those plus `.olx`, and the rubric row yields 23,
32 or 60. The first re-derivation attempt used `_olx(`, matched **nothing**, and reported a
plausible-looking 7. A figure quoted without its needles is not a measurement, it is a preference.
The needles now live in `ROWS` in that script, calibrated against the 2026-09-13 row totals, and
may be changed only with the old and new figures printed side by side.

**Correction 3 — the `recorded artifacts` row does not belong in the union, and never did.** Its
five EXCLUSIVE members (`check_no_recorded_run_is_an_api_error`,
`check_no_recorded_run_is_verdictless`, `check_engines_encode_an_unrecorded_verdict_alike`,
`check_web_code_is_stamped_by_its_own_sha`, `check_scorer_neutrality_is_verified`) were each read
in full on 2026-09-14 and touch **nothing that moves** — no `rubric_h`, `SLOT_SPEC`, `BY_ID`,
`olx_prompts`, `_olx`, `prompt_sha`, `DESIGNED_TEXT`, `load_action` or `ACTION`. They read recorded
runs and stamps, and this migration moves neither; what moves is the sha VALUE stamped on them
(O3), which is not a source relocation. Two meta-checks go the same way:
`check_every_check_is_invoked` and `check_every_declaration_table_has_a_verifier` name
`olx_prompts` only as one entry in a hardcoded list of MODULES TO SCAN, and neither list names a
rubric module — so 06c's deletion cannot silently shrink their coverage.

Note the scope: only the row's **exclusive** members drop out. The four artifact-reading checks
that also read `.olx` bytes or `olx_prompts` stay coupled through that other source.

**Sixty-two of the 140 read something this migration moves.** That is the migration's real size;
the rubric data itself is the easy part. Three successive corrections — prose-only mentions,
unpinned needles, and this row — each made the number SMALLER (76 → 69 → 62), which is worth
stating plainly: the migration has been over-priced at every measurement so far, and the error has
always run the same way. A check with a re-point recorded against it that has nothing to re-point
is not a harmless over-count; it is a false entry in the record that the next reader believes.

**Prompts are now generated at build time, and must stay that way.** The first draft proposed
assembling at *render* time, and spent a risk section (R1) on the inspectability that would lose.
That is no longer a trade worth making: `prompt_sha` hashes the `.olx` section an item's grader is
served, and 20 checks plus the entire staleness machinery rest on the shipped bytes being readable
and hashable. **Build-time generation keeps every one of those working unchanged.** It also keeps
`olx_prompts.py --check` meaningful in exactly its present form: the generated `.olx` either
matches what the rubric would produce, or it does not.

**Prompt-source fingerprinting now spans three sides, not two.** `prompt_sha(item, side)` covers
`olx`, `python` (the `.olx` filtered to what `agreement.py` consumes) and, since 2026-09-10,
`paper`/`paper_opus` via `score.fingerprint_text` — the paper scorer's own constructed prompt.
Any change to how a prompt is produced moves a sha and stales a ledger column. The migration must
therefore land in a state where **every sha is either provably unchanged or deliberately re-swept**,
and never in a state where a sha moves silently.

---

## 1 · The five constraints

These are requirements, not preferences. Each has a gate in §7.

### C1 · The enforcement machinery must keep working at every step

Not "at the end" — at every step. A stage that leaves a check unable to run, or able to run but no
longer able to fire, is a failed stage even if the prompts are byte-identical. Two specific
failure modes are already on record in this codebase and both are silent:

- A check that reads a source that has moved returns `[]` and reports success. On 2026-09-10
  `check_mapped_slots_agree_with_their_map` reported the same count before and after a change,
  having read **zero** paper rows, because `slot_verdict` did not know the paper artifact shape.
- A declaration table whose entries no longer match anything becomes "half the table holding
  reverted attempts' designs of record, indistinguishable from live ones" —
  `check_every_designed_entry_ships`' own words.

So the gate is not "the audit is green". It is **"the audit examined what it claims to examine"**,
proven by the selftest's injected-breakage count and by per-source coverage assertions (§5).

The first draft called for "20/20 injected breakages" as a release gate. The mechanism has since
grown and hardened: `equivalence.SELFTEST_EXPECTED` is **66**, and it is **two-sided** — fewer
means a case was lost and the suite would report success at a smaller denominator; more means one
was added without raising the constant, "leaving slack a later loss can hide in". So the gate is
*exactly 66*, not *at least 66*, and raising it is a deliberate act with its own review.

Its own comment records that the figure is not yet from a measured run — a soft spot worth closing
before stage 00 freezes the baseline, since this number is the baseline.

### C2 · Nothing psychology-specific enters **lo-blocks** code or comments

The constraint is about the ENGINE REPOSITORY, not about OLX markup. "OLX" names two different
things and conflating them makes this rule read as nonsense, so to be explicit:

- **lo-blocks** — the engine: blocks, schemas, parsers, the assembler, tests, and their comments.
  **No psychology item, slot, handout, construct or participant may appear here**, in code or in
  prose. Where the engine needs an example, it uses a neutral one.
- **edu.memphis.psych** — the content, including every `.olx` file in `psychology/`, the new
  rubric object, the course, and the `scoring/` Python. **Psychology belongs here**, and the
  rubric object this plan introduces is psychology content living in the content repository. It
  is written in engine vocabulary, which is a different thing from being part of the engine.

The line is not "no domain words in files with an .olx extension". It is that a general-purpose
system must not learn the name of one course's items.

This cuts against the grain of the current Python, whose comments are dense with measured history
("Q3/p8 credited action_oriented while quoting…"). That history is among the most valuable prose
in the project — it is what stops a settled question being reopened a fifteenth time — and none of
it may follow the assembler into lo-blocks. It stays in `edu.memphis.psych`, beside the content it
describes: in the rubric object's own comments, in `scoring/`, or in `QUALITY_CONTROL.md`.
§6 gives the split rule and the check that enforces it.

### C3 · The rubric is an object, independent of items

The rubric holds what is shared: slot semantics, verdict vocabularies, deduction wordings,
guidance frames, the criteria prose that ten handout-2 screens draw on today via `_OC_FRAME` and
`_EXAMPLE_RULES`. Items **reference** it; they do not contain it. The build resolves each
reference into the item's generated prompt.

This is the point the first draft got closest to and still under-specified: it proposed
`<Rubric>` blocks *per item* with a `<RubricLibrary>` for the shared parts. Inverting that —
**one rubric object, items referencing into it** — matches how the data actually factors and
removes the question of which copy is authoritative.

### C4 · `LLMAction` stays backward compatible

**47 of the 70 `LLMAction`s in this repository are handcrafted prose with no sheet** — the
majority — and they must continue to run untouched. Compatibility is the common case here, not an
edge case. A rubric reference is **strictly opt-in**: absent one, an
`LLMAction` behaves exactly as today, byte for byte. The legacy path stays physically separate
rather than being expressed as "the rubric path with an empty rubric", because that is how a
guarantee becomes a bug.

Note the subtlety the first draft flagged and which still holds: a handcrafted prompt carrying
`slots=` gets **no** generated checklist today. The checklist belongs to the rubric path and must
never be inferred from the presence of `slots=`.

### C5 · A course object presents the three handouts, and holds the rubric

A new `<Course>` in `psychology/` presents handouts 1–3 as three successive assignments, and the
rubric object lives inside it. The pattern already exists — `psychology_sba_course.olx` declares
`<Course id="psych_course" title="…" launchable="course">` with `<Use ref="…"/>` children, and
`manifest.yaml` routes to it.

The course is the natural home for the rubric because the rubric's scope *is* the course: it spans
all three handouts, and no single handout owns it.

---

## 2 · The idea, restated

Today the prompt is prose generated by Python and written into the `.olx`. The rubric lives in
`rubric_hN.py`; `olx_prompts.py` assembles markdown and writes each `<LLMAction>` body.

After: the **rubric is content in the OLX**, and each item's prompt is generated from it **by the
build**. Python stops being the producer of rubric data and becomes a consumer of it, alongside
the engine.

The payoff is not tidiness. Today the web prompt is produced by the same Python that drives the
paper scorer, so web-versus-paper agreement partly measures one generator against itself. Give
each side its own assembler over one shared rubric and the comparison becomes what it was meant to
be: independent implementations of one rubric.

**What does *not* change:** the `.olx` still contains a readable, hashable, reviewable prompt for
every item. Build-time generation moves the *source* of those bytes, not their existence.

---

## 2a · One source, every scorer

**The rubric object is the single source of rubric data for all three scorers.** No scorer keeps
its own copy, and none reads `rubric_hN.py` after stage 06. This is the whole point of the
migration and it is easy to half-do, because two of the three columns are Python and it is
tempting to say "the Python reads the OLX" as though that settled both.

| column | program | how it gets rubric data | what it implements itself |
|---|---|---|---|
| `olx` | `agreement_app.py` → the shipped grader | the generated `.olx`: prompt body + sheet attributes, both produced by the build **from the rubric object** | slot-sheet parsing and scoring in TypeScript (`slotSheet.ts`) |
| `python` | `agreement.py` | the same generated `.olx`, filtered to what it consumes | the same sheet semantics re-implemented in Python |
| `paper` | `score.py` | the **rubric object directly** — it assembles its own prompt in its own words | prompt prose, response schema, scoring arithmetic |
| `paper_opus` | `score.py` on Opus | identical to `paper` | identical to `paper` — it is the same consumer on a different model, not a fourth reading of the data |

Two of those read the rubric *at one remove*, through the `.olx` the build generates from it.
That is still one source: the `.olx` is derived content, and `olx_prompts.py --check` is what
keeps it honest — the shipped bytes either are what the rubric produces or they are not.

**Share the data; keep the logic apart.** The paper scorer is a test instrument, not a product.
Sharing its logic would make the differential test circular; sharing the data is what makes a
disagreement *meaningful* rather than a transcription error.

| shared — exactly one copy | independent — deliberately |
|---|---|
| rubric data (the rubric object) | prompt prose and its assembly |
| slot and rule semantics (`primitives.json`) | scoring arithmetic |
| verdict vocabularies (`<Verdicts>`) | response-schema construction |

**What each comparison then measures**, which is worth stating because it changes:

- `olx` vs `python` — two implementations of the *same generated prompt and sheet*. Tests the rule
  engines and the arithmetic, not the prompt.
- `paper` vs either — two *assemblers* over one rubric. Tests prompt construction and judgement
  together, which is why paper-vs-web divergences this year have so often turned out to be
  translation defects rather than scoring defects.
- Neither comparison can see an error **in the rubric itself**. See §8.

---

## 3 · Data model

### 3.1 The rubric object

A non-rendering content object, using the `_Noop` renderer pattern that `createGrader` already
provides for blocks with no visual output.

```xml
<Rubric id="bmod_rubric" title="Behaviour-modification scoring rubric">

  <!-- Shared vocabulary: one definition, referenced by many items. -->
  <Verdicts name="met_absent_unclear" values="met|absent|unclear"/>
  <Verdicts name="antecedent_kind"
            values="before|unlinked|aftermath|not_doing|already_a_consequence|none"/>

  <!-- Shared prose frames. THIS ARGUMENT HAS GOT STRONGER: the first draft
       cited rubric_h2.py's 4 helpers, 21 f-strings and TWO shared constants.
       Measured today: 4 helpers, 22 f-strings, and TEN shared constants. A
       declarative form without a library mechanism would duplicate all ten.

       AND WHOLE-FRAME INCLUSION IS NOT ENOUGH -- measured 2026-09-14 on
       `_criteria_section`, the largest shared frame there is. It renders FOUR
       distinct blocks across the eight operant items:
         2,410 chars  criteria 1-7          PR, NR, PP, NP
         3,998 chars  + named_type, avoidance variant    DAY1
         4,075 chars  + named_type, cadence "ONE week"   WK1, WK2
         4,072 chars  + named_type, cadence "ONE day"    DAY2
       Two mechanisms produce all four: SELECTION (criteria 8-10 appear only for
       the items that declare a `cadence`) and PARAMETER SUBSTITUTION (WK1 and
       DAY2 differ by three characters -- "week" against "day", from the same
       `cadence`). So `use="@frame"` must be able to take PART of a frame and to
       fill a named parameter in it; a frame that can only be included whole
       would force four near-copies of a 2.4-4KB block.

       THE UNIT OF SELECTION IS A SEGMENT, NOT A CLAUSE -- corrected 2026-09-14,
       having first been written as "clause selection", which is too coarse to
       express what is actually there. Criterion 7 varies by a SENTENCE SPLICED
       INSIDE IT: on every item but DAY1 it reads "...rather than by what is
       added or removed after it. THIS NEVER CHANGES THE SCORE; IT FLAGS THE
       ANSWER FOR A PHRASING COMMENT. It is the ONLY criterion that judges this
       phrasing...", and on DAY1 the middle sentence is suppressed because there
       the reading GATES the item and saying it never changes the score would
       contradict the guidance. A clause-level mechanism cannot express that
       without storing two copies of criterion 7.

       So a frame is an ordered list of SEGMENTS; each may carry a `cond` and may
       contain `{param}` placeholders; segments concatenate. Clause-level
       selection is then the special case where a segment happens to be a whole
       clause, and no second copy of anything is needed.

       SEGMENTS MUST PRESERVE WHITESPACE, and the default text parser does not.
       A spliced segment joins the sentences either side of it with a leading
       space -- "...after it. THIS NEVER CHANGES THE SCORE. It is the ONLY..." --
       and `parsers.text()` trims, which closes the gap invisibly and makes
       byte-exact prose impossible. `<Segment>` uses `parsers.text.raw()`.
       Measured 2026-09-14: the test for it failed before the parser was changed
       and passes after, which is the only reason anyone would know.

       SIX MECHANISMS EXIST; THE WEB USES THREE. `_criteria_section` also takes
       `trigger_slot` and `consequence_slot`, which vary criterion 10 and append
       criterion 11 -- and `build_web_prompt` passes NEITHER. They exist because
       the CLI collects a different ANSWER SHEET (it asks `trigger_behavior`
       where the web asks `targets_own_behavior`, and carries
       `consequence_asserted` as an eleventh criterion rather than a checklist
       slot). Stage 02 therefore needs base + avoidance + cadence only; the other
       two become live at stage 06, when score.py moves onto the same assembler.
       A frame design that covers only what the web needs would block that stage,
       so it is stated here rather than discovered there. -->

       THE COST OF GETTING THIS WRONG IS ALREADY ON THE RECORD. `score.py` used
       to hold a hand-kept "verbatim" copy of this block and it had DRIFTED IN
       THREE PLACES -- criterion 5's example, criterion 7's example, criterion
       10's WK1 rule -- which is why score.py now calls the generator instead of
       holding a second copy. Two copies of a rule are two rules. A migration
       whose purpose is single-sourcing must not emit eight of them.
  <Frame name="oc_criteria"> … </Frame>
  <Frame name="example_rules"> … </Frame>

  <!-- Shared deduction wordings, canonical and quoted verbatim in feedback. -->
  <Deduction code="A_MISMATCH" pts="1.25"> … </Deduction>

  <!-- ITEM TEMPLATES, measured 2026-09-14 and a larger problem than the
       shared prose above. Handout 2 builds TWELVE items from FOUR helpers --
       648 lines producing 12 items -- and the pairs are 92-100% identical once
       serialised. Expanding them literally puts ~86KB of near-duplicate content
       in the rubric, where one shared sentence then needs twelve edits.

       A PROSE mechanism does not cover them. The parameterisation reaches
       STRUCTURE: of the four pairs, three differ in their SLOT KEYS and one in a
       CREDIT key derived from the parameter (`is_pr` against `is_nr`).
       `<Frame>` varies words; this varies what the sheet asks.

       WHERE IT LIVES, and why "lo-blocks" alone is the wrong answer: the
       mechanism is content-neutral so the block type belongs in the engine, but
       EXPANSION MUST BE MATERIALISED BY THE BUILD into literal `<Item>`s in the
       generated `.olx`. `agreement.load_action` parses that file with its own
       regexes, so a template surviving into what Python reads would force a
       SECOND expander. Expanded, the duplication lives in DERIVED content, which
       §2a already treats as honest, while the authored source stays four
       templates. See §11.2.

AUTHORING IT FOUND FIVE THINGS THE SKETCH ABOVE DOES NOT SAY, all
       measured 2026-09-14 while making one item byte-equal:

       * A SHEET SLOT IS NOT A CREDIT LINE. PR has ELEVEN slots and TWO credit
         entries; the other nine are answered and feed rules without scoring
         directly. `<Slot>` therefore carries the whole sheet, and the ones with
         `pts` become the credit components.
       * `<Slot>` NEEDS `label`. Every real slot has one, and it is distinct
         from the judging description in the element's text: the label is shown
         to a learner, the description is read by whoever grades.
       * `<Guidance>` HAS TWO FORMS IN ONE BLOCK -- a literal line, and
         `use="@frame"` pulling in shared prose. Splitting them into two block
         types would make "guidance" mean two things depending on which tag an
         author reached for.
       * PROSE DOES NOT FIT IN AN ATTRIBUTE. `params="a=b|c=d"` produced
         679-character attributes carrying a 351-character question, which no
         reviewer can read in a diff -- and the grammar is delimited by `|` and
         `=`, which prose contains. `<Param name="...">` carries anything
         sentence-length; the attribute stays for identifiers.
       * ESCAPE TEXT MINIMALLY. Escaping apostrophes as `&#x27;` in ELEMENT TEXT
         leaves the entity literal in the assembled prompt -- 20 characters of
         difference on one item. Text needs `<`, `>` and `&`; quotes are an
         attribute concern.

       Per-item entries. The ITEM references this by id; the item's own OLX
       carries no rubric prose.

       `scores=` AND NOT `ref=`. This sketch said `ref` until 2026-09-14, when
       authoring the block found that the platform RESERVES it: parseOLX refuses
       `ref` on anything but `<Use>` -- "Invalid 'ref' attribute on <Item>. Only
       <Use> elements may have 'ref'." The reserved word is the natural one to
       reach for, which is exactly why it is worth writing down.

       Four more reservations found the same way: `id` and `title` cannot be
       REDECLARED (they are base attributes and the factory raises a composition
       conflict rather than letting a layer win); `when` is taken -- it gates
       RENDERING by expression, so frame selection uses `ifDeclared=` instead;
       and `keys` is a RESERVED EXPRESSION-LANGUAGE KEYWORD, refused outright as
       an attribute name, so `<Cover>` names its checks `checks=`. One attribute
       meaning two things depending on the tag it sits on is the failure the
       third avoids, and `cond` is the case that proves it: it is REAL DATA on
       `<Onlyif>`, naming the check a charge depends on, so the template marker
       could not share the word. -->
  <Item scores="bmod_h1_q4a" max="5">
    <Question> … </Question>
    <Slot key="antecedent_kind_1" verdicts="@antecedent_kind" seg="pick(ant_kind)"/>
    <Slot key="antecedent_1" verdicts="met|absent|not_antecedent" pts="2">
      <Desc> … </Desc>
      <Rule> … </Rule>
    </Slot>
    <Map key="antecedent_1" pick="antecedent_kind_1"
         pairs="before~met,none~absent" fallback="not_antecedent"/>
    <Guidance use="@oc_criteria"/>
  </Item>

</Rubric>
```

Three properties matter:

- **Shared things are declared once** (`<Verdicts>`, `<Frame>`, `<Deduction>`) and referenced by
  name. This is the same problem `choices=` solved for categories, one level up.
- **An item's entry is a reference target, not a container.** The item's own OLX says
  `rubric="bmod_rubric"` and nothing more; the build looks the item up.
- **Nothing here is psychology-specific at the schema level.** `Verdicts`, `Frame`, `Deduction`,
  `Slot`, `Map` are engine vocabulary. `antecedent_kind` is content, and lives in content.

### 3.2 The item side

```xml
<LLMAction id="bmod_h1_q4a_grade" rubric="bmod_rubric" target="…"/>
```

No `slots=`, no `derived=`, no body: all of it resolved from the rubric at build. An `LLMAction`
with neither `rubric=` nor a body is an error, never an empty prompt (R3 below).

> **Unresolved against stage 05, and it is the whole budget.** No stage in §7 produces this compact
> tag: stage 05's gate is *"every `.olx` byte identical"* and its text says the `.olx` **still
> carries generated bodies and sheet attributes**. So either this is stale from the first draft or
> there is an unplanned tenth stage. It matters because `prompt_sha(item, "olx")` hashes the served
> tag ENTIRE — collapsing a tag moves every item's prompt sha, which T5 prices at ≈9,400 calls
> corpus-wide. **Decide this before stage 03**, not at 05. If the compact form is wanted, it is
> affordable only with the demotion rule in §7a, and only if the ASK is provably unchanged.
>
> **STRUCK 2026-09-14.** The compact form above is a REJECTED ALTERNATIVE, kept so the price is
> findable rather than re-proposed. The `.olx` keeps generated bodies and sheet attributes; the
> rubric is the source of those bytes, not their runtime container. Measured before deciding:
> 23/23 bodies byte-equal from the rubric, prompt oracles unchanged across 26 items on both
> sides, no `prompt_sha` moved, zero calls. **See §11.9.**

### 3.3 The course

```xml
<Course id="bmod_course" title="Behaviour Modification" launchable="course">
  <Use ref="bmod_rubric"/>
  <Use ref="bmod_handout1"/>
  <Use ref="bmod_handout2"/>
  <Use ref="bmod_handout3"/>
</Course>
```

Lives in `psychology/` beside the handouts, routed from `manifest.yaml`. The rubric is a child of
the course because its scope is the course.

**DECIDED 2026-09-13 (§11.1): a course child**, exactly as drawn above.

**And "a child" means `<Use ref="..."/>`, which needs a RENDER-TIME filter.**
Measured 2026-09-14. A course turns every loose child into a navigation entry, so
a rubric inside one appears in the learner's sidebar as an empty page. Filtering
it in the PARSER does not work: the parser sees the tag `Use`, and cannot know
what the reference points at because the target may live in a file not yet
parsed. Authoring the course with `<Use ref="bmod_rubric"/>` produced four nav
entries; only inlining `<Rubric>` as a literal child produced three.

So the filter belongs at render, where the reference is resolved and the block's
own `internal` flag can be read -- `_Course.tsx` drops internal blocks from
`visibleIds`, the predicate the course already used for `when=`. That covers
every non-rendering block rather than a hardcoded list of tags, and it is why
both `<Use ref>` and an inline child now behave the same. A referenced sibling
would let two courses share a rubric; nothing in the current content needs that, and the reversal
touches no `<LLMAction>` tag so it owes no sweep.

### 3.4 Named givens in exemplars

Q6's exemplars today carry fields literally named `four_a` and `four_c` — this course's assignment
structure baked into a schema. `<Given name="…"/>` keyed off the item's declared `context` fixes
the parochialism **and** buys a check that does not exist today: an exemplar supplying an
undeclared given, or omitting a declared one, is showing the model a different shape than it will
get at run time. That becomes an error.

---

## 4 · Proof obligations

Four oracles. The first three are the original plan's and still hold; the fourth is new and is the
one C1 turns on.

| Oracle | Asserts |
|---|---|
| **Web prompt bytes** | The generated `.olx` bodies are byte-identical to today's, for every item that gains a rubric *and* every handcrafted action that does not. |
| **Paper prompt bytes** | `score.fingerprint_text(item)` is unchanged for all 26 items. Changing where data comes from must not change what the paper scorer asks. |
| **Corpus replay** | Re-scoring a frozen run yields identical scores — exercising segmentation, prompt, schema and arithmetic end to end. Known achievable: a fresh `score.py` has already matched a stored run exactly. |
| **Enforcement neutrality** | Every one of the checks returns *the same findings* before and after — compared as the RAW finding set (§0), not the printed headline — **and** the selftest's injected-breakage count does not fall. The count is re-measured per stage, never quoted from this document. |

The fourth deserves emphasis because it is the one that can pass falsely. A check that has lost
its source returns `[]`, which looks like success. So enforcement neutrality is asserted two ways:

1. **Finding-set equality** — the audit's full output, diffed. Not a count: the same findings.
2. **Coverage assertions** — for each of the five source categories in §0, a check that the
   audit actually read a non-zero number of rows from it. This is the generalisation of the bug
   found on 2026-09-10, where a guard reported findings while reading zero paper rows.

**If all four hold, the migration provably alters neither what any model is asked nor what any
check can detect.** The acceptance sweep then confirms a proof rather than supplying it.

---

## 5 · What the enforcement machinery needs, concretely

### 5.1 The coupled checks — 62 of 140 as of 2026-09-14 (code-only, artifact row
and meta-checks excluded; 69 before that correction, 76 by the older text scan — see §0)

Each check that reads a moving source needs a disposition recorded *before* its source moves. Three dispositions, and the choice is per check, not per category:

- **Re-point** — the check's question is unchanged, only its source moves. Most of the 54
  `olx_prompts` readers are here: `SLOT_NOTES` becomes a rubric lookup, `build_web_prompt`
  becomes the build's assembler.
- **Re-express** — the question survives but its shape changes. `check_rubric_slots_reach_the_sheet`
  compares a Python structure against a sheet attribute; after the move both sides come from the
  rubric, and the check must be re-aimed at *rubric versus generated prompt* or it is testing a
  tautology.
- **Retire, declared** — the check tested a property of the old arrangement that no longer exists.
  Retirement requires an entry saying so, exactly as `ITEM_GATED_MECHANISMS` records retired
  entries with the reason each gave for itself.
- **Deferred to 03, with the criterion written down** — added 2026-09-14, because the first four
  checks that needed it were about to be guessed at. Some checks test a mistake **the Python
  arrangement can express**: `check_maps_tables_are_attached` ("defines MAPS and never hangs it on
  the item spec") is module-and-attach; `check_computed_rules_do_not_share_a_key` ("the second
  silently wins") is dict-overwrite; `check_one_writer_per_computed_key` and
  `check_rubric_items_are_unique` are the same shape. Whether each retires or re-points depends on
  whether the DECLARATIVE form can express the same mistake — and that is fixed by §3.1's rubric
  object in stage 03, which stage 01 runs before.

  **This is a real ordering constraint, not a loophole.** Stage 01's gate demands a disposition per
  coupled check while the information for these four does not yet exist, so the gate as originally
  written was unsatisfiable-in-honesty: it forced a coin-flip into a permanent record. A deferral
  is only valid when it names the **criterion** that will settle it — here, *can the declarative
  form express this mistake?* — so the judgement is recorded even though the answer is not.
  A deferral with no criterion is not a disposition, it is a blank.

A check silently returning `[]` because its source moved is none of these and is the failure C1
exists to prevent.

### 5.2 The declaration tables

61 tables in `enforcement.py` alone, plus `DESIGNED_TEXT` + `DESIGNED_TEXT_SHA.json`,
`DEFINITIONS.json` (43 modules), `CONSENSUS_FIXES`, `SCORING_DIVERGENCES`,
`SLOT_STRUCTURE_DIVERGENCES`, `GOLD_DIVERGENCES`, `ITEM_GATED_MECHANISMS`,
`PROMPT_CONVENTIONS_DECLARED`, `ITEM_NOTES_WHY` / `PAPER_ITEM_NOTES_WHY`.

Two hazards, both observed:

- **Key-shape drift.** `DESIGNED_TEXT` entries are keyed `(item, slot, field)`. If `field` names
  change with the data model, every entry silently stops matching and
  `check_every_designed_entry_ships` fires 100+ findings at once — or worse, matches something
  else. Migrate keys in the same commit as the data, with a one-off assertion that the entry count
  and the match count are both unchanged.
- **Slice edits eating neighbours.** `editguard.safe_write` refuses a write that drops a
  declaration without declaring it, and refused three edits on 2026-09-10 alone. Every migration
  script must write through it, and `DEFINITIONS.json` must be updated by `--accept` one name at
  a time — there is no bulk accept, deliberately.

### 5.3 The prose hook-ins

| file | readers | what breaks if the migration ignores it |
|---|---|---|
| `QUALITY_CONTROL.md` | 10 modules | procedure text keyed to slot/field names; `check_closure_ceilings_are_declared` reads closure prose |
| `GOALS.md` | 5 modules | subgoal citations (`CITE`) name items and slots; `goals.check()` validates them |
| `EQUIVALENCE.md` | 6 modules | the deviations register, and the new limit section in §8 |
| `OVERRIDES.md` | 2 modules | `ALLOW_UNDECLARED` records findings verbatim; format must stay parseable |

None of these are documentation in the passive sense — each is read by code. A rename that lands in
the data but not in the prose produces a check that cannot find its declaration.

### 5.4 The paper-side fingerprint

`score.fingerprint_text` hashes the system prompt, `build_prompt` with an empty response, and
`build_schema`. Every one of those inputs changes shape in stage 5. The fingerprint must be
updated in the same commit as the thing it fingerprints, and
`check_paper_prompt_is_stamped` must keep reading 0 — including its arm asserting that no paper
sha equals its olx sha, which is what caught the paper side borrowing the web's stamp.

---

## 6 · Keeping the engine content-neutral (C2)

**The split rule.** A statement belongs in lo-blocks if it would still be true for a different
course; otherwise it belongs in `edu.memphis.psych`.

- Engine: "a `<Map>` sends a pick value to a verdict; an unmatched value takes the fallback."
- Content: "`antecedent_1` maps from `antecedent_kind_1`, and p18 picks `before` where the web
  picks `none`."

**The measured history must survive the move.** Comments like the `action_oriented` bar's record
of four cells and two dead fix attempts are the most valuable prose in the project — they are what
stops the fifteenth attempt at a settled question. They move to the rubric object's own comments
in `psychology/`, or to `QUALITY_CONTROL.md`, never into lo-blocks.

**The check.** `check_engine_is_content_neutral` — scan lo-blocks source and comments for item
ids, slot keys, handout names and participant ids drawn from the live rubric, and fail on any hit.
Modelled on `check_engine_mechanisms_are_not_item_dependent`, which already parses modules with
`ast` rather than scanning text, after two of my own bugs showed that substring and word-boundary
tests both misfire — one matching `PAPER_ITEM_NOTES` as `ITEM_NOTES`, the other matching a comment
that merely *cited* a name.

---

## 7 · Sequence — nine stages, each with a gate

Stages 0–3 touch nothing live and are reversible. Stage 4 is the first change to shipped bytes.

### Ordering invariants — check any edit to this sequence against these

The stages are not merely a to-do list in a plausible order; four constraints stated elsewhere in
this document fix their relative order, and an edit that breaks one is a defect even if every gate
still reads sensibly.

- **O1 (T1) · engine before content, by a full stage.** The two repositories have no atomic
  commit. Any engine capability must be *accepted and ignored* for a full stage before content
  uses it. A stage that changes **lo-blocks** and **psychology/** together cannot land, and must
  be split into lettered sub-steps with the engine half first.
- **O2 (C1) · no check may read a source that has gone.** The dispositions for the coupled checks
  must be **applied before** the source they read is deleted, never after. A check whose source
  has vanished returns `[]` and reports success — C1's first named failure mode, and silent.
- **O3 (T2/T5) · a stage that moves a sha owns the clearing.** A `scorer_sha` move leaves every
  affected column `STALE SCORER`, which shows up as `ITEM UNMEASURED` findings — so a gate saying
  "audit finding-set identical" cannot be met until those columns are **re-recorded**. Re-record
  through `measured.safe_to_rerecord`, which refuses a column whose ASK moved.
- **O4 (§7a) · sweep, then retire.** Where a stage does spend a sweep, it owns the retirement of
  the artifacts that sweep supersedes; otherwise the all-artifact checks keep firing on evidence
  no sweep can reach.
- **O5 (§7b) · the engine's tests and docs are part of every stage that touches it.** A stage that
  changes a lo-blocks component is not finished when the suite is green: the suite must still be
  *asking the right questions*, and the component's documentation must still describe what it
  does. Both rot silently and neither is visible from the psych side. The stage gate records that
  the suite ran, that every block it added or changed has a current `.md`, and that no test it
  relies on is skipped. See "Passing is not the same as still correct".

**00 · Oracles, registry, and the enforcement baseline** — *no behaviour change*
Freeze all web prompt bodies and all 26 paper `fingerprint_text` values as golden. Capture the
audit's **full finding set** and the selftest's injected-breakage count. Add `rubric` to the
sheet-attribute registry.

> **Preserved for this stage.** `migration/stage00_*.py`. The dry run's goldens
> are in `migration/goldens/` — **for diffing, not for acceptance**: re-freeze
> from the current tree first (`DRIFT.md`, row A/B/C/E/G). Its final enforcement
> state is `goldens/audit_baseline.json` (28 findings) and its selftest sentinel
> is `$COURSE_DATA/migration_reference/.selftest-passed` (`114 detected, 0 failed`). Run
> **§11.13 must be decided before this stage freezes anything** — the seven
> `paths.OUT` fallbacks become part of the baseline on the day it is frozen.
> `migration/preflight.py` before anything: it refuses while the rubric still
> carries student text, and while any stage is unacknowledged against `DRIFT.md`.

Adding a sheet attribute is **four steps, not one**, and each is guarded by a different check —
measured 2026-09-12 while adding `free=`, which cost one finding per step missed:

1. `primitives.json` → `sheetAttributes`, which is what builds `KNOWN_ACTION_ATTRS`. Miss it and
   the audit reports `UNKNOWN ATTRIBUTE … if it changes enforcement, the audit is blind to it`.
2. The block's own zod schema in `LLMAction.ts`. Miss it and `ATTRIBUTE NOT DECLARED IN THE BLOCK`
   fires. These are two registries, in two repositories, and neither implies the other.
Both are **engine** changes, so by O1 they land in lo-blocks and are accepted-and-ignored for a
full stage before any `.olx` sets the attribute.

The remaining two steps are **content**, and they apply *only if* §3.2's compact tag is adopted —
the sequence as written never ships a `rubric=` attribute, because stage 05's gate keeps every
`.olx` byte identical. **Do not perform them until that open question is decided** (§3.2); if the
compact form is rejected they are never needed.

3. **Seed the attribute into every tag that will carry it** — *content, a later stage, never
   stage 00*. `olx_prompts --write` only *owns* an attribute that is already present: absent one
   it refuses with *"declares `rubric` in the rubric but `<LLMAction …>` has no `rubric=`
   attribute to write it into — add the attribute (any value) so the generator can own it"*.
   Seeding 26 tags is a hand edit to generated files, otherwise forbidden, so it takes its own
   reviewed commit.
4. **Land the §7a demotion rule before that seeding.** The moment a tag gains `rubric=`, that
   item's `prompt_sha` moves even though the assembled prompt and schema are byte-identical — the
   sha hashes the tag, not the ask. Without the demotion rule every seeded item is priced as
   `STALE PROMPT` at ~120 calls per side for a question that did not change.

**The five open decisions are closed HERE, not "early".** §11 called them "to take early", which
is not a gate and did not stop the sequence starting with them open. Each changes a later stage's
shape or its budget, and discovering that at the stage is the expensive way:

| decision | what it changes | if left open |
|---|---|---|
| §3.2 · compact tag vs byte-identical `.olx` | **the entire budget** | **CLOSED 2026-09-14: the compact form is STRUCK.** Byte-identical `.olx`, generated bodies retained, zero calls. See §11.9 |
| §11.2 · must paper run with no OLX present? | the target of stage 06 (bundle vs rubric object) | **CLOSED 2026-09-13: NO.** Stage 06 targets the rubric object directly; no export bundle is built, because a generated second copy is still a second copy |
| §11.3 · does `paper_opus` join acceptance? | whether 25 absent columns block the entry condition | **CLOSED 2026-09-13: NO, excluded and declared.** It would have cost ~3,000 calls to manufacture evidence that is non-comparable by construction; the entry condition falls from 36 columns to 10 |
| §11.1 · rubric as course child or sibling | `<Course>`'s shape in 3a | **CLOSED 2026-09-13: a course child.** Sharing across courses is given up; nothing needs it, and reversing costs no sweep |
| §11.4 · what the reference attribute is NAMED | the attribute added in stage 00 itself | **CLOSED 2026-09-13: `rubricDef`.** `rubric` was already taken by `LLMGrader` with an incompatible meaning; applying it would have baked the collision into both repositories |

**Entry condition, measured not assumed.** §7a requires every column freshly swept, reachable and
stamped. Run it and read the number: on 2026-09-13 **33 columns failed** — 25 `paper_opus` absent
(decision §11.3) and 8 carrying a moved prompt sha with no recorded `ask_sha`, which only a sweep
can stamp. Starting with these open means stage 05's "finding-set identical" is measured against a
ledger that was already incomplete.

**Land the one reconstruction helper (T11) before any stage re-reads a recorded cell.** The
artifact stores a counting group's NUMBER and a slot's JUDGEMENT in the same column, so five
separate readers each had to route by the slot spec and two of them got it wrong, silently, for
most of 2026-09-13. Introduce `rebuild_sheet(spec, checks, answers)`, point all five sites at it
(`mirror_self_control`, `_recorded_payloads`, `probe`, `check_computed_slot_recovery_is_faithful`,
`paper_scorer_agreement` — the last has two call sites), and add the check that refuses a
hand-built `{"verdict": …}` in a reconstruction path. This is a **pure refactor**: it must move
neither the audit's finding-set nor any `scorer_sha`, and both are checkable for nothing.

**Gate:** conformance test enumerates every consumer needing work; baseline finding-set committed
as the RAW set (§0); **the reconstruction helper is in place, all five sites call it, and the
refactor moved neither the finding-set nor any of the 104 `scorer_sha` pairs** (T11); **both
registries carry `rubric` and no content references it yet** (O1); the demotion rule is in place,
tested in all three directions, and its comparison recorded per item;
**all five decisions above are closed in writing**; **the entry condition reports zero failing
columns**, or the exceptions are declared with the decision that permits them; **O5's checklist
run and recorded** -- this stage edits `primitives.json` and `LLMAction`'s schema, so
`LLMAction.md`'s attribute list moves with them.

**01 · Disposition pass over the 62 coupled checks** — *no behaviour change, no code moved*
For each: re-point, re-express, or retire-with-declaration. Written down before anything moves.
**Recount before starting.** The figure moves with the tree — it was 72 of 125 on 2026-09-11 and
73 of 135 two days later, and 69 of 140 by script on 2026-09-14 once prose-only mentions stopped
counting — so stage 01 begins by re-running the §0 measurement, not by trusting
the number printed here. Four consumers landed on 2026-09-12 alone and each needs a disposition:

> **Preserved for this stage.** `migration/stage01_recount_coupling.py`,
> `stage01_gate.py`, golden `goldens/stage01_coupling.json`. **Recount — do not
> scale.** The dry run measured 73 of 135 and live now has more checks;
> `preflight.check_stage01_recounts_rather_than_scaling` refuses those numbers
> appearing as values.

- **`free=`** — a sheet attribute *and* a rubric field (`free` beside `codes` on a credit entry),
  carrying the verdicts a scored slot forgives. It is R9's shape exactly: stage 03b must decide
  whether the rubric object expresses it or it stays a declared exception. Note it is **declared,
  never inferred** — deriving it as "a verdict with no code" forgives a real failure wherever a
  code is keyed on a counterpart name.
- **`UNCHARGED_VERDICTS`** — a new declaration table, so R11's entry-count baseline moves.
- **`ask_sha`** — a new **recorded** fingerprint, stamped per column. Stage 00 freezes it with the
  other goldens, and stage 05's "all `prompt_sha` families unchanged" gate now has a fourth family
  to speak to.
- **Three new checks** — `A FAILING VERDICT NOTHING CHARGES`,
  `ENGINES PUT A DIFFERENT REQUEST ON THE WIRE`, `ENGINES READ ONE RESPONSE DIFFERENTLY` — each
  with a selftest case, which is why `SELFTEST_EXPECTED` is 69 and not 66.

**Gate:** the count re-measured and recorded in §0 **by script, both ways** (`code` and `text`);
every check in the CODE union has a disposition — **re-point, re-express, retire-declared, or
deferred-to-03 WITH ITS CRITERION** (§5.1); the uncoupled ones are listed as untouched, and so are
the prose-only ones — a check that needs no disposition must be visible as needing none.

**Stage 03 inherits the deferrals.** Its gate gains: *every check deferred by stage 01 is now
settled against the shape 03 fixed, and each settlement names the criterion it was judged by.* A
deferral that survives stage 03 is a defect, not a decision.

**02 · The assembler** — *no behaviour change*
Pure leaf module in lo-blocks, options object, no block or React imports — the discipline
`slotSheet.ts` already follows. Content-neutral by construction (C2), and measured to be so: no
generator branches on a literal item id (checked 2026-09-14 by `stage02_assembler_surface.py`).

> **Preserved for this stage, and it is the half that lives outside this repo.**
> The assembler itself is `$COURSE_DATA/migration_reference/engine/packages/shared/lib/llm/` —
> `promptAssembler.ts` (327 lines) + `.types.ts` (282) + test, `attributeAssembler`
> (222) + test, `materialiseRubric` (155) + `.md` + test, `itemTemplate` (141) +
> `.md` + test. **These exist nowhere else**: the dry-run lo-blocks was copied
> without `.git`. Verifiers: `migration/verify/*.ts` (their imports were absolute
> sandbox paths and are now `@/lib/...`). Goldens: `all26_inputs.json`,
> `attr_inputs.json`, `criteria_frame.json`, `criteria_slice.json`,
> `fragments.json`, `slice_2b_*`, `type_items.json`, `type_template.json`.

**IT ASSEMBLES BOTH HALVES — PROSE AND ATTRIBUTES.** §2a already says the build produces "prompt
body **and** sheet attributes, both produced from the rubric object", but this stage's gate used to
name only the bodies. Measured 2026-09-14: beside ~600 lines of prose assembly
(`build_web_prompt` 217, `_checklist_section` 199, `_criteria_section` 149) there are **13
`*_attr_for` generators totalling 320 lines** — `choices_attr_for` 105, `derived_attr_for` 39,
`slots_attr_for` 26, `max_attr_for` 25, `free_attr_for` 25, and eight smaller. Leaving them out
gave 320 lines of generation no stage and no gate, to be inherited by stage 05 and first tested by
its every-byte-identical gate — the most expensive possible place to find a porting error.

The asymmetry of consequence is the reason it cannot wait: **a wrong word in a prose fragment
changes a prompt; a wrong `max=` or `slots=` attribute changes SCORING, silently.** R5 is that
failure already recorded — `readChecks` dropped `expect`, it typechecked, and one item fell from
17/18 to 4/18.

**Its input is measured, not designed.** The rubric fields the generators actually read are
**16**: `id`, `max`, `question`, `credit`, `deductions`, `derive_from_criteria`, `context`,
`guidance`, `exemplars`, `cadence`, `avoidance_scores`, `reads_utb_choice`, `expect`, `forbid`,
`maps`, `gates` — plus slot `key` and `options`. The last four come only from the attribute
generators, which is why a body-only scan reported 12 and missed them. **That list is stage 03's
requirement**: a field read here and absent from §3.1's object is a hole the byte oracle finds
late and the expressiveness audit (R9) should find first.

**Gate:** reproduces all **23** generated bodies **and every generated sheet attribute on all 26
items** byte-exact from hand-built structures; **O5's checklist run and recorded** -- a new leaf
module needs its own tests, and mutation-testing them against a COPY is what shows they can fail.

**23 BODIES, NOT 26, AND THE TWO NUMBERS ARE BOTH RIGHT.** `T1`, `T2` and `1b` carry no
`<LLMAction>` -- they are scored deterministically from the fixture, with no prompt at all -- so
there are 23 bodies to reproduce and 26 items whose attributes must match. Stage 00 found the same
three when freezing the oracles (they have a paper `fingerprint_text` and no web body). A gate
demanding 26 bodies cannot be met, and the natural way to "fix" that is to quietly count 23 as
success, which is how a gate stops meaning anything.

**WHICH BYTES — the generator's output, not the element's text.** These are not the same string and
the difference is invisible until it is diffed. Measured 2026-09-14 on the 2b slice:
`build_web_prompt` returns 3,841 characters; the `<LLMAction>` body as stage 00 froze it is 3,842,
because the element text carries a **leading newline** from the XML, and a trailing one at the far
end. A gate read the other way makes every one of the 26 items fail by one character at each end,
for a reason that has nothing to do with the assembler.

So: **the assembler is compared against `build_web_prompt`'s return value**, and the `.olx`
surround is the writer's business, not the assembler's. Stage 00's `prompt_oracles.json` holds the
ELEMENT text, so a comparison against it must strip the surround first — or freeze the generator
output alongside, which is cheaper than remembering.

**Section separators belong to the join, not the section.** `build_web_prompt` accumulates parts
and joins them with `\n`, so the separator before a section exists only because the NEXT section
does. A partial assembler that stops early is short exactly one byte, and that byte is not a
defect. Compare whole bodies, or append a sentinel and cut at it.

**03 · The rubric object, the course, and the expressiveness audit** — *no behaviour change*
Two sub-steps, in this order, because the block types are **engine** and the rubric instance is
**content** — O1 forbids landing them together.

> **Preserved for this stage.** The whole rubric block family —
> `$COURSE_DATA/migration_reference/engine/packages/shared/components/blocks/rubric/`, **31 files**: Rubric,
> Item, Slot, Segment, Verdicts, Deduction, Credit, Counts, Cover, Equals,
> Expect, Forbid, Onlyif, Requires, Derived, Map, Frame, Param, Context,
> Guidance, Question, ItemTemplate, plus tests and `.md`. Also
> `Course.test.ts`, `Course.render.test.tsx`, and `engine_modified.patch` —
> **read it, do not apply it**: it mixes migration work with live drift and would
> revert live's corpus-reference build pipeline. `blockRegistryAutogen.ts`,
> `blockMetadataAutogen.json` and `pegExtensions.json` are GENERATED — regenerate
> them, or the new blocks are inert and say nothing about why (T12).
> `stage03b_gate.py` now runs `check_ref_grammars.py`, which is the only thing
> keeping the Python and TypeScript resolvers from drifting apart.

**3a · the block types (lo-blocks).** SIX new types -- `<Rubric>`, `<Verdicts>`, `<Frame>`,
`<Segment>`, `<Deduction>`, `<Item>` -- plus a change to the `<Course>` that ALREADY EXISTS.
Accepted and ignored: nothing in `psychology/` uses them yet, and the engine must tolerate that
for a full stage.

**`<Course>` IS NOT NEW, and this draft assumed it was.** `layout/Course/Course.ts` has shipped
for some time and live content uses it (`psychology_sba_course.olx`, `launchable="course"`).
Authoring a second one would have been a duplicate registration for one tag. What §11.1's "rubric
as a course child" actually needs is smaller and safer: the existing course parser turns every
loose child into a NAVIGATION entry, so a rubric placed inside one would appear in the learner's
sidebar as an empty page. The parser now skips non-rendering children -- parsed and registered, so
they still resolve, but never listed. `<Segment>` is the sixth type, and was not in this list
because the frame mechanism it belongs to was coarser when the list was written (see above).

*Optional cleanup, folded in here from the retired verdict plan (§12).* `countedVerdicts` still
reads `checks[g.key]?.count ?? checks[g.key]?.verdict`, a fallback for a legacy form no content
produces — the four remaining `counts=` groups recorded **0 non-numeric values in 480
observations**. Deleting the fallback belongs in **3a and not 3b** because it is engine code:
pairing it with content work is exactly the O1 violation these invariants exist to prevent. Skip
it freely; it costs a branch nothing takes.
**3b · the instance (psychology/).** The rubric object and the course, authored against 3a's
blocks. Inventory every computed construct in `rubric_h2.py` and decide, for each, *library
mechanism* or *declared exception that stays in Python*.
**Gate (3a):** every block PARSES a well-formed rubric and REFUSES a malformed one -- the second
half matters more, because a block that accepts anything validates nothing; no content references
them (O1); engine stays content-neutral (C2); the `<Course>` change is covered by tests that pin
BOTH the new behaviour and the old, since it is a block live content already uses; **O5's checklist
run and recorded** -- six new block types means six new `.md` files and their tests, per the
per-component convention every other block already follows. A block that ships without them starts
the debt this migration just finished paying off. **Gate (3b):** one item byte-equal, assembled from the rubric object; course renders three
assignments.

**04 · Migrate the rubric data** — *no behaviour change*
Scripted, idempotent, writing through `editguard.safe_write`, refusing to write unless every item
still assembles to its golden. Two copies exist and are asserted equal.
**Gate:** all 26 byte-equal; second run reports no edits; `DEFINITIONS.json` accepts are explicit.

> **Before quoting any student in the generated `.olx`, read
> `scoring/QUALITY_CONTROL.md` §6d** — the procedure, and why the answer is
> usually to invent the example instead. The migration writes a NEW public
> file from rubric prose, so this is the stage where the question arises.
>
> **Preserved for this stage.** `migration/stage04_migrate_rubric.py`,
> `stage04_gate.py`. The dry run's output is `$COURSE_DATA/migration_reference/olx/bmod_rubric.olx`,
> `bmod_rubric_pr.olx`, `bmod_course.olx` — **diff against them, do not install
> them**: the first two carry 47 and 3 distinctive student 4-grams because they
> predate corpus references. Scoring-side diff: `$COURSE_DATA/migration_reference/migration_changes.patch`
> (33 files, ~12k lines, includes deleting `rubric_h1/h2/h3.py`).
> **Re-freeze `goldens/prompt_oracles.json` first** — the `prompt_sha` slice now
> holds references, so every family differs from a pre-rewrite baseline because
> the REWRITE changed it, not the migration (`DRIFT.md`, stages 04/05).

**THE FIGURE IS 23 ASSEMBLED AND 26 READ.** `T1`, `T2` and `1b` have no
`<LLMAction>` and therefore no prompt body; the other 23 do. Stages 00, 02 and 03b
each measured the same split independently.

**`<Credit>` IS NOT `<Slot>`, and merging them is the trap this stage sets.**
They coincide on the item a slice is most likely to pick, which is how the first
model merged them. On the corpus they diverge twice over, measured 2026-09-14:

* **ELEVEN of twenty-six items list their credit in a different ORDER than their
  slots**, and the order is what the generated prompt renders.
* **FOUR items have credit whose keys are not slots at all** -- an item scored
  from declared criteria earns its points with no sheet line to hang them on. For
  those four, the slot order contains NONE of the credit keys.

Merged, the prompts listed the right components in the wrong order, which reads
as correct until it is diffed. A slot is a line on the ANSWER SHEET; a credit
component is a line in the SCORING.

**Two field shapes are not what their names suggest.** `codes` is a
verdict-to-code MAPPING (`{"absent": "UTB_NOT_STATED"}`), not a list: which
deduction is charged depends on HOW the check failed, and all 70 entries that
carry it are mappings. `gates` on a credit line is a BOOLEAN, and is a different
fact from `gate` on a slot -- the corpus carries both on the same slot.

**Cadence travels as `conditions` and `params`, never as a `cadence=`
attribute.** The engine selects frame segments by NAME and fills placeholders by
NAME; an attribute named for one subject's concept would put that concept in the
engine (C2). The rubric says which conditions hold and supplies the words; the
frame says where they go.

**What `DEFINITIONS.json` is checked FOR.** The gate fails on a listed definition
that has VANISHED, and merely REPORTS names present but unlisted -- 158 of them
on 2026-09-14, all predating this migration. Accepting them in bulk is what the
file's own README refuses: an inventory that agrees with whatever the tree says
enforces nothing. Accept one at a time, against the tree that actually has it --
two names were accepted here against the wrong tree and the guard caught it on
the next run.

**05 · The build generates from the rubric — this converts TWO columns** — *first change to how
bytes are produced*
`olx_prompts.py --write` reads the rubric object instead of `rubric_hN.py`. The `.olx` still
carries generated bodies and sheet attributes; `--check` still means "the shipped bytes are what
the rubric produces". Because `olx` and `python` both consume that `.olx`, this single stage moves
both of them onto the rubric object — at one remove, but from the one source. Neither program
changes; their input's provenance does.
**Gate:** every `.olx` byte identical · all three `prompt_sha` families unchanged · **every
affected column re-recorded** · audit finding-set identical · coverage assertions non-zero ·
**every spent `SCORER_NEUTRAL` pair re-pointed or dropped** · **every cache key audited against
the new source**.

> **Preserved for this stage.** `migration/stage05_complete_rubric.py`,
> `stage05_rubric_equivalence.py`, `stage05_gate.py`, golden
> `goldens/rubric_oracle.json`. Same re-freeze rule as 04;
> `preflight.check_oracles_were_refrozen_for_stages_04_05` enforces it.

The re-record is not optional bookkeeping: changing what `olx_prompts` reads moves `scorer_sha`
for every item, which leaves 26 columns per web side `STALE SCORER` and therefore 26+
`ITEM UNMEASURED` findings — so "finding-set identical" is unreachable until they are re-recorded
(O3). Zero calls, but it is work this stage owns. Drive it through
`measured.safe_to_rerecord(item, side)`, which refuses any column whose ASK moved: `record` stamps
the CURRENT shas onto whatever runs it finds, so re-recording a genuinely prompt-stale column
marks it fresh and destroys the evidence that a sweep was owed.

**MEASURED AT THE DRY RUN, 2026-09-14 — the last three clauses cost nothing, and
that is a finding, not an assumption.** Pointing `olx_prompts` at the rubric
object moved **no fingerprint at all**: `scorer_sha` is identical for all 26
items on all three sides, and so is `prompt_sha`. The reasoning above is sound
and its premise is wrong -- `scorer_sha` hashes the closure of the SCORING
roots and `prompt_sha` hashes the shipped tag, and **the generator is in
neither**. So no column goes `STALE SCORER`, no `ITEM UNMEASURED` follows, no
re-record is owed, and no `SCORER_NEUTRAL` pair is spent. The audit's raw
finding-set came back identical to the stage-00 baseline, 28 findings including
duplicates, with the two already-spent pairs unchanged.

Keep all three as CHECKS rather than deleting them: the expectation was
reasonable, and a future stage that puts the generator inside a fingerprint's
scope makes it true again. `stage05_gate.py` checks each one and names what it
measured.

*What the stage does cost* is the work below, which the plan did not anticipate
at all: the rubric object was **prompt-complete and not scorer-complete** (T15),
and completing it is most of the stage.

The original reasoning, kept because the checks exist to defend it:

The last two are this stage's own doing and neither is optional:

- Moving `scorer_sha` corpus-wide **spends every `SCORER_NEUTRAL` declaration at once**. Each is
  keyed on a *from*-sha; once no column sits at that sha the pair reads as coverage of a difference
  that is no longer there and `SCORER-NEUTRALITY CLAIM IS FALSE` fires for each. A far smaller
  change on 2026-09-12 produced **thirteen** such findings, which alone breaks "finding-set
  identical". Drop them in the same commit that moves the sha, naming each to `editguard`.
- Caches keyed on the OLD provenance serve stale answers silently. `_request_capture` keys on
  `web_code_sha("ask")`, the idmap and the `.olx` mtimes; once the rubric object is an input, a key
  that does not include it returns a capture taken against the previous source. Twice on
  2026-09-12 an incomplete key (`len(payloads)`; the sheets omitted) presented as *the app
  disagreeing with a rule it had never been given*.

  *Audited at the dry run, 2026-09-14, and the answer is "sound but not yet".* At stage 05 a
  rubric change can only reach the app **through** a handout `.olx`, whose mtime is already in
  the key, so no capture can go stale. The rubric files were added to the key anyway. The reason
  is the failure mode, not the present risk: an incomplete key does not fail, it serves a capture
  taken against the previous source, so the cost of adding it one stage early is one re-capture
  and the cost of adding it one stage late is a finding that reads as the app disagreeing with
  itself. It becomes genuinely load-bearing at the stage where the app reads the rubric directly
  rather than the generated body.

*Two things this stage needs on the way into live, neither of them obvious from the diff:*

- **A new module means explicit `DEFINITIONS.json` registrations.** `rubric_reader.py` adds 15
  names and `olx_prompts.py` adds 2 (`RUBRIC_SOURCE`, `_rubric`). Register those 17 and nothing
  else -- the ~158 unlisted names already in the tree are pre-existing drift and adopting them
  alongside is the bulk regenerate the inventory exists to prevent.
- **No block-registry regeneration is required, and T12 makes that worth saying out loud.** This
  stage adds ATTRIBUTES to `<Item>`, `<Cover>` and `<Slot>` and no new block types, so
  `blockRegistryAutogen.ts` does not move. T12's failure -- blocks silently inert until
  `npm run build:gen-block-registry` runs -- applies to new BLOCKS. An attribute is picked up from
  the block's own schema at import.

**06 · The paper scorer inverts, in three steps** — *runtime change*
This is the only column that reads the rubric object **directly**, because it assembles its own
prompt rather than consuming the generated one.
**6a** read both sources and assert equal · **6b** build from the rubric · **6c** delete the Python
rubric data. At no point is there one unverified copy. After 6c **no scorer holds rubric data of
its own** — the condition the whole migration exists to reach, and the point at which
`rubric_hN.py` can be deleted rather than merely bypassed.

> **Preserved for this stage.** `migration/products/selftest_injections.py`
> (the 28 injections — scanned clean, so it lives in this repo),
> `stage06_freeze_rubric_oracle.py`, `stage06b_*`, `stage06c_*`, and
> `$COURSE_DATA/migration_reference/pre_selftest/` — six modules whose bytes are in **no commit**
> (`enforcement.py` 13,381 lines, `equivalence.py`, `measured.py`,
> `olx_prompts.py`, `probe.py`, `sweep_gate.py`), the only record of what they
> looked like before this stage. Recompute `SELFTEST_EXPECTED` from the
> registered injections; the dry run's 114 was against 135 checks.

> **6c CANNOT PRECEDE THE DISPOSITIONS (O2).** Thirty checks read the rubric modules
> (`rubric_hN.py`, `SLOT_SPEC`, `all_items`) — the count is the prepared tool's
> (`stage01_recount_coupling.py`), not a hand scan, which said 42. Deleting them at 6c while stage
> 07 still holds the re-pointings leaves those checks reading a source that is gone — and a check
> whose source has vanished **returns `[]` and reports success**, which is C1's first named failure
> mode and is silent. The audit would go green *because* it had stopped looking.
>
> So the dispositions for the thirty rubric-reading checks are **applied in 6b, before the
> delete**, and stage 07 keeps only the prose rebase and the retirements that need no source.
> Equivalently: 6c's gate includes *"every check that read the deleted module now reads its
> replacement, and each was shown to still fire"* — shown by its selftest case, not by the audit
> being quiet.

**The surface, measured 2026-09-14 rather than estimated.** 06's first draft named the three steps
and no inventory, and the inventory is most of the stage.

*6a.* `config(h)["rubric"]` becomes the one accessor the paper scorer and all thirty
rubric-reading checks share, with three modes — `module`, `dual`, `object`. `dual` proves both
sources agree on first use and serves the module, so while both exist every run that touches a
rubric re-proves they still agree, in the process doing the work rather than in a check somebody
remembers to run. Mutation-test it: corrupt one field in the emitted rubric and the accessor must
refuse by name.

*6b.* Twenty-one direct-import sites bypass that accessor, splitting **20 data reads** — mechanical,
through a new `handouts.rubrics()` — and **1 source-text read**, `check_selectors_govern_something`,
which needs a disposition rather than a swap (§11.8). Four further facts no earlier inventory
carried:

* **`score.py`'s `from rubric_h2 import (...)` is MODULE-LEVEL** — six selectors plus
  `REQUIRED_MOVE` — so it fails at IMPORT, not at first use, and takes every consumer of `score.py`
  with it including those that never touch handout 2. An attribute-access scan does not see it at
  all (T26); count `from X import NAME` separately, and count module-level imports separately from
  function-local ones, because they fail differently and earlier.
* **`REQUIRED_MOVE` is keyed by `item["expected_type"]`, not by item id.** On this corpus the four
  items that have an `expected_type` are named after their own type, so a per-item table would be
  right by accident and wrong in principle. Emit it resolved THROUGH `expected_type`, keeping the
  indirection the scorer has.
* **`SHARED_GUIDANCE` replaces `rubric_h2._OC_FRAME`**, defined as the INTERSECTION of every item's
  guidance — measured, exactly one entry is common to all twelve, so the set operation finds it
  without anyone knowing which item or which position. Reading the enclosing frame instead hands
  its one reader 254 domain words where it wants 58, which is a weaker leakage gate that still
  passes.
* **`SLOT_OPTIONS` is reached by `getattr`**, so it appears in no attribute grep and was nearly
  missed. The rubric surface `olx_prompts` reads is four names — `BY_ID`, `ITEMS`, `SLOT_SPEC`,
  `SLOT_OPTIONS` — not three.

Anything 6b ADDS must be answerable from whichever source is being served, or `dual` stops being a
verification step and becomes a way to run half-migrated (T23).

**6b IS COMPLETE — gate met 2026-09-15**, on `migration/stage06b_gate.py`:

| row | result |
|---|---|
| no module reached as DATA outside the accessor (AST, not grep) | clean |
| no module reached as TEXT or by STRING import | clean |
| only `handouts.py` still imports them — that is 6c's step | `['handouts.py']` |
| selftest: every case constructed and detected | **86 detected, 0 failed, 0 skipped, 86 of 86** |
| audit RAW finding-set identical to the baseline | 28 findings, unchanged |

*Scripts saved off:* `migration/stage06b_gate.py` and
`migration/stage06b_validate_injections.py`.

*Two couplings were found only AFTER 6b had twice been certified complete by a
token scan*, and both are why the gate reads text rather than imports:
`olx_prompts.prior_record` read `rubric_hN.py` as TEXT (migrated to
`RUBRIC_DECISIONS.md`, T29), and `check_maps_tables_are_attached` reached the
modules by STRING through `__import__("rubric_h1")` inside a `try/except:
continue` — after 6c's delete that import would have raised, the `continue`
would have swallowed it for all three handouts, and the check would have
returned `[]` and reported success.

*6c.* The delete list is a decision in its own right and is **not yet written**; see §11.10.

**What 06 costs that 05 did not.** The paper `scorer_sha` genuinely moves here, because `score.py`
IS the paper scorer — unlike stage 05, where the same prediction proved false since the generator
sits inside no fingerprint's scope. Measured: **8 handout-2 columns**, `PR NR PP NP DAY1 DAY2 WK1
WK2`, from `06e0584b6ee7` to `6e5a50472f2b`, attributed by restoring the pre-edit file and
recomputing rather than by inference. All eight passed `safe_to_rerecord` on "prompt unchanged".
`fingerprint_text` stayed unchanged for all 26 and the audit finding-set stayed identical.

**Gate:** `fingerprint_text` unchanged for all 26 · corpus replay identical · no-rubric-constants
guard passes · `check_paper_prompt_is_stamped` still 0 · **every rubric-reading check re-pointed
and demonstrably still firing before 6c deletes anything** · **the eight paper columns re-recorded**
(O3 — 06 moves the paper `scorer_sha`; in live a genuine `--record` re-derivation, not a forged
stamp) · `paper_opus` inherits 06 with no work of its own, being the same program on a different
model.

---

**07 · Rebase the prose, and the dispositions that needed no live source** — *no behaviour change*
The dispositions for checks reading a **deleted** source were applied in 6b (O2); what remains here
is the rest of stage 01's list plus the prose. Add the EQUIVALENCE.md limit section (§8).

> **Preserved for this stage.** `migration/stage07_prose_mentions.py` — now
> strips corpus references BEFORE counting mentions, because a reference is a
> citation, not a claim about where a structure lives, and "rebasing" one would
> either resolve it or repoint it at the wrong cell. The dry run's decisions are
> in `$COURSE_DATA/migration_reference/products/RUBRIC_DECISIONS.md` (2,464 lines; outside this repo — 66
> distinctive student 4-grams).

Update `QUALITY_CONTROL.md` and `GOALS.md` where they name moved structures.

**AMENDED 2026-09-14 — re-derive §0's baseline-numbers table UNCONDITIONALLY, not "if this
migration changed what the audit reports".** Every figure this plan carries from the dry run came
from a ledger that declares its own freshness fabricated, and its own banner says nothing
downstream of it is evidence about the real corpus. The 28-finding baseline, the per-stage gate
readings and the coupling counts are sandbox facts until re-measured against live. Re-deriving
them is cheap and assuming they carried over is the kind of error that reads as a passing gate.
**Gate:** selftest accounts for **exactly** `SELFTEST_EXPECTED` breakages, the constant raised
deliberately if cases were added · every retirement
carries a declaration · all four `.md` hook-ins still parse.

**08 · Acceptance — by default, ZERO calls**
Because the bytes never changed, there is nothing for a sweep to discover: it would re-sample the
same distribution and return its own noise. Acceptance is the four zero-call instruments of §7a,
and a live sweep is a *contingency* priced per item that fails byte-equality, not a scheduled cost.
**Gate:** every §7a instrument green · any item that failed byte-equality swept and declared ·
**every artifact that swept item supersedes retired** (O4), since the all-artifact checks cannot be
cleared by sweeping at any price.

> **Preserved for this stage.** `migration/stage08_acceptance.py` (six rows),
> `e2e_session.sh`, `student_session.sh`, `student_session.spec.ts`. Certified
> browser result: `migration/goldens/student_session_certified.json`; the dry
> run's scorer-side evidence is `$COURSE_DATA/migration_reference/sessions/e2e_session_p1/` (26 items).
> The non-circular served-prompt claim needs a dump that PREDATES the work —
> `$COURSE_DATA/out/idmap_v145.json`, 2026-09-12, confirmed present.

**AMENDED 2026-09-14 — 08's entry condition moved at 06.** Stage 06 moves the paper `scorer_sha`
for the eight handout-2 columns named above, so §7a's instruments cannot be green until those are
re-recorded. In LIVE that is a genuine re-record through `measured.py --record`, re-deriving each
score from its artifact through today's scorer — NOT the dry run's `dryrun_forge_freshness.py`,
which stamps the sha without re-deriving and whose own banner says nothing downstream of it is
evidence. Make the re-record 06's closing step rather than 08's surprise.

---

## 7a · Sweep economics — how to spend almost nothing

A full acceptance measure is **≈ 520 cells × 6 runs × 3 sides ≈ 9,400 calls**, and the first draft
scheduled one at the end as a matter of course. It should not be scheduled at all. **A byte-neutral
migration has nothing for a sweep to find**, and four instruments establish that for zero calls.

| instrument | proves | cost |
|---|---|---|
| **Prompt-byte oracle** | the generated `.olx` bodies are identical to golden, all 70 actions | 0 |
| **`fingerprint_text` oracle** | the paper scorer asks the same question, all 26 items | 0 |
| **`idmap` served-prompt check** | the **running server** serves exactly the current generated prompt — line by line, with a superset arm that catches lines the rubric no longer generates | 0 |
| **Corpus replay** | re-scoring frozen runs under the new code yields identical scores | 0 |

The third is the one that closes the gap people usually pay a sweep to close. The first two are
offline: they prove the bytes on disk are right, not that the deployed system serves them. The
`idmap` check proves exactly that, which is why it already runs in every sweep's preflight — and it
runs without scoring anything.

### Clearing staleness without measuring

A code move stales columns as `STALE SCORER`, whose own message is explicit: *"The PROMPT is
unchanged — what moved is the scoring code. The runs' verdicts still stand; the SCORES computed
from them may not, so re-score or re-sweep."*

**Re-scoring is a re-record, and it USUALLY costs nothing**: `record` recomputes every score from
the already-recorded verdicts under the current code and re-stamps `scorer_sha`. So the module
moves of T2 — which would otherwise be the migration's single largest sweep bill — are mostly
cleared for free.

**But "for free" is not universal, and the exception is invisible until you try it.** Measured
2026-09-14 on the three columns the dry run tried to clear — `olx`/3, `python`/2b, `python`/3.
All three pass `measured.safe_to_rerecord`: the ask has not moved, so a re-record is legitimate in
principle and the batch will select them. All three are then **refused by the side contract**,
because their artifacts predate `agreement._era_for` stamping the backend and **nothing records
which model produced them** — not `era`, not `era.items`, not the sibling `.log`, and not their
own existing ledger entries. The refusal offers hand-stamping `era.model` "if the run's log
settles it"; here nothing settles it, so stamping would invent the fact rather than recover it.

Such a column costs a **re-sweep**, or a **declared exception** in the shape §11.3 uses for
`paper_opus` — recorded through `MEASURED_ALLOW_OFF_CONTRACT=1` with the reason written into the
entry. It is not a re-record, and a budget that assumes otherwise is short by however many
pre-stamping columns the tree still carries. **Count them before quoting a figure**: select the
scorer-stale columns, attempt the re-record, and read `refused` as a separate number from
`recorded`.

**Two further failure modes make the batch lie, both measured 2026-09-12.**

- `record` raises **`SystemExit`** on a side-contract refusal, which `except Exception` does not
  catch. A batch written the obvious way dies on the first refusal and leaves a partly-updated
  ledger that looks untouched — the run reported "to re-record: 43" and nothing else, and the
  staleness count was unchanged, which reads as "nothing needed doing". Catch `SystemExit`
  separately and report `recorded / refused / failed` as three different outcomes.
- **Never re-record a column that is `STALE PROMPT`.** `record` stamps the CURRENT `prompt_sha`
  onto runs produced under the old prompt, so the column claims to be fresh while its verdicts
  answer a question that no longer ships — destroying the evidence that a sweep was owed. A batch
  selecting on `scorer_sha` mismatch alone will do this. It happened to Q1, and only the
  interpretation check's control caught it. **Select on scorer-staleness AND ask-equality.**

### Demotion — the rule that makes an attribute change free

`prompt_sha(item, "olx")` hashes the served tag ENTIRE, attributes included. So a change that adds
or edits an attribute moves the sha **even when the assembled prompt and response schema are
byte-identical** — the model is asked exactly the same question. Priced naively that is
`STALE PROMPT`, ~120 calls per item per side, for nothing.

The rule:

> **ask unchanged ⇒ not `STALE PROMPT` ⇒ treat as `STALE SCORER` ⇒ re-record, zero calls.**

A **demotion, not a dismissal**, and the distinction is load-bearing. A tag attribute that never
reaches the model can still change SCORING — `maps=`, `forbid=`, and `free=` all do — so the
verdicts survive but the scores may not. Marking such a column *fresh* freezes a score the current
rules disagree with: on Q1 that would have pinned p17 at 3.0 where the shipped rule now says 5.0,
which is gold's answer. Re-recording fixes it for nothing.

**"The ask" means prompt AND schema**, compared per included cell, not prose alone — a schema
change alters what the model may answer without touching a word:

```
A.build_prompt(act["body"], fixture_for(item, pid)) + A.checklist_guidance(show_checks)
A.build_schema(act["slots"], act["excluded"], show_checks, act["cover"], act["choices"])
```

`prompt_sha(item, side, olx_text=…)` already accepts a historical `.olx`, so old-vs-new is
computable with zero calls. **Paper needs its own comparison**: its `prompt_sha` hashes
`score.fingerprint_text(item)`, not the `.olx`, so a rubric edit that moves the paper prompt is
genuinely sweep-priced and must not be demoted.

Record the comparison per item, so a demotion is auditable rather than asserted.

### Sweeping does not clear a finding read from every artifact

Two checks scan **every artifact ever recorded**, not the live ledger — deliberately: *"a fault
superseded by the next sweep disappears from the ledger while remaining true of what was
recorded."* `check_mapped_slots_agree_with_their_map` and `check_count_scaffolds_are_arithmetic`
both do. After a migration re-sweep the superseded files are still on disk and still firing, so
those findings **cannot be cleared by sweeping at any price**.

Clearing them is a **retirement**: move the superseded `<item>.runs.json` out of `paths.OUT` with a
manifest saying why. Two constraints, both learned 2026-09-12:

- **Never retire a live ledger source** — a recorded column whose artifact is gone cannot be read
  back, which is R12's unreachable-column failure. Check against every side's recorded `out` first.
- **Retire the FILE, not its directory.** A sweep directory holds other items' runs, and moving it
  retires evidence nobody asked about.

Measured that day: retiring six superseded files took these two families from **14 findings to 4**,
and the four survivors were exactly the ones still pinned to live ledger sources — which a sweep
then frees. So the order is **sweep, then retire**, and a stage that re-sweeps owns the retirement
that follows it.

That works only if the artifact can be read back and is attributable, which is a real
pre-condition and was not met as recently as 2026-09-11:

- The artifact must be **reachable** — under `paths.OUT`, named `<item>.runs.json`.
  `_refuse_unreachable` enforces it now; columns recorded before it existed pointed nowhere.
- The artifact must carry **`era.model` and `era.backend`**. `twoside_web` and `twoside_cli`
  predate stamping and carry `model: None`, so the contract refuses them and ten columns had to be
  re-swept rather than re-recorded — ~1,150 calls spent on a bookkeeping gap.

**Therefore, a precondition of starting the migration:** every column on every side is freshly
swept, reachable, and stamped. Any column that is not is a column the migration will have to
re-measure at full price. The 2026-09-11 top-up pass exists precisely to leave the ledger in that
state, and finishing it is stage 00's true entry condition.

### Where calls actually become unavoidable

Only two situations, and both are priced per item rather than per corpus:

1. **An item whose prompt cannot be reproduced byte-exactly.** R7 anticipates this and says to
   canonicalise both sides and declare it. That item's prompt has moved, so pooling is refused and
   it needs a full 6-run re-measure on the affected sides — **~120 calls per item per side**. The
   whole cost model is therefore *the number of items that fail byte-equality*, and stage 02 exists
   to drive that number to zero while it is still cheap to fix.
2. **A deliberate content change** ridden along with the migration. The rule is not to ride any:
   a rubric edit and a rubric migration must never land in the same commit, because the byte oracle
   is what makes the migration provable and a content change destroys it by design.

### Batching rule

If a sweep does become necessary, **every stage that moves the same column's sha lands before it,
not around it.** Two stages that each move Q6's paper prompt should sweep Q6 once, together. The
worst outcome is paying the 9,400 twice because two stages were sequenced for tidiness rather than
for cost.

---

## 7b · Commit discipline — the audit as a per-stage test

**Every stage commits, and no stage commits once.** This is not bookkeeping: the pre-commit hook
runs `equivalence.py --enforcement`, the full audit, and **refuses the commit** on any blocking
finding. Committing is therefore the cheapest way to run the enforcement machinery against the
work in progress, and a migration that commits often gets the audit run dozens of times instead of
twice.

That matters most for the errors nobody is looking for. The audit's value here is not the check
you wrote for the thing you are doing — it is the 53 checks with no connection to rubric data at
all, which will nonetheless notice when a migration script drops a declaration, renames a slot the
gold table still references, or leaves a table entry matching nothing.

### What the hook does and does not cover

| runs at commit | does **not** run at commit |
|---|---|
| the full enforcement audit (`--enforcement`) | the **selftest** and its `SELFTEST_EXPECTED` count |
| every check wired into `equivalence.py` | the **byte oracles** (prompt bytes, `fingerprint_text`) |
| | the **`idmap` served-prompt check** |
| | `editguard`'s vanished-definition scan, which runs in sweeps |
| | anything in **lo-blocks**, which has no hook of its own |

So committing is a strong net, not a complete one, and the stage gates in §7 remain the
contract — the hook is what catches the incidental damage *between* gates.

### lo-blocks has no net at all — supply one by hand

`edu.memphis.psych` has a pre-commit hook; **lo-blocks has none**. Nothing there runs an audit,
refuses a commit, or notices that a parser stopped accepting an attribute. The engine side of this
migration is therefore the side with no safety rail, which is the opposite of where the attention
naturally goes.

**The discipline: any change to a lo-blocks component runs that repository's own test suite before
it is committed, and the stage gate records that it ran.** Not "CI will catch it" — the suite is
the gate, and a stage that touched lo-blocks without running it has not met its gate regardless of
what the psych-side audit says.

This is not ceremony. Every engine-side failure this plan anticipates was found by a test or not at
all, and three of them were invisible by inspection:

- `choices`/`expect` missing from `LLMAction`'s attribute schema **dropped ten blocks and 40
  `<Ref>` children**, and the symptom was a hang, not an error (R3, R4).
- `readChecks` reconstructing the grader payload field by field **silently dropped `expect`** —
  it typechecked, and one item fell from 17/18 to 4/18 (R5).
- `scoreSlotSheet`'s eight positional parameters transpose without complaint (R8).

None of those would be caught by the psych-side audit, which cannot see inside the engine. They
would surface as a scoring change days later, attributed to a prompt edit.

Concretely, at every stage that touches lo-blocks: run the suite, run the slot-sheet and
`LLMAction` smoke tests specifically, and re-run the psych-side byte oracles afterwards — because
an engine change that alters parsing changes what the build generates, and the byte oracle is the
only thing that will say so.

### Passing is not the same as still correct

The suite going green says the tests ran, not that they still test anything. Every failure below
was found on **2026-09-13**, in *our own* engine code, and each had been invisible for weeks.

**A skipped test cannot tell you it has rotted.** `legendRender.test.ts` is gated
`skipIf(!IDMAP)`, so nothing in CI ever supplies an idmap and it had never run. Exercising it
surfaced **three** accumulated defects at once: the content namespace had been renamed
(`psych` -> `edu.memphis.psych`), `initConfig()` was never called, and the idMap was dispatched to
the store but never passed to `RenderOLX`. A stage that leaves a test skipped has not tested that
thing, and the debt compounds silently.

*So:* every stage names the tests it is relying on and confirms none of them is skipped. Where one
is skipped by design, the gate records **what supplies the missing precondition** and that it was
supplied at least once during the stage.

**Documentation examples can parse perfectly and still be wrong.** Every `derived=` in the grading
documentation was written `key:ref`. The grammar is `key:kind:refs`, and `parseDerived` DROPS a
rule whose kind it does not recognise -- so those examples' rules vanished, every check scored
unsatisfied whatever a student typed, and the prose confidently described behaviour the example did
not have. The playgrounds rendered. The XML was valid. Nothing complained.

*So:* documentation is not checked by reading it. `docPlaygrounds.test.ts` now parses every
`olx:playground` in every block doc through the real `parseOLX`, and asserts that the documented
examples BEHAVE as their prose claims. A stage that changes a primitive's grammar updates that
test in the same commit.

**A new block arrives with neither.** Of the six components this project added to lo-blocks, three
had no documentation and three had no tests; two had neither -- including `DerivedChecks`, which
the grading docs lean on for their runnable examples. A component added mid-migration will do the
same unless the gate asks.

*So:* the stage gate for any stage that ADDS a block requires a `.md` beside it and a test file in
its directory, both before the stage closes. The convention is per-component and already universal
elsewhere in the repository -- every other grader has a `.md`.

**The checklist, for any stage that touches lo-blocks:**

1. `npx tsc --noEmit` clean, and the full suite green -- **excluding `runner.test.ts` while a sweep
   is running**, because the sweep executes it and a second instance interferes.
2. Every block the stage added or changed has a `.md` that matches its current attributes. Check
   them against the zod `.describe()` strings, which are the source of truth; prose drifts from
   them first.
3. `docPlaygrounds.test.ts` green -- examples parse AND behave.
4. No test the stage relies on is skipped; any that is, is run once by hand with its precondition
   supplied, and the result recorded in the gate.
5. Mutation-test anything the stage newly guards, **against a copied module** -- never live source.
   Restoring a file byte-identically still moves its mtime, which is what `server_code_is_stale`
   compares, and doing that mid-sweep makes the guard cry stale.

### Commit granularity

Small enough that a refusal names one cause. A migration script that moves 26 items' data in one
commit turns a single blocking finding into a bisect; the same work as one commit per handout, or
per item where the data is complex, turns it into a message. The scripted migration of stage 04 is
idempotent by design, which makes fine-grained commits free — re-running after a refusal costs
nothing.

### The override is the hazard

`ALLOW_UNDECLARED="reason"` turns a refusal into a recorded override, appending the findings
verbatim to `OVERRIDES.md`. It exists for the case where a finding is understood and the commit is
still right. **During this migration it must not be used to keep moving.**

A blocking finding during a byte-neutral stage means something the plan did not predict — the
prompts are supposed to be identical, so the audit should have nothing to say. Overriding it
discards exactly the signal the stage was designed to produce. The rule for the migration:

- An override during stages 00–04 (which change no shipped bytes) is **a stop**, not a note.
- An override during 05–06 requires the reason to name which oracle disagrees and why that is
  acceptable, reviewed before the commit rather than in the message.
- Overrides are counted per stage and reported at the stage gate. A stage that needed several has
  discovered something about itself.

The failure mode this guards against is well attested in this project's own history: a check
relaxed to clear its output is how detection power is lost quietly, and an override is a check
relaxed for one commit.

---

## 8 · The limit — what shared data costs

Once both implementations read one rubric, a mistake **in the rubric** — a wrong point value, a
wrong canonical wording, a guidance bullet saying the opposite of what was meant — is **invisible
to web-versus-paper comparison**. Both sides will faithfully agree on the wrong thing.

This is the cost of the design, not a defect in it, and a deliverable of this plan is a section in
`EQUIVALENCE.md` stating it plainly, with what actually defends against it, in order of strength:

- **Agreement against the human-graded gold corpus** — the only check anchored outside both
  implementations, and therefore the primary defence.
- **The generated `.olx` diff** — a rubric edit produces a reviewable diff of every prompt it
  touches. Build-time generation preserves this; render-time assembly would have destroyed it.
- **The probe path**, which compares against the paper scorer's *measured behaviour* rather than
  its rubric, so it still detects logic divergence where data is shared.

The section must say plainly that green web-versus-paper agreement is **not** evidence the rubric
is right — it never was, but it is more obviously not once the data is shared.

**Two further additions to the deviations register while it is open**, carried from the first draft
and still owed:

- Each entry should say **which side does what**, not merely that the two differ. The entries
  corrected in that session were stale precisely because they described an intention rather than a
  behaviour.
- The `DECLARATION STALE` check is what keeps them honest, and must be re-aimed at the rubric
  object in stage 07 rather than left pointing at `rubric_hN.py`.

---

## 9 · Risks

Carried forward where still live, restated where the ground moved, and new where today's codebase
created new exposure.

**R1 · inspectability — resolved by design.** Build-time generation means the shipped prompt
remains in the `.olx`, readable and hashable. The original plan's snapshot directories and inspect
tool are no longer needed. *This risk is closed, not mitigated.*

**R2 · the audit's basis shifts under it.** The dominant risk, and C1's subject. Mitigation: the
stage-01 disposition pass, finding-set equality, coverage assertions, and a selftest gate that
cannot fall. Relaxing a check to clear its output is how detection power is lost quietly.

**R3 · silent absence.** An `LLMAction` pointing at a rubric that does not resolve would make a
call with no instructions and return something that looks like an answer. Unresolvable `rubric=`
is a content-load error. A sheet-bearing action with neither body nor rubric is an error. And
`rubric` enters the block's zod schema in the same commit as the parser — `.strict()` silently
dropped ten blocks and 40 `<Ref>` children when that step was missed for `choices`/`expect`, and
the symptom was a hang, not a message.

**R4 · hand-maintained lists.** A registry knows; a hand-written list does not. Add `rubric` to the
sheet-attribute registry *first* and let the conformance test enumerate the work. One invariant
closes the class: for every name in the registry, the block schema accepts it, the Python
forwards it, and the probe round-trips it.

**R5 · hand-copied payloads.** `readChecks` reconstructed the grader payload field by field;
`expect` was added to the type and the scoring call but never copied out of the JSON. Every
ungated cell of four items lost that rule's points and nothing errored. Spread-first then default,
on every boundary rubric data crosses, plus a round-trip test including a field the reader has
never heard of.

**R6 · compatibility (C4).** Handcrafted actions are the common case, not an edge case. A rubric
is strictly opt-in; the legacy path stays physically separate.

**R7 · reproducibility.** The byte oracles are worthless if the assembler cannot hit the same
bytes. Settle whitespace and ordering in stage 02 against the golden bytes, before any content
moves.

**R8 · interface shape.** `scoreSlotSheet` takes eight positional parameters and `satisfiedMap`'s
order differs from it; a caller transposing two gets a wrong score and no error. The assembler
takes an options object from day one.

**R9 · expressiveness.** Not every Python construct has a declarative form; `rubric_h2.py` is
partly computed. The stage-03 audit decides each case before items convert.

**R10 · the paper scorer's new dependency — REALISED AT 06, and it cost more than the risk said.** `score.py` builds from an importable module today;
afterwards it needs the rubric object. Same repo, so the common case is fine — and per §11.2
(closed 2026-09-13) that is the ONLY case: paper scoring never runs where `psychology/` is absent,
so stage 06 reads the rubric object directly. A `rubric --export` to neutral JSON — single
*source* without single *location* — stays an additive option for a consumer that cannot see the
repo, not a deliverable of this migration.

  *Measured 2026-09-14.* The dependency is real and the risk understated its shape: the binding is
  not one import but **four names** (`BY_ID`, `ITEMS`, `SLOT_SPEC`, `SLOT_OPTIONS`, the last by
  `getattr`), plus a MODULE-LEVEL `from rubric_h2 import (...)` that fails at import rather than at
  use, plus two module constants with no home in the rubric object until 06b gave them one
  (`REQUIRED_MOVE`, `_OC_FRAME` → `SHARED_GUIDANCE`). It also moves the paper `scorer_sha` for
  eight columns, which R12's cascade then prices.

**R11 · declaration-key drift (new).** §5.2. Migrate keys with the data; assert entry count and
match count unchanged.

**R12 · fingerprint staleness cascade (new).** Every prompt-source change moves a sha and stales a
column. A stage that moves a PROMPT sha without a planned re-sweep leaves the ledger unreadable
(scorer-sha movement is cleared by re-record instead, §7a) — and, per
2026-09-10, a column can be *recorded* and still unreadable if its artifact is written outside
`paths.OUT` or under a non-canonical name. Each stage states which shas it moves and which columns
it therefore re-sweeps; `_refuse_unreachable` and `append_runs` are the guards.

**R13 · content leaking into the engine (new).** C2's risk. Mitigated by
`check_engine_is_content_neutral`, AST-based rather than text-scanning.

---

## 10 · Traps — failures this plan is likely to walk into

The risks in §9 are things that could go wrong with the design. These are things that will go
wrong with the *execution*, drawn from how this codebase actually behaves. Each is cheap to avoid
and expensive to discover late.

### T1 · Two repositories, no atomic commit

The engine and the content version separately, so **no migration step can land in both at once**.
Between any two commits there is a window where one repo is ahead. A stage that requires them to
change together will half-land and leave the tree in a state neither gate describes.

*Mitigation.* Every stage must be **orderable and independently valid**: engine change first,
tolerant of content that does not use it yet; content change second. The rubric attribute must be
*accepted and ignored* by the engine for a full stage before any content sets it. Never the
reverse — content referencing an engine feature that has not shipped is the failure R3 describes,
and it presents as a hang rather than a message.

### T2 · `scorer_sha` is a closure over module membership

`scorer_sha(item)` hashes the AST of a scoped closure over `agreement`, `olx_prompts` and
`handouts`. It is deliberately prose-insensitive — comments and docstrings are stripped — but it
is **not** insensitive to *where a function lives*. Moving a parser from `olx_prompts` into a new
module changes the closure for every item that uses it, and every affected column goes
`STALE SCORER` at once. Precedent: correcting one comment in `parse_counts` once marked
**21 of 26 items stale**, which is what motivated stripping prose in the first place.

*Mitigation.* Before moving anything, compute `scorer_sha` for all 26 items and diff it after. A
non-empty diff is expected and is **not** a sweep: `STALE SCORER` means the prompt is unchanged and
only the derived scores are suspect, so a **re-record clears it for zero calls** (§7a). What the
stage owns is the *re-record list*, not a measurement budget. The trap is only expensive if module
moves are mixed into a stage that also moves prompts — then the two staleness kinds are
indistinguishable and the cheap remedy no longer applies. Keep module moves in their own stage for
that reason, not because they are costly.

### T3 · The fixture is built from the paper scorer's own output

`agreement_app.scorer_evidence` derives the web's per-box fixture from `score.py`'s evidence
spans — the code says so: *"That is circular: their input is built from the paper scorer's
output."* `CONSENSUS_FIXES` then hand-corrects it, and on Q6 roughly 30% of boxes are hand-set.

So **changing the paper prompt can silently change the fixture the web is scored on**, and a
web-side movement can be caused by a paper-side edit with no web edit at all. During a migration
that rewrites how the paper prompt is assembled, this is a live hazard rather than a theoretical
one.

*Mitigation.* Freeze the fixture explicitly at stage 00 — snapshot every derived box — and assert
it byte-identical at each stage gate. If a stage moves a fixture box, that is a finding requiring
a decision, not a diff to accept. `check_fixture_boxes_hold_the_students_words` and
`check_consensus_spans_are_disjoint` stay in the gate set throughout.

### T4 · A standing benign warning that hides the real one

`olx_prompts.py --write` reports `H3: minted 1 new ref id(s)` on every run. The id is deterministic
and the file is stable, so the warning is harmless — and therefore invisible. The moment a
migration mints a *second* id, the message reads identically to a reader who has learned to ignore
it.

This is the same failure as filtering a log to its success lines, which hid three refusals in one
session on 2026-09-10.

*Mitigation.* Fold the outstanding minted id into `REF_IDS` (or the rubric object) at stage 00 so
the count is **zero**, and make a non-zero mint a gate failure rather than a line of output.
Generalise: no stage may leave a standing warning in a build that a later stage's warning would
resemble.

### T5 · A PROMPT sha move forbids pooling — but a SCORER sha move does not

`append_runs` refuses any stale column by design: runs may only be pooled when they sample the
same prompt, scorer, model and cells. But the two staleness kinds have very different prices, and
conflating them is what makes a migration look unaffordable:

- **`STALE SCORER`** — the prompt is unchanged, the code moved. The recorded verdicts still stand,
  so a **re-record recomputes the scores for zero calls**. This is the migration's common case.
- **`STALE PROMPT`** — the question itself changed. The verdicts describe a prompt that no longer
  ships, so they must be discarded and the column re-swept: **~120 calls per item per side**, and
  ≈ 9,400 if it were the whole corpus on all three sides.

*Mitigation.* Design every stage to move **no prompt sha**, which is what the byte oracles enforce;
scorer-sha movement is then free to happen and free to clear. Where a prompt sha must move, it is
priced per item and stated in advance — **but first check whether it really moved the ASK**: the
sha hashes the served tag entire, so an attribute-only change reads as `STALE PROMPT` while the
model's question is byte-identical. §7a's demotion rule turns that case back into a zero-call
re-record, and it is the difference between the rubric attribute costing ~6,240 calls and nothing.

Batch: two stages moving the same column's prompt land together and are swept once, not twice.

### T6 · The dev server reloads content but not code

The server serves fresh `.olx` while running stale TypeScript, so it will happily score against a
new rubric with an old parser and report nothing wrong. `agreement_app.server_code_is_stale()`
guards it and must be in every sweep's preflight. Restarting is not free either: restarts leak
node children holding inotify watches, and roughly fifty exhaust the limit, after which the next
start fails with `ENOSPC` and `pgrep node` does not find the culprits.

*Mitigation.* Preflight every measurement with `server_code_is_stale()`, which the sweep scripts
already do. Budget engine restarts consciously and kill by cmdline match rather than assuming a
clean exit.

### T7 · Mass deletion meets one-at-a-time acceptance

`editguard` refuses a write that drops a tracked definition, and `DEFINITIONS.json` has **no bulk
accept** — deliberately, so that a slice eating a neighbour cannot be waved through. Stage 06c
deletes the Python rubric data, which is a large number of definitions at once.

*Mitigation.* Script the acceptances as an explicit, reviewable list produced from the diff, and
run them one name at a time as the tool requires. Expect the list to be long; its length is the
point. The same applies to `DESIGNED_TEXT_SHA.json` entries retired with their fields.

### T8 · The acceptance gate must not demand a number sweeping cannot deliver

The ledger's `runs` is `min(observations across cells)`, so a single cell missing from a single run
caps the whole column. Cell-level dropout is provider behaviour, not something a sweep controls:
on 2026-09-11 `NR/python` held 6 raw runs and reported 5 because four cells came back without a
usable score once.

*Mitigation.* State the acceptance gate in terms of **movement beyond known spread**, not in terms
of a run count. Where a column ends below target, top up the short *cells* — `append_runs` accepts
a subset artifact for exactly this — and if dropout persists, record it rather than spending runs
at it.

### T9 · `OVERRIDES.md` is already 47 MB

`ALLOW_UNDECLARED` records findings verbatim, and four modules append to it. A migration that
touches enforcement will generate a great many undeclared-finding events, each appending its
reason and the findings in full.

*Mitigation.* Prefer fixing or declaring over overriding during the migration; where an override
is genuinely right, write one entry per stage rather than per command. If the file becomes
unwieldy, rotating it is a separate decision to take deliberately — it is read by
`precommit_gate.py`, so truncating it is not a free action.

### T10 · A new check is a gate failure until the constant is raised

`SELFTEST_EXPECTED` is two-sided (C1): *"exactly 66, not at least 66"*. Stage 07's gate says so,
but stages 01–06 may also add checks — R13's `check_engine_is_content_neutral` and R3's
rubric-resolution check are both new checks — and each fails its own stage's gate until the
constant moves. Walked into on 2026-09-12: three cases were added and the very next selftest run
reported a count mismatch, having cost an hour of CPU to say so.

*Mitigation.* Treat the constant as part of any commit that adds or retires a check, not as stage
07 cleanup, and say in the stage entry which cases were added. Note the cost asymmetry: the
selftest re-runs the whole audit once per case, so an expensive new check multiplies across every
case. The interpretation check added that day took the run from ~40 to ~80 minutes until it was
memoised — **memoise anything a check calls that scans the corpus**, keyed on
`measured._artifact_fingerprint()` so a re-sweep still invalidates it.

### T11 · The artifact flattens `count` and `verdict` into one column

Every reader that rebuilds a recorded cell has to know, on its own, whether the value it is
holding is a **judgement** or a **number** — because the artifact stores both in the same column.
Nothing in the data says which; the only authority is the slot spec. A reader that guesses
`verdict` for a counting group hands `expand_counted` no count, every member of the group recovers
as unmet, and the cell scores at its **floor**.

**That failure is silent and, worse, plausible.** It does not raise; it produces a lower score
that looks exactly like a genuine engine disagreement. On 2026-09-13 it was reported out loud as
the paper and web scorers disagreeing on 456 cells, on items whose two sides in fact agree
unanimously.

**It has now happened six times, across five distinct sites**, which is what moves this from
carelessness to a design defect. Removing the `count ?? verdict` fallback that day was *correct*
for the scoring path — it let a reconstruction be wrong and still score. But the fallback was also
the only reader that understood the legacy shape, and deleting it broke every reconstruction at
once. Three sites were fixed and named in the fallback's own comment (`mirror_self_control`,
`_recorded_payloads`, `probe`). **Two were not, and were missed precisely because the comment
reads as a complete list**: `enforcement.check_computed_slot_recovery_is_faithful`, which wrapped
every recorded value as `verdict`, and `measured.paper_scorer_agreement`, which did the same at
*two* call sites. The audit went from 27 undeclared to 483 and stayed there for most of a day.

*Mitigation — one helper, not five conventions.* **No reconstruction site may build its own
`{"verdict": v}`.** A single helper owns the routing:

```python
def rebuild_sheet(spec, checks, answers) -> dict:
    """Rebuild a recorded cell, routing each key by the SLOT SPEC."""
```

It reads the counting groups off `spec`, sends a group's key to `count` and everything else to
`verdict`, and attaches `refers_to` from `answers`. Every site above calls it; none reimplements
it. A stage that adds a sixth reader then cannot get this wrong, because there is nothing left to
get wrong.

*And ratchet it*, or the convention decays the moment someone writes a sixth site from memory: a
check that refuses a literal `{"verdict":` constructed anywhere in a reconstruction path, in the
shape `check_engine_is_content_neutral` already uses. It needs its own selftest case, so
`SELFTEST_EXPECTED` moves with it — see T10.

*Why this belongs to the migration and not to a backlog.* Stages 04–08 each re-read every recorded
cell to prove a gate, and **a gate that reconstructs wrongly reports a clean tree as broken, or a
broken one as clean**. The helper lands in stage 00, where its correctness is provable at zero
cost: the audit's finding-set must be byte-identical across the refactor, and `scorer_sha` must
not move on any of the 104 item/side pairs. Both were confirmed when the five sites were repaired
by hand on 2026-09-13.

### T12 · A new block is INERT until the registry is regenerated, and says nothing

`blockRegistryAutogen.ts` is generated by `npm run build:gen-block-registry`, which discovers
blocks by walking the component directories. Add a block and skip that step and the tag still
"works": `parseOLX` falls back to a default parser, so the document parses, ids register, and
children appear. **What is lost is the block's own schema** -- its attributes are not validated,
its parser is not used, and text content it should accept is rejected as if it were stray prose.

Measured 2026-09-14, authoring stage 3a's six types. Every symptom pointed somewhere else: text
inside `<Deduction>` became an `ErrorNode` reading "expected OLX block tags", which looks like a
parser choice and is really a block that does not exist yet. Two rounds of fixing the wrong thing
went past before the registry was regenerated.

*Mitigation.* Regenerating the registry is part of ADDING a block, not part of shipping one. Any
stage that adds a block type runs it, and the stage's tests must exercise the block THROUGH
`parseOLX` -- a unit test that imports the module directly passes whether or not the registry
knows about it, which is precisely the reassurance that hides this.

### T13 · Parsed content does not have the shape a hand-built fixture has

Three defects in stage 3b passed every unit test and broke on the first real
parsed document. Each was SILENT -- no error, no empty output, just a quietly
wrong result -- and each cost a round of diagnosis.

**Text is in `kids`, as a string.** A text block parses its content to
`kids: "{question}"`, not to a `textContent` field. A reader that looks only at
`textContent` loses every placeholder: the structure still materialises, the
items still appear, and all the prose is simply gone. It was caught by an
incidental warning -- "params nothing asks for" -- which was the only visible
symptom of losing the entire body.

**Attributes are typed, not strings.** A schema declaring `pts` as a number
hands back a number, and any code that assumed text fails on it. The expander
worked on hand-built fixtures for two days and broke the moment it was handed a
parsed document.

**`kids` is an array on some blocks and an object of named arrays on others.**
A walker that assumes one shape throws on the other.

*Mitigation.* Do not test a content-reading mechanism on hand-built structures
alone. The stage-3b lesson is specific: the FIRST test of any reader should
parse real authored markup through `parseOLX`, because everything downstream
inherits the shape the parser actually produces and nothing warns when a
fixture disagrees with it.


**T15 · A rubric can be PROMPT-complete and not SCORER-complete, and the stage-04
proof cannot tell.** Stage 04 proved 23/23 bodies byte-equal from the emitted
rubric. That exercises only the fields a PROMPT reads. Reading the rubric object
back into the modules' own shape at the head of stage 05 found **107 omissions
across 18 fields** -- `label`, `increment`, `derive_from_credit`, `blank_code`,
`expected_type`, `unreachable_codes`, `oc_gates`, `SLOT_OPTIONS`, a `Cover`'s
owning entry and verdicts, a `Derived`'s worked example, and the course-specific
flags. Every field was read by `score.py`, `enforcement.py`, `measured.py` or
`equivalence.py` -- never by the prompt -- which is exactly why byte-equality was
silent on all of them.

*What made it safe:* the same reading found **zero contradictions**. The rubric
object was a strict SUBSET of the modules, never in conflict with them, so the
gap closed by adding rather than by re-deciding anything.

*Mitigation.* `migration/stage05_rubric_equivalence.py` walks the whole
structure and reports omissions and contradictions SEPARATELY, because they are
different failures: an omission is unfinished authoring, a contradiction is a
defect. Run it before trusting any byte-equality result. Note also that an empty
container and an absent field are the same statement here (`codes={}` charges
nothing and so does no `codes`), so both normalise away -- otherwise the check
ends on a false difference.

**T16 · `of` is the sixth reserved expression-language keyword, and the seventh
is not worth finding this way.** After `ref`, `id`/`title`, `when`, `cond` and
`keys`, stage 05 walked into `of` on `<Cover>`. The factory refuses it inside
`core()` via `assertNotReserved`, so the block throws **at module load** and the
failure surfaces as an unrelated gate step with a `tsx` stack rather than as
anything about naming.

*Mitigation.* Read `lib/stateLanguage/keywords.ts` BEFORE choosing an attribute
name; the full list is there and includes every array and string method. Do not
write a test for this -- one was written at stage 05 and removed the same hour,
because `core()` throws on import and every test in the file fails first, so the
test can never be the thing that catches it. `of` became `item`, which is what
`<Context>` already calls the same thing.

**T17 · Two writers for one artifact, and the patcher always loses.** Stage 05
began by PATCHING the emitted rubric with the fields stage 04's emitter did not
know about. It worked, the equivalence check passed, and the next run of
`stage04_gate.py` silently erased all of it -- the gate re-runs
`stage04_migrate_rubric.py`, which regenerates the rubric from the modules and
has no idea the patcher exists. The symptom was not an error: the gate PASSED,
reporting "3 already identical", because the emitter and its own output agreed.
The loss only surfaced when an unrelated accessor returned an empty
`SLOT_OPTIONS`.

*Mitigation.* One generated artifact, one writer. The completion logic was
folded into `stage04_migrate_rubric.py` and the patcher retired. Before adding a
second writer for anything generated, check what the gates re-run: a gate that
regenerates is a writer, and it runs last.

**T18 · A "second run reports no edits" check cannot see a field the emitter
never emits.** The same idempotence clause that made T17 invisible is worth
stating on its own, because it reads like a completeness check and is not one.
It proves the emitter is deterministic, nothing more. Pair it with a check that
compares the artifact against the SOURCE -- `stage05_rubric_equivalence.py` --
or a field can be absent from both the emitter and its output forever, in
perfect agreement.

**T19 · A prepared accessor handed the wrong argument form returns empty and says
nothing.** `editguard.definitions` takes the module's TEXT. Handed a PATH it
parses the filename as a one-line program, finds no definitions, and returns an
empty set -- so the difference against `DEFINITIONS.json` came back **"0 new
names"** for a stage that had just added a whole new module. Nothing raised,
nothing warned; the number was simply wrong in the reassuring direction.

*Mitigation.* This is the counterpart to the standing rule that prepared
accessors beat hand-rolled ones -- they do, and using one still means checking
its signature and sanity-checking the first result. A count of zero from a
scanner is a claim that deserves one probe: ask it for something you know is
there. Here, `'_rubric' in got` would have failed immediately.

**T20 · An idempotence check whose baseline is mutated before the comparison
always reports "unchanged".** The completion script compared its output against
a variable that an earlier pass had already rewritten, so a run whose only
change was a new declaration reported "unchanged" and wrote nothing. Same family
as T18: a check that ends up comparing a thing to itself. Compare against the
artifact **as found on disk**, read once, before any pass touches it.

**T21 · A module proxy breaks module-level introspection, and returns something
plausible instead of failing.** Stage 06a made `config(h)["rubric"]` a proxy so
one accessor could serve either source. `vars(proxy)` then returns the PROXY's
instance dict -- `_handout`, `_module`, `_served` -- not the module's globals.
The emitter's selector scan uses `vars()`, found no selectors, and emitted
nothing; the run reported success and wrote an idempotent-looking file. The same
edge applies to `inspect.getsource`, which some checks use on rubric modules.

*Mitigation.* Anything whose job is to read the MODULE must unwrap deliberately
(`getattr(rub, "_module", rub)`), and the emitter especially -- through the proxy
it can end up reading its own output. When introspection returns empty, suspect
the object before the data.

**T22 · Rewriting imports and their uses in separate passes leaves names
unbound, and the audit reports it as a finding REMOVED.** The twenty direct
`import rubric_hN` sites were rewritten with blanket regexes: one pass replaced
import lines, another replaced the tuple form `(rubric_h1, rubric_h2,
rubric_h3)`. They did not match the same set of functions. Six functions lost
their import and kept their references; one file used the new alias with no
import at all. Nothing raised at import time because every one of them is a
function-local import.

The symptom was **not** a crash. The audit's finding-set moved by **−1**: a
control that had been failing 2705/2706 stopped reporting, because the function
feeding it now raised and was swallowed. A removal reads as an improvement, which
is why the baseline script says in as many words that a removal must be
attributed to the stage's own work or a check has stopped looking.

*Mitigation.* Rewrite an import together with the consumption form it feeds, in
one pass, per function -- and verify with a TOKENIZER rather than grep, since
half the surviving `rubric_hN` mentions are prose in comments and docstrings and
the ones that matter are NAME tokens. Then assert uses == imports per file.

**T23 · A name added to the rubric OBJECT and not to the proxy is absent for as
long as `dual` serves the module — and its reader may not say so.** Stage 06b
gave the rubric object a `SHARED_GUIDANCE` accessor to replace `rubric_h2`'s
`_OC_FRAME`. The one reader is `leakage._domain_words`, which guards the access
with a bare `except Exception: pass`. In `dual` mode the proxy serves the
MODULE, the module has no such attribute, and the result was a leakage gate
running on **51 domain words instead of 58** with nothing raised, nothing logged
and the gate still passing.

*Mitigation.* Anything the migration ADDS must be answerable from whichever
source is being served -- put the accessor on the PROXY, computing it from
`ITEMS` when the served source cannot answer. Otherwise `dual` stops being a
verification step and becomes a way to run half-migrated. Note which direction
the failure took: the gate got *stricter-looking* by losing exclusions, so a
spot check of "does it still pass" would have said yes.

**T24 · Checking that a prefix is present is not checking that the text is
present.** Deciding where `_OC_FRAME` lived, the first probe asked whether its
first 60 characters appeared in the emitted rubric. They did, in a different
block with a different continuation, and the conclusion drawn was that the
constant had been absorbed into a frame segment and would need that segment
SPLIT -- a change to shipped bytes, proposed and nearly made. The full string
was in the rubric all along, as the first `<Guidance>` entry on all twelve
handout-2 items, byte for byte.

*Mitigation.* Search for the WHOLE string before concluding anything about where
it went, and when a prefix matches but the whole does not, that is a finding
about two texts sharing an opening, not about one text moving.

**T25 · The process guards are machine-wide in BOTH directions, and only one
direction has been paid for.** `olx_prompts._selftest_source_root` was added on
2026-09-13 after a dry-run self-test refused fifteen live sweep items in fifteen
seconds. The MIRROR of that bug is still live in any tree without the fix:
`_measurements_in_flight` matches a sweep anywhere on the machine, so a live
sweep refuses every self-test in an isolated copy -- which is what a migration
dry run does all day, and the self-test is how stage 06 proves a disposition
still fires.

*Mitigation.* Both guards ask "is it reading or writing THE SOURCE I AM ABOUT TO
TOUCH", never "is something running". `_source_root(pid, tok)` resolves the
other process's script -- absolute if it said so, else against its own cwd --
and the guard skips it when the directory differs. Undeterminable stays refused:
if /proc is unreadable the answer is None and the caller treats it as ours,
because scoring cells against a rule nobody wrote is far worse than a wait.

Do NOT reach for `ALLOW_SELFTEST_OVERLAP` when this bites. It is the same escape
hatch the guard's own comments say trains everyone to pass `--force`, and it
would be suppressing a real refusal rather than fixing a wrong question. **Live
still has only the one direction** and should get the symmetric fix.

*Verify it with a synthetic process table, not by starting a process.* A fake
sweep is hard to produce convincingly -- `sys.argv` does not change what `ps`
reports -- and the test that matters is that the guard still FIRES for our own
tree. Feeding it a table with one live-tree and one own-tree sweep and requiring
exactly one detection takes seconds and checks the dangerous direction.

**T26 · An attribute-access scan misses `from X import NAME`, and that is where
the module-level coupling hides.** Stage 06's first measurement of the paper
scorer's rubric surface used a regex for `["rubric"].NAME` and reported "four
names, a small surface". It missed four `from rubric_hN import ...` sites --
`score.py` twice (six selectors plus `REQUIRED_MOVE`, and `SLOT_OPTIONS`),
`score_h1.py` and `baseline_h1.py`. Three are MODULE-LEVEL, so unlike every
function-local read they break at import the moment 6c deletes anything, and
`REQUIRED_MOVE` is per-item data that no earlier inventory had listed at all.

*Mitigation.* Count both forms, and count module-level imports separately from
function-local ones: they fail differently and at different times.

**T27 · A self-test that detects its own damage and VOIDS the finding will pass
while breaking the tree.** The run computes which inputs moved under it, prints
`*** THE SOURCE MOVED UNDER THIS RUN`, then reports
`restored state is clean: True (VOID -- source moved)` — and `moved` appears in
neither the exit code nor the condition guarding `.selftest-passed`. So a run
that left `agreement.py` carrying its own reporter-crash injection printed
`70 of 70 expected`, exited **0**, and stamped the file `measured.selftest_owed`
reads as proof the checks were re-tested.

*Mitigation, and note it is two separate fixes.* (a) A moved source is a
FAILURE, not an inconclusive result: put `moved` in the exit code and refuse to
stamp the pass. (b) Reporting damage is not the same as not doing it — snapshot
the bytes of every file a case can inject into, repair anything that differs at
the end and from an `atexit` backstop, name what was repaired, and **still
fail**. A case that does not undo its own injection is a defect to fix, not
something to absorb.

*Why the net rather than the root cause:* the per-case `try`/`finally` is
correctly formed and restores perfectly in isolation — reproduced, four hashes,
clean at the end. In the full run it does not fire, and the net covers all 70
cases instead of the one that was caught.


**T28 · Two gates can both pass on artifacts that do not connect to each
other.** Stage 3a proved *"the course renders the three assignments"*. Stage 04
proved *"23/23 items byte-equal, assembled from the emitted rubric"*. Both were
true, both were green, and between them sat a fact neither could see: the course
resolves a 34-line demonstration file while the emitted rubric — 964 lines, 26
items, three files — is referenced by nothing at all.

Each gate tested its own artifact against its own oracle. Nothing tested the
JOIN, so the join was free to be wrong while every number on both sides was
right.

*Mitigation.* When a stage produces an artifact that a LATER stage's artifact
must reference, the gate belongs on the reference, not on either end: resolve
the id the consumer actually uses and assert you reached the thing you built.
The cheap version of that check here is one line — does the rubric `<Course>`
resolves contain the items the corpus scores? — and it would have failed from
the moment stage 04 first emitted.


**T31 · A check can be protected by the audit being quiet, which is not
protection at all.** 6c's gate reads *"every check that read the deleted module
now reads its replacement, and each was shown to still fire"*. Measured
2026-09-15: `stage01_recount_coupling.py` counts **21** checks reading the
rubric modules, and only **five** had a selftest case. The other sixteen were
the checks this migration moves the ground under, and every one of them would
have gone from "green because the rubric is sound" to "green because the source
is gone" without a single line of output changing.

*Mitigation.* Sixteen cases written and each probed against its own check in
isolation before being added — clean, fires once installed, clean again after
restore. `SELFTEST_EXPECTED` 70 → 86. Four first attempts did **not** fire, and
each failure was the check's real contract asserting itself:

* `check_rubric_slots_reach_the_sheet` ignores a credit row with no `verdicts`,
  because a slot with no verdict list is COMPUTED, not asked, and its absence
  from `slots=` is the design.
* `check_mapped_slots_have_no_unreachable_verdict` takes the OFFERED set from
  the `.olx` sheet, so adding a bogus map pair changes what the map emits and
  nothing becomes unreachable. The injection that works REMOVES a pair.
* `check_paper_prompt_has_no_box_deixis` reads the assembled `build_prompt`, and
  not every rubric field reaches it — a credit `desc` did nothing; `question` fired.
* `check_paper_feedback_explains_its_deductions` has STANDING findings, so the
  ordinary arm is true with the breakage installed and removed alike. It needed
  the inverted arm: install a blinding, assert the finding disappears.

The general lesson is that the injection which finally fires is the documentation
of what the check actually reads — and that writing these cases is how you find
out, well before the delete makes the answer unrecoverable.

**T32 · THE DRY RUN IS NOT ISOLATED FROM LIVE, and the leak is one line inside a
function.** `sweep_readout.py` carries
`sys.path.insert(0, "/home/pdeane/code/edu.memphis.psych/scoring")` in four
functions — `_dropped`, `readout`, `slot_profile`, `cell_texts`. The path is
inserted at position **0**, ahead of the sandbox's own directory, and it is
hardcoded to live rather than derived from `__file__`. `sweep_gate.py` has the
same line.

It does not fire at import, which is why it survived: importing `sweep_readout`
in the sandbox leaves `sys.path` clean, and a check for the leak that only
imports the module reports none. It fires when a FUNCTION is CALLED —
`enforcement.py:9620` calls `SR.readout(item, before)` inside
`check_exclusion_claims_are_data`, so **every dry-run audit** puts live's scoring
directory first on `sys.path` partway through, and every module not already in
`sys.modules` resolves to LIVE from that point on.

*How it surfaced.* A dry-run selftest crashed with a traceback whose frames walk
from `migration_dryrun/.../enforcement.py` straight into
`/home/pdeane/code/edu.memphis.psych/scoring/agreement.py`. The sandbox was
executing the live scorer. Since the selftest writes module files by path and its
repair net restores them by path, a sandbox run can in principle write the live
tree — and live's `agreement.py` was in fact found mutated-and-unrestored during
a concurrent live run.

*Why it matters beyond one traceback.* Every dry-run measurement in this plan was
taken through an interpreter that may have been running an unknown mixture of
sandbox and live modules. §0's own amendment already says the sandbox figures are
"sandbox facts until re-measured against live"; this is a sharper version of the
same warning — they may not even be sandbox facts.

*Mitigation.* The insert must be derived, not named:
`str(pathlib.Path(__file__).resolve().parent)`, which is correct in both trees
and cannot point at the wrong one. Until that lands, treat any dry-run result
whose code path can reach `sweep_readout` as provisional, and NEVER run a dry-run
selftest concurrently with a live one — the two can write the same files.

*The general rule.* A sandbox that shares a filesystem with production is only
isolated where every path is relative. One absolute path inside one function is
enough to undo it, and it will be invisible to any check that looks at imports
rather than at calls.

**T33 · Probing a check in isolation validates nothing about the suite.** Each
of 06b's sixteen selftest cases was probed alone first — install the breakage,
call that one check, watch it fire. All sixteen passed. Three then broke the
SUITE, because a case does not call its check: it calls `enforcement_audit()`,
which scores every item through both engines, so an injection must leave the
rubric valid for **all** of that, not merely for the check it targets.

* `{"key": ..., "of": [...]}` fired `check_one_writer_per_computed_key` and then
  crashed the scorer on `rule["left"]` — `KeyError`, 86 cases in.
* the repaired rule then needed a slot carrying `verdicts`; `state_a1` has
  `codes` and raised `KeyError: 'verdicts'`.
* a credit row named `orphan_slot_zz` fired its own check and took the audit down
  two cases later: `agreement.score_slots` treats a rubric credit name with no
  matching sheet slot as a hard `CallFailed`.

Each cost a ~90-minute suite run, one failure per run, and each looked like a
new problem rather than the same one.

*Mitigation.* `migration/stage06b_validate_injections.py` runs every injection
against the FULL audit in one pass — install, whole audit, report
fired/didn't-fire/crashed, restore — so sixteen cases are validated in one sitting
instead of sixteen runs. Run it after touching any injection and before the suite.

*And the corollary worth keeping:* the injection that finally fires is the
documentation of what the check actually reads. Four first attempts did not fire,
and each failure was the check's real contract asserting itself — a slot with no
`verdicts` is COMPUTED, not asked; the unreachable-verdict check takes its offered
set from the `.olx`, so the injection must REMOVE a map pair; box deixis only
fires from fields that reach `build_prompt`; and a check with standing findings
needs the inverted arm.

**T29 · Re-deriving an extraction rule loses what the original found.** Stage
06b moved the rubric commentary out of `rubric_hN.py` into
`RUBRIC_DECISIONS.md`, so `olx_prompts.prior_record` — which read the modules as
TEXT, a coupling no import scan can see — would survive 6c's delete. The first
extractor was written from a reading of what `prior_record` *does*: comment runs
of four or more lines, scoped to the item's `"id": "<item>"` dict span. That is
the rule's FIRST branch. It has a second: where an item has no literal dict
entry, `prior_record` locates the FACTORY that builds it (`_example_use_item("T1"…)`)
and takes the comments inside that function's span. Missing the branch cost ten
blocks across three items, and `T1`, `T2` and `D2` — every one of them built by
a factory — extracted to nothing at all while the run still looked successful.

*Mitigation.* When a migration must preserve what a function finds, lift THAT
FUNCTION'S code, from git if it has already been edited, and run it. Do not
re-derive it from its docstring or from reading it. Then freeze the pre-change
output as an oracle and diff the post-change output against it word for word,
with only the citation scaffolding masked — the prose is the payload and the
line numbers are expected to move.

**T30 · Moving prose between file types moves it between SCANNERS.** The same
migration added a finding to the audit: `PROSE NUMBER CONTRADICTS THE LEDGER`,
on a sentence that had been sitting unchanged in `rubric_h1.py` for weeks.
Nothing about the sentence changed. `measured.prose_claims` globs `*.md`, so
the note became reachable for the first time by moving, and the checker met a
construction it had never been shown: `"Q4b fell from 16-17/19 to 13-14/19"`, a
verb of change reporting an edit that was measured and REVERTED. `_HISTORICAL`
knew `was`, `previously`, `originally`; it did not know `fell from … to`.

*Mitigation.* Expect a file-type change to recruit new checks, and run the
baseline comparison as part of the move rather than after it. The finding here
was correct behaviour by a checker seeing new input, not damage — but it is
indistinguishable from damage until you read it, and it must be resolved
(exempted with a reason, or the prose corrected) before the stage can claim its
baseline. Widening a checker to quiet a finding is only safe once you have
measured the blast radius: apply it in memory, re-run the check, and confirm the
only claim that disappears is the one you meant to exempt.


---

## 11 · Open decisions — gated at stage 00, not merely "early"

> These are **stage 00 gate items** (§7). "Take early" proved too weak: nothing stopped the
> sequence beginning with them open, and three of the four change a later stage's shape or its
> budget. §3.2's tag question is a fourth, added 2026-09-13, and it is the one that decides
> whether the migration costs nothing or ~9,400 calls. §11.4 is a fifth, found the same day by
> the script that would have performed the registry step, and it is the one that cannot be
> deferred at all: stage 00 IS the stage that adds the attribute.

1. **Rubric as course child or referenced sibling** (§3.3). **DECIDED 2026-09-13: a COURSE
   CHILD.** `<Course>` carries the rubric as a child, as §3.3 already draws it, because the
   rubric's scope IS the course — a rubric that outlived its course would be a rubric with no
   subject. This is the simpler of the two and the one C5 is written for.

   *What it gives up, stated so the trade is on the record:* two courses cannot share one rubric.
   Nothing in the current content needs that, and inventing the indirection for a second course
   that does not exist is how a data model acquires a joint nobody uses.

   *What it costs to reverse, which is less than it looks:* promoting a child to a referenced
   sibling is a content move in `psychology/`. It does not touch any `<LLMAction>` tag, so no
   `prompt_sha` moves and no sweep is owed — the reversal is a re-parenting plus `<Course>`'s
   shape, which is stage 3a's business. That asymmetry is the reason to take the simple option
   now: the expensive direction is the one that is cheap to undo.

   *Binding on stage 3a:* the `<Course>` block type is authored with the rubric nested, not
   referenced.
2. **Whether the paper scorer must run with no OLX present at all. DECIDED 2026-09-13: NO.**
   Paper scoring never runs where `psychology/` is not checked out, so **stage 06 targets the
   rubric object DIRECTLY** and the `rubric --export` bundle is NOT built as part of this
   migration.

   *Why the direct target is the right one and not merely the cheaper one.* The migration's end
   state, reached at 6c, is that **no scorer holds rubric data of its own**. An export bundle is
   another copy of that data; it differs from `rubric_hN.py` only in being generated rather than
   hand-written, and it would arrive with exactly the obligations this plan already knows are
   expensive — its own fingerprint, its own staleness rule, its own check that it has not drifted
   from the element it was generated from (R12, T5). Introducing that to serve a consumer that
   does not exist would spend the migration's whole point on a hypothetical.

   *What this binds.* Stage 06's `6b` builds `score.py` from the rubric element read out of
   `psychology/`; its gate — `fingerprint_text` unchanged for all 26, corpus replay identical —
   is measured against that target and no other. R10's "single *source* without single
   *location*" stays available as a LATER option, not a stage-06 obligation.

   *The condition that would reopen it, so the reversal is recognisable rather than rediscovered:*
   a paper-scoring consumer that cannot see `psychology/` — a standalone grading job, a separate
   CI runner, another machine. That is an additive change (`rubric --export` plus a reader) and
   does not undo stage 06; it is not a reason to build the bundle now.

   **"THE RUBRIC OBJECT" MEANS THE EXPANDED ONE.** Added 2026-09-14, because the phrase is
   otherwise an invitation to re-implement. Handout 2 builds 12 of its items from FOUR templates
   (§3.1), and `agreement.load_action` parses the `.olx` with its own regexes: Python does not use
   lo-blocks' parser. So if templates survived into what Python reads, Python would need its own
   expander, and that is two implementations of one rule -- the drift this migration exists to
   end. Templates are therefore expanded by the BUILD and materialised as literal `<Item>`s, and
   every Python reader, `score.py` included, sees ordinary items and needs no template grammar at
   all. A later attempt to teach Python the template syntax is a regression, not an optimisation.
3. **Whether `paper_opus` participates in the acceptance sweep. DECIDED 2026-09-13: NO — it is
   excluded, and this paragraph is the declaration the gate requires.** `paper_opus` does not join
   the acceptance sweep and its columns do not block the entry condition. 1c stays measured on it
   and is re-measured separately when its own question is asked.

   *Why, in the order the reasons matter.* **It cannot do the job acceptance needs.** The column
   differs from the others on two axes at once — a different model *and* different tool
   availability — so a difference it shows is unattributable, and acceptance exists precisely to
   attribute differences to the migration. **Participating would mean manufacturing the evidence,
   not checking it:** measured 2026-09-13, 25 of its 26 columns are ABSENT and the 26th (1c)
   carries a stale prompt, so satisfying the clause costs ~120 calls per item per side — roughly
   **3,000 calls** — to create measurements that then cannot be used for the comparison anyway.
   **And the coverage lost is one item**, because 1c is the only item ever measured there.

   *What it buys.* The entry condition falls from **36 failing columns to 10**: 7 paper columns
   carrying a stale prompt (1c, D1, D2, Q2, Q4a, Q4b, Q5), which are genuine sweeps, and 3 stale
   SCORER columns (`olx`/3, `python`/2b, `python`/3), which a re-record clears for nothing — see
   §7a's demotion rule. That is the real entry cost of stage 00, and it is now stated rather than
   hidden behind a column nobody intends to use.

   *The limit of this decision, stated so it is not read as more than it is.* Excluding the column
   from ACCEPTANCE does not retire it. It stays in the ledger, `SIDE_CONTRACT` still governs it,
   and any claim made FROM it still needs its own justification — a non-comparable column is
   excluded from the gate, not licensed as evidence elsewhere.

4. **What the reference attribute is NAMED — `rubric` is already taken. DECIDED 2026-09-13:
   `rubricDef`.** The reference attribute is `rubricDef`; `rubric` keeps its existing meaning on
   `LLMGrader` and is never added to `LLMAction`. The name says what the value IS -- the
   *definition* the sheet is a projection of -- and it cannot be misread as the grading prose the
   other block carries. Everything below is the reasoning that forced the rename, kept because the
   collision is permanent and the next person to reach for `rubric` needs to find this. Found by
   stage 00's registry script, which refused to run. `LLMGrader` has carried a `rubric` attribute
   since long before this plan, and it means something else entirely:

   | block | `rubric` means | read by |
   |---|---|---|
   | `LLMGrader` (existing) | *"Grading criteria the LLM applies"* — free **prose** | the **model**, as instructions |
   | `LLMAction` (proposed) | the rubric **element** this sheet is generated from — an **id** | the **build**, never the model |

   Per-block zod schemas keep these separable, so nothing fails to compile — this is not a
   correctness bug, it is a legibility one, and it is permanent. Two blocks can sit in one
   document with one attribute name carrying opposite kinds of value, while `LLMAction.md` and
   `LLMGrader.md` document `rubric` as two different things a page apart. It also reaches the
   **shared** registry: `sheetAttributes` is a single list and the psych audit derives
   `KNOWN_ACTION_ATTRS` from it, so the name stops being private to a block the moment it is
   registered there.

   *The cheap answer is a distinct name*, and `rubricDef` is the one taken. Renaming later is the expensive path: by then the attribute is
   in two repositories, 26 tags, both registries and every generated body, and moving it walks
   straight into T5, since the `.olx` tag changes and every `prompt_sha` moves with it.

   This **blocked** stage 00's registry step until it was written down here; the script refuses
   `--apply` without `--name-decided` for exactly that reason. C2 also applies to whatever is chosen: the name and its description
   must be content-neutral.

---

### 11.5 · Where each rubric field lives — SETTLED at stage 05

Completing the rubric object forced an allocation for eighteen fields, and C2
decides it rather than convenience:

1. **Generic facts become attributes in lo-blocks.** `label`, `increment`,
   `deriveFromCredit`, `blankCode`, `expectedType`, `unreachableCodes` on
   `<Item>`; `item` and `verdicts` on `<Cover>`. None of them name subject
   matter.

2. **Course vocabulary rides on `conditions` and `params` as names-as-data.**
   `cadence`, `avoidance_scores`, `reads_utb_choice`, `move_pick`, `graph_item`
   are subject matter -- the user's rule is explicit that even a word like
   *cadence* is course-specific -- so the engine carries them as declared names
   whose meaning it does not hold, and the COURSE repo's reader is where knowing
   what they mean belongs. Two of them were already declared this way for the
   prompt side, which is the pattern confirming itself.

3. **`oc_gates` collapses onto `<Slot>`, and that was measured, not assumed.**
   Every gate key is already a slot carrying `gate="true"`, and the gates run in
   slot order on all four items that have them. So the only facts not already
   held were which deduction a failing gate charges and why: `charge` and
   `because`. A separate ordered block would have repeated the sheet. The
   `because` text cannot live on the `<Deduction>` -- one code (`NOT_OC`) is
   charged by five gates with five different reasons.

4. **A named verdict vocabulary is a `<Verdicts>` declaration.** The modules'
   `SLOT_OPTIONS` table held the contents while the `.olx` named the vocabulary
   through `seg="pick(name)"` and said nothing about what was in it. `<Verdicts>`
   existed for exactly this and had no user until now. The mapping is 1:1 --
   each `pick()` name is one vocabulary on the corpus -- so the reader resolves
   a slot's pick back to its options and rebuilds `SLOT_OPTIONS` unchanged.

**The rubric surface `olx_prompts` actually reads is four names:** `BY_ID` (12
uses), `ITEMS`, `SLOT_SPEC` and `SLOT_OPTIONS` (reached by `getattr`, so it does
not appear in an attribute grep and was nearly missed).

---

---

### 11.6 · Python reads the rubric with its OWN reader — SETTLED at stage 05

The rubric object is parsed twice: once by lo-blocks' `parseOLX` for the app, and
once by `scoring/rubric_reader.py` for everything in this repo. That is
deliberate and it is not the duplication C1 forbids.

* **What must never be duplicated is the RULE, and it is not.** Both readers read
  one file. A second reading of one source is a consumer; a second copy of the
  rubric would be a source.
* **Python already reads `.olx` with its own regexes** -- `agreement.load_action`
  does it today. Introducing an XML parser here would create two readings of one
  file inside this repo that can disagree about an entity or a CDATA block, which
  is a worse failure than the one it would prevent.
* **The reader needs no template grammar.** The build materialises `<ItemTemplate>`
  into literal items, so Python sees ordinary items only. The expansion rules live
  in exactly one place.
* **It returns the modules' own shape** -- `ITEMS`, `BY_ID`, `SLOT_SPEC`,
  `SLOT_OPTIONS` -- on purpose. The point of the stage is that provenance moves and
  consumers do not.

**The `RUBRIC_SOURCE` switch is the PROOF, not a rollback hatch.** A stage that
claims "not one byte moved" has to be able to produce both sides, and
`stage05_gate.py` generates all 23 bodies from each and diffs them. Do not delete
it as dead configuration while `rubric_hN.py` still exists, and do delete it in
the same change that removes them -- at stage 06c, where the Python rubric data
goes. Left standing after that it is a switch with one working position.

---

### 11.7 · Module-level rubric tables — SETTLED at stage 06b

`rubric_hN.py` carries three kinds of module-level name beside `ITEMS`, and they
need different answers:

1. **Selectors** (`CONTINGENCY_GATE_ITEMS` and five siblings, all handout 2) are
   the **inverse index of a per-item condition**. `MOVE_PICK_ITEMS = ("PR",)` is
   the same statement as PR declaring `move_pick`, which stage 05 had already
   migrated without noticing it was the same fact. They are emitted as
   `conditions` on the items they name and rebuilt on the reading side, so they
   need no home of their own. This also repairs what
   `check_selectors_govern_something` was written to catch: a tuple whose slot
   was deleted stays defined and governs nothing, whereas an unconsulted
   CONDITION is visible as a name nothing reads.

2. **Tables keyed by item id** -- `OC_GATES`, `FORBID`, `MAPS` -- ARE the inverse
   index of the matching per-item field, and the reader derives them.

3. **`EXPECT` IS NOT, AND THAT IS THE WARNING.** It reads exactly like the
   others and it is a PARTIAL authoring table: one of two sources merged into
   `item["expect"]`, holding one rule where five items carry one. Deriving it
   would have answered a question about the rubric with a smaller number than the
   rubric holds, and the check reading it would have gone quiet rather than
   wrong. Ten such names were mapped on the family resemblance; **three** were
   real, six named tables no module has, and `EXPECT` was the trap.

4. **Module-level PROSE constants** (`_OC_FRAME`) are already in the rubric --
   this one as the first `<Guidance>` entry on all twelve handout-2 items -- and
   need only a name that says how to FIND them. It is exposed as
   `SHARED_GUIDANCE` and defined as the INTERSECTION of every item's guidance,
   not as "the first entry": measured on the corpus exactly one entry is common
   to every item, so the set operation finds it without anyone knowing which
   item or which position. Reading the enclosing frame instead would have handed
   its one reader 254 domain words where it wants 58.

**The rule this settles: verify each derived name against its module, one at a
time, before serving it.** A module-level table keyed by item id is not
necessarily the inverse index of the matching per-item field, and the failure is
silent in the safe-looking direction.

---

### 11.8 · `check_selectors_govern_something` — part A RETIRES at 6c, part B stays

**Settled 2026-09-14.** The check has two halves and the migration treats them
differently, because it dissolves one hazard and leaves the other untouched.

**Part A retires.** It asks whether each `*_ITEMS` selector in `rubric_h2` still
governs a slot or a paragraph. Measured: all 17 selector references live INSIDE
`rubric_h2.py`, which 6c deletes; nothing outside reads them (`score.py`
imported five and used none). The selectors are a BUILD-TIME device -- they
decide which items get a slot -- and the emitted rubric already carries those
slots on those items. After the build has run there is no selection step left,
so there is nothing for the check to find. It is retired, not re-pointed.

*This is a retirement with a measured cell behind it, so record what it cost and
why it is safe.* `TYPE_BARRIER_ITEMS` outlived the slot it governed and NR/p14
went 6/6 -> 0/6 while every remaining check on its sheet passed. That failure
needed a selector and a slot to disagree. In the emitted rubric the slot is
either on the item or it is not, and a slot that is not there cannot be selected
by something that no longer exists.

**Part B stays, unchanged.** "The scorers read a check key that no item's sheet
emits any more" is the same hazard seen from the reading end, and it is NOT
structural to the module: it survives the migration intact. It already reads
`config(h)["rubric"]`, so it needs no work.

**Two consequences, both required:**

1. **Stop emitting the selector-only conditions.** `barrier_pick`,
   `cadence_barrier`, `contingency_gate`, `polarity_gate` and `type_match` were
   emitted at 06b solely to rebuild tables that will have no reader. Keep
   `cadence` and `avoidance_scores` (a frame segment's `ifDeclared` consumes
   them) and keep `move_pick`, `graph_item` and `reads_utb_choice` (the modules
   carry them as per-item fields, so the equivalence check requires them).
   `move_pick` serves both purposes and stays for the second.

2. **Remove the `*_ITEMS` synthesis from the reader, and do not leave it
   returning an empty tuple.** A synthesised accessor that answers `()` when no
   item declares the condition is C1's named failure mode in miniature: a caller
   asking a question the rubric no longer answers gets a plausible empty result
   and reports success. With the synthesis gone, a stale caller raises
   `AttributeError` and says so.

### 11.9 · The compact tag — STRUCK. Decided 2026-09-14.

**§3.2 draws an `<LLMAction>` with no `slots=`, no `derived=` and no body, all of
it resolved from the rubric at build. No stage in §7 produces it.** The plan
required this closed before stage 03. Stages 03 through 06 ran with it open.

*What the dry run has already established, at zero calls:* the byte-identical
branch works. 23/23 bodies assemble byte-equal from the emitted rubric; the
stage-00 prompt oracles are unchanged across 26 items on both sides; no
`prompt_sha` moves; the audit finding-set is identical. The cheap branch is not
merely cheaper, it is **measured**.

*What the compact branch would cost.* `prompt_sha(item, "olx")` hashes the
served tag ENTIRE, so collapsing a tag moves every item's prompt sha. T5 prices
that at **≈9,400 calls** corpus-wide, affordable only under §7a's demotion rule
and only if the ASK is provably unchanged.

**DECIDED BY THE USER, 2026-09-14: option (A). §3.2's compact form is STRUCK.**
The `.olx` keeps generated bodies and sheet attributes. The rubric is the SOURCE
of those bytes without being their runtime container, and that is the end state
— there is no tenth stage and no ~9,400-call branch. The migration's goal, no
scorer holding rubric data of its own, is reached at 6c without it.

*What this closes:* the last of the five stage-00 gate items, and the only one
that could still have changed the shape of a stage already executed. Stages 04
and 05 built the branch that has now been chosen, so nothing executed needs
revisiting.

*What it gives up, on the record:* the `.olx` stays verbose, and a reader has to
know the bodies are generated rather than authored. That is a documentation
obligation, not a defect — and §3.2 keeps the compact example as a REJECTED
alternative rather than deleting it, so the next person does not re-propose it
without finding the price.

The options as they stood:

* **(A) Strike it.** Declare §3.2's compact form out of scope, keep the `.olx`
  carrying generated bodies and sheet attributes, and note that the rubric is the
  SOURCE of those bytes even though it is not their runtime container. The
  migration's goal — one source, no scorer holding rubric data — is already met
  at 6c without it. Cost: zero. Loss: the `.olx` stays verbose and a reader must
  know the bodies are generated rather than authored.
* **(B) Schedule it as stage 09.** A tenth stage after acceptance, with its own
  entry condition and the ~9,400-call price, or a demoted subset. Nothing in
  stages 00–08 depends on it, which is precisely why it can be deferred cleanly
  rather than retrofitted.

**Why (A) and not the price argument.** It is not that (B) is expensive. It is
that the compact tag buys inspectability the build already provides
— the generated body is in the file where anyone can read what the grader was
asked, and §3.2's own R1 calls that "resolved by design". Collapsing it trades a
readable artifact for a terser one and pays 9,400 calls for the privilege.

*The cost of having left it open is on the record:* four stages were executed
against a plan that contradicted itself about what they were building. It cost
nothing this time only because the stages happened to build the branch that was
later chosen.

---

### 11.12 · WHICH file is the rubric? — CLOSED 2026-09-14: ONE file, under the course id

**Measured in the dry run, 2026-09-14.** Five files in `psychology/` declare a
`<Rubric>`, and the course points at the wrong one:

| file | lines | id | items |
|---|---|---|---|
| `bmod_rubric.olx` | 34 | `bmod_rubric` | 4 + 1 `<ItemTemplate>` |
| `bmod_rubric_pr.olx` | 74 | **`bmod_rubric`** | 1 |
| `bmod_h1_rubric.olx` | 255 | `bmod_h1_rubric` | 8 |
| `bmod_h2_rubric.olx` | 575 | `bmod_h2_rubric` | 12 |
| `bmod_h3_rubric.olx` | 134 | `bmod_h3_rubric` | 6 |

Three things are wrong at once:

1. **`<Course>` references `bmod_rubric`**, which is a 34-line stage-3b
   demonstration — the four type-example items expanded from a template — not
   the rubric.
2. **The real rubric is 964 lines across three files holding all 26 items, and
   nothing references any of them.** Stage 04 emits them under per-handout ids
   that no course, no `<Use>` and no `<LLMAction>` names.
3. **Two files claim `id="bmod_rubric"`** — the 34-line demo and
   `bmod_rubric_pr.olx`, stage 3b's single-item byte-equality proof. Nothing
   references the `_pr` variant, and an id claimed twice is a resolution nobody
   should have to reason about.

**DECIDED BY THE USER, 2026-09-14: stage 04 emits ONE file under the course id.**
`bmod_rubric.olx` now holds all 26 items, 197,207 chars, under the id `<Course>`
resolves; the three per-handout files are superseded and removed by the emitter,
which reports them rather than deleting silently. Stage 3b's byte-equality
demonstration keeps its artifact under a distinct id (`bmod_rubric_pr_demo`), so
the collision is gone without discarding the proof.

*The rubric does not learn what a handout is.* Items are emitted in handout
order because that reads well, and the reading side partitions them by the
item's own content element exactly as `olx_prompts.HANDOUT` already derives it.
Handout membership is a property of the CONTENT; a rubric declaring it would
hold the same fact twice, in a second place free to disagree.

*Verified:* equivalence 0 differences on all three handouts, emission idempotent,
and `migration/join_check.py` — written BEFORE the fix so it would fail on the
real defect, which it did on all three faults — now passes.

*What it cost downstream, which is T28's point made twice:* three consumers held
the old shape and had to follow. `enforcement`'s capture cache key globbed the
three files and RAISED when they went, so `_request_capture` returned "the key
cannot be computed" and the audit's finding-set moved — a caught exception
becoming a changed finding. The stage-04 assembly probe threw ENOENT and the
gate read it as an assembly failure. And the stage-05 gate's cache-key assertion
kept PASSING for the wrong reason, because `bmod_rubric.olx` happens to contain
the substring `_rubric.olx` it was matching.

The superseded framing, for the record: does `bmod_rubric` become a container whose children are the
three per-handout rubrics, does `<Course>` reference all three directly, or does
stage 04 emit ONE file under the course-level id? And which of the two 3b
demonstration files is retired, since both were authored to prove a mechanism
rather than to ship.

**Why it blocks 6c rather than merely being untidy.** 6c deletes
`rubric_hN.py` on the grounds that the rubric object is now the source. That
argument requires the rubric object to be *reachable as the rubric* — and today
the artifact the course resolves holds 4 items of 26. Deleting the modules while
the served rubric is a demonstration file would leave the corpus with no
reachable rubric at all.

*It costs no sweep to fix.* This is content in `psychology/`, and §11.1 already
records that re-parenting a rubric touches no `<LLMAction>` tag, so no
`prompt_sha` moves.

---

### 11.10 · What 6c actually deletes — CLOSED 2026-09-14

**DECIDED BY THE USER, 2026-09-14.**

| artifact | disposition |
|---|---|
| `rubric_h1.py`, `rubric_h2.py`, `rubric_h3.py` | **DELETED** |
| `score_h1.py`, `baseline_h1.py` | **RE-POINTED** at the accessor |
| `gold_slots_q6.py` | **RE-POINTED** — it is in scope |
| `RUBRIC_SOURCE` and the `dual` machinery | retires with the modules (§11.6) |

**THE ORDERING THE DELETE IMPOSES, and it is not obvious from "delete the
modules".** `dual` mode proves the rubric object and the modules agree by
COMPARING them. Once the modules are gone there is nothing to compare against —
`differences()` has no left-hand side and `stage05_rubric_equivalence.py` can
never run again. So:

1. Re-point the three files above. Nothing may still import a rubric module.
2. Apply §11.8's two consequences — stop emitting the five selector-only
   conditions, and remove the reader's `*_ITEMS` synthesis so a stale caller
   raises instead of receiving `()`.
3. **Run the equivalence check one last time and record the result in this
   document.** It is the final evidence that the object says what the modules
   said, and after step 5 it is unreproducible. A migration that deletes its own
   baseline without recording the last reading has destroyed the only proof it
   was faithful.
4. Demonstrate every re-pointed check still FIRES — by its self-test case, not
   by the audit being quiet (O2, C1). A check whose source vanished returns `[]`
   and reports success.
5. `handouts.py` stops importing the modules and serves the object
   unconditionally; `RUBRIC_SOURCE` and `_VerifiedRubric`'s comparison go with
   them.
6. Delete the three modules, declaring every dropped name to `editguard`.

**THE LAST EQUIVALENCE READING — taken 2026-09-15, step 3 of the ordering above.**

This is the final evidence that the object says what the modules said. After step
5 the modules are gone, `differences()` has no left-hand side, and
`stage05_rubric_equivalence.py` can never run again. Recorded here because a
migration that deletes its own baseline without writing down the last reading has
destroyed the only proof it was faithful.

| handout | items | byte-identical from both provenances | differences |
|---|---:|---:|---:|
| 1 | 8 | 8 | **0** |
| 2 | 12 | 12 | **0** |
| 3 | 6 | 6 | **0** |
| **total** | **26** | **26** | **0** |

*What was read, by content hash, so the reading can be attributed to exact bytes:*

| artifact | chars | sha256[:12] |
|---|---:|---|
| `psychology/bmod_rubric.olx` (emitted) | 196,957 | `e0cfc8592890` |
| `scoring/rubric_h1.py` | 202,906 | `60674dd0eea1` |
| `scoring/rubric_h2.py` | 87,873 | `40508e98282f` |
| `scoring/rubric_h3.py` | 50,676 | `34b74ca4143a` |

`stage05_rubric_equivalence.py` reports **PASS — the rubric object says
everything the modules say**, h1/h2/h3 each 0 differences. The frozen
`goldens/rubric_oracle.json` was independently re-verified the same day against
all 15 frozen keys and still matches the modules, so the comparison survives the
delete in the stronger form: not "do these two current sources agree", but "does
the object still say what the modules said on the day they were deleted".

*The superseded framing:*

`6c` is described as "delete the Python rubric data". The delete list had never
been written down, and three of its entries were not obvious:

1. **`rubric_h{1,2,3}.py`** — the intended targets. Uncontroversial.
2. **`score_h1.py` and `baseline_h1.py`** — both carry
   `from rubric_h1 import BY_ID, ITEMS` at MODULE level. Unlike every
   function-local read in the tree, these fail at IMPORT the moment the module
   goes, and they take every consumer of those files with them. They must be
   re-pointed in 6b, not discovered at 6c. *(Patches prepared in the dry run,
   verified at 0 bare name tokens, not yet applied.)*
3. **The five selector-only conditions and the reader's `*_ITEMS` synthesis** —
   decision 11.8's two consequences, decided and not yet implemented. The
   synthesis must GO rather than be left answering `()`, because a stale caller
   receiving a plausible empty tuple is C1's failure mode in miniature.
4. **`RUBRIC_SOURCE`** — 11.6 says the switch retires in the same change that
   removes the modules, since after that it is a switch with one working
   position. Confirm at 6c.

**Also open: does `gold_slots_q6.py` belong on the list?** It reads `BACKLOG.md`
and is handout-specific; it was never classified.

---

### 11.11 · The self-test's own defects — OPEN, and the gates depend on them

Stage 07's gate is *"selftest accounts for exactly `SELFTEST_EXPECTED`
breakages"*. That gate cannot be trusted while the self-test can damage the tree
and still report success. Two defects, both found in the dry run on 2026-09-14,
both present in live:

1. **A case does not restore its own injection.** Measured on a quiet tree with
   nothing else running: `agreement.py` was injected at 17:02:28 and never
   written again across the remaining 29 minutes, while three other injected
   files were restored correctly after it. The run reported
   `restored state is clean: True (VOID -- source moved)`, printed
   `70 of 70 expected`, **exited 0 and stamped `.selftest-passed`** — which
   `measured.selftest_owed` reads as evidence the checks were re-tested.
2. **The process guards are machine-wide in one direction only** (T25). Live has
   `_selftest_source_root` so a sandbox self-test does not refuse live sweeps;
   nothing stops a live sweep refusing a sandbox self-test, and nothing stops
   two self-tests running at once — which is how one of them came to read a file
   the other had already mutated.

*Fixed in the dry run, not in live:* a moved source now FAILS instead of voiding
and does not stamp a pass; a snapshot-and-repair net under all 70 cases puts the
tree back and still fails; both guards are tree-aware; and a second concurrent
self-test is refused before any injection happens.

**The decision: when do these port to live?** They are not migration work, but
the migration's gates rest on them, and live's queued self-test will run the
unfixed code — leaving live's `agreement.py` with an unbound `all_hit` that
parses, imports and passes every audit.


---

### 11.13 · NO HARD-CODED PATHS — **DECIDED 2026-09-16: fail closed. 12 findings cleared.**

**The policy: no module spells a filesystem location. `paths.py` resolves them,
and an exception is declared with its reason.** A literal path does not fail on
the wrong machine or the wrong tree — it SUCCEEDS on it, which is why this class
of defect keeps arriving disguised as a passing run.

`check_filesystem_locations_come_from_paths_py` (2026-09-16) reports **12**,
in four kinds:

| kind | where | why it bites |
|---|---|---|
| **unconditional** | `agreement_app.py:1648`, `enforcement.py:4304` — `/home/pdeane/code/update/lo-blocks` | ignores `$LO_BLOCKS`; measures the wrong checkout in silence |
| **UID baked in** | `score.py:1161`, `simulate_h3.py:65` — `MEDIA_DIR = "/tmp/claude-1000/..."` | correct for one account on one machine |
| **duplicated resolution** | `self_graded_misses.py:39` — `os.environ.get("COURSE_DATA", "~/molly_data")` | re-implements `paths.DATA`, and will drift from it |
| **fallback** | `enforcement.py` ×5, `measured.py` ×2 | **the design question below** |

The first three kinds are bugs and want fixing. **The seven fallbacks are a
design question, not a typo:**

    enforcement.py:6758, 6909, 10405, 10476, 11083
    measured.py:373, 4445
        root = _pl.Path(getattr(_paths, "OUT", "/home/pdeane/molly_data/out"))

The fallback fires when `paths` has **no `OUT` attribute at all**. Three
behaviours are available and they are not equivalent:

| | behaviour when `paths.OUT` is absent |
|---|---|
| **(a) as written** | silently read the developer's own artifact directory |
| **(b) fail closed** | raise, naming `$COURSE_OUT` — `paths.require()` already exists for this |
| **(c) resolve** | `os.environ["COURSE_OUT"]`, i.e. duplicate `paths.py` badly |

**(a) is the least safe available behaviour and it is what ships.** A harness
pointed at a sandbox, a second checkout, or the backup copy gets the developer's
live artifacts instead, and nothing says so: the run succeeds, against the wrong
tree. That is the same shape as the dry run's eleven literal sandbox paths, and
the same shape as the `.selftest-passed`/oracle staleness traps — **a wrong
answer that looks exactly like a right one.**

**Why it must be decided BEFORE stage 00 and not after.** Stage 00 freezes the
enforcement baseline. Whatever these checks do on the day of the freeze becomes
the baseline every later stage is compared against, so changing them afterwards
moves the finding set and makes neutrality unreadable — and leaving them means
the migration's own measurements can silently come from the wrong directory.

**DECIDED: (b), fail closed — and done.** `check_filesystem_locations_come_from_paths_py`
now reports **0**. What changed:

* `paths.out_root()` — for scripts. Uses the existing `require()`, which exits
  naming `COURSE_OUT`.
* `paths.out_root_or_reason()` — **for checks, which must not exit the process.**
  It returns the reason, and the five call sites now report *"this check cannot
  run, which is NOT the same as passing."* This is the half that mattered: the
  old fallback did not merely read the wrong directory, it read one that might
  not exist, found no files, reported nothing — and **nothing read as clean.**
* `paths.MEDIA` / `media_dir()` — replaces `MEDIA_DIR = "/tmp/claude-1000/..."`
  in `score.py` and `simulate_h3.py`, which baked in a numeric UID and was
  correct for one account on one machine.
* `agreement_app.LOBLOCKS`, `enforcement`'s lo-blocks literal, and
  `self_graded_misses`' duplicated `COURSE_DATA` resolution all now use `paths`.

Two glob PATTERNS remain, declared in `ABSOLUTE_PATH_EXCEPTIONS` with their
reason: they are the subject of a check, not locations it reads from.

**The policy stands after the fix**: the check is registered in the audit, so a
new literal is a finding rather than a habit.

### 11.14 · A corpus reference inside `slots=` — **DECIDED 2026-09-16: hide the reference's colons. Fixed both sides.**

The slot-sheet attribute is colon-delimited — `name:description:verdicts@weight`
joined by `|` — and `parse_slots` splits on **every** colon:

    parts = [p.strip() for p in entry.split(":")]
    raw_key, label, seg = parts[0], parts[1], parts[2]

A corpus reference is colon-heavy by construction, so a description carrying one
shifts every later field:

    modify_stated:Says whether it is {{corpus:Q4b/p20:modify:17:40:sha=f3f224b807af}}
                  |__ label ends at the first colon inside the reference
                                      |__ "Q4b/p20" is then read as the VERDICTS

The generator duly emits ``- `modify_stated` — `Q4b`/`p20`:`` where the rubric
says `met`/`absent`. Measured across the rewritten history: **107 of 114
generator states**.

**THIS IS NOT ONLY A REWRITE PROBLEM.** The generator writes that attribute FROM
the rubric description, so the moment any slot description contains a reference —
which is the whole direction of travel — the generator misreads what it just
wrote. The live tree has the same latent defect today; the rewrite merely got
there first.

**The fix is in the parser, and it must land in BOTH.** `olx_prompts.parse_slots`
says in its own docstring that it mirrors `packages/shared/lib/llm/slotSheet.ts`.
Splitting the key off the LEFT and the verdict segment off the RIGHT lets a
description hold anything:

    key, rest = entry.split(":", 1)
    label, seg = rest.rsplit(":", 1) if ":" in rest else (rest, None)

Changing one side only creates precisely the Python/TypeScript divergence that
`check_ref_grammars.py` exists to catch — and that check covers the REFERENCE
grammar, not this one, so it would not notice. **A second equivalence check is
owed for the slot-sheet grammar.**

**Why before stage 04.** Stage 04 migrates the rubric data and stage 05 makes
the build generate from it; both compare `.olx` bytes and `prompt_sha`. With this
unfixed, every slot description carrying a reference produces a wrong verdict
list in the generated body, and the byte comparison fails for a reason that has
nothing to do with the migration.

**DECIDED AND DONE — and the historical states WERE fixed.** The claim above was
wrong: each commit's generator can be reached, because the rewrite already
backdates a shim into every commit. The parser fix rides the same rails.

| where | what |
|---|---|
| `olx_prompts.py` | three sites — `parse_equals`, `parse_slots`, `check_scorer_voice_in_labels` — now share `_split_keeping_refs` |
| `slotSheet.ts` | **seven** sites, not one: slots, onlyif, cover, derived, equals, labels. All use `splitKeepingRefs` |
| every historical commit | the `parse_slots` wrapper is injected by `shims.py`, so each commit's own generator parses correctly |
| `check_slot_grammars.py` | **the second equivalence check.** Feeds seven probe specs through both parsers and compares key, label, options and points |

**Measured:** generator regressions across the rewritten history went from **108
to 0** (chain17). `--check` on the live tree is unchanged at 0 out of date, so
the fix is a no-op on today's content — which is what a latent-defect fix should
be.

**The second equivalence check earned its place immediately.** Run after the
Python fix and before the TypeScript one, it caught three divergences — the
grader and the student would have seen different verdict vocabularies for the
same slot, each side internally consistent and neither complaining. That is the
same failure `check_ref_grammars.py` exists to prevent, one grammar over, and it
would not have been noticed without a check of its own.

## 12 · `VERDICT_VOCABULARY_PLAN.md` is RETIRED — it is not a dependency

Verified against the tree on **2026-09-13**, stage by stage. It is not a companion to sequence
around; it is finished, and the marker that said otherwise was stale.

| its stage | its own status | verified in the tree |
|---|---|---|
| 00–03, 05, 06 | done | done |
| 04 · counts to `count` | "partly — 5 groups ride the legacy side" | **content done**: the 4 remaining `counts=` groups (Q1, Q2, 2b, 3) recorded **0 non-numeric values in 480 observations**. Only a dead fallback remains in the engine |
| 07 · Handout 2 rework | "not done — `matches_chosen_type` still 21×" | **done**: all six items using it are already at the target shape — `observed_type`/`named_type` are PICKS answering `refers_to`, the computed key is plain `met`/`absent` |
| 08 · close the door | "not done" | **subsumed** — the rubric object *is* the door |
| 10 · acceptance | superseded | confirmed; owes no sweep |
| its one named defect | `not_reason` unfixed on Q5 | **fixed** — 0 occurrences; both `example_*` offer `met/absent/wrong_kind/duplicate` |

**Why the status table misled.** Stage 07's evidence was a grep count. On 2026-08-20 twenty-one
occurrences of `matches_chosen_type` meant legacy identity vocabularies; today the same count is
of a slot that already has the target shape. **The marker outlived the thing it described** — and
reading it without checking the tree produced a recommendation to land stage 07 before stage 03,
which would have been work to reproduce a shape that already ships.

**What actually remains: one dead code path, in the engine.** `countedVerdicts` still reads
`checks[g.key]?.count ?? checks[g.key]?.verdict`, tolerating a legacy form no content produces.
Deleting the fallback is a lo-blocks change, so by **O1 it belongs in 3a, not 3b** — it is engine
work, and pairing it with content would be the very violation these invariants exist to stop. It
is optional: leaving it costs nothing but a branch nothing takes.

*Supersedes the 2026-08-14 draft, which assumed render-time assembly and a codebase without the
audit complex. Companion to the verdict-standardisation plan (`VERDICT_VOCABULARY_PLAN.md`),
retired in §12 — verified complete, owes no sweep, not a dependency.*

---

## 13 · Agenda arising from the material classification, 2026-09-23

Folded in from `AGENDA_FROM_CLASSIFICATION.md`, which now points here. It came out
of classifying every material in the two trees against the ten-category scheme in
`MATERIAL_CLASSIFICATION.md`; each item below is a place where that classification
found something sitting in the wrong category, or a module whose two halves belong
to different ones.

**THE ORDER OF WORK, set by the user 2026-09-23.**

    G(a)  ->  G(b)  ->  G2  ->  C  ->  H  ->  B  ->  I

It honours both dependencies this plan states. G2 BEFORE H, because "H assigns one
home per category, and it cannot until each file belongs to one". C BEFORE B,
because they are the two answers to one question -- who produces the handout -- and
C is the cheaper, with B then scoped to the PAGE parts rather than the whole.

C BEFORE H WAS THE ONE GENUINE TOSS-UP and is the user's call, not an inference.
Nothing in this plan settles it. The argument taken: C's proof obligation is
byte-exact reproduction of 23 bodies and 26 attribute sets, which is delicate work,
and doing it on a freshly reorganised tree adds risk that has nothing to do with C.
The argument against, recorded because it is real: H is blocked only by G2, and
doing H earlier means later work lands in its final home instead of being moved
twice.

I IS LAST BECAUSE IT IS INDEPENDENT, not because it is least valuable. Its two
mentions of G2 are methodological -- the false-positive lesson, and "course content
in engine documentation is what G2 removes" -- and neither is a dependency. Its cost
is the four prerequisites in its own section, which are build work.

G(a) -> G(b) is not a preference: G(b) was found BY G(a), and it repairs the very
ledger G(a) writes to.

**State at the time of folding.** D and E are DONE and recorded in place. A, B, C
and F are open. C is the largest and is not new work -- §13 C(i) records what the
prior dry run already built for it. F is ranked above D was, for the reason given
under it.

### A · Split `declaration_source.py` and `generator_source.py` along the seam

Each file holds TWO categories, and that is why every "does this move to the OLX?"
question needed a per-table answer instead of a per-file one.

  declaration_source.py
    -> COURSE METADATA (II):  HANDOUT_FIELDS, CONTEXT_SOURCE,
                              SLOT_STRUCTURE_FAMILIES
    -> DEVIATION RECORDS (II(a)/III): UNCHARGED_VERDICTS,
       DECOMPOSITION_DIVERGENCES, PROSE_ONLY_SLOTS, APP_ONLY_SLOTS,
       COUNTABLE_EXEMPT, PROSE_ONLY_JUDGED_AGAINST, HAND_AUTHORED_ATTRS,
       MULTI_BLOCK_DECLARED
    -> MEASUREMENT HISTORY (III): ASK_EQUIVALENT_PROMPTS, DESIGNED_TEXT, JOBS,
       STAGE, SELFTEST_NAMED_FIXTURES, PROBE_UNREACHABLE_PAIRS, PAPER_ITEM_NOTES*

  generator_source.py
    -> COURSE METADATA (II):  ACTION, RESPONSE, CONTEXT, SHEET_ONLY
    -> CROSS-SCORER DEVICES (III): EVIDENCE, OMIT_GUIDANCE, ITEM_NOTES,
       ITEM_NOTES_WHY, MATCH_DEF/EQUIVALENCE_DEF, SCORING_DIVERGENCES,
       PROBE_REACH_LIMITS
    -> SUBMISSION PARSING (IX): H1_MARKERS, H2_MARKERS, H3_MARKERS

Once split, the rule becomes mechanical: category II moves toward the OLX/
course.json, category III stays, category IX stays. No table needs arguing about
twice. `COURSE_DATA_BUDGET.json` counts per module, so the split changes those
counts and the ratchet must be re-tightened deliberately in the same commit.

#### DONE 2026-09-23 -- proved by a byte-identical export

FOUR MODULES, EIGHT TABLES MOVED. `course_metadata_source.py` takes category II
(`HANDOUT_FIELDS`, `CONTEXT_SOURCE` from declaration; `RESPONSE`, `CONTEXT`,
`SHEET_ONLY` from generator). `submission_markers_source.py` takes category IX
(`H1/H2/H3_MARKERS`). The two originals keep their names and their category-III
contents, so nothing that cites them churns.

`_H*_CTX` deliberately did NOT move. The agenda assigned only the MARKERS to IX,
and those maps are component-id -> item context handed to the grader, which is a
cross-scorer device: being per-handout is not the same as being about parsing.

THE PROOF IS THE EXPORT. Only `rubric_export.py` imports these modules -- every
other consumer reads the exported `course.json` through `coursedata` -- so a
byte-identical export means nothing downstream can have changed. Captured before
the first edit and compared after: sha256 `b884f54e4427c959...`, 375,655 bytes,
identical, and equal to the live course file both times. Belt and braces on top:
all 8 moved tables compared value-identical in their new homes, and all 27 that
stayed compared unchanged.

ONE RESOLVER, NOT A MODULE NAME PER SITE. The exporter groups tables by SHAPE --
item-keyed vs course-level -- and that grouping cuts ACROSS the categories:
`GENERATOR_TABLES` alone spans metadata (`RESPONSE`, `CONTEXT`, `SHEET_ONLY`) and
cross-scorer devices (`EVIDENCE`, `OMIT_GUIDANCE`, `MATCH_DEF`, both
`ITEM_NOTES`). A name-list entry therefore cannot say which module holds it, so
`_authored(name)` resolves across the builders and REFUSES a name two modules
claim -- the characteristic failure of a split being a table copied rather than
moved, which would otherwise be settled silently by module order. Fire-tested.

THE SPLIT FOUND A REAL COUPLING, which is the part worth keeping. The audit rose
44 -> 51: seven `MIGRATED TABLE DOES NOT MATCH ITS SOURCE` findings, one per moved
table, because `migrated_tables.BUILDERS` was a hard-coded pair and the check was
looking in the wrong two files. Fixed at the root rather than by adding two names
in a second place: `BUILDERS` is now the list of record and `rubric_export` reads
it, so a builder added later is found by the exporter and by the audit at once.
Audit back to 44 with a finding set IDENTICAL to the pre-D baseline, not merely
the same count.

`COURSE_DATA_BUDGET.json` re-tightened in the same pass, as this item required:
15 + 16 embeddings became 14 + 10 + 4 + 3 -- 31 before, 31 after, so the
embeddings moved with their tables and none were created or lost.

AND IT EXPOSED ITEM G: neither new module entered `DEFINITIONS.json`, because
new modules never do.

### B · The handouts should be AUTHORED, not generated

Today `bmod_handout1|2|3.olx` are BUILD PRODUCTS of `olx_prompts.py`. That is why
category I currently contains both a source and a build product, and why "the OLX
is the source" is true of the rubric but not of the handouts.

Target: the handouts are hand-authored OLX, and `course.json` says which items
belong to each handout, keyed to the OLX ids, so a scorer can find what to score.

What that requires, in the order it has to happen:
  1. the generated prose in the handouts (`<LLMAction>` prompt bodies and the
     sheet attributes) has to come from somewhere at RUN time rather than being
     baked in at generate time -- or be accepted as authored and checked against
     the rubric instead of rewritten from it
  2. `olx_prompts --write` stops writing the handouts, and
     `check_idmap_is_current` / the prompt-freshness checks change meaning from
     "regenerate matches disk" to "disk agrees with the rubric"
  3. `prompt_sha` currently hashes the SERVED tag; a hand edit to a handout then
     moves it legitimately, so the freshness story needs restating
  4. course.json keeps item -> handout (it already does) and item -> OLX id

### RESOLVED: the item-to-component link lives in the RUBRIC

Decided 2026-09-23. `<Item asks="bmod_h1_q1_llm">` stays where step 3b put it, and
step B's fourth bullet is corrected to match: **course.json keeps item -> handout
and nothing more**; the item -> OLX id link is the rubric's `asks`.

The question was live because the alternative had a real precedent behind it --
`handout` was deliberately kept OFF `<Item>` on the ground that "which handout an
item belongs to is course structure", and the same argument could be made of a
component id. It does not hold, and the reason is worth keeping:

  WHICH HANDOUT an item sits in is a fact about the COURSE -- move the item to a
  different handout and nothing about how it is judged changes. WHICH COMPONENT it
  judges is a fact about the ITEM: change it and the item is judging different
  text. The first is placement, the second is identity, and only the second
  belongs beside the checks that do the judging.

It also keeps the property 3b bought: with `asks` authored on the item, `BLOCKS`
is DERIVED rather than declared, and the link that used to be written twice --
once in `BLOCKS`, once as `prompt_action` -- is written once.

So the division of labour is:
    rubric OLX    what is judged, how, and WHICH COMPONENT it judges  (`asks`)
    course.json   where the item sits in the course                   (`handout`)
                  plus the generator fields that shape the prompt


### C · No part of OLX prompt generation may depend on python

Stated 2026-09-23. For the OLX scorer, what shapes a prompt belongs either (a) in
the OLX rubric, or (b) in a generation chain run by `npm build` -- not in python.

WHERE THE DEPENDENCY ACTUALLY IS, stated precisely because it is narrower than it
sounds: at RUN time the OLX scorer needs no python, because the prompt bodies are
already baked into `bmod_handout*.olx`. The dependency is at BUILD time --
`olx_prompts.py` is what bakes them. So this is not a runtime coupling to break,
it is a PRODUCER to replace.

THE TS HALF ALREADY EXISTS AND IS UNWIRED, which is the important discovery:

    packages/shared/lib/llm/promptAssembler.ts     327 lines -- the prose half
    packages/shared/lib/llm/attributeAssembler.ts  222 lines -- the scoring half
    packages/shared/lib/llm/slotSheet.ts           the answer schema
    packages/shared/lib/llm/materialiseRubric.ts   template expansion -- WIRED
                                                   2026-09-23 as build:expand-rubrics

`promptAssembler` and `attributeAssembler` have NO CALLERS outside their own
tests. They are in exactly the state `materialiseRubric` was in this morning:
written, tested, and producing nothing. Meanwhile `olx_prompts.py` (~3,000 lines)
is what actually writes the shipped prompts. That is one rule with two
implementations, and the python one wins by being the only one plugged in.

WHY IT IS NOW TRACTABLE, and it was not before tonight:
  * the WORDS moved into the rubric -- oc_criteria's frame, the 27 `note:` frames,
    guidance, questions, credit and deduction text. `promptAssembler`'s design
    already assumes this: `Fragments` is supplied by the CALLER and NEVER
    defaulted, because "the KEYS are engine concepts; the WORDS are not".
  * `.stage/expanded` exists -- templates expanded, references intact -- which is
    the artifact an assembler has to read.
  * `renderFrame` in TS and `as_view_frame` in python already implement the SAME
    selection rule, deliberately spelled the same way.

THE SHAPE OF THE WORK
  1. a build step -- `build:assemble-prompts` -- that reads `.stage/expanded`,
     runs the two assemblers, and writes the handouts' `<LLMAction>` bodies and
     sheet attributes
  2. the fragments (the prose keys the assembler needs) sourced from the rubric,
     not from a TS default -- the assembler already refuses to default them
  3. `olx_prompts.py` keeps ONLY what feeds the PAPER scorer; its OLX-generation
     role retires
  4. the freshness checks change meaning with it, exactly as in item B:
     `prompt_sha` hashes the SERVED tag, so "regenerate matches disk" becomes
     "disk agrees with what the assembler produces from the rubric"

RELATION TO ITEM B. B asked for hand-authored handouts; C asks for npm-generated
ones. They are the two answers to the same question -- who produces the handout --
and both satisfy "no python". C is the cheaper one, because the TS assembler is
already written and the rubric already holds the words. B remains right for the
parts of a handout that are PAGE (layout, prose, figures) rather than PROMPT.
The likely end state is both: authored pages, assembled prompts.

PROOF OBLIGATION, and it is the same one used all night: the assembler's output
must reproduce the current handouts byte for byte before the python producer is
retired. Anything else is a prompt change wearing a refactor's clothes, and
`prompt_sha` will say so.

### C(i) · WHAT THE PRIOR DRY RUN ALREADY SETTLED about item C

Checked in `migration_reference` on the user's prompt, and it changes C from "new
work" to "work that was designed, built, and never wired".

THE PRIOR RUN'S README SAYS IT OUTRIGHT:
    "This is stages 02 and 03. The rubric moves into `.olx` as these blocks, and
     `promptAssembler` is what rebuilds the 26 prompt bodies from them byte-exact.
     Without it the migration cannot run at all."

So `promptAssembler.ts` and `attributeAssembler.ts` are not speculative utilities
that happened to go unused. They ARE the designed producer, and the reason they
sit unwired in our tree is that we ported the block family and the assemblers but
never the wiring that drives them.

THE HARNESS AND THE GATE ALREADY EXIST in `migration/`:
    stage02_assembler_surface.py   measures what the assembler must be GIVEN:
        "THE INTERFACE IS NOT A DESIGN CHOICE, it is a measurement... its input is
         whatever the current generator reads -- no more, and provably no less."
        It also feeds stage 03: every `item[...]` key it finds is a field the
        rubric object must carry, "or the assembler cannot be driven from the
        rubric at all".
    stage02_gate.py                the byte oracle
    stage03a_gate.py / stage03b_gate.py   blocks parse and validate; the engine
        stays content-neutral

THE ACCEPTANCE CRITERION, from the gate's own docstring, and it is exact:
    23 BODIES AND 26 ITEMS' ATTRIBUTES -- three items carry no `<LLMAction>`.
    And WHICH bytes: the GENERATOR's output, not the .olx element text, because
    the element carries a leading newline from the XML.
That 23/26 split is the same one measured independently tonight: 23 items carry
`asks`, 3 are deterministic.

WHAT THIS MEANS FOR SEQUENCING. C is not a new design. It is: run stage 02, then
03a/03b, against the rubric as it now stands -- which is in better shape for it
than the prior run's was, because the WORDS have since moved into the rubric and
`.stage/expanded` exists for the assembler to read. The proof obligation I wrote
independently ("reproduce byte for byte before the python producer retires") is
the gate that was already built for it.

#### C(ii) · BASELINE MEASURED 2026-09-23, before any code was written

Five facts, each measured in this tree rather than carried over from the prior
run's notes.

1. THE 23/26 SPLIT STILL HOLDS EXACTLY. A naive count says 26 `<LLMAction>` in
   the handouts, which would contradict the prior gate; three of those are the
   phrase `<LLMAction>` inside each file's own header comment. 23 real bodies,
   26 rubric items. The acceptance criterion is intact and unchanged.

2. THE PRODUCER AGREES WITH DISK TODAY. `olx_prompts.py --check` reports all
   three handouts up to date. That is the invariant C must preserve: the
   assembler has to reproduce what is on disk now, and `prompt_sha` will say so.

3. THE RUBRIC ALREADY CARRIES THE ITEM CONTENT and none of the scaffolding.
   `bmod_rubric.olx` holds Credit (134), Deduction (107), Guidance (193),
   Question (34), Slot (217) and Frame (58). It holds ZERO of the section
   headers -- "## Credit components", "## Deduction codes", "## Grading
   guidance", "## The checklist to return" -- and no system prompt. Those are
   still literals in `olx_prompts.py`, which is exactly what `promptAssembler`
   refuses to default: "the KEYS are engine concepts; the WORDS are not".

4. THE MISSING INPUT IS 27 NAMED FRAGMENTS, and the prior run's set is CURRENT.
   Checked against the shipped bodies rather than against the generator's source
   -- python wraps long literals across lines, so searching the source reports
   drift that is not there, and a first probe did exactly that and said 16 of 27
   had changed. Against the generated text, 25 of 27 appear verbatim, and a 26th
   (`derivedPresent`) is present in the bodies with the probe's wildcard too
   tight to match it. So step 2 of C is bounded and small: move 27 fragments
   into the rubric.

5. THE ASSEMBLERS STILL HAVE NO CALLERS outside their own tests, and the prior
   run's harness is READABLE in `pre_scrub_backup_*/migration/verify/`. Two
   drivers matter: `bodies.ts` proves the assembler against frozen generator
   inputs, and `all26_from_rubric.test.ts` is the one C actually wants -- it
   sources `max, question, credit, deductions, guidance, deriveFromClauses,
   conditions, frameParams` and the shared frame from the emitted rubric, and it
   PRINTS what it did not source: `fragments, contextRefs, responseRefs,
   slotOptions, notes, itemNotes, termDefinition`. That printed list is C's
   remaining work, and item 4 above is the first entry on it.

NEXT CONCRETE STEP: port `all26_from_rubric` into this tree as a real test --
driven from THIS rubric and diffed against THESE handouts, not the prior run's
frozen `expected` -- and report BYTE_EQUAL of 23. Everything after that is
moving entries off the FROM_OLD_SOURCE list one at a time.

#### C(iii) · BYTE_EQUAL=23/23, measured 2026-09-23

`npm run verify:assembled-prompts` in lo-blocks, driven by `olx_prompts.py
--assembler-inputs`. Every shipped body is reproduced by `promptAssembler`. The
proof obligation this item was filed with is met; what remains is sourcing.

FOUR DEFECTS ON THE WAY, none in the assembler:
  * the migration's frozen `criteria_frame.json` has 5 segments where this
    rubric's `oc_criteria` has 9 -- a stale input that reads as an assembler
    defect. The frame is sourced from the rubric now.
  * `_item_conditions` is not the frame's condition set: `_criteria_section`
    computes four more from the sheet. Exposed as `criteria_selection`.
  * `omitGuidance` is INDICES to the assembler and text fragments in python.
  * notes must arrive RESOLVED -- the precedence is now `resolved_slot_notes`,
    read by the generator and the dump alike.

Both extractions are byte-neutral: `--check` still reports three handouts up to
date.

WHAT IS STILL NOT SOURCED FROM THE RUBRIC: `fragments`, the 27 prose keys
measured in C(ii). Everything else the assembler needs now comes either from the
rubric or from the handout's own attributes. Moving those 27 into the rubric is
the last step before `build:assemble-prompts` can replace the python producer,
and the gate for that step already exists and passes.

#### C(iv) · `course.json` HOLDS CONTENT THAT OUGHT TO BE AUTHORED IN THE OLX

Stated by the user 2026-09-23, and measured the same hour. The good news first:
`course.json`'s items carry NO question, credit, deductions or guidance. Those
already live in `bmod_rubric.olx`, so the rubric is not duplicated -- which was
the risk worth checking before anything else.

What remains is 329 KB, and most of it is not bookkeeping:

    item_notes       98 KB   carried commentary
    item_note_runs   98 KB   THE SAME PROSE AGAIN, grouped into runs
    handout_notes    37 KB   carried commentary
    declarations     48 KB   measurement bookkeeping -- STAYS OUT by §0a
    handouts         27 KB   the per-handout `authored` tables -- MOVE IN
    generator        12 KB   prompt_context / prompt_response / prompt_notes
    items            17 KB   the generator fields above, keyed by item

TWO FINDINGS.

  * 227 KB OF 329 IS CARRIED COMMENTARY. §0a already decided where it goes:
    "The carried notes become OLX COMMENTS -- they were comments in the modules
    and were data only for lack of a home." They now have a home, so this is a
    move that is decided and not yet done, not an open question.
  * `item_notes` AND `item_note_runs` ARE THE SAME PROSE TWICE. Flattening the
    runs reproduces `item_notes` exactly for 14 of 14 items. One is a grouped
    view of the other, stored rather than derived -- 98 KB of the 329.

WHAT THIS MEANS FOR C. The remaining python dependence in prompt generation is
NOT what a first reading of the dump suggested. `CONTEXT`, `RESPONSE`,
`EVIDENCE`, `ITEM_NOTES`, `MATCH_DEF` and `OMIT_GUIDANCE` are not python
literals; they are read from `course.json` through `coursedata`, and python is
the reader rather than the source. So "no python" does not require porting
tables -- it requires those fields to be reachable by a TS consumer, and the
right destination is the OLX rather than `course.json`.

`WEB_SYSTEM` was the last prompt PROSE actually written in a module, and it has
moved: `<Frame name="fragment:webSystem">`, 2,416 characters, `{blurb}` filled
from the handout's own authored field. 28 fragments now.

#### C(v) · EXPECT vs the component's `expect`, settled 2026-09-23

The user refused to trust the audit until this was explained. It is explained,
and the audit was right; a DOCSTRING was wrong and a MODELLING ERROR of mine was
hiding behind a coincidence.

1. THE AUDIT IS SOUND. `check_generated_attributes_have_a_declaration` asks
   `expect_attr_for` whether the rubric backs an attribute, and that function
   reads the COMPONENT. All five `expect=` attributes are backed. The authored
   `EXPECT` table is not consulted by any check.

2. THE TABLE HAS ONE CONSUMER LEFT, and it is a test: E44's selftest picks its
   subject with `i in EXPECT`. Narrow or wide, the case still fires -- it would
   simply choose a different item.

3. THE DOCSTRING WAS STALE AND COST AN HOUR. `expect_attr_for` said "Only WK1
   declares one; the four `demonstrates_type` rules stay authored in the .olx".
   The rubric declares all five, so all five are generated, and
   `HAND_AUTHORED_ATTRS` -- the mechanism meant to protect the four -- is EMPTY,
   consistent with that. Nothing reported the prose going stale, because prose is
   not a declaration. It is quoted in place now rather than deleted.

4. THE WARNING IT ENDED ON IS LIVE, measured at exactly one rule: the item whose
   sheet carries a `stimulus_move` slot expects that slot to equal the move its
   `expected_type` requires -- the same string on both sides of a lookup
   `score.py` performs anyway. The other three expect `observed_type` to equal
   the type, a different claim. Recorded, not changed: it reaches scoring.

5. AND I HAD ENCODED `REQUIRED_MOVE` WRONG. It is keyed by TYPE -- `score.py`
   reads `REQUIRED_MOVE.get(item["expected_type"])` -- and I wrote it into the
   rubric as a per-ITEM attribute. On this course the four items are NAMED after
   the four types, so every id equals its own `expected_type` and the item-keyed
   copy answered every lookup correctly. BYTE_EQUAL, ATTRS, `--check` and the
   whole audit passed. No check could have caught it: there is no case in this
   corpus where the two keys differ. It is `<TypeMove type= move=/>` now, a fact
   about the vocabulary rather than about an item.

WHAT THIS SAYS ABOUT GOAL K. The engine's schema caught `requiredMove` as an
attribute `<Item>` may not carry, which is the kind of thing this project's 188
python checks do not ask. It did NOT catch -- and could not have -- that the
attribute was on the wrong noun. Schema validation answers "may this element
carry this?", not "is this the right place for this fact?".

#### C · DONE 2026-09-23 -- the producer is npm, and nothing in it is python

    npm run build:assemble-prompts            expand, build inputs, check
    npm run build:assemble-prompts -- --write  ... and write

PROVED BEFORE IT REPLACED ANYTHING, which was the whole obligation this item was
filed with: 23 of 23 bodies byte-identical, 322 of 322 attribute values, 109
attribute values written back with all three handouts unchanged and git
reporting no diff. `olx_prompts.py --write` now refuses and points at the npm
script; `OLX_LEGACY_WRITE=1` keeps the old path for one case only -- the npm
build is broken and a handout must be regenerated to reach a known tree.

THE SHAPE OF THE WORK, AS DONE:
  1. the assembler reproduced the shipped bodies from a python DUMP (23/23)
  2. the attributes followed (322/322), which needed `expectAttr` and
     `rubricDefAttr` written and `choicesAttr` proved portable after all
  3. the 27 prompt fragments moved into the rubric, and the literals left
     olx_prompts.py, so the words exist once
  4. the dump itself was replaced: `build:rubric-inputs` reads the rubric,
     course.json and the handouts directly
  5. python's OLX-generation role retired

WHAT IS STILL PYTHON, and correctly so: `olx_prompts.py` keeps the PAPER
scorer's half, and `--check` still compares its own generator against disk. That
is a second opinion now rather than the authority, and deleting the generator
code is a separate, larger deletion than this item asked for.

THE DEFECTS THIS FOUND, all caught by bytes and none by reading:
  * a frozen criteria frame with 5 segments where the rubric has 9
  * an item's own conditions are not the frame's -- four more are computed
  * `omitGuidance` is indices to the assembler and text fragments in python
  * notes must arrive RESOLVED, by a four-source precedence
  * `<Question>`/`<Guidance>` carry no attributes and a space-demanding pattern
    read that as an item with no question
  * HANDOUT_FIELDS is a pair list, not an object
  * attribute values are escaped, so a judging `rule=` kept its entities
  * `context` is `<Context item=/>` children, not an attribute
  * `pts=""` is not zero
  * AND `slotSheet.parseSlots` emits `countMax` while `promptAssembler` read
    `count_max` -- the engine's own parser could not drive its own assembler,
    unnoticed because only the python dump had ever fed it

### D · `gold_slots_q6.py` -- a CHECK that nothing runs

Separate from C, and it predates the migration: the prior run's patch touches it
by only 8 lines, so it was already there.

277 lines, imported by nothing. It defines `gold_slots_q6()`, `gold_view()`,
`unresolved_slots()`, `reconcile()` -- and
`check_corrected_slots_account_for_the_totals()`, whose docstring reads:
    "Each row's family changes plus its grid term must explain its total exactly.
     Signed, so a row that RAISES gold is checked as strictly as one that lowers
     it -- Q6/p4 is the only raising row and it is the one most in need of the
     check, since its correction mixes a slot (+1.25) with an off-grid regrade."
Referenced 0 times in equivalence.py, enforcement.py and precommit_gate.py.

A check that is not wired reports nothing forever, which is indistinguishable from
passing -- the exact failure this project fails a vacancy ratchet over. And its
subject is Q6, the item with the known matching ceiling, where the SAME PRINCIPLE
is wired for item 1c (`agreement.gold_slots_1c`, called at agreement.py:1828).

RESOLVED 2026-09-23: GENERALISE IT, do not wire it as it stands.

The first recommendation here was "wire the check as-is, scoped to Q6, which is
what it always was", on the measurement that only 2 of 15 CORRECTED_GOLD entries
carry itemised amounts and 4 of the 15 are Q6 -- so generalising appeared to buy
nothing. That reasoning was wrong, and the correction is the principle:

    AN ITEM-SPECIFIC CHECK IS ITEM CONTENT IN ANALYTIC MACHINERY. It is the same
    embedding this migration removes everywhere else, and `course_inventory`
    already counts it -- gold_slots_q6.py scores 3 ids and 2 named modules. The
    payoff is not today's coverage: a GENERAL check fires for content written
    later, and an item-specific one never will. Writing the specific one is
    choosing to miss the next item silently.

WHAT IT CAN BE MADE GENERAL ON, without inventing a declaration nobody fills in:

  (i) A CORRECTION MUST MOVE GOLD TO A REACHABLE VALUE. An item's score is max
      minus a subset of its component costs, so only certain values exist -- which
      `check_unreachable_gold_is_allowed` already relies on, for the OTHER side of
      the same fact (harnesses must forgive an unreachable gold). Nothing checks
      that a CORRECTION lands on a reachable one. The costs come from the rubric,
      so the check reads no item ids at all and fires on all 15 entries and on
      every future one. Q6/p4 is the case that motivated it: gold 6.00 on an item
      moving in steps of 1.25, corrected to 6.25.

  (ii) WHERE A CORRECTION STATES AMOUNTS, THEY MUST EXPLAIN ITS DELTA. This is the
      Q6 check's actual content, generalised: parse the amounts out of the
      reasoning the declaration already carries, and require them to sum. It
      covers 2 entries today and costs nothing per new entry.

  Both read slot costs FROM THE RUBRIC, which is now the single source for them --
  so this is only possible after tonight's work, and was not before.

THE Q6-SPECIFIC PARTS GO: `CORRECTED_FAMILY` (a table of Q6 pids), and the
per-slot reading (`gold_slots_q6`, `gold_view`, `unresolved_slots`). The reading
solves a problem Q6 does not have -- its wired analogue `gold_slots_1c` exists
because 1c's gold must be REBUILT from feedback, one of the four accounting steps
`check_gold_accounting_is_uniform` names. Q6's gold is taken from the sheet and
corrected where unreachable; there is nothing to rebuild.

So: delete the module, add the two general checks, and record the deletion reason.

#### DONE 2026-09-23 -- and check (ii) was REFUTED BY MEASUREMENT, not built

SHIPPED, both in `enforcement.py`, both registered in `equivalence.py`, both
fire-tested (positive on injected breakage, back to zero on restore):

  check_gold_corrections_land_on_attainable_scores
      every CORRECTED_GOLD entry sets a score the item can produce. 15 entries,
      0 findings. Three of the fifteen exist BECAUSE gold was off-grid -- 1c/p11
      at 7.00, Q4a/p17 at 4.00, Q6/p4 at 6.00 on an item stepping by 1.25 -- so
      the rule is the one those corrections were written to satisfy.

  check_gold_scores_are_attainable
      the REPORTING half of `check_unreachable_gold_is_allowed`, which forgives
      an off-grid gold and never says it did. 519 gold cells carry a score and 0
      are off-grid, because those same three corrections are what regularised
      the corpus. A ratchet at zero that fires on new content only.

Both read slot costs FROM THE RUBRIC and name no item, which is the point.

CHECK (ii) AS SKETCHED ABOVE IS WRONG AND WAS NOT BUILT. The sketch said "parse
the amounts out of the reasoning and require them to sum [to the delta]". The
amounts in these declarations are THE GRADER'S DEDUCTIONS, and they bear on the
corrected SCORE (max minus their sum), never on the delta. Built as written it
would have fired falsely on at least five entries.

And the deeper reason no parse can work, which is what closes this off: THESE
DECLARATIONS STATE NUMBERS IN ORDER TO REJECT THEM, as routinely as they state
the ones they adopt. Measured, three times over:
    Q4a/p19  "the strict reading ... gives 1.00" -- explicitly "not proposed"
    Q6/p9    quotes the grader's "-2.5 pt" to refuse that reading; delta -1.25
    Q6/p17   quotes "-5 pt"; delta -1.25
No regex separates an adopted figure from a refused one, and a check that
cannot tell them apart reports the declaration's own reasoning as an error.
The third option -- a structured `charges` field -- is refused by this item's
own constraint, "without inventing a declaration nobody fills in", and the
entries live in the gold file behind an exporter, not in python.

So the second check is the one measured above instead: same family, no prose.

BOOKKEEPING DONE WITH THE DELETION: 13 definitions accepted through
`editguard.accept`, the empty module key dropped from `DEFINITIONS.json`
(`editguard.vanished()` reads clean), `COURSE_DATA_BUDGET.json` re-tightened via
`course_inventory.py --tighten` (the module's `named_modules` entry and its 3
data embeddings both gone), and the two enforcement comments that used the file
as their worked example re-pointed at `q6_consensus.py`, which is still there.
`BACKLOG.md`'s "generalise the per-slot gold summary" note KEEPS its design
lessons -- they are the measured residue of building the Q6 parser and say what
a general version must handle -- and now records the deletion above them.

AUDIT IMPACT: none. 44 undeclared findings before and after, measured by running
the audit at HEAD on the real tree (a git-worktree copy reports 0 and is not a
valid comparison -- it has no built artifacts). The certification's "45" is these
44 plus the 1 PARKED finding.

### E · `olx_string_idmaps.ts` -- where do the 99 lines belong?

RESOLVED 2026-09-23: THEY STAY IN LO-BLOCKS, and the premise of the question was
wrong -- this file is not an unwired module.

THE MEASUREMENT THAT SETTLED IT. The file has 0 in-repo references, which is why
it was grouped with the other "written but producing nothing" modules. But it
HAS a caller: `process_events.py` spawns it with `npx tsx` against a lo-blocks
installation root (`_OLX_STRINGS_SCRIPT`, `build_parser_idmaps_for_olx`). It is
load-bearing for the event pipeline -- it is what resolves ids for dynamic OLX,
the content an OlxSlot renders from a runtime-authored string, which never lives
in the content/ tree and so is invisible to `xml2json.ts`.

WHY LO-BLOCKS IS THE RIGHT HOME, and the reason is the one this migration keeps
applying elsewhere. The whole point of the script is that the ids it mints MATCH
THE RUNTIME IDS the event stream carries, which it achieves by calling the very
same `parseOLX` with the same provenance and namespace as `_OlxSlot.tsx`. Move
it out and there are only two options: reach into lo-blocks' internals from
another repository, or reimplement the parse -- a second implementation of one
rule, which is exactly the shape retired from `oc_criteria`, from `SLOT_NOTES`,
and the shape item F is filed to retire from `rebuild_gold_1c`. Its companion
`xml2json.ts` already lives here for the same reason.

WHY THE COUPLING ARGUMENT IS STRONGER THAN CODE REUSE, which is what the first
version of this entry missed. The ids are a PRODUCT OF THE PARSE -- `createId()`
hashes the parsed node -- so a second implementation would not drift over time,
it would be WRONG IMMEDIATELY, minting ids that match nothing in the event
stream. And it would fail SILENTLY: no exception, no empty output, just
resolutions that stop happening. That makes this a VERSION-COUPLING argument.
The wrapper must ship from the same build as the parser it wraps, which rules
out moving it to a tools package that depends on lo-blocks as a library.

WHAT WAS ACTUALLY WRONG was not the file's location but that NOTHING EXERCISED
IT. `lib/llm/runner.test.ts` has the identical shape -- lo-blocks code whose only
caller is an external harness -- and is at least wired into the test suite; this
file had no in-repo caller, no test, and no package.json entry, so lo-blocks'
own verification could not see it and the python enforcement framework cannot
see inside it. A header comment fixes legibility and not that.

DELIVERED 2026-09-23:
  * `packages/shared/scripts/olx_string_idmaps.test.ts` -- three tests. (1) the
    script's WHOLE idMap equals a runtime-shaped `parseOLX` call; (2) an
    unparseable string is omitted rather than emitted with an empty map, which is
    the caller's actual fallback contract; (3) a drift guard reading BOTH call
    sites, because test 1 computes its own expectation and so cannot notice
    `_OlxSlot.tsx` itself changing.
  * `package.json` gains `olx-string-idmaps`, beside `xml2json` and `xml2graph`.
  * `packages/shared/scripts/olx_string_idmaps.md`, following the
    `lib/llm/*.md` sibling-doc convention.
  * the header seam note naming `process_events.py` as the caller.

FIRE-TESTED, and the fire test IMPROVED THE TEST, which is the part worth
keeping. Injecting a wrong namespace failed test 1 as expected. But injecting a
changed provenance ref (`validate://` -> `dynamic://`) left the minted ids
IDENTICAL and passed test 1, caught only by the drift guard -- because the first
version compared key sets, and provenance rides in each entry's `source`. Test 1
now compares the whole map and catches both. A key-set comparison would have
shipped looking sufficient.

Full lo-blocks unit suite green after the change: 108 files, 2562 tests.

POPULATION ENUMERATED, not fixed at the instance. Of 18 scripts in
`packages/shared/scripts`, five have no in-repo reference. Three are `.test.ts`
and are collected by vitest's glob, so the count is expected and means nothing.
That leaves two, and only one of them is this file.

  ONE RESIDUAL, NOT PART OF E: `parse-peg.ts` has no in-repo reference AND no
  external caller in the pipeline scripts or in scoring. It is the only script in
  the tree that is unreferenced on both sides, so it is the one that genuinely
  needs a disposition -- wire it, document its caller, or delete it. Filed here
  rather than guessed at.

### G · `DEFINITIONS.json` tracks 40 modules of 73, and new ones never enter

Filed 2026-09-23, on the user's instruction, after item A created two modules and
NEITHER appeared in the ledger. That is not a bug in the split; it is how the
ledger has always behaved, and the split is only what made it visible.

MEASURED, not estimated:

    modules on disk                    73
    tracked by DEFINITIONS.json        40
    UNTRACKED                          33   holding 400 definitions
    ghost entries (tracked, no file)    0

The untracked 33 are not peripheral. They include `coursedata.py` (34
definitions), `rubric_export.py` (24), `rubric_component.py` (19),
`shape_inventory.py` (18), `reader_equivalence.py` (16) and both halves of the
module A just split.

WHAT IS AND IS NOT EXPOSED, because the two guards are easy to conflate:

  * `editguard.safe_write` compares the file's own before/after text and refuses
    an undeclared vanishing. It works on ANY module, tracked or not, and it
    worked throughout A -- it is what caught the `CONTEXT_SOURCE` prose edit that
    had not landed, and what refused the two slices during the Q6 work.
  * `DEFINITIONS.json` + `editguard.vanished()` + `check_no_definition_vanished`
    are the SECOND net: they catch a definition lost by any route that did not go
    through `safe_write` -- a hand edit, another tool, a bad merge, a file
    replaced wholesale.

So the exposure is precisely: on 33 of 73 modules, only edits made through
`safe_write` are guarded, and nothing is watching the rest. `vanished()` iterates
the INVENTORY's keys, so an untracked module cannot report a loss -- it reports
clean, which is indistinguishable from being intact. That is the same
"unwired check reads as coverage" failure item D was filed for, arriving by a
different route.

THE WORK, and the order matters:

  1. Inventory the 33 and seed them. NOT with `seed(force=True)`: that rewrites
     the whole file from whatever the tree currently says, which would silently
     bless any definition already lost from the tracked 40 as well. The seed must
     be ADDITIVE -- add modules absent from the inventory, touch no existing
     entry -- and `seed()` today refuses to overwrite at all, so this needs a
     new, narrower entry point.
  2. Make a NEW module enter automatically, or refuse. Today a module can be
     added and tracked by nothing, forever, with no signal. The check to write is
     the complement of `vanished()`: every `*.py` in the package is either in the
     inventory or declared as deliberately outside it. That check is what makes
     step 1 stay true; without it the gap simply reopens on the next new file.
  3. Decide whether anything is LEGITIMATELY untracked, and declare it rather
     than leaving it to the absence of an entry. Candidates to consider are
     one-shot scripts (`stamp_legacy_artifacts.py`) and tools that regenerate
     themselves -- but the default should be tracked, and an exemption should
     have to say why, the way every other exemption in this project does.

WHY IT IS NOT URGENT AND SHOULD STILL BE DONE SOON: nothing is known to have been
lost, and `safe_write` has covered the edits this project actually makes. The cost
is that no one can SAY that about the untracked 33 -- and the whole argument for
the ledger, written in its own `_README`, is that a file which parses tells you
nothing about whether it still defines what it did yesterday.

#### DONE 2026-09-23 -- all 73 modules tracked, and a check that keeps it so

Done ahead of B, C and F on the user's instruction, and the ordering is the
point: each of those MOVES CODE, and an unwatched definition lost during a move
is the exact failure this ledger exists to catch. Widening the net before the
next move is worth more than widening it after.

    modules on disk   73        tracked before   40      after   73
    definitions       1420      untracked before 33      after    0

THE SEED IS ADDITIVE, and that is the whole design. `seed(force=True)` rewrites
every entry from whatever the tree currently says, so on a package already
carrying a loss it would record the damage as the definitions of record --
laundering the failure the inventory exists to catch. `editguard.track_new()`
only ever ADDS keys, and it REFUSES to run at all while any tracked module is
reporting a loss, because adding coverage is not the moment to be carrying an
unexplained one. Fire-tested: with a phantom name planted in the inventory it
refused and named the loss; with the plant removed it ran.

Precondition checked before seeding rather than assumed: `vanished()` read 0
across the tracked 40, so nothing was blessed by being added around it.

`check_every_module_is_tracked` -- reported as MODULE IS NOT IN THE INVENTORY,
registered in the audit -- is the complement of `check_no_definition_vanished`,
and it is what stops the gap reopening on the next new file. A one-off cleanup
with nothing holding it is a gap with a date on it. Fire-tested both ways: a new
module is reported; declaring it in `editguard.UNTRACKED_BY_DESIGN` silences it;
deleting it restores zero.

`UNTRACKED_BY_DESIGN` ships EMPTY, deliberately. Nothing was found that deserved
an exemption, and the table exists so that "not tracked" is always a decision on
the record rather than the absence of one -- which is what it had been for 33
modules. `editguard.py --track` adds; `editguard.py` with no arguments now
reports both halves.

Audit unchanged: 44 findings, and the set IDENTICAL to the pre-D baseline.

#### G(a) · Definitions named for a course artifact -- OPEN, filed 2026-09-23

G's main body is DONE. This is a substep filed after it, on the user's
instruction, and it belongs here because it is
`check_no_module_is_named_for_a_course_artifact` -- §10.7 category 4, "a generic
engine has no module named for a question, a handout or a course" -- APPLIED ONE
LEVEL DOWN. That check reasons about the repository's file list; nothing reasons
about the names inside the files.

WHY IT SURFACED NOW: item F removed the last item-id LOOKUPS from `agreement.py`
and `agreement_app.py`, and what survived was the item-id NAME. `rebuild_gold_1c`
no longer rebuilds 1c -- it rebuilds whatever the rubric declares
`gold_from_deductions` on, and 1c is merely the only item that declares it today.
The name now describes the caller's history rather than the function's behaviour,
which is the precise defect this substep is for.

THE POPULATION, ENUMERATED -- three, all `1c`:

    agreement.py        rebuild_gold_1c
    agreement_app.py    rebuild_gold_1c
    measured.py         _1C_GATE_CEILING

AND THE SCAN THAT FINDS THEM MUST BE ITEM-ID-ONLY. Running it with
`course_inventory.NAME_MARKERS` as well returns 79 definitions and nearly all are
noise: `gold` is a generic term for reference scores (`check_gold_is_read_by_item`,
`RAW_GOLD_READERS`, `gold_path` ...) and `h1`/`h2`/`h3` name handouts, which is
course STRUCTURE rather than an item. Those markers were written for MODULE names
and over-fire on definitions -- the same false-positive shape as the `.md` scan in
G2, where `PR|NR|PP|NP` turned out to be generic verdict abbreviations. Item ids
alone give three, and three is the real answer.

THE RENAME, and what it costs:

  `rebuild_gold_1c` -> a name for what it does. It now delegates to
      `handouts.rebuild_declared_gold(gold, handout)`, so `rebuild_declared_gold`
      is the honest name on both sides. 22 call sites across 8 modules
      (`measured.py` holds six), and -- the part that is not a find-and-replace --
      `enforcement.check_gold_accounting_is_uniform` names the string
      `"rebuild_gold_1c"` in its `CANON` table as one of the FOUR things that
      separate a published rate from a naive comparison. The table entry must move
      with the name, in the same commit, or the check goes quiet about one of its
      four while still reporting that it ran.

  `_1C_GATE_CEILING` -> LEFT AS IS. Decided by the user 2026-09-23, and the
      reasoning is the distinction this substep turns on: a DECLARATION ABOUT one
      cell is entitled to name that cell, where a FUNCTION that no longer has
      anything to do with it is not. It is also a gold declaration, read through
      `_gold_declaration` and carried by `gold_export.py`, so its name is a key in
      the gold file -- renaming it would be a data migration rather than a rename,
      for no gain.

      So the rename is ONE name in TWO modules, and this becomes the first
      declared exception rather than an open question.

THE CHECK THIS WANTS. Doing the rename without one leaves the next such name to
be found by hand. The general form is the module check's sibling: no definition in
a MIGRATED module is named for an item id, with an `UNTRACKED_BY_DESIGN`-style
declaration carrying the exceptions and their reasons.

THE DECLARATION MECHANISM IS NOT OPTIONAL HERE, because the exception set is
already non-empty: `_1C_GATE_CEILING` stays by decision, so a check without a
place to record that would fire on it forever and be waved through -- which is how
a check stops being read. Write the table with the check, not after it, and put
the reason above in it: a declaration about a cell may name the cell.

##### G(a) DONE 2026-09-23

`rebuild_gold_1c` -> `rebuild_declared_gold` in `agreement.py` and
`agreement_app.py`, across 24 code sites in 8 modules, with
`check_gold_accounting_is_uniform`'s `CANON` entry moved in the same write -- the
part that was not a find-and-replace, since that table names the string as one of
the four things separating a published rate from a naive comparison.

THE PROSE WAS SPLIT BY WHAT IT DESCRIBES, not renamed wholesale. `EQUIVALENCE.md`'s
two mentions describe CURRENT behaviour and were renamed; `GOALS.md` (6) and
`BACKLOG.md` (1) are RECORDS of what was done at the time, and renaming inside them
would make them describe a function that did not exist then. Same principle as the
declared exception below.

AND IT FIXED STALENESS F2 HAD LEFT: both wrappers' docstrings still said "DELEGATES
to `handouts.rebuild_gold_1c`", a function F2 had removed from `handouts`. A rename
pass reads every site, which is how that surfaced.

SHIPPED WITH ITS CHECK AND ITS EXCEPTION TABLE, because the exception set was
already non-empty. `enforcement.check_no_definition_is_named_for_an_item` reads
`editguard.item_named()`; `editguard.ITEM_NAMED_BY_DESIGN` carries
`measured._1C_GATE_CEILING` with the reason -- a DECLARATION ABOUT one cell may name
that cell, where a FUNCTION that no longer touches it may not. Fire-tested:
withdrawing the exception surfaces it, restoring silences it. The check reads 0 and
names item ids ONLY, for the measured reason that adding `NAME_MARKERS` returns 79
where 3 are real.

Audit 44, finding set identical to baseline. Both sides still reproduce the frozen
20-row F baseline.

##### G(b) · 350 DEFINITIONS WERE LIVE AND UNRECORDED -- DONE 2026-09-23

THE LEDGER TRACKS A FROZEN NAME SET PER MODULE. `safe_write` reports `added` but
does not record it, `accept` only removes, and `track_new` adds MODULES, not names.
So every definition created since the original seed is unprotected -- `vanished()`
can only miss what it never knew.

    definitions live in the tree   1769
    definitions in the ledger      1419
    LIVE BUT UNRECORDED             350   across 21 modules

    enforcement.py 130   measured.py 46   olx_prompts.py 26   equivalence.py 22
    score.py 22   precommit_gate.py 19   agreement_app.py 17   editguard.py 15

`editguard.py`'s own 15 include `UNTRACKED_BY_DESIGN` and `track_new`, added by
item G hours earlier -- so G closed the module gap and opened this one in the same
act, which is the clearest possible statement of the shape.

WHAT SHIPPED. `editguard.unrecorded()` reports a tracked module whose recorded set
is stale; `editguard.backfill()` and `--backfill` close it, additively and refusing
on the same condition `track_new` uses -- it will not run while a tracked name is
already reporting lost, so it cannot launder a loss. `check_every_definition_is_
recorded` is the backstop, registered in the audit as DEFINITION IS NOT IN THE
INVENTORY.

`safe_write` WAS DELIBERATELY NOT TOUCHED, and the first design did touch it. The
plan was to record additions automatically as they were written. That would have
made the writer IMPURE: a write-then-revert through `safe_write` -- a speculative
edit, a fixture, a fire test -- would leave a phantom name in the ledger that
`vanished()` then reports forever, and the report would be true of the ledger and
false of the tree. Recording stays an explicit act, which is also the idiom already
here: `--accept` for a removal, `--track` for a module, `--backfill` for a name.

(The question that found it was whether the SELF-TEST would pollute the ledger,
since it renames definitions to inject faults -- `_gold_nameable_slots` to `_NOPE_`.
It would not: it injects through `Path.write_text` directly, never through
`safe_write`. But asking exposed the worse case in the design itself.)

NOT SEPARATELY CERTIFIED, decided by the user 2026-09-23, and recorded here because
in this project everything certifies and an exception belongs on the record rather
than in the gaps. The reasoning: `equivalence.py` contains ZERO references to
`editguard`, so none of the 72 self-test cases exercise it -- they install faults in
the SCORER. Editguard reaches the audit only through `check_no_definition_vanished`,
which the two-minute COLD AUDIT exercises fully. With `safe_write` untouched, G(b)
is two read-only functions and a CLI flag, so nothing every later edit depends on
passes through it. Verified by cold audit and fire test; G2's certification covers
the commit.

THE FAMILY IS NOW COMPLETE, and each member was invisible to the others:

    check_no_definition_vanished        is a RECORDED name still defined?
    check_every_module_is_tracked       is a MODULE recorded at all?
    check_every_definition_is_recorded  is a module's recorded set CURRENT?


THIS IS G'S GAP ONE LEVEL DOWN and the fix is the same shape: a definition is
tracked or it is declared. The likely form is `safe_write` recording what it
reports as `added`, plus a one-time additive backfill under the same refusal
`track_new` carries -- never a reseed, which would bless whatever is currently
there. Not done here because G(a) was a rename and this is a mechanism; filed so it
is not rediscovered a third time.

### F · `1c`'s gold rebuild -- 16 embeddings, implemented TWICE, no owner

Measured with `course_inventory.py` (the prepared tool; it reports populations and
refuses to guess them). Item ids embedded in ANALYTIC machinery, outside the three
declared DATA modules:

    1c   16      <- this item
    Q6    8      3 in gold_slots_q6.py (item D); 4 in enforcement_selftest (D2a)
    Q1    4      reader_equivalence._mutations                          (D2a)
    Q4a/1b/1a  1 each   equivalence.py                                  (D2a)

MOST OF IT IS ALREADY OWNED. `equivalence.py`'s seven ARE the audit's one parked
finding -- "D2a (fixtures that select their target by shape) is the work that
removes them" -- and `reader_equivalence._mutations` is the same class: a
fault-injection fixture NAMING its target instead of selecting it by shape.

`1c` HAS NO OWNER, and it is the worst-shaped of the set:

    agreement.py       gold_slots_1c()  +  rebuild_gold_1c()
    agreement_app.py   rebuild_gold_1c()  AGAIN

and `agreement_app`'s copy says so itself:
    "Mirrors gold_slots_1c in agreement.py. The two must agree: a row scored on
     one side and dropped on the other is not a comparison."

A comment asserting that two implementations must agree, with nothing enforcing
it, is the exact shape removed from `oc_criteria` and from `SLOT_NOTES` tonight.
The remaining hits -- `GRAPH_UNREACHABLE_1C`, and `1c` in measured.py,
enforcement.py, compare_runs.py, olx_prompts.py -- are that special case leaking
outward across six modules.

IT GENERALISES EXACTLY AS ITEM D DOES. The fact is "this item's gold must be
REBUILT from the grader's itemisation, because the sheet's number cannot be
trusted for it". That is an item property -> it belongs in the rubric. The
arithmetic (`10.0 - 2.0 * failures`) is slot costs -> the rubric now holds those.
So: one rebuild, declared on the item, driven from the rubric, serving both
engines -- replacing two hand-kept copies and a comment hoping they agree.

RANK IT ABOVE D: the same generalisation, four times the footprint, and unlike D
it currently sits astride the two scorers' comparison, which is the one place a
silent divergence is most expensive.

`check_gold_accounting_is_uniform` already names `rebuild_gold_1c` as one of the
four things separating a published rate from a naive comparison -- so the rebuild
is load-bearing and must keep working byte-for-byte through the move. Same proof
obligation as everything else tonight.

#### F1 DONE 2026-09-23 -- one implementation, arithmetic from the rubric

WHAT THE DUPLICATE ACTUALLY WAS, measured rather than taken from this entry's own
write-up. `agreement.gold_slots_1c` and `agreement_app.gold_labels_1c` differed in
three places, and only ONE was a divergence:

  * REAL, and latent: `agreement_app` matched `missing (the )?legend`, `agreement`
    only the short form. The rubric's dictionary text IS "missing the legend", so
    the app's was correct and the other would mis-score any row using the
    dictionary's wording. No comment in the corpus does, which is the only reason
    nothing reported it.
  * NOT a divergence, and this entry had it wrong: the two exclusion sources looked
    independent, but `agreement.GRAPH_UNREACHABLE_1C` is DERIVED from
    `PER_ITEM_EXCLUDE["1c"]` -- "not repeated, so the two drops cannot disagree".
    Someone had already met this and fixed it.
  * Cosmetic: `x_axis_label`/`y_axis_label` against `x`/`y`. The rebuild only counts
    falses, so the names never reached the arithmetic.

WHAT THE RUBRIC TURNED OUT TO HOLD, which decided the shape: `max` 10.0, an
`increment` of 2.0, five `credit` slots each with their own `pts`, the gate marked
`gates: true`, and every slot's deduction `codes`. So the whole arithmetic is
rubric-derived and no longer written down anywhere. `series_box_holds` carries no
`pts` and is correctly excluded -- a reader counting "every credit entry" would
have invented a sixth 2-point element.

WHAT THE RUBRIC COULD NOT SUPPLY, and the reason the phrases are still authored:
the dictionary text is NOT what graders typed. The rubric says "-2 pts: missing the
x-axis label"; every grader wrote "missing x-axis". A reader built from the
dictionary strings verbatim would match nothing and score every row full marks in
silence. So `GOLD_COMMENT_PHRASES` is a DECLARATION, keyed by the deduction code
the rubric declares, accepting both wordings for all four labelling codes -- the
legend fix generalised to its siblings, since the same shortening had happened to
every one of them and only that one had been noticed.

  handouts.gold_labels(item, feedback)              general, names no item
  handouts.rebuild_gold_from_comment(gold, item)    general, names no item
  declaration_source.GOLD_COMMENT_PHRASES           course data, exported
  agreement/agreement_app.rebuild_gold_1c           two-line wrappers, kept
      because `check_gold_accounting_is_uniform` verifies BY IMPORT that a module
      comparing predictions to gold reaches the rebuild, and eight modules call it
      through those names.

A CODE WITH NO PHRASE IS NOW A REFUSAL, where both copies hard-coded five keys and
would have ignored a sixth element without a word. Fire-tested.

PROVED BY THE 20 ROWS: both sides reproduce the frozen pre-change baseline exactly,
scores and dropped-list. Audit 44 with the finding set IDENTICAL to the pre-D
baseline. `COURSE_DATA_BUDGET` fell 132 -> 130, so this REMOVED item-specific
content rather than relocating it -- the first attempt put the phrase table and the
"1c" lookup in `handouts.py` and the ratchet caught it growing 1 -> 2, which is how
the current shape was arrived at.

F2, STILL OPEN: the fact that 1c's gold must be rebuilt at all is declared nowhere.
The two wrappers still name the item. Declaring it on `<Item>` in the rubric is what
would retire the last of it, and needs `Item.ts` before the `.olx` -- the ordering
`family=` taught earlier this session.

#### F2 DONE 2026-09-23 -- the item declares it, and no analytic module names it

`<Item scores="1c" ... conditions="graph_item|gold_from_deductions">`. The fact that
an item's gold must be rebuilt from the grader's itemised deductions is a property
OF THE ITEM, so it is declared on the item; `handouts.rebuild_declared_gold(gold,
handout)` rebuilds whatever carries the flag and knows nothing else.

NO `Item.ts` CHANGE WAS NEEDED, which is why this was cheaper than planned. Flags
are not schema attributes -- they ride in the existing `conditions=` and are
recovered by membership, the way `graph_item`, `move_pick`, `avoidance_scores` and
`reads_utb_choice` already were. So the `family=` ordering trap did not apply.

THE RISK WAS THAT `conditions` IS OVERLOADED: the same attribute drives
`as_view_frame` and `_item_conditions`, which gate shared prose in the criteria
frames and the 27 slot notes. A brand-new condition name SHOULD be inert because
no segment references it -- and that was the claim under test, not an assumption.
MEASURED: `prompt_sha` unchanged for all 26 items on BOTH sides, against a
baseline frozen before the edit.

RESULT, from `course_inventory`:

    agreement.py       literals []   tables []
    agreement_app.py   literals []   tables []

Both analytic modules now carry ZERO item ids. Three sites went:
  * the `["1c"]` lookup in each wrapper -> `rebuild_declared_gold(gold, handout)`
  * `agreement_app.main`'s `if args.item == "1c"` -> the item's own flag. Its
    message named 1c's five slots, so a second item declaring the same thing would
    have been described as if it were 1c; it is now built from the item's own
    scored credit and max.
  * `GRAPH_UNREACHABLE_1C`, dead since F1 moved the rebuild out -- referenced only
    from comments afterwards. Accepted through `editguard`.

`COURSE_DATA_BUDGET` 130 -> 125.

THE RATCHET CAUGHT ME AGAIN, and it is worth recording twice: the first version of
the `RUBRIC_FIELDS` comment said "the two wrappers that used to name `1c`", which
put an item id into `coursedata.py`, a module that had none. `coursedata.py 0 -> 1`,
refused to tighten, reworded. F1's first attempt made the same class of mistake in
`handouts.py`. A module gains course data most easily through PROSE.

BUILD ARTIFACTS ARE PART OF THE EDIT, not a follow-up. Editing the `.olx` made
three downstream products stale and the audit said so in three separate findings:
`.stage/expanded` (rebuilt with `build:expand-rubrics`), `.stage/content`
(`build:stage-content` -- which needs `$COURSE_DATA` set or it dies on an
unresolved reference), and `apps/static/public/static-content`
(`build:static-content`). The scorer reads the staged rubric, so an un-rebuilt
stage means it is reading a rubric that no longer exists.

Fire-tested: with the flag, 17 rows rebuilt and 3 withdrawn; with the flag removed,
nothing is rebuilt and gold is untouched; restored, back to 17 and 3.

Audit 44, finding set identical to the pre-D baseline. Both sides reproduce the
frozen 20-row F1 baseline exactly.

WHAT F LEAVES BEHIND: `rebuild_gold_1c` survives as the NAME of the two wrappers,
because `check_gold_accounting_is_uniform` verifies by import that a module
comparing predictions to gold reaches it, and eight modules call it through that
name. The name is the last item-specific thing in the family, and it is a name
rather than a lookup -- renaming it means touching that enforcement table and
every caller, which is its own change.

### G2 · Split the procedure documents from the course they were written against

Filed 2026-09-23 on the user's instruction. Several `.md` files state GENERAL
procedure and are then heavily annotated with this course's items, participants,
gold comments and measured runs. The general half belongs in `scoring/`; the
course-specific half belongs beside the handout OLX in `psychology/`, INCLUDING
the general text by reference rather than quoting it.

THIS IS ITEM A APPLIED TO PROSE, and it is worth seeing that way. A split
`declaration_source.py` and `generator_source.py` because each held two
categories, which is why every "does this move?" question needed a per-table
answer. These documents have the same defect: `QUALITY_CONTROL.md` is category III
machinery AND category II/IV course annotation in one file, so item H cannot file
it anywhere. G2 runs BEFORE H for exactly that reason -- H assigns one home per
category, and it cannot until each file belongs to one.

#### The population, from the prepared classifier and not a regex

Measured with `course_inventory.item_ids()` -- the authoritative id set, read from
DATA -- over every `.md` in BOTH trees. The first attempt at this table used a
hand-rolled pattern over prose and got different numbers; the rule this project
already has is to use the prepared classifier, and it applies to prose as much as
to code.

| file | lines | id hits | python readers |
|---|---|---|---|
| `scoring/OVERRIDES.md` | 257,216 | 255,546 | 4 |
| `scoring/GOALS.md` | 16,765 | 3,947 | 12 |
| `scoring/EQUIVALENCE.md` | 3,036 | 623 | 10 |
| `scoring/BACKLOG.md` | 1,885 | 283 | 9 |
| `scoring/QUALITY_CONTROL.md` | 2,702 | 190 | 15 |
| `scoring/README.md` | 629 | 177 | 1 |
| `SCORING_REFACTOR_PLAN.md` | 5,011 | 133 | -- |
| `RUBRIC_MIGRATION_PLAN.md` | 4,397 | 107 | -- |
| `scoring/drafts/q1q2_reasons_rule.md` | 555 | 32 | -- |
| `scoring/Q6_MATCHING_CEILING.md` | 216 | 30 | 3 |
| `VERDICT_VOCABULARY_PLAN.md` | 301 | 27 | -- |
| + 6 more under 10 hits (`PENDING_DECISIONS`, `ADOPTION_POSTMORTEM`, `STAGE5_RUNBOOK`, `MATERIAL_CLASSIFICATION`, `migration/RUNBOOK`, `drafts/subgoal8`) | | | |

THE SET IS WIDER THAN `scoring/`: the root-level plans carry course content too,
and so do `scoring/drafts/`. H sends the interim plans to deletion and the drafts
with them, so those need no split -- but they must be DISPOSED of rather than
quietly left, which is H's enumeration rule, not something G2 may assume.

LO-BLOCKS IS CLEAN, and proving it is the useful part. Seven of its `.md` files
matched, and ALL SEVEN ARE FALSE POSITIVES: `verdicts="PR|NR|PP|NP"` in
`Equals.md`, `Expect.md` and `LLMAction.md` uses those tokens as generic type
abbreviations, and `Noop.md`'s `Q1`/`Q2` are "question one" and "question two" in
a layout example. They collide with this course's ids because its operant items
ARE named PR/NR/PP/NP.

#### G2 OWNS THE RUN-TO-DECISION LINK that item H found missing

Consolidated here on the user's instruction 2026-09-23, because the two items meet
on the same files and the fix has only one sensible home.

H FOUND THE GAP: `$COURSE_DATA/out` holds 826 runs, and the link between a decision
and the run that supported it was never recorded -- `goals.py` cites the FINDING
("measured 12 configurations: 1/6, 3/6, 6/6 ...") and never the artifact, so 32 of
826 runs are named anywhere at all. H can archive the data but cannot say what any
of it supported.

THE LINK BELONGS ON THE COURSE-SPECIFIC DECISION RECORD, which is the thing G2
creates. It is not a separate mechanism and must not become one: a decision and the
runs behind it are the same record, and splitting them across two items would
recreate the very orphaning H is complaining about.

AND `goals.py` IS A G2 TARGET, which the original framing missed. This item was
scoped to `.md` files, but `CLOSURES_APPROVED` is 52 entries and 107,619 characters
of course-specific decision narrative held as FLAT PROSE STRINGS inside an analytic
module -- `course_inventory` already scores it as a course-data table. Same defect,
`.py` form. The generic half is the CLOSURE PROCEDURE; the course-specific half is
these 52 records.

WHICH IS ALSO WHY THE LINK CANNOT BE ADDED TODAY: a flat string has nowhere to put
a `runs` field. Structuring these records is the enabling step, and it is the same
step this item already proposes for the `.md` files -- "it may be appropriate to
reframe the course-specific information as json records under appropriate keys".
The run link is simply one of those keys.

NOTE THE GRANULARITY, because an existing field looks like it already does this and
does not. `MEASURED.json`'s `items[item][side].out` links ITEM x SIDE -> run, which
is what the ledger needs. The missing link is DECISION -> run, which is coarser and
belongs to the subgoal, not the cell. Both should exist; only the first does.

THE BACKFILL IS PART OF THE SPLIT, NOT A FOLLOW-UP -- the user's instruction, and
it is the cheapest the work will ever be. Splitting a decision record means READING
IT to decide which half each sentence belongs in, and the narrative is the only
place that says what was measured. So the run is identified at the moment someone
already has the record open and the inventory to hand. Do it later and all 52
records must be read a second time, for the one question that could have been
answered during the first pass.

WHAT MAKES THE MATCH POSSIBLE even though no name was recorded: the inventory
carries each run's DATE, size and file count, and the decision records carry dates
and item ids. A closure dated 2026-09-06 discussing Q50 narrows to the runs of that
week touching that item -- usually to one. That is a judgement a reader can make
while reading and a script cannot make at all, which is exactly why it belongs in
the manual pass rather than in a later automated sweep.

AND WHERE THE MATCH FAILS, RECORD THAT TOO. A decision whose supporting run cannot
be identified should say so in its record, rather than leaving a silent absence that
the next reader mistakes for "not looked for". An explicit "run not identified" is
what stops this question being reopened every time someone looks at the archive.

THE PAYOFF IS WHAT MAKES THE ARCHIVE WORTH KEEPING. H's conclusion is "archive
everything, because nothing can say what mattered". With the link, the next such
question is a query -- and "the history of rubric revision", which the user named as
a keep criterion, stops being 107 KB of prose nobody can search and becomes the
index of the archive.

#### Which means the general check cannot be an id scan

This is the design finding, and it has to be settled before the check is written.
`course_inventory` does not have this problem for code because it reads AST
subscripts and string literals IN CODE CONTEXT, and carries `_ambiguous()`,
`VOCABULARY` and `NAME_MARKERS` for precisely this class of collision. Free prose
has no such context, and this course's ids are ordinary words in a generic
document.

So a prose check keyed on ids alone would report the engine's own documentation as
course-contaminated, every run, forever -- and a check that cries wolf is worse
than none, because it trains its readers to wave it through. The signals that do
not collide are the ones to build on: a corpus reference (`{{corpus:ITEM/pN:...}}`),
a participant reference (`pNN` beside an item), a quoted gold comment, a measured
run figure. An id ALONE should at most be a candidate, never a finding.

THE CHECK IS A DELIVERABLE OF G2, confirmed 2026-09-23. There is no general check
for course-specific content in FREE PROSE today -- `course_inventory` parses with
`ast` and sees only `.py`, which is why 25 markdown files were never examined and
why this whole item went unnoticed until someone looked by hand. G2 ships the
check, and ships it with the false-positive discipline above; without it, G2's own
split cannot be verified to have finished, because nothing could say whether a
general document still had course content in it.

#### They are three different kinds of thing, not one

  1. SPLIT (the real G2 targets): `QUALITY_CONTROL.md`, `EQUIVALENCE.md`,
     `README.md`, `BACKLOG.md`. Each is a procedure with the course written
     through it.
  2. MOVE WHOLE, do not split: `GOALS.md` is a subgoal HISTORY -- 3,947 id hits in
     16,765 lines is not annotation, it is the record itself; and
     `Q6_MATCHING_CEILING.md` is named for an item. Splitting these would leave a
     general husk with nothing in it.
  3. NOT A G2 TARGET AT ALL: `OVERRIDES.md` is GENERATED -- "Written by
     precommit_gate.py; do not edit by hand" -- an append-only ledger of every
     gate override. It is certification output, which H already assigns to
     `scoring/`. Its quarter-million id hits are records, not prose.
     `STAGE5_LICENCE.md` (39 lines, 0 hits) is already purely general.

So G2 is FOUR splits and TWO moves, plus a disposition list H inherits.

#### The course-specific half may be better as JSON than as prose

The user's suggestion, and there is precedent for it: `GOALS.md`'s subgoal entries
are already carried as structured records in `goals.py`, keyed by subgoal id, with
the prose as the value. Where the course-specific half of a document is a TABLE OF
CASES -- this cell, this measurement, this verdict -- it should become records
under a key in `course.json` rather than prose in a second markdown file, because
then it is queryable by the tools that already read the course file and it cannot
drift from its own index. Where it is genuinely narrative, it stays prose in
`psychology/`.

Decide this per document, not once for all four. The test: could a reader ask a
question of it that a `grep` cannot answer?

#### `$COURSE_LOCATION` does not exist, and what does

Checked rather than assumed. `paths.py` declares `COURSE_DATA`, `COURSE_OUT`,
`COURSE_MEDIA`, `COURSE_ROOTS`, `CODE_HOME`, `LO_BLOCKS`, and `coursedata` honours
`COURSE_FILE`. NONE of them names the course's own content directory:

  * `COURSE_ROOTS` overrides `CORPUS_ROOTS`, which is the list of OTHER courses
    that count as corpus evidence -- a different question entirely, and an easy
    one to mistake for this.
  * `COURSE_FILE` points at `course.json` alone.
  * the content namespace is a HARD-CODED constant, `NS = "edu.memphis.psych"`.

CONFIRMED NEEDED, 2026-09-23. It is not a maybe: the split gives the same document
two homes, and every consumer must be told which tree it is reading from. The
pattern to follow already exists: Stage 9
renamed `MOLLY_* -> COURSE_*` with a `_RENAMED` table and `env_renamed()` honouring
the old names, and `check_filesystem_locations_come_from_paths_py` REQUIRES every
filesystem location to resolve in `paths.py` -- it has already caught paths spelled
into `olx_corpus.py`, on the reasoning that "a literal path does not fail on the
wrong tree, it SUCCEEDS on it". That check is what makes this enforceable rather
than a convention.

Every program that reads a split document must then be given the variable when it
is called. The sweep and gate shell scripts, the pipeline, and anything invoked
from a harness all need it, not just the python entry points.

#### What will break, and the failure mode to design against

THE CONSUMER COUNT IS THE WORK. 15 python modules read `QUALITY_CONTROL.md`, 12
read `GOALS.md`, 10 read `EQUIVALENCE.md`, 9 read `BACKLOG.md`. Every one must be
pointed at the half it actually wants, and the split is not done until they are.

AND THE FAILURE IS SILENT, which is what makes this dangerous rather than tedious:
a reader that opens the GENERAL file looking for course-specific content does not
error -- it finds nothing and reports nothing, exactly like the unwired check item
D retired. The guard has to be positive: each consumer asserts that what it read
contains what it came for, or the split is a way of losing content quietly.

ANCHORS ARE THE SHARP EDGE. These documents are cited by section anchor -- the
`see: qc:NAME` convention, with `anchors.py` reading all of them and a gate over
it. Splitting a file moves anchors between files; every citation must be
re-pointed, and the anchor gate must be made to check ACROSS the pair rather than
within one file. An anchor that resolves to the wrong half is worse than one that
does not resolve, because it reads as a working citation.

THE PROOF, same shape as A and F: the general document plus its course-specific
half must contain everything the original did, checked mechanically rather than by
reading -- no sentence lost, every anchor still resolving, every consumer still
finding what it came for, and the audit's finding set unchanged across the split.

#### DONE 2026-09-23 — what actually moved, and what measurement changed the plan

The composer is `scoring/compose_docs.py`. Every reader opens a COMPOSED
artifact built at `$COURSE_DATA/courses/<ns>/composed/`; writers keep the real
source. Composition is identity while a document is unsplit, so it was proved
against all four before a paragraph moved, and each move is checked the same
way: compose the halves and require the result to equal the document as it
stood.

  GOALS.md       53 generic / 16720 course   the charter, and this course's ledger
  EQUIVALENCE.md 877 / 2199                  five stages
  README.md      170 / 462                   three blocks
  QUALITY_CONTROL.md   NOT SPLIT             measured already generic
  BACKLOG.md, Q6_MATCHING_CEILING.md         moved whole

TWO RULES, and they are not the same rule. For CODE the test is what the control
flow assumes. For PROSE it is: A SECTION MOVES IF IT IS A RECORD; IT STAYS IF IT
IS A RULE, ILLUSTRATIONS INCLUDED. Settled by trying the code test on prose and
watching it fail -- "Lessons that generalise" puts each lesson and its evidence
on the same LINE, so stripping the course ids leaves bare assertions. Where a
record does carry a rule in passing, the rule is LIFTED VERBATIM into the
generic half, never paraphrased.

THE PLANNED ORDER WAS BACKWARDS, and one measurement says so. Bare item ids per
100 lines: EQUIVALENCE.md 20.5 before splitting and 10.7 after; README.md 28.1;
QUALITY_CONTROL.md 7.0. QUALITY_CONTROL.md is already more generic than the half
five stages of work produced, and README.md -- scheduled last -- was the densest
document in the set.

STORAGE FOLLOWS WHETHER A DOCUMENT ACCUMULATES, not whether it is long. A
guide's course half is authored and stays tracked with the course; a ledger's
grows with course work and is rewritten whole on every entry, so GOALS.md's and
BACKLOG.md's course halves live beside `gold.json`. GOALS.md alone was 1.2 MB
rewritten 414 times. What that cost: `goals.check()` compared against `git show
HEAD` to catch a deleted entry and an unapproved closure, and outside the
repository that returns None and both rules passed silently. `GOAL_STATES.json`
replaces it -- 112 labels and their states, 15 KB, tracked.

THE DEFECTS THIS FOUND ARE THE REASON TO TRUST THE RESULT. A code fence read as
a heading; a trailing anchor dropping its blocks; an `end` block flushing after
the next section's anchor; a block attaching mid-paragraph; a wrapped heading; a
rule COPIED instead of moved so the document said it twice; README.md absent
from `anchors.PROSE_FILES`; and `olx_prompts`' written-record scan reading the
53-line charter and reporting NO RECORD for every item while the composed
document held 249 mentions of Q6. Every one is now a check with a fire test, and
every one surfaced by running the composer on real prose rather than by reading
it.

The unpointed-anchor warning is now a FAILURE for section anchors -- an
unpointed one means the split did not connect -- and stays a warning for the 112
GOALS.md entry aliases, which exist so that any entry CAN be cited and are
unpointed by design.

### H · Regularize WHERE THINGS LIVE, one home per category

Filed 2026-09-23 on the user's instruction. The ten categories of
`MATERIAL_CLASSIFICATION.md` were a survey; this turns them into an address. The
test is a human one: someone opening the tree should be able to say what kind of
thing a file is from where it sits, without asking.

#### The destinations

| cat | what it is | home |
|---|---|---|
| — | the generic OLX engine | `lo-blocks` — already home |
| I | this course's OLX | `edu.memphis.psych/psychology/` — already home |
| II | course metadata (`course.json`) | `edu.memphis.psych/psychology/`, beside the handout OLX |
| II(a) | deviations between scoring versions | `scoring/` — they are declarations the audit reads |
| III | analytic machinery | `scoring/` — stays, and becomes most of what is there |
| IV | structured gold, web + python scorers | a named `$COURSE_DATA` subfolder |
| V | structured gold, paper scorer | a named `$COURSE_DATA` subfolder, separate from IV |
| VI | the original responses and gold comments | a named `$COURSE_DATA` subfolder |
| VII | materials the RUBRIC was derived from | a named `$COURSE_DATA` subfolder |
| VIII | materials the COURSE DESIGN was derived from | a named `$COURSE_DATA` subfolder |
| IX | fixture programs, paper form -> web form | `edu.memphis.psych/bmod_fixture/` |
| X | everything else | triaged: relocated by the same logic, or DELETED |

`scoring/` ends up holding exactly three kinds of thing, and nothing else:

  1. the analytic python that supports audits and certification, together with
     the `QUALITY_CONTROL.md` / `GOALS.md` cycle that governs it
  2. metadata about scorer versions
  3. the results of certifications, sweeps, and the ledger and accounting files
     that track them

WHERE RECORDS LIVE, decided 2026-09-23 and TIGHTENED. The small ledgers stay in
`scoring/` and stay VERSIONED -- `MEASURED.json`, `PROBED.json`,
`PROBE_RECEIPTS.json`, `DESIGNED_TEXT_SHA.json`, `LEAKAGE_REVIEWED.json`,
`GOALS.md`, `OVERRIDES.md`. Their diffs are how a sweep's effect is reviewed and
how `git log -p OVERRIDES.md` reads as the history of what the audit was asked to
excuse; outside git they would lose that. BULK RUN ARTIFACTS NEVER ENTER THE
REPOSITORY, which is already true -- `$COURSE_DATA/out` holds 826 of them, 1.66 GB,
and not one is tracked here.

AND THAT IS AN INTERIM ANSWER, not a settled one. An append-only log inside git
grows without bound, and DELETION DOES NOT RECLAIM: every version ever committed is
a permanent blob. Measured on this repository 2026-09-23:

    tracked content in the working tree      18 MB
    .git                                    362 MB
    OVERRIDES.md, all versions in history    80 blobs, 2,838 MB uncompressed
                                             -- 82% of every blob ever committed

So one machine-appended log is most of the repository's entire history, and
today's cleanup (48 MB -> 3.3 MB in the working tree) recovers NONE of it. The
file will resume doubling in history the next time it is appended to, because
each append rewrites the whole blob.

THE FIX IS CHOSEN, and revised the same day: DECISION LOG DATA GOES TO
`$COURSE_DATA`, with fallbacks so that a reader finding no records starts from a
CLEAN SLATE rather than failing. That is the C1b pattern already proven here --
gold lives outside the repository and may legitimately be absent, and the modules
that need it refuse with a message naming the path they tried while the rubric side
carries on. A log is a better fit for that pattern than gold is: an absent log
means "nothing has been excused yet", which is a perfectly good starting state.

IT SOLVES THE GROWTH AT THE ROOT. A log outside the repository cannot bloat git
history at all, so the question stops being how to rotate or cap and becomes simply
where the file lives. `OVERRIDES.md` is the clear first case, being machine-appended
and read only through `git log -p`; whether `GOALS.md` and `MEASURED.json` follow is
a judgement about whether their DIFFS are part of the code's contract or merely a
record of runs, and should be decided per file rather than by the class name.

THE POPULATION, DERIVED FROM HISTORY RATHER THAN FROM FILENAMES. Ranking every
tracked file by the history it has generated, and by SIZE PER WRITE -- which is what
makes growth unbounded, since a 600 KB source file edited 400 times is normal and a
35 MB log appended 80 times is not:

    scoring/OVERRIDES.md    2,837.7 MB   80 ver   35.47 MB/version   MOVED
    scoring/GOALS.md          128.3 MB  414 ver    0.31 MB/version   owed
    scoring/MEASURED.json       3.7 MB   83 ver    0.05 MB/version   stays
    everything else below 0.5 MB/version, which is ordinary code churn

OVERRIDES.md AND GOALS.md TOGETHER ARE 2,966 OF 3,452 MB -- 86% of every blob this
repository has ever stored, against 18 MB of tracked content.

`OVERRIDES.md` IS DONE: it resolves through `coursedata.overrides_path()` to
`$COURSE_DATA/courses/<id>/OVERRIDES.md`, beside `gold.json`, and the gate no longer
stages it -- it cannot, and never needed to, because every entry records
`(parent <sha>)`, which ties it to its commit more precisely than co-staging did and
survives a rebase that co-staging would not. Copied, verified byte-identical, THEN
removed, per this item's own protocol.

`GOALS.md` IS THE SAME PROBLEM AND A BIGGER JOB, not done here. Six modules read it,
each computing the path from `__file__`'s parent -- the same self-location pattern
that makes the tooling move above dangerous -- and one of the six is a SELF-TEST CASE
(`equivalence.py`) that injects a fault into it. So moving it touches the
certification machinery, which is a different class of change from OVERRIDES.md,
which nothing parsed. It needs its own step and its own certification.

`MEASURED.json` STAYS, measured rather than assumed: its content is BOUNDED. Each
item/side carries `previous` holding exactly ONE prior state, not a chain, so the
file does not grow with run count -- 46 KB per version across 83 versions. The
ledger accumulating runs was the obvious suspicion and the file does not do it.

AND THE RECURRENCE GUARD IS CHEAP, because there is exactly ONE append-mode write in
the entire package -- `precommit_gate`'s, now pointed outside the repository. Every
other record is rewritten wholesale and therefore bounded by its key space (items,
slots, cells) rather than by time. A check that no module opens a repository path in
append mode would keep it that way, and has one case to permit today: none.

AND THE WINDOW FOR REPAIRING THE PAST IS OPEN, WHICH IT WILL NOT ALWAYS BE.
`OVERRIDES.md` HAS NEVER BEEN PUSHED: the only ref known on the public remote is
`origin/main`, and `scoring/OVERRIDES.md` is not in its tree -- the branch carrying
it has no remote-tracking ref at all. (Read from local refs, so it reflects the last
fetch: strong evidence, not proof.) So the 80 blobs and 2,838 MB are private, and a
history rewrite would reclaim them cheaply and harm no one.

THAT STOPS BEING TRUE ON THE FIRST PUSH OF THIS BRANCH. After it, the blobs are in
a public repository that others may have cloned, and reclaiming them means asking
everyone to re-clone -- the reason this project treats its earlier history rewrite
as a scar rather than a tool. SO THE ORDER MATTERS: move the log out, then rewrite
the history that carried it, THEN push. Doing it in any other order either leaves
2,838 MB in a public repository forever or rewrites a history that is about to grow
again.

THE SUPPORTING SCRIPTS GET THEIR OWN SUBDIRECTORY, inside `scoring/` -- the user's
instruction 2026-09-23. They stay (they support audits and certification, which is
category 1 of the three `scoring/` may hold), but they stop being shelved among the
analytic machinery they serve. `editguard.py` is the named example.

TOOLING THAT TOUCHES COURSE CONTENT STILL GOES HERE, and getting that wrong is easy
-- the first discriminator tried was "a CLI tool importing NO course-data module",
and it is wrong in BOTH directions. It over-selects: `rubric_equivalence`,
`migrated_tables` and `shape_inventory` are analytic checks that merely happen not to
import course data. And it under-selects, which is worse: it would EXCLUDE
`course_inventory.py`, the clearest piece of tooling in the package after
`editguard`, because that module imports `coursedata` to fetch the item ids it
measures against.

THE SIGNAL IS NOT WHAT A MODULE READS, IT IS WHAT IT ENCODES -- which is the same
distinction this whole migration turns on. A tool may read every byte of course data
and still know nothing about this course:

    measured.py           12 embedded item ids, reads course data   -> machinery
    olx_prompts.py         8                                        -> machinery
    course_inventory.py    0 embedded item ids, reads course data   -> TOOLING
    corpus_ref.py          0                                        -> TOOLING

So the rule is: a module that ENCODES course knowledge is machinery (`scoring/`) or,
if the knowledge is about mapping paper to web, a fixture (`bmod_fixture/`). A module
that merely PROCESSES course data, carrying none of it, is a supporting tool and goes
in the subdirectory whatever it reads. Nothing is lost by touching course content;
what decides the home is whether the course is IN the module.

EMBEDDED-ID COUNT IS NECESSARY BUT NOT SUFFICIENT, and the residue has to be settled
by hand: `cross_path.py`, `faithful_probe.py` and `self_graded_misses.py` carry zero
ids and are still analytic -- they produce measurements ABOUT the course rather than
operating on the repository. The second question, after "does it encode the course",
is "does it produce a finding or maintain the tree". Settle both before moving
anything; do not move by intuition and declare the rule afterwards.

AND THE MOVE HAS A SILENT FAILURE MODE, which is the reason this is recorded here
rather than treated as shelving. Every one of these tools locates the package it
inspects from its OWN position:

    editguard.py         HERE = pathlib.Path(__file__).parent
    course_inventory.py  HERE = os.path.dirname(os.path.abspath(__file__))
    out_inventory.py     pathlib.Path(__file__).resolve().parent / "MEASURED.json"

`editguard.HERE` is what `modules()` globs and what `INVENTORY` resolves against.
Move the file into `scoring/tools/` and it inventories `scoring/tools/*.py` and looks
for `scoring/tools/DEFINITIONS.json`. IT DOES NOT ERROR. It reports a clean, tiny,
entirely wrong inventory -- and `check_every_module_is_tracked` and
`check_every_definition_is_recorded` would both go quiet at the same moment, since
both ask editguard what the package contains.

So the relocation must repoint those locations FIRST, at the package root rather
than at `__file__`'s parent. The lever already exists:
`check_filesystem_locations_come_from_paths_py` requires filesystem locations to
resolve in `paths.py`, on the reasoning that "a literal path does not fail on the
wrong tree, it SUCCEEDS on it" -- which is precisely this failure, stated in advance.

THE IMPORT CHURN IS SMALL, measured: `editguard` is imported by 1 module,
`course_inventory` by 2, `guide` by 1, `anchors` by 1, `out_inventory` by 0. The
cost is not the imports. It is the three `HERE`s and the two ledgers keyed by bare
module filename (`DEFINITIONS.json`, `COURSE_DATA_BUDGET.json`), which a move
rekeys.

#### H(2) · DONE 2026-09-24 -- the six settled tools are in `scoring/tools/`

    anchors.py  corpus_ref.py  course_inventory.py  editguard.py  guide.py
    out_inventory.py

These are the six this item already settles by name. The remaining 37 zero-data
modules are NOT moved: goal H's second question -- does it produce a FINDING or
MAINTAIN the tree -- has to be answered by reading each one, and this item says
so ("do not move by intuition and declare the rule afterwards").

THE SELF-LOCATION HAZARD WAS REAL AND IT BIT TWICE MORE, both times exactly as
this item predicted and both times silently:
  * `guide.HERE` resolved to `tools/` and looked for QUALITY_CONTROL.md there.
    That one failed LOUDLY only because the thing it wanted is a document; a
    glob would have returned an empty set and said nothing.
  * `guide`'s own tree scan globbed the root alone, so it stopped seeing
    `corpus_ref` the moment it moved and reported its function as "renamed or
    removed" -- a finding about the scan, delivered as a finding about the tree.
    It reads `editguard.modules()` now, the one inventory that knows the
    package's shape.

`editguard.modules()` covers root AND tools, because a glob that misses a
directory is a ledger that misses its modules, and that ledger feeds both
`check_every_module_is_tracked` and `check_every_definition_is_recorded`.

BOTH SPELLINGS WORK. `tools/__init__` puts the package root on the path for
`from tools import X`, and each tool repeats it for `python3 tools/X.py`,
because a file run as a script never executes the package `__init__`.

ONE EDIT WAS REVERTED RATHER THAN WORKED AROUND. Repointing the invocation
strings changed a line inside an APPROVED LESSON in QUALITY_CONTROL.md, and
lessons are approved by the sha of their prose precisely so they cannot be
reworded without agreement. Self-approving would have defeated the gate, so the
doc still says `python3 editguard.py`; correcting it needs the user, and it is
recorded here rather than silently fixed.

#### WHAT MAKES A MODULE GENERIC, and it is not what a scan can tell you

This is the test every placement decision in this item turns on, and it was got
wrong twice before it was stated properly.

NOT "does it embed course data". `course_inventory` reports ZERO item ids across
all nine fixture modules, and on that basis they were called generic. They are not:
they were written to parse THIS course's handouts, tuned against THESE graders'
documents, and have never been run on anything else. Absence of literal ids is weak
evidence, and reading it as proof is the same over-reach that made a bare-id scan
call seven clean lo-blocks files contaminated.

NOT "has it worked for another course" either, however much one would like it. There
is no second course, so the question cannot be asked, and a test that cannot be run
decides nothing.

THE TEST IS WHAT THE CONTROL FLOW ASSUMES, and it is inspectable today, per module,
by reading:

    GENERIC BY CONSTRUCTION   the shape arrives as INPUT. Markers, field lists,
                              item structure come from declarations or data, and
                              the code would meet a different shape unedited.
    FINE-TUNED TO THIS DATA   the shape is IN THE LOGIC. "the answer sits on the
                              same line as its label", "there are three handouts",
                              "the boxes come in this order", a regex adjusted
                              until it matched these particular documents.

No scan answers this. It is a judgement made by reading the code, one module at a
time, and it is the only honest basis for deciding what may leave the course behind.

#### IX REVISED: THE FIXTURE GOES UNDER `$COURSE_LOCATION`

Decided 2026-09-23, reversing this item's own earlier text. The fixture machinery
maps THIS course's paper forms to THIS course's web forms; it looks generic and is
not, by the test above. So it goes to the course's own folder with the rest of the
course's material, rather than to a `bmod_fixture/` at the repository root -- which
would have left it belonging to neither the machinery nor the content.

What travels with it is the course-bearing fixture DATA:
`PROSE_SPLIT_WORKSHEET.json` (1.2 MB, 3,352 course signals) and
`CONSENSUS_SPANS.json` (74). `GRADER_INPUTS.json` and `STRUCTURE_KIDS.json` carry
none and are decided by the same test as everything else, by reading them.

IX IS THE INTERESTING CASE and the reason it gets its own folder rather than a
move out of the repo: the fixture code maps responses and gold comments between
the paper and web forms, so it is COURSE-SPECIFIC — but it is executable
machinery with an audit attached, so it cannot live in `$COURSE_DATA` with the
documents. `bmod_fixture/` names it for what it is and keeps it in the repo.

#### H(4) · CATEGORY IX READ MODULE BY MODULE, and the reading corrects the list

Goal H requires this ("a judgement made by reading the code, one module at a
time") and the result DIFFERS FROM ITS OWN CATEGORY IX LISTING. The listing was
a survey; the test is what the control flow assumes. Per module:

  segment.py            FIXTURE. The shape is in the logic: "Handout 1's
                        template carries a worked fruit-flavored water example
                        and Handout 3's carries an example data table AND an
                        example graph". It would not meet a different handout
                        unedited.
  fixture_edits.py      FIXTURE. Corrections as spans over THIS corpus.
  grader_inputs.py      FIXTURE. The table the intake program is steered by --
                        which grader a chunk of teacher material becomes.

  docx_text.py          NOT FIXTURE, against the listing. "Stdlib-only OOXML
                        text extraction"; it reads paragraphs, tables and chart
                        parts. Item 1c is named as the REASON chart parts are
                        extracted, not as an assumption the code makes. It would
                        meet a different .docx unedited -> generic machinery.
  paper_runs.py         NOT FIXTURE. It folds a paper sweep into the ledger's
                        runs shape -- analytic plumbing between two artifact
                        formats, with no paper-to-web mapping in it.
  prose_split.py        NOT FIXTURE. Its subject is this repository's DOCUMENTS,
                        sorting sentences into specification/incident/split. It
                        maintains the tree -> tooling.
  canonicalise_verdicts.py   MIGRATIONS, not fixtures. Each is a one-off rename
  migrate_verdicts.py        over the vocabulary, already run, and the user's
  stamp_legacy_artifacts.py  instruction is to DELETE migration scripts when
                             they are no longer needed rather than rehome them.

SO CATEGORY IX IS THREE MODULES, not nine, and the other six sort into three
different homes. Recording this before moving anything is the discipline this
item asks for -- "do not move by intuition and declare the rule afterwards".

AND THE MOVE ITSELF RAISES A STRUCTURAL QUESTION THE DECISION DID NOT SETTLE.
`$COURSE_LOCATION` is `psychology/bmod`, inside the CONTENT tree, and
`build:stage-content` copies that tree wholesale -- python modules included. It
is harmless today (the static build emits three parsed artifacts and copies
nothing raw), but it means `import segment` would resolve through a content
directory, and `segment` is imported by four modules. That is a python import
path running through content, which is a different kind of coupling from where
the file sits. The fixture DATA has no such problem.

#### `course.json` moves WITHIN the repo, and that is what keeps C1b intact

Decided 2026-09-23: it goes to `psychology/`, with the handout and rubric `.olx`
it describes — NOT to `$COURSE_DATA`. An earlier draft of this item proposed the
latter and had to raise a conflict against it; the decision removes the conflict
rather than trading against it, so the conflict is recorded here only as the
reason the placement is right.

WHAT WOULD HAVE BROKEN. `coursedata.gold_declaration` rests on the two files
having DIFFERENT availability — "the course file ships inside this public
repository and is always there, while gold lives outside it and may legitimately
be absent (C1b)" — with the measured consequence that with gold absent,
`coursedata` and `rubric_for()` still import and only the four gold-consuming
modules refuse. Putting `course.json` under `$COURSE_DATA` collapses that: the
rubric half stops working without the data directory too, and the error stops
naming which file is missing, which is precisely what C1b's two separate
accessors exist to prevent. Staying in the repo preserves all of it, and no
copy, no sync and no equality check are needed.

AND IT PUTS THE METADATA BESIDE THE CONTENT IT DESCRIBES, which is this item's
whole test: `psychology/` already holds `bmod_rubric.olx`, the three handouts and
39 other course files, and `course.json` is the metadata for exactly those.

`courses/` THEN RETIRES. It holds two files and nothing else: `course.json`, and
`CHANGELOG.md` — which is the course's changelog and follows it to `psychology/`.
The directory goes.

BEWARE THE SURVIVING HOMONYM. `courses/` continues to exist under `$COURSE_DATA`,
where `gold.json` lives (`$COURSE_DATA/courses/<course-id>/gold.json`,
`coursedata.gold_path` and `gold_export`). After this move the name means one
thing instead of two, which is an improvement — but anything reading "courses"
must be checked for WHICH of the two it meant, not assumed.

FOUR IN-REPO HARDCODERS, and A's rule applies: one resolver, never four copies.

    scoring/coursedata.py:116        course_path() -- the one that should stay
    scoring/rubric_equivalence.py:224
    scoring/anchors.py:88
    scoring/prose_vocabulary.py:99

`course_path()` already honours a `$COURSE_FILE` override, so the move is one
line there plus three call sites routed through it. Three modules independently
recomputing the same path is the same shape as `migrated_tables.BUILDERS` being
a second copy of the builder list, which §13 A had to fix mid-flight.

#### What actually moves, counted

`scoring/` today: 73 `.py`, 16 `.json`, 8 `.md`, 4 `.sh`, plus `materials/`,
`drafts/`, `__pycache__/`.

  -> `bmod_fixture/` (IX): `segment.py`, `docx_text.py`, `prose_split.py`,
     `fixture_edits.py`, `canonicalise_verdicts.py`, `migrate_verdicts.py`,
     `grader_inputs.py`, `stamp_legacy_artifacts.py`, `paper_runs.py`, with
     `PROSE_SPLIT_WORKSHEET.json` and `GRADER_INPUTS.json`, and the fixture audit
     that goes with them. The exact set is to be re-derived from the tree at the
     time, not from this list — §13 A is the precedent: the agenda's table list
     was three entries stale by the time it was executed.
  -> `$COURSE_DATA` (VII, VIII): all of `scoring/materials/` — the scoring and
     feedback dictionaries to the rubric-sources folder, the handouts, decks,
     syllabus and schedule to the design-sources folder.
  -> DELETED: `scoring/drafts/` (two interim notes), `__pycache__/`,
     `writescope.sh` (a fixture of this session's scope, not of the project), and
     the interim planning documents named in category X once their content is
     either folded in or genuinely spent.

     TWO ARE NAMED AND CONFIRMED DEAD by the user, 2026-09-23, to be deleted when
     H is implemented -- and each carries a declaration that must go in the SAME
     act, because a declaration naming a file that no longer exists is the shape
     this project has already been bitten by (`RAW_GOLD_READERS` named a check
     that did not exist, and the exemption was legitimate while its name had been
     wrong for as long as nobody looked):

       `SCORING_REFACTOR_PLAN.md`  (5,011 lines, 133 id hits) -- no longer live.
           It is an entry in `enforcement.OLD_ENV_NAMES_ALLOWED`, exempted there
           BECAUSE it documents the `MOLLY_* -> COURSE_*` rename. Delete the file
           and that entry goes with it; leaving it would declare an exemption for
           nothing. `MATERIAL_CLASSIFICATION.md` also lists it.

       `VERDICT_VOCABULARY_PLAN.md` (301 lines, 27 id hits) -- no longer live, and
           already declared RETIRED in §12 of this plan. Cited from
           `scoring/BACKLOG.md:270` and from §12's own closing paragraph; both
           citations become dangling and must be resolved rather than left.

     The rule from item G2 applies to both: the deletion set is stated as a RULE
     with every match shown, never assembled from the files someone remembered.

DELETION IS LICENSED BUT NOT CASUAL. The user's standing instruction is that
planning documents live on in committed history and temp scripts and outputs not
needed for documentation are deletable at H. The discipline that applies is the
one this project already has: ENUMERATE THE POPULATION FIRST and state the rule
that selects it, so a deletion set is never assembled from the instances someone
happened to notice. `fixset_coverage.py` exists for exactly this.

#### THREE BODIES OF WORK THE CATEGORIES DO NOT COVER

Found by enumerating every `.py`/`.sh`/`.ts`/`.js` in the repo rather than trusting
the ten categories to be exhaustive. They were not.

1. `migration/` -- 52 SCRIPT FILES, AND CATEGORY X IS WRONG ABOUT THEM.

   X files them as "the migration harness itself" under "everything else: triaged,
   relocated by the same logic, or DELETED". THAT CONTRADICTS THIS PLAN'S OWN TEXT,
   which says "**Preserved for this stage.**" of `migration/stage00_*.py`,
   `stage01_*`, `stage04_*`, `stage05_*` and more, at four places in section 7.

   They are also LIVE, not spent: newest file 2026-09-22, and
   `enforcement.py` names `migration/goldens/audit_baseline.json` as something the
   freeze cannot pass without. AND ITEM C DEPENDS ON THEM DIRECTLY -- C(i) records
   that "the harness and the gate already exist in `migration/`:
   `stage02_assembler_surface.py`, `stage02_gate.py`, `stage03a_gate.py`,
   `stage03b_gate.py`". Deleting or shelving them would remove the acceptance
   instrument for the item ranked fourth in this queue.

   DECIDED 2026-09-23: DELETE THEM WHEN THEY ARE NOT NEEDED -- which is a retirement
   CONDITION, not a date, and the condition is what H must record. A stage's scripts
   are spent when the stage they gate is complete AND nothing still reads their
   output. Today that is false of at least three:

       stage02_assembler_surface.py, stage02_gate.py, stage03a/b_gate.py
           item C's acceptance instrument. C is fourth in the queue; these go when
           C is done, not before.
       migration/goldens/audit_baseline.json
           named by `enforcement.py` as something the freeze cannot pass without.
           It goes when nothing names it.

   So `migration/` is not a residue to sweep and not a monument to keep. It is
   machinery with an expiry that each stage sets for itself, and the deletion rule
   is per-stage: gate complete, output unread, then delete -- stated as a rule and
   run against every stage, never by eyeballing which look old.

2. `scoring/*.sh` -- LOAD-BEARING SHELL THE RULE DOES NOT MENTION.

   H says `scoring/` holds "the analytic PYTHON that supports audits and
   certification". The sweep drivers are shell and are referenced from python:

       sweep_app.sh     8 referrers, incl. measured.py, head_to_head.py, paper_runs.py
       sweep_cli.sh     6 referrers, incl. measured.py, head_to_head.py
       sweep_paper.sh   5 referrers, incl. enforcement.py, score.py, measured.py

   DECIDED 2026-09-23: THE SWEEP DRIVERS ARE TOOLS and go to the tools
   subdirectory with `editguard` and the inventories. They drive the work rather
   than producing a finding about the course, which is the second of the two
   questions this item uses to place a module. `writescope.sh` is the one genuinely
   disposable member, being a fixture of one session's write scope.

   NOTE WHAT THAT COSTS: five python modules reference these by bare filename
   (`measured.py`, `enforcement.py`, `score.py`, `head_to_head.py`,
   `paper_runs.py`), so the move rewrites those references, and any that build the
   path from `__file__`'s directory hits the same silent redirection as the three
   `HERE`s above.

3. THE EVENT PIPELINE -- OUTSIDE THIS PLAN, AND UNDER NO VERSION CONTROL AT ALL.

   WHAT IT IS, since the name is not self-explanatory. `~/code/scripts/` holds 18
   scripts, four of which are a chain that turns raw lo-blocks LEARNER ACTIVITY
   CAPTURES into readable per-form logs:

       process_events.py         14,922 lines. Rewrites a lo-blocks events .jsonl
                                 stream into a readable log. The raw capture is
                                 optimised to RECOVER STATE for exact replays and
                                 only makes sense replayed against the runtime
                                 state machine; this makes it readable by scanning
                                 events alone.
       consolidate_user_events.py  per-session .json -> one file per USER, time
                                 ordered across sessions, SESSION_BREAK between.
       forms_by_users.py         re-parcels a user's log BY FORM: one file per
                                 (user, form), timeline preserved.
       run_pipeline.sh           runs the three end to end.

   AND IT IS IN NO REPOSITORY, which is worse than being in a different one.
   Neither `~/code` nor `~/code/scripts` is a git repository -- the only repos under
   `~/code` are `edu.memphis.psych` and `lo-blocks`. `process_events.py` also exists
   as two older loose copies:

       ~/Documents/process_events.py      6,962 lines   2026-07-01
       ~/Desktop/process_events.py       12,719 lines   2026-07-14
       ~/code/scripts/process_events.py  14,922 lines   2026-07-29   <- the live one

   So the largest single program in this ecosystem has no history, no diff against
   its own past, and two divergent snapshots beside it.

   DECIDED 2026-09-23: IT STAYS IN `scripts/`, AND THIS SESSION DOES NOT TOUCH IT --
   not reading, not writing, not deleting. H does not relocate it, does not
   annex it, and does not propose a home for it. `scoring/writescope.sh` now names
   `/home/pdeane/code/scripts` in FORBIDDEN rather than relying on the ALLOWED
   list's silence, because an omission stops protecting the moment that list
   widens.

   H STILL NAMES IT, though, for the reason this section exists: a reader checking
   coverage against the ten categories would otherwise conclude the pipeline had
   been considered and placed. It was considered and deliberately left alone, which
   is a different fact and a better one to have written down. The versioning
   observation above is left as an observation -- someone else's call, not this
   plan's.

   IT IS NOT SCORING TOOLING. It processes what a learner did on screen in ANY
   lo-blocks activity; this project grades handout responses. The two touch at
   exactly one point: the pipeline is the only consumer of `olx_string_idmaps.ts`
   (item E). The other 14 scripts there are operational -- sweep drivers, failure
   clustering, wait helpers.

   H should NOT quietly annex it -- it is outside this session's write scope and may
   have its own home. But it must be NAMED, because "the categories cover
   everything in the two directories" is true and misleading: the pipeline is
   neither, and a reader checking coverage against this plan would conclude it was
   considered when it was not.

#### PARKED AND STAGED WORK -- H had no plan for this, and it is the larger half

Everything above is about FILES IN THE REPO. The run artifacts are not in the repo
and are bigger than everything else H moves put together:

    $COURSE_DATA/out/        826 entries    1.6 GB    2026-07-30 .. 2026-09-22

They are sweep and probe runs -- `after_1.json`, `WK1.runs.json`, per-item
directories, A/B pairs -- two months of them. Some are the evidence behind recorded
findings; most are superseded attempts. The user's framing is the right one: some
is still valid, "like goals related work for specific items", and a lot is junk.

THE LICENCE FOR DELETING PLANNING DOCUMENTS DOES NOT REACH HERE, and this is the
single most important thing in this section. That licence rested on the documents
being recoverable: "The planning documents will be in the committed history if we
need to go back to them." `$COURSE_DATA` IS NOT A GIT REPOSITORY -- checked, there
is no `.git` anywhere above `out/`. Deleting a run destroys the only copy of a
measurement that cost real grader calls. Nothing here is recoverable, so nothing
here may be deleted on the same reasoning.

THE INVENTORY EXISTS NOW, written 2026-09-23 before anything was deleted, because
"a lot will be junk" is an impression and a list is a fact. `build_out_inventory.py`
is READ-ONLY and decides nothing: per entry it records size, file count, mtime, and
which LEDGER ENTRIES name it through the ledger's own reference field --
`MEASURED.json`'s `items[item][side].out`, which is the only such field any ledger
carries today.

    entries   826        1.66 GB        2026-07 .. 2026-09
    cited      17          49.2 MB      3% of the volume
    uncited   809        1614.2 MB     97%

    uncited by month:  2026-07  17    2026-08  463    2026-09  329

AND THE FIRST NUMBER I QUOTED WAS WRONG, which is the lesson worth carrying more
than the figure. A substring scan of four ledgers reported 26 referenced; the
ledger's own reference field reports 17. The scan matched directory names inside
unrelated text. That is the FOURTH time in this session a crude pattern over
structured content produced a confident wrong answer -- G2's prose scan called seven
clean lo-blocks docs contaminated, G(a)'s `NAME_MARKERS` returned 79 definitions
where 3 were real, and item I's `{param}` probe reported sharing going DOWN, which
is arithmetically impossible. The rule that keeps being relearned: ASK THE STRUCTURE,
NOT THE TEXT. Here that meant reading the field the ledger actually stores.

#### The goal, stated by the user, and what the measurements say about reaching it

"Prepare for making the data that supported a decision or affects current states
and goals ARCHIVAL, cleaning up anything truly irrelevant to the current state of
the system or the history of rubric revision."

That is a better axis than space or tidiness, and it gives a per-entry test: did
this run SUPPORT A DECISION, does it bear on CURRENT STATE OR GOALS, or is it part
of the HISTORY OF RUBRIC REVISION? Any yes -> archive. Only a no to all three is
deletable.

THE TEST CANNOT BE APPLIED MECHANICALLY, and this is the central finding. The link
between a decision and the run that supported it WAS NEVER RECORDED. `goals.py` is
16,765 lines of decision narrative citing measurements constantly -- "measured 12
configurations: 1/6, 3/6, 6/6 ..." -- and it cites the FINDING, never the artifact.
Searching every distinctive run name across `goals.py`, `BACKLOG.md`,
`QUALITY_CONTROL.md`, `EQUIVALENCE.md`, `measured.py`, `declaration_source.py` and
`README.md` finds 18 named in prose; the ledger names 17; together 32 OF 826. The
other 743 distinctive names appear nowhere at all. (51 names are too short or
wordlike to match safely and were not attempted -- the same restraint the prose scan
in G2 needed.)

So there is no query that separates "supported a decision" from "superseded
attempt". The data to answer it was never written down.

WHICH IS WHY THE ANSWER IS TO ARCHIVE THE LOT. Measured compression on three
representative runs: 16.7x, 20.6x, 22.9x. JSON run artifacts compress
extraordinarily well, so

    1.66 GB of out/   ->   roughly 70-100 MB compressed

At that size the question stops being worth adjudicating. Archiving everything costs
under a tenth of a gigabyte and cannot destroy a measurement that cost hundreds of
grader calls; adjudicating 826 entries against a link that does not exist can, and
would take far longer than compressing them.

THE PROVABLY DELETABLE SET IS TINY, and needs no judgement at all:

    26 entries with no files          a run that created a directory and nothing else
    28 entries of zero bytes
    15 entries holding ONLY logs      0.1 MB -- a run that produced no results

That is the whole of "truly irrelevant" that can be established without guessing.
Everything else is archived, not deleted.

THE DURABLE FIX IS THE LINK, AND IT IS G2'S, NOT THIS ITEM'S. Consolidated there
on the user's instruction: a decision and the runs behind it are ONE record, and G2
is what gives that record a structure to hold them. Specifying a second mechanism
here would orphan the link the same way the runs are orphaned now. See G2's section
"G2 owns the run-to-decision link".

Two things H contributes to it. `MEASURED.json` already carries
`items[item][side].out`, populated for 17 runs -- but that is ITEM x SIDE -> run,
the ledger's granularity, where the missing link is DECISION -> run. And the
inventory built for this item is what a backfill would work from: it is the only
list of what exists.

RECOMMENDED SHAPE, then:
  1. compress every entry in place, one archive per run, keeping the names;
  2. delete only the ~69 empty / zero-byte / log-only entries, listed in full first;
  3. stamp `out` on every future sweep, and backfill it wherever a decision record
     makes the run obvious;
  4. revisit deletion only once (3) has made the question answerable.

#### Write scope H requires, and why it is bigger than any step so far

H CANNOT RUN UNDER THE STANDING OVERNIGHT SCOPE. That scope allows the two dry-run
repos plus `$COURSE_DATA/out/**` and `$COURSE_DATA/courses/**`, and it names as
NEVER writable the source documents and records — "Handout Submissions with
Scoring and Feedback" (the submissions and the graders' workbooks),
`migration_reference`, `migration_goldens`, `retired_artifacts`, `handsplit`,
`pre_scrub_backup_*`, `corpus_refs.json`.

Those are exactly the things categories V and VI say must move into named
subfolders. So H needs an EXPLICIT, DELIBERATE scope amendment covering the new
`$COURSE_DATA` subfolders for IV, V, VI, VII and VIII — and it must be granted as
its own decision, not inherited. `writescope.sh` encodes the current rule and
refuses the rest; it has to be updated in the same act, so that the tool and the
permission never disagree.

THE MATERIAL BEING MOVED IS THE IRREPLACEABLE KIND. The repo can be rebuilt from
git. Student submissions and graders' workbooks cannot be rebuilt from anything.
Everything below exists because of that asymmetry.

#### The move protocol: copy, verify, and only then remove

NEVER `mv`. NEVER a rename. Copy, prove the copy, and only then remove the
original — in that order, for every file, with no exceptions and no batching that
hides a failure.

  1. **Freeze a manifest of the source set** before touching anything: relative
     path, byte size, and sha256 for every file. Written to disk, not held in a
     variable, and the count recorded. This is the thing the move is checked
     against, and it cannot be regenerated afterwards from the destination —
     that would be marking one's own homework.
  2. **Copy** to the destination. Refuse outright if the destination already
     exists with different content; an overwrite during a reorganisation is
     indistinguishable from a loss.
  3. **Verify against the manifest, exhaustively**: every path present, every
     sha256 equal, every size equal, the counts equal on both sides, and NO extra
     files at the destination. A verification that only checks the files it
     copied cannot see one it forgot to copy.
  4. **Verify the READERS still work**, which is a different question from the
     bytes being intact: the `course.json` export still byte-identical, the audit
     finding set unchanged, the certification green. Files can arrive perfectly
     and still be in a place nothing looks.
  5. **Only then remove the source**, and re-run step 3 against the destination
     afterwards to confirm the removal took nothing with it.

`$COURSE_DATA` GETS A STRICTER RULE STILL. For the submissions and the graders'
workbooks — categories V and VI — the source is NOT removed in the same pass at
all. Copy, verify, run the scorers against the new location, and leave the
original standing until the user confirms the move is good. `pre_scrub_backup_*`
exists in that tree precisely because this project has already decided once that
irreplaceable inputs get a backup before a bulk operation; H is a bulk operation
over the same class of data.

A DRY RUN FIRST, ALWAYS: the whole protocol with the copy and the removal
disabled, reporting exactly what it would move, from where, to where, and what it
would delete. The enumeration discipline applies to the deletion set as much as
the move set — state the rule that selects it and show every match, never a set
assembled from what someone happened to notice.

IF ANY STEP FAILS, STOP AND REPORT. Do not continue with the remaining
categories, do not "clean up" a partial move, and do not delete anything to tidy
the state. A half-finished move with both copies present is recoverable; a
half-finished move that has already started deleting is not.

#### What this will break, and the proof obligation

  * **`paths.py` is the chokepoint.** Every constant naming a moved file moves
    with it, and nothing may keep a second copy of a path — the A precedent:
    one list, two consumers, never two lists.
  * **The ledger does not follow a file out of `scoring/`.** `editguard.modules()`
    globs `HERE/*.py` and nothing else, so a module moved to `bmod_fixture/`
    leaves `DEFINITIONS.json` AND leaves item G's `check_every_module_is_tracked`
    — both go quiet together, which is the worst possible combination and
    precisely the silence G was filed to end. `modules()` must learn the new
    directory IN THE SAME COMMIT as the first file that moves there.
  * **`COURSE_DATA_BUDGET.json` is keyed by module filename**, so every move
    rekeys it; it ratchets down only, and re-tightening is deliberate (A).
  * **`check_no_module_is_named_for_a_course_artifact`** must be told what
    `bmod_fixture/` is. A directory named for the course is the correct answer
    here, not a violation — but it has to be declared, not assumed.
  * **Write scope and the move protocol** have their own sections above; nothing
    in H may begin until the scope amendment is granted explicitly.

THE PROOF IS THE ONE A USED, and it is available here for the same reason: the
artifacts are the interface. A byte-identical `course.json` export, an identical
audit finding set, and a green certification across the move together mean the
relocation changed where things are and nothing else. Anything less is a
reorganisation that also did something, and nobody will know what.

### I · Documentation thorough enough to AUTHOR from, for the two components that carry the load

Filed 2026-09-23 on the user's instruction. `SlotSheetGrader` and the `Rubric`
family carry most of the heavy lift for new functionality, and the test for their
documentation is not "is each element described" but: COULD A NEW AUTHOR, READING
ONLY THIS, WRITE RULES FOR A WIDE RANGE OF CASES? Today they could not, and the
reason is structural rather than a matter of length.

WHAT EXISTS IS REFERENCE; WHAT IS NEEDED IS A GUIDE. There are 22 rubric block
documents, 22-90 lines each, one playground apiece -- one element, one example,
no interaction. `SlotSheetGrader.md` is 140 lines with 4. Reference tells you what
`Forbid` is. It does not tell you that `Forbid` plus `Equals` is how three of
these items express a contradiction, or when to reach for `Onlyif` instead.

#### The population to cover, measured from the rubric itself

26 items, and the shape of the corpus is lopsided in a way that decides the work:

| tier | primitives | reach |
|---|---|---|
| in every item | `Credit`, `Deduction`, `Question` | 26/26 |
| near-universal | `Guidance` 25, `Slot` 23, `Context` 23 | |
| DISCRIMINATING, and rare | `Forbid` 7, `Equals` 6, `Onlyif` 5, `Expect` 5, `Map` 4, `Counts` 4, `Derived` 3, `Requires` 2, `Cover` **1** | |

**17 distinct shapes across 26 items.** The four most common:

    x3  Context+Credit+Deduction+Expect+Guidance+Onlyif+Question+Slot
    x3  Context+Credit+Deduction+Guidance+Question            <- NO Slot at all
    x3  Context+Credit+Deduction+Equals+Forbid+Guidance+Question+Slot
    x2  Context+Counts+Credit+Deduction+Guidance+Question+Slot

THE NO-SLOT SHAPE IS A BASE CASE, not an oddity: three items are scored
deterministically from the page with no `<LLMAction>` at all (the `SHEET_ONLY`
set). A guide that opens with slots has already skipped one of the two ways to
build an item.

AND THE TEMPLATE LAYER IS A SECOND AXIS, which a scan of `<Item>` children misses
entirely -- noted by the user, and the first version of this table did miss it:

    Frame        29 uses      Segment    39 uses
    conditions=  11 distinct names, most used by 2-4 items
    params=      on 4 items
    ItemTemplate  0 uses      Param (element)  0 uses

So the conditional layer in THIS course is `Frame`/`Segment`/`conditions=`, and
`ItemTemplate` -- a documented primitive with a 78-line reference page and its own
test -- is exercised by nothing at all.

AND IT NEVER HAS BEEN, which is worth knowing before writing its guide. Checked
against `migration_reference`: the PRIOR dry run's rubric also carries zero
`<ItemTemplate>`. It was built alongside `Frame`, `Param`, `Context`, `Guidance`
and `Question` in that run's block family, shipped with a test and a `.md`, and no
content has ever needed it. So its documentation cannot be written by reading what
someone did with it -- there is nothing to read, and the guide's examples for it
will be the first use it has ever had.

A SECOND MECHANISM IS UNEXERCISED HERE AND WAS NOT THERE. The prior run's items
declared `use="@oc_criteria"` eight times -- a reference to a `<Frame>`, not to an
ItemTemplate. Ours declare it zero times: we carry the same `oc_criteria` frame,
but the items hold `conditions=`/`params=` and the CONSUMER calls
`as_view_frame(name, conditions, params)` by name instead. The declaration moved
out of the content and into the reader. Whether that was deliberate is not
recorded anywhere, and the guide should not describe `use=` as the way frames are
reached until it is settled -- documenting a mechanism this rubric does not use,
as though it were the norm, is how a guide teaches the wrong thing.

CONSEQUENCE FOR THE BUILD STEP: `build:expand-rubrics` is a no-op today.
`.stage/expanded/.../bmod_rubric.olx` is BYTE-IDENTICAL to the authored file, 1,047
lines each. The expansion machinery is wired and has no input -- which is fine
while nothing templates, and is the reason nobody would notice if it broke.

#### Which is exactly where the invented examples are owed

The user's instruction covers combinations the corpus misses but which have an
obvious use case. Measurement says which those are, so the list is derived rather
than guessed:

    ItemTemplate + Param   0 items   documented, never once used. An author
                                     reading the page has no worked case showing
                                     when templating beats writing items out.
    Cover                  1 item    the single hardest primitive to reason about
                                     and the thinnest evidence in the corpus.
    Requires               2 items
    Derived                3 items

Those four need examples built for the guide, not lifted from the handouts --
which is a different and slower kind of work than documenting what is already
there, and should be planned as such.

#### How to build the `ItemTemplate` examples, since there is nothing to copy

Instructed 2026-09-23: crib the first instance off REAL items, prove it works,
and only then make the content generic. That ordering matters because it converts
the hard question -- "does this template actually do what the page claims?" --
from a judgement into a diff.

THE CRIB IS ALREADY PICKED OUT BY THE RUBRIC ITSELF. `family=` declares which
items share slot structure, and one family is large enough to be worth templating:

    h2-cadence-and-type    8 items    PR, NR, PP, NP, DAY1, WK1, DAY2, WK2

Measured across those eight: SEVEN slot keys appear in all eight -- `names_behavior`,
`names_stimulus`, `contingent`, `follows_behavior`, `you_arrange_it`,
`observed_type`, `confident` -- with `phrased_directly` in seven. The rest arrive in
fours and twos, gated by the conditions those items already carry
(`cadence_daily`, `cadence_weekly`, `type_match`, `barrier_pick`,
`contingency_gate`, ...). And four of them ALREADY carry `params="cadence=daily"`
or `cadence=weekly`.

So the template writes itself from the evidence: a shared core of seven slots,
`ifDeclared=` on the gated additions, and `{cadence}` substitution for the pair
that differs only in period. That is precisely the shape `materialiseRubric.md`
documents and nothing has ever exercised.

THE MECHANISM WAS CHECKED AGAINST ITS IMPLEMENTATION BEFORE PLANNING ANY OF THIS,
because the plan otherwise rests on a documentation page for a feature no content
has ever used. It supports what the family needs:

  * `{name}` substitution works INSIDE ATTRIBUTE VALUES, which is what lets a slot
    KEY vary (`key="is_{abbrev}"`), not just its prose;
  * `ifDeclared="x"` on a child includes it only where the item declares `x`, and
    `!x` inverts -- which is how the family's `cadence_daily` / `type_match` /
    `barrier_pick` gating would be expressed;
  * expansion CONSUMES `ifDeclared` and preserves every other attribute, so a
    child's own `cond=` (real data on `<Onlyif>`) survives untouched;
  * the expander that actually runs is `lib/llm/materialiseRubric.ts` via the
    `build:expand-rubrics` script -- not a second implementation.

AND IT HAS A DESIGN RATIONALE WORTH TEACHING, from `ItemTemplate.ts` itself: "A
frame varies WORDS; this varies WHAT THE SHEET ASKS." Measured on a twelve-item
handout built from four helper functions -- the pairs were 92-100% identical once
serialised, yet three of four differed in their SLOT KEYS. That is the distinction
between `Frame` and `ItemTemplate` that a guide has to make, and it comes with
evidence attached even though this course has none.

ONE DEFECT FOUND WHILE CHECKING, and it is the silent kind. `ItemTemplate.ts`'s own
header example writes `<Forbid key="excluded" cond="hasExtra"/>`. The authored
attribute is `ifDeclared`; `cond` is only the INTERNAL field name in
`itemTemplate.ts`, kept deliberately distinct because `cond` is real data on
`<Onlyif key="x" cond="y">`. An author following the block's own source would get a
child that is ALWAYS INCLUDED -- `ifDeclared` absent, so the internal `cond` is
undefined, and the selector returns true -- with no error anywhere.
`ItemTemplate.md` and `materialiseRubric.md` both have it right; only the
implementation's header is wrong. Fix it as part of this item: it is one line, and
it is the first thing a reader of the code meets.

PHASE 1 -- CRIB, IN A SCRATCH COPY, AND PROVE IT BY DIFF.
Work on a copy of `bmod_rubric.olx`, never the shipped one. Replace the eight
items with `<ItemTemplate name="oc_item">` plus eight `<Item use="@oc_item" ...>`
carrying their existing `conditions=` and `params=`. Then run
`build:expand-rubrics` and require:

    expand(templated copy)  ==  today's authored rubric,  BYTE FOR BYTE

The baseline for that comparison already exists and is already confirmed: today
`.stage/expanded/.../bmod_rubric.olx` is byte-identical to the authored file, 1,047
lines each. So the test is exact, mechanical, and needs no judgement about whether
the template "looks right". If the bytes differ, the template is wrong, and the
diff says where.

PROMOTE IT IF THE BYTES HOLD -- authorised by the user 2026-09-23: if the family
can be templated WITHOUT CHANGING ANY SHA, phase 1's output goes into the real
rubric rather than staying a scratch example.

AND THE CONDITION IS SATISFIABLE BY CONSTRUCTION, which is what makes this safe.
The scorer reads `expanded_path()`, never the authored file -- reading the authored
one "would mean implementing the template grammar a second time, which is the drift
`materialiseRubric` opens by refusing". So if `expand(templated) == today's
expanded` byte for byte, every reader downstream sees IDENTICAL BYTES, and
`course.json` and `prompt_sha` follow necessarily rather than by luck. The byte
diff is not evidence for the sha claim; it entails it.

ONE PREREQUISITE, AND IT IS ALREADY WRITTEN DOWN. `authored_path()`'s docstring
says: "WHEN TEMPLATES ARRIVE THIS NEEDS A BUILD STEP. The authored file is expanded
today only because nothing uses `<ItemTemplate>` yet. The artifact this function
should return is EXPANDED BUT UNRESOLVED -- which is neither the authored file nor
`.stage/content`, and does not exist yet." IT EXISTS NOW: `.stage/expanded`, built
2026-09-22/23 as `build:expand-rubrics`, is exactly expanded-but-unresolved.

So the moment the family is templated, `authored_path()` must point at it, or the
GENERATOR -- `olx_prompts`, which needs `{{corpus:...}}` intact and therefore cannot
read `.stage/content` -- would read unexpanded templates. That switch is part of the
promotion, not a follow-up: templating without it means the generator writes
`<Item use="@...">` into the shipped handouts.

#### How many templates, and what each one carries

TWO -- one per group. The shapes WITHIN a group are conditional children, not extra
templates, and that distinction matters because "three shapes" reads like "three
templates" and is not: a shape that differs by a declared condition is precisely
what ONE template with `ifDeclared` exists to express.

    type group     1 template   body = the plain PP/NP shape;
                                PR's extras gated `ifDeclared="move_pick"`,
                                NR's gated `ifDeclared="barrier_pick"`
    cadence group  1 template   body = the 30 children common to all four;
                                the rest gated on the conditions they declare

IS THE FAMILY TEMPLATABLE AT ALL? Measured, because slot-key overlap is not the
question -- slots are only part of an item, and if the `Credit`, `Deduction`,
`Guidance` and `Question` bodies all differ a template factors little. Counting
children that are VERBATIM IDENTICAL across every member of a group:

    type     PR NR PP NP          92 of 131 children shared (70%)   23 distinct
    cadence  DAY1 WK1 DAY2 WK2   120 of 206 children shared (58%)   30 distinct

212 of 337 children -- 63% -- are exact duplicates today. The shared set is not
just slots: `type` shares 8 Slots, 9 Guidance, 3 Deduction, 2 Context, 1 Credit;
`cadence` shares 10 Slots, 10 Guidance, 5 Deduction, 2 Credit, 2 Context, 1 Equals.
The duplication is real and the family is worth templating.

THE TYPE GROUP HAS THREE SHAPES, AND THE ITEMS ALREADY DECLARE THEM:

    plain        PP, NP    30 children each   no conditions
    move-pick    PR        32                 one extra pick slot, and an
                                              `Expect` keyed on `stimulus_move`
    barrier      NR        39                 five extra slots, a `Forbid` with a
                                              three-way `conds=`, an `Onlyif`, and
                                              three extra `Guidance` blocks

PR carries `conditions="move_pick"`, NR carries `conditions="barrier_pick"`, PP and
NP carry none -- exactly the selectors `ifDeclared` consumes. THE RUBRIC WAS ALREADY
WRITTEN AS IF THE TEMPLATE EXISTED, so one template covers all four and neither PR
nor NR needs handling of its own.

THE CADENCE GROUP WORKS THE SAME WAY:

    DAY1  53 children   cadence_daily|avoidance_scores|barrier_pick|cadence_barrier|
                        contingency_gate|polarity_gate|type_match
    WK1   46            cadence_weekly|type_match
    DAY2  53            cadence_daily + the barrier/contingency/polarity set
    WK2   54            cadence_weekly + the same set

WK1 is this group's outlier -- two conditions where the others carry six or seven.
The children unique to a SINGLE item are few (4, 5, 4, 3), so nearly all variation
is children shared by SOME, which is the `ifDeclared` case again. What remains is
pure `{param}`: `Question` varies only as daily/weekly x first/second, and
`cadence_is_daily` vs `cadence_is_daily_counted` is a KEY difference, which
substitution reaches because it works inside attribute values.

LEFT OPEN DELIBERATELY: only 30 of ~52 children are common to all four cadence
items (58%), so that template is a smallish body carrying many conditional extras.
Splitting `DAY2 + WK2` into their own template may be tighter -- they are the
closest pair in the family. Decide while writing, where the diff shows the cost.

#### The pairwise evidence, and two things in it that cut against the naming

Jaccard over verbatim children:

              PR    NR    PP    NP  DAY1   WK1  DAY2   WK2
    PR         -  0.54  0.59  0.59  0.27  0.32  0.29  0.28
    NR      0.54     -  0.50  0.50  0.35  0.29  0.37  0.37
    PP      0.59  0.50     -  0.71  0.28  0.33  0.30  0.29
    NP      0.59  0.50  0.71     -  0.28  0.33  0.30  0.29
    DAY1    0.27  0.35  0.28  0.28     -  0.57  0.68  0.62
    WK1     0.32  0.29  0.33  0.33  0.57     -  0.46  0.56
    DAY2    0.29  0.37  0.30  0.30  0.68  0.46     -  0.75
    WK2     0.28  0.37  0.29  0.29  0.62  0.56  0.75     -

The block structure confirms the two-group split: within either group 0.46-0.75,
across them 0.27-0.37.

THE ORDINAL CLUSTERS HARDER THAN THE PERIOD. `DAY2 + WK2` (both "second") share
0.75, while `DAY1 + DAY2` (both "daily") share 0.68 and `WK1 + WK2` only 0.56. So
the obvious `{cadence}` parameter is NOT the main axis of variation -- first/second
is. A template built on the naming would factor the weaker split.

PR SITS CLOSER TO PP/NP (0.59) THAN TO NR (0.54), which looks wrong until the three
shapes above explain it: PR is the plain shape plus one pick, NR is the plain shape
plus a subsystem. NR is the outlier because it carries the most machinery, not
because it is a different kind of item.

AND THE JACCARD FIGURES UNDERSTATE THE FIT -- they must not be read as a ceiling.
They count a conditional child as a DIFFERENCE between two items when it is declared
variation one template expresses once. 0.54 between PR and NR does not mean "these
barely match"; it means "these differ by exactly the children their own
`conditions=` already name".

EVEN A TWO-ITEM TEMPLATE IS WORTH WRITING. 46 shared children between DAY2 and WK2
is 46 lines that stop being edited twice. There is no threshold below which a
template does not pay; the only question is whether the shared part is real.

#### Two cautions, and two defects found while measuring

DO NOT ESTIMATE THE `{param}` GAIN IN ADVANCE. A probe that substituted the type
names and cadence words before comparing reported sharing going DOWN -- 70% to 58%,
58% to 40% -- which is impossible, since merging children cannot split them. The
probe used a DIFFERENT substitution table per item, so `pts="1"` became `pts="{N}"`
in DAY1 and stayed `pts="1"` in DAY2, splitting children that had been identical.
The verbatim 70%/58% is a FLOOR; the true figure comes out of writing the template.
Same class of error as G2's prose scan and G(a)'s `NAME_MARKERS` over-fire: a crude
pattern over content that looks regular and is not.

`ItemTemplate` COMPOSITION IS UNTESTED. If the cadence template later wants a core
plus specialisations, establish first whether templates can reference each other at
all -- nothing in this corpus has ever tried it.

DEFECT 1, and it is the silent kind: `ItemTemplate.ts`'s own header example writes
`<Forbid key="excluded" cond="hasExtra"/>`. The authored attribute is `ifDeclared`;
`cond` is only the INTERNAL field name in `itemTemplate.ts`, kept deliberately
distinct because `cond` is real data on `<Onlyif key="x" cond="y">`. An author
following the block's own source gets a child that is ALWAYS INCLUDED -- `ifDeclared`
absent, internal `cond` undefined, selector returns true -- with no error anywhere.
`ItemTemplate.md` and `materialiseRubric.md` are both right; only the
implementation's header is wrong. One line, and it is the first thing a reader of
the code meets.

DEFECT 2: PR reads `conditions="move_pick|move_pick"`, the only duplicated condition
in the rubric. Inert -- both readers parse conditions into a set -- but wrong, and
misleading to anything that ever counts them.

WHAT A CLOSER LOOK CHANGED, and it makes the promotion dearer than the byte-diff
made it appear. Three things, all found by reading the expander and the checks
rather than the docs:

  1. THE BYTE-IDENTICAL PROOF DOES NOT SURVIVE `serialise()`. `materialiseRubrics`
     emits an UNTOUCHED element as its own source bytes -- so unexpanded items
     reproduce exactly -- but an EXPANDED one is re-serialised canonically:
     attributes in parse order, two-space indents, self-closing when empty, text
     re-escaped. Hand-authored formatting will not round-trip through that by
     accident. So the gate cannot be "the expanded file is byte-identical". It has
     to be THE PARSED RUBRIC IS IDENTICAL and `prompt_sha` IS UNCHANGED -- which is
     the proof F2 used, and it worked. Byte-identity is a bonus if it happens, not
     the test.

  2. `check_the_expanded_rubric_is_current` COMPARES BYTES AND EXPIRES ON THE DAY A
     TEMPLATE LANDS -- its own words. It REFUSES rather than quietly becoming
     wrong, and says why: "Upgrading it means running the expander and comparing
     its output, which is a node call from python -- deliberately not built today,
     because a check nothing exercises is a check nobody finds out is broken. The
     refusal below is what makes the upgrade unavoidable instead of merely noted."
     So the first template in this repository REQUIRES building that python->node
     call. That is not a side quest; the audit will not pass without it.

  3. `check_the_staged_rubric_is_current` COMPARES AGAINST THE AUTHORED FILE. Once
     items carry `use=`, the authored side parses without the slots the staged
     side has, so it fires on every templated item forever. The fix has an exact
     precedent INSIDE THE CHECK: it already RESOLVES the authored side before
     comparing, because the staged copy has its corpus references expanded. It must
     now EXPAND it as well, for the same reason and in the same place.

TOGETHER WITH `authored_path()`, THAT IS FOUR PREREQUISITES, not one, and three of
them were invisible until the code was read. The honest cost of promotion is: the
template itself, a python->node expander call, two check upgrades, and the
`authored_path` switch. Still worth doing -- eight items sharing seven slots is real
duplication, and every one of these four is owed anyway the first time ANY template
lands -- but it should be planned as a piece of build work with a documentation
example falling out of it, not as a documentation task that happens to touch a
rubric.

AND THE SEQUENCING FOLLOWS: build the four first, against the CURRENT untemplated
rubric where every check still passes and the expander is a no-op. Then the template
is the only variable when it lands. Doing it the other way round means diagnosing a
new template and three newly-expired checks at the same time.

PHASE 2 -- GENERALISE, then let the suite hold it.
With a template proven to reproduce real items exactly, rewrite it with invented
content for the guide: same STRUCTURE, none of this course's slots, behaviours or
wording. The structure is what was validated; the words were never the point, and
leaving them in would put course content in engine documentation -- which is the
thing item G2 exists to remove.

The generic version then goes in as an `olx:playground` fence, and
`docPlaygrounds.test.ts` renders it on every run. That is the only guard these
particular examples get: every other combination in this guide can be checked
against real content, and `ItemTemplate`'s cannot, because there is none. So the
playground IS the test, and a template example that is not a rendering playground
is an unverified claim.

PHASE 3 -- the same two phases for `Cover`, `Requires` and `Derived`, which have
one, two and three real instances respectively. They are thin rather than absent,
so the crib is smaller but the method is identical: reproduce a real item exactly,
then strip it to structure.

#### What the guide has to do, per combination

For each shape: what the combination DOES, and WHEN TO PREFER IT over the
alternatives that could express the same judgement. The second half is the part
reference documentation never carries and the part an author actually needs --
`Equals` vs `Expect`, `Onlyif` vs `Forbid`, `Counts` vs enumerated slots,
`Cover` vs independent slots. Each of those pairs is a real decision someone made
26 times in this rubric, and the reasoning is currently nowhere.

Start from the base configuration -- a slot sheet of independent checks, nothing
else -- and add one primitive at a time, so the guide reads as a progression
rather than a catalogue.

#### Playgrounds are the cost, and they are also the guarantee

24 playground fences exist across the whole rubric family today. This item needs
many more -- plausibly one per combination, which is 17 shapes plus the four
invented cases, before counting the progression's intermediate steps.

THEY ARE NOT FREE AND THEY ARE NOT DECORATIVE: `docPlaygrounds.test.ts` RENDERS
every one, so each new example is a test that must pass. That suite was
strengthened earlier this session precisely because three playgrounds were found
that the engine rejects while the assertion let them through. So a large example
set is a large test set -- which is the argument FOR doing it this way, since a
guide whose examples are executed cannot rot into describing an engine that no
longer exists.

### J · `scoring/` should become its own repository

Filed 2026-09-23 on the user's instruction, and it is the logical end of this
section's own argument: if `edu.memphis.psych` IS the psychology course repository,
then course material belongs in it and the analytic machinery -- which knows nothing
about psychology and is meant to serve any course -- does not.

IT IS A CLAIM BEFORE IT IS A PLAN, and the difference matters. "Move `scoring/` to
its own repository" presumes exactly what has to be established first: that what
moves is GENERIC BY CONSTRUCTION, by the test in item H. Some of it plainly is --
`editguard` guards edits to any package, `course_inventory` counts whatever ids the
data supplies. Some plainly is not -- anything whose logic is shaped around three
handouts and twenty participants. Most of it has never been asked.

SO THE PRECONDITION IS AN AUDIT, module by module, reading control flow rather than
scanning for ids: does this module take the course's shape as input, or does it
assume it? Everything that assumes it goes to `$COURSE_LOCATION` with the fixture;
everything that takes it as input can leave. Until that audit exists there is no
list of what would move, and a repository split without such a list would carry the
course-specific parts along with it and call them generic by relocation.

WHAT THE AUDIT WILL PROBABLY FIND, stated as an expectation to be tested rather than
a conclusion: the machinery was written against this course too. The rubric reader,
the sweep tooling and the enforcement checks were all shaped by one corpus, and the
migration has been moving course DATA out of them for weeks precisely because it was
in them. That work is what makes J reachable at all, and its remaining items -- A's
successors, C, F's residue -- are the same audit under another name.

ORDERING: after H and I. H puts every file in the home its category implies, and I
makes the engine documentation good enough to author from; both are prerequisites
for handing the machinery to someone who does not have this course.

---

# Appendix · THE DRY RUN AS EXECUTED, and the traps it walked into

Carried over verbatim from `~/code/migration_dryrun/psych/RUBRIC_MIGRATION_PLAN.md`
before that directory was deleted. It is here because it existed **only there**:
the two copies of this plan diverged after the 2026-09-13 fork, live gaining the
§11.5–11.12 decisions and the sandbox gaining these records and traps.

**Trap numbering:** the sandbox and live each grew a T12 and a T13 about
different things. The sandbox's two are renumbered **T27** and **T28** here;
live's originals keep their numbers. Everything else keeps the number it was
recorded under, because the QC guide and the scripts cite them.

#### 06c AS EXECUTED — 2026-09-15/16

| gate item | state |
|---|---|
| `fingerprint_text` builds for all 26 | 26/26 |
| no-rubric-constants guard | 0 |
| `check_paper_prompt_is_stamped` | 0 |
| every rubric-reading check demonstrably firing | **28/28 against the full audit** |
| selftest | 86/86 before the new cases, raised to 114 |
| corpus replay identical | NOT RE-RUN since the delete |
| every affected column re-recorded (O3) | NOT VERIFIED |
| `paper_opus` inherits 06 | NOT VERIFIED |

**WHAT THE DELETE COST: NOTHING, and it took two wrong passes to see that.** The
audit read 28 against §0's 32, and the gap looked like four findings going down
with the modules. `migration/goldens/audit_baseline.json`, frozen at 11:13 that
morning, already recorded 28 WITH THE FULL SET: earlier stages had removed those
four legitimately. 06c ADDED four -- three `DEFINITION VANISHED`, one unapproved
guide lesson -- and fixing them left a set IDENTICAL to the frozen baseline.
See T12 and T13, both of which were first written the wrong way round.

**What 06c did cost was a blind check, and no count would ever have shown it.**
`check_maps_tables_are_attached` became a tautology: 06c made `MAPS` a
derivation of the per-item field, so "declared but not attached" stopped being
representable and the check could only pass. A check that cannot fail moves no
number -- its findings were already zero. Its SELFTEST CASE said so, reporting
`NOTHING FIRED`, which is the whole argument for the gate's wording. It is
retired with its declaration in place and replaced by
`check_every_rubric_element_is_consumed`, which guards the same class one layer
up: an element authored in the rubric that `read_rubric` never matches.

Twenty-eight rubric-reading checks had no case at all. Each now has one, every
one shown to fire against the FULL audit, and all 28 are installed in the suite
with `SELFTEST_EXPECTED` counting them.

**Scripts:** `stage06c_validate_injections.py` (the 28 against the full audit),
`stage06c_c1_probe.py` (a recorded negative result -- see its header),
`stage06c_dump_findings.py` (writes the finding SET, which T13 says to keep).
`scoring/selftest_injections.py` holds the injections themselves.

**07 · Rebase the prose, and the dispositions that needed no live source** — *no behaviour change*
The dispositions for checks reading a **deleted** source were applied in 6b (O2); what remains here
is the rest of stage 01's list plus the prose. Add the EQUIVALENCE.md limit section (§8). Update
`QUALITY_CONTROL.md` and `GOALS.md` where they name moved structures, and the **baseline-numbers
table in §0** if this migration changed what the audit reports.
**Gate:** selftest accounts for **exactly** `SELFTEST_EXPECTED` breakages, the constant raised
deliberately if cases were added · every retirement
carries a declaration · all four `.md` hook-ins still parse.

#### 07 AS EXECUTED — 2026-09-16

| gate item | state |
|---|---|
| every retirement carries a declaration | 3 of 3 — the MAPS check (in place + `editguard.accept`), `RUBRIC_SOURCE` (`handouts.py:30`), the maps-detach selftest case |
| all four `.md` hook-ins still parse | `goals.check()` 0; closure-ceilings, guide-structure, guide-lessons, divergence-arithmetic, prose-numbers all 0 |
| selftest accounts for exactly `SELFTEST_EXPECTED` | re-running after the prose edits; the pre-edit run was 114/114, 0 failed |

**The prose rebase.** `EQUIVALENCE.md` 3 → 1 (the survivor names the old module
as history AND the new home); `BACKLOG.md` 4 → 0 (`file:line` citations
re-pointed at structures); `GOALS.md` 36 → 26, all historical, under a header
note that says so. See T17: the log keeps its own tense.

**The limit section** (`EQUIVALENCE.md`, forward-referenced from §2 and never
written) says what the migration made MORE true: before 06, the rubric and the
sheet were authored separately, so a divergence could occasionally expose a
rubric error. One source removes that accidental guard by design. Agreement
between the engines now carries exactly zero information about whether the
rubric is right, and the section names what does carry it -- gold, the fixture
readout, the per-cell error profile.

**Scripts:** `stage07_prose_mentions.py` (mentions split by tense),
`stage07_gate.py` (the three conditions, with the selftest row READ from the
suite's own log rather than re-derived).

**08 · Acceptance — by default, ZERO calls**
Because the bytes never changed, there is nothing for a sweep to discover: it would re-sample the
same distribution and return its own noise. Acceptance is the four zero-call instruments of §7a,
and a live sweep is a *contingency* priced per item that fails byte-equality, not a scheduled cost.
**Gate:** every §7a instrument green · any item that failed byte-equality swept and declared ·
**every artifact that swept item supersedes retired** (O4), since the all-artifact checks cannot be
cleared by sweeping at any price.

---

#### 08 AS EXECUTED — 2026-09-16

| instrument | result |
|---|---|
| prompt oracles (web + paper bytes) | UNCHANGED across 26 items, both sides; leak gate clean |
| `idmap` served-prompt | 23/23 current against `idmap_v145.json` |
| corpus replay | 5668 recorded responses, 0 scored differently; controls olx 2705/2706, python 2908/2908; 2640 paper cells, 0 differing |
| enforcement neutrality | 28 findings, SET-identical to the frozen baseline |
| items failing byte-equality | none — the sweep contingency never triggered |
| O4 sweep-then-retire | vacuous, no sweep spent |
| **e2e session (scorer)** | **26/26 items scored, 0 without a usable cell** |
| **student session (browser)** | **4/4: course page + three handouts, 55 screens, 0 DisplayErrors** |

**Acceptance cost: ZERO calls for the four byte instruments**, against ~9,400 for
the sweep the first draft scheduled as a matter of course. The two session rows
are not free — a few dozen calls between them — and they are the only rows that
RUN the release rather than compare it. See T21: all four byte instruments pass
unchanged on a build whose handouts do not render, because a page that renders
nothing has the same bytes as one that renders.

| the student session, certified 2026-09-16 | screens | inputs answered | feedback presses | not required |
|---|---|---|---|---|
| handout 1 | 11 | 25 | 10 | 1 — submit/PDF |
| handout 2 | 37 | 32 | 33 | 1 — submit/PDF |
| handout 3 |  7 | 12 |  7 | 2 — `Print this page`, submit/PDF |

Zero required-but-silent buttons. Handout 3 screen 2 carries a printer AND a
grader: `Check my labelling` was required and answered, `Print this page` was
excused because it CALLED `window.print`, which the harness observes by stubbing
it rather than inferring from markup. Frozen at
`migration/goldens/student_session_certified.json`.

**The idmap dump PREDATES the migration**, and that is what makes the claim
non-circular: `idmap_v145.json` is from 2026-09-12, four days before this stage,
and every one of the 23 generated prompts still matches it line for line with
nothing extra. Checking against a dump taken afterwards would have proved only
that the tree agrees with itself.

**Scripts:** `stage08_acceptance.py` (six rows now — the four byte instruments
plus the two sessions, each session READ from the artefact its own script left
behind and reported NOT RUN when absent, because absence is not a pass);
`e2e_session.sh` (scorer side, all 26 items); `student_session.sh` +
`student_session.spec.ts` (browser side). The replay row is read from an audit
LOG rather than re-derived -- the same rule as
`stage06b_gate.py` and `stage07_gate.py`. See T20 for why it chdirs first.

### K · How much of the enforcement machinery can be a lo-blocks test suite?

Filed 2026-09-23 on the user's instruction, AFTER H, I and J. The question is
not "can we port 188 checks" -- it is how many of them are asking something the
ENGINE could answer natively, and would answer for every course rather than this
one.

WHY IT IS NOW WORTH ASKING, and it was not before tonight. The subject of most
of these checks has moved. The rubric is an authored OLX component; the prompt
fragments, the criteria frame, the carried commentary, the slot sheets and all
but one of the authored tables are in it. A check over `bmod_rubric.olx` is a
check over CONTENT, and lo-blocks already validates content.

THE EVIDENCE THAT THIS IS REAL rather than speculative arrived during the move
that prompted it. Adding `requiredMove=` to four items was accepted by every
python reader -- `coursedata`, `derived`, the rubric view, the audit at 44 -- and
REFUSED by the engine:

    ❌ ATTRIBUTE_VALIDATION: Invalid attributes for <Item ...>:
       - : Unrecognized key(s) in object: 'requiredMove'

The engine's own Zod schema caught an attribute the rubric had no business
carrying until it was declared. Nothing in `scoring/` noticed, because nothing in
`scoring/` knows what an `<Item>` may hold -- the engine does, and it is the only
side that does.

WHAT TO SORT INTO, and the sorting is the goal rather than the porting:
  * SCHEMA -- what an element may carry, which values are legal, what a
    reference must resolve to. The engine already does this and does it for any
    course; every check in `scoring/` doing it by hand is a second opinion.
  * STRUCTURE -- a slot with no menu, a gate with no text, a code nothing can
    charge, a declaration whose key no longer exists. Answerable from the rubric
    alone, so answerable in a .ts test suite over the component.
  * MEASUREMENT -- everything comparing runs, rates, medians, gold and the two
    scorers. NOT portable, and not a candidate: it is about this corpus's
    numbers, needs the run ledger, and stays in python.

THE PRIZE, stated so it can be checked later: a structural check written in
lo-blocks runs on `npm run build`, fails the build rather than an audit nobody
ran, and applies to the next course for free. A structural check written here
runs when someone runs it and knows only about this one.

THE OBLIGATION IS THE SAME ONE USED ALL NIGHT: a ported check must FIRE on the
case its python original fires on, proved by the same fire test, before the
original retires. A check that moves and stops catching anything is worse than
the check that stayed.

### T27 · Compare the finding SET, and against the RIGHT baseline

06c deleted the rubric modules and the audit read 28 where §0 recorded 32. Four
findings looked as though they had vanished with the modules, and two
measurement passes went into naming them.

**They had not.** `migration/goldens/audit_baseline.json` — frozen at 11:13 on
2026-09-15, before the delete — already recorded 28, with the full set. The four
had been removed by EARLIER stages doing their job. What 06c actually did was
ADD four (three `DEFINITION VANISHED`, one unapproved guide lesson); fixing
those returned the tree to a set IDENTICAL to the frozen 28.

*Mitigation.* Two rules, and the second is the one that cost the time.

1. Compare the SET, never the count — a step that deletes a source can add and
   remove at once, which is when a count says least.
2. Compare against the LAST FROZEN baseline, not against §0. §0 is the number at
   stage 00; every stage since has legitimately moved it. A drift measured
   against the wrong reference produces a real-looking gap and a search for a
   cause that does not exist.

### T28 · Look for the artifact the migration already makes

While hunting the four findings of T12 I concluded the baseline set was
unreconstructible — the dry run is off git, §0 records numbers rather than sets,
and the commit the sandbox was made from returns 869 findings, whole check
families apart. That conclusion was WRONG, and I recorded it here as a trap
before checking.

`stage00_freeze_oracles.py` writes `migration/goldens/`, and that directory
already held `audit_baseline.json` with the full finding set — created by this
migration, for exactly this question. Two passes of hand-rolled measurement went
into a question one `ls` would have answered.

*Mitigation.* Before building an instrument, look in `migration/goldens/` and at
the stage-00 scripts for one that already exists. This is the same standing rule
as preferring a prepared accessor to a hand-rolled scan: the reason a hand-rolled
one is worse is not only that it is slower to write, but that it can be wrong in
a way the prepared one has already been made right.

### T14 · An injection that installs and proves nothing

Of the 28 written at 06c, THIRTEEN did not fire on the first attempt, and every
failure was silent -- installed cleanly, changed nothing, and would have entered
the suite as a case proving its check works. The causes were all small and all
specific: a bare verdict word where the check matches `` `backticks` ``; a
`chdir` that would have held for the whole audit; a string key where the table
uses ints; a participant outside the readout's range; both branches forced the
harmless way; a note no item scores, so the check skips it; `ITEM:slot` keys
parsed as dotted; writing a real file the movement guard watches.

*Mitigation.* Probe every injection before trusting it, and count only the ones
that FIRE. "Written" is not a number worth reporting. This is the same failure
as the check it guards: a case that cannot fail reads exactly like a case that
keeps passing.

### T15 · A single-check probe is weaker than the audit

One injection passed its own check and then killed the whole audit: it made
`agreement.load_action` raise for every caller, which is right for the check
that REPORTS a load failure and fatal for the other checks that load sheets.
`stage06b_validate_injections.py`'s docstring already records three of these
from 06b, each costing a ~90-minute suite run to find.

*Mitigation.* `stage06c_validate_injections.py` runs every injection against the
full audit in one pass and reports fired / missed / crashed / left-dirty. Run it
before the suite, never after.

### T16 · Two instruments, one blind spot, agreeing with each other

Not a rubric-migration trap, but it happened during 06c and the shape
generalises. A substitution matched file text with words joined by `\s+`; the
scan that VERIFIED the substitution used the same pattern. They agreed, and both
missed 137 sentences written across adjacent string literals, where the file
holds a quote, a newline, indentation and another quote between two words.

*Mitigation.* A verifier must not share the scrubber's matching rule. Where the
thing being checked is Python, read it the way Python does -- parse, and look at
the string constants the parser has already joined.

### T17 · A log rewritten to match today stops being a record

`GOALS.md` names `rubric_hN` thirty-six times. Ten are claims about where a
thing IS; twenty-six are entries describing where it WAS when they were written
-- "`unclear` was removed from rubric_h1's `verdicts`" is a true sentence about
2026-08 and a false one about the module list. Rewriting all thirty-six would
have made the file agree with the present and stop being a log.

*Mitigation.* Split by tense (`stage07_prose_mentions.py`), rebase only the
present-tense claims, and put ONE note at the head saying the older entries name
the layout of their time and why they were left. The same applies to `file:line`
citations into a deleted module: re-point them at the STRUCTURE, never at new
line numbers, which will be stale again the next time the file moves.

### T18 · An edit that reports success and changes nothing

The seam-aware matcher was built, the edit script printed its success line, and
the rebuild ran for fifteen minutes with the OLD matcher. The `old` string being
replaced had omitted a trailing `, re.I)`, so it matched nothing. The tell was
that the counts came back IDENTICAL -- a different matcher cannot produce the
same number of variants as the one it replaces.

It happened three times in one night in three forms: an edit that changed no
bytes, thirteen injections that installed and fired nothing, and a leak scan
that shared the scrubber's own blind spot. All three reported success.

*Mitigation.* Verify the EFFECT, never the report. Re-read the file and assert
the new text is present and the old text is gone; then check that the number the
change was supposed to move actually moved. An unchanged number after a change
is a failed change until proven otherwise.

### T19 · A gate item can stay open while every gate passes

§3.2 — compact tag versus byte-identical `.olx` — is a STAGE 00 gate item, and
the plan says so in bold, because "take early proved too weak: nothing stopped
the sequence beginning with them open". The sequence then ran from 00 to 08 with
it open. Every stage gate passed. Acceptance passed. Nothing failed, because at
each stage the byte-identical path was simply the one in front of us, and the
decision that should have chosen it was never made.

It surfaced only when the completion criteria were read for their own sake,
after the last stage gate was already met -- and the check that found it was
reading §11 for `DECIDED` markers, not running anything.

*Mitigation.* A decision is discharged when it is RECORDED, not when the work
that depended on it happens to be finished. Before declaring a plan complete,
re-read its decision list and confirm each carries a verdict; a gate item with
no marker is open however well the stages went. The default that got taken is
not the same as the decision that should have been made, even when it is the
same path -- because nobody priced the alternative, and the record cannot show
that anyone did.

### T20 · The audit is cwd-sensitive, and says so rather than lying

`check_engine_mechanisms_are_not_item_dependent` reads the engine sources by
RELATIVE path. Run the audit from anywhere but `scoring/` and it reports four
`cannot be parsed for item-gating` findings -- 28 becomes 32, and a neutrality
gate comparing against the frozen baseline FAILS on a tree that is perfectly
fine. The first version of `stage08_acceptance.py` did exactly that.

The check is behaving correctly and the wording is the reason it was diagnosable
in minutes: *"the check cannot run, which is not the same as passing"*. A check
that returned `[]` on a missing file would have passed the gate silently and
told nobody the engines were never examined.

*Mitigation.* Any script that calls `enforcement_audit()` chdirs to `scoring/`
first. And when a count differs from a frozen baseline, check the ENVIRONMENT
before the tree: the same four checks that read relative paths also read
`$COURSE_DATA` and `$LO_BLOCKS`, and `paths.py` refuses outright if those point
outside the sandbox.

### T21 · Every acceptance instrument compared bytes, and none of them ran it

Stage 08 finished with four instruments passing and the release unopened. Each
one compares bytes: the frozen prompt oracles, `fingerprint_text`, the served
`idmap` prompt, the corpus replay. All four can pass on a release whose handouts
do not render — because a handout that renders nothing has the same bytes as one
that renders.

The scorer-side session (`e2e_session.sh`) closed half of that: it drives all 26
items through `agreement_app.py`, so a rubric that stops producing a cell shows
up. It still never opens a page. It cannot see an input that will not take text,
a Next button that dead-ends, or a feedback button that answers nothing — which
is how a student actually meets a broken release, and none of which is a byte
difference.

**So a second session drives the UI** (`student_session.sh`): the course page,
then each handout, filling every input on every screen, pressing every feedback
button and waiting for a reply, taking Next to the last screen, and failing on
any DisplayError. Both report NOT RUN rather than PASS when their artefact is
missing.

### T22 · A non-standard port silently forbids the whole UI

The instruction was to run the acceptance server on a port other than the
standard one, and the port was taken as a free parameter. It is not.
`WS_PORT_MAP` in `packages/shared/lib/state/store.ts` maps page port to
event-server port and — deliberately, with a comment saying so — throws on any
port not listed. On 8899 the client never boots: every page is the string
"Failed to start. Check the console for details."

This did not surface for a long time because the first simulation was the
scorer-side one, which never loads a page. It passed 26 of 26 on a port where
the UI could not have rendered at all. **A green run on a port nothing renders
on is not evidence about rendering.** The port must be added to the map first;
Vite serves that module, so no server restart is needed.

### T22a · STATUS of the port edit: sandbox-only, deliberately not upstreamed

`packages/shared/lib/state/store.ts` in the **dry-run** lo-blocks carries one
added line:

    [8899, 0],    // dry-run acceptance server (stage 08), same origin

It is **not** in the live tree and is not proposed for it. The map's own comment
says the table "really belongs in config (e.g. PMSS) rather than hard-coded
here", and adding acceptance ports one at a time is the habit that comment warns
against. What the sandbox needs is a port; what lo-blocks needs is for the
routing table to come from configuration — a change with its own owner, its own
review, and no business being smuggled in under a migration dry run.

**So the entry is a known, recorded divergence between the sandbox and live**,
and anyone reproducing stage 08 on a non-standard port must add their port
there first or every page will read "Failed to start." (T22).

### T23 · Waiting for the DOM to go quiet catches the quiet BEFORE the content

The screen walker waited for "no DOM mutation for 700ms and no spinner". It
reported handouts 2 and 3 as zero blocks, zero buttons, one screen — and they
looked broken. They were merely slower to load than handout 1, and the wait was
satisfied by the still moment before their content arrived.

A quiescence test says "nothing is changing", which is equally true before the
work starts and after it finishes. Anchor on something the content must produce
— here `[class*="lo-tag-"]`, the per-block class the renderer always emits — and
only then wait for quiet.

### T24 · A reporter that buffers turns seven minutes of work into an empty file

The first UI run was `--reporter=line` piped through `grep`. Both buffer when
stdout is not a terminal, so after seven minutes of real browser work the output
file held zero bytes and there was nothing to diagnose. The wrapper now writes
the JSON reporter to a file, and the acceptance row reads that file rather than
scraped console text.

### T25 · Three times the SIMULATION was broken, not the thing simulated

Every failure the browser session reported on its first complete run was a
defect in the test, and each looked exactly like a product defect:

* **"`Check` never answered."** `Correctness` renders a SINGLE EMOJI — `?`
  before submitting, then a tick or a cross. Nothing grows; one glyph replaces
  another. A detector waiting for the feedback text to get longer can never see
  a CapaProblem answer, and it reported an instant, correct response as silence
  on every MCQ screen of handouts 1 and 2. The check now also accepts the
  correctness glyph changing to a SETTLED verdict, and explicitly refuses the
  hourglass and question mark so a *pending* grade cannot pass as an answer.
* **"`Submit here then save to PDF` never answered."** It prints. It is not a
  grader and has nothing to say back. Requiring a reply from it failed handout 1
  for behaving correctly. A reply is now required only on a screen that holds a
  grading block, and exempt presses are reported rather than dropped.
* **"The radio would not accept a click."** `ChoiceInput` hides the native
  control (`opacity: 0; width: 0; pointer-events: none`) behind a styled label.
  Playwright says "Element is outside of the viewport", and `force: true` does
  NOT help — force skips actionability checks, not layout. Click the label,
  which is what a student clicks anyway.

The pattern is worth more than the three fixes: **when a simulation reports that
a working product is broken, suspect the simulation first** — the same order of
suspicion as QUALITY_CONTROL.md §1. Here it cost two full runs,
and the same mistake in the history rewrite cost far more.

### T25a · CERTIFIED: what the browser session actually established

Run of 2026-09-16, one simulated student, 55 screens, zero DisplayErrors:

| handout | screens | inputs answered | feedback presses | not required |
|---|---|---|---|---|
| 1 | 11 | 25 | 10 | 1 — submit/PDF |
| 2 | 37 | 32 | 33 | 1 — submit/PDF |
| 3 |  7 | 12 |  7 | 2 — `Print this page`, submit/PDF |

**Zero required-but-silent buttons.** The exemptions are recorded with their
reason rather than dropped, and handout 3 screen 2 is the one that matters: it
carries the printer AND a grader. `Check my labelling` was required and
answered; `Print this page` was exempted because it CALLED `window.print`, which
the harness observes by stubbing it. A per-screen rule would have demanded
feedback from the printer and failed the handout for behaving correctly — the
defect was caught by review before it ever ran, not by the run.

### T26 · A browser global in a node test file

`CSS.escape` was used to quote a radio's `name`. Playwright test files run in
NODE, where `CSS` does not exist, so the first radio screen of every handout
died with `ReferenceError: CSS is not defined` — reported as a handout failure.
The ternary was meaningless anyway (`CSS.escape ? name : name`).

