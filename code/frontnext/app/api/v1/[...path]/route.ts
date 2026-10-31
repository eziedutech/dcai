import { cookies } from "next/headers";
import { ACCESS_COOKIE, BACKEND, CSRF_HEADER, refresh } from "@/lib/server/backend";

// The dashboard's only way to the backend. It adds the guardian's token from the httpOnly
// cookie, refreshes it once on 401, and streams responses through (live updates are SSE).
// Only paths the dashboard needs pass; the phone's API (/v1/device) never does.

const ALLOWED = [
  /^children(\/[0-9a-f-]{36}(\/(overview|conversations|events|insights|protection|devices|consents|pairing-codes|stream|data|usage|time-requests|digest|screen-policy(\/suggestion)?|class(\/[0-9a-f-]{36})?|classes|history))?)?$/,
  /^time-requests\/[0-9a-f-]{36}\/decision$/,
  /^consents(\/text)?$/,
  /^devices\/[0-9a-f-]{36}$/,
  /^auth\/me$/,
  /^auth\/change-password$/,
  /^ask$/,
  /^messages\/analyze$/,
  /^health$/,
];

const PASS_REQUEST = ["content-type", "accept", "last-event-id"];
const PASS_RESPONSE = ["content-type", "cache-control", "retry-after", "x-accel-buffering"];

async function forward(request: Request, ctx: RouteContext<"/api/v1/[...path]">) {
  const { path } = await ctx.params;
  const joined = path.join("/");
  if (!ALLOWED.some((re) => re.test(joined))) {
    return Response.json({ detail: "not found" }, { status: 404 });
  }
  if (request.method !== "GET" && request.headers.get(CSRF_HEADER) !== "1") {
    return Response.json({ detail: "missing header" }, { status: 403 });
  }

  const url = `${BACKEND}/v1/${joined}${new URL(request.url).search}`;
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  const headers = new Headers();
  for (const name of PASS_REQUEST) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const call = (token: string | undefined) => {
    if (token) headers.set("authorization", `Bearer ${token}`);
    return fetch(url, { method: request.method, headers, body, cache: "no-store", signal: request.signal });
  };

  const jar = await cookies();
  let token = jar.get(ACCESS_COOKIE)?.value;
  if (!token) token = (await refresh())?.access_token;
  let resp = await call(token);
  if (resp.status === 401) {
    const fresh = await refresh();
    if (fresh) resp = await call(fresh.access_token);
  }

  const out = new Headers();
  for (const name of PASS_RESPONSE) {
    const value = resp.headers.get(name);
    if (value) out.set(name, value);
  }
  if (!out.has("cache-control")) out.set("cache-control", "no-store");
  return new Response(resp.body, { status: resp.status, headers: out });
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const DELETE = forward;
