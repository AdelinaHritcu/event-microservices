import { Fragment, useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { EventForm } from "../components/EventForm";
import { Pager } from "../components/Pager";
import { TicketsList } from "../components/TicketsList";
import { EVENTS_API, query } from "../api/types";
import type { EventItem, EventListResponse, EventPayload } from "../api/types";
import { ui } from "../ui/styles";

const PER_PAGE = 10;
const BASE = "/api/event-manager/events";

type Editing = { mode: "create" } | { mode: "edit"; event: EventItem } | null;

// owner-event: full management of the events it created (ID_OWNER = sub)
export function EventsPage() {
  const { state } = useAuth();
  const ownerId = state.status === "authenticated" ? state.sub : "";

  const [data, setData] = useState<EventListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [reload, setReload] = useState(0);
  const [editing, setEditing] = useState<Editing>(null);
  const [openTickets, setOpenTickets] = useState<number | null>(null);

  useEffect(() => {
    if (!ownerId) return;
    let cancelled = false;
    apiFetchAuthed<EventListResponse>(
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
        ? apiFetchAuthed(EVENTS_API, `${BASE}/${editing.event.id}`, "PUT", payload)
        : apiFetchAuthed(EVENTS_API, BASE, "POST", payload)
    );

  const remove = (ev: EventItem) => {
    if (window.confirm(`Delete "${ev.name}"?`)) run(() => apiFetchAuthed(EVENTS_API, `${BASE}/${ev.id}`, "DELETE"));
  };

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>My events</h2>
        <button style={ui.button} onClick={() => setEditing({ mode: "create" })}>
          + New event
        </button>
      </div>

      {editing ? (
        <EventForm
          key={editing.mode === "edit" ? editing.event.id : "new"}
          title={editing.mode === "edit" ? `Edit "${editing.event.name}"` : "New event"}
          initial={editing.mode === "edit" ? editing.event : undefined}
          seatsLocked={
            editing.mode === "edit" &&
            editing.event.total_seats != null &&
            editing.event.available_seats !== editing.event.total_seats
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
          <div style={{ padding: 12, ...ui.muted }}>You have no events yet.</div>
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
                {data.items.map((ev) => (
                  <Fragment key={ev.id}>
                    <tr>
                      <td style={ui.td}>{ev.name}</td>
                      <td style={ui.td}>{ev.location ?? "-"}</td>
                      <td style={ui.td}>
                        {ev.total_seats == null ? "not set" : `${ev.available_seats} / ${ev.total_seats}`}
                      </td>
                      <td style={{ ...ui.td, display: "flex", gap: 6 }}>
                        <button style={ui.button} onClick={() => setEditing({ mode: "edit", event: ev })}>
                          Edit
                        </button>
                        <button
                          style={ui.button}
                          onClick={() => setOpenTickets(openTickets === ev.id ? null : ev.id)}
                        >
                          Tickets
                        </button>
                        <button style={ui.button} onClick={() => remove(ev)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                    {openTickets === ev.id ? (
                      <tr>
                        <td style={{ ...ui.td, whiteSpace: "normal" }} colSpan={4}>
                          <TicketsList basePath={`${BASE}/${ev.id}`} />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data ? <Pager page={page} perPage={PER_PAGE} total={data.total} onPage={setPage} /> : null}
      </div>
    </div>
  );
}
