#!/usr/bin/env python3
"""Read the rubric COMPONENT -- the expanded `<Rubric>` the build stages.

WHY THIS READS THE STAGED FILE AND NOT THE AUTHORED ONE. The authored rubric may
carry `<ItemTemplate>` and `<Item use="@pair" params="..."/>`; the staged one
never does. `materialiseRubric` expands templates during the build, on purpose:

    "If a template survived into that output, every reader would need the template
     grammar -- and a second implementation of one rule is the drift this whole
     model exists to end."

So this reads what the build produced. It is a plain XML walk over ordinary
elements: no template grammar, no second implementation, nothing to fall out of
step with `materialiseRubric`. The same argument is why it does not read the
authored file "just to be safe" -- that would be the second implementation.

IT ALSO READS THE RESOLVED COPY, which matters for a different reason: the staged
file has had its `{{corpus:...}}` references expanded against the corpus, so the
text here is what a student is actually shown. The authored file carries
references, and comparing those to anything rendered would compare two spellings
of the same string -- the mistake that cost a day's work on 2026-09-22.

WHEN THE BUILD HAS NOT RUN, this says so rather than guessing. A stale or absent
artifact is not the same as a rubric with no items, and a reader that quietly
returns nothing is how an empty result comes to look like a clean pass.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET

# COMMENTS ARE STRIPPED BEFORE PARSING, and the reason is not tidiness. The
# frontmatter convention writes YAML inside an XML comment:
#
#     <!--
#     ---
#     corpus_data: $COURSE_DATA/corpus_refs.json
#     ---
#     -->
#
# and `---` contains `--`, which XML forbids inside a comment. lo-blocks' own
# parser accepts it; `xml.etree` refuses the file outright with "not well-formed
# (invalid token): line 2, column 2". Both are right about their own contract --
# the platform defined the convention, and this reader is a guest. Comments carry
# no rubric, so they are removed and the rest is parsed strictly. Comments cannot
# nest, so a non-greedy match is exact.
_COMMENT = re.compile(r"<!--.*?-->", re.S)


def staged_path() -> str:
    """Where the build leaves the expanded, resolved rubric."""
    import paths
    return os.path.join(str(paths.LO), ".stage", "content", paths.NS,
                        "psychology", "bmod_rubric.olx")


def _text(el) -> str:
    return "".join(el.itertext()).strip()


def load(path: str | None = None) -> dict:
    """-> {item_id: {slots, credit, deductions, guidance, question, attrs}}.

    Raises FileNotFoundError when the build has not staged the rubric: the caller
    decides what an absent artifact means, which is never "no findings".
    """
    p = path or staged_path()
    with open(p, encoding="utf8") as fh:
        text = _COMMENT.sub("", fh.read())
    root = ET.fromstring(text)            # raises on malformed, which is correct
    out: dict = {}
    for item in root.iter("Item"):
        iid = item.get("scores")
        if not iid:
            continue
        out[iid] = {
            "attrs": dict(item.attrib),
            "question": next((_text(q) for q in item.findall("Question")), ""),
            "slots": [dict(s.attrib) for s in item.findall("Slot")],
            "credit": [dict(c.attrib) for c in item.findall("Credit")],
            "deductions": [dict(d.attrib) for d in item.findall("Deduction")],
            "guidance": [_text(g) for g in item.findall("Guidance")
                         if not g.get("use")],
            "frames": [g.get("use") for g in item.findall("Guidance")
                       if g.get("use")],
        }
    return out


def slot_keys(item_id: str, path: str | None = None) -> list[str]:
    """The slot keys the rubric declares for one item, in rubric order."""
    entry = load(path).get(item_id) or {}
    return [s.get("key") for s in entry.get("slots", []) if s.get("key")]


if __name__ == "__main__":
    import sys
    d = load(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"{len(d)} items")
    for k in sorted(d):
        print(f"  {k:<6} {len(d[k]['slots']):>3} slots  "
              f"{len(d[k]['credit']):>3} credit  {len(d[k]['deductions']):>3} deductions")
