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

