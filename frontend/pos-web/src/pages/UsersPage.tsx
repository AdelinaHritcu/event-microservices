import React, { useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { ui } from "../ui/styles";

const CLIENTS_API = import.meta.env.VITE_CLIENTS_API as string;

type User = { id: string; email: string; role: string };

// admin only: create owner-event / client accounts (IDM via Client WebService)
export function UsersPage() {
  const [users, setUsers] = useState<User[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"client" | "owner-event">("client");

  const load = async () => {
    try {
      setError(null);
      setUsers(await apiFetchAuthed<User[]>(CLIENTS_API, "/api/users", "GET"));
    } catch (e: any) {
      setError(e?.detail || "failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setError(null);
      await apiFetchAuthed(CLIENTS_API, "/api/users", "POST", { email, password, role });
      setEmail("");
      setPassword("");
      load();
    } catch (err: any) {
      setError(err?.detail || "create failed");
    }
  };

  const remove = async (id: string) => {
    try {
      await apiFetchAuthed(CLIENTS_API, `/api/users/${id}`, "DELETE");
      load();
    } catch (err: any) {
      setError(err?.detail || "delete failed");
    }
  };

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>Users</h2>
      </div>

      <form onSubmit={create} style={{ ...ui.card, ...ui.toolbar, marginBottom: 12 }}>
        <input style={ui.input} placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input
          style={ui.input}
          placeholder="password (min 6)"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <select style={ui.input} value={role} onChange={(e) => setRole(e.target.value as any)}>
          <option value="client">client</option>
          <option value="owner-event">owner-event</option>
        </select>
        <button style={ui.button} type="submit">
          Create user
        </button>
      </form>

      <div style={ui.card}>
        {error ? <div style={ui.alertError}>{error}</div> : null}
        {!users ? (
          <div style={{ padding: 12, ...ui.muted }}>Loading...</div>
        ) : (
          <div style={ui.tableWrap}>
            <table style={ui.table}>
              <thead>
                <tr>
                  <th style={ui.th}>ID</th>
                  <th style={ui.th}>Email</th>
                  <th style={ui.th}>Role</th>
                  <th style={ui.th}></th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td style={ui.td}>{u.id}</td>
                    <td style={ui.td}>{u.email}</td>
                    <td style={ui.td}>{u.role}</td>
                    <td style={ui.td}>
                      {u.role !== "admin" ? (
                        <button style={ui.button} onClick={() => remove(u.id)}>
                          Delete
                        </button>
                      ) : null}
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
