import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

export default function ModelSelectionPage({ pushToast }) {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [jobTitle, setJobTitle] = useState("");
  const [modelOptions, setModelOptions] = useState([]);
  const [model, setModel] = useState("hybrid");

  useEffect(() => {
    let cancelled = false;

    const loadOptions = async () => {
      try {
        const state = await api.getModelSelection(jobId);
        if (cancelled) return;

        const options = Array.isArray(state.summary_model_options) ? state.summary_model_options : [];
        setJobTitle(state.job_title || `Job ${jobId}`);
        setModelOptions(options);
        const defaultOption = options.find((option) => option.checked) || options.find((option) => option.enabled !== false);
        setModel(defaultOption?.value || "hybrid");
      } catch (error) {
        if (!cancelled) {
          pushToast(error?.response?.data?.message || error.message || "Could not load model options.", "error");
        }
      } finally {
        if (!cancelled) {
          setPageLoading(false);
        }
      }
    };

    loadOptions();
    return () => {
      cancelled = true;
    };
  }, [jobId, pushToast]);

  const submit = async () => {
    setLoading(true);
    try {
      await api.startProcessing({ jobId, model });
      pushToast("Processing started.");
      navigate(`/processing/${jobId}`);
    } catch (error) {
      pushToast(error?.response?.data?.message || error.message || "Could not start processing.", "error");
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
        Loading model options...
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-xl font-bold">Model Selection</h1>
      <p className="mt-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
        Video name: <span className="font-normal">{jobTitle}</span>
      </p>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {modelOptions.map((option) => {
          const enabled = option.enabled !== false;
          const selected = model === option.value;
          return (
            <button
              key={option.value}
              type="button"
              disabled={!enabled}
              onClick={() => setModel(option.value)}
              className={`rounded-xl border px-4 py-3 text-left transition ${
                selected
                  ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
                  : "border-slate-300 dark:border-slate-700"
              } ${enabled ? "" : "cursor-not-allowed opacity-50"}`}
            >
              <p className="font-semibold">{option.label}</p>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{option.description}</p>
            </button>
          );
        })}
      </div>

      <button
        onClick={submit}
        disabled={loading || !model}
        className="mt-6 w-full rounded-xl bg-brand-600 px-4 py-3 font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {loading ? "Starting..." : "Start Processing"}
      </button>
    </section>
  );
}
