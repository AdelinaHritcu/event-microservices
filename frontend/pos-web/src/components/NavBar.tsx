import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const linkStyle = (active: boolean) => ({
  padding: "8px 12px",
  borderRadius: 8,
  textDecoration: "none",
  fontWeight: 600,
  color: active ? "#111827" : "#374151",
  background: active ? "#e5e7eb" : "transparent",
});

const LINKS: Record<string, [string, string][]> = {
  admin: [
    ["/users", "Users"],
    ["/clients", "Clients"],
  ],
  "owner-event": [
    ["/events", "My events"],
    ["/packages", "Packages"],
    ["/buyers", "Buyers"],
    ["/browse/events", "Browse"],
  ],
  client: [
    ["/browse/events", "Events"],
    ["/browse/packages", "Packages"],
    ["/my-tickets", "My tickets"],
  ],
};

export function NavBar() {
  const { state, logout } = useAuth();
  const loc = useLocation();

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "12px 16px",
        borderBottom: "1px solid #e5e7eb",
        background: "#fafafa",
      }}
    >
      <strong style={{ marginRight: 16 }}>Event Manager</strong>

      {state.status === "authenticated"
        ? (LINKS[state.role] ?? []).map(([to, label]) => (
            <Link key={to} to={to} style={linkStyle(loc.pathname === to)}>
              {label}
            </Link>
          ))
        : null}

      <div style={{ flex: 1 }} />

      {state.status === "authenticated" ? (
        <button
          onClick={logout}
          style={{
            padding: "8px 12px",
            borderRadius: 8,
            border: "1px solid #e5e7eb",
            background: "#fff",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Logout ({state.email || state.role})
        </button>
      ) : (
        <Link to="/login" style={linkStyle(loc.pathname === "/login")}>
          Login
        </Link>
      )}
    </div>
  );
}
