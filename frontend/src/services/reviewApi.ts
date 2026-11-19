import { apiRequest, subscribeToEventStream } from './apiClient';
import { ConferenceSessionResponse, Review } from '../types/review';

export interface ListReviewsParams {
  pull_request_id?: string;
  status?: string;
  skip?: number;
  limit?: number;
}

export const reviewApi = {
  createReview: (pullRequestId: string, commitSha: string) =>
    apiRequest<Review>('/reviews', {
      method: 'POST',
      body: JSON.stringify({ pull_request_id: pullRequestId, commit_sha: commitSha }),
    }),

  listReviews: (params: ListReviewsParams = {}) => {
    const query = new URLSearchParams();
    if (params.pull_request_id) query.set('pull_request_id', params.pull_request_id);
    if (params.status) query.set('status', params.status);
    if (params.skip !== undefined) query.set('skip', String(params.skip));
    if (params.limit !== undefined) query.set('limit', String(params.limit));
    const qs = query.toString();
    return apiRequest<Review[]>(`/reviews${qs ? `?${qs}` : ''}`);
  },

  getReview: (reviewId: string) => apiRequest<Review>(`/reviews/${reviewId}`),

  listReviewsForPR: (prId: string) => apiRequest<Review[]>(`/reviews?pull_request_id=${encodeURIComponent(prId)}`),

  orchestrateReview: (reviewId: string, customDiff?: string) =>
    apiRequest<Review>(`/reviews/${reviewId}/orchestrate`, {
      method: 'POST',
      body: JSON.stringify({ custom_diff: customDiff }),
    }),

  publishReview: (reviewId: string, payload: any = {}) =>
    apiRequest<any>(`/reviews/${reviewId}/publish`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getPublishPreview: (reviewId: string) =>
    apiRequest<any>(`/reviews/${reviewId}/publish-preview`),

  getConferenceSession: (reviewId: string) =>
    apiRequest<ConferenceSessionResponse>(`/reviews/${reviewId}/conference`),

  deliberateConference: (reviewId: string, maxRounds: number = 2, customDiff?: string) =>
    apiRequest<ConferenceSessionResponse>(`/reviews/${reviewId}/conference/deliberate`, {
      method: 'POST',
      body: JSON.stringify({ max_rounds: maxRounds, custom_diff: customDiff }),
    }),

  listDiscussions: (reviewId: string, findingId?: string) => {
    const q = findingId ? `?finding_id=${encodeURIComponent(findingId)}` : '';
    return apiRequest<any[]>(`/reviews/${reviewId}/discussions${q}`);
  },

  addDiscussion: (reviewId: string, payload: any) =>
    apiRequest<any>(`/reviews/${reviewId}/discussions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  listCouncilAgents: () =>
    apiRequest<{ agents: any[] }>('/reviews/council/registry'),

  streamEvents: (
    reviewId: string,
    onEvent: (event: string, data: any) => void,
    onError?: (err: any) => void
  ) => subscribeToEventStream(`/reviews/${reviewId}/events`, onEvent, onError),
};
