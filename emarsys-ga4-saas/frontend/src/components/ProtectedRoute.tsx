import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLocale } from "../context/LocaleContext";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading, hasSupabaseConfig } = useAuth();
  const authDisabled = import.meta.env.VITE_AUTH_DISABLED === "true";
  const { t } = useLocale();

  if (authDisabled || !hasSupabaseConfig) {
    return <>{children}</>;
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-200">
        {t("common.loading")}
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
