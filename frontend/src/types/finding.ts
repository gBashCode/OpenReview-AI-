export type FindingSeverity = 'Critical' | 'High' | 'Medium' | 'Low' | 'Informational' | string;
export type FindingCategory = 'security' | 'performance' | 'bug' | 'style' | 'architecture' | string;

export interface Finding {
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
  agent_name?: string | null;
  confidence_score?: number | null;
  discussion_state: string;
  evidence?: string | null;
  verification_status: string;
  root_cause?: string | null;
  impact?: string | null;
  actionability_score?: number | null;
  is_publishable: boolean;
  rejection_reason?: string | null;
  is_resolved: boolean;
  github_comment_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FindingUpdateInput {
  is_resolved?: boolean;
  suggested_patch?: string;
  github_comment_id?: string;
}
