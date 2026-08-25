import React from "react";
import { Link } from "react-router-dom";
import { SpectatorLogo } from "./SpectatorLogo";
import { useAuth } from "../context/AuthContext";

// Header used on public marketing/auth pages. When the viewer is signed in we
// swap the brand target to /chat so clicking the logo doesn't bounce them
// through the now-restricted landing page.
export const Header: React.FC = () => {
  const { isAuthenticated, logout } = useAuth();
  const brandTo = isAuthenticated ? "/chat" : "/";

  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full bg-surface border-b border-outline-variant px-margin-mobile md:px-margin-desktop py-4 flex justify-between items-center">
      <Link to={brandTo} className="flex items-center gap-3">
        <SpectatorLogo className="h-8 w-auto" />
      </Link>
      <div className="flex items-center gap-6">
        {isAuthenticated ? (
          <>
            <Link
              to="/chat"
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-colors duration-200"
            >
              Open Chat
            </Link>
            <button
              onClick={logout}
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-colors duration-200"
            >
              Log out
            </button>
          </>
        ) : (
          <>
            <Link
              to="/login"
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-colors duration-200"
            >
              Log in
            </Link>
            <Link
              to="/signup"
              className="bg-primary-container text-on-primary-container font-label-sm text-label-sm px-6 py-2 rounded transition-opacity duration-200 hover:opacity-90"
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </header>
  );
};
