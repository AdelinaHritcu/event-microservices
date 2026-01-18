import { useEffect, useMemo, useState } from "react";
import { ui } from "../ui/styles";

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

async function apiFetchPublic<T>(baseUrl: string, path: string, method: string): Promise<T> {
  const r = await fetch(`${baseUrl}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
  });

  const text = await r.text();
  const body = text ? JSON.parse(text) : null;

  if (!r.ok) {
    throw body ?? { detail: `HTTP ${r.status}` };
  }
  return body as T;
}

export function PublicPackagesPage() {
  const [data, setData] = useState<PackageListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = async (cancelled: { v: boolean }) => {
    try {
      setError(null);
      setData(null);

      const r = await apiFetchPublic<PackageListResponse>(
        EVENTS_API,
        "/api/event-manager/packages?page=1&items_per_page=10",
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
        <h2 style={ui.title}>Public Packages</h2>

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
                </tr>
              </thead>
              <tbody>
                {items.map((p) => (
                  <tr key={p.id}>
                    <td style={ui.td}>{p.id}</td>
                    <td style={ui.td}>{p.name}</td>
                    <td style={ui.td}>{p.location}</td>
                    <td style={ui.td}>{p.available_tickets ?? "-"}</td>
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
