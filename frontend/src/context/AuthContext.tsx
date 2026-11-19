import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '../types/auth';
import { authApi } from '../services/authApi';
import { getAuthToken, setAuthToken } from '../services/apiClient';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  loginWithGitHub: () => Promise<void>;
  loginWithDemo: () => Promise<void>;
  handleOAuthCallback: (tokenOrCode: { token?: string; code?: string }) => Promise<User>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken();
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const currentUser = await authApi.getMe();
        setUser(currentUser);
      } catch (err) {
        setAuthToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const res = await authApi.login(email, password);
    setUser(res.user);
  };

  const loginWithGitHub = async () => {
    // Calling without redirect_uri allows GitHub to use the Callback URL configured on the GitHub App
    const res = await authApi.getGitHubOAuthUrl();
    if (res?.url) {
      window.location.href = res.url;
    }
  };

  const handleOAuthCallback = async ({ token, code }: { token?: string; code?: string }): Promise<User> => {
    if (token) {
      setAuthToken(token);
      const currentUser = await authApi.getMe();
      setUser(currentUser);
      return currentUser;
    } else if (code) {
      const res = await authApi.exchangeGitHubCode(code);
      setUser(res.user);
      return res.user;
    }
    throw new Error('No authorization token or code provided');
  };

  const loginWithDemo = async () => {
    try {
      // Attempt login with standard demo account
      const res = await authApi.login('architect@openreview.ai', 'OpenReview2026!');
      setUser(res.user);
    } catch {
      // If demo account does not exist in local DB, register it with username
      const regRes = await authApi.register(
        'architect@openreview.ai',
        'OpenReview2026!',
        'Lead Architect',
        'OpenReview Engineering',
        'architect'
      );
      setUser(regRes.user);
    }
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        loginWithGitHub,
        loginWithDemo,
        handleOAuthCallback,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
