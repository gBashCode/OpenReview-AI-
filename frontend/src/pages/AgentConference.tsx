import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { mockConferenceAgents, mockDebateTimeline, AgentDebateMessage } from '@/services/mockData';
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
  ArrowRight,
  Send,
  Play,
  RotateCcw,
} from 'lucide-react';
import { useToast } from '@/components/ui/toast';

export const AgentConference: React.FC = () => {
  const { success, info } = useToast();
  const [messages, setMessages] = useState<AgentDebateMessage[]>(mockDebateTimeline);
  const [isSimulating, setIsSimulating] = useState(false);
  const [userPrompt, setUserPrompt] = useState('');

  const handleSimulateDebate = () => {
    setIsSimulating(true);
    info('Deliberating', 'AI Agents are cross-examining findings in parallel...');

    setTimeout(() => {
      const newMessage: AgentDebateMessage = {
        id: `msg-${Date.now()}`,
        agentId: 'agent-arbiter',
        agentName: 'Quality Arbiter',
        timestamp: new Date().toLocaleTimeString(),
        type: 'consensus',
        content: 'Cross-verification complete. All 4 agents agree on remediation strategy. Quality score updated to 94.5/100.',
        verified: true,
      };
      setMessages((prev) => [...prev, newMessage]);
      setIsSimulating(false);
      success('Consensus Reached', 'Agents finalized the review pass without conflicts.');
    }, 1500);
  };

  const handleSendPrompt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userPrompt.trim()) return;

    const userMsg: AgentDebateMessage = {
      id: `usr-${Date.now()}`,
      agentId: 'user',
      agentName: 'Human Reviewer (You)',
      timestamp: new Date().toLocaleTimeString(),
      type: 'claim',
      content: userPrompt,
      verified: true,
    };

    setMessages((prev) => [...prev, userMsg]);
    setUserPrompt('');

    // Simulate Agent response
    setTimeout(() => {
      const agentReply: AgentDebateMessage = {
        id: `reply-${Date.now()}`,
        agentId: 'agent-sec',
        agentName: 'Security Sentinel',
        timestamp: new Date().toLocaleTimeString(),
        type: 'verification',
        content: `Acknowledging reviewer comment: Re-verifying line against OWASP ASVS v4.0 standards. The proposed parameterization adheres to defense-in-depth principles.`,
        verified: true,
      };
      setMessages((prev) => [...prev, agentReply]);
    }, 1000);
  };

  const getAgentIcon = (id: string) => {
    switch (id) {
      case 'agent-sec':
        return <ShieldCheck className="w-4 h-4 text-rose-400" />;
      case 'agent-perf':
        return <Zap className="w-4 h-4 text-amber-400" />;
      case 'agent-bug':
        return <Bug className="w-4 h-4 text-sky-400" />;
      case 'agent-style':
        return <Code2 className="w-4 h-4 text-purple-400" />;
      default:
        return <Bot className="w-4 h-4 text-emerald-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-extrabold text-white tracking-tight">AI Agent Conference Room</h1>
            <Badge variant="purple">LangGraph Multi-Agent Debate</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Observe autonomous agents debate, cross-examine findings, filter false alarms, and formulate consensus.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setMessages(mockDebateTimeline);
              info('Timeline Reset', 'Reverted to initial debate transcript.');
            }}
            className="flex items-center gap-1.5 text-xs"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
            <span>Reset</span>
          </Button>

          <Button
            variant="electric"
            size="sm"
            onClick={handleSimulateDebate}
            isLoading={isSimulating}
            className="flex items-center gap-1.5 text-xs font-semibold"
          >
            <Play className="w-3.5 h-3.5 text-amber-300" />
            <span>Trigger Agent Deliberation</span>
          </Button>
        </div>
      </div>

      {/* Review Progress Stepper */}
      <Card className="border-slate-800 bg-[#0c101c]">
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
            <span className="font-semibold text-white">Review Pipeline Progress</span>
            <span className="text-emerald-400 font-bold">Consensus Reached (100%)</span>
          </div>
          <Progress value={100} className="h-2 mb-4" />

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-[11px] font-mono">
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>1. AST Parsed</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>2. Parallel Passes</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>3. Cross-Debate</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>4. AutoFix Verified</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-emerald-500/30 text-emerald-300 flex items-center justify-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>5. Arbiter Approval</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Agent Roster Cards */}
      <div>
        <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <Bot className="w-4 h-4 text-sky-400" />
          <span>Active Agent Panel (5 Autonomous Specialists)</span>
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
          {mockConferenceAgents.map((agent) => (
            <Card key={agent.id} className="border-slate-800/90 bg-[#0c101c] hover:border-slate-700 transition">
              <CardContent className="p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="w-7 h-7 rounded-lg bg-slate-800/80 flex items-center justify-center">
                    {getAgentIcon(agent.id)}
                  </div>
                  <Badge variant="purple" className="text-[9px] py-0">
                    {agent.confidenceScore}% conf
                  </Badge>
                </div>

                <div>
                  <div className="font-bold text-white text-xs truncate">{agent.name}</div>
                  <div className="text-[10px] text-slate-400 truncate">{agent.role}</div>
                </div>

                <div className="p-1.5 rounded bg-slate-950 border border-slate-800/60 text-[10px] text-slate-300 font-mono truncate">
                  Focus: {agent.currentFocus}
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-1">
                  <span>Findings: {agent.findingsCount}</span>
                  <span className="text-emerald-400 capitalize">{agent.status}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Agent Discussion Timeline & Debate Stream */}
      <Card className="border-slate-800/90 bg-[#0c101c]">
        <CardHeader className="pb-3 border-b border-slate-800/80 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm font-semibold text-white flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-indigo-400" />
              <span>Deliberation Transcript & Reasoning Stream</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Live transcript of multi-agent debate resolving potential false alarms on PR #42
            </CardDescription>
          </div>
          <span className="text-xs font-mono text-emerald-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>Consensus Quorum: 5/5</span>
          </span>
        </CardHeader>

        <CardContent className="p-4 space-y-4">
          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            {messages.map((msg) => {
              const isUser = msg.agentId === 'user';
              return (
                <div
                  key={msg.id}
                  className={`p-3.5 rounded-xl border text-xs leading-relaxed transition ${
                    isUser
                      ? 'border-sky-500/40 bg-sky-950/20 text-sky-100 ml-8'
                      : msg.type === 'consensus'
                      ? 'border-emerald-500/40 bg-emerald-950/15 text-emerald-100'
                      : 'border-slate-800/80 bg-slate-950/60 text-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1 text-[11px] font-mono">
                    <div className="flex items-center gap-2 font-semibold">
                      {getAgentIcon(msg.agentId)}
                      <span className={isUser ? 'text-sky-300' : 'text-white'}>
                        {msg.agentName}
                      </span>
                      <Badge
                        variant={
                          msg.type === 'consensus'
                            ? 'success'
                            : msg.type === 'claim'
                            ? 'destructive'
                            : 'secondary'
                        }
                        className="text-[9px] py-0 uppercase"
                      >
                        {msg.type}
                      </Badge>
                    </div>
                    <span className="text-slate-500 text-[10px]">{msg.timestamp}</span>
                  </div>

                  <p className="mt-1 font-sans">{msg.content}</p>

                  {msg.fileContext && (
                    <div className="mt-2 text-[10px] font-mono text-slate-400 flex items-center gap-1 bg-black/40 px-2 py-1 rounded w-fit border border-slate-800/60">
                      <span>Context:</span>
                      <span className="text-sky-300">{msg.fileContext}</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Interactive human intervention prompt */}
          <form onSubmit={handleSendPrompt} className="pt-2 flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask the agents a question or provide context to steer consensus (e.g. 'Is this endpoint protected by API gateway rate limiting?')..."
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
