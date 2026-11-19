import { apiRequest } from './apiClient';
import { ConferenceSessionResponse, Review } from '../types/review';

export const reviewApi = {
  createReview: (pullRequestId: string, commitSha: string) =>
    apiRequest<Review>('/reviews', {
      method: 'POST',
      body: JSON.stringify({ pull_request_id: pullRequestId, commit_sha: commitSha }),
    }),

  listReviews: () => apiRequest<Review[]>('/reviews'),

  getReview: (reviewId: string) => apiRequest<Review>(`/reviews/${reviewId}`),

  listReviewsForPR: (prId: string) => apiRequest<Review[]>(`/pull-requests/${prId}/reviews`),

  simulateAiPass: (reviewId: string) =>
    apiRequest<Review>(`/reviews/${reviewId}/simulate-ai-pass`, {
      method: 'POST',
    }),

  getConferenceSession: (reviewId: string) =>
    apiRequest<ConferenceSessionResponse>(`/reviews/${reviewId}/conference`),

  deliberateConference: (reviewId: string, maxRounds: number = 2, customDiff?: string) =>
    apiRequest<ConferenceSessionResponse>(`/reviews/${reviewId}/conference/deliberate`, {
      method: 'POST',
      body: JSON.stringify({ max_rounds: maxRounds, custom_diff: customDiff }),
    }),

  listCouncilAgents: () =>
    apiRequest<{ agents: any[] }>('/reviews/council/registry'),
};
