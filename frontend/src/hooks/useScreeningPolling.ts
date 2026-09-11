import { useQuery } from "@tanstack/react-query";
import { getScreening } from "../api/screening";
import type { ScreeningRun } from "../types";

/**
 * Poll a screening run until it reaches a terminal state (completed/failed).
 * Stops polling automatically once terminal. Refetches the dashboard list
 * when a run completes so the landing page stays in sync.
 */
export function useScreeningPolling(id: string | null) {
  return useQuery({
    queryKey: ["screening", id],
    queryFn: () => getScreening(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const state = query.state.data?.status;
      if (state === "completed" || state === "failed") return false;
      return 3000;
    },
    refetchIntervalInBackground: true,
    staleTime: 0,
  });
}

export function isRunning(status: ScreeningRun["status"] | undefined): boolean {
  return status === "queued" || status === "processing";
}