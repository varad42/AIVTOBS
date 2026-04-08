import { useEffect, useRef, useState } from "react";
import api from "../services/api";

export default function useJobStatus(jobId, enabled = true, intervalMs = 2000) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(Boolean(enabled));
  const timerRef = useRef(null);

  useEffect(() => {
    if (!enabled || !jobId) return undefined;

    let cancelled = false;

    const tick = async () => {
      try {
        const payload = await api.getStatus(jobId);
        if (cancelled) return;
        setStatus(payload);
        setError("");
      } catch (err) {
        if (cancelled) return;
        setError(err?.response?.data?.message || err?.message || "Failed to fetch status.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    tick();
    timerRef.current = setInterval(tick, intervalMs);

    return () => {
      cancelled = true;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [enabled, jobId, intervalMs]);

  return { status, error, loading };
}
