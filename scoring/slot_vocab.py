"""The verdict tokens either side may use, in one place.

enforcement.check_slot_rules_are_vocabulary_neutral() needs to recognise a
verdict named literally in a shared `rule`. Listing them here rather than in the
check keeps the list next to the thing it describes: the web's extras come from
EXTRA_VERDICTS in lib/llm/slotSheet.ts, the rubric's from the `verdicts` lists on
credit components, and a rule may legitimately mention neither.
"""

WEB_EXTRAS = ("unclear", "wrong_kind", "incomplete", "duplicate",
              "mismatch", "generic", "tick_values")

RUBRIC_EXTRAS = ("not_active", "not_reason", "duplicate", "not_a_type",
                 "PR", "NR", "PP", "NP")

KNOWN_VERDICTS = ("met", "absent") + WEB_EXTRAS + RUBRIC_EXTRAS
