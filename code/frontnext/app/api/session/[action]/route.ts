import { cookies } from "next/headers";
import {
  ACCESS_COOKIE,
  BACKEND,
  CSRF_HEADER,
  REFRESH_COOKIE,
  clearTokens,
  refresh,
  storeTokens,
  type Tokens,
} from "@/lib/server/backend";

// Sign in, sign up, sign out and "who am I". Tokens live only in httpOnly cookies.

function json(body: unknown, status = 200) {
  return Response.json(body, { status, headers: { "cache-control": "no-store" } });
}

export async function POST(request: Request, ctx: RouteContext<"/api/session/[action]">) {
  const { action } = await ctx.params;
  if (request.headers.get(CSRF_HEADER) !== "1") return json({ detail: "missing header" }, 403);

  if (action === "login" || action === "register") {
    const body = await request.text();
    const resp = await fetch(`${BACKEND}/v1/auth/${action}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body,
      cache: "no-store",
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) return json(data, resp.status);
    const tokens = data as Tokens;
    await storeTokens(tokens);
    return json({ guardian: tokens.guardian }, resp.status);
  }

  if (action === "logout") {
    const jar = await cookies();
    const rt = jar.get(REFRESH_COOKIE)?.value;
    const at = jar.get(ACCESS_COOKIE)?.value;
    if (rt && at) {
      await fetch(`${BACKEND}/v1/auth/logout`, {
        method: "POST",
        headers: { "content-type": "application/json", authorization: `Bearer ${at}` },
        body: JSON.stringify({ refresh_token: rt }),
        cache: "no-store",
      }).catch(() => undefined);
    }
    await clearTokens();
    return new Response(null, { status: 204 });
  }
  return json({ detail: "not found" }, 404);
}

export async function GET(_request: Request, ctx: RouteContext<"/api/session/[action]">) {
  const { action } = await ctx.params;
  if (action !== "me") return json({ detail: "not found" }, 404);
  const jar = await cookies();
  let at = jar.get(ACCESS_COOKIE)?.value;
  if (at) {
    const resp = await fetch(`${BACKEND}/v1/auth/me`, {
      headers: { authorization: `Bearer ${at}` },
      cache: "no-store",
    });
    if (resp.ok) return json({ guardian: await resp.json() });
  }
  const tokens = await refresh();
  if (!tokens) return json({ detail: "not signed in" }, 401);
  at = tokens.access_token;
  return json({ guardian: tokens.guardian });
}
