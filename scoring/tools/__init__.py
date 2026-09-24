"""Supporting tools: they MAINTAIN THE TREE rather than produce a finding.

GOAL H'S SECOND QUESTION, after "does it encode course knowledge". A module that
merely PROCESSES course data, carrying none of it, is a supporting tool and
belongs here whatever it reads -- `course_inventory` imports `coursedata` to
fetch the ids it measures against and is the clearest tool in the package after
`editguard`. A module that produces a FINDING about the course is analytic
machinery and stays at the package root, even at zero embedded ids:
`cross_path`, `faithful_probe` and `self_graded_misses` are the standing cases.

THE PACKAGE ROOT IS ON THE PATH because these modules import their siblings --
`paths`, `coursedata` -- and are also run directly as scripts. Both spellings
have to work, so the bootstrap lives here rather than being repeated in each.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
