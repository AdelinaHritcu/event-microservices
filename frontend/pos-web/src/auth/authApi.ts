import { apiFetch } from "../api/http";

const AUTH_API = import.meta.env.VITE_AUTH_API as string;

type LoginResponse = { access_token: string };
type MeResponse = { sub: string; role: string };

export async function login(email: string, password: string): Promise<string> {
  const r = await apiFetch<LoginResponse>(
    AUTH_API,
    "/auth/login",
    "POST",
    undefined,
    { email, password }
  );
  return r.access_token;
}

export async function logout(token: string): Promise<void> {
  // invalidates the token in the IDM blacklist
  await apiFetch<void>(AUTH_API, "/auth/logout", "POST", token);
}

export async function me(token: string): Promise<MeResponse> {
  return apiFetch<MeResponse>(AUTH_API, "/auth/me", "GET", token);
}
