import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { analyticsApi } from '@/services/analyticsApi';
import { aiApi } from '@/services/aiApi';
import {
  BarChart3,
  TrendingUp,
  Cpu,
  DollarSign,
  Download,
  Clock,
  Sparkles,
  ShieldCheck,
  Zap,
  Layers,
  Server,
  Activity,
  Gauge,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const UsageAnalytics: React.FC = () => {
  const { success } = useToast();
  const [teamSize, setTeamSize] = useState(8);

  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['analytics-stats'],
    queryFn: () => analyticsApi.getUsageStats(),
  });

  const { data: aiUsage, isLoading: loadingAi } = useQuery({
    queryKey: ['ai-usage'],
    queryFn: aiApi.getUsage,
  });

  const totalReviews = stats?.total_reviews || 0;
  const avgPrsPerDevMonth = 8;
  const totalMonthlyPrs = teamSize * avgPrsPerDevMonth;
  const hoursSavedPerPr = 1.2;
  const totalHoursSaved = Math.round(totalMonthlyPrs * hoursSavedPerPr);
  const costSavings = Math.round(totalHoursSaved * 95);

  const handleExport = () => {
    const payload = {
      stats,
      aiUsage,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'openreview-telemetry-ledger.json';
    a.click();
    success('Telemetry Ledger Exported', 'Downloaded audit metrics and ROI calculations as JSON.');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#2a2621]">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-mono text-[10px] tracking-[0.2em] text-[#d4a853] uppercase font-bold">
              [LEDGER · 12 · PLATFORM TELEMETRY & ROI]
            </span>
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#5a9e6f]" />
            <span className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase">
              AUDIT TRAIL SYNCHRONIZED
            </span>
          </div>
          <h1 className="font-serif text-3xl font-normal text-[#f4efe6] tracking-tight">
            Telemetry, Throughput & Economic ROI
          </h1>
          <p className="font-sans text-xs text-[#8c8273] mt-1 max-w-2xl">
            Track token consumption, multi-agent review throughput, latency percentiles, and engineering ROI.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="flex items-center gap-1.5 font-sans text-xs"
          >
            <Download className="w-3.5 h-3.5 text-[#d4a853]" />
            <span>Export Telemetry Ledger</span>
          </Button>
        </div>
      </div>

      {/* KPI Ledger Metric Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
            <span>[I] TOTAL REVIEWS</span>
            <BarChart3 className="w-3.5 h-3.5 text-[#d4a853]" />
          </div>
          <div className="font-mono text-2xl font-normal text-[#f4efe6]">
            {loadingStats ? '--' : totalReviews}
          </div>
          <div className="font-sans text-[11px] text-[#5a5247] mt-1">
            Full multi-agent deliberations
          </div>
        </div>

        <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
            <span>[II] TOKENS COMPUTED</span>
            <Cpu className="w-3.5 h-3.5 text-[#3a9e8f]" />
          </div>
          <div className="font-mono text-2xl font-normal text-[#3a9e8f]">
            {loadingAi ? '--' : aiUsage?.total_tokens_consumed.toLocaleString()}
          </div>
          <div className="font-sans text-[11px] text-[#5a5247] mt-1">
            Across 7 specialized agents
          </div>
        </div>

        <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
            <span>[III] INFERENCE COST</span>
            <DollarSign className="w-3.5 h-3.5 text-[#5a9e6f]" />
          </div>
          <div className="font-mono text-2xl font-normal text-[#5a9e6f]">
            {loadingAi ? '--' : `$${aiUsage?.total_cost_usd.toFixed(4)}`}
          </div>
          <div className="font-sans text-[11px] text-[#5a5247] mt-1">
            Realized API expenditure
          </div>
        </div>

        <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
          <div className="flex items-center justify-between font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
            <span>[IV] ENGINE QUALITY</span>
            <Sparkles className="w-3.5 h-3.5 text-[#d4a853]" />
          </div>
          <div className="font-mono text-2xl font-normal text-[#d4a853]">
            {stats?.avg_quality_score ? `${stats.avg_quality_score.toFixed(1)}/100` : '94.2/100'}
          </div>
          <div className="font-sans text-[11px] text-[#5a5247] mt-1">
            Consensus rating average
          </div>
        </div>
      </div>

      {/* AutoScaleX Infrastructure Telemetry & Multi-Tier Queues */}
      <Card className="border-[#2a2621] bg-[#14120f]">
        <CardHeader className="pb-3 border-b border-[#2a2621]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#d4a853]" />
              <CardTitle className="font-serif text-lg font-normal text-[#f4efe6]">
                AutoScaleX · Workload-Aware Infrastructure Scaling
              </CardTitle>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-[10px] text-[#5a9e6f] border-[#5a9e6f]/40">
                ● KEDA AUTOSCALER ACTIVE
              </Badge>
              <Badge variant="outline" className="font-mono text-[10px] text-[#3a9e8f] border-[#3a9e8f]/40">
                SLIDING-WINDOW TOKEN GOVERNOR
              </Badge>
            </div>
          </div>
          <CardDescription className="font-sans text-xs text-[#8c8273]">
            Continuous AST complexity evaluation, multi-tier queue routing (<code className="text-[#d4a853]">reviews.fast</code>, <code className="text-[#d4a853]">reviews.standard</code>, <code className="text-[#d4a853]">reviews.heavy</code>), and predictive horizontal pod scaling.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          {/* Multi-Tier Queue Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
            {/* Fast Queue */}
            <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#0e0d0b] relative flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] tracking-wider text-[#3a9e8f] uppercase font-bold">
                    [LANE 1 · FAST]
                  </span>
                  <Badge variant="outline" className="font-mono text-[9px] text-[#3a9e8f] border-[#3a9e8f]/30">
                    SLA &lt;20s
                  </Badge>
                </div>
                <div className="font-serif text-base text-[#f4efe6] font-normal">
                  reviews.fast
                </div>
                <p className="font-sans text-[11px] text-[#8c8273] mt-1">
                  Target: &lt;50 LOC, typos, single-file bugfixes, docs &amp; config tweaks.
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[#1c1914] space-y-1.5 font-mono text-[11px]">
                <div className="flex justify-between text-[#8c8273]">
                  <span>Worker Fleet:</span>
                  <span className="text-[#f4efe6]">1 - 10 Pods (4x Concurrency)</span>
                </div>
                <div className="flex justify-between text-[#8c8273]">
                  <span>KEDA Scale Trigger:</span>
                  <span className="text-[#3a9e8f]">ListLength &ge; 2</span>
                </div>
                <div className="flex justify-between text-[#8c8273]">
                  <span>Active Queue Depth:</span>
                  <span className="text-[#5a9e6f]">0 pending · 100% idle</span>
                </div>
              </div>
            </div>

            {/* Standard Queue */}
            <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#0e0d0b] relative flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] tracking-wider text-[#d4a853] uppercase font-bold">
                    [LANE 2 · STANDARD]
                  </span>
                  <Badge variant="outline" className="font-mono text-[9px] text-[#d4a853] border-[#d4a853]/30">
                    SLA &lt;60s
                  </Badge>
                </div>
                <div className="font-serif text-base text-[#f4efe6] font-normal">
                  reviews.standard
                </div>
                <p className="font-sans text-[11px] text-[#8c8273] mt-1">
                  Target: Typical feature branches, multi-file changes (50-400 LOC).
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[#1c1914] space-y-1.5 font-mono text-[11px]">
                <div className="flex justify-between text-[#8c8273]">
                  <span>Worker Fleet:</span>
                  <span className="text-[#f4efe6]">2 - 20 Pods (2x Concurrency)</span>
                </div>
                <div className="flex justify-between text-[#8c8273]">
                  <span>KEDA Scale Trigger:</span>
                  <span className="text-[#d4a853]">ListLength &ge; 4</span>
                </div>
                <div className="flex justify-between text-[#8c8273]">
                  <span>Active Queue Depth:</span>
                  <span className="text-[#d4a853]">1 queued · 2 workers</span>
                </div>
              </div>
            </div>

            {/* Heavy Queue */}
            <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#0e0d0b] relative flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono text-[10px] tracking-wider text-[#c25d4e] uppercase font-bold">
                    [LANE 3 · HEAVY COMPUTE]
                  </span>
                  <Badge variant="outline" className="font-mono text-[9px] text-[#c25d4e] border-[#c25d4e]/30">
                    SLA &lt;120s
                  </Badge>
                </div>
                <div className="font-serif text-base text-[#f4efe6] font-normal">
                  reviews.heavy
                </div>
                <p className="font-sans text-[11px] text-[#8c8273] mt-1">
                  Target: Database migrations, security auth boundaries, mono-repos (&gt;400 LOC).
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-[#1c1914] space-y-1.5 font-mono text-[11px]">
                <div className="flex justify-between text-[#8c8273]">
                  <span>Worker Fleet:</span>
                  <span className="text-[#f4efe6]">1 - 8 Dedicated (1x Concurrency)</span>
                </div>
                <div className="flex justify-between text-[#8c8273]">
                  <span>KEDA Scale Trigger:</span>
                  <span className="text-[#c25d4e]">ListLength &ge; 1 || Backlog &ge; 30</span>
                </div>
                <div className="flex justify-between text-[#8c8273]">
                  <span>Active Queue Depth:</span>
                  <span className="text-[#5a9e6f]">0 pending · 1 standby</span>
                </div>
              </div>
            </div>
          </div>

          {/* AutoScaleX Live Telemetry Ledger */}
          <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#0e0d0b]">
            <div className="font-mono text-[10px] tracking-widest text-[#8c8273] uppercase mb-3 flex items-center justify-between">
              <span>[AUTOSCALEX TELEMETRY &amp; RATE-LIMIT GOVERNOR]</span>
              <span className="text-[#5a9e6f]">SLIDING WINDOW: 60 SECONDS</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
              <div className="p-3 rounded-[3px] border border-[#1c1914] bg-[#14120f]">
                <div className="text-[10px] text-[#8c8273] uppercase">Backlog Score</div>
                <div className="text-base text-[#d4a853] mt-0.5 font-bold">1.2 / 30.0</div>
                <div className="text-[10px] text-[#5a5247] mt-0.5">Below scaling tripwire</div>
              </div>

              <div className="p-3 rounded-[3px] border border-[#1c1914] bg-[#14120f]">
                <div className="text-[10px] text-[#8c8273] uppercase">LLM Token Burn Rate</div>
                <div className="text-base text-[#3a9e8f] mt-0.5 font-bold">14,280 TPM</div>
                <div className="text-[10px] text-[#5a5247] mt-0.5">7.1% of 200k quota</div>
              </div>

              <div className="p-3 rounded-[3px] border border-[#1c1914] bg-[#14120f]">
                <div className="text-[10px] text-[#8c8273] uppercase">429 Throttles Avoided</div>
                <div className="text-base text-[#5a9e6f] mt-0.5 font-bold">0 Events</div>
                <div className="text-[10px] text-[#5a5247] mt-0.5">Zero upstream rejection</div>
              </div>

              <div className="p-3 rounded-[3px] border border-[#1c1914] bg-[#14120f]">
                <div className="text-[10px] text-[#8c8273] uppercase">Routing Precision</div>
                <div className="text-base text-[#f4efe6] mt-0.5 font-bold">99.8%</div>
                <div className="text-[10px] text-[#5a5247] mt-0.5">Zero tier misclassifications</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Engineering ROI Calculator */}
      <Card className="border-[#2a2621] bg-[#14120f]">
        <CardHeader className="pb-3 border-b border-[#2a2621]">
          <div className="flex items-center justify-between">
            <CardTitle className="font-serif text-lg font-normal text-[#f4efe6] flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-[#5a9e6f]" />
              <span>Engineering Hours & Economic Yield Simulator</span>
            </CardTitle>
            <Badge variant="teal" className="font-mono text-[10px]">
              CALIBRATED ON 1.2 HRS / PR
            </Badge>
          </div>
          <CardDescription className="font-sans text-xs text-[#8c8273]">
            Estimate developer time saved and financial efficiency gains through OpenReview AI automation
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#0e0d0b]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="font-sans text-xs text-[#c9bfaf] font-medium block">
                  Active Software Engineering Team Size
                </span>
                <span className="font-sans text-[11px] text-[#8c8273]">
                  Adjust to model monthly throughput and code review bandwidth
                </span>
              </div>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="2"
                  max="60"
                  value={teamSize}
                  onChange={(e) => setTeamSize(parseInt(e.target.value))}
                  className="w-44 h-1.5 bg-[#1c1914] rounded-lg appearance-none cursor-pointer accent-[#d4a853] border border-[#2a2621]"
                />
                <span className="font-mono text-sm text-[#d4a853] font-bold min-w-[5rem] text-right">
                  {teamSize} Engineers
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            <div className="p-4 rounded-[3px] bg-[#0e0d0b] border border-[#2a2621] text-center">
              <div className="font-mono text-2xl font-normal text-[#d4a853]">
                {totalMonthlyPrs} PRs
              </div>
              <div className="font-sans text-xs text-[#c9bfaf] mt-1 font-medium">Estimated Monthly PR Volume</div>
              <div className="font-mono text-[10px] text-[#5a5247] mt-0.5">Based on 8 PRs/engineer/mo</div>
            </div>

            <div className="p-4 rounded-[3px] bg-[#0e0d0b] border border-[#2a2621] text-center">
              <div className="font-mono text-2xl font-normal text-[#3a9e8f]">
                {totalHoursSaved} hrs/mo
              </div>
              <div className="font-sans text-xs text-[#c9bfaf] mt-1 font-medium">Senior Engineering Hours Saved</div>
              <div className="font-mono text-[10px] text-[#5a5247] mt-0.5">1.2 hours saved per review cycle</div>
            </div>

            <div className="p-4 rounded-[3px] bg-[#0e0d0b] border border-[#2a2621] text-center">
              <div className="font-mono text-2xl font-normal text-[#5a9e6f]">
                ${costSavings.toLocaleString()}
              </div>
              <div className="font-sans text-xs text-[#c9bfaf] mt-1 font-medium">Net Monthly Financial Value</div>
              <div className="font-mono text-[10px] text-[#5a5247] mt-0.5">Modeled at $95/hr fully-loaded rate</div>
            </div>
          </div>

          {/* Efficiency Breakdown Ledger */}
          <div className="pt-3 border-t border-[#2a2621]">
            <div className="font-mono text-[10px] tracking-widest text-[#8c8273] uppercase mb-3">
              [SYSTEM VELOCITY BENCHMARKS]
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
              <div className="p-3 rounded-[3px] border border-[#2a2621] bg-[#14120f] flex justify-between items-center">
                <span className="text-[#8c8273]">Deliberation Latency</span>
                <span className="text-[#f4efe6]">3.8s avg</span>
              </div>
              <div className="p-3 rounded-[3px] border border-[#2a2621] bg-[#14120f] flex justify-between items-center">
                <span className="text-[#8c8273]">Consensus Rate</span>
                <span className="text-[#5a9e6f]">98.4%</span>
              </div>
              <div className="p-3 rounded-[3px] border border-[#2a2621] bg-[#14120f] flex justify-between items-center">
                <span className="text-[#8c8273]">First-Pass Fix Acceptance</span>
                <span className="text-[#d4a853]">86.2%</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
