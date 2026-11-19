import { apiRequest } from './apiClient';
import { AuditLog, UsageStats } from '../types/analytics';

export const analyticsApi = {
  getUsageStats: (orgId?: string): Promise<UsageStats> => {
    const q = orgId ? `?organization_id=${encodeURIComponent(orgId)}` : '';
    return apiRequest<UsageStats>(`/analytics/stats${q}`);
  },

  listAuditLogs: (params: { organization_id?: string; action?: string; skip?: number; limit?: number } = {}): Promise<AuditLog[]> => {
    const query = new URLSearchParams();
    if (params.organization_id) query.set('organization_id', params.organization_id);
    if (params.action) query.set('action', params.action);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return apiRequest<AuditLog[]>(`/analytics/audit-logs${qs ? `?${qs}` : ''}`);
  },
};
