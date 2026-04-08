import { Link } from "react-router-dom";
import { API_BASE_URL } from "../services/api";

export default function LoginPage() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-2xl font-bold">Welcome back</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Sign in to continue your AI workflow.</p>

      <form method="POST" action={`${API_BASE_URL}/`} className="mt-5 space-y-3">
        <input
          name="email"
          type="email"
          required
          placeholder="Email address"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        <input
          name="password"
          type="password"
          required
          placeholder="Password"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        <button className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Login
        </button>
      </form>

      <a
        href={`${API_BASE_URL}/auth/google`}
        className="mt-3 block w-full rounded-xl border border-slate-300 px-4 py-2.5 text-center text-sm font-medium hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
      >
        Continue with Google
      </a>

      <div className="mt-4 flex items-center justify-between text-sm">
        <Link to="/forgot-password" className="text-brand-600 hover:underline">
          Forgot password?
        </Link>
        <Link to="/signup" className="text-brand-600 hover:underline">
          Create account
        </Link>
      </div>
    </section>
  );
}
