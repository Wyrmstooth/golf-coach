import client from "./client";

export interface JobStatus {
  job_id: string;
  status: "pending" | "running" | "done" | "error";
  progress: number;
  error?: string | null;
}

export interface FaultDetail {
  phase: string;
  severity: "critical" | "major" | "minor";
  title: string;
  description: string;
  fix: string;
  feature: string;
  value: number;
  expected: string;
}

export interface FaultDetails {
  faults: FaultDetail[];
  by_phase: Record<string, FaultDetail[]>;
  by_severity: Record<string, FaultDetail[]>;
  summary: { total_faults: number; critical_count: number; major_count: number; minor_count: number };
}

export interface AnalysisReport {
  video: string;
  phase_ranges: Record<string, [number, number]>;
  swing_frames: { start: number; end: number };
  fault_analysis: {
    overall_score: number | null;
    swing_quality: string;
    fault_details: FaultDetails;
    messages: string[];
    critical_faults: string[];
  };
  phase_fault_summary: Record<string, {
    max_severity: string;
    counts: { critical: number; major: number; minor: number };
    score: number;
    top_fault_titles: string[];
  }>;
  performance_prediction: {
    BallSpeed: number;
    Distance: number;
    Carry: number;
    confidence: number;
  } | null;
  ball_tracking: {
    enabled: boolean;
    status: string;
    quality: Record<string, number | string>;
    distance_estimation: {
      carry_yards: number;
      distance_yards: number;
      confidence: number;
      method: string;
      notes: string;
    } | null;
    trajectory_2d: Array<{ frame: number; t: number; x: number | null; y: number | null; confidence: number }>;
    files: { csv?: string; json?: string; plot?: string };
  };
  outputs: {
    plot: string;
    annotated_video: string | null;
    ball_plot: string | null;
  };
}

export async function uploadVideo(file: File): Promise<{ job_id: string }> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<{ job_id: string }>("/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getStatus(jobId: string): Promise<JobStatus> {
  const { data } = await client.get<JobStatus>(`/status/${jobId}`);
  return data;
}

export async function getReport(jobId: string): Promise<AnalysisReport> {
  const { data } = await client.get<AnalysisReport>(`/report/${jobId}`);
  return data;
}

export function getFileUrl(jobId: string, filename: string): string {
  return `/api/files/${jobId}/${filename}`;
}
