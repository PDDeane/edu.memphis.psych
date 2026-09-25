#!/usr/bin/env python3
"""The SCORER REGISTRY. Goal E, step 2.

A rubric item says WHICH scorer grades it, and this resolves that name to a
module. The boundary is not new -- `score.py` already dispatched on
`derive_from_criteria` vs `derive_from_credit` -- so this names it and makes the
set open, rather than inventing an architecture.

RESOLUTION ORDER is course first, built-ins second, so a course can ship a scorer
or OVERRIDE one without an engine change. That is the whole point: the engine
stops knowing what operant conditioning is.

AN UNRESOLVABLE NAME IS A REFUSAL, never a fall back to `credit`. A wrong scorer
that runs is worse than one that does not: `credit` would happily produce a
ledger from the slot sheet and report a score, and nothing downstream would say
the item was graded by the wrong rule.

THE LEGACY FLAGS STILL WORK, and must until the OLX is rewritten (step 5). A
rubric saying `deriveFromClauses="true"` means `derive_from="oc"` in this course;
`deriveFromCredit="true"` means `credit`. The alias is one-way -- reading the old
flags -- and nothing writes them back.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
import threading

# Serialises course-scorer loading. See `_course_scorer`.
_LOAD_LOCK = threading.Lock()


class ScorerError(RuntimeError):
    """An item names a scorer that cannot be resolved."""


# The engine's own scorers. `credit` is not here because it is not a plugin: it
# is slot-sheet driven and subject-neutral, it lives in `score.py`, and it is
# what an item gets when it declares no scorer at all.
# EMPTY, AND THAT IS THE POINT OF E. The operant-conditioning scorer used to be
# `scorer_oc` here; step 3 moved it to `COURSE_METADATA/scorers/oc.py`, so the
# engine no longer ships -- or knows about -- any subject's scorer. A course
# supplies its own. If the engine ever gains a genuinely subject-neutral scorer,
# this is where it goes; `credit` is not one of them because it is not a plugin.
# ONE ENTRY, AND IT NAMES NO SUBJECT. Goal E emptied this deliberately -- "the
# engine ships no subject's scorer" -- and said what would earn a place back:
# "if the engine ever gains a genuinely subject-neutral scorer, this is where it
# goes". Goal M built one. `criteria` reads its facts and gates from the RUBRIC,
# so what it scores is the course's to declare and the engine never learns a
# subject. A course-side `scorers/criteria.py` still overrides it, like any other.
BUILTIN: dict[str, str] = {"criteria": "scorer_criteria"}

CREDIT = "credit"


def name_for(item: dict) -> str:
    """Which scorer this item declares.

    The explicit `derive_from` wins; the legacy booleans are read only when it is
    absent, so a rubric can be migrated item by item.
    """
    declared = (item.get("derive_from") or "").strip()
    if declared:
        return declared
    if item.get("derive_from_criteria"):
        return "oc"
    if item.get("derive_from_credit"):
        return CREDIT
    return ""


def _course_scorer(name: str):
    """A scorer the COURSE ships, or None. Tried before the built-ins."""
    import paths

    path = paths.COURSE_METADATA / "scorers" / f"{name}.py"
    if not path.is_file():
        return None
    mod_name = f"_course_scorer_{name}"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ScorerError(f"scorer {name!r} at {path} could not be loaded")
    # PUBLISHED ONLY ONCE IT IS BUILT, AND UNDER A LOCK. `score.py` scores
    # participants in a ThreadPoolExecutor, and this registered the module in
    # `sys.modules` BEFORE executing it -- so a second worker reaching the cache
    # check above during the first worker's `exec_module` was handed a module
    # whose body had not run yet. It got as far as `schema_fragment` not
    # existing and reported the participant as FAILED.
    #
    # MEASURED, not reasoned: the 2026-09-25 paper sweep lost handout 2's
    # participant 3 to exactly this -- "module '_course_scorer_oc' has no
    # attribute 'schema_fragment'" -- while the other nineteen scored, and the
    # module imports perfectly in isolation. A race is what a failure that
    # depends on WHICH participant looks like.
    #
    # Registering after `exec_module` costs the ability to satisfy a module that
    # imports ITSELF by name mid-body; no scorer does, and a half-built module
    # handed to another thread is the worse of the two failures.
    with _LOAD_LOCK:
        if mod_name in sys.modules:                 # won by another worker
            return sys.modules[mod_name]
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[mod_name] = mod
        return mod


def resolve(name: str):
    """The module implementing `name`, or a REFUSAL naming what could not be found."""
    if not name or name == CREDIT:
        raise ScorerError(
            f"{name or 'an item with no scorer'} is not a plugin: `credit` is the "
            f"engine's own path and an item declaring nothing uses it. Call this "
            f"only for items whose `name_for` is a plugin name.")
    course = _course_scorer(name)
    if course is not None:
        return course
    builtin = BUILTIN.get(name)
    if builtin is None:
        raise ScorerError(
            f"no scorer named {name!r}. The course ships none at "
            f"COURSE_METADATA/scorers/{name}.py and the engine has "
            f"{sorted(BUILTIN) or 'none'} built in. Declare it or fix the name -- "
            f"this is NOT falling back to `credit`, because a wrong scorer that "
            f"runs is worse than one that does not.")
    return importlib.import_module(builtin)


def optional(name: str):
    """The module implementing `name`, or None when it cannot be resolved.

    For the ALIAS BINDINGS in `score` and `agreement`, which must be real
    function objects -- `enforcement` reads their SOURCE -- but must not stop a
    course that ships no such scorer from importing the engine at all. The
    refusal still happens, later and where it matters: `for_item` raises when an
    ITEM actually asks for the missing scorer.
    """
    try:
        return resolve(name)
    except ScorerError:
        return None


def for_item(item: dict):
    """The scorer module for one item, or None when the engine's `credit` path owns it."""
    name = name_for(item)
    if name in ("", CREDIT):
        return None
    try:
        return resolve(name)
    except ScorerError as exc:
        raise ScorerError(f"item {item.get('id')!r}: {exc}") from None
