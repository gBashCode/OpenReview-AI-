import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../services/healthApi';
import { Badge } from '../ui/badge';
import { Link, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Activity,
  Zap,
  Bell,
  Search,
  ExternalLink,
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
        <Badge variant="outline" className="animate-pulse flex items-center gap-1.5 py-0.5">
          <Activity className="w-3 h-3 text-[#8a8378]" />
          <span>Syncing...</span>
        </Badge>
      );
    }
    if (health?.status === 'healthy') {
      return (
        <Badge variant="success" className="flex items-center gap-1.5 py-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#5a9e6f] animate-pulse" />
          <span>Engine Online</span>
        </Badge>
      );
    }
    if (health?.status === 'degraded') {
      return (
        <Badge variant="warning" className="flex items-center gap-1.5 py-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#e29b38]" />
          <span>Local Engine (SQLite)</span>
        </Badge>
      );
    }
    return (
      <Badge variant="destructive" className="flex items-center gap-1.5 py-0.5">
        <span className="w-1.5 h-1.5 rounded-full bg-[#c75a4a]" />
        <span>Offline</span>
      </Badge>
    );
  };

  return (
    <header className="sticky top-0 z-40 border-b border-[#26221c] bg-[#12100d]/95 backdrop-blur-md px-6 py-2.5 flex items-center justify-between">
      {/* Left: Brand & Editorial Wordmark */}
      <div className="flex items-center gap-7">
        <Link to="/dashboard" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded-[2px] bg-[#1d1a15] border border-[#d4a853]/40 flex items-center justify-center shadow-sm group-hover:border-[#d4a853] transition-colors">
            <span className="font-serif italic text-base text-[#d4a853] font-bold">O</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-serif text-xl text-[#f5f0e6] tracking-tight group-hover:text-[#d4a853] transition-colors">
              OpenReview
            </span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-[2px] font-mono font-medium tracking-widest bg-[#221f1a] text-[#d4a853] border border-[#38332a]">
              AI
            </span>
          </div>
        </Link>

        {/* Global Quick Search - Editorial Ledger Style */}
        <div
          onClick={() => info('Command Palette', 'Type ⌘K anytime to jump between repositories, PRs, and review rules.')}
          className="hidden md:flex items-center gap-2.5 px-3 py-1.5 rounded-[2px] border border-[#26221c] bg-[#171512] text-[#8a8378] text-xs cursor-pointer hover:border-[#3d372e] hover:text-[#d8d2c4] transition"
        >
          <Search className="w-3.5 h-3.5 text-[#6a6358]" />
          <span className="font-mono text-[11px]">Search PRs, repos, AST rules...</span>
          <kbd className="ml-4 font-mono text-[10px] px-1.5 py-0.5 rounded-[2px] bg-[#221f1a] text-[#a69e90] border border-[#2f2a23]">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Right Action Icons & Status */}
      <div className="flex items-center gap-3.5">
        {getStatusBadge()}

        {/* Public Landing Link */}
        <Link
          to="/landing"
          className="hidden sm:flex items-center gap-1.5 text-xs text-[#8a8378] hover:text-[#f5f0e6] px-2.5 py-1.5 rounded-[2px] hover:bg-[#1d1a15] transition"
        >
          <ExternalLink className="w-3.5 h-3.5 text-[#d4a853]" />
          <span className="font-mono text-[11px]">Product Tour</span>
        </Link>

        {/* API Docs link */}
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          className="hidden sm:flex items-center gap-1.5 text-xs text-[#8a8378] hover:text-[#f5f0e6] px-2.5 py-1.5 rounded-[2px] hover:bg-[#1d1a15] transition"
        >
          <Zap className="w-3.5 h-3.5 text-[#3a9e8f]" />
          <span className="font-mono text-[11px]">API Docs</span>
        </a>

        {/* Notifications Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-[2px] text-[#8a8378] hover:text-[#f5f0e6] hover:bg-[#1d1a15] transition"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-[#d4a853] ring-2 ring-[#12100d]" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-[3px] border border-[#36312a] bg-[#161411] p-4 shadow-2xl shadow-black/90 z-50 text-xs animate-in fade-in duration-100">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#24201a]">
                <span className="font-serif text-sm text-[#f5f0e6]">Review Alerts</span>
                <span className="text-[10px] text-[#d4a853] font-mono">2 unread</span>
              </div>
              <div className="space-y-2.5">
                <div
                  onClick={() => {
                    navigate('/autofix');
                    setShowNotifications(false);
                  }}
                  className="p-2.5 rounded-[2px] bg-[#1c1a16] border border-[#2e2a24] hover:border-[#d4a853]/40 cursor-pointer transition"
                >
                  <div className="flex items-center gap-1.5 text-[#e06c5b] font-medium text-[11px]">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Critical CVE-89 Detected</span>
                  </div>
                  <p className="text-[#a69e90] mt-1 text-[11px] leading-relaxed">
                    PR #42 in openreview-ai has an automated patch verified by sandbox.
                  </p>
                </div>

                <div
                  onClick={() => {
                    navigate('/agents');
                    setShowNotifications(false);
                  }}
                  className="p-2.5 rounded-[2px] bg-[#1c1a16] border border-[#2e2a24] hover:border-[#3a9e8f]/40 cursor-pointer transition"
                >
                  <div className="flex items-center gap-1.5 text-[#6cb582] font-medium text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Agent Consensus Reached</span>
                  </div>
                  <p className="text-[#a69e90] mt-1 text-[11px] leading-relaxed">
                    Arbiter approved findings on commit 7f9a1b2 across 5 agents.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-[#26221c]" />

        {/* User Account / Profile */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1 pl-2 rounded-[2px] border border-[#2a2621] bg-[#171512] hover:border-[#3d372e] transition"
          >
            <div className="w-5 h-5 rounded-[2px] bg-[#2a241b] border border-[#d4a853]/40 flex items-center justify-center text-[10px] font-mono text-[#d4a853] font-bold">
              {(user?.full_name || user?.email || 'OR').slice(0, 2).toUpperCase()}
            </div>
            <span className="text-xs text-[#d8d2c4] font-medium hidden sm:inline">{user?.full_name || 'Lead Architect'}</span>
            <ChevronDown className="w-3 h-3 text-[#6a6358]" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-48 rounded-[3px] border border-[#36312a] bg-[#161411] p-2 shadow-2xl shadow-black/90 z-50 text-xs animate-in fade-in duration-100">
              <div className="px-2 py-1.5 border-b border-[#24201a] mb-1">
                <div className="font-medium text-[#f5f0e6]">{user?.full_name || 'Lead Architect'}</div>
                <div className="text-[10px] text-[#8a8378] font-mono truncate">{user?.email || 'architect@openreview.ai'}</div>
              </div>
              <button
                onClick={() => {
                  navigate('/settings');
                  setShowUserMenu(false);
                }}
                className="w-full text-left px-2 py-1.5 rounded-[2px] hover:bg-[#201d19] text-[#b8b0a2] hover:text-[#f5f0e6] flex items-center gap-2"
              >
                <User className="w-3.5 h-3.5 text-[#8a8378]" />
                <span>Account Profile</span>
              </button>
              <button
                onClick={() => {
                  logout();
                  setShowUserMenu(false);
                  success('Logged Out', 'Returned to sign-in portal.');
                  navigate('/login');
                }}
                className="w-full text-left px-2 py-1.5 rounded-[2px] hover:bg-[#c75a4a]/10 text-[#e06c5b] flex items-center gap-2"
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
