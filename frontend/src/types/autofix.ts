export interface PatchPreview {
  patch_id: string;
  finding_id: string;
  file_path: string;
  original_code: string;
  patched_code: string;
  unified_diff: string;
  rollback_diff?: string | null;
  status: string;
  formatter_status?: string | null;
  linter_status?: string | null;
  sandbox_status?: string | null;
  regression_status?: string | null;
  failure_explanation?: string | null;
  generated_tests?: string | null;
  branch_name?: string | null;
  pr_url?: string | null;
}

export interface PatchReport {
  patch_id: string;
  finding_id: string;
  finding_title: string;
  file_path: string;
  unified_diff: string;
  status: string;
  diff_valid: boolean;
  dry_run_applicable: boolean;
  formatter_status: string;
  linter_status: string;
  sandbox_status: string;
  regression_status: string;
  test_runs_summary: {
    total: number;
    passed: number;
    failed: number;
    execution_time_seconds?: number;
  };
  failure_explanation?: string | null;
  requires_human_approval: boolean;
  can_commit: boolean;
  can_create_pr: boolean;
  can_rollback: boolean;
  created_at: string;
}

export interface TestRun {
  id: string;
  patch_id: string;
  status: string;
  test_framework: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  execution_time_seconds?: number | null;
  stdout_log?: string | null;
  stderr_log?: string | null;
  created_at: string;
}
