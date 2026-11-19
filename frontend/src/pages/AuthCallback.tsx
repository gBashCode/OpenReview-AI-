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

  const provider = (searchParams.get('provider') as 'github' | 'google') || 'github';
  const providerLabel = provider === 'google' ? 'Google' : 'GitHub';

  useEffect(() => {
    if (processedRef.current) return;
    processedRef.current = true;

    const token = searchParams.get('token');
    const code = searchParams.get('code');
    const err = searchParams.get('error');
    const errDesc = searchParams.get('error_description');

    if (err) {
      error(`${providerLabel} Authentication Failed`, errDesc || err);
      navigate('/login');
      return;
    }

    if (!token && !code) {
      error('Authentication Error', `No authorization code or token received from ${providerLabel}.`);
      navigate('/login');
      return;
    }

    const processAuth = async () => {
      try {
        const user = await handleOAuthCallback({
          token: token || undefined,
          code: code || undefined,
          provider,
        });
        success(
          `${providerLabel} Authentication Successful`,
          `Welcome back, ${user.full_name || user.username}!`
        );
        navigate('/dashboard');
      } catch (e: any) {
        error(
          'Authentication Failed',
          e.message || `Could not complete ${providerLabel} OAuth verification.`
        );
        navigate('/login');
      }
    };

    processAuth();
  }, [searchParams, handleOAuthCallback, navigate, success, error, provider, providerLabel]);

  return (
    <div className="min-h-screen bg-transparent flex flex-col justify-center items-center p-6 selection:bg-[#d4a853]/25 selection:text-[#f5f0e6]">
      <div className="w-full max-w-sm text-center space-y-4 animate-in fade-in duration-300">
        <div className="w-14 h-14 mx-auto rounded-[3px] bg-[#1a1814] border border-[#d4a853]/40 flex items-center justify-center shadow-lg">
          {provider === 'google' ? (
            <svg className="w-7 h-7" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"
              />
              <path
                fill="#34A853"
                d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"
              />
              <path
                fill="#FBBC05"
                d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 9.99 0 12s.45 3.82 1.25 5.42l4.03-3.15z"
              />
              <path
                fill="#EA4335"
                d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
              />
            </svg>
          ) : (
            <Github className="w-7 h-7 text-[#f4efe6] animate-pulse" />
          )}
        </div>
        <div className="space-y-1.5">
          <h2 className="text-xl font-serif text-[#f4efe6]">
            Authenticating with {providerLabel}
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
