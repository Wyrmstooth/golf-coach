import client from "./client";
import type { UserOut, SwingSessionOut } from "./auth";

export interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  total_sessions: number;
  avg_score_all: number | null;
  active_jobs: number;
  total_jobs: number;
}

export interface AdminSessionOut extends SwingSessionOut {
  user_id: number;
  user_name: string;
  user_email: string;
}

export interface AdminUserUpdate {
  display_name?: string;
  handicap?: number | null;
  is_admin?: boolean;
  is_active?: boolean;
}

export interface UserStats {
  user_id: number;
  total_sessions: number;
  avg_score: number | null;
  best_score: number | null;
  score_trend: { date: string; score: number }[];
  top_faults: { fault: string; count: number }[];
}

export interface VideoValidation {
  valid: boolean;
  warning?: string;
  frame_count: number;
  duration_sec: number;
  fps?: number;
  pose_detection_ratio?: number;
}

export const adminApi = {
  getStats: () =>
    client.get<AdminStats>("/admin/stats").then((r) => r.data),

  listUsers: (search = "", limit = 100, offset = 0) =>
    client
      .get<UserOut[]>("/admin/users", { params: { search, limit, offset } })
      .then((r) => r.data),

  getUser: (id: number) =>
    client.get<UserOut>(`/admin/users/${id}`).then((r) => r.data),

  updateUser: (id: number, data: AdminUserUpdate) =>
    client.patch<UserOut>(`/admin/users/${id}`, data).then((r) => r.data),

  deleteUser: (id: number) => client.delete(`/admin/users/${id}`),

  listSessions: (limit = 50) =>
    client.get<AdminSessionOut[]>("/admin/sessions", { params: { limit } }).then((r) => r.data),

  listJobs: () => client.get<Record<string, unknown>[]>("/admin/jobs").then((r) => r.data),

  getUserStats: (id: number) =>
    client.get<UserStats>(`/admin/user-stats/${id}`).then((r) => r.data),
};

export async function validateVideo(file: File): Promise<VideoValidation> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<VideoValidation>("/validate", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
