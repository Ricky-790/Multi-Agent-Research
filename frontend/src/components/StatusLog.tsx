import React, { useEffect, useRef } from "react";

export interface LogEntry {
  id: number;
  text: string;
  spinning?: boolean;
}

interface StatusLogProps {
  entries: LogEntry[];
}

// Quiet status log — newest entries push older ones upward and fade out the
// top with a gradient mask, matching the in_progress reference.
export const StatusLog: React.FC<StatusLogProps> = ({ entries }) => {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Keep the latest entry in view at the bottom.
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [entries]);

  return (
    <section className="max-w-2xl mx-auto w-full mt-auto mb-margin-desktop md:mb-section-gap border-t border-outline-variant pt-8">
      <div
        ref={containerRef}
        className="relative font-mono-ui text-mono-ui text-on-surface-variant space-y-2 h-[120px] overflow-hidden flex flex-col justify-end"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-background to-transparent h-12 z-10 pointer-events-none" />
        {entries.map((e, idx) => {
          // Older entries fade out more.
          const opacity = Math.min(1, 0.4 + (idx / Math.max(entries.length - 1, 1)) * 0.6);
          return (
            <div
              key={e.id}
              className="flex items-center gap-2"
              style={{ opacity }}
            >
              {e.spinning && (
                <span className="material-symbols-outlined text-[14px] animate-status-pulse">
                  sync
                </span>
              )}
              <span>&gt; {e.text}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
};
