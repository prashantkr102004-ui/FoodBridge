import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { setAuthToken } from "../api/client";
import { authService } from "../services/authService";
import { roleHome } from "../utils/format";

const AuthContext = createContext(null);
const TOKEN_KEY = "foodbridge_token";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function restoreUser() {
      if (!token) {
        setAuthToken(null);
        setLoading(false);
        return;
      }
      setAuthToken(token);
      try {
        const currentUser = await authService.me();
        if (isMounted) setUser(currentUser);
      } catch {
        logout();
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    restoreUser();
    return () => {
      isMounted = false;
    };
  }, [token]);

  async function login(credentials) {
    const data = await authService.login(credentials);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    setAuthToken(data.access_token);
    setToken(data.access_token);
    const currentUser = await authService.me();
    setUser(currentUser);
    return roleHome(currentUser.role);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setToken(null);
    setUser(null);
  }

  function updateUser(nextUser) {
    setUser(nextUser);
  }

  useEffect(() => {
    window.addEventListener("foodbridge:unauthorized", logout);
    return () => window.removeEventListener("foodbridge:unauthorized", logout);
  }, []);

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(user && token),
      login,
      logout,
      updateUser
    }),
    [user, token, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
