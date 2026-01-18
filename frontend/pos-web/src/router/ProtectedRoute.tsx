import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function ProtectedRoute({
  children,
  roles,
}: {
  children: React.ReactNode;
  roles?: string[];
}) {
  const { state } = useAuth();

  if (state.status === "loading") return <div>Loading...</div>;
  if (state.status !== "authenticated") return <Navigate to="/login" replace />;

  if (roles && roles.length > 0 && !roles.includes(state.role)) {
    return <div>Forbidden</div>;
  }

  return <>{children}</>;
}
