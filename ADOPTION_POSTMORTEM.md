# Adopting the rewritten history — what broke, and how it was fixed

**RESOLVED 2026-09-21.** All three trees now carry revised, scrubbed histories and
every gate passes. The record below is kept in full because the ORDER of events is
the lesson: adoption went first and the gates second, and every defect after that
was found by putting those back the right way round.

    live psych      01a77d0   509 commits   CERTIFIED
    dry run         de1cd704  616 commits   CERTIFIED 72/72, descends from live
    live lo-blocks  542bbb9c  590 commits, main + our 9 branches
    corpus export   2,586 spans (was 2,575), backed up
    bundles         ~/backups/{psych,loblocks,dryrun}-FINAL-20260921

    certifying self-test: 72 detected, 0 failed, 0 skipped, 0 vacuous,
                          restored state clean, baseline 52

## The baseline is 52, and both entries are DECLARED

    51  OLX QUOTES A STUDENT THROUGH A REFERENCE
     1  MIGRATED MODULE HOLDS COURSE DATA   (D2a, parked with its reason)

It was 1 before any of this, and 99 at the worst. The 51 are the rewrite's
concession ledger -- one per worked example that is still a real student answer,
ratcheting DOWN only as each is replaced with an invented one. A clean
certification shows 52. That is the designed state, not a debt.

## From 99 to 52: five more defects, four of them ours

1. THE APP AND THE HARNESS GRADED DIFFERENT TEXT -- 34 findings. The rewrite
   injects its resolver shim BY CONTENT SIGNATURE (`_olx` + `prompt_sha`,
   `build_prompt` + `derive_ledger`, `build_web_prompt`), and two readers matched
   none of them: `agreement.load_action`, and the lo-blocks dev server. Fixing
   only the app made it worse in a NEW way -- all 17 items then differed, because
   the app resolved and the harness did not. THE FINDING IS THE SELECTION RULE,
   not the two names: any future .olx reader of a different shape is skipped the
   same way, silently.

2. A DESIGN SHA WAS ABOUT ENCODING, NOT WORDS -- 7 fields that quote a student
   reported CHANGED with no word altered. `--accept-design-change` would have
   recorded the REFERENCE as the design, after which a real wording edit inside
   those fields would move no sha at all. `_field_sha` resolves before hashing.

3. THE REWRITE PUT A RETIRED VARIABLE NAME BACK -- the injected frontmatter said
   `$MOLLY_DATA`; Stage 9 renamed it and `paths._RENAMED` still honours the old
   one, which is exactly why writing it went unnoticed. It works. The point is
   what happens when the fallback goes: an empty result.

4. THE STAGE CARRIED WHAT NEVER RENDERS -- `.stage/content` copied the scoring
   package, the migrated rubric and the migration scripts: 3 files, 100
   unresolved references, none renderable.

5. A DOCSTRING GREW A RATCHET -- the fix for (2) named the seven affected fields,
   embedding course data in a migrated module and moving the count 10 -> 11. It
   counts them now instead of naming them.

## Two more instrument artifacts -- five for the night

* THE PROOF RUN AGAINST AN ADOPTED LIVE. `prove_sha_paired` hardcodes
  `ORIG=~/code/edu.memphis.psych`; live was still on the previous rewrite, so it
  compared rewritten with rewritten -- 3,070 mismatches and a scope 506
  file-versions too large. Rolling live back to the original is a step that must
  be taken EVERY time.
* A PROOF READING FOR A STRING THE FILTER NO LONGER EMITTED. Line 80 held
  `corpus_data: $MOLLY_DATA/...` literally, to strip the declaration the rewrite
  adds. Changing the filter left the proof unable to strip it, so every handout
  version differed by that one line: 456 x 3 = 1,368. The filter and the proof
  are coupled by a hardcoded string and nothing declares it.

A hardening for the second -- recognise both spellings -- broke 3 file-versions
in BOTH trees and was reverted. Not every hardening is an improvement.

## The re-cut drops commits that are not on its source lineage

Twice now. A re-cut replays the ORIGINAL 102 and every commit made since must be
cherry-picked by hand; the first round lost 2 and the second lost 2 more, both
times documentation rather than code, and only because the file looked short.
`ccc7b7c..<current tip>` is NOT the way to find them -- after a re-cut every sha
is new, so that range returns the whole rewritten history (617 where the answer
was 102). Compare by SUBJECT against the branch, which is how both losses were
found.

## lo-blocks, finished separately -- two decisions and one more defect

RE-RUN WITH THE BACKFILLS OFF. `BACKFILL_CONTENT` and `BACKFILL_PLOTS` repair
historical states so they parse with the CURRENT engine, and for psych they earn
it: `tier2_build.sh` builds those states and they fail without it. lo-blocks' own
old states ARE built and tested -- `sweep_lo_states.sh` runs 54 of them -- so the
question was real. Measured: 29 states carry 3,463 old-style chatpeg arrows, and
13 test/script files mention a `.chatpeg` path, but ALL 13 are path handling
(fileTypes, contentPaths, loadContentTree listing the tree, xml2json with its own
fixtures). Nothing parses a chatpeg with the grammar. The fix would have bought
nothing at the cost of 746 declared-irreversible differences against a history
that otherwise carries 23. Off: scrubbed drops 81 -> 2.

A `D <dir>` THAT WIPES AN `M` FROM THE SAME COMMIT. `fast-import` applies a
commit's operations IN ORDER and `fast-export` emitted the write first:

    M 100644 <sha> content/linear-algebra/eigenvalues/lesson1.xml
    D content

-- a move out of `public/` whose directory delete then erased the file the line
above had just written. It vanished for six commits and returned when something
next touched it. The source repository has no such gap; git's tree model resolves
that commit differently from a literal replay, so this is an export/import
round-trip artifact rather than anything the rewrite introduced. Scoped before
fixing: ONE occurrence in lo-blocks' 534 commits, NONE in psych's 509, so psych
needed no re-run. `rewrite_filter` now emits every D before every M within a
commit, order preserved inside each group.

A THIRD INSTRUMENT FAILURE, same shape as the two below. `prove_loblocks.py`
reported 729 mismatches; it knew the four declared irreversible series but not
`CONTENT_FIXES`/`PLOT_MAP`, so every declared arrow repair counted as a failure.
Applying the same maps to the original side -- which `prove_sha_paired` does --
took it to 0.

AND AN ARGUMENT THAT WAS RIGHT FOR THE WRONG REASON. The case for disabling the
backfills was first made on the premise that lo-blocks' old states are never
built. They are, 54 of them. The conclusion survived; the reasoning did not, and
was replaced with the measurement above.

## The four defects, in the order each was exposed

A fix never revealed itself until the one before it stopped hiding it.

1. **Text-level substitution cannot see syntax.** `MEASURED.json` took a reference
   in a bare JSON array element -- the repo's OWN sweep counts, matched because
   seven of 1,635 table keys are pure digit runs with no lexical anchor. LOUD: the
   file stopped parsing, and `enforcement_audit` raised before its first finding.
   12 dict keys took one SILENTLY, 11 of them in `precommit_gate`, the gate that
   keeps student text out of the repository.
   FIX: a position-aware rule -- substitute inside string literals and comments,
   never a bare token, never a dict key -- plus `# corpus-refs-resolved` resolvers
   in `precommit_gate` and `agreement_app`, which hold needles rather than prose.

2. **The replays were hand-rolled.** They applied the substitution table in a loop
   instead of calling `rewrite_filter.scrub()`, and so reproduced the substitution
   and NONE of the passes around it -- above all the `corpus_data:` frontmatter
   declaration, without which the content build refuses every handout. MINE, and a
   bug `rewrite_filter` had already fixed once and documented.
   FIX: every replay goes through `scrub()`.

3. **A merged literal run swallowed a seam.** Allowing a match to span adjacent
   string literals let a single reference encode the seam in its `shape=`, so
   expansion restored a quote-newline-indent into the string VALUE where the
   original had only syntax. `generator_source.ITEM_NOTES['1c']` went from 1,789
   chars matching its migrated copy exactly to 1,973 against 1,945 -- while the
   file still compiled. Also MINE, introduced by the fix for (1).
   FIX: a seam-crossing entry is confined to a single literal unless its value
   keeps the seam, which is what `_SEAM_IN_KEY` already decided for the retry path.

4. **`split_seams` could not split 10 entries.** With (3) in place those 10 stopped
   being substituted at all, leaving 12 student 8-grams in `agreement_app.py`. The
   locator was failing for two reasons: 9 because the SOURCE writes an escape where
   the CORPUS holds the character, 1 because a part captured a source delimiter.
   FIX: locate with normalised variants while building the shape against the
   ORIGINAL part, so the reference still expands to the exact bytes. 456/466 -> 466/466.

## What each attempt measured

                  seams        student grams   ITEM_NOTES
    psych38       swallowed          0          corrupted
    psych39       intact            12          correct
    psych40       intact             0          correct

## Why seven instruments reported clean

Unchanged from the original finding, and the reason this took four rewrites:

* the byte proof compares bytes AFTER expansion, and expansion was always exact --
  41,861 of 41,861 file-versions passed while `MEASURED.json` would not parse;
* corpus scans use WORD 8-grams, and `"10, 11, 11, 11"` yields none;
* every substitution was reversible, so each was "correct" by every definition the
  rewrite had;
* the self-test could not start, so it reported nothing rather than a failure;
* `enforcement_audit` raised before its first finding.

Expansion fidelity and USABILITY are different properties. Only the first was ever
tested. `check_rewritten_artifacts_still_parse` now asks the second.

## The gates that now run BEFORE adoption

    every .json parses, every .py compiles
    corpus_data: frontmatter wherever references exist
    no shape= reference crossing a literal boundary
    per-version byte proof against the original lineage
    corpus scan with a control that must FIRE
    check_migrated_tables_match_their_source   (2 -> 1 -> 0)

## Two diagnoses that were wrong, kept because they cost the most

* **"Adoption broke the scorer."** 34 findings said the app and the harness send
  different prompts. They compare against a CACHED DUMP of the app's output, which
  adoption invalidated; the check's own message says to re-take it before reading
  it as a divergence. A causal story was built on it before it was tested.
* **"The re-cut stalled on a `tail` pipe."** Twice. `rewrite_filter` runs its main
  loop AT IMPORT, reading fast-export from stdin, so importing it as a library with
  a live stdin blocks forever -- `fd 0 -> socket`, `wchan -> unix_stream_data_wait`.
  The `[0.0s] blobs=0 ... DONE` line in every earlier test WAS that loop hitting
  EOF. The evidence was present from the first run and read as noise. Import it
  with stdin closed.

## Note for anyone running the package

`corpus_refs.json` gained 11 spans for the newly split seam references, so the
scoring package now REQUIRES `$COURSE_DATA` or `$CORPUS_REFS`. A bare run fails at
import with a message naming the variable. The repo and that export must travel
together.

---

## The original record, written while it was still broken

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
