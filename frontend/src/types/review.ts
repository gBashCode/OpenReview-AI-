export type FindingSeverity = 'info' | 'warning' | 'error' | 'critical';
export type FindingCategory = 'security' | 'performance' | 'bug' | 'style' | 'architecture';

export interface ReviewComment {
  id: string;
  review_id: string;
  file_path: string;
  line_number?: number | null;
  end_line_number?: number | null;
  side: string;
  category: FindingCategory;
  severity: FindingSeverity;
  title: string;
  message: string;
  suggested_patch?: string | null;
  is_resolved: boolean;
  github_comment_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface Review {
  id: string;
  pull_request_id: string;
  commit_sha: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  summary?: string | null;
  score?: number | null;
  security_score?: number | null;
  performance_score?: number | null;
  quality_score?: number | null;
  findings_count: number;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  comments?: ReviewComment[];
}
