import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import api from "../services/api";

const DashboardContext = createContext(null);

const readQueryJobId = (search) => {
  const params = new URLSearchParams(search);
  return params.get("job_id") || "";
};

export function DashboardProvider({ children }) {
  const location = useLocation();
  const [dashboard, setDashboard] = useState(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  const refreshDashboard = useCallback(async (options = {}) => {
    const envelope = await api.getDashboardState(options);
    setDashboard(envelope.dashboard || null);
    setAuthenticated(Boolean(envelope.authenticated));
    setLoading(false);
    return envelope;
  }, []);

  useEffect(() => {
    let cancelled = false;
    const activeJobId = location.pathname === "/" ? readQueryJobId(location.search) : "";

    refreshDashboard({ jobId: activeJobId })
      .catch(() => {
        if (cancelled) return;
        setDashboard(null);
        setAuthenticated(false);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [location.pathname, location.search, refreshDashboard]);

  const value = useMemo(
    () => ({
      dashboard,
      authenticated,
      loading,
      refreshDashboard,
    }),
    [authenticated, dashboard, loading, refreshDashboard]
  );

  return <DashboardContext.Provider value={value}>{children}</DashboardContext.Provider>;
}

export function useDashboardState() {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error("useDashboardState must be used inside DashboardProvider");
  }
  return context;
}
