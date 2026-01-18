export type JwtPayload = {
  sub?: string;
  role?: string;
  email?: string;
  exp?: number;
  [k: string]: unknown;
};

function base64UrlDecode(input: string): string {
  const pad = "=".repeat((4 - (input.length % 4)) % 4);
  const b64 = (input + pad).replace(/-/g, "+").replace(/_/g, "/");
  const decoded = atob(b64);
  try {
    return decodeURIComponent(
      Array.from(decoded)
        .map((c) => "%" + c.charCodeAt(0).toString(16).padStart(2, "0"))
        .join("")
    );
  } catch {
    return decoded;
  }
}

export function parseJwt(token: string): JwtPayload {
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("Invalid JWT");
  const json = base64UrlDecode(parts[1]);
  return JSON.parse(json) as JwtPayload;
}

export function isExpired(payload: JwtPayload): boolean {
  if (!payload.exp) return false;
  const now = Math.floor(Date.now() / 1000);
  return payload.exp <= now;
}
