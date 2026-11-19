import { apiRequest } from './apiClient';

export interface GitHubInstallation {
  id: string;
  installation_id: number;
  organization_id: string;
  account_login: string;
  account_type: string;
  created_at: string;
  updated_at: string;
}

export interface GitHubRepositoryItem {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  description?: string | null;
  default_branch: string;
  clone_url?: string | null;
  html_url?: string | null;
}

export const githubApi = {
  listInstallations: (orgId?: string): Promise<GitHubInstallation[]> => {
    const q = orgId ? `?organization_id=${encodeURIComponent(orgId)}` : '';
    return apiRequest<GitHubInstallation[]>(`/github/installations${q}`);
  },

  getConnectUrl: (state?: string): Promise<{ installation_url: string }> => {
    const q = state ? `?state=${encodeURIComponent(state)}` : '';
    return apiRequest<{ installation_url: string }>(`/github/installations/connect${q}`);
  },

  listRemoteRepositories: (installationId: number): Promise<GitHubRepositoryItem[]> =>
    apiRequest<GitHubRepositoryItem[]>(`/github/installations/${installationId}/repositories`),

  syncRepositories: (installationId: number, orgId?: string): Promise<any[]> => {
    const q = orgId ? `?organization_id=${encodeURIComponent(orgId)}` : '';
    return apiRequest(`/github/installations/${installationId}/sync${q}`, {
      method: 'POST',
    });
  },

  syncMyRepositories: (): Promise<any[]> =>
    apiRequest<any[]>('/github/sync-my-repos', {
      method: 'POST',
    }),
};
