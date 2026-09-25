#!/usr/bin/env python3
"""A slice-bounded edit must not take a slice out of the wrong thing.

WHY THIS MODULE EXISTS. Three times in two days an edit computed as "from this
anchor to the next closing brace / the next definition" swallowed something
between the two ends that nobody was looking at:

  1. Rewriting `GOLD_CODE_KNOWN`'s NR/11 entry with a slice bounded by "the next
     dict key" took the table's closing brace, the comment beneath it, AND
     `GOLD_SLOT_BOUNDS_KNOWN`'s declaration line. The file still parsed. The
     symptom -- one table loading 7 keys instead of 5 -- was NOTICED, called
     unexplained, and moved past. It resurfaced as a NameError in `--preflight`.
  2. The same slice had also taken `GOLD_SLOT_BOUNDS_BUDGET`. Found only when
     preflight was next run, which was after the table had been "restored".
  3. Replacing this package's own probe helpers by index slice took
     `_slot_aliases` and `_OPERANT_GATE` with them. Caught in seconds only
     because the very next command imported the module.

The common shape: the edit is correct about what it MEANT to change, the file
still parses, and what went missing is a NAME nothing in the changed region
mentions. Parsing proves syntax, not survival. So the invariant to enforce is
not "the file parses" but "no definition disappeared that I did not say I was
deleting" -- and it is mechanical, which is the only kind of guard that helps at
2am on the fourth occurrence.

TWO LAYERS, deliberately:

  safe_write()        PREVENTION, at write time. Refuses the write if a
                      top-level definition or method vanishes and was not named
                      in `dropping=`. Use it for every programmatic edit.
  DEFINITIONS.json    DETECTION, at gate time, via
                      `enforcement.check_no_definition_vanished()`. Catches a
                      deletion made by any route -- a plain Write, an editor, a
                      hand-run script -- and catches it at the next gate instead
                      of at the next NameError. Same pattern as
                      DESIGNED_TEXT_SHA.json: an inventory of record, and a
                      deliberate command to change it.

There is no `--regenerate-everything` here, on purpose. An inventory that agrees
with whatever the tree currently says enforces nothing; that is exactly why the
design-sha file has no bulk accept either.
"""
from __future__ import annotations

# THE PACKAGE ROOT ON THE PATH, for the direct-script spelling. `tools/__init__`
# does this for `from tools import ...`, and a file run as `python3
# tools/NAME.py` never executes it -- so the import of a sibling fails at the
# first line that needs one. Both spellings are used, so both are made to work.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import ast
import json
import os
import pathlib

import paths
import sys
import tempfile

# THE PACKAGE ROOT, NOT THIS FILE'S PARENT. `modules()` globs HERE and
# `INVENTORY` resolves against it, so a module that locates itself decides what
# the whole inventory contains. Moving this file into a subdirectory would make it
# glob that subdirectory and look for a DEFINITIONS.json beside itself -- and it
# would NOT error. It would report a clean, tiny, entirely wrong inventory, and
# `check_every_module_is_tracked` and `check_every_definition_is_recorded` would
# both go quiet in the same moment, because both ask this module what the package
# contains. Goal H states that failure in advance; `paths.SCORING` is the fix, and
# it has to land BEFORE anything moves rather than with it.
HERE = paths.SCORING
INVENTORY = HERE / "DEFINITIONS.json"

# Modules whose definitions are inventoried. The whole package: a helper deleted
# out of a one-off script is as capable of silently changing a measurement as one
# deleted out of `measured.py`, and the check costs milliseconds.
# The package is TWO directories now: the analytic machinery at the root and the
# supporting tools beside it. Goal H splits them so a reader can tell what kind of
# thing a file is from where it sits.
TOOLS = "tools"


def modules() -> list:
    """Every module in the package, ROOT AND TOOLS.

    A GLOB THAT MISSES A DIRECTORY IS A LEDGER THAT MISSES ITS MODULES, and this
    one feeds `check_every_module_is_tracked` and `check_every_definition_is_
    recorded`. Moving a file into `tools/` without widening this would take it out
    of both checks silently -- the same shape of failure as the self-locating
    `HERE` that goal H makes this move wait for, one level up.
    """
    return sorted(list(HERE.glob("*.py")) + list((HERE / TOOLS).glob("*.py"))
                  + list(paths.COURSE_FIXTURE.glob("*.py"))
                  # COURSE-SUPPLIED SCORERS, since goal E step 3. Moving
                  # `scorer_oc.py` out of the package to `COURSE_METADATA/
                  # scorers/oc.py` took its six definitions out of BOTH checks
                  # -- exactly the silent failure this docstring warns about, one
                  # directory further out. The scorer is course-supplied but it
                  # is still code this ledger depends on.
                  + list((paths.COURSE_METADATA / "scorers").glob("*.py")))


def definitions(text: str) -> set:
    """Every name this module defines that another module could reference.

    Top-level functions, classes and assignments, plus `Class.method` -- a lost
    method is the same failure one scope down. Names inside a function body are
    deliberately excluded: they are private to it and change constantly.
    """
    out: set = set()
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        raise ValueError(f"does not parse: {e}") from None

    def _targets(node) -> list:
        if isinstance(node, ast.Assign):
            return [t.id for t in node.targets if isinstance(t, ast.Name)]
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return [node.target.id]
        return []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(node.name)
        elif isinstance(node, ast.ClassDef):
            out.add(node.name)
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.add(f"{node.name}.{sub.name}")
                for t in _targets(sub):
                    out.add(f"{node.name}.{t}")
        else:
            out.update(_targets(node))
    return out


def container_key_shapes(text: str) -> dict:
    """For each module-level dict literal, the SHAPES of its keys.

    A shape is ("tuple", n) for a tuple key of length n, or ("name", type) for
    anything else. Returned as {container_name: {shape: count}}.

    WHY SHAPE. A declaration table in this project is keyed consistently --
    `PROSE_ONLY_SLOTS` by (item, slot), `DESIGNED_TEXT` by (item, slot, field),
    `GOLD_CEILINGS` by (handout, item). So a key whose arity differs from every
    other key in the same table is almost always an entry that landed in the
    wrong table, which is the one failure `definitions()` cannot see: nothing is
    dropped, the file parses, and the entry is simply somewhere else.
    """
    import ast

    out = {}
    tree = ast.parse(text)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        val = node.value
        if not isinstance(val, ast.Dict):
            continue
        targets = ([node.target] if isinstance(node, ast.AnnAssign)
                   else node.targets)
        names = [x.id for x in targets if isinstance(x, ast.Name)]
        if not names:
            continue
        shapes = {}
        for k in val.keys:
            if k is None:                      # **spread
                continue
            if isinstance(k, ast.Tuple):
                s = ("tuple", len(k.elts))
            else:
                s = ("other", type(k).__name__)
            shapes[s] = shapes.get(s, 0) + 1
        if shapes:
            out[names[0]] = shapes
    return out


def misplacements(before_text: str, new_text: str) -> list[str]:
    """Entries this edit adds to a table whose keys are shaped differently.

    FOUND THE HARD WAY 2026-09-08: four `("Q4b", slot, "desc"): text` entries
    aimed at `DESIGNED_TEXT` landed in `PROSE_ONLY_SLOTS`, which is keyed by
    two-tuples. The anchor matched an earlier `("Q4b", ` in a different table.
    NOTHING CAUGHT IT: no definition vanished, the file parsed, and the entries
    read back as absent from the table that was supposed to hold them -- so the
    only symptom was a later check quietly reporting nothing.

    `dropping=` guards the mirror case (a slice that takes too much). This
    guards a slice that puts its addition in the wrong place, which is the same
    class from the other end and the one `safe_write` could not see.

    ONLY A NEW INHOMOGENEITY IS REFUSED. A table that already mixes shapes goes
    on mixing them: this must not turn into a global tidiness rule that blocks
    every unrelated write, which is how a guard gets disabled.
    """
    try:
        was = container_key_shapes(before_text)
    except SyntaxError:
        return []
    try:
        now = container_key_shapes(new_text)
    except SyntaxError:
        return []
    out = []
    for name, shapes in now.items():
        if len(shapes) < 2:
            continue                            # homogeneous, nothing to say
        old = was.get(name) or {}
        if len(old) >= 2:
            continue                            # already mixed before this edit
        added = {s: n for s, n in shapes.items() if s not in old}
        if not added:
            continue
        kept = sorted(old) or sorted(shapes)
        out.append(
            f"{name} is keyed by {kept[0]} and this edit adds "
            f"{sorted(added)} to it. A key shaped unlike every other key in the "
            f"same table is usually an entry that landed in the WRONG table -- "
            f"check the anchor. If the mix is intended, pass "
            f"allow_mixed_keys=True")
    return out


def container_entries(text: str) -> dict:
    """{container_name: {key_source: True}} for every module-level dict literal.

    Keys are rendered with `ast.unparse`, so `("Q4b", "a1_kind", "desc")` reads
    back exactly as it appears in the source and can be named in `dropping=`.

    WHY THIS EXISTS ALONGSIDE `definitions()`. That function guards module-level
    NAMES: it catches a slice that eats a whole declaration. It cannot see an
    edit that removes an ENTRY from a declaration table, because the table's
    name survives -- and a table entry is exactly what the declarations in this
    project are made of.

    FOUND 2026-09-08, reverting Q4b's eighth attempt. Four DESIGNED_TEXT entries
    had to go. The cut located each key by character offset and then searched for
    the entry's closing "'," -- but `a1_kind`'s text contains an apostrophe, so
    `repr` had written the value in DOUBLE quotes and the search ran PAST the
    entry into the next one. It would have removed a neighbouring declaration
    silently. It only failed safe because an assert on the NEXT key fired before
    `safe_write` was reached, so nothing was written. That is luck, not a guard.
    """
    import ast

    out = {}
    tree = ast.parse(text)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        targets = ([node.target] if isinstance(node, ast.AnnAssign)
                   else node.targets)
        names = [x.id for x in targets if isinstance(x, ast.Name)]
        if not names:
            continue
        keys = {}
        for k in node.value.keys:
            if k is None:
                continue
            try:
                keys[ast.unparse(k)] = True
            except Exception:
                pass
        if keys:
            out[names[0]] = keys
    return out


def lost_entries(before_text: str, new_text: str, dropping=()) -> list[str]:
    """Declaration-table entries this edit removes and did not declare.

    `dropping=` names them as `CONTAINER[key]`, e.g.
        dropping=['DESIGNED_TEXT[("Q4b", "a1_kind", "desc")]']
    which is the same contract `definitions()` uses one level up: say what you
    mean to remove, and an undeclared removal is refused rather than trusted.
    """
    try:
        was = container_entries(before_text)
        now = container_entries(new_text)
    except SyntaxError:
        return []
    declared = set(dropping)
    out = []
    for name, keys in was.items():
        gone = set(keys) - set(now.get(name) or {})
        for k in sorted(gone):
            if f"{name}[{k}]" in declared or name in declared:
                continue
            out.append(f"{name}[{k}]")
    return out


def duplicate_keys(text: str) -> list[str]:
    """Keys a module-level dict literal defines MORE THAN ONCE.

    A dict literal keeps the LAST occurrence and discards the earlier ones in
    silence. So registering an entry whose key already exists does nothing, and
    nothing says so.

    FOUND 2026-09-08 registering a Q4c candidate: the key
    ("Q4c", "consequence_1", "rule_addition") already held cycle 2's reverted
    habit-head text 280 lines further down. The new entry was inserted at the
    top of DESIGNED_TEXT, the old one won, and reading the value back returned
    the OLD text. Two failures in one: a reverted attempt's design of record
    outliving it, and a new one silently discarded.

    `lost_entries` cannot see this -- nothing is lost, and the key set is
    unchanged -- so it needs its own check.
    """
    import ast
    import collections

    out = []
    for node in ast.parse(text).body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        if not isinstance(node.value, ast.Dict):
            continue
        targets = ([node.target] if isinstance(node, ast.AnnAssign)
                   else node.targets)
        names = [x.id for x in targets if isinstance(x, ast.Name)]
        if not names:
            continue
        seen = collections.Counter()
        for k in node.value.keys:
            if k is None:
                continue
            try:
                seen[ast.unparse(k)] += 1
            except Exception:
                pass
        for key, n in seen.items():
            if n > 1:
                out.append(f"{names[0]}[{key}] is defined {n} times")
    return out


def _string_constants(text: str) -> list:
    """Every string constant in the module, as the PARSER sees them.

    Adjacent string literals are joined by Python at parse time, so a wrapped
    prose field is ONE constant however many source lines it spans. That is what
    makes the comparison in `lost_prose` possible: losing a source line does not
    change the number of constants, it shortens one of them.
    """
    import ast

    out = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def _contiguous_deletion(before: str, after: str) -> str | None:
    """The chunk removed if `after` is `before` with ONE contiguous cut, else None."""
    if len(after) >= len(before):
        return None
    head = 0
    while head < len(after) and before[head] == after[head]:
        head += 1
    tail = 0
    while (tail < len(after) - head
           and before[len(before) - 1 - tail] == after[len(after) - 1 - tail]):
        tail += 1
    cut = before[head:len(before) - tail]
    return cut if before[:head] + cut + before[len(before) - tail:] == before else None


LABEL_MIN = 12          # shorter first arguments are not registry labels


def labelled_calls(text: str) -> dict:
    """Every call whose first argument is a distinctive string -> the callee.

    `_scorer_case("a MAPS table is defined but never attached", ...)` is how a
    selftest case is registered, and it is typical: this codebase names things
    by passing a sentence as the first argument to a registrar. That sentence is
    the thing's identity, and it lives INSIDE a function body.
    """
    out: dict = {}
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        raise ValueError(f"does not parse: {e}") from None
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and node.args):
            continue
        first = node.args[0]
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            continue
        if len(first.value) < LABEL_MIN:
            continue
        fn_name = (node.func.attr if isinstance(node.func, ast.Attribute)
                   else getattr(node.func, "id", None))
        if fn_name:
            out[first.value] = fn_name
    return out


def lost_labels(before_text: str, after_text: str, dropping=()) -> list[str]:
    """A registered, named thing that vanished from inside a function body.

    THE THIRD BLIND SPOT, and the one that cost a check its proof on 2026-09-15.
    `definitions` guards module-level NAMES and deliberately ignores everything
    inside a function body, because those are private and churn. `lost_entries`
    guards declaration-table ENTRIES. `lost_prose` guards LINES INSIDE A STRING.
    None of them sees a CALL disappear from inside a function.

    WHAT HAPPENED. A new selftest case had just been added, registering
    `check_every_rubric_element_is_consumed` -- the case that proves the check
    fires. Minutes later the retirement of a neighbouring check cut a block that
    began one comment ABOVE the new case, and took it. The file parsed, every
    module-level name survived, no table entry moved, no string was cut: all
    four guards clean. The audit kept the new check and lost the only thing that
    proved it could fail, which is the exact condition the retired check had
    been in.

    It was caught by `SELFTEST_EXPECTED`, a ratchet on the COUNT -- 85 built
    against 86 expected. That works only where a count exists. This reports the
    loss by NAME, wherever it happens.

    Declare an intended removal as `call:<the label>`, or any distinctive part
    of it -- the fourth `dropping` prefix, kept distinct for the reason the
    others are: bare names to `definitions`, NAME[key] to `lost_entries`,
    `prose:` to `lost_prose`, `call:` here.
    """
    before, after = labelled_calls(before_text), labelled_calls(after_text)
    declared = tuple(d[len("call:"):] for d in dropping
                     if isinstance(d, str) and d.startswith("call:"))
    out = []
    for label, fn_name in before.items():
        if label in after:
            continue
        if any(d and (d in label or label in d) for d in declared):
            continue
        out.append(
            f"{fn_name}({label[:60]!r}...) vanished from inside a function body "
            f"and was not declared. The parse, the module-level names, the "
            f"table entries and the string fields all survive a cut like this, "
            f"so nothing else reports it. If the removal is intended, pass "
            f"call:<label> in dropping=; if not, the slice took a neighbour")
    return out


def lost_prose(before_text: str, after_text: str, dropping=()) -> list[str]:
    """Prose that vanished from inside a string field, unannounced.

    THE BLIND SPOT THIS CLOSES, demonstrated 2026-09-09. `definitions` guards
    module-level NAMES and `lost_entries` guards declaration-table ENTRIES.
    NEITHER SEES A LINE DISAPPEAR FROM INSIDE A WRAPPED PROSE FIELD -- the file
    parses, every name survives, every table entry survives, and the shipped
    prompt is silently short.

    IT HAD ALREADY HAPPENED AND SHIPPED FOR ELEVEN HOURS. Between 23:16 and 23:37
    on 2026-09-08 an edit aimed at Q1 and Q2 deleted ONE LINE from each of Q4c's
    `consequence_1` and `consequence_2`:

        'CONCURRENCE IS NOT CONSEQUENCE. An entry whose only link to the behaviour '

    leaving both slots shipping a decapitated sentence -- "...what it MEANT as a
    consequence.is that the two happen at the same time -- ...". Tested against
    the guards that existed: definitions 6 before and 6 after, `lost_entries` [],
    `duplicate_keys` [], `misplacements` []. All clean, all blind. Q4c was swept
    against that text the next day, and its p4 -- the one cell whose judgement runs
    through the damaged region -- read wrong_by_median off a corrupted prompt.

    Reports a cut only when the field is otherwise UNCHANGED around it, so a
    rewritten field is not flagged as a loss: the test is `after == before` with
    one contiguous run removed. Declare an intended removal by passing any
    distinctive substring of it in `dropping`.
    """
    import collections

    before = collections.Counter(_string_constants(before_text))
    after = collections.Counter(_string_constants(after_text))
    gone = list((before - after).elements())
    arrived = list((after - before).elements())
    # PROSE DECLARATIONS CARRY A `prose:` PREFIX so the three consumers of
    # `dropping` cannot be confused for one another: bare names belong to
    # `definitions`, NAME[key] to `lost_entries`, and `prose:<substring>` here.
    # Without the prefix the idle check reads a prose substring as a module-level
    # name that failed to vanish and refuses a correct write -- which it did on
    # the first attempt to declare the Q4c concurrence removal.
    declared = tuple(d[len("prose:"):] for d in dropping
                     if isinstance(d, str) and d.startswith("prose:"))
    out = []
    # A PLAUSIBILITY FLOOR, or the pairing invents cuts. Every removed constant is
    # tried against every added one, so a short literal that merely CHANGED can be
    # paired with an unrelated one and reported as a deletion: replacing
    # "apps/server" with "apps/server/src/index.ts" was reported as 11 chars
    # vanishing, because the 11-char original also "contiguously deletes" down to
    # some other short constant. The real case this exists for is a 74-char line
    # lost from a ~1600-char prose field, so require the field to be prose-sized
    # and MOSTLY INTACT -- which is what distinguishes a lost line from a rewrite.
    PROSE_MIN = 120
    KEPT_MIN = 0.5
    for old in gone:
        if len(old) < PROSE_MIN:
            continue
        for new in arrived:
            if len(new) < KEPT_MIN * len(old):
                continue
            cut = _contiguous_deletion(old, new)
            if cut is None or not cut.strip():
                continue
            if any(d and (d in cut or cut.strip() in d) for d in declared):
                continue
            out.append(
                f"{len(cut)} chars vanished from inside a string field and were "
                f"not declared -- {cut.strip()[:90]!r}. The name, the table entry "
                f"and the parse all survive a cut like this, so nothing else "
                f"reports it. If the removal is intended, pass a distinctive "
                f"substring of it in dropping=; if not, the slice took more than "
                f"it was aimed at")
            break
    return out


def safe_write(path, new_text: str, dropping=(),
               allow_mixed_keys: bool = False) -> dict:
    """Write `new_text` to `path` unless a definition would vanish unannounced.

    `dropping` names what this edit intends to remove. Naming something that
    does NOT disappear is also refused -- an intent that did not happen is a
    sign the edit landed somewhere other than where it was aimed, which is the
    very failure this guards.

    Returns {path, added, dropped}. Raises RuntimeError on refusal, with the
    lost names listed: on the real cases those lists read
    `GOLD_SLOT_BOUNDS_KNOWN, GOLD_SLOT_BOUNDS_BUDGET` and
    `_slot_aliases, _OPERANT_GATE`, which is the whole diagnosis in one line.
    """
    p = pathlib.Path(path)
    if p.suffix != ".py":
        # The definition invariant is a Python one. A prose file gets the atomic
        # write and nothing else -- the first version parsed everything handed to
        # it and refused a QUALITY_CONTROL.md edit for "leading zeros in decimal
        # integer literals", which is a section number.
        return _atomic(p, new_text)
    before = definitions(p.read_text()) if p.exists() else set()
    after = definitions(new_text)          # raises if the new text is unparseable
    dropping = set(dropping)
    lost = before - after - dropping
    if lost:
        raise RuntimeError(
            f"REFUSING to write {p.name}: {len(lost)} definition(s) would "
            f"vanish and were not declared -- {', '.join(sorted(lost))}. If the "
            f"removal is intended, pass dropping={sorted(lost)!r}; if not, the "
            f"slice took more than it was aimed at")
    for dup in duplicate_keys(new_text):
        raise RuntimeError(
            f"REFUSING to write {p.name}: {dup}. A dict literal keeps the LAST "
            f"occurrence and discards the earlier ones SILENTLY, so a new entry "
            f"under an existing key does nothing and reads back as the old "
            f"value. Drop the stale entry -- usually a reverted attempt's "
            f"design of record -- or edit it in place.")
    gone = lost_entries(p.read_text() if p.exists() else "", new_text, dropping)
    if gone:
        raise RuntimeError(
            f"REFUSING to write {p.name}: {len(gone)} declaration-table "
            f"entr(ies) would vanish and were not declared -- "
            f"{', '.join(gone[:6])}{' ...' if len(gone) > 6 else ''}. A slice "
            f"that removes a table entry can silently take its NEIGHBOUR: "
            f"`repr` uses double quotes when the value contains an apostrophe, "
            f"so an offset search for the closing \"',\" runs past the entry. "
            f"If the removal is intended, pass dropping={gone!r}; if not, cut on "
            f"line boundaries instead of character offsets")
    if not allow_mixed_keys:
        for bad in misplacements(p.read_text() if p.exists() else "", new_text):
            raise RuntimeError(f"REFUSING to write {p.name}: {bad}")
    for bad in lost_prose(p.read_text() if p.exists() else "", new_text, dropping):
        raise RuntimeError(f"REFUSING to write {p.name}: {bad}")
    for bad in lost_labels(p.read_text() if p.exists() else "", new_text, dropping):
        raise RuntimeError(f"REFUSING to write {p.name}: {bad}")
    # AND THE IDLE CHECK FOR PROSE, for the same reason the one below exists: a
    # declaration that did not happen means the edit landed somewhere other than
    # where it was aimed. Tested by whether the declared text is STILL PRESENT
    # afterwards, which is the prose analogue of "still defined".
    stale_prose = [d for d in dropping
                   if isinstance(d, str) and d.startswith("prose:")
                   and d[len("prose:"):].strip()
                   and d[len("prose:"):] in new_text]
    if stale_prose:
        raise RuntimeError(
            f"REFUSING to write {p.name}: declared dropping "
            f"{', '.join(sorted(stale_prose))}, but that text is STILL PRESENT "
            f"afterwards -- the edit did not land where it was aimed")
    # AND FOR LABELS. "Still registered afterwards" is the call analogue, and it
    # catches the case where a retirement names one case and cuts another.
    after_labels = labelled_calls(new_text)
    stale_calls = [d for d in dropping
                   if isinstance(d, str) and d.startswith("call:")
                   and d[len("call:"):].strip()
                   and any(d[len("call:"):] in lb for lb in after_labels)]
    if stale_calls:
        raise RuntimeError(
            f"REFUSING to write {p.name}: declared dropping "
            f"{', '.join(sorted(stale_calls))}, but that call is STILL "
            f"REGISTERED afterwards -- the edit did not land where it was aimed")
    # THE IDLE CHECK IS ABOUT DEFINITIONS ONLY. `dropping` serves TWO guards --
    # module-level names (this one) and declaration-table entries
    # (`lost_entries`) -- and a table-entry declaration is written NAME[key], a
    # form that can never appear in the definitions set. Testing it here made
    # every correctly-declared entry drop read as "still defined afterwards",
    # which blocked three legitimate writes on 2026-09-08 before the cause was
    # found. Entry declarations are validated by `lost_entries`; exclude them.
    idle = {d for d in dropping
            if "[" not in d and not d.startswith(("prose:", "call:"))
            } - (before - after)
    if idle:
        raise RuntimeError(
            f"REFUSING to write {p.name}: declared dropping "
            f"{', '.join(sorted(idle))}, but {'it' if len(idle) == 1 else 'they'} "
            f"{'is' if len(idle) == 1 else 'are'} still defined afterwards -- the "
            f"edit did not land where it was aimed")
    out = _atomic(p, new_text)
    out.update({"added": sorted(after - before), "dropped": sorted(dropping)})
    return out


def unrecorded() -> list:
    """Definitions the tree defines and the inventory does not record.

    The third gap in the same family: `vanished()` asks whether a RECORDED name
    still exists, `untracked()` whether a MODULE is recorded at all, and this
    whether a module's recorded set is CURRENT. A name outside it cannot be
    reported lost, because nothing knows it was ever there.
    """
    inv = _inventory()
    if not inv:
        return ["DEFINITIONS.json is missing or unreadable"]
    out = []
    for path in modules():
        recorded = inv.get(path.name)
        if recorded is None:
            continue                              # untracked() reports this
        try:
            live = definitions(path.read_text())
        except ValueError:
            continue
        gap = sorted(live - set(recorded))
        if gap:
            out.append(
                f"{path.name}: {len(gap)} definition(s) are defined but not "
                f"recorded -- {', '.join(gap[:4])}"
                + (" ..." if len(gap) > 4 else "")
                + ". Nothing would report them lost. Run "
                  "`python3 tools/editguard.py --backfill`")
    return out


def backfill() -> str:
    """Record every live definition the inventory does not yet know.

    ADDITIVE, like `track_new`, and refusing on the same condition: it will not
    run while a tracked name is already reporting lost, because adding coverage
    is not the moment to be carrying an unexplained loss. It never removes, so
    it cannot launder one.
    """
    standing = vanished()
    if standing:
        return ("REFUSING to backfill while the inventory already reports "
                f"{len(standing)} loss(es). Resolve or accept them first -- "
                f"the first is: {standing[0]}")
    try:
        doc = json.loads(INVENTORY.read_text())
    except Exception as e:
        return f"cannot read {INVENTORY.name}: {e}"
    inv = doc.get("modules")
    if inv is None:
        return f"{INVENTORY.name} has no `modules` map"
    added = 0
    touched = []
    for path in modules():
        recorded = inv.get(path.name)
        if recorded is None:
            continue
        try:
            live = definitions(path.read_text())
        except ValueError as e:
            return f"REFUSING to backfill: {path.name} {e}"
        gap = live - set(recorded)
        if gap:
            inv[path.name] = sorted(set(recorded) | live)
            added += len(gap)
            touched.append(path.name)
    if not added:
        return "every live definition is already recorded -- nothing to add"
    INVENTORY.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return (f"recorded {added} definition(s) across {len(touched)} module(s): "
            + ", ".join(sorted(touched)))


def _atomic(p, text: str) -> dict:
    """Write via tempfile + fsync + replace, for the same reason
    `measured.save()` does: a half-written module that still parses is the worst
    of both worlds."""
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=f".{p.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, p)
    except BaseException:
        pathlib.Path(tmp).unlink(missing_ok=True)
        raise
    return {"path": str(p), "added": [], "dropped": []}


def _inventory() -> dict:
    try:
        return json.loads(INVENTORY.read_text()).get("modules") or {}
    except Exception:
        return {}


def vanished() -> list:
    """Definitions the inventory records and the tree no longer defines.

    Reported by `enforcement.check_no_definition_vanished`. An UNPARSEABLE
    module is reported too, and first: `goals.py` was once left unparseable by an
    edit whose text was written before it was checked, and every downstream
    reader then failed with a confusing error instead of that one.
    """
    inv = _inventory()
    if not inv:
        return ["DEFINITIONS.json is missing or unreadable -- run "
                "`python3 tools/editguard.py --seed` to write the inventory of record"]
    out = []
    live = {}
    for p in modules():
        try:
            live[p.name] = definitions(p.read_text())
        except ValueError as e:
            out.append(f"{p.name}: UNPARSEABLE -- {e}")
    for name in sorted(inv):
        if name not in live:
            if not (HERE / name).exists():
                out.append(f"{name}: the whole MODULE is gone, and the inventory "
                           f"records {len(inv[name])} definition(s) in it")
            continue
        lost = set(inv[name]) - live[name]
        if lost:
            out.append(
                f"{name}: {len(lost)} definition(s) VANISHED -- "
                f"{', '.join(sorted(lost))}. Nothing here says the file is "
                f"broken; it parses. Either the removal was deliberate (accept "
                f"it: `python3 tools/editguard.py --accept {name} <NAME>`) or a slice "
                f"took more than it was aimed at")
    return out


def seed(force: bool = False) -> str:
    if INVENTORY.exists() and not force:
        return f"{INVENTORY.name} already exists -- refusing to overwrite it"
    doc = {"_README": (
        "The definitions of record for this package: top-level names and "
        "Class.method, per module. enforcement.check_no_definition_vanished() "
        "refuses a sweep when a recorded name is no longer defined, which is how "
        "a slice-bounded edit that ate a neighbouring declaration gets caught at "
        "the next gate instead of at the next NameError. Removing a definition "
        "on purpose is fine -- accept it one name at a time with "
        "`python3 tools/editguard.py --accept MODULE NAME`. There is no bulk "
        "regenerate, deliberately: an inventory that agrees with the tree "
        "whatever the tree says enforces nothing."),
        "modules": {}}
    for p in modules():
        try:
            doc["modules"][p.name] = sorted(definitions(p.read_text()))
        except ValueError as e:
            return f"REFUSING to seed: {p.name} {e}"
    INVENTORY.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    n = sum(len(v) for v in doc["modules"].values())
    return f"seeded {INVENTORY.name}: {n} definitions across {len(doc['modules'])} modules"


def accept(module: str, name: str) -> str:
    """Record that `name` was removed from `module` on purpose. One at a time."""
    try:
        doc = json.loads(INVENTORY.read_text())
    except Exception as e:
        return f"cannot read {INVENTORY.name}: {e}"
    names = doc.get("modules", {}).get(module)
    if names is None:
        return f"{module} is not in the inventory"
    if name not in names:
        return f"{module} does not record `{name}` -- nothing to accept"
    live = definitions((HERE / module).read_text()) if (HERE / module).exists() else set()
    if name in live:
        return (f"REFUSING: `{name}` is still defined in {module}. Accepting a "
                f"removal that did not happen would hide the next real one")
    doc["modules"][module] = [n for n in names if n != name]
    INVENTORY.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return f"accepted removal of {module}:{name}"


# Modules deliberately OUTSIDE the inventory, each with the reason. Empty, and
# that is the intended state: the default is tracked, and an exemption has to
# argue for itself the way every other exemption in this package does. It exists
# so that "not tracked" is always a decision on the record rather than the
# absence of one -- which is what it was for 33 modules until 2026-09-23.
UNTRACKED_BY_DESIGN: dict[str, str] = {}


# Definitions that name a course artifact ON PURPOSE, each with the reason.
# §10.7 category 4 says a generic engine has no MODULE named for a question, a
# handout or a course; this is the same rule for the names INSIDE the files, and
# `enforcement.check_no_definition_is_named_for_an_item` reports it.
#
# THE DISTINCTION THAT DECIDES AN ENTRY: a DECLARATION ABOUT one cell may name
# that cell -- it is a statement about that cell and nothing else. A FUNCTION may
# not, once it no longer has anything to do with it. That is why
# `rebuild_gold_1c` was renamed to `rebuild_declared_gold` (it rebuilds whatever
# the rubric declares, and 1c is merely the only item declaring it today) and why
# the entry below stays.
ITEM_NAMED_BY_DESIGN: dict[str, str] = {
    "measured._1C_GATE_CEILING":
        "a gold DECLARATION about one cell, and entitled to name it. Renaming it "
        "would also be a data migration rather than a rename: it is read through "
        "`_gold_declaration` and carried by `gold_export`, so the name is a key "
        "in the gold file.",
}


def item_named() -> list:
    """Definitions whose NAME contains a course item id, minus the declared ones.

    ITEM IDS ONLY, and that is not a shortcut. Running this with
    `course_inventory.NAME_MARKERS` as well returns 79 definitions and nearly all
    are noise: `gold` is a generic term for reference scores (`gold_path`,
    `RAW_GOLD_READERS`, `check_gold_is_read_by_item` ...) and `h1`/`h2`/`h3` name
    handouts, which is course STRUCTURE rather than an item. Those markers were
    written for MODULE names and over-fire on definitions.
    """
    import re

    try:
        import course_inventory
    except Exception as exc:                      # pragma: no cover
        return [f"cannot read the item ids: {type(exc).__name__}: {exc}"]
    ids = {i for i in course_inventory.item_ids()
           if not course_inventory._ambiguous(i)}
    out = []
    for path in modules():
        try:
            names = definitions(path.read_text())
        except ValueError:
            continue
        for n in sorted(names):
            low = n.lower()
            for i in sorted(ids, key=len, reverse=True):
                if not re.search(r"(?:^|_)" + re.escape(i.lower()) + r"(?:_|$)", low):
                    continue
                key = f"{path.stem}.{n}"
                if key in ITEM_NAMED_BY_DESIGN:
                    break
                out.append(
                    f"{path.name}: `{n}` is named for item {i}. A name that carries "
                    f"an item id outlives its reason -- the function it describes "
                    f"changes and the name does not. Rename it for what it does, or "
                    f"declare it in editguard.ITEM_NAMED_BY_DESIGN with why the item "
                    f"belongs in the name")
                break
    return out


def untracked() -> list[str]:
    """Modules on disk that the inventory does not record, and has not excused.

    The COMPLEMENT of `vanished()`, and the reason that one could read clean
    while a third of the package was unwatched: `vanished()` iterates the
    INVENTORY's keys, so a module absent from it cannot report a loss -- it is
    silent, which is indistinguishable from intact. Reported by
    `enforcement.check_every_module_is_tracked`.
    """
    inv = _inventory()
    if not inv:
        return ["DEFINITIONS.json is missing or unreadable -- run "
                "`python3 tools/editguard.py --seed` to write the inventory of record"]
    out = []
    for path in modules():
        if path.name in inv or path.name in UNTRACKED_BY_DESIGN:
            continue
        try:
            n = len(definitions(path.read_text()))
        except ValueError:
            n = -1
        out.append(
            f"{path.name} is not in the inventory"
            + (f" and defines {n} name(s)" if n >= 0 else " and does not parse")
            + " -- nothing would report a definition lost from it. Add it with "
              "`python3 tools/editguard.py --track`, or excuse it in "
              "UNTRACKED_BY_DESIGN with the reason")
    return out


def track_new() -> str:
    """Add modules the inventory does not yet record. Touches no existing entry.

    DELIBERATELY NOT `seed(force=True)`. That rewrites every entry from whatever
    the tree currently says, so it would bless a definition already lost from a
    TRACKED module as though it had never been there -- laundering the exact
    failure the inventory exists to catch. This only ever ADDS keys, and it
    refuses to run at all while any tracked module is already reporting a loss,
    because adding coverage is not the moment to be carrying an unexplained one.
    """
    try:
        doc = json.loads(INVENTORY.read_text())
    except Exception as e:
        return f"cannot read {INVENTORY.name}: {e}"
    inv = doc.get("modules")
    if inv is None:
        return f"{INVENTORY.name} has no `modules` map"
    standing = vanished()
    if standing:
        return ("REFUSING to add modules while the inventory already reports "
                f"{len(standing)} loss(es). Resolve or accept them first -- "
                f"the first is: {standing[0]}")
    added = {}
    for path in modules():
        if path.name in inv or path.name in UNTRACKED_BY_DESIGN:
            continue
        try:
            added[path.name] = sorted(definitions(path.read_text()))
        except ValueError as e:
            return f"REFUSING to add {path.name}: {e}"
    if not added:
        return "every module is already tracked or excused -- nothing to add"
    inv.update(added)
    INVENTORY.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    n = sum(len(v) for v in added.values())
    return (f"tracked {len(added)} new module(s), {n} definition(s): "
            + ", ".join(sorted(added)))


def main(argv: list) -> int:
    if len(argv) >= 2 and argv[1] == "--seed":
        print("  " + seed(force="--force" in argv))
        return 0
    if len(argv) >= 2 and argv[1] == "--track":
        print("  " + track_new())
        return 0
    if len(argv) >= 2 and argv[1] == "--backfill":
        print("  " + backfill())
        return 0
    if len(argv) == 4 and argv[1] == "--accept":
        msg = accept(argv[2], argv[3])
        print("  " + msg)
        return 1 if msg.startswith(("REFUS", "cannot")) else 0
    bad = vanished() + untracked() + unrecorded()
    for b in bad:
        print(f"  {b}")
    print(f"  {len(bad)} finding(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
