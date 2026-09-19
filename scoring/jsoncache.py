"""Parsed JSON, kept for as long as the file behind it has not moved.

WHY, MEASURED. One warm `enforcement_audit()` parsed 1,832 MB of JSON across
8,517 `json.loads` calls -- 789 MB of it inside a single check, which walks
every run file once per item to read ONE field out of each. Four checks read
the same run corpus, so most of that is the same bytes parsed again and again.
The audit runs once per self-test case, 71 times.

THE OBJECT IS SHARED, AND THAT IS THE DANGER. Returning the cached dict rather
than a copy is the whole saving -- a deepcopy of these documents costs about
what parsing them costs -- but it means a caller that MUTATES what it gets
corrupts every later reader in the process. `measured.load()` is deliberately
NOT routed through here for exactly that reason: its record-writing path
mutates the document it loads before writing it back.

So the rule is read-only, and it is checked rather than trusted:
`check_json_cache_is_not_mutated` fingerprints each document when it is cached
and re-fingerprints at the end of an audit. A mutation is found in the run that
caused it, not in whatever behaviour it eventually distorts.
"""

import json
import os

# BOUNDED BY BYTES, NOT BY COUNT. One audit's working set is 953 distinct files
# and 281 MB of source text, which as parsed dicts is roughly 844 MB -- too much
# to hold when the self-test may be running beside a sweep, and swapping would
# cost more than the parsing saves. An entry count cannot express that: these
# files range from a few hundred bytes to several megabytes, so 512 of them
# might be 5 MB or 900 MB. The budget is on the SOURCE text, which is measured
# exactly, with parsed size assumed at ~3x.
#
# A COUNT CAP WAS MEASURED AND GAVE NOTHING: at 512 entries the working set
# thrashed and a warm audit stayed at 48.5s against 48.1s uncached.
# 320 MB OF SOURCE TEXT, because one audit's working set is 282 MB and a bound
# below it thrashes: measured at 128 MB the cache held 451 of 954 documents and
# a warm audit came out at 49.0s, SLOWER than the 48.1s it replaced. At 320 MB
# it holds all 954 and the audit is 37.2s. Peak RSS 0.95 GB.
_MAX_BYTES = 320 * 1024 * 1024
# ONE IN EVERY N DOCUMENTS IS FINGERPRINTED, and the rest are not, because
# fingerprinting is `json.dumps` and that costs about what parsing costs -- doing
# it on every insert is what made the 128 MB version slower than no cache at
# all. Sampling keeps the read-only contract checkable at a price worth paying:
# ~30 of 954 documents per audit, and the audit runs 71 times in a self-test, so
# a mutation has many chances to land on a watched document over a run. This is
# detection, not proof, and it says so.
_SAMPLE_EVERY = 32
_INSERTS = 0
_CACHE: dict = {}
_ORDER: list = []
_BYTES = 0


def load(path):
    """The parsed contents of `path`. READ-ONLY -- see the module docstring.

    Keyed on mtime and size, so a rewritten file is re-read on the next call.
    """
    p = str(path)
    try:
        st = os.stat(p)
        key = (p, st.st_mtime_ns, st.st_size)
    except OSError:
        raise
    hit = _CACHE.get(key)
    if hit is not None:
        return hit[0]
    with open(p, errors="ignore") as fh:
        doc = json.loads(fh.read())
    global _BYTES, _INSERTS
    _INSERTS += 1
    watched = (_INSERTS % _SAMPLE_EVERY) == 0
    _CACHE[key] = (doc, _fingerprint(doc) if watched else None, st.st_size)
    _ORDER.append(key)
    _BYTES += st.st_size
    while _BYTES > _MAX_BYTES and _ORDER:
        gone = _CACHE.pop(_ORDER.pop(0), None)
        if gone is not None:
            _BYTES -= gone[2]
    return doc


def _fingerprint(doc) -> int:
    """A cheap, total fingerprint of a parsed document.

    `json.dumps` with sorted keys, hashed. Sorted because a mutation that only
    REORDERS keys is not a mutation this cache can be harmed by, and because
    insertion order is not stable across the dict operations a reader might
    legitimately perform on its own copies.
    """
    try:
        return hash(json.dumps(doc, sort_keys=True, default=str))
    except (TypeError, ValueError):                 # pragma: no cover
        return 0


def mutated() -> list:
    """Cached documents that are no longer what was cached.

    Re-fingerprints the SAMPLED documents; it does not re-read any file, so it
    is cheap enough to run at the end of every audit. It answers a different
    question from staleness: not "has the file changed" but "has someone changed
    OUR COPY". Sampled, so a clean result is evidence and not a guarantee --
    see `_SAMPLE_EVERY`.
    """
    out = []
    for (p, _mtime, _size), (doc, fp, _n) in list(_CACHE.items()):
        if fp is None:                              # not sampled; see _SAMPLE_EVERY
            continue
        if _fingerprint(doc) != fp:
            out.append(p)
    return out


def clear() -> None:
    global _BYTES, _INSERTS
    _CACHE.clear()
    _ORDER.clear()
    _BYTES = 0
    _INSERTS = 0


def stats() -> dict:
    return {"documents_held": len(_CACHE), "source_bytes": _BYTES,
            "cap_bytes": _MAX_BYTES,
            "watched": sum(1 for v in _CACHE.values() if v[1] is not None)}
