import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";
import ResultSections from "../components/ResultSections";
import SkeletonBlock from "../components/SkeletonBlock";
import { useHistoryState } from "../context/HistoryContext";

export default function ResultPage({ pushToast }) {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const { addHistoryItem } = useHistoryState();
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState(null);
  const [generatingBlog, setGeneratingBlog] = useState(false);

  useEffect(() => {
    let mounted = true;

    const fetchResult = async () => {
      try {
        const payload = await api.getResult(jobId);
        if (!mounted) return;
        setResult(payload);
        addHistoryItem({
          id: jobId,
          label: payload?.videoInfo?.title || `Job ${jobId.slice(0, 8)}`,
          source: payload?.videoInfo?.source || "processed",
        });
      } catch (error) {
        if (!mounted) return;
        pushToast(error?.response?.data?.message || error.message || "Unable to load result.", "error");
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchResult();
    return () => {
      mounted = false;
    };
  }, [addHistoryItem, jobId, pushToast]);

  const handleGenerateBlog = async () => {
    setGeneratingBlog(true);
    try {
      await api.triggerBlog(jobId);
      pushToast("Blog generation started.");
      const payload = await api.getResult(jobId);
      setResult(payload);
    } catch (error) {
      pushToast(error?.response?.data?.message || error.message || "Could not generate blog.", "error");
    } finally {
      setGeneratingBlog(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <SkeletonBlock className="h-32" />
        <SkeletonBlock className="h-24" />
        <SkeletonBlock className="h-52" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ResultSections result={result} onToast={pushToast} />
      <div className="flex flex-wrap gap-3">
        {result?.summary && !result?.blog ? (
          <button
            onClick={handleGenerateBlog}
            disabled={generatingBlog}
            className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          >
            {generatingBlog ? "Starting blog generation..." : "Generate Blog"}
          </button>
        ) : null}
        <button
          onClick={() => navigate(`/?job_id=${encodeURIComponent(jobId)}`)}
          className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        >
          Back to Dashboard
        </button>
        <button
          onClick={() => navigate("/?new_chat=1")}
          className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        >
          New Video
        </button>
      </div>
    </div>
  );
}
