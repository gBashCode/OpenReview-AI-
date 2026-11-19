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
  Terminal,
  CheckCircle2,
  Sparkles,
  GitFork,
  Cpu,
} from 'lucide-react';

export const Landing: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'security' | 'perf' | 'fix'>('security');

  return (
    <div className="min-h-screen bg-transparent text-[#d8d2c4] selection:bg-[#d4a853]/25 selection:text-[#f5f0e6]">
      {/* Top Editorial Navigation */}
      <header className="border-b border-[#26221c] px-6 lg:px-12 py-4 flex items-center justify-between max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-[2px] bg-[#1a1814] border border-[#d4a853]/40 flex items-center justify-center">
            <span className="font-serif italic text-base text-[#d4a853] font-bold">O</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-serif text-xl text-[#f5f0e6] tracking-tight">OpenReview</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-[2px] font-mono tracking-widest bg-[#221f1a] text-[#d4a853] border border-[#38332a]">
              AI · 0.1
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3.5">
          <Link to="/login">
            <Button variant="ghost" className="font-mono text-xs text-[#8a8378] hover:text-[#f5f0e6]">Sign In</Button>
          </Link>
          <Link to="/dashboard">
            <Button variant="electric" className="flex items-center gap-1.5 font-mono text-xs font-semibold">
              <span>Open Dashboard</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#0e0d0b]" />
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="px-6 pt-24 pb-16 max-w-4xl mx-auto text-center space-y-7">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-[2px] border border-[#3d372e] bg-[#181612] text-[#d4a853] text-[11px] font-mono tracking-wider">
          <Sparkles className="w-3.5 h-3.5 text-[#d4a853]" />
          <span>AUTONOMOUS MULTI-AGENT CODE REVIEW PLATFORM</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-serif font-normal text-[#f5f0e6] tracking-tight leading-[1.08]">
          Code Reviews That Think Like <br />
          <span className="italic text-[#d4a853]">
            Senior Staff Engineers
          </span>
        </h1>

        <p className="text-sm sm:text-base text-[#9e9689] max-w-2xl mx-auto leading-relaxed">
          OpenReview AI connects with GitHub to understand repository semantics, orchestrates specialized agents across Security, Performance, and Bugs, eliminates false alarms via Arbiter consensus, and outputs verified pull request fixes.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-3.5 pt-2">
          <Link to="/dashboard">
            <Button size="lg" variant="electric" className="flex items-center gap-2 h-10 px-6 text-xs font-mono font-semibold">
              <GitFork className="w-4 h-4 text-[#0e0d0b]" />
              <span>Connect Repository</span>
              <ArrowRight className="w-4 h-4 text-[#0e0d0b]" />
            </Button>
          </Link>
          <Link to="/login">
            <Button size="lg" variant="outline" className="h-10 px-6 text-xs font-mono flex items-center gap-2 border-[#36312a] text-[#d8d2c4] hover:border-[#d4a853]/40">
              <Terminal className="w-4 h-4 text-[#8a8378]" />
              <span>Interactive Console</span>
            </Button>
          </Link>
        </div>

        {/* Feature Badges */}
        <div className="flex flex-wrap items-center justify-center gap-6 pt-6 text-[11px] text-[#787165] font-mono">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#5a9e6f]" />
            Zero Data Training Retention
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#5a9e6f]" />
            Provider-Independent (OpenAI, Claude, Gemini, Ollama)
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#5a9e6f]" />
            LangGraph Multi-Agent Arbiter
          </span>
        </div>
      </section>

      {/* Interactive Review Ledger Console */}
      <section className="px-6 py-10 max-w-5xl mx-auto">
        <div className="rounded-[3px] border border-[#2e2a24] bg-[#14120f] p-6 shadow-2xl shadow-black/90">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4 mb-4 border-b border-[#24201a]">
            <div className="flex items-center gap-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#c75a4a]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#e29b38]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#5a9e6f]" />
              <span className="text-xs font-mono text-[#8a8378] ml-2">
                PR #42 — Multi-Agent Verified Findings & Patch
              </span>
            </div>

            <div className="flex items-center gap-1.5 bg-[#1b1915] p-1 rounded-[2px] border border-[#2a2620]">
              <button
                onClick={() => setActiveTab('security')}
                className={`px-3 py-1 rounded-[2px] text-xs font-mono transition ${
                  activeTab === 'security'
                    ? 'bg-[#26211a] text-[#e06c5b] font-medium border border-[#c75a4a]/30'
                    : 'text-[#8a8378] hover:text-[#d8d2c4]'
                }`}
              >
                Security Agent
              </button>
              <button
                onClick={() => setActiveTab('perf')}
                className={`px-3 py-1 rounded-[2px] text-xs font-mono transition ${
                  activeTab === 'perf'
                    ? 'bg-[#26211a] text-[#f0af54] font-medium border border-[#e29b38]/30'
                    : 'text-[#8a8378] hover:text-[#d8d2c4]'
                }`}
              >
                Performance Agent
              </button>
              <button
                onClick={() => setActiveTab('fix')}
                className={`px-3 py-1 rounded-[2px] text-xs font-mono transition ${
                  activeTab === 'fix'
                    ? 'bg-[#26211a] text-[#6cb582] font-medium border border-[#5a9e6f]/30'
                    : 'text-[#8a8378] hover:text-[#d8d2c4]'
                }`}
              >
                AutoFix Patch
              </button>
            </div>
          </div>

          {activeTab === 'security' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
              <div className="p-4 rounded-[2px] bg-[#181512] border border-[#2a2620] space-y-2.5">
                <div className="text-[#e06c5b] font-medium flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#c75a4a]" />
                  <span>CWE-89: SQL Injection Vector</span>
                </div>
                <p className="text-[#8a8378] text-[11px] leading-relaxed">
                  Raw string interpolation in database query allows arbitrary statement execution.
                </p>
                <div className="p-3 rounded-[2px] bg-[#221614] border border-[#c75a4a]/30 text-[#e06c5b]">
                  - await db.execute(f&quot;SELECT * FROM repos WHERE name = '{'{user_input}'}'&quot;)
                </div>
              </div>

              <div className="p-4 rounded-[2px] bg-[#181512] border border-[#2a2620] space-y-2.5">
                <div className="text-[#6cb582] font-medium flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#5a9e6f]" />
                  <span>Arbiter Validated Remediation</span>
                </div>
                <p className="text-[#8a8378] text-[11px] leading-relaxed">
                  Parameterized SQLAlchemy 2.0 select statement with bound parameter serialization.
                </p>
                <div className="p-3 rounded-[2px] bg-[#141f18] border border-[#5a9e6f]/30 text-[#6cb582]">
                  + await db.execute(select(Repo).where(Repo.name == user_input))
                </div>
              </div>
            </div>
          )}

          {activeTab === 'perf' && (
            <div className="p-4 rounded-[2px] bg-[#181512] border border-[#2a2620] font-mono text-xs space-y-2.5">
              <div className="text-[#f0af54] font-medium flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-[#e29b38]" />
                <span>N+1 Query Regression: Review Comment Eager Loading</span>
              </div>
              <p className="text-[#8a8378] text-[11px] leading-relaxed">
                Sequential ORM traversal generates 40+ roundtrips. Converted to a single query via <code className="text-[#d4a853]">selectinload()</code>, reducing API latency from 380ms to 12ms.
              </p>
            </div>
          )}

          {activeTab === 'fix' && (
            <div className="p-4 rounded-[2px] bg-[#181512] border border-[#2a2620] font-mono text-xs space-y-2.5 text-[#6cb582]">
              <div className="text-[11px] text-[#8a8378]">
                AutoFix proposal generated and validated against local test suite (4/4 tests passed).
              </div>
              <pre className="text-[#d8d2c4] whitespace-pre-wrap leading-relaxed text-[11px]">
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
      <section className="px-6 py-20 max-w-5xl mx-auto">
        <h2 className="text-3xl font-serif font-normal text-[#f5f0e6] text-center mb-12 tracking-tight">
          How Multi-Agent Consensus Operates
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-[2px] border border-[#26221c] bg-[#14120f] space-y-2.5">
            <div className="text-[11px] font-mono text-[#d4a853] font-bold">
              [I] AST PARSING
            </div>
            <h3 className="font-serif text-base text-[#f5f0e6]">Diff Extraction</h3>
            <p className="text-xs text-[#8a8378] leading-relaxed">
              Parses unified git diffs, extracts modified syntax trees, and queries pgvector for codebase context.
            </p>
          </div>

          <div className="p-5 rounded-[2px] border border-[#26221c] bg-[#14120f] space-y-2.5">
            <div className="text-[11px] font-mono text-[#e06c5b] font-bold">
              [II] PARALLEL
            </div>
            <h3 className="font-serif text-base text-[#f5f0e6]">Specialist Passes</h3>
            <p className="text-xs text-[#8a8378] leading-relaxed">
              Specialized agents evaluate OWASP security, algorithmic efficiency, bug risks, and clean coding rules.
            </p>
          </div>

          <div className="p-5 rounded-[2px] border border-[#26221c] bg-[#14120f] space-y-2.5">
            <div className="text-[11px] font-mono text-[#3a9e8f] font-bold">
              [III] DEBATE
            </div>
            <h3 className="font-serif text-base text-[#f5f0e6]">Arbiter Consensus</h3>
            <p className="text-xs text-[#8a8378] leading-relaxed">
              Agents cross-examine findings, filter out noise and false positives, and reach majority consensus.
            </p>
          </div>

          <div className="p-5 rounded-[2px] border border-[#26221c] bg-[#14120f] space-y-2.5">
            <div className="text-[11px] font-mono text-[#5a9e6f] font-bold">
              [IV] AUTOFIX
            </div>
            <h3 className="font-serif text-base text-[#f5f0e6]">Verified Patching</h3>
            <p className="text-xs text-[#8a8378] leading-relaxed">
              Generates unified diff patches, executes sandbox test checks, and posts verified comments to GitHub.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#26221c] px-8 py-8 text-center text-xs text-[#6a6358] font-mono">
        OPENREVIEW AI · AUTONOMOUS MULTI-AGENT CODE REVIEW PLATFORM
      </footer>
    </div>
  );
};
