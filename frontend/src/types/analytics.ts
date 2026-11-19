export interface UsageStats {
  total_reviews: number;
  total_pull_requests: number;
  total_findings: number;
  open_findings: number;
  resolved_findings: number;
  avg_quality_score: number;
  security_score: number;
  performance_score: number;
  quality_score: number;
  reviews_by_status: Record<string, number>;
  findings_by_severity: Record<string, number>;
  findings_by_category: Record<string, number>;
}

export interface AuditLog {
  id: string;
  organization_id: string;
  user_id?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  details?: Record<string, any> | null;
  ip_address?: string | null;
  created_at: string;
}
