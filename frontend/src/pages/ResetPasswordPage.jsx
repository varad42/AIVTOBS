import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { API_BASE_URL, extractFlashesFromHtml } from "../services/api";

export default function ResetPasswordPage() {
  const navigate = useNavigate();
  const { token } = useParams();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const body = new URLSearchParams();
      body.append("password", password);
      body.append("confirm_password", confirmPassword);

      const response = await fetch(`${API_BASE_URL}/reset-password/${token}`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body,
      });

      const html = await response.text();
      const flashes = extractFlashesFromHtml(html);
      const errorFlash = flashes.find((flash) => String(flash?.category || "").toLowerCase() === "error");

      if (errorFlash) {
        throw new Error(errorFlash.message || "Could not update password.");
      }

      navigate("/login?reset=success");
    } catch (submitError) {
      setError(submitError.message || "Could not update password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-slate-800 dark:bg-slate-900">
      <h1 className="text-2xl font-bold">Reset password</h1>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Set your new secure password.</p>

      <form onSubmit={submit} className="mt-5 space-y-3">
        <input
          name="password"
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="New password"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        <input
          name="confirm_password"
          type="password"
          required
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          placeholder="Confirm new password"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-800"
        />
        {error ? <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p> : null}
        <button
          disabled={loading}
          className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {loading ? "Updating Password..." : "Update Password"}
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
