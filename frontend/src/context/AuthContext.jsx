import { createContext, useContext, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("token"));

  const login = async (email, password) => {
    // /auth/login expects OAuth2PasswordRequestForm - form-encoded, with
    // the email going into the "username" field. This is NOT JSON.
    const body = new URLSearchParams();
    body.append("username", email);
    body.append("password", password);

    const response = await api.post("/auth/login", body, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    localStorage.setItem("token", response.data.access_token);
    setToken(response.data.access_token);
  };

  const register = async (email, password) => {
    const response = await api.post("/auth/register", { email, password });

    localStorage.setItem("token", response.data.access_token);
    setToken(response.data.access_token);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated: !!token, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}