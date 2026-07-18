import axios from "axios";
import type { GitRepository, GitBranch, PaginatedResponse } from "#/types/git";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

class GitService {
  static async retrieveUserGitRepositories(): Promise<
    PaginatedResponse<GitRepository>
  > {
    const { data } =
      await api.get<PaginatedResponse<GitRepository>>("/git/repositories");
    return data;
  }

  static async getRepositoryBranches(params: {
    repository_id: string;
  }): Promise<PaginatedResponse<GitBranch>> {
    const { data } = await api.get<PaginatedResponse<GitBranch>>(
      `/git/repositories/${params.repository_id}/branches`,
    );
    return data;
  }
}

export default GitService;
