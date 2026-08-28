"""Find student response language smuggled into the rules we author.

A rule that quotes the cohort is not a rule; it is an answer key for one cell.
It scores that cell correctly and teaches us nothing about whether the criterion
generalises, and because the borrowed sentence is usually taken from the very
cell the rule was written to fix, the gain it reports is circular. Two of this
project's recorded gains were found to rest on quoted prose AFTER they had been
measured, reported and committed — DAY1's avoidance rule reproducing DAY1/p8
almost word for word, WK1's agent rule quoting WK1/p1 verbatim.

That is why this runs as a GATE before a sweep rather than as advice in a guide.
A sweep launched over quoted prose spends its calls proving that we can copy.

    python3 leakage.py                     # report on the four cadence items
    python3 leakage.py --items ALL         # every item in handout 2
    python3 leakage.py --gate --items DAY1,WK1     # exit 1 if anything unreviewed
    python3 leakage.py --review <sha> --verdict vocabulary --note "..."

WHAT IT COMPARES. Every block of authored prose a grader sees — rubric
`guidance` and `rule` strings, and `olx_prompts.SLOT_NOTES` — against every
response field in the fixtures, reporting the content bigrams they share.

WHAT A SHARED BIGRAM MEANS. Three different things, and the tool cannot tell
them apart; a person must.

  DOMAIN VOCABULARY ("positive reinforcement", "take away", "target behavior")
  is what the handout is about. Both sides must use it. Spread across many
  students, which is the signal that it is vocabulary and not a quotation.

  COINCIDENCE — an invented example landing on a stock phrasing a student also
  used. "this should {{corpus:NR/p12:nr:123:139:sha=d881672437f8}} goal" was written here independently and
  collides with DAY2/p17. Usually one student, usually one short pair.

  QUOTATION — a rule example traceable to one student, often the very cell the
  rule was written for. This is the fault. The tell is a RUN of shared bigrams
  concentrated in a single student.

So the report ranks by concentration among distinct STUDENTS (participants are
the same people across DAY1/DAY2/WK1/WK2, so counting item-participant pairs
would score one student's recurring phrase as four).

THE REVIEW LEDGER. Judgement is not automatable, so it is recorded instead.
`--review` files a verdict against the SHA OF THE PROSE ITSELF. Edit the block
and its sha changes, the waiver lapses, and the gate asks again — which is the
property that matters, because a rule is usually re-worded at exactly the moment
someone is tempted to paste a student's sentence into it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEWS = os.path.join(HERE, "LEAKAGE_REVIEWED.json")

CADENCE = ("DAY1", "DAY2", "WK1", "WK2")
VERDICTS = ("vocabulary", "coincidence", "rewritten")

# Words too common to carry evidence of copying. Deliberately short: the point
# is to catch content, and an over-long stoplist hides the very runs we want.
STOP = set("""
a an and the to of for i my me it that this is are be will would can could
in on at as so then with when if do does did have has had not no or but you
your they them something anything one two up out off from by about into over
under than there here what which who whom whose all any each every some more
most less least good bad well badly been being was were am
""".split())

# A block is flagged when this many of its shared bigrams are EXCLUSIVE to one
# student — present in that student's responses and in no other student's.
#
# Exclusivity, not frequency, is what separates a quotation from vocabulary, and
# getting this wrong the first time is instructive. Ranking by "how many of the
# shared bigrams does one student account for" flagged Q3's Time-Bound rule at
# 9 of 9 "from p1 alone" — but every one of those nine ("baseline data", "four
# weeks", "week baseline") appears in ten to sixteen students, because the
# assignment prescribes that structure. One student merely happened to contain
# all nine. Filtering to bigrams NO OTHER student used drops Q3 to zero and
# leaves the real quotations standing, which is the same filter
# `enforcement.check_rule_examples_are_not_corpus` applies to its 6-grams.
MIN_EXCLUSIVE = 2

# A SINGLE word can leak, and the bigram rule cannot see it. Two cases found by
# hand after passing every check: "procrastinating" left in `trigger_behavior`'s
# example list, which is WK1/p7's own trigger word; and "a phone, a snack, an
# evening out, music" offered as valence examples, which are the objects in
# NR/p14, PP/p14, NP/p14 and DAY1/p6 -- the four cells that rule scores.
#
# Neither is EXCLUSIVE to one student, so the bigram filter is blind to both:
# "phone" is in three students' answers. What makes them leak is being CONCRETE
# and CORPUS-SPECIFIC while the rule judges the very cells they come from.
#
# Rarity is the usable proxy. A word the assignment itself uses is shared by
# necessity; a word a handful of students happen to use is theirs. The threshold
# is a fraction of the cohort rather than a count, so it survives a corpus of a
# different size.
MAX_STUDENTS_FOR_INFORMATIVE = 6


def _content(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z']+", (text or "").lower())
            if w not in STOP and len(w) > 3]


def _bigrams(words: list[str]) -> set[str]:
    return {f"{a} {b}" for a, b in zip(words, words[1:])}


def sha(text: str) -> str:
    """Identity of a block is its prose. Re-word it and the waiver lapses."""
    return hashlib.sha256(" ".join((text or "").split()).encode()).hexdigest()[:12]


def load_reviews() -> dict:
    try:
        with open(REVIEWS) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_reviews(data: dict) -> None:
    with open(REVIEWS, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")


def cohort(items: tuple[str, ...]) -> dict[tuple[str, int, str], str]:
    """Every non-empty response field the graders read, keyed by where it came from."""
    import agreement as A
    out: dict[tuple[str, int, str], str] = {}
    for item in items:
        for pid in range(1, 21):
            try:
                fixture = A.fixture_for(item, pid)
            except Exception:
                continue
            for field, value in (fixture or {}).items():
                if (value or "").strip():
                    out[(item, pid, field)] = value.strip()
    return out


def _specs() -> dict[str, dict]:
    """Every rubric item across the three handouts, keyed by id."""
    import handouts as H
    out: dict[str, dict] = {}
    for h in (1, 2, 3):
        try:
            for item in H.config(h)["rubric"].ITEMS:
                out[item["id"]] = item
        except Exception:
            continue
    return out


def authored(items: tuple[str, ...]) -> dict[str, str]:
    """Every block of prose we wrote that reaches a grader."""
    specs = _specs()
    blocks: dict[str, str] = {}
    for item in items:
        spec = specs.get(item) or {}
        guidance = spec.get("guidance") or []
        for g in (guidance if isinstance(guidance, list) else [guidance]):
            blocks[f"{item} guidance :: {str(g)[:52]}"] = str(g)
        for r in spec.get("rules") or []:
            blocks[f"{item} rule :: {str(r)[:52]}"] = str(r)
        # `desc` and `rule` on a credit line are prompt text too, and three of
        # the leaks found here lived there rather than in guidance.
        for c in spec.get("credit") or []:
            for field in ("desc", "rule"):
                if c.get(field):
                    blocks[f"{item} credit.{field} :: {str(c[field])[:52]}"] = str(c[field])
    try:
        import olx_prompts as OP
        for key, note in (getattr(OP, "SLOT_NOTES", {}) or {}).items():
            blocks[f"SLOT_NOTES {key}"] = str(note)
    except Exception:
        pass
    return blocks


def _domain_words(items: tuple[str, ...]) -> set[str]:
    """Words the ASSIGNMENT uses, which authored prose cannot avoid re-using.

    Drawn from the items' own question text and the four type definitions rather
    than a hand-kept list, so it cannot go stale: if the handout says it, both
    sides must say it, and it is not a leak however specific it looks.
    """
    specs = _specs()
    txt = " ".join(str((specs.get(i) or {}).get("question") or "") for i in items)
    try:
        import rubric_h2 as R2
        txt += " " + R2._OC_FRAME
    except Exception:
        pass
    return set(_content(txt))


def _segments(text: str) -> list[str]:
    """Sentence-ish units, normalised, for deciding what counts as OUR OTHER prose.

    The unit matters: with the block as the unit, a paragraph duplicated across
    two blocks is "elsewhere" for both and neither copy is ever checked. With the
    sentence as the unit, a shared sentence is excluded from the evidence of every
    block that contains it, so it has to be vouched for by prose that is genuinely
    somewhere else.
    """
    import re as _re
    out = []
    for s in _re.split(r"(?<=[.!?])\s+|\n+", text or ""):
        s = " ".join(s.split())
        if len(s) > 12:
            out.append(s)
    return out or ([" ".join((text or "").split())] if text else [])


def word_findings(items: tuple[str, ...]) -> list[dict]:
    """Authored blocks re-using a CONCRETE word from a few students' answers.

    Complements `findings`, which needs a shared PAIR. A rule that lists the very
    objects the cohort wrote about is teaching to the test one noun at a time.
    """
    responses = cohort(items)
    students: dict[str, set[int]] = {}
    for (_item, pid, _f), text in responses.items():
        for w in set(_content(text)):
            students.setdefault(w, set()).add(pid)
    domain = _domain_words(items)
    reviews = load_reviews()
    blocks = authored(items)
    # OUR OWN vocabulary, derived rather than hand-kept: every word used in some
    # OTHER authored block. Rarity alone is not informativeness -- with twenty
    # students and short answers, ordinary English words like "already" or
    # "cannot" appear in only a handful, and flagging those buried the real cases
    # 196 blocks deep. A word we use elsewhere in our own prose is ours; a word
    # that appears NOWHERE else in it, and does appear in a few students'
    # answers, is theirs. That is what separates "phone" and "procrastinating"
    # from "activity".
    # OUR OWN prose has to be prose THIS BLOCK DOES NOT CONTAIN, or duplicated
    # text vouches for itself and can never be flagged. Measured before fixing:
    # 139 of 301 blocks carry a full text that also appears verbatim in another
    # block, and 114 sentences appear in more than one block, filling 526 block
    # slots -- the four-type operant definition alone sits in twelve. Under the
    # old per-block union every word of all of that was "elsewhere", so nearly
    # half the authored prose was exempt from the check that exists to police it.
    # `_MOVE_RULE` sat unchecked in four prompts for exactly this reason.
    #
    # Sentence granularity, not block: a paragraph shared between two otherwise
    # different blocks would still vouch for itself if the unit were the block.
    seg_words: dict[str, set[str]] = {}
    block_segs: dict[str, set[str]] = {}
    for lbl, t in blocks.items():
        ss = _segments(t)
        block_segs[lbl] = set(ss)
        for sg in ss:
            seg_words.setdefault(sg, set()).update(_content(sg))
    out: list[dict] = []
    for label, text in blocks.items():
        mine = block_segs.get(label, set())
        elsewhere = set().union(*(w for sg, w in seg_words.items() if sg not in mine)) \
            if any(sg not in mine for sg in seg_words) else set()
        rare = sorted(
            w for w in set(_content(text)) & set(students)
            if w not in domain and w not in elsewhere
            and len(students[w]) <= MAX_STUDENTS_FOR_INFORMATIVE)
        if len(rare) < 2:
            continue
        h = sha(text)
        out.append({"label": label, "sha": h, "text": text, "kind": "word",
                    "shared": rare, "hits": len(rare),
                    "owners": {w: sorted(students[w]) for w in rare},
                    "review": reviews.get(h)})
    out.sort(key=lambda f: -f["hits"])
    return out


def findings(items: tuple[str, ...]) -> list[dict]:
    """Flagged blocks, worst concentration first, each tagged with its review."""
    responses = cohort(items)
    students: dict[str, set[int]] = {}      # bigram -> distinct participant ids
    where: dict[str, set[str]] = {}         # bigram -> "ITEM/pN" labels
    for (item, pid, _field), text in responses.items():
        for b in _bigrams(_content(text)):
            students.setdefault(b, set()).add(pid)
            where.setdefault(b, set()).add(f"{item}/p{pid}")

    reviews = load_reviews()
    out: list[dict] = []
    for label, text in authored(items).items():
        shared = _bigrams(_content(text)) & set(students)
        # Only bigrams no other student used. Anything two students wrote is the
        # handout's language, however striking it looks.
        exclusive: dict[int, list[str]] = {}
        for b in shared:
            if len(students[b]) == 1:
                exclusive.setdefault(next(iter(students[b])), []).append(b)
        if not exclusive:
            continue
        top_pid, own = max(exclusive.items(), key=lambda kv: len(kv[1]))
        if len(own) < MIN_EXCLUSIVE:
            continue
        h = sha(text)
        out.append({
            "label": label, "sha": h, "text": text,
            "shared": sorted(own),
            "owners": {b: sorted(where[b]) for b in sorted(own)},
            "top_participant": top_pid, "hits": len(own),
            "review": reviews.get(h),
        })
    out.sort(key=lambda f: -f["hits"])
    return out


def unreviewed(items: tuple[str, ...] = CADENCE) -> list[str]:
    """One line per flagged block with no standing verdict. The gate's payload.

    AUDITS EVERY ITEM and ignores `items`, for the reason spelled out on `gate`:
    both filters that decide a flag are computed over the scope given, so a
    narrow scope makes ordinary English look borrowed. Every enforcement caller
    -- the sweep gate and `measured.py --preflight` -- comes through here, so
    they cannot disagree about whether the same prose is clean.
    """
    items = tuple(_specs())
    pending = [f"{f['label']}  [sha {f['sha']}] — {f['hits']} bigram(s) "
               f"used by p{f['top_participant']} and no other student"
               for f in findings(items) if not f["review"]]
    pending += [f"{f['label']}  [sha {f['sha']}] — {f['hits']} concrete word(s) "
                f"from few students' answers: "
                + ", ".join(f"{w} (p{'/p'.join(str(x) for x in f['owners'][w][:3])})"
                            for w in f["shared"][:4])
                for f in word_findings(items) if not f["review"]]
    return pending


def gate(items: tuple[str, ...], stream=sys.stderr) -> int:
    """0 to proceed, 1 to refuse. Called before a sweep spends anything.

    AUDITS EVERY ITEM, whatever is being swept. The `items` argument is kept for
    the caller's convenience and deliberately ignored, because both filters that
    decide a flag are computed OVER THE SCOPE GIVEN: `_domain_words` from the
    items' question text, and `ours` from the other authored blocks in scope.
    Narrow the scope and ordinary English stops looking ordinary -- auditing WK1
    alone flagged "work", "food", "healthy" and "should" as concrete borrowings,
    because no other block in scope used them. The same prose passes at ALL.
    A leak is a leak whatever is being measured, so the audit does not narrow.
    """
    pending = unreviewed()
    if not pending:
        return 0
    print(f"REFUSING to sweep: {len(pending)} rule block(s) share wording with "
          f"the cohort and have no recorded verdict.", file=stream)
    for line in pending:
        print(f"    {line}", file=stream)
    print("\nRead each one against the responses it echoes "
          f"(python3 leakage.py --items {','.join(items)}), then either rewrite "
          "the borrowed example or file a verdict:\n"
          "    python3 leakage.py --review <sha> --verdict vocabulary "
          "--note 'why this is not a quotation'\n"
          "Verdicts are keyed to the prose, so re-wording the block asks again.",
          file=stream)
    return 1


def report(items: tuple[str, ...], show_all: bool = False) -> int:
    found = findings(items)
    print(f"{len(cohort(items))} response fields over {len(items)} item(s); "
          f"{len(authored(items))} authored blocks; {len(found)} flagged\n")
    for f in found:
        if f["review"] and not show_all:
            continue
        mark = f"reviewed:{f['review']['verdict']}" if f["review"] else "UNREVIEWED"
        print(f"[{mark}] {f['label']}")
        print(f"    sha {f['sha']} — {f['hits']} bigram(s) used by "
              f"p{f['top_participant']} and by no other student")
        for b in f["shared"]:
            owners = f["owners"][b]
            tail = "" if len(owners) <= 6 else f" (+{len(owners) - 6} more)"
            print(f"      {b!r:32} {', '.join(owners[:6])}{tail}")
        if f["review"]:
            print(f"    verdict: {f['review'].get('note', '')}")
        print()
    pending = [f for f in found if not f["review"]]
    print(f"{len(pending)} unreviewed; {len(found) - len(pending)} with a "
          f"standing verdict.")
    return 1 if pending else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--items", default=",".join(CADENCE),
                    help="comma-separated item ids, or ALL")
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 with the refusal message if anything is unreviewed")
    ap.add_argument("--all", action="store_true",
                    help="show blocks that already have a verdict too")
    ap.add_argument("--review", metavar="SHA",
                    help="file a verdict against a flagged block")
    ap.add_argument("--verdict", choices=VERDICTS,
                    help="vocabulary | coincidence | rewritten")
    ap.add_argument("--note", default="",
                    help="why this is not a quotation — required with --review")
    args = ap.parse_args()

    if args.items.upper() == "ALL":
        items = tuple(_specs())
    else:
        items = tuple(x.strip() for x in args.items.split(",") if x.strip())

    if args.review:
        if not args.verdict or not args.note.strip():
            ap.error("--review needs --verdict and a --note saying why")
        # BOTH checks, not just the bigram one. The word check can flag a block
        # and the gate refuses on it, but `--review` looked only at `findings()`,
        # so a word finding could block every sweep with no way to file a verdict
        # for it. It never bit while the word check was suppressing duplicated
        # prose; widening that check surfaced 43 findings and the jam with them.
        known = {f["sha"]: f["label"] for f in findings(items) + word_findings(items)}
        if args.review not in known:
            ap.error(f"no flagged block with sha {args.review} in {','.join(items)}")
        data = load_reviews()
        data[args.review] = {"label": known[args.review],
                             "verdict": args.verdict, "note": args.note.strip()}
        save_reviews(data)
        print(f"recorded {args.verdict} for {known[args.review]}")
        return 0

    return gate(items) if args.gate else report(items, args.all)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    raise SystemExit(main())
