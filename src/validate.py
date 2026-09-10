"""Validation: schema checks, evidence quality, score ranges, fit-band
consistency, and auto-flag determination (AGENTS.md Sections 8-10).

Pure functions — no LLM calls. Modifies a ScoringResult in place: recomputes
flag_for_human_review / flag_reason based on the rules.
"""

import logging
from typing import List, Tuple

from pydantic import ValidationError

from src.score import CRITERIA_ORDER, ScoringResult

logger = logging.getLogger(__name__)

GENERIC_EVIDENCE_PHRASES = [
    "resume shows relevant experience",
    "resume demonstrates relevant experience",
    "relevant experience",
    "relevant background",
    "shows relevant",
    "demonstrates relevant",
    "candidate has relevant",
    "as can be seen",
    "clearly indicates",
    "suggesting a good fit",
    "appears to be a good fit",
    "seems qualified",
    "strong candidate",
]


def criterion_order_valid(result: ScoringResult) -> Tuple[bool, str]:
    """Check that criteria_scores matches the rubric exactly (all 5, in order)."""
    if len(result.criteria_scores) != len(CRITERIA_ORDER):
        return False, (
            f"Expected {len(CRITERIA_ORDER)} criteria, "
            f"got {len(result.criteria_scores)}"
        )
    for i, criterion in enumerate(CRITERIA_ORDER):
        if result.criteria_scores[i].criterion != criterion:
            return False, (
                f"Criterion {i} expected '{criterion}', "
                f"got '{result.criteria_scores[i].criterion}'"
            )
    return True, ""


def score_ranges_valid(result: ScoringResult) -> Tuple[bool, str]:
    """Check every score is an integer 0-2 (Pydantic already enforces ge/le)."""
    for cs in result.criteria_scores:
        if cs.score not in (0, 1, 2):
            return False, f"Score {cs.score} out of range for {cs.criterion}"
    return True, ""


def evidence_valid(result: ScoringResult) -> Tuple[bool, str]:
    """Check every evidence string is non-empty and non-generic."""
    for cs in result.criteria_scores:
        evidence = (cs.evidence or "").strip()
        if not evidence:
            return False, f"Empty evidence for criterion '{cs.criterion}'"
        low = evidence.lower()
        for phrase in GENERIC_EVIDENCE_PHRASES:
            if phrase in low:
                return False, (
                    f"Generic evidence for '{cs.criterion}': '{cs.evidence}'"
                )
    return True, ""


def _total(result: ScoringResult) -> int:
    return sum(cs.score for cs in result.criteria_scores)


def fit_band_consistent(result: ScoringResult) -> Tuple[bool, str]:
    """Check overall_fit matches the total-score band (Section 9)."""
    total = _total(result)
    if total >= 8:
        expected = "Strong Fit"
    elif total >= 5:
        expected = "Possible Fit"
    else:
        expected = "Not a Fit"
    if result.overall_fit != expected:
        return False, (
            f"overall_fit '{result.overall_fit}' inconsistent with total "
            f"{total} (expected '{expected}')"
        )
    return True, ""


def _should_flag(result: ScoringResult) -> Tuple[bool, str]:
    """Auto-flag rules from AGENTS.md Section 10."""
    reasons: List[str] = []
    total = _total(result)

    if result.confidence == "Low":
        reasons.append("confidence is low")

    if total in (4, 5, 7, 8):
        reasons.append(f"total score {total} is within 1 point of a band boundary")

    if result.overall_fit == "Strong Fit" and any(
        cs.score == 0 for cs in result.criteria_scores
    ):
        reasons.append("criterion scored 0 while overall_fit is Strong Fit")

    return (bool(reasons), "; ".join(reasons))


def indefinite_reason(result: ScoringResult) -> ScoringResult:
    """Recompute flag_for_human_review / flag_reason from scratch."""
    flag, reason = _should_flag(result)
    result.flag_for_human_review = flag
    result.flag_reason = reason if flag else None
    return result


def validate_scoring_result(result: ScoringResult) -> ScoringResult:
    """Run all checks, reject invalid results, and populate flag fields.

    Raises:
        RuntimeError: if any structural/evidential check fails (the caller's
            retry logic is responsible for retrying once per AGENTS.md, then
            exposing the result for human review with a flag).
    """
    checks = [
        ("criterion order", criterion_order_valid(result)),
        ("score range", score_ranges_valid(result)),
        ("evidence quality", evidence_valid(result)),
        ("fit-band consistency", fit_band_consistent(result)),
    ]
    for name, (ok, msg) in checks:
        if not ok:
            raise RuntimeError(f"Validation failed ({name}): {msg}")

    return indefinite_reason(result)


def validate_result_dict(data: dict) -> ScoringResult:
    """Validate a raw dict (e.g. from persisted JSON or the pipeline) against
    the ScoringResult schema, then run all checks.

    Raises:
        ValidationError: invalid schema shape.
        RuntimeError: failed semantic checks.
    """
    result = ScoringResult.model_validate(data)
    return validate_scoring_result(result)