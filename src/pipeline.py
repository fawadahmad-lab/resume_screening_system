"""Pipeline: orchestrates extract -> normalize -> score -> validate -> output.

CLI entry point (AGENTS.md Section 15):
    python src/pipeline.py --jd path/to/jd.txt --resumes ./data/sample_resumes/

Stage [4] rejects and retries once on validation failure before flagging the
candidate for human review (AGENTS.md Section 7).
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

from src.config import get_score_ensemble_n
from src.extract import extract_text
from src.normalize import CandidateProfile, normalize_resume
from src.score import ScoringResult, ensemble_score
from src.validate import validate_scoring_result

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")


class PipelineCandidateError(Exception):
    """Raised when an un-recoverable per-candidate error occurs."""


def process_candidate(
    file_path: str,
    jd_text: str,
    client=None,
    model: Optional[str] = None,
    max_validation_retries: int = 1,
) -> Dict:
    """Run the full Stage [1]-[4] chain for one resume file.

    Returns a result dict in the AGENTS.md Section 8 final-output shape, plus
    the intermediate profile and raw text for inspection:
        {
          "candidate_id", "profile", "raw_text", "result",
          "input_file", "validation_failed"
        }
    """
    candidate_id = os.path.splitext(os.path.basename(file_path))[0]
    try:
        raw_text = extract_text(file_path)
    except Exception as e:
        raise PipelineCandidateError(
            f"{candidate_id}: extraction failed: {e}"
        ) from e

    profile: CandidateProfile = normalize_resume(
        resume_text=raw_text, candidate_id=candidate_id, client=client, model=model
    )

    ensemble_n = get_score_ensemble_n()
    result: Optional[ScoringResult] = None
    for attempt in range(max_validation_retries + 1):
        result = ensemble_score(
            candidate_profile=profile,
            jd_text=jd_text,
            resume_text=raw_text,
            n_runs=ensemble_n,
            client=client,
            model=model,
        )
        try:
            result = validate_scoring_result(result)
            return {
                "candidate_id": candidate_id,
                "input_file": os.path.basename(file_path),
                "profile": profile.model_dump(),
                "raw_text": raw_text,
                "result": result.model_dump(),
                "validation_attempts": attempt + 1,
            }
        except RuntimeError as e:
            logger.warning(
                "%s: validation failed on attempt %d: %s",
                candidate_id, attempt + 1, e,
            )
            if attempt >= max_validation_retries:
                result.flag_for_human_review = True
                result.flag_reason = f"Validation retry failed: {e}"
                return {
                    "candidate_id": candidate_id,
                    "input_file": os.path.basename(file_path),
                    "profile": profile.model_dump(),
                    "raw_text": raw_text,
                    "result": result.model_dump(),
                    "validation_failed": True,
                    "validation_error": str(e),
                    "validation_attempts": attempt + 1,
                }

    raise PipelineCandidateError(f"{candidate_id}: internal pipeline error")


def run_pipeline(
    jd_text: str,
    resume_files: List[str],
    client=None,
    model: Optional[str] = None,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Process a batch of resumes.

    Returns (ordered_results, flagged_review, failures).
    ordered_results is sorted by total score descending.
    """
    ordered: List[Dict] = []
    flagged: List[Dict] = []
    failures: List[Dict] = []

    for file_path in resume_files:
        try:
            outcome = process_candidate(
                file_path=file_path, jd_text=jd_text, client=client, model=model
            )
            result = outcome["result"]
            if result["flag_for_human_review"]:
                flagged.append(outcome)
            ordered.append(outcome)
        except PipelineCandidateError as e:
            logger.error("Pipeline candidate error: %s", e)
            failures.append(
                {
                    "file": os.path.basename(file_path),
                    "error": str(e),
                }
            )
        except Exception as e:
            logger.exception("Unexpected failure for %s", file_path)
            failures.append(
                {"file": os.path.basename(file_path), "error": str(e)}
            )

    def _sort_key(outcome: Dict) -> int:
        return sum(c["score"] for c in outcome["result"]["criteria_scores"])

    ordered.sort(key=_sort_key, reverse=True)
    return ordered, flagged, failures


def _collect_resume_files(resumes_arg: str) -> List[str]:
    """Resolve --resumes to a sorted list of file paths."""
    if os.path.isfile(resumes_arg):
        return [resumes_arg]
    if os.path.isdir(resumes_arg):
        supported = (".txt", ".pdf", ".docx")
        files = [
            os.path.join(resumes_arg, f)
            for f in sorted(os.listdir(resumes_arg))
            if f.lower().endswith(supported)
        ]
        return files
    raise ValueError(f"--resumes must be a file or directory: {resumes_arg}")


def _write_json(path: str, payload: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)


def main() -> None:
    parser = argparse.ArgumentParser(description="Resume screening pipeline")
    parser.add_argument("--jd", required=True, help="Path to the job description file")
    parser.add_argument(
        "--resumes", required=True, help="Path to a resume file or directory"
    )
    parser.add_argument(
        "--output",
        default=os.path.join("data", "results", "latest.json"),
        help="Output JSON path",
    )
    parser.add_argument("--model", default=None, help="Override LLM model")
    args = parser.parse_args()

    try:
        with open(args.jd, "r") as f:
            jd_text = f.read()
        resume_files = _collect_resume_files(args.resumes)
    except (ValueError, OSError) as e:
        sys.exit(f"Input error: {e}")

    if not resume_files:
        sys.exit("No resume files found in the given path")

    logger.info("Processing %d resumes against %s", len(resume_files), args.jd)
    ordered, flagged, failures = run_pipeline(
        jd_text=jd_text, resume_files=resume_files, model=args.model
    )

    for outcome in ordered:
        result = outcome["result"]
        total = sum(c["score"] for c in result["criteria_scores"])
        line = (
            f"{outcome['candidate_id']:<45} {result['overall_fit']:<12} "
            f"total={total} conf={result['confidence']}"
        )
        if result["flag_for_human_review"]:
            line += f"  [FLAG: {result['flag_reason']}]"
        print(line)

    if flagged:
        print(f"\nFlagged for human review: {len(flagged)}")
    if failures:
        print(f"\nFailures ({len(failures)}):")
        for fl in failures:
            print(f"  - {fl}")

    _write_json(
        args.output,
        {
            "jd_file": args.jd,
            "count": len(ordered),
            "flagged_count": len(flagged),
            "failure_count": len(failures),
            "ordered": ordered,
            "flagged": flagged,
            "failures": failures,
        },
    )
    print(f"\nWrote results to {args.output}")


if __name__ == "__main__":
    main()