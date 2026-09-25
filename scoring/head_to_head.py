"""RETIRED 2026-09-24 with the python web engine. Goal O.

It put the olx sweep and the python sweep side by side, item by item: two
harnesses measuring the same prompt -- the app scoring itself, and this harness
deriving the score in Python -- with a per-check breakdown and a test on the
rates.

THERE IS ONE WEB ENGINE NOW, so there is no head to put against a head.

NOT REPOINTED AT `paper`, which would look like the same tool and answer a
different question: the paper scorer reads what a teacher wrote and the web
scorer the same content after structuring, so a difference between them can be a
fact about the OLX authoring rather than about either engine's arithmetic. This
tool's premise was two implementations of ONE sheet over ONE input.

THE RUNS IT READ ARE NOT LOST. The python web column was folded into `olx` --
the two were measured equivalent first, 2,760 and 2,908 recorded cells
reproducing their stored scores through the app's own scorer -- so its evidence
is in the ledger. The full source is in git history at the commit that retired it.
"""

import sys

print(__doc__, file=sys.stderr)
raise SystemExit(2)
