export const ui = {
  page: {
    maxWidth: 1100,
    margin: "0 auto",
    padding: 16,
  } as const,

  headerRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    marginBottom: 12,
  } as const,

  title: {
    margin: 0,
    fontSize: 22,
    fontWeight: 800,
    color: "#111827",
  } as const,

  card: {
    background: "#fff",
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
    padding: 12,
  } as const,

  toolbar: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    flexWrap: "wrap",
  } as const,

  input: {
    height: 36,
    padding: "0 10px",
    borderRadius: 10,
    border: "1px solid #e5e7eb",
    outline: "none",
    minWidth: 240,
  } as const,

  button: {
    height: 36,
    padding: "0 12px",
    borderRadius: 10,
    border: "1px solid #e5e7eb",
    background: "#f9fafb",
    cursor: "pointer",
    fontWeight: 700,
    color: "#111827",
  } as const,

  badge: {
    display: "inline-flex",
    alignItems: "center",
    height: 24,
    padding: "0 10px",
    borderRadius: 999,
    background: "#f3f4f6",
    border: "1px solid #e5e7eb",
    fontSize: 12,
    fontWeight: 700,
    color: "#111827",
  } as const,

  muted: {
    color: "#6b7280",
    fontSize: 13,
  } as const,

  alertError: {
    background: "#fff1f2",
    border: "1px solid #fecdd3",
    color: "#9f1239",
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
  } as const,

  tableWrap: {
    marginTop: 12,
    overflow: "auto",
    borderRadius: 12,
    border: "1px solid #e5e7eb",
  } as const,

  table: {
    width: "100%",
    borderCollapse: "separate",
    borderSpacing: 0,
  } as const,

  th: {
    textAlign: "left" as const,
    position: "sticky" as const,
    top: 0,
    background: "#f9fafb",
    borderBottom: "1px solid #e5e7eb",
    padding: "10px 12px",
    fontSize: 12,
    textTransform: "uppercase" as const,
    letterSpacing: 0.4,
    color: "#374151",
  } as const,

  td: {
    padding: "10px 12px",
    borderBottom: "1px solid #f1f5f9",
    fontSize: 14,
    color: "#111827",
    whiteSpace: "nowrap" as const,
  } as const,
};
