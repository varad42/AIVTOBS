import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import UploadCard from "../components/UploadCard";
import ProgressBar from "../components/ProgressBar";
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
  const [progress, setProgress] = useState(0);
  const [composerResetToken, setComposerResetToken] = useState(0);

  const activeJobId = searchParams.get("job_id") || dashboard?.active_job?.job_id || "";
  const activeJob = useMemo(() => {
    if (!dashboard?.jobs?.length) {
      return dashboard?.active_job || null;
    }

    if (activeJobId) {
      return dashboard.jobs.find((job) => job.job_id === activeJobId) || dashboard.active_job || null;
    }

    return dashboard.active_job || dashboard.jobs[0] || null;
  }, [activeJobId, dashboard]);

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
      setProgress(0);
      setLogs([]);
      return;
    }

    const progressMap = {
      uploading: 10,
      uploaded: 15,
      processing: 18,
      downloading: 20,
      extracting_audio: 40,
      transcribing: 60,
      waiting_for_model: 80,
      summarize_requested: 85,
      blog_requested: 90,
      summary_ready: 100,
      blog_ready: 100,
    };

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

    setProgress(progressMap[activeJob.status] || 0);
    setLogs(statusMap[activeJob.status] || []);
  }, [activeJob]);

  const handleSubmit = async ({ file, videoUrl }) => {
    if (!file && !videoUrl) {
      pushToast("Please upload a file or provide a YouTube URL.", "error");
      return;
    }

    setSubmitting(true);
    setLogs(["Starting upload..."]);
    setProgress(10);

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

  const handleNewChat = async () => {
    setSearchParams({});
    setLogs([]);
    setProgress(0);
    try {
      await refreshDashboard({ newChat: true });
      pushToast("New chat started.");
    } catch (error) {
      pushToast(error?.message || "Could not start a new chat.", "error");
    }
  };

  const handleResetComposer = () => {
    setComposerResetToken((value) => value + 1);
    setLogs([]);
    setProgress(0);
    pushToast("Composer reset.");
  };

  if (dashboardLoading && !dashboard) {
    return <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">Loading workspace...</div>;
  }

  if (!authenticated) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm uppercase tracking-wide text-slate-500 dark:text-slate-400">AI Video Studio</p>
        <h1 className="mt-2 text-3xl font-bold">Log in to access uploads, processing, and history.</h1>
        <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
          The new frontend now works with the existing Flask session. Sign in first, then upload a file or paste a YouTube URL.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/login"
            className="rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700"
          >
            Login
          </Link>
          <Link
            to="/signup"
            className="rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Create account
          </Link>
        </div>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">AI Video Summarizer & Blog Generator</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={handleNewChat}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              New Chat
            </button>
            <button
              type="button"
              onClick={handleResetComposer}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
            >
              Reset Composer
            </button>
          </div>
        </div>
      </section>

      <UploadCard onSubmit={handleSubmit} loading={submitting} resetToken={composerResetToken} />

      {activeJob ? (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-800 dark:bg-slate-900">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Current Job</p>
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

          <div className="mt-4">
            <ProgressBar value={progress} />
          </div>
        </section>
      ) : null}

      <StatusFeed logs={logs} />
    </div>
  );
}
