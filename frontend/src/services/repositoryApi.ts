import { apiRequest } from './apiClient';
import { PullRequest, PullRequestCreateInput, Repository, RepositoryCreateInput } from '../types/repository';

export const repositoryApi = {
  listRepositories: () => apiRequest<Repository[]>('/repositories'),
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

  listPullRequests: (repositoryId?: string) => {
    const query = repositoryId ? `?repository_id=${encodeURIComponent(repositoryId)}` : '';
    return apiRequest<PullRequest[]>(`/pull-requests${query}`);
  },
  getPullRequest: (id: string) => apiRequest<PullRequest>(`/pull-requests/${id}`),
  createPullRequest: (input: PullRequestCreateInput) =>
    apiRequest<PullRequest>('/pull-requests', {
      method: 'POST',
      body: JSON.stringify(input),
    }),
};
