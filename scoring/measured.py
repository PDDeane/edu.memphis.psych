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
import sourcecache
import re
import sys
from pathlib import Path


def _gold_declaration(name: str):
    """One gold declaration, read from the gold file.

    The gold twin of the `_declaration` helper, and separate from it because the
    two files differ in AVAILABILITY: the course file ships inside this public
    repository and is always present, gold does not (C1b). So this module now
    fails to import when the gold file is UNREACHABLE, where before the data was
    inline and it did not. See `coursedata.gold_declaration` for what that does
    and does not mean.

    The reasoning that used to sit INSIDE these tables as comments went with
    them -- `coursedata.gold_notes(table, key)` returns it, per entry, verbatim.
    It is course-specific gold reasoning and a public repository was the wrong
    home for it; it is not gone, and it is not optional reading.
    """
    import coursedata

    return coursedata.gold_declaration(name)


LEDGER = Path(__file__).resolve().parent / "MEASURED.json"


def _jobs() -> dict:
    import agreement_app as APP
    return APP.JOBS


def _olx(handout: int) -> str:
    """The handout's OLX, with corpus references RESOLVED.

    The file on disk may carry `{{corpus:...}}` where a student's words used to
    sit. Every reader of this function -- `prompt_sha`, `_section_bounds`,
    `olx_prompts --check`, the equivalence audit -- must see what a grader sees,
    so the expansion happens here, once, at the single point where the file is
    read. Resolve anywhere later and the fingerprints would move while nothing
    about the served prompt had changed.
    """
    import paths
    text = (paths.OLX_DIR / f"bmod_handout{handout}.olx").read_text()
    if "{{corpus:" in text:
        import corpus_ref
        text = corpus_ref.expand(text)
    return text


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

    THE PAPER SIDES ARE NOT SERVED THE .OLX AT ALL and had no branch here, so
    they were stamped with the WEB's hash: for Q3 the paper and olx shas were
    the same string, and every paper-only prompt element went unstamped. They
    hash `score.fingerprint_text` instead, which is that scorer's own prompt.
    A paper prompt change now reads STALE PROMPT, which is what it is -- not
    STALE SCORER, and no longer nothing at all.
    """
    if side in ("paper", "paper_opus"):
        if olx_text is not None:
            # The historical-revision path cannot serve these sides: the paper
            # prompt is built from the rubric and this file's own code, not from
            # the .olx, so a past .olx says nothing about it. Refused rather
            # than answered with the CURRENT prompt under a historical caller's
            # name, which is the failure this whole branch exists to end.
            raise ValueError(
                f"prompt_sha({item!r}, {side!r}): olx_text cannot re-stamp a "
                f"paper side -- its prompt does not come from the .olx"
            )
        import score as SC
        return hashlib.sha256(
            SC.fingerprint_text(item).encode()).hexdigest()[:12]
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
# it. An unlabelled number is a `python` number (DEFAULT_SIDE), which is what
# `cli` was renamed to on 2026-09-01.
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
    """Write the ledger ATOMICALLY -- temp file in the same directory, then
    os.replace, which is atomic on POSIX.

    WHY THIS IS NOT PARANOIA. `--record` is read-modify-write, and on 2026-09-06
    SEVEN sweep scripts were queued at once, each recording between two and eight
    entries when its measurement finished. The scripts serialise on the .olx
    lock, but only for the WRITE phase: a script's `--write` can succeed the
    moment the previous script's measurement PROCESSES exit, which is before that
    script has finished recording. A plain write_text in that window loses one
    side's recording silently and leaves a syntactically perfect ledger, so
    nothing downstream can tell. The old call also truncated the file before
    serialising, so an exception mid-dump left NO ledger at all -- 22 items of
    measurement, gone, with no copy on disk.

    Serialise first, replace second: the ledger is either fully the old one or
    fully the new one, and never a half of either.
    """
    import os
    import tempfile
    text = json.dumps(led, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=str(LEDGER.parent), prefix=".ledger.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, LEDGER)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _cells_from_artifact(item: str, side: str, out: str | None):
    """Per-cell right-counts rebuilt from a recorded artifact, or None.

    Mirrors what `record` stores in `cells`: for each participant, how many runs
    scored gold exactly. Used by `restore_previous`, whose `previous` summary
    does not carry them.
    """
    if not out:
        return None
    import pathlib as _pl
    import paths as _paths
    # NO LITERAL FALLBACK. `OUT_DIR` absent means the module was loaded without
    # its configuration, and reading the developer's own artifacts then is the
    # least safe answer available -- it succeeds, quietly, on the wrong tree.
    _root = _pl.Path(OUT_DIR) if "OUT_DIR" in globals() else _paths.OUT
    path = _root / out / f"{item}.runs.json"
    if not path.exists():
        return None
    try:
        doc = json.loads(path.read_text())
    except Exception:
        return None
    per: dict[str, int] = {}
    for run in doc.get("runs") or []:
        for r in run.get("results") or []:
            pid = r.get("participant_id") or int(
                str(r.get("cell", "p0/")).split("/")[0][1:])
            g = gold_cell(item, pid)
            if not g or g.get("score") is None:
                continue
            got = r.get("score")
            if got is None:
                got = _score_from_result(item, r) if "_score_from_result" in globals() else None
            if got is None:
                continue
            per[str(pid)] = per.get(str(pid), 0) + (1 if abs(got - g["score"]) < 1e-9 else 0)
    return per or None


def accept_design_change(item: str, slot: str, field: str) -> int:
    """Record a DELIBERATE change to one prompt field's design. 0 on success.

        python3 measured.py --accept-design-change Q4b b1_basis rule

    Prints the designed sha and the shipped text before rewriting, so accepting
    is an act with something to read rather than a rubber stamp. Refuses if the
    field does not exist, or if it already matches -- there is nothing to accept.
    """
    import json
    import pathlib
    import re
    import textwrap

    import handouts as H
    import enforcement as E
    spec = None
    for h in (1, 2, 3):
        try:
            spec = H.config(h)["rubric"].BY_ID.get(item)
        except Exception:
            continue
        if spec:
            break
    if not spec:
        print(f"REFUSING: no rubric item {item!r}", file=sys.stderr)
        return 1
    got = next((c.get(field) for c in (spec.get("credit") or [])
                if c.get("what") == slot), None)
    if got is None:
        print(f"REFUSING: {item}/{slot} has no {field!r} to accept. If the slot "
              f"was reverted, drop its line from {E.DESIGNED_SHA_FILE} instead.",
              file=sys.stderr)
        return 1
    path = pathlib.Path(__file__).parent / E.DESIGNED_SHA_FILE
    doc = json.loads(path.read_text())
    key = f"{item}|{slot}|{field}"
    new = E._field_sha(got)
    old = (doc.get("fields") or {}).get(key)
    if old == new:
        print(f"{key} already matches its design of record ({new}); nothing to accept")
        return 0
    print(f"ACCEPTING a design change to {item}/{slot}.{field}")
    print(f"    designed sha : {old or '(none -- new field)'}")
    print(f"    shipping sha : {new}")
    print(f"    the text now shipping, in full:\n")
    for line in textwrap.wrap(re.sub(r"\s+", " ", str(got)), 92):
        print(f"      {line}")
    doc.setdefault("fields", {})[key] = new
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"\n    recorded. {E.DESIGNED_SHA_FILE} now carries "
          f"{len(doc['fields'])} field(s).")
    return 0


def restore_previous(item: str, side: str = DEFAULT_SIDE) -> int:
    """Put back the recording a REVERT made current again. 0 on success, 1 if refused.

        python3 measured.py --restore-previous Q6 olx

    WHY THIS EXISTS. A reverted edit usually returns the prompt to the EXACT sha
    it had before, and the ledger already holds a real measurement taken at that
    sha, in `previous`. Re-sweeping to recover it spends ~230 calls to reproduce
    a number we have. Before this existed the alternative was hand-editing the
    ledger, which is how a number gets into it that nothing ever measured.

    THE GUARD IS THE WHOLE POINT AND IT IS NOT OPTIONAL: the CURRENT prompt sha
    must equal the sha the previous recording was taken at. If it does not, the
    revert did not land where it started -- something else changed the prompt too
    -- and putting the old number back would assert a measurement of a prompt
    that has never been run. That is indistinguishable from fabrication once it
    is in the file, so it is refused rather than warned about.

    IT IS NOT AN UNDO. It restores ONE side of ONE item from the entry's own
    `previous`, and it does not chain: there is one previous, so a second call
    after a second edit has nothing older to reach for and refuses.
    """
    if side not in SIDES:
        print(f"REFUSING: {side!r} is not one of {SIDES}", file=sys.stderr)
        return 1
    led = load()
    entry = ((led.get("items") or {}).get(item) or {}).get(side)
    if not entry:
        print(f"REFUSING: no {side} recording for {item}", file=sys.stderr)
        return 1
    prev = entry.get("previous") or {}
    if not prev.get("prompt_sha"):
        print(f"REFUSING: {item}/{side} has no previous recording to restore",
              file=sys.stderr)
        return 1
    current = prompt_sha(item, side)
    if prev["prompt_sha"] != current:
        print(f"REFUSING: {item}/{side} is at prompt {current} but the previous "
              f"recording was taken at {prev['prompt_sha']}. The revert did not "
              f"return the prompt to where that number was measured, so restoring "
              f"it would assert a measurement that was never run. Re-sweep instead.",
              file=sys.stderr)
        return 1
    if entry.get("prompt_sha") == current:
        print(f"{item}/{side} is already current at {current}; nothing to restore")
        return 0
    # `previous` IS A SUMMARY, NOT A FULL ENTRY -- six keys, and NO `cells`. And
    # `cell_bands` reads exactly that field, so promoting the summary verbatim
    # removed the item from EVERY cell-level check while leaving correct totals
    # in place. That happened to Q6 on 2026-09-06: four imperfect cells,
    # including TWO at 0 of 12, vanished from `cell_bands` and therefore from
    # `wrong_cells_without_an_owner`, which then reported zero orphans while two
    # always-wrong cells were invisible. The ledger looked healthier for having
    # lost data.
    #
    # So rebuild the per-cell counts from the artifact the summary names. If that
    # cannot be done, REFUSE: a totals-only entry is worse than a stale one,
    # because a stale entry is flagged and a cells-less entry is silently skipped.
    cells = _cells_from_artifact(item, side, prev.get("out"))
    if cells is None:
        print(f"REFUSING: {item}/{side}'s previous recording carries no per-cell "
              f"counts and its artifact ({prev.get('out')!r}) cannot be read. "
              f"Restoring totals alone would drop the item out of cell_bands and "
              f"every check built on it. Re-sweep instead.", file=sys.stderr)
        return 1

    was = f"{entry.get('numerator')}/{entry.get('denominator')} @ {entry.get('prompt_sha')}"
    restored = dict(prev)
    restored["cells"] = cells
    # The restored recording becomes current; what it replaces becomes `previous`,
    # so the entry still records that the reverted attempt happened.
    restored["previous"] = {k: v for k, v in entry.items() if k != "previous"}
    led["items"][item][side] = restored
    save(led)
    print(f"{item}/{side}: restored {prev.get('numerator')}/{prev.get('denominator')} "
          f"@ {prev['prompt_sha']} (was {was}); the reverted attempt is kept as "
          f"`previous`")
    return 0


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
            # DEMOTION. `prompt_sha` hashes the served tag entire, so an
            # attribute-only edit moves it while the model's question is
            # byte-identical -- and STALE PROMPT is priced at a re-sweep,
            # ~120 calls per item per side, to re-sample something that did not
            # change. Where the recorded ASK matches the current one, the runs
            # still answer today's question and only the derived scores are
            # suspect, which is precisely STALE SCORER and clears by re-record
            # for nothing.
            #
            # NOT a dismissal: the attribute that moved may well change scoring
            # (`maps=`, `forbid=`, `free=` all do), so the column still has to be
            # re-recorded. Calling it fresh would freeze a score the shipped
            # rules disagree with.
            #
            # Demoted only on a POSITIVE match of two recorded, non-empty
            # fingerprints. A column with no `ask_sha` -- every column recorded
            # before this existed -- falls through to the conservative verdict.
            _rec_ask, _now_ask = rec.get("ask_sha"), ask_sha(item, side)
            if _rec_ask and _now_ask and _rec_ask == _now_ask:
                out.append((item, f"STALE SCORER — the prompt sha moved "
                                  f"({rec.get('prompt_sha')} -> {want_prompt}) but "
                                  f"the ASK did not ({_now_ask}), so the tag changed "
                                  f"around an unchanged question; re-record, do not "
                                  f"re-sweep"))
                continue
            out.append((item, f"STALE PROMPT — measured at "
                              f"{rec.get('prompt_sha')}, now {want_prompt}"))
            continue
        # A scorer change invalidates a number exactly as a prompt change does.
        # Scoped by fingerprinting the item's OWN scoring path, so the blast
        # radius is COMPUTED rather than guessed. The guess it replaces -- "does
        # this sheet author any computed primitive" -- was true of twenty-one
        # items, which is indistinguishable from a global flag.
        want = scorer_sha(item, side)
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
# THE PAPER SIDE'S ARITHMETIC, which SCORER_PARTS has never covered. Everything
# above this line lives in agreement/olx_prompts/handouts -- the WEB path -- so a
# change to score.py moved no fingerprint and staled nothing, and the paper
# columns carried the WEB's scorer_sha as if it described them. That is the same
# hole `prompt_sha` had until 2026-09-10, when the paper prompt was found to be
# borrowing the web's stamp, and it is closed the same way: per SIDE.
#
# Scoped by BRANCH, for the reason the web side is scoped per item -- score.py
# picks one of these paths per item and the other cannot reach its number, so an
# edit to the operant ledger must not stale the eighteen slot-sheet items. The
# closures are small and exact: derive_oc_ledger + _expect_rule + _forbid_rule,
# and derive_ledger + _hedges.
PAPER_SIDES = ("paper", "paper_opus")
_PAPER_BY_BRANCH = {
    "derive_from_criteria": (("score", "derive_oc_ledger"),
                             ("score", "_expect_rule")),
    "derive_from_credit": (("score", "derive_ledger"),),
}


# The paper scorer's own student-facing composer. Neither `prompt_sha(.., paper)`
# nor `scorer_sha(.., paper)` covers it -- one hashes what the grader is asked,
# the other how its answers become a score, and neither says how the result is
# WORDED to the student. The web needed a third fingerprint for the same reason.
_PAPER_RENDER_FNS = (("score", "compose_feedback"),)


# WHAT THE HARNESS ASKS, which no fingerprint covered. `prompt_sha` hashes the
# `.olx` and `scorer_sha` hashes the SCORING functions; `build_prompt`,
# `checklist_guidance` and `build_schema` are in neither, so an edit to any of
# them changed every python prompt and moved nothing. That is not hypothetical:
# the verdict-default fix was detected only because `default_verdicts` happened
# to join `load_action`'s closure, and the `(left blank)` and dedent fixes -- 60
# cells across 18 items, plus 20 items' indentation -- would have moved NO stamp
# at all. Third instance of one hole today: the paper prompt had it until
# `prompt_sha_paper`, the app had it until `web_code_sha`, this is the harness's.
#
# NOT SCOPED PER ITEM, and that is correct here rather than lazy: every item
# passes through all four of these, so there is no primitive to scope by and a
# single fingerprint is not a "global flag" in the sense `_parts_for` guards
# against -- it is genuinely global behaviour.
_HARNESS_ASK_FNS = (("agreement", "build_prompt"),
                    ("agreement", "checklist_guidance"),
                    ("agreement", "build_schema"),
                    ("agreement", "default_verdicts"))


def harness_ask_sha() -> str:
    """Fingerprint of the code that builds what the HARNESS asks, 12 hex."""
    import hashlib
    import importlib
    import inspect

    out = []
    for mod, name in _scoped_closure(_HARNESS_ASK_FNS):
        try:
            got = inspect.getsource(getattr(importlib.import_module(mod), name))
            out.append(_behaviour_src(got))
        except Exception:
            out.append(f"<missing {mod}.{name}>")
    return hashlib.sha256("".join(out).encode()).hexdigest()[:12]


def paper_render_sha(item: str | None = None) -> str:
    """Fingerprint of the code that words the PAPER scorer's feedback, 12 hex."""
    import hashlib
    import importlib
    import inspect

    out = []
    for mod, name in _scoped_closure(_PAPER_RENDER_FNS):
        try:
            got = inspect.getsource(getattr(importlib.import_module(mod), name))
            out.append(_behaviour_src(got))
        except Exception:
            out.append(f"<missing {mod}.{name}>")
    return hashlib.sha256("".join(out).encode()).hexdigest()[:12]


def _paper_parts(item: str | None) -> tuple:
    """The paper scorer's arithmetic for one item, or all of it when None."""
    every = tuple(dict.fromkeys(p for ps in _PAPER_BY_BRANCH.values() for p in ps))
    if item is None:
        return every
    try:
        import handouts as H
        cfg = H.config(_jobs()[item]["handout"])["rubric"].BY_ID[item]
    except Exception:
        return every                      # unknown shape: assume all of it
    for flag, parts in _PAPER_BY_BRANCH.items():
        if cfg.get(flag):
            return parts
    return every                          # neither branch declared: assume all


SCORER_PARTS = tuple(dict.fromkeys(
    _ALWAYS
    + tuple(_BY_KIND.values())
    + tuple(part for parts in _BY_PRIMITIVE.values() for part in parts)))


@functools.lru_cache(maxsize=4096)
def _behaviour_src(src: str) -> str:
    """A function's source with its PROSE removed, so only behaviour is hashed.

    MEMOISED ON THE SOURCE TEXT, which is the whole of its input: this is a pure
    function, and it was 2,419 of the 3,268 `ast.parse` calls in one enforcement
    audit -- 74% of them -- because the same function bodies are re-hashed for
    every item and every side. Keying on the text means changed source is a
    different key automatically, so there is no staleness to reason about.

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


def _ts_top_fn(src: str, name: str) -> str:
    """A TOP-LEVEL TypeScript function's source, by LINE anchor.

    `function NAME(` at column 0 through the first line that is exactly `}`.

    NOT by brace-matching from the signature, which is what the first version
    did and it silently truncated: `choices: Record<string, string[]> = {}` is a
    parameter DEFAULT, so the matcher opened on that brace and closed on the
    same one, returning 15 lines of signature for a 136-line function. A hash
    over that would never move for an edit to the body -- detection that does
    not detect, which is the fault this whole helper exists to prevent. Object
    literal RETURN TYPES (`scoreSlotSheet`'s is one) break it the same way.

    Raises rather than returning None: a fingerprint that quietly covers nothing
    is worse than one that stops the run.
    """
    import re as _re

    lines = src.splitlines()
    pat = _re.compile(r"^(?:export\s+)?function\s+%s\s*\(" % _re.escape(name))
    for i, line in enumerate(lines):
        if not pat.match(line):
            continue
        for j in range(i + 1, len(lines)):
            if lines[j] == "}":
                block = "\n".join(lines[i:j + 1])
                if block.count("{") != block.count("}"):
                    raise SystemExit(
                        f"_ts_top_fn({name!r}): braces unbalanced over lines "
                        f"{i + 1}-{j + 1}; the line anchor did not find the end")
                return block
    raise SystemExit(f"_ts_top_fn: no top-level `function {name}` in the source")


def _ts_behaviour(text: str) -> str:
    """TypeScript with its PROSE removed, the analogue of `_behaviour_src`.

    Whole-line `//` comments only. An end-of-line `//` can live inside a string
    literal, and this file's descriptions are instruction text sent to a grader,
    so stripping there could silently change what is hashed.
    """
    import re as _re

    text = _re.sub(r"/\*.*?\*/", "", text, flags=_re.S)
    text = _re.sub(r"(?m)^\s*//[^\n]*$", "", text)
    return _re.sub(r"\s+", " ", text).strip()


# The web code that decides what the grader is ASKED, and the web code that
# decides how the answers SCORE. Split, because they fail differently: an ask
# change invalidates the recorded ANSWERS, a scoring change invalidates only the
# numbers computed from them and can be shown score-neutral by re-scoring.
_WEB_ASK_FNS = ("buildSlotSchema",)
# The BASE is what every item passes through whatever it authors. `mappedVerdict`
# and `countedVerdicts` are NOT here: they run only for an item that declares the
# primitive, so they are scoped below -- listing them in both places would leave
# the scoping inert, which it was until this line was corrected.
_WEB_SCORE_FNS = ("satisfiedMap", "chargedMap", "failedGate", "scoreSlotSheet",
                  "isSatisfied")
# And the code that decides what the STUDENT READS. A third kind, because it
# fails a third way: a render change alters neither the question asked nor the
# score, so neither of the other two stamps moves and an artifact written before
# a display fix is indistinguishable from one written after it. That is not
# hypothetical -- `counts` members rendered "not reported" until the app was
# fixed, and the old artifacts still say so, which read as a live defect.
_WEB_RENDER_FNS = ("composeSlotFeedback", "displayVerdict")

# SCOPED BY PRIMITIVE, exactly as `_BY_PRIMITIVE` scopes the python scorer. A
# helper that only runs for a primitive the item does not author cannot change
# what that item's student reads, so it must not move that item's fingerprint --
# otherwise one repair to `expectedVerdict` restamps all 26 columns and the
# stamp becomes a global flag, which is the thing per-item scoping exists to
# prevent (see _scoped_closure, where the same mistake cost ~1800 calls).
_WEB_BY_PRIMITIVE = {
    "equals": {"render": ("computedVerdict",)},
    "expect": {"render": ("expectedVerdict",)},
    "maps": {"render": ("mappedVerdict",), "score": ("mappedVerdict",)},
    "counts": {"render": ("countedVerdicts",), "score": ("countedVerdicts",)},
    "forbid": {"render": ("forbidden",)},
}


def _web_parts(kind: str, item: str | None) -> tuple:
    """The app functions THIS item's answer passes through, for one kind."""
    base = {"ask": _WEB_ASK_FNS, "score": _WEB_SCORE_FNS,
            "render": _WEB_RENDER_FNS}[kind]
    every = tuple(dict.fromkeys(
        base + tuple(n for m in _WEB_BY_PRIMITIVE.values()
                     for n in m.get(kind, ()))))
    if item is None:
        return every                      # the corpus-wide view the header quotes
    try:
        import agreement as A
        import olx_prompts as O
        job = next(j for _h, b in A.BLOCKS.items() for j in b.values()
                   if j["item"] == item)
        action = A.load_action(job["olx"], O.ACTION[item])
    except Exception:
        return every                      # unknown shape: assume all of it
    names = list(base)
    for prim, by_kind in _WEB_BY_PRIMITIVE.items():
        if action.get(prim):
            names.extend(by_kind.get(kind, ()))
    return tuple(dict.fromkeys(names))


def web_code_parts(kind: str = "ask", item: str | None = None) -> dict:
    """Each app function's own digest: {name: sha}. The unit of comparison.

    WHY THIS EXISTS, AND WHY THE AGGREGATE ALONE WAS WRONG. `web_code_sha`
    concatenates the functions named by `_web_parts` and hashes the result, so
    the fingerprint depends on TWO things: lo-blocks' code, and OUR LIST of
    which functions to hash. The list lives here, in the ledger. Adding a
    function to it -- refining our model of what renders -- moves the sha for
    every artifact ever stamped, and the audit then reports that 26 items have
    no artifact attributable to today's renderer.

    Measured 2026-09-14: exactly that happened. `slotSheet.ts` was byte-identical
    in both trees and untouched since 2026-09-13, the shipped `.olx` was
    unchanged, and the render fingerprint had still moved -- because this file
    had. A measurement instrument moving is not evidence about what students
    saw, and the remedy the finding implied was a ~3,100-call sweep to chase it.

    So compare PER FUNCTION, on the intersection of what both sides recorded: a
    name we did not hash before simply was not compared, while a function both
    sides hashed and that differs is a real change with a real remedy.
    """
    import hashlib
    from pathlib import Path

    import paths

    if kind not in ("ask", "score", "render"):
        raise SystemExit(f"web_code_parts: unknown kind {kind!r}")
    src = Path(paths.SLOTSHEET_TS).read_text()
    out = {}
    for n in _web_parts(kind, item):
        try:
            body = _ts_behaviour(_ts_top_fn(src, n))
        except SystemExit:
            body = f"<missing {n}>"
        out[n] = hashlib.sha256(body.encode()).hexdigest()[:12]
    return out


_WEB_CODE_SHA_MEMO: dict = {}


def web_code_sha(kind: str = "ask", item: str | None = None) -> str:
    """Fingerprint of the APP's own schema/scoring code, 12 hex.

    THE HOLE THIS CLOSES. `prompt_sha` hashes the `.olx` and `scorer_sha` hashes
    this repo's python; NEITHER covers lo-blocks, where the schema the grader
    actually answers is built and where the score is actually computed. So a
    change to `buildSlotSchema` altered every web prompt in the corpus and moved
    no fingerprint at all, and a change to `scoreSlotSheet`'s call sites changed
    every web score the same way. Recorded columns went on reading `ok`.

    That is not hypothetical: `scoreSlotSheet` takes `maps` as its ELEVENTH
    positional parameter and SlotSheetGrader passes ten, so the map never
    reaches the scorer -- which is why the app scores a mapped slot's recorded
    verdict, and why lo-blocks b6d3f070 went flat when it stopped asking for one.
    """
    import hashlib
    import os

    import paths

    if kind not in ("ask", "score", "render"):
        raise SystemExit(f"web_code_sha: unknown kind {kind!r}")

    # MEMOIZED ON THE FILE, NOT ON THE ARGUMENTS. This was 6.3s of a 48s
    # enforcement audit across 1,262 calls, every one of them re-reading
    # slotSheet.ts and re-deriving the same behaviour from it. The key carries
    # the file's mtime and size, so an edit to the app's scoring code moves the
    # fingerprint on the very next call -- which is the entire point of this
    # function and the one thing a cache here must not break.
    try:
        st = os.stat(paths.SLOTSHEET_TS)
        stamp = (st.st_mtime_ns, st.st_size)
    except OSError:                                 # pragma: no cover
        stamp = None
    if stamp is not None:
        hit = _WEB_CODE_SHA_MEMO.get((kind, item, stamp))
        if hit is not None:
            return hit

    src = Path(paths.SLOTSHEET_TS).read_text()
    names = _web_parts(kind, item)
    parts = [_ts_behaviour(_ts_top_fn(src, n)) for n in names]
    if kind == "score":
        # THE CALL SITES BELONG TO THE SCORER. Omitting an argument changes the
        # score without touching a single line of slotSheet.ts, which is exactly
        # the live defect: `_ScoreTable` passes eight of eleven and loses
        # `requires`, `forbid` and `maps`.
        import re as _re
        for f in (paths.LO / "packages/shared/components/blocks/grading/SlotSheetGrader.ts",
                  paths.LO / "packages/shared/components/blocks/grading/ScoreTable/_ScoreTable.tsx"):
            try:
                text = Path(f).read_text()
            except Exception:
                parts.append(f"<missing {f.name}>")
                continue
            for m in _re.finditer(r"scoreSlotSheet\(", text):
                depth, k = 0, m.end() - 1
                while k < len(text):
                    if text[k] == "(":
                        depth += 1
                    elif text[k] == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    k += 1
                parts.append(_ts_behaviour(text[m.start():k + 1]))
    out = hashlib.sha256("".join(parts).encode()).hexdigest()[:12]
    if stamp is not None:
        _WEB_CODE_SHA_MEMO[(kind, item, stamp)] = out
    return out


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
            # ALL THREE PROMPTS, one per prompt source. `prompt_sha_paper`
            # was missing entirely, so reading it off an era returned None and
            # looked like an unstamped artifact rather than an absent field.
            per[it] = {"prompt_sha": prompt_sha(it), "scorer_sha": scorer_sha(it),
                       "prompt_sha_python": prompt_sha(it, "python"),
                       "prompt_sha_paper": prompt_sha(it, "paper"),
                       # The paper scorer's own arithmetic, for the same reason
                       # `prompt_sha_paper` is here: an era that records only the
                       # web's fingerprint cannot date a paper artifact.
                       "scorer_sha_paper": scorer_sha(it, "paper"),
                       # PER ITEM, so a helper this item never calls cannot
                       # stale it. The top-level pair stays as the corpus view.
                       "web_ask_sha": web_code_sha("ask", it),
                       "web_score_sha": web_code_sha("score", it),
                       "web_render_sha": web_code_sha("render", it),
                       "paper_render_sha": paper_render_sha(it),
                       "harness_ask_sha": harness_ask_sha()}
        except Exception as e:
            per[it] = {"error": f"{type(e).__name__}: {e}"}
    return {
        # WHEN IT WAS MEASURED, not when the file was last written. Added
        # 2026-09-14 after an artifact assembled from older runs read as NEWER
        # than the clean data it superseded: `pooled_paper` pooled a failed
        # cell-fill and its mtime was the assembly date, so a freshness test on
        # file dates preferred the worse measurement. mtime dates the FILE; this
        # dates the RUNS.
        #
        # 179 of 335 artifact directories carry no era at all and none carries a
        # time, so they cannot be dated by anything but mtime and are therefore
        # not trustworthy as evidence of recency. Treat an undateable artifact
        # as REPLACEABLE: a newer stamped measurement supersedes it, and nothing
        # is owed to a number nobody can place in time.
        "measured_at": __import__("datetime").datetime.now().astimezone().isoformat(timespec="seconds"),
        # The APP's own code, which no other stamp covers. See web_code_sha.
        "web_ask_sha": web_code_sha("ask"),
        "web_score_sha": web_code_sha("score"),
        "web_render_sha": web_code_sha("render"),
        # THE PARTS, NOT ONLY THE AGGREGATE. The aggregate moves when OUR list of
        # functions changes; the parts let a reader compare the functions both
        # sides actually hashed and ignore the ones only one side knew about.
        "web_parts": {k: web_code_parts(k) for k in ("ask", "score", "render")},
        "git": _git("rev-parse", "HEAD") or "unknown",
        "dirty": bool(_git("status", "--porcelain")),
        # Empty when the writer did not say and the environment does not know.
        # Recorded either way, so "unstamped" is visible rather than assumed.
        "model": model or "",
        "backend": backend or "",
        "items": per,
    }


def safe_to_rerecord(item: str, side: str) -> tuple:
    """(ok, why) — may this column be re-recorded instead of re-swept?

    THE GUARD A BATCH RE-RECORD NEEDS. `record` stamps the CURRENT shas onto
    whatever runs it finds, so re-recording a column whose PROMPT really moved
    marks it fresh while its verdicts answer a question that no longer ships --
    destroying the evidence that a sweep was owed. Q1 was mis-stamped exactly
    that way on 2026-09-12 by a batch that selected on scorer-staleness alone;
    only a control failure in the interpretation check caught it.

    So: re-record when the ask is unchanged (or the prompt sha never moved), and
    refuse when it moved and cannot be shown to be the same question.
    """
    rec = entry(item, side)
    if not rec:
        return False, "not recorded"
    if rec.get("prompt_sha") == prompt_sha(item, side):
        return True, "prompt unchanged"
    rec_ask, now_ask = rec.get("ask_sha"), ask_sha(item, side)
    if rec_ask and now_ask and rec_ask == now_ask:
        return True, "prompt sha moved but the ask did not"
    if not rec_ask:
        return False, ("the prompt sha moved and this column carries no recorded "
                       "ask_sha, so the question cannot be shown unchanged -- "
                       "re-sweep, which also stamps one")
    return False, "the ask itself moved -- re-sweep"


def ask_sha(item: str, side: str | None = None) -> str:
    """SHA-256 of WHAT THE MODEL IS ASKED for this item, 12 hex — or "" if it has none.

    `prompt_sha` hashes the served `.olx` tag ENTIRE, attributes included. That is
    deliberately conservative -- an attribute can change scoring -- but it means a
    tag-only edit reads as STALE PROMPT while the model's question is byte-identical,
    and a STALE PROMPT is priced at a re-sweep. Adding `free=` to one tag on
    2026-09-12 did exactly that: ~120 calls per side to re-sample a question that had
    not moved.

    This hashes the ASK instead: the assembled prompt and the response schema, over
    every included cell. Two columns with the same `ask_sha` were asked the same
    thing, whatever their tags look like, and the difference between them is at most
    a SCORER difference -- which a re-record clears for nothing. See
    `_staleness_lines`, which demotes on exactly this.

    PROMPT *AND* SCHEMA, not the prose alone: a schema change alters what the model
    may answer without touching a word, so a text-only comparison would wave a real
    prompt change through.

    "" FOR THE PAPER SIDES, which are not served the `.olx` at all -- their prompt is
    `score.fingerprint_text`, which `prompt_sha` already hashes directly, so there is
    no gap between tag and ask to close. A paper prompt change is genuinely a
    re-sweep and must never be demoted.
    """
    import hashlib
    import json as _json

    if side in PAPER_SIDES:
        return ""
    try:
        import agreement as A
        import olx_prompts as O

        job = _jobs()[item]
        act = A.load_action(f"bmod_handout{job['handout']}.olx", O.ACTION[item])
        schema = A.build_schema(act["slots"], act["excluded"], act["show_checks"],
                                act["cover"], act["choices"])
        parts = [_json.dumps(schema, sort_keys=True)]
        excl = set(exclusions(item) or [])
        for pid in sorted(set(range(1, 21)) - excl):
            try:
                fx = A.fixture_for(item, pid)
            except Exception:
                continue
            parts.append(A.build_prompt(act["body"], fx)
                         + A.checklist_guidance(act["show_checks"]))
        return hashlib.sha256("\x00".join(parts).encode()).hexdigest()[:12]
    except Exception:
        # NOT an exception swallowed into a false "unchanged": an empty string is
        # read as "no ask recorded", which suppresses the demotion and leaves the
        # conservative prompt_sha verdict standing.
        return ""


def scorer_sha(item: str | None = None, side: str | None = None) -> str:
    """SHA-256 of the code that turns THIS item's answers into a score, 12 hex.

    Prose-insensitive and scoped: see `_behaviour_src` and `_parts_for`. Called
    with no item it fingerprints the whole path, which is what the ledger header
    and the reports quote.

    PER SIDE, exactly as `prompt_sha` is. The paper sides are scored by score.py
    and nothing else, so they fingerprint score.py's ledger branch for this item
    and not the web's scorers -- otherwise a web-only scorer edit would report
    the paper measurement as stale, spending a sweep to reproduce a number that
    could not have moved, and a score.py edit would report nothing at all. See
    PAPER_SIDES and _paper_parts.
    """
    import hashlib
    import importlib
    import inspect
    src = []
    # The CLOSURE of the scoped roots, not the roots alone -- minus the parts the
    # scoping deliberately left out for THIS item. See _scoped_closure.
    roots = _paper_parts(item) if side in PAPER_SIDES else _parts_for(item)
    for mod, name in _scoped_closure(roots):
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


def _check_runs_are_measurements(doc: dict, runs_path: str) -> list[str]:
    """Is every run in this artifact a MEASUREMENT, or is one of them a failure?

    ADDED 2026-09-08 as the PREVENTION for a defect `enforcement` could only
    detect after the fact. 18 of 6,147 recorded cell-runs carried a
    247-character feedback --

        Error: LLM error (429): Azure API error: 429 ("Your requests to
        gpt-5-mini ... have exceeded ...

    -- where a real run on those items carries 2,500-4,900, and were RECORDED AS
    SCORED RUNS. An error is not a measurement, so it must not reach the ledger.

    TWO ARMS, because the string test alone is provider-shaped:

      1. THE FEEDBACK IS AN ERROR. Matches an `Error:` prefix or an embedded
         `Azure API error`. Deliberately narrow: a corpus-wide scan for
         error|timeout|rate limit|429|500|502|503|overloaded|unavailable|
         refused|exception|traceback|truncat|could not parse|invalid json|
         empty response|no response returned 42 rows, of which 18 were the 429s
         and 24 were LEGITIMATE GRADER PROSE -- "fix small typographical
         errors", a student's own "{{corpus:2b/p6:response:141:162:sha=bd226d7c8a18}} stretching",
         "unavailable" describing an authored deprivation, "*No response* -- the
         box is empty". Widening it would buy 24 false positives and nothing.

      2. THE RUN RETURNED NO VERDICTS AT ALL, whatever the provider said. This
         is the provider-independent arm and it is what the string test cannot
         do. WK1/p1's rejected run was the ONE row in 6,147 with `score` null
         AND an empty verdict set, so the signal is real and it is rare.
         NOT the same as empty feedback: 528 rows have that, almost all on the
         derived items, which make no LLM call and are perfectly valid.

    WHY IT MUST REFUSE RATHER THAN WARN. A 429 does not fail safe. Across the 18
    the recorded score was 0.00 seven times, 4.00 NINE TIMES -- full marks --
    2.00 once and null once, so the defect INFLATED cells as well as deflating
    them, and it did so while carrying a FULL, well-formed verdict set that
    every contract and sha check accepted. On DAY2/p12 the verdicts were
    identical to three runs scoring 4.00 and the recorded score was 2.00: the
    score did not follow the verdicts at all. Nothing downstream can tell such a
    run from a judgement, which is exactly why the gate belongs here, at the one
    door into the ledger.

    Shares `record`'s existing MEASURED_ALLOW_OFF_CONTRACT escape, because the
    honest use of it is the same: record it anyway and say in the entry why the
    number is worth keeping.
    """
    import cross_path as X

    out = []
    for n, run in enumerate((doc.get("runs") or [])):
        for r in (run.get("results") or []):
            fb = str(r.get("feedback") or "")
            try:
                _, pid, score, verdicts = X.result_cell(r)
            except Exception:
                pid, score, verdicts = None, None, None
            if fb.startswith("Error:") or "Azure API error" in fb:
                head = fb.split("(", 2)[0].strip()[:60]
                out.append(
                    f"{runs_path} run {n}, cell p{pid}: recorded with score "
                    f"{score} but its feedback is an API ERROR ({head}). An "
                    f"error is not a measurement -- re-run the cell or drop the "
                    f"run; do not pool it")
            elif not verdicts:
                out.append(
                    f"{runs_path} run {n}, cell p{pid}: recorded with score "
                    f"{score} and NO VERDICTS AT ALL. Whatever the provider "
                    f"said, a run that judged nothing is not a measurement")
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


def _refuse_unreachable(item: str, runs_path: str, side: str) -> None:
    """Refuse to record an artifact the ledger will not be able to read back.

    THE LEDGER STORES A POINTER, NOT THE RUNS. `_out_pointer` writes the
    artifact's directory RELATIVE TO paths.OUT, and falls back to the bare
    directory NAME for anything outside that tree -- which resolves only if a
    directory of that name happens to exist under paths.OUT. Fold somewhere else
    and the column records fine, reads back as nothing, and every downstream
    check silently agrees that there is nothing wrong on that side.

    THAT IS NOT HYPOTHETICAL, TWICE. `record`'s own comment already describes it
    costing five wrong cells when sweep_paper.sh folded into `out/<dir>/runs/`
    and the basename came out as the literal "runs". On 2026-09-10 it happened
    again at full scale: all 26 paper columns were folded into a scratchpad
    directory, recorded without complaint, and every one of them had unreachable
    per-cell data. `check_mapped_slots_agree_with_their_map` reported the same
    count before and after -- having read zero paper rows.

    Checked here because this is the moment the path is in hand. The artifact
    itself is proof it exists; what needs proving is that the POINTER finds it.
    """
    import paths as _p

    ptr = _out_pointer(runs_path)
    resolved = Path(_p.OUT) / ptr / f"{item}.runs.json"
    if resolved.exists():
        # AND IT MUST BE THIS ARTIFACT. Resolving is not enough: the fallback is
        # a bare directory NAME, so folding to `somewhere_else/foo` while an
        # unrelated `out/foo` exists would point the column at the wrong runs --
        # a worse failure than an unreadable one, because it reads.
        try:
            here = json.loads(Path(runs_path).read_text())
            there = json.loads(resolved.read_text())
        except Exception:
            return                      # unreadable is the caller's problem below
        def shape(d):
            runs = d.get("runs") or []
            return (len(runs), [len(r.get("results") or []) for r in runs])
        if shape(here) != shape(there) and Path(runs_path).resolve() != resolved.resolve():
            raise SystemExit(
                f"REFUSED: {item} [{side}] would record `out` = {ptr!r}, which "
                f"resolves to {resolved} -- a DIFFERENT artifact from the one "
                f"passed ({runs_path}): {shape(there)} runs/results against "
                f"{shape(here)}. The column would read back someone else's runs."
            )
        return
    raise SystemExit(
        f"REFUSED: {item} [{side}] would record `out` = {ptr!r}, which resolves "
        f"to {resolved} and does not exist. The artifact is at {runs_path}, "
        f"OUTSIDE paths.OUT ({_p.OUT}), so the column would read back as nothing "
        f"and every check over it would silently find nothing wrong. Fold or copy "
        f"the artifact under paths.OUT and record from there."
    )


def append_runs(item: str, new_runs_path: str, side: str = DEFAULT_SIDE) -> None:
    """Add runs to an existing column instead of replacing it.

    WHY THIS EXISTS. `record` overwrites, so the only way to take a 3-run column
    to 6 was to sweep 6 fresh and throw the first 3 away. Across the corpus that
    was ~5,900 calls where ~2,900 would do: most columns are short by exactly
    the three runs a screen produced, and runs are independent samples of the
    same prompt -- there is nothing about the first three that stops them being
    the first three of six.

    WHEN IT IS LEGITIMATE, and the answer is narrow. Runs may be pooled only if
    they are samples of THE SAME THING: same prompt, same scoring code, same
    model and backend, same cells. That is exactly what `stale_sides` already
    decides, so a stale column is REFUSED here rather than extended -- if the
    prompt moved, the old runs describe a tree that no longer exists and the
    honest move is to discard them, which is what `record` is for.

    The merged artifact is written under paths.OUT with the canonical name so
    `_runs_path` can find it and `_refuse_unreachable` accepts it; the ledger's
    `out` then points at the pooled file, which is what later readers get.
    """
    import cross_path
    import paths

    bad = stale_sides(item)
    if side in bad:
        raise SystemExit(
            f"REFUSED: {item} [{side}] is stale -- {bad[side]}. Runs may only be "
            f"pooled when they sample the SAME prompt, scorer and cells; a stale "
            f"column's earlier runs describe a tree that no longer exists. "
            f"Re-sweep and `--record` it instead, which replaces rather than adds")
    old_path = _runs_path(item, side)
    if not old_path:
        raise SystemExit(
            f"REFUSED: {item} [{side}] has no reachable artifact to append to. "
            f"Record it first")
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_runs_path).read_text())
    for key in ("model", "backend"):
        a = ((old.get("era") or {}).get(key) or "")
        b = ((new.get("era") or {}).get(key) or "")
        if a != b:
            raise SystemExit(
                f"REFUSED: {item} [{side}] existing runs ran on {key}={a!r} and "
                f"the new ones on {key}={b!r}. Pooling them would average two "
                f"different experiments")

    def cells(doc):
        out = set()
        for run in doc.get("runs") or ():
            for r in run.get("results") or ():
                c = cross_path.result_cell(r)
                if c:
                    out.add(c[1])
        return out

    # A SUBSET IS ALLOWED; A SUPERSET IS NOT. The ledger's `runs` is
    # `min(observations across cells)`, so ONE cell missing from one run caps
    # the whole column -- NR/python holds 6 runs and reads 5 because four cells
    # came back without a usable score once. Lifting that minimum means running
    # those four cells again, not all twenty, and the artifact from a
    # `--participants` sweep covers only them. Pooling it adds observations
    # where they are missing and leaves every other cell untouched, which is
    # precisely the top-up and costs nothing extra.
    #
    # A cell the existing column does NOT have is still refused: that would
    # raise the denominator to something no run measured, which is the failure
    # the strict check was written for.
    extra = cells(new) - cells(old)
    if extra:
        raise SystemExit(
            f"REFUSED: {item} [{side}] the new artifact covers cell(s) "
            f"{sorted(extra)} that the recorded column does not -- pooling "
            f"would report a denominator no run measured")

    merged = dict(new)                      # newer era: git, dirty, timestamp
    merged["runs"] = (old.get("runs") or []) + (new.get("runs") or [])
    dest = Path(paths.OUT) / f"pooled_{side}" / f"{item}.runs.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(merged))
    print(f"  pooled {len(old.get('runs') or [])} + {len(new.get('runs') or [])} "
          f"= {len(merged['runs'])} run(s) for {item} [{side}]")
    record(item, str(dest), side)


def record(item: str, runs_path: str, side: str = DEFAULT_SIDE) -> None:
    """Write item's entry FROM a run artifact, so it cannot claim what was not run."""
    _refuse_unreachable(item, runs_path, side)
    import handouts as H
    import gold
    import agreement_app as APP
    import cross_path as X

    # THE BAND EACH CELL WAS IN BEFORE THIS RECORDING REPLACES IT (subgoal E42).
    # Taken FIRST, before the ledger is loaded or written, because `cell_bands`
    # reads the SAVED ledger: after `save()` the prior band is gone, and it is the
    # only thing about a measurement that cannot be recovered afterwards. The run
    # artifact keeps the runs and git keeps the entry, but "what band was this
    # cell in when the change landed" was answerable only from prose written by
    # hand, which is what E42 was filed on.
    #
    # DERIVED, NEVER RE-DERIVED. It calls `cell_bands` and keeps what that
    # returns. The thresholds are not repeated here and must not be: two
    # implementations of one rule is the class this project keeps closing, and
    # the ranking alone has grown a duplicate band rule twice.
    #
    # POOLED, like the bands themselves, so a python recording's "before" already
    # includes whatever the olx side had recorded at that moment. That is the
    # honest reading -- the band as it stood when THIS measurement landed -- and
    # not a per-side band, which `cell_bands` does not define.
    bands_before = {cell.split("/p", 1)[1]: band
                    for cell, (_r, _n, band) in cell_bands().items()
                    if cell.rsplit("/p", 1)[0] == item}

    h = _jobs()[item]["handout"]
    g = H.apply_corrected_gold(
        {1: gold.load_h1, 2: gold.load_h2, 3: gold.load_h3}[h](), h)
    if item == "1c":
        g, _ = APP.rebuild_declared_gold({p: dict(v) for p, v in g.items()})
    ex = set(exclusions(item))
    per: dict[int, list[bool]] = {}
    exc: dict[int, list[bool]] = {}
    doc = json.loads(Path(runs_path).read_text())
    if side not in SIDE_CONTRACT:
        raise SystemExit(f"unknown side {side!r}; expected one of {SIDES}")
    bad = _check_side_contract(side, doc, runs_path)
    # AND: is every run a measurement? An API error carries a full, well-formed
    # verdict set, so the contract check above accepts it -- see
    # `_check_runs_are_measurements` for the 18 that got in this way.
    bad += _check_runs_are_measurements(doc, runs_path)
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
        # What the model was ASKED, so a later tag-only edit can be demoted from
        # STALE PROMPT to STALE SCORER instead of buying a sweep. See ask_sha.
        # A column recorded before this existed carries no `ask_sha` and is never
        # demoted -- it gets one from its next sweep, exactly as the era stamps do.
        "ask_sha": ask_sha(item, side),
        "scorer_sha": scorer_sha(item, side),
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
        # {pid: band} as it stood BEFORE this recording -- see the note in
        # record(). Top level rather than inside `previous`, because a FIRST
        # recording on one side can still have a pooled band from the other, and
        # `previous` exists only when this side has been recorded before.
        "bands_before": bands_before,
    }
    if prior:
        led["items"][item][side]["previous"] = {
            k: prior.get(k) for k in
            ("numerator", "denominator", "runs", "out", "prompt_sha", "scorer_sha")
        }
    save(led)
    # THE SIDE'S OWN PROMPT, not `prompt_sha(item)`. Unsided, this printed the
    # OLX hash while storing the recorded side's -- so a paper recording
    # announced a sha that was not the one it wrote, which is the confusion the
    # paper branch exists to end.
    print(f"{item} [{side}]: {totals[n // 2]}/{len(per)} recorded at prompt "
          f"{prompt_sha(item, side)} over {len(per)} cells (runs {totals})")
    # WHAT MOVED, printed here because this is the moment the question is asked
    # and the only moment both bands are in hand. `bands_before` was taken from
    # the ledger as it stood on entry, and `cell_bands` now reads what was just
    # saved, so this compares the same cells across exactly this recording. A
    # cell crossing INTO or OUT OF `on_the_line` is the one section 2d warns
    # about: it says the verdict moved by a single run.
    moved = band_moves(item, side)
    for ln in moved:
        print(f"  band: {ln}")
    if not moved:
        print("  band: no cell changed band")
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
        # rebuild_declared_gold removes their gold rows. Reporting those as "unmeasured"
        # every run would nag forever about cells nothing can settle.
        try:
            import gold as _g
            _gold_rows = H.apply_corrected_gold(
                {1: _g.load_h1, 2: _g.load_h2, 3: _g.load_h3}[job["handout"]](),
                job["handout"])
            if item == "1c":
                import agreement_app as _APP
                _gold_rows, _ = _APP.rebuild_declared_gold(
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
                # are exactly this: rebuild_declared_gold removes their gold rows and the
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
            # THE PREPARED ACCESSORS, not a hand-rolled key list. This read
            # `c.get("checks") or c.get("verdicts")` and the PAPER artifact spells
            # its verdicts `credit_checks`, so every paper cell signed as
            # `(pid, (), ())` -- 120 empty signatures per item, matching nothing,
            # while `result_cell` two lines up had already returned the verdicts
            # correctly and they were being thrown away as `_v`. The paper column
            # was invisible here and read as "nothing to compare".
            verd = dict(_v or {})
            extra = dict(X.result_picks(c) or {})
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


def _ENF():
    """enforcement, imported lazily -- it imports measured at module scope."""
    import enforcement as _E
    return _E


# `avoidance_frame` is the one field whose SENSE flips between the sides, and
# ALIAS records why in prose: "The web renamed this to say the good state, and
# inverted it: `met` is phrased directly. The CLI input keeps the old name and
# its boolean sense (True = phrased by what is avoided)." The NAME mapping is
# machine-readable there; the inversion is not, so it is named here and nowhere
# else.
_INVERTED_SENSE = frozenset({"avoidance_frame"})


def _web_slot_names(item_id: str, handout: int) -> set:
    """Every slot key the WEB sheet offers for an item, LLMAction or sheet-only."""
    import agreement as A
    import olx_prompts as O

    if item_id in O.SHEET_ONLY:
        return {s["key"] for s in O.parse_slots(*O._slots_attr(handout, O.SHEET_ONLY[item_id]))}
    spec = A.load_action(f"bmod_handout{handout}.olx", O.ACTION[item_id])
    return {s["key"] for s in spec["slots"]}


def _web_credit_slots(item: dict, verd: dict, picks: dict, web_keys: set) -> dict:
    """The web's judgments as paper's `slots`, in paper's names and tokens.

    THREE THINGS A NAIVE PASS DROPS, and a dropped slot is not a missing score
    but a WRONG one: `derive_ledger` reads an absent slot as `absent` and
    charges it. Each of these was measured as an apparent scorer disagreement
    before being recognised as a reader bug.

      * A COMPUTED key (maps/expect/equals/forbid, and counted members) is
        recorded null on the web because nothing asks the model for it. Omit it
        and let derive_ledger compute it from the operands.
      * A `derived` kind paper CANNOT compute -- the ones COMPUTE_EXEMPT
        declares, which read the web page's typed fields -- is a platform gap
        rather than arithmetic, so the web's recorded value is passed THROUGH.
      * A PICK answers `refers_to`, not `verdict`; and a cover member folds the
        identity into the verdict on this side.
    """
    import enforcement as E

    exempt = set((E.COMPUTE_EXEMPT.get("derived") or {}).get("kinds", ()))
    computed = set()
    for kind in ("maps", "expect", "equals", "forbid"):
        for r in item.get(kind) or ():
            if isinstance(r, dict) and r.get("key"):
                computed.add(r["key"])
    for r in item.get("derived") or ():
        if isinstance(r, dict) and r.get("key") and r.get("kind") not in exempt:
            computed.add(r["key"])
    for cr in item.get("counts") or ():
        computed.update(cr.get("slots") or ())
    cover = {k for g in (item.get("cover") or ()) for k in g["keys"]}

    out = {}
    for c in item.get("credit") or []:
        key = c["what"]
        if key in computed:
            continue
        w = key if key in web_keys else E.web_name(key, web_keys)
        if w is None:
            continue
        v, pick = verd.get(w), picks.get(w)
        # BLANK IS MISSING, NOT AN ANSWER. `_our_failing_slots` records the trap:
        # "a python result stores a pick's value in `answers` and an EMPTY STRING
        # for the same key in `checks`". Testing `v is None` let that empty
        # string through as the verdict, so every pick on the python side
        # compared blank against a real answer and scored 0% -- a perfect zero,
        # which is the tell for an instrument fault rather than a divergence. It
        # halved every pick's apparent agreement in the pooled readout
        # (Q4a/antecedent_kind_1 read 45% where olx alone reads 89%).
        blank = not str(v if v is not None else "").strip()
        # A COVER MEMBER'S VERDICT OUTRANKS ITS LABEL. The web answers two
        # fields -- a verdict and `refers_to` -- and paper folds them into one,
        # so the fold has to respect which field carries the information. An
        # EMPTY box is `('absent', 'none')`, and reading the label first turned
        # that into `neither`: a different paper verdict with a different code
        # (`A_MISMATCH` against `A_NOT_STATED`), meaning "named something, but
        # not one of the listed items" rather than "named nothing".
        #
        # p7/Q6 is the case. The student wrote ONE antecedent/consequence pair,
        # so the fixture hands the web four empty second-position boxes and it
        # records `('absent','none')` on each. Paper, judging the same response,
        # says `absent` -- and agreed all along. The label-first fold reported it
        # as a divergence on state_a2 and state_c2 across most of the corpus.
        if key in cover and not blank and str(v).strip() != "met":
            pass                       # the failing verdict IS the answer
        elif key in cover and pick:
            v = "neither" if pick == "none" else pick
        elif blank and pick is not None:
            v = pick
        elif blank:
            continue
        if v is None:
            continue
        pairs = E.VERDICT_PAIRS.get(f"{item['id']}/{key}") or {}
        out[key] = {"verdict": str(pairs.get(v, v)), "evidence": "x"}
    return out


def _web_oc_analysis(item: dict, verd: dict, picks: dict, web_keys: set) -> dict:
    """The web's judgments as paper's `oc_analysis`, READ OFF PAPER'S SCHEMA.

    Hand-listing the fields got it wrong: it omitted `trigger_behavior` and
    `agent_delivers_consequence`, which WK1 asks for by those exact names and
    the web answers under them, and the two dropped operands read as a scorer
    disagreement on 35 cells. The field list comes from `build_schema`, the
    names from `enforcement.web_name`, and the conversion from the TYPE the
    schema declares.
    """
    import enforcement as E
    import score as SC

    props = (SC.build_schema(item)["properties"]
             .get("oc_analysis", {}).get("properties", {}))
    out = {}
    for field, spec in props.items():
        w = field if field in web_keys else E.web_name(field, web_keys)
        if w is None:
            continue
        if spec.get("type") == "boolean":
            v = verd.get(w)
            if v is None:
                continue
            met = str(v).strip() == "met"
            out[field] = (not met) if field in _INVERTED_SENSE else met
        elif spec.get("enum") or picks.get(w) is not None:
            v = picks.get(w) or verd.get(w)
            if v:
                out[field] = str(v)
        elif str(verd.get(w) or "").strip() == "met":
            # free text: derive_oc_ledger only tests whether it is non-empty
            out[field] = "named"
    return out


def web_judgments_through_paper() -> dict:
    """Do the web's judgments produce the web's score in PAPER's arithmetic?

    THE WIDE DIRECTION. `paper_scorer_agreement` asks the same question the
    other way round and can only use items with a recorded PAPER artifact --
    two of them, 240 cells. Every item has a recorded olx sweep, so this covers
    the corpus: 26 items and ~3,100 cells. Holding the judgments fixed removes
    the model, so a difference here is the two scoring implementations
    disagreeing rather than sampling.

    Measured 2026-09-09 at 3106 of 3120, with 24 of 26 items identical on every
    cell. The 14 exceptions are the KNOWN off-map recording divergence, not a
    new finding: 1c's `legend` verdict sits off its own map on 19 cells and 13
    of those are score-affecting, which is exactly the caveat
    `check_mapped_slots_agree_with_their_map` states.
    """
    import cross_path as X
    import handouts as H
    import score as SC

    out = {"agree": 0, "differing": [], "errors": [], "items": []}
    for item_id in sorted(_jobs()):
        handout = _jobs()[item_id]["handout"]
        item = H.config(handout)["rubric"].BY_ID.get(item_id)
        doc = _runs_doc(item_id, "olx")
        if not item or not doc:
            continue
        try:
            web_keys = _web_slot_names(item_id, handout)
        except Exception:
            continue
        out["items"].append(item_id)
        for run in doc.get("runs") or []:
            for r in run.get("results") or []:
                got = X.result_cell(r)
                if not got or got[2] is None:
                    continue
                _i, pid, web_score, verd = got
                picks = X.result_picks(r) or {}
                try:
                    if item.get("derive_from_criteria"):
                        raw = {"oc_analysis": _web_oc_analysis(item, verd or {}, picks, web_keys)}
                        led, _c, _u, _adv = SC.derive_oc_ledger(item, raw)
                    else:
                        slots = _web_credit_slots(item, verd or {}, picks, web_keys)
                        if not slots:
                            continue
                        led, _c, _u = SC.derive_ledger(item, {"slots": slots},
                                                       "the student's response")
                except Exception as exc:
                    out["errors"].append(f"{item_id}/p{pid}: {type(exc).__name__}: {exc}")
                    continue
                paper = max(0.0, min(item["max"],
                                     item["max"] - sum(d["pts"] for d in led)))
                if abs(paper - float(web_score)) < 1e-9:
                    out["agree"] += 1
                else:
                    out["differing"].append((item_id, pid, float(web_score), paper))
    return out


def mirror_self_control() -> list:
    """(side, item, reproduced, total) — can a side's arithmetic reproduce its own scores?

    THE CONTROL FOR EVERY CROSS-SCORER COMPARISON. Driving one side's verdicts
    through the other's arithmetic only means something if the arithmetic can
    first reproduce ITS OWN side's scores from ITS OWN recorded verdicts. That
    was never checked, and it fails: see
    enforcement.check_mirror_reproduces_its_own_scores for the measurement and
    the cause.

    Deliberately built the way the production path builds it --
    `dict(job, slots=..., cover=..., requires=...)`, the job first -- because
    reading `load_action` alone omits `kind` and `cadence`, which live on the
    job, and a control assembled differently from production is not a control.
    """
    import agreement as A
    import cross_path as X
    import handouts as H
    import olx_prompts as O

    jobs = {j["item"]: j for _h, b in A.BLOCKS.items() for j in b.values()}
    out = []
    for item in sorted(_jobs()):
        job = jobs.get(item) or {}
        scorer = A.SCORERS.get(job.get("kind"))
        if scorer is None:                 # type_stated / data_presence: no mirror
            continue
        try:
            action = A.load_action(job["olx"], O.ACTION[item])
            rub = H.config(_jobs()[item]["handout"])["rubric"].BY_ID[item]
        except Exception:
            continue
        merged = dict(job, slots=action["slots"], cover=action["cover"],
                      requires=action["requires"])
        for side in ("olx", "python"):
            doc = _runs_doc(item, side)
            if not doc:
                continue
            ok = n = 0
            for run in doc.get("runs") or ():
                for r in run.get("results") or ():
                    c = X.result_cell(r)
                    if not c or c[2] is None:
                        continue
                    # REJOIN THE PICKS. The two sides record a classification
                    # in a SEPARATE top-level field -- `refers_to` on the app,
                    # `answers` on the harness -- while `result_cell` returns
                    # only the verdict map. Feeding the verdicts alone drops
                    # every pick, so `derived`/`equals`/`expect`/`maps` recompute
                    # from an empty operand and the mirror reproduced 43% of the
                    # app's own scores. It is not a scoring disagreement; it is
                    # reading half the record. With the picks back it is 100%.
                    picks = (r.get("refers_to") if side == "olx"
                             else r.get("answers")) or {}
                    # A COUNT GOES IN `count`, DECIDED BY THE SLOT SPEC and not
                    # by sniffing the value's type. The artifact flattens `count`
                    # and `verdict` into one column, so a reconstruction that puts
                    # everything back as `verdict` silently depends on
                    # expand_counted's legacy fallback to read it again -- and
                    # removing that fallback then reads every counted member as
                    # absent, which measures the reconstruction rather than the
                    # engines. Q1 read 0/120 that way. The schema has asked for
                    # `count` since the counts migration; only this rebuild
                    # un-migrated it.
                    # T11: `agreement.count_keys` is the ONE authority on
                    # which slots hold a number. This carried its own copy of
                    # the rule -- the duplication the helper exists to end.
                    _counted = A.count_keys(action)
                    checks = {
                        k: {("count" if k in _counted else "verdict"): v,
                            **({"refers_to": picks[k]}
                               if picks.get(k) is not None else {})}
                        for k, v in (c[3] or {}).items()
                        if v is not None or picks.get(k) is not None
                    }
                    try:
                        # Uniform across sides, per the no-item-dependent-
                        # mechanism rule: the app records the verdicts it ASKED
                        # (null where a slot was computed or suppressed), so the
                        # computed families must be filled before scoring. On the
                        # harness side they are already filled and refilling them
                        # is idempotent -- measured at 2908/2908 either way -- so
                        # one path serves both rather than a per-side branch.
                        # Fill-only, exactly as paper_scorer_agreement does
                        # it -- ONE rule for every side, content differing and
                        # mechanism not. The app records a computed slot as
                        # null, so on almost every cell there is nothing to put
                        # back and this is identical to letting the computation
                        # win. Where the app DID record one it scored that, and
                        # restoring it is what the app did: 1c/`legend`, the
                        # last 10 cells short of a perfect control.
                        filled = A.apply_computed(
                            action, dict(checks), A.fixture_for(item, c[1]))
                        filled.update(checks)
                        checks = filled
                        s, _f = scorer(merged, rub, checks)
                    except Exception:
                        continue
                    n += 1
                    ok += abs(s - float(c[2])) < 1e-6
            if n:
                out.append((side, item, ok, n))
    return out


def paper_scorer_agreement() -> dict:
    """Do the PAPER and WEB scorers turn the same verdicts into the same score?

    THE QUESTION `scoring_logic_agreement` CANNOT ASK. That one matches whole
    verdict SIGNATURES between two sides, which requires both to have recorded
    the same slot KEYS. Paper never does: on Q4a the python side records
    `antecedent_kind_1/2` and `confident` and the paper side records neither, so
    the sorted tuples cannot collide and the pair reported 0 shared signatures --
    no evidence at all, for either answer. It compares `olx` against `python` and
    the paper scorer has never been in it.

    So drive the OTHER engine instead of matching keys: take each paper cell's
    recorded verdicts and run them through `agreement.score_slots`, the web
    mirror's arithmetic. Identical verdicts must give an identical score. A key
    the paper side never recorded is simply unanswered, which both engines
    already handle, so the differing slot sets stop being an obstacle.

    IT SEPARATES THE SCORER FROM THE MODEL. Every rate comparison mixes them --
    a cell differs and it could be the model or the arithmetic. Holding the
    verdicts fixed leaves only the arithmetic.

    Coverage is the caveat and is returned with the result: only items with a
    recorded paper artifact can be compared, and at the time of writing that is
    Q4a and Q4c. Silence over two items is not silence over twenty-six.
    """
    import agreement as A
    import cross_path as X
    import handouts as H
    import olx_prompts as O

    # DISPATCH ON THE ITEM'S KIND, and build the spec the way production does.
    # This drove `score_slots` at every item and passed the bare action as the
    # spec. Both were wrong for the eight operant items: `oc`/`oc_cadence` have
    # their own scorer, `cadence` lives on the JOB and not on the action, and
    # score_slots walking an oc rubric raises on the first credit component the
    # slot sheet does not carry. It read as 285 "errors" and 330 cells scoring
    # 0.0 against a paper score of 4.0 -- an engine disagreement that was really
    # the wrong engine. Same rule as mirror_self_control: a control assembled
    # differently from production is not a control.
    jobs = {j["item"]: j for _h, b in A.BLOCKS.items() for j in b.values()}
    out = {"agree": 0, "differing": [], "errors": [], "items": [], "skipped": [],
           "supplemented": 0}
    for item in sorted(_jobs()):
        doc = _runs_doc(item, "paper")
        if not doc:
            continue
        h = _jobs()[item]["handout"]
        job = jobs.get(item) or {}
        scorer = A.SCORERS.get(job.get("kind"))
        if scorer is None:          # type_stated / data_presence: no mirror
            out["skipped"].append(item)
            continue
        try:
            action = A.load_action(f"bmod_handout{h}.olx", O.ACTION[item])
            spec = dict(job, slots=action["slots"], cover=action["cover"],
                        requires=action["requires"])
            rub = H.config(h)["rubric"].BY_ID[item]
        except Exception:
            continue
        out["items"].append(item)
        for run in doc.get("runs") or []:
            for c in run.get("results") or []:
                got = X.result_cell(c)
                if not got or got[2] is None:
                    continue
                _i, pid, paper_score, verd = got
                if not verd:
                    continue
                # NAMES DIFFER ACROSS THE SIDES AND ALIAS IS THE AUTHORITY.
                # Feeding paper's own keys straight into the web mirror's scorer
                # would land an aliased slot as an unrecognised key, which
                # `satisfied_map` reads as UNANSWERED -- so the slot silently
                # stops counting and the two sides can agree for the wrong
                # reason, or differ for no reason at all. `check_rubric_slots_
                # reach_the_sheet` learned this the expensive way: its first
                # version skipped web_name and reported twelve findings of which
                # ten were slots that do reach the sheet.
                #
                # Q4a and Q4c -- the only items with a paper artifact today --
                # happen to need no translation, so this changes nothing now and
                # is here so the first aliased item to be swept is not silently
                # mis-scored.
                webkeys = {s["key"] for s in spec["slots"]}
                # ROUTE COUNTS BY THE SLOT SPEC. The artifact flattens `count`
                # and `verdict` into ONE column, so a counting group's NUMBER
                # arrives here beside real verdicts. Wrapping it as `verdict`
                # leaves expand_counted reading no count, every member recovers
                # unmet, and the cell scores at its floor -- which reads as the
                # paper and web scorers disagreeing when they do not. FIFTH site
                # to need this after the 2026-09-13 fallback removal; it is not
                # named in that comment, which is why it was missed.
                count_keys = {cr["key"] for cr in (action.get("counts") or [])}
                def _wrap(nm, val):
                    return {("count" if nm in count_keys else "verdict"): val}
                checks, unresolved = {}, []
                for k, v in verd.items():
                    name = k if k in webkeys else _ENF().web_name(k, webkeys)
                    if name is None:
                        unresolved.append(k)
                        continue
                    checks[name] = _wrap(name, v)
                # SUPPLEMENT FROM `oc_analysis`, WHICH IS WHERE THE PAPER
                # SCORER PUTS THE REST OF ITS JUDGEMENT. `credit_checks` holds
                # only the checks that carried credit; the full analysis --
                # including `cadence_ok`, `avoidance_frame`, `states_a_
                # contingency`, `aimed_correctly` -- sits in `oc_analysis` and no
                # reader had ever looked at it. That, and nothing else, was the
                # "paper never records the cadence gate" coverage gap: it records
                # it, one field over. ALIAS already carried every name needed
                # (`cadence_ok` -> the three cadence gates, `avoidance_frame` ->
                # phrased_directly*), so this adds no mapping, only the read.
                #
                # THREE GUARDS, because oc_analysis is a wider vocabulary than
                # the sheet: a field already answered by `credit_checks` is never
                # overridden (what was CHARGED wins); a boolean is converted
                # through enforcement._PASS rather than by assuming True means
                # met, which is what makes `avoidance_frame` inverted correctly
                # -- its passing value IS False; and a value the slot does not
                # offer as an option is skipped rather than forced, so free text
                # like `behavior: "walking to class"` cannot land as a verdict.
                oc = c.get("oc_analysis") or {}
                if oc:
                    enf = _ENF()
                    offered = {s["key"]: (s.get("options") or [])
                               for s in spec["slots"]}
                    for k, v in oc.items():
                        name = k if k in webkeys else enf.web_name(k, webkeys)
                        if name is None or name in checks:
                            continue
                        if isinstance(v, bool):
                            want = enf._PASS.get(k)
                            vd = ("met" if (v == want if isinstance(want, bool)
                                            else v) else "absent")
                        elif isinstance(v, str) and v.strip():
                            vd = v.strip()
                        else:
                            continue
                        opts = offered.get(name) or []
                        if opts and vd not in opts:
                            continue
                        checks[name] = _wrap(name, vd)
                        out["supplemented"] += 1
                if unresolved:
                    # NEVER dropped in silence: an unmapped key is the exact thing
                    # this comparison would otherwise hide.
                    out["errors"].append(
                        f"{item}/p{pid}: paper records {sorted(unresolved)}, which "
                        f"neither names a sheet slot nor resolves through "
                        f"enforcement.ALIAS -- so the web mirror cannot be given "
                        f"the same verdicts and the two are not comparable here")
                    continue
                # AN UNANSWERED GATE IS NOT A DISAGREEMENT. A gating slot the
                # paper side never recorded reads as unsatisfied, which takes the
                # whole item to 0.0 -- so the mirror reports 0.0 against a paper
                # 4.0 and it looks like the two engines disagree about the answer
                # when they were never given the same question. That was all 330
                # of the differences left on DAY1/DAY2/WK1/WK2, and the cause is
                # one real coverage gap: the paper scorer does not judge cadence
                # at all (`cadence_is_daily`, `cadence_is_daily_counted`,
                # `cadence_is_weekly` -- every cell of all four items), while the
                # web gates the entire item on it. Reported, in the same breath
                # as the unmapped keys and for the same reason, never dropped.
                # DERIVE WHAT THE WEB DERIVES, then put the recorded verdicts
                # back. `consequence_not_a_setup` is not a question either engine
                # asks -- the web COMPUTES it from `restriction_authored`,
                # `trigger_expects` and `restricts`, all three of which paper
                # records in oc_analysis. Withholding it left 102 cells gated to
                # 0.0 on a judgement paper had in fact supplied the inputs for.
                #
                # THE COMPUTED VALUE WINS, on the computed slots only, which is
                # what `apply_computed` already does: it starts from `checks` and
                # overwrites nothing but the `derived`/`equals`/`expect`/`forbid`/
                # `maps` targets. Those are slots the web mirror NEVER takes from
                # a grader, so a recorded verdict for one is not a competing
                # judgement -- it is the other engine's own rendering of the same
                # rule, and scoring it as if it were independent double-counts.
                # Same rule as mirror_self_control, which is the point: a
                # mechanism that behaved one way for `olx` and another for
                # `paper` would be side-dependent, and only CONTENT may vary.
                #
                # This is what WK1/p6 was. `matches_chosen_type` is an `equals`
                # target carrying `lenient: ["unclear"]`, so the web resolves it
                # to `met` and scores 4; paper charges nothing and scores 4; the
                # two agree. Only paper's RECORD of the check said otherwise, and
                # letting that record win reported a 4-against-2 disagreement
                # between engines that do not disagree. score.py no longer writes
                # that record, and this no longer reads it.
                # FILL-ONLY: compute, then put the recorded verdicts back. A
                # slot a side actually ANSWERED is that side's judgement and is
                # what its score followed; a computed family exists to supply the
                # slots nobody answered. Letting the computation win instead
                # credits 1c/`legend` on the map where both the app and paper
                # scored the recorded `incomplete` -- 95 cells, an engine
                # disagreement invented by the reconstruction.
                try:
                    filled = A.apply_computed(action, dict(checks),
                                              A.fixture_for(item, pid))
                    filled.update(checks)
                    checks = filled
                except Exception:
                    pass
                ungated = sorted(s["key"] for s in spec["slots"]
                                 if s.get("gates") and s["key"] not in checks)
                if ungated:
                    out["errors"].append(
                        f"{item}/p{pid}: the web sheet GATES on {ungated}, which "
                        f"the paper scorer never records -- an unanswered gate "
                        f"scores the item 0.0, so this cell cannot be compared "
                        f"(it is a coverage gap, not a disagreement)")
                    continue
                try:
                    web_score, _f = scorer(spec, rub, checks)
                except Exception as exc:
                    out["errors"].append(f"{item}/p{pid}: {type(exc).__name__}: {exc}")
                    continue
                if abs(web_score - float(paper_score)) < 1e-9:
                    out["agree"] += 1
                else:
                    out["differing"].append((item, pid, float(paper_score), web_score))
    return out


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
    divergences -- QUALITY_CONTROL 2g records three of Q32's five being ONE
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
        g, _ = _APP.rebuild_declared_gold({p: dict(v) for p, v in g.items()})
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


def _goals_record_lines() -> set:
    """GOALS.md line numbers whose figures are a RECORD, not a live claim.

    A number inside a CLOSED entry is the measurement that closed the goal. It
    is supposed to say what was true then, and this project's own convention
    says so explicitly -- Q16's and Q22's closure notes keep sentences that were
    false by closing time and write the correction above them, deliberately,
    "as the record of what was true when written". Reporting those as staleness
    invites exactly the edit that would destroy the record: 11 of the 15 lines
    this check flagged on 2026-09-07 were in closed entries.

    A number in an OPEN entry written BEFORE the item was last recorded is a
    snapshot too -- it was true when typed and the ledger has moved since.

    `goals.py.slot_figures_predating_the_instrument` already draws both of these
    lines, with git blame author-time and the `- [x]`/`- [ ]` entry state, for
    SLOT figures. This is the same distinction one level up, so it uses the same
    two signals rather than inventing a third.
    """
    import re as _re
    import subprocess

    # STAMPS FIRST, blame only as the fallback -- see `goals.line_times`. Dating
    # the record must not depend on where the record is stored, and this reader's
    # own note below says what losing the dates costs: no exemption, which errs
    # toward reporting.
    try:
        import goals as _goals

        rows = _goals.line_times()
        if rows:
            entry = _re.compile(r"^- \[([ x])\] \*?\*?(Q|E)(\d+)")
            out, state = set(), " "
            for n, (when, text) in enumerate(rows, 1):
                m = entry.match(text)
                if m:
                    state = m.group(1)
                if state == "x":
                    out.add(n)
                    continue
                out.add(("when", n, when))
            return out
    except Exception:
        pass
    try:
        bl = subprocess.run(["git", "blame", "--line-porcelain", "GOALS.md"],
                            cwd=str(Path(__file__).parent), capture_output=True,
                            text=True, timeout=300)
        if bl.returncode != 0:
            return set()
    except Exception:
        # No blame available (no git, shallow checkout, timeout) means no
        # exemption, which errs toward reporting. A false staleness report costs
        # a read; a missed one costs a wrong number quoted as current.
        return set()

    rows, at = [], 0
    for row in bl.stdout.splitlines():
        if row.startswith("author-time "):
            at = int(row.split()[1])
        elif row.startswith("\t"):
            rows.append((at, row[1:]))
    entry = _re.compile(r"^- \[([ x])\] \*?\*?(Q|E)(\d+)")
    out, state = set(), " "
    for n, (when, text) in enumerate(rows, 1):
        m = entry.match(text)
        if m:
            state = m.group(1)
        if state == "x":
            out.add(n)
            continue
        out.add(("when", n, when))
    return out


def stale_sides(item: str) -> dict:
    """Sides whose recorded numbers for `item` measure a prompt that no longer
    ships. `{side: reason}`, empty when every side is current.

    Reuses `status()` rather than re-deriving the comparison -- QUALITY_CONTROL.md
    2a-3, and the fourth nonce classifier of 2026-09-07 is the reason that rule
    exists.
    """
    out = {}
    for side in SIDES:
        try:
            for it, why in status(side):
                # STALE ONLY. The first cut also triggered on ABSENT, and the
                # paper sides are unrecorded for nearly every item, so every
                # item in the corpus reported stale -- a banner that fires
                # always says nothing. An absent measurement is not a stale one:
                # it makes no claim to correct.
                if it == item and "STALE" in why:
                    out[side] = why
        except Exception:
            continue
    return out


_STALE_WARNED: set = set()


def warn_if_stale(item: str, where: str = "") -> str:
    """Print a loud banner when a reader is about to quote a stale entry.

    THE GAP THIS CLOSES. `sweep_readout`'s baseline guard refuses a before/after
    whose snapshot measures a different prompt from the tree. It does nothing
    about a reader QUOTING a stale entry, and on 2026-09-07 that let Q4b/p16 be
    reported as a defect at "1 of 12" when those runs measured the REVERTED
    report-slot wording -- the cell's answers still carried
    `b1_names_antecedent`, a slot that no longer exists. The numbers were real
    and described a prompt nobody could reach.
    Returns the banner text (also printed to stderr) or "" when current.
    """
    bad = stale_sides(item)
    if not bad:
        return ""
    # ONCE PER PROCESS PER ITEM. The first cut warned on every `cell_bands()`
    # call, and `cell_bands` is called by nearly everything: one script printed
    # 12 items x 4 lines TWICE and buried the per-cell readout it existed to
    # produce. A diagnostic that hides the result it annotates is worse than
    # none. Silenced by repetition, not by severity -- the first warning still
    # carries the full reason.
    if item in _STALE_WARNED:
        return ""
    _STALE_WARNED.add(item)
    # NAME WHICH KIND OF STALE. The first wording said "do NOT measure the
    # current prompt" for every case, and that is wrong for more than half of
    # them: of the twelve items stale on 2026-09-07 only five were PROMPT-stale,
    # while 1b, 2b, 3, D1, D2, T1 and T2 were SCORER-stale -- their prompts never
    # moved, the code their score depends on did. Telling someone to re-sweep a
    # prompt that never changed is the wrong instruction, and a banner that
    # misdescribes what it found is worse than a quieter one.
    kinds = set()
    for why in bad.values():
        kinds.add("PROMPT" if "STALE PROMPT" in why else
                  "SCORER" if "STALE SCORER" in why else
                  "CELLS" if "STALE CELLS" in why else "OTHER")
    what = "/".join(sorted(kinds))
    lines = [f"*** STALE ({what}): {item}'s recorded runs are not a measurement "
             f"of the current tree{(' -- ' + where) if where else ''} ***"]
    for side, why in sorted(bad.items()):
        lines.append(f"      {side}: {why}")
    if kinds == {"SCORER"}:
        lines.append("      The PROMPT is unchanged -- what moved is the scoring "
                     "code. The runs' verdicts still stand; the SCORES computed "
                     "from them may not, so re-score or re-sweep before citing a "
                     "figure. Do not re-word a prompt on this evidence.")
    elif "PROMPT" in kinds:
        lines.append("      Any per-cell figure below describes a prompt that no "
                     "longer ships. Re-sweep before citing it as a defect.")
    else:
        lines.append("      Read the per-side reason above before citing any "
                     "figure from this item.")
    txt = "\n".join(lines)
    print(txt, file=sys.stderr)
    return txt


def derived_verdicts(item: str, result: dict) -> dict:
    """The DERIVED verdicts a recorded app result does not write down.

    E55's cheap route to its own objective. The app honours the sheet's
    `expect="X:Y=VALUE"` clauses -- subgoal E53 measured that the charge lands --
    but records X as None, so a per-slot readout can see only half the sample on
    every derived slot. On NR that is `barrier_is_not_this_type`,
    `demonstrates_type` and `targets_goal_behavior`, 120 runs each.

    READ-SIDE, AND DELIBERATELY NOT A WRITE. The obvious fix is to fill
    `verdicts` in the stored artifact, and it is the wrong one: a reader treats
    `verdicts` as WHAT THE GRADER ANSWERED, and a value this function inferred is
    not that. Guessing a derivation's semantics slightly wrong would put false
    evidence into a file that later readers trust -- worse than the null it
    replaces. So this computes on demand, returns a SEPARATE dict, and every
    value carries the clause it came from.

    Returns {slot: (verdict, "expect=...")} for slots the result leaves null and
    the sheet derives from a pick it DOES record. Silent for anything whose
    inputs are also missing -- half a derivation is not a verdict.
    """
    import re

    import olx_prompts as O

    bag = {}
    for b in ("checks", "verdicts", "answers", "refers_to"):
        for k, v in (result.get(b) or {}).items():
            if v is not None:
                bag[k] = v
    try:
        _h, tag = None, None
        import probe as _P

        _h, tag = _P._element(item, "observed_type")
    except Exception:
        return {}
    if not tag:
        return {}
    out = {}
    for m in re.finditer(r'expect="([^"]*)"', tag):
        for clause in m.group(1).split("|"):
            # X:Y=VALUE -- X is met when the pick Y equals VALUE
            mm = re.match(r"\s*([A-Za-z0-9_]+)\s*:\s*([A-Za-z0-9_]+)\s*=\s*(.+)\s*$",
                          clause)
            if not mm:
                continue
            x, y, want = mm.group(1), mm.group(2), mm.group(3).strip()
            if bag.get(x) is not None or y not in bag:
                continue
            out[x] = ("met" if str(bag[y]) == want else "absent",
                      f'expect="{clause.strip()}"')
    return out


def orphans_if_closed(label: str) -> dict:
    """What closing `label` would drop on the floor -- asked BEFORE the closure.

    THE GAP THIS CLOSES, and it caught the same person twice in one day. The
    owner checks ask "does an OPEN subgoal name this cell". While the entry you
    are about to close is still open, it still names them, so both checks read
    ZERO and the closure looks clean -- then name the orphans a minute later.
    E45's closure dropped Q5/p9 that way; Q19's dropped six cells the same way,
    two of them WRONG. Running the checks again afterwards works, but only after
    the record is already inconsistent.

    Returns {"wrong": [...], "unstable": [...]} -- the findings that would appear
    if `label` were closed now, and an empty pair means the closure is clean.
    Re-home what it lists FIRST, then close, then run the checks again to confirm.
    """
    return {"wrong": wrong_cells_without_an_owner(excluding=label),
            "unstable": unstable_cells_without_an_owner(excluding=label)}


def declarations_for(item: str, pid: int) -> list:
    """Every declaration touching one cell, from every table, in one call.

    WHY THIS EXISTS, and it cost a sweep on 2026-09-07. Q19's fourth attempt
    spent four wordings, ~72 probe calls and a ~230-call sweep making the engine
    charge Q4b/p4 -- a cell `handouts.GOLD_DIVERGENCES` already declares as
    ANTECEDENT_REUSED_AS_BEHAVIOR, whose entry says the rule "rests on one cell",
    that "the scoring dictionary states no such rule; it was inferred from this
    cell", and that TWO implementations had already been measured and "both were
    worse than not having it" -- misfiring on p6 and p20, and on p1, p14 and p16.
    Today's attempts misfired on p13, p20, p16 and p8. Same shape, same cells,
    third and fourth time.
    Nothing announced it. The declaration was keyed by the exact cell the whole
    time, and the tables are spread across two modules and six names, so knowing
    to look means already knowing the answer. The user's rule: retesting a
    declared divergence is FINE -- what is not fine is not knowing it is one, so
    there is no point at which to give up.

    Returns a list of (table, code_or_key, text) for the cell. Read it BEFORE
    proposing a rule aimed at that cell, and print it in any probe that targets
    it (`sweep_gate` prints it per item).
    """
    import ast

    import handouts as H

    out = []
    cell = (item, pid)
    for d in getattr(H, "GOLD_DIVERGENCES", []):
        try:
            cells = ast.literal_eval(str(d.get("cells") or "[]"))
        except Exception:
            continue
        if cell in [tuple(c) for c in cells]:
            out.append(("GOLD_DIVERGENCES", d.get("code"), str(d.get("why") or "")))
    for name in ("CORRECTED_GOLD", "GOLD_CODE_KNOWN", "GOLD_SLOT_BOUNDS_KNOWN",
                 "GOLD_SLOT_DISAGREEMENTS_KNOWN", "SILENT_GOLD_DIVERGENCES"):
        tbl = globals().get(name) or {}
        for k, v in tbl.items():
            if tuple(k)[:2] == cell if isinstance(k, tuple) else False:
                out.append((name, k, str(v)))
    if (item, pid) in DECLARED_CEILING_CELLS:
        out.append(("DECLARED_CEILING_CELLS", (item, pid),
                    DECLARED_CEILING_CELLS[(item, pid)]))
    try:
        import handouts as _H

        for pid_ in (getattr(_H, "PER_ITEM_EXCLUDE", {}) or {}).get(item, {}) or {}:
            if pid_ == pid:
                out.append(("PER_ITEM_EXCLUDE", (item, pid), "cell DROPPED"))
    except Exception:
        pass
    return out


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

    # OVERRIDES.md is EXCLUDED, and the reason is a defect this check caused.
    # That file is machine-written by precommit_gate._record: it archives the gate
    # findings a commit waved through, VERBATIM. Those quoted findings contain
    # fractions ("says Q2 19/20, but the recorded ... is 18/20"), so this check
    # read its own archived output back as fresh prose claims -- and the gate then
    # recorded THOSE findings too. Each run therefore flagged everything the
    # previous run had written down, and the file DOUBLED per commit:
    # 7,697 -> 15,377 -> 30,739 -> 61,470 -> 122,909 lines, reaching 246,227 of
    # which only 606 were genuine. It is an archive of what was believed at a past
    # moment, which is exactly what _HISTORICAL exempts elsewhere; a stale figure
    # in it is the POINT of the record, not a staleness to report.
    files = paths or [str(p) for p in (
        [p for p in (_paths.SCORING).glob("*.md") if p.name != "OVERRIDES.md"]
        + [_paths.SCORING / "handouts.py"])]
    led = records()
    jobs = set(_jobs())
    out: list[str] = []
    _marks = _goals_record_lines()
    _records_lines = {x for x in _marks if isinstance(x, int)}
    _line_written = {x[1]: x[2] for x in _marks if not isinstance(x, int)}

    def _iso(ts: int) -> str:
        import datetime
        return datetime.datetime.fromtimestamp(ts).date().isoformat()

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
                if Path(path).name == "GOALS.md":
                    if lineno in _records_lines:
                        continue                      # a closed entry: a record
                    when = _line_written.get(lineno)
                    stamped = str(rec.get("recorded") or rec.get("stamp") or "")
                    if when and stamped[:10] and _iso(when) < stamped[:10]:
                        continue                      # typed before the recording
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
                # agreement_app.rebuild_declared_gold before anything scores against
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
            g, _ = APP.rebuild_declared_gold({p: dict(v) for p, v in g.items()})
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

    for path in (glob.glob(str(paths.OUT / "*" / f"{item}.runs.json"))
                 + glob.glob(str(paths.OUT / "*" / "runs" / f"{item}.runs.json"))):
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


# SCORER CHANGES VERIFIED NOT TO MOVE ANY RECORDED SCORE, keyed by the pair of
# fingerprints they sit between. `scorer_sha` answers "did the code this item's
# score depends on change?" and cannot answer "could that change alter this
# item's number?" -- so a real, behavioural change to a check that carries no
# points flags every item measured before it, and asks for thousands of calls to
# re-establish numbers that cannot have moved.
#
# AN ENTRY HERE IS NOT AN ASSERTION, IT IS A CLAIM WITH A VERIFIER.
# enforcement.check_scorer_neutrality_is_verified re-scores every recorded cell
# of the covered items through the CURRENT scorer and refuses the entry if any
# stored score moves -- from artifacts already on disk, at no call cost. And the
# key is the fingerprint PAIR, so the moment either side moves the entry lapses
# and the staleness comes back. That is the prompt_sha idiom applied one level in.
# Web-code transitions whose arithmetic provably cannot move a recorded score.
#
# THE SIBLING OF `SCORER_NEUTRAL`, AND KEYED IN A DIFFERENT SHA SPACE, which is
# exactly why it has to be its own table. `SCORER_NEUTRAL` is keyed on
# `scorer_sha` -- this repo's python. This is keyed on `web_code_sha("score")`
# -- lo-blocks' scoring path. `check_web_code_is_stamped_by_its_own_sha` used to
# advise "declare the pair in SCORER_NEUTRAL", and that advice could not be
# followed: no recorded item ever sits at a web-code sha, so the entry read as
# SPENT the moment it was written and produced a second finding instead of
# clearing the first. Measured 2026-09-14 by trying it.
#
# THE ENTRY IS A CLAIM, NOT A PERMISSION -- the same contract as its sibling.
# `check_web_code_neutrality_is_verified` re-scores every cell the pair covers
# on every audit and fails if one moves, so the approval cannot rot: if the claim
# was wrong it says which cell, and if the app's scoring changes again the
# fingerprints move and the pair stops matching on its own.
WEB_CODE_NEUTRAL: dict[tuple[str, str], str] = {
}


SCORER_NEUTRAL: dict[tuple[str, str], str] = {
    # THIRTEEN PAIRS DROPPED 2026-09-12, spent exactly as Q4b's was: the
    # verdict-default and `free` work moved every item's scorer_sha past the
    # transitions they covered, so no recorded side sits at their `was` sha any
    # more. A spent pair reads as coverage of a difference that is no longer
    # there, which is why the gate refuses one.
    # E25, commit 432fe64 (2026-09-01): "convert the keyword check to a derived
    # `contains` primitive". It changed agreement.apply_computed,
    # olx_prompts.contains_hit and olx_prompts._edit_within -- real scoring
    # machinery, not comments -- and flagged 34 STALE SCORER observations across
    # 17 items. E25's own finding is why it cannot matter: the keyword check is
    # 100% accurate against a MECHANICAL ground truth (240/240) and carries no
    # points, and only Q4a and Q4c have such a slot at all, which is why the
    # flagged set includes items like T1, T2, 1b and PR that have no keyword slot.
    # VERIFIED 2026-09-04 by re-scoring 2776 recorded cells across 14 items on
    # both sides: every one reproduces the score its artifact stored.
    # RE-POINTED 2026-09-14, and MERGED with the pair that stood below. Both
    # declared the same change through different item closures, and those
    # closures have since converged: `3`/olx, `2b`/python and `3`/python all now
    # sit at `29a76b0416e1`, so re-pointing both would have produced one key
    # twice -- a duplicate, where the second silently overwrites the first.
    #
    # THE OLD TARGETS WERE NEVER REACHED. The tree moved past `5ce4a8b5da28` and
    # `a2ef0d9c0e94` to a third sha, so every recorded item was skipped and both
    # pairs verified NOTHING while the audit read clean -- coverage theatre, now
    # caught by the untestable-pair branch of
    # `check_scorer_neutrality_is_verified`.
    #
    # RE-VERIFIED on the sha the tree actually reached: 360 recorded cells across
    # the three columns, 0 that fail to reproduce their stored score. That number
    # was 346 failures an hour earlier, and every one was `rescore_recorded`
    # routing a counted group's NUMBER as a verdict (T11) -- fixed, not excused.
    # RE-KEYED TWICE ON 2026-09-16, and the pair now spans THREE pieces of work.
    # It was ("6526989cd34f" -> "29a76b0416e1"), then "45b539e6082e", and lapsed
    # both times the way this table is designed to lapse: the `now` side moves
    # whenever the scorer closure changes, for any reason at all.
    #
    # THE SECOND LAPSE IS THE INSTRUCTIVE ONE. Nothing about scoring changed --
    # what moved it was making `_pointed()` and `_derived()` item-scoped, the
    # charge-once probe-gap work and three new audit checks. A re-key is cheap and
    # a wrong claim is not, so the rule this table runs on is that the pair is
    # re-pointed and RE-VERIFIED by `check_scorer_neutrality_is_verified`, which
    # re-scores every recorded cell the pair covers from artifacts on disk. It is
    # never carried forward on the strength of the last verification.
    # What moved it was maintenance, not scoring work -- the `parse_slots` colon
    # fix, the `paths.OUT` replacements and an undefined `_re` -- but
    # `scorer_sha` cannot know that, which is the whole reason the claim is
    # re-verified rather than asserted.
    #
    # THE TEXT NAMES BOTH TRANSITIONS ON PURPOSE. Carrying the old wording over
    # would have absorbed the later edits under a rationale written for E25's,
    # and a reader would have had no way to see that the pair had widened.
    # DROPPED 2026-09-17, SPENT. Every recorded column was re-recorded that day
    # after the scorer moved, so no item sits at `6526989cd34f` any longer and
    # the pair covers nothing. A pair whose `was` side is unoccupied verifies
    # nothing while reading like coverage, which is what this table exists to
    # refuse -- `check_scorer_neutrality_is_verified` said so, and the commit
    # gate stopped on it.
    #
    # WHAT IT CLAIMED IS NOT LOST; it is now stronger. All 52 recorded columns
    # were re-derived from artifacts on disk and 0 scores moved, so the
    # transition this pair asserted to be score-neutral is recorded as a
    # measurement rather than as a declaration.
    # The remaining pairs are the SAME change seen through other items' closures:
    # scorer_sha is item-scoped, so one commit produces a different pair for every
    # distinct closure. All seven items below are in the 2776-cell re-score.
    # Q4b's pair ("22f8ceb090da" -> "992381ed67cf") was DROPPED 2026-09-05: Q18's
    # structural edit (b2_names_act) re-staled Q4b, moving its scorer_sha past the
    # transition this pair covered, so no recorded item sits at the `was` sha any
    # more. The gate refuses a spent pair because it reads as coverage of a
    # difference that is no longer there. E25 itself is unaffected -- Q4b is in the
    # 2776-cell re-score above, and this line was only its item-scoped view of it.
    # SIX PAIRS DROPPED 2026-09-12, all of them E25's change seen through a
    # different item's closure. No recorded item sits at any of their `was` shas
    # any more -- every column has been re-recorded or re-swept past that
    # transition -- so each one claimed to excuse a difference that is no longer
    # there. That is what the audit means by a SPENT pair, and it is not
    # harmless: a spent entry reads as coverage, so the next reader checking
    # whether E25 is accounted for finds six lines saying yes about columns none
    # of them describes. Dropped rather than rewritten, because the one pair that
    # still has a column at its `was` sha is the line above, and E25 itself is
    # recorded there with the 2776-cell re-score that verified it.
    #
    # The shas are kept in this note so the history stays findable:
    #   2f11176f1cd0 -> 7d20355c702b   the operant items
    #   4f0592d0beaf -> 4454461f7b6a   the items with no slot sheet (1b, T1, T2)
    #   4334438d6d55 -> bbb4c72ce2a8   1c's closure
    #   7b8f8715488a -> b3b70c8239bc   Q6's closure
    #   8f2c4a9c148c -> 9f791c8ccf03   Q3's and Q5's closure
    #   fa4d1b3a2c1d -> b4860821510d   D1's and D2's closure
    # THE VERDICT-DEFAULT ALIGNMENT, 2026-09-12. `agreement.load_action` fell back
    # to the literal "met,absent,unclear" for a slot naming no verdicts of its
    # own, while the app's `DEFAULT_VERDICTS` is ['met', 'absent']. So the two
    # engines offered the grader different vocabularies on 57 slots, 13 of them
    # scored -- including `matches_chosen_type`, 2 of 4 points on D1/D2/WK1/WK2.
    # `default_verdicts()` now READS the app's list out of slotSheet.ts, so the
    # two cannot drift again, and joining load_action's closure moved the
    # fingerprint for all 26 items on both web-side columns.
    #
    # IT CANNOT REACH A RECORDED NUMBER, measured twice and both ways round:
    #   * before the change, over 2,902 recorded python runs, a grader took the
    #     extra `unclear` option ONCE (NR.you_arrange_it) -- 0.03%;
    #   * after it, re-scoring every recorded cell through the new code
    #     reproduces the stored score EXACTLY, olx 2304/2304 and python
    #     2908/2908.
    # So no column is re-swept for this. What changes is what a FUTURE sweep
    # asks, which is the point of the change.
}


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
            # A SCORER CHANGE DECLARED NEUTRAL, and verified by re-scoring, is
            # not staleness -- it is a fingerprint that moved for a reason that
            # cannot reach the number. See SCORER_NEUTRAL.
            if "STALE SCORER" in state:
                rec = ((records(side).get(item) or {}).get("scorer_sha"))
                if (rec, scorer_sha(item, side)) in SCORER_NEUTRAL:
                    continue
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
        # STEP 5b. The same question one level down. `prose_claims` compares an
        # ITEM figure against the ledger; this compares a SLOT figure against the
        # INSTRUMENT that produced it, which nothing did until 2026-09-04 -- the
        # knowledge that a figure came from a blind profile lived as narrative in
        # one subgoal entry, and would have died when that entry closed. It is
        # STALENESS, not contradiction, which is why it reports here beside step 4
        # rather than blocking a commit through the audit.
        "5b. record — slot figures older than the profile that computed them":
            _stale_slot_claims(),
        "6. leakage — rule blocks echoing the cohort, with no verdict filed":
            _leakage_pending(),
        "7. probes — items whose recorded prompt has unprobed moved cells":
            _unprobed_movers(),
        # STEP 8 IS THE SESSION'S OWN BACKLOG, not the corpus's. The seven above
        # ask what the CORPUS needs; these ask what THIS session started and set
        # aside, which is the thing a context boundary loses and nobody else can
        # see. Standing policy, stated by the user 2026-09-03: at a standstill --
        # a sweep running, a question asked and unanswered -- clear the set-aside
        # work first, then name the next subgoal. Enforced here rather than
        # remembered, because "remember to check" is exactly the instruction that
        # does not survive a compaction.
        "8. set aside — finished work not yet recorded, and gates not yet re-run":
            unrecorded_artifacts() + selftest_owed(),
        # STEP 9 IS NOT OUTSTANDING WORK, IT IS THE ORDER TO DO IT IN. Standing
        # instruction 2026-09-04: knowing the rank order, and redoing it when
        # something changes it, should happen automatically rather than being a
        # conversation. So it is DERIVED here every time preflight runs -- there is
        # no stored ranking to go stale -- and it prints the facts it ordered on
        # rather than a score, because a score cannot be argued with.
        # STEP 5c. Subgoal E41: the ledger books a cell by its per-cell median, so
        # a cell one run from crossing that line is recorded as settled. These are
        # the cells where "the number moved" is the likeliest explanation of a
        # change, and they are not visible anywhere else.
        "5c. record — cells one run from changing their own verdict":
            cells_on_the_median_line(),
        # STEP 5d. Subgoal E42's residual, added 2026-09-05. 5c asks which cells
        # are ONE RUN from moving; this asks which ones ALREADY DID, and in the
        # wrong direction. The two are the same worry at different times: 5c is
        # a warning before a sweep, this is the bill after one.
        # E42 DEFERRED THIS DELIBERATELY -- "there is no case for a third place
        # to read it from until something has been recorded on both sides with
        # bands present" -- and that condition is now met on ten items, so the
        # deferral has expired rather than been overruled.
        # IT BELONGS HERE RATHER THAN ONLY BESIDE A RECORDING because a session
        # that lands several sweeps sees each `record()` print its own moves and
        # then loses them to scrollback. On 2026-09-05 that is exactly what
        # happened: DAY1/p9 and p15 went out of `perfect` and the item total
        # moved by one, which reads as noise until the bands are read together.
        "5d. record — cells the last recording moved to a WORSE band":
            band_regressions(),
        # STEP 5e. Subgoal E45. 5c warns which cells are one run from moving and
        # 5d bills the ones that already did; this asks a different question of
        # the same class -- does anyone OWN the unstable ones at all. A cell can
        # sit at 9 of 12 indefinitely without ever being wrong by the median, so
        # neither 5c nor 5d nor wrong_cells_without_an_owner will ever name it.
        "5e. record — unstable cells no open subgoal names":
            unstable_cells_without_an_owner(),
        # STEP 5f. Subgoal E46. The 5-series asks whether a recorded number means
        # what it says; this asks whether a MAPPED slot was recorded outside its
        # own map. It belongs here rather than only in the equivalence audit
        # because that audit is run deliberately and this appears after a
        # RECORDING: a Q4b divergence sat in an artifact from 2026-08-29 and was
        # found on 2026-09-06, by writing a check for an unrelated reason. Eight
        # days, several sweeps, nothing routine looking.
        "5f. record — mapped slots recorded outside their map":
            _mapped_slot_disagreements(),
        # STEP 5g. Subgoal E53, and it is 5f's question one level up. 5f asks
        # whether a mapped slot was recorded outside its map; this asks whether a
        # SCORED slot was recorded by both engines at all. It has to read
        # artifacts, so it cannot live in sweep_gate.py, and it appears after a
        # RECORDING for 5f's own reason: `matches_chosen_type` has been null in
        # every app result on six items for as long as there have been artifacts,
        # and nothing routine looked.
        "5g. record — scored slots only one engine ever answers":
            _one_sided_scored_slots(),
        "9. priority — open goals in derived order (facts, not a verdict)":
            _ranked_goals(),
    }


def _one_sided_scored_slots() -> list[str]:
    """enforcement.check_scored_slots_are_answered_by_both_engines; never blocks."""
    try:
        import enforcement as E
        return E.check_scored_slots_are_answered_by_both_engines()
    except Exception as e:
        return [f"(check unavailable: {e})"]


def _mapped_slot_disagreements() -> list[str]:
    """enforcement.check_mapped_slots_agree_with_their_map; never blocks."""
    try:
        import enforcement as E
        return E.check_mapped_slots_agree_with_their_map()
    except Exception as e:                       # never block a preflight
        return [f"(could not read: {e})"]


def _ranked_goals() -> list[str]:
    """goals.rank(), formatted; never blocks preflight on its own."""
    try:
        import goals
        return [f"{i:>2}. {lab:5} {why}"
                for i, (lab, _f, why) in enumerate(goals.rank(), 1)]
    except Exception as e:
        return [f"ranking unavailable: {type(e).__name__}: {e}"]


def unrecorded_artifacts() -> list[str]:
    """Sweeps that COMPLETED and were never recorded into the ledger.

    A finished artifact nobody recorded is the most expensive kind of set-aside
    work: the calls are already spent, so the only thing between it and a number
    is one command. It goes unnoticed because nothing about a finished sweep
    announces itself -- the process exits, the log ends, and the next question
    moves on.
    """
    import json as _json
    import paths as _paths

    out: list[str] = []
    # NEWER THAN THE LEDGER, which is what "not yet recorded" actually means.
    # The first version asked only whether a directory was cited as some entry's
    # source, and reported FIVE HUNDRED AND SIXTEEN artifacts -- because out/
    # holds every sweep this project has ever run, and most were measured,
    # read and deliberately not recorded. A backlog list that reports the whole
    # history trains the reader to skip it, which is worse than not having one.
    # Recording rewrites MEASURED.json, so an artifact written after it is a
    # sweep that finished and has not been recorded SINCE. A sweep that finished
    # before some later recording drops off the list; that false negative is
    # worth the signal.
    try:
        # ACROSS SIDES, from the raw ledger. This read `records()`, which
        # returns ONE side's record per item already flattened, and then indexed
        # each one by side AGAIN -- so every lookup missed and `seen_out` was the
        # empty set. The "already the source" filter below therefore never fired
        # once, and the list was held down by the mtime threshold alone. Silent
        # while the recorded artifacts happened to predate the ledger; the moment
        # a migration rewrote them it reported 13 recorded artifacts as
        # un-recorded sweeps and told the reader to re-record what was already in.
        seen_out = {(rec.get(side) or {}).get("out")
                    for rec in (load().get("items") or {}).values() if rec
                    for side in SIDES if rec.get(side)}
        ledger_at = LEDGER.stat().st_mtime
    except Exception:
        return []
    for path in sorted(set(_paths.OUT.glob("*/*.runs.json"))
                       | set(_paths.OUT.glob("*/runs/*.runs.json"))):
        item = path.name[: -len(".runs.json")]
        if item not in _jobs():
            continue
        d = path.parent.name
        if d in seen_out:
            continue                       # this directory is already the source
        try:
            if path.stat().st_mtime <= ledger_at:
                continue                   # predates the last recording
        except OSError:
            continue
        try:
            n = len(_json.loads(path.read_text()).get("runs") or [])
        except Exception:
            continue
        out.append(
            f"{item}: {n} run(s) finished in {d}/ and never recorded — "
            f"`python3 measured.py --record {item} {path} [olx]`. The calls are "
            f"already spent; the number is one command away")
    return out


def selftest_owed() -> list[str]:
    """The enforcement self-test, when the checks have moved since it last passed.

    `equivalence.py --selftest` REFUSES while a measurement is in flight, because
    it injects breakages into source the sweep reads. That refusal is correct and
    it is also how the self-test gets forgotten: it is deferred at the moment the
    checks changed, and the sweep that deferred it ends hours later in a different
    conversation. So the debt is recorded in state instead of in anyone's memory.
    """
    import paths as _paths

    stamp = _paths.SCORING / ".selftest-passed"
    watched = [_paths.SCORING / "enforcement.py", _paths.SCORING / "equivalence.py"]
    if not stamp.exists():
        return ["enforcement self-test has never recorded a pass — run "
                "`python3 equivalence.py --enforcement --selftest`"]
    at = stamp.stat().st_mtime
    moved = [w.name for w in watched if w.exists() and w.stat().st_mtime > at]
    if not moved:
        return []
    return [f"enforcement self-test is OWED: {', '.join(moved)} changed since it "
            f"last passed. Run `python3 equivalence.py --enforcement --selftest` "
            f"(it refuses while a sweep is in flight — that is the reason it gets "
            f"forgotten, not a reason to skip it)"]


def _stale_slot_claims() -> list[str]:
    """Delegates to goals.stale_slot_claims; never blocks preflight on its own."""
    try:
        import goals
        return goals.stale_slot_claims()
    except Exception as e:
        return [f"slot-claim dating unavailable: {type(e).__name__}: {e}"]


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
    accepting "a car", [[corpus Q3/p14 action 90:114 sha=d4443bb53f34]], "{{corpus:Q3/p18:action:71:97:sha=4b1ed59f418c}}
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
        import paths as _paths2
        for cand in _paths2.OUT.glob(f"{art}*/{item}.runs.json"):
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
    if a[:1] == ["--moves"] and len(a) in (1, 2, 3):
        # `--moves [ITEM] [SIDE]`. Subgoal E42: what each cell's band did across
        # the last recording. Reads the band stored BY that recording, so it can
        # answer after the fact -- which `cell_bands` alone cannot.
        lines = band_moves(a[1] if len(a) > 1 else None,
                           a[2] if len(a) > 2 else DEFAULT_SIDE)
        for ln in lines:
            print(f"  {ln}")
        if not lines:
            print("  no cell changed band since it was recorded")
        return 0
    if a[:1] == ["--accept-design-change"] and len(a) == 4:
        # `--accept-design-change ITEM SLOT FIELD`. ONE field, deliberately: a
        # bulk regenerate would make DESIGNED_TEXT_SHA.json agree with anything
        # and enforce nothing, which is the whole reason it exists.
        raise SystemExit(accept_design_change(a[1], a[2], a[3]))
    if a[:1] == ["--restore-previous"] and len(a) in (2, 3):
        # `--restore-previous ITEM [SIDE]`. For a REVERT that returned the prompt
        # to a sha we have already measured.
        raise SystemExit(restore_previous(a[1], a[2] if len(a) == 3 else DEFAULT_SIDE))
    if a[:1] == ["--append"] and len(a) in (3, 4):
        # `--append ITEM ARTIFACT [SIDE]`: pool with what is already recorded
        # rather than replacing it. Refuses a stale column -- see append_runs.
        append_runs(a[1], a[2], a[3] if len(a) == 4 else DEFAULT_SIDE)
        return 0
    if a[:1] == ["--record"] and len(a) in (3, 4):
        # `--record ITEM ARTIFACT [SIDE]`. SIDE defaults to DEFAULT_SIDE, which
        # is `python` -- agreement.py, the OLX prompt scored in Python. A
        # two-sided sweep therefore records its APP half with an explicit `olx`.
        #
        # THIS COMMENT SAID THE OPPOSITE until 2026-09-03, and named a side that
        # no longer exists: "SIDE defaults to the web-prompt path, so a two-sided
        # sweep records the CLI half with an explicit `cli`". Both halves were
        # wrong after the web/cli -> olx/python rename -- the default is the
        # python half, not the app half, and `cli` is not in SIDES, so following
        # the instruction literally fails. Harmless only because the SIDE
        # CONTRACT refuses the mismatch by reading who wrote the artifact; it
        # caught exactly this, on this line, the first time NR's app half was
        # recorded. A stale comment beside a working guard is still a trap for
        # whoever reads the comment and not the guard.
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
        # SCOPED TO THE ITEM JUST RECORDED, and the rest reported as a count.
        # `declaration_conflicts()` is corpus-wide and takes no item, so every
        # `--record` used to print every conflict in the project directly under
        # the item's own output. Recording WK2, 1b, T1 and T2 each announced
        # "GOLD_CEILINGS ('1','Q3') says this item cannot be perfect" -- about
        # Q3, under four items that are not Q3. A corpus-wide report printed
        # under a per-item action reads as being about that item, which is the
        # same scoping fault `leakage.gate` carries and the reason the staleness
        # banner was made once-per-item.
        _conf = declaration_conflicts()
        _mine = [c for c in _conf if f"'{a[1]}'" in c or f" {a[1]} " in c]
        for c in _mine:
            print(f"  DECLARATION EXPIRED? {c}")
        _other = len(_conf) - len(_mine)
        if _other:
            print(f"  ({_other} declaration conflict(s) elsewhere in the corpus, "
                  f"not about {a[1]} -- `measured.declaration_conflicts()` lists "
                  f"them)")
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
# Entries and their reasoning: `coursedata.gold_notes("GOLD_SLOT_CHARGES", key)` (23 lines).
GOLD_SLOT_CHARGES = _gold_declaration("GOLD_SLOT_CHARGES")


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
# again -- Q6_MATCHING_CEILING.md -- seen from the grader's side for the
# first time.
# Deductions that CANNOT map to a slot set, with the reason. Declared rather than
# quietly skipped: an unread charge was exactly the old behaviour.
# Cells whose AMBIGUOUS gold charge still disagrees with us on EVERY reading.
# Separate from GOLD_SLOT_DISAGREEMENTS_KNOWN because the finding is weaker in
# kind -- a count or a subset, not a named slot -- and mixing them would let a
# bounded finding be quoted as an exact one.
# E35. Criteria-derived cells where our deduction CODE differs from gold's.
# Entries and their reasoning: `coursedata.gold_notes("GOLD_CODE_KNOWN", key)` (40 lines).
GOLD_CODE_KNOWN = _gold_declaration("GOLD_CODE_KNOWN")


# Cells whose AMBIGUOUS gold charge still disagrees with us on EVERY reading.
# Separate from GOLD_CODE_KNOWN because the finding is weaker in kind -- a count
# or a subset, not a named slot -- and mixing them would let a bounded finding be
# quoted as an exact one.
#
# THIS TABLE'S DECLARATION LINE WAS DELETED BY ACCIDENT on 2026-09-06 and is
# restored here. Rewriting GOLD_CODE_KNOWN's ("NR", 11) entry used a slice that
# ran to the NEXT dict key, which swallowed this table's closing brace, comment
# and `GOLD_SLOT_BOUNDS_KNOWN: ... = {` line -- so its two entries were absorbed
# into GOLD_CODE_KNOWN and the name went undefined. The file still PARSED and the
# only symptom was GOLD_CODE_KNOWN loading 7 keys instead of 5, which was noticed
# and not explained at the time; `wrong_cells_without_an_owner` then raised
# NameError. A slice bounded by "the next key" is not bounded by the end of the
# value it means to replace.
# Entries and their reasoning: `coursedata.gold_notes("GOLD_SLOT_BOUNDS_KNOWN", key)` (1 lines).
GOLD_SLOT_BOUNDS_KNOWN = _gold_declaration("GOLD_SLOT_BOUNDS_KNOWN")
# DELETED BY ACCIDENT with this table's declaration line on 2026-09-06 and
# restored here. The same bad slice took the closing brace, the comment, the
# `GOLD_SLOT_BOUNDS_KNOWN` line AND this constant; restoring the table alone left
# `preflight` raising NameError on every run, which is how it was found. Two is
# the table's size and the ratchet may only fall.
GOLD_SLOT_BOUNDS_BUDGET = 2


# Entries and their reasoning: `coursedata.gold_notes("GOLD_SLOT_UNMAPPABLE", key)` (5 lines).
GOLD_SLOT_UNMAPPABLE = _gold_declaration("GOLD_SLOT_UNMAPPABLE")


# Entries and their reasoning: `coursedata.gold_notes("GOLD_SLOT_DISAGREEMENTS_KNOWN", key)` (117 lines).
GOLD_SLOT_DISAGREEMENTS_KNOWN = _gold_declaration("GOLD_SLOT_DISAGREEMENTS_KNOWN")
GOLD_SLOT_DISAGREEMENTS_BUDGET = 8


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
GOLD_CODE_CHARGES = _gold_declaration("GOLD_CODE_CHARGES")


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


def gold_box_status(item: str) -> dict:
    """Per-cell, per-slot: does gold CREDIT this box, CHARGE it, or say nothing?

    A PROBE'S PRE-REGISTRATION MUST BE DERIVED FROM THIS AND NOT TYPED OUT.
    Written 2026-09-07 after a Q4c probe hand-typed its own falsifier set and got
    two things wrong in one script:

      * it treated Q4c/p4's first box as gold-CREDITED, so the rule "over-firing"
        there read as a cost. Gold charges that box in its own words -- "specify
        what spending too much time awake means as a consequence" -- and we
        already answer `wrong_kind` on it 9 of 12 runs. Refusing it is AGREEMENT.
      * it took the dropped-cell list from `handouts.suspect(1)`, which is the
        HANDOUT-WIDE reader ("participants whose input cannot be trusted, whatever
        the item") and returns []. Q4c/p16 is excluded PER ITEM, and only
        `exclusions(item)` sees it. Across all of handout 1 Q4c is the ONLY item
        where the two answers differ, so the mistake is invisible everywhere else.

    Returns {pid: {"status", "gold", "max", "charged", "credited"}} where
    `charged` and `credited` are slot-name sets over the item's credit list.

        excluded             `exclusions(item)` drops it. Not evidence in EITHER
                             direction -- see the suspect-cells rule in
                             QUALITY_CONTROL.md.
        no_gold              gold has no number for the cell.
        full_marks           gold charges nothing, so EVERY slot is credited.
                             THE ONLY CELLS A FALSIFIER MAY BE DRAWN FROM.
        charged_slots_known  gold charges and `gold_charged_slots` names which;
                             the rest of the slots are credited.
        charged_box_unknown  gold charges and WHICH SLOT IS NOT READABLE. Then
                             `credited` is EMPTY ON PURPOSE: no slot here may be
                             called gold-credited, because we do not know. An
                             empty set is "we do not know", never "gold charged
                             nothing" -- the same distinction `gold_charged_slots`
                             keeps by returning None.
    """
    import handouts as H

    h = _jobs()[item]["handout"]
    rub = H.config(h)["rubric"].BY_ID[item]
    slots = {c["what"] for c in rub["credit"]}
    top = float(rub["max"])
    dropped = set(exclusions(item))

    out: dict[int, dict] = {}
    for pid in range(1, 21):
        rec = {"status": "", "gold": None, "max": top,
               "charged": set(), "credited": set()}
        if pid in dropped:
            rec["status"] = "excluded"
            out[pid] = rec
            continue
        g = gold_cell(item, pid) or {}
        rec["gold"] = g.get("score")
        if rec["gold"] is None:
            rec["status"] = "no_gold"
        elif abs(rec["gold"] - top) < 1e-9:
            rec["status"] = "full_marks"
            rec["credited"] = set(slots)
        else:
            named = gold_charged_slots(item, pid)
            if named:
                rec["status"] = "charged_slots_known"
                rec["charged"] = set(named)
                rec["credited"] = slots - set(named)
            else:
                rec["status"] = "charged_box_unknown"
        out[pid] = rec
    return out


def probe_falsifiers(item: str, slot: str | None = None):
    """Falsifiers a probe may legitimately claim, and gold's credit is CERTAIN.

    Only cells where gold credits the box outright: full marks, or a charge whose
    slots are named so the REST are known credited. A rule firing on one of these
    is a real cost. Everything else is in `probe_unusable`, and a probe counting
    those as falsifiers reports costs it cannot substantiate -- Q4c/p4 exactly.

    Without `slot`: {pid: credited slot names}. PASS THE SLOT when the probe is
    about one slot, and read the pid list from that: the bare mapping still holds
    the TARGET cell whenever some OTHER slot of it is credited, and a caller
    reading its keys as "the falsifier cells" gets the target back in the set.
    Q4c/p9 is the case in point -- gold charges both consequence boxes, its two
    remaining slots are credited, so p9 is a key here and is NOT a falsifier for
    a consequence rule.
    """
    st = gold_box_status(item)
    if slot is None:
        return {pid: r["credited"] for pid, r in st.items() if r["credited"]}
    return sorted(pid for pid, r in st.items() if slot in r["credited"])


def probe_unusable(item: str) -> dict:
    """{pid: why} cells a probe must NOT read as evidence of a cost.

    Kept as a separate call so a probe has to look at it. Silence about these is
    how a readout claims coverage it does not have.
    """
    why = {"excluded": "dropped by exclusions(item) -- not evidence either way",
           "no_gold": "gold has no number for this cell",
           "charged_box_unknown": "gold charges this cell but which slot is not "
                                  "readable, so no box here counts as credited"}
    return {pid: why[r["status"]] for pid, r in gold_box_status(item).items()
            if r["status"] in why}


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
        g, _ = _APP.rebuild_declared_gold({p_: dict(v) for p_, v in g.items()})
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


def band_moves(item: str | None = None, side: str = DEFAULT_SIDE) -> list[str]:
    """What each cell's band did across the last recording, per recorded item.

    SUBGOAL E42's payoff, and the reason the band is stored at all.
    QUALITY_CONTROL.md 2d tells the reader to ask whether a change "gained a
    STABLE cell or pushed a coin flip across the median line". That needs the
    band BEFORE, which `cell_bands` cannot give once the sweep is recorded, so it
    is read back off the entry and compared with the band now.

    SILENT ABOUT CELLS THAT DID NOT MOVE, and explicit about items recorded
    before this existed: an entry with no `bands_before` says NOT KNOWN, which is
    a different fact from "did not move" and must not be reported as one -- the
    same distinction `rescore_recorded` needed its own third channel for.
    """
    now = cell_bands()
    out: list[str] = []
    for it, s in sorted(records(side).items()):
        if item is not None and it != item:
            continue
        before = s.get("bands_before")
        if before is None:
            out.append(f"{it} [{side}]: recorded before bands were kept "
                       f"— no prior band to compare")
            continue
        for pid, was in sorted(before.items(), key=lambda kv: int(kv[0])):
            cur = now.get(f"{it}/p{pid}")
            if cur is None or cur[2] == was:
                continue
            out.append(f"{it}/p{pid}: {was} -> {cur[2]}  ({cur[0]} of {cur[1]})")
    return out


# Worst to best. `band_regressions` reports a cell that moved DOWN this order and
# says nothing about one that moved up, because a gain needs no one's attention
# and a loss does. Kept beside `cell_bands`, whose docstring defines the bands, so
# the ordering cannot drift from the definitions it orders.
_BAND_ORDER = ("always_wrong", "wrong_by_median", "on_the_line",
               "unstable_counted_right", "perfect")


def band_regressions(side: str | None = None) -> list[str]:
    """Cells the last recording moved to a WORSE band, across every recorded item.

    SUBGOAL E42's residual, built 2026-09-05. `band_moves` reports every move on
    one item and one side and is what a reader calls when they already know which
    recording they are asking about. This asks the question a session has when it
    does NOT know: did anything I landed make a cell worse, anywhere?

    IT EXISTS BECAUSE IT WOULD HAVE PAID FOR ITSELF THE DAY IT WAS WRITTEN. The
    cadence edit of 2026-09-05 took DAY1/p9 and DAY1/p15 from `perfect` to
    `on_the_line` and `wrong_by_median`, against pre-registrations naming both as
    controls. The item TOTAL moved by one, which reads as noise; the band moves
    said plainly that two perfect cells had gone. Nothing surfaced that until the
    bands were read by hand.

    A LOSS OUT OF `perfect` IS CALLED OUT SEPARATELY, because it is the one move
    with no innocent reading: an unstable cell drifting a band is often the
    number moving, but a cell that was right in every run and now is not was made
    worse by something.

    Silent about items with no stored band -- that is `band_moves`'s NOT KNOWN and
    is not a regression.
    """
    now = cell_bands()
    out: list[str] = []
    for sd in ((side,) if side else SIDES):
        try:
            recorded = records(sd)
        except Exception:
            continue
        for it, s in sorted(recorded.items()):
            before = (s or {}).get("bands_before")
            if not before:
                continue
            for pid, was in sorted(before.items(), key=lambda kv: int(kv[0])):
                cur = now.get(f"{it}/p{pid}")
                if cur is None or cur[2] == was:
                    continue
                try:
                    if _BAND_ORDER.index(cur[2]) >= _BAND_ORDER.index(was):
                        continue
                except ValueError:
                    continue      # an unknown band name is another check's business
                lost = " — was RIGHT IN EVERY RUN" if was == "perfect" else ""
                out.append(f"{it}/p{pid} [{sd}]: {was} -> {cur[2]} "
                           f"({cur[0]} of {cur[1]}){lost}")
    return out


def cell_bands(state: dict | None = None) -> dict:
    """Every recorded cell's band, pooled over the OLX-prompt sides.

    {cell: (right, runs, band)} where band is one of:

      always_wrong             right in NO run
      wrong_by_median          counted wrong, but reaches gold sometimes
      on_the_line              ONE RUN either side of the median -- the verdict
                               the ledger records would change if a single run
                               flipped
      unstable_counted_right   counted right, and not always right
      perfect                  right in every run

    SUBGOAL E41 EXISTS BECAUSE THE MIDDLE THREE WERE INVISIBLE. The ledger's item
    figure counts a cell by its per-cell MEDIAN, so a cell right in 7 runs of 12
    is booked as a success and nothing distinguishes it from one right in 12.
    Measured when this was written: of 491 cells, 404 are perfect, 63 are counted
    right while flipping, and only 24 are counted wrong -- so the corpus holds
    more than twice as many unreliable-but-counted-right cells as wrong ones, and
    four of the shakiest had no owning subgoal at all because
    `wrong_cells_without_an_owner` defines "wrong" by the median too.

    `state` is injectable so the band boundaries can be tested on synthetic counts
    rather than on whatever the corpus happens to contain.
    """
    if state is None:
        state = {}
        for side in POOLED_OLX_PROMPT:
            try:
                led = records(side)
            except Exception:
                continue
            for item, s in led.items():
                runs = s.get("runs") or 0
                for pid, n in (s.get("cells") or {}).items():
                    a = state.setdefault(f"{item}/p{pid}", (0, 0))
                    state[f"{item}/p{pid}"] = (a[0] + n, a[1] + runs)
    out = {}
    # WARN ABOUT WHAT THIS IS ABOUT TO REPORT. A band is only as current as the
    # entry it was computed from, and nothing used to say so -- see
    # `warn_if_stale`. Printed to stderr, once per stale item, so no caller that
    # parses stdout is affected.
    _seen_stale = set()
    for cell in state:
        it = str(cell).split("/")[0]
        if it not in _seen_stale:
            _seen_stale.add(it)
            warn_if_stale(it, where="cell_bands")

    for cell, (right, runs) in state.items():
        if not runs:
            continue
        half = runs / 2
        if right == runs:
            band = "perfect"
        elif right == 0:
            band = "always_wrong"
        # ON THE LINE: counted right by one run, or counted wrong by one. Those
        # are the cells whose RECORDED verdict a single run would change, which is
        # a different and more useful question than "is it unstable".
        elif right in (int(half) + 1, int(half)) and runs % 2 == 0:
            band = "on_the_line"
        elif right > half:
            band = "unstable_counted_right"
        else:
            band = "wrong_by_median"
        out[cell] = (right, runs, band)
    return out


def cells_on_the_median_line() -> list[str]:
    """The cells whose recorded verdict one run would change. Preflight step 5c."""
    rows = [(c, r, n) for c, (r, n, b) in cell_bands().items()
            if b == "on_the_line"]
    if not rows:
        return []
    out = [f"{len(rows)} cell(s) sit ONE RUN from changing the verdict the ledger "
           f"records for them — a rule change that moves one is not evidence:"]
    for cell, r, n in sorted(rows):
        side = "counted RIGHT" if r > n / 2 else "counted WRONG"
        out.append(f"    {cell:12} {r}/{n}  {side}")
    return out


def rescore_recorded(item: str, side: str) -> tuple[int, list[str], str | None]:
    """Re-score every recorded cell through the CURRENT scorer.

    Returns (cells compared, scores that MOVED, why it could not be compared).
    The third channel is separate on purpose: the first version returned "no
    comparable sheet" in the mismatch list, and its caller read that as "the
    score moved" -- so 1b, T1 and T2, which have no slot sheet at all and are
    scored deterministically from the fixture, were reported as evidence that a
    neutrality claim was FALSE. Not-comparable and disagrees are different facts
    and must not share a return channel (QUALITY_CONTROL.md 2k).

    ANSWERS THE QUESTION `scorer_sha` CANNOT. The fingerprint says whether the
    code an item's score depends on has changed; it cannot say whether the change
    could move that item's number. This can, from artifacts already on disk, at no
    call cost: take each recorded cell's verdicts, run today's scorer over them,
    and require the score the artifact stored.

    ONLY MISSING KEYS ARE RECOVERED. The first version of this called
    apply_computed unconditionally and OVERWROTE verdicts the artifact already
    held, which reported Q4b/p17 as a scorer disagreement when the stored 2.0 was
    arithmetically right -- `wrong_kind` is unsatisfied on both 1.5-point
    behaviour slots. `_our_failing_slots` guards the same call the same way; the
    guard is the difference between recovering an unrecorded verdict and
    inventing one.
    """
    import agreement as A
    import olx_prompts as O
    import cross_path as X
    import handouts as H

    doc = _runs_doc(item, side)
    if doc is None:
        return 0, [], "no recorded artifact"
    # THE JOB LOOKUP BELONGS INSIDE THE GUARD, and it was outside it until the
    # self-test's own "an item leaves JOBS" injection crashed the whole run with
    # KeyError: '1b' on 2026-09-04. That injection pops an item from the job
    # table and then runs the full audit, which is exactly the state this has to
    # survive: a check that raises under a mutation reports NOTHING, so one
    # unguarded lookup silently disabled all 63 cases rather than failing one.
    # "Not in the job table" is a not-comparable fact like "no comparable sheet",
    # so it takes the same third channel -- but with its own words, because the
    # two are different facts and 2j applies to the reasons as much as to the
    # channels.
    try:
        h = _jobs()[item]["handout"]
    except KeyError:
        return 0, [], "not in the job table"
    try:
        spec = A.load_action(f"bmod_handout{h}.olx", O.ACTION[item])
        rub = H.config(h)["rubric"].BY_ID[item]
        scorer = A.SCORERS[spec.get("kind") or "slots"]
    except Exception as e:
        return 0, [], f"no comparable sheet ({type(e).__name__})"

    n, bad = 0, []
    for run in doc["runs"]:
        for r in (run.get("results") or []):
            got = X.result_cell(r)
            if got is None:
                continue
            cell_item, pid, stored, vd = got
            if cell_item != item or stored is None or not vd:
                continue
            ch = {k: (v if isinstance(v, str) else str(v))
                  for k, v in vd.items() if v is not None}
            ans = {k: v for k, v in (r.get("answers")
                                     or r.get("refers_to") or {}).items()
                   if v is not None}
            rebuilt = A.rebuild_sheet(spec, ch, ans)   # T11: one router
            if _computed_slots(spec) - set(rebuilt):      # the guard
                try:
                    rebuilt = A.apply_computed(spec, rebuilt,
                                               _fixture_cached(item, pid))
                    rebuilt = A.expand_counted(dict(spec, _slots=spec["slots"]),
                                               rebuilt)
                except Exception:
                    continue
            try:
                now, _f = scorer(spec, rub, rebuilt)
            except Exception:
                continue
            n += 1
            if abs(float(now) - float(stored)) > 1e-9:
                bad.append(f"{item}/p{pid} [{side}]: artifact stored {stored:g}, "
                           f"today's scorer gives {now:g}")
    return n, bad, None


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
            # THE TWO WRITERS SPELL A COUNT DIFFERENTLY. agreement.py stores a
            # `counts` answer as the STRING "3"; agreement_app.py stores the INT
            # 3. is_satisfied calls .strip() on the verdict, so the int reached it
            # and raised AttributeError -- for EVERY olx cell of every item with a
            # counted family. Q1 was the case: sweep_summary("Q1") could not run
            # at all, so the per-check table that prints on every recording had
            # never once printed for it, and every slot-level readout of Q1's app
            # half was silently python-only. Same class as the null-verdict trap
            # above -- a difference in COVERAGE and FORMAT between the writers,
            # never in judgement -- so it is normalised here rather than reasoned
            # from.
            ch = {k: (v if isinstance(v, str) else str(v))
                  for k, v in raw.items() if v is not None}
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
            rebuilt = A.rebuild_sheet(spec, ch, ans)   # T11: one router
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


def _our_typical_failing_slots(item: str, pid: int) -> tuple[set, dict, int]:
    """The scored slots we TYPICALLY fail on a cell, pooled over both engines.

    Returns (majority set, per-slot run counts, runs pooled), the set already
    narrowed to gold's own vocabulary by `_gold_nameable_slots`.

    WHY MAJORITY AND NOT THE UNANIMOUS INTERSECTION, which is what
    `gold_slot_disagreements` used until 2026-09-09. An intersection is a LOWER
    BOUND on what we fail, so instability can only ever make our set SMALLER --
    and that biases the comparison in one direction. It manufactures
    under-charging (a slot we fail in 5 runs of 6 drops out and gold looks like
    it charged something we credit) and it is structurally BLIND to
    over-charging (a slot we fail in 11 of 12 can never enter the set unless it
    is unanimous). Six of the nine findings it reported were cells that fail
    exactly gold's slots in 4 or 5 runs of 6, and Q1/p9 -- where we charge
    `reason_2` and gold does not, on a cell the ledger independently bands 2/12
    wrong -- was invisible to it.

    WHY POOLED. `_our_failing_slots`' own docstring states the principle: "the
    two engines are pooled precisely because differences between them are
    sampling, not program". The exact comparison simply never did it and ran on
    the python side alone, at half the sample the ledger bands these same cells
    on. Pooling also absorbs a one-engine artifact correctly -- 1c/p16's `title`
    is a majority failure on python and not when both engines are counted.

    THIS IS THE RULE THE RETIREMENT SIDE ALREADY USED.
    `bounds_declarations_that_expired` has always pooled both engines, taken the
    strict majority and filtered to gold's vocabulary. So one table's entries
    were CREATED by the intersection rule and RETIRED by this one, which is two
    rules wearing one name: an entry could be created and then never be
    retirable. Both sides now call this function.
    """
    import collections

    runs = _our_failing_slots(item, pid, "olx") + _our_failing_slots(item, pid, "python")
    if not runs:
        return set(), {}, 0
    counts = collections.Counter(s for r in runs for s in set(r))
    maj = {s for s, k in counts.items() if k * 2 > len(runs)}
    # AGAINST GOLD'S VOCABULARY ONLY. A slot no phrase maps to cannot appear on
    # gold's side of the comparison, so keeping it on ours manufactures a
    # difference; and where the test is on the COUNT, a gate carrying no points
    # inflates our side so the equality can never hold. See _gold_nameable_slots.
    vocab = _gold_nameable_slots(item)
    if vocab:
        maj &= vocab
    return maj, dict(counts), len(runs)


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
    examined = skipped = declared = owned = 0
    seen_disagreeing: set = set()
    # AN OPEN SUBGOAL IS A DECLARATION. A cell somebody is actively working does
    # not also owe an entry in GOLD_SLOT_DISAGREEMENTS_KNOWN: that table says
    # "we have decided to live with this", and a live subgoal says the opposite
    # -- that the decision has not been made yet. Demanding both makes the audit
    # ask a cell's owner to declare it settled before they have settled it, and
    # the honest answer (an open goal naming it) then reads as an omission.
    # Read once, not per cell: _live_subgoal_owners re-reads GOALS.md each call.
    _owners = _live_subgoal_owners()["any"]
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
            stable, _counts, _n = _our_typical_failing_slots(item, pid)
            if not _n:
                continue
            examined += 1
            if stable == charged:
                continue
            seen_disagreeing.add((item, pid))
            if (item, pid) in GOLD_SLOT_DISAGREEMENTS_KNOWN:
                declared += 1
                continue
            if _owners.get(f"{item}/p{pid}"):
                owned += 1
                continue          # an open subgoal owns it -- see above
            # THE DISTRIBUTION, NEVER A BARE SET. The set is a majority over
            # pooled runs, and quoting it alone rounds each slot's majority up to
            # certainty -- the same misreading as quoting a median alone.
            spread = ", ".join(f"{s} {_counts.get(s, 0)}/{_n}"
                               for s in sorted(charged | stable))
            out.append(
                f"{item}/p{pid}: gold charges {sorted(charged)}, we typically fail "
                f"{sorted(stable)} — differs on {sorted(charged ^ stable)} "
                f"(pooled over {_n} runs: {spread}). The TOTAL can still agree, "
                f"which is how this stayed invisible. Declare it in "
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
            if _owners.get(f"{item}/p{pid}"):
                owned += 1
                continue          # an open subgoal owns it -- see above
            definite, count = b
            stable, _counts, _n = _our_typical_failing_slots(item, pid)
            if not _n:
                continue
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
        # THE SHARED RULE. This function pooled, took the majority and filtered
        # to gold's vocabulary while the DETECTION side used a python-only
        # unanimous intersection, so entries were created by one rule and retired
        # by another. Both now call _our_typical_failing_slots.
        maj, _seen, _n = _our_typical_failing_slots(item, pid)
        if not _n:
            continue          # unreadable is not agreement
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


def _live_subgoal_owners(excluding: str = '') -> dict:
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
        return {"any": {}, "title": {}, "subject": {}, "by_side": {}}
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
    owners: dict = {"any": {}, "title": {}, "subject": {}, "by_side": {}}
    current = None
    title_sides: frozenset = frozenset()
    # A CORPUS REFERENCE IS A CITATION OF TEXT, NOT A CLAIM OF OWNERSHIP.
    # `[[corpus Q5/p4 first 0:53 sha=...]]` names the cell whose WORDS are being
    # quoted, and the cell-mention regex below reads `Q5/p4` out of it exactly as
    # if the entry had said the subgoal covers that cell. Measured when the
    # references landed: five cells became "owned" by a subgoal that only quoted
    # them, and fifteen ownership lists inflated -- which would have taken five
    # genuine orphans off `wrong_cells_without_an_owner` without a word in the
    # output. Strip the references first; an entry that really owns the cell says
    # so in its own prose, which is still scanned.
    text = re.sub(r"\[\[corpus[^\]]*\]\]", " ", text)
    for line in text.splitlines():
        # AN ENTRY ENDS AT THE NEXT ENTRY *OR* THE NEXT HEADING. Without the
        # heading, the LAST labelled entry of a section swallows everything after
        # it: subgoal Q26 is the last before `## THEN` and was owning D2/p11,
        # WK1/p7, Q4b/p12 and DAY2/p7 out of prose that is not its entry at all.
        # That WEAKENS the check it feeds -- a cell counts as owned by a subgoal
        # that never discusses it -- which is the opposite of a false alarm and
        # so leaves no trace. Subgoal E40.
        if re.match(r"^#{1,3} ", line):
            current, title_sides, title_items = None, frozenset(), set()
            continue
        m = re.match(r"- \[( |x)\] ([EQ]\d+)\.", line)
        is_title = bool(m)
        if m:
            # `excluding` lets a caller ask what the field looks like WITHOUT
            # one still-open entry -- see `orphans_if_closed`. Without it the
            # owner checks are blind to exactly the cells a closure is about to
            # drop, because the entry is still open and still naming them.
            current = (None if m.group(1) == "x" or m.group(2) == "E30"
                       or (excluding and m.group(2) == excluding)
                       else m.group(2))
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
        # A CELL WRITTEN AS BARE `pN` IS STILL THIS SUBGOAL'S, when its title
        # names the item. Subgoal E40: matching only `item/pN` lost the cells
        # subgoals actually own. Q14's cells were written "p10 and p18" and Q18's
        # as bare `p12` under a title naming Q4b, so Q1/p10 was attributed to Q20
        # on three passing mentions and Q4b/p12 to Q19 and Q26 on one each, while
        # the two subgoals those cells are ABOUT owned nothing. Seven open entries
        # were affected. The audit never noticed because
        # wrong_cells_without_an_owner asks only whether SOME subgoal owns a cell.
        #
        # `subject` is the new, STRONGER claim: the item comes from this entry's
        # own title, so the entry is about the cell rather than mentioning it.
        # `any` stays generous -- it exists so no wrong cell goes unlooked-at --
        # and `title` still means "written out in the title line".
        resolved = {f"{it}/p{n}" for it in title_items
                    for n in re.findall(r"(?<![\w/])p(\d{1,2})\b", line)}
        for key in sorted(resolved):
            owners["subject"].setdefault(key, []).append(current)
            if key not in owners["any"] or current not in owners["any"][key]:
                owners["any"].setdefault(key, []).append(current)
            for side in here:
                owners["by_side"].setdefault(key, {}).setdefault(
                    side, []).append(current)
        for cell in re.findall(r"\b([A-Za-z0-9]{1,4})/p(\d{1,2})\b", line):
            key = f"{cell[0]}/p{cell[1]}"
            owners["any"].setdefault(key, []).append(current)
            if cell[0] in title_items:
                owners["subject"].setdefault(key, []).append(current)
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


# Cells where gold awarded FULL MARKS IN SILENCE, we charge, and the disagreement
# has been read out and DECLARED rather than left as an open question. Subgoal
# Q45.
#
# WHY A SEPARATE TABLE. `silent_full_marks_we_refuse` reports these as questions
# and rightly does not resolve them; GOLD_CODE_KNOWN cannot hold them, because
# its check skips any cell where gold charged nothing (`if got is None:
# continue`), so a declaration filed there would suppress nothing and sit unread.
# CORRECTED_GOLD is also wrong: these are cells we are NOT correcting.
# Entries: the gold file.
SILENT_GOLD_DIVERGENCES = _gold_declaration("SILENT_GOLD_DIVERGENCES")

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
        if (item, pid) in SILENT_GOLD_DIVERGENCES:
            verdict = "DECLARED divergence -- SILENT_GOLD_DIVERGENCES; " + verdict
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


def wrong_cells_without_an_owner(excluding: str = '') -> list[str]:
    """Cells we get wrong that no live subgoal and no declaration accounts for."""
    import handouts as H

    owned = _live_subgoal_owners(excluding)
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
        # AND NEITHER IS A *SILENT* DECLARED MISS. This check read only
        # GOLD_DIVERGENCES, so a cell declared in SILENT_GOLD_DIVERGENCES was
        # reported as an orphan the moment its subgoal closed -- which happened
        # to PR/p15 on 2026-09-07, minutes after E55 closed, on a cell whose
        # disposition had been filed with a written reason earlier the same day.
        # The two tables say the same thing about ownership: somebody decided,
        # and the decision is findable FROM THE CELL. They differ in whether gold
        # said anything, not in whether we owe an owner.
        # DECLARED_CEILING_CELLS is included for the same reason (subgoal E45).
        if (item, pid) in SILENT_GOLD_DIVERGENCES:
            continue
        if (item, pid) in DECLARED_CEILING_CELLS:
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

# CELL-LEVEL CEILINGS, machine-readable. Subgoal E45's last unmet constraint:
# "IT MUST NOT FIRE ON A DECLARED CELL ... It needs a way to say DECLARED-CEILING,
# or Q35's decision gets re-litigated by machinery every run."
# `unstable_cells_without_an_owner`'s own docstring names the gap it closes -- "a
# ceiling recorded only in a CLOSURE NOTE is not visible here -- 2a/p14 is exactly
# that case, and it passes only because subgoal Q50 names it. That is a real gap."
# Being owned BY ACCIDENT is not being declared: if Q50 ever closes, the cell
# fires and a closed subgoal's decision is re-argued by a check.
# THIS IS NOT `GOLD_DIVERGENCES`. A divergence says our answer is the endorsed one
# and gold is the outlier. A CEILING says the cell cannot be settled either way --
# a weaker and different claim, and conflating them would let a ceiling be cited
# as if we had been vindicated.
# Entries: the gold file.
_1C_GATE_CEILING = _gold_declaration("_1C_GATE_CEILING")

# Entries and their reasoning: `coursedata.gold_notes("DECLARED_CEILING_CELLS", key)` (20 lines).
DECLARED_CEILING_CELLS = _gold_declaration("DECLARED_CEILING_CELLS")


def ceiling_declarations_that_expired() -> list[str]:
    """A cell declared a ceiling that has since gone PERFECT or gone WRONG.

    The same ratchet as `GOLD_SLOT_DISAGREEMENTS_KNOWN`'s expiry check: a
    declaration is a claim about the present, and a claim nothing tests decays
    into folklore. A ceiling cell that is now perfect should lose its entry; one
    that has gone WRONG is no longer a counted-right cell hiding from the wrong-
    cell check, so it needs a real owner instead.
    """
    out = []
    bands = cell_bands()
    for (item, pid), why in sorted(DECLARED_CEILING_CELLS.items()):
        band = (bands.get(f"{item}/p{pid}") or (None, None, None))[2]
        if band == "perfect":
            out.append(f"{item}/p{pid} is declared a CEILING but is now PERFECT -- "
                       f"drop the entry; the ceiling it recorded is gone")
        elif band in ("always_wrong", "wrong_by_median"):
            out.append(f"{item}/p{pid} is declared a CEILING and is now WRONG by "
                       f"the median -- it is no longer hidden from "
                       f"`wrong_cells_without_an_owner`, so give it an owner and "
                       f"drop the ceiling")
    return out


UNSTABLE_UNOWNED_BUDGET = 0
# SUBGOAL E45. Zero, and it starts there because subgoal Q50 took the ten cells
# this check was built to find. A budget that starts at today's count never fires
# until things get worse; this one is satisfied today, so it fires on the FIRST
# unstable cell nobody writes down. Raise it only with the cell named and a
# reason, the way PROSE_ONLY_BUDGET is raised.


def unstable_cells_without_an_owner(excluding: str = '') -> list[str]:
    """Unstable cells no open subgoal names. Preflight step 5e. Subgoal E45.

    THE SIBLING CANNOT SEE THESE. `wrong_cells_without_an_owner` asks whether a
    cell WRONG by the recorded median has an owner. A cell counted RIGHT at
    9 of 12 is a latent wrong cell -- it answers differently on identical input
    and is one run from the median moving -- and nothing asked about it. That is
    the other half of subgoal E41's laundering finding: E41 built `cell_bands` so
    the coin flips are visible, and this asks whether anyone owns them.

    THEY SURFACE BY ACCIDENT OTHERWISE. On 2026-09-05 ten such cells were found
    only because closing subgoal Q10 pushed a NEIGHBOURING cell (Q3/p13) over the
    line into wrong, which made the sibling speak. Nothing else would have.

    OWNERSHIP HERE IS `any`, NOT `by_side`, AND THAT IS A DELIBERATE WEAKENING.
    The sibling demands per-side ownership because a paper-side subgoal is no
    home for a cell we get wrong on olx. Applying that standard here has a cost
    the sibling never pays: `by_side` is populated only from a bare `pN` under a
    title naming the item (subgoal E40), so satisfying it for cells spread across
    six items forces a SIX-ITEM TITLE -- and then every bare `pN` in that entry
    claims a cell on all six. Measured the day this was written: subgoal Q30's
    title gained one item and claimed eleven cells, Q50's claimed three it did
    not mean. A standard that can only be met by masking future orphans is the
    wrong standard, so this one accepts a passing mention and says so. Both
    standards report 0 today; the choice is about which failure mode is bought,
    not about which is currently satisfiable.

    A DECLARED CELL IS NOT AN ORPHAN, on the sibling's own reasoning: a
    GOLD_DIVERGENCES entry already carries the reason, and demanding a subgoal
    too would be two names for one claim. Note that a ceiling recorded only in a
    CLOSURE NOTE is not visible here -- 2a/p14 is exactly that case, and it
    passes only because subgoal Q50 names it. That is a real gap and Q35 wrote
    it down: the written record is the only protection for such a cell.
    """
    import handouts as H

    owners = _live_subgoal_owners(excluding)["any"]
    out: list[str] = []
    for key, (right, total, band) in sorted(cell_bands().items()):
        if band not in ("unstable_counted_right", "on_the_line"):
            continue
        item, _, tail = key.partition("/p")
        try:
            pid = int(tail)
        except ValueError:
            continue
        # A DECLARED CEILING IS NOT AN ORPHAN. E45's constraint, and the reason
        # the table exists rather than the closure note being re-read by hand.
        if (item, pid) in DECLARED_CEILING_CELLS:
            continue
        # SUSPECT CELLS ARE NEVER EVIDENCE, so they are never a debt either.
        if pid in set(H.suspect(_handout_of(item))):
            continue
        if H.gold_divergence(item, pid):
            continue
        if owners.get(key):
            continue
        out.append(
            f"{key} is UNSTABLE at {right} of {total} ({band}) and no OPEN "
            f"subgoal names it. It is counted RIGHT, so "
            f"wrong_cells_without_an_owner will never mention it, and it can "
            f"drift for weeks unread. Name it, declare it, or record that the "
            f"rate is noise and it is watched")
    if len(out) <= UNSTABLE_UNOWNED_BUDGET:
        return []
    return out


def _handout_of(item: str) -> int:
    """Which handout an item belongs to, for the suspect list. Subgoal E45."""
    for h in (1, 2, 3):
        try:
            if item in _handout_gold_items(h):
                return h
        except Exception:
            continue
    return 0


# THE FIELD A RESULT RECORDS A SLOT IN DEPENDS ON WHAT KIND OF SLOT IT IS AND
# WHICH ENGINE WROTE IT, and every consumer used to re-type the lookup. That is
# subgoal E47: eleven places rolled their own two-line version and two of them
# were wrong in opposite directions.
#
#   python results   `answers` holds PICK values; `checks` holds VERDICTS -- and
#                    `checks` ALSO carries the pick key with an EMPTY STRING.
#   olx results      `refers_to` holds picks; `verdicts` holds verdicts, and a
#                    verdict may be a bare string or {"verdict": ...}.
#
# THE TWO FAILURE MODES, both met on 2026-09-05:
#   `r.get("checks") or r.get("verdicts")` -- `checks` is a truthy dict, so this
#   never consults `verdicts`; and for a PICK, `checks[key]` is `''`, so the real
#   answer in `answers` is never reached. This is what made a readout report Q2's
#   `wgb_names` as never answered on the python side when it answered `doing` 97
#   times, and that wrong reading was reported as fact.
#   `r.get("answers") or r.get("refers_to")` -- the same shape the other way: if
#   `answers` exists but lacks the key, `refers_to` is never tried.
# An empty string is ABSENCE here, not a value. That single rule is what both
# hand-rolled forms got wrong.


def slot_answer(result: dict, key: str):
    """What a run's result records for one slot, whatever field it lives in.

    Tries the PICK fields before the VERDICT fields, because a python result
    carries a pick's real value in `answers` and a placeholder `''` for the same
    key in `checks`. Returns None when the slot was not answered at all -- which
    is a real and important state: it is how a rubric slot that never reached the
    sheet's `slots=` list looks from the artifact side.
    """
    for where in ("answers", "refers_to", "checks", "verdicts"):
        d = result.get(where)
        if not isinstance(d, dict):
            continue
        v = d.get(key)
        if isinstance(v, dict):
            v = v.get("refers_to", v.get("verdict"))
        if v not in (None, ""):
            return _same_shape(v)
    # THE PAPER SCORER IS A THIRD SHAPE. score.py writes `credit_checks` as a
    # LIST of {what, met, ...} rather than a verdict map, so none of the four
    # fields above exists on its results. cross_path.py already knew this and
    # folded it to met/absent; this reader did not, and would have returned None
    # for every paper cell -- silently, exactly the failure mode it was built to
    # stop. Subgoal E28 is 24 items of paper measurement waiting to be read.
    for c in (result.get("credit_checks") or []):
        if isinstance(c, dict) and c.get("what") == key:
            # THE RECORDED VALUE, not a met/absent fold of the `met` flag. That
            # fold DISCARDED what was actually answered, so a pick came back as
            # `absent` where the artifact said `before` -- and
            # check_mapped_slots_agree_with_their_map was handed a wrong pick
            # and a null verdict on the same row, from the two readers its own
            # comment calls canonical.
            v = c.get("verdict")
            if v not in (None, ""):
                return _same_shape(v)
            return "met" if c.get("met") else "absent"
    return None


def _same_shape(v):
    """One spelling per answer, whichever engine wrote it. Subgoal E47.

    THE TWO WRITERS SPELL A COUNT DIFFERENTLY -- agreement.py stores it as the
    STRING "3", agreement_app.py as the INT 3 -- and measured.py has said so in a
    comment since the day `is_satisfied` raised AttributeError on the int. The
    canonical reader did NOT act on it, so every cross-engine tally counted one
    answer twice: `Counter` over twelve identical runs returned
    `{'3': 6, 3: 6}`, which reads as a slot flipping 6-6 when nothing moved.
    ON 2026-09-06 THAT MISREAD FOUR OF Q1's SLOTS AT ONCE -- `harms_listed`,
    `reasons_given` and two others were reported as flipping on cells where they
    are stable, and the error was caught only because a "flip" of exactly 6-6 on
    four slots at once looked too tidy to be real.
    Numbers normalise to `str`; everything else is returned unchanged, so a
    verdict like `met` is untouched and a count like 3 and "3" become one answer.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return str(v)
    return v


@functools.lru_cache(maxsize=None)
def _pick_slots(item_id: str) -> frozenset:
    """Slots that answer a PICK rather than a verdict, for one item.

    DECLARED, not guessed: SLOT_SPEC carries each sheet slot's `seg`, and a
    segment of the form `pick(setname)` means the slot answers WHICH member of
    that set it refers to. Read with `olx_prompts.pick_set`, which is the parser
    the web uses on the same string, so the two sides cannot drift on what
    counts as a pick.

    Needed because the PAPER artifact stores a pick's value in the same
    `verdict` field as a real verdict, so `slot_verdict` cannot tell them apart
    from the artifact alone -- and its whole contract is that it never returns a
    pick.
    """
    import olx_prompts as O
    import handouts as _H_R

    for mod in (_H_R.config(1)["rubric"], _H_R.config(2)["rubric"],
                _H_R.config(3)["rubric"]):
        spec = (getattr(mod, "SLOT_SPEC", {}) or {}).get(item_id)
        if spec:
            return frozenset(d["key"] for d in spec if O.pick_set(d.get("seg")))
    return frozenset()


def slot_verdict(result: dict, key: str):
    """The VERDICT a result records for one slot, never its pick value.

    Separate from `slot_answer` on purpose. A mapped slot has a pick and a
    verdict under DIFFERENT keys, but nothing stops a future sheet from using one
    name for both, and a check that means "what verdict was recorded" must not
    silently accept a pick. `enforcement.check_mapped_slots_agree_with_their_map`
    is exactly that check.
    """
    for where in ("checks", "verdicts"):
        d = result.get(where)
        if not isinstance(d, dict):
            continue
        v = d.get(key)
        if isinstance(v, dict):
            v = v.get("verdict")
        if v not in (None, ""):
            return v
    # THE PAPER SCORER IS A THIRD SHAPE and this reader did not know it, while
    # `slot_answer` below did. So every check meaning "what verdict was
    # recorded" skipped every paper row and returned its findings anyway --
    # indistinguishable from having looked. That is how an off-map verdict this
    # project INTRODUCED went unreported by the check written to catch exactly
    # it: Q4a/p18 recorded `antecedent_kind_2` = `before`, which the map sends
    # to `met`, beside an answered `antecedent_2` = `absent`, five runs of six.
    for c in (result.get("credit_checks") or []):
        if not isinstance(c, dict) or c.get("what") != key:
            continue
        # THE CONTRACT HOLDS: never a pick. Paper writes a pick's value into the
        # same `verdict` field as a real verdict, so they are indistinguishable
        # in the artifact and must be separated by the SHEET.
        if key in _pick_slots(result.get("item_id") or ""):
            return None
        v = c.get("verdict")
        if v not in (None, ""):
            return v
        return "met" if c.get("met") else "absent"
    return None


def slot_block(source: str, what: str) -> str | None:
    """The FULL dict literal for one rubric slot, PARSED not scanned. Subgoal E52.

    WHY THIS EXISTS. Four errors in one session came from reading a slot out of
    source with a FIXED SPAN -- `t[i:i+900]`, `find(..., i, i+3000)`, a regex to
    the next `"what":`. All silent, two of them producing confident wrong claims:
    subgoal Q30's edit was declared "not in rubric_h1" because a fixed-span
    extract compared byte-identical across twelve commits (it was there,
    uncommitted, in `example_2`'s failing clause), and a readout reported Q2's
    `wgb_names` as never answered on python when it answered `doing` 97 times.
    A span cannot know where a literal ends: it truncates, so two slots compare
    equal on a shared prefix, or it over-reads and reports a neighbour's change.

    A HAND-ROLLED BRACE COUNTER WAS TRIED FIRST AND WAS WORSE, which is why the
    parser is not over-engineering. Counting braces while tracking quotes looks
    sufficient until a COMMENT contains an apostrophe -- "the slot's own prose" --
    which opens a string that never closes. `wgb_inverts_utb` came back at 25,934
    characters having swallowed `reasons_given` and run to the item's closing
    brace. Python source is not scannable by eye or by regex; it is parseable.

    `ast` DOES NOT IMPORT THE MODULE, it only parses text, so this works on any
    revision `git show` can produce. A revision too broken to parse is too broken
    to compare anyway, and returns None rather than a plausible wrong answer.

    Returns None when the slot is absent -- a real answer, distinct from present
    and empty.
    """
    import ast

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key, val in zip(node.keys, node.values):
            if (isinstance(key, ast.Constant) and key.value == "what"
                    and isinstance(val, ast.Constant) and val.value == what):
                return sourcecache.segment(source, node)
    return None


def slot_blocks_differ(a: str, b: str, what: str) -> bool:
    """Did one slot's literal change between two revisions of a file?"""
    return slot_block(a, what) != slot_block(b, what)


def set_slot_field(path: str, item: str, what: str, field: str,
                   new_value: str, expect_contains: str = "") -> bool:
    """Replace one field of one rubric slot, editing the VALUE not the source.

    Subgoal E47. Every failed edit on 2026-09-06 was a source WRITE, and every
    one failed the same way: a multi-line string literal was hand-written and
    matched against source whose line breaks fall wherever the original author
    put them. `"A response built entirely of such clauses is `absent`"` is ONE
    sentence in the value and TWO lines in the file, broken after "built".
    Matching the sentence finds nothing; matching the lines requires knowing
    where someone else pressed return.

    SO THIS NEVER MATCHES SOURCE TEXT. It parses with `ast`, finds the dict whose
    `"what"` is `what`, locates `field`, and replaces exactly that value's source
    segment with a freshly wrapped literal. Line breaks in the original are
    irrelevant because the whole literal is replaced.

    `expect_contains` is a precondition on the CURRENT value -- the safe form of
    an anchor. It asserts what you believe you are editing without requiring you
    to reproduce its formatting.

    Returns True on success. Raises rather than writing a half-edit.
    """
    import ast
    import pathlib

    src = pathlib.Path(path).read_text()
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = {k.value: v for k, v in zip(node.keys, node.values)
                if isinstance(k, ast.Constant)}
        if keys.get("what") is None or getattr(keys["what"], "value", None) != what:
            continue
        if field not in keys:
            raise KeyError(f"{item}/{what} has no field {field!r}")
        target = keys[field]
        break
    if target is None:
        raise KeyError(f"no slot {what!r} found in {path}")
    old = sourcecache.segment(src, target)
    if old is None:
        raise ValueError("could not locate the field's source segment")
    # THE NODE ALREADY HOLDS THE JOINED VALUE. Implicitly-concatenated literals
    # parse to ONE Constant, so the precondition reads `target.value` -- never
    # `literal_eval` of the source segment, which is indented and raises.
    current = target.value if isinstance(target, ast.Constant) else ""
    if expect_contains and expect_contains not in (current or ""):
        raise AssertionError(
            f"{item}/{what}.{field} does not contain {expect_contains!r} -- "
            f"the value is not what the caller believed")
    indent = " " * 24
    import textwrap
    # NON-STRING FIELDS GO THROUGH repr, NOT THE WRAPPER. `verdicts` and
    # `choices` are LISTS, and _wrap_for_literal calls textwrap on the value --
    # which raises AttributeError on a list, mid-edit, AFTER an earlier field in
    # the same loop has already been written. That is the worst shape a failure
    # can take here: a half-applied edit that still parses. Adding a rule case
    # and its new pick value is one change in two fields, so this path has to
    # handle both kinds or callers hand-edit around it, which is what this
    # function exists to stop.
    if isinstance(new_value, str):
        body = "".join(f'{indent}"{line}"\n'
                       for line in _wrap_for_literal(new_value))
        lit = body.strip()
    else:
        lit = repr(new_value)
    i = src.index(old)
    pathlib.Path(path).write_text(src[:i] + lit + src[i + len(old):])
    ast.parse(pathlib.Path(path).read_text())          # never leave it unparseable
    return True


def _wrap_for_literal(value: str, width: int = 66) -> list:
    """Wrap a value into literal-sized pieces, PRESERVING IT EXACTLY.

    THIS FUNCTION CORRUPTED PROMPT TEXT and the damage was silent. The first
    version handed the whole value to `textwrap.wrap`, which:

      * COLLAPSES ALL WHITESPACE, newlines included. Q4b's `b1_basis` rule lists
        its pick values one per line; a round-trip through here turned
        "\\n  `activity` -- something they did INSTEAD" into
        " `activity` -- something they did INSTEAD" and flattened the list into a
        paragraph. Nothing reported it: the file still parsed, the rule still
        read sensibly, and the only symptom was a prompt sha that would not
        return after a revert.
      * SPLITS ON HYPHENS. "failing-alternative" came back as
        "failing- alternative" in `b2_basis`.

    So an edit made through set_slot_field changed text the caller never touched,
    and a REVERT through it could not restore the original bytes -- which is how
    this was found: `--restore-previous` refused, correctly, because the prompt
    had not come back to the sha its measurement was taken at.

    Now: split on newlines FIRST and re-emit them as explicit escapes, wrap each
    line separately, and never break a hyphenated word. A value with no newlines
    and no hyphens wraps exactly as before, so existing literals are unaffected.
    """
    import textwrap

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace('"', '\\"')

    out: list = []
    lines = value.split("\n")
    for li, line in enumerate(lines):
        last_line = li == len(lines) - 1
        if not line:
            out.append("" if last_line else "\\n")
            continue
        pieces = textwrap.wrap(line, width, break_long_words=False,
                               break_on_hyphens=False) or [""]
        for pi, piece in enumerate(pieces):
            s = esc(piece)
            if pi < len(pieces) - 1:
                s += " "          # the wrap ate a space; put it back
            elif not last_line:
                s += "\\n"        # the split ate a newline; put it back
            out.append(s)
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
