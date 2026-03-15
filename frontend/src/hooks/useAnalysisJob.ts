import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { getStatus, getReport } from "../api/analysis";
import { useAppStore } from "../store/appStore";

/**
 * Polls /api/status/:jobId every 1.5 s until done, then fetches the report.
 * Returns { status, progress, report, isLoading, error }.
 */
export function useAnalysisJob(jobId: string | null) {
  const setReport = useAppStore((s) => s.setReport);

  const statusQuery = useQuery({
    queryKey: ["status", jobId],
    queryFn: () => getStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "done" || s === "error" ? false : 1500;
    },
  });

  const isDone = statusQuery.data?.status === "done";

  const reportQuery = useQuery({
    queryKey: ["report", jobId],
    queryFn: () => getReport(jobId!),
    enabled: !!jobId && isDone,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (reportQuery.data) {
      setReport(reportQuery.data);
    }
  }, [reportQuery.data, setReport]);

  return {
    status: statusQuery.data?.status ?? "pending",
    progress: statusQuery.data?.progress ?? 0,
    report: reportQuery.data ?? null,
    isLoading: statusQuery.isLoading || (isDone && reportQuery.isLoading),
    error: statusQuery.data?.error ?? reportQuery.error,
  };
}
