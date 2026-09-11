#!/usr/bin/env python3
"""Evaluation suite: runs the 13 dev cases through the pipeline and reports
agreement with gold labels (AGENTS.md Section 11, 15).

Usage:
    python tests/test_pipeline.py [--output data/results/day3_baseline.json]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_pipeline

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
RESULT_DIR = os.path.join(DATA_DIR, "results")
DEFAULT_CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases.json")


def load_cases(path: str):
    with open(path, "r") as f:
        return json.load(f)


def run_case(case: dict, client=None, model=None) -> dict:
    resume_path = os.path.join(DATA_DIR, "sample_resumes", case["resume"])
    jd_path = os.path.join(DATA_DIR, "sample_jds", case["jd"])
    with open(jd_path, "r") as f:
        jd_text = f.read()

    ordered, flagged, failures = run_pipeline(
        jd_text=jd_text, resume_files=[resume_path], client=client, model=model
    )

    if failures:
        return {"case": case["case"], "name": case["name"], "error": failures[0]["error"], "gold": case["gold"]}

    outcome = ordered[0]
    result = outcome["result"]
    total = sum(c["score"] for c in result["criteria_scores"])
    return {
        "case": case["case"],
        "name": case["name"],
        "gold": case["gold"],
        "predicted": result["overall_fit"],
        "confidence": result["confidence"],
        "total": total,
        "flag_for_human_review": result["flag_for_human_review"],
        "flag_reason": result["flag_reason"],
        "criteria_scores": result["criteria_scores"],
        "validation_failed": outcome.get("validation_failed", False),
        "validation_error": outcome.get("validation_error"),
        "candidate_id": outcome["candidate_id"],
    }


def report(results: list) -> dict:
    total = len(results)
    comparison = []
    matches = 0
    errors = 0
    for r in results:
        if "error" in r:
            errors += 1
            match = False
            expected, actual = r["gold"], "ERROR"
        else:
            expected, actual = r["gold"], r["predicted"]
            match = expected == actual
            if match:
                matches += 1
        comparison.append(
            {
                "case": r["case"],
                "name": r["name"],
                "expected": expected,
                "actual": actual,
                "match": match,
            }
        )

    total_scored = total - errors
    accuracy = (matches / total_scored) if total_scored else 0.0
    return {
        "summary": {
            "total_cases": total,
            "errors": errors,
            "matched": matches,
            "accuracy": round(accuracy, 4),
        },
        "comparison": comparison,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the dev evaluation suite")
    parser.add_argument("--cases", default=DEFAULT_CASES)
    parser.add_argument(
        "--output",
        default=os.path.join(RESULT_DIR, "latest_test.json"),
        help="Snapshot output path (e.g. data/results/day3_baseline.json)",
    )
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    cases = load_cases(args.cases)
    results = [run_case(c, model=args.model) for c in cases]
    report_data = report(results)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report_data, f, indent=2, default=str)

    print(f"\n{'Case':<4} {'Name':<40} Expected       Actual         Match")
    print("-" * 78)
    for comp in report_data["comparison"]:
        mark = "PASS" if comp["match"] else "FAIL"
        print(
            f"{comp['case']:<4} {comp['name']:<40} "
            f"{comp['expected']:<14} {comp['actual']:<14} {mark}"
        )
    s = report_data["summary"]
    print("-" * 78)
    print(
        f"Accuracy: {s['matched']}/{s['total_cases'] - s['errors']} "
        f"({s['accuracy']:.1%})  Errors: {s['errors']}"
    )
    print(f"Snapshot written to {args.output}")


if __name__ == "__main__":
    main()