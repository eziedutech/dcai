"use client";

// Browser side of the dashboard: every call goes to this app's /api, never to the backend.

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
  }
}

async function parse<T>(resp: Response): Promise<T> {
  if (resp.status === 204) return undefined as T;
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.detail)
          ? "invalid input"
          : `HTTP ${resp.status}`;
    if (resp.status === 401 && typeof window !== "undefined" && location.pathname.startsWith("/dasbor")) {
      // A full load on purpose: the session is gone, so no client state should survive.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      location.href = `/masuk?lanjut=${encodeURIComponent(location.pathname)}`;
    }
    throw new ApiError(resp.status, detail);
  }
  return data as T;
}

export async function api<T>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  const method = init.method ?? "GET";
  const resp = await fetch(`/api/v1/${path}`, {
    method,
    headers: {
      ...(init.body !== undefined ? { "content-type": "application/json" } : {}),
      ...(method !== "GET" ? { "x-dcai-request": "1" } : {}),
    },
    body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    cache: "no-store",
  });
  return parse<T>(resp);
}

export async function session<T>(
  action: "login" | "register" | "logout" | "logout-all",
  body?: unknown,
): Promise<T> {
  const resp = await fetch(`/api/session/${action}`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-dcai-request": "1" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parse<T>(resp);
}

export async function me(): Promise<import("./types").Guardian | null> {
  const resp = await fetch("/api/session/me", { cache: "no-store" });
  if (!resp.ok) return null;
  return (await resp.json()).guardian;
}
