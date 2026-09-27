"""Per-handout wiring: where the files are, how to split them, what scores them."""

# `RUBRIC_SOURCE` IS RETIRED, and this is the declaration 11.6 asks for.
#
# It was an environment switch choosing where the rubric came from -- "module" for
# the `rubric_h{1,2,3}` modules, "object" for the course file -- so the two could be
# run against each other while both existed. 11.6 said it retires in the same change
# that removes the modules, "since after that it is a switch with one working
# position". Stage 5 deleted h1 and h3, Stage 6c moved h2 out of the scoring path as
# `rubric_h2_source.py`, and that position is now the only one: every reader takes
# the rubric from the course file through `coursedata`.
#
# NOTHING IN `scoring/` READS IT. What remain are SETTERS in the migration harness
# -- stage04_migrate_rubric.py, stage06_freeze_rubric_oracle.py and stage05_gate.py
# -- and they are now inert. That matters for one of them: stage05_gate runs a
# comparison with the switch at "module" and again at "object" expecting the two to
# differ, and with no reader left those are the same run twice. It cannot fail on
# that axis any more. Stage 5 is already certified, so this is RECORDED rather than
# acted on -- but a gate that still sets a switch nobody reads is measuring nothing
# by that means, and the next person to trust that row should know it.

from __future__ import annotations

import glob
import os
import re

# `paths` FIRST: it puts this course's `scoring/<course>/` and the general
# `scorers/` on `sys.path`, and the imports just below are modules that live
# there. Importing them before `paths` raises ModuleNotFoundError -- measured
# on 13 modules the day those directories were split out.
import paths  # noqa: F401  (import order is load-bearing; see above)
import gold as gold_mod
# BY HANDOUT, not by name. Goal N: the engine imported `H1_MARKERS,
# H2_MARKERS, H3_MARKERS` from the COURSE -- three per-handout names crossing the
# boundary in the wrong direction, and a fourth handout could not be expressed at
# all. `_markers(h)` reads the course file, which is where they always came from.
from segment import _markers

import paths


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


# ROOT used to be one directory. It is now three: the blank templates ship
# with the code (MATERIALS), the filled-in submissions never enter git
# (SUBS), and run output is scratch (OUT). See paths.py.
MATERIALS = paths.roots().materials
SUBS = paths.roots().submissions
OUT = paths.roots().out

# ── Gold rows the grader got wrong, corrected ────────────────────────────────
#
# A FIFTH kind of gold caveat, and the narrowest. The four already here say what
# to do when gold is unreachable or inconsistent; none of them changes the number
# we are scored against. This one does, and only where the gold row contradicts
# a FACT ESTABLISHED IN THE STUDENT'S OWN SUBMISSION — not where we merely judge
# differently.
#
#   GOLD_DIVERGENCES   we disagree on purpose; the cell is still scored as gold
#                      has it, and the miss stands
#   PER_ITEM_EXCLUDE   the cell is dropped, because nothing correct can score it
#   GOLD_CEILINGS      a criterion gold decides inconsistently, so some cells are
#                      unwinnable whichever rule you pick
#   UNSCORED_GOLD_CRITERIA
#                      criteria neither system scores at all
#   CORRECTED_GOLD     the gold NUMBER is wrong on the submission's own evidence,
#                      and the corrected number is what we score against
#
# A CORRECTION HERE INVALIDATES EVERY EARLIER MEASUREMENT OF THAT CELL, and the
# stored figure does not know it. out/q6_boxbounds_full published "17/20 (85%)"
# for Q6 and was cited as the baseline all through 2026-08-19; it ran before the
# p4 entry below, when p4's gold was the unreachable 6.00 and our 6.25 counted
# exact by nearest_attainable. Against p4 = 7.50 that same run is 16/20. Nothing
# recomputes a stored .json when a row is corrected, so the published number and
# a fresh recomputation of the same data differed by a cell, which I spent part
# of that day attributing to a bug in the reporter. Re-derive a baseline from its
# .runs.json after touching this table, or compare only figures computed on the
# same gold.
#
# The bar is deliberately high, and `was` is asserted against the sheet on every
# run so a correction cannot outlive the row it corrects.
#
# WHAT DOES NOT QUALIFY, with the worked example that nearly got in. On 2026-08-19
# these rows looked like they contradicted themselves: p5, p4 and p17 each charge a
# consequence for not matching 4c and then CREDIT the effect slot for that same
# consequence, which reads as crediting a description of what becomes of something
# gold has just said was never named. Correcting it was proposed and would have
# moved three rows and four slots, 5.00 points.
#
# It is not a contradiction. Surveyed across all twenty rows, gold charges an
# effect slot when NO EFFECT IS DESCRIBED -- p1 "did not say how the first
# consequence is being affected", p15 and p16 "did not clarify ... being affected",
# p8 "did not state each consequence being affected and how" -- and never merely
# because the naming missed. p5's row reads: the wrong consequence was named, which
# is 1.25 off, and a change WAS described, so that is not charged twice. One
# mistake, charged once. Gold is applying no-double-jeopardy, consistently, on
# every row.
#
# So the principle behind the proposed correction -- that effect credit should be
# contingent on naming credit -- is a RUBRIC-DESIGN OPINION, and gold holds a
# defensible opposing one. That is exactly the line this table draws: p18's entry
# rests on a second antecedent that does not exist in the document, p9's on an
# antecedent that appears in no 4a item, p4's on a consequence equivalence the
# student's own 4c supplies. Those are facts about a submission. "We would charge
# this differently" is not, however consistently we would do it, and it belongs in
# GOLD_DIVERGENCES if anywhere.
#
# Worth knowing which way the money went, since it is not the flattering direction:
# applying it would have made p4 exact and turned p5 and p17 into misses, costing
# us a cell. The reason to refuse it is the standard, not the score.
# Entries and their reasoning: `coursedata.gold_notes("CORRECTED_GOLD", key)` (64 lines).
CORRECTED_GOLD = _gold_declaration("CORRECTED_GOLD")


def corrected_gold(item: str, pid: int) -> dict | None:
    """The correction for one cell, or None. See CORRECTED_GOLD."""
    return CORRECTED_GOLD.get((item, pid))


def apply_corrected_gold(rows: dict, form: int) -> dict:
    """Overwrite the gold score wherever CORRECTED_GOLD names a cell.

    Applied inside the gold LOADER rather than at each call site, because eight
    places load gold — the app, the CLI, the paper baseline, interim, the audit,
    self_graded_misses — and a correction applied in some of them would make the
    columns stop being a comparison. Every consumer goes through
    config(h)["gold"](), so this is the one place that reaches all of them.
    """
    for (item, pid), fix in CORRECTED_GOLD.items():
        cell = (rows.get(pid) or {}).get(item)
        if not cell:
            continue                    # different handout, or no such row
        cell["score"] = fix["score"]
        cell["corrected_from"] = fix["was"]
    return rows


def _gold_loader(fn, form: int):
    def load(*a, **kw):
        return apply_corrected_gold(fn(*a, **kw), form)
    return load


# ---------------------------------------------------------------------------
# STAGE 4. `HANDOUTS` holds FIVE different kinds of thing and only one of them is
# course data. The blurb and the parsing flags now come from the course file; the
# paths stay COMPUTED, because storing a resolved path bakes in one machine; the
# markers are read from the course file's own copy rather than duplicated here;
# `gold` and `rubric` are wiring, not data; and the participant lists wait for
# C1b's gold file.
# ---------------------------------------------------------------------------
def _course_field(form: int, name: str, default=None):
    """One of this handout's authored fields, from the course file."""
    import coursedata

    return coursedata.declaration("HANDOUT_FIELDS").get(str(form), {}).get(
        name, default)


class _RubricView:
    """One handout's rubric, served from the COURSE FILE, shaped like the module.

    `config(h)["rubric"]` used to hand out the `rubric_h{h}` MODULE OBJECT, and
    101 call sites across 18 modules reach the rubric through it --
    `config(h)["rubric"].BY_ID[item]`, `.ITEMS`, `.SLOT_SPEC`. That is the real
    dependence on the modules Stage 5 deletes; the thirteen `import rubric_h*`
    statements are the smaller half. Converting the importers alone would take
    the ratchet to zero and leave 101 sites to break on the day the files go.

    So the channel is converted instead of the callers. Every one of those sites
    keeps its spelling and starts reading the course file. Measured before the
    swap: BY_ID, ITEMS and SLOT_SPEC reproduce EXACTLY for all three handouts,
    order-sensitively, once the export's synthesised `handout` field is set
    aside -- an item does not record which handout it is in, because the module
    it was written in WAS the handout.

    MATERIALISED AND MUTABLE, WHICH IS NOT AN OVERSIGHT. `enforcement_selftest`
    injects by mutating `BY_ID` in memory and expects the checks to notice. A
    view that recomputed from the file on every read would make all eleven of
    those injections invisible -- the cases would report VACUOUS, which is what
    happened when forked audits were given their own copy of the tree. Each name
    is built once, on first access, and handed back as the same mutable object.
    """

    __slots__ = ("_form", "_cache")

    def __init__(self, form: int):
        self._form = form
        self._cache: dict = {}

    def __repr__(self):
        return f"<rubric h{self._form} from the course file>"

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        cache = object.__getattribute__(self, "_cache")
        if name in cache:
            return cache[name]
        import coursedata

        h = object.__getattribute__(self, "_form")
        if name in ("BY_ID", "ITEMS"):
            # ONE SET OF ENTRIES, SHARED BY BOTH NAMES. In the modules,
            # `BY_ID[item] IS` the corresponding element of `ITEMS` -- BY_ID is
            # built from ITEMS -- and code relies on it: the self-test pops a
            # key from `BY_ID["Q6"]` and `cli_signatures`, which reads `ITEMS`,
            # is expected to notice. Building the two independently made them
            # value-equal and identity-distinct, so the injection landed on a
            # copy nothing read and the case reported VACUOUS.
            #
            # `same_shape` compares VALUES and cannot see an aliasing
            # difference, which is why this was found by an injection going
            # quiet rather than by the equivalence check passing wrongly.
            items = [{k: v for k, v in it.items() if k != "handout"}
                     for it in coursedata.items()
                     if str(it.get("handout")) == str(h)]
            cache["ITEMS"] = items
            cache["BY_ID"] = {str(it["id"]): it for it in items}
            return cache[name]
        else:
            # Any other module-level authored value the export carried. Raising
            # AttributeError for an absent one is deliberate: `getattr(rub,
            # "SLOT_SPEC", {})` is a real call site and must keep working.
            try:
                value = coursedata.derived(name, h)
            except Exception:
                raise AttributeError(name) from None
            if value is None:
                raise AttributeError(name)
        cache[name] = value
        return value


_RUBRIC_VIEWS: dict = {}


def _rubric(form: int) -> _RubricView:
    """The view for one handout, built once."""
    if form not in _RUBRIC_VIEWS:
        _RUBRIC_VIEWS[form] = _RubricView(form)
    return _RUBRIC_VIEWS[form]


FORMS: dict[int, dict] = {
    1: {
        "rubric": _rubric(1),
        "template": f"{MATERIALS}/BMod Handout #1 - Defining Behaviors, ABCs, and SMART Goals.docx",
        "submissions": f"{SUBS}/Handout 1 Submissions with Scoring and Feedback",
        "markers": (),
        "capture_tail": False,
        "outdir": f"{OUT}/h1",
        "gold": _gold_loader(gold_mod.load_h1, 1),
        "blurb": (
            "Handout 1 of the Behavior Modification Assignment: defining behaviours, "
            "the ABCs of a functional behavioural analysis, and SMART goals."
        ),
        # Participants whose responses appear as few-shot exemplars in the
        # rubric, so scoring them would be self-grading.
        # p6 is an UNSTABLE exemplar and is kept as a diagnostic. Its whole
        # answer and its 6.25 are printed in Q6's prompt, and the scorer
        # reproduces that score in only 6 of 12 runs — unanimous one way in one
        # pass and the other way in the next. It is not a step-1 removal: taking
        # the citation out would mean deleting a worked example the prompt is
        # built around. Watch it while tuning Q6's slot judgements; it should
        # stop flipping when they stabilise, which reads independently of the
        # counted rate. See EQUIVALENCE.md, "Cleaning up an item".
        # EMPTY HERE, FOR THE REASON `cited_participants` BELOW IS. The merge
        # at the foot of this module overwrites this field from the course
        # file's `HANDOUT_FIELDS`, so the literal was a SHADOW: participant
        # numbers sitting in engine code that nothing reads. Student data does
        # not belong in python, and a copy nothing reads is the worst place for
        # it -- it cannot drift into disagreement loudly, only quietly.
        "exemplar_participants": [],
        # ...but only on the items whose PROMPT actually embeds them. Verified
        # against the rubric: Q6 is the sole item with an `exemplars` field, and
        # the three bodies reproduce p10, p8 and p6 verbatim. Their Q1..Q5
        # answers appear in no prompt, so dropping them there discarded 21 cells
        # for nothing. See exemplar_drops() below.
        # Empty since Q6 was rewritten from the dictionary: it no longer
        # reproduces anyone's answer, so no cell on it is self-graded. The
        # handout-wide `exemplar_participants` list above is now inert for
        # handout 1 and kept only so a future item can opt in by naming itself.
        "exemplar_items": [],
        # Participants whose response this handout's prompts CITE by number, per
        # item. Scoring a cited participant on that item is self-grading: the
        # prompt quotes the answer and states the grader's decision.
        #
        # EMPTY HERE ON PURPOSE, and the key is kept so the merge below fires.
        # The values are the COURSE FILE's -- `HANDOUT_FIELDS` -- and the 173
        # lines of evidence behind them, item by item, moved to sit beside that
        # table in `course_metadata_source.py` (E58 step 3, 2026-09-25). What
        # stood here was a shadow: the course file's value overwrites it at
        # import, so the reasoning was attached to the copy nobody reads.
        #
        # J-4c SAYS WHY IT MAY NOT HOLD THIS COURSE'S VALUES. A hardcoded
        # "documented default" does not come back empty for a course that
        # declares nothing -- it comes back as THIS COURSE'S.
        "cited_participants": {},
    },
    2: {
        "rubric": _rubric(2),
        "template": (
            f"{MATERIALS}/BMod Handout #2 - Learning Operant Conditioning and "
            "Applying It to Behavior Change.docx"
        ),
        "submissions": f"{SUBS}/Handout 2 Submissions with Scoring and Feedback",
        "markers": (),
        "capture_tail": True,
        "repair_orphans": True,
        "outdir": f"{OUT}/h2",
        "gold": _gold_loader(gold_mod.load_h2, 2),
        "blurb": (
            "Handout 2 of the Behavior Modification Assignment: applying the four types "
            "of operant conditioning to the student's own behaviour-change plan."
        ),
        "exemplar_participants": [],
        # Two participants have byte-identical transcriptions but different
        # gold rows, so at least one is mis-transcribed and neither can be
        # attributed. Excluded from reported metrics; see README.
        #
        # WHICH TWO IS THE COURSE FILE'S TO SAY, not this module's. The merge
        # below takes the value from `HANDOUT_FIELDS`; naming them here as well
        # put participant numbers in engine code for a copy that is overwritten
        # at import.
        "suspect_participants": [],
    },
    3: {
        "rubric": _rubric(3),
        "template": (
            f"{MATERIALS}/BMod Handout #3 - Presenting Data, Graphing Data, "
            "&amp_ Analyzing Your Intervention.docx"
        ),
        "submissions": f"{SUBS}/Handout 3 Submissions with Scoring and Feedback",
        "markers": (),
        "capture_tail": True,
        "join_aware": True,
        "outdir": f"{OUT}/h3",
        "gold": _gold_loader(gold_mod.load_h3, 3),
        "blurb": (
            "Handout 3 of the Behavior Modification Assignment: presenting and graphing "
            "the data collected during the intervention, and analysing the result."
        ),
        "exemplar_participants": [],
        # See handout 1's entry. 1c is also the item that cannot be scored at all
        # by a backend without image tools — a separate problem, declared in
        # BACKEND_DEVIATIONS below.
        # Empty, and measured empty. All eight of handout 3's registrations were
        # tested the way handout 1's 25 were: rewrite the citation as a rule, sweep
        # the item three times, compare the cited cell against its own cited
        # baseline. Not one survived, though two failed for a reason handout 1
        # never produced.
        #
        # 1a  p1  3/3 cited, and 6/6 uncited when probed with two controls that
        #         both held 6/6 — the 2/3 in the sweep was noise, not a loss.
        #     p15 3/3 -> 3/3. Unnecessary.
        #     p6  0/3 -> 0/3. Wrong with its own verdict in the prompt and wrong
        #         without it; the exclusion was buying a flattering denominator and
        #         nothing else. Counts as a miss now.
        # 1c  p8  2/3 -> 2/3, unchanged. An unchanged cell needs no probe: the
        #         comparison IS the answer.
        #     p4, p20  gold withdrawn by rebuild_declared_gold, so they leave the
        #         denominator on their own and never needed a citation to do it.
        # 2a  p1  1/3 -> 0/3 and p14 2/3 -> 0/3. These are the first two cells in
        #         33 tests whose citation was genuinely load-bearing — and they
        #         still go, because a citation that lifts a cell from wrong to
        #         wrong-slightly-less-often is measuring recall of an answer key,
        #         which is the whole reason this registry exists. Both count as
        #         misses. That makes 2a's known error shape (+2.0 for a second
        #         `how` gold withheld) visible in its rate instead of hidden
        #         behind two absent cells.
        #
        # Handout 3 counted cells: 51 of 60 -> 57 of 60. What is left out is only
        # 1c's p4, p19 and p20, all excluded on grounds that have nothing to do
        # with citations.
        "cited_participants": {},
    },
}


# The authored fields come from the course file, applied here rather than
# written into the table above so the DIFF stays readable: the table keeps its
# shape and each value's origin is stated in one place.
#
# `markers` NEEDED NO CHANGE, and the check that established it is worth keeping:
# this table takes them from `segment`, which already reads them from the course
# file, so the two were never separate copies -- they are the same object. A
# "duplicate" that is a shared reference is not a duplicate, and rewriting it
# would have added a second read path to replace a working one.
# The PATH fields are assembled, not overlaid. The course file stores a LEAF --
# `template_file`, `submissions_dir`, `outdir_name` -- and the base comes from
# `paths`, because the base says where THIS MACHINE keeps course data and the
# leaf is the course's own fact. A course file holding absolute paths could not
# survive $COURSE_DATA moving.
_PATH_FIELDS = {"template":    ("template_file",   MATERIALS),
                "submissions": ("submissions_dir", SUBS),
                "outdir":      ("outdir_name",     OUT)}

for _h, _cfg in FORMS.items():
    for _field in ("blurb", "capture_tail", "exemplar_items", "repair_orphans",
                   "join_aware", "exemplar_participants", "cited_participants",
                   "suspect_participants"):
        if _field in _cfg:
            _cfg[_field] = _course_field(_h, _field, _cfg[_field])
    for _field, (_key, _base) in _PATH_FIELDS.items():
        if _field in _cfg:
            _leaf = _course_field(_h, _key)
            # ABSENT LEAVES THE DEFAULT STANDING, and an empty one does too: a
            # course file that names no template has not asked for `{BASE}/`.
            if _leaf:
                _cfg[_field] = f"{_base}/{_leaf}"



# ── The COURSE FILE decides which handouts exist, and owns its own data ──────
# J-4b and J-4c, both found by running the engine as the stub course.
#
# J-4 moved every handout FIELD into the course file and left the table's KEYS
# as the literal 1, 2, 3, so `declared()` -- whose docstring says "every handout
# this course declares" -- answered for the ENGINE. A two-handout course got
# three, and `score.py --help` offered `--handout {1,2,3}` against it.
#
# J-4c is the worse half. The hardcoded values were kept as "documented
# defaults", which sounds conservative and is not: an UNDECLARED field did not
# come back empty, it came back as THIS COURSE'S. The stub -- which exists so
# that starting a project does not mean borrowing a real cohort -- resolved
# `submissions` to the real cohort's directory, and that path EXISTS, so nothing
# failed. A wrong answer, not an error.
#
# So a course-data field is ABSENT when the course does not declare it. The
# engine FLAGS keep their defaults: `capture_tail` is a fact about how the
# engine reads a document, not about whose course it is.
_COURSE_DATA_FIELDS = {
    "template":              "template_file",
    "submissions":           "submissions_dir",
    "outdir":                "outdir_name",
    "blurb":                 "blurb",
    "exemplar_participants": "exemplar_participants",
    "exemplar_items":        "exemplar_items",
    "cited_participants":    "cited_participants",
    "suspect_participants":  "suspect_participants",
}


# THROUGH THE ACCESSOR, not `_load()`. This read the raw document itself until
# `course_schema`'s Part B caught it: a raw entry defeats the group boundary
# while appearing to honour it, because the code still calls into `coursedata`.
# `coursedata.declared_forms()` was added there rather than exempting this
# module -- if no accessor exists for what you need, add one.
#
# Empty means THE READER CANNOT TELL, so the engine table is left alone --
# refusing to guess is not the same as deleting every handout.
import coursedata as _cd_fields

_DECLARED = _cd_fields.declared_forms()

def declared() -> tuple:
    """Which forms this course has, from the course's own declaration.

    THE ENGINE MUST NOT COUNT THEM. `(1, 2, 3)` was written out at 70 sites
    across 15 modules, plus three separate `HANDOUTS = (1, 2, 3)` constants --
    this course's shape, spelled inside machinery whose whole purpose is to know
    no course. `course.json` declares it and `coursedata.declared_forms()`
    reads it; exactly one module was calling that.

    IT REFUSES RATHER THAN RETURNING EMPTY, and that is the whole reason this
    exists instead of the accessor being called directly. `declared_forms()`
    answers `()` when it cannot tell, and `HANDOUTS` above is deliberately left
    alone in that case -- refusing to guess is not the same as deleting every
    form. But a LOOP handed `()` does not refuse; it runs zero times, finds
    nothing, and reports clean. Sixty-five loops silently examining nothing is a
    worse failure than a crash, and it is the exact shape this package keeps
    paying for: a check that reports zero because it never looked.
    """
    d = _DECLARED or tuple(sorted(FORMS))
    if not d:
        raise SystemExit(
            "forms.declared(): the course declares no forms and the engine "
            "table is empty, so there is nothing to iterate. Refusing rather "
            "than returning () -- a loop over () examines nothing and reports "
            "clean, which is indistinguishable from a corpus with no faults.")
    return tuple(d)

if _DECLARED:
    for _h in [h for h in FORMS if h not in _DECLARED]:
        del FORMS[_h]

# MARKERS, SET HERE RATHER THAN IN THE TABLE. Goal N moved these off the
# `H1/H2/H3_MARKERS` aliases onto `_markers(h)`, which reads the course file --
# but calling it INSIDE the literal made `migrated_tables` read `HANDOUTS` itself
# as a migrated table and demand an authored twin no builder holds. The reader
# call belongs in the assembly step, beside every other course-sourced field.
for _h, _cfg in FORMS.items():
    _cfg["markers"] = _markers(_h)

for _h, _cfg in FORMS.items():
    # WHICH KEYS THE COURSE DECLARED, not which values are truthy -- a course
    # that declares an empty exemplar list has ANSWERED, and must not be given
    # another course's list for it.
    _have = set(_cd_fields.declaration("HANDOUT_FIELDS").get(str(_h), {}))
    for _field, _key in _COURSE_DATA_FIELDS.items():
        if _field in _cfg and _key not in _have:
            _cfg[_field] = None

def declared() -> tuple:
    """Every handout this course declares, in order. J-3.

    The engine had no way to ask this: ten modules wrote `config(1)`,
    `config(2)` or the literal `(1, 2, 3)`, so a four-handout course met an
    engine that knew about three. `HANDOUTS` is the declaration; this is how to
    read it.
    """
    return tuple(sorted(FORMS))


def carrying(field: str) -> tuple:
    """The handouts whose items declare `field`, in order. J-3.

    Five of the hardcoded `config(2)` sites did not want HANDOUT TWO -- they
    wanted "the handout with the criteria items", which is handout 2 only in this
    course. Asking for the PROPERTY is what makes them portable, and it is the
    same move as `item.get("graph_item")` replacing `item == "1c"`.
    """
    import coursedata
    return tuple(sorted({int(it["handout"]) for it in coursedata.items()
                         if it.get("handout") is not None and it.get(field)}))


def config(form: int) -> dict:
    if form not in FORMS:
        raise SystemExit(f"unknown handout {form}; have {sorted(FORMS)}")
    return FORMS[form]


def find_submissions(form: int, pids: list[int] | None = None) -> list[tuple[int, str]]:
    cfg = config(form)
    out = []
    for f in sorted(glob.glob(os.path.join(cfg["submissions"], "*.docx"))):
        m = re.search(r"ID\s*(\d+)", os.path.basename(f))
        if not m:
            continue
        pid = int(m.group(1))
        if pids and pid not in pids:
            continue
        out.append((pid, f))
    return sorted(out)


def excluded(form: int) -> list[int]:
    """Participants that must not count toward a reported baseline.

    Handout-wide, exemplars included. Kept as-is for baseline.py, which measures
    score.py: that engine drops per RUN rather than per item, and its Q6 prompt
    carries the same exemplars, so narrowing here would silently make its
    reported baseline self-grading.
    """
    cfg = config(form)
    return sorted(
        set(cfg.get("exemplar_participants", [])) | set(cfg.get("suspect_participants", []))
    )


def suspect(form: int) -> list[int]:
    """Participants whose INPUT cannot be trusted, whatever the item.

    Handout 2's p2 and p3 have byte-identical transcriptions but different gold
    rows, so at least one is mis-transcribed and neither can be attributed. That
    is a fact about the submission, so it holds for every item — unlike being an
    exemplar, which is a fact about one prompt.
    """
    return sorted(config(form).get("suspect_participants", []) or [])


def exemplar_drops(form: int) -> dict[str, list[int]]:
    """{item: [pid]} — exemplar participants, only on items that embed them.

    Self-grading is a property of a PROMPT, not of a handout. Scoring p10, p8 or
    p6 on Q6 grades a model on text it was shown; scoring them on Q1 does not,
    because their Q1 answers appear nowhere in Q1's prompt. Conflating the two
    cost 3 participants x 7 items = 21 cells of handout-1 evidence.
    """
    cfg = config(form)
    out: dict[str, list[int]] = {}
    pids = sorted(cfg.get("exemplar_participants", []) or [])
    for item in cfg.get("exemplar_items", []) or []:
        if pids:
            out[item] = list(pids)
    # Per-item citations, merged rather than replacing: an item can both embed a
    # worked example and cite others as calibration.
    for item, cited in (cfg.get("cited_participants", {}) or {}).items():
        out[item] = sorted(set(out.get(item, [])) | set(cited or []))
    return out


# ── Deliberate divergences from gold ─────────────────────────────────────────
#
# Cells where the graders applied their OWN written rule inconsistently and both
# implementations apply it uniformly. These are decisions, not defects, and they
# were documented in README prose only — so every harness counted them as errors.
# That cost real conclusions: Q4a reads as one of handout 1's least accurate
# items at 80% exact / 92.8% per check, and is 94% / 98.0 once its three declared
# cells come out. And the DAY2 work was justified partly by "7 of 10 large errors
# are over-credit" when three of those were p8's declared avoidance-framing cells
# — the README says in terms, "anyone measuring the OC items should subtract them
# before concluding the criteria are too permissive."
#
# Distinct from three neighbouring ideas, all of which already exist:
#   olx_prompts.SCORING_DIVERGENCES  — where the WEB and CLI differ from each
#                                      other, not where either differs from gold
#   agreement.UNSCORED_GOLD_CRITERIA — criteria no slot scores at all
#   PER_ITEM_EXCLUDE                 — cells DROPPED, because nothing correct can
#                                      score them. A divergence is still scored;
#                                      we just knowingly disagree.
#
# CORRECTED 2026-09-07: THIS SAID Q6/9 AND Q1/20 ARE "also in PER_ITEM_EXCLUDE,
# so they never reach a comparison". Neither is, and both do. PER_ITEM_EXCLUDE
# has an EMPTY dict for Q6 and no Q1 key at all, and the ledger scores both cells
# -- Q6/p9 at 11 of 12, Q1/p20 perfect. Nor is either of them in the list below:
# its Q6 and Q1 entries are Q6/5, Q6/8 and Q1/9. So the sentence named the wrong
# cells AND asserted an exclusion that does not exist, which is the worst
# combination for a reader deciding whether a cell counts as evidence.
# What is true: every cell in this list is still SCORED, and a divergence records
# that we knowingly disagree with gold -- our answer is the endorsed one. That is
# the opposite of an exclusion, and reading it as one led to a proposal on
# 2026-09-07 to rescore Q6/p8 towards gold, against its own A_NO_CHANGE entry.
# Entries and their reasoning: `coursedata.gold_notes("GOLD_DIVERGENCES", key)` (281 lines).
GOLD_DIVERGENCES = _gold_declaration("GOLD_DIVERGENCES")


def gold_divergence(item: str, pid: int) -> str | None:
    """The divergence code for one cell, or None. See GOLD_DIVERGENCES."""
    for d in GOLD_DIVERGENCES:
        if (item, pid) in d["cells"]:
            return d["code"]
    return None


def gold_divergence_cells() -> dict[tuple[str, int], str]:
    """{(item, pid): code} for every declared cell."""
    return {c: d["code"] for d in GOLD_DIVERGENCES for c in d["cells"]}


# ── Measurement ceilings ─────────────────────────────────────────────────────
#
# Why no correct scorer reaches 100%, per item, with the evidence. A FOURTH kind
# of gold caveat, and the distinctions matter:
#
#   GOLD_DIVERGENCES         we disagree with a grader on purpose, on named cells
#   PER_ITEM_EXCLUDE         cells dropped, nothing correct can score them
#   agreement.UNSCORED_GOLD_CRITERIA
#                            criteria NO slot scores at all
#   GOLD_CEILINGS (here)     criteria that ARE scored, on cells gold itself does
#                            not decide consistently — so some are unwinnable
#                            whichever consistent rule you adopt, and which ones
#                            depends on the rule
#
# The practical use is to stop a ceiling reading as headroom. Q3 sits at 75% and
# looks like 25% of work available; about 10% of it does not exist.
#
# Q6 p4 was listed here and is NOT any more. Its gold of 6.00 implies 3.2 slots
# of 1.25, so no slot-derived score can land on it — but that is now HANDLED
# rather than merely explained: scores_as_exact() credits the nearest reachable
# value, so a scorer returning 6.25 is counted correct and the cell is neither a
# ceiling nor headroom. A note here would tell a reader there is unwinnable
# ground where there is none.
#
# Contrast DAY2 p7 below, which stays. Its gold of 1.00 IS reachable; it just
# does not reconcile with its own itemised comment. Nothing computes that away,
# so it remains a real ceiling.
# Entries and their reasoning: `coursedata.gold_notes("GOLD_CEILINGS", key)` (47 lines).
GOLD_CEILINGS = _gold_declaration("GOLD_CEILINGS")


def gold_ceiling(form: int, item: str) -> tuple[str, ...]:
    """Why this item cannot reach 100% — one entry per ceiling, () if none.

    A tuple rather than a string because an item can hit more than one ceiling
    for unrelated reasons: Q2 has both `reasons_given` (an uncountable
    distinctness judgement) and `wgb_inverts_utb` (substitution vs outcome
    decided both ways). Joined into one string, every caller's summary line
    would show the first and silently drop the rest.
    """
    got = GOLD_CEILINGS.get((str(form), item)) or ()
    return (got,) if isinstance(got, str) else tuple(got)


# Gold criteria that neither system scores, declared rather than left to be
# rediscovered. An omission that is SYMMETRIC costs the head-to-head nothing —
# both columns miss it identically — but an undeclared one is indistinguishable
# from a bug, which is the whole reason this list exists.
#
#   1c, "missing baseline data week" (p11, -1): the only instance in 20 rows,
#   and unreachable on the web by construction. The chart is drawn by
#   SelfMonitorPlot from the four data fields, so a populated baseline series is
#   necessarily plotted — p11's `baseline` field holds "{{corpus:1a/p6:baseline:0:19:sha=66e4f9120272}} 30",
#   which is why their 1b scored a full 4.0. The grader is marking a series
#   absent from a hand-drawn paper graph whose data table contained it. Adding a
#   slot for it would have no reachable failing state: with baseline data present
#   the web always plots it, and with baseline data absent 1b already takes the
#   point, so the slot could only double-count or misfire. Note also that p11's
#   row does not self-reconcile — it itemises -2/-2/-1 against a score of 7.0 —
#   so rebuild_declared_gold derives from the itemised deductions, not the total.
# Cells where the gold row cannot be scored on the item it sits in, dropped from
# that item only. Mirrors PER_ITEM_EXCLUDE in agreement_app.py; the two sides
# must drop the SAME cells or the item's two columns stop being a comparison.
# Entries and their reasoning: `coursedata.gold_notes("PER_ITEM_EXCLUDE", key)` (75 lines).
PER_ITEM_EXCLUDE = _gold_declaration("PER_ITEM_EXCLUDE")


# ── One place that answers "is this cell counted?" ──────────────────────────
#
# Three reasons a cell is not counted, and they mean DIFFERENT things when the
# model gets one wrong, which is why the kind travels with the pid:
#
#   suspect      the SUBMISSION cannot be trusted (mis-transcribed), so the
#                input is not what the student wrote. A miss says nothing.
#   self_graded  the PROMPT contains this participant's answer and the grader's
#                decision. A miss here is a RED FLAG: the answer was supplied
#                and the model missed it anyway.
#   unscoreable  the GOLD ROW cannot be reproduced by any correct scorer. A miss
#                is EXPECTED — the documented behaviour, not a defect.
#
# All three harnesses must read this, or their rates are computed over different
# denominators and the columns stop being a comparison. Not theoretical: the
# table above lived in agreement.py and agreement_app.py as two hand-kept mirrors
# and in baseline.py not at all, so the paper scorer counted five cells the other
# two dropped.

EXCLUSION_KINDS = ("suspect", "self_graded", "unscoreable")


def unscoreable(item: str) -> dict[int, str]:
    """{pid: why} — cells whose gold no correct scorer can reach."""
    return {pid: (e["why"] if isinstance(e, dict) else e)
            for pid, e in PER_ITEM_EXCLUDE.get(item, {}).items()}


def unscoreable_expectation(item: str) -> dict[int, float]:
    """{pid: pred - gold} for unscoreable cells that declare what the miss IS.

    An `unscoreable` reason says a correct scorer CANNOT reach the gold, which is
    a claim about a number. Left in prose that number goes stale without anything
    noticing: Q6's p9 asserted "the CLI's error here is exactly -2.50" while every
    run measured -1.25, and the sentence went on pointing future work at the
    fixture reconstruction when the whole story was a declared divergence.

    Declaring it here makes it an assertion the harnesses check on every run, so
    the cell either behaves as documented or says so.
    """
    return {pid: float(e["expect_error"])
            for pid, e in PER_ITEM_EXCLUDE.get(item, {}).items()
            if isinstance(e, dict) and e.get("expect_error") is not None}


def scored_exactly(item_id: str, gold: float, pred: float) -> bool:
    """Did this cell score exactly right, by ITEM ID rather than rubric record?

    The same decision as `scores_as_exact`, reachable from the places that have
    an item id and a number and nothing else — which turned out to be most of
    them. Every rate in this project is a count of cells that "scored exactly
    right", and that phrase had SIX implementations: two called
    `scores_as_exact`, and four re-derived it as `abs(pred - gold) < 1e-9`. The
    four included the ALL aggregate on both the CLI and paper harnesses and, worse,
    the median-run SELECTOR — so the run chosen for publication was picked by a
    rule the published table then disagreed with. One table printed 67% and 58%
    for the same twelve cells.

    `check_unreachable_gold_is_allowed` did not catch it: it tested that the
    string "scores_as_exact" appeared in each file, and it did — in the one code
    path that used it.
    """
    for h in declared():
        rec = config(h)["rubric"].BY_ID.get(item_id)
        if rec is not None:
            return scores_as_exact(rec, gold, pred)
    raise KeyError(f"no rubric item {item_id!r} in any handout")


def stale_claim(item: str, pid: int, gold: float, pred: float) -> str | None:
    """The warning line for a cell that stopped behaving as its exclusion says.

    Lives here rather than in the three reporters because they are three copies
    of one block already — the same mirror-keeping this module exists to end.
    """
    want = unscoreable_expectation(item).get(pid)
    if want is None or abs((pred - gold) - want) < 1e-9:
        return None
    return (f"<-- CLAIM STALE: declared expect_error={want:+.2f}, measured "
            f"{pred - gold:+.2f}. Fix the reason in "
            f"handouts.PER_ITEM_EXCLUDE or the exclusion")


def cell_exclusions(form: int, item: str) -> dict[int, tuple[str, str]]:
    """{pid: (kind, why)} for one item — every cell that must not be COUNTED.

    Not a work list. Excluded cells are still RUN and still scored: whether the
    model gets them right is evidence in its own right, and suppressing the call
    threw that evidence away. Only the RATE excludes them.
    """
    out: dict[int, tuple[str, str]] = {}
    for pid in suspect(form):
        out[pid] = ("suspect", "mis-transcribed submission; the input is not "
                               "what the student wrote")
    for pid in exemplar_drops(form).get(item, []):
        out[pid] = ("self_graded", "this item's prompt contains their response "
                                   "and the grader's decision")
    for pid, why in unscoreable(item).items():
        out[pid] = ("unscoreable", why)
    return out


# ── Items a backend cannot score at all ─────────────────────────────────────

def not_comparable_items(form: int, supports_tools: bool) -> dict[str, str]:
    """{item: why} — items the PAPER scorer cannot score from this backend.

    Scoped to score.py, and only baseline.py consults it. The web and CLI are
    NOT affected and must not be filtered by this: they never look at an image.
    1c on those sides is scored from the four weeks of data the student typed,
    through `derived="has_own_graph:complete:..."` in the OLX, and web_v8 scores
    it 16/17 with no tool involved. It is score.py's handout-3 prompt that asks
    the model to Read the graph as an IMAGE, because on paper a graph is a
    picture — so the deviation belongs to that prompt, not to the item.

    COMPUTED from the rubric rather than listed, so it cannot go stale: score.py
    passes `allow_tools=["Read"]` for exactly the items flagged `graph_item`, and
    a backend that does not forward tools scores those blind. Blind on a graph
    item is not noise, it is a systematic zero — the model reports no graph
    because it cannot see one.

    Observed, not hypothesised: paper+gpt-5-mini returned 0.00 on 11 of 20 cells
    of 1c where gold is 6-10, against paper+Opus scoring the same cells correctly
    through the Read tool. Reporting that as 5/17 would publish a missing tool as
    a model deficiency.

    Excluded from the RATE and reported as not comparable — a different thing
    from cell_exclusions(), which drops individual cells of an item that is
    otherwise fine.
    """
    if supports_tools:
        return {}
    return {
        it["id"]: ("needs an image tool to read the student's graph; this backend "
                   "sends no tools, so the item scores blind and returns 'no graph'")
        for it in config(form)["rubric"].ITEMS
        if it.get("graph_item")
    }


# ── Scores gold asks for that the item cannot produce ────────────────────────

def attainable_scores(item: dict) -> list[float]:
    """Every score this item can actually produce.

    A score is max minus the sum of some subset of the scorable components,
    clamped at 0, plus 0 itself where a gate can take the whole item. Computed
    from the rubric rather than listed, so an item whose point values change
    cannot leave a stale table behind.
    """
    from itertools import combinations
    pts = [c["pts"] for c in item["credit"]
           if not c.get("reported") and c.get("pts") is not None]
    out = {float(item["max"])}
    for r in range(1, len(pts) + 1):
        for combo in combinations(pts, r):
            out.add(max(0.0, round(item["max"] - sum(combo), 4)))
    if any(c.get("gates") for c in item["credit"]):
        out.add(0.0)
    return sorted(out)


def _scored_credit(item: dict) -> list[dict]:
    """The credit slots that carry points, in authored order.

    `series_box_holds` carries none -- it is a PICK that the `legend` slot's rule
    reads, not a slot that scores -- so a reader counting "every credit entry"
    would invent a sixth 2-point element that does not exist.
    """
    return [c for c in item.get("credit", ()) if c.get("pts") is not None]


def gold_labels(item: dict, feedback: str) -> dict[str, bool]:
    """The grader's verdict on each of `item`'s scored slots, from their comment.

    A MISSING MENTION MEANS THE CRITERION PASSED: these graders itemise what they
    took off and leave the cell blank at full credit, so the absence of "-2 pts:
    missing legend" is evidence the legend was there.

    The slots, their point values, the gate and the deduction codes all come from
    the RUBRIC; only the phrases come from `GOLD_COMMENT_PHRASES`, and a code the
    rubric declares with no phrase here is a REFUSAL rather than a slot that
    quietly never fails. Both previous copies hard-coded five keys, so a sixth
    element added to the rubric would have been ignored by both without a word.
    """
    import coursedata

    phrases = coursedata.declaration("GOLD_COMMENT_PHRASES")
    f = " ".join((feedback or "").lower().split())
    out, gate_ok = {}, True
    for slot in _scored_credit(item):
        codes = [c for c in (slot.get("codes") or {}).values()]
        missing = [c for c in codes if c not in phrases]
        if missing:
            raise SystemExit(
                f"handouts.gold_labels: {item['id']} slot {slot.get('what')!r} "
                f"maps to deduction code(s) {sorted(set(missing))}, which "
                f"GOLD_COMMENT_PHRASES does not know how to find in a comment. "
                f"Add the phrase graders write for it -- an unknown code would "
                f"otherwise read as 'this element never fails'.")
        hit = any(re.search(pat, f)
                  for c in codes for pat in phrases[c])
        ok = not hit
        if slot.get("gates"):
            gate_ok = ok
        out[str(slot.get("what"))] = ok
    if not gate_ok:
        # On a failed gate nothing else was assessed, so the rest ride on it --
        # which is what a gate means anyway.
        out = {k: False for k in out}
    return out


def rebuild_gold_from_comment(gold: dict, item: dict) -> tuple[dict, list[int]]:
    """Restate an item's gold from the grader's itemised deductions.

    WHY THE RAW SCORE CANNOT BE USED for 1c, the only item that needs this:
    p11's row reads `-2 x-axis -2 y-axis -1 missing baseline data week` against a
    score of 7.0, which is neither 10-4 nor 10-5, and the baseline-week point maps
    to no slot on either side. Rebuilding from the verdicts drops that improvised
    charge cleanly, where subtracting from the total could not.

    ONE IMPLEMENTATION, replacing two. `agreement.py` and `agreement_app.py` each
    held a copy under a comment saying "the two must agree" with nothing
    enforcing it, and by 2026-09-23 they had drifted apart in one way that
    mattered: `agreement_app` matched "missing (the )?legend" while `agreement`
    matched only the short form. It was invisible because no comment in the
    corpus says "missing the legend" -- the divergence was real and simply had
    not been reached yet.

    NOT everything that looked like drift was drift, and the difference is worth
    recording. Their exclusion sources -- `GRAPH_UNREACHABLE_1C` and
    `PER_ITEM_EXCLUDE["1c"]` -- read as two tables agreeing by luck, but
    `agreement.py` DERIVES the first from the second ("not repeated, so the two
    drops cannot disagree"): already fixed, by someone who had met this before.
    The slot-name difference (`x_axis_label` vs `x`) was cosmetic, since the
    rebuild only counts falses. One real divergence, not three.

    The arithmetic now comes from the rubric -- `max` and each slot's own `pts` --
    so it cannot drift from the sheet it is meant to mirror either.
    """
    unreachable = set(PER_ITEM_EXCLUDE.get(item["id"], {}))
    dropped: list[int] = []
    for pid, items in gold.items():
        cell = items.get(item["id"])
        if not cell:
            continue
        if pid in unreachable:
            items[item["id"]] = {"score": None, "feedback": cell.get("feedback", "")}
            dropped.append(pid)
            continue
        labels = gold_labels(item, cell.get("feedback"))
        gate = next((c for c in _scored_credit(item) if c.get("gates")), None)
        if gate is not None and not labels[str(gate.get("what"))]:
            score = 0.0
        else:
            lost = sum(float(c["pts"]) for c in _scored_credit(item)
                       if not labels[str(c.get("what"))])
            score = round(float(item["max"]) - lost, 4)
        items[item["id"]] = {"score": score, "feedback": cell.get("feedback", "")}
    return gold, sorted(dropped)


def rebuild_declared_gold(gold: dict, form: int) -> tuple[dict, list[int]]:
    """Rebuild every item in `handout` whose RUBRIC declares `gold_from_deductions`.

    The item-agnostic entry point, and the reason the flag exists. Which items
    need their gold rebuilt is a property OF THE ITEM -- p11's 1c row itemises
    -2/-2/-1 against a recorded 7.0, so the total cannot be trusted and the
    verdicts can -- and an item property belongs on the item, not in a lookup
    written into two analytic modules.

    Today exactly one item declares it. That is not an argument for hard-coding
    that item: a general rule fires for content written later and a specific one
    never does, which is the principle that retired `gold_slots_q6.py`.
    """
    dropped: list[int] = []
    for item in config(form)["rubric"].ITEMS:
        if not item.get("gold_from_deductions"):
            continue
        gold, d = rebuild_gold_from_comment(gold, item)
        dropped.extend(d)
    return gold, sorted(set(dropped))


def rebuilds_gold(item_id: str) -> bool:
    """Does this item's RUBRIC declare `gold_from_deductions`?

    THE PREDICATE THE CALLERS WERE MISSING. `rebuild_declared_gold` above is
    item-agnostic and has been since it was written -- "an item property belongs
    on the item, not in a lookup written into two analytic modules" -- but the
    callers that decide WHETHER to call it were still asking `if item == "1c"`.
    Nine of them, across `measured`, `compare_runs` and `cross_path`. The
    general rule existed and the specific one was still being consulted.

    Subgoal E58, 2026-09-25. Exactly one item declares the flag today, so every
    conversion is inert -- and that is the argument FOR it, not against: a
    general rule fires for content written later and a specific one never does,
    which is the principle that retired `gold_slots_q6.py`.

    DELIBERATELY NOT "and then rebuild". Several of these call sites rebuild and
    several skip a computation instead, and one -- `measured`'s implied-charge
    inference -- must skip precisely BECAUSE the rebuild overrides the row. They
    share the question, not the answer.
    """
    import coursedata

    for it in coursedata.items():
        if str(it.get("id")) == str(item_id):
            return bool(it.get("gold_from_deductions"))
    return False


def nearest_attainable(item: dict, gold: float) -> set[float]:
    """The reachable score(s) closest to `gold` — the whole tie, if it is one.

    Empty when gold is itself reachable, which is the ordinary case: only one
    cell in the corpus is not (Q6 p4, whose 6.00 implies 3.2 slots of 1.25).
    """
    scores = attainable_scores(item)
    if any(abs(gold - a) < 1e-9 for a in scores):
        return set()
    best = min(abs(gold - a) for a in scores)
    return {a for a in scores if abs(abs(gold - a) - best) < 1e-9}


def scores_as_exact(item: dict, gold: float, pred: float) -> bool:
    """Does `pred` count as exact against `gold`?

    Normally that means equality. But where gold names a score the item CANNOT
    produce, the closest reachable value is the best any correct scorer can do,
    and penalising it measures the rubric's arithmetic rather than the scorer's
    judgement. Q6 p4 asks for 6.00 from an item that moves in steps of 1.25; a
    scorer returning 6.25 has done everything right.

    Deliberately not a tolerance. Only an UNREACHABLE gold opens the allowance,
    and only to the nearest reachable value(s) — a cell whose gold is reachable
    is still judged on equality, so this cannot quietly forgive a near miss.
    """
    if abs(pred - gold) < 1e-9:
        return True
    return pred in nearest_attainable(item, gold)
