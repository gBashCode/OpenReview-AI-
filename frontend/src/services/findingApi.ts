import { apiRequest } from './apiClient';
import { Finding, FindingUpdateInput } from '../types/finding';

export interface ListFindingsParams {
  review_id?: string;
  category?: string;
  severity?: string;
  is_resolved?: boolean;
  search?: string;
  skip?: number;
  limit?: number;
}

export const findingApi = {
  listFindings: (params: ListFindingsParams = {}): Promise<Finding[]> => {
    const query = new URLSearchParams();
    if (params.review_id) query.set('review_id', params.review_id);
    if (params.category) query.set('category', params.category);
    if (params.severity) query.set('severity', params.severity);
    if (params.is_resolved !== undefined) query.set('is_resolved', String(params.is_resolved));
    if (params.search) query.set('search', params.search);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));

    const qs = query.toString();
    return apiRequest<Finding[]>(`/findings${qs ? `?${qs}` : ''}`);
  },

  getFinding: (id: string): Promise<Finding> => apiRequest<Finding>(`/findings/${id}`),

  updateFinding: (id: string, payload: FindingUpdateInput): Promise<Finding> =>
    apiRequest<Finding>(`/findings/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
};
