import { Link, useParams } from "react-router-dom";
import { API_BASE_URL } from "../services/api";

export default function ResetPasswordPage() {
  const { token } = useParams();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-2xl font-bold">Reset password</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Set your new secure password.</p>

      <form method="POST" action={`${API_BASE_URL}/reset-password/${token}`} className="mt-5 space-y-3">
        <input
          name="password"
          type="password"
          required
          placeholder="New password"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        <input
          name="confirm_password"
          type="password"
          required
          placeholder="Confirm new password"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        <button className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700">
          Update Password
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
