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
    <div className={`app-shell-bg min-h-screen transition-colors duration-300 ${authenticated ? "" : "relative overflow-hidden"}`}>
      {!authenticated ? (
        <>
          <div className="pointer-events-none absolute -left-24 top-10 h-72 w-72 rounded-full bg-brand-500/10 blur-3xl" />
          <div className="pointer-events-none absolute right-[-5rem] top-1/3 h-80 w-80 rounded-full bg-emerald-500/10 blur-3xl" />
          <div className="pointer-events-none absolute bottom-[-6rem] left-1/2 h-96 w-96 -translate-x-1/2 rounded-full bg-slate-400/10 blur-3xl" />
        </>
      ) : null}
      <div className={`mx-auto min-h-screen w-full max-w-7xl gap-4 px-4 py-4 ${authenticated ? "grid grid-cols-1 md:grid-cols-[260px_1fr]" : "flex items-start justify-center"}`}>
        {authenticated ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 shadow-card dark:border-slate-800 dark:bg-slate-900/80">
            <div className="flex flex-col">
              {authenticated && dashboard?.user_email ? (
                <p className="text-base font-semibold text-slate-900 dark:text-slate-100">{dashboard.user_email}</p>
              ) : null}
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
          </div>
          <HistorySidebar />
        </div>
        ) : null}
        <main className={`min-h-[85vh] rounded-2xl border border-slate-200 bg-white/70 p-4 shadow-card backdrop-blur dark:border-slate-800 dark:bg-slate-900/70 ${authenticated ? "" : "w-full max-w-2xl"}`}>
          {children}
        </main>
      </div>
    </div>
  );
}
