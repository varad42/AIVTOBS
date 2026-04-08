export default function AuthLayout({ children }) {
  return (
    <div className="app-shell-bg min-h-screen px-4 py-8">
      <div className="mx-auto w-full max-w-md">{children}</div>
    </div>
  );
}
