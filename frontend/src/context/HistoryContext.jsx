import React, { createContext, useContext, useMemo, useState } from "react";
import { useDashboardState } from "./DashboardContext";

const HistoryContext = createContext(null);
const STORAGE_KEY = "ai-video-history-v1";

const readInitialHistory = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

export function HistoryProvider({ children }) {
  const { dashboard } = useDashboardState();
  const [history, setHistory] = useState(readInitialHistory);

  const persist = (nextValue) => {
    setHistory(nextValue);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextValue));
  };

  const addHistoryItem = (item) => {
    const id = item?.jobId || item?.job_id || item?.id;
    if (!id) return;

    const normalized = {
      id: String(id),
      label: item.label || item.title || item.videoTitle || `Job ${String(id).slice(0, 8)}`,
      source: item.source || "video",
      updatedAt: new Date().toISOString(),
    };

    persist([normalized, ...history.filter((entry) => entry.id !== normalized.id)].slice(0, 30));
  };

  const value = useMemo(
    () => ({
      history:
        dashboard?.jobs?.length
          ? dashboard.jobs.map((job) => ({
              id: job.job_id,
              label: job.display_name || job.job_slug || `Job ${String(job.job_id).slice(0, 8)}`,
              source: job.source_type || "video",
              status: job.status || "idle",
              updatedAt: job.uploaded_at || job.queued_at || "",
            }))
          : history,
      addHistoryItem,
    }),
    [dashboard?.jobs, history]
  );

  return <HistoryContext.Provider value={value}>{children}</HistoryContext.Provider>;
}

export function useHistoryState() {
  const context = useContext(HistoryContext);
  if (!context) {
    throw new Error("useHistoryState must be used inside HistoryProvider");
  }
  return context;
}
