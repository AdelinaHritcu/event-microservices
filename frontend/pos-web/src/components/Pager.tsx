import { ui } from "../ui/styles";

type PagerProps = {
  page: number;
  perPage: number;
  total: number;
  onPage: (page: number) => void;
};

// Server-side pagination (?page=&items_per_page=), Lab 2
export function Pager({ page, perPage, total, onPage }: PagerProps) {
  const pages = Math.max(1, Math.ceil(total / perPage));
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12 }}>
      <button style={ui.button} disabled={page <= 1} onClick={() => onPage(page - 1)}>
        ‹ Prev
      </button>
      <span style={ui.muted}>
        Page {page} / {pages} · {total} items
      </span>
      <button style={ui.button} disabled={page >= pages} onClick={() => onPage(page + 1)}>
        Next ›
      </button>
    </div>
  );
}
