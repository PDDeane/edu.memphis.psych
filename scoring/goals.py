"""Structural checks and label allocation for GOALS.md.

WHY THIS IS NOT guide.py. Both files carry labelled entries, but the labels mean
opposite things. A guide section's label is its POSITION, so it is derived from
document order and renumbering is the repair. A goal's label is its NAME: `Q22`
is cited in commits, in memory notes, in other subgoals' prose and in
QUALITY_CONTROL.md, and it must mean the same entry forever. Renumbering GOALS.md
would be the defect, not the fix.

So the automation here is the other half of the same idea: labels are ALLOCATED
rather than guessed (`--next`), and the things that would quietly corrupt the
record are refused rather than trusted to care:

    a DUPLICATE label      two entries answering to one citation
    a DANGLING citation    "subgoal Q40" where no Q40 exists
    a DELETED entry        a goal that was in the committed file and is now gone
    an UNAPPROVED closure  `- [ ]` -> `- [x]` without the user agreeing

That last one is GOALS.md's own standing rule -- "NEVER CLOSE A GOAL WITHOUT
ASKING THE USER FIRST" -- which was broken in this project by closing a subgoal
inside a recording step. A rule stated in the file it governs and enforced
nowhere is a rule that depends on whoever reads it last.

    python3 goals.py --check          duplicates, citations, deletions, closures
    python3 goals.py --next Q         the next free label, so ids are not guessed
    python3 goals.py --list           labels with their state, in document order
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOALS = HERE / "GOALS.md"

# `- [ ] Q22. **title**` / `- [x] E30. **title**`. A CAPITAL prefix and an
# INTEGER, unlike the guide's lowercase-letter suffixes -- the two files are
# deliberately not interchangeable.
ENTRY = re.compile(r"^- \[([ x])\] ([A-Z]+)(\d+)\. (.*)$", re.M)

# How a goal is cited. The `subgoal `/`goal ` prefix is REQUIRED, and that is not
# pedantry: `Q1`, `Q2`, `Q4a` are also RUBRIC ITEM ids, so a bare `Q1` in prose
# is usually an item and not a subgoal. Requiring the word is what makes a
# citation check possible on this corpus at all.
CITE = re.compile(r"\b(?:sub)?goal ([A-Z]+)(\d+)\b")

# CLOSURES THE USER HAS AGREED TO, by label. GOALS.md's own first rule is that a
# goal is never closed without asking; this is where the asking is recorded.
# Re-opening and re-closing needs a fresh entry, because the second closure is a
# second decision.
# GOALS MOVED FROM ONE SERIES TO THE OTHER, old label -> (new label, why). A
# refile is not a deletion, but it looks exactly like one to the deletion check,
# so it has to say so -- and the check verifies the new label EXISTS, which is
# what stops "refiled" becoming a way to make an entry disappear.
#
# A REFILED LABEL IS ALSO SPENT. `next_label` allocates from the maximum in use,
# and a refiled number is cited in commits and in the new entry's own history
# note, so reissuing it would make two different subgoals answer to one name.
REFILED: dict[str, tuple[str, str]] = {
    "Q42": ("E43",
            "the THIRD misfiling of 2026-09-04, after Q38 -> E40 and Q39 -> E41, "
            "and the `--next` reminder printed the test before each one. Its "
            "FINDING is a scoring fault -- the reasons scaffold reporting "
            "listed=0, failing=0, given=3, which cannot be arithmetic -- but its "
            "DELIVERABLE is a check plus a decision about whether the engine "
            "should recompute a `reported: True` slot rather than trust it, which "
            "is the audit's own machinery. Three of one kind in a day is the "
            "argument for either the content discriminator E41 measured and "
            "rejected, or for accepting that this judgement has no mechanical "
            "guard: `misfiled_series` compares a label against its SECTION, and a "
            "Q sitting in the quality-control section is consistent however wrong "
            "the series is."),
    "Q39": ("E41", "the second misfiling of 2026-09-04, and the `--next` reminder "
                   "had already printed the test. Its FINDING is 63 unstable "
                   "cells inside the numerator; its DELIVERABLE is a derived "
                   "instability band, which is audit machinery like E37's "
                   "wrong-cell accounting and E40's owner map."),
    "Q38": ("E40", "filed in the wrong series on 2026-09-04 and moved the same "
                   "day. The deliverable decides the series, not the finding "
                   "(subgoal E25 states the test): this one's deliverable is a "
                   "change to measured._live_subgoal_owners plus a fire test, "
                   "which is audit machinery, and subgoal E37 introduced that "
                   "map in the first place."),
}


# WHICH SECTION EACH SERIES LIVES IN. Exact across the corpus: 35 Q-goals are in
# the quality-control section and 32 E-goals in the equivalence one, with no
# exceptions -- so a label filed into the other section is a mistake rather than a
# style.
SERIES_SECTION: dict[str, str] = {
    "Q": "quality control",
    "E": "enforcing equivalence",
}

# WHAT THE SERIES MEANS, quoted where the allocator will be read. Subgoal E25's
# entry states the test and it is not mechanisable: "its FINDING is about accuracy
# but its DELIVERABLE is a primitive conversion ... That is the audit's own
# direction of travel." A CONTENT DISCRIMINATOR WAS BUILT AND REJECTED: scoring
# audit-vocabulary against QC-vocabulary across all 67 entries, Q tops out at 0.42
# and E's median is 0.35, and the case that motivated it -- E40, misfiled as Q38 --
# scores 0.30, BELOW the highest Q. It would have confirmed the mistake it was
# written to catch, so it is not shipped. The judgement stays with the reader; what
# the code enforces is that the label and the section agree.
SERIES_TEST = ("the DELIVERABLE decides the series, not the finding: a subgoal "
               "whose deliverable is a check, a declaration table or the audit's "
               "own machinery is an E, however much it discusses cells and gold")


CLOSURES_APPROVED: dict[str, str] = {
    "3a": "closed 2026-09-09 on the user's instruction, as a LEFTOVER PLANNING STEP rather than work anyone still owes. 3a, 3b and 3c are the three preparatory steps of 'Attempt 3 -- the lever nobody had tried' (find how the gate slots are generated and what `!` means; draft the new gate; scope it to the four cadence items). THE ATTEMPT THEY PLANNED WAS CARRIED OUT AND REVERTED: its own sibling `3d/3e` is already `[x]` and records the outcome -- 'DAY1 15 -> 14, and the probe dissolved it: DAY1/p13 is 3 of 6, not a stable 0/3, and p11's apparent fall probed 6/6. Reverted.' They went unticked because the attempt was abandoned on its own measurement mid-plan, not because the steps remain to be done. THE WHOLE SECTION IS ALREADY CLOSED: they sit under '## DONE (by decision, not by success) -- the four cadence items', whose standing conclusion is that the NOT_OC boundary is misaligned with gold in BOTH directions and that the cells stay counted and wrong. NOTHING IS ORPHANED BY THIS: these are method steps, not cells; the cadence cells they concern are owned by that section's conclusion and, since subgoal Q57's closure, by subgoal Q65. FOUND BY A COUNTING SLIP WORTH RECORDING: they never appeared in any open-goal count all session, because every count used the pattern `- [ ] LABEL. **bold title**` and these three carry no bold title. A goal list that silently skips entries is a worse defect than three stale ticks, and it is why the running total read ten when it was thirteen.",
    "3b": "closed 2026-09-09 on the user's instruction, as a LEFTOVER PLANNING STEP rather than work anyone still owes. 3a, 3b and 3c are the three preparatory steps of 'Attempt 3 -- the lever nobody had tried' (find how the gate slots are generated and what `!` means; draft the new gate; scope it to the four cadence items). THE ATTEMPT THEY PLANNED WAS CARRIED OUT AND REVERTED: its own sibling `3d/3e` is already `[x]` and records the outcome -- 'DAY1 15 -> 14, and the probe dissolved it: DAY1/p13 is 3 of 6, not a stable 0/3, and p11's apparent fall probed 6/6. Reverted.' They went unticked because the attempt was abandoned on its own measurement mid-plan, not because the steps remain to be done. THE WHOLE SECTION IS ALREADY CLOSED: they sit under '## DONE (by decision, not by success) -- the four cadence items', whose standing conclusion is that the NOT_OC boundary is misaligned with gold in BOTH directions and that the cells stay counted and wrong. NOTHING IS ORPHANED BY THIS: these are method steps, not cells; the cadence cells they concern are owned by that section's conclusion and, since subgoal Q57's closure, by subgoal Q65. FOUND BY A COUNTING SLIP WORTH RECORDING: they never appeared in any open-goal count all session, because every count used the pattern `- [ ] LABEL. **bold title**` and these three carry no bold title. A goal list that silently skips entries is a worse defect than three stale ticks, and it is why the running total read ten when it was thirteen.",
    "3c": "closed 2026-09-09 on the user's instruction, as a LEFTOVER PLANNING STEP rather than work anyone still owes. 3a, 3b and 3c are the three preparatory steps of 'Attempt 3 -- the lever nobody had tried' (find how the gate slots are generated and what `!` means; draft the new gate; scope it to the four cadence items). THE ATTEMPT THEY PLANNED WAS CARRIED OUT AND REVERTED: its own sibling `3d/3e` is already `[x]` and records the outcome -- 'DAY1 15 -> 14, and the probe dissolved it: DAY1/p13 is 3 of 6, not a stable 0/3, and p11's apparent fall probed 6/6. Reverted.' They went unticked because the attempt was abandoned on its own measurement mid-plan, not because the steps remain to be done. THE WHOLE SECTION IS ALREADY CLOSED: they sit under '## DONE (by decision, not by success) -- the four cadence items', whose standing conclusion is that the NOT_OC boundary is misaligned with gold in BOTH directions and that the cells stay counted and wrong. NOTHING IS ORPHANED BY THIS: these are method steps, not cells; the cadence cells they concern are owned by that section's conclusion and, since subgoal Q57's closure, by subgoal Q65. FOUND BY A COUNTING SLIP WORTH RECORDING: they never appeared in any open-goal count all session, because every count used the pattern `- [ ] LABEL. **bold title**` and these three carry no bold title. A goal list that silently skips entries is a worse defect than three stale ticks, and it is why the running total read ten when it was thirteen.",
    "Q59": "closed 2026-09-09 on the user's instruction, on the disposition the entry itself reached: two noise cells, one whose mirror forbids the fix, one where we agree with gold's prose, and p4 declared. `reasons_substantial` IS EXPLICITLY KEPT, as the entry required -- the free readout asked whether removing it would lose anything and the answer was yes. ONE THING FOUND WHILE CLOSING, AND IT IS RECORDED ON THE CELL RATHER THAN HERE: Q5/p4 has a LIVE ROUTE for the first time. The entry calls it 'the only cell where wrong_kind is a majority, and DECLARED', which is true, but the reach turns out to be favourable -- only four cells in Q5 ever answer `wrong_kind` (p4 12/12 on both slots, p9 4/12, p14 1/12, p19 1/12) and on the latter three, all gold 5.00, the wrong_kind runs ARE the error. So a loosening scoped to `wrong_kind` gains the target AND firms three cells, and cannot touch the gold-0.00 controls p13 and p17, which answer `absent` 24 of 24. THE ROUTE IS NARROW BECAUSE GOLD IS 2.50: exactly ONE of p4's two examples must be credited, so a blanket loosening would score 5.00 and be wrong in the other direction. The discriminator is that p4's FIRST names the GOAL behaviour ('{{corpus:Q5/p4:first:0:49:sha=d7ca2a227687}} you') while its SECOND names the unwanted one ('{{corpus:Q5/p4:second:0:83:sha=eb41ecd61b04:shape=A75}} tired'). AND example_1 SHIPS FIFTY CHARACTERS against example_2's 629, which is the same under-specification shape that Q3's `realistic` had at 31 characters and that a first rule fixed the same day. Full route on GOLD_SLOT_BOUNDS_KNOWN[('Q5',4)] and in PARKED_WORK.md, so the cell's own reader finds it. NO CELLS ORPHANED: p4 stays declared, p9 stays watched, and both owner readers return 0. CORRECTION 2026-09-13, on the pointer rather than the finding: this note cites `PARKED_WORK.md`, and NO SUCH FILE EXISTS -- not in the repo, not anywhere, and the only two references to the name are this sentence and its copy in GOALS.md. Nothing is lost: the other half of the citation is live, and the full route is on `measured.GOLD_SLOT_BOUNDS_KNOWN[('Q5', 4)]` where the cell's own reader finds it. The parked revisions that DO exist are plan-mode files under `~/.claude/plans/`, and each is now pointed at from its owning open subgoal (Q44, Q66, Q63) with the instruction to re-measure before acting.",
    "Q60": "closed 2026-09-09 on the user's instruction. THE ENTRY MADE ITS OWN CLOSURE CONDITIONAL ON NOTHING -- 'whatever it returns, this entry's own framing is settled' -- and the queued probe has now returned. IT FAILED, and the failure is recorded rather than softened: the Q1 `harms_listed` precedence clause, 360 characters, probed on all 20 cells x 6 runs, moved the item NOT AT ALL by median (17/20 -> 17/20) and moved its own target the WRONG WAY -- Q1/p9 from 2 of 12 to 0 of 6, wrong_by_median to always_wrong. Worse than neutral, it TRADED cells: p6 and p17 crossed WRONG->RIGHT while p11 and p19 crossed RIGHT->WRONG. Four cells crossing in both directions on a net of zero is a reshuffle, and a reshuffle is not evidence for a specification fix. REVERTED, and the revert returns Q1 to prompt_sha ba35305adb30, which is the sha its existing olx ledger entry already cites -- so that entry becomes valid again rather than needing a re-sweep. SO THE ENTRY'S FRAMING SURVIVES ITS OWN TEST BADLY: it filed the drift as 'variance rather than specification', then named a specification fix, and the fix did not hold. Variance is the reading the measurement supports. THE HALVES GO WHERE THE ENTRY SAID: the Q2 half to Q44, which now carries a measured route 8 diagnosis, and p17 to Q54, which also inherits this probe's failure. NO CELLS ORPHANED -- both owner readers return 0.",
    "Q64": "closed 2026-09-09 on the user's instruction, with the entry's own last free step MEASURED first rather than assumed. THE ENTRY'S PROPOSAL WAS ALREADY WITHDRAWN by its 2026-09-08 amendment: `named_type` is textless AND STABLE -- identical on every run of eight of its nine cells -- so a first definition would change nothing, and the Q40 precedent does not transfer, because Q40's `aimed_correctly` was textless AND UNSTABLE. What remained was the fallback the amendment named: read the four `none`-answering cells against the gates that were supposed to have decided them first. DONE, FROM THE LEDGER, NO CALLS, AND IT FINDS NO DEFECT. DAY1/p1 gold 0.00 band PERFECT 9/9; DAY1/p14 gold 0.00 counted right 8/9; DAY2/p16 gold 0.00 PERFECT 10/10; WK1/p13 gold 0.00 PERFECT 9/9. On every one of the four the definitional gates FAILED UNANIMOUSLY -- `contingent` absent 11-12 of 12, `follows_behavior` absent 11-12 of 12, `states_a_contingency` absent 12/12 where it runs. `observed_type`'s shipped text says use `none` ONLY IF GATES 1-4 FAIL, so on these cells `none` is not leaking past the gates -- IT IS REPORTING THAT THEY FAILED, which is exactly what the text asks of it. The premise that it 'answers `none` where it should not' does not survive being read against the gates. AND ON DAY2/p16 THE MAJORITY ANSWER IS NOT EVEN `none`: `observed_type` says NR 5 of 6. All four cells are gold-0.00 and counted right, three of them perfect, so the answer costs nothing anywhere in the corpus and there is no cell for a rule to aim at. NO CELLS ORPHANED: none of the four is wrong by median, so neither owner reader has anything to report, and the nine cells the entry was filed on were already re-attributed to `observed_type` by the same amendment. ONE THING WORTH CARRYING FORWARD, and it is a machinery point rather than a scoring one: WK2's 588-character `named_type` is the only shipped design in DESIGNED_TEXT resting on NO probe receipt, and no check catches that -- it is not a new slot, so `check_new_slots_were_probed` is silent, and `check_probed_fields_keep_their_text` demands full text only where evidence exists. It needs no probe on this entry's finding (textless-and-stable siblings show the slot is inert), but the GAP in what the checks can see is real and is recorded here because this entry is where it surfaced.",
    "Q26": "closed 2026-09-08 on the user's instruction (\"after that, close Q26\"). Its question was answered 2026-09-04 -- the `!` on DAY1 is INTENTIONAL -- and the declaration gap that was the entry's headline is now closed twice: the slot was RENAMED `phrased_directly_gate`, so the asymmetry is visible in the name beside seven ungated siblings; and the 2026-09-08 conversion of `slots=` to a generated attribute moved the slot sheet into rubric_h2.SLOT_SPEC, where DAY1 carries `gate: True` and its siblings `gate: False`. The `!` can no longer differ between rubric and .olx because the .olx is generated from the rubric. DAY1 is 18/18 on both sides and unstale, up from the 17/18 this entry was written against. TWO CELLS RE-HOMED to Q50 first -- DAY1/p14 and DAY1/p8, both unstable_counted_right at 8 of 9 -- which only `orphans_if_closed` could see, since both are counted RIGHT by the median. Subgoal E26 still owns the general sibling-gate-structure check.",
    "Q41": "closed 2026-09-08 on the user's instruction (\"Do Q41\", then \"close Q41\"). STEP 1 DONE AND SHIPPED: seven arithmetic phrases removed from `Q2/wgb_is_counterpart` -- three sentences cut outright (the declared site, \"Where it fires it costs the whole item\", and the rule's \"Not satisfied means the whole item is that finding\") and three amount-clauses trimmed off sentences whose judging halves survive verbatim. desc 1293 -> 940, rule 733 -> 635; Q2 prompt_sha 68a2e62f8cf7 -> 7db0c328295a, verified in the .olx and not in the design view. THE ENTRY UNDERCOUNTED ITS OWN SITE, and the reason is a reader defect fixed first: `probe.question_for` returned only the checklist half of a slot's text, so the `desc` -- which carried SEVEN of the nine phrases -- was invisible to the designated reader. 56 of 179 asked slots were under-reported. Asking it whether this sentence still shipped answered NO while the sentence was in front of the grader. NOTHING WAS RELOCATED and step 1 was wrong to expect otherwise: the arithmetic is already declared in deductions/gates/codes, so the prose was explanatory duplication of code -- which is why the wrong reader could act on it. NO CELL WAS EXPECTED TO MOVE and none was measured: after subgoal Q17's edit (c) no Q2 cell has a failing gate meeting a response that HOLDS reasons, the only configuration in which the contamination acts, so a green sweep proves nothing -- pre-registered before the edit. THE DELIVERABLE WAS THE CHECK the entry named and declined to file: `check_no_judging_field_states_what_a_verdict_costs`, wired into equivalence.py, which found the site and NOTHING ELSE (2 findings on that slot, 0 across the other 25 items and three rubrics -- the class is size one, confirmed structurally rather than from memory) and now reads SILENT. That settles the general question without a cell to watch. THE MECHANISM FINDING STANDS: a model reading a judging prompt EXECUTES an arithmetic statement in it -- Q2/p10 answered `reasons_listed` = 0 on three statements and said why in all five runs. Both owner checks read 0 before and after.",
    "Q57": 'closed 2026-09-09 on the user\'s instruction: "Its results are too various to be a coherent goal." THE ROUTING SUPPORTS THAT AND IS THE CLOSURE\'S EVIDENCE. Filed as ONE mechanism -- "a whole-item GATE that fires differently on identical input" -- and 20 cells. Re-routed by the only question that routes a cell (which field do the RIGHT runs and the WRONG runs disagree about, per side, `confident` excluded as unscored, `refers_to` included) it is SIX mechanisms over 14 cells: `you_arrange_it` 5 (DAY2/p12, NP/p12, NR/p7, NR/p18, NR/p20), `cadence_is_daily_counted` 2, the contingency trio 2, `refers_to` 2, `targets_unwanted_behavior` 2, `phrased_directly_gate` 1. THIRTEEN OF THE FOURTEEN ARE COUNTED RIGHT BY THE MEDIAN, so section 5 forbids sweeping for them and the deliverable was never a rule. FOUR CELLS LEFT ON 2026-09-08 when 18 HTTP 429 rejections recorded as scored runs were re-run -- DAY2/p17, NP/p16, PP/p17 and WK1/p9 are now `perfect` -- and the entry\'s whole "five or more fields vary together" tier (6 cells) dissolved into ONE, DAY1/p14, whose aberrant run is a healthy 4,354-character olx run and not the 429. TWO MORE went to subgoal Q64 (DAY2/p11 `matches_chosen_type`, PP/p6 `refers_to:observed_type`). ITS ONE ACTIONABLE ROUTE WAS TRIED AND WITHDRAWN: criterion 5\'s `you_arrange_it` candidate was built, shipped and probed on all 144 valid cells of the eight OC items, its printed verdict of DO NOT BUILD was WRONG (all six "new losses" were gold-0.00 cells already perfect, where a refusing gate gives the right score), the honest upside after `probe.score_impact` and a leakage revert was TWO cells, and the candidate quoted a student\'s own sentence -- "{{corpus:DAY2/p12:day2:52:80:sha=7227b09920db}} away", p12\'s answer -- so it was reverted and the eight items returned to their ledger shas. ITS 576-CALL RE-PROBE WAS CANCELLED UNSPENT on this closure. NOTHING IS ORPHANED: all 15 cells are named by Q50 or Q64, and both ownership readers read zero at the moment of closing. WHAT THE ENTRY ESTABLISHED AND SHOULD BE READ FOR: the flap lives in `!`-prefixed gate slots that carry no credit entry and therefore no pts, so one gate answering `absent` in one run zeroes a 4-point cell; and `refers_to` is a channel no readout had examined, which is where WK1/p7\'s real mechanism turned out to live -- `trigger_behavior`\'s pick, not `targets_own_behavior`, which has no verdicts of its own.',
    "Q40": 'closed 2026-09-07 on the user\'s instruction, on a SWEPT result and the day\'s one clean win. WK2/p11 IS NOW 12 OF 12 PERFECT, up from 4 of 11 wrong_by_median, and the item is 17/18 python and 18/18 olx with staleness cleared. NOTHING ELSE MOVED: sixteen of eighteen cells perfect, and every gold-0.00 cell the gate correctly refuses -- p10, p13, p14, p16, p18 -- stayed perfect, so no correct refusal was lost. THE DIAGNOSIS THAT MADE IT WORK, and it was not the one this entry filed. This entry proposed narrowing the gate, with 62 correct refusals to preserve. The actual defect was that `aimed_correctly` HAD NO TEXT AT ALL: `probe.question_for("WK2","aimed_correctly")` returned the EMPTY STRING -- sha e3b0c44298fc -- because the slot is absent from WK2\'s rubric credit list and carries no desc, no rule and no SLOT_NOTES. The entire shipped line was `- aimed_correctly **GATE** -- met/absent/unclear`. A gate that takes the whole 4-point item, inferring its meaning from its own identifier. That explains both halves of its behaviour: 95% precision, because the name is nearly self-explanatory, and a wobble on exactly the cell where the name is ambiguous -- aimed correctly FOR THE TYPE CHOSEN, or AS AN ARRANGEMENT? THE TEXT WAS ASSEMBLED FROM THE RECORD, NOT WRITTEN: sentence 1 is `rubric_h2.OC_GATES`\' own declared message for this gate turned from feedback into a question; sentence 2 is the reading BACKLOG.md records the slot ALREADY using on WK2/p8 -- \'answers aimed_correctly: met because the fault is already accounted for\'; sentence 3 covers the blanks. Gold\'s charge language is what licenses it: \'This is an example of NP\' (mistyped but IS operant conditioning -- p3, p11, p15) versus \'This example is not Operant Conditioning\' (p13, p14, p16). PROBED ON ALL 20 CELLS BEFORE BUILDING (QUALITY_CONTROL.md 2b-2 and 2a): target `met` 4/4, p3 and p15 held, no gold-4.00 cell moved, every gold-0 cell still refused, and the probe carried a LOST-REFUSAL line specifically because those cells are perfect by other means and a gate that can no longer refuse anything would have passed a scores-only test. Design registered BEFORE the build, receipt written, and the sweep gate printed `probe receipts for WK2: aimed_correctly=9a4c8a53a1a4` -- the first sweep of the day where probe/shipped identity was POSITIVELY verified rather than vacuously clean. QUESTION 1 OF THIS ENTRY ANSWERED ALONG THE WAY: the gate\'s existence is INTENTIONAL and already declared -- `OC_GATES` carries its code, message and ORDER (\'Order is part of the declaration\'), and `olx_prompts.py` records the one-item-ness as \'the fifth such divergence\' including the note that `check_sibling_slots_share_their_structure` reports nothing on any of them. This entry\'s structural half was already satisfied; what was missing was the entry knowing. WHAT IS NOT CLOSED AND HAS AN OWNER: `named_type`\'s low-rate `unclear` misread is subgoal Q55\'s -- it ALSO ships with no text, and when it fires the 2-point type charge silently vanishes. WK2\'s residue is p8 at 10/12 and p15 at 7/12, both in that entry\'s eight cells. NOTHING RE-HOMED: `measured.orphans_if_closed(\'Q40\')` reports zero before the closure. An earlier hand-rolled read of this entry\'s prose claimed WK2/p8 was sole-owned and needed moving; the prepared check says Q55 names it, and the prepared check is right.',
    "Q19": "closed 2026-09-07 on the user's instruction, having been NARROWED twice and ending with its last live cell DECLARED. THE ENTRY'S THESIS STANDS AND IS LOAD-BEARING ELSEWHERE: the LATER-BOX gradient -- a STATE the student ends up in, or another ACTIVITY rescued by being taken up in the behaviour's place or by a stated endpoint -- is what decides Q4c's consequence boxes, and it is why TWO divergences were retracted in its favour (OFF_DOMAIN_CONSEQUENCE_CHARGED_ONCE on Q4c/p9 and DISTAL_CONSEQUENCE_CHARGED_ONCE on Q4c/p20). Closing this entry does not retire the frame. WHAT WENT OUT OF SCOPE FIRST: the Q4b/p4 repeat criterion, settled as a verified gold divergence after FOUR measured implementations, two of them from this session -- a report-slot pair that was SWEPT (p4 0/12 to 12/12 scoring gold exactly, but p13 fell 4/12 to 0/12 and p16, p20 and p8 all fired; item down 3) and three further wordings probed on all 19 valid cells. ANTECEDENT_REUSED_AS_BEHAVIOR now records all four and ends 'treat as settled unless someone brings a MECHANISM rather than a wording'. WHAT THE Q4b RE-SWEEP THEN SETTLED: the item is 17/19 on BOTH sides with staleness cleared, twelve cells perfect, and NO UNDECLARED WRONG CELL. Q4b/p13 recovered to 9/12 -- its collapse was entirely the reverted wording -- and Q4b/p16, which subgoal Q53 had listed as a defect at 1/12, is PERFECT at 12/12; its 1/12 had measured the reverted prompt, which is why `measured.warn_if_stale` now speaks from `cell_bands` and from the readouts. THE LAST LIVE CELL, Q4c/p20, IS NOW DECLARED. It is 0 of 12, deterministic on both sides, and gold charges its second example -2 for needing 'more explanation on how your second example is a direct consequence of lack of sleep'. THREE HYPOTHESES DIED ON IT, all measured and all recorded in the re-instated divergence: endpoint-present (killed free by an all-golds readout -- ELEVEN full-marks cells state no endpoint either), state-versus-activity (read cleanly across all nineteen valid cells, then failed its probe at 1 of 4 while crediting p9 where gold charges -4 and costing p11 its `duplicate`), and the shipped rule itself. THE GRADER'S OWN WORDS EXPLAIN WHY NO RULE REACHES IT: it classifies the box CORRECTLY as an activity and credits it because 'it explicitly states what lack of sleep leads to' -- satisfying the activity clause's escape FROM THE BOX'S OPENING FRAME, '{{corpus:Q4c/p20:second:0:53:sha=21407d303656}} ...', which every box on the item carries because the item asks for consequences. The escape is satisfied by the prompt's own scaffolding on all twenty cells. AND A RETRACTION WAS FALSIFIED ALONG THE WAY, which is the transferable lesson: DISTAL_CONSEQUENCE_CHARGED_ONCE had been retracted saying 'the rule now carries it, so there is nothing left to declare' -- reasoned from a FRAME that explains the cell, with nothing checking that the SHIPPED TEXT implements the frame. That is subgoal E56's design-versus-shipped gap one level up, and it is now re-instated with our credit kept, because our answer is the one CONSISTENT WITH GOLD'S OWN TREATMENT: the retraction itself recorded that p2, p7 and p12 'reach their consequence through an unstated step and are credited'. Gold demands directness once and waives it three times. TWO CELLS RE-HOMED to subgoal Q50 before closing, using the prepared readers: Q4b/p13 and Q1/p18. Q6/p18 was co-owned there already; Q4c/p20 needs no QC owner now that it is declared. Both owner checks read 0.",
    "E55": 'closed 2026-09-07 on the user\'s instruction, and the closure ABANDONS ITS MAIN DELIVERABLE rather than completing it -- which is recorded here plainly so nobody later reads this as done. WHAT WAS DELIVERED: `measured.derived_verdicts(item, result)`, a READ-SIDE reader that computes the verdicts a recorded app result leaves null, from the sheet\'s own `expect="X:Y=VALUE"` clauses and the pick the result does record. On NR\'s olx side `demonstrates_type` was None in 120 of 120 results and is now readable in all 120 (met 91, absent 29), and it agrees with the mirror -- which answers the slot directly -- on 19 of 20 cells. It is a READ AND NOT A WRITE by design: filling `verdicts` in the stored artifact would put inferred values where readers expect answered ones, and a slightly wrong derivation would manufacture false evidence in a file later readers trust. THE 20th CELL IS NOT A FINDING, on the user\'s correction: NR/p15 reads `absent` 6/6 on python and splits 3/3 derived on olx, and a 3-of-6 split against 6-of-6 is inside the noise floor subgoal E51 measured -- an UNCHANGED prompt moved three of twenty cells, one of them by four runs of six. I had called it a finding; it is meaningless random variation, and the reader\'s value is that the slot is READABLE AT ALL, not that one cell disagrees. WHAT IS ABANDONED, and it is most of the entry: the twelve declared decomposition divergences stand. 2b\'s `sentence_1/2/3` against `sentences_given`, item 3\'s `example_1/2` against `changes_given`, and Q1\'s and Q2\'s `reason_1/2/3` against the aggregate scaffold are all still one-sided, so a per-slot readout on those four items still sees half the sample, and `check_slot_sets_match_gold` -- the strongest gold-alignment instrument in the repo -- remains DARK on one side for each of them. NEITHER SIDE IS WRONG AND THE TOTALS AGREE (2b 20/20 both sides, Q2 19/20 both, NR identical on all twenty), which is why subgoal E53 declared them rather than fixing them and why closing here costs no measured accuracy. WHAT IT COSTS IS DIAGNOSTIC REACH, and the entry\'s own argument for that stands unrefuted: every readout that found something worked by reading ONE SLOT ACROSS TWELVE RUNS ON BOTH SIDES. TWO CORRECTIONS THIS ENTRY EARNED ALONG THE WAY, kept for the next reader: its stated order ("Q1 first") was stale -- Q16 closed and Q1 went STALE PROMPT -- and Q2 is the item that is current with a live subgoal waiting; and its NR pair was MISCLASSIFIED, being the E53 recording gap rather than a decomposition divergence at all, since the app HAS the name `barrier_is_not_this_type` and simply records it null. ONE CELL RE-HOMED to subgoal Q50: WK2/p15, this entry\'s only sole-owned cell. If the enumeration work is ever wanted, file it fresh against Q2 -- current, handout 1, with subgoal Q44 live on its p6 -- and not against Q1.',
    "E45": "closed 2026-09-07 on the user's instruction, with every condition the entry set for itself verified by the PREPARED readers rather than by reading prose. DELIVERED: `measured.unstable_cells_without_an_owner`, beside its wrong-cell sibling, reading `cell_bands` and `_live_subgoal_owners`, ratcheted at UNSTABLE_UNOWNED_BUDGET = 0 and currently SATISFIED. THE THREE DESIGN CONSTRAINTS, all met and all decided rather than inherited: (1) A BUDGET, NOT A ZERO -- it is a ratchet, and it happens to stand at 0 because the cells got dispositions, not because the check was weakened. (2) WHICH OWNERSHIP COUNTS was the question the entry refused to settle in advance, and it is settled EXPLICITLY in the docstring: `any`, not `by_side`, as a DELIBERATE WEAKENING, because `by_side` is populated only from a bare pN under a title naming the item, so meeting it for cells spread over six items means naming all six in one title -- which makes every bare pN in that entry claim a cell on all six and MASKS future orphans wholesale. That is not hypothetical: naming Q3 in subgoal Q30's title claimed eleven cells, and Q50's claimed three it did not mean. A standard that can only be met by masking future orphans is the wrong standard. (3) IT MUST NOT FIRE ON A DECLARED CELL -- and this was the LAST constraint outstanding, closed today. The check's own docstring had named the gap: 'a ceiling recorded only in a CLOSURE NOTE is not visible here -- 2a/p14 is exactly that case, and it passes only because subgoal Q50 names it. That is a real gap.' Owned by accident is not declared. So: `measured.DECLARED_CEILING_CELLS` now carries 2a/p14 with Q35's own three reasons (no open subgoal names any 2a cell or the `verdict` slot; the item's own Q2 had closed at its ceiling and handed the cell on; and the defect is ONE SLOT IN TWO RUNS where THE TWO DISSENTING RUNS DISAGREED WITH EACH OTHER on a garbled sentence the rubric declares irrelevant -- no direction, so nothing for a rule to aim at); the check exempts a declared ceiling BY DESIGN rather than by Q50's continued existence; `declarations_for` reports it so the one-call lookup is complete; and `ceiling_declarations_that_expired()` ratchets it, flagging a ceiling that has gone perfect (drop it) or gone wrong by median (it needs a real owner instead). KEPT SEPARATE FROM `GOLD_DIVERGENCES` DELIBERATELY: a divergence says our answer is the endorsed one and gold is the outlier; a ceiling says the cell cannot be settled either way. Conflating them would let a ceiling be cited as vindication -- the exact error made earlier the same day in proposing to rescore Q6/p8 towards gold against its own A_NO_CHANGE entry. AND THE GENERAL RULE, on the user's question 'should ceilings ever only be recorded in a closure note?': no. `enforcement.check_closure_ceilings_are_declared()` now REFUSES a sweep when a closure note calls a cell a ceiling and no table says so, fire-tested by removing 2a/p14 from the table -- Q35's closure spoke at once. A closure note is prose keyed by GOAL LABEL; nothing indexes it by cell, so no check can consult it and no reader of that cell will ever find it. THE ENTRY'S OWN HAZARD CHECKED BEFORE CLOSING, as it instructed: subgoal Q50 is OPEN and owns the cells, and both owner readers return 0. THE TEN CELLS WERE NEVER THIS ENTRY'S WORK -- three of them (Q4b/p17, Q4c/p8, Q4c/p11) have since gone PERFECT and the rest are Q50's, per the series split the user made when both were filed: reading and routing cells is quality control, building the check that finds them is machinery.",
    "E57": "closed 2026-09-07 on the user's instruction, and the decision it records is CHANGE NOTHING -- reached by measurement after the entry's first pass said only 'probably'. THE TEST THE ENTRY SET ITSELF: find a cell where `harms_listed` is RIGHT, the benefit count is LARGER, and gold wants the larger number. Every Q1 cell was then read against gold's own per-cell reason count and both branches of the tier. THE TIER IS REQUIRED ON SIX CELLS, where the benefit branch would be wrong and the harm branch is right: p3 (gold 3, harms 3, ben 2), p6 (1, 1, 2), p11 (3, 3, 2), p17 (3, 3, 1), p18 (3, 3, 2), p19 (3, 3, 1). IT IS HARMFUL ON ONE: p9 (gold 2, harms 1, ben 2) -- and that harms value is the DECLARED GARBLED_CLAUSE_READ_LITERALLY misread, so with harms correct at 0 the benefit branch fires and returns gold's 2 unaided. p10 and p16 answer harms 0, so the benefit branch is already what runs and both are right; p14 matches NEITHER branch, which is `harms_listed` precision and belongs to subgoal Q54. SO A COMBINING RULE WOULD BREAK SIX CELLS TO FIX ONE DECLARED CELL: `max(harms, benefits - failing)` answers 2 on p6 where gold wants 1, and 2 on p3/p11/p18 where gold wants 3. The tier is not an approximation of gold's rule; on this corpus it IS gold's rule, and the switch does real work six times. WHAT THE ENTRY LEAVES BEHIND, and the reason it earned filing even though nothing changes: the AMPLIFICATION is real and undocumented anywhere else -- a +-1 in `harms_listed` does not cost a fraction, it switches which count is used and costs a WHOLE POINT, so that slot's precision is load-bearing in a way `benefits_listed`'s is not. Any reader diagnosing a wrong Q1 cell should know it. TWO CORRECTIONS MADE IN THE COURSE OF IT: a first tagging pass called p10 and p16 tier-discards by failing to check harms>=1 -- the tags were wrong, the numbers were not; and Q2 has a `reasons_given` slot but NOT this tier text, so the amplification is Q1-only and this entry never reached Q2. NO CELLS ATTRIBUTED, nothing to re-home, nothing swept: the whole entry cost zero calls.",
    "Q47": 'closed 2026-09-07 on the user\'s instruction, as a CEILING rather than a win or a divergence in our favour -- and the distinction is the point. THREE PROBE ARMS, 240 calls, all 20 cells scored against gold AS AMENDED (QUALITY_CONTROL.md 2b-2/2a-3). ARM 1, the engagement test -- where the antecedent names something OTHER than the absence of the goal behaviour the change must ACT ON that thing -- reached the target Q6/p2 `incomplete` 4 of 4 and left DECLARED Q6/p8 at `met` 4/4 on both boxes, the first wording on this item ever to do both; it fired on p3 4/4, p4/a2 4/4, p10 3/4 and p16/a2 3/4, all credited by gold. ARM 2 dropped the one clause the grader had quoted back ("a change that only commits to doing the goal behaviour more") and FIXED EXACTLY the two boxes whose reasoning cited it -- p3 4/4 to 0, p10 3/4 to 0 -- at the cost of one target run, leaving p4/a2 and p16/a2 firing with readings that are CORRECT ABOUT THE TEXT: tracking a situation only monitors it, and a change named in four words says nothing about how it works. ARM 3 carried gold\'s leniency explicitly and fixed p4 and p16 -- AND LOST THE TARGET ENTIRELY, 0 of 4. THE OBSTACLE IS STRUCTURAL, NOT VERBAL: what decides p2 is exactly what crediting p4 and p16 instructs the grader to ignore, because all three changes are weakly aimed at their antecedent and gold charges one while crediting two. GOLD IS RIGHT ON p2 AND WE ARE WRONG -- \'{{corpus:Q6/p2:affect_c2:3:39:sha=7bc493d62ecd:shape=C1}} does not change your {{corpus:Q6/p2:state_a2:17:50:sha=7f56e7f06c95}}\' -- so this is NOT a divergence to declare in our favour, unlike Q16, Q18 and Q33 which closed today on gold contradicting itself. The 1.25 is left unclaimed and the measured reason is written into GOLD_SLOT_DISAGREEMENTS_KNOWN[(\'Q6\',2)]. TWO EARLIER FINDINGS OF THIS ENTRY WERE THEMSELVES CORRECTED ALONG THE WAY, and both corrections matter more than the entry\'s original claim: (1) its premise -- that `affect_c*`\'s long rules \'genuinely discriminate\' at absent 48/132 -- is FALSE; over all 480 recorded answers every `absent` is on a box that HOLDS NOTHING and no box with text was ever called `absent`, so that count is box-emptiness, and the only real judgement the slot makes is `incomplete` on ONE box-slot in the corpus (p16/c2, where gold does charge). (2) A refutation I wrote here -- \'gold never charges that the change is inadequate\' -- was read off TRUNCATED gold summaries and is wrong; p2\'s full note says the opposite in the grader\'s own words. NINE UNSTABLE CELLS RE-HOMED to subgoal Q50, using `unstable_cells_without_an_owner()` before the closure. Q6/p8 is NOT re-homed: declared. Q6/p2 is NOT re-homed: it is the ceiling this entry closes on.',
    "Q16": 'closed 2026-09-07 on the user\'s instruction. Its only remaining wrong cell, Q1/p9, is a DECLARED divergence -- GARBLED_CLAUSE_READ_LITERALLY -- so there is no rule left to write. READ AGAINST ALL VALID GOLDS BEFORE CLOSING, and the answer was that the divergence cannot be closed: the cell turns on ONE ungrammatical clause whose literal sense is the opposite of the intended one -- "{{corpus:Q1/p9:response:181:270:sha=ede628dbabb5}} health" -- read literally exercising WILL HAVE complications, while gold reads the intended "avoid having". Both readings are defensible and the reading alone decides the cell, because a harm flips it into tier one: gold counts 0 harms and 2 benefits and scores 4, the literal reading gives harms_listed=1 and scores 3, and `benefits_listed` is a stable 2 in every run measured. TWELVE CONFIGURATIONS were measured -- 1/6, 3/6, 6/6, 3/6, 4/6, 2/6, 1/6, 1/6, 4/6, 4/6, 3/6, 1/6 -- and the single 6/6 came from a prompt that COST p7 four of six runs, while three probes built to isolate what produced it each scored p9 WORSE than their baseline (2/6, 1/6, 1/6). This is a coin flip on a garbled sentence, not a criterion gap; the only lever left is a charitable-reading instruction with corpus-wide blast radius. NOTHING RE-HOMED: Q16 named no unstable cell of its own and no other cell of its own.',
    "Q18": 'closed 2026-09-07 on the user\'s instruction. Its only remaining wrong cell, Q4b/p12, is a DECLARED divergence -- B_NOT_ACTIVE -- and reading all 19 valid cells of the item against gold shows the divergence CANNOT be closed, because GOLD IS INTERNALLY INCONSISTENT ON THE SHAPE. Gold CREDITS pure avoidances: p12\'s "{{corpus:Q4b/p12:second:0:46:sha=80608b1bd345}} ... {{corpus:Q4b/p12:second:76:126:sha=4281c899b6ba}} bad" at 5.0, and p11\'s "{{corpus:Q4b/p11:first:0:36:sha=22abf12cda4f}} symptoms" at 4.0. It CHARGES boxes naming states or feelings on p8, p10 and p20. And on the closest pair in the corpus it goes both ways: p19\'s "{{corpus:Q4b/p19:first:28:69:sha=ac83b3561af9}} night" is CREDITED in full, p8\'s "{{corpus:Q4b/p8:second:49:99:sha=806bfb376619}}" is CHARGED. So any rule crediting p12\'s not-doing to match gold would also credit what gold charges on p8 and p20 -- which is the trade our `behavior_*` fifth test currently resolves in gold\'s favour on those two. A per-cell exception is the only route, and a declaration IS that exception. THE ENTRY\'S OWN HISTORY IS KEPT: its structural tie-break on `b2_names_besides` was measured and reverted on 2026-09-05 -- it worked mechanically and made p12 worse -- and that reverted attempt is part of why this closes as a divergence rather than as unfinished work. NOTHING RE-HOMED: no unstable cell was named only here.',
    "Q33": 'closed 2026-09-07 on the user\'s instruction. Its only remaining wrong cell, Q4a/p14, is a DECLARED divergence -- A_NOT_ANTECEDENT, with the fuller ANTECEDENT_RULE_APPLIED_AGAINST_ITSELF beside it -- and that declaration proves the divergence unclosable in the strongest form any of today\'s three took: GOLD DEPARTS FROM THE RULE GOLD ITSELF STATES, IN OPPOSITE DIRECTIONS, ON TWO CELLS. The graders spell the rule out on three other rows of the item -- p3 docked "Need further explanation for how not eating is an antecedent of lack of exercise", p4 "how does grumpy emotions lead to lack of sleep?", p20 "An antecedent/trigger is something that causes you to engage in the UTB" -- AND WE SCORE ALL THREE EXACTLY RIGHT, 6/6 each. Then p14 STATES that link and gold rejects both its examples for -4, while p19 states NO link and gold credits it in full with no feedback. No single criterion can credit p14 while refusing p19, so closing this needs gold to be self-consistent rather than a better rule. TWO CELLS RE-HOMED to subgoal Q50 before closing: Q4a/p19 and Q4a/p6, both unstable. Q4a/p19 matters particularly -- it was named ONLY inside the divergence entry and by this entry\'s prose, never as an owned cell, so it would have been orphaned in a way `wrong_cells_without_an_owner` could never report. WHAT DOES NOT CLOSE WITH IT: this entry\'s title is about the PAPER scorer, and paper remains essentially unmeasured -- 24 of 26 items have no paper number, which is subgoal E28\'s deliverable, not this one\'s. The four cells this entry was opened on are decided on the two engines that ARE measured; if the paper sweep later disagrees, that is E28\'s finding to file and a fresh entry to open.',
    "E56": "closed 2026-09-07 on the user's instruction, held open until the framing arm returned so its result could be recorded rather than guessed. DELIVERED: FOUR LINKS, each refusing in `sweep_gate.py` and reported by `agreement.cheap_checks_gate` and `equivalence.py --enforcement`. (1) designed==shipped: `DESIGNED_TEXT_SHA.json`, all 145 rubric desc/rule fields, reporting CHANGED/MISSING/STALE separately; acceptance per field via `--accept-design-change`. (2) probed==shipped AT PROBE TIME, by construction: `probe.question_for` lifts the question out of `build_web_prompt`, the same call the sweep renders from, so there is only one string -- and retyping is not safer for being careful, because the checklist note is `rule` OR `SLOT_NOTES` OR `desc` and on 20 of 68 asked slots the obvious shortcut lifts the wrong text. (3) probed==shipped AT SWEEP TIME: `PROBE_RECEIPTS.json`, the only one that catches a probe read on Monday and cited on Wednesday. (4) baseline==the prompt measured: `sweep_readout` refuses a before-snapshot whose prompt_sha differs from the ledger's -- bought with a wrong KEEP verdict the same day, where the snapshot held an aborted sweep's numbers and the readout printed NET +3 while the item had FALLEN 3 against the pre-registered baseline. BOTH GRADERS COUNT, on the user's correction: all 116 credit slots resolve -- 68 asked, 25 derived (the sheet clause, probed by EVALUATING it at zero calls), 23 composite -- where the first cut refused 42 of 110 and all of 1b, T1 and T2. PLUS `editguard.py` and `DEFINITIONS.json`: three times in two days a slice-bounded edit ate a neighbouring declaration and THE FILE STILL PARSED, once leaving --preflight raising NameError for days. `safe_write` refuses an undeclared drop and refuses a declared drop that did not happen; the 1044-name inventory catches any other route at gate time. E56a RESOLVED: the gate REFUSES an unprobed new slot, upgraded from a notice on the user's decision. E56b RESOLVED BY THE REVERT, not by measurement -- the unprobed routing clauses went with the slots they served, and whether they worked is unanswered, not answered. E56c DELIVERED: `check_designed_text_is_the_measured_text`, after Q4b's design of record turned out to be a PARAPHRASE of the probe, keeping the comparison target and dropping the two clauses that make the test work -- a build faithful to it would still have over-fired. E56d RESOLVED, and THE FIGURE AS FILED WAS WRONG BY FIVE TIMES: 145 of 147 fields are sha-only, not 30 of 145. The rule decided is FULL TEXT FOR FIELDS WITH EVIDENCE, enforced by `check_probed_fields_keep_their_text`. EVERY CHECK IS FIRE-TESTED, and two were worthless until they were: `check_new_slots_were_probed` read `cells[pid]['slots']` where a cells entry is an INT, so it was INERT while reporting clean, and the gate's own probe-receipt reporting died on a NameError inside its own message. ONE HYPOTHESIS REFUSED ADMISSION, measured not assumed: that the CONDITIONS a question is answered under are part of the question. The original probe carried 'you report, you do not grade' in its SYSTEM prompt and the swept wording had no such framing; putting it into the desc and measuring all 19 valid cells made the over-firing WORSE, three cells to five. A pleasing generalisation that fails its own probe is recorded as failed. NO CELLS ATTRIBUTED, so nothing is orphaned; no bulk regenerate exists anywhere in this family, deliberately, because an inventory that agrees with whatever the tree says enforces nothing.",
    "Q49": "closed 2026-09-07 on the user's instruction, deliverable DONE and NO RULE WRITTEN -- the entry's own prescription. Two findings, from artifacts and the .docx, zero calls. FIRST, THE ANOMALY IS RESOLVED AND THE TITLE CONFIRMED. 'p15 10/12, NO SLOT FLIPS AT ALL, yet the score varies' was reading VERDICTS ONLY. The score is a function of verdicts PLUS the matching answers, which `cross_path.result_cell` already normalises: across the seven cells 5 verdict-signatures map to more than one score, and including `answers`/`refers_to` ZERO do. Nothing unrecorded moves the score; the MATCHING CHANNEL is not merely where the drift sits, it is the whole of it. p15 reads 11/12, not 10/12. SECOND, AND THIS ONE WAS LARGELY REFUTED BY THE RECORD -- which is the part worth keeping. A readout of all 40 state_c/affect_c box-slots flagged nine as cut so the structure answers the slot's own question. The user asked for them to be fixed AND WARNED THAT MANUAL OVERRIDES MIGHT EXIST. They do: `agreement_app.CONSENSUS_FIXES` governs most of these boxes and its own rule forbade the patch. EIGHT OF THE NINE ARE NOT DEFECTS -- five duplications (p10 c1+c2, p14 c1+c2, p18/c1) are the DECLARED permitted same-element overlap, in that table's words about the same shape on p4: 'the student wrote only one there; that is the permitted same-element overlap, not a duplication'; p18/c2 is a DECLARED judgement the table names explicitly ('a response with no second consequence to assign at all (p18) is a judgement about the answer ... must not be patched here'); and p15/c1 + p15/c2 are FAITHFUL, both items being [state_a][change_a][one consequence sentence] with no affect clause to assign. ALL FOUR FIXTURE AUDITS PASS CLEAN ON Q6. ONE IS REAL: Q6/p1's `state_c1` holds ITEM 2's consequence sentence while `state_c2` is EMPTY, item 1's own consequence is welded into `change_a1`, and `change_a2` repeats `state_a2`. IT IS NOT FIXED AND THAT IS DELIBERATE: p1 is PERFECT 12/12, coverage holds so no audit calls it a defect, and Q6's fixture is the frozen consensus whose churn already invalidated two published comparisons -- so it is recorded in BACKLOG.md against the next re-freeze, the same disposition as memory `q4a-p18-duplicate-antecedent`. A FIRST INFERENCE WAS REFUTED MID-READOUT and the correction is the useful part: empty affect boxes matched gold's affect charge in 33 of 40 slots, which looked like the fixture encoding gold's judgement, until p6, p7 and p19 read against the .docx showed the WHOLE ITEM blank there (p7's item 2 is an empty ruled line), so those boxes are faithful and gold charges correctly. WHAT THE READOUT BOUGHT ELSEWHERE, and it is the largest result: subgoal Q47's central premise is REFUTED and recorded there. Over all 480 recorded `affect_c*` answers, every `absent` -- 180 of 180 -- is on a box that HOLDS NOTHING, and no box containing text was ever called `absent`. The 'absent 48/132, genuinely discriminates' evidence for copying that slot's rule shape onto `change_a*` is box-emptiness, not judgement. What survives is the narrow `incomplete` reservation, which fires on ONE box-slot in the corpus -- p16/c2, 11 of 12 runs -- where gold does charge. Q47 also inherits the one surviving piece of finding (2): where DOUBLE DUTY is credited, p18/c1 having its single consequence sentence copied into the affect box while p15/c1's comparable sentence was left empty. FOLLOWUPS DISCHARGED BEFORE CLOSING, at the user's instruction not to close with work outstanding: the nine boxes decided (a), Q47's premise re-checked and recorded (b), Q6/p1 written into BACKLOG.md. `handouts.suspect()` was deliberately NOT invoked on any box -- declaring is a decision, a suspect cell becomes untrustworthy INPUT that may not be cited for or against gold, and none of these earned that. SEVEN CELLS RE-HOMED to subgoal Q50: p18 6/12, p16 9/12, p15 11/12, p4 11/12, p6 11/12, p5 11/12, p10 11/12. Q6/p2 and Q6/p8 stay with Q47 and are NOT fixture artefacts -- p8's boxes are blank-and-faithful, p2's hold distinct text. NO TENTH MATCHING WORDING WAS PROPOSED. Nothing is orphaned.",
    "Q36": "closed 2026-09-07 on the user's instruction, on the entry's own argument and its own measurement. 1a/p6 -- the cell this was filed for -- is 12 of 12 RIGHT at gold 6.00 on BOTH sides, and `baseline_week` answers `absent` in all twelve pooled runs. THE ENTRY ITSELF ASKED FOR THIS: 'close this entry and refile the label question if it is still worth asking'. CREDIT WHERE IT IS DUE, WHICH IS NOWHERE: no edit was ever made against 1a/p6. The cell moved under sweeps aimed elsewhere, so the honest reading is that the rule was always capable and the old 11-of-12 was sampling, not a defect -- the same lesson subgoal E51 measured on Q2, where an UNCHANGED prompt moved three of twenty cells and one from 6/6 to 2/6. WHAT IS NOT CLOSED: the second half of the title, 'the label-versus-data question underneath it'. That question is not about p6's score, did not close with it, and is left UNFILED rather than pretended finished -- refile it if it is worth asking. FOUR CELLS RE-HOMED to subgoal Q50 before closing: 1a/p14 9/12, 1a/p15 11/12, 1a/p19 11/12, DAY2/p7 7/10. DAY2/p7 is flagged there as not clean instability -- it read 11/12 after Q46's fix and fell to 8/12 when the criterion-8 leak was removed. Nothing is orphaned.",
    "Q21": "closed 2026-09-07 on the user's instruction, on a headline that was measured, doubled and REPRODUCED ON BOTH ENGINES rather than argued. `you_arrange_it` is refused 66 times across the twelve pooled runs with 18 in cells that scored wrong -- 72% precision against the 71% this entry opened on, so doubling the sample moved it one point. The gate really does run at roughly three refusals in four being right, and that was not an artefact of reading one column: 32/8 (75%) on the olx against 34/10 (71%) on the python -- same instrument, same imprecision, both engines. THE CONCLUSION IS THE ENTRY'S OWN AND IT IS A NEGATIVE ONE: 'neither is a threshold problem'. Its two wrong cells, NR/p4 and NR/p20, are rows gold passed in SILENCE, and NR/p20's readout says our refusal is DEFENSIBLE -- not feeling tired is a natural consequence the student does not arrange, which is exactly what the gate asks. So the precision figure and the false-positive question point at the same cells from different directions, and there is no threshold to move. The wrong cells were already subgoal Q34's. TWO CELLS RE-HOMED to subgoal Q50 before closing: NR/p11 7/11 and NR/p20 9/11; NR/p11's gold is DECLARED in GOLD_CODE_KNOWN, so its residue is a variability question only. Nothing is orphaned.",
    "Q17": (
        "closed 2026-09-06 on the user's instruction, with both cells it was scoped down to now scoring right and the repair traceable to a fix nobody wrote for them. Q2 is 19/20 on both sides. Q2/p17 IS THE DECISIVE ONE. This entry recorded it as A CONTROL THIS ENTRY BROKE: '(b) cost it: `wgb_inverts_utb` answers `met` where it must answer `absent`, and gold charges -2. It was 12 of 12 and this entry named it as a cell that must not move.' MEASURED NOW: `wgb_inverts_utb` answers `absent` in 12 of 12 -- exactly what the entry said it must -- and the cell is right 11 of 12. The broken control is repaired. Q2/p16, the open residue of (d)'s persistence clause, is right 10 of 12 with `wgb_inverts_utb` met 11 and `reasons_given` reading 3 in eleven runs. Unstable, not wrong. AND NEITHER WAS FIXED BY A RULE. Three formulations of (b) were measured and none is in the tree. What changed is subgoal E52's SHEET correction: `unclear` was declared in the sheet's slots= as `wgb_inverts_utb:...:unclear@2` while the rubric had been edited to remove it, so the grader kept being offered a verdict its map could not emit. Dropping it from the SHEET moved Q2's prompt sha for the first time -- E52's own note calls that 'the first evidence any fix reached the grader'. THE LESSON IS THAT THIS ENTRY SPENT THREE MEASURED FORMULATIONS REWORDING A RULE WHILE THE DEFECT WAS AN UNREACHABLE OPTION IN THE SHEET. Check what the grader is OFFERED before rewording what it is TOLD. CLOSED WITH THE RESIDUAL STATED: both cells remain `unstable_counted_right` and are named in subgoal Q50, the variable-cell register. No cell this entry names is wrong by median on either side. Its (a) and (c) results stand as recorded (p20 1->12/12, p7 4->12/12, p10 1->12/12), (b)'s cell p18 was subgoal Q43's and closes with it, and p6 is subgoal Q44's. Verified after the checkbox flipped, not before: `unstable_cells_without_an_owner` reads 0 -- three closures today each orphaned every cell their PROSE named, not just their headline cells."
    ),
    "Q43": (
        "closed 2026-09-06 on the user's instruction. Its one cell now scores right and none of the three rule formulations it measured is responsible. THE CELL. This entry recorded Q2/p18 at 2.00 in 7 of 12 pooled runs, with `wgb_inverts_utb` answering `absent` in exactly those 7 and `met` in the other 5, and nothing else varying. MEASURED NOW: right 11 of 12, `wgb_inverts_utb` met 11 and absent 1. `reasons_given` reads 2 in all twelve runs and gold's own count is 2, exactly as this entry had already checked twice -- so the count was never involved and is not involved now. THREE FORMULATIONS WERE MEASURED AND ALL WERE REVERTED, one of them deterministically wrong at 0 of 6. The cell resolved without any of them, on subgoal E52's SHEET correction: `unclear` was declared in the sheet's slots= for this very slot while the rubric had been edited to remove it, so the grader was being offered a verdict its map could not emit -- five recorded divergences at an IDENTICAL prompt sha. Dropping it from the sheet moved Q2's prompt sha for the first time. SO THE INVERSION BOUNDARY WAS NEVER THE PROBLEM, or at least was not the reachable one: three attempts to word it failed while an unreachable option sat in the sheet giving the grader somewhere else to go. That is the same shape E52 found on this slot from the artifact side, and it is why this entry could not move the cell by rewording. THE ABORT THIS ENTRY RECORDED IS ALSO SETTLED, as noise rather than as a finding: it aborted on a cell movement that the 2026-09-06 noise-floor measurement -- an unchanged prompt moved 3 of 20 cells, one by 4 runs of 6 -- places inside resampling. CLOSED WITH THE RESIDUAL STATED: p18 is `unstable_counted_right` at 11 of 12, not fixed to certainty, and is named in subgoal Q50. Verified after the checkbox flipped: `unstable_cells_without_an_owner` reads 0."
    ),
    "Q30": (
        'closed 2026-09-06 on the user\'s instruction, with its three cells resolved, re-homed or re-filed and none abandoned. THE ENTRY WAS TITLED FOR THREE CELLS and they turned out to be three different kinds of thing. 1c/p11 IS FIXED AND NOW MERELY VARIABLE: 0 of 12 to 9 of 12 under this entry\'s own `series_box_holds` pick, and PERFECT 6 of 6 on the python side. 1c now has no always_wrong and no wrong_by_median cell on either side. Adopted by subgoal Q50 as a variable cell. THE SWEEP THAT MEASURED IT RETURNED \'REVERT\' AND THAT VERDICT WAS WRONG TO ACT ON -- it summed a genuine win on p11 with a wobble on `title` (an unrelated slot) and seven cells of one-run, one-side drift. E51\'s net rule answers \'did this hurt\' and cannot separate \'helped here, hurt there, for different reasons\'. The per-cell reading separates them; the total cannot. Reverting would have restored an always_wrong cell to recover drift. AND THE `title` WOBBLE WAS PROBED RATHER THAN PATCHED (QUALITY_CONTROL.md 2a), 24 calls: asked standalone, the criterion answered `met` on p16\'s "Behavior Modification" in 0 of 4 runs as generic, `met` 4/4 on p13\'s one-word "Sleep", `absent` 4/4 on all three empty titles, and still caught the synthetic "Chart Title" placeholder 4/4. So THE RULE IS CORRECT AS WRITTEN and the 5 `generic` runs inside the full prompt are DRIFT, not a mis-specified scope. A rewording would have treated a symptom. That probe is the cleanest demonstration on record of a probe saying STOP. Q3/p13 needed no action here: it is owned by subgoals E45 and Q50 already. Q5/p4 WAS RE-FILED AS SUBGOAL Q52 RATHER THAN CLOSED OVER OR SWEPT INTO Q50. It is always_wrong at 0 of 12 with ZERO spread -- example_1 and example_2 both `wrong_kind` and `reasons_substantial` absent, 12 of 12 on both sides -- so it is the opposite of a variable cell, and Q50\'s charter is cells counted RIGHT that wobble, with a standing instruction not to sweep for them. Filing it there would have buried a hard disagreement in a table that tells the reader to leave it alone. It is Q5\'s only wrong cell on an item that is 19/20 both sides. THE ENTRY\'S OWN THESIS SURVIVES AND IS NARROWED: \'where we charge MORE than gold\' was filed as the exception to a lenient corpus, and after today exactly ONE of the three cells still charges more than gold. That is Q52\'s, and it is a disagreement about whether the effect-vs-payoff criterion applies at all -- not a rule failing to fire. A CORRECTION MADE ALONG THE WAY: this entry\'s arithmetic note on gold\'s unreachable 7.0 for 1c/p11 was checked again and stands; the gold correction to 6.0 is in CORRECTED_GOLD and the cell now scores 6.0 in 9 runs of 12, which is that correction being confirmed by measurement rather than argued. Verified before closing: `unstable_cells_without_an_owner` reads 0, and no cell this entry named is left without an open owner.'
    ),
    "Q22": (
        "closed 2026-09-06 on the user's instruction, on its own measured result, and it is the best-behaved edit of the day. ONE SENTENCE: a trigger that POINTS AT the student's own goal without restating that goal's schedule states no period of its own, and reading what the goal says elsewhere does not make the goal's schedule the trigger's. DAY2/p8 went 5/12 to 10/12 and WK2/p15 4/12 to 7/11; DAY2/p9, which the clause was NOT aimed at, gained anyway 3/12 to 10/12; and ALL EIGHTEEN goal-referencing controls held -- the readout printed 'controls now refusing: NONE'. DAY1/p9, the abort cell and the ONLY cell in the corpus where this gate agrees with a gold cadence charge, HELD at 11/11 with the gate still refusing. Item totals DAY2 python 16 to 18 and olx 16 to 17 (net +3), DAY1 and WK1 18/18 at net +0. WK2 came back net -1, driven by WK2/p11 falling 6/12 to 4/11 -- a cell this clause does not touch and which had already dropped three runs in the morning's leak-fix sweep. WHY IT WORKED WHERE THE DAY'S OTHER EDITS DID NOT, and this is the transferable part: ITS SCOPE WAS PROVABLE BEFORE A CALL WAS SPENT. Twenty-one cells across the four items have a trigger that refers to the student's goal, and the gate already answered `met` 12 of 12 on EIGHTEEN of them -- it handled the construction right 86% of the time. All eighteen RESTATE A PERIOD beside the reference, so the clause could not reach them, and the only two that do not restate one were exactly the two cells where the gate refused what gold credits. Subgoal Q45's clause and Q47's eleventh attempt were both written without knowing their reach and both failed on reach. THE SIGNATURE THAT IDENTIFIED THE FAULT: the two targets failed in OPPOSITE directions -- DAY2/p8 imported a WEEKLY goal onto a daily item, WK2/p15 a DAILY goal onto a weekly one. No bias toward either schedule could produce both; only reference-resolution can. That is what told us the fault was the SPAN and not the period. AND IT IS WHY A PICK HAD FAILED HERE BEFORE: `trigger_settles`, built for this gate and reverted 2026-09-05, answered `week_end` on DAY2/p8 -- 'a trigger that states no period' -- the very reading it existed to stop. It asked WHAT PERIOD settles the trigger without first fixing WHICH SPAN the trigger is. THREE READINGS OF THIS ENTRY WERE REFUTED ALONG THE WAY and are corrected in it rather than deleted: that the cadence gate was the whole problem on this family (it was implicated in three cells, two of which were rule-following failures the rule already covered); that DAY1/p9 and DAY2/p9 were a gold inconsistency (they are not the same shape -- DAY1/p9 is weekly in BOTH trigger and reward, DAY2/p9's 'out of the 5 days' is genuinely ambiguous, and gold charged the unambiguous one and passed the ambiguous one, which is consistent); and that the grader was reading cadence off the goal STATEMENT (measured, it explains one cell of three -- the mechanism is the bare REFERENCE, not quoting the goal text). CLOSED BECAUSE THE GATE IS DONE ON THIS FAMILY, checked rather than asserted: `cadence_is_weekly` and `cadence_is_daily*` are implicated in NONE of the cells still imperfect on the four items. WK1/p7 fails `targets_own_behavior` (subgoal Q26's), WK2/p11 fails `aimed_correctly` (Q40's, a WK2-only gate) and `matches_chosen_type`, and WK2/p15's residue is `matches_chosen_type` (E55's). RESIDUAL STATED: WK2 is 17/18 both sides and WK2/p11 is wrong_by_median at 4/11, owned by Q40. The cells this entry named that are merely unstable were re-homed to subgoal Q50 on closing, so nothing is orphaned."
    ),
    "Q45": (
        "closed 2026-09-06 on the user's instruction, with its one wrong cell DECLARED rather than fixed and the declaration earned by closing every alternative first. PR/p15 IS THE WHOLE STORY. gold 4.00 in silence; we score 2.00 in 8 runs of 12, 4.00 in 3, 0.00 in 1. The charge is `targets_goal_behavior` = `absent`: the plan rewards with the very screen time the student set out to cut, and its condition names homework rather than the goal. Filed in the new measured.SILENT_GOLD_DIVERGENCES, which had to be created -- GOLD_CODE_KNOWN's check SKIPS any cell where gold charged nothing, so a declaration there would have suppressed nothing and sat unread, and CORRECTED_GOLD is for cells we are correcting. THE ENGINE IS RIGHT AND ARTICULATE, WHICH THE FIRST READING MISSED. Five of the nine refusing runs state the connection in plain words -- 'that reward gives you screen time, so it does not target your stated goal of cutting screen time'. That reasoning is in `feedback`; the `evidence` field holds only a short quote, and reading the quote alone produced the false claim that the rule cannot connect binge-watching to screen time. READ THE FEEDBACK BEFORE CONCLUDING A RULE IS BLIND. And the THREE runs that agree with gold are the ERRONEOUS ones: one infers the plan 'supports your goal to cut screen time', two are diverted into the pronoun wording and never reach the targeting question. Agreement with gold here is reached for bad reasons in every instance. WHY DECLARED AND NOT CORRECTED: gold charges 2.00 NOWHERE on PR, so the report reads PATTERN not OUTLIER and the test that licensed the 1c/p11 correction cannot run. PR's four codes -- NOT_OC, WRONG_TYPE, NOT_EXTERNAL_STIMULUS, BLANK -- contain no charge for targeting the wrong behaviour, so gold could not have expressed this even had the rater seen it. FOUR ROUTES WERE TRIED AND CLOSED, EACH MEASURED: the scoped clause (target 5/12 -> 5/12, and its removal cost 2 runs, so too WEAK rather than inert -- an earlier note calling it inert is corrected in the entry); unscoring the slot (refused by NR/p11, where the outlier test showed gold's 2.00 is right and OUR charge is the accurate route to it); correcting gold (refused by uniqueness); and the fixture (faithful -- participant 15 writes in the second person across all four operant items, so it is a style, not a defect). THE COHERENCE NOTE IS A FINDING, NOT A HYPOTHESIS, and it is the most useful thing here. The response mixes agents inside one contingency -- 'allow MYSELF' arranges the reward, 'YOU finish homework' performs the behaviour -- so it reinforces someone else's homework and does not close as an operant example. It is the ONLY mixed-agent answer in 160 operant cells. Neither side has a criterion for it: gold has no code, and our gates each pass on their own clause because nothing compares the agents across them. IT IS ALREADY COSTING ACCURACY -- the engine flags it in five runs' feedback and in two of those the wording question crowds out the targeting judgement, producing the 4.00. If coherence gated identifying operant conditioning at all, this cell would plausibly score 0.00, which means OUR 2.00 is probably not right either and the reader missed the same thing. Unresolvable here: it needs SCORED EXAMPLES of incoherent responses and the corpus has exactly one, so a criterion built on it would have no negatives to validate against. Revisit when there are more. CLOSED WITH THE RESIDUAL STATED PLAINLY: PR/p15 IS NOT FIXED and ended the day WORSE than it began -- 5/12 to 3/12, because the clause that was holding its split was removed. The item is 17/18 both sides. The TEN unstable cells this entry was titled for are unchanged, and that is the entry's own instruction ('DO NOT SWEEP FOR THE OTHER TEN'), not neglect: they are counted right and re-running them buys an estimate of a rate rather than a fix. Two cells were ADOPTED during the work -- PP/p12 (the `targets_unwanted_behavior` twin of this entry's own slot) and PP/p17 (a whole-run wobble, four gates failing at once, explicitly not to be chased with a rule). Verified before closing: no cell is orphaned."
    ),
    "E54": (
        'closed 2026-09-06 on the user\'s instruction, the day it was filed, with the coverage PROVED rather than asserted and the detector\'s noise measured away. DELIVERED, in four parts. (1) THE CORPUS. `leakage.authored` now derives from the SHIPPED PROMPT via build_web_prompt -- E50\'s move, safe here because the rendered prompt carries responses as REF placeholders and embeds no student text, verified over both handouts before the code was written. Cut into PASSAGES, one per numbered criterion, heading, lettered sub-clause or blank-line stretch: DAY2 went from ONE block of 13,193 chars to 37 passages, median 244, so a finding points at a criterion and a verdict survives an edit elsewhere. (2) THE PROOF. `coverage_gaps()` reports any prompt line of six or more words that nothing scans. It reports 0; with the passage corpus removed it reports 1,471, so the arm can go positive. It found one real hole on the way -- a Q1 bullet dropped for falling under the passage minimum -- and short passages now merge upward rather than being discarded. (3) THE DETECTOR GAP, which was NOT in the original filing and is the more useful half. leakage.py compares CONTENT bigrams, and the leak that founded the module yields exactly ONE after stopword filtering: prompt "...{{corpus:DAY1/p8:day1:117:137:sha=aa91092efc87}} it" against p8\'s "...{{corpus:DAY1/p8:day1:117:137:sha=aa91092efc87}} it" reduces to [\'pushups miss\'] against MIN_EXCLUSIVE=2. The tool could never have flagged it at any granularity or scope, and did not -- it was found by hand. `verbatim_findings` closes that: the longest word-run appearing verbatim in an authored block and in exactly ONE student\'s answers, raw, six words. It REFUSES OUTRIGHT with no review ledger, because such a span is not vocabulary and not coincidence; measured over 26 items on a clean tree it finds nothing. (4) THE TRIGGER-HAPPINESS, raised by the user and confirmed by the output: findings that were \'nothing but high frequency, utterly ordinary words\'. Four measured changes -- the word and bigram reports read only WORKED-EXAMPLE spans (all four leaks this project ever found were quoted illustrations; 83% of prose is outside them and none of the leaks is out there); the assignment\'s own 1,222-word vocabulary is excluded (56 of 90 flagged words); MAX_STUDENTS_FOR_INFORMATIVE 6 -> 4 (24 findings -> 1; the 23 were words a QUARTER of the cohort used, and 4 is the floor the known cases set -- procrastinating 2 students, snack and music 4 each); and a shared bigram now needs one informative word, which killed \'fixed schedule\', \'many times\', \'look like\', \'keep doing\'. 57 unread findings -> 0, and the passage findings were then PROMOTED TO GATING, once there was nothing to promote over. FIRE-TESTED AFTER THE TIGHTENING, both arms, because a quiet detector and a working one look identical: DAY1/p8\'s sentence planted -> verbatim fires 8 times naming the passage, the student and the span; three rare cohort words planted in an example span -> the word report goes 1 -> 9 naming criterion 7 on every item carrying it. TWO LEAKS REMOVED AND PRICED. Criterion 8 quoted WK2/p15\'s definition field verbatim; criterion 7 quoted DAY1/p8 almost word for word -- the leak this module\'s own docstring cites as its founding case and treats as FIXED. It was fixed in the prose the tool scanned and survived in the prose it did not, so the repair and the blind spot were the same event. Re-measured across all eight operant items: DAY1/p8 12/12 -> 9/12 (the circularity test, pre-registered and failed), DAY2/p7 11/12 -> 8/12 (subgoal Q46\'s fix, whose closure note is corrected in place). PP and NP priced the removal ALONE at zero, because they carry a different slot from the one Q45 reverted. About three cells is the price of an honest prompt, and it is not a regression: what changed is what we can claim. SELF-INFLICTED FAULTS KEPT ON THE RECORD, all three: an order-dependent first cut where each item\'s remainder counted as covered for the next; a sentence-splitter that cut \'7. `avoidance_frame`\' at the period after the 7, so no numbered criterion survived intact; and a block rename that silently killed the filter keeping passages out of the gate\'s exit code, so the gate began refusing every sweep on 57 unread passages -- caught by running the gate on the queued items rather than trusting the edit. A filter that matches on a label is hostage to the label. AND ONE FALSE CLAIM CORRECTED IN THE SOURCE: the comment justifying the single-word filter said "\'phone\' is in three students\' answers"; phone is in fifteen. CLOSED WITH THE RESIDUAL STATED: the word report requires TWO rare words, so no single-word leak can trip it -- the founding `procrastinating` case included. That limit is documented, not fixed. Verified before closing: this entry owns no cell; WK2/p15 is Q22\'s, PR/p15 is Q45\'s, and the cells its re-sweeps left ownerless went to Q45.'
    ),
    "Q51": (
        "closed 2026-09-06 on the user's instruction, on its own measured result and against a pre-registration written before a call was spent. Q4a/p3 went 0/12 to 7/12 -- always_wrong to right-by-median -- and the mechanism is exactly the one this entry named: `antecedent_kind_1` answers `unlinked` in 7 runs of 12, and THOSE ARE PRECISELY THE 7 RIGHT RUNS. Item python 17 to 18, olx 17 to 17, NET +1, sweep_readout KEEP. WHY THE CLAUSE REACHED ITS CELL WHERE OTHERS TODAY DID NOT, because the contrast is the transferable part: the entry's FIRST move was to count `unlinked` across the corpus and find it already chosen 12 times on four cells, so the option was known to be live and the only question was whether p3 fell inside it. Subgoal Q45's clause and Q47's eleventh attempt both failed the opposite way -- a distinction that was TRUE about the text and that the grader never applied -- and neither had established that the slot already acted on cells of that kind. Establish reach before shape. THE COST IS NAMED AND NOT HIDDEN: p6 fell 11/12 to 8/11, a drop of 3 on BOTH sides, past the measured noise floor. This entry pre-registered p6 as UNCHANGED, reasoning that `unlinked` already fires there for the other reason -- and it does, 6 of 11 -- so the clause did reach a cell it was told not to. p9 gained 8/12 to 10/12 and p19 held at 8/12, so the movement is not one-directional noise. KEPT on the rule this project uses: the NET across both sides carries the verdict, and one control moving is not evidence of harm on its own. CLOSED WITH THE RESIDUAL STATED AND OWNED: p3 is 7/12, which is `unstable_counted_right`, not fixed -- five runs of twelve still answer `before` and score wrong, and a cell right by median can un-resolve. p6 at 8/11 is this edit's collateral and belongs to whoever picks up Q4a next. p14 held at 0/12 exactly as predicted and is subgoal Q19's, a different fault on the same item. Verified before closing: no cell is orphaned."
    ),
    "E53": (
        "closed 2026-09-06 on the user's instruction, the day it was filed, with every finding dispositioned and NO LIVE SCORING DEFECT FOUND -- which is the honest headline. DELIVERED: enforcement.check_scored_slots_are_answered_by_both_engines, reported as SCORED SLOT ANSWERED BY ONE ENGINE ONLY, running in the equivalence audit and as measured.py preflight STEP 5g. NOT in sweep_gate.py: it reads artifacts, so it cannot run before a sweep exists. 5g is 5f's question one level up -- 5f asks whether a mapped slot was recorded outside its map, 5g whether a scored slot was recorded by both engines at all. THE COUNT MOVED FIVE TIMES AND EVERY MOVE WAS A CORRECTION OF MY OWN READING, which is the transferable part: 37 first, measured with slot_verdict -- which REFUSES A PICK BY DESIGN, so observed_type and stimulus_move were phantom gaps; 26 scored, read with slot_answer; -5 once the sheet's `expect` derivations were excluded; -11 once `equals` and `derived` were read too, because matches_chosen_type on six items was the same class and reading only `expect` had left it looking like a scoring gap; -4 for 1b's week_*/baseline aliased to the app's *_data names; -12 for the declared decomposition divergences. Final: 14 documented recording gaps, 0 undeclared. THE FIX THIS SUBGOAL NEARLY BOUGHT WAS WRONG, and catching it is worth more than the check. The plan was to add a MAPS entry connecting observed_type to the scored demonstrates_type on PR/NR/PP/NP, on the reasoning that the app makes the judgement and cannot charge for it. FALSE: the sheet already derives it -- the four items carry an `expect` rule naming observed_type (or stimulus_move on PR) -- and the app honours it. The proof is arithmetic, on NR/p4: olx runs answering targets_goal_behavior=met with demonstrates_type=null still score 2.0, where an uncharged type criterion would give 4.0. The map would have DOUBLE-CHARGED a working criterion. A missing VALUE is not a missing MECHANISM, and the cheap test is whether the score moves when the criterion should bite. DELIVERED BEYOND THE CHECK: enforcement.DECOMPOSITION_DIVERGENCES, 12 entries where the mirror ENUMERATES (sentence_1/2/3, example_1/2, reason_1/2/3) and the app COUNTS (sentences_given, changes_given, the reasons scaffold in aggregate), each carrying its per-cell measurement rather than an assertion -- 2b 20/20 both sides with identical medians on all twenty cells, Q2 identical on every cell, NR identical on all twenty, and item 3's one differing cell is one the APP gets right and the mirror does not. Four ALIAS entries for 1b, measured before declaring. A RATCHET on the UNDECLARED count only (ONE_SIDED_SCORED_SLOTS_BUDGET = 0); recording gaps are reported but not counted, because they are documented facts about the artifacts and are meant to stay visible. FIRE-TESTED ON FOUR BRANCHES, after E50's warning that an arm which cannot go positive proves nothing: declaring a slot app-only drops it and restores; aliasing to a SCORED slot the app answers excuses it and restores; two consecutive calls are stable; dropping one decomposition declaration makes the ratchet fire at 1 and restoring silences it. ONE SELF-INFLICTED BREAKAGE, kept on the record: the first attempt to write THIS note put an unescaped quoted attribute inside a double-quoted string and left goals.py unparseable on disk, because the file was written before the ast.parse that was supposed to guard it. Verify THEN write, not the reverse -- the same ordering error set_slot_field was built to stop. CLOSED WITH THE RESIDUAL OWNED, NOT WAVED: the 12 decomposition divergences are a standing debt and subgoal E55 is filed to retire them in favour of structural parallelism -- they blind a per-slot readout on one side, which is how every diagnosis this project makes actually works, and they leave check_slot_sets_match_gold dark on five items for one engine. Verified before closing: this entry owns no cell -- WK2/p15 is Q22's, PR/p15 is Q45's."
    ),
    "Q46": (
        "closed 2026-09-06 on the user's instruction, on its own measured result and against a pre-registration written before a call was spent. DAY2/p7 went 0 of 12 to 11 of 12 -- an always_wrong cell to near-perfect -- with `targets_own_behavior` answering `absent` in 12 of 12 runs, which is the mechanism the entry named. Item totals python 16 -> 17 and olx 16 -> 17, NET +2 across both sides, and sweep_readout returned KEEP. THE ENTRY'S OWN RECOMMENDATION WAS WITHDRAWN BEFORE IT WAS FIXED, and that is the transferable part: it first read gold as objecting to the REWARD ('the reward IS the unwanted behaviour') and drafted a DECLARED DIVERGENCE on that basis. WK1/p1 refuted the clause. Re-reading both of gold's comments showed they are about the TRIGGER, not the reward -- DAY2/p7 'make sure the BEHAVIOR YOU ARE TARGETING is...' and WK1/p7 'your UTB is not procrastination' -- so WK1/p1 had never been a counter-example to the question gold actually asks. A divergence declared on the first reading would have recorded a disagreement we had not tried to fix. THE SLOT ALREADY WORKED ON THE SIBLING: WK1/p7 gold 3.00, the slot REFUSES, 9 of 12. It failed only on DAY2, and the blind spot was structural rather than verbal -- the desc said 'UTB or WGB' with NO RULE, so a condition naming the GOAL was `met` by the desc alone. THE RULE IS DAY2-ONLY AND THAT SCOPING IS NOW MEASURED, NOT ARGUED: the four cadence items share one `_example_use_item` builder, and an earlier shared-rule version had been measured and lost -- DAY1 18/18 -> 17/18 on both sides, with p15 collapsing from perfect although the gate answers `met` on it in every baseline run. A reword's blast radius is the whole item, not the cells it gates. After this sweep DAY1 18/18, WK1 18/18 and WK2 17/18 are all six side-recordings CURRENT against their own shas, so the split did not leak. THE CONTROL THAT MATTERED HELD: p15 shares p7's UTB and its `targets_own_behavior` stayed `met` 12 of 12, so the rule separates a SUBSTITUTE goal from an INVERTING one rather than refusing the family. Three further cells gained -- p9 4->6, p12 10->12, p13 11->12 (band unstable_counted_right -> perfect). ONE CELL MOVED DOWN, p8 8 of 12 to 7 of 12, one side, drop 1: INSIDE the measured noise floor and reported rather than charged, per E51's rule. CLOSED WITH THE RESIDUAL STATED AND OWNED: DAY2 is 17/18 on both sides, not finished. p9 at 6/12 is subgoal Q22's (`cadence_is_daily_counted` absent in 8 of 12) and p8 at 7/12 is neither cell this rule was aimed at. Verified before closing: no cell is orphaned."
    ),
    "Q14": (
        "closed 2026-09-06 on the user's instruction, on its own measured result and by the mechanism the entry predicted. p10 went 1 of 12 to 9 of 12. The entry said 'the whole gap is one benefit too many', and one benefit is exactly what is now failed: p10 reads harms 0 / benefits 3 / FAILING 1 / given 2 in eight runs of twelve, so `benefits_failing` catches the restatement of the goal, subtracts one, and `reasons_given` lands on gold's 2. EVERY NAMED CONTROL HELD, and the slot answers 0 on ALL of them and 1 only on p10: p14 ('{{corpus:Q1/p14:response:194:227:sha=a94f59f0a73d}} check'), p16 ('{{corpus:Q1/p16:response:256:285:sha=30187edf82d0}} person') and p18 ('{{corpus:Q1/p18:response:284:312:sha=5f6b8bda29be}} healthy') are each 12/12 with failing 0 in all twelve runs, as are p3, p11 and p19. A RULE THAT FIRES ON ITS TARGET AND NOWHERE ELSE is the opposite of the Q6 pattern, and the difference is the kind of question asked: this tests what an entry IS -- a restatement of the goal, against the goal text already on the screen -- rather than judging whether a benefit is a good one. CLOSED WITH THE RESIDUAL STATED: p10 is `unstable_counted_right`, not fixed. Three runs of twelve remain wrong -- two where `benefits_listed` itself reads 2 so failing 1 over-subtracts to 1, and one where `benefits_failing` does not fire. A cell right by median can un-resolve, and this one is not solved. TWO CLAIMS IN THE ENTRY WERE FALSE AT CLOSING and are left in place as the record of what was true when written -- 'NOT YET SWEPT' (it had been) and 'p10 is right 1 of 12' (9 of 12) -- with the correction written above them. Verified before closing: nothing is orphaned, subgoal Q16 also owns Q1/p9, p10 and p18, and Q16's separate `utb_stated` question on p17 is untouched by this."
    ),
    "E47": (
        "closed 2026-09-06 on the user's instruction. DELIVERED: measured.slot_answer / slot_verdict, which know that an EMPTY STRING IS ABSENCE -- the rule both hand-rolled forms got wrong. `r.get(\"checks\") or r.get(\"verdicts\")` never consults verdicts and returns '' for a pick; the reversed form fails the same way. One of them reported Q2's `wgb_names` as never answered on python when it answered `doing` 97 times, and that was told to the user as fact. slot_answer also reads the PAPER shape (`credit_checks`), which it did not at first -- it would have returned None for every paper cell, silently, with subgoal E28 waiting. THE CONVERSION LIST WAS AUDITED AND WAS MOSTLY WRONG, which is the more useful half: over 4,620 results in 60 artifacts NO result carries both `checks` and `verdicts`, so the dict-SELECT form is correct by construction and measured.py and enforcement.py never needed changing; cross_path.py is BETTER than the accessor, branching on the writer and handling score.py's `credit_checks`, and converting it would have destroyed the paper path. The real fault was the per-KEY lookup, and it lived in the sweep scripts. `sweep_readout.py --slots ITEM slots [cells]` is the repo replacement, verified on Q4a reading pick AND verdict correctly. The scratchpad scripts are NOT patched: an automated pass on 2026-09-06 broke ten of them by inserting a comment mid-expression and was reverted; they are archives of sweeps already run, and the durable fix is that the readers live in the repo."
    ),
    "E49": (
        "closed 2026-09-06 on the user's instruction. DELIVERED: enforcement.check_sheet_slots_reach_the_rubric, reported as SHEET SLOT REACHES NO RUBRIC ELEMENT, wired into the equivalence audit, into scoring/sweep_gate.py, AND into agreement.cheap_checks_gate so it runs at the top of every sweep. THE EXCLUSIONS ARE THE WORK: 119 naive orphans reduce to ONE. `confident` on all 22 items, the eight criteria-derived items (subgoal E35's class, where the rubric holds composites and the sheet enumerates sub-checks), and aliased names through web_name. A check whose false positives outnumber its true ones by 118 is switched off within a day and takes the real finding with it -- the same trap as E48's first cut (12 findings, 10 false) and E52's (39 mismatches, ~37 by design). FIRE-TESTED on three arms: clean 1, Q3's rubric blinded 6, restored 1. THE ONE FINDING IS DISPOSITIONED, NOT SUPPRESSED: Q1/matches_selected is UNSCORED and drives FEEDBACK -- the sheet spells it with no @pts and olx_prompts instructs the grader that `differs` shapes the first sentence of feedback. The python mirror produces no feedback, so there is nothing for it to define, and wiring it into the rubric would add a slot that can never change a number. Declared in the new APP_ONLY_SLOTS, which requires the two facts that make such a claim checkable: no points, and something in the generator consumes it. IT BLOCKED A SWEEP UNTIL DECIDED -- sweep_gate.py Q1 refused with the finding live and passes with the declaration filed, which is the behaviour wanted. The verdict-list direction this entry also claimed was delivered by subgoal E52 instead and is not duplicated."
    ),
    "E51": (
        "closed 2026-09-06 on the user's instruction. DELIVERED: scoring/sweep_readout.py, whose verdict rides the ITEM TOTALS on both sides rather than cell movement. THE OLD RULE -- 'any currently-perfect cell that moved is grounds to revert' -- fired on SIX OF SEVEN sweeps in one day and was refuted by accident: Q2 was swept twice at the SAME prompt_sha, because the edit under test never reached the prompt, and three of twenty cells moved anyway, one from 6/6 to 2/6. It nearly reverted subgoal Q43's edit, which had fixed its target outright, and DAY2's narrowing, which gained a cell on both sides. THE FIRST REPLACEMENT WAS ALSO WRONG and the entry keeps it: a cell rule of '3+ pooled drop on both sides' was tested against the unchanged-prompt case and STILL fired, on Q2/p16 at 12/12 -> 7/12. The cell-level noise floor reaches at least five pooled runs, so no cell threshold low enough to catch a real regression can exclude it. VALIDATED on one case of each kind: unchanged prompt KEEP, Q5's genuine loss REVERT, DAY2's gain KEEP. AND IT RUNS WHERE NO AUTHOR CAN FORGET IT: converting the 21 scratchpad scripts was tried and abandoned -- the pass matched almost nothing and its one effective edit commented out `or r.get(\"verdicts\") or {}` in ten of them, reverted and re-verified with bash -n. The right hook already existed: agreement.cheap_checks_gate runs at the top of every sweep, and the four new structural checks are now in its suite (7 -> 11). Fire-tested: dangling rubric slot -> gate returns 1 and the sweep stops; restored, 0. CORRECTION 2026-09-06, HOURS AFTER CLOSING: the rule as delivered required BOTH sides to fall, and that was too lenient. Subgoal Q47's eighth attempt on Q6 came back with python HELD at 16 while olx went 18 -> 16 and BOTH pre-registered targets missed, and this printed KEEP -- because one side being flat is not 'both fell'. A side holding still does not pay for the other side losing two cells. The test is now the NET across both sides, which is the quantity an edit is supposed to move, and it was re-validated on all four known cases: Q47's eighth attempt net -2 REVERT, Q5 net +2 KEEP (reading its revert as the gain it was), Q2 unchanged-prompt net +1 KEEP, DAY2 net +2 KEEP. THE LESSON IS THAT A THRESHOLD BUILT FROM ONE FAILURE MODE MISSES THE NEXT: the both-sides rule was designed against noise, and the case that broke it was a real loss on one side. A CAVEAT KEPT IN THE ENTRY: item totals are stabler than cells, not stable. Two 6-run halves is a small sample and an edit that trades one cell for another reads as no change. This answers 'did it hurt', not 'did it help' -- for that, read the TARGET cell against its pre-registration."
    ),
    "E52": (
        "closed 2026-09-06 on the user's instruction, delivered the same day it was filed, and narrower than it was filed for. THE FAULT WAS IN THE CHECKS, NOT THE TREE: both mapped-slot checks read the RUBRIC's verdict list, while the grader answers the SHEET. `unclear` was removed from Q2's rubric, the audit went clean, the sheet still declared `wgb_inverts_utb:...:unclear@2`, and the grader kept answering it -- five divergences at an IDENTICAL prompt_sha, with E46's closure note claiming the cell was fixed. DELIVERED: the authoring check resolves offered verdicts from the sheet via E27's `_olx_slot_verdicts`; the artifact check treats a DECLARED COUNTERPART as agreement via `_same_verdict`. A duplicate sheet reader was written here and deleted -- two functions answering 'what does the sheet offer' is how the rubric and sheet came to disagree in the first place. MOST OF WHAT THIS ENTRY ASKED FOR ALREADY EXISTED. It called for a general rubric-vs-sheet vocabulary check; subgoal E27 built one -- VERDICT_SPACE_DIVERGENCES, 12 declared pairs including 'the web's `incomplete` is the paper's `not_described`' in as many words -- and check_verdict_spaces_are_declared reports clean. Read the audit before adding to it. Q4a WAS NOT BROKEN AND IS THE SHARPEST LESSON HERE: the corrected check immediately reported its antecedent_1/antecedent_2 as offering an unreachable verdict. They do not. The mirror records `not_antecedent` 44 times and the app `wrong_kind` 39 over the same runs -- the same judgement under two names -- and the table declares the pair verbatim. ACTING ON THAT FINDING WOULD HAVE EDITED A WORKING ITEM; the check was fixed instead. THE FALSE-POSITIVE CLASS IS NOW MEASURED, three times over: a naive rubric-vs-sheet comparison reports 39 mismatches of which ~37 are E27's design; E48's first cut reported 12 with 10 false; E49's reverse direction 119 with 1 real. Build the exclusions first, the check second. MEASURED EFFECT: artifact findings 17 -> 10, all seven counterpart shapes removed; what survives is Q2's `unclear` (never a declared counterpart, and impossible after the sheet fix) and Q4b's single `wrong_kind`-on-`met` slip in twoside_web, where the grader answered a mapped slot directly. FIRE-TESTED: an undeclared verdict planted in the sheet reader gives exactly 1 finding; restored, 0. CLOSED WITH A DECLARED LIMITATION, not a pretence of completeness: the artifact check can only compare a run in which the PICK was recorded, so it is blind to artifacts predating a pick's introduction. It cannot compare what was never written down, and inferring the pick would invent the evidence. Verified before closing: E52 owns no cell as its only owner -- it is machinery -- so nothing is orphaned."
    ),
    "E43": (
        "closed 2026-09-06 on the user's instruction, after the deferred self-test finally ran and passed: 66 detected, 0 failed, 0 skipped, 66 of 66 expected, with restored state clean at 73 findings against a 73 baseline. THE EXPECTED COUNT WAS RE-DERIVED AND NEEDED NO CHANGE. Four checks were added after SELFTEST_EXPECTED was set to 66 -- the two mapped-slot checks (E46), the rubric-slot check (E48) and the case-name check (E50) -- and the number did not move, because three of the four are preflight- or audit-shaped and carry no `_scorer_case`, which is family-consistent: the whole preflight-diagnostic family has none, since `_scorer_case` installs breakage in the SCORER while those read the ledger. BOTH HALVES OF THE DELIVERABLE ARE GREEN. The check is enforcement.check_count_scaffolds_are_arithmetic, reported as COUNT SCAFFOLD IS NOT ARITHMETIC; the INVERTED arm this entry argued for is present and passing -- 'the count-scaffold check goes blind -> went silent, as it must'. That arm was the entry's own open question: its four findings are STANDING, because the violating artifacts are on disk, so an ordinary case would pass with the breakage installed OR removed and prove nothing. Asserting a finding that is true either way is not a test. THE FOUR VIOLATIONS REMAIN TRUE AND ARE NOT A REASON TO KEEP THIS OPEN: q17b_olx run2 p11 (0-0!=3), cli_v7 run2 p6 and q17_python run1 p6 (2-1!=2, the same cell on both engines), twoside_cli run6 p10 (3-0!=0, the shape running OPPOSITE to the one this entry first described). They are historical facts about recorded artifacts; the check exists so the next one is seen when it happens. THE SELF-TEST HAD BEEN DARK, which is worth recording: the first attempt to run it raised KeyError on 'codes', because `startswith(\"antecedent_\")` also matches subgoal Q33's `antecedent_kind_*` PICKS, which carry no codes since they charge nothing. So the suite had not run since Q33 landed, and this is the first honest reading in that window. The filter now requires `codes` and says why. Verified before closing: no cell is orphaned -- Q2/p11 is also Q17's and Q41's, and the other cells this entry names belong to Q14, Q17, Q41, Q43 and Q44."
    ),
    "E48": (
        "closed 2026-09-06 on the user's instruction. DELIVERED: enforcement.check_rubric_slots_reach_the_sheet, reported as RUBRIC SLOT NEVER REACHES THE SHEET, and it is STANDARD rather than merely present -- it runs in the equivalence audit AND in scoring/sweep_gate.py, where it refuses before a call rather than reporting after one. That placement is the point: the fault it catches cost ~240 calls on 2026-09-05, when subgoal Q18 added `b2_names_besides` to Q4b's rubric, rewrote `b2_basis` to say 'FIRST READ b2_names_besides', and the slot never reached `slots=`. The sweep ran against a prompt with a dangling reference and its targets moved incoherently -- p12 2/12 -> 6/12 while p6, p8, p14 and p20 all broke -- because the rule asked for an answer that did not exist. enforcement exited 0 throughout. THE TRANSFERABLE LESSON IS ABOUT THE GUARD, NOT THE SLOT: that sweep DID have a guard, and it asserted olx.count('b2_names_besides') > 0, which PASSED -- on the two prose mentions the generator had just written. Presence in the FILE is not presence in the SLOT LIST, and a guard that cannot tell them apart certifies the fault it exists to stop. sweep_gate.py exists because of that line. TWO EXCLUSIONS, both found by the first cut reporting TWELVE findings of which TEN were false: aliased slots resolve through web_name, and a slot with no `verdicts` is COMPUTED not answered (`is_operant_conditioning`, `is_nr` and kin carry pts and no verdict list, so their absence from `slots=` is the design). A check whose false positives outnumber its true ones gets suppressed and takes the real finding with it. FIRE-TESTED on three arms: clean 0; the slot removed from `slots=` again 1 finding naming Q4b/b2_names_besides; restored 0. THE COLLATERAL IS FLAGGED, NOT KEPT: Q4b's 17/19 is STALE on both sides against the corrected sheet and must be discarded rather than interpreted; Q4b is re-sweeping. The deliverable was the check, not that number. Verified before closing: no cell is orphaned -- the Q4b cells belong to Q18 and Q50."
    ),
    "E50": (
        "closed 2026-09-06 on the user's instruction, filed and delivered the same day. DELIVERED: enforcement.check_no_case_names_in_prompts, reported as PROMPT NAMES A COHORT CASE, running in the equivalence audit AND in scoring/sweep_gate.py. It reads the RENDERED prompt via build_web_prompt rather than the sources, so it catches every route in -- SLOT_NOTES, a rubric rule or desc, a criteria note, or a hand-authored sheet line -- where checking sources would leave whichever route nobody thought of. IT WAS INSTALLED WHILE THE INVARIANT ALREADY HELD, which is the argument for it: measured before filing, 0 of 26 SLOT_NOTES blocks and 0 rubric rule/desc fields carried a `pN`. An invariant installed while it holds costs nothing and is never argued about afterwards; installed after it breaks, it costs a sweep. The zero had been holding by discipline alone, and the same discipline let rules quote corpus vocabulary until leakage.py was built. IT IS NOT LEAKAGE: leakage.py asks whether a rule echoes the cohort's WORDS, this asks whether it names a cohort MEMBER, and a rule can be free of borrowed vocabulary and still say 'unlike p10'. A FALSE PASS WAS CAUGHT IN TESTING AND IS THE ENTRY'S MOST USEFUL LINE: the first fire test planted the case name in a SLOT_NOTES key that DOES NOT EXIST (`measurable` is a rubric slot, not a notes key), nothing read it, and the arm reported 0 -- indistinguishable from a working check on a clean tree. A negative arm that cannot go positive proves nothing. Re-tested against a live key it produced the finding and named the item; restored, 0."
    ),
    "E46": (
        "closed 2026-09-06 on the user's instruction, with all three of its own questions answered and the preferred answer REFUTED. (a) NOT historical: `maps` landed in lo-blocks 2026-08-28 and twoside_web ran 2026-08-29, one day later, so subgoal E14's fix does not explain it and the only slotSheet.ts change since is an unrelated `contains` primitive. (b) It does not recur, and not because anything was repaired -- zero divergences in the current artifacts with no engine change to account for it. (c) THE APP DID NOT FAIL A MAP LOOKUP: on Q4b/p17 the pick was `activity` in all six runs and the verdicts followed the map in five; in run 1 the grader answered the mapped slot DIRECTLY with `wrong_kind`. Both 'observations' are ONE grader answer in ONE run on ONE cell. THE TRANSFERABLE FINDING: an unreachable verdict does not CREATE this fault, it AMPLIFIES it. Q2's `wgb_inverts_utb` offered `unclear`, which its map could not emit, giving the grader an extra option to reach for -- five divergences in 120 across four cells. Q4b offers no unreachable verdict and ran at one in six on one cell. So the authoring check is prevention and the artifact check is detection, and neither substitutes for the other. CLOSED ON AN INSTRUMENT, NOT AN EDIT, because a grader can always answer a mapped slot directly with an in-range value and no authoring rule can stop that: MAPPED SLOT HAS AN UNREACHABLE VERDICT now runs in the equivalence audit AND in scoring/sweep_gate.py where it refuses before a call; RECORDED VERDICT DISAGREES WITH ITS MAP runs in the audit AND as measured.py preflight step 5f, which is where it belongs -- the Q4b divergence sat unread from 2026-08-29 to 2026-09-06 because nothing routine looked at artifacts after a recording. MAPS[\"Q4b\"] was NOT touched, as the entry warned; Q2 was fixed by dropping `unclear` FROM THE RUBRIC and is being re-swept. CORRECTION 2026-09-06, THE SAME DAY, AND THE SWEEP IS WHAT PROVED IT WRONG: that claim was FALSE. Dropping `unclear` from rubric_h1's `verdicts` changed nothing the grader sees. The option is declared in the SHEET, hand-authored in slots= as `wgb_inverts_utb:...:unclear@2`, and a rubric edit does not touch it. The re-sweep came back at prompt_sha c73a7e96196c -- IDENTICAL to the run before it, so the prompt never changed -- and still carried five `unclear`/`absent` divergences. The sheet has since been corrected and the sha moved to c19aea3e5abb, which is the first evidence any fix reached the grader. THE MISSING INVARIANT IS E48's IN THE OTHER DIRECTION: E48 asserts every rubric SLOT reaches the sheet; NOTHING asserts that a slot's VERDICT LIST agrees between rubric and sheet. A verdict can live in the sheet and not the rubric, and the sheet is what the grader is offered. That belongs with subgoal E49, which already owns the reverse direction at the slot level. ONE SELF-CORRECTION KEPT IN THE ENTRY: this check first asserted the score was unaffected, from a reading of lo-blocks' satisfiedMap, and that was reported to the user as settled before it was true. Per-run alignment refuted it -- every divergent run is a wrong run unless the recorded verdict is score-equivalent to the mapped one, with Q2/p10 as the control. Verified before closing: no cell is orphaned -- Q4b/p17 belongs to Q50, the Q2 cells to Q43, Q17 and Q44."
    ),
    "Q10": (
        "closed 2026-09-05 on the user's instruction, on its own measured result and against the pre-registration it wrote before spending a call. Q3/p10 went 4 of 12 to 12 of 12, the `measurable` gate now answering `absent` 9 and `unclear` 3 where it used to credit, and the item went python 18/20 -> 19/20 and olx 19/20 -> 20/20, a PERFECT olx item. ALL TWELVE NAMED CONTROLS HELD, which was the thing in doubt: the entry's risk was that the rule would read the QUANTITY rather than the HOLDER and reach the ten credited cells that name what the record goes into. It did not reach one of them. Three further cells gained -- p17 11->12, p19 10->11, p20 11->12. THE ENTRY'S OWN SUCCESS SIGNAL IS DISCHARGED: it said measured.GOLD_SLOT_DISAGREEMENTS_KNOWN[('Q3', 10)] should go stale if the rule worked, and to drop it and lower the budget THEN and not before -- done, 14 -> 13. WHY IT WORKED WHERE Q6's DID NOT, recorded because the contrast is the transferable part: this asks a READING question with the target cell already in view -- p10's box says a count will be kept and names nothing that holds it -- where subgoal Q47's structurally identical move on Q6 never fired on its target at all. Structure beats wording when the grounds are confusable AND the slot can see the cell. RESIDUAL, STATED AND OWNED: Q3/p13 lost ground 6 of 12 to 5 of 12 with `measurable` answering `absent` 12 of 12. It is not one of this entry's controls and it is not orphaned -- subgoal Q30 names it and is open. Verified before closing rather than assumed: measured.wrong_cells_without_an_owner() was reporting Q3/p10 as named by an open subgoal while scoring right on every side, which is the audit asking for this closure in as many words."
    ),
    "E44": "closed 2026-09-05 on the user's instruction, filed and finished the "
           "same day with both halves done. THE AUDIT HALF: "
           "check_generated_attributes_have_a_declaration reports an .olx "
           "attribute the generator owns with no rubric rule behind it, unless it "
           "is declared in HAND_AUTHORED_ATTRS -- four entries, the "
           "`demonstrates_type` rules on PR/NR/PP/NP, each with the reason the "
           "rubric must not claim them. THE WRITER HALF: render() empties such an "
           "attribute instead of leaving it, returns the cleared list so --check "
           "and --diff see it as a real difference, and --write reports it and "
           "says the items want re-sweeping. Fire-tested on three arms including "
           "the one that matters -- a hand-authored attribute SURVIVES, and drops "
           "only when its table entry does. "
           "CLOSED WITH A RESIDUAL STATED IN THE ENTRY: the writer half is "
           "fire-tested, NOT measured. The tree has no orphans, so every --write "
           "since has taken the untouched path. The first genuine end-to-end proof "
           "is the next revert that removes a declaration; if its CLEARED line "
           "says nothing where an attribute was left behind, this closed early.",
    "E42": "closed 2026-09-05 on the user's instruction, with its one deferred "
           "residual done first at the user's direction rather than refiled. "
           "DELIVERED: record() captures bands_before from cell_bands() before the "
           "ledger is loaded or written -- taken first because cell_bands reads the "
           "SAVED ledger, so after save() the prior band is gone and it {{corpus:Q4b/p13:modify:42:52:sha=b5a9f95d18e1:shape=R10-0-20}}"
           "{{corpus:Q4b/p13:modify:53:58:sha=5de94d691ae3}} about a measurement that cannot be recovered afterwards. "
           "band_moves() reads it back, measured.py --moves exposes it, and the "
           "residual is band_regressions() at preflight step 5d. Ten items carry "
           "bands on both sides, which is the condition the residual was waiting "
           "on. IT DERIVES AND DOES NOT RE-DERIVE, which the entry made a "
           "condition: no threshold is repeated at the record site. PROVED IN USE "
           "the day it closed -- it is what caught the cadence edit taking DAY1/p9 "
           "and DAY1/p15 out of `perfect` while the item total moved by one and "
           "read as noise.",
    "Q48": "closed 2026-09-05 on the user's instruction. Its question -- does "
           "gold's explanation charge on Q4c/p20 survive? -- is answered YES, and "
           "the cell is declared as GOLD_DIVERGENCES DISTAL_CONSEQUENCE_CHARGED_ONCE. "
           "The FIXABLE route was tested first and refuted, which is why a "
           "divergence rather than a rule: consequence_1 and consequence_2 carry no "
           "rule at all, so a directness test was available and gold uses the word "
           "twice -- but p7, p2 and p12 all state a consequence reached through an "
           "unstated intermediate step and gold passes every one in silence at 5.00. "
           "p7 is structurally identical to p20. A directness rule fixes one cell and "
           "breaks three. THE ENTRY'S OWN COMPARATORS WERE THE WRONG ONES and would "
           "have supported a GOLD CORRECTION: p19 leads with the mechanism where p20 "
           "gives only the outcome, and p3/p14/p17 sit on an exercise behaviour where "
           "the link needs no stating. Q4c/p9 remains, and it is subgoal Q19's.",
    "Q9": "closed 2026-09-05 on the user's instruction, on its own measured "
          "result. Q3/p19 went 0 of 12 to 10 of 12 -- `always_wrong` to "
          "`unstable_counted_right` -- and Q3 olx moved 18/20 to 19/20. The three "
          "cells it pre-registered as at risk (p9, p14, p18) are all 12 of 12, "
          "because none of them rests actionability on measurability and the rule "
          "could not reach them. Residue recorded and deliberately not carried: "
          "two runs still credit `action_oriented` on p19, which is a "
          "wording-strength question on a cell now counted right. Q3/p10 is NOT "
          "this subgoal's -- the entry disowned it twice in writing and it belongs "
          "to Q10, whose defect is `measurable`; the ranking attributes it here "
          "only because the body names the cell in order to hand it away.",
    "Q29": "closed 2026-09-05 on the user's instruction, after both of its "
           "stated questions were answered and neither answer was the one it "
           "expected. (1) Is the gate right? Q2's deduction dictionary carries "
           "WGB_UNRELATED at 5.0 AND WGB_NOT_OPPOSITE at 2.0, so the whole-item "
           "charge is the rubric's rather than ours: the two codes are TIERS of one "
           "criterion, and the question was never whether a gate should exist but "
           "which tier a cell falls in. The entry's framing -- 'the same judgement "
           "is worth 2 to the grader and 5 to us ... that is the wiring' -- was "
           "wrong in that specific way. (2) Is the slot stable enough to gate? It "
           "is now: `wgb_is_counterpart` answers `met` 12 of 12 on p10 where the "
           "entry recorded it flipping five-to-one. And the demonstration cell is "
           "FIXED -- Q2/p10 went 1 of 12 to 12 of 12 when subgoal Q17's edit (c) "
           "re-aimed the gate on the ACTIVITY the goal names. That delivers the "
           "entry's own measured counterfactual (gate does not fire -> 3.00 = gold) "
           "without removing a gate that subgoal Q21 shows PR and PP depend on, so "
           "the option the entry could not see was that the gate was mis-AIMED "
           "rather than mis-wired. Verified before closing: no cell has Q29 as its "
           "only owner. NR/p11 belongs to Q21 and Q45, and the three cadence cells "
           "were already withdrawn to Q22.",
    "Q20": "closed 2026-09-04 on the user's instruction, on the FINDING rather "
           "than the cells. Asked of each of its six stable members whether an "
           "instrument for gold's objection exists, instead of inferring absence "
           "from 'every check passes'. All six have one. Two are counts that "
           "over-report (Q1/p10, Q2/p6), three are slots answering `met` where "
           "gold charges (1a/p6, Q6/p2, DAY2/p7 -- the last at pts=1.0 against "
           "gold's 1 point), and one is an instrument that is RIGHT while gold is "
           "the outlier (Q4c/p20). So the class the entry was built to name does "
           "not exist: the sheet is not missing checks, it is applying the ones it "
           "has too leniently. Two of the entry's own claims were false and are "
           "corrected in it: DAY2 'has no slot to name' (it has one, at the right "
           "price) and Q6/p2 being 'DECLARED' (gold_divergence and corrected_gold "
           "both return nothing). All six cells are routed to owners before "
           "closing -- Q14, Q44, Q36, and the newly filed Q46, Q47 and Q48 -- so "
           "nothing is orphaned.",
    "Q35": "closed 2026-09-04 on the user's instruction, after the routing it "
           "asked for emptied it. Of its six cells: Q2/p20 was FIXED the same day "
           "by subgoal Q17's edit (a), 1 of 12 to 11; Q4b/p13 and DAY2/p8 were "
           "already owned by subgoals Q18 and Q22; PR/p15 moved to the newly filed "
           "subgoal Q45, because the route this entry prescribed did not exist "
           "(Q21 is scoped to NR and PR is a sibling item); and one cell was a "
           "SUSPECT one that was never evidence at all -- handout 2's byte-identical "
           "transcriptions -- now removed and deliberately not named, since the "
           "owner map counts any mention. The last cell, 2a/p14, is recorded as a "
           "CEILING rather than handed on: no open subgoal names any 2a cell or the "
           "`verdict` slot, the item's own subgoal Q2 already closed at its ceiling "
           "and handed this cell here, and the defect is one slot in two runs where "
           "the two dissenting runs disagreed with EACH OTHER on a garbled sentence "
           "the rubric declares irrelevant. Closing with a counted-RIGHT cell is "
           "the hazard and the entry says so: wrong_cells_without_an_owner will not "
           "report 2a/p14, so the written record is the only protection.",
    "Q24": "closed 2026-09-04 on the user's instruction, as the entry's own "
           "standing rule required -- 'IF NEITHER ROUTE OPENS, RECORD THE CEILING "
           "AND STOP'. Neither opened. Route 2 dissolved rather than failed: the "
           "entry treated p19 as a silent-full-marks cell of subgoal Q31's, and "
           "p19's gold had since been corrected 5.00 -> 3.00, so we AGREE with it "
           "in 11 of 12 runs (and Q31 is closed, so the hand-off had nowhere to "
           "land). Route 1 stays closed on the entry's own reading: gold's plural "
           "comment on p14 charges both boxes, box 2 is unambiguously a "
           "consequence, so the row belongs to subgoal Q19's later-box gradient, "
           "which owns the cell. The ceiling is one cell that no box-1 rule can "
           "reach -- p10 and p17 carry the same shape on the same UTB at full "
           "marks, 12 of 12 correct -- and p2 and p9 are counted right and "
           "unstable, which is E41's class. Found while closing, and fixed: the "
           "p19 correction had never been applied to the ledger, so Q4a was "
           "recorded a cell short on both sides. Re-recorded from the existing "
           "artifacts at no call cost, 18/20 -> 19/20 python and 17/20 -> 18/20 "
           "olx. Of the 14 CORRECTED_GOLD cells that was the only stale one.",
    "E41": "closed 2026-09-04 on the user's instruction (\"do steps 1-4 on E41 so "
           "it can be closed\"), after the check for whether it was SAFE to close "
           "found that it was not yet. Closing would have orphaned 1c/p16 and "
           "Q5/p9, whose only live owner was E41, and no check would have said so: "
           "both are counted RIGHT by the per-cell median, and "
           "wrong_cells_without_an_owner only sees cells wrong by it -- the "
           "laundering E41 itself documented, arriving on its own closure. Both "
           "now belong to subgoal Q30 with evidence, and Q5/p9 answers a question "
           "Q30 had left open: gold WROTE ABOUT the weak second reason and charged "
           "nothing for it. Also done first: the band figures re-derived after "
           "DAY2's re-sweep (404 perfect, 59 unstable, 5 on the line, 11 wrong by "
           "median, 12 always wrong, and WK2/p11 has left the on-the-line list), "
           "and the declared residual -- nothing records a cell's band at the time "
           "a change was measured -- refiled as subgoal E42 rather than closed "
           "over. Deliverables verified rather than assumed: cell_bands() bands "
           "all 491 cells, cells_on_the_median_line() is preflight step 5c, "
           "goals.rank() consumes the bands, and wrong_cells_without_an_owner() "
           "holds at zero after the closure.",
    "E40": "closed 2026-09-04 on the user's confirmation. All four deliverables "
           "met -- bare `pN` resolves through the title's item in the shared map, "
           "ownership was fire-tested against the map rather than the regex, "
           "wrong_cells_without_an_owner held at 0, and the ranking's duplicate "
           "was deleted. Two defects found while doing it are recorded in the "
           "entry: the shared map lacked the entry boundary, and deleting the "
           "duplicate let a paper-side subgoal claim OLX-side cells until "
           "subject ownership was routed through by_side.",
    "Q37": "closed 2026-09-04 on the user's confirmation. Its three items were "
           "done, and its WARNING became structural rather than narrative: "
           "stale_slot_claims dates every slot figure in an open goal against "
           "the profile that produced it, so closing the entry no longer loses "
           "the knowledge that a figure may predate its instrument",
}


def entries(text: str) -> dict[str, tuple[str, str]]:
    """label -> (state, title), in document order. state is ' ' or 'x'."""
    out: dict[str, tuple[str, str]] = {}
    for m in ENTRY.finditer(text):
        out[f"{m.group(2)}{m.group(3)}"] = (m.group(1), m.group(4)[:88])
    return out


def _committed() -> str | None:
    try:
        r = subprocess.run(["git", "show", "HEAD:./GOALS.md"], cwd=HERE,
                           capture_output=True, text=True, timeout=30)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def next_label(prefix: str = "Q") -> str:
    """The next free label for a prefix, so a new subgoal's id is not guessed.

    Allocated from the MAXIMUM in use rather than the first gap: a retired number
    must not be reissued, because citations of it survive in commits and memory
    long after the entry is closed.
    """
    text = GOALS.read_text()
    used = [int(m.group(3)) for m in ENTRY.finditer(text) if m.group(2) == prefix]
    # SPENT LABELS COUNT TOO. A refiled number no longer appears as an entry, so
    # the maximum drops and the allocator offers it again -- it offered Q38 back
    # the moment Q38 became E40, while Q38 was still cited in a commit message
    # and in E40's own history note. Two subgoals answering to one name is the
    # thing this function exists to prevent.
    used += [int(l[len(prefix):]) for l in REFILED
             if l.startswith(prefix) and l[len(prefix):].isdigit()]
    return f"{prefix}{(max(used) + 1) if used else 1}"


def check() -> list[str]:
    """Everything about GOALS.md's entries that a program can settle."""
    bad: list[str] = []
    try:
        text = GOALS.read_text()
    except OSError as e:
        return [f"{GOALS.name} cannot be read: {type(e).__name__}: {e}"]

    # 1. DUPLICATES. Two entries answering to one citation.
    seen: dict[str, str] = {}
    for m in ENTRY.finditer(text):
        label = f"{m.group(2)}{m.group(3)}"
        if label in seen:
            bad.append(
                f"{GOALS.name}: duplicate goal label {label} — '{seen[label]}' and "
                f"'{m.group(4)[:60]}'. Every citation of {label} is now ambiguous; "
                f"`python3 goals.py --next {m.group(2)}` allocates a free one")
        else:
            seen[label] = m.group(4)[:60]

    now = entries(text)

    # 2. DANGLING CITATIONS, across the tree.
    for path in sorted(list(HERE.glob("*.md")) + list(HERE.glob("*.py"))):
        if path.name == "goals.py":
            continue
        try:
            src = path.read_text()
        except OSError:
            continue
        for n, line in enumerate(src.splitlines(), 1):
            for pre, num in CITE.findall(line):
                if f"{pre}{num}" not in now:
                    bad.append(
                        f"{path.name}:{n} cites subgoal {pre}{num}, which is not an "
                        f"entry in {GOALS.name} — the label is wrong, or the entry "
                        f"was deleted rather than closed")

    before_text = _committed()
    if before_text is None:
        return bad
    before = entries(before_text)

    # 3. DELETIONS. A goal is closed, never removed: its number is cited
    #    elsewhere and its record is the reason the work is not redone.
    for label, (_state, title) in before.items():
        if label not in now:
            moved = REFILED.get(label)
            if moved:
                if moved[0] in now:
                    continue                  # declared, and the target exists
                bad.append(
                    f"{GOALS.name}: goal {label} is declared REFILED to "
                    f"{moved[0]}, but {moved[0]} is not an entry in the file. A "
                    f"refile that points nowhere is a deletion with a note on it")
                continue
            bad.append(
                f"{GOALS.name}: goal {label} ('{title[:60]}') was in the committed "
                f"file and is GONE. Goals are closed with `- [x]`, never deleted — "
                f"the entry is what stops the work being redone, and its number is "
                f"cited elsewhere. Restore it")

    # 4. UNAPPROVED CLOSURES. GOALS.md's own first rule, enforced.
    for label, (state, title) in now.items():
        was = before.get(label)
        if was and was[0] == " " and state == "x" and label not in CLOSURES_APPROVED:
            bad.append(
                f"{GOALS.name}: goal {label} ('{title[:60]}') is being CLOSED and the "
                f"user has not agreed. This file's own first rule is never to close "
                f"a goal without asking. Ask, then record it in "
                f"goals.CLOSURES_APPROVED as \"{label}\"")
    return bad


def misfiled_series() -> list[str]:
    """Entries whose label series does not match the section they are filed in."""
    out: list[str] = []
    sec = None
    for n, line in enumerate(GOALS.read_text().splitlines(), 1):
        if re.match(r"^## ", line):
            sec = line[3:]
            continue
        m = ENTRY.match(line)
        if not m:
            continue
        want = SERIES_SECTION.get(m.group(2))
        if want and sec is not None and want not in sec:
            out.append(
                f"{GOALS.name}:{n} {m.group(2)}{m.group(3)} is filed under "
                f"'{sec[:44]}' but the {m.group(2)} series lives in the "
                f"'{want}' section. Move the entry, or the label is wrong -- "
                f"{SERIES_TEST}")
    return out


def main(argv: list[str]) -> int:
    if "--next" in argv:
        i = argv.index("--next")
        pre = argv[i + 1] if len(argv) > i + 1 else "Q"
        print(next_label(pre))
        print(f"  ({pre} lives in the '{SERIES_SECTION.get(pre, '?')}' section. "
              f"{SERIES_TEST}.)")
        return 0
    if "--list" in argv:
        for label, (state, title) in entries(GOALS.read_text()).items():
            print(f"  [{state}] {label:5} {title[:70]}")
        return 0
    if "--rank" in argv:
        for i, (lab, _f, why) in enumerate(rank(), 1):
            print(f"  {i:>2}. {lab:5} {why}")
        return 0
    if "--slot-claims" in argv:
        s = stale_slot_claims()
        print("\n".join(f"  ! {x}" for x in s) if s
              else "  no open goal quotes a slot figure older than the instrument")
        return 1 if s else 0
    bad = check() + misfiled_series()
    if bad:
        print("\n".join(f"  ! {b}" for b in bad))
        return 1
    e = entries(GOALS.read_text())
    op = sum(1 for s, _t in e.values() if s == " ")
    print(f"  {GOALS.name}: {len(e)} goals ({op} open, {len(e) - op} closed), "
          f"labels unique, citations resolve, none deleted or newly closed")
    return 0



# ------------------------------------------------- slot claims vs the instrument

# THE FUNCTIONS A SLOT-LEVEL FIGURE IS COMPUTED THROUGH. A claim written before
# any of these last changed was produced by a different instrument, and the two
# were unlinked until 2026-09-04: the knowledge that a figure came from a BLIND
# profile lived as narrative in one subgoal entry, which meant it would die when
# that entry closed. This is the `prompt_sha` treatment applied to prose --
# exactly the STALE PROMPT idea, for claims about slots instead of items.
_PROFILE_TOKENS = ("_our_failing_slots", "_charging_slots", "_gold_nameable_slots")

# A count, in the forms this file actually uses.
_COUNT = re.compile(r"\b\d+\s*(?:of|/)\s*\d+\b|\b\d+ refusals?\b|\b\d+%")

# An era record, marked as one on purpose. The same vocabulary
# `measured._HISTORICAL` uses, so an author marks a figure historical once and
# both checks honour it.
_HISTORICAL = re.compile(
    r"\b(was|were|had been|previously|prior|before|earlier|then|originally|"
    r"superseded|stale|no longer|as measured|as filed|at the time)\b", re.I)


def _slot_keys() -> frozenset:
    """Every real slot key in the corpus, from the OLX sheets.

    Restricting to REAL keys is what keeps this from firing on every backticked
    identifier: `error_profile` and `sweep_summary` are function names, not
    slots, and a claim mentioning them is not a slot-level claim.
    """
    try:
        import agreement as A
        import agreement_app as AA
        import olx_prompts as O
    except Exception:
        return frozenset()
    keys: set = set()
    for item, job in AA.JOBS.items():
        try:
            spec = A.load_action(f"bmod_handout{job['handout']}.olx", O.ACTION[item])
        except Exception:
            continue
        keys |= {s["key"] for s in spec.get("slots") or []}
    return frozenset(k for k in keys if len(k) > 4)


def stale_slot_claims(instrument_at: int | None = None) -> list[str]:
    """Slot-level figures in OPEN goals that predate the instrument that made them.

    A figure like "34 refusals, 71% precision" is a claim about what a program
    computed. When that program changes, the claim does not -- and nothing linked
    the two, so the only record of "these numbers came from a blind profile" was
    a paragraph inside one subgoal. Paragraphs close.

    Scoped and exempted so it stays readable:
      OPEN entries only -- a closed goal's figures are its record, not a claim
        about the present, and 42 of the corpus's 49 slot claims are in closed
        entries.
      HISTORICAL lines are skipped, on the marker vocabulary `prose_claims`
        already uses, so a figure can be kept deliberately as an era record.
      REAL SLOT KEYS only, read from the OLX sheets rather than pattern-matched,
        so a backticked function name is not mistaken for a slot.

    The honest alternative to this check is not to write the numbers: prose that
    names a CELL and a SLOT cannot go stale, prose that quotes a count always
    can. This exists for the ones already written.
    """
    keys = _slot_keys()
    if not keys:
        return ["cannot read the corpus's slot keys, so slot claims cannot be dated"]
    if instrument_at is None:
        # `-L :func:file`, NOT `-S token`. The pickaxe matches TEXTUAL
        # occurrences, so a docstring that merely NAMES one of these functions
        # moved the instrument date and back-dated a figure re-derived hours
        # earlier -- which is how this check produced its first false alarm, on a
        # line the same session had just corrected. `-L` follows the function's
        # own definition, which is the thing whose behaviour matters.
        stamps = []
        for tok in _PROFILE_TOKENS:
            try:
                r = subprocess.run(["git", "log", "-1", "--format=%at",
                                    "-L", f":{tok}:measured.py"], cwd=HERE,
                                   capture_output=True, text=True, timeout=60)
                if r.returncode == 0 and r.stdout.strip():
                    stamps.append(int(r.stdout.splitlines()[0].strip()))
            except Exception:
                pass
        if not stamps:
            return []
        instrument_at = max(stamps)

    try:
        bl = subprocess.run(["git", "blame", "--line-porcelain", "GOALS.md"],
                            cwd=HERE, capture_output=True, text=True, timeout=120)
        if bl.returncode != 0:
            return []
    except Exception:
        return []

    lines: list[tuple[int, str]] = []          # (author_time, text)
    at = 0
    for row in bl.stdout.splitlines():
        if row.startswith("author-time "):
            at = int(row.split()[1])
        elif row.startswith("\t"):
            lines.append((at, row[1:]))

    out: list[str] = []
    label, state = None, "x"
    for n, (when, text) in enumerate(lines, 1):
        m = ENTRY.match(text)
        if m:
            label, state = f"{m.group(2)}{m.group(3)}", m.group(1)
        if state != " " or label is None:
            continue                            # closed entry, or preamble
        if when >= instrument_at:
            continue
        if _HISTORICAL.search(text):
            continue
        named = [k for k in re.findall(r"`([a-z][a-z0-9_]+)`", text) if k in keys]
        if not named or not _COUNT.search(text):
            continue
        out.append(
            f"GOALS.md:{n} (goal {label}) quotes a slot figure for "
            f"{', '.join(named[:3])} that was written BEFORE the slot profile last "
            f"changed, so it is not a figure the current instrument produced: "
            f"\"{text.strip()[:70]}\". Re-derive it with `measured.py --errors "
            f"<item> <artifact>` or `--refusals <item>`, mark the line historical "
            f"if it is meant as an era record, or drop the count and name the cell "
            f"and slot instead")
    return out


# ------------------------------------------------------------------- ranking

def rank() -> list[tuple[str, dict, str]]:
    """Open goals in priority order, DERIVED rather than remembered.

    Standing instruction, 2026-09-04: "Knowing what the rank order of goals is,
    and redoing it when something happens that would affect the ranking, is
    something that ought to be happening automatically." So there is no stored
    ranking to go stale -- it is recomputed from the ledger and the goal file
    every time it is asked for, and it prints the FACTS it ordered on rather than
    a score, because a score cannot be argued with.

    The ordering follows this project's own guide (§0): a DETERMINISTIC miss with
    a named failing check is worth more than a larger gap of unknown shape,
    "because it can be fixed or declared; a wobbling cell cannot be either". So,
    in order:

      deterministic wrong cells    a cell wrong in EVERY pooled run
      cells the TITLE claims       ownership stated rather than mentioned in passing
      citations from other OPEN    how many other subgoals are waiting on it
      items to sweep               fewer is cheaper to settle
      unstable cells               counted, but last: they cannot be measured against

    What it deliberately does NOT do is decide anything. It cannot read whether a
    candidate fix exists, and that has decided more of this project's priorities
    than any count -- so the output is an ordering to argue with, not an answer.
    """
    import re as _re
    try:
        import measured as M
    except Exception as e:
        return [("", {}, f"cannot rank: measured will not import: {type(e).__name__}")]

    text = GOALS.read_text()
    open_labels = [l for l, (st, _t) in entries(text).items() if st == " "]
    try:
        owners = M._live_subgoal_owners()
    except Exception as e:
        return [("", {}, f"cannot rank: {type(e).__name__}: {e}")]

    # PER CELL, POOLED OVER THE OLX-PROMPT SIDES. `records()` takes a SIDE and
    # defaults to one, so `records()[item]["olx"]` is None rather than an error --
    # the trap measured.py records at its own declaration_conflicts, where reading
    # one side made a declaration the other side had refuted invisible. The first
    # version of this ranking hit it and reported that NO open goal owned a wrong
    # cell, which degenerated the whole order into citation counts and looked
    # plausible. Ask for each side by name.
    # BANDS COME FROM measured.cell_bands, not from thresholds repeated here.
    # Subgoal E41 made the band derivable and E40's lesson is why this consumes
    # it rather than recomputing: two implementations of one rule is the
    # divergence class this project exists to close, and this function has now
    # been the second copy twice.
    bands = M.cell_bands()
    state = {c: (r, n) for c, (r, n, _b) in bands.items()}

    # citations between OPEN goals
    cited: dict[str, int] = {l: 0 for l in open_labels}
    label = None
    for line in text.splitlines():
        m = ENTRY.match(line)
        if m:
            label = f"{m.group(2)}{m.group(3)}"
        for pre, num in CITE.findall(line):
            tgt = f"{pre}{num}"
            if tgt in cited and label != tgt and label in open_labels:
                cited[tgt] += 1

    # PRIMARY OWNERSHIP, NOT MENTION. `owners["any"]` repeats a label once per
    # MENTION and is generous on purpose -- it exists so no wrong cell can be
    # left with nobody looking at it. For ranking that is the wrong instrument:
    # the first version credited DAY2/p7 to four subgoals at once and gave Q26,
    # which is about one character of DAY1's OLX, two deterministic cells it has
    # nothing to do with. A subgoal that mentions a cell five times is discussing
    # it; one that mentions it once in an aside is not. So the owner is whoever
    # mentions it MOST among open goals, ties shared.
    # AND AN ENTRY ENDS WHERE THE NEXT ENTRY *OR* THE NEXT HEADING BEGINS. Bounding
    # only at the next entry makes the LAST labelled entry of a section swallow
    # everything after it: Q26's body measured 8223 characters that way and
    # contained other subgoals' cells, which is how a subgoal about one character
    # of DAY1's OLX came to own a Q4b cell. Counted here rather than by changing
    # measured._live_subgoal_owners, which is generous ON PURPOSE -- it exists so
    # that no wrong cell is left unlooked-at, and narrowing it would weaken the
    # audit that depends on it.
    all_items = set(M._jobs())
    ITEM_TOK = _re.compile(r"(?<![\w/])(" + "|".join(sorted(
        (_re.escape(i) for i in all_items), key=len, reverse=True)) + r")(?![\w/])")
    CELL = _re.compile(r"\b([A-Za-z0-9]+)/p(\d+)\b")
    lines = text.splitlines()
    bounds: dict[str, list[str]] = {}
    cur = None
    for line in lines:
        m = ENTRY.match(line)
        if m:
            cur = f"{m.group(2)}{m.group(3)}"
            bounds[cur] = [line]
            continue
        if _re.match(r"^#{1,3} ", line):
            cur = None                      # a heading ends the entry
            continue
        if cur:
            bounds[cur].append(line)

    # OWNERSHIP COMES FROM THE SHARED MAP, not from a second copy of the rule.
    # This function carried its own bare-`pN` resolution while subgoal E40 was
    # open, because the ranking was the thing visibly wrong and the shared map is
    # read by several checks. E40 landed the resolution there -- with the entry
    # boundary and the `subject` map -- so the copy is deleted. Two
    # implementations of one rule is the divergence class this project exists to
    # close, and E40's own entry required this deletion.
    #
    # `subject` means the entry's TITLE names the item and the cell appears in
    # the entry: it is about the cell. `any` is every mention and is generous on
    # purpose, so it decides only when nothing claims the cell as its subject.
    owned = M._live_subgoal_owners()
    primary: dict[str, tuple] = {}
    for cell, labs in owned["any"].items():
        # AND OWNERSHIP MUST BE FOR THE SIDE THE FIGURES COME FROM. The cells
        # counted wrong here are the POOLED OLX-PROMPT ones, so a subgoal about
        # the paper scorer is not a home for them -- which is the whole reason
        # the shared map carries `by_side`. Without this, Q33 ("Q4a on the PAPER
        # scorer") claimed Q4a/p14 and Q4a/p19 the moment bare-`pN` resolution
        # landed, and rose to second place on cells that are wrong on a side it
        # is not about.
        for_side = {l for s in ("olx+python",)
                    for l in (owned["by_side"].get(cell, {}).get(s) or [])}
        subj = [l for l in dict.fromkeys(owned["subject"].get(cell, []))
                if l in open_labels and l in for_side]
        if subj:
            primary[cell] = tuple(sorted(subj))
            continue
        counts: dict[str, int] = {}
        for l in labs:
            if l in open_labels:
                counts[l] = counts.get(l, 0) + 1
        if not counts:
            continue
        top = max(counts.values())
        primary[cell] = tuple(sorted(l for l, c in counts.items() if c == top))

    # NEVER MEASURED OUTRANKS EVERYTHING, because it is the one state where there
    # is nothing to rank ON. An item with no number has no wrong cells, so it looks
    # from the ledger exactly like an item with nothing owed -- which is how E28
    # sat at the bottom of the first ranking while 24 of 26 items had no `paper`
    # figure at all. A gap is not an absence of work; it is work nobody has
    # started.
    #
    # SIDE-AWARE, via measured._sides_named, which the owner map already uses to
    # decide which side a goal speaks about. A goal naming the paper side is asking
    # about paper numbers; one that mentions olx in passing is not asking for a
    # fresh sweep of the corpus. And a goal that names a side but NO item is
    # corpus-wide by construction -- E28's deliverable IS the corpus -- while one
    # that names items is scoped to them.

    def _measured_on(item: str, side: str) -> bool:
        try:
            if side == "olx+python":
                return any(item in M.records(s) for s in M.POOLED_OLX_PROMPT)
            return item in M.records(side)
        except Exception:
            return True                       # unknown is not a gap

    def _unmeasured_for(lab: str) -> list[str]:
        # THE SIDE COMES FROM THE TITLE, not the body. Reading the body put
        # `[paper]` gaps on Q17, Q19, Q20 and Q36, none of which is asking for a
        # paper sweep -- they mention the word once in passing. A goal whose
        # SUBJECT is a side says so where it says what it is about: E28 is "A
        # PAPER sweep the ledger can record", Q33 is "Q4a on the PAPER scorer".
        body = bounds.get(lab) or []
        title = body[0] if body else ""
        sides = M._sides_named(title)
        if not sides:
            return []                        # not a side-scoped goal; nothing owed
        # SCOPE FROM THE TITLE TOO, for the same reason as the side. Scoping from
        # the BODY undercounted E28 at 7 gaps instead of 24: its deliverable is
        # the whole corpus and its title names no item, but its prose mentions a
        # handful, so the scope collapsed onto those. A title that names items is
        # scoped to them (Q33 is "Q4a on the PAPER scorer" and Q4a HAS a paper
        # number, so it owes nothing there); a title that names none, while naming
        # a side, is corpus-wide.
        named = ((set(ITEM_TOK.findall(title)) | {
            c.split("/")[0] for c in primary if lab in primary[c]}) & all_items)
        # `& all_items` on BOTH halves: the cell-derived set was not filtered, so
        # prose like "p10/p18" produced an "item" called p10, which is measured
        # nowhere and therefore counted as a gap.
        scope = sorted(named) if named else sorted(all_items)
        return [f"{i}[{s}]" for s in sorted(sides) for i in scope
                if not _measured_on(i, s)]

    rows = []
    for lab in open_labels:
        det, stab, unst, items, titled = [], [], [], set(), 0
        for cell in primary:
            if lab not in primary[cell]:
                continue
            st = state.get(cell)
            if st is None:
                continue
            right, runs = st
            if right == runs:
                continue                      # cell is correct; nothing owed
            items.add(cell.split("/")[0])
            # THREE BUCKETS, NOT TWO. `right == 0` alone bucketed a cell that
            # reaches gold ONCE in twelve with genuine coin-flips -- Q1/p10 is
            # right 1 of 12 and its own subgoal makes the distinction that
            # matters: "stably wrong ... not a coin flip, and it is worth a rule
            # question rather than more runs". A cell that almost never reaches
            # gold can be fixed or declared; one that lands half the time cannot.
            band = bands[cell][2]
            if band == "always_wrong":
                det.append(cell)
            elif band == "wrong_by_median" or (band == "on_the_line"
                                               and right * 2 < runs):
                # counted wrong and rarely right: fixable or declarable
                stab.append(cell)
            else:
                unst.append(cell)
        for cell, labs in owners["title"].items():
            st = state.get(cell)
            if lab in labs and st is not None and st[0] != st[1]:
                titled += 1
        gaps = _unmeasured_for(lab)
        # COST IN SWEEPS, the unit that actually gets spent: an item measured on
        # both sides is two. Reported rather than folded into a score, because a
        # cost estimate is the part of a ranking most worth arguing with -- E28's
        # own entry puts its real figure at ~3,100 calls, which one sweep of the
        # whole corpus buys more cheaply than 24 separate ones.
        # A WRONG CELL needs the item swept on BOTH sides; a GAP already names the
        # one side it is missing, so counting it twice overstated E28 at 48 when
        # the work is 24 item-sides -- and its own entry puts the real figure at
        # ~3,100 calls, because one paper sweep covers every item at once.
        n_items = len({c.split("/")[0] for c in det + stab + unst}) * 2 + len(gaps)
        facts = {"deterministic": sorted(det), "stably_wrong": sorted(stab),
                 "unstable": sorted(unst),
                 "items": sorted(items), "titled": titled, "cited_by": cited[lab],
                 "unmeasured": gaps, "sweeps": n_items * 2}
        rows.append((lab, facts))

    # TIERS, because cost is not commensurable with evidence and pretending it is
    # means inventing weights. A DETERMINISTIC miss on one or two items can be
    # fixed or declared for a few hundred calls; a corpus-wide gap cannot be
    # touched for less than thousands. So: cheap-and-deterministic first, then
    # deterministic at any price, then the gaps, then cells that only wobble.
    #
    # THE FIRST VERSION PUT never-measured FIRST OUTRIGHT, which sent a ~3,100
    # call job to the top of a list whose next four entries cost a few hundred
    # each. Surfacing a gap and preferring it are different things.
    CHEAP = 4                                # sweeps, i.e. two items on two sides

    def _tier(f: dict) -> int:
        fixable = f["deterministic"] + f["stably_wrong"]
        if fixable and f["sweeps"] <= CHEAP:
            return 0
        if fixable:
            return 1
        if f["unmeasured"]:
            return 2
        if f["unstable"]:
            return 3
        # NOTHING ATTRIBUTED RANKS LAST, and it took a fix to get there: tier 3
        # sorted on COST, so goals owning no cells at all (cost 0) came out above
        # goals owning unstable ones. Cheap is only a virtue when something is
        # being bought.
        return 4

    # WITHIN A DETERMINISTIC TIER, COST LEADS. Sorting on evidence first put a
    # 28-sweep subgoal above an 8-sweep one on the strength of having more wrong
    # cells, which is the opposite of "cheap deterministic wins above expensive
    # calls": five cells settled for 28 sweeps is worse value than two settled
    # for eight, and the cheap one also gets answered sooner. Evidence still
    # breaks ties, and it still leads in the tiers where nothing is cheap.
    def _key(r):
        lab, f = r
        tier = _tier(f)
        if tier in (0, 1):
            return (tier, f["sweeps"],
                    -len(f["deterministic"]) - len(f["stably_wrong"]),
                    -len(f["deterministic"]), -f["titled"], -f["cited_by"], lab)
        return (tier, -len(f["unmeasured"]), -len(f["unstable"]),
                f["sweeps"], -f["titled"], -f["cited_by"], lab)

    rows.sort(key=_key)
    out = []
    for lab, f in rows:
        why = []
        if f["unmeasured"]:
            why.append(f"{len(f['unmeasured'])} NEVER MEASURED "
                       f"({', '.join(f['unmeasured'][:3])})")
        if f["deterministic"]:
            why.append(f"{len(f['deterministic'])} deterministic ({', '.join(f['deterministic'][:3])})")
        if f["stably_wrong"]:
            why.append(f"{len(f['stably_wrong'])} stably wrong "
                       f"({', '.join(f['stably_wrong'][:3])})")
        if f["titled"]:
            why.append(f"{f['titled']} claimed by title")
        if f["cited_by"]:
            why.append(f"{f['cited_by']} open goal(s) cite it")
        if f["unstable"]:
            why.append(f"{len(f['unstable'])} unstable ({', '.join(f['unstable'][:3])})")
        if f["sweeps"]:
            why.append(f"~{f['sweeps']} sweep(s) to settle")
        out.append((lab, f, "; ".join(why) or "no wrong cell currently attributed"))
    return out


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
