"""Score Handout 1 submissions, one rubric item at a time.

Design notes:
  * One call per rubric item, not one per document. Each item has its own
    point ledger and its own feedback cell, and the gold data is per-item, so
    per-item calls are both more accurate and directly measurable.
  * The model never returns a score. It returns credit checks and a deduction
    ledger; the score is computed here as max - sum(deductions), clamped to
    [0, max]. That mirrors how these graders actually write ("-1 pt: ...") and
    makes every point auditable.
  * Items are scored in dependency order, because several are graded against
    other items: Q2's WGB against Q1's UTB, Q4b/Q4c against Q4a for
    distinctness, and Q6 against 4a and 4c for matching. Neighbours listed in
    a rubric record's `context` are passed in as read-only context.

Usage:
  python3 score_h1.py                       # score all 20, CLI backend
  python3 score_h1.py --participants 1 2 3   # subset
  python3 score_h1.py --backend api          # official SDK (needs creds)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from backends import BackendError, make_backend
from rubric_h1 import BY_ID, ITEMS
from segment import H1_MARKERS, segment, utb_hint
import paths

TEMPLATE = f"{paths.MATERIALS}/BMod Handout #1 - Defining Behaviors, ABCs, and SMART Goals.docx"
SUBMISSIONS = f"{paths.SUBS}/Handout 1 Submissions with Scoring and Feedback"
OUTDIR = f"{paths.OUT}/h1"

SYSTEM = """You are an experienced teaching assistant grading Handout 1 of the \
Behavior Modification Assignment in PSYC 1030 (General Psychology, intro level, \
first-year students).

You grade ONE rubric item at a time against the rubric supplied in the message.

Rules you must follow:
1. Award credit component by component. For each component in the rubric's
   credit list, decide whether the student's response earns it, and quote the
   span of the response that earns it. Quote verbatim; never paraphrase into
   the evidence field.
2. Report every failure as a deduction drawn from the supplied deduction list,
   using that list's exact `code` and `pts`. A deduction marked repeatable may
   appear more than once (e.g. two missing reasons = two REASON_MISSING
   entries). Do not invent codes.
3. Do NOT output a score. The score is computed from your deduction ledger.
4. Total deductions must be consistent with the credit components you marked
   unmet: if you mark a 2-point component unmet, there must be a deduction
   accounting for it.
5. Grade what is written, generously but not charitably: these are first-year
   students, so clumsy phrasing that clearly conveys the required idea earns
   credit, but a required element that is absent is absent.
6. If the response is empty, mark every component unmet and use the item's
   "none"/"did not answer" deduction code.
7. Set safety_flag true only if the student describes something that could
   harm them (skipping meals, punishing themselves by withholding food or
   sleep, etc.). This never changes the score.
8. Set escalate true when no supplied deduction code fits what is wrong, when
   the response is off-topic or incoherent, or when you are genuinely unsure.

Return only the JSON object required by the schema."""

SCHEMA = {
    "type": "object",
    "properties": {
        "item_id": {"type": "string"},
        "credit_checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "what": {"type": "string"},
                    "met": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "required": ["what", "met", "evidence"],
                "additionalProperties": False,
            },
        },
        "deductions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "pts": {"type": "number"},
                    "note": {"type": "string"},
                },
                "required": ["code", "pts", "note"],
                "additionalProperties": False,
            },
        },
        "advisory_note": {"type": ["string", "null"]},
        "safety_flag": {"type": "boolean"},
        "escalate": {"type": "boolean"},
    },
    "required": [
        "item_id",
        "credit_checks",
        "deductions",
        "advisory_note",
        "safety_flag",
        "escalate",
    ],
    "additionalProperties": False,
}


def build_schema(item: dict) -> dict:
    """Schema for one item.

    For an item marked `derive_from_credit`, the model does not author a
    deduction ledger at all. It fills in one fixed slot object per credit
    component, and `score_item` derives the ledger from the unmet slots. The
    slots are *required object properties*, so "did the model remember to
    check slot 7" stops being a prompt-following question and becomes a schema
    constraint. (Q6's failure mode in baseline v3 was exactly that: gold
    implied 50 failed slots across the cohort and the model volunteered 31.)
    """
    if not item.get("derive_from_credit"):
        return SCHEMA

    slot = {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["met", "absent", "mismatch", "not_described"],
            },
            "evidence": {"type": "string"},
        },
        "required": ["verdict", "evidence"],
        "additionalProperties": False,
    }
    slots = {c["what"]: slot for c in item["credit"]}
    schema = json.loads(json.dumps(SCHEMA))  # deep copy
    del schema["properties"]["credit_checks"]
    del schema["properties"]["deductions"]
    schema["properties"]["slots"] = {
        "type": "object",
        "properties": slots,
        "required": list(slots),
        "additionalProperties": False,
    }
    schema["required"] = [
        r for r in schema["required"] if r not in ("credit_checks", "deductions")
    ] + ["slots"]
    return schema


def derive_ledger(item: dict, raw: dict) -> tuple[list[dict], list[dict], list[str]]:
    """Turn a slot verdict sheet into a deduction ledger.

    One slot, one deduction, by construction — the stacking that produced
    participant 9's double-penalty in baseline v1 is unrepresentable here.
    """
    slots = raw.get("slots") or {}
    ledger, checks, unknown = [], [], []
    for comp in item["credit"]:
        got = slots.get(comp["what"]) or {}
        verdict = got.get("verdict", "absent")
        evidence = got.get("evidence", "")
        met = verdict == "met"
        checks.append({"what": comp["what"], "met": met, "evidence": evidence})
        if met:
            continue
        code = comp.get("codes", {}).get(verdict)
        if code is None:
            # Verdict that does not apply to this slot (e.g. "mismatch" on a
            # change slot). Fall back to the slot's own primary code.
            code = next(iter(comp.get("codes", {}).values()), None)
            if code is None:
                unknown.append(f"{comp['what']}:{verdict}")
                continue
        ledger.append({"code": code, "pts": comp["pts"], "note": evidence})

    # Nothing at all was answered: report it the way the graders did, as a
    # single "did not answer", rather than as eight separate slot failures.
    if len(ledger) == len(item["credit"]):
        none_code = next(
            (d for d in item["deductions"] if d["text"] == "did not answer"), None
        )
        if none_code:
            ledger = [{"code": none_code["code"], "pts": none_code["pts"], "note": ""}]
    return ledger, checks, unknown


def build_prompt(item: dict, response: str, context: dict[str, str], hint: str | None) -> str:
    parts = [f"# Rubric item {item['id']} — {item['max']:g} points\n"]
    parts.append(f"## Question asked of the student\n{item['question']}\n")

    if item.get("derive_from_credit"):
        parts.append(
            "## Slots to judge — return a verdict for EVERY one of these\n"
            "Each slot is worth "
            f"{item['credit'][0]['pts']:g} points and is judged independently."
        )
        for c in item["credit"]:
            parts.append(f"- `{c['what']}`: {c['desc']}")
        parts.append(
            "\nVerdicts: `met`, `absent` (not there at all), `mismatch` (present but a "
            "different antecedent/consequence than 4a/4c lists), `not_described` (the "
            "element is named but nothing is said about how it changes or is affected). "
            "Quote the span you relied on in `evidence`; for an absent slot, say briefly "
            "what you looked for. Do not output a score or a deduction list — the score "
            "is computed from these verdicts.\n"
        )
    else:
        parts.append("## Credit components")
        for c in item["credit"]:
            parts.append(f"- `{c['what']}` ({c['pts']:g} pt): {c['desc']}")
        parts.append("")

        parts.append("## Deduction codes (use these exact codes and point values)")
        for d in item["deductions"]:
            rep = " [repeatable]" if d.get("repeatable") else ""
            parts.append(f"- `{d['code']}` (-{d['pts']:g}){rep}: {d['text']}")
        parts.append("")

    parts.append("## Grading guidance")
    for g in item["guidance"]:
        parts.append(f"- {g}")
    parts.append("")

    if item.get("exemplars"):
        parts.append(
            "## Worked examples\n"
            "Three responses from other students in this cohort, with the verdict sheet "
            "the human grader's marks imply. Match your judgements to these. They are "
            "reference material only — never grade them."
        )
        for ex in item["exemplars"]:
            parts.append(f"\n### {ex['label']}")
            parts.append(f"Their 4a: {ex['four_a']}")
            parts.append(f"Their 4c: {ex['four_c']}")
            parts.append(f"Their answer: {ex['response']}")
            verdicts = ", ".join(f"{k}={v}" for k, v in ex["slots"].items())
            parts.append(f"Verdicts: {verdicts}")
            parts.append(f"Why: {ex['note']}")
        parts.append("")

    if context:
        parts.append("## Context from this student's other answers (read-only)")
        parts.append(
            "Use these only where the rubric requires cross-item consistency. "
            "Do not grade them here."
        )
        for k, v in context.items():
            body = v.strip() or "(no response)"
            parts.append(f"\n### {k}\n{body}")
        parts.append("")

    if hint and item["id"] in ("Q1", "Q2"):
        parts.append(
            f"## Weak hint\nFormatting in the document marks '{hint}' as the "
            "underlined UTB choice. Only 6 of 20 transcriptions preserve this "
            "markup, so treat it as corroboration at most — read the UTB from "
            "the prose.\n"
        )

    body = response.strip() or "(the student left this item blank)"
    parts.append(f"## Student response to grade (item {item['id']})\n{body}")
    return "\n".join(parts)


_LEADING_PTS = re.compile(r"^-\s*[\d.]+\s*pts?\s*:\s*", re.I)


def compose_feedback(item: dict, result: dict) -> str:
    """Build the grader-style feedback string from the deduction ledger.

    Matches the graders' house style: a "-N pts: reason" ledger, second person,
    canonical dictionary wording. Some dictionary entries already carry their
    own "-1 pt:" prefix, so strip it before adding ours rather than emitting
    "-1 pts: -1 pt: ...".
    """
    texts = {d["code"]: d["text"] for d in item["deductions"]}
    chunks = []
    for d in result.get("deductions", []):
        canonical = _LEADING_PTS.sub("", texts.get(d["code"], "")).strip()
        note = (d.get("note") or "").strip()
        if canonical == "did not answer":
            chunks.append("did not answer")
            continue
        line = f"-{float(d['pts']):g} pts: {canonical}"
        if note and note.lower() not in canonical.lower():
            line += f" {note}"
        chunks.append(line)

    # The graders leave the feedback cell blank on full credit. Carry an
    # advisory note into the visible feedback only when something was actually
    # deducted, or when it is a safety note — otherwise keep it in its own
    # field so it does not read as a criticism of a perfect answer.
    adv = (result.get("advisory_note") or "").strip()
    if adv and (chunks or result.get("safety_flag")):
        chunks.append(adv)
    return " ".join(chunks).strip()


def score_item(backend, item: dict, response: str, context: dict, hint) -> dict:
    prompt = build_prompt(item, response, context, hint)
    raw = backend.complete(SYSTEM, prompt, build_schema(item))

    if item.get("derive_from_credit"):
        # `response` for the same reason score.py passes it: the blank-answer
        # collapse must only fire on an answer that is actually blank.
        ledger, checks, unknown = derive_ledger(item, raw, response)
    else:
        valid = {d["code"]: d for d in item["deductions"]}
        ledger, unknown = [], []
        for d in raw.get("deductions", []):
            spec = valid.get(d.get("code"))
            if spec is None:
                unknown.append(d.get("code"))
                continue
            # Trust the rubric's point value, not the model's arithmetic.
            ledger.append(
                {"code": spec["code"], "pts": spec["pts"], "note": d.get("note", "")}
            )
        checks = raw.get("credit_checks", [])

    # An item cannot fail more slots than it has. Q6 in particular is eight
    # independent 1.25-point slots, and the failure mode observed in the first
    # baseline was stacking two codes on one slot (participant 9 drew five
    # deductions where the grader made two). Keep the largest deductions up to
    # the number of credit components and escalate rather than silently
    # over-deducting.
    over_specified = False
    if len(ledger) > len(item["credit"]):
        ledger = sorted(ledger, key=lambda d: -d["pts"])[: len(item["credit"])]
        over_specified = True

    total_off = sum(d["pts"] for d in ledger)
    score = max(0.0, min(item["max"], item["max"] - total_off))

    return {
        "item_id": item["id"],
        "label": item["label"],
        "max": item["max"],
        "score": round(score, 2),
        "deductions": ledger,
        "unknown_codes": unknown,
        "credit_checks": checks,
        "feedback": compose_feedback(
            item,
            {
                "deductions": ledger,
                "advisory_note": raw.get("advisory_note"),
                "safety_flag": raw.get("safety_flag"),
            },
        ),
        "advisory_note": raw.get("advisory_note"),
        "safety_flag": bool(raw.get("safety_flag")),
        "over_specified": over_specified,
        "escalate": bool(raw.get("escalate")) or bool(unknown) or over_specified,
        "response_chars": len(response.strip()),
    }


def score_participant(
    backend, path: str, pid: int, only: list[str] | None = None, outdir: str = OUTDIR
) -> dict:
    """Score one participant. `only` re-scores a subset of items and merges the
    results into that participant's existing file, so a guidance change can be
    re-measured without paying to re-run items it did not touch."""
    sections = segment(path, TEMPLATE, H1_MARKERS)
    hint = utb_hint(path)
    results: dict[str, dict] = {}

    prior_path = os.path.join(outdir, f"participant_{pid:03d}.json")
    if only and os.path.exists(prior_path):
        with open(prior_path) as fh:
            for it in json.load(fh)["items"]:
                results[it["item_id"]] = it

    # Dependency order: an item is scored only after everything in its
    # `context` has been segmented (segmentation is complete up front, so
    # this ordering exists to make the context passing explicit and to keep
    # room for future context that depends on a scored result).
    for item in ITEMS:
        if only and item["id"] not in only:
            continue
        ctx = {k: sections.get(k, "") for k in item["context"]}
        try:
            results[item["id"]] = score_item(
                backend, item, sections.get(item["id"], ""), ctx, hint
            )
        except BackendError as e:
            results[item["id"]] = {
                "item_id": item["id"],
                "label": item["label"],
                "max": item["max"],
                "score": None,
                "error": str(e),
                "escalate": True,
                "response_chars": len(sections.get(item["id"], "").strip()),
            }

    scored = [
        results[it["id"]]["score"]
        for it in ITEMS
        if results.get(it["id"], {}).get("score") is not None
    ]
    return {
        "participant_id": pid,
        "handout": 1,
        "source_file": os.path.basename(path),
        "scored_total": round(sum(scored), 2),
        "scored_max": sum(it["max"] for it in ITEMS),
        "upload_points": None,  # not derivable from the response — see README
        "items": [results[it["id"]] for it in ITEMS if it["id"] in results],
        "utb_format_hint": hint,
    }


def find_submissions(pids: list[int] | None) -> list[tuple[int, str]]:
    out = []
    for f in sorted(glob.glob(os.path.join(SUBMISSIONS, "*.docx"))):
        m = re.search(r"ID\s*(\d+)", os.path.basename(f))
        if not m:
            continue
        pid = int(m.group(1))
        if pids and pid not in pids:
            continue
        out.append((pid, f))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="cli", choices=["cli", "api"])
    ap.add_argument("--participants", type=int, nargs="*", default=None)
    ap.add_argument(
        "--items",
        nargs="*",
        default=None,
        help="Re-score only these item ids, merging into existing output files.",
    )
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--max-budget-usd", type=float, default=None)
    ap.add_argument("--outdir", default=OUTDIR)
    args = ap.parse_args()

    kw = {}
    if args.backend == "cli" and args.max_budget_usd:
        kw["max_budget_usd"] = args.max_budget_usd
    backend = make_backend(args.backend, **kw)

    os.makedirs(args.outdir, exist_ok=True)
    targets = find_submissions(args.participants)
    n_items = len(args.items) if args.items else len(ITEMS)
    scope = f" ({', '.join(args.items)} only, merging)" if args.items else ""
    print(
        f"scoring {len(targets)} participant(s) x {n_items} items{scope}", file=sys.stderr
    )

    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(
                score_participant, backend, path, pid, args.items, args.outdir
            ): pid
            for pid, path in targets
        }
        for fut in as_completed(futs):
            pid = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:  # keep going; one bad file must not stop the run
                print(f"  participant {pid}: FAILED {e}", file=sys.stderr)
                continue
            with open(os.path.join(args.outdir, f"participant_{pid:03d}.json"), "w") as fh:
                json.dump(rec, fh, indent=2)
            done += 1
            esc = sum(1 for i in rec["items"] if i.get("escalate"))
            print(
                f"  [{done}/{len(targets)}] participant {pid:>2}: "
                f"{rec['scored_total']:>5.2f}/{rec['scored_max']:g}"
                + (f"  ({esc} escalated)" if esc else ""),
                file=sys.stderr,
            )

    dt = time.time() - t0
    cost = getattr(backend, "total_cost_usd", None)
    print(
        f"done in {dt:.0f}s, {backend.calls} calls"
        + (f", ${cost:.2f}" if cost else ""),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# --- corpus reference resolution (backdated) ---
# The paper prompt is assembled from rubric guidance, which may cite a cell by
# reference. Unresolved, the grader is asked to score the reference itself.
try:                                            # pragma: no cover
    import corpus_resolve as _corpus_resolve
    _corpus_orig_build_prompt = build_prompt

    def build_prompt(*a, _orig=_corpus_orig_build_prompt, **kw):
        return _corpus_resolve.expand(_orig(*a, **kw))
except Exception:
    pass
