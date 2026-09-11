export type FitLevel = "Strong Fit" | "Possible Fit" | "Not a Fit";
export type ConfidenceLevel = "High" | "Medium" | "Low";

export interface CriteriaScore {
  criterion: string;
  score: number; // 0-2
  evidence: string;
}

export interface ScreeningResult {
  candidate_id: string;
  overall_fit: FitLevel;
  confidence: ConfidenceLevel;
  criteria_scores: CriteriaScore[];
  flag_for_human_review: boolean;
  flag_reason: string | null;
}

export interface DateRange {
  start: string;
  end: string;
}

export interface CandidateProfile {
  candidate_id: string;
  name: string;
  skills: string[];
  titles: string[];
  date_ranges: DateRange[];
  education: string[];
}

export interface ScreeningOutcome {
  candidate_id: string;
  profile: CandidateProfile;
  raw_text: string;
  result: ScreeningResult;
  input_file: string;
  validation_failed: boolean;
  validation_error?: string | null;
}

export type CandidateStatus = "queued" | "processing" | "done" | "failed";

export interface ScreeningCandidate {
  candidate_id: string;
  file: string;
  source: "upload" | "sample";
  path: string;
  status: CandidateStatus;
  outcome: ScreeningOutcome | null;
  error: string | null;
}

export interface ScreeningRun {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
  jd_text: string;
  jd_name: string;
  candidates: ScreeningCandidate[];
  progress_done: number;
  progress_total: number;
  ordered: ScreeningOutcome[];
  flagged: ScreeningOutcome[];
  failures: { file: string; error: string }[];
  error: string | null;
}

export interface ScreeningListItem {
  id: string;
  status: ScreeningRun["status"];
  created_at: string;
  completed_at: string | null;
  candidate_count: number;
  result_count: number;
  failure_count: number;
  flagged_count: number;
}

export interface SampleJob {
  id: string;
  name: string;
}

export interface SampleJobDetail extends SampleJob {
  text: string;
}

export interface EvalCaseRow {
  case: number;
  name: string;
  expected: string;
  baseline_actual: string | null;
  baseline_match: boolean | null;
  baseline_total: number | null;
  after_actual: string | null;
  after_match: boolean | null;
  after_total: number | null;
}

export interface EvalSnapshotSummary {
  total_cases?: number;
  errors?: number;
  matched?: number;
  accuracy?: number;
  [key: string]: unknown;
}

export interface EvalSnapshot {
  file: string;
  summary: EvalSnapshotSummary | null;
}

export interface EvalView {
  baseline: EvalSnapshot;
  after: EvalSnapshot;
  cases: EvalCaseRow[];
}

export interface SystemState {
  provider: string;
  model: string;
  ollama_model: string;
  temperature: number;
  max_retries: number;
  call_interval_s: number;
  timeout_s: number;
  score_ensemble_n: number;
  data_dir: string;
}

export type ProgressStatus = "idle" | "submitting" | "running" | "done" | "failed";