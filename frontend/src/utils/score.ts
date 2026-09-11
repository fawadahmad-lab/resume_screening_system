import type { ScreeningOutcome } from "../types";

export function totalScore(outcome?: ScreeningOutcome | null): number {
  if (!outcome) return 0;
  return outcome.result.criteria_scores.reduce((sum, c) => sum + c.score, 0);
}

export function isBoundary(total: number): boolean {
  return total === 4 || total === 5 || total === 7 || total === 8;
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}