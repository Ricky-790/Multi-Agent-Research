import React, { useState } from "react";

const API_BASE = "http://localhost:8000";

interface RouterProps {
  currentPath: string;
  navigate: (path: string) => void;
  reportId?: string;
}

export const Router: React.FC<{
  routes: {
    login: React.ReactNode;
    signup: React.ReactNode;
    chat: React.ReactNode;
    report: (id: string) => React.ReactNode;
  };
}> = ({ routes }) => {
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = (path: string) => {
    window.history.pushState({}, "", path);
    setCurrentPath(path);
  };

  // Simple path matching
  if (currentPath === "/signup") {
    return <>{routes.signup}</>;
  }

  if (currentPath.startsWith("/report/")) {
    const reportId = currentPath.split("/report/")[1];
    return <>{routes.report(reportId)}</>;
  }

  if (currentPath === "/chat") {
    return <>{routes.chat}</>;
  }

  // Default fallback route (or /login)
  return <>{routes.login}</>;
};
