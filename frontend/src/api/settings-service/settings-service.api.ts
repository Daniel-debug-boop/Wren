import axios from "axios";
import type { UserSettings } from "#/types/settings";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

class SettingsService {
  static async getSettings(): Promise<UserSettings> {
    const { data } = await api.get<UserSettings>("/settings");
    return data;
  }

  static async saveSettings(
    settings: Partial<UserSettings>,
  ): Promise<UserSettings> {
    const { data } = await api.patch<UserSettings>("/settings", settings);
    return data;
  }
}

export default SettingsService;
