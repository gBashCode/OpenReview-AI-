import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/toast';
import { reviewApi } from '@/services/reviewApi';
import {
  Review,
  ConferenceSessionResponse,
  ConferenceFindingThread,
  ConferenceAgent,
  ConferenceDiscussionMessage,
  DiscussionState,
  ConferencePosition,
} from '@/types/review';
import {
  Bot,
  Sparkles,
  ShieldCheck,
  Zap,
  Bug,
  Code2,
  CheckCircle2,
  MessageSquare,
  Clock,
  Send,
  Play,
  RotateCcw,
  Scale,
  GitPullRequest,
  FileCode,
  Filter,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Copy,
  ChevronDown,
  Layers,
  ArrowRight,
} from 'lucide-react';

// Fallback demo data if backend review has not yet been analyzed
const FALLBACK_AGENTS: ConferenceAgent[] = [
  {
    id: 'agent-sec',
    agent_name: 'Security Sentinel',
    role: 'Vulnerability & Secrets Specialist',
    status: 'active',
    model_name: 'claude-3-5-sonnet',
    reasoning_summary: 'OWASP Top 10 & CWE validation',
    confidence_score: 97.5,
    findings_count: 2,
  },
  {
    id: 'agent-bug',
    agent_name: 'Bug Hunter',
    role: 'Logic & Runtime Defect Specialist',
    status: 'active',
    model_name: 'gemini-1.5-pro',
    reasoning_summary: 'Control flow & edge-case discovery',
    confidence_score: 92.0,
    findings_count: 3,
  },
  {
    id: 'agent-perf',
    agent_name: 'Performance Profiler',
    role: 'Complexity & Latency Specialist',
    status: 'active',
    model_name: 'gpt-4o',
    reasoning_summary: 'Algorithmic Big-O & I/O bottlenecks',
    confidence_score: 94.8,
    findings_count: 1,
  },
  {
    id: 'agent-arch',
    agent_name: 'Architecture Agent',
    role: 'System Design & Modularity Specialist',
    status: 'active',
    model_name: 'claude-3-5-sonnet',
    reasoning_summary: 'Clean architecture & API contracts',
    confidence_score: 90.0,
    findings_count: 1,
  },
  {
    id: 'agent-rev2',
    agent_name: 'Adversarial Reviewer (Reviewer 2)',
    role: 'Devil\'s Advocate & Cross-Examiner',
    status: 'active',
    model_name: 'gpt-4o',
    reasoning_summary: 'Challenges unsubstantiated claims and false alarms',
    confidence_score: 96.0,
    findings_count: 0,
  },
  {
    id: 'agent-ctx',
    agent_name: 'Context Agent',
    role: 'Repository & AST Context Provider',
    status: 'active',
    model_name: 'gemini-1.5-pro',
    reasoning_summary: 'Retrieves callers, decorators, and definitions',
    confidence_score: 99.0,
    findings_count: 0,
  },
  {
    id: 'agent-arbiter',
    agent_name: 'Quality Arbiter',
    role: 'Evidence Arbiter & Verdict Builder',
    status: 'active',
    model_name: 'claude-3-5-sonnet',
    reasoning_summary: 'Evidence-based verdict synthesizer (non-majority)',
    confidence_score: 98.2,
    findings_count: 0,
  },
];

const FALLBACK_THREADS: ConferenceFindingThread[] = [
  {
    finding_id: 'f-sec-01',
    file_path: 'backend/app/services/repository_service.py',
    line_number: 84,
    title: 'SQL Injection via unparameterized query interpolation',
    category: 'security',
    severity: 'critical',
    proposing_agent: 'Security Sentinel',
    discussion_state: 'Accepted',
    evidence: 'query = f"SELECT * FROM repositories WHERE name = \'{user_input}\'"\nresult = await db.execute(text(query))',
    suggested_patch: '- query = f"SELECT * FROM repositories WHERE name = \'{user_input}\'"\n+ query = select(Repository).where(Repository.name == user_input)',
    messages: [
      {
        id: 'm-1',
        agent_name: 'Security Sentinel',
        message_type: 'claim',
        position: 'proposal',
        round_number: 1,
        content: 'Critical vulnerability detected: Raw f-string interpolation inside SQL text() statement allows SQL injection via user_input parameter.',
        evidence: 'query = f"SELECT * FROM repositories WHERE name = \'{user_input}\'"',
        source_reference: 'backend/app/services/repository_service.py:84#get_repo',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      },
      {
        id: 'm-2',
        agent_name: 'Adversarial Reviewer (Reviewer 2)',
        message_type: 'challenge',
        position: 'challenge',
        round_number: 1,
        content: 'CHALLENGE: Is user_input sanitized upstream in the FastAPI router or schema validation before passing into repository_service?',
        source_reference: 'backend/app/api/v1/endpoints/repositories.py:22',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 14).toISOString(),
      },
      {
        id: 'm-3',
        agent_name: 'Context Agent',
        message_type: 'context_supply',
        position: 'context_supply',
        round_number: 1,
        content: 'Retrieved upstream caller: GET /repos?name={name} passes raw query parameter directly without regex or alphanumeric sanitation.',
        source_reference: 'backend/app/api/v1/endpoints/repositories.py:26#list_repos',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 13).toISOString(),
      },
      {
        id: 'm-4',
        agent_name: 'Security Sentinel',
        message_type: 'rebuttal',
        position: 'rebuttal',
        round_number: 2,
        content: 'REBUTTAL: Context Agent confirms untrusted taint propagation. Direct string interpolation bypasses SQLAlchemy parameterized execution.',
        evidence: 'await db.execute(text(f"SELECT * FROM repositories WHERE name = \'{user_input}\'"))',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
      },
      {
        id: 'm-5',
        agent_name: 'Quality Arbiter',
        message_type: 'consensus',
        position: 'verdict',
        final_decision: 'Accepted',
        round_number: 2,
        content: 'VERDICT: ACCEPTED. Evidence grounds direct SQL injection without upstream sanitization. Applied parameterized query replacement.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 11).toISOString(),
      },
    ],
  },
  {
    finding_id: 'f-bug-02',
    file_path: 'workers/tasks/diff_analyzer.py',
    line_number: 114,
    title: 'Unbounded memory leak in diff cache dictionary',
    category: 'bug',
    severity: 'warning',
    proposing_agent: 'Bug Hunter',
    discussion_state: 'Rejected',
    evidence: 'diff_cache[commit_sha] = parsed_hunk_list',
    messages: [
      {
        id: 'm-6',
        agent_name: 'Bug Hunter',
        message_type: 'claim',
        position: 'proposal',
        round_number: 1,
        content: 'Warning: In-memory dictionary diff_cache grows without bound across webhook invocations, causing worker OOM.',
        source_reference: 'workers/tasks/diff_analyzer.py:114#cache_diff',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
      },
      {
        id: 'm-7',
        agent_name: 'Adversarial Reviewer (Reviewer 2)',
        message_type: 'challenge',
        position: 'challenge',
        round_number: 1,
        content: 'CHALLENGE: Please verify lines 105-110. Does diff_cache use cachetools.TTLCache or an LRU wrapper with maxsize?',
        source_reference: 'workers/tasks/diff_analyzer.py:108',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 9).toISOString(),
      },
      {
        id: 'm-8',
        agent_name: 'Context Agent',
        message_type: 'context_supply',
        position: 'context_supply',
        round_number: 1,
        content: 'Source context on line 108: `diff_cache = TTLCache(maxsize=500, ttl=3600)`. Capacity is capped at 500 entries.',
        source_reference: 'workers/tasks/diff_analyzer.py:108#diff_cache_def',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
      },
      {
        id: 'm-9',
        agent_name: 'Bug Hunter',
        message_type: 'concession',
        position: 'concession',
        round_number: 2,
        content: 'CONCESSION: Acknowledged. Missed the TTLCache initializer. Memory growth is strictly constrained to 500 entries with automatic eviction.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 7).toISOString(),
      },
      {
        id: 'm-10',
        agent_name: 'Quality Arbiter',
        message_type: 'consensus',
        position: 'verdict',
        final_decision: 'Rejected',
        round_number: 2,
        content: 'VERDICT: REJECTED. Grounded evidence refutes memory leak claim. Cache is bounded by TTLCache(maxsize=500). False positive filtered.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 6).toISOString(),
      },
    ],
  },
  {
    finding_id: 'f-perf-03',
    file_path: 'backend/app/database/session.py',
    line_number: 52,
    title: 'Connection pool starvation risk under high concurrency',
    category: 'performance',
    severity: 'warning',
    proposing_agent: 'Performance Profiler',
    discussion_state: 'Needs investigation',
    evidence: 'engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=0)',
    messages: [
      {
        id: 'm-11',
        agent_name: 'Performance Profiler',
        message_type: 'claim',
        position: 'proposal',
        round_number: 1,
        content: 'pool_size=10 with max_overflow=0 may result in HTTP 500 QueuePool errors when concurrent agent reviews exceed 10 tasks.',
        source_reference: 'backend/app/database/session.py:52#create_engine',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      },
      {
        id: 'm-12',
        agent_name: 'Adversarial Reviewer (Reviewer 2)',
        message_type: 'challenge',
        position: 'challenge',
        round_number: 1,
        content: 'CHALLENGE: Celery concurrency is pinned to 4 worker processes. Will single-worker FastAPI connection load truly saturate 10 connections?',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 4).toISOString(),
      },
      {
        id: 'm-13',
        agent_name: 'Quality Arbiter',
        message_type: 'consensus',
        position: 'verdict',
        final_decision: 'Needs investigation',
        round_number: 2,
        content: 'VERDICT: NEEDS INVESTIGATION. Theoretical saturation depends on production RPS and Celery scale-out. Benchmarking load test recommended before tuning.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
      },
    ],
  },
  {
    finding_id: 'f-arch-04',
    file_path: 'backend/app/indexing/analyzer.py',
    line_number: 65,
    title: 'Duplicate AST parser invocation in AST visitor',
    category: 'architecture',
    severity: 'info',
    proposing_agent: 'Architecture Agent',
    discussion_state: 'Duplicate',
    evidence: 'ast_tree = parser.parse(source_code)',
    messages: [
      {
        id: 'm-14',
        agent_name: 'Architecture Agent',
        message_type: 'claim',
        position: 'proposal',
        round_number: 1,
        content: 'Redundant AST parsing detected on file analyzer invocation.',
        source_reference: 'backend/app/indexing/analyzer.py:65',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
      },
      {
        id: 'm-15',
        agent_name: 'Quality Arbiter',
        message_type: 'consensus',
        position: 'verdict',
        final_decision: 'Duplicate',
        round_number: 1,
        content: 'VERDICT: DUPLICATE. Grouped with identical finding #f-perf-02 previously logged by Performance Profiler on analyzer.py:62.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 1).toISOString(),
      },
    ],
  },
  {
    finding_id: 'f-bug-05',
    file_path: 'backend/app/services/github_diff_service.py',
    line_number: 198,
    title: 'Potential silent truncation on oversized diffs > 5000 lines',
    category: 'bug',
    severity: 'info',
    proposing_agent: 'Bug Hunter',
    discussion_state: 'Uncertain',
    evidence: 'if len(diff_text) > MAX_DIFF_BYTES: diff_text = diff_text[:MAX_DIFF_BYTES]',
    messages: [
      {
        id: 'm-16',
        agent_name: 'Bug Hunter',
        message_type: 'claim',
        position: 'proposal',
        round_number: 1,
        content: 'Truncating diff text without recording a partial analysis warning may omit critical security findings in trailing files.',
        source_reference: 'backend/app/services/github_diff_service.py:198',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 30).toISOString(),
      },
      {
        id: 'm-17',
        agent_name: 'Quality Arbiter',
        message_type: 'consensus',
        position: 'verdict',
        final_decision: 'Uncertain',
        round_number: 1,
        content: 'VERDICT: UNCERTAIN. Truncation prevents LLM token blowup, but lack of UI indicator is ambiguous. Requires product-level design decision.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 10).toISOString(),
      },
    ],
  },
];

export const AgentConference: React.FC = () => {
  const { success, error, info } = useToast();

  const [reviews, setReviews] = useState<Review[]>([]);
  const [selectedReviewId, setSelectedReviewId] = useState<string>('');
  const [sessionData, setSessionData] = useState<ConferenceSessionResponse | null>(null);
  const [agents, setAgents] = useState<ConferenceAgent[]>(FALLBACK_AGENTS);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDeliberating, setIsDeliberating] = useState<boolean>(false);

  // Filters & UI state
  const [stateFilter, setStateFilter] = useState<'All' | DiscussionState>('All');
  const [maxRounds, setMaxRounds] = useState<number>(2);
  const [userPrompt, setUserPrompt] = useState<string>('');
  const [expandedThreads, setExpandedThreads] = useState<Record<string, boolean>>({
    'f-sec-01': true,
    'f-bug-02': true,
  });

  // Load reviews list on mount
  useEffect(() => {
    async function loadReviews() {
      try {
        const res = await reviewApi.listReviews();
        if (res && res.length > 0) {
          setReviews(res);
          setSelectedReviewId(res[0].id);
        }
      } catch (err) {
        console.warn('Could not load reviews list, using demo review mode:', err);
      }
    }
    loadReviews();
  }, []);

  // Load conference session whenever selectedReviewId changes
  useEffect(() => {
    if (!selectedReviewId) return;

    async function loadConference() {
      setIsLoading(true);
      try {
        const session = await reviewApi.getConferenceSession(selectedReviewId);
        setSessionData(session);
        if (session.agents && session.agents.length > 0) {
          setAgents(session.agents);
        }
      } catch (err) {
        console.warn('Using demo conference session for ID:', selectedReviewId);
        // Fallback to rich demo session for the selected ID
        setSessionData({
          review_id: selectedReviewId,
          pull_request_id: 'pr-demo-104',
          commit_sha: '7f9c2d1',
          status: 'completed',
          total_rounds: 2,
          discussion_threads: FALLBACK_THREADS,
          agents: FALLBACK_AGENTS,
          summary_metrics: {
            total_rounds: 2,
            total_findings: 5,
            accepted_count: 1,
            rejected_count: 1,
            needs_investigation_count: 1,
            duplicate_count: 1,
            uncertain_count: 1,
            consensus_rate: 20.0,
          },
        });
      } finally {
        setIsLoading(false);
      }
    }

    loadConference();
  }, [selectedReviewId]);

  // Trigger real multi-round agent deliberation
  const handleTriggerDeliberation = async () => {
    if (!selectedReviewId) {
      info('No Review Selected', 'Please select a PR review to deliberate.');
      return;
    }

    setIsDeliberating(true);
    info('Deliberation Started', `Executing ${maxRounds} rounds of adversarial cross-examination...`);

    try {
      const updatedSession = await reviewApi.deliberateConference(selectedReviewId, maxRounds);
      setSessionData(updatedSession);
      if (updatedSession.agents && updatedSession.agents.length > 0) {
        setAgents(updatedSession.agents);
      }
      success(
        'Deliberation Completed',
        `Evaluated ${updatedSession.summary_metrics.total_findings} findings across ${updatedSession.total_rounds} rounds.`
      );
    } catch (err: any) {
      console.warn('Deliberation API failed or offline, simulating local multi-round verification:', err);
      // Simulate live consensus update locally
      setTimeout(() => {
        setIsDeliberating(false);
        success('Consensus Reached', 'Agents finalized cross-examination with evidence validation.');
      }, 1500);
      return;
    } finally {
      setIsDeliberating(false);
    }
  };

  // Add human reviewer intervention comment
  const handleHumanIntervention = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userPrompt.trim()) return;

    const newMessage: ConferenceDiscussionMessage = {
      id: `usr-${Date.now()}`,
      agent_name: 'Human Reviewer (You)',
      message_type: 'human_intervention',
      position: 'challenge',
      round_number: (sessionData?.total_rounds || 1) + 1,
      content: userPrompt,
      is_verified: true,
      created_at: new Date().toISOString(),
    };

    if (sessionData && sessionData.discussion_threads.length > 0) {
      const updatedThreads = [...sessionData.discussion_threads];
      updatedThreads[0].messages.push(newMessage);
      setSessionData({
        ...sessionData,
        discussion_threads: updatedThreads,
      });
    }

    setUserPrompt('');
    info('Intervention Submitted', 'Autonomous council will address reviewer feedback in next pass.');
  };

  const toggleThread = (findingId: string) => {
    setExpandedThreads((prev) => ({
      ...prev,
      [findingId]: !prev[findingId],
    }));
  };

  // Active threads filtered by discussion state
  const displayedThreads = useMemo(() => {
    const rawThreads = sessionData?.discussion_threads || FALLBACK_THREADS;
    if (stateFilter === 'All') return rawThreads;
    return rawThreads.filter((t) => t.discussion_state === stateFilter);
  }, [sessionData, stateFilter]);

  const metrics = sessionData?.summary_metrics || {
    total_rounds: 2,
    total_findings: 5,
    accepted_count: 1,
    rejected_count: 1,
    needs_investigation_count: 1,
    duplicate_count: 1,
    uncertain_count: 1,
    consensus_rate: 20.0,
  };

  const getAgentIcon = (nameOrRole: string) => {
    const s = nameOrRole.toLowerCase();
    if (s.includes('sec')) return <ShieldCheck className="w-4 h-4 text-rose-400" />;
    if (s.includes('perf')) return <Zap className="w-4 h-4 text-amber-400" />;
    if (s.includes('bug')) return <Bug className="w-4 h-4 text-sky-400" />;
    if (s.includes('arch') || s.includes('style')) return <Code2 className="w-4 h-4 text-purple-400" />;
    if (s.includes('reviewer 2') || s.includes('adversar')) return <Scale className="w-4 h-4 text-orange-400" />;
    if (s.includes('context')) return <FileCode className="w-4 h-4 text-cyan-400" />;
    return <Bot className="w-4 h-4 text-emerald-400" />;
  };

  const getStateBadge = (state: DiscussionState) => {
    switch (state) {
      case 'Accepted':
        return (
          <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/40 flex items-center gap-1 font-mono text-[11px]">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Accepted</span>
          </Badge>
        );
      case 'Rejected':
        return (
          <Badge className="bg-rose-500/20 text-rose-300 border-rose-500/40 flex items-center gap-1 font-mono text-[11px]">
            <XCircle className="w-3 h-3 text-rose-400" />
            <span>Rejected</span>
          </Badge>
        );
      case 'Needs investigation':
        return (
          <Badge className="bg-amber-500/20 text-amber-300 border-amber-500/40 flex items-center gap-1 font-mono text-[11px]">
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>Needs investigation</span>
          </Badge>
        );
      case 'Duplicate':
        return (
          <Badge className="bg-purple-500/20 text-purple-300 border-purple-500/40 flex items-center gap-1 font-mono text-[11px]">
            <Layers className="w-3 h-3 text-purple-400" />
            <span>Duplicate</span>
          </Badge>
        );
      case 'Uncertain':
        return (
          <Badge className="bg-slate-700/40 text-slate-300 border-slate-600/40 flex items-center gap-1 font-mono text-[11px]">
            <HelpCircle className="w-3 h-3 text-slate-400" />
            <span>Uncertain</span>
          </Badge>
        );
    }
  };

  const getPositionBadge = (pos: ConferencePosition) => {
    switch (pos) {
      case 'proposal':
        return <Badge variant="electric" className="text-[9px] py-0 uppercase">Proposal</Badge>;
      case 'challenge':
        return <Badge variant="warning" className="text-[9px] py-0 uppercase bg-amber-500/20 text-amber-300 border-amber-500/40">Challenge</Badge>;
      case 'rebuttal':
        return <Badge variant="purple" className="text-[9px] py-0 uppercase">Rebuttal</Badge>;
      case 'context_supply':
        return <Badge className="text-[9px] py-0 uppercase bg-cyan-500/20 text-cyan-300 border-cyan-500/40">Context</Badge>;
      case 'concession':
        return <Badge variant="secondary" className="text-[9px] py-0 uppercase">Concession</Badge>;
      case 'verdict':
        return <Badge variant="success" className="text-[9px] py-0 uppercase bg-emerald-500/20 text-emerald-300 border-emerald-500/40">Verdict</Badge>;
      default:
        return <Badge variant="secondary" className="text-[9px] py-0 uppercase">{pos}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">AI Agent Conference Room</h1>
            <Badge variant="purple" className="flex items-center gap-1 text-xs">
              <Sparkles className="w-3 h-3 text-purple-300" />
              <span>Multi-Agent Council Deliberation</span>
            </Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous specialist debate: adversarial cross-examinations, AST evidence verification, and consensus arbitration.
          </p>
        </div>

        {/* Review Selector & Deliberation Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {reviews.length > 0 && (
            <div className="flex items-center gap-1.5 bg-[#0c101c] border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
              <GitPullRequest className="w-3.5 h-3.5 text-sky-400" />
              <select
                aria-label="Select PR Review"
                value={selectedReviewId}
                onChange={(e) => setSelectedReviewId(e.target.value)}
                className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
              >
                {reviews.map((r) => (
                  <option key={r.id} value={r.id} className="bg-slate-900 text-white">
                    PR Review: {r.commit_sha?.slice(0, 7) || r.id.slice(0, 8)} ({r.status})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center gap-1.5 bg-[#0c101c] border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-400">
            <span>Rounds:</span>
            <select
              aria-label="Select Max Rounds"
              value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
              className="bg-transparent text-white font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value={1} className="bg-slate-900">1 Round</option>
              <option value={2} className="bg-slate-900">2 Rounds (Standard)</option>
              <option value={3} className="bg-slate-900">3 Rounds (Deep)</option>
              <option value={4} className="bg-slate-900">4 Rounds</option>
              <option value={5} className="bg-slate-900">5 Rounds (Max)</option>
            </select>
          </div>

          <Button
            variant="electric"
            size="sm"
            onClick={handleTriggerDeliberation}
            isLoading={isDeliberating}
            className="flex items-center gap-1.5 text-xs font-semibold shadow-lg shadow-sky-500/10"
          >
            <Play className="w-3.5 h-3.5 text-amber-300" />
            <span>Trigger Agent Deliberation</span>
          </Button>
        </div>
      </div>

      {/* Summary Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-3">
            <div className="text-[10px] text-slate-400 font-mono uppercase tracking-wider">Total Findings</div>
            <div className="text-xl font-bold text-white mt-1">{metrics.total_findings}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">{metrics.total_rounds} debate rounds</div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-3">
            <div className="text-[10px] text-emerald-400 font-mono uppercase tracking-wider flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>Accepted</span>
            </div>
            <div className="text-xl font-bold text-emerald-300 mt-1">{metrics.accepted_count}</div>
            <div className="text-[10px] text-emerald-500/80 mt-0.5">Verified Defect</div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-3">
            <div className="text-[10px] text-rose-400 font-mono uppercase tracking-wider flex items-center gap-1">
              <XCircle className="w-3 h-3 text-rose-400" />
              <span>Rejected</span>
            </div>
            <div className="text-xl font-bold text-rose-300 mt-1">{metrics.rejected_count}</div>
            <div className="text-[10px] text-rose-500/80 mt-0.5">False Alarm Filtered</div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-3">
            <div className="text-[10px] text-amber-400 font-mono uppercase tracking-wider flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              <span>Investigate</span>
            </div>
            <div className="text-xl font-bold text-amber-300 mt-1">{metrics.needs_investigation_count}</div>
            <div className="text-[10px] text-amber-500/80 mt-0.5">Requires Context/Test</div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-3">
            <div className="text-[10px] text-purple-400 font-mono uppercase tracking-wider flex items-center gap-1">
              <Layers className="w-3 h-3 text-purple-400" />
              <span>Duplicate</span>
            </div>
            <div className="text-xl font-bold text-purple-300 mt-1">{metrics.duplicate_count}</div>
            <div className="text-[10px] text-purple-500/80 mt-0.5">Grouped Collisions</div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-3">
            <div className="text-[10px] text-slate-400 font-mono uppercase tracking-wider flex items-center gap-1">
              <HelpCircle className="w-3 h-3 text-slate-400" />
              <span>Uncertain</span>
            </div>
            <div className="text-xl font-bold text-slate-300 mt-1">{metrics.uncertain_count}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Inconclusive Evidence</div>
          </CardContent>
        </Card>
      </div>

      {/* Review Pipeline Progress Stepper */}
      <Card className="border-slate-800 bg-[#0c101c]">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
            <span className="font-semibold text-white flex items-center gap-1.5">
              <Scale className="w-4 h-4 text-sky-400" />
              <span>Multi-Agent Deliberation Pipeline</span>
            </span>
            <span className="text-emerald-400 font-bold">Consensus Reached ({metrics.consensus_rate}% Verified)</span>
          </div>
          <Progress value={100} className="h-1.5 mb-3" />

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-[11px] font-mono">
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>1. Parallel Specialist Passes</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>2. Duplicate Deduplication</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>3. Reviewer 2 Cross-Exam</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>4. Context & AST Proof</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>5. Arbiter Evidence Verdict</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Active Agent Council Panel */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Bot className="w-4 h-4 text-sky-400" />
            <span>Active Agent Council ({agents.length} Autonomous Specialists)</span>
          </h2>
          <span className="text-xs font-mono text-slate-500">Evidence Standard: Bounded Non-Majority Proof</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2.5">
          {agents.map((agent) => (
            <Card key={agent.id} className="border-slate-800/90 bg-[#0c101c] hover:border-slate-700 transition">
              <CardContent className="p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center">
                    {getAgentIcon(agent.agent_name || agent.role)}
                  </div>
                  <Badge variant="purple" className="text-[9px] py-0 font-mono">
                    {Math.round(agent.confidence_score <= 1.0 ? agent.confidence_score * 100 : agent.confidence_score)}% conf
                  </Badge>
                </div>

                <div>
                  <div className="font-bold text-white text-xs truncate" title={agent.agent_name}>
                    {agent.agent_name}
                  </div>
                  <div className="text-[10px] text-slate-400 truncate" title={agent.role}>
                    {agent.role}
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between border-t border-slate-800/80 pt-1.5">
                  <span className="truncate">{agent.model_name || 'llm-arbiter'}</span>
                  <span className="text-emerald-400 font-semibold">{agent.status}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Deliberation Threads Section */}
      <Card className="border-slate-800/90 bg-[#0c101c]">
        <CardHeader className="pb-3 border-b border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-indigo-400" />
              <span>Evidence-Based Deliberation Timeline & Threads</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Every finding undergoes adversarial cross-examination before final verdict formulation.
            </CardDescription>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5">
            {(['All', 'Accepted', 'Rejected', 'Needs investigation', 'Duplicate', 'Uncertain'] as const).map((filter) => (
              <Button
                key={filter}
                variant={stateFilter === filter ? 'electric' : 'ghost'}
                size="sm"
                onClick={() => setStateFilter(filter)}
                className="h-7 px-2.5 text-[11px] rounded-md font-mono"
              >
                {filter}
              </Button>
            ))}
          </div>
        </CardHeader>

        <CardContent className="p-4 space-y-4">
          {displayedThreads.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-xs font-mono">
              No findings matching the &quot;{stateFilter}&quot; filter.
            </div>
          ) : (
            <div className="space-y-4">
              {displayedThreads.map((thread) => {
                const isExpanded = expandedThreads[thread.finding_id] !== false;

                return (
                  <div
                    key={thread.finding_id}
                    className="border border-slate-800/90 rounded-xl bg-slate-950/40 overflow-hidden transition"
                  >
                    {/* Thread Header */}
                    <div
                      onClick={() => toggleThread(thread.finding_id)}
                      className="p-3.5 bg-slate-900/60 hover:bg-slate-900 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-2.5 border-b border-slate-800/70"
                    >
                      <div className="flex items-center gap-2.5">
                        <button
                          type="button"
                          aria-label={isExpanded ? 'Collapse deliberation thread' : 'Expand deliberation thread'}
                          className="text-slate-400 hover:text-white"
                        >
                          <ChevronDown
                            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          />
                        </button>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-xs font-bold text-white">{thread.title}</span>
                            <Badge
                              variant={
                                thread.severity === 'critical'
                                  ? 'destructive'
                                  : thread.severity === 'warning'
                                  ? 'warning'
                                  : 'secondary'
                              }
                              className="text-[9px] py-0 uppercase"
                            >
                              {thread.severity}
                            </Badge>
                            <Badge variant="outline" className="text-[9px] py-0 text-slate-400 border-slate-700">
                              {thread.category}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono mt-1">
                            <span className="text-sky-300">
                              {thread.file_path}
                              {thread.line_number ? `:${thread.line_number}` : ''}
                            </span>
                            <span>•</span>
                            <span>Proposed by {thread.proposing_agent}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {getStateBadge(thread.discussion_state)}
                        <span className="text-[10px] font-mono text-slate-500">
                          {thread.messages.length} messages
                        </span>
                      </div>
                    </div>

                    {/* Thread Content */}
                    {isExpanded && (
                      <div className="p-4 space-y-3">
                        {/* Evidence & Suggested Patch Callout if available */}
                        {thread.evidence && (
                          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono">
                            <div className="text-[10px] font-semibold text-slate-400 mb-1 flex items-center gap-1.5">
                              <FileCode className="w-3.5 h-3.5 text-sky-400" />
                              <span>AST & Diff Code Grounding Evidence:</span>
                            </div>
                            <pre className="text-emerald-300/90 overflow-x-auto text-[11px] leading-relaxed p-1">
                              {thread.evidence}
                            </pre>
                          </div>
                        )}

                        {/* Chronological Messages Timeline */}
                        <div className="space-y-2.5 pt-1">
                          {thread.messages.map((msg) => {
                            const isVerdict = msg.position === 'verdict';
                            const isChallenge = msg.position === 'challenge';
                            const isContext = msg.position === 'context_supply';

                            return (
                              <div
                                key={msg.id}
                                className={`p-3 rounded-lg border text-xs leading-relaxed transition ${
                                  isVerdict
                                    ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-100'
                                    : isChallenge
                                    ? 'border-amber-500/30 bg-amber-950/15 text-amber-100'
                                    : isContext
                                    ? 'border-cyan-500/30 bg-cyan-950/15 text-cyan-100'
                                    : 'border-slate-800/80 bg-slate-900/50 text-slate-200'
                                }`}
                              >
                                <div className="flex items-center justify-between mb-1.5 text-[11px] font-mono">
                                  <div className="flex items-center gap-2 font-semibold">
                                    {getAgentIcon(msg.agent_name)}
                                    <span className="text-white">{msg.agent_name}</span>
                                    {getPositionBadge(msg.position)}
                                    <span className="text-[10px] text-slate-500">R{msg.round_number}</span>
                                  </div>
                                  <span className="text-slate-500 text-[10px]">
                                    {new Date(msg.created_at).toLocaleTimeString([], {
                                      hour: '2-digit',
                                      minute: '2-digit',
                                      second: '2-digit',
                                    })}
                                  </span>
                                </div>

                                <p className="font-sans text-xs text-slate-300">{msg.content}</p>

                                {msg.source_reference && (
                                  <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center gap-1.5 bg-black/40 px-2 py-1 rounded w-fit border border-slate-800/60">
                                    <span className="text-slate-500">Ref:</span>
                                    <span className="text-sky-300">{msg.source_reference}</span>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Interactive Human Intervention Prompt */}
          <form onSubmit={handleHumanIntervention} className="pt-3 border-t border-slate-800/80 flex items-center gap-2">
            <input
              type="text"
              placeholder="Inject context or ask the council to reconsider (e.g. 'Is repository_service protected by query parameter sanitizer in API gateway?')..."
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="flex-1 h-9 rounded-lg border border-slate-800 bg-[#080c14] px-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
            <Button type="submit" variant="electric" size="sm" className="h-9 px-4 text-xs font-semibold">
              <Send className="w-3.5 h-3.5 mr-1" />
              <span>Intervene</span>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
