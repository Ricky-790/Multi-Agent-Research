import React, { createContext, useContext, useState } from "react";
import axios, { type AxiosInstance } from "axios";

const API_BASE = "http://localhost:8000";

interface AuthContextType {
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
  api: AxiosInstance;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("access_token"));

  const login = (newToken: string) => {
    localStorage.setItem("access_token", newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    setToken(null);
  };

  const api = axios.create({
    baseURL: API_BASE,
    headers: {
      "Content-Type": "application/json",
    },
  });

  // Attach token interceptor dynamically
  api.interceptors.request.use((config) => {
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Handle 401 unauthenticated response
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response && error.response.status === 401) {
        logout();
      }
      return Promise.reject(error);
    }
  );

  return (
    <AuthContext.Provider value={{ token, login, logout, api }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
