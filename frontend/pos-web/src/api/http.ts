import { getToken } from "../auth/session";

export type HttpMethod = "GET" | "POST" | "PUT" | "DELETE";

export type ApiError = {
  status: number;
  detail: string;
};

function readDetail(x: any): string {
  if (!x) return "";
  if (typeof x === "string") return x;
  if (typeof x.detail === "string") return x.detail;
  if (typeof x.message === "string") return x.message;
  return "";
}

export async function apiFetch<T>(
  baseUrl: string,
  path: string,
  method: HttpMethod = "GET",
  token?: string,
  body?: unknown
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (token) headers["Authorization"] = `Bearer ${token}`;

  const hasBody = body !== undefined && body !== null;
  const sendBody =
    method === "GET" || method === "DELETE"
      ? undefined
      : hasBody
      ? JSON.stringify(body)
      : undefined;

  if (sendBody !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(`${baseUrl}${path}`, {
    method,
    headers,
    body: sendBody,
  });

  if (res.status === 204) {
    return undefined as T;
  }

  const ct = res.headers.get("content-type") || "";
  const isJson = ct.includes("application/json");
  const payload = isJson
    ? await res.json().catch(() => null)
    : await res.text().catch(() => "");

  if (!res.ok) {
    const detail = readDetail(payload) || res.statusText || "error";
    throw { status: res.status, detail } satisfies ApiError;
  }

  return payload as T;
}

export async function apiFetchAuthed<T>(
  baseUrl: string,
  path: string,
  method: HttpMethod = "GET",
  body?: unknown
): Promise<T> {
  const token = getToken() ?? undefined;
  return apiFetch<T>(baseUrl, path, method, token, body);
}
