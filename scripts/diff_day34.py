"""Diff Day-3 baseline vs Day-4 after snapshots (Checkpoint E part 2).

Usage: python scripts/diff_day34.py data/results/day3_baseline.json data/results/day4_after.json
Prints a compact per-case regression table plus summary to stdout.
"""

import json
import sys


def _result_map(path):
    with open(path) as f:
        data = json.load(f)
    return {r["name"]: r for r in data["results"]}, data["summary"], data["comparison"]


def main() -> None:
    base_path, after_path = sys.argv[1], sys.argv[2]
    base_res, base_sum, base_comp = _result_map(base_path)
    after_res, after_sum, after_comp = _result_map(after_path)

    print(f"Day-3 baseline: {base_sum.get('matched', 0)}/{base_sum.get('total_cases', 0)} "
          f"({base_sum.get('accuracy', 0) * 100:.1f}%), errors={base_sum.get('errors', 0)}")
    print(f"Day-4 after:    {after_sum.get('matched', 0)}/{after_sum.get('total_cases', 0)} "
          f"({after_sum.get('accuracy', 0) * 100:.1f}%), errors={after_sum.get('errors', 0)}")
    print()

    hdr = f"{'case':>4}  {'name':<32} {'gold':<12} {'base':<12} {'after':<12} {'base_tot':>8} {'aft_tot':>8} {'flag':>5}  {'delta':>6}"
    print(hdr)
    print("-" * len(hdr))

    changes = []
    for comp in base_comp:
        name = comp["name"]
        b = base_res.get(name)
        a = after_res.get(name)
        if a is None:
            # after run errored this candidate
            print(f"{comp['case']:>4}  {name:<32} {comp['expected']:<12} "
                  f"{(b['predicted'] if b else 'ERR'):<12} {'ERROR':<12} "
                  f"{(b['total'] if b else 'n/a'):>8} {'n/a':>8} {'--':>5}  ERROR")
            changes.append(f"{name}: base ok vs after ERROR")
            continue
        base_t = b["total"] if b else None
        delta = a["total"] - base_t if base_t is not None else "new"
        flag = "Y" if a["flag_for_human_review"] else "."
        print(f"{comp['case']:>4}  {name:<32} {comp['expected']:<12} "
              f"{(b['predicted'] if b else 'ERR'):<12} {a['predicted']:<12} "
              f"{(str(base_t) if base_t is not None else 'n/a'):>8} {a['total']:>8} {flag:>5}  {delta:>6}")
        if comp["match"] != after_comp[comp["case"] - 1]["match"]:
            changes.append(f"{name}: match {comp['match']} -> {after_comp[comp['case'] - 1]['match']}")

    print()
    if changes:
        print("BEHAVIOR CHANGES vs baseline:")
        for c in changes:
            print(f"  - {c}")
    else:
        print("No per-case match changes vs baseline.")


if __name__ == "__main__":
    main()