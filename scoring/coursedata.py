#!/usr/bin/env python3
"""The one module that owns the course file. B1a.

WHY ONE MODULE. Every fact about this course reaches the engine through here, so
there is one place that knows the file's shape and one place to change when it
changes.

THE GROUP BOUNDARY IS A MECHANISM, NOT A RULE (§9.2a). B2a puts rubric facts and
prompt-generator hints on the SAME item entry, so the only thing keeping them
apart is this module. "No accessor returns a raw entry" cannot be enforced by
intent -- Python has no private data, and an accessor handing back the inner dict
makes `rubric_for(item)["slot_notes"]` work while appearing to honour the
boundary. So every accessor returns a COPY containing ONLY the fields of the group
asked for. A caller cannot reach the other group because it was never handed it.

COPIES ARE REQUIRED BECAUSE THIS CODE MUTATES. Not hygiene: `enforcement_selftest`
does `rubric_h1.BY_ID["Q6"].pop("cover")` and restores it, and `_drop_dealt` pops
from `JOBS`. Handing out shared dicts would let one caller's injection corrupt
every later reader in the same process -- and the self-test is built on doing
exactly that.

LOADED ONCE PER PROCESS, NEVER RE-READ. 149 enforcement checks plus a sweep call
these constantly, and re-deriving a ~220KB file per call is not viable. A cache
that watched for changes would reintroduce staleness this project has already paid
for -- a dev server serving fresh content from stale code cost 19 observations. A
process that outlives an edit is a process to restart.

GOLD LOADS LAZILY. The rubric is in the repo and `rubric_for()` has no reason to
need gold, which lives outside it under $COURSE_DATA (C1b). Someone with the repo
and not the data keeps the whole rubric side; only a gold call fails, and it says
which variable is unset and which path was tried.
"""
from __future__ import annotations

import copy
import json
import os
import threading

SCHEMA_VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# DERIVATIONS — moved here from `rubric_export.py` on 2026-09-18, and living here
# alone. The export decides what to DROP; this module REBUILDS it. Those are one
# question asked from two sides, and two implementations that must agree is the
# defect T5.1 had to be redesigned to avoid.
#
# A2a's progress meter: §9.0 called twelve names derived. Every entry added here
# lets the export drop one more value on its next run, with T5.1 proving the JSON
# still reproduces the modules. Two of twelve today.
# ---------------------------------------------------------------------------
def _cond_items(pool: list, cond: str) -> tuple:
    """The items declaring one condition, IN RUBRIC ORDER.

    The `*_ITEMS` selectors the modules carried are exactly this: "the items that
    declare X". They were unreachable from the component only because its reader
    recovered five named booleans out of twelve conditions, so the other seven
    sets had nowhere to come from.

    ORDER IS NOT CONTENT HERE, checked rather than assumed: every consumer takes
    membership, `score.py` re-exports them without indexing, and
    `check_selectors_govern_something` reads the module's own `vars`. The authored
    tuples were in module order and these are in rubric order; two of them differ.
    """
    return tuple(it["id"] for it in pool if cond in (it.get("conditions") or []))


def _field_table(pool: list, field: str) -> dict:
    """`{item id: value}` for one per-item rubric field, for the items that carry
    it. An item that omits the field is ABSENT, not present-and-empty."""
    return {it["id"]: copy.deepcopy(it[field]) for it in pool if field in it}


# WHAT THE READER CAN REBUILD FROM THE COMPONENT. Every name here was a
# module-level table the export carried into `handouts[h].authored` when the
# rubric modules were deleted; each is now read from `bmod_rubric.olx`, where it
# was already sitting, because the export carried a SECOND COPY of data the
# component holds.
#
# AN EMPTY RESULT MEANS "NOT THIS HANDOUT", and `derived` treats it as absent
# rather than as an answer. Handout 1 has no `OC_GATES`, and before these
# derivations existed it raised AttributeError through `_RubricView.__getattr__`
# -- which `getattr(rub, "OC_GATES", {})` call sites rely on. A derivation that
# returned `{}` for every handout would silently convert that into a present,
# empty table.
DERIVATIONS = {
    "BY_ID": lambda items: {it["id"]: it for it in items},
    "TOTAL": lambda items: sum(it["max"] for it in items),
    "SLOT_SPEC": lambda items: {
        i: v for i, v in _slots().items() if i in {x["id"] for x in items}},
    "MAPS": lambda items: _field_table(items, "maps"),
    "FORBID": lambda items: _field_table(items, "forbid"),
    "OC_GATES": lambda items: _field_table(items, "oc_gates"),
    "OC_FRAME": lambda items: _oc_frame(items),
    "AVOIDANCE_SCORES": lambda items: _cond_items(items, "avoidance_scores"),
    "MOVE_PICK_ITEMS": lambda items: _cond_items(items, "move_pick"),
    "READS_UTB_CHOICE": lambda items: _cond_items(items, "reads_utb_choice"),
    "BARRIER_PICK_ITEMS": lambda items: _cond_items(items, "barrier_pick"),
    "CADENCE_BARRIER_ITEMS": lambda items: _cond_items(items, "cadence_barrier"),
    "CONTINGENCY_GATE_ITEMS": lambda items: _cond_items(items, "contingency_gate"),
    "POLARITY_GATE_ITEMS": lambda items: _cond_items(items, "polarity_gate"),
    "TYPE_MATCH_ITEMS": lambda items: _cond_items(items, "type_match"),
    "REQUIRED_MOVE": lambda items: {it["id"]: it["required_move"]
                                    for it in items if "required_move" in it},
    "SLOT_OPTIONS": lambda items: _choices(items),
}


def _slots() -> dict:
    import rubric_component

    return rubric_component.as_view_slots()


def _choices(items: list) -> dict:
    """The declared menus, for the handout that uses them. Only handout 2 carries
    any, and an empty result reads as absent -- see DERIVATIONS."""
    import rubric_component

    if not any("cadence" in (it.get("conditions") or []) or it.get("cadence")
               for it in items):
        return {}
    return rubric_component.as_view_choices()


def _oc_frame(items: list) -> str:
    """The shared frame, for the handout that uses it. Empty elsewhere, which
    `derived` reads as absent -- handouts 1 and 3 never carried one."""
    import rubric_component

    if not any("cadence" in (it.get("conditions") or []) or it.get("cadence")
               for it in items):
        return ""
    return rubric_component.as_view_frame("oc_frame")

# Which group each item field belongs to (§9.2a obligation 1). GENERATOR is empty
# until Stage 4 brings `olx_prompts.py`'s tables across under B2a -- and that
# emptiness is the reason T2.2's check cannot prove anything yet, which T2.2's own
# design says out loud rather than letting the check pass while vacuous.
#
# SINCE 3D THESE NAMES ARE NOT COURSE-FILE FIELDS. They were deleted from
# `course.json`'s `items[]` when the rubric became a component, and this set is no
# longer a SELECTOR over course entries -- `_group(entry, RUBRIC_FIELDS)` has no
# callers left, and only GENERATOR_FIELDS is still selected with.
#
# IT IS KEPT WHOLE, and deliberately. It is the rubric's field VOCABULARY, which
# is what its two remaining readers want: `property_ratchet` scans for these names
# as subscripts, and `course_schema` classifies a field by which group declares it
# -- now over the component's rows AND the course file's, since the fields live on
# different sides of that split. Trimming it to the two names left in `items[]`
# would have shrunk the ratchet's vocabulary and let real growth hide inside it.
RUBRIC_FIELDS = {
    "id", "handout", "label", "max", "increment", "question", "guidance",
    "context", "credit", "deductions", "counts", "derive_from_credit",
    "derive_from_criteria", "unreachable_codes", "blank_code", "expected_type",
    "forbid", "equals", "onlyif", "expect", "maps", "cadence", "oc_gates",
    "derived", "reads_utb_choice", "requires", "cover", "move_pick",
    "avoidance_scores", "graph_item",
    # THE CONDITIONS THEMSELVES, and one attribute recovered from the rubric that
    # the modules carried as a table. `conditions` is the set the five named
    # booleans above are a hand-kept subset of -- exposing it is what let the
    # seven `*_ITEMS` selectors be DERIVED instead of carried. `required_move` is
    # `rubric_h2.REQUIRED_MOVE`, which had no per-item home until it was written
    # as one.
    "conditions", "required_move",
    # SINCE F2: the item's gold cannot be taken from the sheet total and must be
    # REBUILT from the grader's itemised deductions. An item property, so it is
    # declared on the item -- `handouts.rebuild_gold_from_comment` reads the
    # arithmetic from the same rubric entry, and the two analytic wrappers that
    # used to name their item now find it by this flag instead.
    "gold_from_deductions",
    # SINCE 3B: what the item is ASKED THROUGH, and which rule scores it. They
    # were `declaration_source.BLOCKS` until then, where the first of them was a
    # second copy of `prompt_action`. RUBRIC and not GENERATOR because the engine
    # reads them through the rubric view like every other field here.
    # `family` joins them at 4a: which pattern an item was built from, which
    # was `declaration_source.SLOT_STRUCTURE_FAMILIES` naming eight item ids.
    "asks", "grading", "family",
}
# STAGE 4, olx_prompts.py's item-keyed tables (B2a: generator fields live on the
# item entry). Every name is PREFIXED `prompt_`, and that is not decoration:
# `CONTEXT` would land as `context`, which RUBRIC_FIELDS already uses for a
# different thing, and §9.2a forbids a field naming two groups. The prefix also
# says what the field is FOR -- these are inputs to prompt generation, not
# scoring rules.
GENERATOR_FIELDS: set[str] = {
    # `prompt_action` LEFT THIS SET AT 4A. It named the component an item is
    # asked through, which is `<Item asks=...>` in the rubric -- one fact that
    # was written in both places and tied by nothing.
    "prompt_response",       # RESPONSE
    "prompt_context",        # CONTEXT
    "prompt_sheet_only",     # SHEET_ONLY
    "prompt_evidence",       # EVIDENCE
    "prompt_omit_guidance",  # OMIT_GUIDANCE
    "prompt_match_def",      # MATCH_DEF
    "prompt_notes",          # ITEM_NOTES
    "prompt_notes_why",      # ITEM_NOTES_WHY
}

_LOCK = threading.Lock()
_DOC = None
_GOLD = None


def course_path() -> str:
    return os.environ.get("COURSE_FILE") or os.path.join(
        HERE, "..", "courses", "edu.memphis.psych", "course.json")


def _load() -> dict:
    global _DOC
    with _LOCK:
        if _DOC is None:
            path = os.path.abspath(course_path())
            if not os.path.exists(path):
                raise SystemExit(
                    f"coursedata: no course file at {path}. Set COURSE_FILE, or "
                    f"generate one with rubric_export.py. Reading an ABSENT course "
                    f"as an empty one would report every item missing, which is "
                    f"not the same as a course with no items.")
            doc = json.load(open(path))
            if doc.get("schema_version") != SCHEMA_VERSION:
                raise SystemExit(
                    f"coursedata: {path} is schema_version "
                    f"{doc.get('schema_version')!r}, this reader speaks "
                    f"{SCHEMA_VERSION}. Refusing rather than reading a shape it "
                    f"may misunderstand.")
            _DOC = doc
    return _DOC


def _detag(x):
    """Undo the export's tagging: `__tuple__` -> a tuple, `__dict__` -> a dict.

    The counterpart of `rubric_export._jsonable`'s tagging. Without it a tuple
    survives a round trip as a list, which is a shape change consumers do not
    expect and behavioural tests need not notice.

    `__dict__` WAS MISSING HERE and its only inverse lived inside
    `gold_export.round_trip`, as a local function. That was survivable exactly as
    long as nothing but the exporter read a tagged dict: the course file has no
    `__dict__` in it, because all seven of its declarations are string-keyed, so
    `declaration()` never met one. Gold does -- `PER_ITEM_EXCLUDE` nests
    participant ids two levels down -- and the tag reached a consumer the moment
    gold got a reader of its own. A decoder that inverts only some of what the
    encoder writes is the same defect as no decoder at all, found later.
    """
    if isinstance(x, dict):
        if set(x) == {"__tuple__"}:
            return tuple(_detag(v) for v in x["__tuple__"])
        if set(x) == {"__frozenset__"}:
            # A frozenset key: see `rubric_export._key`. Sorted on the way out,
            # unordered again on the way back, which is what it always was.
            return frozenset(_detag(v) for v in x["__frozenset__"])
        if set(x) == {"__dict__"}:
            # KEYS GO THROUGH `_detag` TOO. This tag exists because the key was
            # not a string -- a participant id, or a (item, cell) tuple -- so
            # decoding the value and leaving the key encoded would restore the
            # half that was never the problem.
            return {_detag(k): _detag(v) for k, v in x["__dict__"]}
        return {k: _detag(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_detag(v) for v in x]
    return x


def _group(entry: dict, fields: set[str]) -> dict:
    """A COPY holding only this group's fields. The boundary, made of glass."""
    return _detag(copy.deepcopy({k: v for k, v in entry.items() if k in fields}))


def _rubric_rows() -> list[dict]:
    """Every item's rubric fields, from the COMPONENT, in rubric order.

    THE ONE PLACE THE RUBRIC IS READ. `items()`, `rubric_for()` and `derived()`'s
    pool all come through here, so there is exactly one answer to "where does a
    rubric field come from" and exactly one place to change when the artifact it
    reads changes.

    IT RAISES WHEN THE COMPONENT IS UNREADABLE, and that is the whole design.
    Until 3d this fell back to `course.json`'s `items[]`, which was safe only
    while those fields were still there and proven identical. They are gone, so a
    fallback would return rows with no rubric on them -- every gate unsatisfied,
    every deduction absent, every check comparing nothing and passing. A raise is
    the only honest answer, and the failure it replaces is the exact vacuity trap
    this project has hit before.
    """
    import rubric_component
    # THE EXPANDED, UNRESOLVED ARTIFACT -- not the authored file and not the
    # served one. `rubric_component.expanded_path` carries why each of the other
    # two is wrong for this reader. It is a BUILD PRODUCT, so scoring now depends
    # on a build having run, which it did not before: that is the consequence
    # RUBRIC_MIGRATION_PLAN's END STATE accepted when it named this artifact
    # as owed.
    rows = rubric_component.as_view_items(rubric_component.expanded_path())
    if not rows:
        raise RuntimeError(
            f"coursedata: the rubric component at "
            f"{rubric_component.expanded_path()} yielded no items. The rubric "
            f"fields are no longer in course.json, so there is nothing to fall "
            f"back to -- fix the component rather than the reader.")
    # `handout` IS JOINED FROM THE COURSE FILE, not carried by the rubric.
    # `Item`'s schema refuses the attribute, and rightly: which handout an item
    # belongs to is course structure. `handouts.config` selects on it before
    # serving, so it has to be here.
    where = {str(it.get("id")): it.get("handout") for it in _load()["items"]}
    for r in rows:
        h = where.get(str(r.get("id")))
        if h is not None:
            r["handout"] = h
    return rows


def items() -> list[dict]:
    """Every item, rubric fields only, in rubric order -- from the COMPONENT.

    THE RUBRIC LIVES IN THE CONTENT NOW, as a `<Rubric>` the course links beside
    the three handouts. Everything else keeps its spelling:
    `handouts.config(h)["rubric"]` still serves the view, and the 102 call sites
    across 18 modules are untouched. The CHANNEL is converted, not the callers --
    the same move that let Stage 5 delete the modules without breaking a site.

    IT READS THE AUTHORED FILE, NOT THE BUILD'S STAGED COPY, and the difference is
    not stylistic. The staged copy has its corpus references RESOLVED, and
    `olx_prompts` writes this prose back into the shipped `.olx` -- so feeding it
    resolved text would replace every `{{corpus:...}}` with the span it protects
    and undo the scrub, in a public repository, silently. Measured 2026-09-22:
    pointing this function at the staged copy made all three handouts read OUT OF
    DATE, and the diff was the reference replaced by its expansion.
    `rubric_component.authored_path` carries the full reasoning.

    SCORING THEREFORE DOES NOT YET DEPEND ON A BUILD HAVING RUN. It will: the
    artifact this should read is EXPANDED BUT UNRESOLVED, which is neither the
    authored file nor `.stage/content` and does not exist yet. The authored file
    serves today only because nothing uses `<ItemTemplate>` -- a template landing
    before that build step is what `check_the_staged_rubric_is_current` watches
    for, and it is the one piece of build work hand-authoring still owes.
    """
    return _rubric_rows()


def rubric_for(item_id: str) -> dict:
    """One item's RUBRIC fields. Never the raw entry, never generator fields.

    THROUGH THE COMPONENT, like `items()`. Until 3d this read `course.json`'s
    `items[]` directly; with the rubric fields deleted from there it would have
    returned `{}` for every item and raised nothing -- the quiet failure 3d's
    plan names, and the reason both readers now share `_rubric_rows()`.
    """
    for it in _rubric_rows():
        if str(it.get("id")) == str(item_id):
            return it
    raise KeyError(f"coursedata: no item {item_id!r} in the rubric component")


def generator_for(item_id: str) -> dict:
    """One item's GENERATOR fields. Empty until Stage 4 — see GENERATOR_FIELDS."""
    for it in _load()["items"]:
        if str(it.get("id")) == str(item_id):
            return _group(it, GENERATOR_FIELDS)
    raise KeyError(f"coursedata: no item {item_id!r} in {course_path()}")


def generator_items() -> dict[str, dict]:
    """{item_id: generator fields}. KEYED BY ID, so `id` is not a field.

    `items()` returns a list because rubric order matters. This returns a dict
    because a generator table is looked up by item and has no order of its own --
    and because keying by id keeps `id` out of the VALUE, which matters under
    §9.2a: a field may name only one group, and `id` is the key both groups are
    reached by rather than a member of either.
    """
    return {str(it["id"]): _group(it, GENERATOR_FIELDS)
            for it in _load()["items"]}


def gradable_blocks() -> dict:
    """`{handout: {component id: {item, olx, kind}}}` -- DERIVED from the rubric.

    IT WAS A DECLARATION UNTIL 3B, and the declaration said the same thing twice:
    its component-to-item mapping agreed with that item's `prompt_action` on 23 of
    23 LLM items, with no check tying them. `<Item asks=...>` now carries the link
    once and this rebuilds the shape its ten readers expect.

    THE THREE SYNTHETIC KEYS are items scored without a component of their own --
    deterministic items, which have a grading rule and nothing on the page to ask.
    Their key is a name, not an id, and `olx` is None because there is no file to
    point at; that is exactly what the declaration held for them too.

    `olx` follows the handout, which is how the content is laid out: handout N is
    `bmod_handoutN.olx`. Proven against the declaration on all 26 entries before
    it was deleted, not assumed.
    """
    out: dict = {}
    for it in items():
        iid = str(it.get("id"))
        handout, grading = it.get("handout"), it.get("grading")
        if handout is None or not grading:
            continue
        asks = it.get("asks")
        out.setdefault(handout, {})[asks or f"_{iid.lower()}_deterministic"] = {
            "item": iid,
            "olx": f"bmod_handout{handout}.olx" if asks else None,
            "kind": grading,
        }
    return out


def slot_structure_families() -> dict:
    """`{family: (item id, ...)}` -- DERIVED from the rubric's `<Item family=...>`.

    Items built from ONE pattern share slot NAMES, so those names must mean the
    same thing across the family. That is a fact about each item, and it was a
    table in `declaration_source.py` naming eight item ids -- course content in
    analytic machinery, which is the embedding this migration removes.

    ORDER IS PRESERVED because the rubric's order is, and the check that reads
    this compares siblings pairwise; a reordering would change which pair is
    reported first and make a stable finding look like a new one.
    """
    out: dict = {}
    for it in items():
        fam = it.get("family")
        if fam:
            out.setdefault(fam, []).append(str(it.get("id")))
    return {k: tuple(v) for k, v in out.items()}


def declaration(name: str) -> dict:
    """A scoring declaration table, with its TUPLE KEYS restored.

    The file holds `[[key, value], ...]` because six of the seven tables are
    keyed by tuples and JSON has string keys only. A key stored as a LIST comes
    back as the tuple it was: joining the parts with a separator would have been
    lossless only until a part contained the separator.
    """
    raw = _load().get("declarations", {}).get(name)
    if raw is None:
        raise KeyError(
            f"coursedata: no declaration {name!r} in {course_path()}. If it is a "
            f"new table, the export must carry it; if it was removed, the reader "
            f"of it must go too.")
    # THE KEY GOES THROUGH `_detag` TOO, not just the value. A key part can be
    # tagged -- `PROBE_UNREACHABLE_PAIRS` is keyed by (item, frozenset) and the
    # frozenset reaches the file as `{"__frozenset__": [...]}` -- and decoding
    # only the value would hand back a tuple with a raw dict inside it, which is
    # unhashable in some shapes and simply wrong in the rest. The same omission
    # existed on the gold side for `__dict__` and was found the same way: by a
    # key that did not look up.
    return {_detag_key(k): _detag(copy.deepcopy(v)) for k, v in raw}


def _detag_key(k):
    """One stored key, restored: a list becomes a tuple, tags are inverted."""
    if isinstance(k, list):
        return tuple(_detag_key(x) for x in k)
    return _detag(k)


def course_id() -> str:
    """This course's id, as the file declares it. An accessor, not a raw read.

    Added because `agreement_app` reached `_load()["course"]` to recompose job
    namespaces, and `check_course_schema_is_complete` caught it -- the THIRD time
    that raw-entry escape has been flagged, after `olx_prompts` and the
    generator-value path. The escape keeps recurring because `_load()` is right
    there and returns everything; that is exactly why the check exists.
    """
    return _load().get("course")


def generator_value(name: str):
    """A course-level generator value, by name. An ACCESSOR, not a raw entry.

    Added because `olx_prompts` reached `coursedata._load()["generator"]`
    directly and `check_course_schema_is_complete` caught it -- the raw-entry
    escape its Part B was written for, found on the first module to try it. The
    escape matters because a caller holding the whole document can read anything
    in it, so the group boundary stops meaning anything while the code still
    looks like it is going through the reader.
    """
    return _detag(copy.deepcopy(_load().get("generator", {}).get(name)))


def derived(name: str, handout: int | None = None):
    """Rebuild a derived value, or return the authored one the export carried.

    The reader is where A2a's recomputation lives. A name this module can rebuild
    is rebuilt; one it cannot is read from the file, where the export carried it
    precisely because nothing could prove it derivable.
    """
    doc = _load()
    # THE POOL COMES FROM THE COMPONENT TOO. `TOTAL` sums `it["max"]`, so a pool
    # of raw course entries stripped of their rubric fields would have raised a
    # KeyError here -- loud, but for the wrong reason, and only for the
    # derivations that happen to read a deleted field.
    pool = [it for it in _rubric_rows()
            if handout is None or it.get("handout") == handout]
    fn = DERIVATIONS.get(name)
    if fn is not None:
        value = fn(pool)
        # EMPTY IS ABSENT, not an answer -- see DERIVATIONS' own note.
        if value or name in ("TOTAL", "BY_ID"):
            return value
    for h, block in doc.get("handouts", {}).items():
        if handout is not None and int(h) != handout:
            continue
        if name in block.get("authored", {}):
            # DETAGGED LIKE EVERY OTHER READ PATH. This one was missed when tuple
            # tagging was added: `_group`, `declaration` and `generator_value`
            # all untag, and `derived`'s authored branch did not, so a tuple-
            # valued authored table came back as {"__tuple__": [...]}. T3.2
            # caught it immediately -- four handout-2 tables at once.
            return _detag(copy.deepcopy(block["authored"][name]))
    raise KeyError(
        f"coursedata: {name!r} is neither derivable here nor carried in the file. "
        f"If it should be rebuilt, add it to DERIVATIONS; if authored, the export "
        f"must carry it.")


def data_root() -> str | None:
    """The course-data root, or None. RESOLVED THE WAY `paths` RESOLVES IT.

    `gold_path` used to read the environment directly and fall back to `""`,
    which made an unset variable produce a RELATIVE path -- `courses/<id>/
    gold.json` resolving against whatever the working directory happened to be.
    A wrong path that looks like a path is worse than none: it reports "gold is
    not available" while never having looked in the right place, and it would
    find a file if one ever sat beside the caller.

    `paths.DATA` already carries the default (`~/molly_data`) and every other
    reader in this package goes through it.
    """
    root = os.environ.get("COURSE_DATA")
    if root:
        return root
    try:
        import paths

        return str(paths.DATA)
    except Exception:                             # pragma: no cover
        return os.environ.get("COURSE_DATA") or None


def overrides_path() -> str:
    """The enforcement gate's override log, OUTSIDE the repository.

    IT USED TO LIVE IN `scoring/` AND THAT WAS THE MISTAKE. It is append-only and
    machine-written, so every commit rewrote the whole blob: 80 versions, 2,838 MB
    of git history, 82% of every blob this repository has ever stored, against 18
    MB of tracked content. Deleting it from the working tree reclaims none of that
    -- a blob is permanent once committed. A log that grows with COURSE WORK
    therefore cannot live in a repository that must not grow with it.

    Beside `gold.json` for the same reason gold is there: it is per-course
    bookkeeping this project writes and rewrites, not part of the code's contract.

    ABSENT IS A CLEAN SLATE, not an error. No records means nothing has been
    excused yet, which is a perfectly good starting state -- the same shape as
    C1b's treatment of gold, and a better fit for a log than for gold.
    """
    root = data_root()
    if root is None:
        return os.path.join("<COURSE_DATA-unset>", "courses",
                            "edu.memphis.psych", "OVERRIDES.md")
    return os.path.join(root, "courses", "edu.memphis.psych", "OVERRIDES.md")


def gold_path() -> str:
    root = data_root()
    if root is None:
        # Named, not silently relative: the caller gets a path it can report.
        return os.path.join("<COURSE_DATA-unset>", "courses",
                            "edu.memphis.psych", "gold.json")
    return os.path.join(root, "courses", "edu.memphis.psych", "gold.json")


def _load_gold() -> dict:
    return gold()


def _carried() -> dict:
    """The carried commentary, FROM THE .olx, where it is a comment again.

    IT WAS DATA ONLY FOR LACK OF A HOME. These lines were comments in the rubric
    modules; carrying them into the course file was what stopped Stage 5 taking
    the record of WHY along with the data. The rubric is authored OLX now, so they
    are comments there -- `<!-- carried:TAG k/n -->` -- and the course file no
    longer holds content that belongs in the content.

    ONE ARTIFACT, so the drift this used to be checked for cannot happen. The
    retired `check_rubric_notes_match_the_modules` compared a module's comments
    against the course file's copy and reported "a comment was edited and not
    re-exported". There is no copy now; the note and its source are the same
    bytes. What IS still possible is LOSS, and that is what
    `check_carried_notes_are_intact` watches.
    """
    import rubric_component

    return rubric_component.as_view_carried()


def rubric_notes(item: str) -> list:
    """The reasoning written about one item, as its author wrote it.

    `rubric_h1.py` is 49% comments and `rubric_h3.py` 25% -- which hypotheses
    died on a rule, what they cost, why a verdict list is the length it is.
    Those lines live inside the `ITEMS` literal, attached to the entry they
    describe, and they are carried here so that deleting the modules at Stage 5
    takes the DATA and not the record of why it is that data.

    NOT DECORATION, and the same argument as `gold_notes`: a reader who does not
    consult it will re-run an experiment that has already been done and
    reverted.
    """
    return [ln for run in rubric_note_runs(item) for ln in run]


def rubric_note_runs(item: str) -> list:
    """The same reasoning, GROUPED INTO BLOCKS as it was written.

    `rubric_notes` flattens; this keeps the boundaries. The §2e hook needs them:
    it prints the last few blocks about an item and says how many earlier ones
    it is not showing, and Q6 has eleven. A flat 327-line list would either
    flood that output or be cut somewhere arbitrary.
    """
    return _carried().get(str(item), [])


def handout_notes(handout) -> list:
    """The prose OUTSIDE a rubric module's `ITEMS` -- its header.

    What the handout is, how its items are built, what the module as a whole is
    for. 548 lines across the three, and lost with the files if not carried.
    """
    return [ln for run in _carried().get("handout:" + str(handout), [])
            for ln in run]


def gold_declaration(name: str):
    """A GOLD declaration table, with its tuple keys restored.

    The gold twin of `declaration()`, and deliberately a SEPARATE accessor rather
    than a `source=` argument on that one. The two files have different
    availability: the course file ships inside this public repository and is
    always there, while gold lives outside it and may legitimately be absent
    (C1b). One accessor spanning both would answer a caller that asked for a
    rubric table and got a gold failure, and the error would name the wrong file.

    EAGER AT THE CALL SITE, BY DESIGN. Every consumer binds these at module level
    -- `CORRECTED_GOLD = _gold_declaration("CORRECTED_GOLD")` -- so importing a
    gold-consuming module now fails if the gold file is UNREACHABLE, where before
    the data was inline and it did not. Unreachable, not "$COURSE_DATA is unset":
    `data_root()` falls back to `paths.DATA`, so unsetting the variable alone
    changes nothing. Measured: with gold genuinely absent, `coursedata` and
    `rubric_export` still import and the four gold-consuming modules refuse with
    a message naming the path they tried -- which is exactly the split C1b is
    for. That cost was accepted over a lazy proxy for a
    measured reason: the twelve tables carry 96 references from INSIDE their own
    modules, and a module-level `__getattr__` (PEP 562) does not fire for a
    module's own global lookups. Lazy binding would therefore have raised
    NameError internally, or -- worse -- resolved once some other module's access
    had cached the name into globals(), making correctness depend on import
    order. A dict subclass filling on first read fails differently and no better:
    `json.dumps`, `dict(x)` and `{**x}` iterate at C level and would have seen an
    EMPTY table without calling the override, which is the silent-wrong failure
    this whole migration exists to prevent.

    So the modules that consume gold now require gold, which is what they mean.
    `coursedata` itself, and `rubric_for()` with it, still import without it.
    """
    decls = _load_gold().get("declarations", {})
    if name not in decls:
        raise KeyError(
            f"coursedata: no gold declaration {name!r} in {gold_path()}. If it is "
            f"a new table, `gold_export.py` must carry it; if it was removed, the "
            f"reader of it must go too.")
    # `_detag` ALONE, and no pair-list inversion. Unlike the course file's seven
    # declarations, these sixteen are not all mappings -- `GOLD_DIVERGENCES` is a
    # list, `GRAPH_UNREACHABLE_1C` a tuple, `_1C_GATE_CEILING` a prose string --
    # so there is no shape to impose here. The export tags what it writes and
    # this inverts the tags; anything else comes back as it went in.
    #
    # MEMBERSHIP, NOT `.get() is None`: a declaration may legitimately BE None or
    # empty (`FIXTURE_GOLD_OVERRIDES` carries nothing today), and reporting that
    # as "not in the file" would send the reader to the exporter for a table the
    # exporter is carrying correctly.
    return _detag(copy.deepcopy(decls[name]))


def gold_notes(table: str, key=None):
    """The measured reasoning behind a gold entry, as the author wrote it.

    These were 707 comment lines INSIDE the gold tables -- one run against each
    entry it judged, recording the hypotheses that died on that cell, the call
    counts, the probe verdicts. They moved here with the entries (C1b) because
    they are course-specific gold reasoning, not engine documentation, and a
    public repository is the wrong home for them.

    THIS IS NOT DECORATION. What these lines record is the expensive half of the
    record: a cell's note routinely represents several hundred grader calls, and
    a reader who does not consult it will re-run an experiment that has already
    been done and reverted. `read-the-record-first` exists because that has
    happened.

    With no `key`, every note for the table, keyed as the file holds the entry
    (a JSON-encoded key: `'["1c", 11]'` for a tuple-keyed entry, an index for a
    list). With a `key`, just that entry's -- pass the entry key itself, in its
    python form, and it is encoded here.
    """
    per = _load_gold().get("declaration_notes", {}).get(table, {})
    if key is None:
        return copy.deepcopy(per)
    slot = json.dumps(list(key) if isinstance(key, tuple) else key)
    return list(per.get(slot, []))


def handout_participants(handout: int | str, field: str) -> list:
    """One handout's participant list, by field.

    These lived inside `handouts.HANDOUTS` and were left there when the rest of
    that table was split, because they are the one part of it that names people.
    """
    hp = _load_gold().get("handout_participants", {}).get(str(handout))
    if hp is None:
        raise KeyError(f"coursedata: no participants for handout {handout!r} in "
                       f"{gold_path()}.")
    if field not in hp:
        raise KeyError(f"coursedata: handout {handout!r} has no participant field "
                       f"{field!r}; it carries {sorted(hp)}.")
    return _detag(copy.deepcopy(hp[field]))


def gold() -> dict:
    """The gold file, loaded on FIRST USE. Only this fails without $COURSE_DATA."""
    global _GOLD
    with _LOCK:
        if _GOLD is None:
            path = gold_path()
            if not os.path.exists(path):
                raise SystemExit(
                    f"coursedata: gold is not available. COURSE_DATA="
                    f"{os.environ.get('COURSE_DATA') or '<unset>'} and the path "
                    f"tried was {path}. Gold lives OUTSIDE this public repository "
                    f"(C1b); the rubric side of this reader works without it.")
            _GOLD = json.load(open(path))
    return _GOLD
