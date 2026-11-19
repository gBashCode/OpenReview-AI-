import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewApi } from '@/services/reviewApi';
import { Review, ReviewComment } from '@/types/review';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ReviewSummaryScore } from '@/components/reviews/ReviewSummaryScore';
import { FindingCard } from '@/components/reviews/FindingCard';
import { MonacoDiffViewer } from '@/components/code/MonacoDiffViewer';
import {
  Sparkles,
  ArrowLeft,
  CheckCircle2,
  Clock,
  FileCode,
  Shield,
} from 'lucide-react';

const SAMPLE_CODE = `import jwt
import os
from datetime import datetime, timedelta

# SECURITY ISSUE: Do not hardcode secret keys
JWT_SECRET = "insecure_static_secret_key_12345"

def generate_user_token(user_id: str, is_admin: bool = False) -> str:
    """Generates authentication JWT for user session."""
    payload = {
        "sub": user_id,
        "admin": is_admin,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    # VULNERABILITY: Weak algorithm with hardcoded secret
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token: str):
    # Missing audience and issuer validations
    return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
`;

export const ReviewDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  const { data: review, isLoading } = useQuery<Review>({
    queryKey: ['review', id],
    queryFn: () => reviewApi.getReview(id!),
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.status === 'pending' ? 3000 : false),
  });

  const simulateMutation = useMutation({
    mutationFn: () => reviewApi.simulateAiPass(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review', id] });
    },
  });

  if (isLoading) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono text-sm">
        Loading review run details...
      </div>
    );
  }

  if (!review) {
    return (
      <div className="p-12 text-center">
        <h2 className="text-xl font-bold text-white mb-2">Review Not Found</h2>
        <Link to="/pull-requests">
          <Button variant="outline">Back to Pull Requests</Button>
        </Link>
      </div>
    );
  }

  const selectedFinding = review.comments?.find((c: ReviewComment) => c.id === selectedFindingId);

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <Link
            to="/pull-requests"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Pull Requests</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">Code Review Run</h1>
            <Badge
              variant={
                review.status === 'completed'
                  ? 'success'
                  : review.status === 'pending'
                  ? 'warning'
                  : 'secondary'
              }
              className="capitalize"
            >
              {review.status}
            </Badge>
          </div>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Commit SHA: {review.commit_sha}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            onClick={() => simulateMutation.mutate()}
            isLoading={simulateMutation.isPending || review.status === 'pending'}
            className="flex items-center gap-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-600 hover:to-indigo-700 shadow-lg shadow-sky-500/20"
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span>{review.status === 'completed' ? 'Re-run AI Pass' : 'Run AI Multi-Agent Pass'}</span>
          </Button>
        </div>
      </div>

      {/* Scores */}
      <ReviewSummaryScore
        score={review.score}
        securityScore={review.security_score}
        performanceScore={review.performance_score}
        qualityScore={review.quality_score}
      />

      {/* Summary Card */}
      {review.summary && (
        <Card className="border-slate-800 bg-slate-900/40">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Arbiter Executive Summary</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-invert prose-sm max-w-none text-slate-300 whitespace-pre-wrap leading-relaxed font-sans">
              {review.summary}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Review Workspace: Code Diff & Findings */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Code Viewer with Monaco */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <FileCode className="w-4 h-4 text-sky-400" />
              <span>Inspected Diff Context</span>
            </div>
            <span className="text-xs text-slate-400 font-mono">Monaco Editor v0.46</span>
          </div>

          <MonacoDiffViewer
            fileName="app/auth/security.py"
            language="python"
            code={selectedFinding?.suggested_patch ? selectedFinding.suggested_patch : SAMPLE_CODE}
            highlightLine={selectedFinding?.line_number}
            height="460px"
          />
        </div>

        {/* Right: AI Agent Findings List */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <Shield className="w-4 h-4 text-rose-400" />
              <span>Agent Findings ({review.comments?.length || 0})</span>
            </div>
            <span className="text-xs text-slate-400 font-mono">Validated</span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {!review.comments || review.comments.length === 0 ? (
              <Card className="p-8 text-center border-dashed border-slate-800">
                <Clock className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400">
                  No findings recorded yet. Click &quot;Run AI Multi-Agent Pass&quot; to analyze this pull request.
                </p>
              </Card>
            ) : (
              review.comments.map((finding: ReviewComment) => (
                <FindingCard
                  key={finding.id}
                  comment={finding}
                  isSelected={selectedFindingId === finding.id}
                  onSelect={() => setSelectedFindingId(finding.id)}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
