#!/usr/bin/env python3
"""Resolve corpus references. Standard library only, no project imports.

WHY THIS EXISTS SEPARATELY FROM `corpus_ref.py`. That module resolves against
the LIVE corpus, which means importing `agreement_app`, `measured`, `paths` and
parsing .docx submissions. That is right for authoring: it can find a span, check
a cell, build a reference.

It is wrong for history. A commit from before those modules existed cannot import
them, and a rewritten history has to carry a resolver that works AT EVERY COMMIT
-- including the first, where `scoring/` held almost nothing. A resolver with
dependencies is a resolver that stops working the further back you go, which is
precisely the range it has to cover.

So this reads ONE FILE: the export written by `corpus_ref.py --export-olx-data`,
mapping each reference to the span it names. Nothing else. It has no opinion
about where the corpus is, how a cell is addressed, or what a handout looks like.
Drop it into any commit and it works, because there is nothing to break.

    [[corpus Q5/p4 first 0:53 sha=e4fd18eaab99]]     prose form
    {{corpus:Q5/p4:first:0:53:sha=e4fd18eaab99}}     OLX form

Both address the same span and share one key in the export, so one small file
serves both. The sha is checked on every expansion: a reference that resolves to
different words than it was written against is worse than one that fails, and
this is the only guard a historical checkout has.

    python3 corpus_resolve.py --expand FILE     # print FILE with spans filled in
    python3 corpus_resolve.py --check FILE...   # every reference resolves?
"""
import argparse
import hashlib
import json
import os
import re
import sys

PROSE = re.compile(r"\[\[corpus\s+(?P<item>[A-Za-z0-9]+)/p(?P<pid>\d+)\s+"
                   r"(?P<field>[A-Za-z0-9_]+)\s+(?P<a>\d+):(?P<b>\d+)"
                   r"(?:\s+sha=(?P<sha>[0-9a-f]{6,64}))?"
                   r"(?:\s+alt=(?P<alt>[A-Za-z0-9/,_]+))?"
                   r"(?:\s+shape=(?P<shape>[0-9A-Za-z,\-]+))?\]\]")
OLX = re.compile(r"\{\{corpus:(?P<item>[A-Za-z0-9]+)/p(?P<pid>\d+):"
                 r"(?P<field>[A-Za-z0-9_]+):(?P<a>\d+):(?P<b>\d+)"
                 r"(?::sha=(?P<sha>[0-9a-f]{6,64}))?"
                 r"(?::alt=(?P<alt>[A-Za-z0-9/,_]+))?"
                 r"(?::shape=(?P<shape>[0-9A-Za-z,\-]+))?\}\}")
ENV = "CORPUS_REFS"          # path to the export; falls back to $COURSE_DATA


def sha12(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def export_path(explicit=None):
    """Where the spans live. Explicit argument, then $CORPUS_REFS, then
    $COURSE_DATA/corpus_refs.json. No default inside a checkout, ever: the export
    carries student text and belongs beside the corpus."""
    if explicit:
        return explicit
    if os.environ.get(ENV):
        return os.environ[ENV]
    root = os.environ.get("COURSE_DATA")
    if root:
        return os.path.join(root, "corpus_refs.json")
    raise SystemExit(
        "corpus_resolve: no export located. Set $CORPUS_REFS to the file written "
        "by `corpus_ref.py --export-olx-data`, or $COURSE_DATA to the directory "
        "holding corpus_refs.json.")


def load(path=None):
    p = export_path(path)
    try:
        with open(p) as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise SystemExit(f"corpus_resolve: no export at {p}. A reference cannot "
                         f"be resolved without it, and guessing would put the "
                         f"wrong words in front of a reader.")


# `alt=` NAMES THE OTHER CELLS THE SAME WORDS APPEAR IN, and resolves nothing.
#
# Some sentences are written by more than one student. A reference has to name a
# cell to resolve, so a quote sitting in two people's work forces a choice, and
# choosing silently puts an attribution in the record that the corpus does not
# support -- six of them, where no surrounding text named either candidate.
#
# The prose convention for that case is to cite both, joined by " / ". That is
# honest and it cannot be used here: a reference expands to what it replaced,
# and two of them expand to the span TWICE. Five of the six sit in
# `bmod_handout1.olx`, `bmod_handout3.olx`, `rubric_h1.py`, `rubric_h3.py` and
# `olx_prompts.py` -- all fingerprinted -- so the doubled text would move
# `prompt_sha` on two handouts and `scorer_sha` with them.
#
# So the citation and the resolution are separated. The span in the reference
# body is what expands, exactly once; `alt=` carries the other cells alongside
# it as attribution a reader can follow. Nothing reads it to resolve, which is
# why it is safe for it to say more than the resolver needs.


def apply_shape(span, shape):
    """The exported span, put back into the form the file actually held.

    A reference has to reproduce its ORIGINAL BYTES, not merely the right words.
    The text a file quoted often differs from the corpus span in ways that carry
    no meaning -- a sentence lowercased to sit mid-sentence, a line wrapped, a
    typographic apostrophe -- and a reference that expands to the canonical form
    silently rewrites the file. Measured on 2026-09-15: 418 of 477 substitutions
    did not reproduce what they replaced, and the first one found differed by a
    single capital S.

    So the difference travels WITH the reference, as operations over the span:

        S<i>-<hex>  the i-th gap between words is these bytes, not one space
        A<i>        the apostrophe at index i is the other glyph
        C<hex>      bitmask, little-endian: flip the case of these characters

    Applied in that order, each over the result of the last. The ops encode
    SHAPE only -- whitespace, glyph, case -- never a letter, so a reference
    still carries none of the words it stands for.
    """
    if not shape:
        return span
    seps, apos, case, repl = {}, [], None, []
    for op in shape.split(","):
        if not op:
            continue
        if op[0] == "S":
            i, _, h = op[1:].partition("-")
            seps[int(i)] = bytes.fromhex(h).decode("utf-8")
        elif op[0] == "A":
            apos.append(int(op[1:]))
        elif op[0] == "C":
            case = int(op[1:], 16)
        elif op[0] == "R":
            i, ln, hx = op[1:].split("-")
            repl.append((int(i), int(ln), hx))
    if seps:
        parts = re.split(r"(\s+)", span)
        for k, v in seps.items():
            j = 2 * k + 1
            if j < len(parts):
                parts[j] = v
        span = "".join(parts)
    if apos:
        ch = list(span)
        for i in apos:
            if 0 <= i < len(ch):
                ch[i] = "'" if ch[i] == "\u2019" else "\u2019"
        span = "".join(ch)
    if case:
        ch = list(span)
        for i in range(len(ch)):
            if case >> i & 1:
                ch[i] = ch[i].lower() if ch[i].isupper() else ch[i].upper()
        span = "".join(ch)
    if repl:
        # R<i>-<oldlen>-<hex>: the only op that changes LENGTH, so they are
        # applied last and right-to-left, leaving the earlier indices valid.
        # It exists because a .py source may write an apostrophe as the six
        # characters `\u2019`, and no flip turns one character into six -- one
        # sentence survived the whole rewrite on exactly that.
        for i, ln, hx in sorted(repl, key=lambda r: -r[0]):
            span = span[:i] + bytes.fromhex(hx).decode("utf-8") + span[i + ln:]
    return span


def expand(text, data=None, where="<text>"):
    """Both forms, resolved. Raises rather than leaving a reference in place."""
    if "[[corpus " not in text and "{{corpus:" not in text:
        return text
    data = data if data is not None else load()

    def sub(m):
        key = f"{m['item']}/p{m['pid']}:{m['field']}:{m['a']}:{m['b']}"
        span = data.get(key)
        if span is None:
            raise SystemExit(
                f"{where}: the export has no span for {key}. Re-run "
                f"`corpus_ref.py --export-olx-data` against a tree that contains "
                f"this reference.")
        if m["sha"] and sha12(span) != m["sha"]:
            raise SystemExit(
                f"{where}: SHA MISMATCH for {key} -- the reference declares "
                f"{m['sha']}, the exported span hashes to {sha12(span)}. The "
                f"words are not the words this was written against.")
        return apply_shape(span, m.groupdict().get("shape"))

    return OLX.sub(sub, PROSE.sub(sub, text))


def to_olx(text, data=None):
    """Prose references -> OLX references. Convert, do not resolve.

    WHERE THE WORDS ARE ALLOWED TO APPEAR. A rubric carries its references in
    prose form, and `olx_prompts.py` writes the rubric's text into the handout's
    <LLMAction> body. Resolving on the way in put the student's words INTO the
    .olx -- which is the file this whole mechanism exists to keep them out of.

    Converting instead keeps the reference all the way to the page, where both
    consumers already resolve it: `resolveCorpusRefs.ts` when the site is built,
    and `measured._olx` when the scorer reads it. Because both resolve, the text
    a grader is sent is unchanged and no fingerprint moves -- the .olx says the
    same thing in a form that does not spell it out.

    The fields travel in the order the OLX grammar expects: sha, alt, shape.
    """
    def _shape_for(span, want):
        """A shape turning `span` into `want`. The inverse of `apply_shape`.

        Kept here, in the dependency-free resolver, because `to_olx` has to
        REBUILD a shape rather than edit one: dropping a separator changes the
        string's LENGTH, so every case bit and every index after it moves. The
        first attempt edited the op list in place and emitted a case mask
        shifted by one bit against the .olx's -- correct ops, wrong offsets.
        """
        ps, po = re.split(r"(\s+)", span), re.split(r"(\s+)", want)
        ops, cur = [], list(ps)
        if len(ps) == len(po):
            for j in range(1, len(ps), 2):
                if ps[j] != po[j]:
                    ops.append("S%d-%s" % ((j - 1) // 2, po[j].encode("utf-8").hex()))
                    cur[j] = po[j]
        s1 = "".join(cur)
        ch = list(s1)
        if len(s1) == len(want):
            for i, (x, y) in enumerate(zip(s1, want)):
                if x != y and {x, y} <= {"'", "\u2019"}:
                    ops.append("A%d" % i); ch[i] = y
        s2 = "".join(ch)
        mask = 0
        if len(s2) == len(want):
            for i, (x, y) in enumerate(zip(s2, want)):
                if x != y and x.lower() == y.lower():
                    mask |= 1 << i
        if mask:
            ops.append("C%x" % mask)
        s3 = "".join(c.swapcase() if (mask >> i) & 1 else c for i, c in enumerate(s2))
        if s3 != want:
            import difflib
            for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
                    None, s3, want, autojunk=False).get_opcodes():
                if tag != "equal":
                    ops.append("R%d-%d-%s" % (i1, i2 - i1, want[j1:j2].encode("utf-8").hex()))
        return ",".join(ops)

    def _runtime_shape(shape, span):
        """The shape describing the RUNTIME text, not the source layout.

        A prose reference in a .py file carries a shape describing where that
        FILE put the words -- including separators that are a quote, a newline
        and an indent, because the sentence was written across adjacent string
        literals. Python joins those at import, so they were never part of any
        runtime value, and copying them into the .olx emits a reference that
        expands to bytes the generator never produced.

        A separator carrying only whitespace is different: it is real wrapped
        text inside one literal and survives into the value. So the rule is the
        quote character -- a separator containing one is part syntax, and only
        the syntax goes.

        WHAT SURVIVES IS WHAT WAS INSIDE THE QUOTES. Python's implicit
        concatenation joins adjacent literals with NOTHING between them, so a
        seam does not collapse to a space; it collapses to whatever bytes lay
        OUTSIDE the quote characters, which is the text the literals themselves
        carried. Usually that is the one trailing space of `"... word "` -- which
        is why collapsing to a space was right nearly everywhere and wrong in the
        one place it mattered. A line wrapped immediately after a hyphen has no
        space in either literal, and the space this used to insert turned
        `Tuesday-Friday.` into `Tuesday- Friday.`, one character that cost the
        whole history's byte-for-byte proof.

        The shape is then REBUILT against the resulting text, because collapsing
        it moves every later index.
        """
        if not shape or span is None:
            return shape
        want = apply_shape(span, shape)
        for op in shape.split(","):
            if op[:1] != "S":
                continue
            _, _, hx = op[1:].partition("-")
            try:
                raw = bytes.fromhex(hx).decode("utf-8")
            except Exception:
                continue
            q = [i for i, ch in enumerate(raw) if ch in "\"'"]
            if q and raw in want:
                want = want.replace(raw, raw[:q[0]] + raw[q[-1] + 1:])
        return _shape_for(span, want)

    def sub(m):
        g = m.groupdict()
        key = f"{g['item']}/p{g['pid']}:{g['field']}:{g['a']}:{g['b']}"
        out = f"{{{{corpus:{key}"
        if g.get("sha"):
            out += f":sha={g['sha']}"
        if g.get("alt"):
            out += f":alt={g['alt']}"
        sh = _runtime_shape(g.get("shape"), (data or {}).get(key))
        if sh:
            out += f":shape={sh}"
        return out + "}}"

    # BOTH FORMS, because the rubric carries OLX references already. The
    # substitution that put them there used the OLX form everywhere, so a
    # generator that only rewrote PROSE references passed the source-layout
    # shape straight through into the .olx -- which is what this function
    # exists to stop. Normalising an OLX reference is a no-op unless its shape
    # carries a literal seam.
    return OLX.sub(sub, PROSE.sub(sub, text))


def refs_in(text):
    out = []
    for pat in (PROSE, OLX):
        for m in pat.finditer(text):
            out.append(f"{m['item']}/p{m['pid']}:{m['field']}:{m['a']}:{m['b']}")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--expand", metavar="FILE")
    ap.add_argument("--check", nargs="*", metavar="FILE")
    ap.add_argument("--refs", metavar="FILE")
    ap.add_argument("--data", metavar="FILE", help="the export, overriding $CORPUS_REFS")
    a = ap.parse_args(argv)
    if a.expand:
        with open(a.expand) as fh:
            sys.stdout.write(expand(fh.read(), load(a.data), a.expand))
        return 0
    if a.refs:
        with open(a.refs) as fh:
            for r in refs_in(fh.read()):
                print(r)
        return 0
    if a.check is not None:
        data = load(a.data)
        n = bad = 0
        for f in a.check:
            with open(f) as fh:
                text = fh.read()
            found = refs_in(text)
            n += len(found)
            try:
                expand(text, data, f)
            except SystemExit as e:
                bad += 1
                print(str(e), file=sys.stderr)
        print(f"corpus_resolve: {n} reference(s) in {len(a.check)} file(s), "
              f"{bad} unresolvable", file=sys.stderr)
        return 1 if bad else 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
