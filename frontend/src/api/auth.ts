import axios from "axios";

const API = "http://localhost:8000/api";

export interface UserOut {
  id: number;
  email: string;
  display_name: string;
  handicap: number | null;
  avatar_initials: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

export interface SwingSessionOut {
  id: number;
  video_filename: string | null;
  overall_score: number | null;
  swing_quality: string | null;
  faults: string[];
  job_id: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_sessions: number;
  avg_score: number | null;
  best_score: number | null;
  recent_sessions: SwingSessionOut[];
  score_trend: { date: string; score: number }[];
  fault_frequency: { fault: string; count: number }[];
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export const authApi = {
  register: (data: {
    email: string;
    display_name: string;
    password: string;
    handicap?: number | null;
  }) =>
    axios.post<TokenResponse>(`${API}/auth/register`, data).then((r) => r.data),

  login: (email: string, password: string) =>
    axios
      .post<TokenResponse>(`${API}/auth/login`, { email, password })
      .then((r) => r.data),

  me: (token: string) =>
    axios
      .get<UserOut>(`${API}/auth/me`, { headers: authHeaders(token) })
      .then((r) => r.data),

  updateProfile: (
    token: string,
    data: { display_name?: string; handicap?: number | null }
  ) =>
    axios
      .patch<UserOut>(`${API}/auth/me`, data, { headers: authHeaders(token) })
      .then((r) => r.data),
};

export const sessionsApi = {
  list: (token: string) =>
    axios
      .get<SwingSessionOut[]>(`${API}/sessions/`, {
        headers: authHeaders(token),
      })
      .then((r) => r.data),

  dashboard: (token: string) =>
    axios
      .get<DashboardStats>(`${API}/sessions/dashboard`, {
        headers: authHeaders(token),
      })
      .then((r) => r.data),

  deleteSession: (token: string, id: number) =>
    axios.delete(`${API}/sessions/${id}`, { headers: authHeaders(token) }),
};
