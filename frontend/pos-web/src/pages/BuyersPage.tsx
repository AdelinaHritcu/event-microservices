import { useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { ui } from "../ui/styles";

const CLIENTS_API = import.meta.env.VITE_CLIENTS_API as string;

type Ticket = { code: string; event_id?: number | null; package_id?: number | null; event_name?: string | null };
type Buyer = {
  id: string;
  first_name?: string | null;
  last_name?: string | null;
  social?: Record<string, string | boolean | null> | null;
  tickets: Ticket[];
};
type BuyersResponse = { items: Buyer[]; total_items: number };

// owner-event: public data of the clients who bought tickets for my events/packages
export function BuyersPage() {
  const [data, setData] = useState<BuyersResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetchAuthed<BuyersResponse>(CLIENTS_API, "/api/clients/buyers", "GET")
      .then(setData)
      .catch((e: any) => setError(e?.detail || "failed"));
  }, []);

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>Buyers of my events</h2>
      </div>
      <div style={ui.card}>
        <span style={ui.badge}>Total: {data?.total_items ?? "-"}</span>
        {error ? <div style={ui.alertError}>{error}</div> : null}
        {!data ? (
          <div style={{ padding: 12, ...ui.muted }}>Loading...</div>
        ) : data.items.length === 0 ? (
          <div style={{ padding: 12, ...ui.muted }}>No tickets sold yet.</div>
        ) : (
          <div style={ui.tableWrap}>
            <table style={ui.table}>
              <thead>
                <tr>
                  <th style={ui.th}>Name (if public)</th>
                  <th style={ui.th}>Social (if public)</th>
                  <th style={ui.th}>Tickets</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((b) => (
                  <tr key={b.id}>
                    <td style={ui.td}>{[b.first_name, b.last_name].filter(Boolean).join(" ") || "-"}</td>
                    <td style={ui.td}>
                      {b.social
                        ? Object.entries(b.social)
                            .filter(([k, v]) => k !== "public_social" && v)
                            .map(([k, v]) => `${k}: ${v}`)
                            .join(", ")
                        : "-"}
                    </td>
                    <td style={ui.td}>{b.tickets.map((t) => t.event_name || t.code).join(", ")}</td>
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
