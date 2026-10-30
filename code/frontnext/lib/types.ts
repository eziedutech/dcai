// Shapes returned by the backend (code/backpy/app/dashboard/queries.py and friends).

export type Lang = "id" | "en";
export type Level = "aman" | "perhatian" | "waspada" | "mendesak";
export type Scope = "percakapan" | "layar" | "gambar" | "domain" | "keyboard" | "waktu";

export type Guardian = { id: string; email: string; name: string; language: Lang };

// School module (proposal 0004): staff accounts and aggregate-only class views.
export type Staff = { id: string; email: string; name: string; role: string; school_id: string };
export type StaffClass = { id: string; name: string; members: number; join_code?: string | null };
export type ClassOverview = {
  classroom_id: string;
  window_days: number;
  total: number;
  suppressed: boolean;
  by_level: Record<string, number> | null;
  support: number | null;
};

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

// Time online (code/backpy/app/api/family.py).

export type Category = "video" | "game" | "sosial" | "lain";
export type Bedtime = { enabled: boolean; start: string; end: string };
export type ScreenPolicy = {
  enabled: boolean;
  school_days: number[];
  daily_limit_school: number | null;
  daily_limit_weekend: number | null;
  category_limits: Record<Category, number | null>;
  bedtime_school: Bedtime;
  bedtime_weekend: Bedtime;
  wind_down_minutes: number;
  session: { enabled: boolean; nudge_minutes: number; limit_minutes: number; break_minutes: number };
  always_allowed: string[];
  focus_mode: boolean;
};
export type PolicyOut = { policy: ScreenPolicy; is_default: boolean };
export type Suggestion = { policy: ScreenPolicy; rationale: string; source: "model" | "template" };

export type UsageDay = {
  day: string;
  weekend: boolean;
  minutes: Record<Category, number>;
  total: number;
  bedtime_minutes: number;
  longest_session: number;
  session_limits: number;
};

export type TimeAdvice = {
  summary_for_parent: string;
  recommendation: "izinkan" | "sebagian" | "tunda";
  suggested_minutes: number;
  rationale: string;
  source?: string;
};
export type TimeRequest = {
  id: string;
  minutes: number;
  reason: string;
  status: "menunggu" | "diizinkan" | "ditolak" | "kedaluwarsa";
  granted_minutes: number;
  advice: TimeAdvice | null;
  context: { used_today?: number; limit_today?: number | null; category?: Category | null; minutes_to_bedtime?: number | null };
  created_at: string;
  decided_at: string | null;
};

export type Digest = {
  week_start: string;
  output: { headline: string; summary: string; highlights: string[]; conversation_starters: string[]; suggestion: string };
  source: string;
  created_at: string;
};
