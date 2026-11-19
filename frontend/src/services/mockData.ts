/**
 * Mock data for OpenReview AI frontend.
 * Used for features whose backend endpoints are scheduled for subsequent phases,
 * cleanly separated from real API integrations.
 */

export interface SecurityVulnerability {
  id: string;
  cveId?: string;
  category: 'Injection' | 'Authentication' | 'Cryptographic' | 'Access Control' | 'Misconfiguration';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  filePath: string;
  lineNumber: number;
  repository: string;
  detectedAt: string;
  status: 'open' | 'fixing' | 'resolved' | 'ignored';
  owaspTag: string;
  remediationSnippet?: string;
}

export const mockSecurityVulnerabilities: SecurityVulnerability[] = [
  {
    id: 'sec-101',
    cveId: 'CWE-89',
    category: 'Injection',
    severity: 'critical',
    title: 'SQL Injection via Unsanitized Raw String Formatting',
    description: 'Raw string interpolation inside cursor.execute allows arbitrary SQL execution if user input is unescaped.',
    filePath: 'backend/app/services/repository_service.py',
    lineNumber: 84,
    repository: 'google-deepmind/openreview-ai',
    detectedAt: '10 minutes ago',
    status: 'open',
    owaspTag: 'A03:2021-Injection',
    remediationSnippet: 'await session.execute(select(Repository).where(Repository.name == user_input))',
  },
  {
    id: 'sec-102',
    cveId: 'CWE-798',
    category: 'Cryptographic',
    severity: 'critical',
    title: 'Hardcoded Cryptographic Secret / JWT Signing Key',
    description: 'Static JWT secret discovered in source file. In production, tokens can be forged if the repository is cloned.',
    filePath: 'app/auth/security.py',
    lineNumber: 6,
    repository: 'google-deepmind/openreview-ai',
    detectedAt: '25 minutes ago',
    status: 'open',
    owaspTag: 'A02:2021-Cryptographic Failures',
    remediationSnippet: 'JWT_SECRET = settings.SECRET_KEY.get_secret_value()',
  },
  {
    id: 'sec-103',
    cveId: 'CWE-384',
    category: 'Authentication',
    severity: 'high',
    title: 'Missing Session Invalidation on Password Reset',
    description: 'Existing refresh tokens remain valid after account password modification, permitting session hijacking.',
    filePath: 'backend/app/api/v1/endpoints/auth.py',
    lineNumber: 142,
    repository: 'acme/payment-gateway',
    detectedAt: '2 hours ago',
    status: 'fixing',
    owaspTag: 'A07:2021-Auth Failures',
    remediationSnippet: 'await revoke_all_user_sessions(user_id=user.id)',
  },
  {
    id: 'sec-104',
    cveId: 'CWE-639',
    category: 'Access Control',
    severity: 'high',
    title: 'Insecure Direct Object Reference (IDOR) on Pull Request Deletion',
    description: 'Endpoint accepts repository_id and pr_id without verifying the requesting user possesses administrative permissions.',
    filePath: 'backend/app/api/v1/endpoints/pull_requests.py',
    lineNumber: 91,
    repository: 'acme/payment-gateway',
    detectedAt: '5 hours ago',
    status: 'open',
    owaspTag: 'A01:2021-Broken Access Control',
  },
  {
    id: 'sec-105',
    category: 'Misconfiguration',
    severity: 'medium',
    title: 'Permissive Wildcard CORS Header in Staging Profile',
    description: 'Access-Control-Allow-Origin is set to wildcard "*" when credentials flag is enabled.',
    filePath: 'backend/app/main.py',
    lineNumber: 52,
    repository: 'google-deepmind/openreview-ai',
    detectedAt: '1 day ago',
    status: 'resolved',
    owaspTag: 'A05:2021-Security Misconfiguration',
  },
];

export interface PerformanceIssue {
  id: string;
  type: 'N+1 Query' | 'Memory Leak' | 'Big-O Regression' | 'Unindexed Scan' | 'Blocking I/O';
  severity: 'high' | 'medium' | 'low';
  title: string;
  impact: string;
  filePath: string;
  lineNumber: number;
  repository: string;
  estimatedLatencyPenalty: string;
  suggestedOptimization: string;
}

export const mockPerformanceIssues: PerformanceIssue[] = [
  {
    id: 'perf-201',
    type: 'N+1 Query',
    severity: 'high',
    title: 'Sequential ORM Relationship Loading in Loop',
    impact: 'Executes 1 + N database roundtrips when querying review comments, generating 80+ redundant queries under load.',
    filePath: 'backend/app/repositories/review_repo.py',
    lineNumber: 32,
    repository: 'google-deepmind/openreview-ai',
    estimatedLatencyPenalty: '+340ms per request',
    suggestedOptimization: 'Use selectinload(Review.comments) to eagerly load all comments in a single query.',
  },
  {
    id: 'perf-202',
    type: 'Big-O Regression',
    severity: 'high',
    title: 'Nested Array Lookup Generating O(N^2) Time Complexity',
    impact: 'Double nested list traversal during diff hunk reconciliation scales poorly on PRs exceeding 500 lines.',
    filePath: 'workers/tasks/diff_analyzer.py',
    lineNumber: 114,
    repository: 'google-deepmind/openreview-ai',
    estimatedLatencyPenalty: '+1.8s on large diffs',
    suggestedOptimization: 'Pre-index file diffs into a dictionary mapping file path to hunk list for O(1) lookups.',
  },
  {
    id: 'perf-203',
    type: 'Blocking I/O',
    severity: 'medium',
    title: 'Synchronous File Read inside Async Event Loop',
    impact: 'Calling built-in open().read() blocks FastAPI asyncio event loop, starving concurrent client connections.',
    filePath: 'backend/app/services/llm_provider_service.py',
    lineNumber: 68,
    repository: 'google-deepmind/openreview-ai',
    estimatedLatencyPenalty: '+45ms throughput jitter',
    suggestedOptimization: 'Use aiofiles.open() or run the file read inside anyio.to_thread.run_sync().',
  },
  {
    id: 'perf-204',
    type: 'Unindexed Scan',
    severity: 'medium',
    title: 'Missing Composite Index on (repository_id, created_at)',
    impact: 'PostgreSQL performs sequential table scan when ordering pull requests by recency.',
    filePath: 'infrastructure/postgres/init-pgvector.sql',
    lineNumber: 28,
    repository: 'google-deepmind/openreview-ai',
    estimatedLatencyPenalty: '+85ms on tables > 100k rows',
    suggestedOptimization: 'CREATE INDEX ix_pull_requests_repo_created ON pull_requests(repository_id, created_at DESC);',
  },
];

export interface AgentConferenceMember {
  id: string;
  name: string;
  role: string;
  avatarColor: string;
  status: 'active' | 'analyzing' | 'debating' | 'consensus';
  currentFocus: string;
  findingsCount: number;
  confidenceScore: number;
}

export const mockConferenceAgents: AgentConferenceMember[] = [
  {
    id: 'agent-sec',
    name: 'Security Sentinel',
    role: 'Vulnerability & Secrets Specialist',
    avatarColor: 'from-rose-500 to-red-600',
    status: 'debating',
    currentFocus: 'Validating potential CWE-89 injection in query builder',
    findingsCount: 3,
    confidenceScore: 97.4,
  },
  {
    id: 'agent-perf',
    name: 'Performance Profiler',
    role: 'Complexity & Latency Specialist',
    avatarColor: 'from-amber-500 to-orange-600',
    status: 'debating',
    currentFocus: 'Calculating algorithmic asymptotic bound on AST traversal',
    findingsCount: 2,
    confidenceScore: 94.1,
  },
  {
    id: 'agent-bug',
    name: 'Bug Hunter',
    role: 'Logic & Edge-Case Specialist',
    avatarColor: 'from-sky-500 to-blue-600',
    status: 'analyzing',
    currentFocus: 'Checking NoneType dereference if Redis client is disconnected',
    findingsCount: 4,
    confidenceScore: 91.8,
  },
  {
    id: 'agent-style',
    name: 'Style & Standards',
    role: 'Clean Architecture Enforcer',
    avatarColor: 'from-purple-500 to-indigo-600',
    status: 'consensus',
    currentFocus: 'Verifying dependency injection conventions and typing',
    findingsCount: 1,
    confidenceScore: 99.0,
  },
  {
    id: 'agent-arbiter',
    name: 'Quality Arbiter',
    role: 'Consensus Builder & Diff Formatter',
    avatarColor: 'from-emerald-500 to-teal-600',
    status: 'debating',
    currentFocus: 'Synthesizing final Pull Request review score & suggested patches',
    findingsCount: 10,
    confidenceScore: 96.5,
  },
];

export interface AgentDebateMessage {
  id: string;
  agentId: string;
  agentName: string;
  timestamp: string;
  type: 'claim' | 'counter-claim' | 'verification' | 'consensus';
  content: string;
  fileContext?: string;
  verified: boolean;
}

export const mockDebateTimeline: AgentDebateMessage[] = [
  {
    id: 'msg-1',
    agentId: 'agent-sec',
    agentName: 'Security Sentinel',
    timestamp: '11:18:02',
    type: 'claim',
    content: 'Flagging Critical finding: Raw string concatenation inside query string in repository_service.py:84 exposes database to SQL injection.',
    fileContext: 'backend/app/services/repository_service.py#L84',
    verified: true,
  },
  {
    id: 'msg-2',
    agentId: 'agent-bug',
    agentName: 'Bug Hunter',
    timestamp: '11:18:05',
    type: 'counter-claim',
    content: 'Evaluating caller hierarchy: The string parameter is derived from GitHub webhook full_name which regex-validates against ^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$. Does this reduce exploitability?',
    fileContext: 'backend/app/services/repository_service.py#L84',
    verified: true,
  },
  {
    id: 'msg-3',
    agentId: 'agent-sec',
    agentName: 'Security Sentinel',
    timestamp: '11:18:11',
    type: 'counter-claim',
    content: 'While input is currently constrained upstream, defense-in-depth requires parameterized queries to eliminate future regressions or alternative call-sites.',
    verified: true,
  },
  {
    id: 'msg-4',
    agentId: 'agent-perf',
    agentName: 'Performance Profiler',
    timestamp: '11:18:18',
    type: 'verification',
    content: 'Agreed. Furthermore, using parameterized SQLAlchemy select() leverages query plan caching inside asyncpg, improving query throughput by ~12%.',
    verified: true,
  },
  {
    id: 'msg-5',
    agentId: 'agent-arbiter',
    agentName: 'Quality Arbiter',
    timestamp: '11:18:24',
    type: 'consensus',
    content: 'Consensus approved. Severity confirmed as Critical. Generating unified replacement patch using select(Repository).where(Repository.name == user_input).',
    fileContext: 'backend/app/services/repository_service.py',
    verified: true,
  },
];

export interface AutoFixItem {
  id: string;
  title: string;
  category: 'security' | 'performance' | 'bug' | 'style';
  severity: 'critical' | 'high' | 'medium';
  filePath: string;
  prNumber: number;
  originalCode: string;
  proposedCode: string;
  testStatus: 'passed' | 'running' | 'failed';
  testsSummary: string;
  explanation: string;
}

export const mockAutoFixProposals: AutoFixItem[] = [
  {
    id: 'fix-1',
    title: 'Replace Insecure Hardcoded Secret with Settings Loader',
    category: 'security',
    severity: 'critical',
    filePath: 'app/auth/security.py',
    prNumber: 42,
    originalCode: `import jwt
import os

# SECURITY ISSUE: Do not hardcode secret keys
JWT_SECRET = "insecure_static_secret_key_12345"

def generate_user_token(user_id: str, is_admin: bool = False) -> str:
    payload = {"sub": user_id, "admin": is_admin}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
`,
    proposedCode: `import jwt
import os
from app.core.config import get_settings

settings = get_settings()

def generate_user_token(user_id: str, is_admin: bool = False) -> str:
    payload = {"sub": user_id, "admin": is_admin}
    # Dynamically inject secret from environment with secure fallback check
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
`,
    testStatus: 'passed',
    testsSummary: '4/4 unit tests passed (pytest)',
    explanation: 'Safely loads SECRET_KEY from the central Pydantic settings singleton, eliminating credential leaks.',
  },
  {
    id: 'fix-2',
    title: 'Resolve N+1 Query in Review Comment Retrieval',
    category: 'performance',
    severity: 'high',
    filePath: 'backend/app/repositories/review_repo.py',
    prNumber: 42,
    originalCode: `async def get_with_comments(self, review_id: str):
    result = await self.session.execute(
        select(Review).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    # N+1 query: comments accessed lazily without eager selectinload
    return review
`,
    proposedCode: `async def get_with_comments(self, review_id: str):
    result = await self.session.execute(
        select(Review)
        .options(selectinload(Review.comments))
        .where(Review.id == review_id)
    )
    return result.scalar_one_or_none()
`,
    testStatus: 'passed',
    testsSummary: 'Query count reduced from 42 to 1 (97% reduction)',
    explanation: 'Applies SQLAlchemy 2.0 selectinload option to execute a single optimized query with JOIN.',
  },
  {
    id: 'fix-3',
    title: 'Prevent Redis Connection Socket Leak on Ping',
    category: 'bug',
    severity: 'medium',
    filePath: 'backend/app/services/health_service.py',
    prNumber: 39,
    originalCode: `async def check_redis(self):
    client = aioredis.from_url(settings.REDIS_URL)
    pong = await client.ping()
    # Missing explicit client.aclose() on early return
    return pong
`,
    proposedCode: `async def check_redis(self):
    client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2.0)
    try:
        pong = await client.ping()
        return bool(pong)
    finally:
        await client.aclose()
`,
    testStatus: 'passed',
    testsSummary: 'Zero socket leaks detected in stress test',
    explanation: 'Guarantees socket closure in finally block even if ping raises connection timeout.',
  },
];

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'Admin' | 'Maintainer' | 'Reviewer' | 'Auditor';
  avatar: string;
  lastActive: string;
  twoFactorEnabled: boolean;
}

export const mockTeamMembers: TeamMember[] = [
  {
    id: 'usr-1',
    name: 'Dr. Jane Turing',
    email: 'jane@openreview.ai',
    role: 'Admin',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=faces',
    lastActive: 'Active now',
    twoFactorEnabled: true,
  },
  {
    id: 'usr-2',
    name: 'Alex Rivera',
    email: 'alex.rivera@openreview.ai',
    role: 'Maintainer',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=faces',
    lastActive: '12m ago',
    twoFactorEnabled: true,
  },
  {
    id: 'usr-3',
    name: 'Sarah Chen',
    email: 'schen@deepmind-labs.org',
    role: 'Reviewer',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=faces',
    lastActive: '2h ago',
    twoFactorEnabled: true,
  },
  {
    id: 'usr-4',
    name: 'Devon Vance',
    email: 'dvance@security-audit.io',
    role: 'Auditor',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=faces',
    lastActive: 'Yesterday',
    twoFactorEnabled: false,
  },
];

export interface ReviewAuditLog {
  id: string;
  timestamp: string;
  repository: string;
  prNumber: number;
  commitSha: string;
  author: string;
  outcome: 'Passed' | 'Changes Requested' | 'Failed';
  score: number;
  findingsCount: number;
  durationMs: number;
  agentModel: string;
}

export const mockReviewAuditLogs: ReviewAuditLog[] = [
  {
    id: 'audit-001',
    timestamp: '2026-11-19 11:15:30',
    repository: 'google-deepmind/openreview-ai',
    prNumber: 42,
    commitSha: '7f9a1b2',
    author: 'octocat',
    outcome: 'Changes Requested',
    score: 78.5,
    findingsCount: 4,
    durationMs: 2420,
    agentModel: 'gpt-4o-mini',
  },
  {
    id: 'audit-002',
    timestamp: '2026-11-19 10:48:12',
    repository: 'google-deepmind/openreview-ai',
    prNumber: 41,
    commitSha: '9c4d2e1',
    author: 'alexrivera',
    outcome: 'Passed',
    score: 96.0,
    findingsCount: 0,
    durationMs: 1840,
    agentModel: 'claude-3-5-sonnet',
  },
  {
    id: 'audit-003',
    timestamp: '2026-11-19 09:22:45',
    repository: 'acme/payment-gateway',
    prNumber: 104,
    commitSha: 'e3f1a90',
    author: 'schen',
    outcome: 'Changes Requested',
    score: 64.0,
    findingsCount: 6,
    durationMs: 3100,
    agentModel: 'gemini-1.5-pro',
  },
  {
    id: 'audit-004',
    timestamp: '2026-11-18 17:05:19',
    repository: 'acme/payment-gateway',
    prNumber: 103,
    commitSha: 'b4a8c71',
    author: 'dvance',
    outcome: 'Passed',
    score: 92.5,
    findingsCount: 1,
    durationMs: 1650,
    agentModel: 'gpt-4o-mini',
  },
  {
    id: 'audit-005',
    timestamp: '2026-11-18 14:11:03',
    repository: 'google-deepmind/openreview-ai',
    prNumber: 40,
    commitSha: '3d8f1e0',
    author: 'jturing',
    outcome: 'Passed',
    score: 98.0,
    findingsCount: 0,
    durationMs: 1420,
    agentModel: 'claude-3-5-sonnet',
  },
];
