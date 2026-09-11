import type { ScreeningRun } from "../types";

export const sampleOutcome = {
  candidate_id: "resume_06_edge_employment_gap",
  input_file: "resume_06_edge_employment_gap.txt",
  validation_failed: false,
  profile: {
    candidate_id: "resume_06_edge_employment_gap",
    name: "ALEX THOMPSON",
    skills: ["React", "TypeScript", "CSS"],
    titles: ["Frontend Developer"],
    date_ranges: [
      { start: "2020-01", end: "2022-12" },
      { start: "2023-04", end: "present" },
    ],
    education: ["BSc Computer Science"],
  },
  raw_text: "ALEX THOMPSON\nFrontend Developer\n…",
  result: {
    candidate_id: "resume_06_edge_employment_gap",
    overall_fit: "Possible Fit" as const,
    confidence: "Medium" as const,
    criteria_scores: [
      { criterion: "Required skills match", score: 1, evidence: "Resume lists React and TypeScript usage in dashboard project." },
      { criterion: "Years of relevant experience", score: 1, evidence: "Frontend Developer role from Jan 2020 to Dec 2022 (3 years)." },
      { criterion: "Title/seniority alignment", score: 1, evidence: "Title is Frontend Developer, matching the role level." },
      { criterion: "Career trajectory coherence", score: 1, evidence: "Continuous frontend work since 2020." },
      { criterion: "Red flags", score: 1, evidence: "Short unexplained gap in early 2023." },
    ],
    flag_for_human_review: true,
    flag_reason: "Total score is within 1 point of a band boundary.",
  },
};

export const sampleRun: ScreeningRun = {
  id: "abc123",
  status: "completed",
  created_at: "2026-09-11T10:00:00",
  completed_at: "2026-09-11T10:05:00",
  jd_text: "Senior Frontend Developer…",
  jd_name: "Sample JD · jd_frontend.txt",
  candidates: [
    {
      candidate_id: "resume_06_edge_employment_gap",
      file: "resume_06_edge_employment_gap.txt",
      source: "sample",
      path: "/data/sample_resumes/resume_06_edge_employment_gap.txt",
      status: "done",
      outcome: sampleOutcome,
      error: null,
    },
  ],
  progress_done: 1,
  progress_total: 1,
  ordered: [sampleOutcome],
  flagged: [sampleOutcome],
  failures: [],
  error: null,
};