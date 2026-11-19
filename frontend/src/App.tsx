import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ToastProvider } from './components/ui/toast';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import { GlobalVideoBackground } from './components/layout/GlobalVideoBackground';

// 16 Full Application Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { AuthCallback } from './pages/AuthCallback';
import { Dashboard } from './pages/Dashboard';
import { Repositories } from './pages/Repositories';
import { RepositoryDetail } from './pages/RepositoryDetail';
import { PullRequests } from './pages/PullRequests';
import { ReviewDetail } from './pages/ReviewDetail';
import { AgentConference } from './pages/AgentConference';
import { SecurityReports } from './pages/SecurityReports';
import { PerformanceReports } from './pages/PerformanceReports';
import { AutoFix } from './pages/AutoFix';
import { ReviewHistory } from './pages/ReviewHistory';
import { TeamManagement } from './pages/TeamManagement';
import { Settings } from './pages/Settings';
import { AIModelConfig } from './pages/AIModelConfig';
import { UsageAnalytics } from './pages/UsageAnalytics';
import { NotFound } from './pages/NotFound';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5000,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <div className="relative min-h-screen w-full bg-[#000000] text-[#d8d2c4] overflow-x-hidden">
            {/* Cinematic Looping Video Background (Global) */}
            <GlobalVideoBackground />

            {/* Application Views & Router Layer */}
            <div className="relative z-10 min-h-screen flex flex-col">
              <BrowserRouter>
                <Routes>
                  {/* Public Marketing & Auth Pages */}
                  <Route path="/landing" element={<Landing />} />
                  <Route path="/login" element={<Login />} />
                  <Route path="/auth/callback" element={<AuthCallback />} />

                  {/* Authenticated Dashboard Application Shell */}
                  <Route element={<AppLayout />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/repositories" element={<Repositories />} />
                    <Route path="/repositories/:id" element={<RepositoryDetail />} />
                    <Route path="/pull-requests" element={<PullRequests />} />
                    <Route path="/reviews/:id" element={<ReviewDetail />} />
                    <Route path="/agents" element={<AgentConference />} />
                    <Route path="/security" element={<SecurityReports />} />
                    <Route path="/performance" element={<PerformanceReports />} />
                    <Route path="/autofix" element={<AutoFix />} />
                    <Route path="/history" element={<ReviewHistory />} />
                    <Route path="/team" element={<TeamManagement />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/models" element={<AIModelConfig />} />
                    <Route path="/analytics" element={<UsageAnalytics />} />
                    <Route path="*" element={<NotFound />} />
                  </Route>
                </Routes>
              </BrowserRouter>
            </div>
          </div>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
};

export default App;
