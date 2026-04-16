import axios from "axios";

// Determine API base URL: use VITE_API_URL if set, otherwise detect from window.location
const getApiBase = () => {
  // In production (Render), both frontend and backend serve from different onrender.com subdomains
  // The frontend build can inject VITE_API_URL via environment variable
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Local development: assume backend is on localhost:8000
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://localhost:8000/api';
  }
  
  // Production: construct backend URL from frontend URL
  // If frontend is at https://golfcoach-frontend.onrender.com,
  // backend is at https://golfcoach-backend.onrender.com
  const protocol = window.location.protocol; // https: or http:
  const host = window.location.host; // golfcoach-frontend.onrender.com
  const backendHost = host.replace('frontend', 'backend');
  return `${protocol}//${backendHost}/api`;
};

const API = getApiBase();

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
