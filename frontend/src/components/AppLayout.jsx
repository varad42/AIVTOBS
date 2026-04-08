import { Link } from "react-router-dom";
import HistorySidebar from "./HistorySidebar";
import ThemeToggle from "./ThemeToggle";

export default function AppLayout({ children }) {
  return (
    <div className="app-shell-bg min-h-screen transition-colors duration-300">
      <div className="mx-auto grid min-h-screen w-full max-w-7xl grid-cols-1 gap-4 px-4 py-4 md:grid-cols-[260px_1fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 shadow-card dark:border-slate-800 dark:bg-slate-900/80">
            <Link to="/" className="text-sm font-semibold">
              AI Studio
            </Link>
            <ThemeToggle />
          </div>
          <HistorySidebar />
        </div>
        <main className="min-h-[85vh] rounded-2xl border border-slate-200 bg-white/70 p-4 shadow-card backdrop-blur dark:border-slate-800 dark:bg-slate-900/70">
          {children}
        </main>
      </div>
    </div>
  );
}
