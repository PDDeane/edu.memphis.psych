#!/usr/bin/env python3
"""Cite a student's words without storing them: a resolvable reference.

THE PROBLEM THIS SOLVES. Subgoal write-ups quote the answer they are reasoning
about, because that is the natural way to record a judgement -- "gold credited
the first entry and charged the second" means nothing without the entries. 434
such quotes accumulated before anything was looking, 371 of them in `scoring/`.
They are LOAD-BEARING: strip them and the record stops being checkable.

But the corpus lives outside any repo for a reason. The submissions carry real
names in their OOXML metadata, so a participant number is not de-identification,
and a quoted sentence travels wherever the file travels.

So: keep the citation, drop the payload. A reference names WHERE the text is,
and the text stays in `$COURSE_DATA`.

    [[corpus Q5/p4 first 0:74 sha=da91999372f1]]

    item ---^   ^-- participant   ^-- response field   ^-- span   ^-- of the span

WHAT EACH PART IS FOR. `item/pid/field` is the address `_fixture_boxes` already
uses, so this invents no new scheme. The span makes it precise enough to cite a
clause rather than a whole box. The sha is what makes it SAFE: a reference whose
span still resolves but whose text has changed is a silent lie, and the sha turns
that into a loud failure. `--check` is the guard, and it is deliberately unable
to pass quietly -- without the corpus it reports the references as UNVERIFIED and
exits non-zero, rather than reporting success over an empty scan, which is the
failure mode this project keeps meeting.

AN EXCLUDED OR SUSPECT CELL IS STILL REFERENCED, NEVER QUOTED. `PER_ITEM_EXCLUDE`
and `handouts.suspect()` decide whether a cell may be cited as EVIDENCE -- a
suspect cell is untrustworthy input and must not be argued from in either
direction. That is a question about reasoning. This is a question about privacy,
and the two are orthogonal: dropping a cell from every rate does not make the
student's sentence ours to store. So a write-up that discusses an excluded cell
references it exactly like any other, and the fact that its number is not counted
changes nothing about how its words are handled.

BESIDE THE REFERENCE, WRITE A GLOSS IN YOUR OWN WORDS. The reference is the
evidence; the gloss is the meaning, and it has to carry the prose on its own for
a reader without corpus access:

    the first entry names the GOAL behaviour, not the unwanted one, and offers a
    general benefit as its because-clause [[corpus Q5/p4 first 0:74 sha=da9199...]]

    python3 tools/corpus_ref.py --find "<paste the sentence>"             # locate it
    python3 tools/corpus_ref.py --resolve "Q5/p4 first 0:74"               # read it
    python3 tools/corpus_ref.py --expand scoring/GOALS.md                  # read in place
    python3 tools/corpus_ref.py --check                                    # do they still resolve?
"""
# THE PACKAGE ROOT ON THE PATH, for the direct-script spelling. `tools/__init__`
# does this for `from tools import ...`, and a file run as `python3
# tools/NAME.py` never executes it -- so the import of a sibling fails at the
# first line that needs one. Both spellings are used, so both are made to work.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import argparse
import hashlib
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REF = re.compile(r"\[\[corpus\s+(?P<item>[A-Za-z0-9]+)/p(?P<pid>\d+)\s+"
                 r"(?P<field>[A-Za-z0-9_]+)\s+(?P<a>\d+):(?P<b>\d+)"
                 r"(?:\s+sha=(?P<sha>[0-9a-f]{6,64}))?\]\]")


def sha12(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()[:12]


def _index() -> dict:
    """(item, pid, field) -> text, for every cell the corpus holds.

    Built by walking `_fixture_boxes`, which reads the JOBS spec rather than
    guessing field names -- a name heuristic covered handout 1 and silently
    returned nothing for handouts 2 and 3, which is how both were absent from
    every fixture check while reading as "no multi-box cells".
    """
    sys.path.insert(0, str(HERE))
    import enforcement as E
    import measured as M
    out = {}
    for item in M._jobs():
        for pid in range(1, 21):
            try:
                boxes = E._fixture_boxes(item, pid)
            except Exception:
                continue
            for fld, txt in (boxes or {}).items():
                if isinstance(txt, str) and txt.strip():
                    out[(item, pid, fld)] = txt
    return out


def make_ref(cell: tuple, a, b, idx: dict | None = None, *, olx: bool = False) -> str:
    """Build a reference, or REFUSE. The only sanctioned way to write one.

    Every harness that formatted a reference by hand has eventually formatted a
    bad one: three times a span search returned None and the None was written
    straight into the file as `{{corpus:1a/p6:response:None:None:...}}` -- which
    parses, looks like a citation, and resolves to nothing. The failure is always
    the same shape, a search that found nothing feeding a formatter that did not
    ask.

    So the formatter asks. A None offset, a reversed or empty span, a span past
    the end of the field, or a cell that does not exist are all refusals, and the
    sha is computed HERE from the text the offsets actually select rather than
    passed in by the caller.
    """
    idx = idx if idx is not None else _index()
    if a is None or b is None:
        raise ValueError(f"make_ref({cell}): span is {a}:{b} -- the search that "
                         f"produced it found nothing. A reference cannot be "
                         f"built from a failed search.")
    a, b = int(a), int(b)
    if cell not in idx:
        raise ValueError(f"make_ref: no such cell/field {cell}")
    src = idx[cell]
    if not (0 <= a < b <= len(src)):
        raise ValueError(f"make_ref({cell}): span {a}:{b} is not inside a field "
                         f"of {len(src)} chars")
    span = src[a:b]
    if not span.strip():
        raise ValueError(f"make_ref({cell}): span {a}:{b} selects only whitespace")
    item, pid, fld = cell
    if olx:
        return f"{{{{corpus:{item}/p{pid}:{fld}:{a}:{b}:sha={sha12(span)}}}}}"
    return f"[[corpus {item}/p{pid} {fld} {a}:{b} sha={sha12(span)}]]"


def find(needle: str, idx: dict | None = None) -> list[str]:
    """Every reference whose text contains `needle`. Ambiguity is REPORTED.

    A needle matching two cells is not resolved by picking the first: the whole
    point is that the reference names one span, so the caller is told there are
    two and decides. Short needles match everywhere, which is why a match count
    is printed rather than a single answer.
    """
    idx = idx if idx is not None else _index()
    hits = []
    for (item, pid, fld), txt in sorted(idx.items()):
        start = txt.find(needle)
        while start >= 0:
            end = start + len(needle)
            hits.append(f"[[corpus {item}/p{pid} {fld} {start}:{end} "
                        f"sha={sha12(txt[start:end])}]]")
            start = txt.find(needle, start + 1)
    return hits


def resolve(ref: str, idx: dict | None = None) -> tuple[str, str]:
    """(text, status). Never raises on a bad reference -- it reports one."""
    m = REF.search(ref) or REF.search(f"[[corpus {ref.strip()}]]")
    if not m:
        return ("", f"unparseable reference: {ref!r}")
    idx = idx if idx is not None else _index()
    key = (m["item"], int(m["pid"]), m["field"])
    txt = idx.get(key)
    if txt is None:
        return ("", f"no such cell/field: {key[0]}/p{key[1]} {key[2]}")
    a, b = int(m["a"]), int(m["b"])
    if b > len(txt):
        return ("", f"span {a}:{b} runs past the field ({len(txt)} chars) -- "
                    f"the corpus moved under this reference")
    span = txt[a:b]
    if m["sha"] and sha12(span) != m["sha"]:
        return (span, f"SHA MISMATCH: reference says {m['sha']}, span hashes to "
                      f"{sha12(span)} -- the text at this address is not the text "
                      f"that was cited")
    return (span, "ok")


OLX_REF = re.compile(r"\{\{corpus:(?P<item>[A-Za-z0-9]+)/p(?P<pid>\d+):"
                     r"(?P<field>[A-Za-z0-9_]+):(?P<a>\d+):(?P<b>\d+)"
                     r"(?::sha=(?P<sha>[0-9a-f]{6,64}))?\}\}")


def expand(text: str, idx: dict | None = None) -> str:
    """Replace every `{{corpus:...}}` in OLX text with the text it names.

    THE TWO HALVES OF ONE MECHANISM. An .olx file on disk carries a REFERENCE;
    everything that reads it -- fingerprints, section slicing, the served build
    -- sees the RESOLVED text. That is what lets the student's words leave the
    repo without a single sha moving: `prompt_sha` hashes a slice of
    `measured._olx()`, so resolving there means the hash is taken over exactly
    the bytes it was taken over before.

    The OLX spelling is `{{corpus:Q5/p4:first:0:74:sha=...}}` rather than the
    `[[corpus ...]]` used in prose, because `{{...}}` is what OLX already treats
    as a placeholder and the build's template pass understands it.

    A reference that cannot be resolved RAISES. Returning the reference text
    unexpanded would ship `{{corpus:...}}` to a grader as if it were the
    student's answer, and the model would score the placeholder.
    """
    if "{{corpus:" not in text:
        return text
    idx = idx if idx is not None else _index()
    def sub(m):
        key = (m["item"], int(m["pid"]), m["field"])
        src = idx.get(key)
        if src is None:
            raise SystemExit(f"corpus_ref.expand: no such cell/field "
                             f"{key[0]}/p{key[1]} {key[2]}")
        a, b = int(m["a"]), int(m["b"])
        if b > len(src):
            raise SystemExit(f"corpus_ref.expand: span {a}:{b} runs past "
                             f"{key[0]}/p{key[1]} {key[2]} ({len(src)} chars)")
        span = src[a:b]
        if m["sha"] and sha12(span) != m["sha"]:
            raise SystemExit(f"corpus_ref.expand: SHA MISMATCH at "
                             f"{key[0]}/p{key[1]} {key[2]} {a}:{b} -- declared "
                             f"{m['sha']}, found {sha12(span)}. The corpus moved "
                             f"under this reference; read the cell.")
        return span
    return OLX_REF.sub(sub, text)


def expand_prose(text: str, idx: dict | None = None) -> str:
    """Resolve `[[corpus ...]]` -- the prose form -- in a string.

    THE MODEL PATH NEEDS THIS, and that is easy to miss. Rubric `guidance`,
    `rule` and `desc` strings are assembled into BOTH prompts: `score.build_prompt`
    for paper and `olx_prompts.build_web_prompt` for the web. A reference left
    unresolved there is not a privacy win, it is a grader being asked to score
    the string `[[corpus Q5/p4 first 0:53 sha=...]]` as if a student had written
    it. Same failure as an unresolved `{{corpus:...}}` on a rendered page, one
    layer further in.

    Raises rather than degrades, for the same reason `expand` does.
    """
    if "[[corpus " not in text:
        return text
    idx = idx if idx is not None else _index()
    def sub(m):
        key = (m["item"], int(m["pid"]), m["field"])
        src = idx.get(key)
        if src is None:
            raise SystemExit(f"corpus_ref.expand_prose: no such cell/field "
                             f"{key[0]}/p{key[1]} {key[2]}")
        a, b = int(m["a"]), int(m["b"])
        if b > len(src):
            raise SystemExit(f"corpus_ref.expand_prose: span {a}:{b} runs past "
                             f"{key[0]}/p{key[1]} {key[2]} ({len(src)} chars)")
        span = src[a:b]
        if m["sha"] and sha12(span) != m["sha"]:
            raise SystemExit(f"corpus_ref.expand_prose: SHA MISMATCH at "
                             f"{key[0]}/p{key[1]} {key[2]} {a}:{b}")
        return span
    return REF.sub(sub, text)


def _repo_refs() -> list[tuple[str, int, str]]:
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                           cwd=HERE.parent).stdout.split()
    out = []
    for f in files:
        p = HERE.parent / f
        if not p.is_file() or p.suffix not in (".py", ".md", ".json"):
            continue
        try:
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                for m in REF.finditer(line):
                    out.append((f, i, m.group(0)))
        except OSError:
            continue
    return out


def export_olx_data(out_path: str, olx_dir: str | None = None) -> int:
    """Write the spans the .olx files reference, and nothing else.

    THE BUILD CANNOT READ THE CORPUS. lo-blocks is TypeScript and the submissions
    are .docx; only the python side can resolve a reference. So the two halves
    meet at a small JSON file that this writes and the build reads.

    ONLY THE REFERENCED SPANS. Not a cell, not a field, not the corpus -- the
    exact substrings the .olx asks for, keyed by the reference that asks. A
    resolver needs nothing more, and every extra character would be a copy of a
    student's work sitting in a second place for no reason.

    The file belongs OUTSIDE any repository, beside the corpus it comes from.
    Writing it into a checkout would undo the whole exercise, so this refuses a
    destination inside one.
    """
    import json
    import subprocess
    out = pathlib.Path(out_path).resolve()
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, cwd=out.parent)
        if top.returncode == 0 and top.stdout.strip():
            print(f"corpus_ref: REFUSING to write {out} -- it is inside the git "
                  f"repository at {top.stdout.strip()}. The export carries student "
                  f"text and belongs beside the corpus, outside any checkout.",
                  file=sys.stderr)
            return 1
    except Exception:
        pass
    if olx_dir:
        root = pathlib.Path(olx_dir)
    else:
        # J-7b, AND A BUG THIS FOUND. The default was `HERE.parent /
        # "psychology"`, and `HERE` is this file's own directory -- `tools/` --
        # so the fallback resolved to `scoring/psychology`, WHICH DOES NOT
        # EXIST. Any caller that omitted `olx_dir` scanned nothing and reported
        # an empty corpus rather than failing. `paths.OLX_DIR` is the content
        # directory the parameter names, resolved one way for everyone.
        import paths
        root = paths.OLX_DIR
    idx = _index()
    data, seen = {}, 0
    # BOTH FORMS, AND THE WHOLE TREE. The export feeds `corpus_resolve.py`, which
    # is the only resolver a historical checkout has -- and history carries prose
    # references in rubric guidance, notes and write-ups, not only `{{corpus:}}`
    # in the .olx. Exporting the .olx form alone would leave every prose
    # reference unresolvable exactly where nothing else can help.
    targets = []
    for d in (root, HERE):
        for pat in ("*.olx", "*.py", "*.md", "*.json"):
            targets.extend(sorted(d.glob(pat)))
    for f in targets:
        if f.name == "corpus_refs.json":
            continue
        text = f.read_text(errors="replace")
        for m in list(OLX_REF.finditer(text)) + list(REF.finditer(text)):
            seen += 1
            key = (f"{m['item']}/p{m['pid']}:{m['field']}:{m['a']}:{m['b']}")
            cell = (m["item"], int(m["pid"]), m["field"])
            src = idx.get(cell)
            if src is None:
                print(f"corpus_ref: {f.name} references {cell}, which does not "
                      f"exist", file=sys.stderr)
                return 1
            a, b = int(m["a"]), int(m["b"])
            span = src[a:b]
            if m["sha"] and sha12(span) != m["sha"]:
                print(f"corpus_ref: {f.name} SHA MISMATCH at {key} -- declared "
                      f"{m['sha']}, found {sha12(span)}", file=sys.stderr)
                return 1
            data[key] = span
    out.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print(f"corpus_ref: {seen} reference(s), {len(data)} distinct span(s) -> {out}",
          file=sys.stderr)
    return 0


def check() -> int:
    """0 only if every reference in the repo resolves to the text it cites.

    ABSENT CORPUS IS NOT A PASS. A checker that returns [] when its source is
    missing reports success for having looked at nothing, and this repo has been
    bitten by that shape more than once. No corpus means the references are
    UNVERIFIED, which is a different answer from "verified good".
    """
    refs = _repo_refs()
    if not refs:
        print("corpus_ref: no references in the repo yet", file=sys.stderr)
        return 0
    try:
        idx = _index()
    except Exception as e:
        print(f"corpus_ref: {len(refs)} reference(s) UNVERIFIED -- the corpus is "
              f"unreadable ({type(e).__name__}: {e}).\nThis is not a pass.",
              file=sys.stderr)
        return 1
    if not idx:
        print(f"corpus_ref: {len(refs)} reference(s) UNVERIFIED -- the corpus "
              f"resolved to zero cells.\nThis is not a pass.", file=sys.stderr)
        return 1
    bad = []
    for f, line, ref in refs:
        _, status = resolve(ref, idx)
        if status != "ok":
            bad.append(f"{f}:{line}: {status}")
    print(f"corpus_ref: {len(refs)} reference(s), {len(bad)} broken",
          file=sys.stderr)
    for b in bad:
        print(f"    {b}", file=sys.stderr)
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--find", metavar="TEXT")
    ap.add_argument("--resolve", metavar="REF")
    ap.add_argument("--expand", metavar="FILE")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--export-olx-data", metavar="FILE",
                    help="write the spans the .olx files reference, for the build")
    a = ap.parse_args()
    if a.export_olx_data:
        return export_olx_data(a.export_olx_data)
    if a.check:
        return check()
    if a.find:
        hits = find(a.find)
        if not hits:
            print("no cell contains that text -- it may be normalised, elided, or "
                  "from a context field rather than a response box", file=sys.stderr)
            return 1
        if len(hits) > 1:
            print(f"{len(hits)} cells match; the reference must name ONE:",
                  file=sys.stderr)
        for h in hits:
            print(h)
        return 0
    if a.resolve:
        text, status = resolve(a.resolve)
        if status != "ok":
            print(status, file=sys.stderr)
            return 1
        print(text)
        return 0
    if a.expand:
        idx = _index()
        p = pathlib.Path(a.expand)
        for line in p.read_text(errors="replace").splitlines():
            def sub(m):
                text, status = resolve(m.group(0), idx)
                return f"{m.group(0)} -> {text!r}" if status == "ok" else \
                       f"{m.group(0)} -> <{status}>"
            print(REF.sub(sub, line))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
