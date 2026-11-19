import { apiRequest } from './apiClient';
import { PatchPreview, PatchReport, TestRun } from '../types/autofix';

export interface GenerateAutoFixInput {
  finding_id: string;
  original_code?: string;
  patch_instructions?: string;
}

export interface PatchDecisionInput {
  decision: 'approve' | 'reject';
  rejection_reason?: string;
}

export interface CommitPatchInput {
  branch_name?: string;
  commit_message?: string;
}

export interface CreatePrInput {
  target_branch?: string;
  pr_title?: string;
  pr_body?: string;
}

export interface RollbackPatchInput {
  branch_name?: string;
}

export const autofixApi = {
  listPatches: (params: { skip?: number; limit?: number } = {}): Promise<any[]> => {
    const query = new URLSearchParams();
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return apiRequest<any[]>(`/autofix${qs ? `?${qs}` : ''}`);
  },

  generateAutoFix: (input: GenerateAutoFixInput): Promise<PatchReport> =>
    apiRequest<PatchReport>('/autofix/generate', {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  getPreview: (patchId: string): Promise<PatchPreview> =>
    apiRequest<PatchPreview>(`/autofix/${patchId}/preview`),

  getReport: (patchId: string): Promise<PatchReport> =>
    apiRequest<PatchReport>(`/autofix/${patchId}/report`),

  submitDecision: (patchId: string, input: PatchDecisionInput): Promise<PatchReport> =>
    apiRequest<PatchReport>(`/autofix/${patchId}/decision`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  approveAndCommit: (patchId: string, input: CommitPatchInput = {}): Promise<any> =>
    apiRequest(`/autofix/${patchId}/commit`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  approveAndCreatePr: (patchId: string, input: CreatePrInput = {}): Promise<any> =>
    apiRequest(`/autofix/${patchId}/create-pr`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  rollbackPatch: (patchId: string, input: RollbackPatchInput = {}): Promise<any> =>
    apiRequest(`/autofix/${patchId}/rollback`, {
      method: 'POST',
      body: JSON.stringify(input),
    }),

  listTestRuns: (patchId: string): Promise<TestRun[]> =>
    apiRequest<TestRun[]>(`/autofix/${patchId}/test-runs`),
};
