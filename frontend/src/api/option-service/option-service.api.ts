import axios from "axios";
import type { AppConfig } from "#/types/config";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

class OptionService {
  static async getConfig(): Promise<AppConfig> {
    const { data } = await api.get<AppConfig>("/config");
    return data;
  }
}

export default OptionService;
