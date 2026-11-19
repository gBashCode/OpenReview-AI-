export interface Repository {
  id: string;
  github_repo_id: number;
  owner: string;
  name: string;
  full_name: string;
  default_branch: string;
  description?: string | null;
  is_active: boolean;
  clone_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepositoryCreateInput {
  github_repo_id: number;
  owner: string;
  name: string;
  default_branch?: string;
  description?: string;
  is_active?: boolean;
}

export interface PullRequest {
  id: string;
  repository_id: string;
  github_pr_id?: number | null;
  pr_number: number;
  title: string;
  description?: string | null;
  head_branch: string;
  base_branch: string;
  head_sha: string;
  base_sha: string;
  author_username: string;
  state: string;
  created_at: string;
  updated_at: string;
}

export interface PullRequestCreateInput {
  repository_id: string;
  pr_number: number;
  title: string;
  head_branch: string;
  base_branch: string;
  head_sha: string;
  base_sha: string;
  author_username: string;
  description?: string;
}
