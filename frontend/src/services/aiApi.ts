import { apiRequest } from './apiClient';

export interface ProviderHealth {
  provider_name: string;
  is_healthy: boolean;
  latency_ms: number;
  message?: string;
  checked_at: string;
}

export interface ModelCatalog {
  default_provider: string;
  default_model: string;
  fallback_provider?: string;
  fallback_model?: string;
  max_context_length: number;
  pricing_per_million_tokens_usd: Record<string, { prompt_price: number; completion_price: number }>;
}

export interface AiUsageInfo {
  token_budget: number;
  total_tokens_consumed: number;
  total_cost_usd: number;
  budget_remaining: number;
}

export const aiApi = {
  checkHealth: (): Promise<Record<string, ProviderHealth>> => apiRequest('/ai/health'),
  listModels: (): Promise<ModelCatalog> => apiRequest('/ai/models'),
  listPrompts: (): Promise<any[]> => apiRequest('/ai/prompts'),
  getUsage: (): Promise<AiUsageInfo> => apiRequest('/ai/usage'),
};
