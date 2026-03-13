/**
 * Auth cookie helpers for middleware compatibility.
 * Middleware runs on the server and can only read cookies, not localStorage.
 * We mirror the token in a cookie so protected routes can be guarded.
 */

const AUTH_COOKIE = "omnidocs_token";
const MAX_AGE_DAYS = 1;

export function setAuthCookie(token: string): void {
  if (typeof document === "undefined") return;
  const maxAge = MAX_AGE_DAYS * 24 * 60 * 60;
  document.cookie = `${AUTH_COOKIE}=${encodeURIComponent(token)}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

export function clearAuthCookie(): void {
  if (typeof document === "undefined") return;
  document.cookie = `${AUTH_COOKIE}=; path=/; max-age=0`;
}
