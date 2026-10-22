import { useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { ui } from "../ui/styles";

const CLIENTS_API = import.meta.env.VITE_CLIENTS_API as string;

type Ticket = {
  code: string;
  event_id?: number | null;
  package_id?: number | null;
  event_name?: string | null;
  location?: string | null;
  events?: { id: number; name: string }[] | null;
};
type TicketsResponse = { client_id: string; email: string; items: Ticket[] };
type Validation = { ticket_code: string; is_valid: boolean };

// client: tickets stored in my MongoDB document, validated through Event WebService
export function MyTicketsPage() {
  const [data, setData] = useState<TicketsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checked, setChecked] = useState<Record<string, boolean>>({});

  useEffect(() => {
    apiFetchAuthed<TicketsResponse>(CLIENTS_API, "/api/clients/me/tickets", "GET")
      .then(setData)
      .catch((e: any) => setError(e?.detail || "failed"));
  }, []);

  const validate = async (code: string) => {
    if (!data) return;
    try {
      const r = await apiFetchAuthed<Validation>(
        CLIENTS_API,
        `/api/clients/${data.client_id}/tickets/${code}`,
        "GET"
      );
      setChecked((c) => ({ ...c, [code]: r.is_valid }));
    } catch (e: any) {
      setError(e?.detail || "validation failed");
    }
  };

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>My tickets</h2>
      </div>
      <div style={ui.card}>
        {error ? <div style={ui.alertError}>{error}</div> : null}
        {!data ? (
          <div style={{ padding: 12, ...ui.muted }}>{error ? "" : "Loading..."}</div>
        ) : data.items.length === 0 ? (
          <div style={{ padding: 12, ...ui.muted }}>No tickets yet.</div>
        ) : (
          <div style={ui.tableWrap}>
            <table style={ui.table}>
              <thead>
                <tr>
                  <th style={ui.th}>Code</th>
                  <th style={ui.th}>Event / package</th>
                  <th style={ui.th}>Location</th>
                  <th style={ui.th}>Included events</th>
                  <th style={ui.th}></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((t) => (
                  <tr key={t.code}>
                    <td style={ui.td}>{t.code.slice(0, 10)}…</td>
                    <td style={ui.td}>{t.event_name ?? "-"}</td>
                    <td style={ui.td}>{t.location ?? "-"}</td>
                    <td style={ui.td}>{t.events?.map((e) => e.name).join(", ") || "-"}</td>
                    <td style={ui.td}>
                      {t.code in checked ? (
                        <span style={ui.badge}>{checked[t.code] ? "valid" : "invalid"}</span>
                      ) : (
                        <button style={ui.button} onClick={() => validate(t.code)}>
                          Validate
                        </button>
                      )}
                    </td>
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
