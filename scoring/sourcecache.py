"""Cached source splitting, for code that asks the same file the same question.

WHY THIS EXISTS, MEASURED. One warm `enforcement_audit()` spent 7.4s inside
`ast.get_source_segment` across 2,361 calls, and 6.9s of that was `tottime` in
`ast._splitlines_no_ff` -- the helper that splits the WHOLE file into lines
every single time it is called. The audit runs once per self-test case, and
there are 71 cases, so the same handful of files were re-split roughly 168,000
times. Measured against a cached `splitlines`: 300 calls on a 738KB file took
2.81s through the stdlib and 0.0005s through the cache. 5,776x.

THE CACHE IS ON THE SPLIT, NOT ON THE ANSWER. Two different nodes of one file
give two different segments, so caching segments would key on the node and save
nothing; what repeats is the SPLIT. `segment()` therefore reproduces
`ast.get_source_segment` exactly -- byte offsets, `\\r\\n` handling, padding --
and differs from it only in where the line list comes from.

EXACTLY, AND PROVED RATHER THAN CLAIMED. `check_source_cache_matches_the_stdlib`
compares this against `ast.get_source_segment` on every node of every module in
this directory. The reimplementation copies the stdlib's body deliberately: a
paraphrase would drift, and the one thing this must never do is hand a check a
segment that is subtly not the code it is judging.
"""

import ast

_MAX = 128                    # distinct sources held; the audit's working set is far smaller
_CACHE: dict = {}
_ORDER: list = []


def lines_of(source: str) -> list:
    """`source` split as the parser splits it, computed once per distinct text.

    KEYED ON THE TEXT, NOT ON A PATH, because half the callers hold source they
    read themselves and never had a path for. `hash` on a str is computed once
    and cached by the interpreter, so the lookup is O(1) after the first call;
    the stored text is compared on hit so a hash collision cannot serve one
    file's lines for another.
    """
    key = hash(source)
    hit = _CACHE.get(key)
    if hit is not None and (hit[0] is source or hit[0] == source):
        return hit[1]
    lines = ast._splitlines_no_ff(source)
    _CACHE[key] = (source, lines)
    _ORDER.append(key)
    while len(_ORDER) > _MAX:
        _CACHE.pop(_ORDER.pop(0), None)
    return lines


def segment(source: str, node, *, padded: bool = False):
    """`ast.get_source_segment(source, node)`, off the cached split.

    The body below is the stdlib's, with `_splitlines_no_ff` replaced by
    `lines_of`. The stdlib passes `maxlines=end_lineno+1` and so splits only as
    far as it needs; this splits the whole file once and slices, which is why
    the saving grows with how many nodes are asked about.
    """
    try:
        if node.end_lineno is None or node.end_col_offset is None:
            return None
        lineno = node.lineno - 1
        end_lineno = node.end_lineno - 1
        col_offset = node.col_offset
        end_col_offset = node.end_col_offset
    except AttributeError:
        return None

    lines = lines_of(source)
    if end_lineno == lineno:
        return lines[lineno].encode()[col_offset:end_col_offset].decode()

    padding = (ast._pad_whitespace(lines[lineno].encode()[:col_offset].decode())
               if padded else "")
    first = padding + lines[lineno].encode()[col_offset:].decode()
    last = lines[end_lineno].encode()[:end_col_offset].decode()
    body = lines[lineno + 1:end_lineno]

    body.insert(0, first)
    body.append(last)
    return "".join(body)


def clear() -> None:
    """Drop everything held. For a caller that has just rewritten a file."""
    _CACHE.clear()
    _ORDER.clear()


def stats() -> dict:
    return {"sources_held": len(_CACHE), "cap": _MAX}
