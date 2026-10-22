import { useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { Pager } from "../components/Pager";
import { CLIENTS_API, EVENTS_API, query } from "../api/types";
import type { EventListResponse } from "../api/types";
import { ui } from "../ui/styles";

const PER_PAGE = 10;

// Public: guests, clients and owners can browse events (Lab 6 / 2.2)
export function PublicEventsPage() {
  const { state } = useAuth();
  const isClient = state.status === "authenticated" && state.role === "client";

  const [data, setData] = useState<EventListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // filter inputs, and the filters actually applied (sent to the API)
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [minAvailable, setMinAvailable] = useState("");
  const [filters, setFilters] = useState({ name: "", location: "", available_tickets: "" });
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    apiFetchAuthed<EventListResponse>(
      EVENTS_API,
      `/api/event-manager/events${query({ ...filters, page, items_per_page: PER_PAGE })}`,
      "GET"
    )
      .then((r) => !cancelled && (setData(r), setError(null)))
      .catch((e: { detail?: string }) => !cancelled && setError(e?.detail || "failed"));
    return () => {
      cancelled = true;
    };
  }, [filters, page, reload]);

  const search = () => {
    setPage(1);
    setFilters({ name, location, available_tickets: minAvailable });
  };

  const buy = async (eventId: number) => {
    setNotice(null);
    try {
      // chain call: Client WebService -> Event WebService
      await apiFetchAuthed(CLIENTS_API, "/api/clients/me/tickets", "POST", { event_id: eventId });
      setNotice("Ticket purchased. See it under My tickets.");
      setReload((x) => x + 1);
    } catch (e: unknown) {
      setError((e as { detail?: string })?.detail || "purchase failed");
    }
  };

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>Events</h2>
      </div>

      <div style={{ ...ui.card, ...ui.toolbar, marginBottom: 12 }}>
        <input style={ui.input} placeholder="Name contains..." value={name} onChange={(e) => setName(e.target.value)} />
        <input
          style={ui.input}
          placeholder="Location contains..."
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <input
          style={{ ...ui.input, minWidth: 160 }}
          type="number"
          min={0}
          placeholder="Min. available tickets"
          value={minAvailable}
          onChange={(e) => setMinAvailable(e.target.value)}
        />
        <button style={ui.button} onClick={search}>
          Search
        </button>
      </div>

      <div style={ui.card}>
        {error ? <div style={ui.alertError}>{error}</div> : null}
        {notice ? <div style={{ marginBottom: 8, ...ui.muted }}>{notice}</div> : null}

        {!data ? (
          <div style={{ padding: 12, ...ui.muted }}>Loading...</div>
        ) : data.items.length === 0 ? (
          <div style={{ padding: 12, ...ui.muted }}>No results.</div>
        ) : (
          <div style={ui.tableWrap}>
            <table style={ui.table}>
              <thead>
                <tr>
                  <th style={ui.th}>Name</th>
                  <th style={ui.th}>Location</th>
                  <th style={ui.th}>Description</th>
                  <th style={ui.th}>Available / seats</th>
                  {isClient ? <th style={ui.th}></th> : null}
                </tr>
              </thead>
              <tbody>
                {data.items.map((ev) => (
                  <tr key={ev.id}>
                    <td style={ui.td}>{ev.name}</td>
                    <td style={ui.td}>{ev.location ?? "-"}</td>
                    <td style={{ ...ui.td, whiteSpace: "normal" }}>{ev.description ?? "-"}</td>
                    <td style={ui.td}>
                      {ev.total_seats == null ? "not on sale" : `${ev.available_seats} / ${ev.total_seats}`}
                    </td>
                    {isClient ? (
                      <td style={ui.td}>
                        <button
                          style={ui.button}
                          disabled={!ev.available_seats}
                          onClick={() => buy(ev.id)}
                        >
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
        {data ? <Pager page={page} perPage={PER_PAGE} total={data.total} onPage={setPage} /> : null}
        {state.status !== "authenticated" ? (
          <div style={{ marginTop: 8, ...ui.muted }}>Log in as a client to buy tickets.</div>
        ) : null}
      </div>
    </div>
  );
}
