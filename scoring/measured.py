"""The measurement ledger: which items were measured, at which prompt, on which cells.

    python3 measured.py --status                 what is stale, what is pending
    python3 measured.py --record Q1 OUT/Q1.runs.json    after a sweep of Q1
    python3 measured.py --refusals Q4b                 refusals vs gold's itemisation
    python3 measured.py --silent-refusals              silent full marks we refuse, and their comparators

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
def _python_read_attrs() -> frozenset:
    """Which <LLMAction> attributes agreement.py actually reads off the open tag.

    DERIVED from its source, not listed here, so it cannot go stale: the day that
    side starts reading a new attribute, that attribute starts counting toward its
    fingerprint automatically.

    THREE WAYS IT READS ONE, and the first version knew only about the first --
    which is subgoal E38. `_attr(open_tag, "X")` is the helper, but `slots`,
    `verdicts`, `equals`, `cover` and `derived` each have a bespoke parser with
    its own `re.search(r'X="...')`, and `excluded_keys` reads EVERY
    schema-excluding primitive dynamically off the registry. Those five changed
    what the side sends while leaving its fingerprint byte-identical, so a
    measurement could go stale in silence -- and nearly did under E25, which
    edited `slots=` and `derived=` and was flagged only because the prompt body
    moved in the same commit.
    """
    src = (Path(__file__).resolve().parent / "agreement.py").read_text()
    out = set(re.findall(r'_attr\(open_tag,\s*"([^"]+)"\)', src))
    # the bespoke parsers: `re.search(r'X="([^"]*)"', open_tag ...)`
    out |= set(re.findall(r"""re\.search\(r?['"]\\?b?(\w+)=\\?["']""", src))
    # `excluded_keys` builds its pattern from the registry, so every
    # schema-excluding primitive is read whether or not it is named in source.
    try:
        import olx_prompts as _op

        out |= set(_op.primitive_attrs(excluding_keys=True))
    except Exception:
        pass
    # `target` is read to locate the feedback element, not to score with, and it
    # is not part of what the model is sent.
    return frozenset(a for a in out if a not in ("target",))


def _olx_only_visible(section: str) -> str:
    """The section as the CLI SEES it: prompt bodies plus the attributes it reads.

    Everything else on the open tag reaches the CLI from the RUBRIC, not the OLX
    -- `max`, `slots`, `cover`, `equals`, `derived`, `showChecks`. Hashing them
    into the CLI's fingerprint reports a CLI measurement as stale when a olx-only
    attribute changed, which is a false positive in the expensive direction: it
    asks for a re-run of a side that cannot have moved.

    That is not hypothetical. Adding `max="5"` to Q4a -- a olx-only fix for a
    olx-only defect, since the CLI takes the item max from `item["max"]` -- flagged
    the CLI side STALE PROMPT and made cross_path refuse a comparison that was
    perfectly valid.
    """
    keep = _python_read_attrs()

    def _one(m: re.Match) -> str:
        tag = m.group(0)
        return "<LLMAction" + "".join(
            ' %s="%s"' % (n, v)
            for n, v in re.findall(r'(?:^|\s)(\w+)="([^"]*)"', tag)
            if n in keep) + ">"

    return re.sub(r"<LLMAction\b[^>]*>", _one, section, flags=re.S)


def prompt_sha(item: str, side: str | None = None,
               olx_text: str | None = None) -> str:
    """SHA-256 of the OLX text that item's grader is served, to 12 hex chars.

    `side="python"` hashes only what agreement.py consumes -- see
    `_olx_only_visible`. Omit it for the `olx` side, which is served the tag
    entire.
    """
    jobs = _jobs()
    job = jobs[item]
    sid = job["screen"].split("/")[-1]
    # `olx_text` lets a caller hash a HISTORICAL revision -- the .olx as it stood
    # at the commit an artifact recorded -- which is what re-stamping a
    # measurement against git history needs. Omitted, it reads the working tree.
    text = olx_text if olx_text is not None else _olx(job["handout"])
    screen_ids = {j["screen"].split("/")[-1] for j in jobs.values()
                  if j["handout"] == job["handout"]}
    bounds = _section_bounds(text, screen_ids)
    if sid not in bounds:
        raise KeyError(f"{item}: no <Vertical id=\"{sid}\"> in handout "
                       f"{job['handout']}'s OLX")
    a, b = bounds[sid]
    section = text[a:b]
    if side == "python":
        section = _olx_only_visible(section)
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
SIDES = ("olx", "python", "paper", "paper_opus")
DEFAULT_SIDE = "python"


def _migrate(led: dict) -> dict:
    """Fold a pre-side ledger into the per-side shape, in memory.

    The old entry was the record itself: {"numerator": ..., "prompt_sha": ...}.
    The new one is {"olx": {...}, "python": {...}} -- spelled `web` and `cli` until
    the rename of 2026-09-01, which this function also folds -- because a
    two-sided sweep measures
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
        elif isinstance(rec, dict):
            # The sides were called `web` and `cli` until 2026-09-01. `cli`
            # collided with the `--backend cli` PROVIDER -- which is Opus, not
            # the shipped model -- and that collision is how an Opus run came to
            # be recorded as the python column. The names now say whose rules
            # score the sheet and cannot be read as a provider flag.
            #
            # Migrated on READ, by shape, like the pre-side fold above: a ledger
            # or a hand-edit still carrying the old key is honoured rather than
            # having that column silently disappear.
            for was, now in (("web", "olx"), ("cli", "python")):
                if was in rec and now not in rec:
                    rec[now] = rec.pop(was)
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
        # PER SIDE. A olx-only attribute changing must not report the CLI's
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
                       "prompt_sha_python": prompt_sha(it, "python")}
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


# What each SIDE contracts to be, enforced when an artifact is recorded.
#
#   ("app"|"python", model)
#
# "app" is agreement_app.py, whose results are keyed `cell` and whose score is a
# FRACTION of sheet_max; "python" is agreement.py or score.py, keyed
# `participant_id` with absolute points. See cross_path.result_cell, which is
# where both shapes are read.
SIDE_CONTRACT = {
    "olx":        ("olx_app",       "gpt-5-mini"),
    "python":     ("olx_python",    "gpt-5-mini"),
    "paper":      ("rubric_python", "gpt-5-mini"),
    "paper_opus": ("rubric_python", "opus"),
}


def _artifact_program(doc: dict) -> str:
    """Which program wrote this artifact: the three are told apart by shape.

    THE LANGUAGE IS NOT THE DISCRIMINATOR, and naming it "python" was a trap
    worth removing: agreement.py and score.py are BOTH Python, so a contract
    demanding "python" would have accepted a paper-scorer artifact into the
    `python` column -- the column that exists to be compared against `olx` on
    equal terms. What separates them is the PROMPT SOURCE.

        olx_app        results keyed `cell`, score a FRACTION of `sheet_max`
        olx_python     results keyed `participant_id`, absolute points
        rubric_python  no `runs` array at all -- score.py writes one
                       `participant_{pid:03d}.json` per participant, carrying
                       `items` and `scored_total`

    That last one is why no paper artifact has ever been recordable here, and
    what subgoal E28 is for. It is detected rather than assumed absent, so the
    day score.py grows a runs.json the contract already refuses it.
    """
    if "runs" not in doc:
        if "items" in doc or "scored_total" in doc:
            return "rubric_python"
        return ""
    for run in doc.get("runs") or ():
        for r in run.get("results") or ():
            # score.py FOLDED by paper_runs.py: it grows a `runs` array, so the
            # no-runs test above cannot see it, and its results are keyed neither
            # `cell` nor `participant_id` but `_pid` + `credit_checks`. Without
            # this branch the function returned "" for a folded paper artifact,
            # and "" SKIPS the program check -- so the one shape most likely to
            # be filed under the wrong side was the one shape nothing objected
            # to. Found by folding the first real paper sweep, not by reasoning.
            if "credit_checks" in r or ("_pid" in r and "item_id" in r):
                return "rubric_python"
            if "cell" in r:
                return "olx_app"
            if "participant_id" in r:
                # `response_chars` is agreement.py's own field. Absent, the entry
                # is still keyed like agreement.py's, so it is read as such --
                # but a rubric_python record reaching here would have been caught
                # by the `runs` test above.
                return "olx_python"
    return ""




def _check_side_contract(side: str, doc: dict, runs_path: str) -> list[str]:
    """Does this artifact come from the program and model the side promises?

    THE DEFAULTS ARE ENFORCED HERE RATHER THAN REMEMBERED. A sweep is
    gpt-5-mini unless Opus is asked for, and `cli` means the python scorer
    running the SAME model as the web so the comparison isolates the PROGRAM.
    Opus belongs to `paper_opus`, which exists precisely so a model change and a
    path change are never recorded as one number.

    Both halves were violated on 2026-09-01 and neither was noticed at the time:
    `agreement.py --backend cli` (Opus) was recorded as `cli`, and
    `agreement.py --backend lo` was recorded as `web`, which is agreement_app.py.
    The ledger then held one number from the wrong model and one from the wrong
    program, and the analysis built on top concluded that the web/cli axis was
    model-versus-model -- a conclusion produced entirely by the mislabelling.
    """
    want_shape, want_model = SIDE_CONTRACT[side]
    era = doc.get("era") or {}
    got_model = (era.get("model") or "").strip()
    got_shape = _artifact_program(doc)
    out = []
    if got_shape and got_shape != want_shape:
        was = {"olx_app": "agreement_app.py (the OLX prompt, scored by the shipped grader)",
               "olx_python": "agreement.py (the OLX prompt, scored in Python)",
               "rubric_python": "score.py (the RUBRIC prompt, scored in Python)"}
        out.append(
            f"side {side!r} must be recorded from {was[want_shape]}, but "
            f"{runs_path} was written by {was[got_shape]} (results are keyed "
            f"{'`cell`' if got_shape == 'olx_app' else '`participant_id`'})")
    if not got_model:
        out.append(
            f"{runs_path} does not say which model produced it, so it cannot be "
            f"recorded against side {side!r}. Artifacts written before "
            f"agreement._era_for passed its backend are all unstamped or stamped "
            f"with the deployment id regardless of `--backend`; re-sweep, or "
            f"stamp `era.model` by hand if the run's log settles it")
    elif got_model != want_model:
        out.append(
            f"side {side!r} is the {want_model} column and {runs_path} ran on "
            f"{got_model!r}. A sweep is gpt-5-mini unless Opus was asked for, and "
            f"an Opus run of the python scorer belongs to `paper_opus`, not here "
            f"-- recording it as {side!r} varies the model and the path at once")
    return out


def _out_pointer(runs_path: str) -> str:
    """Where an artifact lives, as a path relative to `paths.OUT`.

    Falls back to the bare directory name for anything outside that tree, which
    is what every pre-2026-09-01 entry holds and what `_runs_doc` still resolves.
    """
    import paths as _p

    d = Path(runs_path).resolve().parent
    try:
        return str(d.relative_to(Path(_p.OUT).resolve()))
    except ValueError:
        return d.name


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
    doc = json.loads(Path(runs_path).read_text())
    if side not in SIDE_CONTRACT:
        raise SystemExit(f"unknown side {side!r}; expected one of {SIDES}")
    bad = _check_side_contract(side, doc, runs_path)
    if bad and os.environ.get("MEASURED_ALLOW_OFF_CONTRACT") != "1":
        raise SystemExit(
            "\n".join(f"REFUSED: {b}" for b in bad)
            + "\n  Set MEASURED_ALLOW_OFF_CONTRACT=1 to record it anyway, and say "
              "in the ledger entry why the number is worth keeping off-contract.")
    for run in doc["runs"]:
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
        # The artifact's directory RELATIVE TO paths.OUT, not just its basename.
        # A basename is enough only while every sweep writes into a flat
        # `out/<dir>/`, and sweep_paper.sh does not: it folds into
        # `out/<dir>/runs/`, so the basename came out as the literal "runs" and
        # `_runs_doc` looked for `out/runs/<item>.runs.json`. The paper column was
        # RECORDED and its per-cell data unreachable -- which the ownership check
        # then read as "nothing wrong on that side", silently, on five wrong cells.
        "out": _out_pointer(runs_path),
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
    # PRINTED ON EVERY RECORD, and it takes no `side`: the report pools the
    # two OLX-prompt halves, so recording either one shows the same honest
    # spread rather than that half's flattering median.
    print(sweep_summary(item))


def sweep_summary(item: str) -> str:
    """What a sweep actually produced: the SPREAD of scores and per-check accuracy.

    NEITHER A MEDIAN NOR A SIDE SPLIT, and both exclusions are deliberate.

    THE MEDIAN HERE IS OVER ACTUAL SCORES, which is the distinction that matters.
    The ledger's headline is a median taken PER CELL and then counted, so a cell
    right in seven runs of twelve is scored as simply right; 2a read 20 of 20 on
    2026-09-03 that way while no run above 20 existed and six runs scored 18.
    This one is the median of the runs that actually happened -- 18.5 for that
    same sweep -- reported beside the range, the mean and the distribution,
    because no single number carries a spread.

    And it does not report olx against python. The two are one sample drawn
    twice -- same prompt, same model -- so a per-side figure throws away half the
    observations and invites divergence claims one observation apart. Worse, a
    six-run median of a 3-3 split lands on a value no run produced and that an
    item's increment may not even permit. Everything here pools the twelve.

    PER-CHECK ACCURACY needs gold's expectation per slot, which is determinate in
    two situations and no others: gold awarded the maximum, so every scored slot
    must be met; or gold's comment itemises, so `gold_charged_slots` names the
    ones it charged. Cells where gold charged something and named nothing are
    counted as INDETERMINATE and reported as such rather than guessed at, on the
    same principle as `gold_charged_slots` returning None.
    """
    import collections
    import statistics

    import agreement as A
    import handouts as H
    import olx_prompts as O

    h = _jobs()[item]["handout"]
    g = _corrected_gold(h)
    try:
        spec = A.load_action(f"bmod_handout{h}.olx", O.ACTION[item])
        # GATES INCLUDED. They carry no points and can zero the item, so a
        # per-check table without them omits its most expensive checks -- see
        # _charging_slots. What they cannot do is be compared against a PARTIAL
        # gold comment, because gold's vocabulary has no word for a gate; that
        # restriction is applied per cell below, not by dropping them here.
        scored = [sl["key"] for sl in spec["slots"]
                  if sl.get("pts") is not None or sl.get("gates")]
        top = {i["id"]: i["max"] for i in H.config(h)["rubric"].ITEMS}[item]
    except Exception as e:
        return f"  (cannot read {item}'s sheet: {type(e).__name__}: {e})"

    gold, drop = {}, set(exclusions(item))
    for pid in g:
        row = (g.get(pid) or {}).get(item) or {}
        if pid not in drop and row.get("score") is not None:
            gold[pid] = row["score"]

    # One matrix of scores, pooling the two OLX-prompt sides as one sample.
    cols: list = []
    for sd in POOLED_OLX_PROMPT:
        got = {pid: _cell_scores(item, pid, sd) for pid in gold}
        n = min((len(v) for v in got.values() if v), default=0)
        for r in range(n):
            cols.append({pid: got[pid][r] for pid in gold if got[pid]})
    if not cols:
        return f"  (no pooled run data for {item})"

    per_run = [sum(1 for pid, sc in col.items()
                   if H.scored_exactly(item, gold[pid], sc)) for col in cols]
    dist = collections.Counter(per_run)
    N = len(gold)
    out = [f"  {item}: {len(cols)} runs pooled over {N} cells "
           f"({' + '.join(POOLED_OLX_PROMPT)} as one sample)",
           "",
           "  CELLS CORRECT PER RUN",
           "    " + " ".join(str(x) for x in sorted(per_run)),
           f"    range {min(per_run)}-{max(per_run)} of {N}   "
           f"median {statistics.median(per_run):g}   "
           f"mean {statistics.mean(per_run):.1f} ({statistics.mean(per_run)/N:.1%})",
           "    " + ", ".join(f"{k} x{dist[k]}" for k in sorted(dist)),
           ""]

    # Gold's implied verdict per slot, where it is determinate at all.
    expect, indet = {}, []
    for pid, sc in gold.items():
        if abs(sc - top) < 1e-9:
            expect[pid] = {k: True for k in scored}
            continue
        named = gold_charged_slots(item, pid)
        if named is None:
            indet.append(pid)
        else:
            # ONLY THE SLOTS GOLD COULD HAVE NAMED. On a FULL-MARKS cell above,
            # every check passing is implied whatever its kind, so gates are
            # determinate there and that is where a gate false-positive shows up
            # (NR/p20, DAY2/p8). On a partial-credit cell the expectation is read
            # off the grader's prose, and a slot outside that vocabulary would be
            # scored as expected-to-pass by default -- turning every correct gate
            # refusal into a false charge. Left out instead, per
            # _gold_nameable_slots.
            vocab = _gold_nameable_slots(item)
            expect[pid] = {k: (k not in named) for k in scored
                           if not vocab or k in vocab}

    out.append("  PERCENT CORRECT BY CHECK")
    tally = {k: [0, 0, 0] for k in scored}          # n, correct, false-charge
    for sd in POOLED_OLX_PROMPT:
        for pid in expect:
            for failed in _our_failing_slots(item, pid, sd):
                for k in expect[pid]:          # not `scored`: a cell contributes
                    want = expect[pid][k]      # only the slots it can speak to
                    ours = k not in failed
                    tally[k][0] += 1
                    if ours == want:
                        tally[k][1] += 1
                    elif want:
                        tally[k][2] += 1
    width = max((len(k) for k in scored), default=8)
    for k in scored:
        n_, c_, f_ = tally[k]
        if not n_:
            out.append(f"    {k:<{width}}  no comparable observations")
            continue
        out.append(f"    {k:<{width}}  {c_:>4}/{n_:<4} {c_/n_:>6.1%}   "
                   f"charged where gold credits: {f_}, "
                   f"credited where gold charges: {n_ - c_ - f_}")
    out.append(f"    determinate on {len(expect)} of {N} cells" +
               (f"; INDETERMINATE on {sorted(indet)} -- gold charged there and "
                f"named no slot, so no per-check expectation exists"
                if indet else ""))
    return "\n".join(out)


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
                    # AGAINST GOLD'S VOCABULARY ONLY. Declining on a difference
                    # gold could never have expressed is declining for no reason:
                    # a GATE is in `stable` and can never be in `charged`, so
                    # every cell with a firing gate would suppress its own
                    # conflict report. The harm is silent -- fewer findings, and
                    # nothing saying why. See _gold_nameable_slots.
                    _vocab = _gold_nameable_slots(item)
                    if _vocab:
                        stable &= _vocab
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


def _artifact_path(item: str, side: str):
    """Where a recorded side's artifact lives, or None if it is not recorded."""
    import paths as _p

    e = entry(item, side)
    if not e or not e.get("out"):
        return None
    return Path(_p.OUT) / str(e["out"]) / f"{item}.runs.json"


@functools.lru_cache(maxsize=None)
def _verdict_signatures(item: str, side: str, path: str, mtime: float,
                        size: int) -> tuple:
    """((pid, verdicts, answers), score) for every cell in one side's artifact.

    KEYED ON THE ARTIFACT'S mtime AND size, so a fresh sweep of ONE item
    invalidates only that item's signatures and every other item stays cached.
    That is the natural invalidation here: the signatures are a pure function of
    the recorded runs, and the recorded runs change exactly when the file is
    rewritten.

    `path`, `mtime` and `size` are arguments rather than looked up inside,
    because lru_cache keys on arguments -- reading the mtime in the body would
    cache the first value seen and never notice a re-sweep, which is the bug
    this signature shape exists to avoid.
    """
    import cross_path as X

    doc = _runs_doc(item, side)
    if not doc:
        return ()
    out = []
    for run in doc["runs"]:
        for c in run.get("results") or []:
            got = X.result_cell(c)
            if not got or got[2] is None:
                continue
            _it, pid, score, _v = got
            verd = dict(c.get("checks") or c.get("verdicts") or {})
            extra = dict(c.get("answers") or c.get("refers_to") or {})
            out.append(((pid,
                         tuple(sorted((k, str(v)) for k, v in verd.items() if v)),
                         tuple(sorted((k, str(v)) for k, v in extra.items() if v))),
                        round(float(score), 4)))
    return tuple(out)


def _artifact_fingerprint() -> tuple:
    """(item, side, mtime, size) for every recorded artifact, sorted.

    The cache key for `scoring_logic_agreement`. Re-sweeping ONE item changes
    one tuple, which invalidates the composed answer while every other item's
    signatures stay cached in `_verdict_signatures` -- so the recomputation
    costs that item alone.
    """
    # ONE ledger read, not one per (item, side). Going through `entry()` re-read
    # and re-parsed MEASURED.json 52 times, which WAS the whole warm cost of the
    # scoring comparison -- 0.023s of stat plus parse, against 0.001s of actual
    # work. Caching `load()` itself would be the wrong fix: `record` writes the
    # ledger, so a process-wide cache would need invalidating on every write.
    import paths as _p

    items = (load().get("items") or {})
    out = []
    for item in sorted(_jobs()):
        rec = items.get(item) or {}
        for side in ("olx", "python"):
            e = rec.get(side) or {}
            if not e.get("out"):
                continue
            f = Path(_p.OUT) / str(e["out"]) / f"{item}.runs.json"
            try:
                st = f.stat()
            except OSError:
                continue
            out.append((item, side, st.st_mtime, st.st_size))
    return tuple(out)


def scoring_logic_agreement() -> dict:
    """See `_scoring_logic_agreement`; cached on the artifacts' fingerprint."""
    d = _scoring_logic_agreement_cached(_artifact_fingerprint())
    # A copy, so a caller that mutates the result cannot poison the next one --
    # the same guard `fixture_for` makes for the same reason.
    return {"matched": d["matched"], "differing": list(d["differing"])}


@functools.lru_cache(maxsize=8)
def _scoring_logic_agreement_cached(_fingerprint: tuple) -> dict:
    """Where both engines produced the SAME verdicts, did they produce the same score?

    THIS SEPARATES THE SCORER FROM THE MODEL, which nothing else here does. Every
    other comparison mixes them: a cell scores differently and the cause could be
    the model answering differently or the arithmetic over those answers
    differing. Holding the verdicts fixed removes the model from the question --
    if identical answers ever yield different totals, the two implementations of
    the scoring rules disagree, and that is a defect rather than sampling.

    NOT PROOF, and worth being plain about. It only covers the verdict
    combinations both engines happened to produce on the sampled cells, so it
    cannot speak for a combination neither reached. What it gives is evidence
    proportional to its coverage, which is why the MATCHED count is returned
    alongside the differences: silence over 221 shared signatures means
    something, and silence over none means nothing at all.

    The signature is the verdicts AND the classification answers -- `checks` plus
    `answers` on the python side, `verdicts` plus `refers_to` on the olx side --
    because a cover group's score depends on which member a slot refers to, not
    only on whether it was met.
    """
    import collections

    out = {"matched": 0, "differing": []}
    for item in sorted(_jobs()):
        by_sig = collections.defaultdict(lambda: collections.defaultdict(set))
        for side in ("olx", "python"):
            f = _artifact_path(item, side)
            try:
                st = f.stat() if f else None
            except OSError:
                st = None
            if st is None:
                continue
            for sig, score in _verdict_signatures(item, side, str(f),
                                                  st.st_mtime, st.st_size):
                by_sig[sig][side].add(score)
        for sig, sides in by_sig.items():
            if len(sides) < 2:
                continue
            out["matched"] += 1
            if sides["olx"] != sides["python"]:
                out["differing"].append((item, sig[0], sorted(sides["olx"]),
                                         sorted(sides["python"])))
    return out


def _fisher_two_tailed(a: int, b: int, c: int, d: int) -> float:
    """Exact p for the 2x2 table [[a, b], [c, d]], two-tailed.

    Written out rather than imported: scipy is not a dependency here, and the
    tables are tiny. Sums the probability of every table at least as extreme as
    the observed one, which is the conventional two-tailed exact test.
    """
    from math import comb

    n, r1, r2, c1 = a + b + c + d, a + b, c + d, a + c
    if not (r1 and r2 and c1 and n - c1):
        return 1.0
    pr = lambda x: comb(r1, x) * comb(r2, c1 - x) / comb(n, c1)
    p0 = pr(a)
    lo, hi = max(0, c1 - r2), min(r1, c1)
    return min(1.0, sum(pr(x) for x in range(lo, hi + 1) if pr(x) <= p0 + 1e-12))


def rate_divergence(alpha: float = 0.05) -> dict:
    """Per cell, is the two engines' agreement RATE distinguishable from chance?

    THE QUESTION E39 ASKED, and the answer turns out to be about statistical
    power rather than about the engines. Comparing medians manufactures
    divergences -- QUALITY_CONTROL 2e records three of Q32's five being ONE
    observation apart -- so the comparison is a two-proportion exact test on
    each cell's right/wrong counts.

    At six runs a side the test can barely fire. The smallest p it can produce
    is 0.0022, from a perfect 6-against-0 split, and with ~516 comparable cells
    a Bonferroni threshold sits at 0.0001. So NO cell can reach significance at
    this run count, whatever the engines do: the ledger cannot support a claim
    of engine divergence, in either direction.

    Returns the counts rather than a verdict, so the caller decides what to do
    with a corpus that has no power.
    """
    import handouts as H

    jobs = _jobs()
    out = {"cells": 0, "flagged": [], "alpha": alpha, "min_p_possible": None}
    for item in sorted(jobs):
        h = jobs[item]["handout"]
        try:
            g = _corrected_gold(h, rebuild_1c=(item == "1c"))
        except Exception:
            continue
        for pid in sorted(g):
            tgt = ((g.get(pid) or {}).get(item) or {}).get("score")
            if tgt is None:
                continue
            counts = {}
            for s in ("olx", "python"):
                sc = _cell_scores(item, pid, s)
                if not sc:
                    counts = None
                    break
                counts[s] = (sum(1 for v in sc
                                 if H.scored_exactly(item, tgt, v)), len(sc))
            if not counts:
                continue
            out["cells"] += 1
            (a, na), (c, nc) = counts["olx"], counts["python"]
            best = _fisher_two_tailed(na, 0, 0, nc)
            out["min_p_possible"] = (best if out["min_p_possible"] is None
                                     else min(out["min_p_possible"], best))
            pv = _fisher_two_tailed(a, na - a, c, nc - c)
            if pv < alpha:
                out["flagged"].append((pv, item, pid, a, na, c, nc))
    out["flagged"].sort()
    out["bonferroni"] = alpha / max(out["cells"], 1)
    return out


def rate_divergence_report(alpha: float = 0.05) -> str:
    """`rate_divergence` as text, for `measured.py --rates`."""
    d = rate_divergence(alpha)
    n, bonf = d["cells"], d["bonferroni"]
    lines = [f"engine agreement RATES over {n} comparable cell(s)",
             f"  uncorrected alpha {alpha}; Bonferroni over {n} cells: "
             f"p < {bonf:.5f}",
             f"  smallest p the recorded run count can produce: "
             f"{d['min_p_possible']:.5f}"]
    if d["min_p_possible"] is not None and d["min_p_possible"] > bonf:
        lines.append("  SO NO CELL CAN REACH SIGNIFICANCE at this run count -- the "
                     "test has no power here and no divergence claim is "
                     "supportable from the ledger")
    lines.append(f"  cells at uncorrected p < {alpha}: {len(d['flagged'])} "
                 f"(chance alone predicts about {alpha * n:.0f})")
    for pv, item, pid, a, na, c, nc in d["flagged"]:
        mark = "  SURVIVES CORRECTION" if pv < bonf else ""
        lines.append(f"    {item}/p{pid:<3} olx {a}/{na}  python {c}/{nc}  "
                     f"p={pv:.4f}{mark}")
    return "\n".join(lines)


def refusal_precision(item: str, side: str = DEFAULT_SIDE) -> str:
    """Per slot: how many of our refusals gold's own itemisation CONTRADICTS.

    THE STATISTIC THIS REPLACES counted a refusal against us whenever the CELL
    was wrong. That conflates two opposite errors, and subgoal Q19 was framed by
    the conflation: on Q4c every one of the 15 `wrong_kind` refusals of the
    second box sat in a wrong cell, which reads as a rule that is always wrong --
    but 12 of those 15 are p9, where gold charges BOTH consequences, so our
    refusal is RIGHT and merely incomplete. Crediting the box there moves the
    cell further from gold, not closer. Counted this way the two affected items
    have four contradicted refusals between them rather than forty-nine.

    A refusal is CONTRADICTED when gold's comment itemises the cell and does not
    name that slot -- we charge something the grader did not. It is CORROBORATED
    when gold names it. Where the comment cannot be itemised the refusal is
    UNDECIDABLE and is reported separately rather than folded into either, on the
    same principle as `gold_charged_slots` returning None: not knowing is not the
    same as knowing there was nothing.

    Ambiguity is honoured. `gold_charge_bounds` gives the slots a comment names
    for certain and the COUNT it charges in total, so a refusal outside the
    definite set is only contradicted when the definite set already accounts for
    every slot gold charged; otherwise it might be the one the ambiguous segment
    meant, and it is left undecidable.
    """
    import collections

    doc = _runs_doc(item, side)
    if doc is None:
        return f"{item} [{side}]: no artifact to read"
    # CHARGING SLOTS ONLY -- points OR gates -- via the shared predicate, the
    # same restriction `_our_failing_slots` makes. The first version of this
    # counted every non-`met` answer, which put `keyword` and `confident` at the
    # top of the table -- 6 and 40 "contradicted" refusals for two checks that
    # cannot charge anything. Narrowing it to `pts is not None` fixed that and
    # went one slot-class too far: see _charging_slots for the 546 gate-unmet
    # observations both sites were blind to, and why gates are back in.
    import agreement as A
    import olx_prompts as O

    try:
        spec = A.load_action(f"bmod_handout{_jobs()[item]['handout']}.olx",
                             O.ACTION[item])
        scored = _charging_slots(spec)
    except Exception as e:
        return f"{item} [{side}]: cannot read the slot sheet: {type(e).__name__}: {e}"
    per = collections.defaultdict(lambda: collections.Counter())
    for run in doc["runs"]:
        for c in run.get("results") or []:
            pid = c.get("participant_id") or (
                c.get("cell", "").split("/")[0].lstrip("pP") if c.get("cell") else None)
            if pid is None:
                continue
            pid = int(pid)
            named = gold_charged_slots(item, pid)
            bounds = gold_charge_bounds(item, pid)
            checks = c.get("checks") or c.get("verdicts") or {}
            for slot, v in checks.items():
                if v in (None, "", "met") or slot not in scored:
                    continue
                # OUTSIDE GOLD'S VOCABULARY IS UNDECIDABLE, NOT CONTRADICTED.
                # A CONTRADICTED refusal means the grader itemised the cell and
                # did not name this slot. That reading requires the grader to
                # have been ABLE to name it, and for a GATE they never are --
                # gates carry no points and no phrase in any table maps to one.
                # Scored raw, 1a's `distinguishes_periods` came back 11 refusals,
                # 11 contradicted, 0 corroborated: the worst instrument on the
                # item, on a slot that agrees with gold every time it fires.
                # Same alphabet mismatch as gold_slot_disagreements; see
                # _gold_nameable_slots.
                # Hoisted above BOTH readings: `definite` comes from the same
                # prose as `named`, so a gate cannot appear there either and the
                # bounds branch would call it contradicted whenever the definite
                # set already accounted for gold's count. Guarded on a non-empty
                # vocabulary, so an item with no phrase table is unaffected --
                # there every slot is undecidable already, by the else below.
                _vocab = _gold_nameable_slots(item)
                if _vocab and slot not in _vocab:
                    per[slot]["undecidable"] += 1
                elif named is not None:
                    per[slot]["corroborated" if slot in named else "contradicted"] += 1
                elif bounds is not None:
                    definite, count = bounds
                    if slot in definite:
                        per[slot]["corroborated"] += 1
                    elif len(definite) >= count:
                        per[slot]["contradicted"] += 1
                    else:
                        per[slot]["undecidable"] += 1
                else:
                    per[slot]["undecidable"] += 1
    if not per:
        return f"{item} [{side}]: no refusals recorded"
    out = [f"{item} [{side}] refusals against GOLD'S OWN ITEMISATION "
           f"(not against whether the cell scored right)",
           f"  {'slot':22s} {'refusals':>8s} {'gold agrees':>12s} "
           f"{'CONTRADICTED':>13s} {'undecidable':>12s}"]
    for slot in sorted(per, key=lambda s: -sum(per[s].values())):
        c = per[slot]
        tot = sum(c.values())
        out.append(f"  {slot:22s} {tot:8d} {c['corroborated']:12d} "
                   f"{c['contradicted']:13d} {c['undecidable']:12d}")
    tot_c = sum(per[s]["contradicted"] for s in per)
    tot_u = sum(per[s]["undecidable"] for s in per)
    out.append(f"  A CONTRADICTED refusal charges a slot gold's comment does not "
               f"name. {tot_c} here, with {tot_u} undecidable.")
    return "\n".join(out)


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
                # BOTH VOCABULARIES are cues. The sides were renamed on
                # 2026-09-01, and the prose this scans is years of history --
                # dropping "web"/"cli" as cues would have made every older
                # sentence resolve to the default side and compared its number
                # against the wrong column.
                # `paper` and `opus` are cues too, and their absence was a
                # silent gap rather than a missing feature: a sentence reading
                # "Q4a olx 17/20  python 18/20  paper 15/20" had no cue for its
                # third figure, so the nearest known cue -- `python` -- claimed
                # it and the check reported a contradiction that was not one.
                # `opus` sits later in "paper_opus" than `paper` does, so the
                # rfind-max below resolves that pair correctly.
                for cue, s_ in (("web", "olx"), ("app", "olx"),
                                ("olx", "olx"),
                                ("cli", "python"), ("harness", "python"),
                                ("python", "python"),
                                ("paper", "paper"), ("opus", "paper_opus")):
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
        # said so -- so a olx-only miss is examined instead of skipped.
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
    accepting "a car", "{{corpus:Q3/p14:action:91:114:sha=ef5c3179ffeb}}", "{{corpus:Q3/p18:action:71:97:sha=4b1ed59f418c}}
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
    # `--refusals ITEM [SIDE]`. The companion to --errors: that one asks which
    # slots are unmet in cells that scored wrong, this one asks whether GOLD'S
    # COMMENT contradicts the refusal. They answer differently whenever a
    # refusal is right and the cell is wrong for another reason, which is what
    # framed subgoal Q19 for three days.
    if a[:1] == ["--rates"] and len(a) == 1:
        print(rate_divergence_report())
        return 0
    # `--silent-refusals [SIDE]`. Gold's SILENCES, which no other readout looks
    # at: every other one starts from a charge and asks whether we agree. This
    # starts from the absence of a charge and asks whether there should have been
    # one. Defaults to the pooled side, since a single engine's median is the
    # noisier basis for calling a cell an outlier.
    if a[:1] == ["--silent-refusals"] and len(a) in (1, 2):
        print(silent_full_marks_we_refuse(a[1] if len(a) == 2 else "olx+python"))
        return 0
    if a[:1] == ["--refusals"] and len(a) in (2, 3):
        print(refusal_precision(a[1], a[2] if len(a) == 3 else DEFAULT_SIDE))
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
        (r"did not address how {{corpus:Q4c/p19:second:0:25:sha=d4d526f38996:shape=C1}} being affected",
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
    # KEEP THIS ENTRY EVEN THOUGH p3 IS SUSPECT. It was deleted once, on the
    # reasoning that an excluded cell has no disagreement with gold to declare.
    # That is wrong: excluded cells are still RUN and still SCORED (see
    # check_slot_sets_match_gold), they are only left out of the RATE, so
    # deleting this made the slot comparison start reporting p3 as undeclared.
    # Declaring a suspect cell and ARGUING FROM one are different acts -- this is
    # bookkeeping, and only the latter is the error that
    # enforcement.check_no_declaration_cites_a_suspect_cell forbids.
    ("WK2", 3): "gold charges TYPE_MISMATCH (2) -- \"This is NP.\" -- and we "
                "charge nothing.",
    # Self-contained on purpose. This read "same as WK2/p3" until that put a
    # LIVE cell's reasoning inside a suspect one; p15 is scored and counted, so
    # its argument has to stand on its own.
    ("WK2", 15): "gold charges TYPE_MISMATCH (2) -- \"This is an example of "
                 "NP.\" -- and we charge nothing.",
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


# THE BUDGET, and it may only fall -- the same bargain as
# GOLD_SLOT_DISAGREEMENTS_BUDGET and SLOT_RULE_BACKLOG. It went 8 -> 5 on
# 2026-09-02: 8 -> 5 when 2a's conjunction rule made p1, p13 and p15 agree with
# gold, then 5 -> 3 when the ratchet's FIRST run found Q4a/p6 and Q4a/p9 had
# been stale for longer. Q20's own text already said p6 agreed; this table was
# never updated to match, which is the gap the ratchet closes. 3 -> 2 the same
# day, when the mechanism rule made 2a/p14 charge the slot gold charged: the
# ratchet reported it on the first audit after the sweep, unprompted.
GOLD_SLOT_BOUNDS_BUDGET = 2

GOLD_SLOT_BOUNDS_KNOWN: dict[tuple[str, int], str] = {
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
    ("Q4c", 16): "the comment is \"did not say if {{corpus:Q4b/p15:modify:0:30:sha=431b4811e0ab:shape=R0-1-74,R30-0-20}}"
                 "{{corpus:Q4b/p15:modify:31:34:sha=10c22bcf4c76}} you modify and why\", which is Q4b's `modify_why` test on a "
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
def _handout_gold_items(handout: int) -> frozenset:
    """Which item ids handout `handout`'s gold sheet actually grades."""
    keys: set = set()
    for row in _corrected_gold(handout).values():
        keys |= set(row)
    return frozenset(keys)


def gold_cell(item: str, pid: int, *, rebuild_1c: bool = False) -> dict:
    """One cell's corrected gold, keyed by ITEM so the handout cannot be picked wrong.

    THE HANDOUT IS DERIVED, NEVER PASSED. Reading gold for an item requires
    knowing which of the three sheets grades it, and every call site did that
    lookup by hand: `{1: load_h1, 2: load_h2, 3: load_h3}[h]()`. Pick the wrong
    `h` and the sheet loads fine, the row lookup misses, and you get `{}` --
    indistinguishable from "this cell has no gold row". On 2026-09-03 that
    happened live while reading 1a/p15: 1a is a HANDOUT 3 item, `load_h1` was
    called for it, and the readout said `gold 1a/p15: {}`. It was caught only
    because an empty row looked odd on a cell that was under discussion. The same
    silence on a cell being scanned in bulk reads as "nothing to see", which is
    how a real disagreement disappears.

    So the mistake is removed rather than detected: callers name the ITEM, and
    RAISE is the failure mode instead of an empty dict. A handout whose sheet
    grades no such item is a programming error, not a missing cell, and the two
    are now distinguishable -- `{}` means only "this participant has no row for
    this item", which is a real and different thing.

    Verified by enforcement.check_gold_is_read_by_item, which requires this to
    raise on a wrong pairing and holds the remaining hand-rolled loader sites to
    a declared allowlist.
    """
    jobs = _jobs()
    if item not in jobs:
        raise KeyError(f"{item!r} is not an item in agreement_app.JOBS; "
                       f"gold cannot be read for it")
    h = jobs[item]["handout"]
    if item not in _handout_gold_items(h):
        raise KeyError(
            f"handout {h}'s gold sheet grades no item {item!r} "
            f"(it grades {sorted(_handout_gold_items(h))}). JOBS says {item} is "
            f"a handout-{h} item, so one of the two is wrong -- this is a bug, "
            f"not a missing cell")
    rows = _corrected_gold(h, rebuild_1c)
    return dict((rows.get(pid) or {}).get(item) or {})


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


_FIXTURES: dict = {}
_COMPUTED_SLOTS: dict = {}


def _charging_slots(spec: dict) -> set:
    """The slots that can CHARGE a cell: point-bearing ones, and GATES.

    A GATE CARRIES NO POINTS AND IS THE MOST EXPENSIVE INSTRUMENT ON ITS SHEET.
    `pts=None, gates=True` zeroes the whole item on one unmet verdict, so
    filtering on `pts is not None` -- which both call sites did -- made every
    gate in the corpus invisible to the slot profile: 546 gate-unmet run
    observations across fourteen items, including `you_arrange_it` (four operant
    items), `cadence_is_daily`/`cadence_is_weekly` (subgoal Q22's whole subject)
    and `wgb_is_counterpart` (Q29's). A cell zeroed by a gate reported NO FAILING
    SLOT, which reads as "every scoring check passes" -- the signature of subgoal
    Q20's over-credit class -- so gate false-positives were liable to be filed as
    the opposite kind of error.

    THE RESTRICTION IT REPLACES WAS RIGHT ABOUT A DIFFERENT CLASS, and that
    finding is preserved. Counting every non-`met` answer put `keyword` and
    `confident` at the top of the contradicted-refusal table with 6 and 40
    refusals, for two checks that cannot charge anything. Those neither score nor
    gate, so they stay out, along with the GROUNDS of a computed slot
    (2a's `names_enabler`, `states_size`, `names_plan_content`, `mechanism_named`)
    -- a ground feeds a rule, it does not charge. Only slots that can take points
    off a student are in.
    """
    return {s["key"] for s in spec["slots"]
            if s.get("pts") is not None or s.get("gates")}


def _computed_slots(spec: dict) -> frozenset:
    """Which slot keys a PRIMITIVE answers rather than the model.

    Sourced from score._computed_keys, which reads primitives.json through
    olx_prompts.primitive_attrs -- so a new primitive is covered without editing
    a list here.

    KEYED ON THE SLOT KEYS, because a spec dict is unhashable and carries no name
    or id -- it holds body/slots/derived/... and nothing identifying. The first
    version keyed on `spec.get("name") or spec.get("id") or id(spec)`, which
    therefore ALWAYS fell through to the address. Addresses are reused after
    collection, so one action could be handed another's computed set; the
    symptom was two counts of the same corpus disagreeing, 4200 against 3720.
    The slot-key tuple is stable, unique per action, and cannot be recycled.
    """
    name = tuple(s.get("key") for s in (spec.get("slots") or ()))
    got = _COMPUTED_SLOTS.get(name)
    if got is None:
        import score as S
        try:
            got = frozenset(S._computed_keys(spec))
        except Exception:
            got = frozenset()
        _COMPUTED_SLOTS[name] = got
    return got


def _fixture_cached(item: str, pid: int) -> dict:
    """One reconstruction per cell; apply_computed reads its fields."""
    import agreement as A

    key = (item, pid)
    if key not in _FIXTURES:
        _FIXTURES[key] = A.fixture_for(item, pid)
    return _FIXTURES[key]


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
    scored = _charging_slots(spec)
    out = []
    for run in runs:
        for r in (run.get("results") or []):
            # BOTH ARTIFACT SHAPES. agreement.py writes participant_id/checks;
            # agreement_app.py writes cell "p19/Q4a" and `verdicts`, with
            # per-slot refers_to where the other has `answers`. Reading only the
            # first shape made this return [] for every olx cell, so every
            # slot-level readout built on it was silently python-only while
            # reporting nothing amiss -- the same failure as the `out` pointer
            # that made the paper column unreadable and read as "nothing wrong".
            rid = r.get("participant_id")
            if rid is None and r.get("cell"):
                head = str(r["cell"]).split("/")[0].lstrip("pP")
                rid = int(head) if head.isdigit() else None
            if rid != pid:
                continue
            # A `None` VERDICT IS NOT RECORDED, NOT FAILED. When a gate fails,
            # agreement_app.py never asks the downstream scored slots and stores
            # them as null; agreement.py stores a real verdict for every slot.
            # Passing the nulls through made satisfied_map read them as
            # unsatisfied and INVENTED failures out of missing data -- NR/p20
            # reported barrier_is_not_this_type and demonstrates_type failing on
            # olx and nothing on python, which read as an engine divergence when
            # both sides in fact agree unanimously that `you_arrange_it` is
            # absent, 12 runs out of 12. There is no divergence there to reason
            # from, and the two engines are pooled precisely because differences
            # between them are sampling, not program. Unknown stays unknown.
            raw = dict(r.get("checks") or r.get("verdicts") or {})
            ch = {k: v for k, v in raw.items() if v is not None}
            ans = {k: v for k, v in (r.get("answers")
                                     or r.get("refers_to") or {}).items()
                   if v is not None}
            # THE UNION, NOT THE VERDICTS. A CLASSIFICATION slot answers
            # `refers_to` and can carry a null verdict beside it -- NR/p20's olx
            # record has verdicts.observed_type null and refers_to.observed_type
            # "NR". Building this from `ch` alone dropped the operand, so the
            # `expect` rule downstream compared against nothing and recomputed
            # demonstrates_type as FAILING where python has it met. That is the
            # invented-failure bug returning by a side door, one level down.
            rebuilt = {k: dict(**({"verdict": ch[k]} if k in ch else {}),
                               **({"refers_to": ans[k]} if k in ans else {}))
                       for k in set(ch) | set(ans)}
            # RECOMPUTE WHAT THE OLX ARTIFACT NEVER RECORDED. A primitive's key is
            # stripped from the web response schema -- the model must not be asked
            # a question a rule answers -- so the app computes it locally and the
            # artifact stores null in BOTH `verdicts` and `evidence`. Skipping
            # nulls therefore fixed the invented-failure bug but left this
            # function blind to every computed slot on the olx side: NR's
            # `demonstrates_type` (expect) and `barrier_is_not_this_type` (forbid)
            # were simply invisible, so a caller pooling both sides and taking a
            # majority under-weighted them without anything saying so.
            # The values are not lost, only unrecorded: a computed slot is a
            # function of the answered fields and the fixture, which is exactly
            # what apply_computed evaluates -- the same call agreement.py makes on
            # its own path. Faithfulness is verified rather than assumed:
            # check_olx_computed_slots_are_recoverable rescores every olx cell
            # from the recomputed map and requires the recorded score back.
            if _computed_slots(spec) - set(rebuilt):
                try:
                    rebuilt = A.apply_computed(spec, rebuilt,
                                               _fixture_cached(item, pid))
                    # AND THE COUNTED MEMBERS, which apply_computed does not
                    # touch. A counted group is the one primitive whose KEY the
                    # model answers -- 2a's `hows_given` comes back 2 -- while
                    # `how_1`/`how_2` are DERIVED from that number by
                    # expand_counted and stored null. Recovering with
                    # apply_computed alone reproduced only 2640 of 4200 recorded
                    # verdicts, and all 1560 misses were counted members. This is
                    # the same misreading expand_counted's own docstring records
                    # costing 140 calls: members that look unanswered when they
                    # were plainly charged.
                    rebuilt = A.expand_counted(
                        dict(spec, _slots=spec["slots"]), rebuilt)
                except Exception:
                    pass          # unrecoverable here; stays unknown, not failed
            sm = A.satisfied_map(spec, rebuilt)
            out.append(frozenset(k for k, ok in sm.items()
                                 if not ok and k in scored and k in rebuilt))
    return out


@functools.lru_cache(maxsize=None)
def _gold_nameable_slots(item: str) -> frozenset:
    """The slots an item's gold PHRASE TABLE is capable of naming.

    GOLD AND WE DRAW OUR SLOT SETS FROM DIFFERENT ALPHABETS. Ours comes from the
    slot sheet; gold's is reconstructed from grader prose through
    GOLD_SLOT_CHARGES, so a slot no phrase maps to can never appear in it however
    plainly the grader objected. GATES are the whole class: they carry no points,
    graders never name them, and no entry in any phrase table produces one.

    So diffing the two sets raw reports a difference that was guaranteed before
    any cell was read. It did, the hour gates were added to the slot profile:
    1a/p15 came back as `differs on ['distinguishes_periods']` -- a gate 1a's
    table cannot express, on a cell where gold and we BOTH score 0.0 and gold's
    own comment ("did not discuss data for each week") asserts exactly what the
    gate asserts. Declaring that would have enshrined an artefact of our own
    reader as a disagreement with a grader.

    A slot outside gold's vocabulary is UNDECIDABLE, not disagreed -- the same
    doctrine gold_charged_slots states for an unreadable comment: not knowing is
    not the same as knowing there was nothing.
    """
    out: set = set()
    for entry in GOLD_SLOT_CHARGES.get(item) or ():
        tail = entry[-1]
        if isinstance(tail, (tuple, list, set, frozenset)):
            out |= {s for s in tail if isinstance(s, str)}
    return frozenset(out)


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
            # ONLY WHAT GOLD COULD HAVE SAID. See _gold_nameable_slots: a slot no
            # phrase maps to cannot appear on gold's side of this comparison, so
            # keeping it on ours manufactures a difference.
            stable &= _gold_nameable_slots(item)
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

    # THE SAME RATCHET FOR THE BOUNDS TABLE, which had none. That gap let three
    # 2a entries stand asserting "gold charges one how_* slot; we charge none"
    # on the very day the conjunction rule made us charge the box gold NAMED, in
    # 12 of 12 runs on both sides. Nothing reported them: the disagreements table
    # is ratcheted and this one was not, so its entries could only ever be
    # retired by somebody remembering to look. Two of the three also said "same
    # as 2a/p1", so the stale claim was propagating by cross-reference.
    #
    # A BOUNDS entry claims we disagree on EVERY reading of an ambiguous charge,
    # so it expires when our slot set becomes CONSISTENT with the bounds: we fail
    # as many scored slots as gold charged, and every slot gold named for certain
    # is among them. That is weaker than the disagreements table's exact-set test
    # on purpose, because the charge itself is weaker -- a count or a subset
    # rather than a named slot.
    out += bounds_declarations_that_expired()
    return out


def bounds_declarations_that_expired() -> list[str]:
    """GOLD_SLOT_BOUNDS_KNOWN entries whose cell now agrees with gold."""
    import collections

    out: list[str] = []
    for (item, pid), _why in sorted(GOLD_SLOT_BOUNDS_KNOWN.items()):
        bounds = gold_charge_bounds(item, pid)
        if bounds is None:
            continue
        definite, count = bounds
        runs = (_our_failing_slots(item, pid, "olx")
                + _our_failing_slots(item, pid, "python"))
        if not runs:
            continue          # unreadable is not agreement
        seen = collections.Counter(s for r in runs for s in r)
        maj = {s for s, k in seen.items() if k > len(runs) / 2}
        # AGAINST GOLD'S VOCABULARY ONLY. `count` is how many charges the grader
        # made, so our side has to be counted in the same units. A GATE is not in
        # those units -- it carries no points and no phrase names it -- and
        # leaving it in inflates len(maj) so the equality can never hold. That
        # does not raise a false alarm; it JAMS THE RATCHET, and an entry that
        # can never expire is the exact failure this function was written to
        # stop. See _gold_nameable_slots.
        _vocab = _gold_nameable_slots(item)
        if _vocab:
            maj &= _vocab
        if len(maj) == count and set(definite) <= maj:
            out.append(
                f"GOLD_SLOT_BOUNDS_KNOWN names {item}/p{pid}, but we now fail "
                f"{len(maj)} scored slot(s) -- {sorted(maj) or 'none'} -- against "
                f"gold's charge of {count}, so the two are CONSISTENT on at least "
                f"one reading and the entry no longer describes a disagreement. "
                f"Drop it and lower GOLD_SLOT_BOUNDS_BUDGET")
    n = len(GOLD_SLOT_BOUNDS_KNOWN)
    if n != GOLD_SLOT_BOUNDS_BUDGET:
        verb = "grew to" if n > GOLD_SLOT_BOUNDS_BUDGET else "is down to"
        out.append(f"GOLD_SLOT_BOUNDS_KNOWN {verb} {n} against a budget of "
                   f"{GOLD_SLOT_BOUNDS_BUDGET} -- it may only fall")
    return out


# ---------------------------------------------------------------------------
# E37. Every cell we get WRONG must have somewhere to live.
#
# The accounting that produced this was done by hand: 34 wrong cells found and
# mapped, 16 orphans chased to none. Doing it once proves nothing about tomorrow,
# because a cell moves in or out of "wrong" whenever a rule is edited and nothing
# reports the move. Both directions matter, and closing a subgoal is a third:
# closing E35 orphaned five cells and it was noticed by reading, not by a check.
_OWNER_SIDE_CUES: tuple = (
    # (word-boundary cue, which EVALUATED side it concerns). The vocabulary is
    # the same one prose_claims scans -- both spellings, because the sides were
    # renamed on 2026-09-01 and GOALS.md is years of history -- but the semantics
    # differ on purpose. prose_claims wants the ONE side a sentence's number
    # belongs to, so it takes the last cue. Ownership wants EVERY side a line
    # speaks about, so this collects the set.
    (r"\bolx\b", "olx+python"), (r"\bweb\b", "olx+python"),
    (r"\bapp\b", "olx+python"), (r"\bpython\b", "olx+python"),
    (r"\bcli\b", "olx+python"), (r"\bharness\b", "olx+python"),
    (r"\bboth (sides|scorers|engines)\b", "olx+python"),
    (r"\bevery side\b", "olx+python"),
    (r"\bopus\b", "paper_opus"),
    (r"\bpaper\b", "paper"),
)


def _sides_named(text: str) -> frozenset:
    """Which evaluated sides a line SPEAKS ABOUT; empty when it says nothing.

    `paper_opus` is removed before the bare `paper` cue runs, so the compound
    name counts once for the side it actually is rather than for both.
    """
    import re

    low = str(text or "").lower()
    found = set()
    if "paper_opus" in low:
        found.add("paper_opus")
        low = low.replace("paper_opus", " ")
    for pat, side in _OWNER_SIDE_CUES:
        if re.search(pat, low):
            found.add(side)
    return frozenset(found)


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
        return {"any": {}, "title": {}, "by_side": {}}
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
    #
    # AND OWNERSHIP IS PER SIDE, which `any` cannot express. A cell is wrong on a
    # particular side, and a subgoal about a DIFFERENT side is not a home for it.
    # 1a/p6 is the case that forced this: we over-credit it on the OLX prompt in
    # 11 of 12 runs, and every mention of it in this file was about the PAPER
    # scorer -- "paper 0.0 vs olx 6.0-8.0", Q33's territory. Any-mention
    # ownership read that as covered, so an 11-of-12 over-credit sat unchased
    # while the audit reported clean. The side context is the line's own cues if
    # it has any, else the SUBGOAL TITLE's, else every side: Q33's title says "on
    # the PAPER scorer", so its body lines inherit paper rather than claiming
    # everything by omission.
    owners: dict = {"any": {}, "title": {}, "by_side": {}}
    current = None
    title_sides: frozenset = frozenset()
    for line in text.splitlines():
        m = re.match(r"- \[( |x)\] ([EQ]\d+)\.", line)
        is_title = bool(m)
        if m:
            current = None if m.group(1) == "x" or m.group(2) == "E30" else m.group(2)
            title_sides = _sides_named(line) if current else frozenset()
            # WHICH ITEMS THE TITLE CLAIMS. The subgoal id is stripped first
            # because the two namespaces COLLIDE: subgoal Q2 and item Q2 are
            # different things, and reading the id as an item would let every
            # low-numbered subgoal claim an item it has nothing to do with.
            body = re.sub(r"^- \[( |x)\] [EQ]\d+\.", "", line)
            title_items = ({it for it in _jobs()
                            if re.search(rf"\b{re.escape(it)}\b", body)}
                           if current else set())
        if current is None:
            continue
        here = _sides_named(line) or title_sides or frozenset(_EVALUATED_SIDES)
        for cell in re.findall(r"\b([A-Za-z0-9]{1,4})/p(\d{1,2})\b", line):
            key = f"{cell[0]}/p{cell[1]}"
            owners["any"].setdefault(key, []).append(current)
            # A TITLE THAT NAMES ITS ITEMS CANNOT OWN ANOTHER ITEM'S CELL by an
            # aside. This is the gap that actually mattered, and it is not the
            # side gap it was first taken for. 1a/p6 was over-credited on the
            # pooled OLX prompt in 11 of 12 runs and read as OWNED -- not by a
            # paper-side subgoal, but by Q17, whose title is "Q2:
            # `wgb_is_counterpart`..." and whose body mentions the cell purely as
            # history: "as 1a's five were on 2026-08-28, which cost 1a/p6 the
            # whole item before the migration". A sentence about a past migration
            # in a subgoal about a different item is not a home for a live error.
            # Corpus-wide subgoals keep their reach: Q19 and Q20 name no item in
            # their titles, so they own cells across items as before.
            if is_title or not title_items or cell[0] in title_items:
                for side in here:
                    owners["by_side"].setdefault(key, {}).setdefault(
                        side, []).append(current)
            if is_title:
                owners["title"].setdefault(key, []).append(current)
    return owners


# THE TWO OLX-PROMPT SIDES ARE ONE SAMPLE, decided 2026-09-01. `olx` and
# `python` send an identical prompt to the same model and score it with logic
# that agrees on every verdict signature both have produced, so their runs are
# twelve draws from one process rather than six each from two. Judging a cell
# separately on each half threw away half the sample and manufactured
# "divergences" that were one observation apart.
#
# `paper` STAYS SEPARATE, and so does `paper_opus`. Paper runs the RUBRIC
# prompt, not the OLX sheet -- that is the whole reason it is its own column --
# so pooling it with the other two would average two different questions.
POOLED_OLX_PROMPT = ("olx", "python")
_EVALUATED_SIDES = ("olx+python", "paper", "paper_opus")


def _pooled_cell_scores(item: str, pid: int, side: str) -> list:
    """One cell's recorded scores for an EVALUATED side.

    `olx+python` returns both engines' runs concatenated; every other side
    returns its own, unchanged.
    """
    if side != "olx+python":
        return _cell_scores(item, pid, side)
    out = []
    for s in POOLED_OLX_PROMPT:
        out += _cell_scores(item, pid, s)
    return out


def silent_full_marks_we_refuse(side: str = "olx+python") -> str:
    """Cells gold awarded the maximum IN SILENCE that we refuse, and the
    comparators that say whether the silence was an oversight.

    THE PRINCIPLE, stated by the user after the NR/p4 correction and generalised
    from it: if a rater awarded full marks with no comment and our scorer refuses,
    one explanation is that the rater was careless and missed something. That
    becomes much more likely when the cell is an OUTLIER against the pattern the
    raters applied elsewhere -- above all to other cells of the SAME ITEM.

    SILENCE IS AMBIGUOUS, which is the whole reason this needs a comparator
    column rather than a list. It can mean the rater missed the defect, or that
    they deliberately accepted it -- Q4a's own prompt says "ACCEPT generously",
    so a silent pass there may be the rubric working as written. What separates
    the two readings is whether that rater ever charged this defect ELSEWHERE on
    this item:

      comparators exist  -> the silent cell is the outlier. Carelessness is the
                            likely story and a gold correction is a candidate.
                            NR/p4 against p9: same item, same structural error,
                            gold charged p9 "-2 pts: This is an example of PP",
                            landing on the very score the correction assigns.
      no comparators     -> silence IS the pattern on this item, and it is OUR
                            scorer that is out of step. Not a gold correction --
                            a divergence, or over-strictness to fix on our side.

    So a row here is a QUESTION, never a verdict. Matching by deduction
    MAGNITUDE is what makes the scan work corpus-wide: gold's comments itemise
    into slots on some items and into deduction codes on others
    (`gold_charged_slots` returns None for all of the operant-type items), while
    "gold took N points off somewhere on this item" is always readable. The cost
    is that magnitude cannot tell whether the comparator's defect is the SAME
    defect, so each comparator's comment is printed for reading rather than
    counted. That judgement is not mechanisable and the readout does not pretend
    it is.

    SUSPECT CELLS ARE EXCLUDED FROM BOTH COLUMNS, as candidates and as
    comparators. A row whose transcription cannot be attributed is evidence for
    nothing in either direction -- see
    enforcement.check_no_declaration_cites_a_suspect_cell, which exists because
    this very correction's first draft argued from two of them.
    """
    import statistics
    import handouts as H

    out = [f"SILENT FULL MARKS WE REFUSE  [{side}]",
           "gold awarded the maximum with no comment and we charge something.",
           "A comparator is another cell of the same item where gold DID charge "
           "the same",
           "number of points -- read its comment to judge whether the defect is "
           "the same.",
           ""]
    rows: list[tuple] = []
    for item in sorted(_jobs()):
        h = _jobs()[item]["handout"]
        try:
            maxes = {i["id"]: i["max"] for i in H.config(h)["rubric"].ITEMS}
            gold = _corrected_gold(h)
        except Exception:
            continue
        top = maxes.get(item)
        if top is None:
            continue
        drop = set(exclusions(item))
        # Every charge gold made on this item, magnitude -> [(pid, comment)].
        charged: dict[float, list[tuple[int, str]]] = {}
        for pid, per in gold.items():
            if pid in drop:
                continue
            row = (per or {}).get(item) or {}
            sc, fb = row.get("score"), (row.get("feedback") or "").strip()
            if sc is None or not fb:
                continue
            charged.setdefault(round(top - sc, 2), []).append((pid, fb))
        for pid in sorted(gold):
            if pid in drop:
                continue
            row = (gold.get(pid) or {}).get(item) or {}
            sc, fb = row.get("score"), (row.get("feedback") or "").strip()
            if sc is None or fb or abs(sc - top) > 1e-9:
                continue                      # not a silent full-marks row
            got = _pooled_cell_scores(item, pid, side)
            if not got:
                continue
            ours = statistics.median(got)
            if ours >= sc - 1e-9:
                continue                      # we do not refuse it
            comps = charged.get(round(top - ours, 2), [])
            rows.append((item, pid, sc, ours, len(got), comps))
    if not rows:
        out.append("  none: no cell has gold at the maximum in silence while we "
                   "charge.")
        return "\n".join(out)
    rows.sort(key=lambda r: (-len(r[5]), r[0], r[1]))
    out.append(f"  {'cell':<10} {'gold':>5} {'ours':>6} {'runs':>5}  reading")
    for item, pid, sc, ours, n, comps in rows:
        verdict = (f"OUTLIER -- gold charged {round(sc - ours, 2)} on "
                   f"{len(comps)} other cell(s) of this item"
                   if comps else
                   f"PATTERN -- gold charged {round(sc - ours, 2)} NOWHERE on "
                   f"this item; suspect our own rule first")
        out.append(f"  {item + '/p' + str(pid):<10} {sc:>5.2f} {ours:>6.2f} "
                   f"{n:>5}  {verdict}")
        for cpid, fb in comps[:4]:
            out.append(f"      p{cpid}: {fb[:88]}")
        if len(comps) > 4:
            out.append(f"      ... and {len(comps) - 4} more")
    out += ["",
            f"{sum(1 for r in rows if r[5])} outlier(s) worth a gold-correction "
            f"argument; {sum(1 for r in rows if not r[5])} where our own rule is "
            f"the likelier fault.",
            "A row is a question, not a verdict. Read the comparator comments "
            "before declaring anything."]
    return "\n".join(out)


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
            for side in _EVALUATED_SIDES:
                scores = _pooled_cell_scores(item, pid, side)
                if not scores:
                    # A side with no per-cell data is UNREADABLE, not clean, and
                    # conflating the two is how this function reported zero
                    # orphans while five Q4a cells were wrong on `paper`: the
                    # ledger held the numerator, but its `out` pointer named
                    # "runs" instead of "e25_paper/runs", so every per-cell read
                    # came back empty and every cell looked fine. Recorded but
                    # unreadable is reported by
                    # `sides_recorded_but_unreadable()`, which the audit runs
                    # beside this one -- silence here must never mean "nothing
                    # to see".
                    continue
                ours = sorted(scores)[len(scores) // 2]
                if not H.scored_exactly(item, target, ours):
                    out.append((item, pid, side, target, ours))
    return out


def sides_recorded_but_unreadable() -> list[str]:
    """A side with a recorded numerator whose per-cell scores cannot be read.

    The ownership check in `wrong_cells_without_an_owner` walks cells, and a side
    it cannot read contributes nothing -- which is indistinguishable, in its
    output, from a side that gets everything right. So the readability of each
    recorded side is asserted separately rather than inferred from silence.

    This is not hypothetical: the first `paper` column recorded, on 2026-09-01,
    was unreadable for exactly this reason, and the ownership check reported a
    clean corpus while five cells were wrong.
    """
    out = []
    for item, rec in sorted((load().get("items") or {}).items()):
        for side in SIDES:
            e = (rec or {}).get(side)
            if not e or e.get("pending") or e.get("numerator") is None:
                continue
            doc = _runs_doc(item, side)
            if doc is None:
                out.append(
                    f"{item} [{side}] is recorded at {e['numerator']}/"
                    f"{e['denominator']} but its artifact cannot be found at "
                    f"out/{e.get('out')}/{item}.runs.json, so every per-cell "
                    f"check reads it as having nothing wrong")
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
        # PER SIDE, not per cell. A subgoal about the paper scorer is not a home
        # for a cell we get wrong on the OLX prompt -- see _live_subgoal_owners.
        if (owned["by_side"].get(key) or {}).get(side):
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

# THE ENTRY POINT LIVES AT THE END, and it has to. It used to sit two thirds of
# the way up, with fifteen `def`s below it, so `main()` ran before those names
# existed and any CLI command reaching one died with a bare NameError. The
# commands that predated the split all happened to use functions defined above
# it, which is why nothing noticed until `--refusals` called `_runs_doc`.
# enforcement.py had the same defect and the same fix.
# --- corpus reference resolution (backdated) ---
# `_olx` hands the handout's OLX to prompt_sha, section slicing and the audit.
# Resolving HERE means every fingerprint sees the words the file used to hold,
# so a rewritten history hashes what the original hashed.
try:                                            # pragma: no cover
    import corpus_resolve as _corpus_resolve
    _corpus_orig_olx = _olx

    def _olx(handout, _orig=_corpus_orig_olx):
        return _corpus_resolve.expand(_orig(handout))
except Exception:
    pass


if __name__ == "__main__":
    raise SystemExit(main())
