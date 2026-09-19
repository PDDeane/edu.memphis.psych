#!/usr/bin/env python3
"""T7.3 — no course vocabulary in GENERAL prose. F1's precondition, not F1.

WHAT IT ENFORCES, AND WHAT IT DOES NOT. §10.3.2 sorts a course-derived sentence
into *specification* (moves to the course file), *incident* (moves to the
changelog) or *split* (generic half stays). **A word list cannot tell those
apart.** This says only "a course word appears here"; which remedy applies is a
human decision. It enforces the condition that makes F1 checkable, and claims no
more than that.

WHAT COUNTS AS GENERAL PROSE. Defined, because after Goal G's split the COURSE
halves are supposed to be full of psychology and a gate reading them would fire
on correct work:

  * the GENERAL half of each of the four split files, and
  * every module docstring outside `courses/`.

So it runs AFTER the split. Before it, there is no general half, and this module
says so rather than reporting a clean sweep of a distinction that does not exist
yet -- the shape T2.2 also has, and for the same reason.

`behaviour` IS NOT EXCLUDED BY WORD. T1.1 excludes software-sense `behaviour`
from a MEASUREMENT, which is acceptable there. In a GATE it is a false negative
on the single most likely course word to appear: "the student's target
behaviour" would pass. So surviving uses must be unambiguous -- `code behaviour`,
`runtime behaviour`, the behaviour of a named function -- and a bare `behaviour`
in general prose fails and is rephrased.

THE CHANGELOG MUST EXIST FIRST. F1 sends incidents to a changelog, and none
existed when this was designed. A gate that strips sentences while their
destination is undefined produces deletions, not moves. This module REFUSES to
report on prose while the changelog is missing.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SPLIT_FILES = ("GOALS.md", "QUALITY_CONTROL.md", "BACKLOG.md", "EQUIVALENCE.md")

# The marker a split file uses to separate its general half from its course half.
# Until Stage 7 writes these, there is no general half to check.
GENERAL_MARKER = "<!-- general -->"
COURSE_MARKER = "<!-- course-specific -->"

# Course vocabulary. Read from the course itself where possible -- a hand list
# would drift from the course it describes.
EXTRA_TERMS = {
    "reinforcement", "punishment", "operant", "antecedent", "consequence",
    "baseline", "handout", "bmod", "psych", "psychology",
}

# `behaviour` needs a QUALIFIER to survive. These are the software senses.
BEHAVIOUR_OK = re.compile(
    r"\b(code|runtime|engine|parser|program|function|module|caller|check|"
    r"scorer|reader|gate|tool)'?s?\s+behaviou?r\b", re.I)
BEHAVIOUR_ANY = re.compile(r"\bbehaviou?rs?\b", re.I)


def course_terms() -> set[str]:
    """Item ids and label words, from the course file, plus the declared extras."""
    terms = set(EXTRA_TERMS)
    try:
        import coursedata

        for it in coursedata.items():
            terms.add(str(it["id"]).lower())
            for word in re.findall(r"[A-Za-z]{4,}", str(it.get("label") or "")):
                terms.add(word.lower())
    except Exception:                             # pragma: no cover
        pass
    return {t for t in terms if len(t) >= 3}


def split_state() -> tuple[bool, list[str]]:
    """-> (has the split happened, notes). The reason this check may be inert."""
    notes = []
    split_done = False
    for name in SPLIT_FILES:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        text = open(path, errors="ignore").read()
        if GENERAL_MARKER in text:
            split_done = True
        else:
            notes.append(f"{name} carries no {GENERAL_MARKER} marker")
    return split_done, notes


def changelog_path() -> str:
    return os.path.join(os.path.dirname(HERE), "courses", "edu.memphis.psych",
                        "CHANGELOG.md")


def docstrings_outside_courses(directory: str | None = None) -> list[tuple[str, str]]:
    """(module, docstring) for every module whose prose is meant to be general."""
    directory = directory or HERE
    out = []
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".py"):
            continue
        try:
            tree = ast.parse(open(os.path.join(directory, fn), errors="ignore").read())
        except SyntaxError:
            continue
        doc = ast.get_docstring(tree)
        if doc:
            out.append((fn, doc))
    return out


def offences(text: str, terms: set[str]) -> list[str]:
    """Course words in this prose, and bare `behaviour`."""
    found = []
    lowered = text.lower()
    for term in sorted(terms):
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            found.append(term)
    for m in BEHAVIOUR_ANY.finditer(text):
        window = text[max(0, m.start() - 40):m.end()]
        if not BEHAVIOUR_OK.search(window):
            found.append("behaviour (unqualified)")
            break
    return found


def check(directory: str | None = None) -> dict:
    done, notes = split_state()
    if not os.path.exists(changelog_path()):
        return {"blocked": [
            f"the changelog at {os.path.relpath(changelog_path(), os.path.dirname(HERE))} "
            f"does not exist. F1 sends incidents there, and a gate that strips "
            f"sentences while their destination is undefined produces DELETIONS, "
            f"not moves."], "findings": [], "split_done": done, "notes": notes}
    if not done:
        return {"blocked": [], "findings": [], "split_done": False, "notes": notes}
    terms = course_terms()
    findings = []
    for name, doc in docstrings_outside_courses(directory):
        hits = offences(doc, terms)
        if hits:
            findings.append(f"{name} docstring carries course vocabulary: "
                            f"{', '.join(hits[:6])}")
    return {"blocked": [], "findings": findings, "split_done": True, "notes": notes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=HERE)
    args = ap.parse_args(argv)
    got = check(args.dir)

    print(f"  changelog: {'present' if os.path.exists(changelog_path()) else 'MISSING'}")
    print(f"  course vocabulary terms: {len(course_terms())}")
    if got["blocked"]:
        for b in got["blocked"]:
            print(f"  REFUSING: {b}")
        return 2
    if not got["split_done"]:
        print("  Stage 7's split has NOT run, so there is no general half to "
              "check. This is inert by design, not clean:")
        for n in got["notes"]:
            print(f"    {n}")
        return 0
    for f in got["findings"]:
        print(f"    {f}")
    print(f"  {len(got['findings'])} module(s) carry course vocabulary in general prose")
    return 1 if got["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
