import React, { useEffect, useState } from "react";
import { apiFetchAuthed } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import { CLIENTS_API } from "../api/types";
import { ui } from "../ui/styles";

type Social = { facebook?: string | null; instagram?: string | null; tiktok?: string | null; public_social?: boolean | null };
type Profile = {
  id?: string;
  email?: string;
  first_name?: string | null;
  last_name?: string | null;
  public_name?: boolean | null;
  social?: Social | null;
};

const EMPTY: Profile = { first_name: "", last_name: "", public_name: false, social: { public_social: false } };

// client: manage own personal data (MongoDB document, mapped by email)
export function ProfilePage() {
  const { state } = useAuth();
  const email = state.status === "authenticated" ? state.email : "";

  const [profile, setProfile] = useState<Profile>(EMPTY);
  const [exists, setExists] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    apiFetchAuthed<Profile>(CLIENTS_API, "/api/clients/me", "GET")
      .then((p) => {
        setProfile({ ...EMPTY, ...p, social: { ...EMPTY.social, ...(p.social ?? {}) } });
        setExists(true);
      })
      .catch((e: { status?: number; detail?: string }) => {
        if (e?.status === 404) setExists(false); // no profile yet: offer to create it
        else setError(e?.detail || "failed");
      });
  }, []);

  const social = profile.social ?? {};
  const setSocial = (patch: Social) => setProfile({ ...profile, social: { ...social, ...patch } });

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setNotice(null);
    const body = {
      first_name: profile.first_name || null,
      last_name: profile.last_name || null,
      public_name: !!profile.public_name,
      social: {
        facebook: social.facebook || null,
        instagram: social.instagram || null,
        tiktok: social.tiktok || null,
        public_social: !!social.public_social,
      },
    };
    try {
      if (exists) {
        await apiFetchAuthed(CLIENTS_API, "/api/clients/me", "PUT", body);
      } else {
        await apiFetchAuthed(CLIENTS_API, "/api/clients", "POST", { ...body, email });
        setExists(true);
      }
      setNotice("Saved.");
    } catch (err: unknown) {
      setError((err as { detail?: string })?.detail || "save failed");
    }
  };

  const text = (value: string | null | undefined, onChange: (v: string) => void, placeholder: string) => (
    <input style={ui.input} placeholder={placeholder} value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
  );

  return (
    <div style={ui.page}>
      <div style={ui.headerRow}>
        <h2 style={ui.title}>My profile</h2>
        <span style={ui.muted}>{email}</span>
      </div>

      {exists === null && !error ? <div style={ui.muted}>Loading...</div> : null}
      {exists === false ? (
        <div style={{ ...ui.card, marginBottom: 12 }}>You have no profile yet. Fill in the form to create it.</div>
      ) : null}

      <form onSubmit={save} style={ui.card}>
        <strong>Name</strong>
        <div style={{ ...ui.toolbar, marginTop: 8 }}>
          {text(profile.first_name, (v) => setProfile({ ...profile, first_name: v }), "First name")}
          {text(profile.last_name, (v) => setProfile({ ...profile, last_name: v }), "Last name")}
          <label style={ui.muted}>
            <input
              type="checkbox"
              checked={!!profile.public_name}
              onChange={(e) => setProfile({ ...profile, public_name: e.target.checked })}
            />{" "}
            visible to event owners
          </label>
        </div>

        <div style={{ marginTop: 16 }}>
          <strong>Social media</strong>
        </div>
        <div style={{ ...ui.toolbar, marginTop: 8 }}>
          {text(social.facebook, (v) => setSocial({ facebook: v }), "Facebook")}
          {text(social.instagram, (v) => setSocial({ instagram: v }), "Instagram")}
          {text(social.tiktok, (v) => setSocial({ tiktok: v }), "TikTok")}
          <label style={ui.muted}>
            <input
              type="checkbox"
              checked={!!social.public_social}
              onChange={(e) => setSocial({ public_social: e.target.checked })}
            />{" "}
            visible to event owners
          </label>
        </div>

        <div style={{ ...ui.toolbar, marginTop: 16 }}>
          <button style={ui.button} type="submit" disabled={exists === null && !error}>
            {exists === false ? "Create profile" : "Save"}
          </button>
          {notice ? <span style={ui.muted}>{notice}</span> : null}
        </div>
        {error ? <div style={ui.alertError}>{error}</div> : null}
      </form>
    </div>
  );
}
