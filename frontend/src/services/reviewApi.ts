import { apiRequest } from './apiClient';
import { Review } from '../types/review';

export const reviewApi = {
  createReview: (pullRequestId: string, commitSha: string) =>
    apiRequest<Review>('/reviews', {
      method: 'POST',
      body: JSON.stringify({ pull_request_id: pullRequestId, commit_sha: commitSha }),
    }),

  getReview: (reviewId: string) => apiRequest<Review>(`/reviews/${reviewId}`),

  listReviewsForPR: (prId: string) => apiRequest<Review[]>(`/pull-requests/${prId}/reviews`),

  simulateAiPass: (reviewId: string) =>
    apiRequest<Review>(`/reviews/${reviewId}/simulate-ai-pass`, {
      method: 'POST',
    }),
};
