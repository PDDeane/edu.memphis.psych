# Deleting `rubric_h1.py` and `rubric_h3.py` — the steps, rehearsed

Written 2026-09-20. Every step below was run against a real deletion and then
restored from git, which is how the list was found: reasoning about what would
break produced a shorter and wrong list.

`rubric_h2.py` STAYS. It holds the four builders A1c preserves
(`_example_item`, `_type_item`, `_definition_item`, `_example_use_item`), and
h1/h3 hold none — that is what divides "Stage 5 deletes the rubric modules"
from "the builders survive".

## Done in advance — the tree already survives the deletion

These were the breakages. All are fixed and committed; the rehearsal that found
each is named so the fix can be re-checked rather than trusted.

| what broke | now |
|---|---|
| `rubric_export` raised ModuleNotFoundError, so the course file could never be rebuilt — and not just for h1: the loop stopped at the first missing module, so h2's builders could not be re-expanded either | a handout whose module is gone is carried forward from the file being rewritten; verified all three come back with identical items, `item_notes` and `item_note_runs` |
| the §2e hook scanned `rubric_hN.py` source and reported "no recorded comments found" for 13 items | reads the carried record from the course file, the factory bodies for h2; 13 findings → 0 |
| `rubric_equivalence` and `reader_equivalence` crashed | report that they have no oracle and point at `STAGE5_LICENCE.md` |
| `check_rubric_notes_match_the_modules` crashed | stands down when the modules are gone |
| `reader_equivalence` called Q4c, Q5 and Q6 orphans | that direction is asked only while all three modules exist |

`check_selectors_govern_something` needs nothing: it reads rubric_h2's source,
and rubric_h2 stays.

## The deletion itself

    git rm scoring/rubric_h1.py scoring/rubric_h3.py

Then three declarations still name the deleted files. Each says what to do, and
each was confirmed by rehearsal:

1. **`check_no_module_is_named_for_a_course_artifact`** — "in the
   course-named-module budget but no longer matches". Fixed by
   `python3 course_inventory.py --tighten`. VERIFIED: 2 findings → 0.

2. **`check_module_has_no_course_data`** — "rubric_h1.py is declared a DATA
   module and the scan never saw it". Remove the `rubric_h1.py` and
   `rubric_h3.py` entries from `enforcement.DATA_MODULES`. editguard requires
   the removals be declared:

       dropping=["DATA_MODULES['rubric_h1.py']", "DATA_MODULES['rubric_h3.py']",
                 "prose:the handout 1 rubric, authored",
                 "prose:the handout 3 rubric, authored"]

3. **`check_no_definition_vanished`** — "the whole MODULE is gone, and the
   inventory records 5 definition(s) in it". The `DEFINITIONS.json` entries for
   both files come out. `editguard.py --accept` takes a single NAME, not a
   module, so this one is a deliberate edit rather than a command.

Then: `python3 rubric_export.py --out <course.json>` to confirm regeneration
still works, both equivalence tools to confirm they stand down cleanly, the
check sweep, and a certifying self-test.

## What changes for a person afterwards

Handout 1 and 3 rubrics are authored in `course.json`. Their reasoning is
reachable through `coursedata.rubric_notes(item)` and `rubric_note_runs(item)`
— 1,567 lines of it, plus 548 of handout header prose, carried before any of
this so that nothing depends on the files still being there. The §2e hook
prints it at the moment a rule changes, which is the only moment it matters.
