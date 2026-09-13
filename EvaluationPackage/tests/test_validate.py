#!/usr/bin/env python3
"""Unit tests for src/validate.py evidence-quality logic (no LLM calls).

Covers the 2026-09-13 hardening (AGENTS.md Section 16): a generic phrase is
only a validation failure when the evidence is otherwise low-information
(no digits). Specific, grounded evidence that merely echoes a rubric
criterion name must pass.

Usage:
    python EvaluationPackage/tests/test_validate.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src.score import ScoringResult, CriterionScore
from src.validate import evidence_valid, validate_scoring_result


def make_result(evidences):
    return ScoringResult(
        candidate_id="test",
        overall_fit="Strong Fit",
        confidence="High",
        criteria_scores=[
            CriterionScore(criterion=c, score=s, evidence=e)
            for c, s, e in zip(
                ["Required skills match", "Years of relevant experience",
                 "Title/seniority alignment", "Career trajectory coherence",
                 "Red flags"],
                [2, 2, 2, 2, 2],
                evidences,
            )
        ],
        flag_for_human_review=False,
        flag_reason=None,
    )


def test_empty_evidence_rejected():
    result = make_result(["x", "", "y", "z", "w"])
    ok, msg = evidence_valid(result)
    assert not ok and "Empty evidence" in msg


def test_digit_free_boilerplate_still_rejected():
    # Generic phrasing with no dates/numbers remains a failure.
    result = make_result(["resume shows relevant experience", "y", "z", "w", "v"])
    ok, msg = evidence_valid(result)
    assert not ok and "Generic evidence" in msg


def test_grounded_evidence_starting_with_relevant_experience_passes():
    # The reported false positive (tmpfzidvmn0): cites roles + dates + domains.
    evidence = (
        "Relevant experience spans from the Data Science Fellow role beginning "
        "May 2024 through the current AI Engineer role beginning February 2026, "
        "including production AI systems, model deployment, MLOps, and "
        "real-time generative AI applications."
    )
    result = make_result([evidence, "y", "z", "w", "v"])
    ok, msg = evidence_valid(result)
    assert ok, f"grounded evidence was rejected: {msg}"


def test_generic_phrase_with_digits_passes():
    # Phrase collides with the rubric criterion name but cites a concrete value.
    result = make_result([
        "Relevant experience totals 5 years working on React and TypeScript",
        "y", "z", "w", "v",
    ])
    ok, msg = evidence_valid(result)
    assert ok, f"digit-bearing evidence was rejected: {msg}"


def test_full_validation_accepts_grounded_evidence():
    result = make_result([
        "Relevant experience spans from the Data Science Fellow role beginning "
        "May 2024 through the current AI Engineer role beginning February 2026",
        "Currently AI Engineer at Acme since February 2026",
        "Title of AI Engineer since February 2026 with prior Data Science Fellow",
        "Career moved from Data Science Fellow in May 2024 to AI Engineer",
        "No unexplained gaps; continuous employment since May 2024",
    ])
    result = validate_scoring_result(result)
    assert result.flag_for_human_review is False


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\n{len(tests)}/{'%d' % len(tests)} validator tests passed")