import { useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { EVENTS_API } from "../api/types";
import type { TicketListResponse } from "../api/types";
import { ui } from "../ui/styles";

// Tickets sold for one of the owner's events / packages
export function TicketsList({ basePath }: { basePath: string }) {
  const [data, setData] = useState<TicketListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetchAuthed<TicketListResponse>(EVENTS_API, `${basePath}/tickets?items_per_page=100`, "GET")
      .then(setData)
      .catch((e: { detail?: string }) => setError(e?.detail || "failed"));
  }, [basePath]);

  if (error) return <div style={ui.alertError}>{error}</div>;
  if (!data) return <span style={ui.muted}>Loading tickets...</span>;
  if (data.items.length === 0) return <span style={ui.muted}>No tickets sold yet.</span>;
  return (
    <span style={ui.muted}>
      {data.total_items} sold: {data.items.map((t) => t.code).join(", ")}
    </span>
  );
}
