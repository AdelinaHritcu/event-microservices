import { useEffect, useMemo, useState } from "react";
import { ui } from "../ui/styles";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";

const CLIENTS_API = import.meta.env.VITE_CLIENTS_API as string;

const EVENTS_API = import.meta.env.VITE_EVENTS_API as string;

type Link = { href: string; type?: string };

type EventItem = {
  id: number;
  id_owner: number;
  name: string;
  location: string;
  description?: string | null;
  total_seats?: number | null;
  available_seats?: number | null;
  links?: Record<string, Link>;
};

type EventListResponse = {
  items: EventItem[];
  page: number;
  items_per_page: number;
  total: number;
};

export function PublicEventsPage() {
  const { state } = useAuth();
  const isClient = state.status === "authenticated" && state.role === "client";
  const [notice, setNotice] = useState<string | null>(null);

  const buy = async (id: number) => {
    setNotice(null);
    try {
      // chain call: Client WebService -> Event WebService
      await apiFetchAuthed(CLIENTS_API, "/api/clients/me/tickets", "POST", { event_id: id });
      setNotice("Ticket purchased. See it under My tickets.");
      load({ v: false });
    } catch (e: any) {
      setError(e?.detail || "purchase failed");
    }
  };
  const [data, setData] = useState<EventListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = async (cancelled: { v: boolean }) => {
    try {
      setError(null);
      setData(null);

      const r = await apiFetchAuthed<EventListResponse>(
        EVENTS_API,
        "/api/event-manager/events?page=1&items_per_page=10",
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
    return data.items.filter((ev) => {
      const id = String(ev.id);
      return (
        id.includes(s) ||
        ev.name.toLowerCase().includes(s) ||
        ev.location.toLowerCase().includes(s)
      );
    });
  }, [data, q]);

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>Events</h2>

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
          <span style={ui.badge}>Total: {data?.total ?? "-"}</span>
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
                {items.map((ev) => (
                  <tr key={ev.id}>
                    <td style={ui.td}>{ev.id}</td>
                    <td style={ui.td}>{ev.name}</td>
                    <td style={ui.td}>{ev.location}</td>
                    <td style={ui.td}>{ev.available_seats ?? "-"}</td>
                    {isClient ? (
                      <td style={ui.td}>
                        <button style={ui.button} onClick={() => buy(ev.id)}>
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
