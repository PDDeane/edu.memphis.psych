#!/usr/bin/env python3
"""Does every native assembler actually READ the source it claims to?

SIBLING OF `injection_reach.py`, AND A DIFFERENT QUESTION.
    injection_reach : does every ported check SEE its self-test injection?
    assembler_reach : does an assembler's payload MOVE when its source changes?

WHY IT EXISTS. Rules asked with a null payload have no python assembly left --
the runner builds it. GOALS.md E63 required the comparison against python's
payload "BEFORE ANY PYTHON IS DELETED", and for rules that were self-assembling
from the start there never WAS a python payload, so that comparison was not
skipped: it was impossible. What remains provable is weaker and still worth
having -- that the assembler READS ITS SOURCE. A payload that does not move
when its source is mutated is not reading it.

WHY IT IS NOT A SELF-TEST CASE. These injections are ON DISK, and
`equivalence._DISK_CASES` records the cost: a disk case cannot overlap a forked
audit, must be declared in advance, and forces an `_audit_drain()` barrier. The
self-test runs in PARALLEL and takes ~20 minutes; adding a barrier per
assembler would serialise it into hours. So this runs SEPARATELY and SERIALLY.

WHAT IT PROVES, AND WHAT IT DOES NOT.
    PROVES     the assembler reads the source it names.
    DOES NOT   prove it reads it CORRECTLY. That was E63's payload comparison,
               and for rules whose python half is gone it cannot be rebuilt.
               A green run here must not be read as more than it is.
"""

import json
import os
import re
import shutil
import sys

# THE PACKAGE DIRECTORY, not this one. `tools/` is a subdirectory; `paths.py`
# and the rest of the engine live one level up, and `paths` in turn is what puts
# the general-scorer directory on sys.path. injection_reach.py opens the same
# way for the same reason.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _allowed_roots() -> tuple:
    """The trees this tool may write to, RESOLVED rather than spelled.

    An earlier version named an absolute path here and the audit refused it, on
    the rule that no module spells a filesystem location. It was right twice
    over: `paths` already knows both trees, and a spelled ancestor would have
    permitted writes anywhere beneath it -- including a sibling checkout -- while
    what this tool may touch is exactly the engine repo and its lo-blocks.
    """
    import paths

    return (os.path.realpath(str(paths.REPO)), os.path.realpath(str(paths.LO)))


def _guard_path(path: str) -> str:
    """Refuse any write outside the trees `paths` resolves.

    Checked on every write rather than inferred from the cwd: this tool edits
    real files, and the one failure that must never happen is editing another
    checkout because it was invoked from the wrong directory.
    """
    real = os.path.realpath(path)
    roots = _allowed_roots()
    if not any(real == r or real.startswith(r + os.sep) for r in roots):
        raise SystemExit(f"assembler_reach: refusing to touch {real} -- "
                         f"outside {' and '.join(roots)}")
    return real


class Mutation:
    """One edit to one file, with the ORIGINAL MTIME restored.

    RESTORING BYTES IS NOT RESTORING THE FILE. Identical content with a NEW
    mtime makes the build-staleness gates fire, and `every_sweep_is_recorded`
    -- a rule this tool can cover -- compares mtimes DIRECTLY. A tool that left
    mtimes moved would manufacture the staleness it exists to detect.
    """

    def __init__(self, path: str, transform):
        self.path = _guard_path(path)
        self.transform = transform
        self.backup = self.path + ".assembler_reach.bak"
        self.stat = None

    def __enter__(self):
        self.stat = os.stat(self.path)
        shutil.copy2(self.path, self.backup)
        with open(self.path, encoding="utf8") as fh:
            src = fh.read()
        new = self.transform(src)
        if new == src:
            os.remove(self.backup)
            raise SystemExit(f"assembler_reach: the mutation changed nothing in "
                             f"{self.path}; the case proves nothing as written")
        with open(self.path, "w", encoding="utf8") as fh:
            fh.write(new)
        return self

    def __exit__(self, *exc):
        # ORDER MATTERS: restore, VERIFY AGAINST THE BACKUP, then delete it. An
        # earlier draft removed the backup first and then read it, which would
        # have thrown inside the cleanup path -- the worst place to fail while
        # holding a mutated tree.
        shutil.copy2(self.backup, self.path)
        os.utime(self.path, (self.stat.st_atime, self.stat.st_mtime))
        with open(self.path, encoding="utf8") as fh:
            restored = fh.read()
        with open(self.backup, encoding="utf8") as fh:
            original = fh.read()
        if restored != original:
            raise SystemExit(f"assembler_reach: {self.path} was NOT restored; "
                             f"the backup is KEPT at {self.backup}")
        if os.stat(self.path).st_mtime != self.stat.st_mtime:
            raise SystemExit(f"assembler_reach: {self.path} content restored but "
                             f"its MTIME moved; backup KEPT at {self.backup}")
        os.remove(self.backup)
        return False


def _recover(paths_to_check) -> list:
    """Restore anything a KILLED earlier run left mutated, before doing anything.

    `Mutation.__exit__` restores on exceptions, but it cannot run at all if the
    process is killed -- a timeout, a Ctrl-C, an OOM. THAT IS NOT HYPOTHETICAL:
    a throwaway coverage probe with the same `finally` shape was killed by a
    two-minute timeout on 2026-09-28 and left the authored rubric mutated with
    its backup beside it. The tree was recovered by hand from that backup.

    So the backup file is the RECOVERY RECORD, not just an implementation
    detail: if one exists at startup, a previous run died holding a mutation,
    and the right first act is to put the file back -- mtime included, since the
    backup was copied with metadata.
    """
    restored = []
    for path in paths_to_check:
        bak = path + ".assembler_reach.bak"
        if os.path.exists(bak):
            st = os.stat(bak)
            shutil.copy2(bak, path)
            os.utime(path, (st.st_atime, st.st_mtime))
            os.remove(bak)
            restored.append(path)
    return restored


def _assemble(rule: str, ns: str):
    """Assemble `rule`'s payload in a COLD runner.

    THE BRIDGE REUSES ONE NODE SERVER -- "started on first use and reused" --
    and several readers memoise at module scope: `archive.ts` caches the ledger
    and every runs document it opens. So a payload read after a mutation can be
    served from a cache populated BEFORE it, and the assembler looks like it is
    not reading its source when in fact this tool never let it.

    MEASURED: `every_sweep_is_recorded` reported DID NOT MOVE with its artifact
    mutated in three different ways, until the server was restarted between
    reads. `sheet_matches_rubric` moved throughout, because rubricSource does
    not memoise -- which is exactly how a cache-shaped blindness hides: it
    afflicts some rules and not others, and the ones it spares look like proof
    the tool works.

    Restarting costs a process start per read. That is the price of the answer
    meaning anything.
    """
    import lo_enforce

    lo_enforce._stop_server()
    return lo_enforce.probe("assemble", {"rule": rule, "ns": ns})


def _drop_first_slot(src: str) -> str:
    import re
    m = re.search(r"\n\s*<Slot\b[^>]*/>", src)
    return src.replace(m.group(0), "", 1) if m else src


def _break_one_artifact_program(src: str) -> str:
    """Make one recorded cell unrecognisable to `artifactProgram`.

    THE MUTATION HAS TO MOVE WHAT THE PAYLOAD IS BUILT FROM, which for
    `every_sweep_is_recorded` is the ARCHIVE, not the rubric. Its rows carry an
    `inspected` count -- candidates whose program is admissible for that column
    -- and `artifactProgram` decides that by the KEY a result is stored under.
    Renaming `cell` makes this artifact unattributable, so the count moves.
    """
    # EVERY occurrence, not the first. `artifactProgram` returns on the FIRST
    # result it can classify, so renaming one key leaves the next result still
    # identifying the file and the payload does not move -- which is exactly
    # what this tool reported when the case was written that way.
    return src.replace('"cell"', '"cell_broken"')


def _cases():
    """(rule, path, transform). Each must mutate THE SOURCE THAT RULE READS.

    A case is not "change any file": it has to change the file this assembler
    derives its payload from, or a green result means nothing.
    """
    import rubric_component as RC

    # THE MUTATION MUST CHANGE WHAT THE PAYLOAD DEPENDS ON -- not merely the
    # file the assembler opens. Learned by measurement here, twice over:
    #
    #   1. The first cases named the STAGED rubric for all three rules. Two did
    #      not move, because most assemblers read the AUTHORED file through
    #      `rubricPath(ns)`; only `sheet_matches_rubric` reads the staged copy.
    #   2. Pointed at the authored file, the SAME two still did not move -- and
    #      that was right. Dropping a `<Slot>` does not change item IDs, which
    #      is all `rubric_items_are_unique` looks at, nor the prose-only tally
    #      `prose_only_slots_are_declared` counts. The file changed; their
    #      inputs did not.
    #
    # So a case is THREE things, and the third is the one that is easy to miss:
    # the right rule, the right FILE, and a mutation that moves the part of that
    # file the rule's payload is built from. A case that satisfies the first two
    # and fails the third reports a blind assembler that is not blind, which
    # would train a reader to ignore this tool.
    #
    # Cases are therefore added ONE AT A TIME, each shown to move before it is
    # committed, rather than generated in bulk from a file list.
    import glob
    import paths as _p

    staged = RC.staged_path()
    cases = [
        # SLOT KEYS ARE LITERALLY THIS RULE'S SUBJECT: it compares the sheet's
        # keys against the staged rubric's, so removing one must move it.
        ("sheet_matches_rubric", staged, _drop_first_slot),
    ]
    # A DIFFERENT SOURCE ENTIRELY: this rule reads the RUN ARCHIVE. Any recorded
    # artifact will do, so take the first by name rather than naming one -- a
    # case that hard-codes an artifact goes stale the next time the archive is
    # rebuilt, and then reports a blind assembler that is not blind.
    # THE ARTIFACT HAS TO BE ONE THE PAYLOAD ACTUALLY READS, and that took
    # three refusals from this tool to get right. The rows are built per JOB
    # ITEM and match candidates by basename, so an artifact is only counted when
    # it is named `<item>.runs.json` for an item in JOBS. The first pick was
    # `_refold_NP/NP.runs.json`, which has no `cell` key at all -- refused for
    # changing nothing. The second was `c1move/web.runs.json`: it HAS the key,
    # the mutation applied cleanly, and the payload still did not move, because
    # `web` is not a job item and nothing ever reads that file.
    #
    # Each refusal was the tool working. A case that mutates a file the payload
    # never opens proves nothing, and would have been recorded as coverage.
    import measured as _M

    job_items = set(_M._jobs())
    for cand in sorted(glob.glob(os.path.join(str(_p.OUT), "*", "*.runs.json"))):
        item = os.path.basename(cand)[: -len(".runs.json")]
        if item not in job_items:
            continue
        try:
            if '"cell"' in open(cand, encoding="utf8").read():
                cases.append(("every_sweep_is_recorded", cand,
                              _break_one_artifact_program))
                break
        except OSError:
            continue
    return cases


def _cleared_rules() -> set:
    """The rules lo-blocks has cleared for self-assembly.

    STRIP `//` COMMENT LINES BEFORE SCRAPING. The block carries prose, and that
    prose quotes identifiers: a scan that did not strip comments once read the
    SLOT KEY `link_c2` out of a comment and reported it as a cleared rule with
    no assembler -- a defect that did not exist.
    """
    import paths

    src = (paths.LO / "packages/shared/lib/llm/enforce/native.ts").read_text(
        encoding="utf8")
    m = re.search(r"SELF_ASSEMBLING[^=]*=\s*new Set\(\[(.*?)\n\]\)", src, re.S)
    if not m:
        raise SystemExit("assembler_reach: SELF_ASSEMBLING not found in native.ts")
    code = "\n".join(l for l in m.group(1).splitlines()
                     if not l.strip().startswith("//"))
    return set(re.findall(r"'([a-z_0-9]+)'", code))


def _budget_path():
    import paths

    return paths.SCORING / "metadata" / "ASSEMBLER_REACH_BUDGET.json"


def _check_budget(covered: set) -> list:
    """Uncovered cleared rules may only DECREASE.

    A RATCHET, not a pass/fail line (QUALITY_CONTROL §5: every declaration table
    needs one, or its entries outlive their reason). 74 of 75 cleared rules have
    no case today, and failing on that would put the tool straight into the set
    of things people switch off. What must not happen is the number GROWING: a
    rule cleared for self-assembly from now on arrives with a case, or the
    budget refuses it.
    """
    cleared = _cleared_rules()
    uncovered = sorted(cleared - covered)
    path = _budget_path()
    try:
        budget = json.loads(path.read_text(encoding="utf8"))["uncovered"]
    except Exception:
        budget = None
    out = []
    if budget is None:
        path.write_text(json.dumps({"uncovered": len(uncovered),
                                    "rules": uncovered}, indent=1) + "\n",
                        encoding="utf8")
        print(f"  budget written: {len(uncovered)} cleared rule(s) without a case")
    elif len(uncovered) > budget:
        new = sorted(set(uncovered) - set(json.loads(
            path.read_text(encoding="utf8")).get("rules", [])))
        out.append(
            f"{len(uncovered)} cleared rule(s) have no assembler-reach case, up "
            f"from {budget}. A rule cleared for self-assembly must arrive with a "
            f"case showing its assembler reads its source: {', '.join(new) or '?'}")
    elif len(uncovered) < budget:
        path.write_text(json.dumps({"uncovered": len(uncovered),
                                    "rules": uncovered}, indent=1) + "\n",
                        encoding="utf8")
        print(f"  budget TIGHTENED: {budget} -> {len(uncovered)} uncovered")
    print(f"  coverage: {len(covered)} of {len(cleared)} cleared rule(s) have a case")
    return out


def _cold() -> None:
    """Drop the bridge's node server so the next read repopulates its caches."""
    import lo_enforce

    lo_enforce._stop_server()


def _assemble_nocold(rule: str, ns: str):
    import lo_enforce

    return lo_enforce.probe("assemble", {"rule": rule, "ns": ns})


def _mutations() -> list:
    """(name, path, transform) -- each aimed at ONE SOURCE an assembler reads.

    Measured coverage on this corpus, 2026-09-28, which is why these and not
    others: item-id 38 rules, declarations 29, action-id 20, slots-attr 11,
    drop-slot 3, staged drop-slot 2, first-declaration 3, archive 1, composed 1.
    """
    import glob

    import measured as _M
    import paths as _pp
    import rubric_component as _RC

    sys.path.insert(0, str(_pp.REPO / "scorers"))
    import agreement as _A

    authored, staged = _RC.authored_path(), _RC.staged_path()
    handout = os.path.join(_A.OLX_DIR, _pp.handout_olx(1))
    course = str(_pp.roots().rubric_dir / "course.json")
    composed = sorted(glob.glob(str(_pp.roots().rubric_dir / "derived" / "composed" / "*.md")))
    jobs = set(_M._jobs())
    artifact = None
    for c in sorted(glob.glob(os.path.join(str(_pp.OUT), "*", "*.runs.json"))):
        if os.path.basename(c)[: -len(".runs.json")] in jobs:
            if '"cell"' in open(c, encoding="utf8").read():
                artifact = c
                break

    def _decls(src):
        d = json.loads(src)
        decl = d.get("declarations")
        if not isinstance(decl, dict):
            return src
        d["declarations"] = {("ZZ" + k): v for k, v in decl.items()}
        return json.dumps(d, indent=1)

    return [
        ("rubric-authored:item-id", authored,
         lambda x: re.sub(r'(<Item\b[^>]*\bscores=")([^"]+)(")', r"\1ZZ\2\3", x, count=1)),
        ("rubric-authored:drop-slot", authored,
         lambda x: re.sub(r"\n[ \t]*<Slot\b[^>]*/>", "", x, count=1)),
        ("rubric-staged:drop-slot", staged,
         lambda x: re.sub(r"\n[ \t]*<Slot\b[^>]*/>", "", x, count=1)),
        ("handout-olx:action-id", handout,
         lambda x: re.sub(r'(<LLMAction\b[^>]*\bid=")([^"]+)(")', r"\1ZZ\2\3", x, count=1)),
        ("handout-olx:slots-attr", handout,
         lambda x: re.sub(r'(slots=")([^"]+)(")', r"\1zzz:\2\3", x, count=1)),
        ("course-json:declarations", course, _decls),
        ("composed-doc:first-heading", composed[0] if composed else None,
         lambda x: x.replace("\n#", "\nZZ#", 1)),
        ("archive:break-program", artifact,
         lambda x: x.replace('"cell"', '"cell_broken"')),
    ]


def _sweep_all(ns: str) -> tuple:
    """Run every mutation once and collect which cleared rules MOVED.

    COVERAGE IS MUTATION-DRIVEN, NOT CASE-DRIVEN, and that is the whole design.
    Writing one case per rule was the first plan and it does not scale: 77 rules
    would be 77 bespoke mutations, each needing the right file AND a change that
    moves what that payload is built from. Measured instead, a handful of
    mutations cover most of the corpus at once -- renaming one `<Item scores=>`
    in the authored rubric moved 38 rules; renaming every key under
    `declarations` in course.json moved 29; renaming one `<LLMAction id=>`
    moved 20.
    
    So a MUTATION is the unit that is written by hand, and coverage is derived.
    Each read is COLD -- the bridge reuses one node server and archive.ts
    memoises -- so the restart happens once per mutation rather than once per
    rule, which is ~77x cheaper and still correct: the cache is populated after
    the mutation, not before it.
    """
    rules = sorted(_cleared_rules())
    base = {}
    for r in rules:
        try:
            base[r] = json.dumps(_assemble_nocold(r, ns), sort_keys=True)
        except Exception as exc:
            base[r] = f"<refused:{type(exc).__name__}>"
    covered, report = {}, []
    for name, path, fn in _mutations():
        if not path or not os.path.isfile(path):
            report.append(f"  {name:38} no target")
            continue
        try:
            with Mutation(path, fn):
                moved = []
                _cold()
                for r in rules:
                    try:
                        now = json.dumps(_assemble_nocold(r, ns), sort_keys=True)
                    except Exception as exc:
                        now = f"<refused:{type(exc).__name__}>"
                    if now != base[r]:
                        moved.append(r)
        except SystemExit as exc:
            report.append(f"  {name:38} {exc}")
            continue
        for r in moved:
            covered.setdefault(r, name)
        report.append(f"  {name:38} moved {len(moved)}")
    return covered, report, rules


def main() -> int:
    # `paths` FIRST AND ON ITS OWN. It is what puts the general-scorer directory
    # on sys.path, and `olx_prompts` lives there. injection_reach.py carries the
    # same note for the same reason: alphabetical import order put the scorer
    # first and died with ModuleNotFoundError.
    import paths as _paths  # noqa: F401  (import order is the point)

    import olx_prompts as _OP
    _OP.refuse_if_selftest_running("assembler_reach")

    import coursedata
    ns = coursedata.course_id()

    # `--all` SWEEPS EVERY MUTATION ACROSS EVERY CLEARED RULE and rewrites the
    # budget from what it finds. It is minutes, not seconds, because each
    # mutation needs a cold read of every rule -- so the GATE runs the quick
    # cases and this is a deliberate pre-certification step.
    if "--all" in sys.argv:
        covered, report, rules = _sweep_all(ns)
        for line in report:
            print(line)
        print()
        uncovered = sorted(set(rules) - set(covered))
        _budget_path().write_text(
            json.dumps({"uncovered": len(uncovered), "rules": uncovered,
                        "covered": {k: covered[k] for k in sorted(covered)}},
                       indent=1) + "\n", encoding="utf8")
        print(f"  coverage: {len(covered)} of {len(rules)} cleared rule(s) move "
              f"under some mutation")
        print(f"  budget rewritten: {len(uncovered)} uncovered")
        return 0

    cases = _cases()
    # RECOVER FIRST, ALWAYS. A killed run leaves a mutated tree and a backup;
    # every later reader of that file -- including this tool's own baseline --
    # would otherwise measure the mutation as if it were the source.
    for path in _recover([c[1] for c in cases]):
        print(f"  RECOVERED {path} from a previous run that was killed mid-mutation")

    blind, ran = [], 0
    for rule, path, transform in cases:
        try:
            before = json.dumps(_assemble(rule, ns), sort_keys=True)
        except Exception as exc:
            print(f"  {rule:42} assembler REFUSED: {str(exc)[:80]}")
            blind.append(rule)
            continue
        with Mutation(path, transform):
            try:
                after = json.dumps(_assemble(rule, ns), sort_keys=True)
            except Exception as exc:
                # A THROW IS A MOVE, and a legible one: the assembler noticed.
                after = f"<threw: {type(exc).__name__}>"
        ran += 1
        moved = before != after
        print(f"  {rule:42} {'moved' if moved else 'DID NOT MOVE'}")
        if not moved:
            blind.append(rule)

    print()
    # THE BUDGET BELONGS TO `--all`, NOT TO THIS PATH. The quick path runs a
    # couple of named cases so the gate stays seconds long; judging coverage
    # from those would report 75 uncovered against a budget the SWEEP set at 20
    # and fail every gate. Coverage is a claim about the whole corpus and only
    # the sweep measures it.
    if blind:
        print(f"{len(blind)} assembler(s) did not move when their source "
              f"changed: {', '.join(blind)}")
        print("An assembler whose payload is identical after its source is "
              "mutated is not reading that source. Either the case names the "
              "wrong file, or the assembler does.")
        return 1
    print(f"{ran} assembler(s) each moved when their source changed.")
    print("NOTE: this proves each READS its source. It does NOT prove it reads "
          "it correctly -- that was E63's comparison against python's payload, "
          "which cannot be rebuilt for rules whose python half is gone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
