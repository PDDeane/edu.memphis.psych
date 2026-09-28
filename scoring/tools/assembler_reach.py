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


def _assemble(rule: str, ns: str):
    import lo_enforce
    return lo_enforce.probe("assemble", {"rule": rule, "ns": ns})


def _drop_first_slot(src: str) -> str:
    import re
    m = re.search(r"\n\s*<Slot\b[^>]*/>", src)
    return src.replace(m.group(0), "", 1) if m else src


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
    staged = RC.staged_path()
    return [
        # SLOT KEYS ARE LITERALLY THIS RULE'S SUBJECT: it compares the sheet's
        # keys against the staged rubric's, so removing one must move it.
        ("sheet_matches_rubric", staged, _drop_first_slot),
    ]


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
    blind, ran = [], 0
    for rule, path, transform in _cases():
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
