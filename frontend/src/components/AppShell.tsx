import React, { useState } from "react";
import { Sidebar } from "./Sidebar";

// Layout shell used by /chat and /report/:reportId. Provides the persistent
// sidebar with a mobile toggle.
export const AppShell: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background text-on-surface antialiased font-body-md">
      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 w-full bg-surface border-b border-outline-variant z-50 p-4 flex justify-between items-center">
        <div className="font-headline-md text-headline-md font-semibold text-on-surface tracking-tight flex items-center gap-2">
          Spectator
          <span className="material-symbols-outlined text-primary text-xl">
            visibility
          </span>
        </div>
        <button
          onClick={() => setMobileOpen((v) => !v)}
          className="text-on-surface"
          aria-label="Toggle menu"
        >
          <span className="material-symbols-outlined">
            {mobileOpen ? "close" : "menu"}
          </span>
        </button>
      </div>

      <Sidebar
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <main className="flex-1 md:ml-[260px] min-h-screen pt-[72px] md:pt-0 bg-background overflow-y-auto">
        {children}
      </main>
    </div>
  );
};
