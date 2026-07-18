import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/* ── Types ── */

export interface SkillInfo {
  name: string;
  type: "knowledge" | "repo" | "task";
  source: "global" | "user" | string;
  triggers: string[] | null;
}

export interface SkillPage {
  items: SkillInfo[];
  next_page_id: string | null;
}

/* ── API Service ── */

export class SkillsApi {
  static async searchSkills(
    limit = 100,
    pageId?: string,
  ): Promise<SkillPage> {
    const params: Record<string, string | number> = { limit };
    if (pageId) params.page_id = pageId;
    const { data } = await api.get<SkillPage>("/skills/search", { params });
    return data;
  }
}

export default SkillsApi;
