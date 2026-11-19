import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  ShieldCheck,
  Zap,
  Bot,
  GitPullRequest,
  ArrowRight,
  Code2,
  Terminal,
  CheckCircle2,
  Lock,
  Sparkles,
  GitFork,
  Cpu,
} from 'lucide-react';

export const Landing: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'security' | 'perf' | 'fix'>('security');

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 selection:bg-sky-500/30">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 px-8 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg text-white tracking-tight">OpenReview AI</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-sky-500/20 text-sky-400 border border-sky-500/30">
            v0.1
          </span>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/login">
            <Button variant="ghost">Sign In</Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="electric" className="flex items-center gap-1.5">
              <span>Open Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 pt-20 pb-16 max-w-5xl mx-auto text-center space-y-6">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-sky-500/30 bg-sky-500/10 text-sky-400 text-xs font-mono font-medium">
          <Sparkles className="w-3.5 h-3.5 text-amber-300" />
          <span>Autonomous Multi-Agent Code Review Platform</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-[1.1]">
          Code Reviews That Think Like <br />
          <span className="bg-gradient-to-r from-sky-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
            Senior Staff Engineers
          </span>
        </h1>

        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          OpenReview AI connects with GitHub to understand repository semantics, orchestrates specialized agents across Security, Performance, and Bugs, eliminates false alarms via Arbiter consensus, and outputs verified pull request fixes.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          <Link to="/dashboard">
            <Button size="lg" variant="electric" className="flex items-center gap-2 h-11 px-6 text-sm">
              <GitFork className="w-4 h-4" />
              <span>Connect GitHub Repository</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
          <Link to="/login">
            <Button size="lg" variant="outline" className="h-11 px-6 text-sm flex items-center gap-2">
              <Terminal className="w-4 h-4 text-slate-400" />
              <span>Try Interactive Sandbox</span>
            </Button>
          </Link>
        </div>

        {/* Feature Badges */}
        <div className="flex flex-wrap items-center justify-center gap-6 pt-6 text-xs text-slate-400 font-mono">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Zero Data Training Retention
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Provider-Independent (OpenAI, Claude, Gemini, Ollama)
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            LangGraph Multi-Agent Arbiter
          </span>
        </div>
      </section>

      {/* Interactive Live Review Preview */}
      <section className="px-6 py-12 max-w-5xl mx-auto">
        <div className="rounded-2xl border border-slate-800 bg-[#0d121f] p-6 shadow-2xl shadow-black/80">
          <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500/80" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs font-mono text-slate-400 ml-2">
                PR #42 — Automated Multi-Agent Findings
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('security')}
                className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                  activeTab === 'security' ? 'bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/30' : 'text-slate-400 hover:text-white'
                }`}
              >
                Security Agent
              </button>
              <button
                onClick={() => setActiveTab('perf')}
                className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                  activeTab === 'perf' ? 'bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/30' : 'text-slate-400 hover:text-white'
                }`}
              >
                Performance Agent
              </button>
              <button
                onClick={() => setActiveTab('fix')}
                className={`px-2.5 py-1 rounded text-xs font-mono transition ${
                  activeTab === 'fix' ? 'bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30' : 'text-slate-400 hover:text-white'
                }`}
              >
                AutoFix Patch
              </button>
            </div>
          </div>

          {activeTab === 'security' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 space-y-2">
                <div className="text-rose-400 font-semibold flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  <span>CWE-89: SQL Injection Vector</span>
                </div>
                <p className="text-slate-400 text-[11px] font-sans leading-relaxed">
                  Raw string interpolation inside database query allows arbitrary statement execution.
                </p>
                <div className="p-2.5 rounded bg-rose-950/20 border border-rose-900/40 text-rose-300">
                  - await db.execute(f&quot;SELECT * FROM repos WHERE name = '{'{user_input}'}'&quot;)
                </div>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-300 space-y-2">
                <div className="text-emerald-400 font-semibold flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Arbiter Validated Remediation</span>
                </div>
                <p className="text-slate-400 text-[11px] font-sans leading-relaxed">
                  Parameterized SQLAlchemy 2.0 select statement with bound parameter serialization.
                </p>
                <div className="p-2.5 rounded bg-emerald-950/20 border border-emerald-900/40 text-emerald-300">
                  + await db.execute(select(Repo).where(Repo.name == user_input))
                </div>
              </div>
            </div>
          )}

          {activeTab === 'perf' && (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-2">
              <div className="text-amber-400 font-semibold flex items-center gap-1.5">
                <Zap className="w-4 h-4" />
                <span>N+1 Query Regression: Review Comment Eager Loading</span>
              </div>
              <p className="text-slate-400 text-[11px] font-sans leading-relaxed">
                Sequential ORM traversal generates 40+ roundtrips. Converted to a single query via <code className="text-sky-300">selectinload()</code>, reducing API latency from 380ms to 12ms.
              </p>
            </div>
          )}

          {activeTab === 'fix' && (
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-2 text-emerald-400">
              <div className="text-[11px] text-slate-400 font-sans">
                AutoFix proposal generated and validated against local test suite (4/4 tests passed).
              </div>
              <pre className="text-slate-300 whitespace-pre-wrap leading-relaxed">
{`git apply << 'EOF'
--- a/backend/app/repositories/review_repo.py
+++ b/backend/app/repositories/review_repo.py
@@ -32,3 +32,3 @@
- return await session.execute(select(Review).where(Review.id == review_id))
+ return await session.execute(select(Review).options(selectinload(Review.comments)).where(Review.id == review_id))
EOF`}
              </pre>
            </div>
          )}
        </div>
      </section>

      {/* Multi-Agent Architecture Pillars */}
      <section className="px-6 py-16 max-w-5xl mx-auto">
        <h2 className="text-2xl font-bold text-white text-center mb-10 tracking-tight">
          How OpenReview AI Multi-Agent Consensus Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-xl border border-slate-800 bg-[#0c101c] space-y-2">
            <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-400 flex items-center justify-center font-mono font-bold text-sm">
              01
            </div>
            <h3 className="font-semibold text-white text-sm">AST Diff Extraction</h3>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Parses unified git diffs, extracts modified syntax trees, and queries pgvector for codebase context.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-[#0c101c] space-y-2">
            <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center font-mono font-bold text-sm">
              02
            </div>
            <h3 className="font-semibold text-white text-sm">Parallel Agent Passes</h3>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Specialized agents evaluate OWASP security, algorithmic efficiency, bug risks, and clean coding rules.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-[#0c101c] space-y-2">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center font-mono font-bold text-sm">
              03
            </div>
            <h3 className="font-semibold text-white text-sm">Arbiter Debate</h3>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Agents cross-examine findings, filter out noise and false positives, and reach majority consensus.
            </p>
          </div>

          <div className="p-5 rounded-xl border border-slate-800 bg-[#0c101c] space-y-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-mono font-bold text-sm">
              04
            </div>
            <h3 className="font-semibold text-white text-sm">AutoFix & Publish</h3>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Generates unified diff patches, executes sandbox test checks, and posts verified comments to GitHub.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 px-8 py-8 text-center text-xs text-slate-500 font-mono">
        OpenReview AI • Autonomous Multi-Agent Code Review Platform
      </footer>
    </div>
  );
};
