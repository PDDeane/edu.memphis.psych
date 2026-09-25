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


#### B RE-READ AFTER C, 2026-09-24: three of its four steps are done

B and C were two answers to one question -- who produces the handout -- and C
answered it. What B still asks for is smaller than its own text suggests:

  1. THE GENERATED PROSE COMES FROM THE RUBRIC. Done, at BUILD time rather than
     run time: `build:assemble-prompts` reads the rubric and writes the bodies
     and the sheet attributes. B offered "or be accepted as authored and checked
     against the rubric instead of rewritten from it" as the alternative; the
     assembler does the stronger thing, since a difference is a failed build.
  2. `olx_prompts --write` STOPS WRITING. Done -- it refuses and names the npm
     script.
  4. course.json KEEPS item -> handout AND NOTHING MORE, with item -> OLX id on
     the rubric's `asks`. Done, and unchanged by the moves since.

  3. THE FRESHNESS STORY IS THE RESIDUE, and it is one check. `prompt_sha` hashes
     the SERVED tag, and `olx_prompts.py --check` still compares disk against
     what PYTHON's `render()` would write -- a second opinion from the producer
     that just retired. The audit already asks the better question for
     ATTRIBUTES ("is every attribute PRODUCED BY A GENERATOR from the rubric? An
     attribute nobody generates passes --check forever"). The same question for
     BODIES is now answerable by the assembler, which exits non-zero on any
     difference.

AND THE PAGE IS ALREADY AUTHORED. B's title asks for hand-authored handouts; the
only generated parts are 23 `<LLMAction>` bodies and 109 attribute values. The
layout, prose, figures and refs around them were never generated. So "authored
pages, assembled prompts" -- the end state C predicted -- is what the tree holds
today.

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

#### H(7) · `scoring/materials/` STAYS, against this item's own category table

Categories VII and VIII send "materials the rubric/course design was derived
from" to a named `$COURSE_DATA` subfolder. `paths.py` already carries a decision
that says otherwise, and it is the better-reasoned of the two:

    MATERIALS is deliberately NOT part of DATA: the blank handout templates are
    course teaching materials and ship with the code, because `segment.py`
    subtracts the template from a submission to isolate student text, and a
    scorer that cannot find its templates cannot score anything. Only the
    filled-in submissions are sensitive.

The templates are a SCORING DEPENDENCY, not merely a source document. Moving
them would make scoring fail wherever `$COURSE_DATA` is absent -- which is a
supported state everywhere else, by design, because gold and the logs may
legitimately be missing.

THE DIRECTORY COULD BE SPLIT -- the three handout templates are the dependency;
the three decks and the scoring dictionaries are pure source. It is 4.1 MB
either way, static, and splitting a directory on "which of these does segment.py
open" trades a clear rule for a subtle one. Left whole, recorded here, and
raised rather than done quietly: the category table and the code disagreed, and
the code had measured a reason.

#### REVIEW BEFORE K, and each entry is a thing deliberately left standing

Not defects to fix in passing -- decisions deferred because they reach scoring or
the user's judgement, and K rewrites the machinery that would have to encode
them. Settle these first or K will port them as they are.

1. THE `EXPECT` DUPLICATION. One rule states a fact the type vocabulary already
   states: the item whose sheet carries a `stimulus_move` slot expects that slot
   to equal the move its `expected_type` requires, and `score.py` performs that
   lookup anyway. The other three expect `observed_type` to equal the type, which
   is a different claim. Both are plain `<Expect>` elements in the rubric, so the
   distinction the old `EXPECT` table encoded has no expression there. Collapsing
   it changes what `equivalence.py:3100` selects, from one item to five.

2. THE AUTHORED `EXPECT` TABLE ITSELF, the last entry in `handouts.authored`. It
   is not the component's per-item `expect` -- the component carries five, the
   table names one -- and its only consumer is E44's selftest picking a subject.
   Deriving it would change that subject; deleting it needs (1) settled first.

3. THE 37 UNCLASSIFIED MODULES. Goal H's second question -- produces a FINDING or
   maintains the TREE -- is answered for the six tools and for category IX. The
   rest are unread, and K's sorting (schema / structure / measurement) needs the
   same reading to know what may leave python at all.


#### J · PREPARED WORK, 2026-09-24 (measured, not applied)

Folded in from the working notes so it lives with its goal.

Written 2026-09-24 while the post-split certification ran. Everything here is
DESIGNED, not applied. Items 4–6 execute the moment certification lands; J and L
wait on the user's say-so.

---

## 1. The EXPECT duplication — eliminate it by retiring a STALE PREMISE

**What the duplication actually is.** Two tables in `rubric_h2_source.py` —
`EXPECT` (line 1106, WK1's `targets_own_behavior`) and `_EXPECT_SHIPPED`
(line 1191, NP/NR/PP/PR's `demonstrates_type`) — together hold exactly the five
`<Expect>` elements in `psychology/bmod_rubric.olx`. They match perfectly: no
extra on either side, no drift. `expect` never reaches `course.json`.

**Why it exists.** It is a MIGRATION-VERIFICATION PAIR, not redundancy:

| | role |
|---|---|
| builder tables | the DECLARATION — what was authored |
| `.olx` `expect=` | the GENERATED artifact |
| `check_olx_attributes_are_all_generated` | every generated attribute traces to a declaration |
| selftest case `a rubric declaration is removed, its attribute is not` | picks an item with BOTH, drops both, asserts `GENERATED ATTRIBUTE HAS NO DECLARATION` fires |

**Why it can now go.** Goal C is complete — *python no longer produces the OLX*.
The OLX is hand-authored and IS the source. A check that every generated
attribute has a declaration is asking about a generation that no longer happens.
**The stale thing is the check's premise, not the data**, which is why deleting
the tables naively would look like vandalism and why nothing has removed them.

**The change, in order. Each step leaves the tree certifiable.**

1. Add `EXPECT` to `coursedata.DERIVATIONS`, reading `<Expect>` off the rubric
   component — the pattern already used for SLOT_SPEC, MAPS, FORBID, OC_GATES,
   the seven `*_ITEMS` tables, REQUIRED_MOVE and SLOT_OPTIONS.
2. Point the PAPER path at it: `score.py` reads `item["expect"]` (lines 308, 916)
   from items built by the component rather than by the builder.
3. Prove equality BEFORE deleting anything — assert the component-derived table
   equals the builder's two tables, all five entries, for one full certification.
   This is `migrated_tables.py`'s own discipline applied to itself.
4. Retire the two builder tables with `editguard.safe_write(..., dropping=[...])`.
5. **Re-point the selftest case, do not delete it.** With one source, "a
   declaration removed while its attribute stays" is no longer a reachable state.
   The case becomes: remove the rubric's `<Expect>` and assert BOTH engines stop
   seeing it — which tests the property that now matters, that the two sides read
   one source. Deleting the case would retire coverage rather than re-aim it.
6. Re-point `check_olx_attributes_are_all_generated` the same way, or declare it
   expired with the reason, as `enforcement.py:4281` did for its own repointing.

**Do not skip step 3.** The two tables agreeing today is what makes this safe;
that agreement is the thing to verify, not assume.

---

## 2. The handout-set revision — 67 sites, population reconciled

`handouts.HANDOUTS` is the declared set; `baseline.py` already reads it correctly
(`choices=sorted(HANDOUTS)`). Everywhere else the literal `(1, 2, 3)` is inline.

**FIX SET — 67**
- 59 × `for h|hh|handout in (1, 2, 3)` — enforcement (39), measured (5), probe (2),
  sweep_readout (3), olx_prompts (3), self_graded_misses (2), precommit_gate (2),
  rubric_export, score, leakage, handouts, equivalence
- 3 × a module-level `HANDOUTS = (1, 2, 3)` of its own — `rubric_export.py:44`,
  `rubric_equivalence.py:42`, `reader_equivalence.py:55`. None imports
  `handouts`, so this is the same fact declared independently four times
- 3 × `for hnd|_h in (1, 2, 3)` — enforcement 12454, 12465, 15557
- 2 × head_to_head (`for _h`, and `("ALL", (1, 2, 3))` in a label table)

**MUST NOT CHANGE — 7.** A blind replacement corrupts these:
- `probe.py:242,243`, `declaration_source.py:651,663` — `for n in (1, 2, 3)` is a
  SENTENCE index (`sentence_{n}`), not a handout
- `measured.py:4615` — `len(a) in (1, 2, 3)` is an argument count
- `rubric_equivalence.py:134`, `reader_equivalence.py:411` — prose in comments

67 + 7 = 74, the full population. Rule: the set comes from
`sorted(handouts.HANDOUTS)`; a literal handout tuple is a finding. Add a
`check_*` once converted, or it grows back. Needs its own certification cycle.

---

## 5. `tools/guide.py` — split the resolution, do not repoint it

NOW UNBLOCKED: zero lessons await approval, so the approval machinery can move.

`GUIDE` feeds two consumers with opposite requirements:

| consumer | needs | why |
|---|---|---|
| `check()` — lines 146, 250, 305 | the **composed** document | it validates what READERS see, and a §-citation or backticked identifier can live in either half |
| `unapproved_lessons()` — line 535 | the **generic** half | it diffs against `git show HEAD:./QUALITY_CONTROL.md`, and only the generic half is tracked there |

Repointing `GUIDE` wholesale — the one-line "fix" — would make the lesson check
compare the composed document against the HEAD-committed generic half and flag
every course-half lesson as newly added.

**Change:** give `check()` a `composed_path()` resolution and leave
`unapproved_lessons()` on `paths.SCORING`. At the same time add
`"QUALITY_CONTROL.md": "composed"` to `equivalence._SELFTEST_DOC_HOME`, so the
two QC injection cases land where `check()` now reads — the same lockstep the
GOALS.md fix established. Verify: the two QC selftest cases must still DETECT,
not MISS.

**Live gap this closes:** the course half already carries a `§2k` citation and
dozens of backticked identifiers that nothing validates.

---

## 6. `compose_docs.missing()` — it cannot see a lost course half

It checks only that the COMPOSED path exists, so "no course half because nothing
moved" and "course half lost in a checkout" are indistinguishable — the exact
failure its own docstring says it exists to prevent.

**Change, in the project's idiom (`migrated_tables.py`: DECLARED RATHER THAN
SNIFFED):** a split document with no course half must declare that fact, e.g.
`NO_COURSE_HALF = frozenset({...})`. `missing()` then reports a split doc whose
specific half is absent and undeclared. Today every one of the four has a course
half, so the declared set is EMPTY and the check is pure ratchet.

---

## J. `scoring/` becomes its own repository

**Blocker cleared today:** the 4.2 MB of course materials are copied to
`$COURSE_DATA/courses/edu.memphis.psych/materials/` and verified byte-identical;
`paths.MATERIALS` and the removal land when certification does.

**What the module audit established** (`scoring/MODULE_AUDIT.md`), 76 modules:

| category | modules | loc | course signal |
|---|---:|---:|---:|
| COURSE-CONTENT (`*_source.py` builders) | 5 | 3,547 | 53 |
| SEAM (paths, coursedata, handouts, rubric_*) | 6 | 3,742 | 2 |
| ONE-OFF / migration | 14 | 3,341 | 4 |
| ENGINE | 51 | 53,268 | 74 |

**Order of work:**
1. Finish the materials move; re-certify.
2. Resolve the five builder modules — they are course content by nature. Either
   they move to `$COURSE_METADATA` with the rest of the authoring artifacts, or
   they retire once the rubric is the sole source (item 1 is the first instance
   of exactly that question, and its answer sets the pattern).
3. Convert the 67 handout-set sites (item 2), so the engine stops assuming three
   handouts.
4. Triage the 14 one-offs — two are already self-documenting tombstones
   (`rubric_equivalence`, `reader_equivalence`) and must keep their pointer to
   `STAGE5_LICENCE.md`.
5. Then split the repository: `scoring/` + `scoring/tools/` move; `psychology/`,
   `course_metadata/` and `$COURSE_DATA` stay with the course.
6. `paths.py` is the whole seam. After the split its roots are found by env var
   with no in-repo defaults, because the engine no longer knows where a course is.

**Precondition not yet met:** the 74 course-signal units still in ENGINE modules,
43 of them in five files (measured, enforcement, olx_prompts, equivalence, score).
Most is docstring prose, which the ratchet counts and a reader would forgive —
but J should not ship with the engine's own documentation naming this course's
items. Measure with `tools/course_inventory.py` and drive it to zero.

---

## L. `$COURSE_DATA` on shared storage, with write locking

**Goal:** `$COURSE_DATA` cannot live in a repository but must be reachable by
everyone working on the project. Target is the existing Drive folder holding the
raw materials.

**Access.** `rclone mount` with a service account is the only option that makes
`$COURSE_DATA` a real POSIX path, which every reader here assumes (`paths.py`
hands out `Path` objects and modules `open()` them). Google Drive for Desktop is
per-user and interactive, so it fails in cron and headless runs — the same class
of failure as the MCP caveat on workflow agents. The Drive API without a mount
would mean rewriting every reader, which is out of proportion.

**The locking requirement, which is the substance.** Drive has no POSIX advisory
locks and `rclone mount` does not provide `flock` semantics, so locking must be
implemented in the project, not borrowed from the filesystem.

Design — a lock DIRECTORY, not a lock file:

* `mkdir` is atomic on the underlying store in a way `O_EXCL` on a file is not
  once a network filesystem is between you and it. The winner is whoever's
  `mkdir` succeeds.
* the directory holds `holder.json`: user, host, pid, ISO timestamp, and the
  operation being performed, so a blocked writer can SAY who it is waiting for
  rather than just hanging.
* **block until clear**, as asked, with a ceiling: poll with backoff, and after a
  declared timeout FAIL LOUDLY naming the holder. A wait that never ends is
  indistinguishable from a hang, which is the `wait_loop_self_match` lesson.
* **stale-lock policy must be declared, not inferred.** A holder that died leaves
  the directory behind. Do not auto-break on age alone — print the holder and
  require `--break-lock`, because silently stealing a lock from a live slow
  writer is worse than waiting.
* scope: one lock per WRITE TARGET (`out/`, `courses/<ns>/`), not one global
  lock, so a sweep writing `out/` does not block a document rebuild.

**Durability is part of L, not a separate task (added 2026-09-25, subgoal E59).**
This section plans ACCESS and LOCKING and says nothing about what happens when
data is LOST rather than contended, and the move changes that risk in both
directions.

What is actually at stake, measured rather than asserted:

    $COURSE_DATA/courses/<ns>/GOALS.md   1.2 MB   the goal ledger's BODIES
    $COURSE_DATA/courses/<ns>/gold.json  152 KB   the grading targets
    $COURSE_DATA/courses/<ns>/BACKLOG.md 112 KB
    $COURSE_DATA/out/**                           every sweep artifact

and none of it is in a repository, deliberately: it is course-specific data and
cannot go on a public one. The user's framing settles the shape of the answer --
*"we're talking data here, not code"* -- so this wants snapshots, an append
journal or versioned object storage, NOT commit semantics.

**THE INDEX IS ALREADY SAFE AND THE BODIES ARE NOT.** `GOAL_STATES.json` is 11 KB,
in the repo and tracked, and holds `{label: (state, title)}` for all 112 entries
-- which is what `check_goals_record_is_intact` compares against. Losing the
ledger would not lose which goals exist, their state, or their titles. It would
lose the measurements, the reasoning and the closure notes. That is most of the
value and it is a narrower claim than "the record is unprotected".

**THREE THINGS TO SETTLE BEFORE THE MOVE, and the first is a measurement:**

* **Does an `rclone mount` write produce a Drive REVISION?** Drive keeps version
  history for files edited through its own clients; whether a POSIX write
  through a mount creates one -- for every file type, and for how long -- is a
  question with an answer, and the plan should carry the measured answer rather
  than the hope. If it does, recoverability largely comes free with the move
  and this section is short. If it does not, the move makes things WORSE: one
  copy becomes one copy that more people can delete.
* **Shared storage multiplies writers, which is the other half of the locking
  problem.** The lock stops two writers corrupting a file; it does nothing about
  one writer deleting it. A retention or trash policy has to be named.
* **`out/**` is regenerable and the course records are not.** They are pooled
  here under one `$COURSE_DATA` and want different policies: a lost sweep costs
  calls, a lost ledger costs the reasoning behind every decision this project
  has made. Whatever is chosen should distinguish them.


**Where it goes.** A single `paths.locked_write(target)` context manager, since
`paths.py` is already the one module that owns filesystem locations and
`check_filesystem_locations_come_from_paths_py` enforces that. Every writer to
`$COURSE_DATA` acquires through it; a writer that does not is a finding.

**Verify before trusting:** two processes racing the same target, one must block
and then proceed; a killed holder must leave a lock that is REPORTED, not
silently broken; and a reader must never block, because reads outnumber writes
hugely and blocking them would make the mount unusable.

---

## J precondition, measured: 78 course-signal units in 26 ENGINE modules

`tools/course_inventory.py`, 2026-09-24. By kind: vocabulary 39, literal_ids 22,
tables 11, named 6.

### The 22 literal_ids are TWO patterns, not twenty-two problems

**(a) `item == "1c"` — ten sites, four modules.** The single biggest cluster:
`measured.py` ×7 (1741, 2184, 3003, 3196, 3815, 3885, 6449), `compare_runs.py:128`,
`enforcement.py:13225`, `olx_prompts.py:1868`. Two of them pass
`rebuild_1c=(item == "1c")` into `_corrected_gold`, so the item id has reached a
PARAMETER NAME.

This is the graph item, and **the rubric already declares the property**:
`handouts.py:846` refers to `derived="has_own_graph:complete:..."` in the OLX. So
the fix is a property test — *does this item declare a derived graph?* — read
from the rubric component, exactly as `coursedata.DERIVATIONS` does for the other
tables. Ten sites collapse to one predicate, and the engine stops knowing that
this course's graph item is called `1c`.

**(b) selftest and test-fixture item picks — eleven sites.**
`equivalence.py` ×7 inside `enforcement_selftest`, `reader_equivalence.py` ×4 in
`_mutations`, `q6_consensus.py` ×1. The suite ALREADY HAS the right mechanism:
`_pick(label, candidates, why)` chooses a target dynamically and records why —
it is used for the GOALS case and the `cover`-group case. These eleven hardcode
what `_pick` exists to select. Converting them is mechanical and removes the
"first h1 item with a keyed cover group" class of hidden assumption.

### The 11 tables

| module | table | lines | note |
|---|---|---:|---|
| `goals.py` | `CLOSURES_APPROVED` | 234 | an ACCUMULATING record of approved closures — belongs in `$COURSE_DATA` with GOALS.md, by the rule that already moved the ledger |
| `precommit_gate.py` | `NOT_STUDENT_TEXT` | 153 | only ONE item id in 153 lines; check whether it is course data at all before moving it |
| `enforcement.py` | `PROBE_PROVOCATIONS` | 113 | course data |
| `enforcement.py` | `_PASS` / `_FAIL` | 31 / 33 | the oc_analysis probe tables, keyed by type |
| `probe.py` | `ANSWERED_UNDER` | 18 | course data |
| `gold.py` | `H1/H2/H3_HEADER_TO_ITEM` | 28 | maps grader-workbook column headers to item ids — pure course data, and the clearest candidate for `$COURSE_METADATA` |
| `slot_vocab.py` | `RUBRIC_EXTRAS` | 10 | course data |
| `leakage.py` | `CADENCE` | 1 | course data |

### The 6 NAMED modules

`baseline_h1.py`, `score_h1.py` (h1), `simulate_h3.py` (h3), `q6_consensus.py`
(Q6), `gold.py`, `gold_export.py` (gold). Engine modules named for a course
artifact. Renaming is cosmetic but the ratchet counts it, and
`check_no_module_is_named_for_a_course_artifact` already exists — so these are
either renamed or declared, not left silent.

### Order

1. `item == "1c"` → a declared property. Biggest win, ten sites, and it removes an
   item id from a parameter name.
2. The eleven selftest picks → `_pick`. Mechanical, and the mechanism is already there.
3. `CLOSURES_APPROVED` → `$COURSE_DATA`, following GOALS.md.
4. The remaining tables → `$COURSE_METADATA`, starting with `gold.py`'s three.
5. The six module names → rename or declare.
6. The 39 vocabulary units are docstring prose; sweep last, since they are
   documentation rather than behaviour and the ratchet's vocabulary arm reads
   DOCSTRINGS ONLY (see MODULE_AUDIT.md F1).

---

## J, revised: the blocker is a MISSING DEFAULT COURSE, not eager loading

**A wrong turn, recorded because the reasoning matters.** I measured that 7 of 18
engine modules `SystemExit` at import against an empty `$COURSE_DATA`, and
proposed making the 51 eager module-level course loads lazy. That was wrong twice:

* **The user's correction:** a scorer needing course data to load is a LOGICAL
  NECESSITY — there is nothing to score without it. Laziness defers the failure
  rather than fixing it. The real problem is the BOOTSTRAP case: starting a new
  project should not mean borrowing someone's real course.
* **The code's own record:** `coursedata.gold_declaration`'s docstring says
  *"EAGER AT THE CALL SITE, BY DESIGN ... importing a gold-consuming module now
  fails if the gold file is UNREACHABLE, where before the data was inline and it
  did not"*, and names subgoal C1b. The eagerness is measured, declared work.
  Making it lazy would have quietly undone it. (See the standing lesson: the
  comment above a rule usually holds prior measured work.)

### The fix: ship a STUB COURSE with the engine

A minimal course the engine falls back to when `$COURSE_DATA` points at no real
one — enough to initialise, and meant to be modified or repointed.

It buys three things laziness could not:
1. the engine repo becomes testable, lintable and CI-able on its own;
2. a new project starts from a template instead of a real cohort's data;
3. **"what must a course provide?" becomes answerable** instead of folklore.

### The stub's contract, derived from the 51 load sites

`declaration(name)` raises `KeyError` when a name is absent — *"if it is a new
table, the export must carry it; if it was removed, the reader of it must go
too."* So every key must EXIST; almost all may be EMPTY.

| provider | count | names |
|---|---:|---|
| `_gold_declaration` | 16 | CORRECTED_GOLD, GOLD_DIVERGENCES, GOLD_CEILINGS, PER_ITEM_EXCLUDE, GOLD_SLOT_CHARGES, GOLD_CODE_KNOWN, GOLD_SLOT_BOUNDS_KNOWN, GOLD_SLOT_UNMAPPABLE, GOLD_SLOT_DISAGREEMENTS_KNOWN, GOLD_CODE_CHARGES, SILENT_GOLD_DIVERGENCES, UNSCORED_GOLD_CRITERIA, CONSENSUS_OVERLAP_BACKLOG, DECLARED_CEILING_CELLS, FIXTURE_GOLD_OVERRIDES, `_1C_GATE_CEILING` |
| `_declaration` | 15 | APP_ONLY_SLOTS, ASK_EQUIVALENT_PROMPTS, CONTEXT_SOURCE, COUNTABLE_EXEMPT, DECOMPOSITION_DIVERGENCES, DESIGNED_TEXT, HAND_AUTHORED_ATTRS, MULTI_BLOCK_DECLARED, PAPER_ITEM_NOTES, PAPER_ITEM_NOTES_WHY, PROBE_UNREACHABLE_PAIRS, PROSE_ONLY_JUDGED_AGAINST, PROSE_ONLY_SLOTS, SELFTEST_NAMED_FIXTURES, UNCHARGED_VERDICTS |
| `_generator_table` | 8 | prompt_context, prompt_evidence, prompt_match_def, prompt_notes, prompt_notes_why, prompt_omit_guidance, prompt_response, prompt_sheet_only |
| `_generator_value` | 2 | PROBE_REACH_LIMITS, SCORING_DIVERGENCES |
| `_context_refs`, `_markers` | 3 each | one per declared handout |
| `config` | 2 | a rubric per handout it declares |
| `_field_table` | 1 | `items` |

**A defect this surfaced:** `_1C_GATE_CEILING` is a GOLD DECLARATION TABLE NAMED
FOR AN ITEM (`measured.py:6588`). A stub cannot supply it without inheriting this
course's item `1c`, and `check_no_definition_is_named_for_an_item` exists. It
should be renamed before the stub is built, or the stub is course-shaped on day
one.

### Build order

1. **Rename `_1C_GATE_CEILING`** — it blocks a course-neutral stub by construction.
2. **Build the stub** at `scoring/stub_course/` (ships with the engine): one
   handout, one item, one slot, all 31 tables present and empty, and a rubric
   that parses. It is a FIXTURE, so it may be tiny.
3. **`paths.py` falls back to it** when no course is found — declared, printed at
   startup, never silent. A run that scored the stub without noticing would be
   worse than a crash.
4. **Verify by the test that found this:** all 18 modules import against a
   `$COURSE_DATA` holding only the stub, zero `SystemExit`.
5. **Then the 786 course references** (`item == "1c"` → property test, the 11
   selftest picks → `_pick`, the tables → `$COURSE_METADATA`).
6. `olx_prompts.REF_IDS` (161 lines): check whether it is DEAD post-goal-C before
   moving it — its comment says it exists "so component ids stay stable across the
   rewrite", and the rewrite is done.

**The stub doubles as the J completion test.** When the engine can score the stub
end to end with no real course present, it is separable. That is a sharper
criterion than driving a ratchet to zero — and the ratchet under-reports anyway:
78 units by `course_inventory`, 786 distinct code lines by a twelve-class scan.

---

## J: the prepared fix set, derived by BUILDING the stub

The stub now imports all eight engine modules with no real course present
(`scratchpad/stub_course/`, regenerated by `build_stub_course.py`). Getting there
falsified three of my own proposed fixes and produced six real ones.

### THREE NON-FIXES — deliberate design the stub must SATISFY, not change

| behaviour | the record |
|---|---|
| 51 eager module-level course loads | `coursedata.gold_declaration`: *"EAGER AT THE CALL SITE, BY DESIGN"*, subgoal C1b. Making them lazy would undo measured work |
| `derived()` treats empty as absent | *"EMPTY IS ABSENT, not an answer"* — it is the fallback to the authored value, the migration safety net |
| `_RubricView.__getattr__` raises on absent | *"Raising AttributeError for an absent one is deliberate: `getattr(rub, "SLOT_SPEC", {})` is a real call site"* |

**The stub satisfies all three** by declaring the 15 non-structural derivations as
AUTHORED-EMPTY under each handout, using the export's own fallback path. No
engine change. This is the pattern for any future course that does not use a
given primitive.

### SIX REAL FIXES, in dependency order

**J-1. `paths.NS` is a hardcoded constant** (`paths.py:145`, `"edu.memphis.psych"`).
The engine resolves exactly one namespace. Its own comment says the standalone
repo declares the namespace in `psychology/manifest.yaml` "and the runner
resolves nothing if these disagree" — so the manifest is already the source of
truth and `paths.py` duplicates it. *Fix:* read NS from the manifest, env
override, stub's namespace as the final fallback.

**J-2. `olx_prompts.py:184` infers the handout from a block-id prefix.**
`HANDOUT = {i: (1 if a.startswith("bmod_h1") else 2 if a.startswith("bmod_h2") else 3) ...}`.
A course whose ids are not `bmod_*` is **silently classified handout 3** — a
wrong answer, not an error. *Fix:* every item already carries `"handout": N` in
the course file; read the declared field. One line, and it removes this course's
namespace from engine code.

**J-3. Ten modules hardcode a handout number** — `config(1)`/`config(2)`/`config(3)`
in `score.py:42`, `agreement.py:2232`, `leakage.py:492`, `measured.py:6807-6808`,
`baseline_h1.py:26`, `score_h1.py:38`, `q6_consensus.py:146`, `rubric_olx.py:364`,
`oc_grid.py:16`, and a comment in `rubric_h2_source.py`. This is why a
one-handout stub failed: `score.py` demands handout 2 EXIST. *Fix:* iterate
`sorted(handouts.HANDOUTS)`; where a module genuinely serves one handout, take it
as a parameter. Overlaps the 67-site `(1, 2, 3)` revision — do them together.

**J-4. `handouts.HANDOUTS` is 281 hardcoded lines** (`handouts.py:255-535`), 3 x 11
keys, ~7 per handout being course data: template path, submissions path, outdir,
blurb, exemplar_participants, exemplar_items / suspect_participants,
cited_participants. Only `capture_tail`, `repair_orphans`, `join_aware` are
engine flags. `course.json` ALREADY has a `handouts` key, holding only
`{"authored": {}}` — the structure exists and is unused. *Fix:* move the course
keys into it; `handouts.py` assembles `HANDOUTS` from the file plus the flags.
**This is what makes a second course possible at all** — today, adding one means
editing engine code.

**J-4 DONE** (2026-09-24), behaviour-preserving. The mechanism was already half
built and unfinished: `HANDOUT_FIELDS` existed in `course_metadata_source.py`,
was exported at `rubric_export.py:335`, read back by `handouts._course_field`,
and OVERLAID onto the table at `handouts.py:545` — but it carried only three of
the nine course keys. J-4 widened it to eight and extended the overlay, so every
course key in `HANDOUTS` is now driven by the course file.

The three PATH keys are stored as LEAVES (`template_file`, `submissions_dir`,
`outdir_name`) and joined to `MATERIALS`/`SUBS`/`OUT` in `handouts.py`. A course
file holding absolute paths could not survive $COURSE_DATA moving. `markers`
needed no change and deliberately stays out — `handouts.py` takes it from
`segment`, which already reads the course file, so they are one object.

The hardcoded table STAYS, as documented defaults. Its remaining bulk is the
reasoning comments attached to the values (the unstable-p6 exemplar note and the
rest), which are provenance; deleting the values would strip their anchors. The
portability goal is met by the overlay, not by the line count.

Verified three ways: `HANDOUTS` identical field-by-field to a baseline captured
before the change; a fire test proving all seven newly-moved fields are actually
driven by the course file (an identity check alone would also pass on dead code);
and the authoring source checked equal to the course file. Gate: 44 findings, all
the pre-existing corpus-reference class, matching J-1/J-2/J-3. `_PATH_FIELDS`
backfilled into the inventory.

**A blocker was found and NOT fixed here:** `rubric_export.py` no longer
reproduces `course.json`. Handout 2 is the only handout whose builder still
exists, and the rubric content it derived from has moved to the OLX, so all seven
of its derivable tables now recompute to `()`; `classify()` correctly reads that
as "differed" and re-carries them as authored data. Re-exporting would therefore
REGRESS the file by restoring duplication the migration removed. No live bug —
`coursedata.derived()` reads the OLX and returns the right answer for all seven
(verified) — but it is why J-4 patched the course file surgically instead of
regenerating it. Belongs with the export work. Noted in passing: `derived()` is
set-equal but not order-equal to the authored tuples.

**J-5. `score.py:43+` reads derived values UNGUARDED** — `BARRIER_PICK_ITEMS =
_RUBRIC2.BARRIER_PICK_ITEMS` and a run of siblings, where the documented contract
is `getattr(rub, NAME, default)`. *Fix:* use the guarded form at these call
sites. Without it, every course must declare every derivation even when it uses
none of them — which is what the stub is currently forced to do.

**J-6. The course-file TYPE and PRESENCE contract is undocumented.**
- generator tables are MIXED: `TABLE_ORDER`, `CONTEXT_REFS`, `SEGMENT_MARKERS`,
  `CONTEXT__non_item` are dicts; `SCORING_DIVERGENCES`, `PROBE_REACH_LIMITS` are lists
- declarations are uniformly lists
- per-item `prompt_*` fields: **presence is meaningful**. `prompt_sheet_only`
  holds a block-id STRING; an empty list there reaches `.startswith()` and
  raises. The real course omits fields an item does not use.

*Fix:* declare this in `course_schema.py`, which already exists for exactly this
purpose ("every item field belongs to a declared group"), and have the stub
builder read the schema rather than hardcode the shapes.

**J-5 DONE** (2026-09-24). The six reads in `score.py` now use
`getattr(_RUBRIC2, NAME, default)` -- five tuples default `()`, `REQUIRED_MOVE`
defaults `{}`. The defaults are an ANSWER, not a shrug: each name is a set of
items of some kind, so "the course declared none" and "no item is of that kind"
are the same fact. That reasoning does NOT carry to `coursedata.derived()`, where
empty means ABSENT and falls through to the authored value, and the comment at
the call sites says so to stop the default being copied there.

The population was enumerated by PROPERTY -- "reads a rubric table by name,
however the base is spelled" -- rather than by grepping the spellings already
seen, and cross-checked two ways. Outside the six, exactly **two** bare reads
exist, and BOTH are correct as they stand:

* `leakage.py:494` (`OC_FRAME`) is already inside `try/except Exception: pass`;
  absence is tolerated by construction and `getattr` would add nothing.
* `score.py:313` (`SLOT_OPTIONS`) raises DELIBERATELY, and its docstring says
  why: *"a silent empty enum would let the model answer anything and the engine
  would compare it against values it never offered."*

`BY_ID` and `ITEMS` are excluded as core -- always served, and guarding them
would hide a real breakage. Gate: 44, baseline.

**J-6 DONE** (2026-09-24). `course_schema.py` now carries the contract as three
declarations -- `GENERATOR_TABLE_TYPES` (4 dicts, 2 lists; mixed deliberately,
since a table keyed by something is a dict and a sequence of records is a list),
`DECLARATION_TYPE` (uniformly `list`, because the file stores every declaration
as `[[key, value], ...]`), and `OPTIONAL_ITEM_FIELD_TYPES` (8 fields) -- checked
by `type_check()` and wired into `check()`. Every shape was MEASURED against the
live course file, not transcribed from this plan.

The table's point is presence, not emptiness: **an absent field and an empty one
are different facts.** `_generator_table` collects `{iid: gen[field] ... if field
in gen}` and its docstring states the contract outright -- *"Absent keys stay
ABSENT ... so `in SHEET_ONLY` still means what it meant."*

Fire-tested on all three arms plus a clean control, per this module's own rule
that a check nobody has watched fail proves nothing.

*This found a real defect in the stub builder.* It emitted `"prompt_context": []`
and three siblings on every item, which would have JOINED the stub's items to the
RESPONSE and CONTEXT tables with empty values instead of leaving them out. The
builder's own docstring already said items should omit unused fields; a stale
comment above the code claimed the opposite and the code followed the comment.
The reader is the contract, so the fields are now omitted and the stale comment
is gone. Verified import-neutral against the previous stub.

**J-4b. The handout SET is still hardcoded, and J-4 did not fix it.** Found
2026-09-24 while testing the stub. J-4 moved every handout FIELD into the course
file, but `HANDOUTS`'s KEYS are still the literal `1, 2, 3`. So `declared()` --
the J-3 accessor whose docstring says "every handout this course declares" --
reports the ENGINE's set, not the course's. Measured against the stub, which
declares two: `handouts.declared()` returns `(1, 2, 3)` while
`coursedata.items()` and the course file's `handouts` block both say `[1, 2]`.
`score.py --help` offers `--handout {1,2,3}` against a two-handout course. *Fix:*
build `HANDOUTS` over the handouts the COURSE FILE declares, not over a literal.

**J-4c. Absent declarations silently inherit THIS course's data. SECURITY-ISH,
and it defeats the stub's whole purpose.** J-4 kept the hardcoded table as
"documented defaults", with the course file overlaid on top. That reads as
conservative and is not: a course that declares nothing does not get *no* value,
it gets **edu.memphis.psych's** value. Measured against the stub, whose
`HANDOUT_FIELDS` is `{}`:

    h1 submissions -> .../Handout Submissions with Scoring and Feedback/...   EXISTS

The stub -- which exists precisely so "starting a new project does not mean
borrowing a real cohort's course" -- resolves to the real cohort's submissions
directory, and the path is present on disk, so nothing fails loudly. A wrong
answer, not an error, which is the failure mode this plan keeps naming.

*This corrects the J-4 note above.* "The portability goal is met by the overlay"
is FALSE as written: the overlay makes a declared field course-driven, and leaves
an UNDECLARED field silently course-contaminated. *Fix:* a data path must have no
engine-side default -- absent means absent, and a course that does not declare
its submissions directory has none. Keep defaults only for the engine FLAGS.

**J-4d. `SUBS` and `OUT` are not namespaced, so two courses collide.** J-1
namespaced `MATERIALS` (`$COURSE_DATA/courses/<ns>/materials`) but not its
siblings. Measured under `COURSE_NS=stub`:

    MATERIALS  .../courses/stub/materials        namespaced
    SUBS       .../Handout Submissions ...       SHARED
    OUT        .../out                           SHARED

Two courses therefore read submissions from one root and write results into one
`out/`, where `h1`/`h2`/`h3` are the only separation -- so a second course
OVERWRITES the first's output rather than sitting beside it. *Fix:* namespace
both the way `MATERIALS` already is. Small, and it belongs with J-4c since both
are about a course's data being reachable only by accident.

**J-4b, J-4c and J-4d DONE** (2026-09-24), all three gate-clean at 44 findings
with a set identical to baseline, and the real course's `HANDOUTS` still
byte-identical to the pre-J-4 snapshot.

* **J-4b.** `coursedata.declared_handouts()` is the accessor; `handouts.py`
  builds the table over what the COURSE FILE declares. Stub reports 2 handouts,
  real course 3. *The first attempt read `_load()` directly and `course_schema`'s
  Part B caught it* -- "a raw entry defeats the boundary while appearing to
  honour it, because the code still calls into `coursedata`". The answer was to
  ADD THE ACCESSOR to the boundary module, not to exempt the caller.
* **J-4c.** A course-data field the course does not declare is now `None`. The
  stub's `submissions` went from the real cohort's directory to absent. Engine
  FLAGS keep defaults: `capture_tail` describes how the engine reads a document,
  not whose course it is. The test is WHICH KEYS WERE DECLARED, not which values
  are truthy -- a course declaring an empty exemplar list has answered.
* **J-4d.** `SUBS` and `OUT` are namespaced, with the legacy shared layout
  declared as `shared_data_layout: true` in `psychology/manifest.yaml`.

  **The manifest key needed scoping to work at all.** `_manifest()` reads
  whatever manifest sits beside `OLX_DIR` -- the ENGINE REPO's content directory,
  which does not change when `COURSE_NS` does -- so a bare key leaked to the stub
  and would have re-created J-4c. `_course_manifest()` honours a key only when
  that manifest's own `namespace` equals the active `NS`. Legacy is opt-in, so a
  new course cannot fall into it; NO DATA MOVED, and this course's paths resolve
  exactly as before. `OUT` moved below `NS` since its default now depends on the
  namespace -- checked first that nothing reads it in between, which is the
  ordering trap that broke `paths.py` earlier in this session.

**J-7. Course content paths are hardcoded in engine code.** *Found while testing
the stub.* `psychology/` and the `bmod_*` stems are THIS course's names, living
in engine code, concentrated in `enforcement.py` and `measured.py`.

**The counts below are reconciled, because the first one was wrong.** An initial
scan reported "67 code sites"; it counted a line once per matching SPELLING, so
a line naming both `psychology/` and a `bmod_handout` stem was counted twice.
Counting LINES gives 58 matching, 56 of them code. Both numbers described the
same tree -- state the unit, or the size of the job moves when nothing has.

    before J-7a/J-7b   58 lines match, 56 code
    after  J-7a/J-7b   27 lines match, 17 code

The 17 that remain are the declarations in `paths.py`, an authored OLX template's
`<Use ref>` lines, a domain-vocabulary word list and a check's expected-stem set
-- enumerated under J-7b, and correct where they are.

**J-7a DONE** (2026-09-24) — the RUBRIC COMPONENT half, which is what blocked the
stub. `paths._manifest(key, default, env)` generalises the three-step resolution
`_namespace` already used (environment, then the content collection's
`manifest.yaml`, then a fallback), and `paths.RUBRIC_COMPONENT` resolves the
component's file name through it. `rubric_component.py`'s three literals now read
`paths.OLX_DIR.name` and `paths.RUBRIC_COMPONENT`, so no course stem remains in
that module. `COURSE_RUBRIC_OLX` names the file outright, for content that is not
in the staged layout at all -- the stub ships its rubric beside its `course.json`
and is never staged, so no combination of namespace and component name reaches
it. Defaults keep every existing tree reading the file it already read: verified
identical `staged_path()`/`expanded_path()`, 26 items, 8/8 modules importing.

**J-7b DONE** (2026-09-24) — the HANDOUT stems and the globs over them. Gate
clean: 44 findings, SET identical to baseline, nothing added or removed.

`paths.HANDOUT_OLX` is manifest-declared (`handout_olx`, default
`bmod_handout%d.olx`), with `handout_olx(h)`, `handout_olx_glob()` and
`handout_olx_path(h)` beside it. **The glob is DERIVED from the pattern** rather
than written next to it: they were one fact in two places, and a course changing
the pattern would have left the glob matching nothing.

45 of 58 sites converted:

| class | count | now reads |
|---|---|---|
| `f"bmod_handout{h}.olx"` | 25 | `paths.handout_olx(h)` |
| `.glob("bmod_handout*.olx")` | 8 | `paths.handout_olx_glob()` |
| content dir built from `__file__` | 12 | `paths.OLX_DIR` |

The remaining 13 are correct where they are, and are listed so nobody re-opens
them: three are docstring prose, three are the definitions in `paths.py`, three
are `<Use ref="bmod_handout1"/>` inside an AUTHORED OLX template, one is a
domain-vocabulary word list (a different class entirely), one is a check's
expected-stem set, and the rest are comments.

### Three defects this found, none of them in the plan

1. **`agreement.py:158` would have raised `NameError` at call time.** The
   substitution landed in a module that received no `paths` import, and the
   module still IMPORTED CLEANLY because `_h1` is not called during import.
   "8/8 modules import" did not cover it; checking the import BINDING did.
2. **`olx_corpus.default_roots()` — the same bug, and my audit missed it**
   because that substitution used the name `paths` while the audit looked for
   `_p7`. *The search reproduced the blind spot of the fix.* Re-run by PROPERTY
   -- "a Name loaded in a function body that is bound nowhere reachable" -- over
   every touched file: 4 candidates, all pre-existing and unrelated.
3. **`tools/corpus_ref.py` had a DEAD default path.** Its fallback was
   `HERE.parent / "psychology"`, but `HERE` is `tools/`, so it resolved to
   `scoring/psychology`, WHICH DOES NOT EXIST. Any caller omitting `olx_dir`
   scanned nothing and reported an empty corpus instead of failing. Recorded at
   the site, because it is a behaviour change and not a pure refactor.

### The gate was reporting CLEAN while the audit crashed

Found the same day, and it is the finding that matters most, because it was
MASKING the two above.

`precommit_gate.main()` runs `equivalence.py --enforcement` as a subprocess and
keeps the lines starting with `! `. A crashed audit emits none, so `blocking` was
empty, and the gate printed **"enforcement audit clean"** and returned 0. Any
crash in the audit read as a pass. It surfaced only because a 44-finding baseline
dropped to zero -- had the break left a few findings standing, the drop would not
have been obvious.

**Refusing on a non-zero exit does not work, and that was the first instinct.**
`print_enforcement` returns `1 if findings else 0`, and an uncaught exception
also exits 1, so "non-zero means crashed" would refuse every ordinary run that
found something -- including today's baseline. The exit code cannot separate the
two.

The test is therefore POSITIVE LIVENESS: did the audit print the banner it emits
BEFORE any finding? Plus the traceback as a second signal. The bug was reading
absence of evidence as evidence of absence, and an exit-code check would have
kept doing that in a different shape. Fire-tested on four arms:

| induced | result |
|---|---|
| traceback, no banner | refuses -- "did not COMPLETE" |
| no banner, no traceback (killed by a signal) | refuses |
| banner, no findings | passes clean |
| banner + findings | refuses with the original divergence message |

The third row is why liveness beats the exit code twice over: a signal-killed
subprocess prints no traceback at all.

NOT OVERRIDABLE by `ALLOW_UNDECLARED`: that flag declares a KNOWN divergence, and
an audit that did not run has not found one.

### The completion test

**First half MET** (2026-09-24): **8/8 modules import against the stub with no
real course present** -- `coursedata`, `handouts`, `olx_prompts`, `score`,
`course_schema`, `leakage`, `measured`, `agreement`, under `COURSE_FILE`,
`COURSE_NS=stub` and `COURSE_RUBRIC_OLX`. Reaching it took four distinct
failures, each of which was a real defect in the stub rather than in the engine:

1. the rubric path named one course's stem (J-7a);
2. **the stub rubric parsed but READ AS EMPTY.** It was written to a guessed
   schema -- `<Item id=... handout=...>`, `verdicts="met,absent"`, `points="1"` --
   while `as_view_items` keys on `el.get("scores")` and skips an Item without it.
   *A rubric that parses is not a rubric that reads.* The vocabulary is now taken
   from the real component and the builder records it;
3. **prompt fragments were missing.** `olx_prompts` refuses one it cannot find,
   because "a missing one truncates a prompt in silence". All **28** are
   enumerated from the real component's `<Frame name="fragment:...">`
   declarations -- not discovered one failure at a time, which is what keeps the
   list complete when a fragment is added;
4. the stub declared NO criteria handout, so J-3's own refusal in
   `score._criteria_rubric()` fired -- correctly. The stub now declares exactly
   one (`CRITERIA_HANDOUT = 2`) and exercises that path rather than dodging it.

**Second half MET** (2026-09-24). `score.main()` runs both handouts against the
stub with no real course present and writes results:

    H1: scoring 1 participant(s) x 1 items
      [1/1] participant  1:  1.00/1
    H2: scoring 1 participant(s) x 1 items
      [1/1] participant  1:  1.00/1  (1 escalated)
    -> courses/stub/out/h{1,2}/participant_001.json

The whole path is real engine code: CLI -> course file -> rubric component ->
find submissions -> segment the .docx -> build the prompt -> parse -> derive the
ledger -> write results with provenance (`backend`, `supports_tools`, `era`).

**THE MODEL CALL IS CANNED, and that is the one qualification.** There is no
offline backend -- `cli`, `api` and `lo` each call a model or a server -- so
`score.make_backend` is replaced by a fixed, schema-shaped response. Everything
on both sides of that call is real. The model is not what J tests; a run against
a live backend is a separate, paid step and has NOT been taken.

Three things were needed, and the third was a defect:

1. **The stub declares its own data** -- `template_file`, `submissions_dir`,
   `outdir_name`, `blurb`, `capture_tail`. That is J-4c working as designed, not
   a workaround: undeclared is absent, so a stub that wants to be scored must say
   where its data lives.
2. **A data fixture**, `make_stub_fixture.py`: a blank template and one
   submission per handout, written as hand-built zips (`docx_text` reads a .docx
   with `zipfile` + `ElementTree`, so no python-docx), into
   `$COURSE_DATA/courses/stub/` -- outside any repository, where course data
   belongs.
3. **The stub was scoring an EMPTY RESPONSE.** The first successful run reported
   `1.00/1` with **`response_chars: 0`**: no `SEGMENT_MARKERS` were declared, so
   `segment()` returned `{}` and the model was being asked to grade nothing while
   the totals looked perfect. *A stub that scores nothing is not a stub that
   scores.* With markers declared, `response_chars` is 47, and the student's text
   reaching the prompt was verified directly rather than inferred from the score.

### The escalate on H2, traced: the stub demonstrates M

`escalate` is `raw.escalate or unknown or over_specified or forced_advisory`. The
term that fires is **`unknown == ['NOT_OC']`**.

S2 declares `derive_from_criteria`, so `derive_oc_ledger` runs -- and **goal M
below already records why that is course-specific** (the fact vocabulary, the
gate structure, the type taxonomy). This is not a new finding; it is M observed
RUNNING, on a course that has no operant conditioning in it. Two things it adds
to what M already says:

1. **`derive_from_criteria` is the trigger, so the flag itself carries the
   frame.** It does not mean "score this item from criteria"; it means "score it
   through the operant-conditioning frame". A second course declaring the flag
   inherits psychology's domain model without naming it.
2. **An undeclared code is SILENTLY DROPPED.** `add()` looks the code up in the
   item's declared deductions and, on a miss, appends to `unknown` and returns
   without charging:

        spec = codes.get(code)
        if spec is None:
            unknown.append(code)
            return

   The stub kept its 1.00/1 ONLY because its rubric does not declare `NOT_OC`. A
   course that happened to declare that code would be charged for failing
   criteria it never authored; one that does not is silently not charged.
   Neither is a correct answer, and `escalate` is the only surviving signal --
   which is why this reads as noise until it is traced.

**When M is taken up, the stub is part of it** (user, 2026-09-24): the stub must
score its criteria item WITHOUT inheriting a frame it never declared, and
`escalate` on a clean stub run is the acceptance test. See M's own note.



`lo-blocks/packages/shared/lib/grading/stub_course/` (it moved there, so the
scorer can reach it as its default) + all eight modules importing is the gate,
and it is
sharper than a ratchet: an outsider can run it. Full J is met when the engine
SCORES the stub end to end with no real course present.

---

# The 786 course references: a disposition plan

**Measured, not estimated.** `course_inventory` reports 78 units; a twelve-class
scan over CODE lines (comments excluded) finds **786 distinct lines across 39
modules in 393 contiguous blocks**. The ratchet under-reports ~10x because it
counts four things — module-level tables naming item ids, item ids in
comparisons, vocabulary IN DOCSTRINGS ONLY, and module names — and does not look
at rubric slot keys, deduction codes, OLX block ids, corpus refs in code, or
domain vocabulary outside docstrings.

**Every reference falls into one of seven dispositions.** Counted in blocks, not
lines: 393 blocks is the honest size, because one 161-line table is one decision.

---

## A — MOVE the table to course data (8 tables, ~548 lines)

Pure course data sitting in engine modules. Each moves whole.

| module | table | lines | destination |
|---|---|---:|---|
| `olx_prompts.py` | `REF_IDS` | 161 | `course.json` generator section |
| `precommit_gate.py` | `NOT_STUDENT_TEXT` | 153 | **audit first** — 153 lines carrying ONE item id; it may be generic prose the scan mis-flagged |
| `enforcement.py` | `PROBE_PROVOCATIONS` | 113 | course data |
| `enforcement.py` | `_PASS` / `_FAIL` | 64 | course data (the oc_analysis probe pair) |
| `gold.py` | `H1/H2/H3_HEADER_TO_ITEM` | 28 | `$COURSE_METADATA` — maps grader-workbook column headers to item ids |
| `probe.py` | `ANSWERED_UNDER` | 18 | course data |
| `slot_vocab.py` | `RUBRIC_EXTRAS` | 10 | course data |
| `leakage.py` | `CADENCE` | 1 | course data |

**`REF_IDS` IS LIVE — do not delete it.** I assumed goal C had made it dead; it
is read at `olx_prompts.py:979` and `:3062` and registered in enforcement as
"minted `<Ref>` ids, generated and checked by `--refs`". It moves.

## B — MOVE to `$COURSE_DATA` as an accumulating record (1 table, 234 lines)

`goals.CLOSURES_APPROVED` — subgoal closure notes, thick with cell ids and corpus
references, and it GROWS with course work. Follows `GOALS.md` by the rule already
applied to the ledger and `OVERRIDES.md`: a record that accumulates leaves the
repository.

## C — REPLACE with a declared property (11 sites)

| pattern | sites | replacement |
|---|---:|---|
| `item == "1c"` | 10 | the rubric already declares `derived="has_own_graph:complete:..."` — test the property. Two sites pass `rebuild_1c=(item == "1c")`, so the id has reached a PARAMETER NAME |
| `a.startswith("bmod_h1")` | 1 | every item carries `"handout": N`; read the declared field (J-2) |

Ten sites collapse to one predicate. This is the highest value-per-edit in the set.

## D — REPLACE with dynamic selection (11 sites)

`equivalence.py` x7 in `enforcement_selftest`, `reader_equivalence.py` x4 in
`_mutations`, `q6_consensus.py` x1. The suite ALREADY has `_pick(label,
candidates, why)`, which chooses a target and records the reason — used for the
GOALS case and the cover-group case. These eleven hardcode what it exists to
select. Mechanical.

## E — EXTRACT as a course-specific SCORER (~2,187 lines, upper bound)

**The largest and most consequential disposition, and it is not "data in code".**
It is this course's subject matter implemented as code:

| module | loc | OC loc | % | biggest |
|---|---:|---:|---:|---|
| `stale_check.py` | 243 | 140 | **57%** | `audit` (140) |
| `rubric_olx.py` | 417 | 203 | **48%** | `render_item` (144) |
| `score.py` | 2307 | 775 | **33%** | `derive_oc_ledger` (232) |
| `rubric_component.py` | 640 | 127 | 19% | `as_view_items` (127) |
| `olx_prompts.py` | 3384 | 302 | 8% | `assembler_inputs` (191) |
| `measured.py` | 7048 | 254 | 3% | `paper_scorer_agreement` (220) |
| `enforcement.py` | 16417 | 256 | 1% | `check_selectors_govern_something` (103) |
| `agreement.py` | 2460 | 112 | 4% | `score_oc_cadence` (61) |

`score.py`'s `derive_oc_ledger` computes `is_oc` from `has_behavior`,
`has_stimulus`, `contingent`, `follows_behavior`, `stimulus_is_arranged` — the
definitional structure of operant conditioning, not a table about it.

**Treat this figure as an UPPER BOUND.** It counts every function with three or
more OC references, so generic machinery that merely NAMES oc fields
(`as_view_items`, `check_selectors_govern_something`) is included. The real
extractable core is `derive_oc_ledger` + `oc_passing_sheet` + `oc_check_names` +
the OC half of `build_schema`, plus `oc_grid.py` entire.

**The decision this forces, and it is the user's:** a scorer for a different
subject cannot reuse this logic. Either
(a) it moves to the course side as a course-supplied scorer,
(b) it becomes a PLUGIN the engine loads by declaration — which fits the existing
    design, since `_forbid_rule(item, "consequence_not_a_setup")` already reads
    the rubric rather than hardcoding, so the seam exists, or
(c) it stays and the engine is honestly "a scorer for behaviour-modification
    courses", which is a legitimate answer but should be stated rather than
    implied.

**Recommend (b).** It preserves the two-engine comparison the whole project rests
on, and the plugin boundary is already half-built.

## F — RENAME (7 names)

Six modules named for course artifacts — `baseline_h1`, `score_h1` (h1),
`simulate_h3` (h3), `q6_consensus` (Q6), `gold`, `gold_export` — plus the gold
declaration key `_1C_GATE_CEILING`, which blocks a course-neutral stub by
construction. `check_no_module_is_named_for_a_course_artifact` exists but does
not catch the gold KEY, because it is not a module-level definition.

## G — KEEP (generic, verify individually)

Ordinary English and engine vocabulary the scan flags: `consequence` and
`behaviour` in their plain senses, `verdict`, `confident`, `BLANK`. The
QUALITY_CONTROL split judged 20 such hits one at a time and kept 8 — the same
per-site judgement is needed here, not a blanket rule.

---

## Order, and why

1. **F (renames)** — cheapest, and `_1C_GATE_CEILING` blocks the stub.
2. **C (property test)** — 10 sites to 1 predicate, removes an id from a parameter name.
3. **D (dynamic picks)** — mechanical, mechanism already exists.
4. **A + B (tables)** — bulk data movement, ~782 lines, each verifiable by equality before deletion (`migrated_tables.py`'s discipline).
5. **G (judgement pass)** — per site, after the mechanical work stops moving the target.
6. **E (the scorer)** — LAST, and only after the user chooses (a), (b) or (c). It is the one disposition that changes what the engine IS, and doing it before the rest would churn everything else.

**Verification at each step:** the stub must still import all eight modules, and
the twelve-class scan must fall monotonically. Neither alone is sufficient — the
scan under-reports by construction and the stub proves only initialisation.

---

# E, decided: the OC scorer becomes a PLUGIN

User's decision, 2026-09-24. The design below is built from the seam that already
exists rather than an invented one.

## The boundary is already there, and it is already declaration-driven

`score.py` dispatches on a rubric flag:

```python
if item.get("derive_from_criteria"):
    ledger, checks, unknown, forced_advisory = derive_oc_ledger(item, raw)
elif item.get("derive_from_credit"):
    ledger, checks, unknown = derive_ledger(item, raw, response)
```

The rubric ALREADY says which scorer each item uses, and the split is exact:

| path | items | disposition |
|---|---|---|
| `derive_from_criteria` | PR, NR, PP, NP, DAY1, WK1, DAY2, WK2 (8) | becomes the **oc plugin** |
| `derive_from_credit` | Q1-Q6, T1, T2, D1, D2 (12) | stays as the engine's generic path |

So this is not a new architecture. It is naming a boundary that exists, and
moving one side of it out.

## The contract

A scorer plugin supplies five functions. All five already exist; four are in
`score.py` and one pair is the web mirror in `agreement.py`.

| plugin function | today | lines |
|---|---|---:|
| `derive_ledger(item, raw)` -> `(ledger, checks, unknown, advisory)` | `score.derive_oc_ledger` | 232 |
| `schema_fragment(item)` -> schema properties | the OC half of `score.build_schema` | ~100 of 197 |
| `passing_sheet(item)` -> a full-marks answer | `score.oc_passing_sheet` | 22 |
| `check_names(item)` -> `[str]` | `score.oc_check_names` | 11 |
| `score_web(...)`, `score_web_cadence(...)` | `agreement.score_oc`, `score_oc_cadence` | 112 |

Plus `oc_grid.py` (38 lines) entire, which exercises the ledger and belongs with
it.

## Resolution

1. The rubric declares the scorer by NAME: `derive_from="oc"`, with today's
   `derive_from_criteria` kept as an alias until the OLX is rewritten.
2. The engine resolves the name through a registry, looking first at the course
   (`$COURSE_METADATA/scorers/`) and then at built-ins, so a course can ship or
   override a scorer without an engine change.
3. `credit` stays built in: it is slot-sheet driven and subject-neutral.
4. An unresolvable name is a REFUSAL naming the item and the scorer, never a
   silent fallback to `credit` -- a wrong scorer that runs is worse than one that
   does not.

## What this must not break, and how each is kept

* **The two-engine comparison.** `enforcement.py:4334` compares
  `agreement.score_oc`, `agreement.score_oc_cadence` and `score.derive_oc_ledger`
  BY READING THEIR SOURCE, and `check_slot_rules_reach_both_prompts` depends on
  it. Both sides move together into the plugin, and the comparison resolves
  through the registry instead of by import. **This is the thing most likely to
  break silently**, because a source-reading check that cannot find its target
  can pass vacuously -- so its finding must be asserted before and after.
* **`enforcement.py:40`** imports `derive_oc_ledger` directly. That becomes a
  registry lookup.
* **`CLI_FNS = ("derive_ledger", "derive_oc_ledger")`** (`enforcement.py:1749`)
  names both paths; it becomes the registry's members.
* **The selftest's OC cases** inject into OC fixtures. They move with the plugin,
  or they are re-aimed at the generic path -- decided per case, not in bulk.

## Order within E

1. Extract the five functions + `oc_grid.py` into one module, still imported
   directly. **Prove identical behaviour before moving anything**: the ledger for
   every `derive_from_criteria` item, every cell, must be byte-identical.
2. Introduce the registry and the `derive_from` name; keep `derive_from_criteria`
   working as an alias.
3. Move the module to the course side.
4. Re-point `enforcement`'s three touchpoints and assert its findings are
   unchanged -- including that the source-reading comparison still FIRES, not
   merely passes.
5. Only then delete the aliases.

**Step 1 is the whole safety of this.** The comparison machinery reads source
text, so a move that changes formatting can change a check's answer without
changing behaviour. Byte-identical ledgers first, structure second.

## E IS DONE (2026-09-24). All five steps, gate clean at 44 findings, set identical

`COURSE_METADATA/scorers/oc.py` holds the operant-conditioning scorer;
`scorers.py` is the registry; `BUILTIN` is `{}`. **The engine ships no subject's
scorer and names no course's subject.**

| step | what landed |
|---|---|
| 1 | five functions + `oc_grid` extracted, verbatim |
| 2 | registry, `derive_from` name, legacy flags as one-way aliases |
| 3 | module moved to the course side, `BUILTIN` emptied |
| 4 | `enforcement`'s FIVE touchpoints repointed (the plan said three) |
| 5 | aliases deleted; `stale_check` and `agreement.SCORERS` repointed first |

**The proof throughout was a 51,200-case behavioural fingerprint** -- the ledger
is a pure function of `(item, raw)`, so the input space was swept rather than the
cells, which would have needed model calls. sha256 `1971e534...` before step 1
and after step 5, unchanged.

### Three traps sprang, and each was caught by a different guard

**1. A wrapper passes every behavioural test and breaks the audit silently.**
Step 1 first bound the old names as `def derive_oc_ledger(...): return
scorer_oc.derive_ledger(...)`. `inspect.getsource` returns the WRAPPER, so the
source `check_selectors_govern_something` greps went from **13,424 characters to
112** -- it found no slot reads and reported nothing, passing vacuously, while
`check_weighted_slots_are_scored` correctly flagged 21 weighted slots reaching no
scorer. **Bind the function OBJECT, never a wrapper**, and the comment at the
site says so because a future reader will want to "tidy" it back.

**2. The population was truncated by my own `head -4`.** Checking what still used
the aliases, the grep was piped through `head -4`, so two live users in
`measured.py` never appeared. Deleting the aliases then broke
`paper_scorer_agreement` **960 times**. The rule was followed and the TOOL
defeated it: the rule was followed and the TOOL broke it. A truncated scan
is not a scan, and `head` on a population check is a defect in the check.

**3. A module name that is DATA cannot be found by grepping for the call.**
`_PAPER_BY_BRANCH` holds `("score", "derive_oc_ledger")` as a STRING PAIR,
resolved later by `importlib.import_module`. No call site names the function, so
nothing greppable existed. Worse, the first fix wrote `"scorers:oc"` into the
table without checking the consumer -- `import_module("scorers:oc")` throws into
an `except: return []` and is recorded as "missing", so it would have LOOKED
fixed. `_part_module()` now resolves `scorers:<name>` through the registry,
because **which file implements `oc` is the course's answer and cannot be an
import path**.

### What the ratchets required

* `modules()` did not glob the scorers directory, so moving the file took its six
  definitions out of the inventory entirely -- the exact silent failure its own
  docstring warns about, one directory further out. Widened.
* The property budget tightened **11 -> 9**: `cadence` and `expected_type` are no
  longer branched on in engine code, because that branching left with the scorer.
  The ratchet made the improvement permanent rather than merely observed.

### The verification harnesses had to move too

The controls patched `score.derive_oc_ledger` and the fingerprint called it. Left
alone, the controls would have reported INERT and the fingerprint would have
crashed -- **a control that cannot find its target is the vacuity it exists to
detect, one level up**. Both retargeted at the plugin: 3/3 controls fire, sha
unchanged.

## What E buys

The engine stops knowing what operant conditioning is. A second course supplies
its own scorer, or uses `credit` alone, and the stub uses `credit` -- which is
why the stub could import with zero OC items and no OC declarations.

---


### P · THE ENGINE NAMES THIS COURSE'S FACTS (filed 2026-09-24, user)

**Found by the user challenging a name.** Reviewing the converged vocabulary, the
user observed that `cadence_ok` and `targets_intended_behavior` "don't sound
quite generic -- they still use behavior and cadence, which is still psych
language." Chasing that found something wider than the two names.

**Measured: 60 code sites across five ENGINE modules name 10 of this course's
facts.** Docstrings excluded -- these are in code:

| module | code sites | distinct facts |
|---|---:|---:|
| `enforcement.py` | 35 | 10 |
| `goals.py` | 17 | 5 |
| `score.py` | 5 | 2 |
| `measured.py` | 2 | 2 |
| `precommit_gate.py` | 1 | 1 |

The facts: `avoidance_frame`, `cadence_ok`, `observed_type`, `named_type`,
`stimulus_move`, `stimulus_is_arranged`, `targets_own_behavior`,
`targets_intended_behavior`, `consequence_asserted`, `restriction_authored`.

## P IN PROGRESS (2026-09-24): enforcement is at ZERO; six sites remain

**THE FILED COUNT OF 60 WAS WRONG.** The honest figure, excluding prose inside
string literals, is **12 code sites**. `goals.py` and `precommit_gate.py` have
NONE -- their seventeen "sites" were subgoal closure notes recording what was
measured, which is history, not logic. The detector stripped docstrings but still
counted ordinary strings, so it read text that MENTIONS a name as text that USES
one.

### Moved to the course file

Five tables, with 52 declared table-entry removals, each verified identical
afterwards: `SIDE_ALIAS`, `SIDE_INVERTED`, `PROBE_PASS`, `PROBE_FAIL`,
`PROBE_TYPE_FIELDS`. The reasoning for every value travelled with them.

`SIDE_INVERTED` is the one worth noting: `measured.py` held
`frozenset({"avoidance_frame"})` with a comment saying it was named "here and
nowhere else" BECAUSE the alias map could not carry an inversion. Both halves of
that fact now travel together and neither is in engine code.

### Moved to the course SCORER (user's instruction)

`_tbl`, `_oc_baseline` and `_oc_fail` are `_probe_value`, `probe_baseline` and
`probe_fail` in `scorers/oc.py`, reached through the registry like the scorer
itself. They built this course's hypothetical answers -- naming `observed_type`,
`named_type` and the PR/NR/PP/NP taxonomy -- so the audit could only construct a
probe for a subject it already knew. `signature()` over all eight criteria items
is byte-identical, sha `e39b41fe...`.

**`enforcement.py` is now at ZERO course-fact sites.**

### THE MOVE BROKE THE AUDIT, AND THE HARDENED GATE CAUGHT IT

`ALIAS` maps a name to EITHER one alternative (a string) or several (a tuple),
and **JSON has no tuple**: `("baseline", "baseline_data")` returned as a list and
`cand in web_keys` died with `TypeError: unhashable type: 'list'`.

Two things this proves, both worth more than the move:

1. **The gate refused instead of passing.** It printed *"the enforcement audit did
   not COMPLETE, so 'no findings' means nothing"* -- the hardening added earlier
   the same day, arriving within hours of being written. Before it, a crashed
   audit read as a clean one.
2. **The equality check that should have caught it was blind.** It compared with
   `json.dumps(..., default=str)`, which serialises a tuple and a list
   IDENTICALLY -- so it reported the tables identical while the types changed
   underneath. `segment._markers` records the same rule for the same reason:
   *"Tuples, not the lists JSON gives back ... a reader should not change a
   published shape while moving where it is stored."*

`_course_vocab` now restores tuple values, and the comparison preserves types.

### The six that remain need the PLUGIN CONTRACT to grow

| site | what it is |
|---|---|
| `score.py:1414` | composes this course's criteria PROMPT SECTION (`consequence_slot=`, `avoidance_scores=`) |
| `score.py:1766,1771` | emits `avoidance_frame` as an output RECORD FIELD |
| `measured.py:3550` | `_P._element(item, "observed_type")` |

All three are "what a scorer contributes BACK" -- a prompt section and extra
record fields -- which the contract expresses nowhere. That is a design step, not
a move, and it belongs with the vocabulary convergence rather than before it.

## The distinction, because two questions were being conflated

**Where a fact name is LEGITIMATE.** Under M's design the facts are DECLARED BY
THE COURSE in its rubric. A behaviour-modification course calling a fact
`targets_intended_behavior` is correct -- that is its subject matter, in its own
file. `course_metadata/scorers/oc.py` naming them is equally correct: it is the
course's scorer.

**Where it is NOT.** `enforcement`, `goals`, `score`, `measured` and
`precommit_gate` are ENGINE. Naming `avoidance_frame` in their code is the same
defect class as `bmod_handout1` in J-7b: a second course meets an engine that
already knows this course's psychology.

**`scorer_criteria.py` is the proof the boundary can hold.** It names
`cadence_ok` ONCE, in a docstring explaining why `apply_fact_gate` exists, and
has ZERO course tokens in code -- verified with docstrings stripped. That is
H(4)'s own test, the one it applied to `docx_text.py`: *"named as the REASON ...
not as an assumption the code makes."*

## Why this changes the vocabulary work rather than following it

A better-sounding name does not fix this. Renaming `cadence_ok` to something
subject-neutral would still leave the engine KNOWING A FACT NAME AT ALL, which is
the actual defect. What those five modules should ask is the rubric -- "which
facts does this item declare?" -- exactly as `scorer_criteria` does.

So **converging the two vocabularies and removing them from engine code are one
job**. Doing the rename first would touch all ten names twice, and would move the
item-specificity out while leaving the subject-specificity sitting in the engine
-- which is precisely what the user heard in the name.

## DECIDED: the converged names are the COURSE'S choice

Once the engine no longer names them, what they are called is the course's
business, and this plan should stop legislating it. The constraint that remains
is structural, not lexical: ONE name per fact across both engines, and no
item-specificity in the name (`cadence_is_daily` vs `cadence_is_daily_counted`
for two items that are both daily is the shape J-7b removed).

*Sequencing:* P before the rename, and both before the 960-cell re-sweep, so the
sweep is spent once on a settled vocabulary.

### O · IS THE PYTHON WEB SCORER STILL NECESSARY? (filed 2026-09-24, CONSIDER LAST)

Raised by the user while M-3 was in progress, and it follows directly from M step
4. To be taken up LAST, after M, because the answer depends on M's outcome and
because this is the measurement apparatus the whole project has been judged by.

**The question.** `agreement.py` drives the OLX prompts from Python -- the
`python` column of the ledger (`olx_python` in `measured.SIDE_CONTRACT`), as
distinct from `olx` (the web app) and `paper`/`paper_opus` (`score.py`). Its OC
half, `score_oc` / `score_oc_cadence`, is a HAND-WRITTEN MIRROR of
`derive_oc_ledger`. If M step 4 GENERATES that mirror from the same declarations
the paper scorer interprets, the mirror can no longer drift -- and a copy that
cannot drift raises the question of why there are two.

**What it would retire if the answer is no.** `enforcement.py`'s three-way
source-reading comparison, which goal E had to preserve with unusual care and
which sprang its vacuity trap once during E: the wrapper that made
`check_selectors_govern_something` grep 112 characters instead of 13,424 and
report nothing. A check that exists to catch drift between two implementations is
dead weight once there is one implementation.

**What it would COST, and this is why it goes last.**

* **A ledger column.** `python` is one of four sides, and the cross-path
  comparison `olx` vs `python` is what separates a PROMPT difference from a MODEL
  difference. Losing it does not just remove a scorer; it removes the ability to
  ask that question of any future change.
* **The measurement history.** Every recorded cell was measured against these
  sides. Retiring one does not invalidate the record, but it does mean no future
  sweep can be compared against the old one on that axis.
* **`agreement_app.py`** is the human review surface and reads the same path.

**What would have to be true first**, none of which is true today:

1. M step 4 lands -- the mirror is generated, not written.
2. The OLX path is genuinely pure (M's "pure OLX" end state), so `olx` alone
   answers what `olx` and `python` together answer now.
3. Someone states what the `olx`-vs-`python` comparison is FOR in the future, and
   whether any open question still needs it. If the answer is "nothing since
   2026-09", that is evidence; if it is "the next prompt change", it stays.

**Do not treat this as a cleanup.** It is a decision about what the project can
still measure, and the honest default is that a measurement axis stays until
someone can say what it is no longer needed for.

### L · `$COURSE_DATA` AND `$COURSE_METADATA` ON SHARED STORAGE

Raised by the user 2026-09-24, to be taken up AFTER K. `$COURSE_DATA` cannot go
in a repository and everyone on the project needs it. There is a Drive folder
holding the raw original materials:
https://drive.google.com/drive/folders/1JMqB0-XOCm1uY3k3Ww-IPcPo8ag04kDe

CAN IT BE READ PROGRAMMATICALLY? YES, by MOUNTING rather than by API. Every
reader here uses ordinary `open()` against a path that already resolves through
`paths.DATA` and an environment variable -- so a Drive-for-Desktop or `rclone`
mount needs NO code change at all: `COURSE_DATA=/mnt/drive/molly_data` and the
package is pointed at it. Going through the Drive API instead would mean
rewriting every read behind a client, which is a different and much larger job
for no gain over a mount.

## `$COURSE_METADATA` MOVES TOO (user, 2026-09-24)

L was written about `$COURSE_DATA` alone. The user's instruction widens it: the
metadata root is **also** to live in the shared private location. Both roots
move; they stay SEPARATE roots that happen to share a home, which is not the same
as merging metadata into `$COURSE_DATA`.

After J and N, `$COURSE_METADATA` holds four files and they are not alike:

| | what it is | consequence of mounting it |
|---|---|---|
| `course.json` | the course file | read at IMPORT by everything; a slow or absent mount stops the engine starting, not just a run |
| `CHANGELOG.md` | this course's incident record | ordinary document |
| `scorers/oc.py` | the OC scorer (goal E) | **executable code, imported at run time** |
| `fixture/course_segment.py` | this course's segmentation hook | **executable code** |

**TWO OF THE FOUR ARE CODE, AND THAT IS NEW SINCE L WAS WRITTEN.** Goal E moved
the scorer here and goal N moved the segmentation hook here, so mounting this
root means the engine IMPORTS PYTHON FROM SHARED STORAGE. That is a different
risk from reading documents:

* **Trust.** Anyone who can write the share can change what the scorer computes.
  `$COURSE_DATA` holds inputs; this holds behaviour. The four things L already
  measures -- latency, locking, partial reads, who can read it -- need a FIFTH:
  who may WRITE executable code there, which is not the same question as who may
  read students' words.
* **Import semantics.** `scorers._course_scorer` loads by file path and caches in
  `sys.modules`; a file that changes mid-session is not re-read. On a local disk
  that is a non-issue; on a synced mount a file can change under a running
  process.
* **The audit follows it.** `editguard.modules()` now globs
  `COURSE_METADATA/scorers/*.py` (widened during E, for exactly the reason that
  moving code out of the package took it out of the inventory). Mounting the root
  puts the definition ledger's own inputs on the share, so an unavailable mount
  makes the guard report definitions VANISHED rather than report nothing.

*Option worth weighing when L is taken up:* keep the two CODE files in the
repository and move only `course.json` and `CHANGELOG.md`. That splits on the
same line N and E already drew -- data and declarations travel, executable
machinery stays where it can be reviewed and version-controlled -- and it is the
distinction the fixture decision of 2026-09-23 made for the same reason
("executable machinery with an audit attached"). The user's instruction is to
move the directory; this records what moving the code half costs, so the choice
is made knowingly rather than discovered later.

FOUR THINGS TO MEASURE BEFORE COMMITTING, each a real risk here rather than a
generic caveat:

  1. SIZE. `out/` is 1.6 GB across 827 entries. A sync that pulls it all is slow;
     a streaming mount makes every ledger read a network round trip.
  2. MTIME. Four modules already decide freshness by modification time --
     `jsoncache`, `shape_inventory`, `goals`, `cross_path` -- and the audit's
     build-freshness checks compare "older than the newest .olx". Sync tools
     rewrite mtimes on their own schedule, so a cache could serve stale content
     or a check could fire for no reason. This is the failure most likely to be
     silent.
  3. CONCURRENT APPEND. `OVERRIDES.md` is machine-appended, and Drive resolves a
     write conflict by KEEPING BOTH as "file (1).md". Two people running the gate
     at once would not collide loudly; the log would quietly split in two.
  4. WHO CAN READ IT. `corpus_refs.json` and the submissions hold student
     writing. Moving them to shared storage is a DISCLOSURE decision about who
     may read students' words, not a storage decision, and it is the one part of
     this that no measurement settles.

A HYBRID IS LIKELY THE ANSWER: gold, the rubric-side records and the small
ledgers are the things people actually need to share, and they are megabytes.
`out/` is bulk run artifacts that only the machine that produced them reads.
Splitting on that line gets the sharing without the 1.6 GB or most of the mtime
exposure -- but it should be decided against a measurement of what is actually
read by more than one person, not by this paragraph.

#### THE MODULE AUDIT J AND K BOTH WAIT ON -- first pass, 2026-09-24

J says it plainly: "a repository split without such a list would carry the
course-specific parts along with it and call them generic by relocation." K needs
the same list to know what may leave python. This is the first pass.

**THE FIXTURE'S COURSE HALF COMES WITH IT** (user, 2026-09-24). L had this gap:
it discusses who may READ student data but never said that
`course_metadata/fixture/` currently holds ~1.3 MB of student-derived records --
`CONSENSUS_SPANS.json` is keyed `item/participant` -- inside a REPOSITORY. Goal N
separates the generic machinery from the course-specific implementation; what
remains of the course half is `$COURSE_DATA` material and moves with everything
else L is placing. See N's "Where the course half goes". N must therefore be
settled before L's inventory of what lives on shared storage is complete.

ALREADY SETTLED by goal H, by reading: six tools (maintain the tree), three
fixture modules (segment, fixture_edits, grader_inputs -- the shape is in the
logic), and six more read and placed elsewhere (docx_text and paper_runs generic,
prose_split tooling, three migrations).

THIRTY REMAIN, and a scan of LIVE CODE -- not comments -- for the course's shape
finds it in FIVE:

    cross_path.py           if h == 3:
    rubric_equivalence.py   for h in (1, 2, 3)
    rubric_export.py        for handout in (1, 2, 3)
    self_graded_misses.py   if handout == 3:  and  for h in (1, 2, 3)
    sweep_readout.py        for h in (1, 2, 3)   (three sites)

AND ALL FIVE ARE THE USER'S THIRD VERDICT, not the second: course-specific NOW,
but they OUGHT to be generic, so the action is a REVISION rather than a
relocation. The evidence is that a source of truth already exists --
`handouts.HANDOUTS` is keyed 1/2/3 and the course file declares the same set --
so `(1, 2, 3)` is a literal standing in for a list the course could supply.
Replacing it is small and makes each module meet a four-handout course unedited.

THE OTHER 25 SHOW NO SHAPE ASSUMPTION IN LIVE CODE, and that is EVIDENCE RATHER
THAN PROOF -- goal H is explicit that absence of a literal is weak, and the
fixture modules scanned clean on ids while being tuned to these documents. What
it does establish is where the remaining reading should go: five modules with a
known defect and a known fix, and twenty-five that need the control-flow question
asked one at a time before anything is promised about them.

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

### N · `segment.py` is ENGINE MACHINERY living in COURSE territory

**Filed 2026-09-24, found by pointing the stub at its own `COURSE_METADATA`.
The user's instruction: fix this BEFORE M.**

Every other finding in this plan is course-specific code sitting in the engine.
This is the INVERSE, and it is why it went unnoticed: generic machinery sitting
in the course, where the engine reaches in to import it.

`$COURSE_METADATA/fixture/segment.py` is **413 lines, of which ~20 (4%) are
course-specific** -- `utb_hint` (20 lines, and "UTB" is this course's vocabulary)
plus the three `H1/H2/H3_MARKERS` aliases. The other 96% is subject-neutral
document segmentation:

    clean  norm  strip_orphan_head  template_index  strip_template_prefix
    _is_boilerplate  segment (119 lines)  repair_orphans (31 lines)

`_markers` and `_handout_items` already read the COURSE FILE, so the mechanism
for keeping the course half out is built and working -- it was simply never
applied to the module's location.

## Seven engine modules import it from the course

    agreement.py  agreement_app.py  handouts.py  q6_consensus.py
    score.py      score_h1.py       simulate_h3.py

`handouts.py:29` is the sharpest: `from segment import H1_MARKERS, H2_MARKERS,
H3_MARKERS` -- the ENGINE importing three per-handout names from the COURSE, the
same course-shaped coupling J-7b removed for file stems, one level worse because
it crosses the boundary in the wrong direction.

## What it costs, measured

**A second course cannot be scored without shipping a copy of 413 lines of
generic segmentation.** The stub proved it: with `COURSE_METADATA` pointed at the
stub, `import handouts` dies with `ModuleNotFoundError: No module named
'segment'` before any scoring can begin.

**And until then the stub silently BORROWS this course's.** That is the J-4c
class again -- it was invisible for as long as `COURSE_METADATA` defaulted to
this repo, which is to say every run before this one. The stub's E step 3 run had
to keep `COURSE_FIXTURE` pointed at this course's fixture to isolate the scorer
question; that leak is still open.

## The rest of the fixture, enumerated

Not only `segment.py`, so the fix is not "move one file":

| file | lines | what it is |
|---|---:|---|
| `segment.py` | 413 | 96% generic; imported by SEVEN engine modules |
| `grader_inputs.py` | 472 | imported by `enforcement.py` |
| `fixture_edits.py` | 271 | imported by `agreement_app.py` |
| `*.json` (4 files) | -- | genuine course DATA; stays |

The three `.py` files are 1,156 lines total. The `.json` files are course data and
belong exactly where they are -- this finding is about CODE in the fixture, not
about the fixture existing.

## N-1 vs the 2026-09-23 judgement: the premise changed, the judgement did not

**H(4) read `segment.py` module by module and called it FIXTURE** -- "the shape
is in the logic: Handout 1's template carries a worked fruit-flavored water
example and Handout 3's carries an example data table AND an example graph. It
would not meet a different handout unedited." N-1 moves it to the engine, which
is the opposite disposition, so the disagreement is recorded rather than quietly
resolved in the newer entry's favour.

**That judgement was right when it was made, and its premise has since been
removed by another goal.** `segment.py` then held the markers and item lists as
LITERALS; the module's own comment records the change -- *"`H1_ITEMS` was a
literal `["Q1", "Q2", ...]` ... Verified equal for all three handouts before the
literals were removed."* Once the tables moved to the course file and `_markers`
/ `_handout_items` became READERS, the coupling H(4) identified was gone.

Measured today, with comments and docstrings stripped: **157 lines of code and
ZERO course-specific tokens** -- no `fruit`, no `EXAMPLE OF`, no handout number,
no item id. What remained was `utb_hint` and the aliases, and N-1 moved those to
`course_segment.py`.

**The course-specificity that made H(4) right is now entirely in the PROSE.** The
docstrings carry this course's evidence -- handout 3 item 3's punctuation, "47
boxes across 13 items", a corpus reference -- explaining why a generic regex
exists. That is provenance worth keeping, and it is not a coupling: a docstring
naming the case that motivated a rule does not make the rule specific to it. The
same distinction H(4) itself drew for `docx_text.py`: *"Item 1c is named as the
REASON chart parts are extracted, not as an assumption the code makes."*

**N-1 also settles the structural question H(4) left open.** It observed that
`$COURSE_LOCATION` sits inside the CONTENT tree, which `build:stage-content`
copies wholesale, so `import segment` would resolve through a content directory
-- "a python import path running through content". Moving the machinery to
`scoring/` removes that path entirely rather than relocating it.

## N-1 DONE (2026-09-24): `segment.py` split, gate clean at 44, set identical

`scoring/segment.py` is the engine's now -- 407 lines, nothing in it naming a
handout number or a subject. `course_metadata/fixture/course_segment.py` keeps
the 74 lines that are about THIS COURSE: `utb_hint`, which hardcodes the four
target behaviours, and the per-handout aliases whose value is the REASONING in
the comments around them.

**Proved by a segmentation fingerprint over the whole real corpus** -- every
handout, every participant, `{item: student text}` hashed. Deterministic and
file-driven, so no sampling and no model. sha256 `c990b59d...` before and after,
and `HANDOUTS` still identical to its pre-J-4 baseline.

Three things beyond the move:

1. **`handouts.py` stopped importing `H1/H2/H3_MARKERS`** and asks `_markers(h)`,
   which reads the course file where they always came from. Three per-handout
   names crossed the boundary in the wrong direction, and a FOURTH handout could
   not be expressed at all.
2. **`segment()`'s default is gone.** It was `markers = markers or H1_MARKERS` --
   silently substituting this course's handout 1. The record says what that cost:
   four bare `segment()` calls "judged fixtures against text no scorer ever
   sees", and "every accusation that followed was false" (D2/p19, 1c/p11,
   1c/p20 reported for text no student wrote). It now REFUSES.
3. **`utb_hint` is an optional HOOK**, via `segment.course_hook`. Importing it
   from the course meant a course shipping no such helper could not import the
   engine at all. Deliberately NOT a registry like `scorers`: a scorer is
   required once an item names one and its absence must refuse; a hint nobody
   supplies costs nothing.

**N's completion test PASSES**: the stub scores end to end with `COURSE_METADATA`
AND `COURSE_FIXTURE` both pointed at itself, borrowing nothing. An empty
`fixture/` directory sufficed, which is the measure of how much of that directory
was never the course's.

### Two checks fired on the move, and both were right

* `migrated_tables` read `HANDOUTS` as a migrated table demanding an authored
  twin, because `_markers` is in `READER_CALLS` and the call sat INSIDE the table
  literal. Moved into the assembly step beside every other course-sourced field.
  That check's own comment records the same confusion from an earlier move.
* A plan edit cited a developer's private notes by wiki-link. There is a check
  for that, and it is right: a document in this repository must not point at
  something only one person can read.

## THE $COURSE_DATA QUESTION FOR FIXTURE DATA: SETTLED (2026-09-24)

Settled on the user's instruction to settle it before M, and settled by
MEASURING rather than by declaring a policy.

**What moved, and where it ended:**

| | |
|---|---|
| `CONSENSUS_SPANS.json` | `$COURSE_DATA/courses/<ns>/fixture/` -- the only participant-keyed record |
| `GRADER_INPUTS.json` | `scoring/` -- platform evidence, **no participant ids in it** |
| `PROSE_SPLIT_WORKSHEET.json`, `STRUCTURE_KIDS.json` | `scoring/drafts/` -- planning for a future generic capability |
| `fixture_edits.py`, `grader_inputs.py` | `scoring/` -- generic control flow |
| `course_segment.py` | stays: the ONLY file left in `course_metadata/fixture/` |

`paths.COURSE_FIXTURE_DATA` names the data root, separately from
`COURSE_FIXTURE`, which now holds code and no data at all.

**The repository holds NO inline student text.** Measured with the project's own
classifier (`precommit_gate._classifier` + `_quotes`), across all nine files the
budget names, in BOTH the dry-run and the live tree: every count is 0. The scrub
replaced quoted sentences with `{{corpus:...}}` references that resolve against
`$COURSE_DATA`, which is why the 44 standing findings are all "OLX QUOTES A
STUDENT THROUGH A REFERENCE" and none is "quotes a student directly".

**A uniform zero was not taken at face value.** Two accessor traps came first:
`_staged_counts()` reads the GIT INDEX, so in a non-git tree it reports 0 for
everything and would have "proved" anything; and the classifier itself was
positive-controlled against a real student span (classified student: True) and a
engine sentence (False) before the zeros were believed.

### The budget was 15 instances of pure slack, and is now 0

`STUDENT_TEXT_BUDGET.json` permitted 15 instances across 9 files. Two of those
files no longer exist; the other seven measure 0. **The gate only refuses GROWTH**
(`n > base.get(f, 0)`) and never tightens, so 15 sentences could have been
reintroduced silently -- into `GOALS.md`, `README.md`, `enforcement.py` -- and
the gate would have permitted every one.

That is contrary to the rule the codebase states about this very file: *"they may
fall and may not rise"*. Tightened to `{}`. A single reintroduced sentence now
REFUSES, verified. This is the same move the property ratchet required after E
(11 -> 9): an improvement that is only observed can be undone, and one that is
recorded cannot.

## N-2 DONE (2026-09-24): the rest of the fixture, dispositioned and moved

`course_metadata/fixture/` now holds ONE file, `course_segment.py`. That was the
test proposed for whether the split was cut in the right place, and it holds.

### The two remaining modules went to the ENGINE, reversing H(4) knowingly

`fixture_edits.py` and `grader_inputs.py` were read against the genericity test
-- what the CONTROL FLOW assumes, not what the prose names:

* **`fixture_edits.py`**: spans, SHA verification, engine accessors. Its only
  course token is `handout`, read as a DECLARED FIELD
  (`_jobs()[item]["handout"]`), never a literal. H(4) called it FIXTURE for
  "corrections as spans over THIS corpus" -- which is about the DATA, and that
  data is now in `$COURSE_DATA`. Same shape as its `segment.py` call: right about
  the material at the time, describing the subject rather than the control flow.
* **`grader_inputs.py`**: `GRADER_INPUTS` is keyed by LO-BLOCKS GRADER CLASS
  NAMES -- 19 of them -- and exists because *"no grader declares the inputs it
  pairs with"*, a fact about the platform, true for every course. `mine(roots,
  inventory)` takes roots as a PARAMETER. Its three `psych` mentions are evidence
  provenance in prose, which is H(4)'s own `docx_text.py` distinction: *"named as
  the REASON ... not as an assumption the code makes."*

`GRADER_INPUTS.json` went with it: checked, and it carries NO participant ids.

### Verified firing, not merely passing

|  | before | after |
|---|---|---|
| `fixture_edits.py --verify` | 102 spans, 0 broken | same |
| `grader_inputs.py` | declaration and evidence agree both ways | same |
| `check_grader_input_pairings_are_declared` | 0 findings | 0 findings |
| the same check with the table emptied | **fires, 60** | **fires, 60** |
| a span with a corrupted sha | -- | **fires**, SHA MISMATCH |

The second consumer needed its control fixed first: it called `scorer_evidence`
with the wrong signature and reported a `TypeError`, which proved nothing.
Exercised through the real path (`FE._sections` -> `FE.resolve`) it resolves 3/3
spans and refuses a corrupted one.

**A silent break was avoided by looking.** Both modules carried a `sys.path`
bootstrap walking THREE parents up and appending `"scoring"` -- correct from the
fixture, but from inside `scoring/` it lands outside the repo. It would have
failed only when run as a SCRIPT, so the checks would have kept passing while
both CLIs broke. Both now insert their own directory.

### The two planning worksheets

`PROSE_SPLIT_WORKSHEET.json` and `STRUCTURE_KIDS.json` are planning inputs for a
generic course-construction capability that does not exist yet (user,
2026-09-24), so they are in `scoring/drafts/` with a README. Both are on-demand
outputs -- `--json PATH` -- and nothing reads the checked-in copies. Two
classifications in `MATERIAL_CLASSIFICATION.md` were corrected: `STRUCTURE_KIDS`
was filed under "ratchets and frozen records" and is neither, and
`PROSE_SPLIT_WORKSHEET` was filed under "fixture programs" although H(4) had
already ruled its producer NOT a fixture program.

## Shape of the fix

1. Split `segment.py`: the 96% moves to the engine beside `docx_text.py`; the
   ~20 course-specific lines become either a course-supplied hook or
   declarations, the way `_markers` already is.
2. `handouts.py` stops importing `H1/H2/H3_MARKERS` by name. They are already
   derivable -- `_markers(h)` reads the course file -- so this is the J-3 move
   applied once more: ask for the property, not the numbered name.
3. Audit `grader_inputs.py` and `fixture_edits.py` the same way before moving
   either; neither has been measured for its generic share yet.
4. The completion test is the stub's: `COURSE_METADATA` and `COURSE_FIXTURE` both
   pointed at the stub, and the engine still scores it end to end.

## WHERE THE COURSE HALF GOES: `$COURSE_DATA`, not the repo

Raised by the user 2026-09-24, and it changes N's destination rather than only
its shape. **The fixture's course half is STUDENT-DERIVED, so it cannot stay in a
repository at all** -- splitting generic machinery out of `segment.py` and
leaving the rest in `course_metadata/fixture/` would only make the remainder
smaller, not correctly placed.

Measured, in the tree today:

| file | size | what it is |
|---|---:|---|
| `PROSE_SPLIT_WORKSHEET.json` | 1.2 MB | keyed by document, references p1-p20 |
| `CONSENSUS_SPANS.json` | 8 KB | **keyed `item/participant`** (`1c/p20`, `2a/p1`) |
| `STRUCTURE_KIDS.json` | 108 KB | structure evidence |
| `GRADER_INPUTS.json` | 20 KB | grader wiring |

`CONSENSUS_SPANS.json` holds span OFFSETS rather than prose -- checked, no
student sentences in it -- but it is keyed by participant and describes
individual answers, which makes it a record ABOUT students even where it does
not quote them. `$COURSE_DATA` is where the submissions and `corpus_refs.json`
already live for exactly this reason, and this is the same class of material one
step removed.

So N's split has THREE destinations, not two:

    generic machinery      -> the engine, beside `docx_text.py`
    course-specific CODE   -> the course's own scorers/hooks (repo is fine:
                              `utb_hint` names a concept, not a student)
    student-derived DATA   -> $COURSE_DATA, out of every repository

The third is the one that was not previously stated anywhere, and the one that
has to be settled BEFORE the split, because "where does the remainder live"
decides how the split is cut.

**Why before M.** M rewrites the criteria scorer and proves itself ON THE STUB
(M step 5). A stub that cannot run without borrowing this course's fixture cannot
prove anything about generality, so N is a precondition for M's own acceptance
test rather than a parallel tidy-up.

### M · Generalise the criteria scorer (filed 2026-09-24, not for today)

**Filed by the user while deciding E.** The plugin (E) puts the OC scorer behind
a registry so the engine stops knowing about operant conditioning. But it parks a
REUSABLE CAPABILITY inside a course-specific wrapper: what `derive_oc_ledger`
does is generic, and only what it does it TO is not.

This is the genericity test's THIRD VERDICT -- *course-specific now but ought to
be generic* -- which is a revision task, not a relocation. E and M are therefore
complementary, not alternatives: **E moves it out, M makes it reusable.** Doing E
first is right, because M is a big lift and E unblocks J.

## What is generic in it

A criteria scorer that:

1. asks the model for structured FACTS rather than judgements (the shape §3
   recommends: "a question about the SENTENCE has a procedure in it");
2. computes definitional GATES as conjunctions of those facts;
3. SHORT-CIRCUITS at the first definitional failure, so a rule below an unmet
   gate is never consulted -- which is why a control that already fails one gate
   makes everything under it invisible;
4. emits DEDUCTION CODES from the gate that failed;
5. returns `(ledger, checks, unknown, advisory)` -- with `unknown` and `advisory`
   distinguishing "could not tell" from "did not meet", which is the distinction
   the whole project keeps insisting on.

None of that is about behaviour modification. Any rubric asking *does this answer
instantiate concept X* has the same shape.

## What is course-specific in it

| | |
|---|---|
| the FACT VOCABULARY | 14 answer fields: `behavior`, `stimulus`, `contingent`, `follows_behavior`, `stimulus_is_arranged`, `observed_type`, `named_type`, `stimulus_move`, `targets_own_behavior`, `targets_intended_behavior`, `restriction_authored`, `consequence_asserted`, `avoidance_frame`, `cadence_ok` |
| the GATE STRUCTURE | which conjunctions constitute "is an instance" |
| the TYPE TAXONOMY | PR / NR / PP / NP and the moves between them |

## The path is half-built already

`derive_oc_ledger` reads SIX fields from the item -- `oc_gates`, `expected_type`,
`cadence`, `avoidance_scores`, `deductions`, `id` -- so the gates are ALREADY
partly declared, and `OC_GATES` is already in `coursedata.DERIVATIONS`. The rubric
also already carries `<Forbid>`, `<Onlyif>`, `<Requires>`, `<Equals>`, `<Expect>`
primitives, which express exactly the conjunctions this logic hardcodes.

So M is not "write a new engine". It is: finish moving the gate structure and the
fact vocabulary into declarations the rubric already has shapes for, until what
remains is a subject-neutral interpreter.

## Why it is a big lift anyway

* **The 14 fact fields are a SCHEMA the model answers**, so changing how they are
  declared changes every prompt on the 8 criteria items -- a measured change, not
  a refactor. Every step needs a sweep.
* **`agreement.score_oc` / `score_oc_cadence` are hand-written MIRRORS** of this
  logic on the web side, and `enforcement.py:4334` compares them by reading
  source. Generalising one side without the other breaks the comparison the
  project rests on; generalising both doubles the work.
* **The short-circuit ORDER is load-bearing** and currently implicit in Python
  control flow. Declaring it means declaring precedence, which the rubric has no
  shape for yet.
* It touches the most-measured code in the project. `derive_oc_ledger`'s
  behaviour is baked into the ledger for 8 items x 20 cells x 12 runs.

## The STUB is part of M (user, 2026-09-24)

Added after the stub scored end to end and its criteria item escalated. The stub
is where M's success is VISIBLE, because it is the only course in the tree with
no operant conditioning in it:

* Today S2 declares `derive_from_criteria`, `derive_oc_ledger` runs, and the
  hardcoded `NOT_OC` charge lands in `unknown` because the stub's rubric does not
  declare that code. The stub keeps full marks by accident, not by judgement.
* **Acceptance test for M:** the stub scores its criteria item through ITS OWN
  declared facts and gates, and a clean stub run reports `escalate: False`. That
  is a one-command check an outsider can run, and it fails today for exactly the
  reason M exists.
* When the fact vocabulary and gates move into the rubric (steps 1-2 below), the
  stub's `stub_rubric.olx` needs a `<Facts>` block and gates of its own -- two or
  three facts, not fourteen. `build_stub_course.py` is where they go, so the stub
  tracks the contract instead of drifting from it.

Do NOT relax this by declaring `NOT_OC` in the stub's rubric. That would silence
the signal while leaving the frame imposed, which is the opposite of the fix.

## M-1/M-2 DONE (2026-09-24): the generic interpreter exists and the STUB uses it

Gate clean at 44, set identical. `oc.py` UNTOUCHED and byte-identical to its
pre-E baseline (sha `1971e534...`, 51,200 cases, 3/3 controls firing).

`scoring/scorer_criteria.py` is the subject-neutral criteria scorer: it reads
FACTS and GATES from the rubric, short-circuits at the first failed gate in
DECLARATION ORDER, emits that gate's code, and returns the
`(ledger, checks, unknown, advisory)` contract. Registered as
`BUILTIN = {"criteria": "scorer_criteria"}` -- which is what goal E reserved that
table for when it emptied it: *"if the engine ever gains a genuinely
subject-neutral scorer, this is where it goes."*

**NO NEW VOCABULARY WAS INVENTED.** A course declares:

    <Slot key="answered" gate="true" charge="STUB_MISS" because="Nothing was answered."/>

which is exactly what `rubric_component` already parsed into `oc_gates` -- *"an
oc_gate is a SLOT THAT CHARGES, not merely one that gates"*. The declaration
shape M needed was already in the file; what was missing was something that read
it without knowing a subject.

**ORDER IS DECLARATION ORDER.** M records the short-circuit order as load-bearing
and "currently implicit in Python control flow". Here the rubric's own order is
the precedence, visible in the file a person edits.

### M step 5 -- the completion test -- IS MET

`scorers/stub.py` is deleted. The stub scores end to end with **no Python at
all**, which is step 5 verbatim: *"a second, trivial criteria scorer declared
entirely in a rubric, scoring the stub's one item, with no Python at all."*

    h1: S1 score=1.0 escalate=False unknown=[] deductions=[]
    h2: S2 score=0.0 escalate=False unknown=[] deductions=['STUB_MISS']

Compare the state this goal was filed in: `escalate=True`, `unknown=['NOT_OC']`,
and full marks kept BY ACCIDENT because the stub's rubric did not declare the
foreign code. The acceptance test in "The STUB is part of M" -- `escalate: False`
on a clean stub run, scoring through its OWN declared facts and gates -- passes,
and it passes without the shortcut that section warned against (declaring
`NOT_OC` in the stub's rubric, which "would silence the signal while leaving the
frame imposed").

### The limit, stated in the code rather than discovered later

The interpreter derives its facts FROM THE GATES. A rubric's non-gating `<Slot>`s
are served in the rubric view's `SLOT_SPEC`, keyed by item, NOT on the item dict
a scorer receives -- so it can only see a fact some gate reads. That is sound as
far as it goes (a fact no gate consults cannot change the ledger, so asking the
model for it would discard the answer), and it is why this is M-1/M-2 and not all
of M. `item.get("facts")` is honoured first, so an explicit declaration can land
later without that function changing again.

## M-3: what migrating OC actually requires, mapped

`derive_ledger`'s decision structure, read: **two of its gates are conjunctions
of booleans and the rest are not.**

| rule | shape | migratable today |
|---|---|---|
| `is_oc` -> NOT_OC | AND of 4 booleans | **yes** |
| `arranged` -> NOT_EXTERNAL_STIMULUS | 1 boolean | **yes** |
| the declared `oc_gates` loop | 1 boolean each | **already declared** |
| `observed != named` -> TYPE_MISMATCH | ENUM COMPARISON | no |
| cadence -> CADENCE_MISMATCH | enum + counted reading | no |
| `move_pick` -> WRONG_TYPE | enum over `stimulus_move` | no |
| avoidance -> NOT_OC / advisory | boolean + per-item SCORES table | no |

So M-3 is not one migration. The definitional half can move as soon as the
interpreter expresses an AND-of-facts gate; the typed and counted half needs a
declaration form for ENUM VOCABULARIES and their comparisons, which is the same
`SLOT_OPTIONS` access the limit above describes.

**Every step must hold the 51,200-case fingerprint byte-identical**, which is
what makes this tractable at all: the ledger is a pure function of `(item, raw)`,
so a migration either reproduces it exactly or is visibly wrong.

## M-3 IN PROGRESS (2026-09-24): five rules migrated, fingerprint held at every step

`oc.py` now runs five of its rules from `scorer_criteria`. The 51,200-case
fingerprint is sha `1971e534...` before the first migration and after the last --
checked between EVERY step, not once at the end, because a migration that
reproduces the ledger exactly is the only kind that is safe here.

| primitive | what moved | shape |
|---|---|---|
| `apply_declared_gates` | the `oc_gates` loop | declared booleans, short-circuit |
| `apply_conjunction_gate` | `is_oc` -> `NOT_OC`; `arranged` -> `NOT_EXTERNAL_STIMULUS` | AND of checks, short-circuit |
| `apply_charge` | `WRONG_BEHAVIOR`, `LINK_NOT_ASSERTED` | one check, NO short-circuit |

### Two corrections the code forced, and M's analysis was wrong about the second

1. **The interpreter had the wrong default for an absent fact.** It failed them;
   `oc.py` uses `a.get(key, True)` -- *"a gate the model was not asked cannot
   fail"*. Charging for a question nobody put is plainly wrong, and the OC
   default is the considered one. Found by reading `oc.py` BEFORE delegating to
   it. Now pinned by a three-way test: facts true -> no charge, false -> charge,
   ABSENT -> no charge.

2. **`WRONG_BEHAVIOR` and `LINK_NOT_ASSERTED` are not gates.** They look like
   single-boolean gates and this plan listed them as such. Both are
   `if not x: add(...)` with **no `return`** -- they charge and scoring
   continues, which their own comment states: *"charged additively alongside
   TYPE_MISMATCH and WRONG_BEHAVIOR, and in the same order as agreement.py's
   score_oc_cadence."* Migrating them as gates would have truncated every ledger
   that reached them.

   **This is a gap in M's own "what is generic" list**, which names
   short-circuiting and never names its opposite. GATES STOP; CHARGES ACCUMULATE.
   `apply_charge` exists to keep them apart, with the reasoning at the site.

## M-3b DONE (2026-09-24): the enum rules migrated, and two corrections to this plan

Gate clean at 44, set identical. OC fingerprint byte-identical at every step
(sha `1971e534...`). **Nine of `derive_ledger`'s rules now run from the
interpreter**; what is left is five charge sites whose CONDITIONS are one
course's, reached through shared primitives.

### The prerequisite, done first

Items now carry `slot_options` -- the answer menus their own slots name, attached
by `rubric_component` from the `<Choices>` the rubric already declared, and added
to `RUBRIC_FIELDS` so `course_schema` accepts the field. That keeps a scorer a
function of `(item, raw)`, which is what makes the ledger pure and the
fingerprint meaningful. Without it an enum comparison could only be hardcoded.

### Primitives now in `scorer_criteria`

| primitive | shape | sites |
|---|---|---|
| `charge` | look a code up; UNDECLARED -> `unknown`, charges nothing | 5 |
| `apply_declared_gates` | declared booleans, short-circuit | 2 |
| `apply_conjunction_gate` | AND of checks, lists the missing, short-circuit | 2 rules |
| `apply_charge` | one check, ADDITIVE | 2 |
| `apply_fact_gate` | gates on a fact that is not a recorded check | 1 |
| `apply_enum_mismatch` | two enums disagree; LENIENT values first-class | 1 |
| `forbid_hit` | the rubric's `forbid` conjunction | 2 |

### THIS PLAN WAS WRONG TWICE, and the corrections matter more than the migration

**1. "The type taxonomy is course-specific, so its rules stay."** That conflated
the TAXONOMY with the code that consults it. `REQUIRED_MOVE` is a declared course
table and `expected_type` a declared item field; looking a value up in one and
comparing is no more about operant conditioning than any other comparison. The
same distinction this plan drew correctly for the fact vocabulary, not applied
one level further in until the user asked whether it really held. It did not.

**2. `WRONG_BEHAVIOR` and `LINK_NOT_ASSERTED` are not gates** -- they charge
without returning. Migrating them as gates would have truncated every ledger
beneath them. M's "what is generic" list names short-circuiting and never names
its opposite: **GATES STOP; CHARGES ACCUMULATE.**

### And one primitive was BUILT AND THEN REMOVED

`meets_expectation(a, fact, want, fallback_fact, fallback_want)` lasted one
commit. One caller, and a signature encoding THAT rule's shape under a general
name -- which is worse than inline code, because a primitive advertises a
contract a second course can meet. Reverted, with the reasoning left at the site
so it is not helpfully re-extracted.

**The standard that fell out is not call-count.** `apply_conjunction_gate` has one
call site and serves two rules; `apply_fact_gate` and `apply_enum_mismatch` have
one each and fully general signatures. The test is: *does the signature
generalise, or does it encode one rule's shape?*

The same question retired a duplicate: `apply_charge` and `oc.py`'s local `add()`
both implemented "charge or report an undeclared code". That is the SUBTLE rule --
the silent drop that let the stub keep full marks by accident before E -- and two
copies of it agree until one is edited. `codes.get(` now appears ONCE in the
module.

### The primitives are tested against their contracts, not just their usage

`scorer_criteria.py --self-test`: **19 cases, all passing**, shipped with the
module for the reason `course_schema` gives about its own -- a check whose cases
live elsewhere is one nobody has watched fail. The fingerprint proves the OC
scorer's USAGE reproduces; it says nothing about an undeclared code, an absent
fact, a lenient value, or a charge that must not short-circuit, and those are
exactly what a second course would rely on.

Proven non-vacuous: breaking `charge` fails 7 cases, breaking `forbid_hit` fails
1.

## DECIDED (2026-09-24): `avoidance_scores` becomes NOTHING -- it is deleted

The rubric ALREADY declares the distinction it encodes, and declares it twice:

    DAY1                        <Slot key="phrased_directly_gate" ... gate="true"/>
    PR NR PP NP WK1 DAY2 WK2    <Slot key="phrased_directly"      ... (no gate)/>

DAY1 gates on an avoidance frame; every other criteria item treats it as
advisory. `avoidance_scores: true` -- declared on DAY1 and nowhere else -- is a
PYTHON-SIDE DUPLICATE of `gate="true"`, and `oc.py`'s own comment says why it had
to exist: *"DAY1 GATES on this, and the CLI must gate with it or the two
implementations score the same answer differently."* The flag was needed only
because a gate had no way to say WHICH CODE it charges, which the OLX engine's
new `charge`/`because` attributes now fix.

So the mapping is: put `charge="NOT_OC" because="The consequence is stated only
as something avoided."` on DAY1's gate slot, and delete the flag and the
hand-written block. `rubric_component` already collects gate-slots-that-charge
into `oc_gates`, and `apply_declared_gates` already handles them -- no new code.

### BLOCKER 2 ANSWERED (2026-09-24): the build invocation, inside the dry run

`materialiseRubrics` FOLLOWS SYMLINKS because "a content tree mounts other
repositories by symlink, and the plain form walks straight past a mounted course
and reports a clean zero". Neither `lo-blocks/content` -- dry-run OR live --
mounts the psych course, so `npm run build:expand-rubrics` was never how this
course's artifacts were made. The invocation is:

    ./node_modules/.bin/tsx packages/shared/scripts/materialiseRubrics.ts \
        --content <course root> --out .stage/expanded/<namespace>

Verified by building to a TEMP directory and comparing: the output is
BYTE-IDENTICAL to the staged artifact the scorer reads. The namespace level comes
from `--out`, not from the content tree. Second stage is
`resolveCorpusRefs --content .stage/expanded --out .stage/content --no-mount`.

**It is a pass-through today**: authored `bmod_rubric.olx` == staged, because
nothing uses `<ItemTemplate>` yet. So a rubric edit propagates by re-running the
above, entirely within the dry-run branch, touching no live tree.

### BLOCKER 1, PROPOSED SHAPE: two STAGES, not an ordering number

The avoidance gate must run AFTER the type rules; the declared-gates loop runs
before them. Rather than an arbitrary precedence integer, declare the KIND of
gate, which is what the code's two positions already mean:

    gate="true"    definitional -- is this an instance at all?   (early, today)
    gate="final"   presentational -- how is it phrased?          (late)

`apply_declared_gates(item, a, checks, codes, stage=...)` filters by stage and
`oc.py` calls it twice, once at each existing position. Order WITHIN a stage
stays declaration order. This reproduces today's behaviour exactly -- avoidance
is the only late gate -- so the 51,200-case fingerprint verifies it rather than a
reviewer having to reason about it.

### TWO BLOCKERS, both real, neither worked around

**1. ORDER. This is M's undeclared-precedence gap, arriving.** The hand-written
avoidance charge is the LAST rule in `derive_ledger` (line ~250); the declared-
gates loop runs at line ~140, with `LINK_NOT_ASSERTED` between them. Moving the
charge into the loop moves it earlier, so a DAY1 cell that is both
avoidance-framed and missing its asserted link would charge a different code.
M records this exactly: *"the short-circuit ORDER is load-bearing and currently
implicit in Python control flow. Declaring it means declaring precedence, which
the rubric has no shape for yet."* This is the case that forces it.

**2. THE BUILD PATH IS NOT REACHABLE IN THIS TREE.** The scorer reads BUILD
PRODUCTS -- `as_view_items` from `.stage/expanded/<ns>/psychology/`,
`as_view_slot_spec` from `.stage/content/` -- produced by
`npm run build:expand-rubrics`, which runs `materialiseRubrics --content
./content`. In this dry-run `lo-blocks/content` holds only `demos/`: the psych
rubric is not reachable from it. So an edit to the authored
`psychology/bmod_rubric.olx` cannot be propagated to the artifacts the scorer
actually reads, and running the build as documented would regenerate nothing for
this course rather than fail loudly. **Not worked around**: guessing an
invocation against the artifacts the scorer depends on is how a tree gets
silently corrupted.

## TWO-STAGE GATES DONE; THE MAPPING IS BLOCKED ON ONE VOCABULARY (2026-09-24)

**Done, byte-identical:** a gate declares its stage -- `gate="true"`
definitional, `gate="final"` presentational -- `rubric_component` carries it,
`apply_declared_gates(..., stage=...)` filters, and `oc.py` calls the loop twice,
at the two positions its control flow already used. An entry with no stage is
definitional, so nothing written before this behaves differently. Fingerprint
`1971e534...` unchanged; self-test 19/19.

**Then the mapping stopped, and the reason is the finding.** The two engines ASK
DIFFERENT QUESTIONS for the same concepts:

| concept | paper asks | web asks |
|---|---|---|
| behaviour named | `behavior` | `names_behavior` |
| stimulus named | `stimulus` | `names_stimulus` |
| arranged | `stimulus_is_arranged` | `you_arrange_it` |
| avoidance | `avoidance_frame` | `phrased_directly_gate` (INVERTED) |
| cadence | `cadence_ok` | `cadence_is_daily` |
| type match | computed | `matches_chosen_type` |

Declaring the avoidance gate on the web's `phrased_directly_gate` makes the paper
scorer read a fact it never asks: `a.get("phrased_directly_gate", True)` is
absent, so the gate silently never fires -- the ledger would look unchanged while
the rule stopped existing. The alternative, declaring it on `avoidance_frame`,
leaves the WEB unable to read it and inverts the sense.

**So the last five rules cannot be mapped onto shared declarations until the two
FACT VOCABULARIES are reconciled into one.** That is M step 1 done properly --
"declare the FACT VOCABULARY in the rubric" -- and it is a MEASURED change, not a
refactor: it alters what the model is asked on all eight criteria items, so it
needs a sweep and cannot be proved by the fingerprint. The fingerprint proves the
ledger is unchanged for a GIVEN answer; it cannot prove the answers stay the same
when the question changes.

*What this does not block:* the two-stage machinery, the coded deductions in the
OLX engine, and the nine rules already migrated all stand, and none of them
changes a prompt.

## THE CONSOLIDATION IS WITHDRAWN (user, 2026-09-24) -- THE ALIAS ALREADY IS IT

**Withdrawn before it was built, on the user's question: "I thought we had
already decided that courses name their slots?"** They had, and goal P delivered
it -- the engine is at zero. The consolidation below would then have rewritten
COURSE-AUTHORED TEACHING PROSE to satisfy an engine-side convenience, which is
the opposite of what P established.

**And it was never needed.** The blocker was that the declared rules name the
WEB's slots (`phrased_directly_gate`, `targets_goal_behavior`,
`demonstrates_type`) while the paper scorer asks its own. `SIDE_ALIAS` -- which
P had just moved INTO the course file, and which carries `SIDE_INVERTED` beside
it -- maps every one of them:

    phrased_directly_gate     -> avoidance_frame            (INVERTED, declared)
    targets_goal_behavior     -> targets_intended_behavior
    demonstrates_type         -> stimulus_move
    barrier_is_not_this_type  -> already shared / computed
    consequence_not_a_setup   -> already shared / computed

So the last five rules map by RESOLVING OPERANDS THROUGH THE ALIAS, and nothing
about what the model is asked changes.

### What that cancels

| was planned | now |
|---|---|
| ~90 prose edits in `bmod_rubric.olx` and `bmod_handout2.olx` | none |
| a 2,068-cell RE-SWEEP | none for the rename |
| the `behavior`/`stimulus` judgement over 275 prose sites | none |
| a changed `criteria_slice.json` golden | unchanged |

The 26 provenance findings still need one re-sweep, for the `slotSheet.ts` hash;
that is a different and smaller debt.

### What it cost to find, and what nearly happened

The rename was measured before it was applied, which is the only reason it was
caught. The counts showed the fact names live in AUTHORED PROSE -- *"5.
`stimulus_is_arranged` -- is the consequence something the student arranges"* --
and that `behavior` appears 113 times in the rubric, overwhelmingly as the
ENGLISH WORD rather than the fact name. A substitution rename would have mangled
the teaching text; a careful one meant judging 275 sites, which is the
mention-versus-use error that had already produced three wrong figures that day,
at ten times the scale.

**The decision that actually mattered was made earlier and not followed
through:** once the course names its slots, two names for one fact is the
COURSE's business, and the engine's job is to resolve them -- which is what the
alias is for, and why moving it into the course file was the right move rather
than an incidental one.

*The vocabulary table below is kept as the record of what was decided and why it
was not needed. It is NOT a plan.*

## THE CONVERGED FACT VOCABULARY (decided 2026-09-24, SUPERSEDED -- see above)

Verified first: the two sides DO converge. The same five paper facts and six web
facts diverge on ALL EIGHT criteria items -- identical every time, which is
itself evidence they describe one thing rather than two.

User's decisions: **the web's slot starts asking for TEXT**, and **generic names
beat item-specific ones, however that shakes out.** That resolves every case:

| concept | converged name | from | why |
|---|---|---|---|
| behaviour named | `names_behavior`, TEXT-BEARING | web | web's name, paper's evidence |
| stimulus named | `names_stimulus`, TEXT-BEARING | web | same |
| arranged | `you_arrange_it` | web | pure rename |
| avoidance | `phrased_directly` | web | inversion handled at the gate |
| cadence | `cadence_ok` | **paper** | generic beats `cadence_is_daily` / `_weekly` / `_daily_counted` |
| targets | `targets_intended_behavior` | **paper** | generic beats `targets_goal_behavior` / `targets_unwanted_behavior` |
| confidence | `confident` | web | web-only, no paper counterpart |

The two that keep the PAPER's name are the two where the web encodes the item in
the FACT NAME. It is not even derivable: DAY1 and DAY2 are BOTH daily, and use
`cadence_is_daily` and `cadence_is_daily_counted`. That is the `bmod_handout1`
shape -- an item's identity inside a name -- which J-7b spent a day removing.

## THE COST: 2,068 CELLS BECOME HISTORICAL, AND MUST BE RE-SWEPT NOT RESCORED

Measured: **2,068 of 9,628 recorded cells, across all eight criteria items**,
carry a verdict keyed by a name this rename retires.

    olx          3120 recorded    960 affected
    python       3268 recorded   1108 affected
    paper        3120 recorded      0
    paper_opus    120 recorded      0

**THE FIRST COUNT SAID 960 AND WAS WRONG BY MORE THAN HALF.** It scanned for
`verdicts` and `slots` -- the OLX shape -- and the python side stores `checks`
and `answers`, so it reported ZERO affected on a side that drives the same OLX
prompts. It read as "python is unaffected" when it meant "wrong accessor". One
whole side coming back clean is never a data finding; it is the tell for reading
the wrong key, and it cost a figure that had already been written into this plan.

**They cannot be migrated, and should not be.** `migrate_verdicts.py` renames
over the RUBRIC and states the rule this falls under: *"a rewrite that would
change what the model is asked does not get written; it gets reported."*
Rewriting a recorded verdict's KEY would claim the model was asked
`cadence_ok` when it was asked `cadence_is_daily`. That is falsifying the record,
and this project keeps superseded measurements precisely because "a fault
superseded by a later sweep stays true of what was recorded".

So the eight criteria items need a RE-SWEEP -- new model calls -- not a rescore.
A rescore replays recorded answers; this changes the question, so there are no
answers to replay. Budget it as 960 cells, and expect the ledger's history on
those items to end at this line rather than continue through it.

## O COMES BEFORE THE RE-SWEEP (user, 2026-09-24)

The user's sequencing, and the numbers back it: **the python side is 1,108 of the
2,068 cells -- 53% of the re-sweep.** If it can validly be retired, the sweep is
halved, and there is no sense in spending model calls re-measuring a column that
is about to be deleted.

The rationale is not only economic. **The python web scorer only ever existed as
a CROSSCHECK** -- `olx_python` against `olx_app`, separating a prompt difference
from a model difference. After P (the engine stops naming this course's facts)
and M step 4 (the mirror is GENERATED from the declarations rather than
hand-written), the two sides cannot drift by construction, and a crosscheck
between implementations that cannot differ is measuring nothing.

So the order is: **P -> vocabulary convergence -> the last five rules -> generate
the mirror -> O -> ONE re-sweep**, of whatever columns survive O.

O's own entry lists three things that must be true first; the mirror being
generated is the one that does the work, and it is now scheduled before O rather
than after.

**This is the first step in the whole migration that cannot be proved by the
fingerprint.** Everything else -- E's five steps, M's nine rules, the two-stage
gates, the OLX engine's coded deductions -- held sha `1971e534...` because the
question never changed. This one changes it, so only measurement can say whether
accuracy moved.

## PERFORMANCE vs THE CURRENT LEDGER: no change on either side

Asked directly, and answered with evidence rather than argument.

**PYTHON: no behavioural change, proven.** Every migration step -- nine rules
moved onto the interpreter, across E and M -- held the 51,200-case fingerprint at
sha `1971e534...`, checked BETWEEN steps, not once at the end. The ledger is a
pure function of `(item, raw)`, so identical output over the whole input space is
identical behaviour.

**OLX: cannot alter a score.** `git diff` removes exactly THREE lines from
`slotSheet.ts`, none of them arithmetic:

    -                           freeAttr?: string): SlotSpec[] {
    -): { score: number; max: number; failed: string[] } | null {
    -  if (gate) return { score: 0, max, failed: [gate.key] };

The first two are a signature and a return type; the third returns the SAME
values plus the new key. `score: Math.max(0, Math.min(max, max - lost))` and the
`failed` computation are untouched. `deductions` is additive and empty unless a
slot declares `charge`, which no rubric yet does -- 0 deductions across all 3,120
recorded cells.

**So the exposure is PROVENANCE, not performance.** Changing `slotSheet.ts`
changed the hash every recorded web cell was stamped against, which is why the
gate reports 26 "WEB COLUMN IS NOT STAMPED BY THE APP'S OWN CODE" findings. The
declared remedy is `measured.WEB_CODE_NEUTRAL`, and `SCORER_NEUTRAL`'s precedent
demands a RE-SCORE as evidence ("VERIFIED 2026-09-04 by re-scoring 2776 recorded
cells"), not a reasoned case.

**A first re-score attempt was made and is NOT usable.** It reported 554 of 3,120
cells differing -- and the harness was at fault, not the engine: it invented
`options: ["met","absent"]` for slots that record none, and passed none of
`cover/equals/onlyif/counts/expect/requires/forbid/maps`, which are exactly what
decide satisfaction. A cell whose gate should zero it came back at 6. Recorded
artifacts do not carry enough to reconstruct the call; a faithful re-score has to
assemble the sheet the way `agreement.py` does. Recorded here so the 554 is not
mistaken for a finding by whoever picks this up.

## What finishing M still needs, in order

**M-3b. Four charge sites remain, and all four need an ENUM VOCABULARY.** They
are not conjunctions of booleans, which is why they could not move with the rest:

| site | what it compares |
|---|---|
| `TYPE_MISMATCH` | `observed_type` vs `named_type` -- enum equality, with `"unclear"` a LENIENT value that is deliberately not charged |
| `CADENCE_MISMATCH` | `cadence_ok`, a counted reading, and it SHORT-CIRCUITS before `TYPE_MISMATCH` |
| `WRONG_TYPE` x3 | `stimulus_move` against `REQUIRED_MOVE[expected_type]`, plus a forbid-rule condition |
| `NOT_OC` (avoidance) | `avoidance_frame` against the item's `avoidance_scores` TABLE |

The prerequisite is the same one the interpreter's stated limit names: a scorer
receives an ITEM DICT, and slot vocabularies live in the rubric view's
`SLOT_SPEC`, keyed by item. Until a scorer can read those, an enum comparison
cannot be declared -- only hardcoded.

So the order is:

1. **Give a scorer access to its slot vocabularies.** Either pass `SLOT_SPEC`
   into the plugin contract or expose an accessor; this is the single change that
   unblocks the remaining four.
2. **Declare enum comparisons**, with lenient values first-class -- `"unclear"`
   is not an edge case here, it is a declared verdict that must not charge.
3. **Migrate the four sites**, holding the fingerprint at each.
4. **M step 4, the web mirror.** `score_web`/`score_web_cadence` are hand-written
   mirrors of exactly these rules. Once the rules are declarations, GENERATE the
   mirror from them rather than migrating it -- which is what retires the
   source-reading comparison in `enforcement` that goal E had to preserve so
   carefully, and with it a whole class of divergence check.
5. **Re-run the item sweeps.** Steps 2-3 change no behaviour if done right, but
   M's own warning stands: the 14 fact fields are a SCHEMA THE MODEL ANSWERS, so
   any step that changes what is asked needs a sweep, not just a fingerprint.

**What is already true and should not be re-litigated:** the engine ships a
subject-neutral criteria scorer, the stub uses it with no Python, and `escalate`
on a clean stub run is `False`. M's completion test is met; what remains is
moving the REST of one course's scorer onto the thing that test proved works.

## Suggested shape when it is taken up

1. Declare the FACT VOCABULARY in the rubric (a `<Facts>` block per scorer),
   replacing `build_schema`'s hardcoded OC half.
2. Declare the GATES and their ORDER, extending `oc_gates` to carry precedence.
3. Reduce `derive_oc_ledger` to an interpreter over those two declarations.
4. Do the same to the web mirror, or generate the mirror from the declarations so
   the two cannot drift -- which would retire a whole class of divergence check.
5. Prove it on the stub: a second, trivial criteria scorer declared entirely in a
   rubric, scoring the stub's one item, with no Python at all.

Step 5 is the completion test, and it is the same shape as J's: the capability is
generic when something OTHER than this course uses it.

---

## CORRECTION: `_1C_GATE_CEILING` is NOT to be renamed

Filed as step 1 of the stub work and as disposition F. **Both were wrong**, and
the record says so in two places.

`editguard.ITEM_NAMED_BY_DESIGN` carries it explicitly:

> *"a gold DECLARATION about one cell, and entitled to name it. Renaming it would
> also be a data migration rather than a rename: it is read through
> `_gold_declaration` and carried by `gold_export`, so the name is a key in the
> gold file."*

and `enforcement.py:9566` records the principle:

> *"a DECLARATION ABOUT one cell may name that cell where a FUNCTION that no
> longer touches it may not. A check with nowhere to record that would fire on it
> forever and be waved through, which is how a check stops being read."*

The distinction is real: `rebuild_gold_1c` was renamed because the FUNCTION
outlived the item and the name described its caller's history. A declaration
about one cell is a different thing.

**The stub's actual fix.** The symptom was right -- a course-neutral stub should
not carry a table named for another course's item -- but the remedy is not a
rename. The stub simply DOES NOT DECLARE IT, and the consumer at
`measured.py:6588` reads it guarded. That is **J-5** (unguarded derived reads),
not a rename. `_1C_GATE_CEILING` leaves disposition F and the stub build order.

**FOURTH instance today** of proposing a change to deliberate, documented design
-- after the eager module-level loads (C1b), `derived()`'s "EMPTY IS ABSENT", and
`_RubricView.__getattr__` raising on absent. In this codebase an oddity that
looks like an oversight usually has a comment above it saying why it is not, and
the exception sets (`ITEM_NAMED_BY_DESIGN`, `SCORING_DIVERGENCES`,
`LESSONS_APPROVED`) exist precisely so those decisions are findable rather than
folklore. **Read the exception table before proposing to fix what it exempts.**

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

## M-3 CONTINUED (2026-09-24): THE AVOIDANCE RULE IS DECLARED, AND `gate="final"` WAS BROKEN IN FIVE PLACES

**Rule 1 of five is migrated, end to end and measured.** DAY1's avoidance charge
is now `<Slot key="phrased_directly_gate" gate="final" charge="NOT_OC"
because="The consequence is stated only as something avoided."/>`, applied by the
generic final-stage loop. The operand is the WEB's name and the scorer reads it
from its own `avoidance_frame`, INVERTED, through the course's `SIDE_ALIAS` --
the route the withdrawn consolidation was going to rewrite ~90 sites of authored
prose to avoid needing.

Declaring it on DAY1 alone is exactly what `item.get("avoidance_scores")`
selected: that condition is declared on DAY1 and on no other item (verified
against all eight). The "not extended to the other items" decision is now
enforced by the declaration's ABSENCE rather than by an `if`.

### What it cost, measured rather than asserted

| check | result |
|---|---|
| ledger over DAY1's 6400 swept answers | **identical** |
| advisory, unknown-list | **identical** |
| `checks` | **100 rows gain a recorded `phrased_directly_gate` entry** |
| other 7 criteria items | unchanged |
| the 217 shipping slot prompts | **all identical -> NO SWEEP NEEDED** |

The only behaviour change is that the judgement behind a NOT_OC charge is now
RECORDED on the paper side, which is the side that was missing it. Fingerprint
re-recorded as `f7a6341615a27177` with that account attached.

### BLOCKER 2 WAS WRONG, AND IT WAS MY ERROR

The plan recorded that the build path "is not reachable in this tree" because
`lo-blocks/content` holds only `demos/`. **It holds only demos because the course
is MOUNTED BY SYMLINK, and this dry-run simply had no symlink.** One
`ln -s` later the build runs, and `materialiseRubrics` announces "staged mounted
source edu.memphis.psych". The enforcement check at `enforcement.py:6768`
describes the mounting rule in its own comment; I filed the blocker without
reading it.

Before trusting the restored path I rebuilt to a SCRATCH directory and diffed:
both stages reproduce today's artifacts byte-for-byte (`.stage/expanded` and
`.stage/content`), so the build is derived from this tree and not a copy of the
live one.

### `gate="final"` WAS NEVER TAUGHT TO ANY READER BUT THE ONE THAT DEFINED IT

The two-stage gate landed earlier today in `rubric_component.as_view_items`.
FIVE other places read the same attribute, and every one of them was still
written for `true`/`false` only. The first `final` gate ever declared found all
five:

| reader | what it did | consequence |
|---|---|---|
| `rubric_component.as_view_slot_spec` | `gate in _TRUE` | slot silently stops being a gate **for the web** |
| `rubric_component` (third projection) | `gate in _TRUE` | same, in a third place |
| `rubric_olx.py` round-trip | wrote `gate="true"` | **demotes a final gate to definitional on regeneration** -- authored data lost by rewriting the file it was authored in |
| `rubric-inputs.ts` | `TRUE.has(x.gate)` | dropped the `!` from the generated `slots=`; **it wrote that regression into `bmod_handout2.olx`, and stripped `**GATE**` from the body**, leaving the prose and the attribute contradicting each other |
| `Slot.ts` zod schema | `z.enum(['true','false'])` | the content loader REFUSED the value and **aborted the static build** |

All five fixed. Four failed SILENTLY and one failed loudly; the loud one is the
only reason the set was ever completed, which is the argument for the schema
being the strictest reader rather than the most permissive.

**The lesson is the one already in the ledger and not applied:** I fixed the
instance I noticed (`as_view_slot_spec`), and only then enumerated the
population. Two of the five were found after that enumeration and one after the
build failed. A new attribute VALUE is a fix-set problem exactly like a new
identifier class.

### THE WEB DOES NOT RECEIVE ANY DEDUCTION CODE AT ALL -- OPEN

`slotSheet.ts` parses `charge`/`because` and `scoreSlotSheet` returns coded
deductions, but **no `charge=` attribute is generated onto any LLMAction in any
handout** (0 occurrences across all three). DAY1's action carries `slots`,
`forbid`, `equals`, `choices`, `max` -- and no `charge`. So the coded-deduction
work is plumbed at the runtime and unconnected at the generator: the rubric
declares the code, the paper scorer reads it, and the web still charges nothing
by code. This affects `states_a_contingency` too, which was migrated before
today.

That is the next step for "the OLX engine has coded deductions", and it CHANGES
WHAT SHIPS, so it wants its own verification rather than being folded in here.

### The remaining four rules, honestly

`consequence_not_a_setup` and `barrier_is_not_this_type` need no alias and are
already declared (`<Forbid>`) and already run on the shared `forbid_hit`
primitive -- the plan's own table said "already shared / computed".

`demonstrates_type` and `targets_goal_behavior` are declared as slots and are
charged CONDITIONALLY: `if not demonstrates: WRONG_TYPE elif not aimed:
WRONG_TYPE`, one charge for either cause, never two. That is the web's `onlyif`
primitive, which `slotSheet.ts` already implements and documents against
`score.py:derive_oc_ledger` by name -- and which the paper interpreter does not
have. Porting `onlyif` as a SHARED primitive is the honest next move and matches
"we want to make sure we're using the same primitives across all engines".

**And one divergence found while reading them:** the rubric declares
`<Expect key="demonstrates_type" left="observed_type" value="NR"/>`, comparing
OBSERVED_TYPE, while `oc.py` computes the same fact from `stimulus_move` against
the declared `<TypeMove>` table and falls back to `observed == expected` only
when the move is missing. **The two sides compute one named fact from different
answers.** Not yet measured for how often they disagree; recorded here rather
than fixed, because a fix changes scoring.

## M-3: RULES 3 AND 4 MIGRATED -- `onlyif` IS A SHARED PRIMITIVE NOW (2026-09-24)

**All five rules were declared in the rubric the whole time.** Rules 3 and 4 are
`<Onlyif key="targets_goal_behavior" cond="demonstrates_type"/>` on PR/NR and
`<Onlyif key="targets_unwanted_behavior" .../>` on PP/NP -- and the handouts
already carry the generated `onlyif=` attribute, so the WEB has been applying
them. Only the paper scorer hand-wrote the rule, as `if not demonstrates: ...
elif not aimed: ...`, with the precedence living in Python control flow.

I did not find them at first because I grepped `OnlyIf\|onlyif` and the element
is spelled **`<Onlyif>`** -- neither pattern matches. A detector built from a
guessed spelling reported "not declared" about something declared six times.

`scorer_criteria.charge_suppressed` is the primitive, and it is the same rule
`slotSheet.ts` implements -- that file documents itself against
`score.py:derive_oc_ledger` BY NAME. Both engines now read one declaration.

### THREE FINDINGS FROM THE VERIFICATION, none of which the fingerprint alone gave

**1. A guard bolted onto the `elif` was DEAD, and looked fine.** `elif not aimed
and not charge_suppressed(...)` can never fire the suppression: reaching the
`elif` already implies `demonstrates`, which is the condition. The fingerprint
reproduced, because nothing changed. What caught it was the CONTROL -- deleting
`<Onlyif>` from the item and finding the ledger identical, i.e. the declaration
was not being read. Migrating it properly meant making the two charges
INDEPENDENT `if`s and letting the declaration do the suppressing.

**2. One fact, two declared names, and a single-name lookup double-charges.** The
course declares `targets_intended_behavior -> ['targets_goal_behavior',
'targets_unwanted_behavior']` because reinforcement items aim at the GOAL
behaviour and punishment items at the UNWANTED one. Asking suppression under one
name left PP and NP unsuppressed, so both causes charged, 2 + 2 against a max of
4. The fingerprint caught this one immediately.

**3. THE FINGERPRINT WAS BLIND TO EVERY `forbid` RULE.** `forbid_hit` fired on
**0 of NR's 6400 swept answers**: the sweep never varied `trigger_expects` or
`restricts`, and fed `restriction_authored` True/False when the fact is a PICK
over strings. So it LOOKED covered -- the fact was being varied, over values the
rule can never match. A migration of `barrier_is_not_this_type` or
`consequence_not_a_setup` could have changed the ledger with the guard still
reporting "reproduces". The sweep now carries all 18 pick-combinations; case
count 51,200 -> 115,200, runtime 1.9s -> 4.8s. What it still does not cover is
stated in the docstring rather than left to be inferred.

This is the third time today a comparison was trusted because it came back the
way it was expected to. `evidence.certify` now guards this one: the declaration
is CERTIFIED load-bearing, meaning deleting it provably changes the ledger.

### Where the five rules stand

| rule | state |
|---|---|
| avoidance (`phrased_directly_gate`) | **declared**, final-stage gate, alias-resolved |
| `targets_goal_behavior` / `targets_unwanted_behavior` | **declared**, `<Onlyif>`, alias-resolved |
| `barrier_is_not_this_type` | **declared**, `<Onlyif>` + `<Forbid>`, NR only |
| `consequence_not_a_setup` | already `<Forbid>` on the shared `forbid_hit` |
| `demonstrates_type` | computed; see the divergence below |

**M-3 is done for the rules the alias governs.** What remains under M is step 4
(generate the web mirror from declarations) and the two open items below.

### STILL OPEN

1. **The web receives no deduction CODE at all** -- no `charge=` attribute is
   generated onto any LLMAction (0 across all three handouts), though
   `slotSheet.ts` parses it and `scoreSlotSheet` returns coded deductions. The
   rubric declares the code, the paper scorer reads it, the web charges nothing
   by code. Changes what ships; wants its own verification.
2. **`demonstrates_type` -- RESOLVED, AND THE 13% FIGURE I REPORTED WAS WRONG.**

   The earlier entry said the two sides compute this fact differently and
   disagree on 13% of recorded answers. **That described history, not the shipped
   scorer, and the reasoning behind it was wrong twice over.**

   *What is actually declared -- and this is the real finding.* The rubric is not
   uniform: `PR` declares `<Expect key="demonstrates_type" left="stimulus_move"
   value="given_desirable"/>` while `NR`, `PP` and `NP` declare
   `left="observed_type"`. One named check, computed from a different fact on
   different items. Correspondingly, only `PR` declares a
   `<Slot key="stimulus_move">` at all.

   *What the scorer does.* `oc.py` asks `stimulus_move` only
   `if item.get("move_pick")`, and PR is the only item carrying that condition.
   So on NR/PP/NP the move is never asked, `move` is None, and the computation
   falls back to `observed == expected` -- **exactly what those items declare.**
   Verified directly: NR with `observed_type=PR` charges WRONG_TYPE (-2), with
   `observed_type=NR` charges nothing. There is no live divergence.

   *Why the measurement said otherwise.* It was taken over recorded `.runs.json`
   artifacts, which PREDATE the `move_pick` gating -- they carry `stimulus_move`
   answers on NR/PP/NP because the scorer used to ask for it everywhere. Reading
   current behaviour off stale artifacts is what produced the 13%.

   *And the first reading of those artifacts was wrong too*: the check is stored
   as the STRING `"met"`/`"absent"`, and `bool()` on it is True either way, which
   collapsed every row to "met" and made the table meaningless until the shape
   was checked. Suspect the reader first -- twice on one question.

   **What remains, and it is small:** `oc.py` still PREFERS the move whenever the
   fact is present, so if `stimulus_move` ever reached NR/PP/NP -- it cannot
   today, since it is not asked -- the scorer would silently diverge from those
   items' declarations. Latent, not active. The honest fix is for the computation
   to read the item's OWN `<Expect>` operand instead of hardcoding a preference
   order: the same "read the declaration" move as the rest of M-3.

   *Accuracy cost: none.* `demonstrates_type` scores 191/191, 94/94, 188/188 and
   188/191 against gold on PR/NR/PP/NP -- 100% on three and 98.4% on NP.

### PYTHON vs OLX ON THE FOUR TYPE ITEMS -- NO PERFORMANCE DIFFERENCE

| | python | olx |
|---|---|---|
| ledger headline | 70/72 (97.2%) | 71/72 (98.6%) |
| pooled mean cells/run (of 18) | **17.522** | **17.542** |
| worst / best single run | 17 / 18 | **16** / 18 |

**The gap is +0.02 cells per run -- 0.11 percentage points -- on n=23 vs n=24.**
The whole headline difference is ONE cell on NR, where python has 5 runs
([17,17,17,17,18], median 17) and olx has 6 ([16,17,18,18,18,18], median 18):
the median falling either side of a sample that straddles 17/18. `sweep_summary`
pools the two sides as ONE sample for exactly this reason, because they share the
OLX prompt.

The direction also flips by item -- olx +0.30 on NR, python +0.33 on NP,
identical on PR, olx +0.17 on PP -- and olx produced the single worst run in the
set (16) while python never fell below 17.

**Bearing on O:** on these four items there is no accuracy argument either way
for retiring the python web scorer. That case has to rest on something else.

## THE OLX ENGINE HAS CODED DEDUCTIONS NOW (2026-09-24)

**The rubric declared the code, the paper ledger read it, and nothing ever
carried it to the web:** `charge=` appeared ZERO times across all three
handouts, while `slotSheet.ts` had parsed `charge`/`because` and returned coded
deductions since the engine gained them. Every web gate charged the right points
under no name at all.

Five places had to learn the two fields, which is the same shape as the
`gate="final"` sweep earlier today:

| | what it needed |
|---|---|
| `rubric_component.as_view_slots` | carry `charge`/`because` -- and it is THIS reader `SLOT_SPEC` is built from (via `coursedata._slots`), not `as_view_slot_spec`, which was the wrong one I edited first |
| `olx_prompts` | `charge_attr_for` / `because_attr_for`, registered in `GENERATED_ATTRS` |
| `rubric-inputs.ts` | carry both into `slotSpec` |
| `attributeAssembler.ts` | `slotPairsAttr(rules, field)` -- one emitter, since the runtime parses both with `parseCharge` |
| `assemble-prompts.ts` | register both in `attrsFor` |

Plus a HAND EDIT the generator refuses to do for you: it will not invent an
attribute slot (*"a tag with no `name=` to write into is python's hard error, not
something to invent here"*), so `charge="" because=""` was added by hand to the
four `<LLMAction>` tags that need it and the generator then filled all eight
values. That refusal is a good design and it reported exactly what was missing.

### It is REPORTING, not arithmetic -- certified, not assumed

`scoreSlotSheet` computes `score`, `max` and `failed` without ever consulting
`charge`; the field only populates `deductions[]`. Verified by scoring every
single-slot failure on all four items BOTH WAYS, with and without the attribute:

    cases compared        : 74
    same score AND failed : 74
    DIFFERENT score       : 0
    cases gaining a code  : 6

So the web now says WHICH rule it broke and why -- e.g.
`{"code":"NOT_OC","note":"The consequence is stated only as something avoided."}`
-- with no score moving anywhere. Fingerprint unchanged, self-test 19/19, static
content rebuilds clean.

### HOW DID THE TWO SIDES EVER AGREE, THEN?

Worth writing down, because the answer is the reason this mattered. **They
reached the same total by different accounting.** DAY1:

| web subtracts | paper charges |
|---|---|
| slot `matches_chosen_type` -2 | `TYPE_MISMATCH` -2 |
| slot `targets_own_behavior` -1 | `WRONG_BEHAVIOR` -1 |
| slot `consequence_asserted` -1 | `LINK_NOT_ASSERTED` -1 |
| any of 9 gates -> 0 | `NOT_OC` / `CADENCE_MISMATCH` / `BLANK` / `NOT_EXTERNAL_STIMULUS` -4 |

The code was never needed to compute the NUMBER -- only to say what the number
was FOR. The web subtracts a failing slot's `pts`; the ledger charges a named
code worth the same. They agree exactly as long as the two enumerations stay
COMPLEMENTS, and nothing enforced that: it was maintained by hand, in the rubric,
by whoever authored both columns.

Two ways that had already bitten:

1. **A verdict neither enumeration expected.** The engines default in opposite
   directions -- the web fails anything non-satisfying, the ledger charges only
   what a code names -- so an unforeseen third verdict costs points on one side
   and nothing on the other. `free_attr_for` exists for this, and records that
   Q1's `utb_stated` ran **62 observations** before the model answered `unclear`
   and exposed it.

2. **Many slots, one code.** On NR, THREE slots at -2 map to a single
   `WRONG_TYPE` -2. The arithmetic only matches if at most one ever charges,
   which is exactly what `<Onlyif>` is for -- and exactly where PP and NP were
   charging 2+2 against a max of 4 until the fix earlier today. That bug existed
   BECAUSE the correspondence was implicit.

With the code carried across, the two sides agree by construction rather than by
coincidence, and a future divergence is a mismatch in a named field instead of a
silent difference of two totals.

### THE AUDIT CAUGHT THE HALF I HAD NOT DONE

Emitting the attribute produced 10 new findings, all correct, in two classes:

**`UNKNOWN ATTRIBUTE` (8).** `KNOWN_ACTION_ATTRS` is derived from the SHARED
registry `primitives.json`, whose own comment says adding a primitive "has to be
taught to FIVE consumers and every hand-maintained mirror of them has rotted at
least once". `charge`/`because` now sit in `sheetAttributes` there, so every
consumer sees them from one place.

**`OLX ATTRIBUTE UNREAD` (2), and this was the real one.** *"<LLMAction> authors
`charge=`, and neither agreement.py nor any rubric item carries it."* Correct:
I had given the WEB the code and left the harness's python mirror reproducing the
number without it. An attribute that only one of two mirrors reads is precisely
the failure that check exists for.

So `agreement.py` now carries `charge`/`because` on the slot -- the same way it
already carried `free`, and mirroring `SlotSpec` -- and `slot_deductions()`
mirrors `scoreSlotSheet`'s `deduct`. Verified against the TS engine on the same
sheet and answer, both produce the identical object:

    [{"code": "NOT_OC", "pts": 4.0,
      "note": "The consequence is stated only as something avoided."}]

`olx_prompts.parse_charge` is the python mirror of `parseCharge`, splitting on
the FIRST colon only -- which is what lets a `because` sentence keep its own
colon and arrive whole.

### THE CODES ARE RECORDED IN THE RUN ARTIFACTS (user, same session)

`.runs.json` results now carry a `deductions` field beside `failed_slots`, which
is a COUNT and says nothing about what was broken. The paper ledger has always
recorded codes; this side recorded none, so a disagreement between them could
only ever be compared as two totals.

**The web mirrors already knew the codes and threw them away at the `return`.**
`score_web` and `score_web_cadence` computed
`max(0.0, item["max"] - codes["WRONG_TYPE"])` and returned `(score, 1)` -- the
name was right there in the expression. Both now derive their pair FROM a
deductions list (`web_deductions`, `web_deductions_cadence`), so the number and
the name cannot drift apart. Verified behaviour-preserving over every
single-slot failure on all eight items plus the all-pass and all-fail corners:
**131 rows, 0 differing.**

**Two places declare a code, and both are read.** A GATE names it on the slot
(`charge=`/`because=`); a SCORED component names it per failing verdict
(`<Credit codes="absent=UTB_NOT_STATED">`), which is the form the paper ledger
has always used. Reading only `charge` would have left all nineteen slot-sheet
items recording an empty list while their ledger side named a code for every
charge -- so `slot_deductions` reads both. Q1 now records
`[{UTB_NOT_STATED, 2.0}, {REASON_MISSING, 1.0}]` where it recorded nothing.

Reconciliation checked rather than assumed: over 123 OC cells, `sum(deduction
pts)` accounts for the score in every one.

The generic gate loop in `score_web_cadence` also stopped hardcoding `NOT_OC`
for any gate it did not recognise and now reads the slot's own declared charge.
Identical today -- all six declared charges are `NOT_OC` -- and correct when a
future gate declares something else.

### AND THE REFACTOR BLINDED A CHECK, WHICH SAID SO

Moving the rules out of `score_web` into `web_deductions` left the entry point a
thin wrapper, and `check_weighted_slots_are_scored` greps the scorer's SOURCE for
the slot names it consults. It found none and reported all 21 weighted slots
unscored.

That is the third appearance of the same shape today -- a check reading a
WRAPPER instead of the body -- after `check_selectors_govern_something` passed
vacuously on 112 characters and `check_criteria_prose_has_one_source` had to be
pointed through its delegation. Here it failed loudly rather than quietly, which
is the better direction, but the remedy is the same and is now GENERIC:
`_source_through_delegates(fns, module)` gathers a function's source plus every
module-level function it reaches, transitively. A check about what a scorer DOES
stops depending on how its body happens to be split up.

Certified rather than assumed, because a check that has just stopped firing is
exactly the thing to distrust:

    source gathered            8,028 chars (the wrapper alone is ~400)
    contains the four slot names   yes
    against a stub naming nothing  21 findings -- still live

**Note the asymmetry is deliberate on both sides:** `failed_slots` and
`deductions` are different sets. A slot with points but no declared code costs
its points and names none, so the count includes it and the list does not.

Note `score_slots`'s count and `slot_deductions`'s list are deliberately NOT the
same set, on both sides: a slot with points but no `charge` costs its points and
names no code, so `failed` counts it and the deduction list does not.

### What this does NOT do

The four cadence items carry charges because they are the only ones whose gates
declare a code. `PR/NR/PP/NP` declare none, so they emit no `charge=` and the web
still reports their deductions namelessly. That is a rubric-authoring gap rather
than an engine one, and closing it means deciding the code for each gate -- a
content decision, not a refactor.

## O · DECIDED: THE PYTHON WEB SCORER STAYS (2026-09-24)

O asked for a decision, and the plan set the bar: *"the honest default is that a
measurement axis stays until someone can say what it is no longer needed for."*
It can now be said what it IS needed for, so it stays.

### Precondition 1 has not landed

M step 4 -- the mirror GENERATED rather than written -- is not done. The mirror
is closer than it was (it reads `onlyif`, `charge`, `because` and the declared
gates from the rubric) but `web_deductions` and `web_deductions_cadence` are
still hand-written. The precondition the goal itself set is unmet.

### Precondition 3 is answered, and the answer is concrete and current

**`measured.rescore_recorded` drives `agreement.SCORERS` -- the python mirror --
and it is the mechanism that verifies a lo-blocks code change moved no recorded
score, from artifacts already on disk, at no call cost.** That is not a
historical use: it is what cleared the 26 provenance findings this session,
instead of a sweep.

Retiring the mirror would leave two options for the next such question: re-run
the app over every recorded cell, or accept the findings unverified. The first is
what the mirror exists to avoid; the second is what the audit exists to prevent.

### On quality there is no argument either way

Measured over the four type items: python 17.522 mean cells/run, olx 17.542 --
**+0.02 of 18, 0.11 percentage points.** The headline 70/72 vs 71/72 is one cell
on NR, a median falling either side of a sample that straddles 17/18.

### And the mirror is currently EXACT, so its upkeep is self-checking

`mirror_self_control`: **olx 2,760/2,760 and python 2,908/2,908** recorded scores
reproduced from recorded verdicts. A mirror that drifts stops reproducing, which
is a test that runs in the audit rather than a promise anyone has to keep.

**The honest case against** is that this is a HAND-WRITTEN mirror and it does
drift: this session found `onlyif` dead on the web path, and `charge`/`because`
parsed by the runtime but never generated. Both were caught, both by machinery
that depends on there being two implementations to compare.

### WHAT RETIRING IT ACTUALLY COSTS (user, 2026-09-24)

**It means dropping a COLUMN from the ledger and the associated RUNS.** Not only
"no future sweep can be compared on that axis" -- the recorded measurements go
too. Concretely, that is `python` across 26 items: **2,908 recorded cell-runs**,
every one of which currently reproduces its stored score.

That reframes the trade. The upkeep argument for retiring it is that a
hand-written mirror drifts; the cost is destroying measurement history that
cannot be recreated without re-running the sweeps that produced it. And the
column is not idle: `rescore_recorded` drives this scorer, and it is what
verified the 26 provenance findings at no call cost this session.

### WHAT THE TWO REMAINING SIDES WOULD BE FOR (user, 2026-09-24)

**"With the retirement of the python web scorer there is a simple functional
difference between the paper and web scorers: the PAPER scorer scores
teacher-provided artifacts, often in only implicitly structured formats, whereas
the WEB scorer scores the OLX version of the same content after it has been
structured for effective web delivery."**

That reframes what survives. `python` and `olx` are two implementations of ONE
job -- score this slot sheet -- and the 55 checks below exist to keep them from
drifting apart. `paper` and `web` are not that. They score DIFFERENT INPUTS: one
reads what a teacher actually wrote, in whatever shape they wrote it; the other
reads the same content after it has been given structure for delivery.

Two consequences worth stating before anyone retires anything:

* **A paper/web disagreement is not automatically a bug.** Where `python` vs
  `olx` differing always meant one implementation was wrong, paper vs web can
  differ because the STRUCTURING changed what is legible -- which is a finding
  about the OLX authoring, not about either scorer.
* **The comparison that remains answers a different question**, and the
  machinery built for the first one should not be pointed at the second without
  saying so. A check that reads "these two must agree" is true of the retired
  pair and is an open question for the surviving one.

### THE ENFORCEMENT MACHINERY IS BUILT ON THE TWO SIDES BEING COMPARABLE (user)

**"A LOT of the enforcement machinery deals with keeping the python and olx web
scorers in sync, so there will have to be a very thorough check that it still
works after the python web scorer is retired, without losing the checks that keep
the scorer from going off the rails on the web, olx or paper side."**

Measured rather than estimated, scanning each `check_*` for the names the python
side is reached by:

    enforcement checks total        191
    checks reaching the python side  55   (29%)

    by hook:  agreement 51 | "python" 7 | score_slots 3 | SCORERS 2
              score_web 2 | web_deductions 2 | paper_scorer_agreement 2
              mirror_self_control 2 | rescore_recorded 2

So retiring the column is not one deletion and a ledger edit: **29% of the audit
reaches that side**, and some of those checks are not ABOUT the comparison at all
-- `check_app_and_harness_send_the_same_prompt`,
`check_computed_slot_recovery_is_faithful`,
`check_both_engines_compute_the_same_primitives` -- they USE the harness as the
instrument that makes a property observable. Each would have to be re-homed onto
an instrument that still exists, or be retired with a statement of what stops
being watched.

**This is the strongest argument yet for the default the goal already states.**
A measurement axis stays until someone can say what it is no longer needed for,
and 55 checks currently answer that question in the other direction. Retiring the
column means auditing all 55 first -- which is a larger piece of work than the
retirement itself, and the honest order: prove the audit survives BEFORE dropping
the runs, not after.

**Revisit when M step 4 lands.** A generated mirror cannot drift, and a copy that
cannot drift is a different question from this one.

## THE RE-SWEEP IS NOT NEEDED -- THE DEBT WAS VERIFIABLE, NOT MEASURABLE

The 26 `WEB COLUMN IS NOT STAMPED BY THE APP'S OWN CODE` findings have been
carried for days as "needs one re-sweep". They did not. The finding's own remedy
says so -- *"re-score, and declare the pair in measured.WEB_CODE_NEUTRAL if every
recorded cell reproduces"* -- and every recorded cell does.

**Verified with the app's own code, not with the mirror.** `rescore_recorded`
drives the python mirror, which cannot see a TypeScript-only change; so the
recorded verdicts were run through `slotSheet.scoreSlotSheet` itself under `tsx`.
Verdicts and picks were lifted with `cross_path.result_cell` / `result_picks`
rather than read by hand -- that accessor exists because **the app stores
`grader.score` as a FRACTION of `sheet_max`** while every other writer stores
absolute points, and a second copy of that conversion is a second chance to
forget the multiply.

    2,760 recorded olx cells    0 moved    0 errors    0 non-finite

Four `(recorded -> now)` pairs declared in `WEB_CODE_NEUTRAL`, covering all 26
items. Both checks now return zero.

### THE HARNESS LIED FIRST, AND THE CONTROL CAUGHT IT

The first run of that harness reported **0 moved across all 2,760 cells** and was
worthless. `scoreSlotSheet` takes POSITIONAL arguments and an options bag was
passed as `explicitMax`, so `max` became an object, every score came back `NaN`,
and `Math.abs(NaN - x) > 1e-9` is **false** -- every cell silently "matched".

What exposed it was the control, not the result: shifting every stored score by
+0.5 should move all 2,760 and moved only 286. A second control (flip one
`met`->`absent` per cell) now moves 1,736. With the signature fixed, control A
moves 2,760 of 2,760 -- the comparison can fail, so the zero means something.

**The same bug was in the charge-additivity test reported earlier**, which also
passed `{}` as `explicitMax`. Re-run correctly: 74 cases, 0 score/failed
differences, 6 gaining a code, all finite. The conclusion held; the measurement
behind it did not, and was replaced.

### One check corrected, not excused

`check_web_code_neutrality_is_verified` treated "this item has no web sheet" as
"cannot be verified". `1b`, `T1` and `T2` carry no `<LLMAction>` -- they are
scored deterministically from the fixture and `scoreSlotSheet` never runs for
them -- so a sheet-scoring change cannot move their numbers. That is NOT
APPLICABLE, not unproven; demanding evidence that cannot exist would make a true
claim look unverified. An item that HAS a sheet and still fails to compare is
still a finding.

## M STEP 4: THE SCORE MIRROR IS ONE FUNCTION; THE DEDUCTION HALF IS BLOCKED, AND THE BLOCKER IS REAL

### Done: `agreement.score_sheet` replaces all three scorers

`SCORERS` was `score_slots` plus two hand-written operant mirrors. It is now ONE
function for every kind, reading the slot sheet the way `scoreSlotSheet` does.

**Why the operant mirrors existed at all, which nothing had written down:**
`score_slots` scored from the rubric's CREDIT components, and on those eight
items the credits and the slots are DIFFERENT SETS -- DAY1's credits sum to 5
against a 4-point sheet, NR's slots sum to 6 against a max of 4 (its three
2-point findings, only one of which `onlyif` ever lets charge). The app has never
had operant-specific code; it reads the sheet. Scoring from the sheet removes the
reason the mirrors existed, rather than migrating them.

Verified BEFORE the swap:

| | |
|---|---|
| `mirror_self_control`, olx | **2,760/2,760** |
| `mirror_self_control`, python | **2,908/2,908** |
| 131 synthetic operant states | **0 differing** |
| paper fingerprint / 217 prompts | unchanged |

Two defects were found by that verification and fixed before it passed: the
denominator (the TS takes `explicitMax ?? sum(scored)`, and `merged` carries no
`sheet_max`, so NR scored against 6) and the counted-family expansion, which now
uses the same prepared `expand_counted` helper `score_slots` used rather than a
second copy of a rule already got wrong twice.

### NOT done: one DEDUCER, and the reason is a coupling worth recording

The generic deducer reproduces the hand-written operant ones EXACTLY -- 131 of
131 states agreeing on codes AND points -- but only once every gate declares its
`charge`. And **declaring a charge on a GATE slot also creates an `oc_gates`
entry, which the PAPER scorer's declared loop then applies on top of its own
hand-written definitional gates.** Measured: DAY1's feedback began reading
"Missing: ... follows_behavior" on answers where `follows_behavior` was TRUE --
the same code and the same points, and a note that tells a student a fact was
absent that the model judged present.

So the 68 gate charges were reverted and 21 remain on the SCORED slots, where
they feed the web and leave the paper ledger untouched. The operant deducers stay
hand-written until `derive_ledger`'s definitional half is an interpreter too,
which is M step 3's remaining work. Routing them through the generic one today
would name FEWER codes than the artifacts already carry -- a regression dressed
as a simplification.

**This is the honest state of step 4:** the promise was "generate the mirror from
the declarations so the two cannot drift". The SCORE mirror is there. The
DEDUCTION mirror is one rubric edit away and that edit is blocked on the paper
scorer, which is a finding about sequencing, not a failure of the approach.

### The source-reading comparison is NOT retired, and it nearly died quietly

Step 4 promised to retire `enforcement`'s source-reading comparison. It cannot
be: `web_deductions`/`web_deductions_cadence` are still hand-written, so there is
still a body to read.

Worse, that comparison had ALREADY gone blind. `check_selectors_govern_something`
scans the operant scorers for `yes("...")` reads; those moved into
`web_deductions*` when the mirrors were split so the score could be derived from
the coded deductions, and the check reads the ENTRY POINTS. Measured: **0 slot
names found, against 10 through delegation** -- and because its finding branch is
`read - emitted`, an empty `read` reports nothing and looks clean. It is the same
check the plan already records as springing this trap during goal E.

**Fourth instance of the wrapper shape in one day.** It now uses
`_source_through_delegates`, and it is CERTIFIED live: planting one unemitted key
in the scanned source produces exactly one finding, while the live tree is
genuinely clean. The first control attempted was invalid -- functions defined in
a heredoc have no readable source, so `inspect.getsource` failed and the control
"passed" for a reason that had nothing to do with the check.

### AND THE TAG EDIT DEMOTED EVERY LIVE-RUN CLAIM, WHICH IS THE POINT OF THAT CHECK

Adding `charge=`/`because=` to eight `<LLMAction>` tags moved their
`prompt_sha`, and `_primitives_with_live_app_evidence` requires a recorded web
run to be CURRENT before it counts as having exercised a primitive. So twelve
closed goals -- E3, E8, E10, E44, E48, E53, E55, E56, Q21, Q22, Q57, Q64 --
reported `GOAL RETIRED WITHOUT A LIVE RUN` for `expect`, which had simply
stopped having a live artifact.

That check is behaving exactly as designed; the function's own comment records
the case ("a tag-only edit made every live artifact read as history here"), and
the remedy is the declaration it points at.

**And the fingerprints separate the two questions cleanly, which is the part
worth keeping.** The edit moved `prompt_sha` (the whole tag) and left `ask_sha`
untouched on all eight items -- recorded and current are byte-identical --
because `charge` and `because` are never ASKED: they are read after the model
has answered, and `scoreSlotSheet` computes score, max and failed without
consulting them. Independently: all 217 slot prompts hash identically across the
edit.

So eight rows in `ASK_EQUIVALENT_PROMPTS` (23 -> 31), each carrying that reason,
each self-checked against the current `ask_sha` so it stops applying the moment
the question does change. `check_ask_equivalences_still_hold` and
`check_closed_goals_that_changed_code_were_exercised` both return zero.

### THE DECLARATION HAS TWO COPIES, AND ORDER IS PART OF THEM

Declaring the eight rows took three attempts, each caught by a check comparing
two things that must agree:

1. Edited `course.json` (the MIGRATED copy) only. `MIGRATED TABLE DOES NOT MATCH
   ITS SOURCE` named the three rows it could see: the authored copy lives in
   `declaration_source.py`.
2. Added them to the authored copy and checked with `set(a) == set(b)`. Still a
   finding: **"SAME KEYS, DIFFERENT ORDER -- `==` calls these equal; the order is
   the data."** I had prepended in one file and appended in the other, and my own
   comparison was blind in exactly the dimension that mattered -- the same shape
   as the NaN comparison earlier today, and the reason `evidence.certify` exists.
3. Moved them to the end so both copies read in the same order. STILL a
   finding: the two copies carried DIFFERENT REASON TEXT for the same key, and
   the check compares values as well as keys and order. The migrated copy now
   takes its strings verbatim from the authored one.

Four attempts, and the check was right every time -- it was reading a
projection against its source and refusing to call them equal on any axis that
differed: which keys, in what order, with what values.

Worth keeping because the failure is instructive: a check that compares an
AUTHORED table against its MIGRATED projection catches a half-finished edit that
no single-file review would, and it was right to insist on order.

## M STEP 3: THE DEFINITIONAL GATES ARE DECLARED (2026-09-24)

`derive_ledger`'s definitional half -- the conjunction that decides whether an
answer is operant conditioning at all -- was a hardcoded tuple naming four
checks, a code and a note. It is now
`<Conjunction code="NOT_OC" note="Missing: " list="true" over="..."/>` on each of
the eight items, plus the `NOT_EXTERNAL_STIMULUS` one beside it. Adding or moving
a definitional reading is an edit to the OLX and nothing else.

**The declaration names the SLOTS**, the same ones the web's sheet is generated
from, and `check_named` resolves each to the check this scorer records through
the course's `SIDE_ALIAS`. Declaring them in the paper's vocabulary would have
made the rubric speak a language only one engine uses.

    fingerprint reproduces over all 115,200 cases
    CERTIFIED load-bearing: deleting <Conjunction> changes the ledger

**The inverse alias is ambiguous, and that cost a wrong answer first.** TWO of
this scorer's names map to one of the web's -- `behavior` AND `operant_behavior`
both alias to `names_behavior`, the first being the FACT the model answers and
the second the CHECK recorded from it. Returning whichever came first dropped
`operant_behavior` from the conjunction, and 5,800 of DAY1's 6,400 rows quietly
stopped naming a missing reading they had always named. `check_named` now
resolves against the names actually present.

### It unblocked half of what it was meant to

With conjunction members excluded from `oc_gates` -- a member and an independent
gate read the same slot, and the singles charge the FIRST failure while the
conjunction reports ALL of them -- the definitional gates can now carry a
`charge` for the web without the paper scorer double-handling it. The generic
deducer went from 55/131 states agreeing to **124/131**, fingerprint unchanged.

**The remaining 7 are the rules still hand-written in `derive_ledger`:**
`CADENCE_MISMATCH` (4 states) is `apply_fact_gate` on `cadence_ok`, and one
`NOT_OC` on each cadence item is the `consequence_not_a_setup` forbid. Declaring
a charge on those slots reproduces the original collision, because the paper
scorer still applies them by hand. They are the same shape as the avoidance gate
M-3 migrated, with one extra question: `CADENCE_MISMATCH` SHORT-CIRCUITS before
`TYPE_MISMATCH`, so moving it into the declared loop moves it relative to the
type rules and the order is load-bearing.

So `DEDUCERS` stays split for now. Routing it through the generic deducer today
would name fewer codes than the artifacts already carry.

### A NEW RUBRIC ELEMENT IS A BLOCK, AND THE BUILD SAID SO TWICE

`<Conjunction>` was authored before it existed as a block, and two checks caught
that in the order they should:

**1. `COURSE SCHEMA INCOMPLETE: 'oc_conjunctions' belongs to no declared group.`**
A new ITEM FIELD must name the group the engine reads it through -- §9.2a makes
it FAIL rather than default. Added to `RUBRIC_FIELDS` beside `oc_gates`, which is
how the scorer reads it.

**2. `DUPLICATE_ID` x14, and the static build ABORTED.** An unregistered tag is
loaded as a generic block with a CONTENT-DERIVED id, and every operant item
declares the same definitional conjunction -- so eight identical elements
collided, twice over. The remedy was already written down on `Onlyif`:
`requiresUniqueId: false`, because "two items carrying the same guidance line,
the same slot or the same deduction text collide -- and that is not a conflict,
it is the same statement made twice."

So `Conjunction.ts` and `Conjunction.md` now sit beside the other rubric blocks,
and the registry was REGENERATED (`npm run build:gen-block-registry`) rather than
hand-edited -- the file says DO NOT EDIT MANUALLY at the top, and the generator
also writes the metadata, css and i18n registries that would otherwise drift.

**This is the same shape as `gate="final"` this morning**, and the lesson held:
adding a value or an element to the rubric grammar means teaching every reader,
and the LOUD reader -- the schema, the content loader -- is the one that makes
the set findable. Four silent readers were found by enumeration that morning;
here the build refused outright and named the count.

## THE LAST TWO RULES ARE DECLARED, AND `DEDUCERS` IS ONE FUNCTION (2026-09-24)

`CADENCE_MISMATCH` and the `consequence_not_a_setup` forbid were the 7 states
keeping the generic deducer from matching. Both are now declarations, and the
deducer gap is **131 of 131 states agreeing on codes AND points**, so `DEDUCERS`
is one function for every kind -- which is what M step 4 promised and could not
deliver until these moved.

| rule | how |
|---|---|
| `consequence_not_a_setup` | NO code change. A gate slot a `<Forbid>` COMPUTES is excluded from `oc_gates`, so it carries a `charge` for the web while the paper goes on computing it from the rule |
| `CADENCE_MISMATCH` | `<Slot gate="scope" charge="CADENCE_MISMATCH"/>` -- a THIRD stage |

**`scope` is a meaning, not a precedence number** -- M rejected numbers, and
rightly. It says the gate asks whether the answer addresses THIS ITEM'S OWN
TERMS: a weekly answer to a daily question is not a wrong TYPE, it is an answer
to a different question, and it must run BEFORE the type comparison. That order
was load-bearing and implicit in `derive_ledger`'s layout -- running it after
would leave `TYPE_MISMATCH` in the ledger beside it, two codes for one fault.

Measured against the previous tree via `git stash`, which is the only comparison
that could settle it: **DAY1's ledger and advisory identical on all 14,400
rows**, 450 rows gaining a recorded `cadence_is_daily` check that
`apply_fact_gate` deliberately never wrote. `mirror_self_control` holds at
olx 2,760/2,760 and python 2,908/2,908.

### THE GATE VOCABULARY NOW LIVES IN THE SHARED REGISTRY, because it reoffended

`gate="final"` cost four silent readers this morning. Adding `gate="scope"`
IMMEDIATELY repeated it: `rubric-inputs.ts` still tested `=== 'final'` by hand,
dropped the `!` from the shipped `slots=` attribute, and the deducer gap sat at
127/131 until that was found.

So the stages are in `primitives.json` -- the file whose own header says
"adding one has to be taught to FIVE consumers and every hand-maintained mirror
of them has rotted at least once" -- as `gateStages`. Both languages read it:
`rubric_component.is_gate`/`gate_stage` in Python, `isGate` in TypeScript.
Spelling a stage literal anywhere else is now the bug.

**Three exclusions now keep a declared code from colliding with a hand-written
rule, and each names a rule that computes the slot elsewhere:** conjunction
members, `<Forbid>`-computed slots, and the cadence gate (which moved INTO the
declared loop rather than being excluded from it). That is the shape of the
answer M was looking for -- not "declare everything", but "a slot is an
independent gate only when nothing else decides it".

## K · FIRST-PASS SORT, FILED AND STOPPED (2026-09-24, user: "not yet")

Work on K stopped on the user's instruction. What was found in the first pass is
filed here so the next attempt starts from it rather than repeating it.

### The sort, and it is NOT yet trustworthy

191 `check_*` functions, classified by what each READS and what its question is
ABOUT:

    MEASUREMENT (stays)                        41   21%
    ABOUT OUR PYTHON (stays, or dies with it)  44   23%
    CONTENT ONLY (portable to lo-blocks)       58   30%
    UNCLASSIFIED (needs eyes)                  48   25%

**Treat these numbers as a starting point, not a result.** Two earlier passes
over the same 191 checks disagreed violently -- one put 75% in MEASUREMENT, the
next 19% -- because both keyed on names appearing anywhere in the body, and a
structural check that merely mentions `prompt_sha` is not a measurement check.
A third of the population is still unclassified. A hand-written detector over
prose was the wrong instrument and is the documented wrong instrument.

### What reading a sample showed, which the sort could not

The decisive distinction is NOT which modules a check reads -- it is **what its
question is about**. Both of these read the rubric and the slot sheet:

  * `check_rubric_slots_reach_the_sheet` -- "a rubric slot with no entry in its
    item's `slots=`". Content against content. **Portable.**
  * `check_weighted_slots_are_scored` -- "does every point-bearing slot reach a
    scorer?" It reads the same declarations, but the subject is OUR PYTHON
    SCORER'S SOURCE. **Not portable; it dies with the thing it interrogates.**

So the criterion that matters is the SUBJECT, and the usable proxy found for it
is whether the check reads python source (`inspect.getsource`,
`_source_through_delegates`, `_oc_scorer()`, `SCORERS`/`DEDUCERS`). That is what
the 44 in the second bucket have in common, and several of them are checks this
session repaired precisely because reading source is fragile.

### What to do next, when K is taken up

1. **Classify by SUBJECT, by reading, not by grep.** The population is 191 and
   the docstrings are excellent; the sort is a day of reading, not a script.
   Every automated attempt so far has been wrong in a way only reading found.
2. **The 58 in CONTENT ONLY are candidates, not a work list.** They have not
   been checked individually, and the sample above shows the false-positive rate
   is real.
3. **The obligation the goal already states stands:** a ported check must FIRE
   on the case its python original fires on, proved by the same fire test,
   before the original retires.
4. **K and O are entangled.** 44 checks are ABOUT our python, and O would retire
   part of what they interrogate. Sorting K before deciding O risks porting
   checks that are about to become moot -- and O's own answer depends on what
   survives K.

Raw sorts kept at `scratchpad/k_sorted.json` for the next pass; they are inputs
to a reading, not a conclusion.

## THE CONFIRMATION SWEEPS (2026-09-25): WHAT THEY CONFIRMED AND WHAT THEY BROKE

One run per item on each side, asked for as a check that the scorers still work
after M, O and the gate-stage changes -- not as a measurement. **One run is not
a measurement**, and nothing here may be quoted as one: Q3 has been seen at
16/20, 12/20 and 15/20 across three runs of identical code. So each item is
read against the RANGE its own recorded runs have already produced, and only an
item outside that range is a question.

### The paper side (gpt-5-mini): clean, and it found a real bug

**Handout 2 lost a participant to a race in the scorer registry.**
`scorers._course_scorer` registered a module in `sys.modules` BEFORE running it,
and `score.py` scores participants in a `ThreadPoolExecutor`. A second worker
reaching the cache check during the first worker's `exec_module` was handed a
module whose body had not run, and died on `module '_course_scorer_oc' has no
attribute 'schema_fragment'` -- while the other nineteen scored, and while the
module imports perfectly in isolation. A failure that depends on WHICH
participant is what a race looks like.

Fixed by publishing only after `exec_module` completes, under a lock, and
verified cold in five fresh processes at 12 threads. Re-running handout 2 gave
0 failures and 20 participants, and every handout-2 item went from 19 cells back
to 20.

    24 of 26 items inside their recorded range.
    DAY2  19 (range 16-18)  -- one ABOVE
    Q1    17 (range 18-19)  -- one BELOW

Both are one cell outside a six-run range, which is what a single draw does.

### The web side: 26 of 26 items inside their own recorded range

    1a  19/20 (18-20)   1b  20/20 (20-20)   1c  17/17 (16-17)
    2a  19/20 (18-20)   2b  20/20 (20-20)   3   20/20 (19-20)
    D1  18/18 (18-18)   D2  18/18 (18-18)   DAY1 18/18 (13-18)
    DAY2 18/18 (11-18)  NP  17/18 (14-18)   NR  17/18 (15-18)
    PP  18/18 (15-18)   PR  18/18 (15-18)   Q1  18/20 (15-19)
    Q2  18/20 (17-20)   Q3  20/20 (19-20)   Q4a 19/20 (17-19)
    Q4b 18/19 (16-18)   Q4c 16/19 (15-17)   Q5  19/20 (17-19)
    Q6  16/20 (14-18)   T1  18/18 (18-18)   T2  18/18 (18-18)
    WK1 18/18 (15-18)   WK2 17/18 (16-18)

**Not one item fell outside the range its own recorded runs have already
produced.** That is the whole claim, and it is the claim the question deserves:
the scorer still behaves as the ledger says it behaves. It is NOT a measurement
and none of these numbers may be quoted as one.

### THE SWEEP WAS SENDING ITS LLM CALLS TO THE LIVE TREE'S SERVER

Found while checking write scope, and it is a defect in the harness rather than
an accident of how one sweep was launched. Two independent defaults point at
8888:

    backends.py:238         ENDPOINT = "http://localhost:8888/api/llm/chat/completions"
    runner.test.ts:58       const SERVER = process.env.LO_SERVER || 'http://localhost:8888'

8888 is the LIVE tree's dev server (`~/code/update/lo-blocks`). So a sweep run
entirely from the dry-run tree -- dry-run idmap, dry-run vitest, dry-run
scoring code -- still had its requests SHAPED by the live tree's
`routes/llm.ts`, which is twelve days older. Scoring was never affected; request
shaping was, and nothing said so.

It also made the live server write ~2,800 rate-limiter files inside a tree this
session is forbidden to write to. That is reported separately to the user.

Fixed for the run by exporting `LO_SERVER=http://localhost:8899`; the nine items
already swept through 8888 were set aside under `via_8888/` and re-run, so the
confirmation uses ONE transport path end to end. **The defaults themselves are
still 8888 and should be changed** -- a dry-run tree that silently borrows the
live tree's request path is the same class of fault as the stale dev server of
2026-09-09, and `agreement_app.server_code_is_stale` does not cover it.

### The preflight refused twenty items mid-sweep, and was right to

Between those two passes the remaining twenty items refused with

    REFUSING to sweep: the instruments disagree with the code.
        DEFINITION VANISHED FROM THE PACKAGE ... _app_envelope, _harness_envelope

because a programmatic edit to `enforcement.py` had eaten `_app_envelope` and
`_harness_envelope` while the sweep was running. **The guard cost time and saved data**: not one item
produced a number against a broken tree. Repaired, the sweep resumed on the
items it had skipped.

THE EDIT'S OWN LESSON, since it is a fourth instance of a known class: the
script did `tree = ast.parse(src)` ONCE and then replaced two functions in a
loop, reassigning `src` between them. `ast.get_source_segment` uses offsets from
the ORIGINAL text, so the second cut landed mid-way through a different function
-- duplicating one definition and swallowing two. The file parsed. Re-parse
after every write, or collect every exact old string before the first one.

### AND THE AUDIT HAD BEEN STOPPING EARLY, UNNOTICED

Both audits run earlier on 2026-09-25 ended in an `AttributeError` at
`engine_interpretation_line` and were read as complete. They were not: they had
reported about two thirds of their findings.

`check_engines_read_a_response_the_same_way` was retired in goal O, but three
things that SERVED it were not -- `_recorded_payloads` (which still selected
items by the eliminated `agreement.SCORERS`), `_interpretation_comparison_cached`
(which still called it), and equivalence.py's fire case for it. A retirement is
not finished until its callers and its fire cases go with it. All three are
retired now and the audit runs to the end.

**The first complete audit reports 96 lines in exactly three classes:**

    44  OLX QUOTES A STUDENT THROUGH A REFERENCE   -- the standing baseline
    26  WEB COLUMN IS NOT STAMPED BY THE APP'S OWN CODE
    26  A SWEEP ON DISK WAS NEVER RECORDED

and one line worth reading beside them: *paper-vs-web arithmetic: 6268 of 6268
cells score IDENTICALLY when the web's own judgments are run through the paper
scorer.* Holding the judgments fixed removes the model; what is left is the
arithmetic, and it agrees exactly.

### Why the two new classes were not cleared, and what would clear them

**26 unstamped web columns.** The declared cost of retiring `WEB_CODE_NEUTRAL`
with the python engine, compounded by O's unfinished tail (above). The app's
scoring code genuinely changed tonight, so every recorded column predates it.
Only a real multi-run re-sweep clears these; a 1-run confirmation cannot, and
the instrument that used to settle such a pair by re-scoring recorded answers
went with the engine by the user's own decision.

**26 unrecorded sweeps.** Tonight's artifacts, deliberately not recorded.
`--append` refuses them because `stale_sides` calls the column stale, and
`--record` would replace a 12-run column with a single run -- discarding the
pooled python-era runs the user explicitly asked to keep. Neither is right, so
the artifacts sit on disk and the audit says so, which is true.

## K: THE CRITERION WAS WRONG, AND THE PORTABLE SURFACE IS FOUR TIMES LARGER (2026-09-25)

### What the user corrected

This plan filed ~32 of 171 checks as portable, on the reasoning that MEASUREMENT
and DECLARATION TABLES are python's by nature. That was wrong. The user's
correction: *"there may be parts of the code in the measurement that can and
should be ported to typescript, and it may be possible to move the access code
for declaration tables to typescript too (with the content of course living in
$COURSE_METADATA, and the access code being relativized to need that
specified)... for a course that uses SlotSheetGrader (which is what sets our
handout course apart from the other psychology SBAs)."*

That is this project's own GENERICITY TEST, which asks what the CONTROL FLOW
assumes rather than what data it touches. "Did this run judge anything at all?"
is a question about the SHAPE of a recorded result; it is generic for any course
scored by `SlotSheetGrader`, and only the data is ours.

### The access layer, and whose discipline it copies

`enforce/courseData.ts` reaches `$COURSE_DATA` and `$COURSE_METADATA` exactly as
`resolveCorpusRefs.corpusDataPath` already does: the location is SUPPLIED, never
assumed, and an unset variable THROWS. It also refuses a path that resolves
outside the named root -- a rule that can read any file is not a rule about this
course. Both refusals are fire-tested.

**A refusal is never a finding of zero.** Every failure path throws, so a caller
cannot mistake "I could not read the corpus" for "the corpus is clean".

### Five ported, and they cover all four shapes

    no_case_names_in_prompts                 a regex over shipped prompts
    prompt_prose_names_only_offered_verdicts  real logic, two arms, pick groups
    computed_rules_do_not_share_a_key         structural collision over the rubric
    no_cell_is_both_corrected_and_declared    DECLARATION TABLES ($COURSE_METADATA)
    no_recorded_run_is_verdictless            MEASUREMENT ($COURSE_DATA)

plus two probes (`resolve_corpus_refs`, `parse_slot_specs`) that replaced the
ad-hoc TypeScript those two grammar scripts wrote to a temp file at run time,
and `score_recorded_sheets`, which is itself a measurement-side port -- it reads
recorded artifacts and re-derives scores through the shipped scorer.

36 vitest fixtures, a wire self-test, and an end-to-end fire through the live
python path for every rule. That last one keeps earning its place: the
offered-verdicts fire got NOTHING first time, because the slot it aimed at has
since migrated to a `rule` and is correctly skipped. The case was wrong, not the
port, and only a test against the live tree could tell those apart.

### The disposition of all 171, and what it is worth

    132  PORTABLE
          40  now, self-contained
          32  now, content only
          33  via courseData ($COURSE_DATA -- measurement)
          27  via courseData ($COURSE_METADATA -- declaration tables)
     34  PYTHON-ONLY
          21  read our own source (inspect.getsource and kin)
          13  about our documents and inventory
      5  DONE

**TREAT THIS AS EVIDENCE, NOT A RESULT.** It is a machine disposition keyed on
what each check IMPORTS, and this plan has already recorded that every automated
attempt at this sort was wrong in a way only reading found -- two earlier passes
disagreed violently, 75% against 19%. The buckets are a work list to READ
against, and the one number in them that is certain is the 5.

The 21 that read our own source are the only ones that die with the python they
interrogate. The 13 about documents could move if the documents did, which is a
different goal. Everything else is a day of reading and a port each, and the
mechanism for the port now exists and is proven on all four shapes.

## THE CONFIRMATION RUNS ARE POOLED (2026-09-25): 26 + 26 FINDINGS DOWN TO 11

The chain the user authorised, and what each step actually proved.

### The rescore: 5,668 of 5,668

`lo_rescore.py` reconstructs what the model ANSWERED for every recorded web
cell and runs it back through the SHIPPED `scoreSlotSheet` -- the goal-K bridge,
calling the app's own scorer with the eleven arguments `SlotSheetGrader:115`
passes. Holding the answers fixed removes the model, so what is left is
arithmetic:

    control (+0.5 on every recorded value): 5668/5668 moved
    reproduce exactly: 5668   differ: 0

**The control is not ceremony.** A comparison that cannot fail is not evidence
of agreement, and this family has failed exactly that way before: an options bag
reached `explicitMax`, every score came back NaN, `Math.abs(NaN - x) > 1e-9` is
FALSE, and every cell "matched". `lo_rescore` REFUSES to report unless +0.5
moves every cell.

THREE ITEMS ARE NOT COVERED AND SAY SO. `1b`, `T1` and `T2` are
`data_presence`/`type_stated`: their slot sheet is not an `<LLMAction>`, so
`load_action` -- which assembles its nine tables from an `<LLMAction>` opening
tag -- has nothing to read. Mirroring its assembly for three items would be a
SECOND sheet reader, which is the divergence class this project exists to close.
They were refused at append time rather than waved through on the argument that
they are deterministic.

### What replaced WEB_CODE_NEUTRAL

`measured.staleness_is_answered` accepts exactly two answers and refuses the
rest:

  * the scorer moved and EVERY recorded cell re-scores identically, evidenced by
    `$COURSE_DATA/out/rescore_evidence.json`, which must name THIS column's
    recorded sha as `from` and today's as `to`;
  * the prompt TAG moved and the ASK did not -- which `status` already
    distinguishes, and about which it already says "re-record, do not re-sweep".

The difference from the table it replaces is that the claim is DERIVED. An entry
was previously a person asserting two shas were score-neutral; it is now a
measurement that names the cells it covers and the control that proves it could
have failed.

### THE APPEND LOST DATA ON ITS FIRST ATTEMPT

`append_runs` read `_runs_path` -- the artifact the ledger POINTS AT -- and
those columns are the union of two files, because goal O folded the eliminated
engine's runs in via `folded_from`. So appending one run to 1a read the primary
file's six, wrote seven, and `record` replaced a TWELVE-run column with it.
The ledger read `runs: 7` where it had said 12.

Caught on the run-count readout one command later and restored from a backup
taken one command earlier. **Nothing was lost, and only because the backup
existed.** `append_runs` now pools `_runs_doc` -- the column as it is actually
counted -- and the story is its comment.

### Where the ledger stands

    23 web columns  12 -> 13 runs      (1b, T1, T2 refused: no rescore evidence)
    18 paper columns    +1 run         (8 refused: paper scorer stale since before tonight)
    total olx runs      323 -> 334

    WEB COLUMN IS NOT STAMPED BY THE APP'S OWN CODE   26 -> 3
    A SWEEP ON DISK WAS NEVER RECORDED                26 -> 8

### TWO FINDINGS THE APPEND CREATED, AND THEY ARE THE USER'S TO SETTLE

Adding a thirteenth run moved two medians, and the accounting noticed:

  * **Q4a/p3** is named by OPEN subgoal Q67 and now scores RIGHT at the median
    on every side. Q67 is entirely ABOUT that cell, and it cites medians
    (`olx 4.00 / python 5.00 / paper 3.00`) that no longer exist -- the python
    column was eliminated and the numbers have moved.
  * **1c/p7** is wrong on paper (gold 10, we record 8) and no open subgoal names
    it. More data made it wrong; that is information, not damage.

NEITHER WAS ACTED ON, deliberately. `goals.CLOSURES_APPROVED` records every
closure in this project as "closed ... **on the user's instruction**", and the
check's alternative -- "drop the cell" -- would gut a subgoal whose whole
content is that cell. Filing a new subgoal for 1c/p7 is the same kind of call.
Both are reported rather than decided.

## WHERE THE DATA FILES BELONG (2026-09-25)

`scoring/` held fifteen `.json` files. Classified by WHAT THEIR KEYS ARE, not by
their names -- `GOAL_STATES.json` has six keys that pattern-match an item id and
is not course data at all.

### Six are course data and move to `$COURSE_METADATA`

    MEASURED.json           `items` keyed by the 26 course items
    CARRIED_NOTES.json      keyed `1a`, `Q4b`, `handout:2`
    PROBED.json             records of {item, cells, artifact, runs}
    PROBE_RECEIPTS.json     {item, slot, question} -- probed text per course slot
    DESIGNED_TEXT_SHA.json  keys `1a|baseline_week|desc` -- shas of shipped course prose
    LEAKAGE_REVIEWED.json   keyed by sha of course prose, labels naming `Q5 credit.rule`

Each gets a `paths.COURSE_*` constant in the shape `COURSE_FILE` and
`COURSE_FIXTURE` already use, so there is ONE spelling per file. There were
NINE path constructions across six files, in four different idioms --
`Path(__file__).parent`, `_HERE_DIR`, `os.path.join(HERE, ...)` and
`paths.SCORING` -- and `enforcement.py:1914` built `MEASURED.json`'s path
independently of `measured.LEDGER`, so it would have gone on reading the old
location after any move. That second spelling was a latent bug before this.

### Six are engine data and stay

`DEFINITIONS.json` (module inventory), `COURSE_DATA_BUDGET.json`,
`PROPERTY_BUDGET.json`, `PROPERTY_BUDGET_REPORT.json`,
`STUDENT_TEXT_BUDGET.json` (keyed by OUR document paths), `GOAL_STATES.json`
(keyed by our subgoal labels).

### Three are neither, and are DEFERRED with a decision recorded

`GRADER_INPUTS.json`, `PEG_FORMATS.json`, `SHAPE_INVENTORY.json` describe
LO-BLOCKS' OWN REGISTRIES -- which inputs each grader block pairs with, which
authoring formats exist, which blocks are registered. `SlotSheetGrader` appears
in two of them as ONE ENTRY among many block types, not as their subject: the
sentence that mentions it is drawing a contrast ("Contrast SlotSheetGrader,
which scores a STRUCTURED sheet of slots"). None measures anything.

**AND ALL THREE ARE GENERATED EXPORTS.** `grader_inputs.py:454` dumps the
python `GRADER_INPUTS` dict and `json["declared"] == GRADER_INPUTS` exactly;
`peg_formats.py:231` dumps its registry the same way. Moving an export to a new
directory looks like progress and changes nothing.

THE USER'S DECISION, 2026-09-25: *"We should be simply getting exports when we
need them rather than storing a copy for convenience."* So the work is not a
move at all -- it is to DERIVE these when a check needs them and stop keeping a
stored copy that can go stale. A stored export is a second source of truth, and
this project already has a name for what that does.

One genuinely course-specific slice is buried in `SHAPE_INVENTORY.json`:
`coverage/used` records which blocks THIS course uses. That is a split, not a
move, and it belongs with the derive-on-demand work rather than before it.

## O'S UNFINISHED TAIL (2026-09-25): THE WEB COLUMN IS FINGERPRINTED AGAINST A SCORER THAT NO LONGER SCORES IT

Found while asking why a 1-run additive web sweep could not be recorded. It is
the cause of every `STALE SCORER` verdict on the `olx` column, and it is not a
measurement problem -- it is the last piece of the python web engine.

### The evidence, not the argument

`measured.scorer_sha(item, "olx")` hashes the closure of `_parts_for(item)`,
and that table still names the eliminated engine:

    _BY_KIND = {"slots":      ("agreement", "score_slots"),
                "oc":         ("agreement", "score_oc"),
                "oc_cadence": ("agreement", "score_oc_cadence")}

* `agreement.score_oc` and `agreement.score_oc_cadence` **no longer exist.**
  `_scoped_closure` cannot resolve them, so the fingerprint hashes the literal
  string `<missing agreement.score_oc>`. Eight items are stamped this way:
  DAY1, DAY2, NP, NR, PP, PR, WK1, WK2.
* `agreement.score_slots` **exists and has no call sites.** Verified: the only
  occurrences outside its own definition are docstrings and `_BY_KIND` itself.
  It is the python mirror of `scoreSlotSheet`, kept alive solely so that a sha
  can be taken of it.

So the ledger's answer to "has the code this item's score depends on changed?"
is computed from a function that does not score it, and for a third of the
corpus from a function that does not exist.

### What follows, and what does not

**It does not mean the recorded numbers are wrong.** Nothing here touched a
score. `check_web_code_is_stamped_by_its_own_sha` has been tracking the app's
real scoring code all along, separately and correctly, and its 26 findings say
what is actually true: the columns were recorded against app code that has
since changed.

**It does mean two signals are reporting the same fact, one of them wrongly.**
`STALE SCORER` on the `olx` row is noise; the web-code stamp is the signal.

**And it is why `--append` refuses the confirmation sweep.** `append_runs`
consults `stale_sides`, correctly: runs may be pooled only when they sample the
same prompt, scorer and cells. It refuses on a verdict derived from the dead
mirror rather than on the real one.

### The fix, and why it was NOT done on the night it was found

The `olx` column's number is produced by lo-blocks' `scoreSlotSheet`, compared
to gold by `handouts.scores_as_exact` / `attainable_scores`, with unrecorded
computed slots recovered through `agreement.satisfied_map` / `apply_computed`.
Those are the parts that belong in its fingerprint. `_BY_KIND` is not one of
them for this side, and `web_code_sha("score", item)` is.

Three reasons it was filed rather than applied at 01:10:

1. **A 5-hour sweep was in flight.** `era_stamp` writes `scorer_sha` into every
   artifact as it is produced; changing the function mid-sweep stamps the first
   items differently from the last, which is the inconsistency the era stamp
   exists to prevent.
2. **It changes ledger semantics, not one call site.** `status`, `stale_sides`,
   `append_runs`, `record` and several checks all read it.
3. **It would not have changed tonight's outcome.** Every recorded row holds a
   PYTHON scorer_sha; after the repoint, current would be a web sha and every
   row would still read stale -- correctly this time, because the app's scoring
   code genuinely did change tonight. The append stays refused either way. The
   fix buys a true signal, not a clear audit, and buying it under a running
   sweep is the wrong trade.

Next session's first item, and it should carry the retirement of
`agreement.score_slots` and of `oc.score_web` / `score_web_cadence` /
`web_deductions` / `web_deductions_cadence` with it -- the same corpse, in the
course scorer. Note that `enforcement.py:3997-4073` reads `oc.score_web`'s
SOURCE through `_source_through_delegates`; those checks need dispositioning in
the same pass, not deleting around.

## K IN PROGRESS (2026-09-25): THE BRIDGE EXISTS AND TWO RULES HAVE CROSSED IT

The first pass stopped at a sort nobody trusted. This pass did not re-sort. It
built the MECHANISM the goal needs and proved it on two real checks, because a
classification with no way to act on it is what the last pass already produced.

### What "moved to lo-blocks" now means, concretely

The user's framing: *python programs that do the work of the existing scripts,
but with as much of that work as possible moved to testing functions inside
lo-blocks, called by the python functions.* Applied to a `check_*`, that splits
it in two:

  * **Python keeps the FETCH and the REPORT.** It knows where the inputs live
    (`olx_prompts`, the rubric view, `paths`), and `equivalence.py` invokes it.
  * **TypeScript takes the JUDGEMENT**, as a pure function in
    `packages/shared/lib/llm/enforce/`, next to the code it is judging and
    exercised by vitest against its own fixtures.

    scoring/lo_enforce.py            -- the bridge: one tsx process per call
    lib/llm/enforce/runner.ts        -- stdin {check,payload} -> stdout {findings}
    lib/llm/enforce/index.ts         -- RULES, the name registry python dispatches on
    lib/llm/enforce/enforce.test.ts  -- the FIRE tests

`runner.ts` reads stdin rather than argv because a payload can carry every
shipped prompt in the corpus, and a check that silently truncates its input
reports clean for the wrong reason. Every failure path in `lo_enforce.run` --
missing `tsx`, a throw, a timeout, an unknown rule name -- returns a FINDING
saying the rule could not be RUN. A check that reports clean because it never
ran is the defect this audit exists to prevent.

### The two that crossed, and what each one cost to port faithfully

**`no_case_names_in_prompts`.** A regex over every shipped prompt. The first
draft of the port wrote `\bp\d{1,3}\b` for python's `(?<![\w/])p\d{1,2}\b` and
would have passed a corpus-only test suite, because BOTH report zero against a
clean corpus. The two details are the whole rule: `(?<![\w/])` excludes the
`p10` inside a corpus-reference PATH, and `{1,2}` is a cohort of twenty.

**`prompt_prose_names_only_offered_verdicts`.** Real logic -- two arms, a
`pick(NAME)` group resolved out of `choices=`, and a `rule` precedence that
hands the slot to a different check. Python still resolves the four views; TS
decides.

### THE OBLIGATION IS NOT SATISFIED BY VITEST ALONE

Goal K's standing rule is that a ported check must FIRE on the case its python
original fires on. Both ports report ZERO against the live corpus -- so does a
rule deleted to `return []`, and so would a broken bridge. Three separate
proofs are therefore kept:

  1. vitest fire fixtures (14), including the two details above;
  2. `lo_enforce.self_test()` -- that a finding raised in TypeScript ARRIVES in
     python, that clean input arrives as silence, and that an unknown rule name
     is a finding rather than a pass;
  3. an end-to-end fire through the real python path, by injecting the fault
     into the live inputs: 23 findings for a case name pushed into every
     prompt, 1 for an unofferable token in `Q5:example_1`'s note, 0 once
     restored -- with python's original finding wording reproduced exactly, so
     a baseline diff cannot mistake a port for a new fault.

The third proof is the one that caught something: the first attempt fired on
`Q5:example_2` and got nothing, because that note has since migrated to `rule`
and is correctly skipped. The fire case was wrong, not the port -- but only a
test that runs against the live tree could tell those apart.

### The sort, redone by reading (2026-09-25)

171 live checks, classified by the criterion the first pass arrived at -- what
the QUESTION is about, not which modules the body imports. The imports were used
only as evidence, one line per check beside its own first docstring line.

    CONTENT (the rule can live in lo-blocks)          ~32   19%
    CROSS-SIDE (two paths must agree)                  18   11%
    MEASUREMENT (recorded runs, the ledger, gold)     ~28   16%
    DECLARATION TABLES (our claims, re-tested)        ~30   18%
    OUR PYTHON (source, inventory, documents)         ~63   37%

**~32 CONTENT, not the first pass's 58.** That pass called its 58 "candidates,
not a work list" and warned the false-positive rate was real. It is: the
difference is almost entirely checks whose subject turns out to be a
DECLARATION TABLE of ours that happens to be *about* content, which is our
python's business and not the app's.

### THE CROSS-SIDE BUCKET, AND WHETHER O LEFT IT STANDING ON AIR

Eighteen checks ask "do the two X agree". The python web SCORER was eliminated,
so the first question is whether they now compare something against nothing.
**They do not.** What O removed was the scoring mirror -- `SCORERS`, `DEDUCERS`,
`score_sheet`, `slot_deductions`, `measure_one`. The ASK paths all survived and
are all still called:

  * `agreement.build_schema` / `apply_computed` / `satisfied_map` are live --
    `measured.py` uses them to RECOVER a computed slot that was not recorded
    (measured.py:1497, 5565), and enforcement calls them in three places. A
    divergence between the app's schema and that one would silently corrupt the
    recovery, which is exactly what these checks are for.
  * `score.py` (the paper/CLI prompt) is live and is one side of four of them.

So the eighteen compare app-vs-harness or CLI-vs-app, and both sides of each
are reachable code. **What IS stale is the vocabulary.** "The two engines" meant
two SCORERS when these were written and now means two ASK paths, and a reader
who takes the phrase at face value will conclude the check is dead.

`check_mapped_slots_have_no_unreachable_verdict` was the first case found and
is fixed: it argued the orphan verdict was "dead on the python mirror, live on
the app", and the invariant survives the mirror perfectly well -- the sheet
offers an answer the map has no rule for. Rationale rewritten 2026-09-25, logic
untouched, still reports 0.

**The remaining seventeen have not been reread.** That is the next unit of K
work, and it is a rewrite of prose, not of logic: for each, say which two live
paths it compares and why they must agree, so the check survives the next
reader. A SECOND question is owed for each and was not answered tonight --
whether it still examines a non-empty set. Both sides being live code does not
prove the loop between them iterates, and a check that compares nothing reports
clean. Proving that needs a perturbation per check, which is a day's work of
its own and must not be guessed at.

### What is NOT done, and the honest size of the rest

169 of the 171 live checks have not moved. The first pass's warning stands:
sorting them is a day of READING, and three automated attempts have each been
wrong in a way only reading found. This pass deliberately spent its time on the
mechanism instead, so that the reading, when it happens, has somewhere to land.

Two things learned here that the sort will need:

  * **A rule is portable only if its INPUTS are serialisable.**
    `check_prompts_carry_no_process_history` looks portable from its docstring
    and is not: it delegates to `leakage.process_findings`, which carries a
    declared conventions table and a kind taxonomy. Porting it means porting
    `leakage`, which is a goal of its own.
  * **Some checks became partly moot when O landed.**
    `check_mapped_slots_have_no_unreachable_verdict` argues from "the python
    mirror derives this slot and can never answer that" -- and the mirror was
    eliminated. The INVARIANT survives (a slot offering what its map cannot
    emit is still incoherent); the RATIONALE needs rewriting. K's first pass
    predicted exactly this entanglement.

## M STEPS 1 AND 2: THE ENUM COMPARISON IS DECLARED (2026-09-24)

`TYPE_MISMATCH` was the last rule stated twice. It is now stated once:

    <Equals key="matches_chosen_type" left="observed_type" right="named_type"
            lenient="unclear" note="This example is {observed}, but you chose {named}."/>

plus the slot's own `charge="TYPE_MISMATCH"`. Operands, lenient values, code and
wording all come from the rubric; `derive_ledger` reads them.

**Step 1 had to land first, and it is why this was blocked.** M said so: "a
scorer receives an ITEM DICT, and slot vocabularies live in the rubric view's
`SLOT_SPEC`, keyed by item. Until a scorer can read those, an enum comparison
cannot be declared -- only hardcoded." The minimal form is `slot_charges` on the
item, carried exactly as `oc_gates` and `oc_conjunctions` are, rather than
handing the scorer a global table.

**The operands could not be assumed, and that is the point.** D1 and D2 declare
the SAME key over a DIFFERENT left operand -- `defines_type`, not
`observed_type`. The hardcoded call was right for the four items it ran on by
coincidence of which items it ran on.

    fingerprint reproduces -- the ledger does not move
    <Equals> removed / lenient emptied / note removed: all LOAD-BEARING
    slot_charges removed: RAISES, rather than defaulting to a hidden code

### AND THE GUARD COULD NOT SEE THE ONE THING THE STEP IS ABOUT

M's emphasis on this step is `unclear`: "not an edge case here, it is a declared
verdict that must not charge." **Emptying the lenient list changed nothing**, so
the fingerprint could not tell a correct lenient list from an absent one.

The sweep offered `""` for `observed_type` and `named_type` -- a value NEITHER
slot admits -- and never produced `none` or `unclear`, which both do. It now
reads each fact's declared enum from the scorer's own schema
(`observed_type: PR/NR/PP/NP/none`, `named_type: PR/NR/PP/NP/unclear`). Case
count unchanged at 115,200; with the values corrected, every part of the
declaration is certified load-bearing.

**That is the third coverage hole this guard has had**, after the forbid rules it
never exercised and the facts it fed to items whose schema forbids them. The
pattern is the same each time: the sweep was written from a picture of the
answer space rather than from the DECLARED one, and every fix has been to make it
read what the item says it asks.

### Two readers refused the new attribute, and both were right

  * `check_course_schema_is_complete` -- `slot_charges` named no group. §9.2a
    makes that FAIL rather than default; declared in `RUBRIC_FIELDS`.
  * The ENGINE -- `Invalid attributes for <Equals>: Unrecognized key(s): 'note'`,
    and the static build aborted. This is exactly the case K cites as its
    evidence: the engine's zod schema is the only side that knows what an element
    may carry. Declared on `Equals.ts`.

`rubric_olx` now round-trips the note, so regenerating the rubric cannot silently
destroy the wording -- the failure `gate=` already had once today.

## O · ANSWERED WITH THE EXPERIMENT, NOT THE ARGUMENT (2026-09-24)

O said "revisit when M step 4 lands". It has, so this is the revisit.

### Precondition 1 is substantially met

`agreement.score_sheet` is a 67-line PURE INTERPRETER. Its only string literals
are `cond, counts, free, gates, onlyif, slots, verdict` -- structural field
names. No rules, no codes, no item ids. It cannot drift on RULES any more; it can
still drift on ARITHMETIC, because it is a second implementation of
`scoreSlotSheet` -- and `mirror_self_control` tests exactly that continuously,
currently olx 2,760/2,760 and python 2,908/2,908.

### THE 29% FIGURE WAS WRONG, and the experiment says so

Static analysis said 55 of 191 checks reach the python side. **Running it says
the audit barely notices.** Every runnable check was executed twice -- once
normally, once with every recorded python artifact suppressed AND the python
ledger column removed:

    checks run   185
    UNCHANGED    182
    changed        3   (one of which RAISES)

The 55 was counting checks that need the mirror's CODE, which retirement does not
remove. That is the fourth hand-written detector over source to give a confident
wrong number in one session.

### What actually changes, all three

| check | effect | is it a loss? |
|---|---|---|
| `check_items_are_measured_as_configured` | 26 findings | **No** -- it asks whether each item's number matches the CURRENT setup. Stop configuring a python column and it stops firing. A configuration statement, not a capability. |
| `check_computed_slot_recovery_is_faithful` | 1 finding | **Partly** -- loses one side's worth of input for "does recovering an unrecorded slot reproduce the recorded one?" |
| `check_scored_slots_are_answered_by_both_engines` | **RAISES** | **Yes, definitionally** -- "a slot the sheet gives POINTS to, answered by one engine and never the other" has no subject with one engine. |

**So the audit survives.** The honest cost is ONE check that loses its subject and
one that loses half its input -- not 29% of the machinery.

### THE RECOMMENDATION: retire the MEASUREMENT, keep the RUNS and the CODE

The framing that makes this answerable is the user's own -- retirement means
"dropping a column from the ledger and the associated runs". Those are separable,
and separating them gets the benefit without the destruction:

1. **STOP SWEEPING the python column.** This is the entire benefit the question
   was asked for -- "we have to sweep a lot fewer cells" -- and it costs nothing
   but a configuration change.
2. **KEEP the 2,908 recorded runs as history.** They cannot be recreated without
   re-running the sweeps that produced them, they currently reproduce their
   stored scores exactly, and keeping them costs disk.
3. **KEEP `agreement.py`'s mirror as an INSTRUMENT.** `rescore_recorded` drives
   it, and that is what verified the 26 provenance findings at no call cost this
   session. It is not the column; it survives the column.

That leaves exactly one real question for the user, and it is not a refactoring
question: **is the olx-vs-python axis worth its sweep cost going forward?** It is
the only SAME-INPUT comparison -- the user's own note establishes that paper and
web score DIFFERENT inputs, so no surviving pair can separate a prompt difference
from a model difference. Today that axis detects nothing
(`check_engine_rate_divergence` reports 0), which is what two agreeing
implementations look like and is not by itself evidence it is useless.

### A DEFECT FOUND BY THE EXPERIMENT, worth fixing either way

`check_scored_slots_are_answered_by_both_engines` **raises** `TypeError` on a
missing side rather than reporting. A check that crashes on absent input cannot
tell "nothing to compare" from "comparison failed" -- the same failure class as
the false-clean gate this session opened with, and it would fire the moment any
side is missing for any reason, not only retirement.

## O EXECUTED: THE PYTHON WEB ENGINE IS ELIMINATED (user, 2026-09-24)

**Decision: option 2 -- eliminate, and let `WEB_CODE_NEUTRAL` retire with it.**

The instrument question settled it. A first attempt REPLACED the mirror with a
TypeScript re-scorer (`rescoreRecorded.ts`) so `rescore_recorded` could keep
answering "did a lo-blocks change move a recorded number?" at no call cost. That
was reverted on the user's correction:

> "Except we shouldn't HAVE a new instrument. That's the whole point."

Eliminating an engine and rebuilding it in another language is not elimination.

### What the user's compensation is, and why the cost is not real

> "We should still be able to identify changes that only affect the logic by
> rescoring, and if we keep an ARCHIVAL COPY of each prompt instead of just
> calculating shas, we will be able to tell if engine changes change the
> prompts. So no cost really."

That is the right trade and it is better than what it replaces. A `prompt_sha`
says SOMETHING changed; an archived prompt says WHAT. The whole
`ASK_EQUIVALENT_PROMPTS` apparatus -- 31 rows declaring "this superseded prompt
asked the same thing", each self-checked against a second sha -- exists because
a hash cannot distinguish a tag-only edit from a changed question. With the
prompt itself on disk, that is a diff.

### What retires with the engine, sorted honestly

**Dead weight, exactly as O's own text predicted** ("a check that exists to catch
drift between two implementations is dead weight once there is one
implementation"):

  * `check_mirror_reproduces_its_own_scores`
  * `check_engines_score_identical_verdicts_alike`
  * `check_scored_slots_are_answered_by_both_engines`
  * `check_paper_scorer_agrees_on_identical_verdicts`

**Would have gone VACUOUS, and this is the pile that matters.**
`check_web_scorer_exercises_its_sheet` and `check_recorded_answers_are_complete`
GUARD on `SCORERS` membership and SKIP. With the registry gone they return 0
findings and look clean while checking nothing -- and the experiment that ran
every check with the engine removed counted them as "unchanged" for exactly that
reason. They are retired explicitly rather than left to skip.

**Retired with the mechanism:** `WEB_CODE_NEUTRAL` and
`check_web_code_neutrality_is_verified`. A neutrality claim that cannot be
verified should not stand unverified.

**Also going:** the two self-test fire cases that break `SCORERS["slots"]` on
purpose, and `probe.py`'s use of the registry.

### What STAYS, and is not the web engine

`apply_computed`, `build_schema`, `satisfied_map`, `answer_of`, `load_action`,
`expand_counted`, `BLOCKS`, `fixture_for`, `cheap_checks_gate`. `score.py` and
`oc.py` -- the PAPER scorer -- import these directly. They live in `agreement.py`
because that is where the module grew, not because they belong to the web column.
