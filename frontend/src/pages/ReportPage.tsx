import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiRequest, ApiError } from "../lib/api";
import { WS_BASE_URL } from "../config";
import { AppShell } from "../components/AppShell";
import { Stepper, statusToStepIndex, STEP_PHASES } from "../components/Stepper";
import { StatusLog } from "../components/StatusLog";
import type { LogEntry } from "../components/StatusLog";

interface CompletedReport {
  report_id: string;
  goal: string;
  intent: string | null;
  categories: string[] | null;
  strategy_summary: string | null;
  title: string | null;
  content: string | null;
  created_at: string;
  updated_at: string;
}

interface InProgressReport {
  report_id: string;
  status: string;
}

type ReportData =
  | { kind: "completed"; data: CompletedReport }
  | { kind: "in_progress"; data: InProgressReport }
  | { kind: "failed" }
  | { kind: "loading" }
  | { kind: "error"; message: string };

interface WsMessage {
  phase?: string;
  status?: string;
  done?: boolean;
}

let logIdCounter = 1;

export const ReportPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const { token } = useAuth();

  const [state, setState] = useState<ReportData>({ kind: "loading" });
  const [activeStep, setActiveStep] = useState<number>(-1);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [wsError, setWsError] = useState<string | null>(null);
  const [originalQuery, setOriginalQuery] = useState<string>("");
  const wsRef = useRef<WebSocket | null>(null);
  const doneRef = useRef(false);

  const appendLog = useCallback(
    (text: string, spinning = false) => {
      setLogs((prev) => {
        const next = [...prev, { id: logIdCounter++, text, spinning }];
        // Keep the log bounded so it doesn't grow forever.
        return next.slice(-50);
      });
    },
    [],
  );

  const refresh = useCallback(
    async (isWebSocketDriven = false) => {
      if (!reportId || !token) return;
      try {
        const data = await apiRequest(`/reports/report/${reportId}`, { token });
        const hasContent = data && Object.prototype.hasOwnProperty.call(data, "content");

        if (!hasContent) {
          const ip = data as InProgressReport;
          const idx = statusToStepIndex(ip.status);
          setActiveStep(idx >= 0 ? idx : 0);
          setState({ kind: "in_progress", data: ip });
          if (!isWebSocketDriven) {
            appendLog(`Current status: ${ip.status || "pending"}.`);
          }
        } else {
          const comp = data as CompletedReport;
          if (comp.content != null) {
            setOriginalQuery(comp.goal || "");
            setState({ kind: "completed", data: comp });
          } else {
            // Shape B with null content — treat as still in-progress.
            setState({ kind: "in_progress", data: { report_id: comp.report_id, status: "synthesizing" } });
            setActiveStep(statusToStepIndex("synthesizing"));
          }
        }
      } catch (err) {
        if (err instanceof ApiError) {
          setState({ kind: "error", message: err.message });
        } else {
          setState({ kind: "error", message: "Failed to load report." });
        }
      }
    },
    [reportId, token, appendLog],
  );

  // Open WebSocket while in-progress.
  useEffect(() => {
    doneRef.current = false;
    setWsError(null);

    // Always do an initial load on mount / reportId change.
    refresh(false);

    return () => {
      doneRef.current = true;
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          /* noop */
        }
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reportId, token]);

  // Connect WS when we know the report is in progress.
  useEffect(() => {
    if (state.kind !== "in_progress") return;
    if (!reportId || !token) return;
    if (wsRef.current) return; // already connected

    const url = `${WS_BASE_URL}/ws/${reportId}?token=${encodeURIComponent(token)}`;
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch (err) {
      setWsError("Failed to connect to live updates.");
      return;
    }
    wsRef.current = ws;

    ws.onopen = () => {
      setWsError(null);
      appendLog("Live updates connected.");
    };

    ws.onmessage = (ev) => {
      let msg: WsMessage;
      try {
        msg = JSON.parse(ev.data);
      } catch {
        return;
      }
      const phase = (msg.phase || "").toLowerCase();
      const status = (msg.status || "").toLowerCase();
      const done = !!msg.done;

      // Advance stepper based on phase.
      if (phase === "planning") {
        setActiveStep(0);
        appendLog(`Planning ${status || "started"}…`);
      } else if (phase === "research" || phase === "researching") {
        setActiveStep(1);
        appendLog(`Research ${status || "running"}…`);
      } else if (phase === "synthesis" || phase === "synthesizing") {
        setActiveStep(2);
        appendLog(`Synthesis ${status || "running"}…`);
      } else if (phase === "done") {
        setActiveStep(3);
        appendLog(`Done.`);
      } else if (phase === "failed") {
        appendLog(`Failed: ${status || "unknown error"}.`);
      } else if (status) {
        // Generic status update — append as log entry.
        appendLog(status);
      }

      if (done) {
        if (wsRef.current) {
          try {
            wsRef.current.close();
          } catch {
            /* noop */
          }
          wsRef.current = null;
        }
        if (phase === "failed") {
          setState({ kind: "failed" });
        } else {
          // Re-fetch to get completed content.
          refresh(true).then(() => {
            /* state updated by refresh */
          });
        }
      }
    };

    ws.onerror = () => {
      if (!doneRef.current) {
        setWsError("Live updates unavailable. Refresh to retry.");
      }
    };

    ws.onclose = () => {
      if (wsRef.current === ws) wsRef.current = null;
    };

    return () => {
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch {
          /* noop */
        }
        wsRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.kind, reportId, token]);

  if (state.kind === "loading") {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-full">
          <p className="font-body-lg text-body-lg text-on-surface-variant opacity-60">
            Loading report…
          </p>
        </div>
      </AppShell>
    );
  }

  if (state.kind === "error") {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-full p-8">
          <div className="text-center max-w-md">
            <p className="font-headline-md text-headline-md text-error mb-4">
              Could not load report
            </p>
            <p className="font-body-md text-body-md text-on-surface-variant mb-6">
              {state.message}
            </p>
            <button
              onClick={() => refresh(false)}
              className="bg-primary-container text-on-primary-container font-label-sm text-label-sm px-6 py-2 rounded hover:opacity-90 transition-opacity duration-200"
            >
              Retry
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  if (state.kind === "failed") {
    return (
      <AppShell>
        <div className="min-h-full flex flex-col items-center justify-center p-margin-mobile md:p-margin-desktop text-center">
          {originalQuery && (
            <h1 className="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface-variant opacity-80 max-w-3xl leading-tight mb-6">
              "{originalQuery}"
            </h1>
          )}
          <p className="font-body-lg text-body-lg text-error flex items-center gap-3 justify-center">
            <span className="material-symbols-outlined text-[24px]">error</span>
            Spectator could not complete this research.
          </p>
          <p className="mt-3 font-body-md text-body-md text-on-surface-variant opacity-70 max-w-xl">
            Please try again with a refined query, or come back later.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-8 bg-primary-container text-on-primary-container font-label-sm text-label-sm px-6 py-2 rounded hover:opacity-90 transition-opacity duration-200"
          >
            Refresh
          </button>
        </div>
      </AppShell>
    );
  }

  if (state.kind === "in_progress") {
    return (
      <AppShell>
        <div className="min-h-full flex flex-col max-w-container-max mx-auto w-full p-margin-mobile md:p-margin-desktop">
          {/* Top Section: Query & Status */}
          <header className="mt-section-gap md:mt-[120px] mb-12 flex flex-col items-center text-center">
            <h1 className="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface-variant opacity-80 max-w-3xl leading-tight">
              {originalQuery
                ? `"${originalQuery}"`
                : "Spectator is researching this now."}
            </h1>
            {wsError ? (
              <p className="mt-6 font-body-md text-body-md text-on-surface-variant flex items-center gap-3 justify-center">
                <span className="material-symbols-outlined text-[18px] text-error">
                  wifi_off
                </span>
                {wsError}{" "}
                <button
                  onClick={() => refresh(false)}
                  className="underline hover:text-primary"
                >
                  Refresh
                </button>
              </p>
            ) : (
              <p className="mt-6 font-body-lg text-body-lg text-on-surface-variant flex items-center gap-3 justify-center">
                <span className="w-2 h-2 rounded-full bg-primary animate-status-pulse"></span>
                Spectator is researching this now.
              </p>
            )}
          </header>

          <Stepper activeIndex={activeStep} />

          <StatusLog entries={logs} />
        </div>
      </AppShell>
    );
  }

  // completed
  const report = state.data;
  return (
    <AppShell>
      <article className="max-w-[700px] mx-auto px-margin-mobile md:px-0 py-section-gap">
        {/* Report Header */}
        <header className="mb-12 border-b border-outline-variant pb-8">
          {report.categories && report.categories.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {report.categories.map((c) => (
                <span
                  key={c}
                  className="px-3 py-1 border border-outline-variant rounded-full font-label-sm text-label-sm text-on-surface-variant"
                >
                  {c}
                </span>
              ))}
            </div>
          )}
          <h1 className="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface mb-6">
            {report.title || "Untitled report"}
          </h1>
          {report.goal && (
            <div className="bg-surface-container-low p-4 rounded-lg border border-outline-variant flex items-start space-x-3">
              <span className="material-symbols-outlined text-primary mt-1">
                search
              </span>
              <div>
                <p className="font-label-sm text-label-sm text-on-surface-variant mb-1">
                  ORIGINAL QUERY
                </p>
                <p className="font-body-md text-body-md text-on-surface">
                  {report.goal}
                </p>
              </div>
            </div>
          )}
        </header>

        {/* Report Body */}
        <div className="editorial-content font-body-lg text-body-lg">
          {report.content ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {report.content}
            </ReactMarkdown>
          ) : (
            <p className="text-on-surface-variant opacity-70">
              No content available.
            </p>
          )}
        </div>

        {/* Footer Actions */}
        <div className="mt-16 pt-8 border-t border-outline-variant flex justify-between items-center">
          <button
            onClick={() => window.print()}
            className="flex items-center space-x-2 text-on-surface-variant hover:text-primary transition-colors"
          >
            <span className="material-symbols-outlined">download</span>
            <span className="font-label-sm text-label-sm">Export PDF</span>
          </button>
          <div className="flex space-x-4">
            <button
              className="flex items-center space-x-2 text-on-surface-variant hover:text-primary transition-colors"
              aria-label="Bookmark"
            >
              <span className="material-symbols-outlined">bookmark</span>
            </button>
            <button
              className="flex items-center space-x-2 text-on-surface-variant hover:text-primary transition-colors"
              aria-label="Share"
            >
              <span className="material-symbols-outlined">share</span>
            </button>
          </div>
        </div>
      </article>
    </AppShell>
  );
};
