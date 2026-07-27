import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";

const BASE_URL = "/api/v1";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export function getAuthToken(): string | null {
  return authToken;
}

const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach auth token to every request if available
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

// Unified error handler
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // If we get a 401 and there's no session, redirect to login
    if (error.response?.status === 401 && !window.location.pathname.includes("/login")) {
      // Don't redirect on API health checks
      if (!error.config?.url?.includes("/alive") && !error.config?.url?.includes("/health")) {
        setAuthToken(null);
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default apiClient;
