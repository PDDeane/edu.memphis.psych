#!/usr/bin/env python3
"""Fixture corrections as SPANS over the corpus, not as copies of it.

WHAT WAS WRONG. `agreement_app.CONSENSUS_FIXES` corrects a mis-segmented cell by
naming the text the box should hold:

    ("set", "change_a1", "<the sentence the box should hold, typed out in full>")

That is a student's sentence, stored in the repo, and there are 102 of them. They
cannot simply be paraphrased the way a write-up can: this is the INPUT the
scorers run on, so rewording one silently changes what was measured and every
number in the ledger with it.

WHAT THEY ACTUALLY ARE. Measured rather than assumed: of the 102, nine set a box
EMPTY and carry no text at all, and of the remaining 93, **91 are an exact
substring of the raw section text** the fixture was split from, with one more
exact once whitespace is normalised. They are not edits. They are re-segmentations
-- someone read the submission, saw the split had put the wrong clause in the
wrong box, and wrote out the correct clause by hand.

So the correction can name the SPAN instead of the words:

    ("slice", "change_a1", "Q6", 118, 291)   # section Q6, characters 118:291
                                             # ^ the same bytes, named not copied

and the text is read from `$MOLLY_DATA` when the fixture is built. Identical
input to the scorer, nothing quoted in the repo.

WHY THE SHA IS NOT OPTIONAL. A span that still resolves but whose text has moved
is worse than a missing one: the fixture builds, the sweep runs, and it scores
something nobody chose. Every span carries the hash of the text it was written
against, and `--verify` refuses on a mismatch rather than repairing it, because
the right response to "the corpus moved" is a person reading the cell.

    python3 fixture_edits.py --generate    # derive spans from today's literals
    python3 fixture_edits.py --verify      # every span still yields its text
    python3 fixture_edits.py --show Q6 2   # what a cell's corrections resolve to
"""
import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SPANS = HERE / "CONSENSUS_SPANS.json"


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def _sections(item: str, pid: int) -> dict:
    """The RAW sections for a cell, before any split or fix.

    This is the source the corrections were actually made against. The post-split
    fixture FIELDS are not: measured, only 62 of 102 corrections are a substring
    of any field, because a re-segmentation by definition crosses the split that
    put the text in the wrong field. Against the sections it is 91.
    """
    sys.path.insert(0, str(HERE))
    import agreement_app as A
    import measured as M
    return A.sections_for(M._jobs()[item]["handout"], pid)


def resolve(entry: list, item: str, pid: int, sections: dict | None = None) -> tuple:
    """(text, status) for one correction. Reports; never raises."""
    sections = sections if sections is not None else _sections(item, pid)
    op = entry[0]
    if op == "clear":
        return ("", "ok")
    if op == "slice":
        _, _box, section, a, b, want_sha = entry
        src = sections.get(section)
        if not isinstance(src, str):
            return ("", f"no section {section!r} for {item}/p{pid}")
        if b > len(src):
            return ("", f"span {a}:{b} runs past section {section} "
                        f"({len(src)} chars) -- the corpus moved")
        text = src[a:b]
        if sha12(text) != want_sha:
            return (text, f"SHA MISMATCH in {section} {a}:{b} -- declared "
                          f"{want_sha}, found {sha12(text)}")
        return (text, "ok")
    if op == "slice_ws":
        # The span is right, the WHITESPACE differs: the correction was typed with
        # single spaces where the submission has a newline or a run. Normalising
        # is a change to layout, never to words, so it cannot alter a judgement --
        # and it keeps one more cell from needing a literal.
        _, _box, section, a, b, want_sha = entry
        src = sections.get(section)
        if not isinstance(src, str):
            return ("", f"no section {section!r} for {item}/p{pid}")
        if b > len(src):
            return ("", f"span {a}:{b} runs past section {section} "
                        f"({len(src)} chars) -- the corpus moved")
        text = " ".join(src[a:b].split())
        if sha12(text) != want_sha:
            return (text, f"SHA MISMATCH in {section} {a}:{b} (normalised) -- "
                          f"declared {want_sha}, found {sha12(text)}")
        return (text, "ok")
    if op == "join":
        # Two spans of the SAME submission, concatenated. Q6/p6 is the only one:
        # the student wrote [[corpus Q6/p6 state_a2 3:38 sha=d7d19592b8a2]] and the correction keeps the negation and the second
        # conjunct without the first. Every character still comes from the
        # corpus; what is stored here is which characters, not what they say.
        _, _box, spans, want_sha = entry
        out = []
        for section, a, b in spans:
            src = sections.get(section)
            if not isinstance(src, str):
                return ("", f"no section {section!r} for {item}/p{pid}")
            if b > len(src):
                return ("", f"span {a}:{b} runs past section {section} "
                            f"({len(src)} chars) -- the corpus moved")
            out.append(src[a:b])
        text = "".join(out)
        if sha12(text) != want_sha:
            return (text, f"SHA MISMATCH in join -- declared {want_sha}, "
                          f"found {sha12(text)}")
        return (text, "ok")
    return ("", f"unknown op {op!r}")


def generate() -> int:
    """Derive spans from the literals that are there today, and PROVE equivalence.

    The generator is the risky moment -- it is the one step that reads the
    literals -- so it does not merely write the table, it resolves every span it
    writes and refuses to emit unless the resolved text is byte-identical to the
    literal it replaces. A conversion that changes one character changes what the
    ledger measured.
    """
    sys.path.insert(0, str(HERE))
    import agreement_app as A
    out, unconverted = {}, []
    for (item, pid), fixes in sorted(A.CONSENSUS_FIXES.items()):
        try:
            sections = _sections(item, pid)
        except Exception as e:
            unconverted.append(f"{item}/p{pid}: sections unavailable ({e})")
            continue
        entries = []
        for f in fixes:
            if f[0] != "set":
                unconverted.append(f"{item}/p{pid} {f[1]}: op {f[0]!r} is not a set")
                continue
            box, want = f[1], f[2]
            if not isinstance(want, str) or not want.strip():
                entries.append(["clear", box])
                continue
            hit = None
            for name, src in sections.items():
                if isinstance(src, str) and want in src:
                    i = src.find(want)
                    hit = ["slice", box, name, i, i + len(want), sha12(want)]
                    break
            if hit is None:                      # whitespace-only difference?
                nw = " ".join(want.split())
                for name, src in sections.items():
                    if not isinstance(src, str) or nw not in " ".join(src.split()):
                        continue
                    for i in range(len(src)):
                        if " ".join(src[i:].split()).startswith(nw):
                            for j in range(i + len(nw), len(src) + 1):
                                if " ".join(src[i:j].split()) == nw:
                                    hit = ["slice_ws", box, name, i, j, sha12(nw)]
                                    break
                            break
                    if hit:
                        break
            if hit is None:                          # a join of two spans?
                for name, src in sections.items():
                    if not isinstance(src, str):
                        continue
                    for cut in range(4, len(want) - 3):
                        head, tail = want[:cut], want[cut:]
                        i, j = src.find(head), src.find(tail)
                        if i >= 0 and j >= 0:
                            hit = ["join", box,
                                   [[name, i, i + len(head)], [name, j, j + len(tail)]],
                                   sha12(want)]
                            break
                    if hit:
                        break
            if hit is None:
                unconverted.append(f"{item}/p{pid} {box}: not a span of any section")
                continue
            text, status = resolve(hit, item, pid, sections)
            if status != "ok" or text != want:
                unconverted.append(f"{item}/p{pid} {box}: round-trip failed ({status})")
                continue
            entries.append(hit)
        if entries:
            out[f"{item}/p{pid}"] = entries
    n = sum(len(v) for v in out.values())
    print(f"  converted {n} correction(s) across {len(out)} cell(s)", file=sys.stderr)
    if unconverted:
        print(f"  {len(unconverted)} NOT converted -- these still carry text:",
              file=sys.stderr)
        for u in unconverted:
            print(f"      {u}", file=sys.stderr)
    SPANS.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"  wrote {SPANS.name}", file=sys.stderr)
    return 1 if unconverted else 0


def verify() -> int:
    """0 only if every declared span still yields text with its declared hash."""
    if not SPANS.exists():
        print("  no CONSENSUS_SPANS.json yet -- run --generate", file=sys.stderr)
        return 1
    table = json.loads(SPANS.read_text())
    bad, checked = [], 0
    for cell, entries in sorted(table.items()):
        item, pid = cell.split("/p")
        try:
            sections = _sections(item, int(pid))
        except Exception as e:
            bad.append(f"{cell}: corpus unreadable ({type(e).__name__}: {e})")
            continue
        for e in entries:
            checked += 1
            _, status = resolve(e, item, int(pid), sections)
            if status != "ok":
                bad.append(f"{cell} {e[1]}: {status}")
    print(f"  {checked} span(s) checked, {len(bad)} broken", file=sys.stderr)
    for b in bad:
        print(f"      {b}", file=sys.stderr)
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--generate", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show", nargs=2, metavar=("ITEM", "PID"))
    a = ap.parse_args()
    if a.generate:
        return generate()
    if a.verify:
        return verify()
    if a.show:
        item, pid = a.show[0], int(a.show[1])
        table = json.loads(SPANS.read_text())
        sections = _sections(item, pid)
        for e in table.get(f"{item}/p{pid}", []):
            text, status = resolve(e, item, pid, sections)
            print(f"  {e[1]:<14} {status:<10} {text[:90]!r}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
