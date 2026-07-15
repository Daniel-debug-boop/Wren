export interface GitRepository {
  id: string;
  full_name: string;
  git_provider: string;
  is_public: boolean;
  main_branch: string;
}

export interface GitBranch {
  name: string;
  commit_sha: string;
  protected: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  next_page_id: string | null;
}
