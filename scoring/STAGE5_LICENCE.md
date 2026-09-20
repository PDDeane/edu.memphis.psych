# Stage 5 licence — the last run of the equivalence tools

`rubric_equivalence.py` says of itself: *"The rubric modules are deleted at
Stage 5, and the last run of this tool is what licenses removing them."* This
file is that run, recorded before the modules go, because after they go the
tools have no oracle to compare against and the result cannot be reproduced.

## rubric_equivalence.py (T5.1) — the module side
```
  compared 26 items, 333 item fields, 74 generator fields, 19 module-level authored values
  EQUIVALENT — the file reproduces the modules on every authored field.
  (Derived values are T3.2's, through the reader: ['BY_ID', 'TOTAL'])
```

## reader_equivalence.py (T3.2) — through `coursedata`
```
  51 values compared through the reader, unknown (pass --inventory) tables not yet migrated
  39 module-level names accounted for, 11 by justification
  EQUIVALENT: the reader serves exactly what the modules hold.
```

## What the modules still contain, measured
```
rubric_h1.py   2948 lines  0 builder function(s)
rubric_h2.py   1355 lines  4 builder function(s)  _example_item, _type_item, _definition_item, _example_use_item
rubric_h3.py    829 lines  0 builder function(s)
```

**h1 and h3 are pure data** and reproduce exactly from the course file.
**h2 holds the four builders A1c preserves**, which is why A1c says the
builders survive outside the pipeline rather than being deleted with the data.

## The one import site that remains

`check_selectors_govern_something` reads rubric_h2's SOURCE to find selector
tuples still defined and no longer consulted. It is retired WITH the modules:
a check for stale selectors in a file that no longer exists has nothing to find.

Recorded 2026-09-20 08:48.
