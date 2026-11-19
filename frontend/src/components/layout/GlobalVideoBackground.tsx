import React, { useState, useEffect, useRef } from 'react';

const VIDEO_URL =
  'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260328_105406_16f4600d-7a92-4292-b96e-b19156c7830a.mp4';

interface GlobalVideoBackgroundProps {
  /** Optional custom overlay class name (defaults to 80% black) */
  overlayClassName?: string;
}

/**
 * GlobalVideoBackground
 *
 * Cinematic, full-screen looping video background for OpenReview AI.
 * Plays the official background video smoothly behind all application routes,
 * styled with a deep dark overlay (75-85% black) to preserve UI contrast,
 * text readability, and the signature black-and-gold aesthetic.
 */
export const GlobalVideoBackground: React.FC<GlobalVideoBackgroundProps> = ({
  overlayClassName = 'bg-black/80',
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [hasError, setHasError] = useState(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Respect user reduced motion accessibility preferences
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const handleMotionChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleMotionChange);
    return () => mediaQuery.removeEventListener('change', handleMotionChange);
  }, []);

  useEffect(() => {
    const video = videoRef.current;
    if (video && !prefersReducedMotion && !hasError) {
      video.play().catch(() => {
        // Autoplay policy fallback: muted video keeps waiting or playing inline
      });
    }
  }, [prefersReducedMotion, hasError]);

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 w-full h-full overflow-hidden pointer-events-none select-none z-0 bg-[#000000]"
    >
      {/* Looping Cinematic Video */}
      {!hasError && !prefersReducedMotion && (
        <video
          ref={videoRef}
          autoPlay
          loop
          muted
          playsInline
          preload="auto"
          onError={() => setHasError(true)}
          className="absolute inset-0 w-full h-full object-cover object-center transform-gpu will-change-transform"
        >
          <source src={VIDEO_URL} type="video/mp4" />
        </video>
      )}

      {/* Primary Dark Black Overlay (75-85% black) */}
      <div className={`absolute inset-0 ${overlayClassName} pointer-events-none`} />

      {/* Subtle cinematic vignette for enhanced depth and readability */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/40 pointer-events-none" />
    </div>
  );
};

export default GlobalVideoBackground;
