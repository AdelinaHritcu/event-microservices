import React, { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ui } from "../ui/styles";

export function LoginPage() {
  const { state, login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@test.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = useMemo(() => {
    return email.trim().length > 0 && password.trim().length > 0 && !submitting;
  }, [email, password, submitting]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      nav("/clients", { replace: true });
    } catch (err: any) {
      setError(err?.detail || "login failed");
    } finally {
      setSubmitting(false);
    }
  };

  if (state.status === "authenticated") {
    return (
      <div style={ui.page}>
        <div style={{ ...ui.card, maxWidth: 520, margin: "0 auto" }}>
          <h2 style={ui.title}>You are already logged in</h2>
          <div style={{ marginTop: 8, ...ui.muted }}>
            You can continue to the dashboard pages.
          </div>

          <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
            <button
              style={ui.button}
              onClick={() => nav("/clients", { replace: true })}
            >
              Go to Clients
            </button>
            <button
              style={ui.button}
              onClick={() => nav("/events", { replace: true })}
            >
              Go to Events
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={ui.page}>
      <div style={{ ...ui.card, maxWidth: 520, margin: "0 auto", padding: 16 }}>
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12 }}>
          <h2 style={ui.title}>Login</h2>
          <span style={ui.muted}>Authentication required</span>
        </div>

        <div style={{ marginTop: 8, ...ui.muted }}>
          Use your IDM credentials to obtain a bearer token.
        </div>

        {error ? <div style={ui.alertError}>{error}</div> : null}

        <form onSubmit={onSubmit} style={{ marginTop: 14 }}>
          <div style={{ display: "grid", gap: 12 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>Email</span>
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ ...ui.input, width: "100%" }}
                autoComplete="username"
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ ...ui.input, width: "100%" }}
                autoComplete="current-password"
              />
            </label>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
              <button
                type="submit"
                style={{
                  ...ui.button,
                  background: canSubmit ? "#111827" : "#f3f4f6",
                  color: canSubmit ? "#fff" : "#9ca3af",
                  borderColor: canSubmit ? "#111827" : "#e5e7eb",
                  cursor: canSubmit ? "pointer" : "not-allowed",
                }}
                disabled={!canSubmit}
              >
                {submitting ? "Signing in..." : "Login"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
