# The migration's hand-written products

No stage script regenerates these. Losing them loses the migration.

`selftest_injections.py` is **here**, in the repository: it was scanned against
the whole student response space and carries none of it.

## The other three are NOT here, deliberately

    $MOLLY_DATA/migration_reference/products/
        RUBRIC_DECISIONS.md          66 distinctive student 4-grams
        rubric_reader.py              1
        FABRICATED.txt                0  (kept there for company)
        MEASURED.json.pre_fabrication

    $MOLLY_DATA/migration_reference/olx/
        bmod_rubric.olx              47 distinctive student 4-grams
        bmod_rubric_pr.olx            3
        bmod_course.olx               0

    $MOLLY_DATA/migration_reference/migration_changes.patch
        the dry run's complete diff -- 33 files, ~12k lines, includes the
        deletion of rubric_h1/h2/h3.py, which quoted students verbatim

**This repository is PUBLIC.** The rubric quotes student writing as scoring
evidence, so the dry run's rubric artifacts carry it and cannot live here until
they carry corpus REFERENCES instead. They were copied into this directory on
2026-09-16 and removed the same hour, before any commit; the scan that caught it
is `scripts/history_rewrite/scan_full_corpus.py`, matching against
`corpus_ref._index()` -- the whole response space, not the cited spans.

**When the real migration runs**, its `RUBRIC_DECISIONS.md` and its `.olx` must
be written with references from the start, and `precommit_gate` must pass on
them before they are committed. Do not copy the dry run's versions in.

## Reading them

They are reference material for the real run: what the dry run decided, and what
its output looked like. Diff against them; do not install them.
