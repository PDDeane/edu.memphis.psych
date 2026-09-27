#!/usr/bin/env python3
"""Does a PORTED check still see the self-test's injection?

WHY THIS EXISTS. The enforcement self-test injects a fault by MUTATING AN
IN-MEMORY table and forking, so the child inherits the mutation copy-on-write.
A ported check that asks the runner to assemble its own payload gets one built
from the FILES ON DISK, which were never mutated -- so the injected fault is
invisible, the check returns clean, and the audit agrees with itself for
entirely the wrong reason.

That is not hypothetical and it was not rare. Measured 2026-09-26, NINE of the
twelve ported checks carrying a self-test case were blind: every one had passed
the four-item port standard, because that standard compares findings on inputs
the porter constructs and never asks whether the audit's own injection still
reaches the rule.

WHY NOT JUST RUN THE SELF-TEST. Because it takes over ninety minutes and
answers this question only as a side effect. This asks it directly, in seconds,
and names the check rather than the case.

WHAT A PASS MEANS. `before` findings, then the injection, then `after`. If
`after` is not larger, the check cannot see its own case: the fetch is reading
somewhere the injection does not reach. The remedy is for python to PASS the
payload it was handed -- or, when python owns only one of the rule's inputs, to
ask `lo_enforce.probe("assemble", ...)` and patch that field.
"""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _cases():
    """(name, check, install, restore) for every ported check with a case.

    THE INJECTIONS ARE THE SELF-TEST'S OWN, copied deliberately rather than
    imported: `equivalence.py` builds them inline inside a 3000-line function,
    and importing that would mean running the audit. A copy that drifts is
    caught by the case failing to fire on the UNPORTED side, which is what the
    `--control` flag is for.
    """
    import copy

    import agreement_app as APP
    import enforcement as ENF
    import paths as _paths
    import forms as H
    import olx_prompts as O

    out = []

    R1 = H.config(ENF._forms()[0])["rubric"]
    dup = sorted(R1.BY_ID)[0]
    out.append(("rubric_items_are_unique", ENF.check_rubric_items_are_unique,
                lambda: R1.ITEMS.append(dict(R1.BY_ID[dup])),
                lambda: R1.ITEMS.pop()))

    # FILLS A BOX GOLD REPORTS AS ABSENT, by patching `_fixture_boxes` -- which
    # is why the delegator keeps python's fetch: `_fixture_cells` is memoised on
    # the SEGMENTATION only, so a patched boxes function is still seen, and a
    # payload rebuilt from the record would not be.
    #
    # THE CELL IS DERIVED, NOT NAMED. Spelling one put a course's item id into
    # this module and the course-data ratchet reported it the same day -- and a
    # named cell also rots the moment that cell's gold changes. The self-test's
    # own injections derive theirs for the same reason; this searches for the
    # first cell the check actually reacts to.
    _real_fb = ENF._fixture_boxes

    def _fill_all(item, pid):
        return {k: (v or "placeholder for a box gold records as empty")
                for k, v in _real_fb(item, pid).items()}

    def _derive_fixture_cell():
        """The first cell that FIRES when its empty boxes are filled."""
        for _h, iid, pid, _raw, _bx in ENF._fixture_cells():
            def one(i=iid, p=pid):
                def f(item, q):
                    bx = dict(_real_fb(item, q))
                    if (item, q) == (i, p):
                        return {k: (v or "placeholder for a box gold "
                                          "records as empty")
                                for k, v in bx.items()}
                    return bx
                return f
            ENF._fixture_boxes = one()
            try:
                if ENF.check_fixture_agrees_with_gold():
                    return one()
            finally:
                ENF._fixture_boxes = _real_fb
        return _fill_all

    _fixture_injection = _derive_fixture_cell()
    out.append(("fixture_agrees_with_gold",
                ENF.check_fixture_agrees_with_gold,
                lambda: setattr(ENF, "_fixture_boxes", _fixture_injection),
                lambda: setattr(ENF, "_fixture_boxes", _real_fb)))

    # A GENERATED PROMPT LINE STOPS REACHING THE SHIPPED HANDOUT. The line is
    # DERIVED, not named: take one the prompt generates and the handout
    # currently carries, then remove it from what `_src` returns. Naming a line
    # would rot the moment the prompt was reworded, and a weaker injection --
    # deleting a single word -- does not fire at all, because the check matches
    # WHOLE lines. Measured: it reported nothing until the whole line went.
    _real_src = O._src
    _drop_line = None
    for _it in sorted(O.ACTION):
        try:
            _want = O.build_web_prompt(_it)
            _src = _real_src(ENF._p7.roots() and __import__("measured")._jobs()[_it]["handout"])
        except Exception:
            continue
        _cand = [l.strip() for l in _want.split("\n")
                 if len(l.strip()) > 40 and "REF:" not in l and "<Ref" not in l
                 and l.strip() in _src]
        if _cand:
            _drop_line = _cand[0]
            break

    if _drop_line is not None:
        out.append(("written_rules_reach_the_shipped_prompt",
                    ENF.check_written_rules_reach_the_shipped_prompt,
                    lambda: setattr(O, "_src", lambda h: _real_src(h).replace(
                        _drop_line, "A LINE THE HANDOUT NO LONGER CARRIES")),
                    lambda: setattr(O, "_src", _real_src)))

    # THE PROMPT STOPS WARNING ABOUT AN EXCLUDED KEY. Patching the generator
    # rather than naming a key: the check reports every excluded key on every
    # item, so what matters is that the WARNING goes, not which key it was.
    _real_bwp = O.build_web_prompt

    def _unwarned(item, *a, **k):
        return _real_bwp(item, *a, **k).replace("DO NOT ANSWER", "please answer")

    out.append(("primitive_conformance",
                ENF.check_primitive_conformance,
                lambda: setattr(O, "build_web_prompt", _unwarned),
                lambda: setattr(O, "build_web_prompt", _real_bwp)))

    # QUOTES A COUNTED PARTICIPANT VERBATIM. The run is taken from a cell's own
    # answer and planted into the PROMPT -- the rubric rule the check reads --
    # which is the direction that makes a leak. A first version planted it back
    # into the CORPUS, where the gram already was, so nothing changed and the
    # check reported clean: this tool caught that, which is what it is for.
    #
    # A RUN FROM THE MIDDLE of the answer, because the opening words are the
    # template sentence many students share and a shared run is filtered as the
    # assignment's own language.
    _leak = None
    for (_iid, _pid), _body in sorted(ENF._corpus_cells().items()):
        _h = next((h for h in ENF._forms()
                   if _iid in {i["id"] for i in H.config(h)["rubric"].ITEMS}), None)
        if _h is None or len(_body.split()) <= 40:
            continue
        if _pid in H.cell_exclusions(_h, _iid):
            continue
        if (_iid, _pid) in ENF.CORPUS_QUOTE_BACKLOG:
            continue
        _spec = H.config(_h)["rubric"].BY_ID.get(_iid) or {}
        _credit = [c for c in (_spec.get("credit") or []) if c.get("what")]
        if not _credit:
            continue
        _leak = (_credit[0], " ".join(_body.split()[12:26]))
        break

    if _leak is not None:
        _slot, _run = _leak
        _saved_rule = _slot.get("rule")

        def _plant():
            _slot["rule"] = f'A response reading "{_run}" counts.'

        def _unplant():
            if _saved_rule is None:
                _slot.pop("rule", None)
            else:
                _slot["rule"] = _saved_rule

        out.append(("rule_examples_are_not_corpus",
                    ENF.check_rule_examples_are_not_corpus, _plant, _unplant))

    # THE INJECTION MUTATES A LIVE ENTRY'S PROSE, which is why the delegator
    # keeps python's fetch: a payload rebuilt from `gold.json` on disk carries
    # the shipped `why`, not this one, and the check reports clean.
    _sus_key = ("NR", 4)
    _sus_real = H.CORRECTED_GOLD[_sus_key]["why"]
    out.append(("no_declaration_cites_a_suspect_cell",
                ENF.check_no_declaration_cites_a_suspect_cell,
                lambda: H.CORRECTED_GOLD[_sus_key].__setitem__(
                    "why", _sus_real + " Compare p3, which gold credits."),
                lambda: H.CORRECTED_GOLD[_sus_key].__setitem__(
                    "why", _sus_real)))

    out.append(("no_cell_is_both_corrected_and_declared",
                ENF.check_no_cell_is_both_corrected_and_declared,
                lambda: H.GOLD_DIVERGENCES.append(
                    {"code": "PROBE", "cells": [("NR", 4)], "why": "injected"}),
                lambda: H.GOLD_DIVERGENCES.pop()))

    real_hs = ENF._handsplit_tables
    out.append(("handsplit_rows_are_disjoint",
                ENF.check_handsplit_rows_are_disjoint,
                lambda: setattr(ENF, "_handsplit_tables", lambda: {
                    "/injected/Q4b.json": {"7": {
                        "bmod_h1_q4b_first":
                            "1) the whole sentence including the modify answer",
                        "bmod_h1_q4b_modify": "the modify answer"}}}),
                lambda: setattr(ENF, "_handsplit_tables", real_hs)))

    cell = next((k for k, v in sorted(APP.CONSENSUS_FIXES.items()) if v), None)
    if cell is not None:
        box = APP.CONSENSUS_FIXES[cell][0][1]
        out.append(("consensus_fixes_are_unique",
                    ENF.check_consensus_fixes_are_unique,
                    lambda: APP.CONSENSUS_FIXES[cell].append(
                        ("set", box, "duplicate")),
                    lambda: APP.CONSENSUS_FIXES[cell].pop()))

    def _dup_source():
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        fh.write('{\n  "Q6/p8": [["slice","state_c1","Q6",0,3,"aaaaaaaaaaaa"]],\n'
                 '  "Q6/p8": [["slice","change_a2","Q6",4,7,"bbbbbbbbbbbb"]]\n}\n')
        fh.close()
        ENF._CONSENSUS_SOURCE = fh.name

    out.append(("consensus_fixes_have_no_duplicate_cells",
                ENF.check_consensus_fixes_have_no_duplicate_cells,
                _dup_source,
                lambda: setattr(ENF, "_CONSENSUS_SOURCE", None)))

    ex = next(((i, p) for i, d in sorted(H.PER_ITEM_EXCLUDE.items())
               for p, e in d.items()
               if isinstance(e, dict) and e.get("expect_error") is not None), None)
    if ex is not None:
        p9 = H.PER_ITEM_EXCLUDE[ex[0]][ex[1]]
        saved_err, saved_why = p9["expect_error"], p9["why"]

        def _prose():
            p9["expect_error"] = None
            p9["why"] = saved_why + " the error here is exactly +2.00."

        def _unprose():
            p9["expect_error"] = saved_err
            p9["why"] = saved_why

        out.append(("exclusion_claims_are_data",
                    ENF.check_exclusion_claims_are_data, _prose, _unprose))

    nk = sorted(O.SLOT_NOTES)[0] if O.SLOT_NOTES else None
    if nk is not None:
        saved_note = O.SLOT_NOTES[nk]
        out.append(("prompt_prose_names_only_offered_verdicts",
                    ENF.check_prompt_prose_names_only_offered_verdicts,
                    lambda: O.SLOT_NOTES.__setitem__(
                        nk, saved_note + " Answer `not_a_type` if unsure."),
                    lambda: O.SLOT_NOTES.__setitem__(nk, saved_note)))

    R1b = H.config(ENF._forms()[0])["rubric"]
    ante = next((i for i, e in sorted(R1b.BY_ID.items())
                 if [c for c in (e.get("credit") or [])
                     if c["what"].startswith("antecedent_") and c.get("codes")]), None)
    if ante is not None:
        slots = [c for c in R1b.BY_ID[ante]["credit"]
                 if c["what"].startswith("antecedent_") and c.get("codes")]
        saved = [(list(c["verdicts"]), dict(c["codes"])) for c in slots]

        def _drop_verdicts():
            for c in slots:
                c["verdicts"] = ["met", "absent"]
                c["codes"] = {"absent": "A_ONLY_ONE"}

        def _restore_verdicts():
            for c, (v, k) in zip(slots, saved):
                c["verdicts"], c["codes"] = v, k

        out.append(("codes_reachable",
                    lambda: ENF.check_codes_reachable(ENF.all_items()),
                    _drop_verdicts, _restore_verdicts))

    out.append(("countable_families_converted",
                lambda: ENF.check_countable_families_converted(ENF.all_items()),
                lambda: ENF.COUNTABLE_EXEMPT.__setitem__(
                    ("2b", "sentence"), "stale on purpose"),
                lambda: ENF.COUNTABLE_EXEMPT.pop(("2b", "sentence"), None)))

    # "a forgiven verdict loses its declaration" -- clears the exemption table.
    real_unch = dict(ENF.UNCHARGED_VERDICTS)

    def _clear_unch():
        ENF.UNCHARGED_VERDICTS.clear()

    def _restore_unch():
        ENF.UNCHARGED_VERDICTS.clear()
        ENF.UNCHARGED_VERDICTS.update(real_unch)

    out.append(("every_failing_verdict_has_a_charge",
                ENF.check_every_failing_verdict_has_a_charge,
                _clear_unch, _restore_unch))

    # "a shared rule names one side's verdict token" -- rewrites `{fail}` in a
    # credit entry's rule, in memory.
    rule_site = next((c for m in (H.config(h)["rubric"] for h in ENF._forms())
                      for it in m.ITEMS for c in (it.get("credit") or [])
                      if "`{fail}`" in (c.get("rule") or "")), None)
    if rule_site is not None:
        saved_rule = rule_site["rule"]
        out.append(("slot_rules_are_vocabulary_neutral",
                    ENF.check_slot_rules_are_vocabulary_neutral,
                    lambda: rule_site.__setitem__(
                        "rule", saved_rule.replace("{fail}", "wrong_kind")),
                    lambda: rule_site.__setitem__("rule", saved_rule)))

    # "a rubric declaration is removed, its attribute is not" -- pops an
    # `expect` rule from BOTH the EXPECT table and the item spec, in memory.
    # ONE CASE, TWO CHECKS: both report under `GENERATED ATTRIBUTE HAS NO
    # DECLARATION`, so both must see it.
    R2 = H.config(ENF._forms()[1])["rubric"]
    exp_item = next((i for i in sorted(getattr(R2, "EXPECT", {}) or {})), None)
    if exp_item is not None:
        real_EXPECT = copy.deepcopy(R2.EXPECT.get(exp_item))
        real_expect = copy.deepcopy((R2.BY_ID.get(exp_item) or {}).get("expect"))

        def _drop_expect():
            R2.EXPECT.pop(exp_item, None)
            (R2.BY_ID.get(exp_item) or {}).pop("expect", None)

        def _restore_expect():
            if real_EXPECT is not None:
                R2.EXPECT[exp_item] = real_EXPECT
            if real_expect is not None:
                R2.BY_ID[exp_item]["expect"] = real_expect

        for name in ("generated_attributes_have_a_declaration",
                     "hand_authored_attrs_still_suppress_something"):
            out.append((name, getattr(ENF, f"check_{name}"),
                        _drop_expect, _restore_expect))

    # "a content file never reaches the build" -- a DISK case: it writes a new
    # .olx into the collection. Unlike every other injection here that is
    # visible to a payload assembled from disk, which is why this one was safe
    # to self-assemble; it is exercised anyway rather than reasoned about.
    probe_olx = _paths.OLX_DIR / "_selftest_provenance.olx"
    out.append(("no_unresolved_reference_reaches_the_page",
                ENF.check_no_unresolved_reference_reaches_the_page,
                lambda: probe_olx.write_text("<Course><Vertical/></Course>\n"),
                lambda: probe_olx.unlink(missing_ok=True)))

    # "a CORRECTED_GOLD entry no longer matches the sheet" -- rewrites one
    # entry's `was` to a value the sheet does not hold, in memory.
    real_cg = dict(H.CORRECTED_GOLD)
    cg_key = ("Q6", 18) if ("Q6", 18) in real_cg else (
        sorted(real_cg)[0] if real_cg else None)
    if cg_key is not None:
        def _drift_cg():
            H.CORRECTED_GOLD[cg_key] = {**real_cg[cg_key], "was": 9.75}

        def _restore_cg():
            H.CORRECTED_GOLD.clear()
            H.CORRECTED_GOLD.update(real_cg)

        out.append(("corrected_gold_matches_the_sheet",
                    ENF.check_corrected_gold_matches_the_sheet,
                    _drift_cg, _restore_cg))

    # "an exclusion outlives the citation that justified it" -- adds a
    # participant no cohort contains to the citation registry, in memory.
    cp = H.FORMS[ENF._forms()[0]].get("cited_participants")
    if cp is not None:
        R1c = H.config(ENF._forms()[0])["rubric"]
        cite_item = sorted(R1c.BY_ID)[0]
        saved_cp = dict(cp)

        def _cite():
            cp[cite_item] = sorted(set(cp.get(cite_item, []) or []) | {99})

        def _uncite():
            cp.clear()
            cp.update(saved_cp)

        out.append(("citations_match_exclusions",
                    ENF.check_citations_match_exclusions, _cite, _uncite))

    R3 = H.config(ENF._forms()[2])["rubric"]
    coded = next((i for i, e in sorted(R3.BY_ID.items())
                  if (e.get("credit") or [{}])[0].get("codes")), None)
    if coded is not None:
        q = R3.BY_ID[coded]["credit"][0]["codes"]
        saved_codes = dict(q)
        out.append(("slot_codes_exist",
                    lambda: ENF.check_slot_codes_exist(ENF.all_items()),
                    lambda: q.__setitem__("absent", "NO_VERDIKT"),
                    lambda: (q.clear(), q.update(saved_codes))))
    return out


def covered_cases() -> tuple[set, set]:
    """(ported checks that carry a self-test case, the ones this tool covers).

    THE GAP THIS CLOSES was real and cost a blind port. `_cases()` is a
    hand-written list, and a check ported AFTER it was written carries its case
    into the suite while this tool says nothing about it -- which is exactly
    what happened to `every_failing_verdict_has_a_charge`: the tool reported
    "every ported check still sees its injection" while that one could not see
    its own. A guard whose population is hand-maintained certifies the checks
    somebody remembered.
    """
    import ast
    import re

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(here, "enforcement.py"), encoding="utf8").read()
    eq = open(os.path.join(here, "equivalence.py"), encoding="utf8").read()
    ported = {f.name for f in ast.parse(src).body
              if isinstance(f, ast.FunctionDef) and f.name.startswith("check_")
              and "lo_enforce.run(" in (ast.get_source_segment(src, f) or "")}
    label = {}
    for m in re.finditer(r"ENF\.(check_\w+)\([^\n]*\n\s*findings\.append\(\(\s*"
                         r"[^,]+,\s*\"([^\"]+)\"", eq):
        label.setdefault(m.group(1), m.group(2))
    wants = set(re.findall(r'want=\s*"([^"]+)"', eq))
    wants |= set(re.findall(r'cases\.append\(\(\s*"[^"]*",\s*\n?\s*"([A-Z][^"]+)"', eq))
    for m in re.finditer(r'(_\w*want\w*) = "([^"]+)"', eq):
        wants.add(m.group(2))
    with_case = {c for c in ported if label.get(c) in wants}
    return with_case, {f"check_{n}" for n, _c, _i, _r in _cases()}


def main() -> int:
    # A LABEL MAY BE SHARED, AND THEN ONE CHECK ANSWERS FOR IT. Two checks
    # report under `GENERATED ATTRIBUTE HAS NO DECLARATION`; the case that
    # removes a rubric declaration is aimed at ONE of them, and demanding the
    # other fire too reports a blindness that is not there. The suite matches a
    # case to its finding by LABEL, so this does too: a label is covered when
    # ANY check reporting it sees the injection.
    import ast
    import re

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    eq = open(os.path.join(here, "equivalence.py"), encoding="utf8").read()
    label_of = {}
    for m in re.finditer(r"ENF\.(check_\w+)\([^\n]*\n\s*findings\.append\(\(\s*"
                         r"[^,]+,\s*\"([^\"]+)\"", eq):
        label_of.setdefault(m.group(1), m.group(2))

    seen: dict = {}
    for name, check, install, restore in _cases():
        before = check()
        install()
        try:
            after = check()
        finally:
            restore()
        ok = len(after) > len(before)
        lab = label_of.get(f"check_{name}", name)
        seen[lab] = seen.get(lab, False) or ok
        print(f"  {name:44} before={len(before):2} after={len(after):2}  "
              f"{'sees it' if ok else 'not this one'}")
    blind = sorted(lab for lab, ok in seen.items() if not ok)
    print()
    with_case, covered = covered_cases()
    missing = sorted(with_case - covered)
    if missing:
        print(f"{len(missing)} ported check(s) carry a self-test case that this "
              f"tool does NOT exercise: {', '.join(n[6:] for n in missing)}")
        print("Add each to `_cases()` with the injection its case performs. A "
              "guard that does not know about a case cannot say it is reached.")
        return 1
    print(f"all {len(with_case)} ported checks carrying a self-test case are "
          f"covered by this tool")
    if blind:
        print(f"{len(blind)} self-test finding(s) that NO ported check can "
              f"see: {', '.join(blind)}")
        print("Each one's python side must pass the payload rather than asking "
              "the runner to assemble it from disk.")
        return 1
    print("every ported check with a self-test case still sees its injection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
