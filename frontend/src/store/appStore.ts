import { create } from "zustand";
import type { AnalysisReport } from "../api/analysis";

interface AppState {
  jobId: string | null;
  report: AnalysisReport | null;
  setJobId: (id: string | null) => void;
  setReport: (r: AnalysisReport | null) => void;
  reset: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  jobId: null,
  report: null,
  setJobId: (id) => set({ jobId: id }),
  setReport: (r) => set({ report: r }),
  reset: () => set({ jobId: null, report: null }),
}));
