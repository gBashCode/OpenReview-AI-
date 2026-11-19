import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  BarChart3,
  TrendingUp,
  Cpu,
  DollarSign,
  Clock,
  Zap,
  Sparkles,
  Download,
  Calendar,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const UsageAnalytics: React.FC = () => {
  const { success } = useToast();
  const [teamSize, setTeamSize] = useState(12);

  // Time and savings formulas
  const avgPrsPerDevMonth = 8;
  const totalMonthlyPrs = teamSize * avgPrsPerDevMonth;
  const hoursSavedPerPr = 1.2;
  const totalHoursSaved = Math.round(totalMonthlyPrs * hoursSavedPerPr);
  const costSavings = Math.round(totalHoursSaved * 95); // ~$95/hr blended engineer cost

  const handleExport = () => {
    success('Analytics Exported', 'Usage telemetry downloaded in JSON format.');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">Usage, Telemetry & ROI Analytics</h1>
            <Badge variant="purple">Team Pro Tier</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Track token consumption, agent review throughput, latency percentiles, and engineering ROI.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="flex items-center gap-1.5 text-xs"
          >
            <Download className="w-3.5 h-3.5 text-slate-400" />
            <span>Export Analytics</span>
          </Button>
        </div>
      </div>

      {/* Top ROI & Cost Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Monthly LLM Cost</span>
              <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">$18.42</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Across 1.6M total tokens</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Engineering Hours Saved</span>
              <Clock className="w-3.5 h-3.5 text-sky-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-sky-400">{totalHoursSaved} hrs</div>
            <p className="text-[11px] text-slate-500 mt-0.5">Based on {teamSize} active developers</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>Estimated Team ROI</span>
              <TrendingUp className="w-3.5 h-3.5 text-purple-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-purple-400">${costSavings.toLocaleString()}</div>
            <p className="text-[11px] text-slate-500 mt-0.5">vs manual human review latency</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-[#0c101c]">
          <CardContent className="p-4">
            <div className="text-xs text-slate-400 font-medium mb-1 flex items-center justify-between">
              <span>p95 Review Latency</span>
              <Zap className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-amber-300">2.4s</div>
            <p className="text-[11px] text-slate-500 mt-0.5">p50 turnaround: 1.6s</p>
          </CardContent>
        </Card>
      </div>

      {/* Token Consumption by Model Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-sky-400" />
              <span>Token Consumption by Foundation Model</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div>
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-slate-300">OpenAI (gpt-4o-mini)</span>
                <span className="text-sky-400 font-bold">1,120,400 tokens (70%)</span>
              </div>
              <Progress value={70} className="h-1.5" />
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-slate-300">Anthropic (Claude 3.5 Sonnet)</span>
                <span className="text-purple-400 font-bold">384,100 tokens (24%)</span>
              </div>
              <Progress value={24} indicatorClassName="bg-purple-500" className="h-1.5" />
            </div>

            <div>
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-slate-300">Google Gemini (1.5 Flash)</span>
                <span className="text-emerald-400 font-bold">96,200 tokens (6%)</span>
              </div>
              <Progress value={6} indicatorClassName="bg-emerald-500" className="h-1.5" />
            </div>
          </CardContent>
        </Card>

        {/* Interactive ROI Calculator */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-amber-300" />
              <span>Interactive ROI & Time Saved Calculator</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Simulate review hours reclaimed based on your engineering organization size
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300 font-medium">Active Engineers: {teamSize}</span>
                <span className="font-mono text-sky-400 font-bold">~{totalMonthlyPrs} PRs / month</span>
              </div>
              <input
                type="range"
                min="2"
                max="100"
                step="1"
                value={teamSize}
                onChange={(e) => setTeamSize(parseInt(e.target.value))}
                className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
              />
            </div>

            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs font-mono space-y-1">
              <div className="flex justify-between text-slate-300">
                <span>Estimated Time Saved:</span>
                <span className="text-emerald-400 font-bold">{totalHoursSaved} developer hours/mo</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Equivalent Dollar Value:</span>
                <span className="text-purple-400 font-bold">${costSavings.toLocaleString()} / month</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Subscription Quota Status */}
      <Card className="border-slate-800 bg-[#0c101c]">
        <CardHeader className="pb-3 border-b border-slate-800/80 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-semibold text-white">Monthly Plan Quota & Limits</CardTitle>
            <CardDescription className="text-xs">Team Pro Tier (Unlimited public repositories, 5,000 PR reviews/mo)</CardDescription>
          </div>
          <Badge variant="success">Active Plan</Badge>
        </CardHeader>
        <CardContent className="p-4">
          <div className="flex justify-between text-xs font-mono mb-1.5">
            <span className="text-slate-400">Reviews Consumed: 142 / 5,000</span>
            <span className="text-emerald-400 font-bold">2.8% used</span>
          </div>
          <Progress value={2.8} className="h-2" />
        </CardContent>
      </Card>
    </div>
  );
};
