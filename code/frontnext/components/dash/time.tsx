"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { follow } from "@/lib/sse";
import type { Bedtime, Category, Digest, PolicyOut, ScreenPolicy, Suggestion, TimeRequest, UsageDay } from "@/lib/types";
import { Button, Skeleton, formatWhen } from "../ui";

const CATS: Category[] = ["video", "game", "sosial", "lain"];
// Four quiet tones that stay apart for common colour vision; the legend and the hover
// text carry the names, so colour is never the only cue.
const CAT_COLOR: Record<Category, string> = { video: "#1f3a5f", game: "#3c7a86", sosial: "#b08d57", lain: "#a3adb9" };

const fill = (s: string, v: Record<string, string | number>) => s.replace(/\{(\w+)\}/g, (_, k) => String(v[k] ?? ""));

/** "45 menit", "2 j 15 m" / "45 min", "2 h 15 m". */
function duration(minutes: number, lang: string) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (!h) return `${m} ${lang === "id" ? "menit" : "min"}`;
  return `${h} ${lang === "id" ? "j" : "h"}${m ? ` ${m} m` : ""}`;
}

type Data = { policy: PolicyOut; usage: UsageDay[]; requests: TimeRequest[]; digest: Digest | null };

/** Time online for one child: requests first (they wait for an answer), then the last two
 * weeks, the weekly summary and the rules. */
export function TimeView({ childId, ageRange }: { childId: string; ageRange: string }) {
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    try {
      const [policy, usage, requests, digest] = await Promise.all([
        api<PolicyOut>(`children/${childId}/screen-policy`),
        api<UsageDay[]>(`children/${childId}/usage?days=14`),
        api<TimeRequest[]>(`children/${childId}/time-requests`),
        api<Digest | null>(`children/${childId}/digest`),
      ]);
      setData({ policy, usage, requests, digest });
      setError(false);
    } catch {
      setError(true);
    }
  }, [childId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch on mount and child change
    void load();
    // A new request and its AI advice arrive on the child's stream.
    const stop = follow(`children/${childId}/stream`, (m) => {
      if (m.event !== "time_request" && m.event !== "event") return;
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void load(), 300);
    });
    return () => {
      stop();
      if (timer.current) clearTimeout(timer.current);
    };
  }, [childId, load]);

  const { t } = useT();
  if (error && !data) return <p className="mt-6 text-slate">{t("common.error")}</p>;
  if (!data) return <Skeleton label={t("common.loading")} />;
  return (
    <div className="mt-6 space-y-6">
      <Requests requests={data.requests} onChange={load} />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <UsageChart usage={data.usage} policy={data.policy.policy} />
        <DigestCard childId={childId} digest={data.digest} onMade={(d) => setData({ ...data, digest: d })} />
      </div>
      <PolicyForm childId={childId} ageRange={ageRange} initial={data.policy} onSaved={(p) => setData({ ...data, policy: p })} />
    </div>
  );
}

// ---------------------------------------------------------------- requests

function Requests({ requests, onChange }: { requests: TimeRequest[]; onChange: () => Promise<void> }) {
  const { t } = useT();
  const open = requests.filter((r) => r.status === "menunggu");
  const past = requests.filter((r) => r.status !== "menunggu").slice(0, 5);
  return (
    <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="req-h">
      <h2 id="req-h" className="text-lg font-bold">{t("time.requests")}</h2>
      {requests.length === 0 && <p className="mt-3 text-slate">{t("time.noRequests")}</p>}
      {open.length > 0 && (
        <ul className="mt-4 space-y-4">
          {open.map((r) => (
            <OpenRequest key={r.id} r={r} onChange={onChange} />
          ))}
        </ul>
      )}
      {past.length > 0 && (
        <>
          <h3 className="eyebrow mt-6">{t("time.history")}</h3>
          <ul className="mt-2 divide-y divide-ink/[0.07]">
            {past.map((r) => (
              <PastRequest key={r.id} r={r} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function RequestFacts({ r }: { r: TimeRequest }) {
  const { t, tx, lang } = useT();
  const c = r.context;
  const facts: string[] = [];
  if (c.category) facts.push(tx(`time.cat.${c.category}`, c.category));
  if (c.limit_today != null) facts.push(fill(t("time.ctx.used"), { u: c.used_today ?? 0, l: c.limit_today }));
  else if (c.used_today) facts.push(fill(t("time.ctx.usedOnly"), { u: c.used_today }));
  if (c.minutes_to_bedtime != null) {
    facts.push(c.minutes_to_bedtime <= 0 ? t("time.ctx.inBedtime") : fill(t("time.ctx.bedtime"), { d: duration(c.minutes_to_bedtime, lang) }));
  }
  return facts.length ? <p className="mt-1 text-sm text-slate">{facts.join(" · ")}</p> : null;
}

function OpenRequest({ r, onChange }: { r: TimeRequest; onChange: () => Promise<void> }) {
  const { t, lang } = useT();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const a = r.advice;
  const suggested = a && a.recommendation === "sebagian" && a.suggested_minutes > 0 ? a.suggested_minutes : null;

  async function decide(approve: boolean, minutes?: number) {
    setBusy(true);
    setFailed(false);
    try {
      await api(`time-requests/${r.id}/decision`, { method: "POST", body: { approve, minutes } });
      await onChange();
    } catch {
      setFailed(true);
      setBusy(false);
    }
  }

  return (
    <li className="glass-fill rounded-2xl p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-[1.05rem] font-bold">{fill(t("time.askMinutes"), { m: r.minutes })}</p>
        <p className="text-sm text-slate tabular">{formatWhen(r.created_at, lang)}</p>
      </div>
      <p className="mt-1">{r.reason ? <>&ldquo;{r.reason}&rdquo;</> : <span className="text-slate">{t("time.noReason")}</span>}</p>
      <RequestFacts r={r} />

      <div className="mt-4 rounded-xl bg-navy/[0.05] px-4 py-3">
        <p className="eyebrow">{t("time.advice")}</p>
        {a ? (
          <>
            <p className="mt-1.5 font-semibold">
              {t(`time.rec.${a.recommendation}`)}
              {a.recommendation === "sebagian" && a.suggested_minutes > 0 && ` · ${a.suggested_minutes} ${t("time.minutes")}`}
            </p>
            <p className="mt-1 text-[0.95rem]">{a.summary_for_parent}</p>
            <p className="mt-1 text-[0.95rem] text-slate">{a.rationale}</p>
            {a.source === "template" && <p className="mt-1 text-sm text-slate">{t("dash.template")}</p>}
          </>
        ) : (
          <p className="mt-1.5 text-slate" role="status">{t("time.adviceWaiting")}</p>
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button disabled={busy} onClick={() => decide(true, r.minutes)}>{fill(t("time.allow"), { m: r.minutes })}</Button>
        {suggested && suggested !== r.minutes && (
          <Button variant="quiet" disabled={busy} onClick={() => decide(true, suggested)}>
            {fill(t("time.allow"), { m: suggested })}
          </Button>
        )}
        <Button variant="quiet" disabled={busy} onClick={() => decide(false)}>{t("time.deny")}</Button>
      </div>
      {failed && <p role="alert" className="mt-2 text-sm text-mendesak">{t("common.error")}</p>}
    </li>
  );
}

function PastRequest({ r }: { r: TimeRequest }) {
  const { t, lang } = useT();
  const tone = r.status === "diizinkan" ? "text-aman" : "text-slate";
  return (
    <li className="flex flex-wrap items-baseline justify-between gap-2 py-2.5">
      <span className="min-w-0">
        <span className="font-medium">{fill(t("time.askMinutes"), { m: r.minutes })}</span>
        {r.reason && <span className="text-slate"> · &ldquo;{r.reason}&rdquo;</span>}
      </span>
      <span className="text-sm">
        <span className={`font-semibold ${tone}`}>{fill(t(`time.status.${r.status}`), { m: r.granted_minutes })}</span>
        <span className="ml-2 text-slate tabular">{formatWhen(r.created_at, lang)}</span>
      </span>
    </li>
  );
}

// ---------------------------------------------------------------- usage

function UsageChart({ usage, policy }: { usage: UsageDay[]; policy: ScreenPolicy }) {
  const { t, tx, lang } = useT();
  // Fourteen slots ending today, empty where the phone sent nothing.
  const byDay = new Map(usage.map((u) => [u.day, u]));
  const days = Array.from({ length: 14 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (13 - i));
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    return { key, date: d, u: byDay.get(key) };
  });
  const isSchool = (d: Date) => policy.school_days.includes(((d.getDay() + 6) % 7) + 1);
  const limitFor = (d: Date) => (isSchool(d) ? policy.daily_limit_school : policy.daily_limit_weekend);
  const max = Math.max(60, ...days.map((d) => d.u?.total ?? 0), ...days.map((d) => limitFor(d.date) ?? 0));
  const withData = usage.filter((u) => u.total > 0);
  const avg = withData.length ? Math.round(withData.reduce((s, u) => s + u.total, 0) / withData.length) : 0;
  const bedtime = usage.reduce((s, u) => s + u.bedtime_minutes, 0);
  const longest = usage.reduce((m, u) => Math.max(m, u.longest_session), 0);
  const H = 160;
  const fmt = new Intl.DateTimeFormat(lang === "id" ? "id-ID" : "en-GB", { day: "numeric", month: "short" });
  const wk = new Intl.DateTimeFormat(lang === "id" ? "id-ID" : "en-GB", { weekday: "narrow" });

  return (
    <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="usage-h">
      <h2 id="usage-h" className="text-lg font-bold">{t("time.usage")}</h2>
      {usage.length === 0 ? (
        <p className="mt-3 text-slate">{t("time.noUsage")}</p>
      ) : (
        <>
          <dl className="mt-4 grid grid-cols-3 gap-4">
            {[
              [t("time.avg"), `${avg} ${t("time.minutes")}`],
              [t("time.bedtimeUse"), `${bedtime} ${t("time.minutes")}`],
              [t("time.longest"), `${longest} ${t("time.minutes")}`],
            ].map(([label, value]) => (
              <div key={label} className="flex flex-col-reverse">
                <dt className="mt-1 text-sm leading-tight text-slate">{label}</dt>
                <dd className="text-[1.4rem] font-bold leading-none tabular">{value}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-6 flex items-end gap-1.5" style={{ height: H + 24 }} role="img" aria-label={t("time.usage")}>
            {days.map(({ key, date, u }) => {
              const limit = limitFor(date);
              const label = `${fmt.format(date)}: ${u ? u.total : 0} ${t("time.minutes")}${
                u ? " (" + CATS.map((c) => `${tx(`time.cat.${c}`, c)} ${u.minutes[c]}`).join(", ") + ")" : ""
              }`;
              return (
                <div key={key} className="flex min-w-0 flex-1 flex-col items-center" title={label}>
                  <div className="relative w-full" style={{ height: H }}>
                    {limit != null && policy.enabled && (
                      <div
                        aria-hidden
                        className="absolute inset-x-[-3px] border-t border-dashed border-mendesak/50"
                        style={{ bottom: (limit / max) * H }}
                      />
                    )}
                    <div className="absolute inset-x-0 bottom-0 flex flex-col-reverse overflow-hidden rounded-md">
                      {CATS.map((c) =>
                        u && u.minutes[c] > 0 ? (
                          <div key={c} style={{ height: (u.minutes[c] / max) * H, background: CAT_COLOR[c] }} />
                        ) : null,
                      )}
                    </div>
                  </div>
                  <span className={`mt-1.5 text-[0.7rem] ${isSchool(date) ? "text-slate" : "font-semibold text-ink"}`}>
                    {wk.format(date)}
                  </span>
                </div>
              );
            })}
          </div>
          <ul className="mt-4 flex flex-wrap gap-x-4 gap-y-1.5 text-sm text-slate">
            {CATS.map((c) => (
              <li key={c} className="flex items-center gap-1.5">
                <span aria-hidden className="h-2.5 w-2.5 rounded-sm" style={{ background: CAT_COLOR[c] }} />
                {tx(`time.cat.${c}`, c)}
              </li>
            ))}
            <li className="flex items-center gap-1.5">
              <span aria-hidden className="w-4 border-t border-dashed border-mendesak/60" />
              {t("time.limitLine")}
            </li>
          </ul>
        </>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- digest

function DigestCard({ childId, digest, onMade }: { childId: string; digest: Digest | null; onMade: (d: Digest) => void }) {
  const { t, lang } = useT();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  async function make() {
    setBusy(true);
    setFailed(false);
    try {
      onMade(await api<Digest>(`children/${childId}/digest`, { method: "POST" }));
    } catch {
      setFailed(true);
    }
    setBusy(false);
  }
  const o = digest?.output;
  return (
    <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="digest-h">
      <div className="flex items-start justify-between gap-3">
        <h2 id="digest-h" className="text-lg font-bold">{t("time.digest")}</h2>
        <Button variant="quiet" disabled={busy} onClick={make} className="shrink-0 !px-3 !py-1.5 text-sm">
          {t("time.digestMake")}
        </Button>
      </div>
      {!o ? (
        <p className="mt-3 text-slate">{t("time.digestNone")}</p>
      ) : (
        <div className="mt-3">
          <p className="text-[1.05rem] font-semibold">{o.headline}</p>
          <p className="mt-2 text-[0.95rem]">{o.summary}</p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-[0.95rem] text-slate">
            {o.highlights.map((h) => (
              <li key={h}>{h}</li>
            ))}
          </ul>
          <h3 className="mt-4 text-sm font-semibold text-slate">{t("dash.starters")}</h3>
          <ul className="mt-2 space-y-2">
            {o.conversation_starters.map((s) => (
              <li key={s} className="glass-fill rounded-xl border-l-4 !border-l-navy px-3.5 py-2 text-[0.95rem] font-medium">
                &ldquo;{s}&rdquo;
              </li>
            ))}
          </ul>
          <p className="mt-4 text-sm font-semibold text-slate">{t("time.digestSuggestion")}</p>
          <p className="mt-1 text-[0.95rem]">{o.suggestion}</p>
          <p className="mt-3 text-sm text-slate tabular">
            {formatWhen(digest.created_at, lang)}
            {digest.source === "template" && ` · ${t("dash.template")}`}
          </p>
        </div>
      )}
      {failed && <p role="alert" className="mt-2 text-sm text-mendesak">{t("common.error")}</p>}
    </section>
  );
}

// ---------------------------------------------------------------- rules

function Minutes({ label, value, onChange, nullable = false, min = 0, max = 1440 }: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  nullable?: boolean;
  min?: number;
  max?: number;
}) {
  const { t } = useT();
  const off = value === null;
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-semibold">{label}</span>
      <span className="flex items-center gap-2">
        <input
          type="number"
          inputMode="numeric"
          min={min}
          max={max}
          step={5}
          disabled={off}
          value={off ? "" : value}
          onChange={(e) => onChange(e.target.value === "" ? min : Math.max(min, Math.min(max, Number(e.target.value))))}
          className="w-24 rounded-xl border border-ink/10 bg-white/75 px-3 py-2 tabular outline-none focus:border-navy disabled:opacity-50"
        />
        <span className="text-sm text-slate">{t("time.minutes")}</span>
        {nullable && (
          <span className="ml-1 flex items-center gap-1.5 text-sm text-slate">
            <input type="checkbox" className="h-4 w-4 accent-[#1f3a5f]" checked={off} onChange={(e) => onChange(e.target.checked ? null : 60)} />
            {t("time.noLimit")}
          </span>
        )}
      </span>
    </label>
  );
}

function BedtimeFields({ label, value, onChange }: { label: string; value: Bedtime; onChange: (b: Bedtime) => void }) {
  const { t } = useT();
  const time = "rounded-xl border border-ink/10 bg-white/75 px-3 py-2 tabular outline-none focus:border-navy disabled:opacity-50";
  return (
    <fieldset className="glass-fill rounded-2xl p-4">
      <legend className="sr-only">{label}</legend>
      <label className="flex items-center gap-2 font-semibold">
        <input type="checkbox" className="h-4 w-4 accent-[#1f3a5f]" checked={value.enabled} onChange={(e) => onChange({ ...value, enabled: e.target.checked })} />
        {label}
      </label>
      <div className="mt-3 flex flex-wrap gap-4">
        <label className="text-sm">
          <span className="mb-1 block text-slate">{t("time.from")}</span>
          <input type="time" className={time} disabled={!value.enabled} value={value.start} onChange={(e) => onChange({ ...value, start: e.target.value })} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate">{t("time.until")}</span>
          <input type="time" className={time} disabled={!value.enabled} value={value.end} onChange={(e) => onChange({ ...value, end: e.target.value })} />
        </label>
      </div>
    </fieldset>
  );
}

function PolicyForm({ childId, ageRange, initial, onSaved }: {
  childId: string;
  ageRange: string;
  initial: PolicyOut;
  onSaved: (p: PolicyOut) => void;
}) {
  const { t, tx } = useT();
  const [p, setP] = useState<ScreenPolicy>(initial.policy);
  const [allowed, setAllowed] = useState(initial.policy.always_allowed.join("\n"));
  const [state, setState] = useState<"idle" | "busy" | "saved" | "invalid" | "error">("idle");
  const [proposal, setProposal] = useState<Suggestion | null>(null);
  const [suggesting, setSuggesting] = useState(false);
  const days = t("time.days").split(",");
  const set = (patch: Partial<ScreenPolicy>) => {
    setP({ ...p, ...patch });
    setState("idle");
  };

  async function save() {
    if (p.session.nudge_minutes >= p.session.limit_minutes) return setState("invalid");
    setState("busy");
    const body = { ...p, always_allowed: allowed.split(/\s+/).map((s) => s.trim()).filter(Boolean) };
    try {
      const out = await api<PolicyOut>(`children/${childId}/screen-policy`, { method: "PUT", body });
      onSaved(out);
      setState("saved");
    } catch (err) {
      setState(err instanceof Error && /invalid|422/.test(err.message) ? "invalid" : "error");
    }
  }

  async function suggest() {
    setSuggesting(true);
    try {
      setProposal(await api<Suggestion>(`children/${childId}/screen-policy/suggestion`, { method: "POST" }));
    } catch {
      setState("error");
    }
    setSuggesting(false);
  }

  return (
    <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="policy-h">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id="policy-h" className="text-lg font-bold">{t("time.policy")}</h2>
          {initial.is_default && <p className="mt-1 max-w-[60ch] text-sm text-slate">{fill(t("time.policyDefault"), { a: ageRange })}</p>}
        </div>
        <Button variant="quiet" disabled={suggesting} onClick={suggest} className="shrink-0">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
            <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1" strokeLinecap="round" />
          </svg>
          {t("time.suggest")}
        </Button>
      </div>

      {proposal && (
        <div className="mt-5 rounded-2xl bg-navy/[0.05] px-5 py-4">
          <p className="eyebrow">{t("time.suggestion")}</p>
          <p className="mt-1.5 text-[0.95rem]">{proposal.rationale}</p>
          <p className="mt-2 text-sm text-slate tabular">
            {t("time.school")} {proposal.policy.daily_limit_school ?? "-"} · {t("time.weekend")} {proposal.policy.daily_limit_weekend ?? "-"} ·{" "}
            {CATS.filter((c) => c !== "lain")
              .map((c) => `${tx(`time.cat.${c}`, c)} ${proposal.policy.category_limits[c] ?? "-"}`)
              .join(" · ")}{" "}
            {t("time.minutes")}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <Button
              variant="quiet"
              onClick={() => {
                setP(proposal.policy);
                setAllowed(proposal.policy.always_allowed.join("\n"));
                setProposal(null);
                setState("idle");
              }}
            >
              {t("time.useSuggestion")}
            </Button>
            <span className="text-sm text-slate">{t("time.suggestionNote")}</span>
          </div>
        </div>
      )}

      <label className="mt-6 flex items-center gap-2.5 font-semibold">
        <input type="checkbox" className="h-4 w-4 accent-[#1f3a5f]" checked={p.enabled} onChange={(e) => set({ enabled: e.target.checked })} />
        {t("time.enabled")}
      </label>

      <fieldset className={`mt-6 space-y-6 ${p.enabled ? "" : "pointer-events-none opacity-50"}`} disabled={!p.enabled}>
        <div>
          <p className="text-sm font-semibold">{t("time.schoolDays")}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {days.map((name, i) => {
              const n = i + 1;
              const on = p.school_days.includes(n);
              return (
                <button
                  key={n}
                  type="button"
                  aria-pressed={on}
                  onClick={() => set({ school_days: on ? p.school_days.filter((d) => d !== n) : [...p.school_days, n].sort() })}
                  className={`rounded-full border px-3.5 py-1.5 text-sm font-semibold ${on ? "border-navy bg-navy text-paper" : "border-ink/10 bg-white/60 hover:border-navy/50"}`}
                >
                  {name}
                </button>
              );
            })}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-4">
            <p className="font-bold">{t("time.daily")}</p>
            <Minutes label={t("time.school")} nullable value={p.daily_limit_school} onChange={(v) => set({ daily_limit_school: v })} />
            <Minutes label={t("time.weekend")} nullable value={p.daily_limit_weekend} onChange={(v) => set({ daily_limit_weekend: v })} />
          </div>
          <div className="space-y-4">
            <p className="font-bold">{t("time.categories")}</p>
            {CATS.map((c) => (
              <Minutes
                key={c}
                label={tx(`time.cat.${c}`, c)}
                nullable
                value={p.category_limits[c]}
                onChange={(v) => set({ category_limits: { ...p.category_limits, [c]: v } })}
              />
            ))}
          </div>
        </div>

        <div>
          <p className="font-bold">{t("time.bedtime")}</p>
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <BedtimeFields label={t("time.school")} value={p.bedtime_school} onChange={(b) => set({ bedtime_school: b })} />
            <BedtimeFields label={t("time.weekend")} value={p.bedtime_weekend} onChange={(b) => set({ bedtime_weekend: b })} />
          </div>
          <div className="mt-4">
            <Minutes label={t("time.windDown")} min={0} max={60} value={p.wind_down_minutes} onChange={(v) => set({ wind_down_minutes: v ?? 0 })} />
          </div>
        </div>

        <div>
          <label className="flex items-center gap-2.5 font-bold">
            <input
              type="checkbox"
              className="h-4 w-4 accent-[#1f3a5f]"
              checked={p.session.enabled}
              onChange={(e) => set({ session: { ...p.session, enabled: e.target.checked } })}
            />
            {t("time.session")}
          </label>
          <div className={`mt-3 grid gap-4 sm:grid-cols-3 ${p.session.enabled ? "" : "opacity-50"}`}>
            <Minutes label={t("time.sessionNudge")} min={5} max={180} value={p.session.nudge_minutes} onChange={(v) => set({ session: { ...p.session, nudge_minutes: v ?? 5 } })} />
            <Minutes label={t("time.sessionLimit")} min={10} max={240} value={p.session.limit_minutes} onChange={(v) => set({ session: { ...p.session, limit_minutes: v ?? 10 } })} />
            <Minutes label={t("time.sessionBreak")} min={1} max={60} value={p.session.break_minutes} onChange={(v) => set({ session: { ...p.session, break_minutes: v ?? 1 } })} />
          </div>
        </div>

        <label className="block">
          <span className="block font-bold">{t("time.allowed")}</span>
          <span className="mt-1 block text-sm text-slate">{t("time.allowedHint")}</span>
          <textarea
            rows={3}
            value={allowed}
            onChange={(e) => {
              setAllowed(e.target.value);
              setState("idle");
            }}
            spellCheck={false}
            className="mt-2 w-full max-w-xl rounded-xl border border-ink/10 bg-white/75 px-3.5 py-2.5 font-mono text-sm outline-none focus:border-navy"
            placeholder="com.example.belajar"
          />
        </label>

        <label className="flex items-start gap-2.5">
          <input
            type="checkbox"
            className="mt-1 h-4 w-4 accent-[#1f3a5f]"
            checked={p.focus_mode}
            onChange={(e) => set({ focus_mode: e.target.checked })}
          />
          <span>
            <span className="block font-bold">{t("time.focus")}</span>
            <span className="mt-1 block text-sm text-slate">{t("time.focusHint")}</span>
          </span>
        </label>
      </fieldset>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Button onClick={save} disabled={state === "busy"}>{t("time.save")}</Button>
        <p className="text-sm" role="status" aria-live="polite">
          {state === "saved" && <span className="text-aman">{t("time.saved")}</span>}
          {state === "invalid" && <span className="text-mendesak">{t("time.invalid")}</span>}
          {state === "error" && <span className="text-mendesak">{t("common.error")}</span>}
        </p>
      </div>
    </section>
  );
}
