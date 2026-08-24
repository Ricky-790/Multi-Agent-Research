import React from "react";

// Maps a backend status string to one of our 4 stepper phases.
// Returns the *index* of the active step (0..3), where 3 = done.
// If unknown, returns -1 (no step shown active).
export const STEP_PHASES = ["planning", "researching", "synthesizing", "done"];

export function statusToStepIndex(
  status: string | null | undefined,
): number {
  const s = (status || "").toLowerCase();
  if (s === "pending") return -1;
  if (s === "planning") return 0;
  if (s === "researching" || s === "research") return 1;
  if (s === "synthesizing" || s === "synthesis") return 2;
  if (s === "done" || s === "completed") return 3;
  if (s === "failed") return -1;
  return -1;
}

interface StepperProps {
  activeIndex: number; // 0..3
}

// Visual treatment matches the in_progress reference:
//  - connecting line fills from 0 up to activeIndex
//  - active step = primary-container filled circle with pulse
//  - completed steps = check icon, secondary container
//  - pending steps = hollow outline circle, dim text
export const Stepper: React.FC<StepperProps> = ({ activeIndex }) => {
  const labels = ["Planning", "Researching", "Synthesizing", "Done"];
  const total = labels.length;
  // Active line covers up to the center of the current step circle.
  // Step centers are at (i + 0.5) / total fraction of width.
  const lineWidthPercent =
    activeIndex >= 0
      ? Math.max(0, Math.min(100, ((activeIndex + 0.5) / total) * 100))
      : 0;

  return (
    <section className="max-w-2xl mx-auto w-full mb-16 px-4">
      <div className="relative flex items-center justify-between">
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-[1px] bg-outline-variant z-0"></div>
        <div
          className="absolute left-0 top-1/2 -translate-y-1/2 h-[1px] bg-primary z-0 transition-all duration-1000"
          style={{ width: `${lineWidthPercent}%` }}
        ></div>

        {labels.map((label, i) => {
          const isCompleted = activeIndex > i;
          const isActive = activeIndex === i;
          return (
            <div
              key={label}
              className="relative z-10 flex flex-col items-center gap-3 bg-background px-2"
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center ${
                  isCompleted
                    ? "bg-surface-container-highest border border-outline-variant text-on-surface-variant"
                    : isActive
                      ? "bg-primary-container border border-primary text-on-primary-container shadow-glow-primary animate-status-pulse"
                      : "bg-surface border border-outline-variant"
                }`}
              >
                {isCompleted ? (
                  <span className="material-symbols-outlined text-[14px]">
                    check
                  </span>
                ) : isActive ? (
                  <span className="w-2 h-2 rounded-full bg-on-primary-container"></span>
                ) : null}
              </div>
              <span
                className={`font-label-sm text-label-sm uppercase tracking-widest ${
                  isActive
                    ? "text-primary font-semibold"
                    : "text-on-surface-variant"
                }`}
                style={{ opacity: isActive ? 1 : isCompleted ? 0.7 : 0.4 }}
              >
                {label}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
};
