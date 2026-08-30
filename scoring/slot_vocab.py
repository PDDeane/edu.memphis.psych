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


# WHO HAS TO KNOW THE TWO LISTS ARE SEPARATE, audited 2026-08-30 after a
# migration read the rubric's list as "what this slot offers" and renamed a
# rule's `wrong_kind` to `not_reason`. That pointed a live instruction at a token
# the model cannot emit and cost a cell before the measurement caught it.
#
#   enforcement.check_slot_rules_are_vocabulary_neutral
#       Flags a shared `rule` naming ANY token from either list. That strictness
#       is the point: the two sides do not share a vocabulary, so naming either
#       token instructs one of them about something it cannot answer. It was
#       weakened twice on the theory that a slot "declaring" a token makes it
#       safe; it does not, because the rubric's declaration is the PAPER side's.
#   enforcement.check_rule_fail_tokens_agree
#       The other half: `{fail}` is the sanctioned escape, and this checks the
#       two generators fill it with tokens that mean the same thing.
#   cross_path._slot_diffs
#       Compares verdicts BETWEEN artifacts. Raw-string comparison is right for
#       harness-vs-app (one vocabulary, and which failure mode was chosen is
#       worth keeping) and wrong the moment a PAPER artifact is involved, where
#       `wrong_kind` and `not_reason` are counterparts. It folds to
#       satisfied/failed in that case only.
#
# SAFE BY CONSTRUCTION, and worth knowing so they are not "fixed" into hazards:
#   agreement.is_satisfied / slotSheet.isSatisfied compare against the slot's OWN
#   options, so they are correct under either vocabulary; measured.error_profile
#   reads them rather than matching strings; olx_prompts._fail_token and
#   score._fail_verdict are per-side BY DESIGN and must stay that way.
