import { Fragment, useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { EventForm } from "../components/EventForm";
import { Pager } from "../components/Pager";
import { TicketsList } from "../components/TicketsList";
import { EVENTS_API, query } from "../api/types";
import type { EventItem, EventListResponse, EventPayload, PackageItem, PackageListResponse } from "../api/types";
import { ui } from "../ui/styles";

const PER_PAGE = 10;
const BASE = "/api/event-manager/event-packets";

type Editing = { mode: "create" } | { mode: "edit"; pkg: PackageItem } | null;

// Events included in a package: add / remove (PUT / DELETE /event-packets/{id}/events/{eid})
function PackageEventsEditor({
  pkg,
  allEvents,
  onError,
  onChanged,
}: {
  pkg: PackageItem;
  allEvents: EventItem[];
  onError: (msg: string) => void;
  onChanged: () => void;
}) {
  const [included, setIncluded] = useState<EventItem[] | null>(null);
  const [selected, setSelected] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    apiFetchAuthed<{ items: EventItem[] }>(EVENTS_API, `${BASE}/${pkg.id}/events`, "GET")
      .then((r) => setIncluded(r.items))
      .catch((e: { detail?: string }) => onError(e?.detail || "failed"));
  }, [pkg.id, reload, onError]);

  const change = async (method: "PUT" | "DELETE", eventId: number) => {
    try {
      await apiFetchAuthed(EVENTS_API, `${BASE}/${pkg.id}/events/${eventId}`, method);
      setReload((x) => x + 1);
      setSelected("");
      onChanged();
    } catch (e: unknown) {
      onError((e as { detail?: string })?.detail || "request failed");
    }
  };

  if (!included) return <span style={ui.muted}>Loading...</span>;
  const candidates = allEvents.filter((e) => !included.some((i) => i.id === e.id));

  return (
    <div>
      <div style={{ ...ui.toolbar, marginBottom: 8 }}>
        {included.length === 0 ? <span style={ui.muted}>No events in this package.</span> : null}
        {included.map((e) => (
          <span key={e.id} style={ui.badge}>
            {e.name} ({e.total_seats ?? "no"} seats)
            <button
              style={{ marginLeft: 6, border: "none", background: "none", cursor: "pointer" }}
              title="Remove from package"
              onClick={() => change("DELETE", e.id)}
            >
              ✕
            </button>
          </span>
        ))}
      </div>
      <div style={ui.toolbar}>
        <select style={ui.input} value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Add an event...</option>
          {candidates.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name} ({e.total_seats ?? "no"} seats)
            </option>
          ))}
        </select>
        <button style={ui.button} disabled={!selected} onClick={() => change("PUT", Number(selected))}>
          Add
        </button>
        <span style={ui.muted}>Package seats must not exceed the seats of any included event.</span>
      </div>
    </div>
  );
}

// owner-event: full management of the packages it created
export function PackagesPage() {
  const { state } = useAuth();
  const ownerId = state.status === "authenticated" ? state.sub : "";

  const [data, setData] = useState<PackageListResponse | null>(null);
  const [allEvents, setAllEvents] = useState<EventItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);
  const [editing, setEditing] = useState<Editing>(null);
  const [open, setOpen] = useState<{ id: number; panel: "events" | "tickets" } | null>(null);

  useEffect(() => {
    if (!ownerId) return;
    let cancelled = false;
    apiFetchAuthed<PackageListResponse>(
      EVENTS_API,
      `${BASE}${query({ id_owner: ownerId, page, items_per_page: PER_PAGE })}`,
      "GET"
    )
      .then((r) => !cancelled && setData(r))
      .catch((e: { detail?: string }) => !cancelled && setError(e?.detail || "failed"));
    return () => {
      cancelled = true;
    };
  }, [ownerId, page, reload]);

  useEffect(() => {
    // events that can be included in a package
    apiFetchAuthed<EventListResponse>(EVENTS_API, "/api/event-manager/events?items_per_page=100", "GET")
      .then((r) => setAllEvents(r.items))
      .catch(() => setAllEvents([]));
  }, []);

  const run = async (action: () => Promise<unknown>) => {
    setError(null);
    try {
      await action();
      setEditing(null);
      setReload((x) => x + 1);
    } catch (e: unknown) {
      setError((e as { detail?: string })?.detail || "request failed");
    }
  };

  const save = (payload: EventPayload) =>
    run(() =>
      editing?.mode === "edit"
        ? apiFetchAuthed(EVENTS_API, `${BASE}/${editing.pkg.id}`, "PUT", payload)
        : apiFetchAuthed(EVENTS_API, BASE, "POST", payload)
    );

  const remove = (p: PackageItem) => {
    if (window.confirm(`Delete "${p.name}"?`)) run(() => apiFetchAuthed(EVENTS_API, `${BASE}/${p.id}`, "DELETE"));
  };

  const toggle = (id: number, panel: "events" | "tickets") =>
    setOpen(open?.id === id && open.panel === panel ? null : { id, panel });

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>My event packages</h2>
        <button style={ui.button} onClick={() => setEditing({ mode: "create" })}>
          + New package
        </button>
      </div>

      {editing ? (
        <EventForm
          key={editing.mode === "edit" ? editing.pkg.id : "new"}
          title={editing.mode === "edit" ? `Edit "${editing.pkg.name}"` : "New package"}
          initial={editing.mode === "edit" ? editing.pkg : undefined}
          seatsLocked={
            editing.mode === "edit" &&
            editing.pkg.total_seats != null &&
            editing.pkg.available_tickets !== editing.pkg.total_seats
          }
          onSubmit={save}
          onCancel={() => setEditing(null)}
        />
      ) : null}

      <div style={ui.card}>
        {error ? <div style={ui.alertError}>{error}</div> : null}
        {!data ? (
          <div style={{ padding: 12, ...ui.muted }}>Loading...</div>
        ) : data.items.length === 0 ? (
          <div style={{ padding: 12, ...ui.muted }}>You have no packages yet.</div>
        ) : (
          <div style={ui.tableWrap}>
            <table style={ui.table}>
              <thead>
                <tr>
                  <th style={ui.th}>Name</th>
                  <th style={ui.th}>Location</th>
                  <th style={ui.th}>Available / seats</th>
                  <th style={ui.th}></th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((p) => (
                  <Fragment key={p.id}>
                    <tr>
                      <td style={ui.td}>{p.name}</td>
                      <td style={ui.td}>{p.location ?? "-"}</td>
                      <td style={ui.td}>
                        {p.total_seats == null ? "not set" : `${p.available_tickets} / ${p.total_seats}`}
                      </td>
                      <td style={{ ...ui.td, display: "flex", gap: 6 }}>
                        <button style={ui.button} onClick={() => setEditing({ mode: "edit", pkg: p })}>
                          Edit
                        </button>
                        <button style={ui.button} onClick={() => toggle(p.id, "events")}>
                          Events
                        </button>
                        <button style={ui.button} onClick={() => toggle(p.id, "tickets")}>
                          Tickets
                        </button>
                        <button style={ui.button} onClick={() => remove(p)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                    {open?.id === p.id ? (
                      <tr>
                        <td style={{ ...ui.td, whiteSpace: "normal" }} colSpan={4}>
                          {open.panel === "events" ? (
                            <PackageEventsEditor
                              pkg={p}
                              allEvents={allEvents}
                              onError={setError}
                              onChanged={() => setError(null)}
                            />
                          ) : (
                            <TicketsList basePath={`${BASE}/${p.id}`} />
                          )}
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
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
