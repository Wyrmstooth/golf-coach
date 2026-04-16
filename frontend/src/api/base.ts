export function getApiBase(): string {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "http://localhost:8000/api";
  }

  const protocol = window.location.protocol;
  const host = window.location.host.replace("frontend", "backend");
  return `${protocol}//${host}/api`;
}

export function getWsBase(): string {
  const apiBase = getApiBase();
  if (apiBase.startsWith("https://")) {
    return apiBase.replace("https://", "wss://");
  }
  if (apiBase.startsWith("http://")) {
    return apiBase.replace("http://", "ws://");
  }
  return apiBase;
}