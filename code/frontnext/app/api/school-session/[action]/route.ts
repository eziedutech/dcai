import { cookies } from "next/headers";
import { BACKEND, CSRF_HEADER, STAFF_COOKIE, clearStaffToken, storeStaffToken } from "@/lib/server/backend";

// School staff sign in, sign up, sign out and "who am I". The access token lives only in an
// httpOnly cookie. There is no refresh yet, so a session ends when the access token expires.

function json(body: unknown, status = 200) {
  return Response.json(body, { status, headers: { "cache-control": "no-store" } });
}

export async function POST(request: Request, ctx: RouteContext<"/api/school-session/[action]">) {
  const { action } = await ctx.params;
  if (request.headers.get(CSRF_HEADER) !== "1") return json({ detail: "missing header" }, 403);

  if (action === "login" || action === "register") {
    const resp = await fetch(`${BACKEND}/v1/school/${action}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: await request.text(),
      cache: "no-store",
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) return json(data, resp.status);
    await storeStaffToken(data.access_token, data.access_expires_at);
    return json({ staff: data.staff }, resp.status);
  }

  if (action === "logout") {
    await clearStaffToken();
    return new Response(null, { status: 204 });
  }
  return json({ detail: "not found" }, 404);
}

export async function GET(_request: Request, ctx: RouteContext<"/api/school-session/[action]">) {
  const { action } = await ctx.params;
  if (action !== "me") return json({ detail: "not found" }, 404);
  const jar = await cookies();
  const at = jar.get(STAFF_COOKIE)?.value;
  if (at) {
    const resp = await fetch(`${BACKEND}/v1/school/me`, {
      headers: { authorization: `Bearer ${at}` },
      cache: "no-store",
    });
    if (resp.ok) return json({ staff: await resp.json() });
  }
  return json({ detail: "not signed in" }, 401);
}
