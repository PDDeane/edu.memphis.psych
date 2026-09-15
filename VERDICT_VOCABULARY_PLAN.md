# One Verdict Vocabulary

*lo-blocks · slot sheets · migration plan*

Standardising what a verdict may say, so that authors never write one from scratch and the engine
can check every judgement it is given.

> 26 blocks · 182 slots · 25 vocabularies today — 2 repos — baseline: `web_v6`, `web_v7_run1`

> # RETIRED 2026-09-13 — COMPLETE, NOT A DEPENDENCY
>
> Verified stage by stage against the tree; the disposition is recorded in
> `RUBRIC_MIGRATION_PLAN.md` §12. **Nothing here is owed.** Do not sequence work around this
> document, and do not read the status table below as current.
>
> - **07 (Handout 2 rework) is DONE**, though the table below says otherwise. Its evidence was a
>   grep count: 21 occurrences of `matches_chosen_type`. That count meant legacy identity
>   vocabularies on 2026-08-20; today it counts a slot already at the target shape — all six
>   items have `observed_type`/`named_type` as PICKS answering `refers_to`, with the computed key
>   plain `met`/`absent`. **The marker outlived the thing it described.**
> - **04 is done in the content**: the four surviving `counts=` groups recorded 0 non-numeric
>   values in 480 observations. One dead fallback remains in `countedVerdicts`, folded into that
>   plan's stage 3a as optional cleanup.
> - **08 is subsumed**: the rubric object is the door it wanted to close.
> - **10 was already superseded**, so no sweep is owed — in particular none against
>   `web_v6`/`web_v7_run1`.
> - Its one named defect (`not_reason` on Q5's `example_2`) is **fixed**: 0 occurrences.
>
> Kept rather than deleted because the reframing below — *a verdict judges content; it is not the
> content* — is the reasoning behind the shape the sheets now have, and that argument is worth
> having on the record.

*Retrieved 2026-08-20 from the artifact published 2026-08-13
(`https://claude.ai/code/artifact/379e952f-24d3-4e76-92e5-ecad514ce92b`) and converted to
markdown. Status table at the foot is **as retrieved on 2026-08-20 and now stale** — see the
retirement notice above.*

---

## The reframing — a verdict judges content; it is not the content

> `PR`, `NR`, `PP`, `NP` were never verdicts. They are subject matter — the answer itself. A
> verdict answers one question only: **is the required content present?**
>
> Once the expected content is authored (or interpolated from the student's own earlier answer),
> identification stops being a judgement and becomes an ordinary `met` / `absent` check. That
> single move removes the permutation hack, two proposed primitives, and a whole kind from the
> design.

Today one mechanism — an ordered token list where `options[0]` means "satisfied" — carries four
unrelated jobs. The fix is not a richer verdict language. It is separating identification and
measurement out of `verdict` entirely, leaving it with exactly one vocabulary that the engine owns.

---

## Target — three fields, one vocabulary

**The per-check object in a published sheet**

| Field | Answers | Values |
| --- | --- | --- |
| `verdict` | Is the required content present? | `met` · `absent` · opt-in `unclear` · a failure reason |
| `refers_to` | Which item in the list does this box address? | a label from the cover group's own list, or `none` |
| `count` | How many? | integer |

`verdict` has one vocabulary everywhere, defined once in `slotSheet.ts`. A plain judgement slot
authors nothing at all — `key:Label`, no third segment. That is roughly 135 of the 182 slots, where
the migration *deletes* vocabulary rather than rewriting it.

### The canonical failure reasons

Six tokens replace ten. Each is a distinct diagnosis that drives different feedback, so collapsing
further would cost teaching content rather than noise.

**Failure reasons and what the student reads**

| Token | Replaces | Displayed as |
| --- | --- | --- |
| `wrong_kind` | `not_antecedent`, `not_active`, `not_consequence`, `not_reason` | not the kind of thing asked for |
| `incomplete` | `not_described`, `incomplete` | named, but not described |
| `duplicate` | — | repeats an earlier answer |
| `mismatch` | — | does not match what it should |
| `generic` | — | still the example's wording |
| `tick_values` | — | these are the axis's values, not a label |

> **Why a display map is not optional**
>
> `composeSlotFeedback` prints the raw token to the student — `· **First antecedent is a genuine
> trigger** — not_antecedent` — and `showChecks` defaults to true, so 23 of 26 blocks show it.
> Normalising tokens without a token → phrase map in the engine would make student feedback worse,
> not better. The map covers `met` and `absent` too.

---

## Where we are — what the 182 slots actually do

**Census by job — the four things one mechanism is carrying**

| Job | Slots | Scored | Becomes |
| --- | ---: | ---: | --- |
| Binary judgement | 103 | 54 | authors nothing |
| Binary judgement, polarity inverted (`no/yes`) | 32 | 0 | relabelled so `met` is the good state |
| Judgement + failure diagnosis | 17 | 17 | canonical reason tokens |
| Identity / classification | 21 | 8 | judgements, or `refers_to` |
| Count | 9 | 0 | `count` field |

The 32 inverted slots are the `uncertain` checks, all unscored. They become **"All judgments
confident — met"**, which removes polarity-by-ordering from the design entirely.

### The identity slots, individually

- **Operant type — 16 slots, disappears.** The four *scored* `observed_type` slots have *no*
  `equals` rule: the permutation (`PR/NR/…`, `NR/PR/…`, `PP/PR/…`, `NP/PR/…`) is the entire grading
  mechanism. Each screen already names its own type, so the slot becomes `demonstrates_type` →
  `met`/`absent` with `wrong_kind`. The 12 unscored pairs plus 6 `equals` rules collapse into 6
  judgements by interpolating the student's chosen type into the prompt.
- **Which-in-a-list — 4 slots, moves to `refers_to`.** This one genuinely needs identification,
  because `cover` must know which of 4a's antecedents each box addresses so two boxes cannot both
  claim the same one.
- **`matches`/`differs` — 1 slot,** a binary judgement in identity clothing. Becomes an ordinary
  judgement.

### Generalising which-of-two to which-in-a-list

`CoverGroup` is already `{ keys: string[]; labels: string[] }` and the claiming loop uses a `Set`,
so the arithmetic generalises to any N labels and M boxes with no engine change. Only the
vocabulary was fixed at two. So `refers_to` draws from the group's own label list, which comes from
either an authored list or a **state reference resolved at call time** — the schema is then built
per invocation, which `LLMAction` already does.

A side benefit confirms the split: today `neither` ("named something not on the list") and `absent`
("nothing here") are crammed into one field. They now land in different fields naturally.

---

## Simplifications — what earlier drafts proposed, and we are not building

- **An `equals`-against-literal primitive.** Existed only to compare an identity slot to a
  constant. With authored content there is nothing to compare.
- **Named verdict sets.** There are no domains left to name.
- **An `identity` kind.** Identification is a different field, not a different kind of verdict.
- **`require=` on cover groups.** Per-box distinct-claim already generalises; a default of "all
  boxes" is exactly today's behaviour. A future "cover at least k of N" is a *computed slot*
  alongside `equals`, not a threshold on cover.
- **A direction flag on counts.** All five `counts` groups count upward; the one inverted count,
  `reasons_failing`, is unscored and in no group.

---

## Sequence — ten stages, dependency-ordered

This spans two repositories and cannot land atomically. Each stage is independently verifiable, and
nothing is irreversible until the last.

**00 · Settle the display wording** — *content*
Student-visible phrasing for the six reason tokens and for `met`/`absent`/`unclear`. Applied
uniformly, so it is decided once.

**01 · Engine, permissive** — *lo-blocks* · *neutral*
Add the `verdict`/`refers_to`/`count` fields, the canonical vocabulary, the display map, and the
permanent legacy-read path. The old syntax still parses; the guard warns only.

**02 · Delete vocabulary from plain judgements** — *content* · *neutral*
~135 slots lose their third segment. Strip `verdicts=` from the 13 blocks that declare it, then
remove the attribute from the block schemas so defaults can no longer be redefined.

**03 · Reason tokens and the confidence relabel** — *content* · *neutral*
17 slots onto canonical reasons; 32 `uncertain` slots to "All judgments confident". All 32 are
unscored, so the polarity fix cannot move a score.

**04 · Counts to the `count` field** — *both* · *neutral*
9 slots. `countedVerdicts` reads `count` and writes canonical member verdicts instead of depending
on `options[0] === 'met'`.

**05 · Move the two derived emitters** — *lo-blocks* · *neutral*
`derivedVerdicts.ts` and `SelfMonitorPlot/dataVerdict.ts` emit `met`/`absent`/`mismatch` literally.
Today that is an unguarded coincidence; here it becomes correct by construction.

**06 · Cover generalisation** — *both* · *measure*
Q6's 4 slots to `refers_to`; cover labels resolvable from state; schema built per call. Points here
are already governed by cover rather than by `options[0]`, so the scoring path is unchanged — but
the prompt changes, so measure it.

**07 · Handout 2 rework** — *content* · *measure*
10 of 26 items. This is a change in *what is asked*, not a rename, and `matches_chosen_type` is a
**gate** — a change in its derivation can void whole items. The largest risk in the plan.

**08 · Close the door** — *lo-blocks*
Guard from warning to error; delete the legacy *authoring* parser while keeping the legacy
*reading* path. Add the content lint so the standard cannot erode.

**09 · Regenerate and re-declare** — *edu.memphis.psych*
`olx_prompts.py --write`, then `--check` and `equivalence.py --enforcement`. Audit `SLOT_NOTES`:
entries that exist only to announce "this reports an identity" are now dead. Update
`EQUIVALENCE.md`.

**10 · Acceptance** — *measure*
A **3-run** sweep against `web_v6` and `web_v7_run1`. One run cannot clear this — Q3 alone has
measured a 4-cell spread across runs.

---

## Correctness — what is proved, and what must be measured

Stages 01–05 are score-neutral *by construction*, and that is written as a check rather than an
argument: the migration is a scripted rewrite, and an assertion over the before/after pair confirms
that for every scored slot the new `met` corresponds to the old `options[0]`, and that no scored
slot gains a verdict it did not have. The script must also be idempotent — a second run produces an
empty diff.

`unclear` is kept as **opt-in per slot** precisely to protect this: 30 slots have it today and 24
scored slots deliberately do not. Making it universal would hand those 24 an escape hatch that
costs points, producing a score drop with no rubric change behind it.

Stages 06–07 are **not** neutral and no argument should pretend otherwise. They change what the
model is asked. They get measured.

### Facts that keep this cheap

- **Gold is safe.** `gold.py` contains no verdict strings. Gold is human-grader *points* from the
  paper corpus, and the harness compares points — so renaming cannot invalidate it.
- **The scorer is uncoupled.** The Python scorer and harness contain **zero** references to any of
  the ten failure tokens. They are pure data there.
- **No data migration.** `publishedSheet` stores the full `slots` array including options, so
  stored sheets are self-describing and re-score under the vocabulary in force when they were
  written.
- **One table, both repos.** `agreement.py` already extracts guidance functions from the TypeScript
  source. The verdict table and display map travel the same way, so the two repos cannot drift.

> **The one permanent compatibility burden**
>
> Because stored sheets carry their own `options` and no field split, `isSatisfied` and
> `composeSlotFeedback` must keep scoring old-shape sheets by the legacy positional rule
> *indefinitely* — this is not the staged authoring guard, which is temporary. Without it, every
> already-graded handout silently re-scores the next time a `ScoreTable` reads it.

---

## Also fixed — a live display bug this closes

`equals` overwrites only the *computed* slot, not its operands, so an unscored identity slot is
still run through `isSatisfied` for its ✓/· mark. A student on the Negative Punishment screen who
correctly answers `NP` currently sees

`· **Type named** — NP`

— a dot, as though they were wrong, because `NP` is not index 0 of `PR/NR/PP/NP/unclear`. Identity
slots stop being judged, so they render as a stated fact with no tick at all.

---

## Open — deliberately deferred

- **"Cover at least k of N."** Not expressible after this, by choice. When an item needs it, it
  arrives as a computed rule beside `equals`, sitting on per-box semantics that do not change.
- **The lost wrong-type diagnosis.** `observed_type` returning `NP` on the PR screen currently
  records *which* wrong type it was. Under a judgement that moves into `note` and `evidence` —
  where prose belongs, but it is a genuine change in what the sheet records.
- **Widening `unclear`.** Kept opt-in here so the migration stays neutral; whether more slots
  should offer it is a separate, measurable decision.

---

*Revision follows the reframing that a verdict judges content rather than being it · supersedes the
identity-kind and named-set drafts · companion to the prompt-assembly plan ("One Rubric, Two
Scorers", `RUBRIC_MIGRATION_PLAN.md`)*

---

## Execution status as retrieved (2026-08-20)

Unlike its companion, most of this plan **has** landed. Checked against
`lo-blocks@d712c299` and this repo's HEAD:

| Stage | State | Evidence |
| --- | --- | --- |
| 00 display wording | done | `VERDICT_DISPLAY` map in `packages/shared/lib/llm/slotSheet.ts` |
| 01 engine, permissive | done | `verdict`/`refers_to`/`count` on `CheckPayload`; canonical token list; legacy-read path documented at the parser |
| 02 strip `verdicts=` | done | no `verdicts=` attribute survives in any `.olx` (only two test fixtures in lo-blocks) |
| 03 reason tokens + confidence relabel | done | `wrong_kind`/`duplicate`/`tick_values` in the sheets; `confident:All judgments confident` is the standing wording |
| 04 counts to `count` | partly | `countedVerdicts` reads `count ?? verdict` — the dual-read is in, and 5 `counts=` groups still ride the legacy side |
| 05 derived emitters | done | `derivedVerdicts.ts` present as its own module |
| 06 cover generalisation | done | Q6 scores on `refers_to` with `none`; this session's work sits on top of it |
| 07 Handout 2 rework | **not done** | `matches_chosen_type` still appears 21× in `psychology/bmod_handout2.olx` |
| 08 close the door | **not done** | no error-level guard and no content lint; the legacy authoring parser is still live |
| 09 regenerate / re-declare | ongoing | `olx_prompts.py --write` + `--check` are the working loop; `SLOT_NOTES` not audited for dead identity announcements |
| 10 acceptance | superseded | measured per item since, not as one sweep against `web_v6`/`web_v7_run1` |

One defect the stage-08 lint would have caught, found while checking the above and left
unfixed. `bmod_handout1.olx:1072` tells the web grader to answer **`not_reason`** on Q5's
`example_2`, but the same line's `slots=` offers it `wrong_kind/duplicate` — the prompt names a
token that is not in its own enum, so that test is inert. This is precisely the failure the
`{fail}` mechanism at `olx_prompts.py:1682` was built to stop ("a rule naming one side's token
literally is unreadable on the other"), and it was built for the same slot family. But `{fail}`
is substituted into the rubric's `rule` text only (`olx_prompts.py:1698`); the offending string
is the `SLOT_NOTES["Q5:example_2"]` entry at `olx_prompts.py:1245`, a second source of prompt
prose that the substitution never touches. `not_reason` remains correct where it appears in
`rubric_h1.py:979` — that is the paper scorer's own vocabulary, bridged by `enforcement.ALIAS`.

Also note `scoring/migrate_verdicts.py`, the scripted rewrite stages 01–05 called for. It exists
and was run; it is not a live part of the pipeline.
