import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../services/api";

export default function ModelSelectionPage({ pushToast }) {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [model, setModel] = useState("t5");
  const [length, setLength] = useState("medium");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      await api.startProcessing({ jobId, model, length });
      pushToast("Processing started.");
      navigate(`/processing/${jobId}`);
    } catch (error) {
      pushToast(error?.response?.data?.message || error.message || "Could not start processing.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-xl font-bold">Model Selection</h1>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Job: {jobId}</p>

      <div className="mt-5 grid gap-3 md:grid-cols-2">
        {[
          { id: "t5", label: "T5" },
          { id: "bart", label: "BART" },
        ].map((option) => (
          <button
            key={option.id}
            onClick={() => setModel(option.id)}
            className={`rounded-xl border px-4 py-3 text-left ${
              model === option.id
                ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
                : "border-slate-300 dark:border-slate-700"
            }`}
          >
            <p className="font-semibold">{option.label}</p>
          </button>
        ))}
      </div>

      <div className="mt-5">
        <p className="mb-2 text-sm font-medium">Summary Length</p>
        <div className="flex flex-wrap gap-2">
          {["short", "medium", "long"].map((item) => (
            <button
              key={item}
              onClick={() => setLength(item)}
              className={`rounded-lg px-4 py-2 text-sm ${
                length === item
                  ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                  : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200"
              }`}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={submit}
        disabled={loading}
        className="mt-6 w-full rounded-xl bg-brand-600 px-4 py-3 font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
      >
        {loading ? "Starting..." : "Start Processing"}
      </button>
    </section>
  );
}
