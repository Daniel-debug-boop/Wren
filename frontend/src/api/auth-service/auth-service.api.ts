import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

class AuthService {
  static async authenticate(): Promise<boolean> {
    const { data } = await api.post<{ authenticated: boolean }>(
      "/auth/authenticate",
    );
    return data.authenticated;
  }

  static async logout(): Promise<void> {
    try {
      await api.post("/auth/logout");
    } finally {
      localStorage.removeItem("token");
    }
  }
}

export default AuthService;
