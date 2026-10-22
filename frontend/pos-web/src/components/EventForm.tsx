import React, { useState } from "react";
import type { EventPayload } from "../api/types";
import { ui } from "../ui/styles";

type EventFormProps = {
  title: string;
  initial?: EventPayload;
  /** total_seats cannot change after the first sale (backend returns 409) */
  seatsLocked?: boolean;
  onSubmit: (payload: EventPayload) => Promise<void>;
  onCancel: () => void;
};

// Shared by events and event packages: same fields (Lab 1, tables 1-2)
export function EventForm({ title, initial, seatsLocked, onSubmit, onCancel }: EventFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [location, setLocation] = useState(initial?.location ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [seats, setSeats] = useState(initial?.total_seats?.toString() ?? "");
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await onSubmit({
        name: name.trim(),
        location: location.trim() || null,
        description: description.trim() || null,
        total_seats: seats.trim() === "" ? null : Number(seats),
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} style={{ ...ui.card, marginBottom: 12 }}>
      <strong>{title}</strong>
      <div style={{ ...ui.toolbar, marginTop: 10 }}>
        <input style={ui.input} placeholder="Name *" value={name} onChange={(e) => setName(e.target.value)} />
        <input
          style={ui.input}
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <input
          style={{ ...ui.input, minWidth: 120 }}
          placeholder="Seats"
          type="number"
          min={0}
          value={seats}
          disabled={seatsLocked}
          title={seatsLocked ? "Tickets already sold: seats cannot be changed" : ""}
          onChange={(e) => setSeats(e.target.value)}
        />
      </div>
      <textarea
        style={{ ...ui.input, width: "100%", height: 60, marginTop: 8, padding: 8, boxSizing: "border-box" }}
        placeholder="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <div style={{ ...ui.toolbar, marginTop: 8 }}>
        <button style={ui.button} type="submit" disabled={busy || name.trim().length < 3}>
          Save
        </button>
        <button style={ui.button} type="button" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  );
}
