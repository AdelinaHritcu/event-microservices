import { useEffect, useMemo, useState } from "react";
import { ui } from "../ui/styles";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";

const CLIENTS_API = import.meta.env.VITE_CLIENTS_API as string;

const EVENTS_API = import.meta.env.VITE_EVENTS_API as string;

type Link = { href: string; type?: string };

type PackageItem = {
  id: number;
  id_owner: number;
  name: string;
  location: string;
  description?: string | null;
  total_seats?: number | null;
  available_tickets?: number | null;
  links?: Record<string, Link>;
};

type PackageListResponse = {
  items: PackageItem[];
  page: number;
  items_per_page: number;
  total_items: number;
};

export function PublicPackagesPage() {
  const { state } = useAuth();
  const isClient = state.status === "authenticated" && state.role === "client";
  const [notice, setNotice] = useState<string | null>(null);

  const buy = async (id: number) => {
    setNotice(null);
    try {
      // chain call: Client WebService -> Event WebService
      await apiFetchAuthed(CLIENTS_API, "/api/clients/me/tickets", "POST", { package_id: id });
      setNotice("Ticket purchased. See it under My tickets.");
      load({ v: false });
    } catch (e: any) {
      setError(e?.detail || "purchase failed");
    }
  };
  const [data, setData] = useState<PackageListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = async (cancelled: { v: boolean }) => {
    try {
      setError(null);
      setData(null);

      const r = await apiFetchAuthed<PackageListResponse>(
        EVENTS_API,
        "/api/event-manager/event-packets?page=1&items_per_page=10",
        "GET"
      );

      if (!cancelled.v) setData(r);
    } catch (e: any) {
      if (!cancelled.v) setError(e?.detail || "failed");
    }
  };

  useEffect(() => {
    const cancelled = { v: false };
    load(cancelled);
    return () => {
      cancelled.v = true;
    };
  }, []);

  const items = useMemo(() => {
    if (!data) return [];
    const s = q.trim().toLowerCase();
    if (!s) return data.items;
    return data.items.filter((p) => {
      const id = String(p.id);
      return (
        id.includes(s) ||
        p.name.toLowerCase().includes(s) ||
        p.location.toLowerCase().includes(s)
      );
    });
  }, [data, q]);

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>Event packages</h2>

        <div style={ui.toolbar}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by id, name, location."
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
          <span style={ui.muted}>Service: {EVENTS_API}</span>
        </div>

        {error ? <div style={ui.alertError}>{error}</div> : null}
        {notice ? <div style={{ marginTop: 12, ...ui.muted }}>{notice}</div> : null}

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
                  <th style={ui.th}>Name</th>
                  <th style={ui.th}>Location</th>
                  <th style={ui.th}>Available</th>
                  {isClient ? <th style={ui.th}></th> : null}
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id}>
                    <td style={ui.td}>{p.id}</td>
                    <td style={ui.td}>{p.name}</td>
                    <td style={ui.td}>{p.location}</td>
                    <td style={ui.td}>{p.available_tickets ?? "-"}</td>
                    {isClient ? (
                      <td style={ui.td}>
                        <button style={ui.button} onClick={() => buy(p.id)}>
                          Buy
                        </button>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
