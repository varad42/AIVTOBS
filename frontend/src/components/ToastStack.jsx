export default function ToastStack({ toasts, onDismiss }) {
  return (
    <div className="fixed right-4 top-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`min-w-[260px] rounded-xl border px-4 py-3 text-sm shadow-lg ${
            toast.type === "error"
              ? "border-rose-200 bg-rose-50 text-rose-900 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200"
              : "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200"
          }`}
        >
          <div className="flex items-start justify-between gap-2">
            <p>{toast.message}</p>
            <button onClick={() => onDismiss(toast.id)} className="text-xs opacity-70 hover:opacity-100">
              Close
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
