#!/usr/bin/env python3
"""Run the held-out set once through the pipeline and save the snapshot.

Usage:
    python scripts/run_held_out.py [--output data/results/day4_held_out.json] [--jd data/sample_jds/jd_frontend.txt]

The held-out set is a blind test: it is generated once on Day 4 and run
exactly once. Results are reported as-is (AGENTS.md Section 6, 11). There
are no gold labels — this is an as-is results dump, not an accuracy score.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import run_pipeline

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
HELD_OUT_DIR = os.path.join(DATA_DIR, "held_out_resumes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the held-out set once")
    parser.add_argument(
        "--jd", default=os.path.join(DATA_DIR, "sample_jds", "jd_frontend.txt")
    )
    parser.add_argument(
        "--output",
        default=os.path.join(DATA_DIR, "results", "day4_held_out.json"),
    )
    parser.add_argument("--model", default=None)
    args = parser.parse_args()

    with open(args.jd, "r") as f:
        jd_text = f.read()
    resume_files = sorted(
        os.path.join(HELD_OUT_DIR, f) for f in os.listdir(HELD_OUT_DIR) if f.endswith(".txt")
    )

    ordered, flagged, failures = run_pipeline(
        jd_text=jd_text, resume_files=resume_files, model=args.model
    )

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    payload = {
        "jd_file": args.jd,
        "count": len(ordered),
        "flagged_count": len(flagged),
        "failure_count": len(failures),
        "ordered": ordered,
        "flagged": flagged,
        "failures": failures,
    }
    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    print("\nHELD-OUT RESULTS (as-is)")
    for outcome in ordered:
        r = outcome["result"]
        total = sum(c["score"] for c in r["criteria_scores"])
        flag = " *FLAG*" if r["flag_for_human_review"] else ""
        print(
            f"  {outcome['candidate_id']:<40} {r['overall_fit']:<12} "
            f"total={total} conf={r['confidence']}{flag}"
        )
    if failures:
        print("Failures:")
        for fl in failures:
            print(f"  - {fl}")
    print(f"Snapshot written to {args.output}")


if __name__ == "__main__":
    main()