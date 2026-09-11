import type { FitLevel } from "../../types";

const FIT_VARIANT: Record<FitLevel, string> = {
  "Strong Fit": "badge--strong",
  "Possible Fit": "badge--possible",
  "Not a Fit": "badge--not-fit",
};

export function FitBadge({ level }: { level: FitLevel }) {
  return <span className={`badge ${FIT_VARIANT[level]}`}>{level}</span>;
}