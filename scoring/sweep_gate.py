#!/usr/bin/env python3
"""Every check that must pass BEFORE a sweep spends a call. Subgoals E46/E48/E50.

    python3 sweep_gate.py ITEM [ITEM ...]

Exits 0 to proceed, 1 to refuse, and says which gate refused and why.

WHY THIS EXISTS AS ONE FILE. Each sweep script used to carry its own gates,
re-typed by hand, and the copies drifted: on 2026-09-05 fourteen of twenty-one
scripts gated on leakage and ONE checked anything else. The consequence is on
record -- subgoal Q18's sweep spent ~240 calls on a prompt whose rule named a
slot that never reached the sheet, because that script's guard asked whether the
slot name appeared ANYWHERE IN THE FILE and it appeared twice, in the two prose
mentions the generator had just written. A gate that cannot tell presence in the
file from presence in the slot list certifies the fault it exists to stop.

THE RULE THESE ENFORCE, and why each is BEFORE the calls rather than after: a
sweep records a number against a prompt sha. If the prompt is malformed, the
number describes something nobody meant to measure, and the cost is the whole
sweep. Every check here is static -- no model calls, no artifacts -- so the gate
is cheap and can never itself be the reason a sweep is slow.

NOT INCLUDED, deliberately: the mapped-slot ARTIFACT check. It reads what a
sweep PRODUCED, so it cannot run before one; it is preflight step 5f instead.
"""
import sys


def gate(items: tuple[str, ...]) -> int:
    """0 to proceed, 1 to refuse."""
    sys.path.insert(0, "/home/pdeane/code/edu.memphis.psych/scoring")
    import enforcement as E
    import leakage as L

    refused: list[str] = []

    # 1. LEAKAGE. Audits every item whatever is being swept -- see leakage.gate,
    #    which ignores its argument on purpose. Passed through so the refusal
    #    message names the sweep's own items.
    if L.gate(items):
        refused.append("leakage")

    # 2. EVERY RUBRIC SLOT REACHES THE SHEET (E48). Scoped to the items being
    #    swept: a dangling slot on an item nobody is measuring is a real finding
    #    for the audit but not a reason to refuse THIS sweep.
    bad = [x for x in E.check_rubric_slots_reach_the_sheet()
           if any(x.startswith(f"{i}/") for i in items)]
    if bad:
        print("REFUSING: a rubric slot never reaches the sheet, so a rule naming "
              "it points at an answer that cannot exist:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("rubric-slot")

    # 3. NO MAPPED SLOT OFFERS A VERDICT ITS MAP CANNOT EMIT (E46). Corpus-wide,
    #    not item-scoped: the mirror derives a mapped slot and the app can answer
    #    it directly, so an unreachable verdict is a divergence surface wherever
    #    it sits, and it costs nothing to refuse on it.
    bad = E.check_mapped_slots_have_no_unreachable_verdict()
    if bad:
        print("REFUSING: a mapped slot offers a verdict its map cannot emit:",
              file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("mapped-slot")

    # 4. THE REVERSE DIRECTION (E49): a sheet slot no rubric element defines.
    #    Scoped to the swept items -- an app-only question on an item nobody is
    #    measuring is a finding for the audit, not a reason to refuse this sweep.
    bad = [x for x in E.check_sheet_slots_reach_the_rubric()
           if any(x.startswith(f"{i}/") for i in items)]
    if bad:
        print("REFUSING: the sheet asks a question no rubric element defines:",
              file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("sheet-slot")

    # 5b. A MAPS TABLE THAT WAS NEVER ATTACHED. Corpus-wide and unconditional:
    #     an unattached table means a pick has no route to its verdict on ANY
    #     item that uses it, and the failure is silent everywhere -- the sheet,
    #     the rubric and `olx_prompts.py --check` all read green. Found on
    #     2026-09-06 by a hand-written assertion in subgoal Q30's own sweep
    #     script, which is the arrangement this file exists to replace.
    bad = E.check_maps_tables_are_attached()
    if bad:
        print("REFUSING: a MAPS table is defined but never attached, so the pick "
              "it belongs to has no route to its verdict:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("maps-attached")

    # 5d. MANDATORY, ALL 145 PROMPT FIELDS. 5c guards wording somebody chose to
    #     write down; this guards every desc/rule the graders read, against a
    #     sha design-of-record. Made mandatory at the user's instruction after
    #     the opt-in version was shown to be unable to police a field nobody
    #     thought to record -- which was the case that cost the sweep.
    bad = E.check_every_prompt_field_is_designed()
    if bad:
        print("REFUSING: a prompt field is not the designed text:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("undesigned-field")

    # 5f. NO DEFINITION MAY VANISH UNANNOUNCED. Cheapest gate here and the one
    #     with the worst failure mode behind it: a slice-bounded edit that ate a
    #     neighbouring declaration left `--preflight` raising NameError for days,
    #     and the ledger tables it silently emptied were being read by cell-level
    #     checks the whole time. A sweep run on a tree in that state measures
    #     something nobody can reconstruct afterwards.
    bad = E.check_no_definition_vanished()
    if bad:
        print("REFUSING: a definition vanished from the package:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("vanished-definition")

    # 5e. A PROBE'S RESULT MUST DESCRIBE THE STRING ABOUT TO BE SWEPT.
    #     The two checks above compare shipped text against a DESIGN. This
    #     compares it against what was actually MEASURED, which is the only one
    #     of the three that can catch a probe read on Monday and cited on
    #     Wednesday. Refusing here is right: a stale probe is worse than no
    #     probe, because it reads as evidence.
    bad = E.check_probe_receipts_match_shipping()
    if bad:
        print("REFUSING: a probe measured text that no longer ships:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("stale-probe")

    # 5j. WHICH OF THIS ITEM'S CELLS ARE ALREADY DECLARED. Printed, never a
    #     refusal -- retesting a declared divergence is legitimate and sometimes
    #     right. What is NOT legitimate is not KNOWING, because then there is no
    #     point at which to give up. On 2026-09-07 four wordings and a ~230-call
    #     sweep were spent making the engine charge Q4b/p4, whose
    #     ANTECEDENT_REUSED_AS_BEHAVIOR entry already said the rule "rests on one
    #     cell" and that two prior implementations were "both worse than not
    #     having it". The declaration was keyed by that exact cell the whole time;
    #     the tables are spread over two modules and six names, so knowing to
    #     look meant already knowing the answer.
    try:
        import measured as _M

        for _it in items:
            _dec = []
            for _pid in range(1, 21):
                for _tbl, _code, _why in _M.declarations_for(_it, _pid):
                    if _tbl == "GOLD_DIVERGENCES":
                        _dec.append(f"p{_pid} {_code}")
            if _dec:
                print(f"    DECLARED on {_it} (our answer is the endorsed one; a "
                      f"rule that changes these is a REGRESSION): "
                      + ", ".join(_dec))
                print(f"      read the entry before aiming at one: "
                      f"measured.declarations_for('{_it}', N)")
    except Exception as _e:
        print(f"    declared-cell listing unavailable ({type(_e).__name__})")

    # 5k. A CEILING MUST BE DECLARED, NOT JUST NARRATED (E45's last constraint).
    bad = E.check_closure_ceilings_are_declared()
    if bad:
        print("REFUSING: a closure calls a cell a ceiling and no table says so:",
              file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("prose-only-ceiling")

    # 5i. A PROBED WORDING MUST BE RECOVERABLE, NOT MERELY DETECTABLE (E56d).
    bad = E.check_probed_fields_keep_their_text()
    if bad:
        print("REFUSING: a probed wording is recorded only as a sha:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("probed-text-not-recorded")

    # 5g. A DESIGN MUST BE THE EVIDENCE, NOT A SUMMARY OF IT (E56c). Refuses:
    #     a design that disagrees with the probe that is its only evidence would
    #     certify text nobody measured, which is what nearly shipped on Q4b.
    bad = E.check_designed_text_is_the_measured_text()
    if bad:
        print("REFUSING: a design is a paraphrase of its own evidence:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("paraphrased-design")

    # 5g-bis. A DESIGN OF RECORD THAT DOES NOT SHIP. Refuses. 5g compares a
    #     design against its PROBE; this compares it against the PROMPT, the
    #     only direction that catches a revert which dropped the build and left
    #     the entry, or a build that never landed. Added 2026-09-09 after SEVEN
    #     OF TWELVE entries turned out not to ship: the three sha-keyed links
    #     all skip a fragment key, because `DESIGNED_TEXT_SHA.json` holds only
    #     the rubric's own desc/rule fields.
    bad = E.check_every_designed_entry_ships()
    if bad:
        print("REFUSING: a design of record does not ship:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("design-does-not-ship")

    # 5h. A BRAND NEW QUESTION ABOUT TO BE MEASURED FOR THE FIRST TIME (E56a).
    #     REFUSES, on the user's decision of 2026-09-07. It began as a notice on
    #     the argument that the sweep might BE the experiment; the day's evidence
    #     went the other way. Every unprobed new question measured this way has
    #     cost a sweep and taught what ~30 calls would have: Q19's report slot
    #     (~230 calls, over-fired on nine cells), and the same slot's second
    #     wording, which a 76-call probe then killed on three cells a 6-cell
    #     probe had not looked at. The refusal is narrow by construction -- a
    #     slot the last recording never saw AND no probe ever asked -- so a
    #     re-measurement of unchanged questions still passes.
    bad = E.check_new_slots_were_probed()
    if bad:
        print("REFUSING: a new question would be measured for the first time by "
              "a sweep, unprobed:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("unprobed-new-slot")

    # 5e-bis. SAY WHEN THE PROBE CHECK VERIFIED NOTHING. A vacuous pass reads
    #     exactly like a verified one: with no receipt on record,
    #     `check_probe_receipts_match_shipping` is clean because there is nothing
    #     to compare. Asked directly -- "are we sweeping the same prompt as the
    #     one we last probed?" -- the gate could not answer, and its silence
    #     looked like a yes. This is a NOTICE, not a refusal: a re-measurement
    #     asks no new question and needs no probe.
    try:
        import probe as _PR

        # `gate` takes the items TUPLE, not one item -- the first cut wrote
        # `item` and every gate run died on NameError inside its own reporting.
        for _it in items:
            _seen = _PR.receipts(_it)
            if _seen:
                print(f"    probe receipts for {_it}: "
                      + ", ".join(f"{r['slot']}={r['sha']}" for r in _seen[:4]))
            else:
                print(f"    probe receipts for {_it}: NONE on record -- this gate "
                      f"verified nothing about probe/sweep identity. Fine for a "
                      f"re-measurement; for a new question, probe first (2a0).")
    except Exception as _e:
        print(f"    probe receipts: could not be read ({type(_e).__name__}: {_e})")

    # 5c. WHAT IS DESIGNED MUST BE WHAT SHIPS. Corpus-wide and unconditional.
    #     Every other gate here asks whether the shipped text is WELL-FORMED;
    #     this asks whether it is THE TEXT SOMEBODY DECIDED ON. Added after a
    #     re-typed `desc` dropped a question's comparison clause, passed every
    #     other gate, and cost a ~230-call sweep whose failure was then blamed on
    #     a "prompt-load effect" that did not exist.
    bad = E.check_shipped_text_matches_design()
    if bad:
        print("REFUSING: a slot ships wording its subgoal did not design -- the "
              "sweep would measure a question nobody chose:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("designed-text")

    # 5. NO COHORT CASE NAME IN A SHIPPED PROMPT (E50).
    bad = E.check_no_case_names_in_prompts()
    if bad:
        print("REFUSING: a shipped prompt names a cohort case:", file=sys.stderr)
        for x in bad:
            print(f"    {x}", file=sys.stderr)
        refused.append("case-name")

    if refused:
        print(f"\n    gates refused: {', '.join(refused)}", file=sys.stderr)
        return 1
    print(f"    sweep gate: all clear for {', '.join(items)}")
    # THE LAST THING SAID BEFORE THE CALLS. Not a gate -- nothing here can tell
    # whether a probe was run -- but this is the only place every sweep passes
    # through, and the question it asks is the one three reverted edits on
    # 2026-09-06 failed to ask. See QUALITY_CONTROL.md section 2a0.
    print("    -- before you spend this: has the new question been PROBED? A "
          "standalone\n"
          "       ask on the target plus its negatives costs ~30 calls and "
          "answers 'will the\n"
          "       grader apply this at all', which is what most reverted edits "
          "here died of.\n"
          "       Worked example: scratchpad/probe_q4b_report.py. Guide: "
          "QUALITY_CONTROL.md 2a0.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: sweep_gate.py ITEM [ITEM ...]")
    raise SystemExit(gate(tuple(sys.argv[1:])))
