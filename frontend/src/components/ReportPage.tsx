import React, { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Loader2, AlertCircle, CheckCircle2, Clock, Activity } from "lucide-react";

interface ReportPageProps {
  reportId: string;
}

interface StepperStage {
  id: string;
  label: string;
}

const STAGES: StepperStage[] = [
  { id: "planning", label: "Planning" },
  { id: "researching", label: "Researching" },
  { id: "synthesizing", label: "Synthesizing" },
];

interface LogEntry {
  timestamp: string;
  phase: string;
  status: string;
}

export const ReportPage: React.FC<ReportPageProps> = ({ reportId }) => {
  const { api, token } = useAuth();
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Stepper and logs state for live WebSocket updates
  const [currentPhase, setCurrentPhase] = useState<string>("planning");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isWsConnecting, setIsWsConnecting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const fetchReport = useCallback(async () => {
    try {
      const res = await api.get(`/reports/report/${reportId}`);
      const data = res.data;
      setReportData(data);
      return data;
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || err.message || "Error loading report.";
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, [reportId, api]);

  // Connect WebSocket for live status updates
  const connectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    setIsWsConnecting(true);
    const wsUrl = `ws://localhost:8000/ws/${reportId}?token=${(token || "")}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsWsConnecting(false);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.phase) {
          setCurrentPhase(msg.phase.toLowerCase());
          setLogs((prev) => [
            ...prev,
            {
              timestamp: new Date().toLocaleTimeString(),
              phase: msg.phase,
              status: msg.status,
            },
          ]);
        }

        if (msg.done) {
          ws.close();
          fetchReport();
        }
      } catch (err) {
        console.error("Failed to parse WS message", err);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
      setError("WebSocket connection failed while tracking report progress.");
      setIsWsConnecting(false);
    };

    ws.onclose = () => {
      setIsWsConnecting(false);
    };
  }, [reportId, token, fetchReport]);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);
    setLogs([]);

    fetchReport().then((data) => {
      if (!isMounted || !data) return;

      const hasContent = data.content !== undefined && data.content !== null;

      if (!hasContent) {
        const status = (data.status || "").toLowerCase();
        if (status === "done" || status === "failed") {
          fetchReport();
        } else {
          connectWebSocket();
        }
      }
    });

    return () => {
      isMounted = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [reportId, fetchReport, connectWebSocket]);

  const activeStageIndex = STAGES.findIndex((s) => s.id === currentPhase);
  const displayGoal = reportData?.goal || (reportData?.content ? reportData?.title : null);

  return (
    <div className="report-container">
      {/* Top section: Query / Goal heading */}
      <div className="report-header shadow-card">
        <span className="report-label">Research Goal</span>
        <h1 className="report-goal-title">
          {displayGoal ? displayGoal : "Loading your report..."}
        </h1>
        {reportData?.categories && reportData.categories.length > 0 && (
          <div className="categories-tags">
            {reportData.categories.map((cat: string, idx: number) => (
              <span key={idx} className="category-tag">
                {cat}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="report-status-card center-card">
          <Loader2 className="spinner" size={32} />
          <p>Fetching report details...</p>
        </div>
      ) : error ? (
        <div className="report-status-card error-card">
          <AlertCircle size={32} />
          <h3>Error Loading Report</h3>
          <p>{error}</p>
        </div>
      ) : reportData?.content !== undefined && reportData?.content !== null ? (
        /* Completed Report Rendering */
        <div className="report-body shadow-card">
          {reportData.title && (
            <h2 className="report-main-title">{reportData.title}</h2>
          )}

          {reportData.strategy_summary && (
            <div className="strategy-box">
              <h3>Strategy Summary</h3>
              <p>{reportData.strategy_summary}</p>
            </div>
          )}

          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {reportData.content}
            </ReactMarkdown>
          </div>
        </div>
      ) : (
        /* Live Progress View (In Progress) */
        <div className="progress-section shadow-card">
          <div className="progress-header">
            <Activity className="pulse-icon" size={24} />
            <h2>Research In Progress</h2>
          </div>

          {/* Stepper */}
          <div className="stepper">
            {STAGES.map((stage, idx) => {
              const isCurrent = currentPhase === stage.id;
              const isPassed = activeStageIndex > idx;
              return (
                <div key={stage.id} className="stepper-step">
                  <div
                    className={`step-circle ${isPassed ? "completed" : isCurrent ? "active" : ""
                      }`}
                  >
                    {isPassed ? (
                      <CheckCircle2 size={18} />
                    ) : isCurrent ? (
                      <Loader2 className="spinner" size={18} />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  <span className={`step-label ${isCurrent ? "active" : ""}`}>
                    {stage.label}
                  </span>
                  {idx < STAGES.length - 1 && (
                    <div
                      className={`step-line ${activeStageIndex > idx ? "completed" : ""
                        }`}
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Progress Logs */}
          <div className="logs-card">
            <div className="logs-header">
              <Clock size={16} />
              <span>Live Update Stream</span>
            </div>
            <div className="logs-list">
              {logs.length === 0 ? (
                <div className="log-item placeholder">
                  <span className="log-time">--:--:--</span>
                  <span className="log-text">Connecting to progress stream...</span>
                </div>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className="log-item">
                    <span className="log-time">[{log.timestamp}]</span>
                    <span className="log-phase">{log.phase}:</span>
                    <span className="log-status">{log.status}</span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
