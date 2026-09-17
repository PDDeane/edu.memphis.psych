"""Refuse to start a migration that cannot succeed. Run before stage 00.

WHAT THIS EXISTS TO PREVENT. Every failure below was met for real during the dry
run, and each one reports SUCCESS rather than failure when it happens -- which is
why they need a check rather than care.

    python3 migration/preflight.py
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migration_paths as MP

DRY = "migration_dryrun"


def check_no_script_names_a_sandbox() -> list[str]:
    """A hard-coded sandbox path does not fail on a live tree. It SUCCEEDS.

    Eleven of the dry run's scripts named `/home/pdeane/code/migration_dryrun`
    literally. Run against the live tree they would have edited the sandbox,
    passed every gate, and migrated nothing -- the worst available outcome,
    because it is indistinguishable from success.
    """
    out = []
    # EVERY SCRIPT, NOT EVERY PYTHON SCRIPT. The first version globbed `*.py`
    # and `*.sh`, reported PASS, and missed seventeen TypeScript verifiers whose
    # imports were ABSOLUTE paths into the sandbox --
    # `from '/home/pdeane/code/migration_dryrun/lo-blocks/.../promptAssembler'`.
    # They would have broken the moment the sandbox was deleted, and the check
    # written to prevent exactly that said nothing, because of its glob.
    #
    # ANY absolute path into a home directory is reported, not just the
    # sandbox's: a script that names `/home/<someone>/code/...` works on one
    # machine and nowhere else, which is the same defect wearing a different
    # path.
    files = sorted(set(list(MP.MIGRATION.rglob("*.py")) + list(MP.MIGRATION.rglob("*.sh"))
                       + list(MP.MIGRATION.rglob("*.ts")) + list(MP.MIGRATION.rglob("*.tsx"))))
    for p in files:
        # `env.sh` and `migration_paths.py` name the sandbox inside the guard
        # that REFUSES it; flagging that would fire on the defence itself.
        if p.name in ("preflight.py", "migration_paths.py", "env.sh"):
            continue
        rel = p.relative_to(MP.MIGRATION)
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith(("#", "//", "*")):
                continue
            if DRY in line:
                out.append(f"{rel}:{i} names the sandbox path literally")
            elif re.search(r"['\"]/home/[^'\"]*/(code|molly_data)/", line):
                out.append(f"{rel}:{i} hard-codes an absolute home path -- "
                           f"resolve it instead (migration_paths / $MIGRATION_ROOT)")
    return out


def check_goldens_are_not_older_than_what_they_certify() -> list[str]:
    """A frozen oracle older than the source it certifies proves nothing.

    The acceptance argument is "the bytes did not change", measured against
    frozen oracles. If those oracles were frozen from an EARLIER tree, the
    comparison still passes -- it just stops being about the tree being
    migrated. The dry run forked on 2026-09-13 and the live rubric has moved
    since, so replaying its goldens would certify a rubric that no longer
    exists, greenly.
    """
    out = []
    sources = list(MP.SCORING.glob("rubric*.py")) + list(MP.PSYCHOLOGY.glob("*.olx"))
    if not sources:
        return ["no rubric or .olx sources found -- refusing to judge freshness"]
    newest = max(s.stat().st_mtime for s in sources)
    for g in sorted(MP.GOLDENS.glob("*.json")):
        if g.stat().st_mtime < newest:
            age = (newest - g.stat().st_mtime) / 3600
            out.append(f"goldens/{g.name} is {age:.0f}h older than the newest "
                       f"source it certifies -- re-freeze before relying on it")
    return out


def check_the_products_exist() -> list[str]:
    """No stage script regenerates these; losing them loses the migration.

    TWO OF THEM CANNOT LIVE IN THIS REPOSITORY. `RUBRIC_DECISIONS.md` carries 66
    distinctive student 4-grams and `rubric_reader.py` one, because the dry run
    wrote them before the references existed; this repository is public. They
    are kept in `$MOLLY_DATA/migration_reference/products/` and the real run must
    regenerate them WITH references rather than copying those in. See
    products/README.md.
    """
    out = []
    here = MP.MIGRATION / "products"
    if not (here / "selftest_injections.py").exists():
        out.append("products/selftest_injections.py is missing")
    ref = Path(os.environ.get("MOLLY_DATA", "/home/pdeane/molly_data")) / "migration_reference"
    for w in ("products/RUBRIC_DECISIONS.md", "products/rubric_reader.py",
              "olx/bmod_rubric.olx", "migration_changes.patch"):
        if not (ref / w).exists():
            out.append(f"$MOLLY_DATA/migration_reference/{w} is missing -- the dry "
                       f"run's reference copy is gone and cannot be diffed against")
    return out


def check_the_tree_is_not_carrying_student_text() -> list[str]:
    """Do not start moving text around in a tree that already leaks.

    The migration rewrites the rubric and regenerates every .olx body. Starting
    from a tree that carries student text means the migration's own diffs become
    the place it hides.
    """
    gate = MP.SCORING / "precommit_gate.py"
    if not gate.exists():
        return ["precommit_gate.py is absent -- cannot establish the tree is clean"]
    r = subprocess.run([sys.executable, str(gate)], cwd=str(MP.SCORING),
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        first = next((l for l in (r.stdout + r.stderr).splitlines() if l.strip()), "")
        return [f"precommit_gate refuses the tree: {first[:120]}"]
    return []


def check_the_engine_is_reachable() -> list[str]:
    """The .olx is built by a separate repository; it must be present."""
    if not MP.LO_BLOCKS.exists():
        return [f"$LO_BLOCKS does not exist: {MP.LO_BLOCKS}"]
    if not (MP.LO_BLOCKS / "package.json").exists():
        return [f"{MP.LO_BLOCKS} does not look like lo-blocks"]
    return []


def check_the_rubric_carries_no_student_text() -> list[str]:
    """THE GATE ON STAGE 00. The migration lifts rubric prose into a public .olx.

    If the prose still holds a student's words, the migration does not leak them
    by accident -- it PUBLISHES them, into a new file, and every downstream
    artefact inherits it. The dry run's own `bmod_rubric.olx` carries 47
    distinctive student 4-grams for exactly this reason: it was built before the
    references existed.

    The reference set is the whole response space (`corpus_ref._index()`, 1023
    boxes), not the citation export, and course text is subtracted because the
    handout's own words echoed back by a student are the course's. Four words is
    the threshold at which copying from a unique source is detectable; two
    content words is what makes such a run distinctive rather than idiom.
    """
    import re
    sys.path.insert(0, str(MP.SCORING))
    sys.path.insert(0, "/home/pdeane/code/scripts/history_rewrite")
    try:
        import corpus_ref as CR
        import olx_prompts as O
        from content_words import is_distinctive
    except Exception as e:
        return [f"cannot load the corpus or the distinctiveness rule ({type(e).__name__}: {e}) "
                f"-- refusing to certify the rubric clean"]

    def norm(t):
        return re.sub(r"\s+", " ", re.sub(r"['\u2019]", "'", t)).strip().lower()

    def grams(t, n=4):
        w = norm(t).split()
        return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}

    idx = CR._index()
    if not idx:
        return ["the corpus resolved to zero cells -- cannot certify anything clean"]
    student = {g for t in idx.values() for g in grams(t)}
    student = {g for g in student if is_distinctive(g)}
    for h in (1, 2, 3):
        try:
            student -= grams(O._src(h))
        except Exception:
            pass
    out = []
    for f in sorted(MP.SCORING.glob("rubric*.py")):
        hits = grams(f.read_text(errors="replace")) & student
        if hits:
            out.append(f"{f.name}: {len(hits)} distinctive student 4-gram(s) -- "
                       f"e.g. {sorted(hits)[0]!r}. The rewrite must replace these "
                       f"with references BEFORE the migration lifts them into .olx")
    return out


def check_every_stage_acknowledged_the_current_drift() -> list[str]:
    """Each stage's scripts must be read against the CURRENT DRIFT.md.

    The dry run's scripts were written against the tree of 2026-09-13. They all
    still RUN; several would run and be wrong, because what they compare against
    moved underneath them. Nothing about that failure is loud.

    The acknowledgement is bound to DRIFT.md's SHA, so editing DRIFT.md lapses
    every stage -- a stage reviewed against last week's drift has not been
    reviewed. Record one with `drift_ack.py <stage> "<what you changed>"`.
    """
    sys.path.insert(0, str(MP.MIGRATION))
    import drift_ack as DA
    try:
        sha = DA.drift_sha()
    except SystemExit as e:
        return [str(e)]
    stale = DA.stale(DA.load(), sha)
    return [f"stage {s} has not been read against DRIFT.md {sha}" for s in stale]


def check_stage01_recounts_rather_than_scaling() -> list[str]:
    """Stage 01 must COUNT the coupled checks, not carry the dry run's number.

    The dry run measured 73 of 135. Live now has more checks than that, and the
    ratio is not a property of the code -- it is a measurement of one tree on one
    day. A script repeating it is asserting something it did not observe.
    """
    p = MP.MIGRATION / "stage01_recount_coupling.py"
    if not p.exists():
        return ["stage01_recount_coupling.py is missing"]
    src = p.read_text()
    out = []
    for stale in ("73", "135"):
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if re.search(rf"\b{stale}\b", line) and "=" in line:
                out.append(f"stage01_recount_coupling.py:{i} carries the dry run's "
                           f"count {stale} as a value -- recount against this tree")
    return out


def check_stage03_guards_the_two_resolvers() -> list[str]:
    """Two resolvers now read the reference grammar; they must not drift apart.

    `corpus_resolve.py` resolves in Python (the scorer's path) and
    `resolveCorpusRefs.ts` resolves at build time (the page's path). If they
    disagree about a field or a shape op, the grader and the student see
    different text and nothing else notices. `check_ref_grammars.py` is the only
    thing that compares them, so stage 03 is where it belongs.
    """
    out = []
    checker = MP.SCORING / "check_ref_grammars.py"
    if not checker.exists():
        out.append("scoring/check_ref_grammars.py is missing -- nothing compares "
                   "the Python and TypeScript reference grammars")
    ts = MP.LO_BLOCKS / "packages/shared/scripts/resolveCorpusRefs.ts"
    if not ts.exists():
        out.append(f"{ts} is missing -- the build cannot resolve references")
    gate = MP.MIGRATION / "stage03b_gate.py"
    if gate.exists() and "check_ref_grammars" not in gate.read_text():
        out.append("stage03b_gate.py does not run check_ref_grammars.py -- the "
                   "resolvers can drift through the gate that exists to catch it")
    return out


def check_oracles_were_refrozen_for_stages_04_05() -> list[str]:
    """Stages 04/05 compare `prompt_sha` against a frozen oracle.

    That slice of the .olx now holds corpus REFERENCES, so every family's value
    differs from any pre-rewrite baseline -- because the rewrite changed it, not
    because the migration did. Comparing against an oracle frozen before the
    rewrite reports a migration defect that does not exist, and the fix is a
    re-freeze, not an investigation.
    """
    out = []
    oracle = MP.GOLDENS / "prompt_oracles.json"
    if not oracle.exists():
        return ["goldens/prompt_oracles.json is missing -- stages 04/05 have "
                "nothing to compare against"]
    newest = 0.0
    for f in list(MP.SCORING.glob("*.py")) + list(MP.PSYCHOLOGY.glob("*.olx")):
        newest = max(newest, f.stat().st_mtime)
    if oracle.stat().st_mtime < newest:
        hrs = (newest - oracle.stat().st_mtime) / 3600
        out.append(f"prompt_oracles.json is {hrs:.0f}h older than the newest source "
                   f"it certifies -- re-freeze before stage 04")
    return out


CHECKS = (
    check_no_script_names_a_sandbox,
    check_goldens_are_not_older_than_what_they_certify,
    check_the_products_exist,
    check_the_engine_is_reachable,
    check_the_tree_is_not_carrying_student_text,
    check_the_rubric_carries_no_student_text,
    check_every_stage_acknowledged_the_current_drift,
    check_stage01_recounts_rather_than_scaling,
    check_stage03_guards_the_two_resolvers,
    check_oracles_were_refrozen_for_stages_04_05,
)


def main() -> int:
    MP.require_real_tree()
    print(f"  migrating: {MP.ROOT}")
    bad = 0
    for fn in CHECKS:
        try:
            found = fn()
        except Exception as e:                      # a check that cannot run is not a pass
            found = [f"the check itself failed: {type(e).__name__}: {e}"]
        bad += len(found)
        print(f"  {'FAIL' if found else 'PASS'}  {fn.__name__}")
        for f in found[:8]:
            print(f"         {f}")
    print("PREFLIGHT " + ("NOT MET" if bad else "MET"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
