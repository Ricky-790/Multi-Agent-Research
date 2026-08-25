import React from "react";

// Inline SVG logo. Matches the wordmark used across the design references —
// dark amber primary color, "Spectator" logotype with an eye glyph on the right.
export const SpectatorLogo: React.FC<{ className?: string; alt?: string }> = ({
  className = "h-8 w-auto",
  alt = "Spectator",
}) => (
  <svg
    viewBox="0 0 220 40"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    role="img"
    aria-label={alt}
  >
    <text
      x="110"
      y="29"
      fill="#f7bf59"
      fontFamily='"Source Serif 4", Georgia, serif'
      fontSize="28"
      fontWeight="600"
      letterSpacing="-0.5"
      textAnchor="middle"
    >
      Spectator
    </text>
    {/* Eye glyph */}
  </svg>
);
