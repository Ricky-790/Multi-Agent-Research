import React, { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiRequest } from "../lib/api";
import { StatusDot } from "./StatusDot";

interface ReportSummary {
  report_id: string;
  title: string | null;
  status: string | null;
}

interface SidebarProps {
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  mobileOpen,
  onCloseMobile,
}) => {
  const { token, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setLoading(true);
    apiRequest("/reports/reports", { token })
      .then((data) => {
        if (cancelled) return;
        setReports(Array.isArray(data?.reports) ? data.reports : []);
      })
      .catch(() => {
        if (!cancelled) setReports([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const handleNewResearch = () => {
    onCloseMobile();
    navigate("/chat");
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isOnReport =
    location.pathname.startsWith("/report/") ||
    location.pathname === "/chat" ||
    location.pathname === "/chat/";

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black/60 z-30"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-full w-[260px] border-r border-outline-variant bg-surface flex flex-col z-40 transition-transform duration-300 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0`}
      >
        {/* Brand / Header */}
        <div className="px-6 py-8 flex flex-col gap-4">
          <Link
            to="/chat"
            onClick={onCloseMobile}
            className="flex flex-col gap-4"
          >
            <div>
              <h1 className="font-headline-md text-headline-md font-semibold text-on-surface tracking-tight">
                Spectator
              </h1>
            </div>
          </Link>
          <button
            onClick={handleNewResearch}
            className="mt-4 w-full bg-primary-container text-on-primary-container hover:bg-primary transition-colors duration-200 py-2 px-4 rounded font-label-sm text-label-sm flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Research
          </button>
        </div>

        {/* Main Navigation */}
        <nav className="flex-1 overflow-y-auto px-4 py-2 flex flex-col gap-1">
          <p className="px-4 py-2 text-xs font-medium text-outline uppercase tracking-widest mb-1">
            Navigation
          </p>
          <NavItem icon="book" label="Library" onClick={onCloseMobile} />

          {/* Recent Reports list */}
          <div className="mt-8 mb-2">
            <p className="px-4 py-2 text-xs font-medium text-outline uppercase tracking-widest">
              Recent Reports
            </p>
            {loading ? (
              <p className="px-4 py-2 font-label-sm text-label-sm text-on-surface-variant opacity-60">
                Loading…
              </p>
            ) : reports.length === 0 ? (
              <p className="px-4 py-2 font-label-sm text-label-sm text-on-surface-variant opacity-60">
                No reports yet.
              </p>
            ) : (
              reports.map((r) => (
                <Link
                  key={r.report_id}
                  to={`/report/${r.report_id}`}
                  onClick={onCloseMobile}
                  className="px-4 py-2 flex items-center gap-3 text-on-surface-variant font-label-sm text-label-sm hover:bg-surface-container-low rounded transition-colors duration-200"
                >
                  <StatusDot status={r.status} />
                  <span className="truncate">
                    {r.title || "Untitled report"}
                  </span>
                </Link>
              ))
            )}
          </div>
        </nav>

        {/* Footer Navigation */}
        <div className="p-4 border-t border-outline-variant bg-surface">
          <NavItem icon="settings" label="Settings" onClick={onCloseMobile} />
          <NavItem icon="help" label="Support" onClick={onCloseMobile} />
          <button
            onClick={handleLogout}
            className="w-full text-left flex items-center gap-3 px-4 py-2 rounded hover:bg-surface-container-low transition-colors duration-200 text-on-surface-variant font-label-sm text-label-sm group"
          >
            <span className="material-symbols-outlined text-[20px] text-outline group-hover:text-error transition-colors duration-200">
              logout
            </span>
            <span>Log out</span>
          </button>
        </div>
      </aside>
    </>
  );
};

const NavItem: React.FC<{
  icon: string;
  label: string;
  active?: boolean;
  onClick?: () => void;
}> = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-3 px-4 py-2.5 rounded hover:bg-surface-container-low transition-colors duration-200 font-label-sm text-label-sm group text-left ${
      active
        ? "bg-surface-container-low text-primary"
        : "text-on-surface-variant"
    }`}
  >
    <span
      className={`material-symbols-outlined text-[20px] transition-colors duration-200 ${
        active ? "text-primary" : "text-outline group-hover:text-primary"
      }`}
    >
      {icon}
    </span>
    <span>{label}</span>
  </button>
);
