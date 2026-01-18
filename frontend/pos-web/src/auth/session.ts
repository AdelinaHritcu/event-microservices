const ACCESS_KEY = "access_token";

export function getToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(ACCESS_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(ACCESS_KEY);
}
