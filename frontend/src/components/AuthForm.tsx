import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { Lock, Mail, User, ArrowRight, AlertCircle, Loader2 } from "lucide-react";
import axios from "axios";

interface AuthFormProps {
  mode: "login" | "signup";
  onNavigate: (path: string) => void;
}

export const AuthForm: React.FC<AuthFormProps> = ({ mode, onNavigate }) => {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const endpoint = mode === "signup" ? "/auth/signup" : "/auth/signin";
    const payload = mode === "signup" ? { username, email, password } : { email, password };

    try {
      const res = await axios.post(`http://localhost:8000${endpoint}`, payload, {
        headers: { "Content-Type": "application/json" },
      });

      const data = res.data;

      if (data.access_token) {
        login(data.access_token);
        onNavigate("/chat");
      } else {
        throw new Error("No access token returned from server");
      }
    } catch (err: any) {
      const serverMessage = err.response?.data?.detail || err.response?.data?.message || err.message;
      setError(serverMessage || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-badge">
            <div className="pulse-dot"></div>
            <span>Deep Research AI</span>
          </div>
          <h1>{mode === "signup" ? "Create an Account" : "Welcome Back"}</h1>
          <p>{mode === "signup" ? "Sign up to start autonomous research workflows" : "Sign in to access your research reports"}</p>
        </div>

        {error && (
          <div className="error-banner">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === "signup" && (
            <div className="form-group">
              <label htmlFor="username">Username</label>
              <div className="input-wrapper">
                <User size={18} className="input-icon" />
                <input
                  id="username"
                  type="text"
                  placeholder="johndoe"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="email">Email address</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input
                id="email"
                type="email"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? (
              <Loader2 className="spinner" size={20} />
            ) : (
              <>
                <span>{mode === "signup" ? "Sign Up" : "Sign In"}</span>
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <div className="auth-footer">
          {mode === "signup" ? (
            <p>
              Already have an account?{" "}
              <button type="button" className="link-btn" onClick={() => onNavigate("/login")}>
                Sign In
              </button>
            </p>
          ) : (
            <p>
              Don't have an account?{" "}
              <button type="button" className="link-btn" onClick={() => onNavigate("/signup")}>
                Sign Up
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
