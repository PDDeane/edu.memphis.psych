# Drafts

Interim material: notes and worksheets that are not machinery, not records of
record, and not read by anything. Category X of `MATERIAL_CLASSIFICATION.md`.

## The two JSON worksheets (moved here 2026-09-24)

`PROSE_SPLIT_WORKSHEET.json` (1.2 MB) and `STRUCTURE_KIDS.json` (108 KB) are
**planning inputs for a generic course-construction capability that does not
exist yet** (user, 2026-09-24). They were in `course_metadata/fixture/`, which
said the opposite of what they are: that directory is THIS COURSE's fixture, and
these describe a future capability meant to serve any course.

Both are ON-DEMAND OUTPUTS, not stored state. `prose_split.py --json PATH` and
`structure_kids.py --json PATH` write them wherever they are told; nothing reads
the checked-in copies, and their producers read something else
(`structure_kids.py` reads `SHAPE_INVENTORY.json`, not its own namesake).
Regenerate rather than edit.

Two classifications were wrong and are corrected in `MATERIAL_CLASSIFICATION.md`:

* `STRUCTURE_KIDS.json` sat in III, "the ratchets and frozen records". It is
  neither -- no check reads it, and nothing ratchets against it.
* `PROSE_SPLIT_WORKSHEET.json` sat in IX, "fixture programs". H(4) had already
  found its producer is NOT a fixture program: *"prose_split.py NOT FIXTURE. Its
  subject is this repository's DOCUMENTS ... it maintains the tree -> tooling."*
  The worksheet inherited a placement its own producer had already lost.
