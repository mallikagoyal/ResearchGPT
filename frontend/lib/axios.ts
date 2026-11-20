import axios, { type AxiosError } from "axios";

/**
 * Base URL for the ResearchGPT backend API. Must be set at build/runtime
 * via NEXT_PUBLIC_API_URL since this is read in the browser.
 */
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const TOKEN_STORAGE_KEY = "researchgpt_access_token";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach the JWT (if present) to every outgoing request.
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Centralized handling for expired/invalid sessions: clear the stored
// token so AuthProvider's next check redirects to /login, rather than
// every caller having to special-case 401s.
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
    return Promise.reject(error);
  }
);

/**
 * Extract a human-readable message from a FastAPI error response.
 * FastAPI returns either {"detail": "message"} or, for Pydantic
 * validation errors, {"detail": [{"msg": "...", "loc": [...]}]}.
 */
export function getApiErrorMessage(error: unknown, fallback = "Something went wrong."): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(" ");
    }
    if (error.message) return error.message;
  }
  return fallback;
}
