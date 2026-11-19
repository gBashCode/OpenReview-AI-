import React, { useEffect, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/toast';
import { Github, Loader2 } from 'lucide-react';

export const AuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { handleOAuthCallback } = useAuth();
  const { success, error } = useToast();
  const processedRef = useRef(false);

  useEffect(() => {
    if (processedRef.current) return;
    processedRef.current = true;

    const token = searchParams.get('token');
    const code = searchParams.get('code');
    const err = searchParams.get('error');
    const errDesc = searchParams.get('error_description');

    if (err) {
      error('GitHub Authentication Failed', errDesc || err);
      navigate('/login');
      return;
    }

    if (!token && !code) {
      error('Authentication Error', 'No authorization code or token received from GitHub.');
      navigate('/login');
      return;
    }

    const processAuth = async () => {
      try {
        const user = await handleOAuthCallback({
          token: token || undefined,
          code: code || undefined,
        });
        success(
          'GitHub Authentication Successful',
          `Welcome back, ${user.full_name || user.username}!`
        );
        navigate('/dashboard');
      } catch (e: any) {
        error(
          'Authentication Failed',
          e.message || 'Could not complete GitHub OAuth verification.'
        );
        navigate('/login');
      }
    };

    processAuth();
  }, [searchParams, handleOAuthCallback, navigate, success, error]);

  return (
    <div className="min-h-screen bg-[#0e0d0b] flex flex-col justify-center items-center p-6 selection:bg-[#d4a853]/25 selection:text-[#f5f0e6]">
      <div className="w-full max-w-sm text-center space-y-4 animate-in fade-in duration-300">
        <div className="w-14 h-14 mx-auto rounded-[3px] bg-[#1a1814] border border-[#d4a853]/40 flex items-center justify-center shadow-lg">
          <Github className="w-7 h-7 text-[#f4efe6] animate-pulse" />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-xl font-serif text-[#f4efe6]">
            Authenticating with GitHub
          </h2>
          <p className="text-xs font-mono text-[#8c8273]">
            Exchanging secure credentials and establishing your session...
          </p>
        </div>
        <div className="flex justify-center pt-2">
          <Loader2 className="w-5 h-5 text-[#d4a853] animate-spin" />
        </div>
      </div>
    </div>
  );
};
