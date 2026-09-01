"""The verdict tokens either side may use, in one place.

enforcement.check_slot_rules_are_vocabulary_neutral() needs to recognise a
verdict named literally in a shared `rule`. Listing them here rather than in the
check keeps the list next to the thing it describes: the web's extras come from
EXTRA_VERDICTS in lib/llm/slotSheet.ts, the rubric's from the `verdicts` lists on
credit components, and a rule may legitimately mention neither.
"""

WEB_EXTRAS = ("unclear", "wrong_kind", "incomplete", "duplicate",
              "mismatch", "generic", "tick_values")

# `not_active` is HISTORICAL and kept only so the scan still recognises it: no
# rubric slot declares it any more. It was Q4b's failing verdict when the paper
# scorer was told to answer `wrong_kind` while being offered met/absent/not_active
# -- the incident every docstring here cites -- and those slots declare
# `wrong_kind` now. Removing it would stop the audit scanning for a token that
# could still appear in an old rule.
#
# `not_antecedent`, `not_consequence` and `not_described` were MISSING until
# 2026-08-30, and missing here means invisible: KNOWN_VERDICTS is the scan
# vocabulary, so no check looked for them anywhere. They are the paper-side
# failing verdicts for Q4a, Q4c and 1c -- the counterparts of the web's
# `wrong_kind` and `incomplete` -- so a shared `rule` naming one would have
# instructed the WEB about a token it cannot emit, and passed every check.
# `wrong_kind` is here because Q4b's behavior_1/behavior_2 declare it; see the
# warning on SHARED_EXTRAS about what that does and does not mean.
#
# Identities are deliberately NOT here: `first`/`second`/`neither`, Q4b's
# activity/consequence/goal_behaviour/not_doing, and the count values 0-3 are
# what a slot REPORTS, not a judgement it returns, and scanning prose for
# backticked `0` would be noise.
RUBRIC_EXTRAS = ("not_active", "not_reason", "duplicate", "not_a_type",
                 "not_antecedent", "not_consequence", "not_described",
                 "wrong_kind",
                 # `unclear` was missing here until 2026-08-30 while TWENTY-ONE
                 # rubric slots declared it, across all three handouts -- Q1's
                 # utb_stated, all five of Q3's, both keyword slots, D1/D2's
                 # type slots, 1a's four week slots, 2a's verdict. It is offered
                 # by both sides and always was; the list simply did not say so.
                 "unclear",
                 "PR", "NR", "PP", "NP")

# Tokens that appear in both lists. NOT AN EXEMPTION LIST, and it must never be
# used as one again -- that is what this comment exists to prevent.
#
# It was one until 2026-08-30, and it was wrong, because whether a token is
# shared is a fact about a SLOT and this is a fact about the corpus. `unclear` is
# in both lists and the two sides disagree about it on SEVENTEEN slots -- 2a's
# how_*, 2b's sentence_*, 3's example_*, Q1's and Q2's reason_* -- where the web
# offers it and the paper has only met/absent. Exempting it globally left a rule
# free to name it on any of those. No rule did, so it stayed latent.
# `wrong_kind` is the same shape in reverse: shared on Q4b's behavior_*, olx-only
# on Q4a's antecedent_*, Q4c's consequence_* and Q5's example_*.
#
# enforcement.check_slot_rules_are_vocabulary_neutral now asks the per-slot
# question directly, against the OLX sheet and the credit component, and needs no
# exemption list at all. This is kept because it states something true and useful
# -- these tokens exist on both sides SOMEWHERE -- and for no other purpose.
SHARED_EXTRAS = tuple(sorted(set(WEB_EXTRAS) & set(RUBRIC_EXTRAS)))

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
