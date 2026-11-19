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

export type DiscussionState = 'Accepted' | 'Rejected' | 'Needs investigation' | 'Duplicate' | 'Uncertain';
export type ConferencePosition = 'proposal' | 'challenge' | 'rebuttal' | 'context_supply' | 'verdict' | 'concession';

export interface ConferenceDiscussionMessage {
  id: string;
  review_id?: string;
  finding_id?: string;
  agent_name: string;
  message_type: string;
  position: ConferencePosition;
  final_decision?: DiscussionState | null;
  content: string;
  file_context?: string | null;
  evidence?: string | null;
  source_reference?: string | null;
  round_number: number;
  is_verified: boolean;
  created_at: string;
}

export interface ConferenceFindingThread {
  finding_id: string;
  file_path: string;
  line_number?: number | null;
  title: string;
  category: string;
  severity: string;
  proposing_agent: string;
  discussion_state: DiscussionState;
  evidence?: string | null;
  suggested_patch?: string | null;
  messages: ConferenceDiscussionMessage[];
}

export interface ConferenceAgent {
  id: string;
  agent_name: string;
  role: string;
  status: string;
  model_name?: string | null;
  reasoning_summary?: string | null;
  confidence_score: number;
  findings_count: number;
  execution_time_ms?: number | null;
}

export interface ConferenceSessionResponse {
  review_id: string;
  pull_request_id: string;
  commit_sha: string;
  status: string;
  total_rounds: number;
  discussion_threads: ConferenceFindingThread[];
  general_discussions?: ConferenceDiscussionMessage[];
  agents: ConferenceAgent[];
  summary_metrics: {
    total_rounds: number;
    total_findings: number;
    accepted_count: number;
    rejected_count: number;
    needs_investigation_count: number;
    duplicate_count: number;
    uncertain_count: number;
    consensus_rate: number;
  };
}
