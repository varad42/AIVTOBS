export default function ThinkingAnimation() {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <div className="relative h-24 w-24">
        <span className="absolute inset-0 animate-ping rounded-full bg-brand-500/40" />
        <span className="absolute inset-2 animate-pulse rounded-full bg-brand-500/70" />
        <span className="absolute inset-6 rounded-full bg-brand-600" />
      </div>
      <p className="mt-5 text-sm font-medium text-slate-600 dark:text-slate-300">
        AI is thinking and generating your output...
      </p>
    </div>
  );
}
