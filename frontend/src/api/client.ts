import axios from "axios";
import { useAuthStore } from "../store/authStore";

const client = axios.create({
  baseURL: "/api",
  timeout: 300_000, // 5-min timeout for long analyses
});

// Add Authorization header if token exists
client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
