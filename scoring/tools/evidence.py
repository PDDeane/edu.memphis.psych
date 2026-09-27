#!/usr/bin/env python3
"""A comparison used as EVIDENCE must be shown to fail on a known difference.

WHY THIS EXISTS. On 2026-09-24 the same mistake was made three times in one
session, each time producing a confident wrong answer that reached the migration
plan before it was caught:

  1. A leak count read text that MENTIONS a fact name as text that USES one --
     prose inside string literals counted as code. Filed as 60 sites; the real
     figure was 12.
  2. A re-sweep scan read one side's keys off the other. The python column
     reported ZERO cells affected while driving the same prompts, because it
     stores `checks`/`answers` and the scan looked for `verdicts`/`slots`. Filed
     as 960 cells; the real figure was 2,068.
  3. An equality check compared two tables through
     `json.dumps(..., default=str)`, which serialises a TUPLE and a LIST
     identically. It reported them IDENTICAL while the types changed underneath,
     and the audit then died on `unhashable type: 'list'`.

Three different scans, one root: **a comparison that normalises away the thing
that matters, trusted because it came back clean.** None was caught by review;
all three were caught later, by something downstream breaking.

WHAT THIS DOES. It refuses to report sameness until the SAME comparison has been
shown to report difference on a pair that is known to differ. A check that cannot
fail is not evidence, and this makes that structural rather than remembered.

WHAT IT DOES NOT DO. It cannot tell you whether you compared the RIGHT things --
only that your comparison can tell things apart at all. Choosing the control is
the judgement; this enforces that one exists.

    from evidence import certify
    certify("tables unchanged", before, after,
            must_differ=(before, {**before, "_probe": ("a",)}))
"""
from __future__ import annotations


class NotEvidence(RuntimeError):
    """A comparison was asked to certify sameness without a positive control."""


def _default_same(a, b) -> bool:
    """Equality that does NOT normalise: type differences count.

    `==` alone is not enough, because `("a","b") == ["a","b"]` is False but
    `{"k": ("a","b")} == {"k": ["a","b"]}` is also False only by luck of the
    container. Comparing `repr` keeps types visible at every depth, which is the
    property the json comparison threw away.
    """
    return a == b and repr(a) == repr(b)


def certify(label: str, a, b, *, must_differ, same=None) -> bool:
    """-> whether `a` and `b` are the same, having PROVED the test can fail.

    `must_differ` is a (x, y) pair the comparison MUST call different. If it does
    not, this raises rather than returning an answer: the comparison is blind in
    the dimension being relied on, and its verdict means nothing.
    """
    cmp = same or _default_same
    x, y = must_differ
    if cmp(x, y):
        raise NotEvidence(
            f"{label}: the comparison cannot tell the control pair apart, so its "
            f"verdict is not evidence. It called these the same:\n"
            f"  {x!r}\n  {y!r}\n"
            f"Pick a control that differs in the dimension you are relying on -- "
            f"types, keys, order -- or use a comparison that can see it.")
    return cmp(a, b)


def self_test() -> int:
    """The three failures above, reconstructed. 0 when all pass."""
    import json

    ok = fail = 0

    def check(label, got, want):
        nonlocal ok, fail
        good = got == want
        ok, fail = ok + good, fail + (not good)
        print("  " + ("PASS" if good else "FAIL") + "  " + label)

    # 3. the tuple/list erasure that actually happened
    before = {"baseline": ("baseline", "baseline_data")}
    after = {"baseline": ["baseline", "baseline_data"]}
    lossy = lambda p, q: json.dumps(p, sort_keys=True, default=str) == \
                         json.dumps(q, sort_keys=True, default=str)
    check("lossy json comparison calls tuple and list the same", lossy(before, after), True)
    try:
        certify("tables", before, after, must_differ=(before, after), same=lossy)
        check("certify REFUSES a blind comparison", False, True)
    except NotEvidence:
        check("certify REFUSES a blind comparison", True, True)
    check("the type-preserving default sees the difference",
          certify("tables", before, after, must_differ=(before, after)), False)

    # 1. counting a mention as a use
    # A NONCE, NOT A REAL FACT NAME. This case is about prose containing a
    # name, so any name will do -- and using a live course fact made a
    # self-test of the evidence mechanism depend on this course's vocabulary.
    # Step 7, 2026-09-25.
    check("a name inside prose is not the same value as the name",
          certify("count", "uses widget_flag here", "widget_flag",
                  must_differ=("a", "b")), False)

    # 2. one side reading clean is not a finding
    check("an empty result is not certified without a live control",
          certify("scan", {}, {}, must_differ=({"k": 1}, {})), True)

    print("\n  " + str(ok) + " passed, " + str(fail) + " failed")
    return 1 if fail else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(self_test() if "--self-test" in sys.argv else 0)
