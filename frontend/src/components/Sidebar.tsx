import React, { useEffect, useState, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { Plus, LogOut, FileText, Loader2, RefreshCw } from "lucide-react";

interface ReportItem {
  report_id: string;
  title: string | null;
  status: string | null;
}

interface SidebarProps {
  currentReportId?: string;
  onNavigate: (path: string) => void;
  activePath: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentReportId, onNavigate, activePath }) => {
  const { api, logout } = useAuth();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get("/reports/reports");
      setReports(res.data.reports || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Error loading sidebar reports");
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports, activePath, currentReportId]);

  const getStatusBadge = (status: string | null) => {
    const s = (status || "").toLowerCase();
    if (s === "done" || s === "completed") {
      return <span className="status-badge badge-done">done</span>;
    }
    if (s === "failed" || s === "error") {
      return <span className="status-badge badge-failed">failed</span>;
    }
    return <span className="status-badge badge-progress">{s || "in progress"}</span>;
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button
          className="new-chat-btn"
          onClick={() => onNavigate("/chat")}
        >
          <Plus size={18} />
          <span>New Chat</span>
        </button>
      </div>

      <div className="sidebar-section-title">
        <span>Recent Research</span>
        <button className="icon-refresh-btn" onClick={fetchReports} title="Refresh reports">
          <RefreshCw size={14} className={loading ? "spin" : ""} />
        </button>
      </div>

      <div className="sidebar-list">
        {loading && reports.length === 0 ? (
          <div className="sidebar-loading">
            <Loader2 className="spinner" size={20} />
            <span>Loading reports...</span>
          </div>
        ) : error ? (
          <div className="sidebar-error">
            <span>Failed to load reports</span>
            <button onClick={fetchReports} className="retry-btn">Retry</button>
          </div>
        ) : reports.length === 0 ? (
          <div className="sidebar-empty">
            <FileText size={24} />
            <p>No research reports yet.</p>
          </div>
        ) : (
          reports.map((report) => {
            const isActive = currentReportId === report.report_id;
            return (
              <div
                key={report.report_id}
                className={`sidebar-item ${isActive ? "active" : ""}`}
                onClick={() => onNavigate(`/report/${report.report_id}`)}
              >
                <FileText size={16} className="item-icon" />
                <span className="item-title">
                  {report.title ? report.title : "Untitled Report"}
                </span>
                {getStatusBadge(report.status)}
              </div>
            );
          })
        )}
      </div>

      <div className="sidebar-footer">
        <button className="logout-btn" onClick={logout}>
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
