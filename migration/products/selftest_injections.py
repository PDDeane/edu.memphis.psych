"""One injection per rubric-reading check that had no selftest case.

WHY THESE EXIST. 06c deletes the rubric modules, and the plan's gate asks that
every check which read them be "demonstrably still firing -- shown by its
selftest case, not by the audit being quiet". Twenty-eight rubric-reading checks
had no case. `check_maps_tables_are_attached` is why that matters: it had become
impossible to fail, its findings had been zero for two stages, and only its case
could tell that apart from a check that keeps passing.

EVERY ONE IS VALIDATED AGAINST THE FULL AUDIT, not against its own check. A case
does not call its check, it calls `enforcement_audit()`, which scores every item
through both engines -- so an injection must leave the rubric valid for all of
that. Thirteen of these needed correcting before they fired at all, each failing
SILENTLY: installed cleanly, changed nothing, and would have entered the suite
as a case proving nothing. One more passed its own probe and then killed the
audit by raising for every caller of `load_action`, which is the exact failure
`migration/stage06b_validate_injections.py` was written for.

Where possible an injection breaks a REGISTRY rather than the scoring path -- an
equal-copy exclusions table, a duplicated rule that scores identically, a
backend nothing selects, .olx copies in a temp directory -- so the audit scores
what it scored before and only the invariant under test is broken.
"""

import handouts as H

INJECTIONS = {}

def inject(check, kind):
    def deco(fn):
        INJECTIONS[check] = (kind, fn)
        return fn
    return deco


@inject("check_rubric_items_are_unique", "RUBRIC ITEMS NOT UNIQUE")
def _items_unique():
    """BY_ID gains an entry no ITEMS id accounts for.

    The id list is left alone on purpose: duplicating an ITEMS entry makes the
    scorer score it twice, which takes the audit down somewhere else entirely.
    """
    mod = H.config(1)["rubric"]
    first = mod.ITEMS[0]["id"]
    def install():
        mod.BY_ID["zz_ghost"] = mod.BY_ID[first]
    def restore():
        mod.BY_ID.pop("zz_ghost", None)
    return install, restore


@inject("check_every_declaration_table_has_a_verifier", "DECLARATION TABLE UNWATCHED")
def _table_unwatched():
    """The registry names a table that does not exist, and gives it no verifier.

    Registry-only: touches no rubric and no scoring path, so the full audit
    scores exactly what it scored before.
    """
    import enforcement as E
    key = "handouts.ZZ_GHOST_TABLE"
    def install():
        E.DECLARATION_TABLES[key] = ("a table nobody has", ())
    def restore():
        E.DECLARATION_TABLES.pop(key, None)
    return install, restore


@inject("check_exclusions_agree", "EXCLUSIONS DIVERGE")
def _exclusions_diverge():
    """A scorer keeps its OWN copy of the exclusions table.

    A COPY, not a different table: the check's point is that an equal copy is
    the dangerous case -- "equal to handouts' today, which is how the last one
    survived -- it will drift". Equal content also means the audit scores the
    same cells, which is what keeps the injection safe to run inside it.
    """
    import agreement as A
    orig = A.PER_ITEM_EXCLUDE
    def install():
        A.PER_ITEM_EXCLUDE = dict(orig)
    def restore():
        A.PER_ITEM_EXCLUDE = orig
    return install, restore


@inject("check_computed_rules_do_not_share_a_key", "COMPUTED RULES SHARE A KEY")
def _rules_share_key():
    """Two `forbid` rules writing one key: the last assignment wins silently.

    A DUPLICATE OF AN EXISTING RULE, not a new one. Both engines assign the
    computed check per rule, so a copy scores identically to the original and
    the audit's numbers do not move -- only the check's invariant is broken.
    """
    import handouts as H
    for h in (1, 2, 3):
        for item in H.config(h)["rubric"].ITEMS:
            for kind in ("forbid", "expect", "equals", "derived"):
                rules = item.get(kind) or []
                if rules and isinstance(rules[0], dict) and rules[0].get("key"):
                    target, k = rules, dict(rules[0])
                    def install(t=target, r=k): t.append(r)
                    def restore(t=target): t.pop()
                    return install, restore
    raise RuntimeError("no computed rule with a key found to duplicate")


@inject("check_prose_only_slots_are_declared", "PROSE-ONLY SLOT UNDECLARED")
def _prose_only_undeclared():
    """The declaration table names a slot the rubric does not have.

    The other direction -- an undeclared prose-only slot -- would need a rubric
    slot rewritten from computable to prose, which changes what the scorer
    scores. This direction is a table-only edit and fires the same check.
    """
    import enforcement as E
    key = ("ZZ_GHOST", "zz_slot")
    tbl = E.PROSE_ONLY_SLOTS
    def install():
        if isinstance(tbl, dict): tbl[key] = "a slot nobody has"
        else: tbl.add(key)
    def restore():
        if isinstance(tbl, dict): tbl.pop(key, None)
        else: tbl.discard(key)
    return install, restore


@inject("check_backend_deviations_declared", "BACKEND DEVIATION UNDECLARED")
def _backend_undeclared():
    """A backend that does not say whether it forwards allow_tools.

    Adds a class rather than editing one: an existing backend is used to score,
    and a new one nothing selects is inert for everything but this check.
    """
    import backends as B
    class ZZGhostBackend:                       # no SUPPORTS_TOOLS, by design
        pass
    def install(): B.ZZGhostBackend = ZZGhostBackend
    def restore(): delattr(B, "ZZGhostBackend")
    return install, restore


@inject("check_citations_match_exclusions", "EXCLUSION UNJUSTIFIED")
def _citation_stale():
    """A participant registered as self-cited whom no prompt actually cites.

    Registry-side, so no prompt text moves and every cell still scores as it
    did. `stale = registered - cited` is what fires.
    """
    from handouts import HANDOUTS
    cfg = HANDOUTS[1]
    reg = cfg.setdefault("cited_participants", {})
    iid = None
    import handouts as H
    for item in H.config(1)["rubric"].ITEMS:
        iid = item["id"]; break
    def install():
        reg.setdefault(iid, [])
        reg[iid] = list(reg.get(iid, [])) + [9999]
    def restore():
        reg[iid] = [x for x in reg.get(iid, []) if x != 9999]
        if not reg[iid]: reg.pop(iid, None)
    return install, restore


@inject("check_no_judging_field_states_what_a_verdict_costs", "JUDGING FIELD STATES WHAT A VERDICT COSTS")
def _field_states_cost():
    """A judging field that tells the grader what the verdict is worth.

    Appended to a `desc`, then removed: the added clause is prose the model
    would read, so it is chosen to be scoring-neutral phrasing that only this
    check's pattern matches.
    """
    import handouts as H
    for h in (1, 2, 3):
        for item in H.config(h)["rubric"].ITEMS:
            for c in item.get("credit") or []:
                if c.get("desc"):
                    orig = c["desc"]
                    def install(cc=c, o=orig): cc["desc"] = o + " This zeroes the item."
                    def restore(cc=c, o=orig): cc["desc"] = o
                    return install, restore
    raise RuntimeError("no credit row with a desc")


@inject("check_unreachable_gold_is_allowed", "UNREACHABLE GOLD PENALISED")
def _unreachable_gold():
    """A scorer file that reports an exact-match rate without the allowance.

    NO REAL FILE IS TOUCHED. The check locates the scorers from
    `os.path.dirname(handouts.__file__)`, so the injection points that at a
    temp directory holding COPIES, one with both accepted call names removed.
    Writing the real `baseline.py` would work too and is exactly what the
    movement guard reads as "the source moved under this run".
    """
    import os, shutil, tempfile, handouts as H
    real = H.__file__
    here = os.path.dirname(real)
    tmp = tempfile.mkdtemp(prefix="inj_gold_")
    for f in ("agreement.py", "agreement_app.py", "baseline.py"):
        src = os.path.join(here, f)
        if os.path.exists(src):
            txt = open(src).read()
            if f == "baseline.py":
                txt = txt.replace("scores_as_exact", "zz_gone_zz").replace("scored_exactly", "zz_gone2_zz")
            open(os.path.join(tmp, f), "w").write(txt)
    def install(): H.__file__ = os.path.join(tmp, "handouts.py")
    def restore():
        H.__file__ = real
        shutil.rmtree(tmp, ignore_errors=True)
    return install, restore


@inject("check_slot_rules_are_vocabulary_neutral", "SLOT RULE NAMES A VERDICT")
def _rule_names_verdict():
    """A per-slot rule that names a verdict word instead of describing the test.

    Appends a clause naming a KNOWN verdict the slot does not offer, which is
    what makes the rule vocabulary-dependent. The rest of the rule is untouched,
    so the model reads the same test.
    """
    import handouts as H
    from slot_vocab import KNOWN_VERDICTS
    word = sorted(KNOWN_VERDICTS)[0]
    for h in (1, 2, 3):
        for item in H.config(h)["rubric"].ITEMS:
            for c in item.get("credit") or []:
                if c.get("rule"):
                    offered = set(c.get("verdicts") or []) | set((c.get("codes") or {}) or {}) | {"met", "absent"}
                    pick = next((w for w in sorted(KNOWN_VERDICTS) if w not in offered), None)
                    if not pick: continue
                    orig = c["rule"]
                    # BACKTICKED: the check matches f"`{v}`", not the bare word.
                    def install(cc=c, o=orig, w=pick): cc["rule"] = o + f" Answer `{w}`."
                    def restore(cc=c, o=orig): cc["rule"] = o
                    return install, restore
    raise RuntimeError("no slot rule available")


@inject("check_rule_examples_are_not_corpus", "PROMPT QUOTES A COUNTED CELL")
def _rule_quotes_corpus():
    """A rule that quotes a cell the item is scored against.

    Takes the quoted words FROM the corpus the check compares against, so the
    injection is guaranteed to be a real hit rather than a lucky string.
    """
    import handouts as H, enforcement as E
    cells = E._corpus_cells()
    if not cells: raise RuntimeError("no corpus cells")
    text = None
    for v in (cells.values() if isinstance(cells, dict) else cells):
        s = v if isinstance(v, str) else (v[0] if v else "")
        if isinstance(s, str) and len(s.split()) >= 8: text = s; break
    if not text: raise RuntimeError("no long corpus cell")
    for h in (1, 2, 3):
        for item in H.config(h)["rubric"].ITEMS:
            for c in item.get("credit") or []:
                if c.get("desc"):
                    orig = c["desc"]
                    def install(cc=c, o=orig, t=text): cc["desc"] = o + " For example: " + t
                    def restore(cc=c, o=orig): cc["desc"] = o
                    return install, restore
    raise RuntimeError("no credit desc")


@inject("check_prose_numbers_match_the_ledger", "PROSE NUMBER CONTRADICTS THE LEDGER")
def _prose_number_wrong():
    """A documented number the ledger contradicts.

    The check delegates entirely to `measured.prose_claims()`, so the injection
    goes there: one extra claim whose stated figure cannot match. Nothing in the
    scoring path reads it.
    """
    import measured as MEAS
    orig = MEAS.prose_claims
    def install():
        MEAS.prose_claims = lambda *a, **k: list(orig(*a, **k)) + [
            "ZZ_GHOST.md says 99 cells are perfect; the ledger records none"]
    def restore():
        MEAS.prose_claims = orig
    return install, restore


@inject("check_engine_mechanisms_are_not_item_dependent", "A MECHANISM VARIES BY ITEM")
def _mechanism_varies():
    """An engine module that branches on a specific item id.

    The check reads the engine SOURCE from disk by module name, so the
    injection adds a module to the list it walks and writes that one file into
    a temp directory -- the real engines are not touched.
    """
    import enforcement as E, tempfile, shutil, pathlib
    import handouts as H
    tmp = tempfile.mkdtemp(prefix="inj_mech_")
    iid = H.config(1)["rubric"].ITEMS[0]["id"]
    ghost = pathlib.Path(tmp) / "zz_ghost_engine.py"
    # A MODULE-LEVEL COLLECTION OF ITEM IDS is what the check looks for -- it
    # walks top-level assignments whose value is a tuple/list/set of constants
    # that are ALL item ids. A branch inside a function is invisible to it.
    ghost.write_text(f'ZZ_GATED_MECHANISM = ({iid!r},)\n')
    orig_mods = E._ENGINE_MODULES
    # AN ABSOLUTE NAME, so the check's `Path(f"{mod}.py")` resolves without a
    # chdir. Changing the working directory would have held for the WHOLE audit
    # and broken every other check that reads a relative path.
    name = str(ghost)[:-3]
    def install():
        E._ENGINE_MODULES = tuple(orig_mods) + (name,)
    def restore():
        E._ENGINE_MODULES = orig_mods
        shutil.rmtree(tmp, ignore_errors=True)
    return install, restore


@inject("check_verdict_paths_drop_excluded_cells", "EXCLUDED CELL REACHES A VERDICT PATH")
def _excluded_reaches_path():
    """A verdict path that prints a cell the exclusions say to drop.

    ON THE CONSUMER, NOT THE TABLE. Adding a cell to `PER_ITEM_EXCLUDE` cannot
    create this contradiction: the readout reads the same table, so the cell
    disappears from both sides at once and the check correctly says nothing.
    The defect being guarded is a path that fails to consult the exclusions, so
    that is what the injection simulates -- one extra line for a cell that IS
    excluded.
    """
    import handouts as H
    import sweep_readout as SR
    tbl = getattr(H, "PER_ITEM_EXCLUDE", None)
    if not tbl: raise RuntimeError("no PER_ITEM_EXCLUDE")
    item = sorted(tbl)[0]
    pid = sorted(k for k in tbl[item] if isinstance(k, int))[0]
    orig = SR.readout
    def install():
        def leaky(it, scores, *a, **k):
            out = orig(it, scores, *a, **k)
            if it == item:
                print(f"p{pid} 12  (injected: an excluded cell on a verdict path)")
            return out
        SR.readout = leaky
    def restore():
        SR.readout = orig
    return install, restore


@inject("check_prompt_prose_names_only_offered_verdicts", "PROMPT ASKS FOR AN IMPOSSIBLE VERDICT")
def _prompt_impossible_verdict():
    """Prompt prose telling the model to answer a verdict the slot cannot emit.

    THE CHECK READS `SLOT_NOTES`, not the rubric guidance -- and only for slots
    with NO rubric `rule`, since a ruled slot is governed elsewhere. The first
    attempt appended to `item["guidance"]`, which this check never looks at, so
    it installed cleanly and proved nothing.
    """
    import olx_prompts as O
    from slot_vocab import KNOWN_VERDICTS
    import enforcement as E
    by_id = {it["id"]: it for it in E.all_items()}
    for item_id, action in sorted(O.ACTION.items()):
        h = O.HANDOUT.get(item_id)
        if h is None: continue
        try:
            spec, defaults = O._slots_attr(h, action)
            choices = O._choices_attr(h, action)
            slots = O.parse_slots(spec, defaults)
        except Exception:
            continue
        rubric = by_id.get(item_id) or {}
        ruled = {c["what"] for c in (rubric.get("credit") or []) if c.get("rule")}
        for sl in slots:
            key = sl["key"]
            if key in ruled: continue
            offered = set(sl["options"] or ())
            if sl.get("picks") is not None:
                offered |= set(choices.get(sl["picks"], []) or ())
            pick = next((v for v in sorted(KNOWN_VERDICTS) if v not in offered), None)
            if not pick: continue
            nk = f"{item_id}:{key}"
            had = nk in O.SLOT_NOTES
            prev = O.SLOT_NOTES.get(nk, "")
            def install(k=nk, p=prev, w=pick):
                O.SLOT_NOTES[k] = p + f" Answer `{w}` when it applies."
            def restore(k=nk, p=prev, h_=had):
                if h_: O.SLOT_NOTES[k] = p
                else: O.SLOT_NOTES.pop(k, None)
            return install, restore
    raise RuntimeError("no ruleless slot with an unoffered verdict")


@inject("check_consensus_spans_are_disjoint", "CONSENSUS SPANS OVERLAP")
def _spans_overlap():
    """Two boxes on one cell holding the same words.

    Injected on `_fixture_cells`, which is what the check walks: one extra
    synthetic cell whose two boxes carry identical text. A real cell is not
    touched, so every score the audit computes is the score it computed before.
    """
    import enforcement as E
    orig = E._fixture_cells
    text = ("the same sentence in two boxes at once, long enough to pass the "
            "ten-character floor the check applies")
    def install():
        def with_ghost(*a, **k):
            yield from orig(*a, **k)
            yield (1, "ZZ_GHOST", 999, text, {"box_a": text, "box_b": text})
        E._fixture_cells = with_ghost
    def restore():
        E._fixture_cells = orig
    return install, restore


@inject("check_scored_slots_are_answered_by_both_engines", "SCORED SLOT ANSWERED BY ONE ENGINE ONLY")
def _one_engine_only():
    """A scored slot the two engines answer under names nothing connects.

    NOT A GHOST SLOT. The first attempt added a pointed slot to a copy of the
    .olx; a slot NEITHER engine answers never reaches the reporting branch,
    which only speaks when one side answers and the other does not. What
    excuses the real ones is the ALIAS table, so removing an alias is the
    injection -- a registry edit that leaves every sheet and every score alone.
    """
    import enforcement as E
    orig = E.ALIAS
    if not orig: raise RuntimeError("ALIAS is empty; nothing to un-alias")
    def install(): E.ALIAS = {}
    def restore(): E.ALIAS = orig
    return install, restore


@inject("check_every_prompt_field_is_designed", "PROMPT FIELD IS NOT THE DESIGNED TEXT")
def _field_not_designed():
    """A prompt field with no entry in the design of record.

    A NEW slot rather than an edited one: editing an existing `desc` changes
    what the model is asked and moves the scoring, while an added credit row
    with no points is inert everywhere except this check's inventory.
    """
    import handouts as H
    for h in (1, 2, 3):
        for item in H.config(h)["rubric"].ITEMS:
            credit = item.get("credit")
            if not credit: continue
            row = {"what": "zz_ghost_slot", "desc": "A field nobody designed.",
                   "reported": True, "pts": None}
            def install(c=credit, r=row): c.append(r)
            def restore(c=credit): 
                if c and c[-1].get("what") == "zz_ghost_slot": c.pop()
            return install, restore
    raise RuntimeError("no item with credit rows")


@inject("check_olx_attributes_are_read", "OLX ATTRIBUTE UNREAD")
def _olx_attribute_unread():
    """An attribute the .olx carries that reaches no scorer.

    The check reads the handout through `olx_prompts.OLX`, so the injection
    points that at COPIES with one extra attribute on a single <LLMAction>.
    Editing the real content would be seen by the build, the movement guard and
    every other check at once; an unknown attribute on a copy is ignored by
    `parse_slots`, so the audit scores exactly what it scored before.
    """
    import olx_prompts as O, pathlib, tempfile, shutil, re
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="inj_attr_"))
    orig_pat = O.OLX
    for h in (1, 2, 3):
        src = pathlib.Path(orig_pat % h)
        if not src.exists(): continue
        txt = src.read_text()
        if h == 1:
            txt = re.sub(r'(<LLMAction\b)', r'\1 zzGhostAttr="1"', txt, count=1)
        (tmp / src.name).write_text(txt)
    new_pat = str(tmp / pathlib.Path(orig_pat).name)
    def install():
        O.OLX = new_pat
    def restore():
        O.OLX = orig_pat
        shutil.rmtree(tmp, ignore_errors=True)
    return install, restore


@inject("check_selectors_govern_something", "SELECTOR GOVERNS NOTHING")
def _selector_governs_nothing():
    """The scorers consult a check no slot sheet emits any more.

    The check reads the SCORER SOURCE for `yes("key")` and compares against what
    the sheets emit. Injected by wrapping the scorer function whose source is
    read, so the name appears in the source text without any slot being removed
    -- the sheets are untouched and every cell scores as before.
    """
    import agreement as A, inspect
    orig = A.score_oc
    def install():
        def score_oc(*a, **k):
            # yes("zz_ghost_check")
            return orig(*a, **k)
        score_oc.__doc__ = 'if yes("zz_ghost_check"): pass'
        A.score_oc = score_oc
    def restore():
        A.score_oc = orig
    return install, restore


@inject("check_rule_fail_tokens_agree", "SLOT RULE FAILS DIFFERENTLY")
def _fail_tokens_differ():
    """`{fail}` renders to a verdict the paper side does not offer.

    The paper token comes from `score._fail_verdict`, so the injection makes
    that return a verdict outside the slot's vocabulary. The rule text and the
    sheets are untouched; only the token the two sides would render differs,
    which is the divergence the check names.
    """
    import score as S
    orig = S._fail_verdict
    def install():
        S._fail_verdict = lambda item, c: "zz_ghost_verdict"
    def restore():
        S._fail_verdict = orig
    return install, restore


@inject("check_blank_collapse_is_gated", "BLANK COLLAPSE UNGATED")
def _blank_collapse_ungated():
    """A blank response and a written one collapse to the same ledger.

    The check compares `derive_ledger` on an empty response against a written
    one and expects the blank to be gated to the item's blank code. Making the
    ledger ignore the response reproduces exactly that, without touching a
    rubric or a sheet -- and it is restored before anything else scores.
    """
    import score as S
    orig = S.derive_ledger
    def install():
        # BOTH SIDES BLANK, not both written. The check fires when the blank
        # code appears for a written answer too, so the ledger has to behave as
        # if every response were empty -- forcing the written case to look
        # written makes the two agree in the harmless direction and proves
        # nothing.
        def flat(item, raw, response=None, *a, **k):
            return orig(item, raw, response="   \n  ", *a, **k)
        S.derive_ledger = flat
    def restore():
        S.derive_ledger = orig
    return install, restore


@inject("check_web_scorer_exercises_its_sheet", "SHEET REACHES NO ARITHMETIC")
def _sheet_no_arithmetic():
    """A sheet that cannot be loaded to probe it.

    SCOPED TO THE CHECK'S OWN CALL, and that is the whole lesson. The first
    version made `load_action` raise for everybody: correct against this check,
    which reports a load failure as a finding, and fatal against the FULL audit,
    where other checks call the same function and the exception escaped and took
    the run down. The 06b validator caught it -- which is what that validator is
    for, and why passing a single-check probe is the weaker claim.

    So the refusal is raised only when this check is on the stack. Everything
    else that loads a sheet during the audit loads it normally.
    """
    import agreement as A, sys
    orig = A.load_action
    calls = {"n": 0}
    WANT = "check_web_scorer_exercises_its_sheet"

    def _asked_by_the_check():
        f = sys._getframe(1)
        for _ in range(12):                     # bounded: this runs per call
            if f is None:
                return False
            if f.f_code.co_name == WANT:
                return True
            f = f.f_back
        return False

    def install():
        def refusing(*a, **k):
            if _asked_by_the_check() and calls["n"] == 0:
                calls["n"] += 1
                raise RuntimeError("injected: this sheet will not load")
            return orig(*a, **k)
        A.load_action = refusing

    def restore():
        A.load_action = orig
        calls["n"] = 0
    return install, restore


@inject("check_single_box_fixtures_are_verbatim", "ONE-BLOCK FIXTURE NOT VERBATIM")
def _fixture_not_verbatim():
    """A one-box fixture that is not what the student wrote.

    Injected on `_fixture_boxes`, which the check reads: one box comes back with
    a character changed. Nothing is written to a fixture file, and the change is
    confined to the call the check makes.
    """
    import enforcement as E
    orig = E._fixture_boxes
    def install():
        def altered(iid, pid, *a, **k):
            boxes = orig(iid, pid, *a, **k)
            if len(boxes) == 1:
                k0 = next(iter(boxes))
                v = boxes[k0]
                if isinstance(v, str) and len(v) > 12:
                    boxes = dict(boxes)
                    boxes[k0] = v[:-1] + ("X" if v[-1] != "X" else "Y")
            return boxes
        E._fixture_boxes = altered
    def restore():
        E._fixture_boxes = orig
    return install, restore


@inject("check_slot_rules_reach_both_prompts", "SLOT RULE OLX ONLY")
def _rule_olx_only():
    """A slot note that reaches the web prompt and not the paper one.

    IT IS THE NOTE'S TEXT THAT HAS TO GO MISSING, not the slot's name. The
    check asks `_note_reaches(note, prompt)` for each side, so renaming a slot
    or dropping a backtick leaves both sides still carrying the note and the
    check correctly says nothing. Here a distinctive run of the note is removed
    from the PAPER prompt only, which is exactly "web only, paper scorer never
    sees it".
    """
    import score as S, olx_prompts as OP
    # AND IT MUST BE A NOTE THE CHECK MEASURES. A note whose slot no item
    # scores has no owner, so the check skips it and the injection is invisible
    # -- which is what the alphabetically-first long note turned out to be. Of
    # the fifteen long notes exactly one currently reaches BOTH prompts on an
    # item that scores its slot; that is the only one whose removal from the
    # paper side can produce "web only".
    import handouts as H, enforcement as E
    notes = getattr(OP, "SLOT_NOTES", {}) or {}
    scored = {}
    for mod in H.rubrics():
        for item in mod.ITEMS:
            for c in item.get("credit") or []:
                scored.setdefault(item["id"], set()).add(c["what"])
    by_id = {it["id"]: it for it in E.all_items()}
    pick = None
    for key, note in sorted(notes.items()):
        if len(note) <= 220: continue
        item_id, _, slot = key.partition(":")
        if not slot: item_id, slot = None, key
        owners = [item_id] if item_id and item_id in scored else [i for i, sl in scored.items() if slot in sl]
        if not owners: continue
        o = sorted(owners)[0]
        try:
            web = OP.build_web_prompt(o)
            paper = S.build_prompt(by_id[o], "STUDENT RESPONSE", {}, None)
        except Exception:
            continue
        if E._note_reaches(note, web) and E._note_reaches(note, paper):
            pick = " ".join(note.split()[:8]); break
    if not pick: raise RuntimeError("no owned note reaching both prompts")
    # ACROSS WHITESPACE. `_note_reaches` normalises before matching, but the
    # prompt itself is WRAPPED -- so a literal replace of the note's words with
    # single spaces finds nothing and removes nothing, which is why the first
    # version installed cleanly and changed neither side.
    import re as _re
    rx = _re.compile(r"\s+".join(_re.escape(w) for w in pick.split()))
    orig = S.build_prompt
    def install():
        def thinner(*a, **k):
            out = orig(*a, **k)
            return rx.sub("", out) if isinstance(out, str) else out
        S.build_prompt = thinner
    def restore():
        S.build_prompt = orig
    return install, restore


@inject("check_fixture_covers_the_response", "FIXTURE DROPS RESPONSE TEXT")
def _fixture_drops_text():
    """The backlog names a cell that no longer has unassigned text.

    THE BACKLOG SIDE, not the fixture side. Making a real cell drop text would
    mean altering a fixture the scorers read, and the check's other branch is
    just as much its contract: an entry that has been fixed and not removed is
    a record describing a defect nobody has.
    """
    import enforcement as E
    tbl = E.FIXTURE_GAP_BACKLOG
    key = ("ZZ_GHOST", 999)
    def install():
        if isinstance(tbl, dict): tbl[key] = "a gap nobody has"
        else: tbl.add(key)
    def restore():
        if isinstance(tbl, dict): tbl.pop(key, None)
        else: tbl.discard(key)
    return install, restore


@inject("check_weighted_slots_are_scored", "WEIGHTED SLOT UNSCORED")
def _weighted_unscored():
    """A pointed slot the harness never names, so its verdict is ignored.

    The check reads the SOURCE of `score_oc` and `score_oc_cadence` for slot
    names, so wrapping them with thin functions removes the names from what it
    reads while the scoring itself still runs through the originals -- the
    audit's numbers do not move, only the check's view of what is named.
    """
    import agreement as A
    o1, o2 = A.score_oc, A.score_oc_cadence
    def install():
        def score_oc(*a, **k): return o1(*a, **k)
        def score_oc_cadence(*a, **k): return o2(*a, **k)
        A.score_oc, A.score_oc_cadence = score_oc, score_oc_cadence
    def restore():
        A.score_oc, A.score_oc_cadence = o1, o2
    return install, restore


@inject("check_mapped_slots_agree_with_their_map", "RECORDED VERDICT DISAGREES WITH ITS MAP")
def _map_disagrees():
    """The map computes a verdict the artifacts recorded differently.

    The check tallies RECORDED verdicts against what MAPS computes for the pick
    that was recorded with them, so the injection flips what the map computes
    and leaves every artifact alone. Restored immediately: a map is rubric
    CONTENT and the scorers read it live.
    """
    import enforcement as E
    specs = E._maps_specs()
    if not specs: raise RuntimeError("no map specs")
    for item, mod, s in specs:
        pairs = s.get("pairs") or []
        if not pairs: continue
        pair = pairs[0]
        orig = pair.get("verdict")
        if not orig: continue
        flipped = "absent" if orig != "absent" else "met"
        def install(p=pair, f=flipped): p["verdict"] = f
        def restore(p=pair, o=orig): p["verdict"] = o
        return install, restore
    raise RuntimeError("no map pair with a verdict")
