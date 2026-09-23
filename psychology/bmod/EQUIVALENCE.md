see: qc:EQ.sweep

`out/web_v2`, all 26 items, 466 cells with gold on both sides, five excluded as
structurally unreachable on the olx. Built from the per-item JSON.

| | n | python | olx | cliMAE | webMAE | same score |
| --- | --- | --- | --- | --- | --- | --- |
| **ALL** | 466 | **90.8%** | **87.1%** | 0.17 | 0.29 | **91.2%** |
| H1 | 133 | 82.0% | 75.2% | 0.24 | 0.39 | 82.0% |
| H2 | 216 | 94.0% | 90.7% | 0.15 | 0.29 | 94.0% |
| H3 | 117 | 94.9% | 94.0% | 0.10 | 0.17 | 96.6% |

**Eleven items agree on every single cell** — D1, NP, PP, PR, T1, T2, 1b, 2a, 2b, 3.
**[web_v2 only.** On web_v8/v9, 2a is 14-16 of 18 and 3 is 20 of 20; the
reference re-run below invalidated every `from_scorer` fixture, 2a's among them.
Do not quote this list as current.**]**
All are criteria-path OC items or items whose checks are derived: where both sides run
the same sheet they are indistinguishable. **D2 and Q6 beat the python** (94 vs 89, 62 vs
56). **1c and Q1 are level** with it.

Where the olx still trails: Q4b (100 vs 75), Q4c (76 vs 65), DAY1/WK1 (89 vs 78),
DAY2 (83 vs 72), Q5 (100 vs 88). Every one asks the student for several things at once
and the olx splits them into boxes the reconstruction has to fill — DEVIATION 1, not
something the equivalence machinery can close.

**Five cells excluded**, each because the olx has REMOVED the failure rather than
missed it: 1c p4/p19/p20 (complete data, no graph or a written description of one — on
the olx that data draws a labelled chart), Q1 p20 (the UTB is a closed choice, so
"never declared it" cannot arise), Q6 p9 (a documented gold divergence plus a
consensus tie).

### Read the per-item numbers with the noise floor in mind

Q1 was run twice at the final configuration: **81% then 75%, one cell apart** (p18's
reason count moved 3 -> 2). At n=16 one cell is 6 points, so an item-level difference
under about two cells says nothing. The corpus figure is one run per cell throughout.

### Q4b is the largest remaining gap, and it is DEVIATION 1 with nothing behind it

python 100%, olx 75% over 16 cells — the biggest per-item difference in the corpus.
Investigated and deliberately LEFT ALONE.

**All four misses are one check**: `not_active` on `behavior_1`/`behavior_2`. The
modify slots agree on every cell, so the `onlyif` work holds. The direction is mostly
leniency — the olx credits what gold rejects on p4, p7 and p20 — but not uniformly:
on p16 it wrongly rejects.

**Ruled out, in this order:**

* *Fixture* — the `handsplit` boxes are faithful splits of the prose; the python reads
  the same words.
* *Context* — all eight refs seeded on every cell: UTB, Q1, Q2, both Q4a antecedents,
  all three Q4b boxes. Nothing empty, so not another `repair_orphans` case.
* *Guidance* — the ACCEPT and REJECT bullets are byte-identical in the two prompts,
  including the examples that name these very students.

**What is left is the SHAPE of the input.** The python reads one prose block and has to
decide whether there are two activities at all. The olx is handed two boxes whose
labels assert there are, and judges each alone.

p7 shows it cleanly. That student's own "1)" item is [[corpus Q4b/p7 modify 0:85 sha=277012b710a5]] — meta-commentary, which the
rubric names as REJECT case (b) and cites p7 for by name. The split faithfully puts it
in `behavior_1`, and under a heading reading "First example is something done during
the behavior" the model credits it. Reading the whole block, the python does not.

The story is not uniform, and p16 is the counter-example: its box holds [[corpus Q4b/p16 first 0:38 sha=b400463aa325]], which appears VERBATIM in the ACCEPT list, and the olx
returned `not_active` anyway. That is not box-priming; that is simply wrong.

**Why nothing was changed.**

* *More prompt text* — the guidance already names p7's shape and p16's example, and
  the olx receives both. Framing changes have never moved the numbers here (three
  attempts, all inside noise); a fourth aimed at cases the prompt already describes
  would be the least promising yet.
* *Re-splitting the fixture* — putting p7's meta-commentary in the modify box would
  match gold by deciding the answer in the fixture. That is fitting the fixture to
  the result.

Two of the four (p4, p20) are borderline for gold itself — "scrolling on tiktok" and
"sleeping in my car" are activities the graders read as outcomes. So the honest count
is one structural case, one olx error, two coin-flips.

One thing worth recording rather than acting on: a live olx student has a SEPARATE box
for the modify statement, so p7's confusion — numbering meta-commentary as item 1 —
is much less likely to arise on screen than on paper. Not unreachable the way 1c's
cells are, so it is not excluded; but the measured gap probably overstates what a live
cohort would show.

### Q4c: four of six misses are SHARED, and the olx-only gap is two cells

python 76%, olx 65% over 17 cells — and the headline overstates it badly.

**Four of the six misses have IDENTICAL verdicts on both sides.** p15 and p17 are the
documented `C_NO_KEYWORD` divergence, which the rubric declares outright: "the graders
enforced this unevenly (participants 15 and 17 kept the point despite omitting it);
the dictionary is explicit, so apply it." Both systems apply it and are wrong against
gold on purpose. p9 and p16 are shared misses — the two systems agree with each other
and differ from the graders.

**The olx-only gap is two cells:**

* **p13** — `keyword: absent` on the olx, `met` on the python. This student wrote
  "conequence", one letter short. The python's model reads through the typo; the olx's
  does not. It is the exact case examined when deciding NOT to replace this check
  with a regex — and the regex would have failed the same way the olx just did, so
  the earlier decision stands and this cell is the price of it.
* **p20** — `consequence_2` judged `met` on the olx, `not_consequence` on the python.
  An ordinary judgement difference.

    all cells                      python 76%   olx 65%
    minus the declared divergence  python 87%   olx 73%
    minus that and the shared      python 100%  olx 85%

Nothing to fix. Left alone. **[Superseded on all three counts, 2026-08-20.** The
denominator is 12 counted, not 17. The olx-only p13 gap was `keyword: absent` on
"conequence", which cannot arise now that Q4c's keyword slot is advisory with
`pts=None`. And three boxes WERE fixed — p13's and both of p16's kept the
student's enumerator. The readout also found that 12/12 measures only the accept
side of this item; see the fixture-audit section.**]**

### DAY2: two cells of cadence judgement, and a larger problem both sides share

python 83%, olx 72% over 18 cells. Five misses, and only two are olx-only.

**Both olx-only misses are the cadence gate**, which takes the whole item, so two
judgement calls produce the entire 11-point gap:

* **p8** — [[corpus DAY2/p8 day2 0:108 sha=9b3f489db805]] The olx answered `cadence_is_daily: no` and
  zeroed it. The prompt covers this shape THREE times over, including "a daily trigger
  whose reward runs to the end of the week is still daily" and an explicit tie-breaker,
  "when it could be read either way, it is daily". It received all of that and went the
  other way — the same class as Q4b's p16 and Q2's p7, where the prompt names the case
  and the model does not follow it. More text will not help.
* **p9** — [[corpus DAY2/p9 day2 0:89 sha=8db4bb08899f]] Defensible: "out of the 5 days" reads as exactly the
  whole-week tally the guidance names as the one reason to answer `no`. Gold and the
  python read it as daily.

**The three remaining misses are SHARED, and are the item's real problem**: p7 (gold
1, both 4), p13 (gold 0, both 4), p14 (gold 0, python 2, olx 4). Both systems credit
contingencies the graders refused. That is a rubric-versus-gold question on the OC
criteria, not a olx/python one, and it is where DAY2's accuracy actually goes — the python
loses three cells to it too.

Nothing to fix. Left alone.

### DAY1, WK1, WK2: six olx-only cells across 54, split evenly both ways

python 89/89/94, olx 78/78/83. Eleven misses in total; **five are SHARED** and six are
olx-only, and the olx-only ones do NOT lean one way — three too generous, three too
strict. There is no systematic bias to correct.

**Too generous** (crediting what gold and the python both reject):

* **DAY1 p6** — [[corpus DAY1/p6 day1 0:106 sha=15a19c9bc3c7]] Every gate passed. Criterion 4 names
  this exact shape: it fails "when the plan is purely to remove a temptation or set up
  the environment in advance, which is an antecedent manipulation rather than a
  consequence." The fourth instance of the prompt naming a case and the model going
  the other way, after Q4b p16, Q2 p7 and DAY2 p8.
* **DAY1 p13**, **WK2 p13** — vague answers with no arranged consequence, credited.

**Too strict** (gates firing on answers gold and the python accept):

* **WK2 p11** — "If I don[[corpus WK2/p11 wk2 9:53 sha=7e470e88f8aa]]t {{corpus:WK2/p11:wk2:56:76:sha=12dea3a69f2a:shape=S2-0a2020,R22-0-22}} **Every gate failed**, zeroing a plain contingency. Not a borderline call;
  a bad read, and the most expensive single cell in these three items.
* **WK1 p12** — `names_behavior: no` on [[corpus WK1/p12 wk1 0:92 sha=b4fa34d9b68e]] The behaviour is referred to
  indirectly ("meet my goal") rather than named, and the olx would not take it.
* **WK1 p19** — `targets_own_behavior: no` on an answer plainly about the student's own
  goal, costing 1.

**The shared misses are the more interesting half**, and they are one thing.
Participant 8 is a shared miss on ALL THREE items, and gold's reason is the same each
time: "This is not an example of operant conditioning. For PP/NR, you should state
what undesirable thing will…" Both systems credit those answers. WK1 p7 and DAY1 p1
are the same kind of disagreement (p1 in reverse — both systems reject what gold
accepted).

Taken with DAY2's p7/p13/p14, the H2 example items share one calibration gap: **the OC
criteria credit contingencies the graders called not-OC.** That costs the python as much
as the olx, it is a rubric-versus-gold question rather than a olx/python one, and it is
where these items' accuracy actually goes. The olx/python difference on top of it is six
cells in 54, scattered in both directions.

Nothing to fix on the equivalence side. Left alone.

### The "OC calibration gap" was mostly a decision already taken — a correction

The DAY1/WK1/WK2 write-up above concluded that the H2 example items share a
calibration gap, "the OC criteria credit contingencies the graders called not-OC",
and called it worth more cells than anything olx-specific. **That framing was wrong**,
and checking it took one query I should have run before saying it.

Both systems over-credit on **7 cells across the 8 OC items — none of them on
PR/NR/PP/NP**, all on the four intervention-plan items. They decompose:

* **3 cells are a DELIBERATE divergence already recorded in the code.** p8's DAY1,
  WK1 and WK2 answers state their contingency by what is AVOIDED ("[[corpus DAY1/p8 day1 104:130 sha=fdab95974d4c]]..."). `derive_oc_ledger` says outright: "the graders zeroed
  two of these on participant 8 for what was really a phrasing problem. Flag for
  review, never deduct." Both systems refuse to follow gold BY DESIGN, and both attach
  an advisory note saying so. Not a gap — a decision.
* **2 cells are named-case misses.** p7's UTB is electronic devices; their WK1 plan is
  about procrastination and their DAY2 plan about reading. The WRONG_BEHAVIOR guidance
  names this verbatim — "a plan about procrastination when the UTB is time on
  electronic devices" — and both systems still answered `targets_own_behavior: yes`.
* **2 cells are genuinely borderline** (p13, p14 on DAY2), where the graders were
  stricter than the criteria and the answers can be read either way.

So there is no systematic permissiveness to correct. What is left after the deliberate
divergence is two named-case misses and two coin-flips — the same shape as every other
item examined, and the same lesson: the guidance already describes these cases and
saying it again is not the lever.

**The divergence was missing from README's list**, which said "Five known, deliberate
divergences" and did not include the largest by cell count. Now six. Anyone measuring
the OC items should subtract those three cells before drawing conclusions — which is
exactly the mistake made here.

### Q1's `utb_stated` reads the CHOICE on the olx, and two prompt bugs behind the count

**The check was scoring rhetorical form.** p17 and p20 both NAME their behaviour in
the prose — [[corpus Q1/p17 response 0:40 sha=9086cd1358c1]], [[corpus Q1/p20 response 0:42 sha=985d50a12bff]] — what they lack is a sentence declaring it as their *target*. On paper
that distinction did real work: with no dropdown, the prose was the only place the
target could be identified. On the olx the student answers "Which behavior will you
work on?" from a closed choice BEFORE reaching the box, so requiring the prose to
declare it again scores form for a fact the interface already holds. It is also the
one rule the graders could not apply consistently — p17 kept the points, p20 lost
them, on materially identical answers, which is itself evidence the distinction is
too slippery to carry 2 of 5.

So the olx derives it: `derived="utb_stated:present:bmod_h1_utb"`. Declared per-key
in SCORING_DIVERGENCES; the guidance bullet describing the prose test is omitted on
the olx, since it asks for a judgement the olx is not given a slot to report. **p20 is
excluded** — its deduction cannot arise there. p17 needs no exclusion: the olx now
agrees with gold on it.

Note this keeps UTB_NOT_STATED **reachable**: a student who skips the choice loses the
2 points. That also closes the robustness gap where an unselected UTB was absorbed
silently — `CorrectGrader` on that CapaProblem scores nothing and never fails.

**Two prompt bugs surfaced while chasing the reason-count offset**, where the olx read
one reason fewer than the python on every disagreement:

* The olx checklist still listed `reason_1`, `reason_2`, `reason_3` individually
  ALONGSIDE `reasons_given`, while the schema accepted only the count —
  `_checklist_section` knew about `equals` and `derived` but not `counts`, so the olx
  got two framings of one judgement and no "DO NOT ANSWER" line. The python had one.
* Q1's new derived line was emitted with **1c's graph wording** ("satisfied when EVERY
  week of data is present"), because the DO NOT ANSWER text was hardcoded to the
  plots/complete kind rather than varying by it.

With both fixed the counts agree on 14 of 16 cells, up from 13 with a systematic
one-lower offset on all three. p9 and p16 remain, and are genuine disagreements about
what counts as a distinct reason rather than a framing artefact.

**Q1: olx 76% -> 81%, MAE 0.29 -> 0.19 — now level with the python's 81%.**

Corpus: **python 90.8% / MAE 0.17, olx 87.3% / MAE 0.28, same score on 91.4% of 466
cells.**

### 1c gates on COMPLETE data — the olx's equivalent of the graph check

The paper item charges the whole 10 for not supplying a graph. The olx draws the
graph, so that exact failure is gone — but the analogous one is not: **a chart
missing weeks is not the graph the item asks for**, and the runtime can see it. So
`has_own_graph` changed kind from `plots` to `complete`:

    derived="has_own_graph:complete:<four week refs>:<template data>"

`complete` is satisfied only when EVERY week holds data; a partial month is `absent`
and fails the gate, costing the whole item exactly as the paper rubric does. It stays
lenient WITHIN a week — a short week is still a week, because that is 1b's business
and the rubric says not to deduct for gaps. And it still catches the worked example
once the month is complete. Seven new tests, including one pinning that `dataVerdict`
(1b's reading) still says `met` on the same partial data `completeVerdict` rejects.

The feedback names the gap rather than just failing: *"2 of the 4 weeks hold no data,
so the graph covers only part of the month. Enter all four weeks — the baseline week
and weeks 1, 2 and 3."*

**Measured: 1c 70% -> 87%.** p15 (two of four weeks, gold 0) is recovered by the gate
and p18 (nothing at all, gold 0) stays correct.

**Three cells are excluded as unreachable** (`agreement_app.PER_ITEM_EXCLUDE`), all
the same failure in different forms — a student whose DATA is complete and whose
GRAPH is not the answer the paper item wanted:

* **p4, p19** — four complete weeks, no graph at all on paper, gold 0. Nothing the
  runtime can observe distinguishes them from the sixteen who charted: their per-week
  counts are identical.
* **p20** — supplied a written DESCRIPTION of a graph, which the rubric names as this
  item's "did not include" ("Participant 20 wrote exactly that"). On the olx a
  description IS the answer: those labels are typed into fields and the chart is drawn
  from the four complete weeks, so there is nothing left to fail.

p15 and p18 are deliberately NOT excluded — their data is incomplete, and the
completeness gate catches both, which is the whole point of adding it.

The distinction that decides the list: an item is excluded when the olx has removed
the failure, not when the olx fails to notice it. Every excluded row has complete
data; every retained row with a gold 0 has data the gate can see is short.

Corpus after this, honouring the declared exclusions: **python 91.0% / MAE 0.16, olx
87.2% / MAE 0.29, same score on 90.8% of 468 cells.** H3 agreement is now 95.8%.

### One registry for the primitives, and a check that all four consult it

Every primitive has had to be taught to FOUR places — `slotSheet.ts`, the block that
wires the attribute, `probe.test.ts`, and the prompt generator — and the generator was
missed twice. `derived` shipped, and later `counts`, with their keys still listed in
the olx checklist while the response schema refused them: the model asked for answers
it could not return, alongside the thing meant to replace them. **Neither showed up in
any score**, because the grader ignores surplus verdicts.

`packages/shared/lib/llm/primitives.json` is now the single list, read by all four:

    sheetAttributes: id, target, slots, verdicts, max, showChecks
    primitives:      cover, equals(excludesKeys), onlyif,
                     derived(excludesKeys, kinds: plots|complete|present),
                     counts(excludesKeys)

`slotSheet.DERIVED_KINDS`, `olx_prompts.DERIVED_KINDS`, `primitive_attrs()` and
`equivalence.KNOWN_ACTION_ATTRS` all derive from it rather than restating it.

**But a registry is only a declaration, and this project's declarations rot.** So
`check_primitive_conformance()` verifies the behaviour instead: for every live sheet
and every primitive whose keys leave the schema, the generated prompt must NOT list
those keys in the checklist and MUST carry a line telling the model not to answer
them. Empirical, over the real content, in the same spirit as probing rather than
mirroring.

It was tested by reproducing both shipped bugs — blinding the generator to `counts`,
then to `derived`:

    generator blind to `counts`:  Q1: `reason_1` is excluded from the schema but
                                  still listed in the checklist the model fills  (x3)
    generator blind to `derived`: 1c: `has_own_graph` ... still listed
                                  1c: `has_own_graph` ... prompt never tells the
                                  model not to answer it

Both caught. The first case is in the self-test, which is now **14/14**.

What this does not cover: a primitive added to the registry and to `slotSheet` but
never parsed in `LLMAction`, which would leave the attribute inert. `probe.test.ts`
asserts its own handled list matches the registry, which catches the audit going
blind; the block wiring is still checked only by the item working at all.

### Fixture provenance is now reported with every rate

Any analysis over `simulate_h3`-reconstructed fields reports WHERE each value came
from, not just that one exists:

    reconstructed field provenance: {'model': 60, 'chart_xml': 16, 'weekly_total_spread': 4}
      trust: chart_xml (literal) > model (transcribed) > weekly_total_spread (computed)
    *** 4 field(s) across 1 cell(s) are SYNTHESISED, not recorded:
          p12/1b: Counter({'weekly_total_spread': 4})

`spread_total` turns a weekly total into seven daily values summing to it, and the
result is indistinguishable from a student who logged seven numbers unless the
provenance is read. One participant is affected — p12 logged "days met goal (out of
7)" as four totals — and it appears in both 1b and 1c, so **1b's 100% on both sides
includes one cell whose four weeks are arithmetic**. Defensible (the student did
supply data for all four weeks, and gold agrees at 4.0), but it belongs next to the
number.

**Why this was added.** Comparing the students who supplied a chart against those who
did not, all 16 chart-supplying rows showed exactly `[7,7,7,7]` — and that uniformity
was used as evidence that data completeness separates the groups. Sixteen independent
human submissions do not agree to the value; `simulate_h3`'s own docstring lists how
messy the raw material is. The tidiness was the signature of a normalising step, and
the right reaction was suspicion rather than a finding. Checking afterwards showed the
conclusion survived — 19 of 20 rows genuine — but by proportion, not by reasoning: had
`spread_total` applied broadly, the comparison would have been between two normalised
outputs rather than two groups of students.

`provenance` was recorded per field the whole time and simply not read. This is the
third variant of one habit — after suspicious ZEROS (`0 of 0` ungated cells, `0/20`
coverage, `0 differences` after `derived` landed), a suspicious PERFECT. Same tell
either way: a value too tidy for the process that supposedly produced it.

### Three defects the sweep surfaced, all fixed

**A harness bug: the two systems were reading different input.** `score.py` applies
`repair_orphans`, which moves a block the segmenter filed under the wrong heading to
the item it belongs to; `agreement_app` never did. H2 p19's DAY2 answer was filed
under D2, so the olx scored DAY2 against an EMPTY box — correctly reporting nothing
and gating to 0 against a gold of 4 — while the python read the 82 characters the
student wrote. Measured blast radius: that one participant, two cells in opposite
directions. **DAY2 56% -> 72%, D2 89% -> 94%.**

A second miss of the same kind followed: having fixed the two items whose own text
changed, WK2 also reads D2 as CONTEXT and needed re-sweeping too. `context_targets()`
answers "who reads this field" in one call and should be consulted BEFORE choosing
what to re-run, not after.

**Q4b's `unclear` cost the whole sub-area.** Once `modify_stated` carried
B_NO_MODIFY's full 2 points, a hedge there charged 2 and suppressed `modify_why` with
it: p14 and p17 both fell to 3.0 against a gold of 5.0. `unclear` is gone from both
modify slots on both sides — presence questions do not need a hedge, and the sheet's
the doubt check is where doubt belongs. **69% -> 75%**, though honestly it fixed
three cells and broke two; worth about one cell, not the three hoped for.

**The Q6 regression** is written up in its own section below — a dropped verdict on
Q4a/Q4c, three steps removed from the item it damaged.

### Operational notes from the sweep

* `sweep_app.sh` covered 23 items — it predated T1, T2 and 1b. Now 26, checked
  against the scored set.
* Transient `No response from LLM` hit 6 cells on the first pass and a few more on
  the second; deleting the item's `.json` and re-running the script recovers them,
  which is what the resumability is for. Final state: **0 unscored cells**.
* **Do not read a running sweep's tail as completion.** Launching a re-sweep while
  the previous one was still on its last item left two processes appending one
  `summary.txt`. The per-item JSONs were unaffected — each item goes to whichever
  sweep claims it first, and a re-write is an equally valid run — but the summary
  was not, hence rebuilding the table from the JSONs. Wait for `=== sweep finished`.

### The first sweep was invalid, and why

The first pass measured Q6 at **24%** (MAE 2.56, bias −2.12), six rows at exactly
−5.00 and 41 `mismatch` verdicts. The model was right and the harness was wrong:
Q6's fixture never seeded 4a or 4c, so the prompt's context refs resolved to
empty and every stated antecedent was compared against nothing.

The regeneration added the cross-item context the python passes (deviation 5) but
did not teach `build_jobs` to supply it. **An unseeded ref is not "no context",
it is an empty answer, and the model reads it as one.** The old paraphrased
prompt was vague about cross-item matching and credited anyway; the faithful
prompt, which says verbatim "check each stated antecedent against 4a … before
crediting the slot", surfaced a latent gap that had been there all along.

An audit of every `<Ref>` against its fixture found **21 refs across 9 items**
resolving to nothing. `from_scorer` only ever read the item's own components, and
cross-item context was a hardcoded special case for Q4c. That is now a
`CONTEXT_SOURCE` table derived from `olx_prompts.CONTEXT`, so a context ref added
to a prompt cannot go unfed. Re-audit: 0.

Keep that audit in the pre-flight for any future sweep — it is cheap, and the
failure it catches looks exactly like a bad prompt.

| item | before the fix | after |
| --- | --- | --- |
| Q6 | 4/17 24% | 12/17 71% |
| Q4c | 10/17 59% | 11/17 65% |
| Q4a | 13/17 76% | 14/17 82% |

### The cadence sheets were incoherent — fixed, and it did NOT help

Worth recording as a negative result, because the hypothesis was good and the
measurement refused it.

The four cadence items (DAY1/WK1/DAY2/WK2) told the model to answer the rubric's
ten numbered criteria "in order", then handed it a sheet missing two of them —
`avoidance_frame` and `named_type` — with `targets_own_behavior` ahead of the
cadence gate. The four type items (PR/NR/PP/NP) were coherent. The correlation
looked compelling: coherent 100/89/100/100, incoherent 78/83/61/89.

Both checks were added (unscored, as on the type items), `named_type` placed
before the comparison that consumes it, and the order aligned with the criteria.
All eight OC sheets now have zero orphaned criteria.

**Measured like-for-like on the 67 cells that scored in both runs: 53/67 → 54/67.**
Three cells moved — p11/DAY1 and p11/DAY2 fixed (both cadence-gate misfires),
p15/DAY1 broke. Net +1, which is noise. **The correlation was not causal, or the
effect is below what one run per cell can see.** Keep the change on coherence
grounds — a prompt that asks for what the schema cannot hold is wrong regardless
— but do not credit it with accuracy.

Shipped alongside it, and equally unproven: criterion 9's caveat repeated in the
cadence gate's checklist note, and `unclear` dropped from that gate so a hedge
cannot silently cost the whole item. Both mirror the python (`cadence_ok` is a
boolean defaulting to pass). A third change — relabelling the gate — was tried
and REVERTED: no evidence, and the run that appeared to test it showed an
unrelated slot flipping, which is what iterating on three cells looks like.

DAY2's p8 and p9 remain wrong and are the reason to stop here. "…{{corpus:DAY2/p8:day2:83:102:sha=ceeef43b24ca:shape=S3-0a}} week" and "…out of the 5 days" both carry real weekly language; gold and the
python read them as daily, the olx does not. Pushing wording until two specific
rows flip is fitting the corpus, not fixing a rule.

### `unclear` was charged on the olx and free on the python

The one change in this whole exercise with a clean measured effect.

Every python boolean in `derive_oc_ledger` defaults to the favourable value —
`a.get("targets_own_behavior", True)`, `a.get("cadence_ok", True)` — and
TYPE_MISMATCH is guarded by `named != "unclear"`, so a type the model cannot read
costs nothing. The olx had no such asymmetry: `scoreSlotSheet` satisfies only the
FIRST verdict, so an `unclear` was a full deduction, and on D1/D2's gating
`matches_chosen_type` it cost the whole item.

Live, not theoretical: nine cells in the previous sweep returned `unclear` on a
scored check. Four changes went in together — `matches_chosen_type` told to
answer `yes` when `named_type` is `unclear`; `unclear` dropped from the scored
checks with a favourable default (`targets_own_behavior`, `targets_goal_behavior`,
`targets_unwanted_behavior`, and D1/D2's gate); label parity on item 1's
`matches_chosen_type`; mirrored cadence-gate labels.

**Like-for-like on 171 cells: 151/171 (88%) → 155/171 (91%).** Eight cells moved:

| | cell | gold | before → after | slot responsible |
| --- | --- | --- | --- | --- |
| fixed | p15/D1 | 2 | 0 → 2 | gating `matches_chosen_type` |
| fixed | p16/D2 | 1 | 0 → 1 | gating `matches_chosen_type` |
| fixed | p15/DAY1 | 4 | 3 → 4 | `targets_own_behavior` |
| fixed | p19/WK1 | 4 | 3 → 4 | `targets_own_behavior` |
| fixed | p8/DAY2 | 4 | 0 → 4 | cadence gate |
| fixed | p15/WK2 | 2 | 0 → 2 | gating check |
| broke | p20/NR | 4 | 4 → 0 | `you_arrange_it` flipped to `unclear` |
| broke | p6/PP | 4 | 4 → 2 | `observed_type` flipped PP → PR |

**All six fixes are on slots this change touched; both regressions are on slots
it did not.** `you_arrange_it` and `observed_type` keep `unclear` deliberately —
the python fails those too (`bool(a.get("contingent"))` is False when missing), so
removing it there would over-apply the rule. Their movement is run-to-run
variance. That asymmetry is the evidence: the change moved what it was aimed at
and nothing else.

Do not over-read +4 at n=171 from single runs. But unlike the cadence-coherence
round, the moved cells line up with the mechanism.

Also worth recording: p8/DAY2 was predicted to stay wrong as a genuinely
borderline reading ("…{{corpus:DAY2/p8:day2:83:102:sha=ceeef43b24ca}} week") and flipped to correct; p9
("…out of the 5 days") did not. One of two, once. Not evidence either way.

### Slot LABELS are not rubric text, and must not be made to match

Fifty-eight of the sheets' labels differ from the rubric `desc` they correspond
to. That is the design, not drift, and the audit that finds them is measuring
the wrong thing.

The two strings have different audiences and neither reaches the other's:

* the rubric **`desc`** is what the MODEL reads — `olx_prompts._checklist_section`
  falls back to it, so the prompt carries the rubric's own grader-facing
  shorthand, third person and free to say "the student", "T1", "4a";
* the slot **`label`** is what the STUDENT reads — `composeSlotFeedback` renders
  `**${slot.label}**` next to the tick — so it has to be second person and must
  not leak internal item ids.

Hence `desc` "Targets the student's own UTB or WGB" against label "Aimed at your
own target or goal behavior", and `desc` "Matches the type named in T1" against
label "Matches your first chosen type". Both are right for their reader.

**A label was briefly changed to match its `desc` on item 3 and has been
reverted.** "Second, different change" was replaced with the rubric's "Second
specific change", which dropped the distinctness cue the item's own guidance
turns on ("Count DISTINCT proposed changes") and broke the parallel with Q5's
"Second, different reason". If a label reads oddly, check it against the item's
GUIDANCE and its sibling items — not against the `desc`.

### Asserting response headings — fixed, no measurable effect

The olx labelled each response box with what it was supposed to contain
("### How (2)"), which asserts the box IS a second explanation of how — the very
thing the check decides. The python sends one undivided block and asserts nothing,
so this was deviation 1 leaking a judgement. Nine items did it. Headings are now
"### Asked for: How (2)", with a line stating that the heading is the field label
and not a claim about what arrived.

**Like-for-like on 156 cells: 121/156 → 121/156. Exactly flat.** Six cells moved,
two fixed, two broke, two wrong both ways. Bias −0.08 → −0.03, MAE unchanged.

Two ways the prediction failed, both worth recording:

* **Direction was wrong.** The mechanism says the model should become willing to
  REJECT a box that does not do what it was asked, so scores should fall. Five of
  the six moves went UP.
* **The target cell did not move.** 2a p1 — whose third sentence the rubric names
  as a deduction case, where the python marks `how_2` unmet — came back `met` both
  before and after. The one cell the change was aimed at was unaffected; only its
  quoted evidence got shorter.

The change stands, because the python demonstrably sends no such assertion and
parallelism is the goal. But it buys nothing measurable, and I should not have
implied it would.

### Q6's positional pairing — the fix worked on its target and cost variance

The olx's eight boxes are positional; the rubric's matching is not. The python reads
one undivided block and pairs the student's antecedents against 4a's set-wise, so
splitting the answer made ORDER part of the test — a commitment the python never
makes. `ITEM_NOTES["Q6"]` now says the pair corresponds to 4a/4c **not in order**:
a box is `met` if its content is either listed item, `mismatch` only if neither,
and if only one of the two is addressed anywhere then the other's slots are
`absent` (which preserves the whole-missing-half rule).

Measured with the two-run protocol against a frozen `out/h1` — checksum verified
identical to the null runs before and after, so the prompt section is the only
variable.

**The target case is fixed, decisively.** p12 addressed both of 4c's consequences
in the opposite order and lost 5 of 10 on four `mismatch` verdicts, where gold and
the python both gave full marks. All four went `met` in BOTH new runs: 5.00 → 10.00.
Four slots against a two-slot band.

**The whole-missing-half rule held.** p17's and p19's `state_a2`/`change_a2` stayed
`absent` in every run, and p17's four second-half slots all stayed `absent`. No
leak into crediting a missing half.

**But self-consistency fell: 134/136 slots (98.5%) → 130/136 (95.6%).** Judging
each box against both listed items is a harder call than positional matching, and
the model wavers more. Exact-match is unchanged — A/B 10/11, C/D 11/10 — because
p12's recovered cell is offset by the extra flipping.

The consolation is where the new instability sits: all six flipped slots are on
p4, p9, p15, p17, p18 — **cells that already disagreed with gold before the
change.** The clean cells stayed clean. So the added variance is inside the grey
zone rather than corrupting settled judgements.

Keep it: it removes a systematic error that will hit any live student whose
ordering differs from 4a/4c's, and ordering is unconstrained on a real form.
Do not claim it as an accuracy gain.

**Unrelated finding, now visible:** p19 is credited `state_c2`/`affect_c2` in every
run, before and after, on [[corpus Q6/p19 affect_c1 83:125 sha=cd352a4926ea]] against
4c's [[corpus Q4c/p19 second 35:59 sha=4b0a1d20acd8]]. Gold says the second consequence was never
addressed and took 5 points. That is a stable olx-vs-gold disagreement of its own,
independent of this change — run B's 6.25 was the outlier, not the rule.

### Grader-side pairing (`cover`): meets baseline, and the corpus cannot test it

The generic problem: the prompt was being asked to enforce logic the grader could
compute. Q6's two antecedent boxes correspond to 4a's two antecedents without
regard to order, so "does this box match?" bundled two jobs — identify WHICH item
the box names, and decide whether the pair covers both. The second is arithmetic,
and leaving it in prose made correctness depend on the model reasoning about its
own other answer.

`cover` moves it into the scoring model. `slotSheet.ts` gains `parseCover` and
`satisfiedMap`; a check is satisfied when it names one of its group's labels and
no earlier check has claimed that label. **Order-independence and one-item-one-
credit are now structural** — the double-claim is unrepresentable, not merely
discouraged. Q6's four `state_` checks report `first`/`second`/`neither`/`absent`
and the sheet declares
`cover="state_a1,state_a2:first,second|state_c1,state_c2:first,second"`.
14 new unit tests; the 58 existing slot-sheet tests still pass.

Two runs each, same frozen fixture (hash verified identical), n=16:

| | exact | MAE | bias | within-pair differing |
| --- | --- | --- | --- | --- |
| prose pairing | 8, 10 (mean 9.0) | 0.80 / 0.56 | +0.64 / +0.41 | 3 |
| grader pairing | 9, 9 (mean **9.0**) | 0.64 / 0.64 | +0.33 / +0.48 | 3 |

**Exactly at baseline.** MAE mean 0.68 → 0.64 and bias mean +0.53 → +0.41, both
inside noise. Variance unchanged. p12 holds at 10.00 in both runs, and p7/p17/p19's
`absent` slots hold — no leak into crediting a missing half.

**Why the corpus cannot decide this.** Counting the cases only `cover` can get
right: across 32 pair-decisions per run there is exactly **one order-swap**
(p12 `state_c`) and **one duplicate label** (p18 `state_c`). Everything else is
`first,second` in order, or an absence, where prose and grader agree by
construction. The prose note already handled p12. So this corpus has two
discriminating cells and a 2-4 cell noise band — it is structurally incapable of
separating the two approaches, and no number of reruns fixes that.

The case for keeping it is therefore not the measurement. It is that the failure
mode is now impossible rather than instructed against, and that ordering is
unconstrained for a live student in a way it is not across these 16 paper
answers. Recorded as meeting the bar, not beating it.

### Auditing the fragilities themselves: three were still live

The notes call several checks "fragile", meaning not *might break* but **might stop
checking without saying so** — a lookup that misses and returns something innocuous,
so the code carries on and reports success. Re-testing every one of them found three
still live, one of them a bug introduced by the conversion work.

**A typo in an `onlyif` condition silently cancelled the deduction.** The python port
read the missing slot's verdict as `""`, treated that as a failed condition, and
suppressed the charge — the exact inverse of the olx's rule, which `chargedMap`
spells out: *a typo must not silently stop a check being charged.* An unknown
condition now suppresses nothing.

**The blank-collapse text fallback was still load-bearing.** `blank_code` was added
for the converted items, but Q6, D1 and D2 were still finding their code by matching
the literal string "did not answer" — so renaming that phrase would have removed
their collapse in silence. All three now declare it and **the fallback is deleted**:
an item with no `blank_code` has no collapse, which is a property of the rubric
rather than of a phrase.

**Nothing checked that a slot's codes exist.** `derive_ledger` puts whatever the
`codes` map says straight into the ledger, so a misspelled code name would be
emitted, carry the slot's points, and reach the student's feedback with no wording
behind it — a typo presenting as a rubric finding. `check_slot_codes_exist` now
validates every `codes` value, `blank_code`, and every `counts`/`onlyif` key against
the item's own deduction list and credit components. It runs in `--enforcement` and
is in the self-test (**12/12**).

The rest held up under test: fragment-keyed guidance omissions still exit on a
non-matching key; the worked-example template is still fatal on drift in
`--check`/`--write`; all three attribute readers go through `_sheet_tag` rather than
matching `<LLMAction`; `web_name` still returns None for an unmapped key rather than
assuming equivalence; `KNOWN_ACTION_ATTRS` covers all eleven attributes including
`counts`.

No scores changed — the three fixes correct paths nothing currently takes. That is
the point of them: they are all about what happens on the next edit.

### Q1 and Q4b closed too: 26 of 26 items derive their score, 4 declared divergences

Both were the leftovers from the batched conversion, and each needed a different
thing. Neither cost accuracy — Q4b gained.

**Q4b: `onlyif` ported to the python.** Its blocker was never the mechanism, it was the
amount. `B_NO_MODIFY` (-2) covers "did not say IF it is a good choice AND why" while
`B_NO_MODIFY_WHY` (-1) covers only the second half, so two independent 1-point slots
charged the right total under two codes at the wrong values. Giving `modify_stated`
the full 2 and suppressing `modify_why` when it fails emits both codes at their
dictionary amounts. **94% → 100%, MAE 0.06 → 0.00** — exact on all 16 measured cells.
`B_NONE` becomes unreachable (never emitted, no gold row at 0), so that divergence is
gone. The olx sheet matches: `modify_stated@2` plus `onlyif` plus `max="5"`, since the
costs now deliberately exceed the item.

**Q1: a correction to the earlier verdict.** The batch report said converting Q1 cost
two cells, "replicated exactly across two runs, not noise". That was drawn from too
few runs of a noisy item. A `counts` derivation — the model answers HOW MANY reasons
once and the code awards that many — scored **76% then 88% on the same config**, and
the plain path had given 82% and 88%. All three overlap. Only ONE cell ever separates
them (p9, a marginal "two or three reasons" call), and Q1's own run-to-run band is
wider than the effect. The earlier claim was wrong.

So Q1 is converted, and `UTB_NOT_ON_LIST` is unreachable on both sides. Its
divergence is gone as well.

`counts` is worth having on its own terms: the model answers 2 questions instead of
4, and threshold arithmetic moves into code, which is the Goal-2 test. Ported to both
sides (`slotSheet.ts` + `LLMAction`, six new tests).

**The audit could not see Q1's asymmetry, and now can.** Every computed-check test ran
one way — "the olx computes it, the python asks" — so moving a check into python code while
the olx still asked for it read as clean. `ASKED ON OLX ONLY` is the mirror, and it
fired on all three reason slots until the olx got `counts` too. In the self-test.

Also fixed: the probe's baseline set every slot to `"met"` regardless of its declared
vocabulary, so a counted slot read `met`, parsed as a count of zero, and the all-pass
baseline stopped being full marks — which cascaded into three spurious findings. It
now uses each slot's own first verdict.

**The plain path is now empty.** All 26 items derive their score from checks, so
`--enforcement` compares every one of them against probed python behaviour rather than
against a deduction vocabulary — the residual that motivated the conversion is gone.
The audit's plain-path branch stays for a future item, and the self-test says
**SKIP** on the case that needs one rather than quietly passing.

Corpus after all of it: **H1 82% / MAE 0.25, H2 94% / 0.15, H3 95% / 0.10.**

### The 16-item conversion, in batches: 24 of 26 items now derive their score

Done in five batches with a rescore after each, and the result is item-dependent —
which is why it was worth batching rather than shipping as one change.

| batch | items | exact | MAE | verdict |
| --- | --- | --- | --- | --- |
| H3 | 1a, 1b, 2a, 2b, 3 | 93% → **95%** | 0.14 → **0.10** | kept — a real gain |
| H1 uniform | Q3, Q5 | Q3 76% → 76%, Q5 94% → 94% | unchanged | kept, neutral |
| H1 stated+reasons | Q2 (kept), **Q1 (reverted)** | Q2 82% → 82% | 0.24 → 0.24 | see below |
| H1 A/C | Q4a, Q4c | Q4a 82% → 82%, Q4c 82% → 76% | both unchanged | kept, within noise |
| H2 | T1, T2 | 100% → 100% | 0.00 | kept |

**H3 is the case for doing this at all.** Two cells moved and both landed exactly on
gold: p15's 2a from 6.0 to 4.0 (the forced per-slot judgement found a missing
sentence the free-form ledger had credited — the grader wrote "your second sentence
does not explain how your plan was successful") and p15's 3 from 3.0 to 0.0. That is
the `derive_from_credit` mechanism doing what it was built for.

**Q1 is the case against doing it everywhere, and it was reverted.** Converted, it
scored **76% / MAE 0.29 against 88% / MAE 0.18, replicated exactly across two runs** —
not noise. Q1's reason counting is the one place the rubric says to be GENEROUS about
distinctness, and a per-slot sheet makes that judgement noisier rather than sharper.
The opposite of Q6, where forcing separate slots helped because gold implied more
failures than the model volunteered. Reverting recovered it (82%, inside the
plain-path run-to-run range).

**A defect I introduced and caught by measuring.** Q2's gate was first written as the
rubric's tier (a) — "is the direct positive counterpart" — so tier (b) answers that
merely fail to invert the behaviour were zeroed: p10 (gold 3) and p18 (gold 4) went to
0 while only p17 was correctly zeroed. `WGB_UNRELATED` is reserved for tier (c), *a
different behaviour altogether*. Rewritten to say so, Q2 returned to 82% / MAE 0.24
with p17 still correctly at 0.

**Three divergences closed, one narrowed.** `UTB_NOT_ON_LIST`, `A_NONE` and `C_NONE`
were **never once emitted** across the cohort and no gold row sits at 0 on those
items, so conversion made them unreachable on the python too — which is what the olx
already was, by construction. Q1's reverted, so its entry is back; Q4a/Q4c's is gone
and the entry now names **Q4b alone**.

**Q4b is the one item conversion cannot reach without a dictionary decision.**
`B_NO_MODIFY` (-2) spans both 1-point modify slots, and `derive_ledger` charges a
slot's own points under whatever code it maps to — so mapping `modify_stated` to
`B_NO_MODIFY` would emit that code at 1.0 where the phrase bank says 2.0, and the
ledger would contradict the graders' own wording. Left plain.

**Mechanism work this needed**, beyond D1/D2's three generalisations: `blank_code` on
the item, so the "did not answer" collapse is DECLARED rather than found by matching
that literal string (1b's says "did not provide data" — the text match was the same
fragility as index-keyed omissions); and the collapse now requires more than one
scorable slot, because a single-slot item otherwise reported every failure as "did not
answer" and T1's `not_a_type` came back as `BLANK`.

Self-test is **11/11**. Its plain-path computed-check case now injects a rule onto a
plain item, because T1/T2 and 1b all moved to the derive path and nothing live trips
that branch any more — the guard has to stay tested even when nothing exercises it.

### D1/D2 converted: the last fixable divergence is closed, at zero score cost

`matches_chosen_type` is now computed on the python too, so the only `necessary: False`
entry on the books is gone — **6 declared divergences, 0 fixable.** D1/D2 also move
from the `rubric` basis to `probe` in `--enforcement`, which is the audit gain: their
enforcement is now compared against python behaviour rather than against a deduction
vocabulary.

This is the per-item redesign the 16-item conversion was rejected for, done twice.
It needed `derive_from_credit` generalised three ways:

* **per-slot verdict vocabularies** — `defines_type`/`named_type` take the four OC
  types, `add_or_remove` takes met/absent;
* **reported-only slots** (`reported: True`) — answered because a later check needs
  them, never a component of the score, so they can never produce a deduction. The
  "did not answer" collapse counts against the SCORABLE slots, not all of them;
* **`equals` as rubric data** — computed from two answered slots, excluded from the
  schema, lenient on `unclear`, and gating to `WRONG_DEFINITION`.

Eight unit cases pass, including the gate subsuming `INCOMPLETE_DEFINITION` and all
three lenient shapes. **Measured: D1 100%, D2 89% — unchanged, and 0 of 36 cells
moved.** A mechanism change that costs nothing is what this should look like.

**Four latent crashes came out of it**, all the same assumption — that every credit
component carries `pts`: `baseline.py` and `baseline_h1.py`'s tolerance,
`agreement.py`'s tolerance and its point set. The first surfaced as a traceback
mid-table, which is why D1/D2's rows were missing from the first comparison; the
`agreement.py` pair would have taken the olx harness down on the next D1 run. All
four now skip unscored components.

Two probe bugs on the python side, both found by the audit refusing to go clean:
`inputs` counted computed slots as model-answered (so it reported the python as still
asking for `matches_chosen_type`), and the credit-path flip forced `"absent"`
regardless of a slot's vocabulary — which made two flipped operands *agree*, hiding
the very rule being checked. And `equals`-operand pairs are no longer compared as
charge-once when the computed check **gates**: flipping either operand then costs the
whole item, so the pair is not sublinear on either side and the comparison was
vacuous. Where both sides declare `equals` as data it is now compared exactly, like
`cover`. Self-test **10/10**.

### `--enforcement` now covers all 26 items, on two different bases

The mode used to compare only the 10 items whose score both sides derive from
checks, printing the other 16 as "outside the compared set". That was an honest
label for a real hole: **a olx-only enforcement rule on any of those 16 was
invisible**, which is how D1/D2's `equals` gate sat undeclared.

The hole is not closable by probing the python — on the plain path the model authors
the ledger, so there is no arithmetic to flip inputs against. What *is* closable is
the other direction: the olx always **declares** its enforcement, so every declared
rule can be checked against the rubric it has to come from.

| basis | items | what is asserted |
| --- | --- | --- |
| `probe` | 10 | the python's own behaviour, flipping inputs — gates, charge-once, cover, vocabulary |
| `rubric` | 16 | every declared gate is backed by a whole-item deduction code; every computed check is named in a divergence's `web_computes`; `cover`/`onlyif` require a declaration |

Turning it on surfaced **8 undeclared computed checks** on five items — all real,
all known-good, none previously written down:

* **D1, D2** — `matches_chosen_type`. The olx has both halves as checks and compares
  them; the python reaches `WRONG_DEFINITION` by having the model author the code.
  Marked **not necessary**: converting D1/D2 to `derive_from_credit` would close it,
  at the cost of the rubric redesign recorded below. The only fixable divergence on
  the books.
* **1b** — the four `*_data` checks, computed from the fields.
* **T1, T2** — `type_stated`, computed from the choice field.

Each is now declared per-key rather than by a blanket item exemption, so the
exemption cannot outlive what it exempts. **7 declared divergences, 9/9 self-test.**

The report says which basis each item used and prints `-` where a python count does
not exist, rather than `0`, so the weaker basis stays visible: **a rubric-checked
rule can be justified by the deduction vocabulary without any check that the python
applies it the same way.** That is the residual, and it is the honest limit of
auditing a model-authored ledger.

### The measurement guard: scored is not the same as measured

Third instance of one blind spot, closed. The audits checked that the items they
knew about agreed; then `uncovered_cli_items` checked that the olx scores every
python item. Neither checked that a scored item is ever **measured** — an item can be
graded correctly on screen and contribute to no number at all, which is exactly
what 1b and T1/T2 were.

`unmeasured_items()` now diffs `agreement_app.JOBS` against `ACTION ∪ SHEET_ONLY`
in **both** directions:

* **NEVER MEASURED** — the olx scores it, no job drives it, so no run reports it.
* **MEASURED, NOT SCORED** — a job exists but nothing grades it, so the run can
  only report a blank.

Both branches were verified to fire (the second by injecting a bogus job), and the
first is in the self-test: **8/8**. Every run now prints the coverage plainly —
`26 python item(s) scored on the olx, 26 of them measured` — so the number is visible
rather than something to re-derive by hand.

`JOBS` is imported inside the function, not at module scope: `agreement_app` pulls
in the reconstruction and the gold readers, and none of that is needed unless this
audit runs.

### T1, T2 and 1b are measured: 100% on all three, and deterministic

All three are in `JOBS` now, and all three come back **exact on every cell** with
MAE 0.00 — T1 18/18, T2 18/18, 1b 20/20 (H2 drops p2/p3 as mis-transcribed). A
repeat run of 1b was **bit-identical on 20/20 cells**, verdicts and score, which is
the point: no model is consulted, so these cells cannot move.

That they land on 100% is not luck. Gold for all three is pure presence:

| item | gold | the non-full rows |
| --- | --- | --- |
| T1 | 17×2.0, 3×0.0 | p10, p15, p18 — all "did not answer" |
| T2 | 17×2.0, 3×0.0 | the same three |
| 1b | 18×4.0, 1×2.0, 1×0.0 | p15 "missing two weeks", p18 "did not include" |

which is exactly what `present` and `plots` compute. 1b reuses the four data fields
1c already seeds from `simulate_h3`, and the fixture note there had *already*
recorded p18 (all four weeks absent) and p15 (baseline and week 3) — the two rows
gold docks.

**`OnChange`, and why not navigation.** A grader only runs when something executes
its action, and these items have nothing to submit. The obvious design — autoscore
when the student proceeds to the next screen — **cannot work**: a grader must be
MOUNTED to fire (`executeNodeActions` throws otherwise) and `Sequential` renders
only the current child, so an on-arrival hook on the next screen cannot reach back.
`Trigger` is no help either, being edge-triggered on truth: it fires once on
false→true and would go stale on the next keystroke.

So a new block re-grades whenever the published sheet changes:

```xml
<OnChange id="bmod_h3_data_regrade" watch="@bmod_h3_data_checks.checks"
          target="bmod_h3_data_grader" />
```

The score therefore always reflects the fields as typed, with no button and no
navigation coupling. It is safe from a write loop by construction: the actions it
fires must not alter the watched value, and a grader writes correct/score/
submitCount on *itself*, not on the sheet it reads. The watched value is compared
as a string, since a published sheet is JSON and its identity changes every render.

**A rejected first attempt is worth recording**: an `ActionButton` labelled "Check
my data". It works, but it invents a submit step for an item that has nothing to
submit, and none of these three should need the student to ask.

**Runner change.** `button` is now optional on a job. Without one the runner skips
the click-and-settle loop entirely and waits for the sheet to publish, reporting
`status: 'derived'` and gating `ok` on the sheet rather than on an LLM status that
would never change.

One fixture bug found and fixed: `detect_type` first used `\b`, which fails on
p20's transcribed underline (`_Positive Reinforcement`) because `_` is a word
character — it read as unanswered against a gold of 2.0. Now bounded on letters,
and verified against gold on all 40 T1/T2 cells before any run.

### The item sets now match, and a guard says so: 125 points / 26 items on both sides

Diffing the two sets found **T1 and T2**, 4 points, scored on the python and by nothing
on the olx. They looked graded — `CapaProblem` + `CorrectGrader` over a closed
`ChoiceInput` whose four options are the four types — but `CorrectGrader` is the
*always-correct grader for surveys and ungraded activities*: it emits no score, and
there is no `weight=` anywhere in Handout 2. The fields existed to feed context to
D1/DAY1/WK1, and nothing assessed them.

Both are now `DerivedChecks` + `SlotSheetGrader`, one `present` check at `@2`. That
needed a **second derivation kind**: `dataVerdict` parses numbers, and a closed
choice holds text. So `derived` rules are now `key:kind:refs[:tail]` —

    derived="type_stated:present:bmod_h2_t1"
    derived="baseline_data:plots:bmod_h3_baseline"
    derived="has_own_graph:plots:<four refs>:<template data>"

— with the kind **explicit on every rule**, because a guessed one misgrades rather
than fails. `verdictFor` dispatches in one place for both callers; an unknown kind
is dropped by `parseDerived`, and `DerivedChecks` then reports the scored check
left without a rule as a visible author error.

`NOT_A_TYPE` (-2) is declared unreachable: a closed list of the four types cannot
be answered with a non-type. Same shape as Q1's `UTB_NOT_ON_LIST`, same cause, and
it had been undeclared. `BLANK` stays reachable, so answering scores 2 and not
answering scores 0, as on paper.

**The guard.** Both misses — 1b and T1/T2 — came from the same blind spot: the
audits verified that the items they knew about agreed, and nothing verified that
they knew about every item. `uncovered_cli_items()` now asserts
`ACTION ∪ SHEET_ONLY == every python item id`, and it is in the self-test (7/7). It
would have failed on 1b and on T1/T2 from the day each was written.

Two latent bugs surfaced while wiring this: `_derived_attr` and `_equals_attr` both
matched only `<LLMAction>`, so they returned **silently empty** for a
`DerivedChecks` element — 1b's and T1/T2's rules were invisible to the generator
until both were routed through `_sheet_tag`.

### 1b is now scored on the olx: `DerivedChecks` + `SlotSheetGrader`

**1b was scored on the python (4 points) and not at all on the olx** — it wasn't even
in the measured set. That is a larger python/olx difference than anything in
`SCORING_DIVERGENCES`, and it went unlisted because the olx's *item set* was being
treated as fixed rather than as part of the comparison.

`SlotSheetGrader` could always have scored it; what was missing was a producer of
the sheet that isn't an LLM call. `DerivedChecks` is that:

```xml
<DerivedChecks id="bmod_h3_data_checks" verdicts="met,absent" max="4"
               slots="baseline_data:Baseline week's data present@1|…"
               derived="baseline_data:bmod_h3_baseline|week_1_data:bmod_h3_wk1|…" />
<SlotSheetGrader target="bmod_h3_data_checks" />
```

It carries its **own `checks` field**, so an item with nothing for a model to say
needs no `LLMFeedback` it would leave empty. It renders nothing and republishes
whenever the watched fields change, so the grader always reads current verdicts
with no button and nothing to wait for. The write is guarded on the serialised
payload — an effect that writes state on every render re-renders and writes again,
the storm `CompactPopout` documents.

**The leniency is the part to get right.** The rubric says "Any legible daily
figures for a week earn its point… **Do not deduct for formatting, units, or gaps
within a week**", so one number earns it. That makes the score deliberately more
lenient than `SelfMonitorPlot`'s warnings, which also flag short weeks and
unreadable tokens — those are advice about data quality. Ten of the 27
`dataVerdict` tests pin exactly this.

`dataVerdict` was extracted from the 1c work and lives **beside `parseSeries`**, so
one function answers both items and the grader cannot disagree with the chart.
`LLMAction` now calls it too.

**Not `CustomGrader`**, which would have worked today with inline JS over `inputs`:
its sandbox sees only `input`/`inputs`/`correctness`, so it cannot reach
`parseSeries`. That means a second "is this a number" drifting from the one the
chart draws with — the exact failure this design avoids. Same objection to
`RulesGrader`/`FormulaGrader`: they match values, they do not parse series.

**Audit changes.** A prompt-less item broke assumptions in all three modes:
`_ACTION_RE` hardcoded `<LLMAction`, so there is now a `_SHEET_RE` and a
`SHEET_ONLY` map. `--prompts` prints 1b as `n/a` with a line saying why rather
than silently omitting it; `--scoring` covers it (24 items now, up from 23) and
was verified to bite by inflating a slot to `@2`; `--enforcement` lists its
`derived` rule under "outside the compared set", since 1b is plain-path on the python
like D1/D2.

### 1c's `has_own_graph` is read off the page (`derived`) — the last Goal-2 item

On paper "did the student produce a graph of their own data" is a judgement about a
.docx: an embedded chart, an image, or prose describing a graph that is not there.
On the olx the chart is **drawn from** the four 1b fields, so the runtime already
knows the answer, and it was a *gate* worth the whole 10 points.

`derived="has_own_graph:<four field refs>:<template data>"` computes all three
verdicts:

| verdict | condition |
| --- | --- |
| `absent` | no field holds a plottable number |
| `mismatch` | every series equals the worked example's own numbers |
| `met` | otherwise |

The parse comes from **`parseSeries` — the chart's own function** — so the grader
cannot disagree with what the student sees. A second "is this a number" would
eventually drift, and the drift would be invisible.

**The `mismatch` case nearly got dropped.** My first version returned only
met/absent, which would have silently retired a check the olx deliberately makes:
the worked example sits *on the same screen* as the boxes, so typing its numbers
reproduces the paper item's "left the template in place" failure. That is a
comparison of numbers, and the prompt had been handing the model the example's data
so it could recognise them. It requires ALL four series to match — a student who
copied one week and tracked the rest has still tracked their own behaviour.

The example's numbers now live twice: in `bmod_h3_example_plot`'s YAML and in the
attribute. `olx_prompts.check_template_matches_example` **fails `--check`/`--write`**
if they disagree, because an unbound copied constant is the failure mode this
project keeps re-learning.

**Prompt changes.** `has_own_graph` leaves the response schema and gets a DO NOT
ANSWER line. Guidance bullet 1 ("FIRST DECIDE WHOSE GRAPH IT IS") is now a declared
omission — it asked for a judgement with no slot to report it in. `ITEM_NOTES`
keeps the *wording*-copied half, which is still the model's job on the label
checks, and hands the *data*-copied half to the grader. `parseDerived` also drops
empty tokens before `Number()`, since `Number('') === 0` made an absent template
parse as `[[0]]` — caught by the "no template" test case.

**Declared, because it is platform-forced**, and the declaration is machine-checked:
the entry carries `web_computes: {"1c": ["has_own_graph"]}` and `--enforcement`
asserts the olx really does compute it. A stale exemption is worse than none — it
silences the audit for a difference that has moved.

**And the audit was blind to it at first.** `--enforcement` reported 0 differences
after this landed, because the probe only knew `equals` and `onlyif`. Two guards
now close that: derived keys join `computed`, and `KNOWN_ACTION_ATTRS` makes an
`<LLMAction>` attribute the audit does not forward a **finding**. Adding the next
primitive cannot leave the audit quiet. Self-test is 6/6.

### Q6's python vocabulary collapsed onto the olx's — and `cover` finally bit

Porting `cover` left the python asking two questions for one fact: `verdict`
(met/absent/mismatch/not_described) **and** `matches` (first/second/neither) on
the four state slots. The olx had always used one field —
`first/second/neither/absent` — which is the same information without the
redundancy, and without the contradictions the pair admitted (`met` + `neither`
needed resolving in code; `absent` + `first` was not resolved at all).

The python now uses that one field. `verdicts` is declared on the cover group, the
state slots' `codes` maps are keyed by it (`neither` → `A_MISMATCH`, `absent` →
`A_NOT_STATED`), and the coverage pass lost its contradiction handling because a
contradiction is no longer expressible:

```python
for key in group["keys"]:
    v = ((slots.get(key) or {}).get("verdict") or "").strip()
    if v not in group["labels"]:
        continue          # `absent` or `neither`: already failing on its own
    if v in claimed:
        demoted[key] = ("absent", f"Names the same {group['of']} item as ...")
    else:
        claimed[v] = key
```

Eight unit cases pass, including the all-absent collapse to a single `Q6_NONE`.
`--enforcement` gained a **vocabulary** comparison, since both sides now declare
one, and the self-test gained a fourth injection for it — 4/4 detected.

**The model's judgement did not move**, which is what a redundancy removal should
do: 56 → 57 of 80 state slots credited across the cohort, `neither` 7 → 7,
`absent` 17 → 16.

**And coverage fired for the first time on real data.** p5 named 4c's *first*
consequence in both boxes; the duplicate was demoted to `C_NOT_STATED`, taking the
item from what would have been 8.75 to 7.5 against gold's 6.25. So the mechanism
worked and moved the cell toward gold — the residual 1.25 is a separate judgement
error, the model crediting `state_c1` where the graders wrote "First consequence
does not match 4c". Worth noting the duplicate was a *symptom* of that: the model
claimed one label twice because neither box actually matched.

Q6's exact-match nonetheless reads 65% → 59%, which is **one cell** at n=17. p5 is
that cell, and it was exact before only by a different route — the previous run
happened to call `state_c2` absent and `affect_c2` unmet, landing on 6.25 from the
other side. Attribution, not delta: the demotion is correct, the vocabulary is
inert, and the item is still 1.25 generous on p5 for an unrelated reason.

### The parity-audit gap is closed: `--enforcement`

Q6's distinctness rule went unnoticed for months because it fell between the two
audit modes — `--prompts` compares prompt elements verbatim, `--scoring` compares
item totals and reachable costs, and *what each side enforces* is neither. A third
mode now covers it.

    python3 equivalence.py --enforcement            # the comparison
    python3 equivalence.py --enforcement --selftest # confirm it still bites

**Probed, not mirrored.** The temptation is a table of "the rules the python
implements", diffed against the olx's attributes — but that is a hand-written copy
of Python, and the copy is what rots (see the index-keyed guidance omissions).
Instead both sides are *exercised*: flip one input at a time, then in pairs, and
read the rules off the losses.

| fact | how it is established |
| --- | --- |
| gates | an input whose failure alone costs the whole item |
| charge-once | two inputs that together cost less than they do apart |
| computed | a check the model is never asked for |
| cover | data on both sides, so compared exactly |

The olx half runs through `probe.test.ts` (env-gated on `RUN_SLOT_PROBE`, the
`runner.test.ts` convention) using the shipped `parseSlots`/`scoreSlotSheet`, so
the thing measured is the thing that runs. Current state — **0 differences**
across the 10 items both sides derive from checks:

```
item     max        gates   charge-once   cover  computed
Q6        10          0/0           0/0     2/2       0/0
PR         4          5/5           1/1     0/0       0/0
DAY1       4          6/6           1/1     0/0       0/1
1c        10          1/1           0/0     0/0       0/0
```

The probe found the `elif` on PR/NR/PP/NP and the type comparison on the cadence
items **from behaviour alone**, which is the point: neither is declared anywhere
in the python.

**Three details worth keeping.** (1) Charge-once pairs are discovered only on the
python. An open-ended search on the olx also reports both operands of an `equals` —
flip them both to the same wrong value and they agree again, so the computed check
comes back satisfied. Real behaviour, not a rule; the olx declares its rules, so
there is nothing to infer. (2) On the python the two type fields fail to *different*
wrong values for the same reason. (3) Cover labels are claimed per group, not
globally — sharing one set hands the second group labels the first already took,
and the all-satisfied baseline silently stops being full marks.

**The self-test is the part that matters.** A guard that has never failed is not
known to work, so `--selftest` removes each of the three rules in turn and asserts
the audit says so — the Q6 coverage that actually went wrong, plus Tier 1's
`equals` and Tier 2's `onlyif`. 3/3 detected, and it restores clean.

**What it deliberately does not cover**, printed on every run rather than left to
look like coverage: D1 and D2 declare `equals` on the olx while the python scores them
by a model-authored ledger, so there is no check arithmetic to compare. Those
reach the same outcome by the model picking a whole-item code — the slot-sheet
design difference, not drift. The 16 plain-path items are excluded for the same
reason, and `ENF.check_criteria_table_is_complete` fails the audit if an
`oc_analysis` field is added without deciding how it fails, so the probe cannot
quietly stop covering something.

### `cover` ported back to the python — and a correction to the case for doing it

Q6 asks the student to change **each of their two** antecedents, so the two state
slots must name DIFFERENT 4a items. The python's verdict vocabulary
(`met`/`absent`/`mismatch`/`not_described`) carries no identity, so nothing could
check it and no guidance asked the model to. Now the model also reports `matches`
— `first`, `second`, or `neither` — as a required schema property on the four
state slots, and `derive_ledger` does the pairing:

* a state slot the model called `met` whose label duplicates an earlier claim in
  its group is demoted, charged the slot's own **`absent`** code —
  `A_NOT_STATED` / `C_NOT_STATED`, which is what the graders wrote ("did not
  address how {{corpus:Q4c/p19:second:0:25:sha=d4d526f38996:shape=C1}} being affected");
* `met` with `matches: neither` is a contradiction, and resolves to the
  **`mismatch`** code, which is what it describes;
* a **missing** `matches` demotes nothing. The field is schema-required, so its
  absence means a provider ignored the schema, and inventing a deduction from
  that is worse than losing the check.

A demotion deliberately does **not** rewrite the reported verdict. The model's
`met` was a true statement about that box — the student did name a 4a item there
— and the finding is about the PAIR. Keeping the verdict also keeps
`scorer_evidence` correct: a demoted box still holds the student's words and must
not be emptied the way `absent` is. `1c`, the other `derive_from_credit` item,
declares no `cover` and its schema is byte-identical to before.

Eight unit cases pass, including the two that matter: an order-swap scores 10.0
and a duplicate scores 8.75 with the right code. The three worked examples now
carry identities, and exemplar 2 is itself an order-swap (box 1 names 4a's
*second* antecedent), which is the anchor for not penalising order.

**Measured: 0 demotions across 20 cells.** Q6 exact 65% → 65%, one cell moved
(p4 7.5 → 8.75) and that move is not attributable — coverage fired nowhere. Three
cells reported swapped pairs (`second, first`), which the mechanism credits, as
the python already did.

**The correction.** This work was justified by p18: the olx's identity report had
both consequence boxes naming the same 4c item, the python scored 8.75 against gold's
7.5, and I attributed the 1.25 to unenforced distinctness. Asked for its own
identity read, **the python called them distinct** (`first`, `second`) — so the
duplicate is not a stable reading of that answer, and the p18 gap is a judgement
difference about whether the second consequence was addressed at all, not a
pairing failure. The recovered point I predicted does not exist.

What survives is the structural argument, the same one `cover` was kept on for the
olx: a double-claim is now unrepresentable rather than unchecked, and ordering is
unconstrained for a live student in a way it is not across 16 paper answers. Do
not cite p18 as evidence for it.

### The python asked the model for two values it then discarded — removed

The same audit turned on the reference implementation: *does the python use the model
to compute anything code could?* Two required schema properties were being thrown
away on every call.

**`item_id`** — required on all 26 items; `score_item` returns `item["id"]` and
never reads the model's. **`pts`** — required on every deduction for the 16
plain-path items, and immediately overwritten:

```python
# Trust the rubric's point value, not the model's arithmetic.
ledger.append({"code": spec["code"], "pts": spec["pts"], "note": d.get("note", "")})
```

The code already knew the model's arithmetic was not to be trusted; it asked
anyway. That is the same incoherence `equals` removed on the olx side, in the
reference. It leaked twice over: on **318 of 320** plain-path cells the model also
echoed the points into the free-form `what` string it authors
(`"utb_stated (2 pt): ..."`).

Both are gone, along with system-prompt rule 2's demand to restate `pts` and the
"use these exact codes and point values" heading. The point VALUES stay in the
prompt's deduction list — that is what the model needs to judge severity; only
the echo went. Watch for a regression anyway: `additionalProperties: false` means
a model that volunteers `pts` now produces an *invalid* response, and the habit
was well established. A two-cell smoke test passed and matched the old reference
exactly before the full re-run.

### The recalculated reference: net zero, and the olx fixtures it invalidates

Full re-run after the removal — 520 cells, 520 calls, $43.58, 37 min. The old
reference is preserved at `out/h{1,2,3}_preschema`; nothing was overwritten
without a copy.

| | exact | MAE | bias | n |
| --- | --- | --- | --- | --- |
| H1 | 80% → **83%** | 0.27 → 0.24 | +0.02 → -0.01 | 135 |
| H2 | 94% → **94%** | 0.14 → 0.15 | +0.06 → +0.07 | 216 |
| H3 | 96% → **93%** | 0.08 → 0.14 | +0.03 → +0.04 | 120 |

Read in cells rather than percentage points, because at n=17–20 one cell is
5–6 points: **H1 +4** (Q1, Q2, Q4c, Q6), **H2 −1** (NR), **H3 −3** (1c, 2a, 3) —
**net 0 of 471**. Movement in both directions, inside the 4–8% band. The honest
conclusion is that removing the two fields changed nothing measurable, which is
what a semantics-preserving change should do.

Structurally clean too: 520/520 cells scored, `over_specified` 0,
`unknown_codes` 0, and **no invalid responses** — the `additionalProperties:
false` risk did not materialise, so the model dropped the `pts` habit when told
to.

**What this invalidates.** 7 items' olx fixtures are built from python output via
`from_scorer` — Q3, Q4a, Q4c, Q5, 1c, 2a, 3 — and `CONTEXT_SOURCE` feeds 17 refs
of cross-item context from the same files. Those fixtures have now shifted, so
the olx numbers in the table below are **not comparable** for those items and
need re-measuring before being read against anything.

Three items are unaffected by construction: **Q6** (frozen consensus, which is
exactly why it was frozen), **Q4b** (`handsplit`, hand-authored), **1a** (`sim`).
The remaining H2 items take raw responses, not scorer output.

### `derive_from_credit` for the other 16 items: assessed, recommended AGAINST

The plain path also keeps a failure mode the two derive paths design out — the
model can stack more deductions than there are credit components, and
`score_item` sorts by size and truncates, flagging `over_specified`. Converting
the 16 plain items to `derive_from_credit` would make that unrepresentable ("One
slot, one deduction, by construction").

**It has never happened.** Across 320 plain-path cells in the reference:
`over_specified` **0**, `unknown_codes` **0**. The mechanism was built for Q6,
where the failure was real and severe — gold implied 50 failed slots and the model
volunteered 31 — and the plain items simply do not exhibit it.

The cost, meanwhile, is a per-item rubric redesign, not a refactor:

| blocker | items | what it needs |
| --- | --- | --- |
| no `codes` map on any credit component | **all 16** | a `{verdict: CODE}` map authored per slot |
| non-uniform slot points | Q1, Q2, Q4a, Q4b, Q4c | the derive prompt hardcodes `credit[0]['pts']` as "each slot is worth N" — a lie for these |
| whole-item codes that are not slot failures | T1, T2 (`NOT_A_TYPE`), D1, D2 (`WRONG_DEFINITION`), 1a (`NO_WEEKLY_BREAKDOWN`) | a gating slot that is not a credit component, i.e. a new credit list |
| no "did not answer" code | 8 items | `derive_ledger`'s all-failed collapse matches that text exactly; without it a blank emits N slot codes instead of one |
| points match no slot | Q4b (`B_NO_MODIFY`) | reassignment |

Some of it would change scores, not just codes — Q4a distinguishes `A_NONE` (-5)
from `A_ONLY_ONE` (-2), and under slots both antecedents absent is 2+2+1, the same
total reached by a different vocabulary and different feedback text. So it needs
its own gold comparison, which is a reason not to fold it into the same re-run
that removes the discarded fields: that would confound them, the error already
made twice here.

Verdict: **do not convert.** A 16-item redesign to prevent a failure observed 0
times in 320 cells is not worth the scoring risk. Revisit only if
`over_specified` starts firing.

### Tiers 1 and 2: two more prompt jobs moved into the grader, both provably inert here

`cover` established the pattern; two further cases were found by asking which
prompts instruct the model to *do arithmetic about its own other answers*. Both
were shipped, and in both the corpus was shown — before measuring — to be
incapable of moving.

**Tier 1, `equals` (six H2 items).** DAY1/WK1/DAY2/WK2 asked `observed_type`,
`named_type`, and then a third check whether they match, worth 2 of 4. D1/D2
asked the same comparison as a **gate**. `equals="matches_chosen_type:observed_type,named_type:unclear"`
has the grader compute it; the check leaves the response schema entirely, so the
model is not asked for an answer that would be discarded. The `:unclear` clause
is not convenience — it mirrors `derive_oc_ledger`'s
`named != "unclear" && observed != named`, and without it the olx charges 2 for
the model's own hedge, which is [the `unclear` divergence](#unclear-was-charged-on-the-olx-and-free-on-the-python)
rebuilt inside the new primitive. A test asserts that failure mode.

*Why no measurement.* Replaying the recorded verdicts: the grader's arithmetic
differs from the model's own answer on **6 of 71 cells**, every one of them
`observed_type=none` with `named_type=unclear` — and all six were **already
gated to 0** by all five OC gates plus the cadence gate. The change cannot move
a score on this corpus. Two runs would have produced pure noise.

**Tier 2, `onlyif` (PR/NR/PP/NP).** These charge WRONG_TYPE (-2) for the wrong
type, and the *same code* for a right-type example aimed at the wrong behaviour —
`derive_oc_ledger` uses `elif`, so at most one -2 lands. Two scored checks charge
4. The old prompt bought the arithmetic by telling the model **"if `observed_type`
is not the type this item asks for, set this `yes`"**: a verdict that is false
about the student's answer, and one the student is shown in the checklist.

`onlyif="targets_goal_behavior:observed_type"` suppresses the *charge* while
leaving *satisfaction* honest. That split matters and is the rubric's own: its
check list records `met: bool(aimed)` truthfully while its ledger declines to
bill for it. So `onlyif` deliberately does not touch `satisfiedMap` — only
`scoreSlotSheet` and `failedGate`, plus a `(not counted separately)` note so an
unsatisfied-but-uncharged line does not read as a lost point the score omits.

*Why no measurement.* The old instruction bit on **5 of 58 ungated cells** (NR 3,
PP 2) and the model obeyed it **5/5**, so the change is score-neutral here by the
exact necessary-and-sufficient condition — `observed_type` unsatisfied *and*
`targets_*` unsatisfied *and* no gate failed occurs **0 times**. Note the first
version of this check read 0/0 because it tested gates against
`met/absent/unclear`; these sheets set `verdicts="yes,no,unclear"`. A pre-check
that returns all zeros deserves the same suspicion as a result that is too good.

What Tier 2 buys is therefore not accuracy: it is that 5 cells' worth of
displayed verdict stops being a value the prompt fixed in advance and starts
being the model's actual judgement. Score-equivalent, feedback-honest.

**The generalisable rule.** All three primitives answer one question — *is the
model being asked to compute something the grader could compute?* Pairing
(`cover`), comparison (`equals`), and charge-once (`onlyif`) were all prose. What
remains prose is genuine judgement.

### Q6's fixture is now frozen from a 10-run consensus — no accuracy gain

The python was run ten times on Q6 (`out/q6_consensus/run1..10`, ~$13.50) to answer
whether a stable parse of each answer exists. It does, decisively:

* **156 of 160 slots had the same verdict in all ten runs (98%).** Only p4
  `state_a2` (8/10), p11 `state_c1` (8/10) and p9 `state_c2`/`affect_c2` (5/10)
  wavered at all.
* The spans, by contrast, move on 47% of slots per rerun.

So the python's JUDGEMENT is near-deterministic and only its QUOTATION drifts —
which is the whole of Q6's measurement instability, since the fixture is built
from quotations. `q6_consensus.py` votes each slot's span word by word across the
ten runs, independently per slot so overlap survives, and `JOBS["Q6"]` now reads
the frozen result. Fixture hash verified deterministic.

**It does not improve agreement.** Two runs on each of three fixtures, n=16:

| fixture | exact | MAE | bias | within-pair differing cells |
| --- | --- | --- | --- | --- |
| single python run | 11/16, 10/16 | 0.64/0.56 | +0.33/+0.41 | 4 |
| consensus @0.5 | 8/16, 8/16 | 0.88/0.88 | +0.56/+0.41 | 2 |
| consensus @0.6 | 8/16, 10/16 | 0.80/0.56 | +0.64/+0.41 | 3 |

@0.5 lost 2-3 cells by WIDENING the boxes — at half the votes a word joins if any
half of the runs claimed it, which unions rather than converges. @0.6 reproduces
the single-run width exactly (102 filled, 34 overlapping, 103% vs 105% retention)
and recovers most of that, but nothing here separates 8-11 of 16 at a 2-4 cell
band. Adopted anyway, on the one benefit that is not in doubt: **the fixture can
no longer move, so future Q6 comparisons are valid.** Two of the comparisons
recorded above were invalidated by exactly that churn.

Adoption rule, to avoid cherry-picking: the FIRST run of a pair goes into
`out/web_v1/`, not the better one.

### The olx now beats the python on Q6, and p5 is the only cell going the other way

Reconciling two figures that were reported side by side and are not comparable:
**python 13/20 = 9 on the olx's 16 cells + 4 on cells the olx excludes.** Three of
those four are Q6's own prompt exemplars (p6, p8, p10), which appear verbatim with
their verdict sheets — the python scoring them exactly is close to tautological, and
that is why `handouts.excluded()` drops them from any reported baseline. p9 is the
fourth. On matched cells:

| | exact, same 16 cells |
| --- | --- |
| python | 9/16 |
| olx | **11/16** |

The olx is ahead by two. It is right where the python is wrong on p11, p17 and p18,
and wrong where the python is right on **p5 alone**.

**p5 has no systematic explanation.** Two mechanisms were proposed and both test
negative:

* *Context fidelity* — the python reads the whole 4a section while the olx reads two
  extracted spans, so the spans might be lossy. They are not: retention is
  **100%**, the two spans concatenated are the section verbatim.
* *The identity question being more lenient than the match question* — a forced
  "which of the two?" might invite picking the closest rather than `neither`. It
  does not: state slots are faulted at **26%** under the identity framing against
  **27%** under the old one.

What actually happened is narrower. p5's `state_a1` asks whether [[corpus Q6/p5 state_a1 38:98 sha=8bd5d4dd9d6d]] is the same antecedent as 4a's [[corpus Q4a/p5 first 28:67 sha=35a81e2b3bda]]. Gold and the python say no — a craving is not
a stocking habit. The olx has never had a stable read on it: across the six
pre-`cover` runs it came back `mismatch` three times and `met` three times, an
even coin flip. The identity framing did not bias it, it **stabilised** it — at
`first`, i.e. credited, which is the wrong side.

So the olx went from intermittently wrong to consistently wrong on one borderline
call, while gaining stability everywhere else. Not worth chasing: it is one cell
against three in the other direction, and the underlying judgement is one a
careful reader could go either way on.

### Q6 on the olx: 9.0 → 11.0 of 16, replicated

The `change_*` rule is the first change in this whole exercise with a clearly
replicated effect. Two runs each, identical frozen fixture (hash
`dcf5fa536115602c` verified before both), n=16:

| | exact | MAE | bias | within-pair differing |
| --- | --- | --- | --- | --- |
| prose pairing (baseline) | 8, 10 — mean 9.0 | 0.80 / 0.56 | +0.64 / +0.41 | 3 |
| grader pairing (`cover`) | 9, 9 — mean 9.0 | 0.64 / 0.64 | +0.33 / +0.48 | 3 |
| **+ the `change_*` rule** | **11, 11 — mean 11.0** | 0.45 / 0.48 | +0.17 / +0.48 | **2** |

**Both runs landed on 11**, which is better evidence than any single-run delta
recorded above: two independent runs each two cells clear of both earlier runs.
Three cells became consistently correct — p2 (the target case) 7.5/10.0 → 8.75
both times, p17 5.0/3.75 → 5.0 both times, p18 6.25/7.5 → 7.5 both times. Two
became less stable: p4 and p15 each have one run overshooting downward.

Worth noting the asymmetry with the python, where the same rubric change left exact
agreement at 13/20. Same rule, different effect on the two implementations —
different n, different excluded cells, and the python's own p3/p11 movement. Not
over-interpreted here; the point is that a rubric change is the only kind that has
moved the olx materially, and it moved it in the direction the rubric intended.

Still caution: n=16 against a 2–4 cell band. Replication across two runs is what
makes this credible, not the size. Remaining misses, both runs: p4, p5, p15, p16,
p19.

### The `change_*` tightening: a rubric change, kept with its contrast case

Acting on the finding below — that both implementations credit a `change_*` slot
when the described change is really a plan to do the goal behaviour — the fix went
into the rubric's `guidance` — then `rubric_h1.py`, now the course file — NOT into
a prompt. That is the right place: the python and the
generated olx prompt both read it, so equivalence is preserved by construction
and `equivalence.py` still reports 9/9 guidance verbatim.

The bullet alone fixed p2 and improved calibration sharply, but cost p3 — a 10/10
answer whose change acts on a belief while naming the gym as its result. The
contrast case recovered p3 and gave back most of the calibration:

| python's own Q6 agreement | exact | MAE | bias |
| --- | --- | --- | --- |
| before the bullet | 13/20 | 0.51 | +0.39 |
| bullet only | 12/20 | 0.45 | **+0.07** |
| bullet + contrast — **kept** | 13/20 | 0.51 | +0.26 |

Kept with the contrast: penalising a correct answer is the more visible failure.
The decision is a judgement between two error types, not a measurement — one cell
at n=20 with this much run-to-run movement is not resolvable, and README.md had
already concluded after six attempts that Q6 rubric tuning was not productive.
This is the seventh and it returns exact agreement to where it started.

Note the fixture insulation that made this safe: the python was rescored twice
during this work and the olx fixture hash never moved, because the frozen
consensus overrides `from_scorer`. Two rounds earlier the same rescore would have
invalidated the olx comparison outright.

### Q6's over-crediting is the RUBRIC's, not the olx's — a correction

Recorded above as "what Q6 actually gets wrong: it over-credits", attributed to
the olx. That attribution was wrong. Checking the four cells against the python:

| pid | gold | python | olx (8 runs) | gold's own reason |
| --- | --- | --- | --- | --- |
| p2 | 8.75 | **10.00** | 10.0 ×7, 7.5 ×1 | `change_a2` — "{{corpus:Q6/p2:affect_c2:3:39:sha=7bc493d62ecd}} does not change your {{corpus:Q6/p2:state_a2:17:50:sha=7f56e7f06c95:shape=R33-0-22}} |
| p4 | 6.00 | **7.50** | 7.5–8.75 | "-2.5: missing both consequences -1.5; missing one antecedent" |
| p16 | 8.75 | **10.00** | 10.00 ×8 | `affect_c2` — "did not clarify the second consequence being affected" |
| p19 | 5.00 | **7.50** | 7.50 ×8 | bundles the second antecedent AND its consequence as one −5 |

**The python over-credits every one, by the same amount or more.** These are
rubric-vs-gold disagreements shared by both implementations, so the olx is doing
its job — reproducing the python. Only p4, p16 and p19 are stably over gold across
all eight runs; p2 dipped once.

One is genuinely actionable and one is a gold artifact:

* **p2 is a guidance-application failure both sides make.** Gold's objection is
  that the change described does not change the named antecedent, and the item's
  own exemplar #2 is exactly this case — *"A plan to perform the WGB is not a
  change to the antecedent, so both change slots are `not_described`"*, on
  "{{corpus:Q6/p8:change_a1:10:31:sha=59e2c4a3daa0}} Tuesday-Friday". [[corpus Q6/p2 affect_c2 2:39 sha=e7e6d110d334]]
  is the same shape against "playing video games". The exemplar is verbatim in
  both prompts and neither applies it. Fixing that is rubric work on the
  `change_*` slots, and it would move the python's own baseline — so it is scoring
  improvement, not equivalence, and belongs in its own measured step.
* **p4's gold does not use its own slot structure.** "−1.5" is not a multiple of
  1.25 on a 1.25-increment item, and gold faults the consequences where both
  implementations fault the antecedents. Nearly inverted, and not reconcilable
  by anything on the olx side.

### The original (superseded) note on Q6 over-crediting

Six runs across three fixtures agree on the direction. Bias is positive in every
single one (+0.33, +0.41, +0.56, +0.41, +0.64, +0.41), and four cells are over
gold in **all six** while none is ever under:

| pid | gold | olx over by |
| --- | --- | --- |
| p2 | 8.75 | 1.25 |
| p4 | 6.00 | 1.50–2.75 |
| p16 | 8.75 | 1.25 |
| p19 | 5.00 | 2.50 |

That is the signal worth pursuing on this item, and it is not a fixture or
framing question — the olx credits slots the graders did not. p19 is the clearest:
it is credited `state_c2`/`affect_c2` on [[corpus Q6/p19 affect_c1 83:125 sha=cd352a4926ea]] against 4c's [[corpus Q4c/p19 second 35:59 sha=4b0a1d20acd8]], where gold took 5
points for the second consequence never being addressed.

### The same-fixture noise band for Q6, measured properly

Two olx runs, identical prompt, identical frozen `out/h1` (fixture hash verified
identical before each; `out/h1` re-checksummed after). Results in `out/q6_null/`.

| | exact | MAE | bias |
| --- | --- | --- | --- |
| run A | 10/17 (59%) | 0.82 | +0.09 |
| run B | 11/17 (65%) | 0.68 | −0.06 |

* **slot level: 134 of 136 verdicts identical (99%)** — only 2 flipped
* **cell level: 2 of 17 disagree between runs (12%)**, each by exactly one slot
  (1.25 pts)

So the olx model's Q6 judgement is highly self-consistent, and the churn that has
made this item so hard to measure comes from the python's quotation — 47% of
evidence spans change per rescore — not from the olx. Freeze `out/h1` and Q6 is
one of the steadier items, not the noisiest.

What that settles about the changes recorded here:

* the anchoring collapse (11/17 → 3/17, 8 cells) was **unambiguously real** —
  four times the band;
* the verdict-filter comparison (7/12 → 5/12) was **confounded**, as suspected:
  the rescore moved 64 of 136 spans, dwarfing a 2-cell band;
* 12% of cells at 8 slots each is consistent with the 4–8% corpus figure above.

**Stable disagreements with gold** — the same in both runs, so worth attention in
a way single-run misses are not: p2 (+1.25), p4 (+1.5), p9 (−1.25, a documented
gold divergence), p16 (+1.25), and **p12 (−5.00, four slots)**. p12 is the
largest stable gap on the item and has never been examined.

### Q6's fixture is not stable across python reruns — freeze it before comparing

`score.py --items Q6` was re-run to populate a new field. One rerun apart, on the
17 measured participants:

* the python's **met/unmet verdict** was identical on **134 of 136** slots (99%);
* the **evidence span** it quoted changed on **64 of 136** (47%), and on three
  participants all eight changed.

The python's own Q6 score was unmoved (13/20 against gold before and after, MAE
0.51). But the olx fixture is built entirely from those spans, so **it inherits
variance the python never sees.** That is a large part of why Q6 has been the
noisiest item in every sweep.

Consequence for method: a olx Q6 measurement is only comparable to another built
from the SAME `out/h1` snapshot. Re-scoring the python invalidates the comparison
even when the python's own numbers are unchanged. Snapshot `out/h1` alongside any
Q6 result, or do not compare.

This was learned the hard way: the verdict-filter change below was evaluated in
the same step as the rescore, so its before/after (7/12 → 5/12) measures the
rescore's span churn and says nothing about the filter. Five cells moved and not
one of them was a cell the filter touched.

### `derive_ledger` now records the verdict, not just met/unmet

`absent` and `mismatch` cost the same 1.25 but are different findings: a mismatch
means the student DID write something. `derive_ledger` had the verdict and threw
it away, so `scorer_evidence` had to guess from the evidence prose
(`^looked for|no |nothing|not |absent|none`) whether a box should be emptied.

The verdict is now carried through and trusted — only `absent` empties a box.
Plain-path items have no verdict and keep the heuristic. Across 160 Q6 checks the
new rule differs from the old on **3 boxes, all where the heuristic KEPT text it
should have dropped** ("With falling asleep in class never named…", "Since the
irritability consequence is never named…") — the python's own reasoning being typed
into the student's field. Zero boxes went the other way.

**A correction to what this was expected to fix.** p5 and p15 were reported above
as boxes wrongly emptied where gold says `mismatch`. Gold does say mismatch — but
the python says `absent`, and the empty box was faithfully reporting the python. The
rescore confirms it. So the disagreement is python-vs-gold about the KIND of
failure, which this change cannot touch; Q6's first visible verdict distribution
is 116 met, 34 absent, 8 mismatch, 2 not_described.

### Q6's overlapping fixture boxes are FAITHFUL — do not split them

A cautionary entry, because the reasoning looked sound and cost the item most of
its agreement.

Q6's eight boxes are filled from `credit_checks[].evidence`, and 36 of 117 filled
boxes share text with a sibling — `state_c1` and `affect_c1` are frequently one
sentence, or one contained in the other. That was diagnosed as a fixture defect
and Q6 was switched to the `anchored` split, which slices disjoint spans instead.

**It took Q6 from 11/17 to 3/17, MAE 0.75 → 1.41, bias −0.13 → −0.94.** Eleven of
seventeen cells moved, eight broken. Reverted.

The overlap is not a defect. A single sentence can both name the consequence and
say how it is affected, and this item's own guidance is the instruction to allow
exactly that: *"PRESENCE IS NOT WORDING. Be generous about how loosely something
is phrased and strict about whether it is there at all."* Slicing it leaves
fragments — p9's `affect_c1` became "With this". `anchored_split`'s docstring
already said so: *"Where a component maps to a discrete answer — one of Q6's
eight slots — the quote is the whole answer and can be used directly."*

The metric was the mistake: "boxes overlapping a sibling" was counted as harm
when it was fidelity. The generalisable test — **is the olx receiving something
the python is not?** — was never satisfied here. Both sides see the same evidence
quotes; this was second-guessing a shared representation on aesthetic grounds,
which is not equivalence work.

What survived from that round is `_quoted_span`: the scorer sometimes annotates a
real quote (`"…bad health" — loosely worded, but this is the 4c consequence`) and
the commentary was landing in the student's box on 9 of Q6's fields. The python's
reasoning about the student's text is not the student's text. It is the only
`from_scorer` item affected — all eight were checked. **[Not true, corrected
2026-08-20.** Eight boxes of ONE item were checked and the sentence was written
about the corpus. 1c's `title`/`x`/`y` were affected in ten of twenty cells, on
the item where it matters most, because there the box IS the graded value. See
"The fixture audit: all 26 items read out".**]** Measured: 8/12 → 7/12,
three cells moved, i.e. **nothing outside noise.** Kept on correctness grounds,
not for the numbers.

### What actually moves the numbers, and what does not

Across the rounds recorded above, a pattern separates them cleanly:

| change | kind | measured |
| --- | --- | --- |
| seeding the unfed context refs | wiring bug | Q6 **24% → 71%** |
| `unclear` charged where the python defaults favourable | arithmetic parity | +4/171, every fix on a touched slot |
| cadence sheets' orphaned criteria | prompt/schema coherence | +1/67 — noise |
| the doubt channel added to ten sheets | schema, provably score-neutral | −4/173 — noise |
| asserting response headings | prompt framing | 0/156 — flat |
| stripping the scorer's commentary from a quote | fixture correctness | 8/12 → 7/12 — noise |
| anchoring Q6's eight boxes | **fixture, misdiagnosed** | **11/17 → 3/17 — REVERTED** |
| carrying the verdict through to the fixture | fixture correctness | 3 boxes de-contaminated; unmeasurable (confounded with a rescore) |

**Wiring and arithmetic defects move the numbers. Framing changes have not, once.**
Three framing/coherence rounds produced nothing outside noise. That is not an
argument against making them — a prompt that asks for checks its schema cannot
hold, or asserts the answer to its own question, is wrong on its face — but it is
an argument against predicting that they will show up, and a strong argument for
spending remaining effort on wiring and arithmetic rather than wording.

### `confident` earns its place — it predicts disagreement

All 23 model-scored sheets carry the channel, matching the paper scorer's
`escalate`. The three that do not — `bmod_h2_t1_checks`, `bmod_h2_t2_checks`,
`bmod_h3_data_checks` — are `DerivedChecks` sheets with no model call, so there
is nothing to be uncertain about.

**It was called `uncertain` and is now `confident`, with the sense INVERTED**:
the flag is `absent`, not `yes`. Renamed by the same change that un-inverted the
advisory flags so every check says its good state. The numbers below are
therefore re-measured in the new polarity, from `web_v8`; the older table read
`uncertain = yes 47% / no 15%` over 173 cells and is superseded.

| | cells | miss rate |
| --- | --- | --- |
| `confident = absent` (flagged) | 274 | **16%** |
| `confident = met` | 157 | 5% |
| all | 431 | 12% |

Three times the miss rate when flagged, on 2.5x the evidence the first
measurement had. Q2 and Q4b each flag 18 of 19, and 2a flags 18 of 20 — but the
flag discriminates within them rather than just marking hard items: Q4b misses
33% of its flagged cells and Q2 only 6%. At the other end, item 3 flags 5 of 20
and scores 100%, 1c flags 7 of 17 and scores 94%. The model knows where it is
guessing.

Two caveats on these figures. `web_v8` predates the cited-participant
registrations, so its cells include the 55 now excluded from rates — the
correlation is unaffected, but the denominators are not the ones a current sweep
reports. And nothing consumes the signal: grepping `lib/llm/` and
`components/blocks/grading/` finds no reader of `confident`, so it is published
in the sheet and dropped. The paper scorer's `escalate` is also wired to two
triggers this has no equivalent for — an unknown deduction code, and a ledger
with more deductions than credit components — though the olx's strict enum
schema and one-slot-per-component shape make both faults unrepresentable there.

That is a usable routing signal: it is what the paper scorer's `escalate` exists for, and
on the olx it could gate which responses get a human read. Worth keeping for
that alone, independently of the parallelism argument that motivated it.

### Where the remaining error is

DAY2 (61%, MAE 1.39) and DAY1 (78%, MAE 0.89) carry the most; then Q3 and Q4c at
65%. Q4b measures 16 cells, not 17 — gold has no Q4b row for p2. Three cells lost
to transient `No response from LLM` after three retries on the first pass were
recovered by the re-run.

Tuning is unblocked. Re-measure against this table, not against the 83%.

see: qc:EQ.fixtures end

The whole corpus's fixtures were read out one cell at a time against the
submissions, finishing what `--fixture` was built for. Six items had never been
declared (2a, Q4a, Q4c, Q5, 3, 1c); five had been declared without being read
(Q3, Q4b, Q6, 1a, 1b), and three of those five were carrying defects. All 26
items now pass every fixture check and none is undeclared.

**Nothing here is measured yet, and that is the first thing to know.** This
session changed served text in nine items. Every stored number for a repaired
cell describes a fixture that is no longer served, and the list of what owes a
re-baseline is in `scoring/BACKLOG.md`. One of them is expected to MOVE rather
than sit still — see 1c below.

### What was wrong, by class

**Scaffolding served as the student's words — 30 boxes, 7 items.** A student's
own list marker or field label, kept in the box while most cells of the same
item strip theirs: 2a/p16's `"Sentence 3: "`, Q4c/p13 and p16, Q5/p1 and p16,
Q3/p6's four `"- "` bullets, Q4b's fourteen `"1) "`/`"2) "`, Q6's five (p10,
p18, p20). Class now closed — no box in the corpus opens with a marker. Q4b's
and Q6's went through `CONSENSUS_FIXES` rather than their own sources, because
those live in `COURSE_DATA` and this table's note already records what editing
data outside the repo cost: a p7 fix invisible to anyone who clones the repo.
It also leaves Q6's consensus frozen, which is the property it was frozen for.

**A box holding a neighbour's clause — 8 boxes.** Item 3's five cells opened
`second` with a sentence elaborating the FIRST change (p4's "I hate school!"
and four more), and 2a/p20's `how1` was a comma-initial adjunct sliced out of
the verdict's own sentence. In every case the union of the pair was asserted
unchanged, so the repair moves a boundary and nothing else.

see: qc:EQ.readouts end
### What the readouts said about the items themselves

Three findings that are not fixture defects at all, and are the reason to read
a fixture out even when it turns out clean:

* **Q4a's one counted miss is an accept the prompt quotes.** `antecedent_1`
  returns `wrong_kind` 6/6 on "{{corpus:Q4a/p19:first:23:58:sha=ca9d4ea70d5d:shape=S4-20}}", which the
  item's own ACCEPT bullet lists as an example that "all earned full credit".
  The phrase is six words, under `check_rule_examples_are_not_corpus`'s 8-word
  floor. And `antecedent_1`/`antecedent_2` carry no `rule` field at all, so
  every accept and reject test for the item sits in `guidance`, far below the
  components that apply it.
* **A perfect counted rate can measure half an item.** Q4c is 12/12 and Q5 is
  14/14, and in both cases nearly every counted cell is a full-credit row: no
  counted cell in Q4c requires REFUSING a stated consequence, and none in Q5
  requires refusing a reason or calling two the same. Every cell that tests
  those criteria is excluded. Read as diagnostics they separate cleanly — Q4c's
  category test fires on the exact text its REJECT bullet quotes, and its
  sufficiency test does not fire on the exact text its DEDUCT bullet quotes.
* **2a's error is one shape.** Every miss but one is +2.0 for a second `how`
  gold withheld, which makes it a one-directional target: a rule that can only
  refuse a `how` cannot disturb the twelve cells that agree.

see: qc:EQ.no-image

score.py's handout-3 prompt asks the model to **Read the student's graph as an
image**, because on paper a graph is a picture. `ClaudeCliBackend` forwards
`allow_tools=["Read"]`; `LoBlocksBackend` sends `"tools": []` unconditionally,
because that is the shipped route and the app gives the grader no tools.

So paper+gpt-5-mini scores 1c blind, and blind on a graph item is not noise — it
is a systematic zero. It returned **0.00 on 11 of 20 cells where gold is 6–10**,
which reads as 5/17 for the model until you find the cause.

**This is a deviation of the PAPER scorer only.** The olx and python never look at
an image: 1c is scored from the four weeks of data the student TYPED, through

```
derived="has_own_graph:complete:bmod_h3_baseline,bmod_h3_wk1,bmod_h3_wk2,bmod_h3_wk3:…"
```

and `web_v8` scores it **16/17 (94%)** with no tool involved. Only baseline.py
consults `not_comparable_items()`; agreement.py and agreement_app.py must not be
filtered by it, and are not.

**1c is therefore not comparable between the paper scorer on a tool-less backend
and anything else** — not between paper+mini and paper+Opus, and not between
paper+mini and the olx. It is excluded from paper+mini's rate entirely and
printed under `NOT COMPARABLE`, rather than counted as a score.

see: qc:EQ.no-image end
With 1c out, paper+mini measures **88.3%** against paper+Opus's **90.9%**.

see: qc:EQ.dev4

`SelfMonitorPlot` draws the chart live from the four weeks of data in 1b and the
labelling fields in 1c. The python grades a `.docx` and gets a graph-evidence bundle
(chart XML, embedded images, grouped shape text).

**The bundle has a olx analogue, and 1c is passed it.** The chart is generated
*from the 1b data*, so the data is what decides whether a graph exists and whose
it is. `olx_prompts.EVIDENCE` puts the four fields under `## Graph evidence for
this submission`, in the position `build_prompt` gives the bundle, and the sheet
opens with a `!has_own_graph` GATE carrying both of the paper item's whole-item
findings:

* `absent` = NO_GRAPH. Blank or non-numeric weeks render no chart. Deliberately
  generous — fail it only when the data is plainly missing or plainly not
  numbers, since a whole-item gate should not turn on a miscount and
  `SelfMonitorPlot` already warns under the chart about a short or unreadable
  week.
* `mismatch` = TEMPLATE_GRAPH_ONLY. A student can type the worked example's own
  numbers into 1b and get the example's chart back — the paper failure of
  leaving the template in place, reproduced exactly. `ITEM_NOTES["1c"]` gives
  the prompt those numbers so it can recognise them.

**The legend is scored, because the student writes it.** They type the four
series names into their own box and `SelfMonitorPlot` keys the chart off them
(`labelsTarget`), with a second box for the legend's heading
(`legendTitleTarget`). Crucially `labelsTarget` does *not* fall back to the
authored `labels` when empty: a student who has not named their series sees
`Series 1, Series 2, …` on their own chart, which is what an unlabelled key
looks like and is scored as no legend. Handing them correct series names is what
made this check unanswerable in an earlier revision. The slot carries
`met/absent/incomplete @2` and the rubric's legend bullet is back, verbatim.

**So 1c now totals 10 on both sides, with all five components and all six
deduction codes live.** Nothing about its scoring diverges. `rebuild_declared_gold`
rebuilds gold from the grader's own verdicts on the same 10 rather than
rescaling, because two rows need it: p11 carries an improvised "-1 pt: missing
baseline data week" that belongs to 1b, and the graph-gate rows state no
labelling verdicts at all.

What is still dropped, with `olx_prompts.OMIT_GUIDANCE` recording each, is three
guidance bullets describing `.docx` evidence that does not exist here: the
bundle's student/template labels, shape-drawn run-together text, and
description-is-not-a-graph.

**The worked example is on the 1c screen**, rendered by `ObservablePlot`
immediately above the student's boxes, carrying exactly the strings the rubric
names as the template's: *Water Consumption Over Four Weeks*, *Days of the
Week*, *Ounces of Water per Day*. Copying it is easier here than on paper. Two
distinct failures come out of that and the prompt separates them: copied DATA is
the gate's `mismatch` (whole item), copied WORDING is `generic` on the label
(2 points). `y_axis_label` gained `generic` alongside `title` so the sheet can
say which — score-neutral, since any verdict but the first already costs the
slot's 2 points. The x-axis is exempt: *Days of the Week* is the example's
label, the placeholder, and the right answer for nearly every student.

**A trap removed.** 1b's placeholders used to read "e.g. 8, 10, 8, 12, 6, 10, 0"
and "e.g. 32, 20, 22, 28, 30, 32, 10" — the worked example's baseline and week 1,
verbatim. That invited the copying the gate now scores. They are now plainly
different numbers. Keep any future placeholder distinct from the water data.

**A measurement dependency, easy to miss.** `JOBS["1c"]` must seed the four 1b
fields (it now carries the same `sim` block as 1a). Unseeded, they arrive empty,
the gate fires on every cell, and the whole item reads as zero — which looks
like a prompt collapse and is not.

Verified end to end after the change: p1 (full reconstructed data) →
`has_own_graph=met`, 6/6 against gold 6; p18 (all four weeks absent) →
`has_own_graph=absent`, grader 0 against gold 0 ("did not include").

**Open, and deliberately not done in the same step:** `rebuild_declared_gold` still
drops p4, p15, p18, p19 and p20 as incomparable, because gold zeroed them on the
graph gate and so states no label verdicts. p18 is now reproduced exactly and
p15 (baseline and week 3 absent) probably is too, so both are candidates to
bring back into the comparison. p4, p19 and p20 are gold 0 for a paper-specific
reason — a template chart, or a written description instead of a figure — and
their data reconstructs fine, so the olx correctly does not zero them; they must
go on being dropped. The rule would be "a gold-zeroed row is comparable iff the
reconstruction has no data", which is a fact about the submission rather than
about the prediction. Widening the gold set is a measurement change and belongs
in its own step, not stacked on the sheet change.

see: qc:EQ.dev4 end
This makes 1c worth 6 on the olx against 10 in the python. It is the one item where
the two are not measuring the same thing, and its rows are not comparable.

see: qc:EQ.dev5 end

| item | removed | rubric `context` |
| --- | --- | --- |
| D2 | the FIRST chosen type (`bmod_h2_t1`) | `_utb`, `_wgb`, `T2` |
| 1a | the four weeks of data from 1b | `[]` |
| 1c | the student's goal behavior | `[]` |
| 2b | both chosen OC types | `2a` |

Conversely, context the rubric DOES ask for and the olx was not passing has been
added: Q1's prose into Q2/Q3/Q4a/Q4b/Q4c/Q5/Q6, Q2's into Q4b/Q6, the UTB choice
into Q4b/Q6/D1/D2, the WGB into D1/D2, 2a's three fields into 2b and 3, and 2b
into 3. The paper Q1 block holds both the chosen UTB and the prose about it, so
the rubric key `Q1` maps to the closed choice *and* the text area; `_utb` /
`_wgb` are the same split.

see: qc:EQ.dev6

`build_prompt` adds a `## Weak hint` section for Q1 and Q2, read from the .docx's
underline formatting and correct in only 6 of 20 transcriptions. The olx asks
for the UTB as a closed `ChoiceInput` before question 1, so the same fact
arrives authoritatively as `## The behavior they chose`.

**Q1 only.** Everywhere after it, the olx sends the behavior the student
DESCRIBED in question 1 rather than the one they ticked — `bmod_h1_utb_observed`,
a `SheetValue` over `utb_stated`'s evidence, falling back to the choice until
question 1 has been checked. Seven prompts carry it (Q2, Q3, Q4a, Q4b, Q4c, Q5,
Q6), labelled "as they described it".

The reason is that the two can disagree, and everything after question 1 is
graded against what the student actually wrote: someone who ticks "lack of
sleep" and then writes about exercise is doing the exercise project, and Q4a's
antecedents are antecedents of *that*. On paper the question cannot arise —
there is one handwritten answer and nothing to disagree with it — so the python
keeps sending the underlined hint and this is a olx-only refinement, not a
divergence in what is being judged.

Q2 was also dropped from `UTB_CHOICE` as part of this. It had been getting the
raw choice under "the behavior they chose" *and* the described behavior under
context — two different answers to the same question under two headings. The
`seen` guard in `build_web_prompt` exists to stop exactly that, but it keys on
component id, so pointing context at a different component walked past it. Q1
keeps the section, because comparing the two is its own `matches_selected` check.

see: qc:EQ.divergences end
All 23 items were walked: the python's ledger (`score_item`, `derive_ledger`,
`derive_oc_ledger` and each item's deduction costs) against the olx's
`scoreSlotSheet` over the authored `slots=`. Sixteen items are **exactly
equivalent** — every deduction cost is reachable by the right check, whole-item
codes land on gates, and the totals agree: Q2, Q3, Q5, Q6, D1/D2 (totals),
DAY1, WK1, DAY2, WK2, 1a, 1c, 2a, 2b, 3. `increment` on a rubric record is
documentation; no scoring code reads it.

Three divergences remain, declared in `olx_prompts.SCORING_DIVERGENCES`, and
**all three are forced** — there is nothing left that could be brought into
line. One earlier entry was fixed and one was withdrawn as not real; both are
written up below, because a retracted finding is as worth recording as a fixed
one.

| divergence | items | forced? |
| --- | --- | --- |
| a legend keyed by DAY, not by week | 1c | yes — the olx's chart has one orientation |
| `UTB_NOT_ON_LIST` (−5) unreachable | Q1 | yes — closed `ChoiceInput` |
| the "−5, none listed" code has no gate | Q4a Q4b Q4c | yes — see below |

**`targets_*` unscored — FIXED.** `derive_oc_ledger` charges WRONG_TYPE (−2)
when the type is right but the plan aims at the wrong behaviour; the olx charged
nothing, because `targets_goal_behavior` / `targets_unwanted_behavior` carried no
`@n`. They now carry `@2`.

The rubric charges that code **once**, for either cause — `derive_oc_ledger`
uses `elif`, so a wrong-type example that also aims wrong still loses only 2.
Two scored checks could charge it twice, so the exclusion is stated on the check
itself: *answer this only when `observed_type` is the type this item asks for;
if it is not, set it `yes`, because the mismatch is already recorded there.*
Verified on three constructed NR cases:

| case | observed_type | targets | score |
| --- | --- | --- | --- |
| NR aimed at the unwanted behaviour | NR | no | 2/4 (was 4/4) |
| wrong type *and* wrong target | NP | yes | 2/4 — not double-charged |
| correct | NR | yes | 4/4 |

Then measured on the whole NR item, 18 cells, which is where gold has the most
rows in the −2 band. It changed exactly **one** cell: p11, from 4 to 2 against a
gold of 2. Worth reading, because it is the `elif` in miniature — the grader
wrote "-2 pts: This is an example of NP", the olx called it NR aimed at the
wrong behaviour, and both land on the same single −2. That is precisely the case
only one scored check could not express. No row double-charged.

NR after the fix: 15/18 exact, MAE 0.44, bias −0.22; before it, on the same
verdict sheets, 14/18. **Do not read that as an accuracy gain** — one cell at
n=18 is far inside the noise floor this file sets (~15 points). The
justification is that the rule now matches; the cell is a bystander. The three
remaining NR misses (p4, p14, p20) all have `targets = yes` and are untouched by
this change: p4 and p14 are type judgements, p20 is a `you_arrange_it` gate
misfire.

**The "none listed" gate is now recorded as forced, not fixable.** A_NONE /
B_NONE / C_NONE cost the whole item and the olx reaches 0 only when every check
fails, so a response listing nothing that still uses the keyword keeps a point.
But **zero of the 20 gold rows sits at 0 on Q4a, Q4b or Q4c** — the python can zero
them; the graders never did. A gate would fire on no observed case, against a
reading (the keyword point is separately earned) that is arguably the more
faithful one.

**`INCOMPLETE_DEFINITION` on D1/D2 — WITHDRAWN, this was never a divergence.**
It was listed on the reasoning that a definition missing both halves costs 2 on
the olx (two failed checks) and 1 on the python, because the code is not
`repeatable`. Three things say otherwise:

* The rubric scopes the code to a one-half omission — *"right as far as it goes
  but omits one of the two halves"*. A definition stating neither is not that
  code; it is WRONG_DEFINITION (−2) or BLANK, which is −2 on both sides.
* `repeatable` is a statement in the prompt, not an arithmetic cap. The plain
  path in `score_item` sums whatever codes the model returns with no dedup, and
  two entries do not trip the `over_specified` clamp on a two-component item —
  so the python can reach −2 by that route too.
* No corpus row exercises it. Every −1 row on either item omits exactly one
  half: p13 D1 *[[corpus D1/p13 d1 0:41 sha=0b432b4eca1b]]*, p16 D1 *[[corpus D1/p16 d1 0:27 sha=0bedbac96df6]]*, p9 D2 *[[corpus D2/p9 d2 0:69 sha=033f3485e11c]]* The olx scores each of those 1, matching gold.

**The day-keyed legend** is structural. The olx's chart has one orientation —
series are the four weeks, the x-axis is the seven days. A paper student who
plotted it the other way round has a legend naming days, which the graders
accepted and the olx scores as not naming the four series. Confirmed on p11:
gold 6, olx 4. One row, and not a prompt defect.

What `--scoring` can and cannot do: it checks totals and whether each deduction
cost is *reachable at all* by some combination of checks, so it catches a
deleted `max="4"` (PR's −4 codes become unreachable) or a slot whose points
match no code. It cannot tell whether the RIGHT check fires — that is what the
declared list is for. Clean output means "nothing drifted since that list was
written", not "the two agree".

see: qc:EQ.olx-wrong end

DAY1 was self-contradictory in two places at once. Criterion 7 said
the avoidance reading "never changes the score; it flags the answer for a
phrasing comment", and the `consequence_asserted` note repeated it — while DAY1's
own guidance said "AVOIDANCE FRAMING TAKES THE WHOLE ITEM HERE. An answer whose
only claim is about dodging a penalty ... the graders scored those zero." The python
had suppressed the false half; the olx shipped both halves and contradicted
itself.

That is now `rubric_h2.AVOIDANCE_SCORES` — declared once, on the rubric, read by
both generators. DAY1 is the only member, DAY2 is unaffected, and DAY1's is the
only olx prompt this work moved; the other 22 are byte-unchanged.

see: qc:EQ.scored-exactly end
### Q6's `affect_c*` never fired, so gold's own charge was unreachable

Measured over the cohort, `affect_c1`/`affect_c2` copied `state_c1`/`state_c2`'s
verdict in **18 of 20 responses**, and their "named but not described" verdict
fired **zero** times — while the same verdict on `change_a1`/`change_a2` fired
five. The consequence side had collapsed to a binary mirror of its sibling.

Two causes. The `state_c*` and `affect_c*` fixture boxes hold OVERLAPPING text,
which is faithful and must not be split; and `change_a*` carries a worked
operational test ("judge WHAT THE CHANGE ACTS ON") where `affect_c*` carried a
one-line desc. The same text twice, with nothing to separate the questions, gets
the same answer twice.

The consequence: gold's commonest charge on this item — "did not clarify the
[first/second] consequence being affected" — is exactly an `affect_c*` failure
with the consequence named, and was therefore MECHANICALLY UNREACHABLE. Two
counted cells could not be scored right by any run.

This is also why an earlier attempt made it worse. That rule asked `affect_c*`
whether the 4c consequence was IDENTIFIED — `state_c*`'s question restated — so
it pushed the two slots to agree harder. The rule that worked asks about
MECHANISM, which is what the deduction code already said and the desc had
dropped: "how the consequence will be affected BY CHANGING THE ANTECEDENT". Both
observed failure shapes are named in it: a bare good outcome, and the plan
restated.

The rule was measured, reverted, and is worth reading for HOW it was measured.
Its first run scored [8, 8, 8] against a baseline of [7, 8, 8], with p15 and p16
both landing on gold. That result was an artefact: the rule illustrated its own
test with examples lifted from the corpus — a positive example verbatim from
p14, a counted cell scoring exact, and a negative example that described p15's
answer, p15's own 4c AND the verdict. An answer key for one of the two cells it
was measured as fixing.

Re-measured with invented examples, verified absent from every submission: [8,
7, 7]. **p16 is genuinely fixed** — 8.75 in all three runs, where baseline gave
10.00 — so the diagnosis holds and the mechanism test does reach a cell nothing
else could. p15 never moved, and p1 and p18 broke. +1 for −2, so the rule came
out and the item stayed at baseline.

The diagnosis is the durable part: the `affect_c*` slots cannot express gold's
commonest charge, and any future attempt has to make that verdict fire without
disturbing the cells that legitimately credit it.

see: qc:EQ.prompt-leak end

`exemplar_items` existed for one shape of self-grading: a response reproduced in
full as a worked example, which handout 1 does on Q6 for p10/p8/p6. Auditing
every item's prompt-bearing text for a participant cited BY NUMBER found a
second shape, nine times more common and entirely unregistered.

The citations read like this, from Q4b:

> falling asleep in the car or {{corpus:Q6/p20:affect_c2:46:65:sha=f4404254ef89}} cost participant 20 three
> [points]

> Participant 7 offered one sentence about why it {{corpus:Q4b/p7:modify:21:38:sha=1fa4115cf4a6}} and one
> about procrastination consequences, and the grader took 3 points

Each quotes the student's answer AND states the grader's decision. For that
participant on that item it is an answer key, so scoring them there measures
recall, not judgement. `guidance` is copied verbatim into both the paper prompt
and the OLX, so both scorers see it.

Ten items cite participants this way — 53 item-cells:

| handout | item | cited |
| --- | --- | --- |
| 1 | Q1  | 1, 2, 6, 9, 10, 16 |
| 1 | Q2  | 3, 6, 7, 10 |
| 1 | Q4a | 3, 4, 6, 9, 14, 15, 17 |
| 1 | Q4b | 2, 4, 6, 7, 13, 15, 19, 20 |
| 1 | Q4c | 4, 9, 11, 12, 15, 17, 20 |
| 1 | Q5  | 4, 6, 8, 9, 19, 20 |
| 1 | Q6  | 2, 3, 5, 10, 11, 17, 19 |
| 3 | 1a  | 1, 6, 15 |
| 3 | 1c  | 4, 8, 20 |
| 3 | 2a  | 1, 14 |

Only Q4b is registered, in `cited_participants` — a per-item map, because the
sets differ item by item and the handout-wide `exemplar_participants` list
cannot express that. Q6's own citation list is also wider than the three
few-shot bodies already registered for it.

**It matters to a published comparison.** Q4b was the largest olx/paper gap in
the corpus, and most of that gap was the citations:

| | before | after dropping the 8 cited |
| --- | --- | --- |
| olx | 13/19 (68%) | 9/12 (75%) |
| paper+Opus | 17/19 (89%) | 10/12 (83%) |

A 21-point gap becomes 8. Across the whole corpus, dropping all ten items'
citations moves olx 89.3% -> 91.8% and paper+Opus 90.9% -> 92.1%, closing a
1.6-point difference to 0.3. Opus, the stronger model, is the one that exploits
them here: it scored every cited Q4b cell correctly, while the olx missed
three.

The other nine are deliberately NOT registered here, for the reason stated
above: it wants to be a decision rather than a side effect of fixing Q4b.

