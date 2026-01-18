import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { clearToken, getToken, setToken } from "./session";
import { login as loginApi } from "./authApi";
import { parseJwt, isExpired } from "./jwt";

type AuthState =
  | { status: "anonymous" }
  | { status: "loading" }
  | { status: "authenticated"; token: string; sub: string; role: string };

type AuthCtx = {
  state: AuthState;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    const t = getToken();
    if (!t) {
      setState({ status: "anonymous" });
      return;
    }

    try {
      const payload = parseJwt(t);
      if (isExpired(payload)) throw new Error("token expired");

      const sub = String(payload.sub ?? "");
      const role = String(payload.role ?? "");

      if (!sub || !role) throw new Error("missing claims");

      setState({ status: "authenticated", token: t, sub, role });
    } catch {
      clearToken();
      setState({ status: "anonymous" });
    }
  }, []);

  const value = useMemo<AuthCtx>(
    () => ({
      state,
      login: async (email, password) => {
        setState({ status: "loading" });

        const t = await loginApi(email, password);
        setToken(t);

        const payload = parseJwt(t);
        if (isExpired(payload)) throw new Error("token expired");

        const sub = String(payload.sub ?? "");
        const role = String(payload.role ?? "");
        if (!sub || !role) throw new Error("missing claims");

        setState({ status: "authenticated", token: t, sub, role });
      },
      logout: () => {
        clearToken();
        setState({ status: "anonymous" });
      },
    }),
    [state]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("AuthProvider missing");
  return v;
}
