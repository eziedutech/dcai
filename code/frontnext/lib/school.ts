"use client";

// Browser side of the school dashboard: every call goes to this app's /api/school, never to
// the backend. Staff sessions use the dcai_sat cookie set by /api/school-session.

import { ApiError } from "./api";
import type { ClassOverview, Staff, StaffClass } from "./types";

async function parse<T>(resp: Response): Promise<T> {
  if (resp.status === 204) return undefined as T;
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : `HTTP ${resp.status}`;
    if (resp.status === 401 && typeof window !== "undefined" && location.pathname.startsWith("/sekolah") && !location.pathname.startsWith("/sekolah/masuk")) {
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      location.href = "/sekolah/masuk";
    }
    throw new ApiError(resp.status, detail);
  }
  return data as T;
}

export async function schoolApi<T>(path: string, init: { method?: string; body?: unknown } = {}): Promise<T> {
  const method = init.method ?? "GET";
  const resp = await fetch(`/api/school/${path}`, {
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

export async function schoolSession(action: "login" | "register" | "logout", body?: unknown): Promise<{ staff: Staff }> {
  const resp = await fetch(`/api/school-session/${action}`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-dcai-request": "1" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return parse<{ staff: Staff }>(resp);
}

export async function schoolMe(): Promise<Staff | null> {
  const resp = await fetch("/api/school-session/me", { cache: "no-store" });
  if (!resp.ok) return null;
  return (await resp.json()).staff;
}

export type { ClassOverview, Staff, StaffClass };
