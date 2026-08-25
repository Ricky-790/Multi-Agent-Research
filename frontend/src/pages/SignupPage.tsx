import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { SpectatorLogo } from "../components/SpectatorLogo";
import { useAuth } from "../context/AuthContext";
import { apiRequest, ApiError } from "../lib/api";

export const SignupPage: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate("/chat", { replace: true });
  }, [isAuthenticated, navigate]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const data = await apiRequest("/auth/signup", {
        method: "POST",
        body: { username, email, password },
      });
      if (!data?.access_token) {
        throw new ApiError("Unexpected response from server.", 500);
      }
      login(data.access_token);
      navigate("/chat", { replace: true });
    } catch (err) {
      if (err instanceof ApiError) setError(err.message);
      else setError("Something went wrong. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-background text-on-surface antialiased font-body-md min-h-screen flex items-center justify-center p-margin-mobile md:p-margin-desktop">
      <main className="w-full max-w-[400px]">
        <div className="mb-gutter flex justify-center">
          <SpectatorLogo className="h-16 w-auto object-contain" />
        </div>

        <div className="bg-[#17181B] border border-surface-variant rounded-lg p-gutter">
          <form onSubmit={onSubmit} className="flex flex-col gap-6">
            <div>
              <label
                className="block font-label-sm text-label-sm text-on-surface-variant mb-2"
                htmlFor="username"
              >
                Username
              </label>
              <input
                className="w-full bg-surface border border-outline-variant rounded focus:border-primary focus:ring-0 text-on-surface font-body-md text-body-md px-4 py-2 transition-colors duration-200"
                id="username"
                name="username"
                placeholder="Enter your username"
                required
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
              />
            </div>
            <div>
              <label
                className="block font-label-sm text-label-sm text-on-surface-variant mb-2"
                htmlFor="email"
              >
                Email
              </label>
              <input
                className="w-full bg-surface border border-outline-variant rounded focus:border-primary focus:ring-0 text-on-surface font-body-md text-body-md px-4 py-2 transition-colors duration-200"
                id="email"
                name="email"
                placeholder="name@example.com"
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>
            <div>
              <label
                className="block font-label-sm text-label-sm text-on-surface-variant mb-2"
                htmlFor="password"
              >
                Password
              </label>
              <input
                className="w-full bg-surface border border-outline-variant rounded focus:border-primary focus:ring-0 text-on-surface font-body-md text-body-md px-4 py-2 transition-colors duration-200"
                id="password"
                name="password"
                placeholder="••••••••"
                required
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                minLength={6}
              />
            </div>

            {error && (
              <div
                role="alert"
                className="font-body-md text-body-md text-error border border-error-container bg-surface-container-low rounded px-3 py-2"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-primary-container text-[#111417] font-label-sm text-label-sm py-3 px-4 rounded hover:opacity-80 transition-opacity duration-200 mt-2 disabled:opacity-60"
            >
              {submitting ? "Creating account…" : "Create account"}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link
              to="/login"
              className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary transition-colors duration-200"
            >
              Already have an account? Log in
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
};
