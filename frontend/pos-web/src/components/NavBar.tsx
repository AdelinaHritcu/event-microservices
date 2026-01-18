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

      <Link to="/clients" style={linkStyle(loc.pathname === "/clients")}>
        Clients
      </Link>
      <Link to="/packages" style={linkStyle(loc.pathname === "/packages")}>
        Packages
      </Link>
      <Link to="/events" style={linkStyle(loc.pathname === "/events")}>
        Events
      </Link>

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
          Logout
        </button>
      ) : (
        <Link to="/login" style={linkStyle(loc.pathname === "/login")}>
          Login
        </Link>
      )}
    </div>
  );
}
