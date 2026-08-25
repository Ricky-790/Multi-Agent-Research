import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiRequest, ApiError } from "../lib/api";
import { AppShell } from "../components/AppShell";

interface ReportSummary {
  report_id: string;
  title: string | null;
  status: string | null;
}

interface ReportsListResponse {
  reports: ReportSummary[];
  limit: number;
  offset: number;
}

export const ReportsListPage: React.FC = () => {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    apiRequest("/reports/all", { token })
      .then((data: ReportsListResponse) => {
        if (cancelled) return;
        setReports(Array.isArray(data?.reports) ? data.reports : []);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const msg =
          err instanceof ApiError
            ? err.message
            : "Failed to load your reports.";
        setError(msg);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const onOpen = (id: string) => {
    navigate(`/report/${id}`);
  };

  return (
    <AppShell>
      <div className="max-w-container-max mx-auto w-full px-margin-mobile md:px-margin-desktop py-section-gap">
        <header className="mb-10">
          <h1 className="font-display-lg-mobile md:font-display-lg text-display-lg-mobile md:text-display-lg text-on-surface tracking-tight">
            Library
          </h1>
          <p className="mt-3 font-body-md text-body-md text-on-surface-variant">
            All the reports Spectator has produced for you.
          </p>
        </header>

        {loading && (
          <div className="flex items-center justify-center py-16">
            <p className="font-body-lg text-body-lg text-on-surface-variant opacity-60">
              Loading your reports…
            </p>
          </div>
        )}

        {error && !loading && (
          <div className="border border-error-container bg-surface-container-low rounded px-4 py-3 font-body-md text-body-md text-error">
            {error}
          </div>
        )}

        {!loading && !error && reports.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center gap-4">
            <span className="material-symbols-outlined text-[48px] text-outline">
              article
            </span>
            <p className="font-headline-md text-headline-md text-on-surface">
              No reports yet
            </p>
            <p className="font-body-md text-body-md text-on-surface-variant max-w-md">
              Start a research and your finished reports will show up here.
            </p>
            <button
              onClick={() => navigate("/chat")}
              className="mt-2 bg-primary-container text-on-primary-container font-label-sm text-label-sm px-6 py-2 rounded hover:opacity-90 transition-opacity duration-200"
            >
              New research
            </button>
          </div>
        )}

        {!loading && !error && reports.length > 0 && (
          <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {reports.map((r) => (
              <ReportTile
                key={r.report_id}
                report={r}
                onOpen={() => onOpen(r.report_id)}
              />
            ))}
          </ul>
        )}
      </div>
    </AppShell>
  );
};

const ReportTile: React.FC<{
  report: ReportSummary;
  onOpen: () => void;
}> = ({ report, onOpen }) => {
  const status = (report.status || "unknown").toLowerCase();
  const statusLabel =
    status === "done"
      ? "Done"
      : status === "failed"
        ? "Failed"
        : "In progress";
  const statusColor =
    status === "done"
      ? "text-primary border-primary"
      : status === "failed"
        ? "text-error border-error"
        : "text-on-surface-variant border-outline-variant";

  return (
    <li>
      <button
        onClick={onOpen}
        className="w-full h-full text-left bg-surface-container-lowest border border-outline-variant rounded-lg p-6 hover:border-primary hover:shadow-sm transition-all duration-200 flex flex-col gap-4 min-h-[160px]"
      >
        <div className="flex items-start gap-3">
          <span className="material-symbols-outlined text-primary text-[28px] shrink-0">
            description
          </span>
          <h3 className="font-headline-sm text-headline-sm text-on-surface line-clamp-2 flex-1">
            {report.title || "Untitled report"}
          </h3>
        </div>
        <div className="mt-auto flex items-center justify-between">
          <span
            className={`px-2.5 py-1 border rounded-full font-label-sm text-label-sm ${statusColor}`}
          >
            {statusLabel}
          </span>
          <span className="material-symbols-outlined text-outline text-[20px]">
            arrow_forward
          </span>
        </div>
      </button>
    </li>
  );
};
