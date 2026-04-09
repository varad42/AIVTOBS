import { useState } from "react";
import { Link } from "react-router-dom";
import { API_BASE_URL } from "../services/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [resetLink, setResetLink] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResetLink("");

    try {
      const body = new URLSearchParams();
      body.append("email", email);

      const response = await fetch(`${API_BASE_URL}/forgot-password`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
      });

      const html = await response.text();
      const match = html.match(/https?:\/\/[^\s"'<>]+/);
      if (match?.[0]) {
        setResetLink(match[0]);
      }

      if (!response.ok) {
        throw new Error("Could not create reset link.");
      }
    } catch (submitError) {
      setError(submitError.message || "Could not create reset link.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-2xl font-bold">Forgot password</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">We will generate your reset link.</p>

      <form onSubmit={submit} className="mt-5 space-y-3">
        <input
          name="email"
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="Enter your account email"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        {error ? <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p> : null}
        <button
          disabled={loading}
          className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Creating Reset Link..." : "Create Reset Link"}
        </button>
      </form>

      {resetLink ? (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-950/30 dark:text-emerald-100">
          <p className="font-semibold">Reset link created</p>
          <a href={resetLink} className="mt-2 block break-all underline">
            {resetLink}
          </a>
        </div>
      ) : null}

      <p className="mt-4 text-sm">
        Back to{" "}
        <Link to="/login" className="text-brand-600 hover:underline">
          Login
        </Link>
      </p>
    </section>
  );
}
