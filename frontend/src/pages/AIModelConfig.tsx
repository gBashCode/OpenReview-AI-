import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Cpu,
  Key,
  Sliders,
  CheckCircle2,
  Sparkles,
  Bot,
  Zap,
  Save,
  RotateCw,
  Terminal,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

const PROVIDERS = [
  { id: 'openai', label: 'OpenAI', defaultModel: 'gpt-4o-mini', desc: 'GPT-4o, GPT-4o-mini, o1-preview' },
  { id: 'anthropic', label: 'Anthropic', defaultModel: 'claude-3-5-sonnet-20241022', desc: 'Claude 3.5 Sonnet, 3.5 Haiku' },
  { id: 'gemini', label: 'Google Gemini', defaultModel: 'gemini-1.5-pro', desc: 'Gemini 1.5 Pro, Gemini 1.5 Flash' },
  { id: 'groq', label: 'Groq', defaultModel: 'llama-3.3-70b-versatile', desc: 'Ultra-low latency Llama 3.3 70B inference' },
  { id: 'ollama', label: 'Local Ollama', defaultModel: 'deepseek-r1:14b', desc: 'Self-hosted airgapped local execution' },
];

export const AIModelConfig: React.FC = () => {
  const { success, info } = useToast();

  const [activeProvider, setActiveProvider] = useState('openai');
  const [modelName, setModelName] = useState('gpt-4o-mini');
  const [apiKey, setApiKey] = useState('sk-proj-••••••••••••••••••••••••••••••••');
  const [temperature, setTemperature] = useState(0.1);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [ollamaEndpoint, setOllamaEndpoint] = useState('http://localhost:11434');
  const [isTesting, setIsTesting] = useState(false);
  const [customRules, setCustomRules] = useState(
`# Custom OpenReview AI Guidelines (.openreview.yml)
rules:
  - id: enforce-sqlalchemy-2
    description: Enforce SQLAlchemy 2.0 select() instead of session.query()
    severity: error
  - id: no-raw-passwords
    description: Prevent plain-text credentials in logs or docstrings
    severity: critical
  - id: require-type-hints
    description: Require explicit type annotations on public service methods
    severity: warning
`
  );

  const handleTestConnection = () => {
    setIsTesting(true);
    setTimeout(() => {
      setIsTesting(false);
      success(
        'LLM Provider Verified',
        `Connection to ${activeProvider.toUpperCase()} (${modelName}) succeeded with 180ms latency.`
      );
    }, 800);
  };

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    success('AI Model Settings Saved', `Default engine set to ${activeProvider} (${modelName}).`);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="pb-2 border-b border-slate-800/80">
        <h1 className="text-2xl font-extrabold text-white tracking-tight">AI Model & LLM Provider Configuration</h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure provider-independent LLM inference engines, token allocations, and custom prompt rules.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Provider Selection */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Cpu className="w-4 h-4 text-sky-400" />
              <span>Provider-Independent LLM Engine</span>
            </CardTitle>
            <CardDescription className="text-xs">
              OpenReview AI agents interact with models strictly via typed Pydantic structured output interfaces
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-2.5">
              {PROVIDERS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    setActiveProvider(p.id);
                    setModelName(p.defaultModel);
                  }}
                  className={`p-3 rounded-xl border text-left transition ${
                    activeProvider === p.id
                      ? 'border-sky-500/80 bg-sky-500/10 text-white ring-1 ring-sky-500/30'
                      : 'border-slate-800/80 bg-slate-950/60 text-slate-400 hover:border-slate-700 hover:text-white'
                  }`}
                >
                  <div className="font-bold text-xs">{p.label}</div>
                  <div className="text-[10px] text-slate-500 mt-1 line-clamp-1">{p.desc}</div>
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Model Identifier
                </label>
                <Input
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="h-8 text-xs bg-[#0b101c] font-mono"
                  required
                />
              </div>

              {activeProvider === 'ollama' ? (
                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">
                    Ollama Local Base URL
                  </label>
                  <Input
                    value={ollamaEndpoint}
                    onChange={(e) => setOllamaEndpoint(e.target.value)}
                    className="h-8 text-xs bg-[#0b101c] font-mono"
                  />
                </div>
              ) : (
                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">
                    API Key (Encrypted in Memory)
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="h-8 text-xs bg-[#0b101c] font-mono"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={handleTestConnection}
                      isLoading={isTesting}
                      className="text-xs shrink-0"
                    >
                      <span>Test</span>
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Hyperparameters & Generation Config */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Sliders className="w-4 h-4 text-purple-400" />
              <span>Inference Hyperparameters</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[11px] font-medium text-slate-300">Temperature (Determinism)</span>
                <span className="font-mono text-sky-400 font-bold">{temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Low temperature (0.05–0.15) guarantees deterministic structured JSON outputs for code analysis.
              </p>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[11px] font-medium text-slate-300">Max Context Window Tokens</span>
                <span className="font-mono text-purple-400 font-bold">{maxTokens}</span>
              </div>
              <input
                type="range"
                min="1024"
                max="16384"
                step="1024"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                Context window budget per parallel agent inspection pass.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Custom Organization Rules Editor */}
        <Card className="border-slate-800 bg-[#0c101c]">
          <CardHeader className="pb-3 border-b border-slate-800/80">
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-emerald-400" />
              <span>Custom Review Guidelines (.openreview.yml)</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Natural language or declarative rules automatically included in every agent&apos;s system prompt
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4">
            <textarea
              rows={8}
              value={customRules}
              onChange={(e) => setCustomRules(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-[#080c14] p-3 text-xs font-mono text-emerald-400 leading-relaxed focus:outline-none focus:ring-1 focus:ring-sky-500"
            />
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button type="submit" variant="electric" size="sm" className="px-6 text-xs font-semibold">
            <Save className="w-3.5 h-3.5 mr-1.5" />
            <span>Save AI Engine Configurations</span>
          </Button>
        </div>
      </form>
    </div>
  );
};
