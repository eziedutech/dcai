import { NextResponse, type NextRequest } from "next/server";

// Dashboard pages need a session. This only checks that a refresh cookie exists; the
// backend decides whether it is valid, and the dashboard returns to sign-in on 401.
export function proxy(request: NextRequest) {
  if (!request.cookies.has("dcai_rt")) {
    const url = new URL("/masuk", request.url);
    url.searchParams.set("lanjut", request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: "/dasbor/:path*",
};
