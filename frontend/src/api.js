export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
export const TOKEN_KEY = "movie_tracker_token";
export const USER_KEY = "movie_tracker_user";

export function posterUrl(path, size = "w342") {
  return path ? `https://image.tmdb.org/t/p/${size}${path}` : null;
}

export function signOut() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// fetch() with the stored JWT attached. An expired/invalid token (401) signs the user out and sends them to /login.
export async function authFetch(path, options = {}) {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  // FormData uploads must keep the browser-generated multipart header, so only default JSON for string bodies.
  if (typeof options.body === "string" && !headers["Content-Type"]) headers["Content-Type"] = "application/json";

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (response.status === 401) {
    signOut();
    window.location.assign("/login");
  }
  return response;
}

// authFetch + JSON parsing; throws an Error carrying the API's `detail` message when the request fails.
export async function apiRequest(path, { method = "GET", body } = {}) {
  const response = await authFetch(path, {
    method,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : "Something went wrong. Please try again.";
    throw new Error(detail);
  }
  return data;
}

// "2026-10-11" -> "Sun, Oct 11" (parsed as a local date so the day never shifts with timezones)
export function formatDay(isoDate) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

export function todayISO() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}
