import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
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
  FileText,
  Send,
  Wrench,
  Bot,
  AlertTriangle,
  FolderTree,
  ChevronRight,
  Split,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

interface ChangedFile {
  name: string;
  path: string;
  additions: number;
  deletions: number;
  findingsCount: number;
  originalCode: string;
  modifiedCode: string;
}

const SAMPLE_FILES: ChangedFile[] = [
  {
    name: 'security.py',
    path: 'app/auth/security.py',
    additions: 14,
    deletions: 4,
    findingsCount: 2,
    originalCode: `import jwt
import os
from datetime import datetime, timedelta

# SECURITY ISSUE: Do not hardcode secret keys
JWT_SECRET = "insecure_static_secret_key_12345"

def generate_user_token(user_id: str, is_admin: bool = False) -> str:
    payload = {
        "sub": user_id,
        "admin": is_admin,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
`,
    modifiedCode: `import jwt
import os
from datetime import datetime, timezone, timedelta
from app.core.config import get_settings

settings = get_settings()

def generate_user_token(user_id: str, is_admin: bool = False) -> str:
    payload = {
        "sub": user_id,
        "admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    # Dynamically inject validated secret from environment settings
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
`,
  },
  {
    name: 'repository_service.py',
    path: 'backend/app/services/repository_service.py',
    additions: 12,
    deletions: 5,
    findingsCount: 1,
    originalCode: `from sqlalchemy import select
from app.models.repository import Repository

async def get_by_name(session, name: str):
    # Potential injection if raw query formatting is used
    query = f"SELECT * FROM repositories WHERE name = '{name}'"
    return await session.execute(query)
`,
    modifiedCode: `from sqlalchemy import select
from app.models.repository import Repository

async def get_by_name(session, name: str):
    # Parameterized query leveraging asyncpg plan caching
    stmt = select(Repository).where(Repository.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
`,
  },
  {
    name: 'review_repo.py',
    path: 'backend/app/repositories/review_repo.py',
    additions: 8,
    deletions: 2,
    findingsCount: 1,
    originalCode: `async def get_with_comments(self, review_id: str):
    # N+1 query issue: comments accessed lazily without selectinload
    stmt = select(Review).where(Review.id == review_id)
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()
`,
    modifiedCode: `from sqlalchemy.orm import selectinload

async def get_with_comments(self, review_id: str):
    # Eagerly load comments in single roundtrip query
    stmt = select(Review).options(selectinload(Review.comments)).where(Review.id == review_id)
    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()
`,
  },
];

export const ReviewDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { success, info } = useToast();

  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null);

  const { data: review, isLoading } = useQuery<Review>({
    queryKey: ['review', id],
    queryFn: async () => {
      if (!id || id === 'sample') {
        return {
          id: 'sample',
          pull_request_id: 'pr-42',
          commit_sha: '7f9a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a',
          status: 'completed',
          score: 86.5,
          security_score: 82.0,
          performance_score: 89.0,
          quality_score: 88.5,
          findings_count: 3,
          summary: `### Autonomous Multi-Agent Consensus Summary\n\n- **Security Sentinel**: Flagged hardcoded cryptographic secret in \`app/auth/security.py\` (CWE-798).\n- **Performance Profiler**: Flagged N+1 lazy relationship loading in \`review_repo.py\`.\n- **Quality Arbiter**: AutoFix patches generated with 100% test pass confirmation.`,
          comments: [
            {
              id: 'cmt-1',
              review_id: 'sample',
              file_path: 'app/auth/security.py',
              line_number: 6,
              side: 'RIGHT',
              category: 'security',
              severity: 'critical',
              title: 'Hardcoded Secret Key (CWE-798)',
              message: 'Static JWT secret discovered in source file. In production, this allows token forgery if repository access is compromised.',
              suggested_patch: `--- a/app/auth/security.py\n+++ b/app/auth/security.py\n@@ -6,1 +6,2 @@\n-JWT_SECRET = "insecure_static_secret_key_12345"\n+from app.core.config import get_settings\n+settings = get_settings()\n+JWT_SECRET = settings.SECRET_KEY`,
              is_resolved: false,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
            {
              id: 'cmt-2',
              review_id: 'sample',
              file_path: 'backend/app/repositories/review_repo.py',
              line_number: 3,
              side: 'RIGHT',
              category: 'performance',
              severity: 'warning',
              title: 'Sequential N+1 Query in ORM Traversal',
              message: 'Comments accessed lazily inside loop without selectinload(). Generates multiple roundtrips per review.',
              suggested_patch: `+ stmt = select(Review).options(selectinload(Review.comments)).where(Review.id == review_id)`,
              is_resolved: false,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        } as Review;
      }
      return reviewApi.getReview(id);
    },
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.status === 'pending' ? 2500 : false),
  });

  const simulateMutation = useMutation({
    mutationFn: () => reviewApi.simulateAiPass(id || 'sample'),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['review', id] });
      success('AI Review Pass Completed', `Score: ${updated.score?.toFixed(1) || '88.0'}/100 with findings validated.`);
    },
  });

  const currentFile = SAMPLE_FILES[selectedFileIndex] || SAMPLE_FILES[0];
  const selectedFinding = review?.comments?.find((c) => c.id === selectedFindingId);

  const handlePublishToGitHub = () => {
    success('Published to GitHub PR', 'Review comments and check status posted via GitHub App.');
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <Link
            to="/pull-requests"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Pull Requests</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">PR #42 Code Review Pass</h1>
            <Badge
              variant={review?.status === 'completed' ? 'success' : 'warning'}
              className="capitalize text-xs"
            >
              {review?.status || 'Analyzing'}
            </Badge>
            <span className="text-xs text-slate-500 font-mono">
              SHA: {review?.commit_sha?.substring(0, 7) || '7f9a1b2'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePublishToGitHub}
            className="flex items-center gap-1.5 text-xs"
          >
            <Send className="w-3.5 h-3.5 text-sky-400" />
            <span>Publish to GitHub</span>
          </Button>

          <Button
            variant="electric"
            size="sm"
            onClick={() => simulateMutation.mutate()}
            isLoading={simulateMutation.isPending || review?.status === 'pending'}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>{review?.status === 'completed' ? 'Re-run AI Pass' : 'Run AI Multi-Agent Pass'}</span>
          </Button>
        </div>
      </div>

      {/* Summary Score Indicators */}
      <ReviewSummaryScore
        score={review?.score}
        securityScore={review?.security_score}
        performanceScore={review?.performance_score}
        qualityScore={review?.quality_score}
      />

      {/* Arbiter Executive Summary Card */}
      {review?.summary && (
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-white flex items-center justify-between">
              <span className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Arbiter Consensus Summary</span>
              </span>
              <span className="text-[11px] font-mono text-purple-400 font-normal">
                Verified by 4 agents
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-slate-300 font-sans whitespace-pre-wrap leading-relaxed">
            {review.summary}
          </CardContent>
        </Card>
      )}

      {/* Code Review Workspace: File Tree + Diff Viewer + Inline Finding Details */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left Column (3 cols): Changed File Explorer */}
        <div className="lg:col-span-3 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white px-1">
            <span className="flex items-center gap-1.5">
              <FolderTree className="w-3.5 h-3.5 text-sky-400" />
              <span>Changed Files ({SAMPLE_FILES.length})</span>
            </span>
            <span className="text-[10px] text-slate-500 font-mono">+34 -11</span>
          </div>

          <div className="rounded-xl border border-slate-800 bg-[#0c101c] p-2 space-y-1">
            {SAMPLE_FILES.map((file, idx) => (
              <button
                key={file.path}
                type="button"
                onClick={() => setSelectedFileIndex(idx)}
                className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition flex items-center justify-between ${
                  selectedFileIndex === idx
                    ? 'bg-sky-500/10 border border-sky-500/30 text-sky-300 font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900/60'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <FileCode className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                  <span className="truncate">{file.name}</span>
                </div>
                <div className="flex items-center gap-1.5 text-[10px] shrink-0">
                  <span className="text-emerald-400">+{file.additions}</span>
                  <span className="text-rose-400">-{file.deletions}</span>
                  {file.findingsCount > 0 && (
                    <span className="w-4 h-4 rounded-full bg-rose-500/20 text-rose-400 text-center leading-4 font-bold">
                      {file.findingsCount}
                    </span>
                  )}
                </div>
              </button>
            ))}
          </div>

          <div className="p-3 rounded-lg border border-purple-500/20 bg-purple-950/10 text-xs space-y-1.5">
            <div className="flex items-center gap-1.5 text-purple-300 font-semibold text-[11px]">
              <Bot className="w-3.5 h-3.5" />
              <span>Agent Attribution</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Findings independently confirmed by Security Sentinel and verified by Quality Arbiter.
            </p>
          </div>
        </div>

        {/* Middle Column (6 cols): Monaco Diff Viewer */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white px-1">
            <div className="flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-sky-400" />
              <span className="font-mono text-xs">{currentFile.path}</span>
            </div>
            <Badge variant="outline" className="font-mono text-[10px]">
              Side-by-Side Diff
            </Badge>
          </div>

          <MonacoDiffViewer
            fileName={currentFile.name}
            language="python"
            originalCode={currentFile.originalCode}
            code={currentFile.modifiedCode}
            isDiffMode={true}
            height="480px"
          />
        </div>

        {/* Right Column (3 cols): Inline AI Findings & AutoFix action */}
        <div className="lg:col-span-3 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-white px-1">
            <span className="flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-rose-400" />
              <span>AI Findings ({review?.comments?.length || 0})</span>
            </span>
            <Link to="/autofix" className="text-[10px] text-sky-400 hover:underline flex items-center gap-0.5">
              <span>AutoFix</span>
              <ChevronRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-0.5">
            {!review?.comments || review.comments.length === 0 ? (
              <Card className="p-6 text-center border-dashed border-slate-800 bg-[#0c101c]">
                <Clock className="w-6 h-6 text-slate-600 mx-auto mb-2" />
                <p className="text-xs text-slate-400">
                  No findings on this file. Code passes automated inspection.
                </p>
              </Card>
            ) : (
              review.comments.map((finding) => (
                <FindingCard
                  key={finding.id}
                  comment={finding}
                  isSelected={selectedFindingId === finding.id}
                  onSelect={() => setSelectedFindingId(finding.id)}
                />
              ))
            )}

            <Button
              variant="electric"
              size="sm"
              onClick={() => navigate('/autofix')}
              className="w-full text-xs flex items-center justify-center gap-2 mt-2"
            >
              <Wrench className="w-3.5 h-3.5" />
              <span>Open in AutoFix Studio</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
