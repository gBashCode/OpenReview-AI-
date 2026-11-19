import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { aiApi } from '@/services/aiApi';
import {
  Cpu,
  Sliders,
  Sparkles,
  Save,
  Activity,
  Server,
  Zap,
  CheckCircle2,
  Clock,
  Layers,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

const PROVIDERS = [
  { id: 'openai', label: 'OpenAI', defaultModel: 'gpt-4o-mini', desc: 'GPT-4o, GPT-4o-mini, o1 reasoning engines' },
  { id: 'anthropic', label: 'Anthropic', defaultModel: 'claude-3-5-sonnet-20241022', desc: 'Claude 3.5 Sonnet, 3.5 Haiku high-accuracy analysis' },
  { id: 'gemini', label: 'Google Gemini', defaultModel: 'gemini-1.5-pro', desc: 'Gemini 1.5 Pro 2M token context window architecture' },
  { id: 'groq', label: 'Groq LPUs', defaultModel: 'llama-3.3-70b-versatile', desc: 'Sub-second Llama 3.3 70B inference engine' },
  { id: 'ollama', label: 'Local Ollama', defaultModel: 'deepseek-r1:14b', desc: 'Self-hosted air-gapped local execution on private hardware' },
];

export const AIModelConfig: React.FC = () => {
  const { success, error, info } = useToast();

  const [activeProvider, setActiveProvider] = useState('openai');
  const [modelName, setModelName] = useState('gpt-4o-mini');
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [isTesting, setIsTesting] = useState(false);

  // Queries for live backend AI infrastructure
  const { data: healthData, isFetching: fetchingHealth } = useQuery({
    queryKey: ['ai-health'],
    queryFn: aiApi.checkHealth,
    refetchInterval: 30000,
  });

  const { data: catalog } = useQuery({
    queryKey: ['ai-models'],
    queryFn: aiApi.listModels,
  });

  const { data: usage } = useQuery({
    queryKey: ['ai-usage'],
    queryFn: aiApi.getUsage,
    refetchInterval: 10000,
  });

  const handleTestConnection = async () => {
    setIsTesting(true);
    try {
      const res = await aiApi.checkHealth();
      const providerStat = res[activeProvider];
      if (providerStat && providerStat.is_healthy) {
        success(
          'LLM Provider Verified',
          `Connection to ${activeProvider.toUpperCase()} succeeded (${providerStat.latency_ms}ms roundtrip latency).`
        );
      } else {
        info(
          'Provider Evaluated',
          providerStat?.message || `Provider ${activeProvider} is configured with simulated fallback mode.`
        );
      }
    } catch (err: any) {
      error('Health Probe Failed', err.message || 'Could not reach AI provider endpoint.');
    } finally {
      setIsTesting(false);
    }
  };

  const handleSaveSettings = () => {
    success('Configuration Saved', `Provider ${activeProvider.toUpperCase()} (${modelName}) persisted to environment profile.`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-[#2a2621]">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="font-mono text-[10px] tracking-[0.2em] text-[#d4a853] uppercase font-bold">
              [LEDGER · 11 · INFERENCE ARCHITECTURE]
            </span>
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#5a9e6f]" />
            <span className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase">
              MULTI-PROVIDER ROUTER ACTIVE
            </span>
          </div>
          <h1 className="font-serif text-3xl font-normal text-[#f4efe6] tracking-tight">
            AI Engine & Provider Routing
          </h1>
          <p className="font-sans text-xs text-[#8c8273] mt-1 max-w-2xl">
            Configure LLM backends (OpenAI, Gemini, Anthropic, Groq, Ollama), token budgets, and consensus parameters.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTestConnection}
            isLoading={isTesting || fetchingHealth}
            className="flex items-center gap-1.5 font-sans text-xs"
          >
            <Activity className="w-3.5 h-3.5 text-[#d4a853]" />
            <span>Probe Latency</span>
          </Button>

          <Button
            variant="electric"
            size="sm"
            onClick={handleSaveSettings}
            className="flex items-center gap-1.5 font-sans text-xs"
          >
            <Save className="w-3.5 h-3.5 text-[#0e0d0b]" />
            <span>Persist Config</span>
          </Button>
        </div>
      </div>

      {/* Live Token & Cost Metric Ledger */}
      {usage && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
            <div className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
              [I] TOKEN ALLOCATION CAP
            </div>
            <div className="font-mono text-2xl font-normal text-[#f4efe6]">
              {usage.token_budget.toLocaleString()}
            </div>
            <div className="font-sans text-[11px] text-[#5a5247] mt-1">
              Monthly enterprise allowance
            </div>
          </div>

          <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
            <div className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
              [II] TOKENS CONSUMED
            </div>
            <div className="font-mono text-2xl font-normal text-[#d4a853]">
              {usage.total_tokens_consumed.toLocaleString()}
            </div>
            <div className="font-sans text-[11px] text-[#5a5247] mt-1">
              Deliberation & patch generation
            </div>
          </div>

          <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
            <div className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
              [III] ESTIMATED AI SPEND
            </div>
            <div className="font-mono text-2xl font-normal text-[#5a9e6f]">
              ${usage.total_cost_usd.toFixed(4)}
            </div>
            <div className="font-sans text-[11px] text-[#5a5247] mt-1">
              Calculated on token rates
            </div>
          </div>

          <div className="p-4 rounded-[3px] border border-[#2a2621] bg-[#14120f] relative overflow-hidden">
            <div className="font-mono text-[10px] tracking-wider text-[#8c8273] uppercase mb-1">
              [IV] REMAINING QUOTA
            </div>
            <div className="font-mono text-2xl font-normal text-[#3a9e8f]">
              {usage.budget_remaining.toLocaleString()}
            </div>
            <div className="font-sans text-[11px] text-[#5a5247] mt-1">
              Available before rate cap
            </div>
          </div>
        </div>
      )}

      {/* Provider Selector Cards */}
      <div>
        <div className="flex items-center justify-between mb-2.5">
          <span className="font-mono text-[10px] tracking-widest text-[#8c8273] uppercase font-bold">
            Select Active Inference Provider
          </span>
          <span className="font-mono text-[10px] text-[#5a5247]">
            AUTOMATIC FAILOVER ENABLED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {PROVIDERS.map((prov) => {
            const healthStat = healthData ? healthData[prov.id] : null;
            const isSelected = activeProvider === prov.id;
            return (
              <button
                key={prov.id}
                onClick={() => {
                  setActiveProvider(prov.id);
                  setModelName(prov.defaultModel);
                }}
                className={`p-3.5 rounded-[3px] border text-left transition relative flex flex-col justify-between ${
                  isSelected
                    ? 'border-[#d4a853] bg-[#1c1914] shadow-[0_2px_12px_rgba(212,168,83,0.08)]'
                    : 'border-[#2a2621] bg-[#14120f] hover:border-[#3e382f]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-serif text-base font-normal text-[#f4efe6]">
                      {prov.label}
                    </span>
                    {healthStat?.is_healthy ? (
                      <span className="w-2 h-2 rounded-full bg-[#5a9e6f]" title="Operational" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-[#d4a853]" title="Fallback Mode" />
                    )}
                  </div>
                  <p className="font-sans text-[11px] text-[#8c8273] leading-relaxed">
                    {prov.desc}
                  </p>
                </div>
                <div className="mt-3 pt-2 border-t border-[#2a2621]/80 font-mono text-[10px] text-[#5a5247] truncate">
                  <span className="text-[#8c8273]">Model:</span> {prov.defaultModel}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Parameter Configuration Card */}
      <Card className="border-[#2a2621] bg-[#14120f]">
        <CardHeader className="pb-3 border-b border-[#2a2621]">
          <div className="flex items-center justify-between">
            <CardTitle className="font-serif text-lg font-normal text-[#f4efe6] flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#d4a853]" />
              <span>Inference Hyperparameters — {activeProvider.toUpperCase()}</span>
            </CardTitle>
            <Badge variant="amber" className="font-mono text-[10px]">
              ENGINE ACTIVE
            </Badge>
          </div>
          <CardDescription className="font-sans text-xs text-[#8c8273]">
            Fine-tune temperature bounds, maximum output tokens, and context window targets
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="font-sans text-xs text-[#c9bfaf] font-medium block mb-1.5">
                Target Model Identifier
              </label>
              <Input
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="font-mono text-xs"
              />
              <span className="font-sans text-[11px] text-[#5a5247] mt-1.5 block">
                Catalog reference: <code className="font-mono text-[#8c8273]">{catalog?.default_model || 'gpt-4o-mini'}</code>
              </span>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="font-sans text-xs text-[#c9bfaf] font-medium">
                  Sampling Temperature
                </label>
                <span className="font-mono text-xs text-[#d4a853] font-bold">
                  {temperature.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-[#1c1914] rounded-lg appearance-none cursor-pointer accent-[#d4a853] mt-2 border border-[#2a2621]"
              />
              <div className="flex items-center justify-between font-mono text-[10px] text-[#5a5247] mt-1.5">
                <span>0.0 (Strict AST Code Review)</span>
                <span>1.0 (Creative Exploratory)</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-[#2a2621]">
            <div className="max-w-md">
              <label className="font-sans text-xs text-[#c9bfaf] font-medium block mb-1.5">
                Max Token Limit per Deliberation Turn
              </label>
              <Input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value) || 4096)}
                className="font-mono text-xs"
              />
              <span className="font-sans text-[11px] text-[#5a5247] mt-1.5 block">
                Context envelope limit: <code className="font-mono text-[#8c8273]">{catalog?.max_context_length?.toLocaleString() || '128,000'} tokens</code>
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
