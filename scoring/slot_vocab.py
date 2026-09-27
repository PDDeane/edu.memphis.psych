"""The verdict tokens either side may use, in one place.

enforcement.check_slot_rules_are_vocabulary_neutral() needs to recognise a
verdict named literally in a shared `rule`. Listing them here rather than in the
check keeps the list next to the thing it describes: the web's extras come from
EXTRA_VERDICTS in lib/llm/slotSheet.ts, the rubric's from the `verdicts` lists on
credit components, and a rule may legitimately mention neither.
"""

_VOCAB: dict = {}


def _vocabulary() -> dict:
    """The verdict lists, from lo-blocks, EVALUATED rather than scraped.

    THERE WAS A SECOND COPY. `WEB_EXTRAS` was a verbatim transcription of
    `slotSheet.EXTRA_VERDICTS` -- measured identical 2026-09-25, with the
    docstring above naming its source and nothing checking it still matched.
    The user's ruling: keep one copy.

    AND THE FIRST REPLACEMENT WAS NO BETTER: a regex over the TypeScript SOURCE,
    which let a `//` comment run into the token after it and yielded a garbage
    verdict. A hand-rolled parser over someone else's syntax is the thing this
    project keeps being burned by. The probe hands back the real value of the
    real module, so there is nothing to parse and nothing to drift.

    LAZY, so importing this module costs nothing: the bridge is asked on first
    use and the answer cached. REFUSES rather than falling back -- a vocabulary
    that quietly reverts to a stale copy is how the scan stopped recognising
    `unclear` while twenty-one rubric slots declared it.
    """
    if not _VOCAB:
        import lo_enforce

        got = lo_enforce.probe("verdict_vocabulary", {})
        if not isinstance(got, dict) or "KNOWN_VERDICTS" not in got:
            raise SystemExit(
                "slot_vocab: the verdict vocabulary could not be read from "
                "lo-blocks, so the audit cannot tell which tokens are verdicts")
        _VOCAB.update({k: tuple(v) for k, v in got.items()})
    return _VOCAB


def known_verdicts() -> tuple:
    """Every verdict token either side may use.

    A FUNCTION, NOT A MODULE `__getattr__`. The first version of this served
    `KNOWN_VERDICTS` through one so callers could keep `from slot_vocab import
    KNOWN_VERDICTS`. The user's ruling, 2026-09-25: no `__getattr__`. It earns
    that -- it does not intercept a BARE NAME looked up inside its own module
    (`agreement_app` raised NameError and took the audit down with it), and the
    names it serves are invisible to `editguard`'s inventory, so each one has to
    be ACCEPTED as a removal that never happened.

    An explicit call says where the value comes from at the point of use, which
    is the thing the attribute spelling was hiding.
    """
    return _vocabulary()["KNOWN_VERDICTS"]


def web_extras() -> tuple:
    """The web's extra verdicts -- `slotSheet.EXTRA_VERDICTS`, via the probe."""
    return _vocabulary()["WEB_EXTRAS"]


def rubric_extras() -> tuple:
    """The rubric's extra verdicts."""
    return _vocabulary()["RUBRIC_EXTRAS"]


def shared_extras() -> tuple:
    """The tokens BOTH sides declare."""
    v = _vocabulary()
    return tuple(sorted(set(v["WEB_EXTRAS"]) & set(v["RUBRIC_EXTRAS"])))

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
