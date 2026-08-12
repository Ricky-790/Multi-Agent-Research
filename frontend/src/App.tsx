import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { AuthForm } from "./components/AuthForm";
import { Sidebar } from "./components/Sidebar";
import { ChatPage } from "./components/ChatPage";
import { ReportPage } from "./components/ReportPage";
import "./index.css";

const MainApp: React.FC = () => {
  const { token } = useAuth();
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

  // Auth routing check
  if (!token) {
    if (currentPath === "/signup") {
      return <AuthForm mode="signup" onNavigate={navigate} />;
    }
    return <AuthForm mode="login" onNavigate={navigate} />;
  }

  // If logged in but on /login or /signup, redirect to /chat
  if (currentPath === "/login" || currentPath === "/signup" || currentPath === "/") {
    navigate("/chat");
  }

  // Extract reportId if on report page
  let reportId: string | undefined = undefined;
  if (currentPath.startsWith("/report/")) {
    reportId = currentPath.split("/report/")[1];
  }

  return (
    <div className="layout-container">
      <Sidebar
        currentReportId={reportId}
        onNavigate={navigate}
        activePath={currentPath}
      />
      <main className="main-content">
        {reportId ? (
          <ReportPage reportId={reportId} />
        ) : (
          <ChatPage onNavigate={navigate} />
        )}
      </main>
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

export default App;
