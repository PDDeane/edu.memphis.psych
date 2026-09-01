"""The measurement ledger: which items were measured, at which prompt, on which cells.

    python3 measured.py --status                 what is stale, what is pending
    python3 measured.py --record Q1 OUT/Q1.runs.json    after a sweep of Q1

An item's published number is only meaningful against two things: the prompt the
grader was sent, and the set of cells the rate was computed over. Change either
and the number is stale — but nothing in the tree LOOKED different, because both
changes are invisible after the fact. A rewritten rule is a diff that landed
weeks ago; a removed exclusion deletes the only record that the cell was ever in
question. An item whose denominator moved and whose prompt was rewritten is
byte-identical, in git, to an item nobody has touched.

That is not hypothetical. On 2026-08-24 an audit found Q1 had five exclusions
removed and its six citations rewritten into rules in the same commit, with no
sweep afterwards — its last item-level measurement predated both changes, and
its reported number rested on re-derivation. Two other guards had gone in that
same day (`olx_prompts --write` naming UNMEASURED sections, `compare_runs.py`
refusing unprobed verdicts) and neither could have caught it: one fires at write
time and prints to stderr, the other only if someone runs it. Guard prose in
QUALITY_CONTROL.md could not catch it either, because the guide had said to
measure and had been read.

So the ledger records, per item, the SHA of the prompt text that was measured
and the exact exclusion set it was measured over. `check_items_are_measured_as_configured`
in enforcement.py recomputes both from the working tree and fails when they
disagree — which turns "someone must remember to re-measure" into a check that
names the item and what changed under it.

Recording is deliberate and mechanical: `--record` reads the run artifact and
writes the entry, so an entry cannot claim a measurement that was not run, and
nobody hand-types a SHA.

A gap may be DECLARED rather than closed, in this project's usual idiom: an
entry may say `pending` with a reason, which the check lists instead of failing
on. What it may not do is be absent. An item that is neither recorded nor
declared is a hard failure, because silence is what let Q1 through.
"""
from __future__ import annotations

import hashlib
import functools
import json
import os
import re
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "MEASURED.json"


def _jobs() -> dict:
    import agreement_app as APP
    return APP.JOBS


def _olx(handout: int) -> str:
    import paths
    return (paths.OLX_DIR / f"bmod_handout{handout}.olx").read_text()


def _section_bounds(text: str, screen_ids: set[str]) -> dict[str, tuple[int, int]]:
    """Slice the OLX into per-item sections, keyed by screen id.

    A section runs from its own <Vertical> to the next <Vertical> that is ALSO an
    item screen — not merely the next <Vertical>, since an item's own tabs are
    Verticals too and slicing at those would cut an item's prompt in half.
    """
    starts: list[tuple[int, str]] = []
    for m in re.finditer(r'<Vertical id="([^"]+)"', text):
        if m.group(1) in screen_ids:
            starts.append((m.start(), m.group(1)))
    out: dict[str, tuple[int, int]] = {}
    for i, (pos, sid) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        out[sid] = (pos, end)
    return out


@functools.lru_cache(maxsize=1)
def _cli_read_attrs() -> frozenset:
    """Which <LLMAction> attributes agreement.py actually reads off the open tag.

    DERIVED from its source, not listed here, so it cannot go stale: the day the
    CLI starts reading a new attribute, that attribute starts counting toward the
    CLI's fingerprint automatically.
    """
    src = (Path(__file__).resolve().parent / "agreement.py").read_text()
    return frozenset(re.findall(r'_attr\(open_tag,\s*"([^"]+)"\)', src))


def _cli_visible(section: str) -> str:
    """The section as the CLI SEES it: prompt bodies plus the attributes it reads.

    Everything else on the open tag reaches the CLI from the RUBRIC, not the OLX
    -- `max`, `slots`, `cover`, `equals`, `derived`, `showChecks`. Hashing them
    into the CLI's fingerprint reports a CLI measurement as stale when a web-only
    attribute changed, which is a false positive in the expensive direction: it
    asks for a re-run of a side that cannot have moved.

    That is not hypothetical. Adding `max="5"` to Q4a -- a web-only fix for a
    web-only defect, since the CLI takes the item max from `item["max"]` -- flagged
    the CLI side STALE PROMPT and made cross_path refuse a comparison that was
    perfectly valid.
    """
    keep = _cli_read_attrs()

    def _one(m: re.Match) -> str:
        tag = m.group(0)
        return "<LLMAction" + "".join(
            ' %s="%s"' % (n, v)
            for n, v in re.findall(r'(?:^|\s)(\w+)="([^"]*)"', tag)
            if n in keep) + ">"

    return re.sub(r"<LLMAction\b[^>]*>", _one, section, flags=re.S)


def prompt_sha(item: str, side: str | None = None) -> str:
    """SHA-256 of the OLX text that item's grader is served, to 12 hex chars.

    `side="cli"` hashes only what the CLI consumes -- see `_cli_visible`. Omit it
    for the web, which is served the tag entire.
    """
    jobs = _jobs()
    job = jobs[item]
    sid = job["screen"].split("/")[-1]
    text = _olx(job["handout"])
    screen_ids = {j["screen"].split("/")[-1] for j in jobs.values()
                  if j["handout"] == job["handout"]}
    bounds = _section_bounds(text, screen_ids)
    if sid not in bounds:
        raise KeyError(f"{item}: no <Vertical id=\"{sid}\"> in handout "
                       f"{job['handout']}'s OLX")
    a, b = bounds[sid]
    section = text[a:b]
    if side == "cli":
        section = _cli_visible(section)
    return hashlib.sha256(section.encode()).hexdigest()[:12]


def exclusions(item: str) -> list[int]:
    import handouts as H
    return sorted(H.cell_exclusions(_jobs()[item]["handout"], item))


def load() -> dict:
    if not LEDGER.exists():
        return {"items": {}}
    return _migrate(json.loads(LEDGER.read_text()))


# The two scoring paths a number can come from, and WHICH IS WHICH matters more
# than it looks -- I got it backwards once, in the migration that added the
# dimension, and it would have mislabelled every historical number.
#
#   "cli"  agreement.py, driven by sweep_cli.sh: the shipped prompt, scored by the
#          CLI's RULES in python. This is what every number in the ledger has
#          always been -- baseline_20260824's own log says "via lo-blocks endpoint
#          (what the browser calls)", and measured.SCORER_PARTS hashes agreement.py's
#          functions, because that is the code whose arithmetic the number depends on.
#   "web"  agreement_app.py, driven by sweep_app.sh: the same prompt scored by the
#          APP's own SlotSheetGrader, which is what a student actually meets.
#
# The trap: the artifact directory holding the CLI column is called `cli_v8`, but
# the harness inside it talks to the web endpoint, so a glance at the log reads
# "web". The prompt is the web's on BOTH sides; what differs is whose rules score
# it. An unlabelled number is a `cli` number.
# THE THREE SCORERS, and which is which matters more than it looks -- see the
# comment below. `paper` was added 2026-08-30, when the third scorer finally had
# a harness that could produce a recordable artifact: before that a paper sweep
# could be RUN and not RECORDED, which is the same shape as the web-side gap the
# shared reader closed.
# THE SCORER x MODEL combinations a number can come from. Scorer alone is not
# enough: the paper scorer runs on gpt-5-mini through the dev server (`--backend
# lo`) and on Opus directly (`--backend cli`/`api`), and those are different
# experiments, not successive versions of one. Recording both under a single
# `paper` key would make each overwrite the other, with `previous` implying a
# progression that never happened.
#
#   web         agreement_app.py -- the app's own grader, gpt-5-mini
#   cli         agreement.py     -- the web prompt scored in python, gpt-5-mini
#   paper       score.py         -- the .docx scorer, gpt-5-mini: the column that
#                                   is COMPARABLE to the two above
#   paper_opus  score.py on Opus -- the headroom experiment, deliberately NOT
#                                   comparable to the others, since it varies the
#                                   model and the path at once
SIDES = ("web", "cli", "paper", "paper_opus")
DEFAULT_SIDE = "cli"


def _migrate(led: dict) -> dict:
    """Fold a pre-side ledger into the per-side shape, in memory.

    The old entry was the record itself: {"numerator": ..., "prompt_sha": ...}.
    The new one is {"web": {...}, "cli": {...}}, because a two-sided sweep measures
    both paths and the old shape had nowhere to put the second -- it could compare
    the paths and record only one of them, which is the whole point of the sweep
    lost at the last step.

    Migration is by SHAPE, not by a version field: an entry carrying `numerator` at
    the top is old. That way a half-migrated file, or a hand-edit that reverts one
    entry, still reads correctly instead of raising.
    """
    items = led.get("items") or {}
    for item, rec in list(items.items()):
        if isinstance(rec, dict) and "numerator" in rec:
            items[item] = {DEFAULT_SIDE: rec}
    return led


def entry(item: str, side: str = DEFAULT_SIDE) -> dict:
    """One side's record for an item, or {} if that side has never been recorded.

    Readers go through this rather than indexing the ledger, so the shape lives in
    one place. It tolerates the old shape via `_migrate`.
    """
    if side not in SIDES:
        raise SystemExit(f"unknown side {side!r}; expected one of {SIDES}")
    rec = (load().get("items") or {}).get(item) or {}
    return rec.get(side) or {}


def records(side: str = DEFAULT_SIDE) -> dict:
    """{item: record} for one side, skipping items that side has no number for.

    Every reader that used to write `records()` calls this instead,
    so adding the side dimension did not mean auditing nine index expressions for
    which of them meant "the web's number" -- all of them did.
    """
    if side not in SIDES:
        raise SystemExit(f"unknown side {side!r}; expected one of {SIDES}")
    out = {}
    for item, rec in (load().get("items") or {}).items():
        got = (rec or {}).get(side)
        if got:
            out[item] = got
    return out


def sides_recorded(item: str) -> list:
    """Which sides have a number for this item."""
    rec = (load().get("items") or {}).get(item) or {}
    return [s for s in SIDES if rec.get(s)]


def save(led: dict) -> None:
    LEDGER.write_text(json.dumps(led, indent=2, sort_keys=True) + "\n")


def status(side: str = DEFAULT_SIDE) -> list[tuple[str, str]]:
    """Per item, one of: ok, pending (declared), stale-prompt, stale-cells, absent.

    Per SIDE. The default is the CLI column -- agreement.py, the shipped prompt
    scored by the CLI's rules -- which is where every number recorded before
    2026-08-28 came from, so existing callers keep their meaning.
    """
    led = records(side)
    out = []
    for item in sorted(_jobs()):
        rec = led.get(item)
        if rec is None:
            out.append((item, "ABSENT — never recorded, and not declared pending"))
            continue
        if rec.get("pending"):
            out.append((item, f"pending: {rec['pending']}"))
            continue
        # PER SIDE. A web-only attribute changing must not report the CLI's
        # measurement as stale: the CLI cannot have moved, so asking for a re-run
        # spends a sweep to reproduce a number we already have.
        want_prompt = prompt_sha(item, side)
        if rec.get("prompt_sha") != want_prompt:
            out.append((item, f"STALE PROMPT — measured at "
                              f"{rec.get('prompt_sha')}, now {want_prompt}"))
            continue
        # A scorer change invalidates a number exactly as a prompt change does.
        # Scoped by fingerprinting the item's OWN scoring path, so the blast
        # radius is COMPUTED rather than guessed. The guess it replaces -- "does
        # this sheet author any computed primitive" -- was true of twenty-one
        # items, which is indistinguishable from a global flag.
        want = scorer_sha(item)
        if rec.get("scorer_sha") not in (None, want):
            out.append((item, f"STALE SCORER — measured at "
                              f"{rec.get('scorer_sha')}, now {want}; the code "
                              f"this item's score depends on has changed"))
            continue
        if rec.get("exclusions") != exclusions(item):
            out.append((item, f"STALE CELLS — measured over "
                              f"{rec.get('exclusions')}, now {exclusions(item)}"))
            continue
        out.append((item, f"ok  {rec.get('numerator')}/{rec.get('denominator')} "
                          f"in {rec.get('runs')} run(s)  {rec.get('out', '')}"))
    return out


# The SCORER's own version. `prompt_sha` catches a changed prompt; nothing
# caught a changed SCORER, and the two invalidate a recorded number equally.
# Found the hard way: `counts=` had never been parsed into the action dict, so
# five items scored with two-to-six points permanently uncharged. Fixing the
# harness left every prompt sha untouched, so `--status` reported all six items
# as current while their recorded numbers described arithmetic that no longer
# existed.
#
# Hashed FUNCTION BY FUNCTION rather than whole-file, so an edit to a CLI flag
# or a log line does not invalidate the corpus. The list is the path from a
# model's answers to a score: the attribute parsers that build the sheet, the
# satisfied/computed resolution, and the three scorers.


# Which parts each item's number actually depends on. A change to `score_oc`
# cannot move a slots-path item, and a parser for a primitive the item does not
# author cannot move it either -- so hashing all eighteen parts for every item
# marks the whole corpus stale on any edit, which is a flag that gets ignored.
_ALWAYS = (("agreement", "load_action"), ("agreement", "parse_slots"),
           ("agreement", "satisfied_map"), ("agreement", "apply_computed"),
           ("agreement", "expand_counted"), ("olx_prompts", "parse_slots"),
           ("handouts", "scores_as_exact"), ("handouts", "attainable_scores"))
_BY_KIND = {"slots": ("agreement", "score_slots"),
            "oc": ("agreement", "score_oc"),
            "oc_cadence": ("agreement", "score_oc_cadence")}
_BY_PRIMITIVE = {
    "equals": (("agreement", "parse_equals"),),
    "derived": (("agreement", "parse_derived"),),
    "cover": (("agreement", "parse_cover"),),
    "counts": (("olx_prompts", "parse_counts"),),
    "onlyif": (("olx_prompts", "parse_onlyif"),),
    "expect": (("olx_prompts", "parse_expect"),),
    "forbid": (("olx_prompts", "parse_forbid"),),
    "requires": (("olx_prompts", "parse_requires"),),
}


# DERIVED, not authored. This was a hand-written list beside the three tables
# above, and it had already drifted: it omitted `agreement.expand_counted`, which
# `_ALWAYS` includes -- so the WHOLE-PATH fingerprint, the one the ledger header
# quotes and the one an unknown-shaped item falls back to, was missing a part that
# every per-item fingerprint had. A fallback that is meant to be conservative and
# is quietly narrower than the scoped case is worse than no fallback.
SCORER_PARTS = tuple(dict.fromkeys(
    _ALWAYS
    + tuple(_BY_KIND.values())
    + tuple(part for parts in _BY_PRIMITIVE.values() for part in parts)))


def _behaviour_src(src: str) -> str:
    """A function's source with its PROSE removed, so only behaviour is hashed.

    This codebase documents heavily, and a fingerprint that moves on a docstring
    is a fingerprint that cries wolf. Correcting one comment in `parse_counts` --
    retracting a misdiagnosis, changing no code -- marked TWENTY-ONE of
    twenty-six items STALE SCORER and would have put ~1800 calls of re-sweeping
    on the list to reconfirm numbers nothing had touched.

    Comments never reach the AST, and unparsing normalises formatting, so what is
    left is the behaviour. Docstrings are dropped at every level.
    """
    import ast, textwrap
    tree = ast.parse(textwrap.dedent(src))
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def _local_callees(mod_name: str, fn_name: str) -> list[tuple[str, str]]:
    """The functions THIS function calls that live in this project's own modules.

    Resolved from the AST, two ways: a bare `f(...)` against the defining
    module's namespace, and an `A.f(...)` through whatever module `A` is bound to
    there. Anything outside this directory is not ours and cannot change under us.
    """
    import ast, importlib, inspect, textwrap
    from pathlib import Path as _P

    here = _P(__file__).resolve().parent

    def _is_local(mod) -> bool:
        f = getattr(mod, "__file__", None)
        return bool(f) and _P(f).resolve().parent == here

    try:
        mod = importlib.import_module(mod_name)
        fn = getattr(mod, fn_name)
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    except Exception:
        return []                       # unreadable: scorer_sha records it missing

    out: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name):
            tgt = getattr(mod, f.id, None)
            if inspect.isfunction(tgt) and getattr(tgt, "__module__", "") == mod_name:
                out.append((mod_name, f.id))
        elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            alias = getattr(mod, f.value.id, None)
            if inspect.ismodule(alias) and _is_local(alias):
                tgt = getattr(alias, f.attr, None)
                if inspect.isfunction(tgt):
                    out.append((alias.__name__, f.attr))
    return out


@functools.lru_cache(maxsize=None)
def _closure(roots: tuple) -> tuple:
    """The roots PLUS everything they transitively call, sorted.

    Hashing a function does not hash its callees, and three of them --
    `verdict_of`, `answer_of`, `is_satisfied` -- decide verdicts for every item
    while being reachable only through `satisfied_map` and `apply_computed`.
    Editing any of them changed scores while all 26 items still read current.

    Enumerating the three would have fixed those three. Taking the closure fixes
    the class, including the callee someone adds next year: twelve functions came
    in when this replaced the enumeration, and only three of them were the ones
    that had been noticed.

    Sorted, so the fingerprint does not depend on AST walk order.
    """
    seen: set[tuple[str, str]] = set()
    queue = list(roots)
    while queue:
        part = queue.pop()
        if part in seen:
            continue
        seen.add(part)
        queue.extend(_local_callees(*part))
    return tuple(sorted(seen))


def _parts_for(item: str | None) -> tuple:
    """The scoring path for one item, or every part when item is None."""
    if item is None:
        return SCORER_PARTS
    import re
    import agreement as A
    import olx_prompts as O
    parts = list(_ALWAYS)
    # The handout comes from the BLOCKS key, not from the job: those entries
    # carry item/olx/refs/kind and no handout, so reading one raised a KeyError
    # into the fallback below and every item quietly fingerprinted all eighteen
    # parts -- conservative, so it looked like nothing was wrong.
    found = next(((h, j) for h, b in A.BLOCKS.items() for j in b.values()
                  if j["item"] == item), None)
    if found is None:
        return SCORER_PARTS               # unknown shape: assume all of it
    handout, job = found
    if job["kind"] in _BY_KIND:
        parts.append(_BY_KIND[job["kind"]])
    aid = O.ACTION.get(item)
    tag = ""
    if aid and job.get("olx"):
        try:
            text = Path(O.OLX % handout).read_text()
        except Exception as e:            # a sheet that cannot be read stales all
            return SCORER_PARTS
        m = re.search(rf'<LLMAction id="{re.escape(aid)}"[^>]*>', text, re.S)
        tag = m.group(0) if m else ""
        # BOTH tags. The primitives are detected by looking for `attr="`, and this
        # looked only at the <LLMAction> tag -- but `forbid`, `equals`, `derived`
        # and the rest are read by olx_prompts from `_sheet_tag`, "whichever
        # element carries this action's slot sheet", which is NOT always the same
        # element. Q4a and Q4c declare `forbid` there, so their fingerprints did
        # not cover `parse_forbid` while their numbers depended on it: exactly the
        # miss this subgoal is about, one level further out.
        try:
            tag += " " + O._sheet_tag(handout, aid)
        except SystemExit:                # no separate sheet element; the tag stands
            pass
    for attr, extra in _BY_PRIMITIVE.items():
        if f'{attr}="' in tag:
            parts.extend(extra)
    return tuple(dict.fromkeys(parts))


# The parts that are ITEM-DEPENDENT by design: one scorer per kind, one parser
# per primitive. Everything else the closure finds is on every item's path.
_SCOPED_PARTS = frozenset(
    tuple(_BY_KIND.values())
    + tuple(part for parts in _BY_PRIMITIVE.values() for part in parts))


@functools.lru_cache(maxsize=None)
def _scoped_closure(roots: tuple) -> tuple:
    """The closure, with the scoping preserved.

    Taking the raw closure destroyed the scoping, and not subtly: `load_action`
    is an unconditional root and it parses the WHOLE sheet, so it calls every
    primitive parser. The closure therefore pulled `parse_forbid` onto all 26
    items, and a one-line edit to it moved all 26 fingerprints -- rebuilding by
    the back door the global flag that the per-item scoping exists to prevent,
    and that a docstring edit once turned into ~1800 calls of pointless
    re-sweeping.

    So a part that is item-dependent BY DESIGN is included only when this item's
    roots asked for it. A parser for a primitive the item does not author cannot
    move its number, whoever calls it: on a sheet with no `forbid` attribute
    `parse_forbid` is handed nothing and returns nothing.

    Everything else the closure discovers is unconditional and comes in -- which
    is the whole point, and is how `verdict_of`, `answer_of` and `is_satisfied`
    finally get hashed.
    """
    return tuple(sorted(
        p for p in _closure(roots)
        if p in roots or p not in _SCOPED_PARTS))


def era_stamp(items=None, model: str | None = None,
              backend: str | None = None) -> dict:
    """What an artifact must record to be comparable with another artifact.

    A sweep's .json said WHAT it scored and never WHAT IT SCORED AGAINST, so two
    directories could only be dated by file mtime. That is not a version: it made
    version indistinguishable from path, and the cross-path scoping on 2026-08-28
    hit it head on -- 18 cells diverged in both of two comparisons and 17 in only
    one, which is what prompt drift looks like when you cannot see it. Those 17
    could not be attributed to anything.

    So: the git commit, whether the tree was dirty when it ran, and each item's
    prompt and scorer fingerprints -- the same two the ledger stamps, from the same
    functions, so an artifact and a recorded measurement can be compared directly.
    A dirty tree is recorded rather than refused, because a probe on uncommitted
    work is legitimate; what is not legitimate is not knowing afterwards.
    """
    import subprocess
    from pathlib import Path as _P

    here = _P(__file__).resolve().parent
    def _git(*a):
        try:
            return subprocess.run(("git", *a), cwd=here, capture_output=True,
                                  text=True, timeout=10).stdout.strip()
        except Exception:
            return ""

    # WHICH MODEL ANSWERED is part of the era and was missing from it. Every
    # measurement in the ledger before 2026-08-30 is silent about this, which was
    # survivable only because all of them ran on the same deployment. The moment
    # the paper scorer is swept on two models, an artifact that cannot say which
    # one produced it is unattributable in exactly the way an unstamped prompt is.
    # Passed by the WRITER, which is the only thing that knows.
    if model is None:
        model = os.environ.get("AZURE_DEPLOYMENT_ID") or ""
    if items is None:
        items = sorted(_jobs())
    per = {}
    for it in items:
        try:
            per[it] = {"prompt_sha": prompt_sha(it), "scorer_sha": scorer_sha(it),
                       "prompt_sha_cli": prompt_sha(it, "cli")}
        except Exception as e:
            per[it] = {"error": f"{type(e).__name__}: {e}"}
    return {
        "git": _git("rev-parse", "HEAD") or "unknown",
        "dirty": bool(_git("status", "--porcelain")),
        # Empty when the writer did not say and the environment does not know.
        # Recorded either way, so "unstamped" is visible rather than assumed.
        "model": model or "",
        "backend": backend or "",
        "items": per,
    }


def scorer_sha(item: str | None = None) -> str:
    """SHA-256 of the code that turns THIS item's answers into a score, 12 hex.

    Prose-insensitive and scoped: see `_behaviour_src` and `_parts_for`. Called
    with no item it fingerprints the whole path, which is what the ledger header
    and the reports quote.
    """
    import hashlib
    import importlib
    import inspect
    src = []
    # The CLOSURE of the scoped roots, not the roots alone -- minus the parts the
    # scoping deliberately left out for THIS item. See _scoped_closure.
    for mod, name in _scoped_closure(_parts_for(item)):
        try:
            got = inspect.getsource(getattr(importlib.import_module(mod), name))
            src.append(_behaviour_src(got))
        except Exception:
            src.append(f"<missing {mod}.{name}>")
    return hashlib.sha256("".join(src).encode()).hexdigest()[:12]


def record(item: str, runs_path: str, side: str = DEFAULT_SIDE) -> None:
    """Write item's entry FROM a run artifact, so it cannot claim what was not run."""
    import handouts as H
    import gold
    import agreement_app as APP
    import cross_path as X

    h = _jobs()[item]["handout"]
    g = H.apply_corrected_gold(
        {1: gold.load_h1, 2: gold.load_h2, 3: gold.load_h3}[h](), h)
    if item == "1c":
        g, _ = APP.rebuild_gold_1c({p: dict(v) for p, v in g.items()})
    ex = set(exclusions(item))
    per: dict[int, list[bool]] = {}
    exc: dict[int, list[bool]] = {}
    for run in json.loads(Path(runs_path).read_text())["runs"]:
        for c in run["results"]:
            # Shape-reading lives in cross_path, which documents all three and
            # owns the app's fraction-of-sheet_max conversion. The ledger must
            # be recordable from EITHER scorer's artifact -- the whole point of
            # the side dimension -- and two copies of that conversion is one
            # too many.
            got = X.result_cell(c)
            if got is None:
                continue
            cell_item, pid, s, _v = got
            if cell_item != item:
                continue
            row = (g.get(pid) or {}).get(item) or {}
            if row.get("score") is None:
                continue
            right = s is not None and H.scored_exactly(item, row["score"], s)
            # Excluded cells are still run and still scored, so recording them
            # costs nothing and is what lets a declaration be caught outliving
            # its evidence: an exclusion whose cell now agrees, every run, is a
            # cell being subtracted from every rate for a reason that expired.
            (exc if pid in ex else per).setdefault(pid, []).append(right)
    if not per:
        raise SystemExit(f"{item}: no counted cells in {runs_path}")
    n = min(len(v) for v in per.values())
    totals = sorted(sum(1 for p in per if per[p][i]) for i in range(n))
    if side not in SIDES:
        raise SystemExit(f"unknown side {side!r}; expected one of {SIDES}")
    led = load()
    # WHAT THIS REPLACES, kept on the entry. Recording used to overwrite outright,
    # so "what did this item score before the change" meant `git show` -- and the
    # ledger is the thing people actually read. One generation is enough: the
    # artifact directory named in `out` holds every run, and git holds the rest, so
    # this is a pointer to the last number rather than a second archive.
    prior = (led.get("items", {}).get(item, {}) or {}).get(side)
    led.setdefault("items", {}).setdefault(item, {})[side] = {
        "prompt_sha": prompt_sha(item, side),
        "scorer_sha": scorer_sha(item),
        "exclusions": exclusions(item),
        "runs": n,
        "numerator": totals[n // 2],
        "denominator": len(per),
        "run_totals": totals,
        "out": str(Path(runs_path).parent.name),
        # Per cell, how many of the recorded runs scored it right. Keyed by str
        # because JSON keys are strings; read back through `_cells`.
        "cells": {str(p): sum(1 for v in per[p][:n] if v) for p in sorted(per)},
        "excluded_cells": {str(p): sum(1 for v in exc[p] if v)
                           for p in sorted(exc)},
    }
    if prior:
        led["items"][item][side]["previous"] = {
            k: prior.get(k) for k in
            ("numerator", "denominator", "runs", "out", "prompt_sha", "scorer_sha")
        }
    save(led)
    print(f"{item} [{side}]: {totals[n // 2]}/{len(per)} recorded at prompt "
          f"{prompt_sha(item)} over {len(per)} cells (runs {totals})")


def declaration_conflicts() -> list[str]:
    """Declarations the recorded measurements no longer support.

    Every declaration in handouts.py is a PREDICTION about a cell or an item: a
    divergence predicts we miss this cell and mean to; a ceiling predicts the
    item cannot be perfect because gold is incoherent; an exclusion predicts the
    cell should not be counted. Predictions can expire — the model improves, a
    fixture defect is repaired, a rule is rewritten — and an expired declaration
    is invisible, because a cell that has stopped being a problem produces no
    error to notice. It just quietly costs a cell in every rate, forever.

    Section 5's "reduce the declarations" schedule exists for this and was run by
    hand, which is why 25 unnecessary registrations survived several passes. So
    the ledger, which records every cell's per-run outcome INCLUDING the excluded
    ones, is compared against the declarations automatically.

    The threshold follows Q2/p17: three uniform passes prove nothing, in either
    direction. So a declaration contradicted by fewer than six recorded runs
    yields a demand for a probe, not a retirement; only 6+ runs of unbroken
    agreement asks for the declaration to go. Nothing is flagged from a partial
    rate, because a declaration about a cell the model gets right half the time
    is doing exactly the job it was written for.
    """
    import handouts as H

    # EVERY recorded side, not just the CLI. This read `records()` -- which
    # defaults to `cli` -- so a declaration the WEB had already refuted was
    # invisible. Q6/p5 is the case that exposed it: after E15 the web scored it
    # right in 6 of 6 runs while the cli missed one, so the check reported ZERO
    # conflicts and DUPLICATE_EFFECT_TIE_BREAK stood unchallenged on the strength
    # of the side that happened to be the default.
    #
    # Retirement still requires EVERY measured side to agree, because a
    # divergence one path still hits is a true statement about that path. What
    # changes is that a SPLIT is now reported instead of silently resolved in the
    # default side's favour: a declaration true on one path and false on another
    # is a finding about the paths, and it was previously unsayable.
    per_side = {}
    for _s in SIDES:
        try:
            _r = records(_s)
        except Exception:
            continue
        if _r:
            per_side[_s] = _r
    led = per_side.get(DEFAULT_SIDE) or {}
    out: list[str] = []

    def verdict(what: str, right: int, runs: int, action: str) -> str:
        if runs >= 6:
            return (f"{what} is contradicted by {right}/{runs} recorded runs. "
                    f"{action}")
        lead = action[:1].lower() + action[1:]   # not .lower(): "Q6/p5" is a name
        return (f"{what} is contradicted by {right}/{runs} recorded runs, but "
                f"{runs} runs cannot settle a per-cell claim (see Q2/p17). Probe "
                f"it at six passes with controls; if it holds, {lead}")

    def _sides(item: str, read):
        """(right, runs) per side for one declaration, from every side with data.

        `read` pulls the pair out of one side's record, so the three declaration
        kinds below share the side handling instead of each growing its own.
        """
        got = {}
        for s, recs in per_side.items():
            rec = recs.get(item)
            if not rec or rec.get("pending"):
                continue
            pair = read(rec)
            if pair is None:
                continue
            right, runs = pair
            if right is None or not runs:
                continue
            got[s] = (right, runs)
        return got

    def split_verdict(what: str, action: str, got: dict) -> str | None:
        """One message for a declaration measured on more than one side."""
        against = {s: v for s, v in got.items() if v[0] >= v[1]}
        if not against:
            return None
        holds = {s: v for s, v in got.items() if v[0] < v[1]}
        if not holds:
            worst = min(against.values(), key=lambda v: v[1])
            where = ", ".join(f"{s} {v[0]}/{v[1]}" for s, v in sorted(against.items()))
            return verdict(f"{what} on EVERY measured side ({where})",
                           worst[0], worst[1], action)
        # Split. Not a retirement: the declaration is still true where it holds.
        a = ", ".join(f"{s} {v[0]}/{v[1]}" for s, v in sorted(against.items()))
        h = ", ".join(f"{s} {v[0]}/{v[1]}" for s, v in sorted(holds.items()))
        return (f"{what} on {a}, but still holds on {h}. A declaration true on "
                f"one path and false on another is a finding about the PATHS: "
                f"scope the entry to the side it describes, or bring the lagging "
                f"side up and then {action[:1].lower() + action[1:]}")

    for entry in getattr(H, "GOLD_DIVERGENCES", []) or []:
        for item, pid in entry.get("cells", []):
            got = _sides(item, lambda rec, _p=str(pid): (
                (rec.get("cells") or {}).get(_p), rec.get("runs") or 0))
            msg = split_verdict(
                f"GOLD_DIVERGENCES {entry['code']} says we knowingly miss "
                f"{item}/p{pid}, but it scores RIGHT every run",
                f"Retire the {item}/p{pid} cell from that entry", got)
            if not msg:
                continue
            # SCORING RIGHT IS NOT THE SAME AS AGREEING. This check reported a
            # contradiction on the strength of the TOTAL, which is all the ledger
            # holds -- and Q6/p5 agrees on the total while failing a different set
            # of slots from the ones gold charged: gold takes state_a1/state_c1/
            # state_c2, we take state_a1/state_c2/affect_c2, two disagreements
            # cancelling. On that evidence DUPLICATE_EFFECT_TIE_BREAK was proposed
            # for retirement, and gold's own comment confirms its stated reason.
            #
            # So where the slot sets can be compared and DIFFER, the declaration
            # is not contradicted and nothing is reported. This is not an
            # exemption for one cell: it is the check declining to draw a
            # conclusion the evidence does not support, and it protects every
            # divergence the same way. Where slots cannot be read
            # (gold_charged_slots returns None) the total stands as before, which
            # is the old behaviour and the honest default for an unread comment.
            charged = gold_charged_slots(item, pid)
            if charged is not None:
                ours = _our_failing_slots(item, pid)
                if ours:
                    stable = set.intersection(*[set(f) for f in ours])
                    if stable != charged:
                        continue
            out.append(msg)

    for (h, item), _why in (getattr(H, "GOLD_CEILINGS", {}) or {}).items():
        def _perfect(rec):
            num, den = rec.get("numerator"), rec.get("denominator")
            runs = rec.get("runs") or 0
            if not den or num is None:
                return None
            # A ceiling is contradicted only by a PERFECT rate, so the pair fed
            # to the split logic is (runs, runs) when perfect and (0, runs) when
            # not -- the same "right >= runs" test the other two kinds use.
            return ((runs if num == den else 0), runs)
        got = _sides(item, _perfect)
        msg = split_verdict(
            f"GOLD_CEILINGS ({h!r}, {item!r}) says this item cannot be perfect, "
            f"but it recorded a perfect rate",
            f"Retire the ({h!r}, {item!r}) ceiling", got)
        if msg:
            out.append(msg)

    # Union across sides, not the cli ledger's keys: an item measured on the web
    # only would have had its exclusions unchecked entirely.
    all_items = sorted({i for recs in per_side.values() for i in recs})
    for item in all_items:
        rec = led.get(item) or next(
            (recs[item] for recs in per_side.values() if item in recs), None)
        if not rec or rec.get("pending"):
            continue
        runs = rec.get("runs") or 0
        job = _jobs().get(item)
        if job is None:
            # In the ledger but no longer driven by agreement_app.JOBS. A real
            # condition, and one the audit already reports on its own ("NEVER
            # MEASURED"), so skip rather than raise: `_jobs()[item]` here turned
            # an item leaving JOBS into a KeyError that took down the whole audit
            # -- including `--selftest`, whose "an item leaves JOBS" case is
            # exactly this scenario, so the crash hid the very check meant to
            # catch it.
            continue
        # E33. THE TABLE SAYS WHICH CELLS ARE EXCLUDED; THE ARTIFACT SAYS HOW THEY
        # SCORED. This loop used to read only the ledger's `excluded_cells`, which
        # is a snapshot taken when the item was last recorded -- so an exclusion
        # was invisible to it unless it happened to be in place at the last sweep
        # AND produced a scored observation. Both halves are now read, and a cell
        # present in one but not the other is reported rather than skipped,
        # because "no evidence" is a different state from "no problem" and this
        # check exists to stop an exclusion outliving its justification.
        kinds = H.cell_exclusions(job["handout"], item)
        now_excluded = set(kinds)
        recorded = {int(k) for recs in per_side.values()
                    for k in ((recs.get(item) or {}).get("excluded_cells") or {})}

        # Does gold even have a score for the cell? Without one no measurement can
        # ever agree or disagree, so the exclusion is unfalsifiable BY DESIGN
        # rather than merely unmeasured -- 1c's p4/p19/p20 are this, because
        # rebuild_gold_1c removes their gold rows. Reporting those as "unmeasured"
        # every run would nag forever about cells nothing can settle.
        try:
            import gold as _g
            _gold_rows = H.apply_corrected_gold(
                {1: _g.load_h1, 2: _g.load_h2, 3: _g.load_h3}[job["handout"]](),
                job["handout"])
            if item == "1c":
                import agreement_app as _APP
                _gold_rows, _ = _APP.rebuild_gold_1c(
                    {p_: dict(v) for p_, v in _gold_rows.items()})
        except Exception:
            _gold_rows = {}

        for pid in sorted(now_excluded - recorded):
            kind = (kinds.get(pid) or ("", ""))[0]
            if kind == "suspect":
                continue          # a fact about the input; measurement cannot speak
            has_gold = ((_gold_rows.get(pid) or {}).get(item) or {}).get(
                "score") is not None
            if not has_gold:
                # `unscoreable` ASSERTS that gold's row is unreachable, so a
                # missing gold score is the declaration and the evidence agreeing.
                # Reporting it would nag forever about cells nothing can settle,
                # and would train the reader to skip this check. 1c's p4/p19/p20
                # are exactly this: rebuild_gold_1c removes their gold rows and the
                # exclusion says they are unscoreable. Consistent, so silent.
                #
                # Any OTHER kind with no gold row is a real inconsistency: the
                # exclusion claims something measurement could contradict, and
                # there is nothing to contradict it with.
                if kind == "unscoreable":
                    continue
                out.append(
                    f"{item}/p{pid} is EXCLUDED as {kind or 'excluded'}, which is "
                    f"a claim measurement could refute, but gold has no score for "
                    f"the cell so nothing can. Either the exclusion is really "
                    f"`unscoreable` -- say that -- or the missing gold row is the "
                    f"defect and the exclusion is hiding it")
            else:
                out.append(
                    f"{item}/p{pid} is EXCLUDED as {kind or 'excluded'} but is not "
                    f"in the last recorded run's excluded cells, so there is NO "
                    f"evidence either way -- the exclusion was added since that "
                    f"sweep, or the scorer produced nothing for it. Re-sweep "
                    f"{item} before trusting the exclusion")

        for pid in sorted(recorded - now_excluded):
            out.append(
                f"{item}/p{pid} was recorded as EXCLUDED but the exclusion table "
                f"no longer lists it. The two sources disagree: a check reading "
                f"only one of them cannot say which is current. Re-record {item}, "
                f"or restore the exclusion if dropping it was not intended")

        for pid_s in sorted({str(p) for p in now_excluded & recorded}, key=int):
            kind = (kinds.get(int(pid_s)) or ("", ""))[0]
            # Not every exclusion is a hypothesis about the model, and only the
            # ones that are can be retired by measuring it.
            #
            # `suspect` is a fact about the INPUT: the submission was
            # mis-transcribed and the prompt carries another participant's data.
            # A cell like that agreeing with gold is a coincidence between the
            # wrong student's answer and this student's score — the one reading
            # that must NOT be taken as evidence the cell is fine. PR/p2 hit this
            # within minutes of the check going in, offering to count a cell
            # whose input is known to belong to someone else.
            #
            # `self_graded` and `unscoreable` are claims that measurement can
            # contradict: the first says the prompt gives the answer away, the
            # second says gold's row is unreachable, and a cell that agrees
            # anyway refutes both.
            if kind == "suspect":
                continue
            got = _sides(item, lambda rec, _p=pid_s: (
                (rec.get("excluded_cells") or {}).get(_p), rec.get("runs") or 0))
            msg = split_verdict(
                f"{item}/p{pid_s} is EXCLUDED as {kind or 'excluded'}, yet scores "
                f"right every recorded run",
                f"Remove {item}/p{pid_s} from its exclusion and let it count", got)
            if msg:
                out.append(msg)
    return out


# Fractions first, item names second — NOT one pattern anchored on the name.
# Anchoring on the name meant any word in front of it was consumed as the
# candidate and the real name never got its turn: "Item 3 is 20/20" matched
# "Item", found it absent from JOBS, and moved past the fraction without ever
# testing "3", because finditer does not retry overlapping starts.
_FRAC_RE = re.compile(r"\b(?P<num>\d{1,2})\s*(?:/|\s+of\s+)\s*(?P<den>\d{1,2})\b")
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_WINDOW = 45

# Prose legitimately cites superseded numbers; those sentences say so. A claim
# framed as history is not a claim about the present.
_HISTORICAL = re.compile(
    r"\b(was|were|had been|used to|previously|prior|before|earlier|once|"
    r"then|originally|superseded|stale|reported as|no longer)\b"
    # A fraction attributed to a NAMED artifact is a claim about that run, not
    # about the present configuration, however present-tense the verb.
    # EQUIVALENCE.md line 491 reads "On web_v8/v9, 2a is 14-16 of 18 and 3 is 20
    # of 20" inside a block that already says "Do not quote this list as
    # current" — correct prose that the first version of this check called stale.
    r"|\b(web_v|cli_v|qc_v|qc_h|opusweb|baseline_)\w*", re.I)

# Words that make a fraction a COUNT of cells rather than a score over them.
# "Q6 excludes 10 of 20" and "2a flags 18 of 20" are both true and neither is a
# rate; each produced a confident false positive before this list existed.
_COUNTING = re.compile(r"exclud|flag|cells|participants|of the rest|"
                       r"rows|boxes|slots|passes|runs", re.I)


def error_profile(item: str, runs_path: str) -> str:
    """Where an item's errors COME FROM, by slot. Run after every sweep.

    A median says how many cells are wrong. It never says which JUDGEMENT is
    wrong, and the two answers can point at different work entirely. Q1 spent a
    day on its merge rule because three misses looked like merge failures; this
    profile over the same artifact says 16 of 17 count errors are OVER-counts and
    8 of those are on cells where gold credits ONE reason -- an exclusion problem
    roughly twice the size of the merge problem, and untouched by any of the
    eleven configurations tried.

    Three tables, because each answers a different question:

      DIRECTION   over- vs under-credit. A one-sided profile means a threshold is
                  set wrong; a two-sided one means the judgement is unstable.
      BY SLOT     how often each slot is unsatisfied, split by whether the CELL
                  was right. A slot that is unsatisfied mostly in correct cells is
                  doing its job; one that tracks the errors is the lever.
      DRIFT       how often a slot's verdict changes across runs of the SAME cell.
                  High drift means the prompt is asking something the model cannot
                  answer twice the same way, which no rewrite of the rule fixes.
    """
    import json
    import collections
    import agreement as A
    import gold as _gold
    import handouts as _H
    import cross_path as _X

    h = _jobs()[item]["handout"]
    g = _H.apply_corrected_gold(
        {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}[h](), h)
    if item == "1c":
        # The SAME rebuild `record` applies. Without it this read 1c as 18
        # over-credits and 78% correct, when the item has ZERO over-credits: the
        # 18 were three cells scored against gold the rebuild removes. A profile
        # that disagrees with the ledger about the same artifact is worse than no
        # profile, because the per-slot table looks authoritative -- it sent
        # `1c +9` into a corpus-wide over-credit ranking before the per-cell
        # readout contradicted it.
        import agreement_app as _APP
        g, _ = _APP.rebuild_gold_1c({p: dict(v) for p, v in g.items()})
    runs = json.loads(Path(runs_path).read_text())["runs"]

    # EXCLUDED cells are skipped, the same ones `record` leaves out of the
    # published figure. They were not, and the profile was computed over a
    # different cell set from the number it exists to diagnose: all 20 against a
    # figure over 18. On the twelve H2 items that is p2 and p3 -- 10% of every
    # profile's observations, declared suspect for a recorded reason -- feeding
    # the DIRECTION counts and the one-sided verdict below.
    #
    # It misled exactly the way a trusted diagnostic does. The 2026-08-30
    # re-sweep read WK1 as 8 over / 1 under and WK2 as 11 over / 4 under, three
    # of four flagged one-sided, and a subgoal was filed claiming p3 carried 24
    # of 37 over-credits and a threshold was set wrong. p3 is excluded on both
    # items. Filtered, WK1 is 2 over / 1 under and WK2 is 5 over / 4 under --
    # balanced, and nothing to investigate. Same shape as the 1c rebuild above:
    # a profile that disagrees with the ledger about the same artifact is worse
    # than no profile, because the tables look authoritative.
    excluded = set(exclusions(item))

    obs = []
    seen_cells = set()
    for i, run in enumerate(runs, 1):
        for r in run["results"]:
            got = _X.result_cell(r)          # either scorer's artifact shape
            if got is None:
                continue
            cell_item, pid, sc, vd = got
            if cell_item != item or sc is None:
                continue
            seen_cells.add(pid)
            if pid in excluded:
                continue
            gv = (g.get(pid, {}).get(item) or {}).get("score")
            if gv is None:
                continue
            obs.append((i, pid, gv, sc, vd))
    if not obs:
        return f"{item}: no scored observations in {runs_path}"

    # Name the cell set in the header. A reader comparing this to the ledger
    # needs to see WHICH cells it was computed over without reading the code --
    # that is the whole failure being fixed.
    kept = len({p for _, p, *_ in obs})
    scope = f"{kept} of {len(seen_cells)} cell(s)"
    if excluded & seen_cells:
        scope += (" — excluding p"
                  + ", p".join(str(p) for p in sorted(excluded & seen_cells)))
    out = [f"{item}: error profile over {len(obs)} observation(s), "
           f"{scope} — {runs_path}"]
    n = len(obs)
    corr = sum(1 for *_, gv, s, _ in [(0, 0, o[2], o[3], 0) for o in obs] if s == gv)
    over = sum(1 for o in obs if o[3] > o[2])
    under = sum(1 for o in obs if o[3] < o[2])
    out.append(f"  DIRECTION   correct {corr} ({100*corr/n:.0f}%)   "
               f"over-credit {over} ({100*over/n:.0f}%)   "
               f"under-credit {under} ({100*under/n:.0f}%)")
    if over and under and min(over, under) / max(over, under) < 0.25:
        out.append("              one-sided: a threshold is set wrong, not unstable")

    # Which slots are unsatisfied, and do they track the errors?
    try:
        spec = A.load_action(f"bmod_handout{h}.olx", __import__("olx_prompts").ACTION[item])
        slots = spec["slots"]
    except Exception:
        slots = []
    out.append(f"  {'BY SLOT':12} {'unmet':>6} {'in WRONG cells':>15} {'in right cells':>15}")
    for sl in slots:
        k = sl["key"]
        if sl.get("count_max"):
            continue                      # counts are profiled below, not as verdicts
        unmet = wrong = right = 0
        for _, pid, gv, s, ch in obs:
            v = (ch or {}).get(k)
            if v in (None, ""):
                continue                  # unrecorded: see the count-slot gap
            if not A.is_satisfied(sl, v):
                unmet += 1
                if s != gv: wrong += 1
                else: right += 1
        if unmet:
            flag = "  <-- tracks the errors" if wrong and wrong >= right else ""
            out.append(f"  {k:14} {unmet:>6} {wrong:>15} {right:>15}{flag}")

    # Counted families: what number was given, against what gold implies
    counts = collections.Counter()
    for cr in (_H.config(h)["rubric"].BY_ID[item].get("counts") or []):
        for _, pid, gv, s, ch in obs:
            raw = str((ch or {}).get(cr["key"], "")).strip()
            if raw.isdigit() and s != gv:
                counts[f"said {raw}, scored {s:g} against gold {gv:g}"] += 1
    if counts:
        out.append("  COUNTS in wrong cells:")
        for k, v in counts.most_common(8):
            out.append(f"    {k:44} x{v}")

    # Drift: same cell, different verdict across runs
    per = collections.defaultdict(lambda: collections.defaultdict(set))
    for _, pid, gv, s, ch in obs:
        for k, v in (ch or {}).items():
            if v not in (None, ""):
                per[k][pid].add(v)
    drifty = [(k, sum(1 for pid, vs in cells.items() if len(vs) > 1))
              for k, cells in per.items()]
    drifty = [(k, c) for k, c in drifty if c]
    if drifty:
        out.append("  DRIFT (cells whose verdict changed across runs):")
        for k, c in sorted(drifty, key=lambda x: -x[1]):
            out.append(f"    {k:24} {c} cell(s)")
    return "\n".join(out)


def prose_claims(paths: list[str] | None = None) -> list[str]:
    """Numbers written into the repo that disagree with the recorded measurement.

    A figure in prose is the form a measurement actually travels in — a guide,
    a backlog entry, a note in handouts.py — and it goes stale silently. This
    project has done it: Q4c and Q5 were described in writing as perfect items
    and were 12/14 and 14/15, because the sentences outlived the denominators
    they were computed over.

    The rule is deliberately narrow, so it fires on real staleness rather than on
    every number in the tree. A finding needs all of: an item name from JOBS, a
    fraction within 40 characters of it, a DENOMINATOR equal to that item's
    currently recorded one — and a numerator that disagrees. Matching the
    denominator is what makes it a claim about the present configuration; a
    fraction over the old denominator is history and is left alone, as is any
    sentence framed in the past tense.
    """
    import paths as _paths

    files = paths or [str(p) for p in (
        list((_paths.SCORING).glob("*.md")) + [_paths.SCORING / "handouts.py"])]
    led = records()
    jobs = set(_jobs())
    out: list[str] = []
    for path in files:
        try:
            text = Path(path).read_text()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if _HISTORICAL.search(line):
                continue
            for m in _FRAC_RE.finditer(line):
                window = line[max(0, m.start() - _WINDOW):m.start()]
                # The NEAREST item name before the fraction owns it.
                names = [t for t in _TOKEN_RE.findall(window) if t in jobs]
                if not names:
                    continue
                item = names[-1]
                # WHICH SIDE the sentence is talking about. The ledger has held
                # two since the side dimension landed, and this check compared
                # against the default one only -- so a correctly quoted WEB figure
                # read as a contradiction of the CLI's. That fired on the E14
                # closure note, which reports the seven re-measured items on the
                # side that could not previously run them.
                # Naming a side is what selects it; saying nothing still means the
                # default, so no existing sentence changes meaning.
                # The NEAREST cue owns it, exactly as the nearest item name does
                # above. This took the last cue in ITERATION order instead, so a
                # sentence naming both sides -- "Q6 records cli 17/20 and web
                # 18/20" -- attributed the WEB figure to the cli, because "cli"
                # sits later in the tuple than "web". Every such sentence read as
                # a contradiction and the only way to quiet it was to write one
                # side per line, which is a formatting rule invented by a bug.
                side = DEFAULT_SIDE
                low = window.lower()
                best = -1
                for cue, s_ in (("web", "web"), ("app", "web"),
                                ("cli", "cli"), ("harness", "cli")):
                    at = low.rfind(cue)
                    if at > best:
                        best, side = at, s_
                rec = records(side).get(item)
                if not rec or rec.get("pending"):
                    continue
                num, den = int(m.group("num")), int(m.group("den"))
                if den != rec["denominator"] or num == rec["numerator"]:
                    continue
                # The denominator is the same 20 whether the fraction counts
                # cells or scores them, so the surrounding words are the only
                # way to tell, and getting it wrong yields a confident lie.
                if _COUNTING.search(window):
                    continue
                out.append(
                    f"{Path(path).name}:{lineno} says {item} {num}/{den}, but the "
                    f"recorded {side} measurement is "
                    f"{rec['numerator']}/{rec['denominator']}"
                    f" — update the sentence, or re-record if the sweep is newer")
    return out


# The unit is OPTIONAL BEFORE A COLON. Graders write "-1.25 pts:" and also
# "-1.25:" and "-1.5;", and requiring the unit made those invisible. Q6/p1 itemises
# FOUR 1.25 charges, the third of them unitless, and was reported for two
# months as implying 6.25 against a row of 5.00. Q6/p4 writes "-2.5:" and
# "-1.5;" for 4.00 off 10, exactly its recorded 6.00. Both reconcile.
# An itemised deduction in a grader's comment. TWO shapes, because the graders
# wrote two: "-2 pts", "-1.25:" and so on, and a bare "-1.25 First antecedent
# does not match ...". Only the first was matched, so a row written the second way
# had NO parseable deductions and gold_rows_that_do_not_reconcile skipped it
# entirely -- 3 of the 183 rows with a comment, and Q6/p5 among them, which is
# the row that turned out to charge different slots from ours while agreeing on
# the total (E30). A row nobody can read the arithmetic of is the last place to
# leave unread.
#
# The second alternative is deliberately narrow: start of line, then the number,
# then whitespace, then a LETTER. A bare "-1.25" mid-sentence does not match, and
# neither does a negative number in prose. Verified across all 183 commented rows
# -- 180 parse identically to before, the 3 new ones all reconcile, and no row
# gained a deduction it did not name.
_DEDUCT_RE = re.compile(
    r"-\s*(\d+(?:\.\d+)?)\s*(?:pts?\b|points?\b|[:;])"
    r"|^[ \t]*-[ \t]*(\d+(?:\.\d+)?)[ \t]+(?=[A-Za-z])", re.I | re.M)


def deductions_named(feedback: str) -> list[float]:
    """The deduction amounts a grader's comment itemises, in order.

    Wraps _DEDUCT_RE because it now has two alternatives and so returns pairs:
    every caller wants the amounts, and one of them was doing
    `[float(x) for x in _DEDUCT_RE.findall(fb)]`, which becomes a TypeError the
    moment a second group exists. One accessor, so the next caller cannot get it
    wrong either.
    """
    return [float(a or b) for a, b in _DEDUCT_RE.findall(feedback or "")]


def gold_rows_that_do_not_reconcile() -> list[str]:
    """Rows whose own comment itemises deductions that do not reach their score.

    D2/p11 was found this way by hand: the grader named one defect, charged 1
    point for it, and the deduction dictionary plus the same grader's own
    treatment of the identical defect one item earlier both said 2. That is a
    wrong NUMBER — CORRECTED_GOLD — rather than a disagreement to declare.

    The generalisation is mechanical wherever a comment itemises its arithmetic:
    take the item's maximum, subtract the deductions the comment names, and
    compare with the score written. A row that does not reconcile is a gold
    question, and gold questions come BEFORE model work (step 2 before step 3),
    because tuning a criterion against an incoherent row measures the row.

    Reported, never auto-corrected. A row can fail to reconcile because the
    grader slipped OR because they applied a deduction they did not write down,
    and only reading the submission distinguishes those. What this removes is the
    part that was left to memory: noticing that the row is worth reading.
    """
    import gold as _gold
    import handouts as H

    out: list[str] = []
    loaders = {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}
    jobs = _jobs()
    for h in (1, 2, 3):
        try:
            g = loaders[h]()
        except Exception:
            continue
        items = [i for i in sorted(jobs) if jobs[i]["handout"] == h]
        maxes = {i: max(((g.get(p) or {}).get(i) or {}).get("score") or 0
                        for p in g) for i in items}
        for item in items:
            for pid in sorted(g):
                row = (g.get(pid) or {}).get(item) or {}
                score, fb = row.get("score"), (row.get("feedback") or "").strip()
                if score is None or not fb:
                    continue
                named = deductions_named(fb)
                if not named:
                    continue
                # 1c's gold is RESTATED FROM ITS VERDICTS by
                # agreement_app.rebuild_gold_1c before anything scores against
                # it, precisely so p11's improvised "-1 pt: missing baseline
                # data week" -- a charge no slot on either side prices -- is
                # dropped rather than subtracted. Reading the raw row here
                # reported p11 as an open question for two months when it had
                # already been settled upstream: the rebuild puts it at 6.00,
                # and a CORRECTED_GOLD entry written against the raw 7.00 is
                # inert, because the rebuild overrides it.
                if item == "1c":
                    continue
                implied = maxes[item] - sum(named)
                if abs(implied - score) < 1e-9:
                    continue
                # A cell already declared has had this argument had about it.
                if H.gold_divergence(item, pid) or H.corrected_gold(item, pid):
                    continue
                out.append(
                    f"{item}/p{pid}: gold {score:g}, but its comment itemises "
                    f"{'+'.join(f'{n:g}' for n in named)} off a max of "
                    f"{maxes[item]:g}, which implies {implied:g}. Read the "
                    f"submission: a slip is CORRECTED_GOLD, an unwritten "
                    f"deduction is not")
    return out


def fixture_suspects() -> list[str]:
    """Cells whose miss looks like a mis-parsed box rather than a judgement.

    Two signatures, both requiring the cell to be wrong in EVERY recorded run,
    since an intermittent miss is a judgement wobbling:

      * we award NOTHING where gold awarded full marks — the grader found no
        creditable content in an answer the paper scorer credited completely
      * we award something where gold awarded ZERO — credit found in an answer
        judged empty of it

    Every other stable miss in this corpus is off by one deduction step, which is
    what a criterion boundary looks like. These two are what a box holding the
    wrong text looks like, and §1 puts a fixture read-out before any rubric work,
    because a criterion tuned against a mis-cut box measures the box.

    Declared cells are skipped: a divergence or correction means the disagreement
    has already been examined.
    """
    import gold as _gold
    import handouts as H

    # EVERY recorded side. This read the cli ledger alone, so a cell the WEB
    # missed in every run was never examined -- and a fixture defect is a fact
    # about the INPUT, which both paths read. Missing it on one path is the same
    # evidence whichever path noticed.
    per_side = {}
    for _s in SIDES:
        try:
            _r = records(_s)
        except Exception:
            continue
        if _r:
            per_side[_s] = _r
    loaders = {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}
    jobs = _jobs()
    out: list[str] = []
    seen: set = set()
    for item in sorted({i for recs in per_side.values() for i in recs}):
        # Which sides say this cell was wrong in every run, and where their
        # artifacts are. A signature has to hold on the side that reports it.
        sides_for_item = {s: recs[item] for s, recs in per_side.items()
                          if item in recs
                          and not recs[item].get("pending")
                          and recs[item].get("cells")}
        if not sides_for_item:
            continue
        rec = sides_for_item.get(DEFAULT_SIDE) or next(iter(sides_for_item.values()))
        h = jobs[item]["handout"]
        try:
            g = H.apply_corrected_gold(loaders[h](), h)
        except Exception:
            continue
        if item == "1c":
            import agreement_app as APP
            g, _ = APP.rebuild_gold_1c({p: dict(v) for p, v in g.items()})
        top = max(((g.get(p) or {}).get(item) or {}).get("score") or 0 for p in g)
        # Union of cells any side got wrong in every run, with the side that
        # said so -- so a web-only miss is examined instead of skipped.
        zero: dict[str, str] = {}
        for s, r in sides_for_item.items():
            for pid_s, right in (r.get("cells") or {}).items():
                if right == 0 and pid_s not in zero:
                    zero[pid_s] = s
        for pid_s in sorted(zero, key=int):
            side = zero[pid_s]
            runs_path = _runs_path(item, side)
            pid = int(pid_s)
            gs = ((g.get(pid) or {}).get(item) or {}).get("score")
            if gs is None or H.gold_divergence(item, pid):
                continue
            got = _scores_for(item, pid, runs_path)
            if not got or any(s is None for s in got):
                continue
            # Three runs cannot distinguish a stable miss from a coin, and
            # sending someone to read a fixture for a cell that is merely
            # unstable wastes the expensive step. Q2/p17 read 0/3 here and is
            # 10/18 across six sweeps. So ask every artifact that ever measured
            # this cell — the corollary in QUALITY_CONTROL.md, and cheaper than
            # either a probe or a fixture read.
            if _ever_right(item, pid, gs):
                continue
            if (item, pid) in seen:
                continue
            if gs == top and all(s == 0 for s in got):
                seen.add((item, pid))
                out.append(f"{item}/p{pid} [{side}]: gold {gs:g} (full marks) and "
                           f"we award 0 in every run — read the fixture before "
                           f"the rubric")
            elif gs == 0 and all(s > 0 for s in got):
                seen.add((item, pid))
                out.append(f"{item}/p{pid} [{side}]: gold 0 and we award "
                           f"{'/'.join(f'{s:g}' for s in got)} in every run — "
                           f"read the fixture before the rubric")
    return out


def _runs_path(item: str, side: str = DEFAULT_SIDE) -> str | None:
    """Where the recorded sweep's artifact is, derived from the ledger entry.

    The ledger stores the output DIRECTORY name it recorded from, so the artifact
    is findable without a second registry to keep in step.
    """
    import paths

    rec = entry(item, side)
    out = rec.get("out")
    if not out:
        return None
    p = paths.OUT / out / f"{item}.runs.json"
    return str(p) if p.exists() else None


def _ever_right(item: str, pid: int, gold_score: float) -> bool:
    """Has this cell EVER agreed with gold, in any artifact on disk?

    A cell that has been right before is unstable, not mis-parsed. Reading its
    fixture will find nothing, because the fixture did not change between the
    run that scored it right and the one that did not.
    """
    import glob

    import cross_path as _X
    import handouts as H
    import paths

    for path in glob.glob(str(paths.OUT / "*" / f"{item}.runs.json")):
        try:
            data = json.loads(Path(path).read_text())
        except (OSError, ValueError):
            continue
        for run in data.get("runs", []):
            for c in run.get("results", []):
                # Read through result_cell, which knows all THREE artifact
                # shapes. This matched `participant_id` directly -- the python
                # harness's key -- so it silently skipped every web artifact
                # (keyed `cell`) and every paper one (keyed `item_id`), while its
                # own docstring promised "any artifact on disk". A cell right on
                # the WEB and never on the cli therefore read as never-right, and
                # got reported as a fixture suspect: exactly the wasted fixture
                # read this function exists to prevent, caused by the function.
                if not isinstance(c, dict):
                    continue
                got = _X.result_cell(c)
                if got is None:
                    continue
                cell_item, cell_pid, s, _ = got
                if cell_item != item or cell_pid != pid:
                    continue
                if s is not None and H.scored_exactly(item, gold_score, s):
                    return True
    return False


def _scores_for(item: str, pid: int, runs_path: str | None) -> list:
    if not runs_path:
        return []
    try:
        data = json.loads(Path(runs_path).read_text())
    except OSError:
        return []
    return [c.get("score") for run in data["runs"] for c in run["results"]
            if c.get("participant_id") == pid]


def _staleness_lines() -> list[str]:
    """Staleness across every recorded side, ABSENT only for the default one.

    ABSENT on a paper side means that sweep has not been run, which is E28's
    business and not a gap in this item's measurement; reporting it here would
    put twenty-six standing entries on a list meant to be short enough to read.
    """
    out = []
    for side in SIDES:
        try:
            rows = status(side)
        except Exception:
            continue
        for item, state in rows:
            if not state.startswith(("ABSENT", "STALE", "pending")):
                continue
            if state.startswith("ABSENT") and side != DEFAULT_SIDE:
                continue
            where = "" if side == DEFAULT_SIDE else f" [{side}]"
            out.append(f"{item}{where}: {state}")
    return out


def preflight() -> dict[str, list[str]]:
    """Everything outstanding, in the order the guide says to address it.

    Probes are the last step, not the next one. A probe costs 24 calls to settle
    one cell, and settling a cell is worthless while the item's fixture is
    unread, its gold incoherent, or its declarations unexamined — the guide's
    step order exists because work done out of order measures the wrong thing.
    Leaving that ordering to memory is how a session spends an afternoon probing
    cells on an item whose gold row does not add up.
    """
    return {
        "1. fixture — read these boxes before any rubric work":
            fixture_suspects(),
        "2. gold — these rows do not reconcile with their own comments":
            gold_rows_that_do_not_reconcile(),
        # Step 2b, beside it and not after the model steps: a cell failing the
        # wrong slots is a gold-reading question, and tuning a criterion against
        # one measures the compensating error rather than the criterion.
        "2b. gold — cells failing DIFFERENT slots from the ones gold charged":
            gold_slot_disagreements(),
        "3. declarations — contradicted by a recorded measurement":
            declaration_conflicts(),
        # Every side, and labelled. This listed `status()` -- the cli default --
        # so a session reading preflight to decide what to sweep next could not
        # see that the WEB number for an item was measured against a different
        # prompt. The two can diverge: prompt_sha is side-aware, so a change to
        # an attribute the harness never reads moves only the web's fingerprint.
        "4. staleness — items not measured as currently configured":
            _staleness_lines(),
        "5. record — prose that disagrees with the ledger":
            prose_claims(),
        "6. leakage — rule blocks echoing the cohort, with no verdict filed":
            _leakage_pending(),
        "7. probes — items whose recorded prompt has unprobed moved cells":
            _unprobed_movers(),
    }


def _unprobed_movers() -> list[str]:
    """Items measured at a prompt whose moved cells were never probed.

    `compare_runs` withholds its verdict on these, so they are decisions that
    cannot honestly be made yet — neither keeping a change nor reverting it. They
    belong on the same list as an unread fixture for the same reason: work done
    on top of one is work done on a number nobody has established.
    """
    try:
        import compare_runs as CR
    except Exception:
        return []
    out = []
    # EVERY recorded side. A cell that moved on the web and was never probed is
    # the same unmade decision as one that moved on the cli, and the prompt_sha a
    # probe is filed against is per-side, so the cli's probes do not answer for
    # the web's movers.
    for side in SIDES:
        try:
            recs = records(side)
        except Exception:
            continue
        for item, rec in recs.items():
            pending = rec.get("unprobed_movers") or []
            if not pending:
                continue
            have = CR.probed_cells(item, rec.get("prompt_sha", ""))
            left = [p for p in pending if p not in have]
            if left:
                where = "" if side == DEFAULT_SIDE else f" [{side}]"
                out.append(
                    f"{item}{where}: moved cell(s) "
                    f"{', '.join('p%s' % p for p in left)} never probed at prompt "
                    f"{rec.get('prompt_sha')}")
    return out


def _leakage_pending() -> list[str]:
    """Rule prose that shares wording with the responses it is meant to judge.

    Listed here as well as gated in agreement.py because preflight is what a
    session reads to decide what to do next, and "our rule quotes the cell it
    was written to fix" belongs on that list — it invalidates a measurement
    rather than merely delaying one.
    """
    try:
        import leakage
        return leakage.unreviewed()
    except Exception:
        return []


def report() -> str:
    """The canonical table, generated. Paste this rather than retyping figures.

    Every number here is the median of the recorded runs over the recorded
    denominator, because those are the two things a reported figure is most
    easily wrong about: the best run instead of the median, and a denominator
    that has since grown. Handout 1's items were once reported as 12/14 and
    14/15 while their denominators were 19 and 20.
    """
    # EXPLICITLY TWO-SIDED. This printed one side -- the cli default -- with no
    # label, so the canonical table said "Q6 17/20" about a project that measures
    # every item twice, and a reader could not tell which scorer the figure came
    # from or that another number existed. Any side with data gets a row; the
    # side is always named, including when only one has any, because an unlabelled
    # number is how a single-path figure gets quoted as the project's result.
    per_side = {}
    for s in SIDES:
        try:
            recs = records(s)
        except Exception:
            continue
        if recs:
            per_side[s] = recs
    if not per_side:
        return "no measurements recorded"

    lines: list[str] = []
    totals = {s: [0, 0] for s in per_side}
    for h in (1, 2, 3):
        items = [i for i in sorted(_jobs()) if _jobs()[i]["handout"] == h]
        lines.append(f"Handout {h}")
        for item in items:
            got = {s: recs.get(item) for s, recs in per_side.items()
                   if recs.get(item)}
            if not got:
                lines.append(f"  {item:<5} not recorded on any side")
                continue
            for s in (x for x in SIDES if x in got):
                rec = got[s]
                if rec.get("pending"):
                    lines.append(f"  {item:<5} {s:<10} pending")
                    continue
                n, d = rec["numerator"], rec["denominator"]
                totals[s][0] += n
                totals[s][1] += d
                ex = f"  excl {rec['exclusions']}" if rec["exclusions"] else ""
                lines.append(
                    f"  {item:<5} {s:<10} {n:>3}/{d:<3} {100.0 * n / d:5.1f}%  "
                    f"median of {rec['runs']} runs {rec['run_totals']}{ex}")
    live = [(s, n, d) for s, (n, d) in totals.items() if d]
    if live:
        lines.append("")
        for s, n, d in live:
            lines.append(f"TOTAL {s:<10} {n}/{d} = {100.0 * n / d:.1f}% "
                         f"(sum of per-item medians; not a run of the whole corpus)")
        if len(live) > 1:
            lines.append("The per-side totals are NOT comparable unless every "
                         "item is recorded on both: a side missing an item is "
                         "missing its denominator too.")
    return "\n".join(lines)


def criterion_rows(item: str, check: str) -> str:
    """Every row of an item, GROUPED BY whether gold charged one criterion.

    Built because the same table was assembled by hand twice in one day and the
    second time it changed the answer. Reading only the cells we MISS points at
    tightening a criterion; the cells gold CREDITS are what say where the line
    actually falls. On Q3's `action_oriented` the three misses (p8, p16, p19) all
    justify actionability with something that is not a doing, which suggests
    demanding a doing -- and that would have cost p9, p14 and p18, three cells
    gold credits on ACCESS alone, because the sixteen credited rows show gold
    accepting "a car", "my gym is near my house", "access to the university's
    gym". The rule the corpus actually draws was activity-or-access, never time,
    and only the credited rows contain it.

    Prints, for each row: gold's score, whether its comment charges this
    criterion, what our own last recorded run answered for the check, and the
    student's text. Grouped so the contrast is the layout rather than something
    to hold in mind.
    """
    import re
    import agreement as A
    import gold as _gold
    import handouts as H

    h = _jobs()[item]["handout"]
    g = H.apply_corrected_gold(
        {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}[h](), h)
    rec = entry(item)
    ours: dict[int, list[str]] = {}
    art = rec.get("out")
    if art:
        for cand in Path("/home/pdeane/molly_data/out").glob(f"{art}*/{item}.runs.json"):
            try:
                runs = json.loads(cand.read_text())["runs"]
            except Exception:
                continue
            for run in runs:
                for c in run.get("results", []):
                    v = (c.get("checks") or {}).get(check)
                    if v:
                        ours.setdefault(c["participant_id"], []).append(v)
            break

    # The comment charges this criterion if it names it. Graders write the
    # criterion's own word ("For action", "Actionable"), so match on the check
    # name's parts rather than on a deduction code they never write.
    parts = re.split(r"[_\s]+", check)
    words = [w for w in parts if len(w) > 3]
    # "antecedent_1" -> also look at a field named ..._first, "_2" -> ..._second
    ordinal = {"1": "first", "2": "second"}.get(parts[-1])
    out = [f"  {item}: rows grouped by whether GOLD charges `{check}`",
           f"  (our verdicts from the recorded run set: {art or 'none recorded'})",
           "  GROUPING IS A HEURISTIC -- it matches the criterion's own words in",
           "  the grader's comment, and a comment can name the word for another",
           "  reason (Q4a/p17 says \"did not use the word 'antecedent'\" and is a",
           "  KEYWORD charge). The comment is printed so a mis-group is visible.", ""]
    groups: dict[str, list[str]] = {"CHARGED": [], "CREDITED": []}
    for pid in sorted(g):
        row = (g.get(pid) or {}).get(item) or {}
        if row.get("score") is None:
            continue
        fb = row.get("feedback") or ""
        charged = any(re.search(rf"\b{w}", fb, re.I) for w in words)
        try:
            fx = A.fixture_for(item, pid)
        except Exception:
            fx = {}
        text = ""
        for k, v in fx.items():
            if v and (any(w.lower() in k.lower() for w in words)
                      or (ordinal and k.lower().endswith(ordinal))):
                text = str(v)
                break
        mine = "/".join(sorted(set(ours.get(pid, [])))) or "-"
        fbs = " ".join((fb or "(no comment)").split())[:90]
        groups["CHARGED" if charged else "CREDITED"].append(
            f"    p{pid:<3} gold {row['score']:>5g}  we said {mine:<10} {text[:120]}\n"
            f"         gold: {fbs}")
    for name in ("CHARGED", "CREDITED"):
        out.append(f"  --- GOLD {name} ({len(groups[name])} rows) ---")
        out.extend(groups[name] or ["    (none)"])
        out.append("")
    return "\n".join(out)


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--status"]:
        worst = 0
        for item, s in status():
            print(f"  {item:<5} {s}")
            worst = max(worst, 2 if s.startswith(("ABSENT", "STALE")) else 0)
        return worst
    if a[:1] == ["--record"] and len(a) in (3, 4):
        # `--record ITEM ARTIFACT [SIDE]`. SIDE defaults to the web-prompt path,
        # so a two-sided sweep records the CLI half with an explicit `cli`.
        record(a[1], a[2], a[3] if len(a) == 4 else DEFAULT_SIDE)
        # The error profile is PRINTED, not offered. A median says how many cells
        # are wrong and never which judgement is wrong, and those point at
        # different work: Q1 spent a day on its merge rule while this profile,
        # over the same artifact, said 16 of 17 count errors were OVER-counts and
        # half of those sat on cells crediting ONE reason. Nobody runs an optional
        # diagnostic at the moment they think they already know the answer.
        try:
            print(error_profile(a[1], a[2]))
        except Exception as e:                       # never block a recording
            print(f"  (error profile unavailable: {type(e).__name__}: {e})")
        for c in declaration_conflicts():
            print(f"  DECLARATION EXPIRED? {c}")
        return 0
    if a[:1] == ["--errors"] and len(a) == 3:
        print(error_profile(a[1], a[2]))
        return 0
    if a[:1] == ["--criterion"] and len(a) == 3:
        print(criterion_rows(a[1], a[2]))
        return 0
    if a[:1] == ["--report"]:
        print(report())
        return 0
    if a[:1] == ["--preflight"]:
        # The active objective, printed wherever the gate is consulted. A goal
        # kept only in someone's head is a goal that gets swapped for a
        # different one mid-task without anything noticing.
        goals = LEDGER.parent / "GOALS.md"
        if goals.exists():
            lines = goals.read_text().splitlines()
            for i, line in enumerate(lines):
                if line.startswith("## ACTIVE"):
                    print(line[3:].strip())
                    for nxt in lines[i + 1:]:
                        if nxt.startswith("## "):
                            break
                        if nxt.strip().startswith("- [ ]"):
                            print(f"  {nxt.strip()}")
                    print()
                    break
        blockers = preflight()
        n = sum(len(v) for v in blockers.values())
        for heading, items in blockers.items():
            if not items:
                continue
            print(f"\n{heading}")
            for x in items:
                print(f"    {x}")
        if n:
            print(f"\n{n} outstanding item(s). Probes are the LAST step: settling "
                  f"one cell is worthless while an item's fixture is unread or its "
                  f"gold does not reconcile.")
        else:
            print("nothing outstanding — probes are the right next step")
        return 2 if n else 0
    if a[:1] == ["--conflicts"]:
        conflicts = declaration_conflicts()
        for c in conflicts:
            print(f"  {c}")
        if not conflicts:
            print("  no declaration is contradicted by a recorded measurement")
        return 2 if conflicts else 0
    print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
    print(__doc__.strip().splitlines()[3].strip(), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------------------
# E30: does our failing SLOT SET match the slots gold actually charged?
#
# Every rate in this project compares a cell's TOTAL. So a cell that fails the
# wrong slots in the right quantity reads as a match everywhere it is looked at,
# and Q6/p5 is the demonstration: gold charges state_a1, state_c1 and state_c2,
# we charge state_a1, state_c2 and affect_c2, and both come to 6.25. It read as a
# 6-of-6 success on the web and a divergence was proposed for retirement on that
# strength. cross_path --slots does not cover it either -- that compares the two
# SCORERS, which agree with each other here and differ from the grader together.
#
# COVERAGE IS PARTIAL AND DECLARED. Mapping a grader's prose to a slot key is not
# mechanical: "First consequence does not match 4c" is state_c1 only if you know
# this item's naming, and the graders wrote for students. So the table below
# covers the items whose phrasing has been read, every unmapped deduction is
# REPORTED rather than skipped, and the check says what fraction it examined. The
# failure being avoided is a check that looks thorough by ignoring what it cannot
# parse.
#
# ONE DEDUCTION CAN COVER SEVERAL SLOTS -- "did not state the second antecedent
# and how it is being changed" is two at 1.25 -- so a pattern maps to a SET and
# the amount validates the count. That validation is what catches a mapping
# mistake in this table, which is otherwise unfalsifiable prose.
GOLD_SLOT_CHARGES: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    # Ordered: more specific phrasings first, because several are substrings of
    # each other ("second consequence" appears in six different charges).
    # Q3's five SMART slots are 1 pt each and the graders' phrasings are close to
    # canonical, which makes this the cleanest table in the set.
    "Q3": [
        (r"for specific", ("specific",)),
        (r"for measurable|how are you tracking|how will you track|"
         r"did not say how you will measure", ("measurable",)),
        (r"for action|actionable", ("action_oriented",)),
        (r"missing realistic|for realistic", ("realistic",)),
        (r"for time.?bound", ("time_bound",)),
    ],
    # 1a: the baseline sentence is named explicitly, and the all-weeks charge is
    # 8 = four slots at 2.
    "1a": [
        (r"pertaining to the baseline week|sentece pertaining to the baseline",
         ("baseline_week",)),
        (r"did not discuss data for each week", 8.0,
         ("baseline_week", "week_1", "week_2", "week_3")),
    ],
    # 3: two example slots at 3 apiece, and "only provided one" names the second.
    "3": [
        (r"only provided one example of a change", 3.0, ("example_2",)),
    ],
    # 1c's five slots are 2 pts each, so a 2-pt charge is exactly one slot.
    "1c": [
        (r"missing graph title", ("title",)),
        (r"missing legend", ("legend",)),
        (r"missing x.?axis title", ("x_axis_label",)),
        (r"missing y.?axis title", ("y_axis_label",)),
    ],
    "Q4c": [
        (r"missing second consequence|listed the same consequence twice|"
         r"need more explanation on how your second example", ("consequence_2",)),
        (r"consequences are a direct result", 4.0,
         ("consequence_1", "consequence_2")),
    ],
    "Q4a": [
        (r"only provided one antecedent|second example is not an antecedent",
         ("antecedent_2",)),
        (r'did not use the word "antecedent"|did not use the word .antecedent.',
         ("keyword",)),
        (r"examples are not antecedents|an antecedent/trigger is something that "
         r"causes", ("antecedent_1", "antecedent_2")),
    ],
    "Q4b": [
        (r"did not say why it is a good choice to modify", ("modify_why",)),
        (r"did not provide two examples|these examples are not what you|"
         r"behaviors cannot be the same as your antecedents",
         ("behavior_1", "behavior_2")),
        (r"second example is not|second behavior|second example is the same",
         ("behavior_2",)),
    ],
    "Q2": [
        (r"missing a third reason", ("reason_3",)),
        (r"missing three reasons", ("reason_1", "reason_2", "reason_3")),
        (r"1 pt per reason", ("reason_1", "reason_2", "reason_3")),
        # Same phrase, two scopes, told apart by the amount: 2 points is the
        # inversion slot alone, 5 is that plus all three reasons.
        (r"wgb should be the opposite|wanted goal behavior should be the opposite",
         2.0, ("wgb_inverts_utb",)),
        (r"wgb should be the opposite|wanted goal behavior should be the opposite",
         5.0, ("wgb_inverts_utb", "reason_1", "reason_2", "reason_3")),
    ],
    "Q1": [
        (r"did not have one sentence describing your utb", ("utb_stated",)),
        (r"missing a third reason|only provided two reasons", ("reason_3",)),
        (r"missing two reasons|only provided one reason",
         ("reason_2", "reason_3")),
    ],
    "Q6": [
        (r"did not address your second antecedent being changed and how it will "
         r"affect your second consequence",
         ("state_a2", "change_a2", "state_c2", "affect_c2")),
        (r"did not state each consequence being affected and how it is being "
         r"affected", ("state_c1", "affect_c1", "state_c2", "affect_c2")),
        (r"did not state the second antecedent and how it is being changed",
         ("state_a2", "change_a2")),
        (r"did not state the second consequence and how it is being affected",
         ("state_c2", "affect_c2")),
        (r"did not say how each antecedent is being changed",
         ("change_a1", "change_a2")),
        (r"did not say how you would change your second antecedent",
         ("change_a2",)),
        (r"did not say how the first consequence.{0,20}is being affected",
         ("affect_c1",)),
        (r"did not say how the second consequence.{0,30}is being affected",
         ("affect_c2",)),
        # The grader charged 2.5 here, which is TWO slots at 1.25, so this
        # phrasing covers the second consequence PAIR and not just its effect
        # box. The amount is the evidence; the pairing is inferred from it, and
        # the amount check above is what forced the correction.
        (r"did not address how the second consequence is being affected",
         ("state_c2", "affect_c2")),
        (r"did not clarify the first consequence being affected", ("affect_c1",)),
        (r"did not clarify the second consequence being affected", ("affect_c2",)),
        # NEGATIVE LOOKAHEAD on "and how": the two-slot forms above are
        # "did not state the Nth consequence AND HOW it is being affected", and
        # these narrow ones must not also match them. They did, and first-match
        # ordering happened to give the right answer -- which is luck, not a
        # rule, and the ambiguity check exposed it on Q6/p7.
        (r"did not state the first consequence(?!.{0,30}and how).{0,20}being affected",
         ("state_c1",)),
        (r"did not state the second consequence(?!.{0,30}and how).{0,20}being affected",
         ("state_c2",)),
        (r"did not state a second consequence", ("state_c2",)),
        (r"first antecedent does not match", ("state_a1",)),
        (r"second antecedent is not the same", ("state_a2",)),
        (r"first consequence does not match", ("state_c1",)),
        # Also charged 2.5 -- the pair, not the state box alone.
        (r"second consequence is not the same", ("state_c2", "affect_c2")),
        (r"second consequence does not match", ("state_c2",)),
        (r"missing second antecedent", ("state_a2", "change_a2")),
        (r"missing second consequence", ("state_c2", "affect_c2")),
        # "both consequences" charged 2.5, not 5: this grader is counting one
        # slot per consequence, so it is the two STATE boxes. Read off the amount
        # rather than the wording, which would have given four slots.
        (r"missing both consequences", ("state_c1", "state_c2")),
    ],
}


# The cells KNOWN to fail different slots from the ones gold charged. Declared so
# a NEW one is a finding, listed so the eight already found are not mistaken for
# drift, and budgeted so the list can only shrink -- the same bargain as
# SLOT_RULE_BACKLOG.
#
# Eight of Q6's twelve mappable cells are here, which is the point of E30: the
# item records 17/20 on the cli and 18/20 on the web, and most of that agreement
# is compensating error at the slot level. Nothing before this check could say so.
#
# These are NOT declared as acceptable. Each is a real disagreement about which
# judgement is wrong, and the pattern across them is worth reading as one thing:
# on six of the eight we fail FEWER or DIFFERENT state_*/affect_* slots than the
# grader, and `affect_c2` and `state_a2` recur. That is the `refers_to` channel
# again -- memory/q6-matching-ceiling.md -- seen from the grader's side for the
# first time.
# Deductions that CANNOT map to a slot set, with the reason. Declared rather than
# quietly skipped: an unread charge was exactly the old behaviour.
# Cells whose AMBIGUOUS gold charge still disagrees with us on EVERY reading.
# Separate from GOLD_SLOT_DISAGREEMENTS_KNOWN because the finding is weaker in
# kind -- a count or a subset, not a named slot -- and mixing them would let a
# bounded finding be quoted as an exact one.
# E35. Criteria-derived cells where our deduction CODE differs from gold's.
GOLD_CODE_KNOWN: dict[tuple[str, int], str] = {
    # FOUR LENIENT, ONE HARSH, on the same judgement -- the operant TYPE. That
    # combination is the signature of an unstable derived check rather than a
    # threshold set wrong, and it is subgoal Q23's `matches_chosen_type` family
    # seen from the grader's side for the first time.
    ("NR", 15): "gold charges WRONG_TYPE (2) -- \"This is an example of PR.\" -- "
                "and we charge nothing: we accept the example as NR.",
    ("WK2", 3): "gold charges TYPE_MISMATCH (2) -- \"This is NP.\" -- and we "
                "charge nothing.",
    ("WK2", 15): "same as WK2/p3, phrased \"This is an example of NP.\"",
    ("DAY2", 7): "gold charges WRONG_BEHAVIOR (1) -- the plan targets the wrong "
                 "behavior -- and we charge nothing.",
    # THE ONE THAT RUNS THE OTHER WAY, and the more serious of the two directions:
    # a 4-point charge takes the whole item where gold takes 2.
    ("NR", 11): "gold charges WRONG_TYPE (2), saying the example IS operant "
                "conditioning but of the wrong type. We charge 4 -- NOT_OC, "
                "NOT_EXTERNAL_STIMULUS or BLANK, which the score alone cannot "
                "separate -- so we reject it as not operant conditioning at all. "
                "The cascade in agreement.score_oc returns at its FIRST failure, "
                "so a definitional criterion reading unmet hides the type "
                "question entirely: read which of the four criteria failed before "
                "touching the type rule.",
}


GOLD_SLOT_BOUNDS_KNOWN: dict[tuple[str, int], str] = {
    # 2a, FOUR CELLS, ONE SHAPE: gold charges one `how_*` slot -- "your third
    # sentece does not explain how your plan was successful" / "need more
    # explanation on how it was or was not successful" -- and we charge NOTHING.
    # Gold 4.0 against our 6.0 on all four. This is subgoal Q2's finding ("2a
    # over-credits hows_given: one rule, five cells") reached from the slot side,
    # and it is the strongest confirmation of that subgoal available: the
    # over-credit is not spread over the item, it is one uncharged slot.
    # Q4a/p9, ADDED 2026-09-01 by the E25 re-measurement, and the reason it is a
    # bounds entry rather than an exact one is that gold's comment -- "-2 pts: The
    # second example is not an antecedent" -- names the slot in prose the parser
    # cannot pin to a key, so the COUNT is certain and the identity is not.
    #
    # THE CELL INVERTED. Before the keyword conversion the cli scored it 3.0
    # (right) and the web 5.0 (wrong); now the web fails `antecedent_2` in all six
    # runs and scores 3.0, and the cli fails nothing and scores 5.0. Both sides are
    # stable at 6/6, so this is not noise. The web moved ONTO gold and the cli
    # moved OFF it, on a cell where nothing about `antecedent_2` was touched --
    # the only change either side saw is that `keyword` left the sheet.
    # Owned by Q32, whose entry records the inversion.
    ("Q4a", 9): "gold charges 1 slot (antecedent_2, in prose); cli fails none "
                "and scores 5.0 against gold 3.0, while the web fails it and "
                "agrees. Inverted by the E25 conversion -- see Q32.",
    ("2a", 1): "gold charges one how_* slot; we charge none. 4.0 vs 6.0.",
    ("2a", 13): "same as 2a/p1.",
    ("2a", 14): "same as 2a/p1, phrased as \"need more explanation\".",
    ("2a", 15): "same as 2a/p1, naming the second sentence rather than the third.",
    ("Q4a", 6): "gold charges one antecedent -- \"how does not stretching lead to "
                "lack of exercise?\" -- and we charge none.",
    ("Q4c", 16): "gold charges one consequence slot and we charge none. The "
                 "comment is Q4b's `modify_why` text on a Q4c row, so WHICH slot "
                 "is unknowable, but that one was charged is not. Also "
                 "PER_ITEM_EXCLUDEd on that ground.",
    # THE ONLY CELL IN THE CORPUS WHERE WE CHARGE MORE THAN GOLD.
    ("Q5", 4): "gold charges ONE example slot -- \"missing one reason why you "
               "continue to engage\" -- and we fail BOTH, scoring 0.0 against "
               "gold's 2.5. Every other disagreement in this accounting runs the "
               "other way, which makes this one worth reading first: it is the "
               "only evidence that the leniency is not uniform.",
}


GOLD_SLOT_UNMAPPABLE: dict[tuple[str, int], str] = {
    # THE COMMON CASE, and it is one shape: the grader named a defect without
    # saying WHICH of several interchangeable slots it lands on. "missing one
    # reason" on a three-reason item, "how does X lead to Y?" on a two-antecedent
    # item. The amount says how many, never which, and picking one would put a
    # wrong slot set into the comparison while looking precise.
    ("Q1", 1): "\"missing a reason for why you chose lack of sleep as your UTB\" "
               "-- one point, but Q1 has three interchangeable reason slots and "
               "the comment does not say which is missing.",
    ("Q1", 2): "same shape as Q1/p1: one reason short of three, which one unsaid.",
    ("Q2", 6): "\"missing one reason\" -- one of three reason slots, unspecified.",
    ("Q3", 3): "one -1 pt charge NAMES TWO SLOTS: \"For specific, ... For "
               "measurable, make sure you are tracking your specific goal.\" The "
               "cell's two charges cover three named slots, so which two were "
               "deducted is not recoverable. Found by the ambiguity check, which "
               "exists because first-match mapping had silently taken `specific` "
               "and dropped `measurable`.",
    ("Q4a", 3): "\"Need further explanation for how not eating is an antecedent\" "
                "-- 2 points, so exactly one antecedent slot, but the comment "
                "describes the response rather than naming first or second.",
    ("Q4a", 4): "same shape: \"how does grumpy emotions lead to lack of sleep?\" "
                "names the content, not the slot.",
    ("Q4a", 6): "same shape: \"how does not stretching lead to lack of exercise?\"",
    ("Q4c", 4): "\"specify what spending too much time awake means as a "
                "consequence\" -- 2 points, so one consequence slot, but the "
                "comment names the content and not which of the two.",
    ("Q4c", 16): "the comment is \"did not say if this behavior is a good choice "
                 "for you modify and why\", which is Q4b's `modify_why` test on a "
                 "Q4c row -- it names no Q4c slot at all. Either the grader "
                 "carried a comment across items or the charge belongs to Q4b; "
                 "this cell is ALSO PER_ITEM_EXCLUDEd on that ground, so the "
                 "exclusion and this entry are the same observation.",
    ("Q4a", 9): "AMBIGUOUS between antecedent_1 and antecedent_2 -- the phrasing "
                "matches both the single-slot and the both-slots patterns, and "
                "the amount does not separate them.",

    ("Q6", 4): "\"-1.5; missing one antecedent\" -- unmappable on TWO counts: it "
               "does not say WHICH antecedent, and 1.5 is not a whole number of "
               "this item's 1.25-point slots, so no slot set can account for it. "
               "NOT A TYPO FOR 1.25, checked rather than assumed: the row is "
               "score 6.0 = 10 - 2.5 - 1.5 and RECONCILES at 1.5, where 1.25 "
               "would imply 6.25. Correcting the deduction alone would break the "
               "row; correcting both would be re-scoring the cell, so this is not "
               "a CORRECTED_GOLD case -- that table is for a row whose arithmetic "
               "contradicts ITSELF, and this one does not. "
               "WHAT IT ACTUALLY SHOWS is that this grader apportioned Q6 "
               "differently from the sheet: the same comment charges 2.5 for "
               "\"missing both consequences\" -- 1.25 each -- and 1.5 for one "
               "antecedent, valuing antecedents above consequences where the "
               "sheet is a flat 1.25 x 8. Idiosyncratic to this row: every other "
               "Q6 comment charges an antecedent miss at 1.25.",
}


GOLD_SLOT_DISAGREEMENTS_KNOWN: dict[tuple[str, int], str] = {
    ("Q6", 2): "gold charges change_a2; we fail nothing. The +1.25 over-credit "
               "E15 predicted would move and did not.",
    ("Q6", 5): "gold charges state_a1/state_c1/state_c2; we charge "
               "state_a1/state_c2/affect_c2. Two disagreements cancelling -- see "
               "Q28. DUPLICATE_EFFECT_TIE_BREAK's reason is confirmed by this.",
    ("Q6", 6): "we miss state_a2, which gold charges.",
    ("Q6", 8): "gold also charges both change_* slots -- the A_NO_CHANGE "
               "divergence, already declared, seen here per slot.",
    ("Q6", 16): "gold charges affect_c2; we fail nothing.",
    # Q6/p9, p17 and p18 ALL LEFT on 2026-08-31: their slot sets now MATCH gold.
    # Three of the eight original entries were artefacts of a pattern overlap in
    # the Q6 table -- the narrow "did not state the second consequence being
    # affected" also matched the two-slot "...and how it is being affected", and
    # first-match ordering decided it. The ratchet reported all three as stale the
    # moment the overlap was fixed, which is what a ratchet is for, and it is the
    # argument for the ambiguity check that exposed the overlap.
    #
    # ARRIVED with the coverage extension to Q1, Q2, Q3, Q4a and Q4b. All six have
    # ONE shape: gold charges a slot we CREDIT, so we are lenient relative to the
    # grader at slot level even where the total agrees. Same direction as Q6's,
    # and worth reading as one finding rather than six.
    ("Q1", 10): "gold charges reason_3; we fail nothing.",
    ("Q2", 7): "gold charges wgb_inverts_utb on top of all three reasons; we fail "
               "the reasons only. Its 5-point charge covers the inversion slot "
               "too -- see the amount-keyed entry in GOLD_SLOT_CHARGES.",
    ("Q3", 10): "gold charges specific AND measurable; we fail specific only.",
    ("Q3", 19): "gold charges measurable AND action_oriented; we fail measurable "
                "only. action_oriented is subgoal Q9's slot.",
    ("Q4a", 14): "gold charges both antecedents; we fail antecedent_2 only.",
    ("1a", 1): "gold charges all four week slots -- \"did not discuss data for "
               "each week\" at 8 points -- and we fail baseline_week only. The "
               "widest slot-level gap found: three slots credited that the grader "
               "charged.",
    ("1a", 6): "gold charges baseline_week; we fail nothing.",
    ("Q4c", 9): "gold charges both consequences; we fail consequence_2 only.",
    ("Q4c", 20): "gold charges consequence_2; we fail nothing.",
    ("Q4b", 4): "gold charges both behaviors; we fail behavior_2 only -- the same "
                "second-box shape subgoal Q18 records for this item.",
    # Q6/p18 LEFT on 2026-08-31: its slot set now MATCHES gold. It was listed
    # while a pattern overlap in the Q6 table mis-mapped its charge -- the narrow
    # "did not state the second consequence being affected" pattern also matched
    # the two-slot "...and how it is being affected" form, and first-match
    # ordering decided it. The ratchet reported the entry as stale the moment the
    # overlap was fixed, which is what the ratchet is for.
}
GOLD_SLOT_DISAGREEMENTS_BUDGET = 15


def _table_hits(table, seg: str, amounts: list) -> list:
    """Which entries of a phrase table match one deduction segment.

    An entry is (pattern, slots) or (pattern, amount, slots). The three-element
    form matches only when the grader charged that amount, because THE SAME
    PHRASE CAN COVER DIFFERENT SCOPES: Q2's "your WGB should be the opposite of
    your UTB" is wgb_inverts_utb alone at 2 points and the whole item at 5. Without
    the amount the table cannot tell those apart, and the phrase-only version
    mapped the 5-point charge to a 2-point slot -- caught by the amount check,
    which is the check earning its place a second time.
    """
    import re

    got = []
    for entry in table:
        if len(entry) == 3:
            pat, want, slots = entry
            if not amounts or abs(amounts[0] - want) > 1e-9:
                continue
        else:
            pat, slots = entry
        if re.search(pat, seg, re.I):
            got.append(slots)
    return got


def _slots_are_not_comparable(item: str) -> bool:
    """Is this item's rubric slot set a DIFFERENT vocabulary from its web sheet's?

    A `derive_from_criteria` item's rubric carries the two or four checks the
    DEDUCTIONS are written against, while its web sheet asks fourteen criteria the
    CLI derives them from. "Which slots we failed" and "which slots gold charged"
    are then not the same kind of thing, and comparing them produces nonsense that
    looks like a finding: NR reported gold charging `is_nr` against our failing
    `demonstrates_type` and `targets_goal_behavior`, which is two naming schemes
    passing each other rather than a disagreement.

    Refused structurally rather than declared, because it is a fact about the
    item's shape. It is also why WK1, WK2, DAY1 and DAY2 could not be tabled: their
    gold speaks about the operant TYPE, which is a derived conclusion and not a
    slot on the sheet at all.
    """
    import handouts as H

    try:
        rub = H.config(_jobs()[item]["handout"])["rubric"].BY_ID[item]
    except Exception:
        return False
    return bool(rub.get("derive_from_criteria"))


# E35. The eight `derive_from_criteria` items cannot be compared slot by slot --
# their rubric carries the checks the DEDUCTIONS are written against while their
# sheet asks fourteen criteria the CLI derives those from. But they CAN be
# compared by deduction CODE, which is what both sides actually produce:
# agreement.score_oc is a cascade returning exactly one code, and gold's comments
# name the same three or four judgements.
#
# One table for all eight: they share a vocabulary, because they are the same
# question asked about four operant types and two cadences.
GOLD_CODE_CHARGES: list[tuple[str, str]] = [
    (r"not operant conditioning", "NOT_OC"),
    (r"this is (an example of )?(np|nr|pp|pr)\b", "WRONG_TYPE"),
    (r"make sure the behavior you are targeting", "WRONG_BEHAVIOR"),
]


def _cell_scores(item: str, pid: int, side: str = DEFAULT_SIDE) -> list:
    """Every recorded score for one cell, from the side's own artifact."""
    import cross_path as _X

    doc = _runs_doc(item, side)
    if doc is None:
        return []
    runs = doc.get("runs") or []
    out = []
    for run in runs:
        for r in (run.get("results") or []):
            got = _X.result_cell(r)
            if got and got[0] == item and got[1] == pid and got[2] is not None:
                out.append(got[2])
    return out


def gold_charged_code(item: str, pid: int):
    """(code, amount) gold's comment charges on a criteria-derived item, or None.

    The amount is what makes this checkable: WRONG_TYPE is 2 and NOT_OC is 4, so a
    phrase and an amount that disagree mean the table is wrong rather than the
    scorer -- the same guard the slot tables carry.
    """
    import re
    import gold as _gold
    import handouts as H

    if not _slots_are_not_comparable(item):
        return None
    h = _jobs()[item]["handout"]
    try:
        g = _corrected_gold(h)
        rub = H.config(h)["rubric"].BY_ID[item]
    except Exception:
        return None
    row = (g.get(pid) or {}).get(item) or {}
    fb = row.get("feedback") or ""
    amts = deductions_named(fb)
    if len(amts) != 1:
        return None            # more than one charge is a different shape
    # The comment must describe the score in force, as everywhere else here.
    if row.get("score") is None or abs(
            (rub["max"] - amts[0]) - row["score"]) > 1e-9:
        return None
    hits = [c for pat, c in GOLD_CODE_CHARGES if re.search(pat, fb, re.I)]
    if len(set(hits)) != 1:
        return None
    code = hits[0]
    # TYPE_MISMATCH is the cadence items' name for WRONG_TYPE. Same judgement,
    # different code, and the rubric is what says which exists on this item.
    codes = {d["code"]: d["pts"] for d in rub["deductions"]}
    if code == "WRONG_TYPE" and code not in codes and "TYPE_MISMATCH" in codes:
        code = "TYPE_MISMATCH"
    if code not in codes or abs(codes[code] - amts[0]) > 1e-9:
        return None            # phrase and amount disagree: the TABLE is wrong
    return code, amts[0]


def gold_charge_bounds(item: str, pid: int):
    """What gold's comment says about a cell even when the slots are AMBIGUOUS.

    Returns (definite, count) or None: `definite` is the slots named by segments
    that map unambiguously, and `count` is how many slots the whole comment
    charges, derived from the AMOUNTS. An ambiguous segment contributes to the
    count without contributing to `definite` -- "missing one reason" on a
    three-reason item is one slot, unknown which.

    WHY THIS EXISTS. GOLD_SLOT_UNMAPPABLE cells were skipped entirely, and 6 of
    the 24 skipped cells disagree with us on the TOTAL. Skipping is not
    accounting. Two things can be said without disambiguating anything:
      * if our failing set does not CONTAIN every definitely-charged slot, we
        credit a slot gold charged, whichever reading is right;
      * if the SIZE of our failing set differs from gold's count, the two
        disagree about how many slots failed, whichever ones they were.
    Q5/p4 is the case that motivated it: gold charges ONE of example_1/example_2
    and we fail BOTH, so we over-charge by a slot on every reading.
    """
    import re
    import gold as _gold
    import handouts as H
    import olx_prompts as O

    # A TABLE IS NOT REQUIRED. Bounds come from the AMOUNTS and the slot points,
    # so an item with no phrase table still yields a count -- which is how 2b,
    # D1, D2, Q5 and 1b get accounted for at all. Without a table `definite` is
    # simply empty, and the size comparison is the whole finding.
    table = GOLD_SLOT_CHARGES.get(item) or []
    if _slots_are_not_comparable(item):
        return None
    h = _jobs()[item]["handout"]
    try:
        g = _corrected_gold(h)
        spec, defs = O._slots_attr(h, O.ACTION[item])
        pts = {s["key"]: s["pts"] for s in O.parse_slots(spec, defs)
               if s.get("pts")}
    except Exception:
        return None
    row = (g.get(pid) or {}).get(item) or {}
    fb = row.get("feedback") or ""
    segs = [s for s in re.split(r"(?=-\s*\d)", fb) if re.match(r"-\s*\d", s)]
    if not segs:
        return None
    # Same reconcile guard as the other readers: a comment that does not describe
    # the score in force cannot bound anything either.
    top = max(((g.get(q) or {}).get(item) or {}).get("score") or 0 for q in g)
    if row.get("score") is None or abs(
            (top - sum(deductions_named(fb))) - row["score"]) > 1e-9:
        return None

    unit = min(pts.values()) if pts else None
    definite: set = set()
    count = 0
    for seg in segs:
        amt = deductions_named(seg)
        hits = _table_hits(table, seg, amt)
        if len(set(hits)) == 1:
            definite |= set(hits[0])
            count += len(hits[0])
            continue
        # Ambiguous or unmatched: the AMOUNT still says how many slots, provided
        # the item's slots are uniform. They are on every item tabled so far.
        if not amt or not pts:
            return None
        n = _slots_worth(amt[0], sorted(pts.values()))
        if n is None:
            return None       # the amount does not determine HOW MANY slots
        count += n
    return definite, count


def _slots_worth(amount: float, values: list):
    """How many slots an amount can be, or None if that is not determined.

    Every subset of the slot points that sums to the amount is a possible
    reading; if they all have the same SIZE, the count is known even though the
    membership is not. Q1's 1-point charge can only be one of its three 1-point
    reason slots -- utb_stated is 2 -- so the count is 1 while which reason is
    unknowable. Requiring uniform slot values instead, as the first version did,
    threw that away and returned nothing for every mixed-value item.
    """
    sizes = set()

    def walk(i: int, left: float, n: int):
        if abs(left) < 1e-9:
            sizes.add(n)
            return
        if left < -1e-9 or i >= len(values) or len(sizes) > 1:
            return
        walk(i + 1, left - values[i], n + 1)      # take this slot
        walk(i + 1, left, n)                      # skip it
    walk(0, amount, 0)
    return sizes.pop() if len(sizes) == 1 else None


def gold_charged_slots(item: str, pid: int):
    """The slots gold's comment charges for one cell, or None if it cannot be read.

    None means "no opinion", and the callers must treat it that way: either the
    item has no phrase table, or the comment itemises nothing, or a deduction did
    not map. Returning an empty set for those would assert that gold charged
    NOTHING, which is the opposite of not knowing.

    Extracted so declaration_conflicts and gold_slot_disagreements ask the same
    question of the same table. Two copies of this would drift, and the drift
    would be invisible: both would still produce a plausible slot set.
    """
    import re
    import gold as _gold
    import handouts as H

    table = GOLD_SLOT_CHARGES.get(item)
    if not table:
        return None
    if _slots_are_not_comparable(item):
        return None
    if (item, pid) in GOLD_SLOT_UNMAPPABLE:
        return None
    h = _jobs()[item]["handout"]
    try:
        g = _corrected_gold(h)
    except Exception:
        return None
    row = (g.get(pid) or {}).get(item) or {}
    fb = row.get("feedback") or ""
    segs = [s for s in re.split(r"(?=-\s*\d)", fb) if re.match(r"-\s*\d", s)]
    if not segs:
        return None

    # THE COMMENT MUST DESCRIBE THE SCORE IT IS BEING READ AGAINST. A corrected
    # cell keeps the grader's original prose, so a charge named there may be one
    # the correction deliberately removed -- Q4a/p17's comment docks the keyword
    # point and CORRECTED_GOLD[("Q4a", 17)] takes it back, because the graders
    # charged that point once in seven comparable cases. Reading the comment
    # anyway reported a charge we correctly do not make.
    #
    # Tested by arithmetic rather than by another declaration: if max minus the
    # named deductions does not equal the score in force, the itemisation is not
    # describing this score and the slot set derived from it is unusable. That
    # also covers Q6/p4, corrected the same day.
    score = row.get("score")
    top = max(((g.get(q) or {}).get(item) or {}).get("score") or 0 for q in g)
    named = sum(deductions_named(fb))
    if score is None or abs((top - named) - score) > 1e-9:
        return None
    charged: set = set()
    for seg in segs:
        # EVERY match, not the first. `next(...)` took the first pattern that hit
        # and silently dropped the rest, so a grader charging one point while
        # naming two slots -- Q3/p3's "For specific, ... For measurable, make sure
        # you are tracking your specific goal." -- mapped to `specific` alone and
        # passed the amount check, because one slot is one point on that item.
        # Silently wrong is worse than unmapped, so a segment naming more than one
        # distinct slot set is ambiguous and the whole cell goes unread.
        amt = deductions_named(seg)
        hits = _table_hits(table, seg, amt)
        if len(set(hits)) != 1:
            return None       # unmatched, or ambiguous between several slots
        charged |= set(hits[0])
    return charged


@functools.lru_cache(maxsize=None)
def _corrected_gold(handout: int, rebuild_1c: bool = False):
    """Corrected gold for one handout, loaded ONCE.

    gold_charged_slots, gold_charge_bounds and gold_charged_code each called
    apply_corrected_gold on every invocation, so a corpus-wide pass re-loaded and
    re-corrected the whole gold set once per CELL. That, not the artifact
    parsing, was the 42 seconds: memoising the artifacts first changed nothing,
    which is how the real cause was found rather than assumed.
    """
    import gold as _gold
    import handouts as H

    g = H.apply_corrected_gold(
        {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}[handout](), handout)
    if rebuild_1c:
        import agreement_app as _APP
        g, _ = _APP.rebuild_gold_1c({p_: dict(v) for p_, v in g.items()})
    return g


@functools.lru_cache(maxsize=None)
def _runs_doc(item: str, side: str):
    """The parsed runs artifact for one (item, side), read ONCE.

    _our_failing_slots and _cell_scores took a cell at a time and re-parsed the
    whole file for each, so a corpus-wide pass parsed the same multi-megabyte
    JSON twenty times per item -- 520 parses over the corpus.
    check_slot_sets_match_gold cost 42 seconds of an 80-second audit because of
    it, and the SELF-TEST runs that audit fifty-one times, which took the suite
    from fifteen minutes to over thirty-five.

    Cached on (item, side) rather than on the path, so a re-record during one
    process is not picked up -- that is correct here, because every caller is a
    read-only audit and an artifact does not change under a running audit. The
    self-test's source fingerprint is what catches a tree that moved.
    """
    path = _runs_path(item, side)
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


def _our_failing_slots(item: str, pid: int, side: str = DEFAULT_SIDE):
    """Which SCORED slots our recorded runs failed, per run, for one cell.

    Rebuilt through agreement.satisfied_map rather than read off the artifact,
    which stores only a `failed_slots` COUNT. Every key is wrapped in a dict on
    the way in: verdict_of returns "" for a bare string, so passing the artifact's
    {key: "met"} shape straight through marked every ungrouped slot unsatisfied
    and inflated the count from 3 to 6.
    """
    import agreement as A
    import olx_prompts as O

    doc = _runs_doc(item, side)
    if doc is None:
        return []
    try:
        spec = A.load_action(f"bmod_handout{_jobs()[item]['handout']}.olx",
                            O.ACTION[item])
        runs = doc["runs"]
    except Exception:
        return []
    scored = {s["key"] for s in spec["slots"] if s.get("pts") is not None}
    out = []
    for run in runs:
        for r in (run.get("results") or []):
            if r.get("participant_id") != pid:
                continue
            ch, ans = dict(r.get("checks") or {}), (r.get("answers") or {})
            rebuilt = {k: dict(verdict=v,
                               **({"refers_to": ans[k]} if k in ans else {}))
                       for k, v in ch.items()}
            sm = A.satisfied_map(spec, rebuilt)
            out.append(frozenset(k for k, ok in sm.items()
                                 if not ok and k in scored))
    return out


def gold_slot_disagreements() -> list[str]:
    """Cells where our failing slots differ from the slots gold charged.

    Reported even when the TOTAL agrees -- especially then, because that is the
    case nothing else can see.
    """
    import re
    import gold as _gold
    import handouts as H
    import olx_prompts as O

    out: list[str] = []
    examined = skipped = declared = 0
    seen_disagreeing: set = set()
    for item, table in sorted(GOLD_SLOT_CHARGES.items()):
        if _slots_are_not_comparable(item):
            continue          # see _slots_are_not_comparable
        h = _jobs()[item]["handout"]
        try:
            g = H.apply_corrected_gold(
                {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}[h](), h)
            spec = __import__("agreement").load_action(
                f"bmod_handout{h}.olx", O.ACTION[item])
        except Exception:
            continue
        pts = {s["key"]: s["pts"] for s in spec["slots"] if s.get("pts") is not None}
        for pid in sorted(g):
            row = (g.get(pid) or {}).get(item) or {}
            fb = (row.get("feedback") or "").strip()
            if not fb:
                continue
            # Split into deduction segments: each starts at a "-<amount>".
            segs = [s for s in re.split(r"(?=-\s*\d)", fb) if re.match(r"-\s*\d", s)]
            if not segs:
                continue
            # SAME GUARD AS gold_charged_slots: a comment that does not reconcile
            # with the score in force is not describing it, so neither its slot
            # set nor its amounts can be checked. Without this, Q4a/p17 reported
            # its keyword charge as a MAPPING error -- the mapping is right, the
            # comment simply predates CORRECTED_GOLD[("Q4a", 17)] taking that
            # point back.
            top_score = max(((g.get(q) or {}).get(item) or {}).get("score") or 0
                            for q in g)
            if (row.get("score") is None
                    or abs((top_score - sum(deductions_named(fb)))
                           - row["score"]) > 1e-9):
                continue

            charged: set = set()
            unmapped = []
            for seg in segs:
                amt = deductions_named(seg)
                hits = _table_hits(table, seg, amt)
                if len(set(hits)) > 1:
                    # Named several slots under one charge. Which ones the grader
                    # actually deducted for is not recoverable from the comment,
                    # and guessing would put a wrong slot set into the comparison.
                    unmapped.append(
                        f"AMBIGUOUS between {sorted({s for h in hits for s in h})}"
                        f": {seg.strip()[:44]}")
                    continue
                hit = hits[0] if hits else None
                if hit is None:
                    unmapped.append(seg.strip()[:60])
                    continue
                charged |= set(hit)
                # The amount says HOW MANY slots the charge covers. A mismatch is
                # a bug in the table above, not in the scorer, and saying so here
                # is what keeps the table honest.
                want = sum(pts.get(k, 0) for k in hit)
                if amt and abs(sum(amt[:1]) - want) > 1e-9:
                    out.append(
                        f"{item}/p{pid}: the table maps \"{seg.strip()[:44]}\" to "
                        f"{sorted(hit)} worth {want:g}, but the grader charged "
                        f"{amt[0]:g} — the MAPPING is wrong, not the score")
            if unmapped:
                skipped += 1
                if (item, pid) not in GOLD_SLOT_UNMAPPABLE:
                    out.append(
                        f"{item}/p{pid}: gold charges something the phrase table "
                        f"does not map — {unmapped}. Add it to GOLD_SLOT_CHARGES, "
                        f"or to GOLD_SLOT_UNMAPPABLE with the reason; an unread "
                        f"charge is not a passing cell")
                continue
            ours = _our_failing_slots(item, pid)
            if not ours:
                continue
            examined += 1
            stable = set.intersection(*[set(f) for f in ours]) if ours else set()
            if stable == charged:
                continue
            seen_disagreeing.add((item, pid))
            if (item, pid) in GOLD_SLOT_DISAGREEMENTS_KNOWN:
                declared += 1
                continue
            out.append(
                f"{item}/p{pid}: gold charges {sorted(charged)}, we fail "
                f"{sorted(stable)} in every run — differs on "
                f"{sorted(charged ^ stable)}. The TOTAL can still agree, which "
                f"is how this stayed invisible. Declare it in "
                f"GOLD_SLOT_DISAGREEMENTS_KNOWN with what is wrong, or fix it")

    # BOUNDED ACCOUNTING for the cells the exact comparison cannot read. Skipping
    # them was not accounting: 6 of the 24 skipped cells disagree with us on the
    # TOTAL and the check said nothing about any of them. Two statements survive
    # ambiguity -- see gold_charge_bounds.
    for item in sorted(_jobs()):
        if _slots_are_not_comparable(item):
            continue
        for pid in range(1, 21):
            if gold_charged_slots(item, pid) is not None:
                continue          # the exact comparison already covered it
            b = gold_charge_bounds(item, pid)
            if b is None or (item, pid) in GOLD_SLOT_BOUNDS_KNOWN:
                continue
            definite, count = b
            got = _our_failing_slots(item, pid)
            if not got:
                continue
            stable = set.intersection(*[set(f) for f in got])
            missed = sorted(definite - stable)
            if missed:
                out.append(
                    f"{item}/p{pid}: gold definitely charges {missed}, which we "
                    f"credit -- true on every reading of the ambiguous part of "
                    f"its comment. Declare it in GOLD_SLOT_BOUNDS_KNOWN or fix it")
            elif len(stable) != count:
                out.append(
                    f"{item}/p{pid}: gold charges {count} slot(s) and we fail "
                    f"{len(stable)} ({sorted(stable)}). WHICH slots gold meant is "
                    f"ambiguous; the COUNT is not, so the two disagree on every "
                    f"reading. Declare it in GOLD_SLOT_BOUNDS_KNOWN or fix it")

    # E35. CODE-LEVEL accounting for the eight criteria-derived items, which the
    # slot comparison refuses. Both sides charge exactly one deduction code here,
    # so the comparison is code against code -- and OUR code is recoverable from
    # the score, because every one of these items has max 4 and charges once.
    for item in sorted(_jobs()):
        if not _slots_are_not_comparable(item):
            continue
        try:
            rub = H.config(_jobs()[item]["handout"])["rubric"].BY_ID[item]
        except Exception:
            continue
        codes = {d["code"]: d["pts"] for d in rub["deductions"]}
        for pid in range(1, 21):
            got = gold_charged_code(item, pid)
            if got is None or (item, pid) in GOLD_CODE_KNOWN:
                continue
            code, amt = got
            preds = _cell_scores(item, pid)
            if not preds:
                continue
            ours = sorted(preds)[len(preds) // 2]
            our_amt = rub["max"] - ours
            if abs(our_amt - amt) < 1e-9:
                continue          # same size charge; the codes agree by amount
            # Which codes could OUR deduction be? Several share an amount, so the
            # honest report names the candidates rather than picking one.
            cand = sorted(c for c, v in codes.items()
                          if abs(v - our_amt) < 1e-9) or ["nothing"]
            out.append(
                f"{item}/p{pid}: gold charges {code} ({amt:g}); we charge "
                f"{our_amt:g} ({' or '.join(cand)}). Both sides charge ONE code on "
                f"this item, so the two disagree about WHICH judgement failed, not "
                f"just by how much. Declare it in GOLD_CODE_KNOWN or fix it")

    # A declaration that outlived its cell, and the ratchet.
    live = {k for k in GOLD_SLOT_DISAGREEMENTS_KNOWN if k[0] in GOLD_SLOT_CHARGES}
    for item, pid in sorted(live - seen_disagreeing):
        out.append(
            f"GOLD_SLOT_DISAGREEMENTS_KNOWN names {item}/p{pid}, but its slot set "
            f"now MATCHES gold — drop the entry and lower the budget")
    n = len(GOLD_SLOT_DISAGREEMENTS_KNOWN)
    if n != GOLD_SLOT_DISAGREEMENTS_BUDGET:
        verb = "grew to" if n > GOLD_SLOT_DISAGREEMENTS_BUDGET else "is down to"
        out.append(f"GOLD_SLOT_DISAGREEMENTS_KNOWN {verb} {n} against a budget of "
                   f"{GOLD_SLOT_DISAGREEMENTS_BUDGET} -- it may only fall")
    return out


# ---------------------------------------------------------------------------
# E37. Every cell we get WRONG must have somewhere to live.
#
# The accounting that produced this was done by hand: 34 wrong cells found and
# mapped, 16 orphans chased to none. Doing it once proves nothing about tomorrow,
# because a cell moves in or out of "wrong" whenever a rule is edited and nothing
# reports the move. Both directions matter, and closing a subgoal is a third:
# closing E35 orphaned five cells and it was noticed by reading, not by a check.
def _live_subgoal_owners() -> dict:
    """{`item/pN`: [subgoal ids]} for every OPEN subgoal that names a cell.

    Closed subgoals do not count. A finished goal is not a place for a live
    problem to live, and treating it as one is how five cells were orphaned by a
    closure that looked clean.

    E30 is excluded by name: it is the ACCOUNTING, and every cell appears in it by
    construction, so counting it as an owner would make this check vacuous.
    """
    import re

    try:
        text = (Path(__file__).resolve().parent / "GOALS.md").read_text()
    except OSError:
        return {}
    # TWO KINDS OF MENTION, and the asymmetry between them is the point.
    #
    # ANY mention makes a subgoal an OWNER: a subgoal listing cells is a home for
    # them, and being generous here avoids nagging about a cell that is plainly
    # accounted for.
    #
    # Only a TITLE mention makes the subgoal ABOUT that cell. A body mention is
    # very often history or a control -- Q19 names 1a/p15 and Q4b/p8 precisely
    # because we score them RIGHT, and a line about "gold corrections earned by
    # control sets" names D2/p11 and WK1/p7 as past work. Flagging those as
    # "evidence has gone" would report the subgoal for citing its own controls.
    # Q11 is what the strict form is for: its TITLE is "Q3/p13: `realistic`
    # over-charged", and that cell now scores right.
    owners: dict = {"any": {}, "title": {}}
    current = None
    for line in text.splitlines():
        m = re.match(r"- \[( |x)\] ([EQ]\d+)\.", line)
        is_title = bool(m)
        if m:
            current = None if m.group(1) == "x" or m.group(2) == "E30" else m.group(2)
        if current is None:
            continue
        for cell in re.findall(r"\b([A-Za-z0-9]{1,4})/p(\d{1,2})\b", line):
            key = f"{cell[0]}/p{cell[1]}"
            owners["any"].setdefault(key, []).append(current)
            if is_title:
                owners["title"].setdefault(key, []).append(current)
    return owners


def _wrong_cells() -> list:
    """(item, pid, side, gold, ours) for every cell wrong at the recorded median.

    Both sides, because a cell wrong on the web and right on the cli is still a
    cell we get wrong -- and reading one side is the mistake the whole
    both-sides sweep of 2026-08-31 was about.
    """
    import handouts as H

    out = []
    for item in sorted(_jobs()):
        h = _jobs()[item]["handout"]
        try:
            g = _corrected_gold(h, rebuild_1c=(item == "1c"))
        except Exception:
            continue
        excluded = set(exclusions(item))
        for pid in sorted(g):
            if pid in excluded:
                continue
            target = ((g.get(pid) or {}).get(item) or {}).get("score")
            if target is None:
                continue
            for side in SIDES:
                scores = _cell_scores(item, pid, side)
                if not scores:
                    continue
                ours = sorted(scores)[len(scores) // 2]
                if not H.scored_exactly(item, target, ours):
                    out.append((item, pid, side, target, ours))
    return out


def wrong_cells_without_an_owner() -> list[str]:
    """Cells we get wrong that no live subgoal and no declaration accounts for."""
    import handouts as H

    owned = _live_subgoal_owners()
    owners, subjects = owned["any"], owned["title"]
    wrong = _wrong_cells()
    seen: set = set()
    out: list[str] = []
    for item, pid, side, target, ours in wrong:
        key = f"{item}/p{pid}"
        if key in seen:
            continue
        seen.add(key)
        if owners.get(key):
            continue
        # A DECLARED MISS IS NOT AN ORPHAN. GOLD_DIVERGENCES already carries the
        # reason we miss the cell on purpose; demanding a QC subgoal too would be
        # two names for one claim.
        if H.gold_divergence(item, pid):
            continue
        out.append(
            f"{key} is WRONG on {side} -- gold {target:g}, we record {ours:g} -- "
            f"and no OPEN subgoal names it. Every cell we get wrong needs "
            f"somewhere to live, or the next sweep buries it in a median. Name it "
            f"in the subgoal that owns its shape, or declare it")

    # The other direction: a subgoal citing a cell that has stopped being wrong.
    still_wrong = {f"{i}/p{p}" for i, p, *_ in wrong}
    measured_cells = set()
    for item in sorted(_jobs()):
        for pid in range(1, 21):
            if _cell_scores(item, pid):
                measured_cells.add(f"{item}/p{pid}")
    # A CELL CAN BE RIGHT AT THE TOTAL AND STILL BE A LIVE FINDING. Q19 names
    # 1a/p1 because we credit three week slots the grader charged, and the two
    # errors cancel to the same total -- which is the whole point of the slot
    # accounting. Treating "total agrees" as "problem gone" would have retired the
    # cells that exist precisely because the total hides them.
    declared_at_slot_level = (set(GOLD_SLOT_DISAGREEMENTS_KNOWN)
                              | set(GOLD_SLOT_BOUNDS_KNOWN)
                              | set(GOLD_CODE_KNOWN))
    slot_live = {f"{i}/p{p_}" for i, p_ in declared_at_slot_level}
    for key, who in sorted(subjects.items()):
        if key in still_wrong or key not in measured_cells or key in slot_live:
            continue
        out.append(
            f"{key} is named by OPEN subgoal(s) {sorted(set(who))} but now scores "
            f"RIGHT at the recorded median on every side. The evidence the "
            f"subgoal cites has gone: re-read it, and drop the cell or close the "
            f"subgoal")
    return out
