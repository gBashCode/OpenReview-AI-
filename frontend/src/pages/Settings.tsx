import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Cpu,
  Github,
  Key,
  ShieldCheck,
  Check,
} from 'lucide-react';

export const Settings: React.FC = () => {
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-4o-mini');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Engine Settings</h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure provider-independent AI models, LangGraph agent workflows, and GitHub integrations.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* LLM Provider Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-sky-400" />
              <span>Provider-Independent LLM Engine</span>
            </CardTitle>
            <CardDescription>
              Select the primary foundation model executing security, performance, and arbiter agent tasks.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Active Provider
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                  { id: 'openai', label: 'OpenAI' },
                  { id: 'anthropic', label: 'Anthropic' },
                  { id: 'gemini', label: 'Google Gemini' },
                  { id: 'groq', label: 'Groq (Llama 3)' },
                  { id: 'ollama', label: 'Local Ollama' },
                ].map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setProvider(p.id)}
                    className={`p-3 rounded-lg border text-xs font-semibold transition text-center ${
                      provider === p.id
                        ? 'border-sky-500 bg-sky-500/10 text-sky-400'
                        : 'border-slate-800 bg-slate-900/40 text-slate-400 hover:border-slate-700 hover:text-white'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Model Name</label>
                <Input
                  value={model}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setModel(e.target.value)}
                  placeholder="e.g. gpt-4o-mini or claude-3-5-sonnet"
                />
              </div>
              {provider === 'ollama' && (
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Ollama Base URL</label>
                  <Input
                    value={ollamaUrl}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setOllamaUrl(e.target.value)}
                  />
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* GitHub App Integration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Github className="w-5 h-5 text-indigo-400" />
              <span>GitHub App Integration</span>
            </CardTitle>
            <CardDescription>
              Webhook and API secrets configured via environment variables (<code className="text-sky-300">.env</code>).
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-xs text-slate-400">Webhook Status</div>
                <div className="text-sm font-semibold text-emerald-400 flex items-center gap-1.5 mt-1">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Configured</span>
                </div>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-xs text-slate-400">Review Comments API</div>
                <div className="text-sm font-semibold text-sky-400 flex items-center gap-1.5 mt-1">
                  <Key className="w-4 h-4" />
                  <span>Ready</span>
                </div>
              </div>
              <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
                <div className="text-xs text-slate-400">Vector Embeddings</div>
                <div className="text-sm font-semibold text-indigo-400 flex items-center gap-1.5 mt-1">
                  <span>pgvector 1536-dim</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="flex items-center justify-end gap-3">
          {saved && (
            <span className="text-xs text-emerald-400 flex items-center gap-1">
              <Check className="w-4 h-4" />
              <span>Settings saved</span>
            </span>
          )}
          <Button type="submit">Save Changes</Button>
        </div>
      </form>
    </div>
  );
};
