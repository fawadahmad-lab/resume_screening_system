import type { EvalView } from "../types";
import { request } from "./client";

export function listSampleResumes(): Promise<{ resumes: string[] }> {
  return request<{ resumes: string[] }>("/api/sample-resumes");
}

export function getEvals(): Promise<EvalView> {
  return request<EvalView>("/api/evals");
}