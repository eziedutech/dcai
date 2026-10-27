import "server-only";
import { cookies } from "next/headers";

// The FastAPI backend. Only this server talks to it; the browser talks to /api/*.
export const BACKEND = (process.env.DCAI_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export const ACCESS_COOKIE = "dcai_at";
export const REFRESH_COOKIE = "dcai_rt";
const secure = process.env.NODE_ENV === "production";

export type Tokens = {
  access_token: string;
  access_expires_at: string;
  refresh_token: string;
  guardian: { id: string; email: string; name: string; language: "id" | "en" };
};

export async function storeTokens(tokens: Tokens) {
  const jar = await cookies();
  const accessMax = Math.max(
    60,
    Math.floor((Date.parse(tokens.access_expires_at) - Date.now()) / 1000),
  );
  jar.set(ACCESS_COOKIE, tokens.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/api",
    maxAge: accessMax,
  });
  jar.set(REFRESH_COOKIE, tokens.refresh_token, {
    httpOnly: true,
    sameSite: "lax",
    secure,
    path: "/",
    maxAge: 7 * 24 * 3600,
  });
}

export async function clearTokens() {
  const jar = await cookies();
  jar.delete({ name: ACCESS_COOKIE, path: "/api" });
  jar.delete({ name: REFRESH_COOKIE, path: "/" });
}

// Refresh tokens rotate, and the backend revokes the whole session when an old one is
// used again. A dashboard loads several panels at once, so parallel requests holding the
// same expired access token share one refresh, and late ones reuse its result briefly.
const inflight = new Map<string, Promise<Tokens | null>>();
const REUSE_MS = 15_000;

async function exchange(rt: string): Promise<Tokens | null> {
  const resp = await fetch(`${BACKEND}/v1/auth/refresh`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ refresh_token: rt }),
    cache: "no-store",
  });
  return resp.ok ? ((await resp.json()) as Tokens) : null;
}

/** Trade the refresh cookie for new tokens and store them. */
export async function refresh(): Promise<Tokens | null> {
  const jar = await cookies();
  const rt = jar.get(REFRESH_COOKIE)?.value;
  if (!rt) return null;
  let pending = inflight.get(rt);
  if (!pending) {
    pending = exchange(rt);
    inflight.set(rt, pending);
    setTimeout(() => inflight.delete(rt), REUSE_MS);
  }
  const tokens = await pending;
  if (!tokens) {
    await clearTokens();
    return null;
  }
  await storeTokens(tokens);
  return tokens;
}

/** Non-GET calls from the browser must carry this header. A cross-site form cannot set
 * it, and a cross-site script cannot send it without a CORS preflight this app refuses. */
export const CSRF_HEADER = "x-dcai-request";
