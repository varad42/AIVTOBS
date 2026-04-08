import { Navigate, Route, Routes } from "react-router-dom";
import { useCallback, useMemo, useState } from "react";
import AppLayout from "./components/AppLayout";
import AuthLayout from "./components/AuthLayout";
import ToastStack from "./components/ToastStack";
import HomePage from "./pages/HomePage";
import ModelSelectionPage from "./pages/ModelSelectionPage";
import ProcessingPage from "./pages/ProcessingPage";
import ResultPage from "./pages/ResultPage";
import LoginPage from "./pages/LoginPage";
import SignupPage from "./pages/SignupPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";

export default function App() {
  const [toasts, setToasts] = useState([]);

  const dismissToast = useCallback((id) => {
    setToasts((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const pushToast = useCallback(
    (message, type = "success") => {
      const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => dismissToast(id), 3500);
    },
    [dismissToast]
  );

  const sharedProps = useMemo(() => ({ pushToast }), [pushToast]);

  return (
    <>
      <Routes>
        <Route
          path="/"
          element={
            <AppLayout>
              <HomePage {...sharedProps} />
            </AppLayout>
          }
        />
        <Route
          path="/model/:jobId"
          element={
            <AppLayout>
              <ModelSelectionPage {...sharedProps} />
            </AppLayout>
          }
        />
        <Route
          path="/processing/:jobId"
          element={
            <AppLayout>
              <ProcessingPage {...sharedProps} />
            </AppLayout>
          }
        />
        <Route
          path="/result/:jobId"
          element={
            <AppLayout>
              <ResultPage {...sharedProps} />
            </AppLayout>
          }
        />
        <Route
          path="/login"
          element={
            <AuthLayout>
              <LoginPage />
            </AuthLayout>
          }
        />
        <Route
          path="/signup"
          element={
            <AuthLayout>
              <SignupPage />
            </AuthLayout>
          }
        />
        <Route
          path="/forgot-password"
          element={
            <AuthLayout>
              <ForgotPasswordPage />
            </AuthLayout>
          }
        />
        <Route
          path="/reset-password/:token"
          element={
            <AuthLayout>
              <ResetPasswordPage />
            </AuthLayout>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ToastStack toasts={toasts} onDismiss={dismissToast} />
    </>
  );
}
