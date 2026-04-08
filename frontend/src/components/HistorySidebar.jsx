import { useNavigate } from "react-router-dom";
import { useHistoryState } from "../context/HistoryContext";

export default function HistorySidebar() {
  const { history } = useHistoryState();
  const navigate = useNavigate();

  return (
    <aside className="h-full rounded-2xl border border-slate-200 bg-white/80 p-4 shadow-card backdrop-blur dark:border-slate-800 dark:bg-slate-900/75">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        History
      </h2>
      <div className="space-y-2">
        {history.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-3 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
            No processed videos yet.
          </div>
        ) : (
          history.map((item) => (
            <button
              key={item.id}
              onClick={() => navigate(`/result/${item.id}`)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-left text-sm transition hover:border-brand-500 hover:bg-brand-50 dark:border-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700"
            >
              <p className="truncate font-medium text-slate-800 dark:text-slate-100">{item.label}</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{item.source}</p>
            </button>
          ))
        )}
      </div>
    </aside>
  );
}
