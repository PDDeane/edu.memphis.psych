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
DERIVATIONS = {
    "BY_ID": lambda items: {it["id"]: it for it in items},
    "TOTAL": lambda items: sum(it["max"] for it in items),
}

# Which group each item field belongs to (§9.2a obligation 1). GENERATOR is empty
# until Stage 4 brings `olx_prompts.py`'s tables across under B2a -- and that
# emptiness is the reason T2.2's check cannot prove anything yet, which T2.2's own
# design says out loud rather than letting the check pass while vacuous.
RUBRIC_FIELDS = {
    "id", "handout", "label", "max", "increment", "question", "guidance",
    "context", "credit", "deductions", "counts", "derive_from_credit",
    "derive_from_criteria", "unreachable_codes", "blank_code", "expected_type",
    "forbid", "equals", "onlyif", "expect", "maps", "cadence", "oc_gates",
    "derived", "reads_utb_choice", "requires", "cover", "move_pick",
    "avoidance_scores", "graph_item",
}
# STAGE 4, olx_prompts.py's item-keyed tables (B2a: generator fields live on the
# item entry). Every name is PREFIXED `prompt_`, and that is not decoration:
# `CONTEXT` would land as `context`, which RUBRIC_FIELDS already uses for a
# different thing, and §9.2a forbids a field naming two groups. The prefix also
# says what the field is FOR -- these are inputs to prompt generation, not
# scoring rules.
GENERATOR_FIELDS: set[str] = {
    "prompt_action",         # ACTION
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


def items() -> list[dict]:
    """Every item, rubric fields only, in rubric order."""
    return [_group(it, RUBRIC_FIELDS) for it in _load()["items"]]


def rubric_for(item_id: str) -> dict:
    """One item's RUBRIC fields. Never the raw entry, never generator fields."""
    for it in _load()["items"]:
        if str(it.get("id")) == str(item_id):
            return _group(it, RUBRIC_FIELDS)
    raise KeyError(f"coursedata: no item {item_id!r} in {course_path()}")


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
    pool = [it for it in doc["items"]
            if handout is None or it.get("handout") == handout]
    fn = DERIVATIONS.get(name)
    if fn is not None:
        return fn([_group(it, RUBRIC_FIELDS) for it in pool])
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


def gold_path() -> str:
    root = data_root()
    if root is None:
        # Named, not silently relative: the caller gets a path it can report.
        return os.path.join("<COURSE_DATA-unset>", "courses",
                            "edu.memphis.psych", "gold.json")
    return os.path.join(root, "courses", "edu.memphis.psych", "gold.json")


def _load_gold() -> dict:
    return gold()


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
