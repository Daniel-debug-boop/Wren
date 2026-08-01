import axios from "axios";

const API_HOST = import.meta.env.VITE_BACKEND_HOST || "127.0.0.1:3000";
const PROTOCOL = import.meta.env.VITE_USE_TLS === "true" ? "https" : "http";

export const api = axios.create({
  baseURL: `${PROTOCOL}://${API_HOST}/api/v1`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem("wren_llm_api_key");
  if (apiKey) {
    config.headers.set("Authorization", `Bearer ${apiKey}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("[Wren] API auth required");
    }
    return Promise.reject(error);
  },
);

export const healthApi = {
  check: () => api.get("/alive"),
  status: () => api.get("/status"),
};

export const conversationApi = {
  list: () => api.get("/conversations"),
  get: (id: string) => api.get(`/conversations/${id}`),
  create: (data?: Record<string, unknown>) =>
    api.post("/conversations", data || {}),
  delete: (id: string) => api.delete(`/conversations/${id}`),
  sendMessage: (id: string, content: string) =>
    api.post(`/conversations/${id}/messages`, { content }),
};

export const settingsApi = {
  get: () => api.get("/settings"),
  update: (data: Record<string, unknown>) => api.put("/settings", data),
};

export const modelsApi = {
  list: () => api.get("/models"),
};

export const filesApi = {
  tree: () => api.get("/workspace/tree"),
  read: (path: string) => api.get("/workspace/file", { params: { path } }),
  write: (path: string, content: string) =>
    api.put("/workspace/file", { path, content }),
};

// Default export for endpoints.ts which imports as default
export default api;
