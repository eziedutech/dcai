import { cookies } from "next/headers";
import { BACKEND, CSRF_HEADER, STAFF_COOKIE } from "@/lib/server/backend";

// The staff dashboard's only way to the backend. It adds the staff token from the httpOnly
// cookie. Only the aggregate-only school paths pass; nothing that could name a child does.

const ALLOWED = [/^me$/, /^classes$/, /^classes\/[0-9a-f-]{36}\/overview$/];

const PASS_REQUEST = ["content-type", "accept"];
const PASS_RESPONSE = ["content-type", "cache-control"];

async function forward(request: Request, ctx: RouteContext<"/api/school/[...path]">) {
  const { path } = await ctx.params;
  const joined = path.join("/");
  if (!ALLOWED.some((re) => re.test(joined))) {
    return Response.json({ detail: "not found" }, { status: 404 });
  }
  if (request.method !== "GET" && request.headers.get(CSRF_HEADER) !== "1") {
    return Response.json({ detail: "missing header" }, { status: 403 });
  }

  const url = `${BACKEND}/v1/school/${joined}${new URL(request.url).search}`;
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  const headers = new Headers();
  for (const name of PASS_REQUEST) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const jar = await cookies();
  const token = jar.get(STAFF_COOKIE)?.value;
  if (token) headers.set("authorization", `Bearer ${token}`);

  const resp = await fetch(url, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
    signal: request.signal,
  });
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
