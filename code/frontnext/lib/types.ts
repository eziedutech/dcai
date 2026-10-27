// Shapes returned by the backend (code/backpy/app/dashboard/queries.py and friends).

export type Lang = "id" | "en";
export type Level = "aman" | "perhatian" | "waspada" | "mendesak";
export type Scope = "percakapan" | "gambar" | "domain" | "suara" | "keyboard";

export type Guardian = { id: string; email: string; name: string; language: Lang };

export type Child = {
  id: string;
  nickname: string;
  age_range: string;
  created_at: string;
  consent_scopes: Scope[];
};

export type ParentInsight = {
  what_we_see: string;
  why_it_matters: string;
  conversation_starters: string[];
  do: string[];
  dont: string[];
};

export type MicroLesson = { title: string; body: string } | null;

export type Insight = {
  id: string;
  conversation_id: string;
  app: string | null;
  level: Level;
  patterns: string[];
  situation: string | null;
  source: string | null;
  child_nudge: string;
  parent_insight: ParentInsight;
  micro_lesson: MicroLesson;
  help_channels: string[];
  created_at: string;
};

export type DeviceStatus = {
  device_id: string;
  name: string;
  protection_on: boolean;
  services: Record<string, boolean>;
  last_seen_at: string | null;
};

export type Overview = {
  child_id: string;
  nickname: string;
  age_range: string;
  consent_scopes: Scope[];
  level: Level;
  window_days: number;
  conversations_active: number;
  conversations_needing_attention: number;
  events_by_kind: Record<string, number>;
  sensitive_images_blurred: number;
  devices: DeviceStatus[];
  latest_insight: Insight | null;
};

export type Conversation = {
  conversation_id: string;
  app: string | null;
  channel: string;
  level: Level;
  risk_score: number;
  patterns: string[];
  confidence: string;
  rationale_for_parent: string;
  started_at: string;
  updated_at: string;
};

export type EventRow = { id: string; kind: string; level: Level; created_at: string };

export type Device = {
  id: string;
  child_id: string;
  name: string;
  platform: string;
  app_version: string;
  services: Record<string, boolean>;
  paired_at: string;
  last_seen_at: string | null;
  revoked: boolean;
};

export type ConsentText = { version: string; id: string; en: string; scopes: Scope[] };

export type AskTurn = { role: "user" | "assistant"; content: string };
export type AskOut = {
  answer: string;
  source: "model" | "fallback";
  tools_used: string[];
  is_estimate: boolean;
};
