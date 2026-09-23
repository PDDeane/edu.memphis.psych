# Agenda items arising from the material classification, 2026-09-23

**FOLDED INTO `RUBRIC_MIGRATION_PLAN.md` §13 on 2026-09-23, which is now the copy
of record.** Kept as a pointer rather than deleted because this file was committed
under its own name (01c44514) and a copy is synced to `$COURSE_DATA/out/`, so a
reader can arrive at either one. Nothing cites it in code or prose -- checked, the
only reference anywhere is §13's own note saying where it came from.

Edit §13 of the plan, not this file. The items were:

| item | subject | state |
|---|---|---|
| A | split `declaration_source.py` / `generator_source.py` along the seam | **done 2026-09-23** |
| B | the handouts should be AUTHORED, not generated | open |
| C | no part of OLX prompt generation may depend on python | open, largest |
| C(i) | what the prior dry run already settled about C | record |
| D | `gold_slots_q6.py` -- a check nothing ran | **done 2026-09-23** |
| E | `olx_string_idmaps.ts` -- where the 99 lines belong | **done 2026-09-23** |
| F | `1c`'s gold rebuild -- implemented twice, no owner | **F1 done 2026-09-23**; F2 open |
| G | `DEFINITIONS.json` tracked 40 modules of 73; new ones never entered | **done 2026-09-23** |
| G2 | split procedure docs from the course they were written against | open, filed 2026-09-23 |
| H | regularize where things live -- one home per category | open, filed 2026-09-23 |
| I | documentation thorough enough to author from (SlotSheetGrader, Rubric) | open, filed 2026-09-23 |
| J | `scoring/` should become its own repository | open, filed 2026-09-23 |

Also decided along the way, and recorded in §13: the item-to-component link lives
in the RUBRIC (`<Item asks=...>`), so `course.json` keeps item -> handout only.
