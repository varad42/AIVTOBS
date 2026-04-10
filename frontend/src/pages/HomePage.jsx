import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import UploadCard from "../components/UploadCard";
import StatusFeed from "../components/StatusFeed";
import api from "../services/api";
import { useHistoryState } from "../context/HistoryContext";
import { useDashboardState } from "../context/DashboardContext";

const ACTIVE_STATES = new Set([
  "uploading",
  "uploaded",
  "processing",
  "downloading",
  "extracting_audio",
  "transcribing",
  "waiting_for_model",
  "summarize_requested",
  "blog_requested",
]);

export default function HomePage({ pushToast }) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { addHistoryItem } = useHistoryState();
  const { dashboard, authenticated, loading: dashboardLoading, refreshDashboard } = useDashboardState();
  const [submitting, setSubmitting] = useState(false);
  const [logs, setLogs] = useState([]);
  const [composerResetToken, setComposerResetToken] = useState(0);

  const activeJobId = searchParams.get("job_id") || "";
  const freshWorkspace = searchParams.get("new_chat") === "1";

  useEffect(() => {
    const root = document.documentElement;
    root.classList.add("dark");
    localStorage.setItem("ai-video-theme", "dark");
  }, []);

  const activeJob = useMemo(() => {
    if (activeJobId) {
      return dashboard?.jobs?.find((job) => job.job_id === activeJobId) || dashboard?.active_job || null;
    }

    if (freshWorkspace) {
      return null;
    }

    if (dashboard?.active_job?.job_id) {
      return dashboard.active_job;
    }

    return null;
  }, [activeJobId, dashboard, freshWorkspace]);

  useEffect(() => {
    if (!authenticated || !activeJob?.job_id || !ACTIVE_STATES.has(activeJob.status)) {
      return undefined;
    }

    const timer = setInterval(() => {
      refreshDashboard({ jobId: activeJob.job_id }).catch(() => {});
    }, 3000);

    return () => clearInterval(timer);
  }, [activeJob?.job_id, activeJob?.status, authenticated, refreshDashboard]);

  useEffect(() => {
    if (!activeJob) {
      setLogs([]);
      return;
    }

    const statusMap = {
      uploading: ["Receiving upload...", "Preparing storage..."],
      uploaded: ["Upload completed.", "Waiting for worker..."],
      processing: ["Worker claimed the job.", "Preparing pipeline..."],
      downloading: ["Downloading video source..."],
      extracting_audio: ["Extracting audio stream..."],
      transcribing: ["Transcribing video audio..."],
      waiting_for_model: ["Transcript ready.", "Choose a model to continue."],
      summarize_requested: ["Model selected.", "Generating summary..."],
      summary_ready: ["Summary ready.", "Open the result or generate a blog."],
      blog_requested: ["Generating blog draft..."],
      blog_ready: ["Blog ready."],
      error: [activeJob.error_message || "This job failed during processing."],
    };

    setLogs(statusMap[activeJob.status] || []);
  }, [activeJob]);

  const handleSubmit = async ({ file, videoUrl }) => {
    if (!file && !videoUrl) {
      pushToast("Please upload a file or provide a YouTube URL.", "error");
      return;
    }

    setSubmitting(true);
    setLogs(["Starting upload..."]);

    try {
      let response;
      if (file) {
        response = await api.uploadVideo(file);
        setLogs((prev) => [...prev, "Video uploaded successfully."]);
      } else {
        response = await api.processYoutube(videoUrl);
        setLogs((prev) => [...prev, "YouTube URL accepted and queued."]);
      }

      const jobId = response?.jobId;
      if (!jobId) {
        throw new Error("Backend did not return a job id.");
      }

      addHistoryItem({
        id: jobId,
        label: file?.name || videoUrl,
        source: file ? "upload" : "youtube",
      });

      setSearchParams({ job_id: jobId });
      await refreshDashboard({ jobId });
    } catch (error) {
      pushToast(error?.response?.data?.message || error.message || "Failed to start processing.", "error");
      setLogs((prev) => [...prev, "Request failed. Please retry."]);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGenerateBlog = async () => {
    if (!activeJob?.job_id) return;

    try {
      await api.triggerBlog(activeJob.job_id);
      pushToast("Blog generation started.");
      await refreshDashboard({ jobId: activeJob.job_id });
    } catch (error) {
      pushToast(error?.response?.data?.message || error.message || "Could not start blog generation.", "error");
    }
  };

  const handleNewChat = () => {
    setSearchParams({ new_chat: "1" });
    setLogs([]);
    pushToast("New chat started.");
  };

  if (dashboardLoading && !dashboard) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">Loading workspace...</div>;
  }

  if (!authenticated) {
    return (
      <section className="flex min-h-[92vh] flex-col items-center justify-start px-4 pt-4 pb-10 sm:pt-6">
        <div className="w-full max-w-5xl rounded-[2rem] border border-slate-200/80 bg-white/88 px-14 py-24 text-center shadow-[0_28px_80px_rgba(15,23,42,0.16)] backdrop-blur-xl dark:border-slate-800/80 dark:bg-slate-900/88 sm:px-20 sm:py-28">
          <h1 className="font-serif text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-4xl">
            AI Video Summarizer to Blog Generator
          </h1>
          <h2 className="mt-8 text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 sm:text-3xl">Log in</h2>
          <p className="mt-4 text-base text-slate-500 dark:text-slate-400 sm:text-lg">New user? Create your account first.</p>
          <div className="mt-16 grid gap-5 sm:grid-cols-2">
          <Link to="/login" className="rounded-2xl bg-brand-600 px-6 py-4 text-base font-semibold text-white hover:bg-brand-700">
            Login
          </Link>
          <Link to="/signup" className="rounded-2xl border border-slate-300 px-6 py-4 text-base font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800">
            Create account
          </Link>
          </div>
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-serif text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 md:text-3xl">
              AI Video Summarizer & Blog Generator
            </h2>
          </div>
          <button
            type="button"
            onClick={handleNewChat}
            className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400"
          >
            New Chat
          </button>
        </div>
      </section>

      <UploadCard onSubmit={handleSubmit} loading={submitting} resetToken={composerResetToken} />

      {activeJob ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="mt-1 text-xl font-semibold">{activeJob.display_name || activeJob.job_slug || activeJob.job_id}</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                {activeJob.source_type || "video"} - {String(activeJob.status || "idle").replaceAll("_", " ")}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {activeJob.status === "waiting_for_model" ? (
                <button
                  type="button"
                  onClick={() => navigate(`/model/${activeJob.job_id}`)}
                  className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
                >
                  Select Model
                </button>
              ) : null}
              {activeJob.summary_file ? (
                <button
                  type="button"
                  onClick={() => navigate(`/result/${activeJob.job_id}`)}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  View Summary
                </button>
              ) : null}
              {activeJob.summary_file && !activeJob.blog_file ? (
                <button
                  type="button"
                  onClick={handleGenerateBlog}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  Generate Blog
                </button>
              ) : null}
              {activeJob.blog_file ? (
                <button
                  type="button"
                  onClick={() => navigate(`/result/${activeJob.job_id}`)}
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  View Blog
                </button>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}

      {logs.length ? <StatusFeed logs={logs} /> : null}
    </div>
  );
}
