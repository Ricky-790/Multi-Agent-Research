import React from "react";

interface StatusDotProps {
  status: string | null | undefined;
  className?: string;
}

// Visual treatment for report status indicators:
//   - in-progress states (pending, planning, researching, synthesizing, null)
//     -> amber pulse
//   - done -> sage/secondary (no pulse)
//   - failed -> terracotta/error
export const StatusDot: React.FC<StatusDotProps> = ({ status, className = "" }) => {
  const normalized = (status || "").toLowerCase();
  let color = "bg-primary";
  let pulse = true;

  if (normalized === "done" || normalized === "completed") {
    color = "bg-secondary";
    pulse = false;
  } else if (normalized === "failed") {
    color = "bg-error";
    pulse = false;
  }

  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${color} ${
        pulse ? "animate-status-pulse" : ""
      } ${className}`}
    />
  );
};
