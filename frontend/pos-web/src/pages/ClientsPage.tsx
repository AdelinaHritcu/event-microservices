import { useEffect, useMemo, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { ui } from "../ui/styles";

const CLIENTS_API = import.meta.env.VITE_CLIENTS_API as string;

type Link = { href: string; type?: string };

type ClientOut = {
  _id?: string;
  id?: string;
  email: string;
  tickets?: any[];
  links?: Record<string, Link>;
};

type ClientsListResponse = {
  items: ClientOut[];
  page: number;
  items_per_page: number;
  total_items: number;
};

export function ClientsPage() {
  const { state } = useAuth();
  const [data, setData] = useState<ClientsListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = async (cancelled: { v: boolean }) => {
    try {
      setError(null);
      setData(null);

      const r = await apiFetchAuthed<ClientsListResponse>(
        CLIENTS_API,
        "/api/clients?page=1&items_per_page=10",
        "GET"
      );

      if (!cancelled.v) setData(r);
    } catch (e: any) {
      if (!cancelled.v) setError(e?.detail || "failed");
    }
  };

  useEffect(() => {
    if (state.status !== "authenticated") return;
    const cancelled = { v: false };
    load(cancelled);
    return () => {
      cancelled.v = true;
    };
  }, [state.status]);

  const items = useMemo(() => {
    if (!data) return [];
    const s = q.trim().toLowerCase();
    if (!s) return data.items;
    return data.items.filter((c) => {
      const id = String(c._id ?? c.id ?? "");
      return c.email.toLowerCase().includes(s) || id.toLowerCase().includes(s);
    });
  }, [data, q]);

  if (state.status !== "authenticated") return null;

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>Clients</h2>
        <div style={ui.toolbar}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by email or id..."
            style={ui.input}
          />
          <button
            style={ui.button}
            onClick={() => {
              const cancelled = { v: false };
              load(cancelled);
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      <div style={ui.card}>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <span style={ui.badge}>Total: {data?.total_items ?? "-"}</span>
          <span style={ui.badge}>Shown: {data ? items.length : "-"}</span>
          <span style={ui.muted}>Service: {CLIENTS_API}</span>
        </div>

        {error ? <div style={ui.alertError}>{error}</div> : null}

        {!data ? (
          <div style={{ padding: 12, ...ui.muted }}>Loading...</div>
        ) : items.length === 0 ? (
          <div style={{ padding: 12, ...ui.muted }}>No results.</div>
        ) : (
          <div style={ui.tableWrap}>
            <table style={ui.table}>
              <thead>
                <tr>
                  <th style={ui.th}>ID</th>
                  <th style={ui.th}>Email</th>
                  <th style={ui.th}>Tickets</th>
                </tr>
              </thead>
              <tbody>
                {items.map((c) => {
                  const id = c._id ?? c.id ?? "-";
                  return (
                    <tr key={`${id}-${c.email}`}>
                      <td style={ui.td}>{id}</td>
                      <td style={ui.td}>{c.email}</td>
                      <td style={ui.td}>{(c.tickets || []).length}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
