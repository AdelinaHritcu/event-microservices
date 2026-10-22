export type Link = { href: string; type?: string };

export type EventItem = {
  id: number;
  id_owner: number;
  name: string;
  location?: string | null;
  description?: string | null;
  total_seats?: number | null;
  available_seats?: number | null;
  _links?: Record<string, Link>;
};

export type EventListResponse = {
  items: EventItem[];
  page: number;
  items_per_page: number;
  total: number;
};

export type PackageItem = {
  id: number;
  id_owner: number;
  name: string;
  location?: string | null;
  description?: string | null;
  total_seats?: number | null;
  available_tickets?: number | null;
  _links?: Record<string, Link>;
};

export type PackageListResponse = {
  items: PackageItem[];
  page: number;
  items_per_page: number;
  total_items: number;
};

export type TicketItem = {
  code: string;
  event_id?: number | null;
  package_id?: number | null;
};

export type TicketListResponse = {
  items: TicketItem[];
  page: number;
  items_per_page: number;
  total_items: number;
};

/** Body for POST/PUT on events and event-packets (owner is taken from the token). */
export type EventPayload = {
  name: string;
  location?: string | null;
  description?: string | null;
  total_seats?: number | null;
};

export const EVENTS_API = import.meta.env.VITE_EVENTS_API as string;
export const CLIENTS_API = import.meta.env.VITE_CLIENTS_API as string;

/** Builds "?a=1&b=x" from the non-empty values only. */
export function query(params: Record<string, string | number | null | undefined>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== null && v !== undefined && String(v).trim() !== "") q.set(k, String(v).trim());
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}
