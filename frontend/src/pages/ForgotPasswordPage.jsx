import { Link } from "react-router-dom";
import { API_BASE_URL } from "../services/api";

export default function ForgotPasswordPage() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-2xl font-bold">Forgot password</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">We will generate your reset link.</p>

      <form method="POST" action={`${API_BASE_URL}/forgot-password`} className="mt-5 space-y-3">
        <input
          name="email"
          type="email"
          required
          placeholder="Enter your account email"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        <button className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Create Reset Link
        </button>
      </form>

      <p className="mt-4 text-sm">
        Back to{" "}
        <Link to="/login" className="text-brand-600 hover:underline">
          Login
        </Link>
      </p>
    </section>
  );
}
