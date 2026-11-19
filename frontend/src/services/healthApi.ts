import { apiRequest } from './apiClient';
import { HealthCheckResponse } from '../types/health';

export const healthApi = {
  getHealth: () => apiRequest<HealthCheckResponse>('/health'),
  getReadiness: () => apiRequest<{ status: string; database?: string }>('/health/ready'),
  getLiveness: () => apiRequest<{ status: string }>('/health/live'),
};
