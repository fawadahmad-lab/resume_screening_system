import type { ScreeningListItem, ScreeningRun } from "../types";
import { postFormData, request } from "./client";

export function createScreening(form: FormData): Promise<{ screening_id: string }> {
  return postFormData<{ screening_id: string }>("/api/screenings", form);
}

export function listScreenings(): Promise<{ screenings: ScreeningListItem[] }> {
  return request<{ screenings: ScreeningListItem[] }>("/api/screenings");
}

export function getScreening(id: string): Promise<ScreeningRun> {
  return request<ScreeningRun>(`/api/screenings/${id}`);
}