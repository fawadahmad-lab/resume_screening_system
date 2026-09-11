import type { SampleJob, SampleJobDetail } from "../types";
import { request } from "./client";

export function listJobs(): Promise<{ jobs: SampleJob[] }> {
  return request<{ jobs: SampleJob[] }>("/api/jobs");
}

export function getJob(id: string): Promise<SampleJobDetail> {
  return request<SampleJobDetail>(`/api/jobs/${encodeURIComponent(id)}`);
}