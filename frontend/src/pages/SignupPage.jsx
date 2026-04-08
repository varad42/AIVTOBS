import { Link } from "react-router-dom";
import { API_BASE_URL } from "../services/api";

export default function SignupPage() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-2xl font-bold">Create account</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Start summarizing videos in minutes.</p>

      <form method="POST" action={`${API_BASE_URL}/register`} className="mt-5 space-y-3">
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
          placeholder="Password (min 8 chars)"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        <button className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Sign Up
        </button>
      </form>

      <p className="mt-4 text-sm">
        Already have an account?{" "}
        <Link to="/login" className="text-brand-600 hover:underline">
          Login
        </Link>
      </p>
    </section>
  );
}
