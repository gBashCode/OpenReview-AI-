import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../services/healthApi';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Activity,
  Github,
  Zap,
  Bell,
  Search,
  ExternalLink,
  Sparkles,
  User,
  LogOut,
  ChevronDown,
  CheckCircle2,
} from 'lucide-react';
import { useToast } from '../ui/toast';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { info, success } = useToast();
  const { user, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const { data: health, isLoading } = useQuery({
    queryKey: ['system-health'],
    queryFn: healthApi.getHealth,
    refetchInterval: 15000,
  });

  const getStatusBadge = () => {
    if (isLoading) {
      return (
        <Badge variant="outline" className="animate-pulse flex items-center gap-1.5 py-1">
          <Activity className="w-3 h-3 text-slate-400" />
          <span>Verifying...</span>
        </Badge>
      );
    }
    if (health?.status === 'healthy') {
      return (
        <Badge variant="success" className="flex items-center gap-1.5 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Engine Healthy</span>
        </Badge>
      );
    }
    if (health?.status === 'degraded') {
      return (
        <Badge variant="warning" className="flex items-center gap-1.5 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          <span>Local Engine (Degraded)</span>
        </Badge>
      );
    }
    return (
      <Badge variant="destructive" className="flex items-center gap-1.5 py-1">
        <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
        <span>Offline</span>
      </Badge>
    );
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-[#090d16]/95 backdrop-blur-md px-6 py-2.5 flex items-center justify-between">
      {/* Left: Brand & Breadcrumb */}
      <div className="flex items-center gap-6">
        <Link to="/dashboard" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-sky-500/20 group-hover:scale-105 transition-transform">
            <ShieldCheck className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-base text-white tracking-tight">OpenReview</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                AI
              </span>
            </div>
          </div>
        </Link>

        {/* Global Quick Search Mock Trigger */}
        <div
          onClick={() => info('Command Palette', 'Type ⌘K anytime to jump between repositories, PRs, and rules.')}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-[#0e1422] text-slate-400 text-xs cursor-pointer hover:border-slate-700 hover:text-slate-200 transition"
        >
          <Search className="w-3.5 h-3.5 text-slate-500" />
          <span>Search PRs, repos, security rules...</span>
          <kbd className="ml-4 font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right Action Icons & Status */}
      <div className="flex items-center gap-3">
        {/* Real Backend Health Status Indicator */}
        {getStatusBadge()}

        {/* Public Landing Link */}
        <Link
          to="/landing"
          className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-md hover:bg-slate-800/60 transition"
        >
          <ExternalLink className="w-3.5 h-3.5 text-purple-400" />
          <span>Product Tour</span>
        </Link>

        {/* API Docs link */}
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 hover:text-white px-2.5 py-1.5 rounded-md hover:bg-slate-800/60 transition"
        >
          <Zap className="w-3.5 h-3.5 text-amber-400" />
          <span>API Docs</span>
        </a>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-sky-400 ring-2 ring-[#090d16]" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl border border-slate-800 bg-[#0e1422] p-4 shadow-2xl shadow-black/80 z-50 text-xs animate-in fade-in duration-100">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
                <span className="font-semibold text-white">Review Alerts</span>
                <span className="text-[10px] text-sky-400 font-mono">2 unread</span>
              </div>
              <div className="space-y-2.5">
                <div
                  onClick={() => {
                    navigate('/autofix');
                    setShowNotifications(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 cursor-pointer transition"
                >
                  <div className="flex items-center gap-1.5 text-rose-400 font-semibold text-[11px]">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Critical CVE-89 Detected</span>
                  </div>
                  <p className="text-slate-300 mt-0.5 text-[11px]">
                    PR #42 in openreview-ai has an automated patch ready for review.
                  </p>
                </div>

                <div
                  onClick={() => {
                    navigate('/agents');
                    setShowNotifications(false);
                  }}
                  className="p-2 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 cursor-pointer transition"
                >
                  <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Agent Consensus Complete</span>
                  </div>
                  <p className="text-slate-300 mt-0.5 text-[11px]">
                    Multi-agent review pass passed on commit 7f9a1b2.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-slate-800" />

        {/* User Account / Demo Profile */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1 pl-2 rounded-lg border border-slate-800 bg-[#0e1422] hover:border-slate-700 transition"
          >
            <div className="w-5 h-5 rounded-full bg-gradient-to-r from-sky-400 to-indigo-500 flex items-center justify-center text-[10px] font-bold text-slate-950 font-mono">
              {(user?.full_name || user?.email || 'OR').slice(0, 2).toUpperCase()}
            </div>
            <span className="text-xs text-slate-200 font-medium hidden sm:inline">{user?.full_name || 'Lead Architect'}</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 rounded-xl border border-slate-800 bg-[#0e1422] p-2 shadow-2xl shadow-black/80 z-50 text-xs animate-in fade-in duration-100">
              <div className="px-2 py-1.5 border-b border-slate-800 mb-1">
                <div className="font-semibold text-white">{user?.full_name || 'Lead Architect'}</div>
                <div className="text-[10px] text-slate-400 font-mono truncate">{user?.email || 'architect@openreview.ai'}</div>
              </div>
              <button
                onClick={() => {
                  navigate('/settings');
                  setShowUserMenu(false);
                }}
                className="w-full text-left px-2 py-1.5 rounded hover:bg-slate-800/80 text-slate-300 flex items-center gap-2"
              >
                <User className="w-3.5 h-3.5 text-slate-400" />
                <span>Account Profile</span>
              </button>
              <button
                onClick={() => {
                  logout();
                  setShowUserMenu(false);
                  success('Logged Out', 'Returned to sign-in portal.');
                  navigate('/login');
                }}
                className="w-full text-left px-2 py-1.5 rounded hover:bg-rose-500/10 text-rose-400 flex items-center gap-2"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
