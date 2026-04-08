export default function StatusFeed({ logs = [] }) {
  const defaults = [
    "Uploading video...",
    "Extracting audio...",
    "Transcribing...",
    "Generating summary...",
    "Generating blog...",
  ];
  const merged = logs.length ? logs : defaults;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        Live Status Logs
      </h2>
      <div className="max-h-64 space-y-2 overflow-auto rounded-xl bg-slate-950 p-3 text-sm text-emerald-300">
        {merged.map((line, index) => (
          <p key={`${line}-${index}`} className="font-mono">
            <span className="mr-2 text-slate-500">{">"}</span>
            {line}
          </p>
        ))}
      </div>
    </section>
  );
}
