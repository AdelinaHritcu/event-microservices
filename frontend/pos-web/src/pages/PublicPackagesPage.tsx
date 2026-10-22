import { useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { Pager } from "../components/Pager";
import { CLIENTS_API, EVENTS_API, query } from "../api/types";
import type { EventItem, PackageListResponse } from "../api/types";
import { ui } from "../ui/styles";

const PER_PAGE = 10;

// Events included in a package, loaded on demand
function PackageEvents({ packageId }: { packageId: number }) {
  const [events, setEvents] = useState<EventItem[] | null>(null);
  useEffect(() => {
    apiFetchAuthed<{ items: EventItem[] }>(EVENTS_API, `/api/event-manager/event-packets/${packageId}/events`, "GET")
      .then((r) => setEvents(r.items))
      .catch(() => setEvents([]));
  }, [packageId]);
  if (!events) return <span style={ui.muted}>...</span>;
  return <span style={ui.muted}>{events.map((e) => e.name).join(", ") || "no events yet"}</span>;
}

// Public: guests, clients and owners can browse event packages (Lab 6 / 2.2)
export function PublicPackagesPage() {
  const { state } = useAuth();
  const isClient = state.status === "authenticated" && state.role === "client";

  const [data, setData] = useState<PackageListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const [form, setForm] = useState({ name: "", event_name: "", type: "", location: "", available_tickets: "" });
  const [filters, setFilters] = useState(form);
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let cancelled = false;
    apiFetchAuthed<PackageListResponse>(
      EVENTS_API,
      `/api/event-manager/event-packets${query({ ...filters, page, items_per_page: PER_PAGE })}`,
      "GET"
    )
      .then((r) => !cancelled && (setData(r), setError(null)))
      .catch((e: { detail?: string }) => !cancelled && setError(e?.detail || "failed"));
    return () => {
      cancelled = true;
    };
  }, [filters, page, reload]);

  const field = (key: keyof typeof form, placeholder: string, type = "text") => (
    <input
      style={{ ...ui.input, minWidth: 170 }}
      type={type}
      placeholder={placeholder}
      value={form[key]}
      onChange={(e) => setForm({ ...form, [key]: e.target.value })}
    />
  );

  const buy = async (packageId: number) => {
    setNotice(null);
    try {
      await apiFetchAuthed(CLIENTS_API, "/api/clients/me/tickets", "POST", { package_id: packageId });
      setNotice("Ticket purchased. See it under My tickets.");
      setReload((x) => x + 1);
    } catch (e: unknown) {
      setError((e as { detail?: string })?.detail || "purchase failed");
    }
  };

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>Event packages</h2>
      </div>

      <div style={{ ...ui.card, ...ui.toolbar, marginBottom: 12 }}>
        {field("name", "Package name contains...")}
        {field("event_name", "Includes event named...")}
        {field("type", "Type (in description)...")}
        {field("location", "Location contains...")}
        {field("available_tickets", "Min. available", "number")}
        <button
          style={ui.button}
          onClick={() => {
            setPage(1);
            setFilters(form);
          }}
        >
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
                  <th style={ui.th}>Includes</th>
                  <th style={ui.th}>Available / seats</th>
                  {isClient ? <th style={ui.th}></th> : null}
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <tr key={p.id}>
                    <td style={ui.td}>{p.name}</td>
                    <td style={ui.td}>{p.location ?? "-"}</td>
                    <td style={{ ...ui.td, whiteSpace: "normal" }}>
                      <PackageEvents packageId={p.id} />
                    </td>
                    <td style={ui.td}>
                      {p.total_seats == null ? "not on sale" : `${p.available_tickets} / ${p.total_seats}`}
                    </td>
                    {isClient ? (
                      <td style={ui.td}>
                        <button style={ui.button} disabled={!p.available_tickets} onClick={() => buy(p.id)}>
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
        {data ? <Pager page={page} perPage={PER_PAGE} total={data.total_items} onPage={setPage} /> : null}
      </div>
    </div>
  );
}
