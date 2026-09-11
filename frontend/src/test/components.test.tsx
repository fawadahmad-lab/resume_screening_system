import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { CandidatesTable } from "../components/candidates/CandidatesTable";
import { FitBadge } from "../components/ui/FitBadge";
import { ScoreBar } from "../components/ui/ScoreBar";
import { sampleRun } from "./fixtures";
import { isBoundary, totalScore } from "../utils/score";

describe("totalScore", () => {
  it("sums criteria scores", () => {
    const outcome = sampleRun.ordered[0];
    expect(totalScore(outcome)).toBe(5);
  });

  it("returns 0 for missing outcome", () => {
    expect(totalScore(null)).toBe(0);
  });
});

describe("isBoundary", () => {
  it("flags band-boundary totals", () => {
    expect(isBoundary(4)).toBe(true);
    expect(isBoundary(5)).toBe(true);
    expect(isBoundary(7)).toBe(true);
    expect(isBoundary(8)).toBe(true);
    expect(isBoundary(3)).toBe(false);
    expect(isBoundary(9)).toBe(false);
  });
});

describe("FitBadge", () => {
  it("renders the level text", () => {
    render(<FitBadge level="Strong Fit" />);
    expect(screen.getByText("Strong Fit")).toBeInTheDocument();
  });
});

describe("ScoreBar", () => {
  it("renders 2/2 segments for max score", () => {
    const { container } = render(<ScoreBar score={2} />);
    expect(container.querySelectorAll(".score-bar__seg--on")).toHaveLength(2);
    expect(screen.getByText("2/2")).toBeInTheDocument();
  });
});

describe("CandidatesTable", () => {
  it("renders each candidate with fit and total", () => {
    render(
      <MemoryRouter>
        <CandidatesTable run={sampleRun} />
      </MemoryRouter>,
    );
    expect(screen.getByText("ALEX THOMPSON")).toBeInTheDocument();
    expect(screen.getByText("Possible Fit")).toBeInTheDocument();
    expect(screen.getByText("5/10")).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getByText("Flagged")).toBeInTheDocument();
  });
});