import type { SystemState } from "../types";
import { request } from "./client";

export function getSystemState(): Promise<SystemState> {
  return request<SystemState>("/api/system");
}