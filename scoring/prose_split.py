#!/usr/bin/env python3
"""Stage 7's split, prepared as a WORKSHEET — because the decision is not mechanical.

§10.3.2 sorts each course-derived sentence into one of three outcomes:

    specification -> the course file
    incident      -> the course changelog
    split         -> generic half stays in the engine, instance goes to the changelog

**No tool can make that choice.** T7.3 says so about itself and the same is true
here: a word list finds the sentences, it cannot tell a specification from an
incident. So this does not move anything. It produces the worksheet a person
works from, with the evidence already gathered for each decision.

WHY A WORKSHEET AND NOT A PASS. Measured 2026-09-19: **all 31 sections of
`QUALITY_CONTROL.md` carry course vocabulary.** The split is therefore a
sentence-level rewrite of every section, not a move of a few -- and an
unreviewed diff that touches every section is the failure T7.1's design names:
*a diff that touches every line cannot be reviewed*, and these files are read by
five modules and by people.

WHAT IT GIVES EACH SENTENCE. The terms that flagged it, and a SUGGESTED bucket
with the reason for the suggestion -- never a decision:

  * a sentence with a date or a measured number reads as an INCIDENT, because
    that is what the changelog exists to keep;
  * a sentence naming an item or a slot but carrying no number reads as a
    SPECIFICATION, because it states a rule about this course;
  * anything else is left UNCLASSIFIED, which is the honest answer and the one
    a human has to resolve.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

FILES = ("GOALS.md", "QUALITY_CONTROL.md", "BACKLOG.md", "EQUIVALENCE.md",
         "README.md")
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`*])")
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
NUMBER = re.compile(r"\b\d+(?:/\d+|%|\.\d+)?\b")


def suggest(sentence: str, terms: list[str]) -> tuple[str, str]:
    """-> (bucket, why). A SUGGESTION with its reason, never a decision."""
    if DATE.search(sentence):
        return ("incident", "carries a date, which is what the changelog keeps")
    numbers = [n for n in NUMBER.findall(sentence) if len(n) > 1 or n not in "0123456789"]
    if len(NUMBER.findall(sentence)) >= 2:
        return ("incident", "carries measured numbers; a generic retelling would "
                            "lose the evidence")
    if terms and not numbers:
        return ("specification",
                f"names {terms[0]} and states a rule rather than an event")
    return ("unclassified",
            "a word list cannot tell a specification from an incident here")


def worksheet(path: str) -> list[dict]:
    import prose_vocabulary as PV

    terms = PV.course_terms()
    rows = []
    section = "<preamble>"
    fenced = False
    for n, line in enumerate(open(path, errors="ignore").read().split("\n"), 1):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        # INDENTATION IS NOT A CODE BLOCK HERE. The first version skipped any
        # line starting with four spaces, on the usual Markdown convention --
        # and GOALS.md's prose is indented under its entries, so 15,640 of its
        # 16,762 lines were discarded and the worksheet reported 89 sentences
        # for a file that is almost entirely prose. Fenced blocks are tracked
        # properly instead; a table row is still skipped.
        if not line.strip() or line.lstrip().startswith("|"):
            continue
        for sentence in SENTENCE.split(line):
            hits = PV.offences(sentence, terms)
            if not hits:
                continue
            bucket, why = suggest(sentence, hits)
            rows.append({"line": n, "section": section, "terms": hits[:4],
                         "suggested": bucket, "why": why,
                         "text": sentence.strip()[:160]})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", action="append", default=None)
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args(argv)

    # RESOLVED, not joined onto HERE: three of these five now live with the course.
    # Joining the name here would silently shorten the list to the ones that have
    # not moved yet, which is a smaller job reported as a finished one.
    import compose_docs

    files = args.file or [compose_docs.doc_path(f) for f in FILES
                          if os.path.exists(compose_docs.doc_path(f))]
    everything = {}
    for name in files:
        rows = worksheet(os.path.join(HERE, name))
        everything[name] = rows
        by = {}
        for r in rows:
            by[r["suggested"]] = by.get(r["suggested"], 0) + 1
        print(f"  {name:<22} {len(rows):>4} sentence(s) to decide   "
              + "  ".join(f"{k}:{v}" for k, v in sorted(by.items())))
    total = sum(len(v) for v in everything.values())
    print(f"\n  {total} sentences carry course vocabulary across {len(files)} file(s).")
    print("  NOTHING HAS BEEN MOVED. Each needs one of: specification -> the course "
          "file,\n  incident -> the changelog, split -> generic half stays. The "
          "suggestion is\n  evidence for that decision, not the decision.")
    if args.json:
        json.dump(everything, open(args.json, "w"), indent=1)
        print(f"  worksheet written: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
