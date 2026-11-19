import { apiRequest } from './apiClient';
import { PullRequest, PullRequestCreateInput, Repository, RepositoryCreateInput } from '../types/repository';

export interface ListReposParams {
  organization_id?: string;
  skip?: number;
  limit?: number;
}

export interface ListPRsParams {
  repository_id?: string;
  state?: string;
  skip?: number;
  limit?: number;
}

export const repositoryApi = {
  listRepositories: (params: ListReposParams = {}) => {
    const query = new URLSearchParams();
    if (params.organization_id) query.set('organization_id', params.organization_id);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return apiRequest<Repository[]>(`/repositories${qs ? `?${qs}` : ''}`);
  },

  getRepository: (id: string) => apiRequest<Repository>(`/repositories/${id}`),

  createRepository: (input: RepositoryCreateInput) =>
    apiRequest<Repository>('/repositories', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  deleteRepository: (id: string) =>
    apiRequest<void>(`/repositories/${id}`, {
      method: 'DELETE',
    }),

  listIndexes: (repoId: string) =>
    apiRequest<any[]>(`/repositories/${repoId}/indexes`),

  triggerIndex: (repoId: string) =>
    apiRequest<any>(`/repositories/${repoId}/index`, {
      method: 'POST',
    }),

  getArchitecture: (repoId: string) =>
    apiRequest<any>(`/repositories/${repoId}/architecture`),

  listSymbols: (repoId: string, query?: string) => {
    const q = query ? `?query=${encodeURIComponent(query)}` : '';
    return apiRequest<any[]>(`/repositories/${repoId}/symbols${q}`);
  },

  listChunks: (repoId: string, filePath?: string) => {
    const q = filePath ? `?file_path=${encodeURIComponent(filePath)}` : '';
    return apiRequest<any[]>(`/repositories/${repoId}/chunks${q}`);
  },

  listPullRequests: (params?: string | ListPRsParams) => {
    const opts: ListPRsParams = typeof params === 'string' ? { repository_id: params } : (params || {});
    const query = new URLSearchParams();
    if (opts.repository_id) query.set('repository_id', opts.repository_id);
    if (opts.state) query.set('state', opts.state);
    if (opts.skip !== undefined) query.set('skip', String(opts.skip));
    if (opts.limit !== undefined) query.set('limit', String(opts.limit));
    const qs = query.toString();
    return apiRequest<PullRequest[]>(`/pull-requests${qs ? `?${qs}` : ''}`);
  },

  getPullRequest: (id: string) => apiRequest<PullRequest>(`/pull-requests/${id}`),

  createPullRequest: (input: PullRequestCreateInput) =>
    apiRequest<PullRequest>('/pull-requests', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  analyzePullRequest: (id: string) =>
    apiRequest<any>(`/pull-requests/${id}/analyze`, {
      method: 'POST',
    }),
};
