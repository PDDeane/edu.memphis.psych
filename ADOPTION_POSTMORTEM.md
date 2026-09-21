# Adopting the rewritten history broke the scorer — 2026-09-21

The histories are sound. The WORKING TREES built from them are not. Both facts
are established by measurement and neither cancels the other.

## What was adopted

    live psych      00e09d8   509 commits   refs/preadopt/* holds 4be35ce, 3198bce
    live lo-blocks  c2c282d0  + 8 grafted   refs/preadopt/* holds the originals
    dry run         86959bb   611 commits   refs/preadopt/* holds 789d18c

Scrubbing is proven, with controls that fire: live psych 0 student 8-grams
against 1,655 on the pre-adoption history; the dry run 0 against 1,655;
`prove_sha_paired` 41,861 of 41,861 file-versions expanding to the original,
0 mismatches, 0 paths missing.

## What broke, and it is one cause wearing three faces

Reference substitution is TEXT-LEVEL. It cannot see whether the text it replaces
is inert prose or a load-bearing token. Measured across both trees:

| where the reference landed | count | effect |
|---|---|---|
| bare JSON array element | 1 | the file stops parsing -- LOUD |
| dict KEY in a live lookup | 12 | wrong match, wrong value -- SILENT |
| string value, docstring, comment | ~98 | inert |

    scoring/MEASURED.json    run_totals: [8, 10, 11, 11, 11, 13] -- the repo's OWN
                             sweep counts, matched because the digit run happens to
                             equal a student's wk2 series. NOT student data.
    scoring/precommit_gate.py   11 dict keys -- the hook that BLOCKS student text
                             from being committed, its own detection table rewritten
                             into references it does not resolve.
    scoring/agreement_app.py    UTB_CHOICES, one of four closed-choice values
                             `detect_utb` returns as the fixture the web block gets.

Consequence, from the audit once MEASURED.json was repaired enough to let it run:
101 findings against a pre-adoption baseline of 1. Of those, 52 are the expected
`OLX QUOTES A STUDENT THROUGH A REFERENCE` concession ledger; 34 are ENGINES
SEND DIFFERENT PROMPTS / A DIFFERENT REQUEST -- the harness resolves references
(it carries the shim), `agreement_app.py` does not (it never got one), so the two
sides send different text. Q1 15,493 chars vs 15,606; 1c 13,669 vs 13,825.

## Why seven instruments reported clean

* the byte proof compares bytes AFTER expansion, and expansion is exact;
* corpus scans use WORD 8-grams -- `"10, 11, 11, 11"` yields none;
* the substitution is reversible, so it is "correct" by every definition the
  rewrite had;
* the self-test could not run at all (the ledger would not load), so it reported
  nothing rather than reporting a failure;
* `enforcement_audit` itself raised JSONDecodeError before its first finding.

In the state the rewrite produced, calling one check directly was the ONLY way to
learn anything. Expansion fidelity and USABILITY are different properties and
only the first was ever tested.

## The two gates that close it

1. `check_rewritten_artifacts_still_parse` -- every .json parses, every .py
   compiles. WRITTEN, wired into `enforcement_audit`, and it found the real defect
   on its first run rather than on a synthetic one.
2. Scorer equivalence must be green BEFORE adoption, not discovered after. The 34
   engine findings were always going to appear; nothing asked them in time.

Neither existed when the adoption was made. That is the process defect, and it is
larger than the substitution bug.

## Rollback

Six `update-ref` calls, nothing lost -- every history is bundled in ~/backups and
independently restore-tested:

    git -C ~/code/edu.memphis.psych update-ref refs/heads/pdeane/bmod-scoring-project 4be35ce
    git -C ~/code/edu.memphis.psych update-ref refs/heads/main 3198bce
    ... and the equivalents from refs/preadopt/* in lo-blocks and the dry run

## What re-adoption needs

A position-aware substitution rule -- never replace outside a string literal, and
never replace a dict key -- then re-run the rewrite, then BOTH gates green, then
adopt. Not the reverse order, which is what happened here.
