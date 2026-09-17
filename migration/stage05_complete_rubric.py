#!/usr/bin/env python3
"""RETIRED at stage 05. Do not run this; it is kept only as a signpost.

This script PATCHED the emitted rubric with the scorer-side fields that
`stage04_migrate_rubric.py` did not know how to emit. It worked, and it was
erased without a word the next time a gate ran -- because the gate re-runs the
emitter, the emitter regenerates the rubric from the modules, and a gate that
regenerates is a writer that runs last. See T17 in RUBRIC_MIGRATION_PLAN.md.

The logic now lives in `stage04_migrate_rubric.py`, which is the one writer of
the rubric object. Add new fields there.
"""
import sys

sys.exit(
    "stage05_complete_rubric.py is RETIRED: one generated artifact, one writer.\n"
    "The completion logic is in stage04_migrate_rubric.py. See T17 in the plan.")
