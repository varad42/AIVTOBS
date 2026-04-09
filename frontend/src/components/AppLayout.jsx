import { Link, useNavigate } from "react-router-dom";
import HistorySidebar from "./HistorySidebar";
import ThemeToggle from "./ThemeToggle";
import { useDashboardState } from "../context/DashboardContext";
import api from "../services/api";

export default function AppLayout({ children }) {
  const navigate = useNavigate();
  const { dashboard, authenticated } = useDashboardState();

  const handleLogout = async () => {
    await api.logout();
    navigate("/login");
    window.location.reload();
  };

  return (
    <div className="app-shell-bg min-h-screen transition-colors duration-300">
      <div className="mx-auto grid min-h-screen w-full max-w-7xl grid-cols-1 gap-4 px-4 py-4 md:grid-cols-[260px_1fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 shadow-card dark:border-slate-800 dark:bg-slate-900/80">
            <div>
              {authenticated && dashboard?.user_email ? (
                <p className="text-base font-semibold text-slate-900 dark:text-slate-100">{dashboard.user_email}</p>
              ) : null}
            </div>
            <div className="mt-2 flex items-center gap-2">
              <ThemeToggle />
              {authenticated ? (
                <button
                  type="button"
                  onClick={handleLogout}
                  className="rounded-full border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
                >
                  Logout
                </button>
              ) : null}
            </div>
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
