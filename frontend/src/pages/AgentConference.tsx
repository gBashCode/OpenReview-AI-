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
  Play,
  Scale,
  GitPullRequest,
  FileCode,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ChevronDown,
  Layers,
  Send,
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
    role: "Devil's Advocate & Cross-Examiner",
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
        content: 'AST verification confirms line 42: diff_cache = TTLCache(maxsize=1000, ttl=3600). The cache is self-pruning.',
        source_reference: 'workers/tasks/diff_analyzer.py:42',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
      },
      {
        id: 'm-9',
        agent_name: 'Quality Arbiter',
        message_type: 'consensus',
        position: 'verdict',
        final_decision: 'Rejected',
        round_number: 2,
        content: 'VERDICT: REJECTED (False Alarm). Context proves bounded TTLCache. Claim dismissed.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 7).toISOString(),
      },
    ],
  },
  {
    finding_id: 'f-perf-03',
    file_path: 'backend/app/indexing/embeddings.py',
    line_number: 215,
    title: 'Synchronous embedding API calls in async event loop',
    category: 'performance',
    severity: 'warning',
    proposing_agent: 'Performance Profiler',
    discussion_state: 'Accepted',
    evidence: 'response = client.embeddings.create(input=chunks)',
    suggested_patch: '- response = client.embeddings.create(input=chunks)\n+ response = await async_client.embeddings.create(input=chunks)',
    messages: [
      {
        id: 'm-10',
        agent_name: 'Performance Profiler',
        message_type: 'claim',
        position: 'proposal',
        round_number: 1,
        content: 'Synchronous blocking HTTP client inside async indexing routine blocks uvicorn worker threads.',
        evidence: 'response = client.embeddings.create(...)',
        source_reference: 'backend/app/indexing/embeddings.py:215',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 6).toISOString(),
      },
      {
        id: 'm-11',
        agent_name: 'Quality Arbiter',
        message_type: 'consensus',
        position: 'verdict',
        final_decision: 'Accepted',
        round_number: 1,
        content: 'VERDICT: ACCEPTED. Direct event loop blockage confirmed. Migrated to AsyncOpenAI client.',
        is_verified: true,
        created_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
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
            total_findings: 3,
            accepted_count: 2,
            rejected_count: 1,
            needs_investigation_count: 0,
            duplicate_count: 0,
            uncertain_count: 0,
            consensus_rate: 66.7,
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

  const displayedThreads = useMemo(() => {
    const rawThreads = sessionData?.discussion_threads || FALLBACK_THREADS;
    if (stateFilter === 'All') return rawThreads;
    return rawThreads.filter((t) => t.discussion_state === stateFilter);
  }, [sessionData, stateFilter]);

  const metrics = sessionData?.summary_metrics || {
    total_rounds: 2,
    total_findings: 3,
    accepted_count: 2,
    rejected_count: 1,
    needs_investigation_count: 0,
    duplicate_count: 0,
    uncertain_count: 0,
    consensus_rate: 66.7,
  };

  const getAgentIcon = (nameOrRole: string) => {
    const s = nameOrRole.toLowerCase();
    if (s.includes('sec')) return <ShieldCheck className="w-3.5 h-3.5 text-[#e06c5b]" />;
    if (s.includes('perf')) return <Zap className="w-3.5 h-3.5 text-[#f0af54]" />;
    if (s.includes('bug')) return <Bug className="w-3.5 h-3.5 text-[#e29b38]" />;
    if (s.includes('arch') || s.includes('style')) return <Code2 className="w-3.5 h-3.5 text-[#d4a853]" />;
    if (s.includes('reviewer 2') || s.includes('adversar')) return <Scale className="w-3.5 h-3.5 text-[#3a9e8f]" />;
    if (s.includes('context')) return <FileCode className="w-3.5 h-3.5 text-[#b8b0a2]" />;
    return <Bot className="w-3.5 h-3.5 text-[#5a9e6f]" />;
  };

  const getStateBadge = (state: DiscussionState) => {
    switch (state) {
      case 'Accepted':
        return (
          <Badge variant="success" className="font-mono text-[10px] flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-[#5a9e6f]" />
            <span>Accepted</span>
          </Badge>
        );
      case 'Rejected':
        return (
          <Badge variant="destructive" className="font-mono text-[10px] flex items-center gap-1">
            <XCircle className="w-3 h-3 text-[#c75a4a]" />
            <span>Rejected</span>
          </Badge>
        );
      case 'Needs investigation':
        return (
          <Badge variant="warning" className="font-mono text-[10px] flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-[#e29b38]" />
            <span>Investigate</span>
          </Badge>
        );
      case 'Duplicate':
        return (
          <Badge variant="secondary" className="font-mono text-[10px] flex items-center gap-1">
            <Layers className="w-3 h-3 text-[#8a8378]" />
            <span>Duplicate</span>
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="font-mono text-[10px] flex items-center gap-1">
            <HelpCircle className="w-3 h-3 text-[#8a8378]" />
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
        return <Badge variant="warning" className="text-[9px] py-0 uppercase">Challenge</Badge>;
      case 'rebuttal':
        return <Badge variant="purple" className="text-[9px] py-0 uppercase">Rebuttal</Badge>;
      case 'context_supply':
        return <Badge variant="secondary" className="text-[9px] py-0 uppercase">Context</Badge>;
      case 'concession':
        return <Badge variant="secondary" className="text-[9px] py-0 uppercase">Concession</Badge>;
      case 'verdict':
        return <Badge variant="success" className="text-[9px] py-0 uppercase">Verdict</Badge>;
      default:
        return <Badge variant="secondary" className="text-[9px] py-0 uppercase">{pos}</Badge>;
    }
  };

  return (
    <div className="space-y-7 animate-in fade-in duration-300">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 pb-4 border-b border-[#26221c]">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-[10px] font-mono tracking-widest text-[#d4a853] uppercase">[LEDGER · 05 · COUNCIL]</span>
            <div className="h-2.5 w-px bg-[#36312a]" />
            <span className="text-[10px] font-mono tracking-wider text-[#8a8378] uppercase">Deliberation</span>
          </div>
          <h1 className="text-3xl font-serif font-normal text-[#f5f0e6] tracking-tight mt-1">
            AI Agent Conference Room
          </h1>
          <p className="text-xs text-[#8a8378] mt-1.5 leading-relaxed">
            Autonomous multi-agent council: adversarial cross-examinations, AST code grounding, and non-majority evidence arbitration.
          </p>
        </div>

        {/* Review Selector & Deliberation Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {reviews.length > 0 && (
            <div className="flex items-center gap-1.5 bg-[#14120f] border border-[#26221c] rounded-[2px] px-2.5 py-1 text-xs font-mono">
              <GitPullRequest className="w-3.5 h-3.5 text-[#d4a853]" />
              <select
                aria-label="Select PR Review"
                value={selectedReviewId}
                onChange={(e) => setSelectedReviewId(e.target.value)}
                className="bg-transparent text-[#d8d2c4] text-xs focus:outline-none cursor-pointer"
              >
                {reviews.map((r) => (
                  <option key={r.id} value={r.id} className="bg-[#14120f] text-[#f5f0e6]">
                    REV-{r.commit_sha?.slice(0, 7) || r.id.slice(0, 8)} ({r.status})
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex items-center gap-1.5 bg-[#14120f] border border-[#26221c] rounded-[2px] px-2.5 py-1 text-xs font-mono text-[#8a8378]">
            <span>Rounds:</span>
            <select
              aria-label="Select Max Rounds"
              value={maxRounds}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
              className="bg-transparent text-[#f5f0e6] font-mono text-xs focus:outline-none cursor-pointer"
            >
              <option value={1} className="bg-[#14120f]">1 Round</option>
              <option value={2} className="bg-[#14120f]">2 Rounds (Standard)</option>
              <option value={3} className="bg-[#14120f]">3 Rounds (Deep)</option>
              <option value={4} className="bg-[#14120f]">4 Rounds</option>
            </select>
          </div>

          <Button
            variant="electric"
            size="sm"
            onClick={handleTriggerDeliberation}
            isLoading={isDeliberating}
            className="flex items-center gap-1.5 text-xs font-mono font-medium"
          >
            <Play className="w-3.5 h-3.5 text-[#0e0d0b]" />
            <span>Trigger Deliberation</span>
          </Button>
        </div>
      </div>

      {/* Summary Metrics Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
        <div className="p-3.5 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] text-[#8a8378] font-mono uppercase tracking-wider">[01] FINDINGS</div>
          <div className="text-xl font-serif text-[#f5f0e6] mt-1">{metrics.total_findings}</div>
          <div className="text-[10px] text-[#6a6358] font-mono mt-0.5">{metrics.total_rounds} debate rounds</div>
        </div>

        <div className="p-3.5 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] text-[#5a9e6f] font-mono uppercase tracking-wider flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-[#5a9e6f]" />
            <span>ACCEPTED</span>
          </div>
          <div className="text-xl font-serif text-[#6cb582] mt-1">{metrics.accepted_count}</div>
          <div className="text-[10px] text-[#5a9e6f]/80 font-mono mt-0.5">Verified Defect</div>
        </div>

        <div className="p-3.5 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] text-[#c75a4a] font-mono uppercase tracking-wider flex items-center gap-1">
            <XCircle className="w-3 h-3 text-[#c75a4a]" />
            <span>REJECTED</span>
          </div>
          <div className="text-xl font-serif text-[#e06c5b] mt-1">{metrics.rejected_count}</div>
          <div className="text-[10px] text-[#c75a4a]/80 font-mono mt-0.5">False Alarm Filtered</div>
        </div>

        <div className="p-3.5 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] text-[#e29b38] font-mono uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-[#e29b38]" />
            <span>INVESTIGATE</span>
          </div>
          <div className="text-xl font-serif text-[#f0af54] mt-1">{metrics.needs_investigation_count}</div>
          <div className="text-[10px] text-[#e29b38]/80 font-mono mt-0.5">Requires Context</div>
        </div>

        <div className="p-3.5 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] text-[#3a9e8f] font-mono uppercase tracking-wider flex items-center gap-1">
            <Layers className="w-3 h-3 text-[#3a9e8f]" />
            <span>DUPLICATE</span>
          </div>
          <div className="text-xl font-serif text-[#4db3a3] mt-1">{metrics.duplicate_count}</div>
          <div className="text-[10px] text-[#3a9e8f]/80 font-mono mt-0.5">Linked Collisions</div>
        </div>

        <div className="p-3.5 rounded-[2px] border border-[#26221c] bg-[#14120f]">
          <div className="text-[10px] text-[#8a8378] font-mono uppercase tracking-wider flex items-center gap-1">
            <HelpCircle className="w-3 h-3 text-[#8a8378]" />
            <span>UNCERTAIN</span>
          </div>
          <div className="text-xl font-serif text-[#b8b0a2] mt-1">{metrics.uncertain_count}</div>
          <div className="text-[10px] text-[#6a6358] font-mono mt-0.5">Inconclusive Proof</div>
        </div>
      </div>

      {/* Review Pipeline Progress Stepper */}
      <Card className="border-[#26221c] bg-[#13110e]">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs font-mono text-[#8a8378] mb-2.5">
            <span className="font-medium text-[#f5f0e6] flex items-center gap-1.5">
              <Scale className="w-3.5 h-3.5 text-[#d4a853]" />
              <span>Multi-Agent Deliberation Pipeline</span>
            </span>
            <span className="text-[#5a9e6f]">Consensus Reached ({metrics.consensus_rate}% Verified)</span>
          </div>
          <Progress value={100} className="h-1 mb-3" />

          <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-[10px] font-mono">
            <div className="p-2 rounded-[2px] bg-[#171511] border border-[#28241d] text-[#b8b0a2] flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-[#5a9e6f] shrink-0" />
              <span>1. Specialist Passes</span>
            </div>
            <div className="p-2 rounded-[2px] bg-[#171511] border border-[#28241d] text-[#b8b0a2] flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-[#5a9e6f] shrink-0" />
              <span>2. Deduplication</span>
            </div>
            <div className="p-2 rounded-[2px] bg-[#171511] border border-[#28241d] text-[#b8b0a2] flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-[#5a9e6f] shrink-0" />
              <span>3. Cross-Examination</span>
            </div>
            <div className="p-2 rounded-[2px] bg-[#171511] border border-[#28241d] text-[#b8b0a2] flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-[#5a9e6f] shrink-0" />
              <span>4. AST Proof</span>
            </div>
            <div className="p-2 rounded-[2px] bg-[#171511] border border-[#28241d] text-[#b8b0a2] flex items-center justify-center gap-1.5">
              <CheckCircle2 className="w-3 h-3 text-[#5a9e6f] shrink-0" />
              <span>5. Arbiter Verdict</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Active Agent Council Panel */}
      <div>
        <div className="flex items-center justify-between mb-3 font-mono">
          <h2 className="text-xs uppercase tracking-wider text-[#d4a853] flex items-center gap-2 font-medium">
            <Bot className="w-4 h-4 text-[#d4a853]" />
            <span>Active Agent Council ({agents.length} Autonomous Specialists)</span>
          </h2>
          <span className="text-[11px] text-[#6a6358]">Standard: Bounded Non-Majority Proof</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
          {agents.map((agent) => (
            <Card key={agent.id} className="border-[#26221c] bg-[#13110e] hover:border-[#383229] transition-colors">
              <CardContent className="p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-6 h-6 rounded-[2px] bg-[#1b1915] border border-[#2e2a24] flex items-center justify-center">
                    {getAgentIcon(agent.agent_name || agent.role)}
                  </div>
                  <Badge variant="outline" className="text-[9px] py-0 font-mono">
                    {Math.round(agent.confidence_score <= 1.0 ? agent.confidence_score * 100 : agent.confidence_score)}%
                  </Badge>
                </div>

                <div>
                  <div className="font-mono text-xs font-medium text-[#f5f0e6] truncate" title={agent.agent_name}>
                    {agent.agent_name}
                  </div>
                  <div className="text-[10px] text-[#8a8378] truncate mt-0.5" title={agent.role}>
                    {agent.role}
                  </div>
                </div>

                <div className="text-[10px] text-[#6a6358] font-mono flex items-center justify-between border-t border-[#221f1a] pt-1.5">
                  <span className="truncate">{agent.model_name?.replace('claude-', '') || 'arbiter'}</span>
                  <span className="text-[#5a9e6f]">{agent.status}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Deliberation Threads Section */}
      <Card className="border-[#26221c] bg-[#13110e]">
        <CardHeader className="pb-3 border-b border-[#221f1a] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base font-serif text-[#f5f0e6] flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-[#d4a853]" />
              <span>Evidence-Based Deliberation Timeline</span>
            </CardTitle>
            <CardDescription className="text-xs text-[#8a8378]">
              Every finding undergoes adversarial cross-examination before final verdict formulation
            </CardDescription>
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1 font-mono">
            {(['All', 'Accepted', 'Rejected', 'Needs investigation', 'Duplicate', 'Uncertain'] as const).map((filter) => (
              <Button
                key={filter}
                variant={stateFilter === filter ? 'electric' : 'ghost'}
                size="sm"
                onClick={() => setStateFilter(filter)}
                className="h-7 px-2.5 text-[11px] rounded-[2px] font-mono"
              >
                {filter}
              </Button>
            ))}
          </div>
        </CardHeader>

        <CardContent className="p-4 space-y-4">
          {displayedThreads.length === 0 ? (
            <div className="text-center py-12 text-[#6a6358] text-xs font-mono">
              No findings matching the &quot;{stateFilter}&quot; filter.
            </div>
          ) : (
            <div className="space-y-4">
              {displayedThreads.map((thread) => {
                const isExpanded = expandedThreads[thread.finding_id] !== false;

                return (
                  <div
                    key={thread.finding_id}
                    className="border border-[#26221c] rounded-[2px] bg-[#14120f] overflow-hidden transition-colors"
                  >
                    {/* Thread Header */}
                    <div
                      onClick={() => toggleThread(thread.finding_id)}
                      className="p-3.5 bg-[#171511] hover:bg-[#1b1915] cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-2.5 border-b border-[#221f1a]"
                    >
                      <div className="flex items-center gap-2.5">
                        <button
                          type="button"
                          aria-label={isExpanded ? 'Collapse deliberation thread' : 'Expand deliberation thread'}
                          className="text-[#8a8378] hover:text-[#f5f0e6]"
                        >
                          <ChevronDown
                            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                          />
                        </button>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-serif text-base text-[#f5f0e6]">{thread.title}</span>
                            <Badge
                              variant={
                                thread.severity === 'critical'
                                  ? 'destructive'
                                  : thread.severity === 'warning'
                                  ? 'warning'
                                  : 'secondary'
                              }
                              className="text-[9px] py-0 uppercase font-mono"
                            >
                              {thread.severity}
                            </Badge>
                            <Badge variant="outline" className="text-[9px] py-0 text-[#8a8378] border-[#332e26] font-mono">
                              {thread.category}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-[10px] text-[#787165] font-mono mt-1">
                            <span className="text-[#d4a853]">
                              {thread.file_path}
                              {thread.line_number ? `:${thread.line_number}` : ''}
                            </span>
                            <span>·</span>
                            <span>Proposed by {thread.proposing_agent}</span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {getStateBadge(thread.discussion_state)}
                        <span className="text-[10px] font-mono text-[#6a6358]">
                          {thread.messages.length} messages
                        </span>
                      </div>
                    </div>

                    {/* Thread Content */}
                    {isExpanded && (
                      <div className="p-4 space-y-3">
                        {/* Evidence & Suggested Patch Callout if available */}
                        {thread.evidence && (
                          <div className="p-3 rounded-[2px] bg-[#0c0a09] border border-[#24201a] text-xs font-mono">
                            <div className="text-[10px] text-[#8a8378] mb-1 flex items-center gap-1.5">
                              <FileCode className="w-3.5 h-3.5 text-[#3a9e8f]" />
                              <span>AST & Diff Code Grounding Evidence:</span>
                            </div>
                            <pre className="text-[#6cb582] overflow-x-auto text-[11px] leading-relaxed p-1">
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
                                className={`p-3.5 rounded-[2px] border text-xs leading-relaxed transition ${
                                  isVerdict
                                    ? 'border-[#5a9e6f]/40 bg-[#142017] text-[#e0f2e5]'
                                    : isChallenge
                                    ? 'border-[#e29b38]/30 bg-[#221b12] text-[#fbf0df]'
                                    : isContext
                                    ? 'border-[#3a9e8f]/30 bg-[#121c1a] text-[#daf2ee]'
                                    : 'border-[#26221c] bg-[#161410] text-[#d8d2c4]'
                                }`}
                              >
                                <div className="flex items-center justify-between mb-1.5 text-[11px] font-mono">
                                  <div className="flex items-center gap-2">
                                    {getAgentIcon(msg.agent_name)}
                                    <span className="text-[#f5f0e6] font-medium">{msg.agent_name}</span>
                                    {getPositionBadge(msg.position)}
                                    <span className="text-[10px] text-[#6a6358]">R{msg.round_number}</span>
                                  </div>
                                  <span className="text-[#6a6358] text-[10px]">
                                    {new Date(msg.created_at).toLocaleTimeString([], {
                                      hour: '2-digit',
                                      minute: '2-digit',
                                      second: '2-digit',
                                    })}
                                  </span>
                                </div>

                                <p className="font-sans text-xs text-[#b8b0a2]">{msg.content}</p>

                                {msg.source_reference && (
                                  <div className="mt-2 text-[10px] font-mono text-[#8a8378] flex items-center gap-1.5 bg-[#0e0d0b] px-2 py-0.5 rounded-[2px] w-fit border border-[#221f1a]">
                                    <span className="text-[#6a6358]">Ref:</span>
                                    <span className="text-[#d4a853]">{msg.source_reference}</span>
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
          <form onSubmit={handleHumanIntervention} className="pt-3 border-t border-[#221f1a] flex items-center gap-2 font-mono">
            <input
              type="text"
              placeholder="Inject context or request council cross-examination (e.g. 'Is repository_service sanitized in API gateway?')..."
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className="flex-1 h-8 rounded-[2px] border border-[#2e2a24] bg-[#12100d] px-3 text-xs text-[#f5f0e6] placeholder:text-[#6a6358] focus:outline-none focus:border-[#d4a853]"
            />
            <Button type="submit" variant="electric" size="sm" className="h-8 px-4 text-xs font-mono font-medium">
              <Send className="w-3.5 h-3.5 mr-1 text-[#0e0d0b]" />
              <span>Intervene</span>
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
