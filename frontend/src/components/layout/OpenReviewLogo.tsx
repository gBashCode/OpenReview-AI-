import React from 'react';

interface OpenReviewLogoProps {
  className?: string;
  size?: number;
}

/**
 * OpenReviewLogo
 *
 * Distinctive, animated geometric vector emblem for OpenReview AI:
 * - Outer continuous slow-rotating celestial review radar ring.
 * - Dual gold aperture arcs representing multi-agent consensus validation.
 * - Converging code brackets (< >) forming the stylized central "O".
 * - Inner pulsing neural core with an animated focal spark.
 * - Accelerates and expands smoothly on container hover.
 */
export const OpenReviewLogo: React.FC<OpenReviewLogoProps> = ({
  className = '',
  size = 36,
}) => {
  return (
    <div
      className={`relative flex items-center justify-center rounded-full bg-[rgba(224,176,74,0.14)] border-[1.5px] border-[#e0b04a] shadow-[0_0_12px_rgba(224,176,74,0.2)] group-hover:border-[#fae29c] group-hover:shadow-[0_0_20px_rgba(224,176,74,0.45)] transition-all duration-500 shrink-0 ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full p-1 transform transition-transform duration-700 ease-out group-hover:rotate-[360deg] group-hover:scale-105"
      >
        <defs>
          {/* Radiant Gold Gradients */}
          <linearGradient id="or-gold-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fae29c" />
            <stop offset="45%" stopColor="#e0b04a" />
            <stop offset="100%" stopColor="#b38222" />
          </linearGradient>

          <linearGradient id="or-bracket-grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#fae29c" />
          </linearGradient>

          <filter id="or-soft-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* 1. Orbiting Outer Radar Ring (Continuous Smooth Rotation) */}
        <g style={{ transformOrigin: '50px 50px' }} className="animate-[spin_12s_linear_infinite]">
          <circle
            cx="50"
            cy="50"
            r="41"
            stroke="url(#or-gold-grad)"
            strokeWidth="1.75"
            strokeDasharray="14 9 4 9"
            opacity="0.65"
          />
        </g>

        {/* 2. Top-Right and Bottom-Left Aperture Arcs */}
        <path
          d="M 50 17 A 33 33 0 0 1 83 50"
          stroke="url(#or-gold-grad)"
          strokeWidth="3.25"
          strokeLinecap="round"
          filter="url(#or-soft-glow)"
        />
        <path
          d="M 50 83 A 33 33 0 0 1 17 50"
          stroke="url(#or-gold-grad)"
          strokeWidth="3.25"
          strokeLinecap="round"
          filter="url(#or-soft-glow)"
        />

        {/* 3. Code Brackets forming Stylized 'O' */}
        <path
          d="M 39 36 L 29 50 L 39 64"
          stroke="url(#or-bracket-grad)"
          strokeWidth="3.25"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M 61 36 L 71 50 L 61 64"
          stroke="url(#or-bracket-grad)"
          strokeWidth="3.25"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* 4. Central Multi-Agent Neural Spark (Pulsing Diamond) */}
        <g style={{ transformOrigin: '50px 50px' }} className="animate-pulse">
          <path
            d="M 50 37 L 53.5 46.5 L 63 50 L 53.5 53.5 L 50 63 L 46.5 53.5 L 37 50 L 46.5 46.5 Z"
            fill="url(#or-gold-grad)"
            filter="url(#or-soft-glow)"
          />
        </g>

        {/* Glowing Center Core */}
        <circle cx="50" cy="50" r="2.5" fill="#ffffff" className="animate-ping opacity-75" style={{ transformOrigin: '50px 50px' }} />
        <circle cx="50" cy="50" r="2" fill="#ffffff" />
      </svg>
    </div>
  );
};
