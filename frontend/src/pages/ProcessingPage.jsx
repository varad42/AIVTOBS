import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import ThinkingAnimation from "../components/ThinkingAnimation";
import ProgressBar from "../components/ProgressBar";
import StatusFeed from "../components/StatusFeed";
import useJobStatus from "../hooks/useJobStatus";

const doneStates = new Set(["completed", "done", "summary_ready", "blog_ready", "finished"]);

export default function ProcessingPage({ pushToast }) {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { status, error } = useJobStatus(jobId, true, 2200);

  const logs = status?.logs || status?.messages || [];
  const progress = status?.progress ?? 0;
  const stateLabel = String(status?.status || "").toLowerCase();

  useEffect(() => {
    if (error) {
      pushToast(error, "error");
    }
  }, [error, pushToast]);

  useEffect(() => {
    if (stateLabel === "waiting_for_model") {
      navigate(`/model/${jobId}`);
      return;
    }

    if (doneStates.has(stateLabel) || progress >= 100) {
      navigate(`/result/${jobId}`);
    }
  }, [jobId, navigate, progress, stateLabel]);

  return (
    <div className="space-y-4">
      <ThinkingAnimation />
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">Please wait while processing completes.</p>
        <ProgressBar value={progress} />
      </section>
      <StatusFeed logs={logs} />
    </div>
  );
}
