"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { type TKey, useT } from "@/lib/i18n";
import { follow } from "@/lib/sse";
import type {
  Child,
  ChildClass,
  Conversation,
  ConsentText,
  Device,
  EventRow,
  Insight,
  Level,
  Overview,
  Scope,
} from "@/lib/types";
import { Button, Field, LEVEL_STYLE, LevelBadge, Skeleton, appLabel, formatWhen } from "../ui";
import { useDash } from "./shell";
import { TimeView } from "./time";

// One page per child, split into tabs that live in the URL hash so a reload or a shared link
// keeps the tab, and the sidebar's sub-menu can point straight at one.
const TABS = ["overview", "time", "school", "phone", "settings"] as const;
type Tab = (typeof TABS)[number];
const TAB_LABEL: Record<Tab, TKey> = {
  overview: "dash.tab.overview",
  time: "dash.tab.time",
  school: "dash.tab.school",
  phone: "dash.tab.phone",
  settings: "dash.tab.settings",
};

function tabFromParam(value: string | null): Tab {
  return (TABS as readonly string[]).includes(value ?? "") ? (value as Tab) : "overview";
}

export function ChildView({ childId }: { childId: string }) {
  const { t } = useT();
  const { kids } = useDash();
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const child = kids.find((k) => k.id === childId);
  const tab = tabFromParam(params.get("tab"));

  const setTab = (next: Tab) => {
    // The tab lives in ?tab= so a reload or a shared link keeps it, and the sidebar's
    // sub-menu can point straight at one (useSearchParams keeps both in sync).
    router.replace(next === "overview" ? pathname : `${pathname}?tab=${next}`, { scroll: false });
  };

  if (!child) return <p className="text-slate">{t("common.error")}</p>;

  return (
    <div className="mx-auto max-w-5xl">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[2rem] font-bold tracking-[-0.02em]">{child.nickname}</h1>
          <p className="text-slate">
            {child.age_range} {t("common.age")}
          </p>
        </div>
      </header>

      <div role="tablist" aria-label={child.nickname} className="glass-fill mt-6 flex flex-wrap gap-1 rounded-2xl p-1">
        {TABS.map((k) => (
          <button
            key={k}
            role="tab"
            type="button"
            aria-selected={tab === k}
            onClick={() => setTab(k)}
            className={`rounded-xl px-4 py-2 text-[0.95rem] font-semibold transition-colors ${
              tab === k ? "bg-navy text-paper shadow-[0_8px_20px_-12px_rgba(31,58,95,0.9)]" : "text-slate hover:text-ink"
            }`}
          >
            {t(TAB_LABEL[k])}
          </button>
        ))}
      </div>

      <div className="mt-6">
        {tab === "overview" && <OverviewPanel childId={childId} />}
        {tab === "time" && <TimeView childId={childId} ageRange={child.age_range} />}
        {tab === "school" && <SchoolPanel child={child} />}
        {tab === "phone" && <PhonePanel childId={childId} />}
        {tab === "settings" && <SettingsPanel child={child} />}
      </div>
    </div>
  );
}

// --- Overview (level, insight, events, conversations) ---

type Data = { overview: Overview; events: EventRow[]; conversations: Conversation[] };

function OverviewPanel({ childId }: { childId: string }) {
  const { t, tx, lang } = useT();
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [live, setLive] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    try {
      const [overview, events, conversations] = await Promise.all([
        api<Overview>(`children/${childId}/overview?lang=${lang}`),
        api<EventRow[]>(`children/${childId}/events?days=30&limit=40`),
        api<Conversation[]>(`children/${childId}/conversations?days=30&lang=${lang}`),
      ]);
      setData({ overview, events, conversations });
      setError(false);
    } catch {
      setError(true);
    }
  }, [childId, lang]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch on mount and child change
    void load();
    const stop = follow(`children/${childId}/stream`, () => {
      setLive(true);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => void load(), 400);
    });
    return () => {
      stop();
      if (timer.current) clearTimeout(timer.current);
    };
  }, [childId, load]);

  if (error && !data) return <p className="text-slate">{t("common.error")}</p>;
  if (!data) return <Skeleton label={t("common.loading")} />;
  const { overview: ov, events, conversations } = data;

  return (
    <>
      <p className="flex items-center gap-2 text-sm text-slate" aria-live="polite">
        <span aria-hidden className={`inline-block h-2 w-2 rounded-full ${live ? "bg-aman" : "bg-line"}`} />
        {live ? t("dash.live") : t("dash.window")}
      </p>
      <LevelStrip ov={ov} />

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <section aria-labelledby="insight-h" className="glass rounded-2xl p-6 sm:p-7">
          <h2 id="insight-h" className="text-lg font-bold">{t("dash.latestInsight")}</h2>
          {ov.latest_insight ? (
            <InsightBlock insight={ov.latest_insight} />
          ) : (
            <p className="mt-3 max-w-[56ch] text-slate">{t("dash.noInsight")}</p>
          )}
        </section>
        <section aria-labelledby="events-h" className="glass rounded-2xl p-6">
          <h2 id="events-h" className="text-lg font-bold">{t("dash.events")}</h2>
          {events.length === 0 ? (
            <p className="mt-3 text-slate">{t("dash.noEvents")}</p>
          ) : (
            <ol className="mt-3 space-y-3">
              {events.map((e) => (
                <li key={e.id} className="flex items-baseline gap-2.5">
                  <span
                    aria-hidden
                    className={`relative top-[0.4rem] h-2 w-2 shrink-0 rounded-full ${LEVEL_STYLE[e.level as Level]?.bar ?? "bg-slate"}`}
                  />
                  <span className="text-[0.95rem] font-medium">{tx(`event.${e.kind}`, e.kind)}</span>
                  <span className="ml-auto shrink-0 text-sm text-slate tabular">{formatWhen(e.created_at, lang)}</span>
                </li>
              ))}
            </ol>
          )}
        </section>
      </div>

      <section className="glass mt-6 rounded-2xl p-6 sm:p-7" aria-labelledby="conv-h">
        <h2 id="conv-h" className="text-lg font-bold">{t("dash.conversations")}</h2>
        <p className="mt-1 text-sm text-slate">{t("dash.textNotStored")}</p>
        {conversations.length === 0 ? (
          <p className="mt-3 text-slate">{t("dash.noConversations")}</p>
        ) : (
          <ul className="mt-4 divide-y divide-ink/[0.07] border-t border-ink/[0.07]">
            {conversations.map((c) => (
              <ConversationRow key={c.conversation_id} c={c} />
            ))}
          </ul>
        )}
      </section>
    </>
  );
}

function LevelStrip({ ov }: { ov: Overview }) {
  const { t } = useT();
  const s = LEVEL_STYLE[ov.level];
  const stats: [number, string][] = [
    [ov.conversations_active, t("dash.convActive")],
    [ov.conversations_needing_attention, t("dash.convAttention")],
    [ov.sensitive_images_blurred, t("dash.blurred")],
  ];
  return (
    <section className="glass mt-4 flex flex-wrap items-start justify-between gap-6 rounded-2xl px-7 py-6" aria-labelledby="level-h">
      <div className="max-w-[46ch]">
        <h2 id="level-h" className="text-sm font-semibold text-slate">
          {t("dash.levelNow")}, {t("dash.window").toLowerCase()}
        </h2>
        <div className="mt-2">
          <LevelBadge level={ov.level} size="lg" />
        </div>
        <p className={`mt-3 text-[1.05rem] font-medium ${s.text}`}>{t(`levelHint.${ov.level}`)}</p>
        <p className="mt-1 text-sm text-slate">{t("dash.estimate")}</p>
      </div>
      <dl className="flex gap-8">
        {stats.map(([n, label]) => (
          <div key={label} className="flex flex-col-reverse">
            <dt className="mt-1 max-w-[10ch] text-sm leading-tight text-slate">{label}</dt>
            <dd className="text-[1.9rem] font-bold leading-none tabular">{n}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export function InsightBlock({ insight }: { insight: Insight }) {
  const { t, tx, lang } = useT();
  const pi = insight.parent_insight;
  return (
    <article className="mt-3">
      <p className="flex flex-wrap items-center gap-2 text-sm text-slate">
        <LevelBadge level={insight.level} />
        {insight.app && (
          <span>
            {t("dash.in")} {appLabel(insight.app)}
          </span>
        )}
        <span className="tabular">{formatWhen(insight.created_at, lang)}</span>
      </p>
      {insight.patterns.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-2">
          {insight.patterns.map((p) => (
            <li key={p} className="rounded-full bg-mist px-3 py-1 text-sm font-medium">
              {tx(`pattern.${p}`, p)}
            </li>
          ))}
        </ul>
      )}
      <dl className="mt-5 space-y-4">
        <div>
          <dt className="text-sm font-semibold text-slate">{t("dash.whatWeSee")}</dt>
          <dd className="mt-1 max-w-[62ch]">{pi.what_we_see}</dd>
        </div>
        <div>
          <dt className="text-sm font-semibold text-slate">{t("dash.whyItMatters")}</dt>
          <dd className="mt-1 max-w-[62ch]">{pi.why_it_matters}</dd>
        </div>
      </dl>
      <h3 className="mt-6 text-sm font-semibold text-slate">{t("dash.starters")}</h3>
      <ul className="mt-2 space-y-1.5">
        {pi.conversation_starters.map((s) => (
          <li key={s} className="rounded-lg border border-ink/10 bg-white/60 px-3.5 py-2 text-[1.02rem]">
            &ldquo;{s}&rdquo;
          </li>
        ))}
      </ul>
      <div className="mt-6 grid gap-6 sm:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-aman">{t("dash.do")}</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-[0.95rem]">
            {pi.do.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-mendesak">{t("dash.dont")}</h3>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-[0.95rem]">
            {pi.dont.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="glass-fill mt-6 rounded-xl px-4 py-3">
        <p className="text-sm font-semibold text-slate">{t("dash.childWasTold")}</p>
        <p className="mt-1">{insight.child_nudge}</p>
        {insight.source === "template" && <p className="mt-1 text-sm text-slate">{t("dash.template")}</p>}
      </div>
      {insight.help_channels.length > 0 && (
        <div className="mt-4 px-4">
          <p className="text-sm font-semibold text-slate">{t("dash.help")}</p>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-[0.95rem]">
            {insight.help_channels.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </div>
      )}
      {insight.micro_lesson && (
        <div className="mt-4 px-4">
          <p className="text-sm font-semibold text-slate">{t("dash.lesson")}</p>
          <p className="mt-1 font-semibold">{insight.micro_lesson.title}</p>
          <p className="mt-1 max-w-[62ch] text-[0.95rem] text-slate">{insight.micro_lesson.body}</p>
        </div>
      )}
    </article>
  );
}

function ConversationRow({ c }: { c: Conversation }) {
  const { t, tx, lang } = useT();
  return (
    <li className="grid gap-2 py-4 sm:grid-cols-[10rem_1fr_auto] sm:items-start sm:gap-6">
      <div>
        <p className="font-semibold">{appLabel(c.app) ?? c.channel}</p>
        <p className="text-sm text-slate tabular">{formatWhen(c.updated_at, lang)}</p>
      </div>
      <div className="min-w-0">
        <p className="max-w-[60ch] text-[0.95rem]">{c.rationale_for_parent}</p>
        {c.patterns.length > 0 && (
          <p className="mt-1.5 text-sm text-slate">{c.patterns.map((p) => tx(`pattern.${p}`, p)).join(", ")}</p>
        )}
      </div>
      <div className="sm:text-right">
        <LevelBadge level={c.level} />
        <p className="mt-1 text-sm text-slate">
          {t("dash.confidence")}: {tx(`conf.${c.confidence}`, c.confidence)}
        </p>
      </div>
    </li>
  );
}

// --- Phone: pair, view and unpair this child's devices ---

function PhonePanel({ childId }: { childId: string }) {
  const { t, tx, lang } = useT();
  const [devices, setDevices] = useState<Device[] | null>(null);

  const load = useCallback(() => {
    api<Device[]>(`children/${childId}/devices`).then(setDevices, () => setDevices([]));
  }, [childId]);
  useEffect(() => load(), [load]);

  async function unpair(id: string) {
    await api(`devices/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <section className="glass rounded-2xl p-6 sm:p-7" aria-labelledby="phone-h">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 id="phone-h" className="text-lg font-bold">{t("dash.protection")}</h2>
          <p className="mt-1 max-w-[56ch] text-sm text-slate">{t("dash.phoneLead")}</p>
        </div>
        <Link
          href={`/dasbor/tambah?anak=${childId}`}
          className="shrink-0 rounded-xl bg-navy px-4 py-2.5 text-[0.95rem] font-semibold text-paper hover:bg-ink"
        >
          {t("dash.pairAnother")}
        </Link>
      </div>

      {devices === null ? (
        <p className="mt-4 text-slate">{t("common.loading")}</p>
      ) : devices.filter((d) => !d.revoked).length === 0 ? (
        <p className="mt-4 text-slate">{t("dash.noDevice")}</p>
      ) : (
        <ul className="mt-4 space-y-5">
          {devices.map((d) => (
            <li key={d.id} className="rounded-2xl border border-ink/[0.08] p-4">
              <div className="flex items-center justify-between gap-3">
                <span className="font-semibold">{d.name}</span>
                {d.revoked ? (
                  <span className="text-sm text-slate">{t("set.revoked")}</span>
                ) : (
                  <Button variant="quiet" onClick={() => unpair(d.id)}>{t("set.revoke")}</Button>
                )}
              </div>
              <p className="mt-0.5 text-sm text-slate tabular">
                {formatWhen(d.paired_at, lang)}, v{d.app_version}
              </p>
              {!d.revoked && (
                <ul className="mt-3 space-y-0.5 border-t border-ink/[0.07] pt-3 text-sm text-slate">
                  {Object.entries(d.services).map(([name, on]) => (
                    <li key={name} className="flex justify-between">
                      <span>{tx(`service.${name}`, name)}</span>
                      <span className={on ? "text-aman font-semibold" : "font-semibold text-mendesak"}>
                        {on ? t("dash.protectionOn") : t("dash.protectionOff")}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {d.last_seen_at && (
                <p className="mt-2 text-sm text-slate tabular">
                  {t("dash.lastSeen")}: {formatWhen(d.last_seen_at, lang)}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// --- School: this child's class connection ---

function SchoolPanel({ child }: { child: Child }) {
  const { t } = useT();
  const hasScope = child.consent_scopes.includes("sekolah");
  const [classes, setClasses] = useState<ChildClass[]>([]);
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!hasScope) return;
    api<ChildClass[]>(`children/${child.id}/classes`).then(setClasses, () => undefined);
  }, [child.id, hasScope]);

  async function join(e: React.FormEvent) {
    e.preventDefault();
    const c = code.trim();
    if (!c) return;
    setBusy(true);
    setError(null);
    try {
      await api(`children/${child.id}/class`, { method: "POST", body: { join_code: c } });
      setCode("");
      setClasses(await api<ChildClass[]>(`children/${child.id}/classes`));
    } catch {
      setError(t("set.joinError"));
    } finally {
      setBusy(false);
    }
  }

  async function leave(classroomId: string) {
    setBusy(true);
    try {
      await api(`children/${child.id}/class/${classroomId}`, { method: "DELETE" });
      setClasses((cs) => cs.filter((c) => c.classroom_id !== classroomId));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="glass rounded-2xl p-6 sm:p-7" aria-labelledby="school-h">
      <h2 id="school-h" className="text-lg font-bold">{t("set.school")}</h2>
      <p className="mt-1 max-w-[62ch] text-sm text-slate">{t("dash.schoolLead")}</p>
      {!hasScope ? (
        <p className="mt-4 rounded-xl bg-navy/[0.05] px-4 py-3 text-sm text-slate">{t("set.schoolNeedScope")}</p>
      ) : (
        <>
          {classes.length === 0 ? (
            <p className="mt-4 text-slate">{t("set.noJoined")}</p>
          ) : (
            <ul className="mt-4 divide-y divide-ink/[0.07] border-y border-ink/[0.07]">
              {classes.map((c) => (
                <li key={c.classroom_id} className="flex items-center justify-between gap-4 py-3">
                  <span className="font-medium">{c.name}</span>
                  <Button variant="quiet" disabled={busy} onClick={() => leave(c.classroom_id)} className="shrink-0">
                    {t("set.leave")}
                  </Button>
                </li>
              ))}
            </ul>
          )}
          <form onSubmit={join} className="mt-5 flex flex-wrap items-end gap-2">
            <Field
              id={`join-${child.id}`}
              label={t("set.joinCode")}
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              autoComplete="off"
              maxLength={16}
              className="tracking-[0.15em] tabular uppercase"
            />
            <Button type="submit" disabled={busy || !code.trim()}>{t("set.join")}</Button>
          </form>
          {error && <p role="alert" className="mt-2 text-sm font-medium text-mendesak">{error}</p>}
        </>
      )}
    </section>
  );
}

// --- Per-child settings: consent scopes and data ---

function SettingsPanel({ child }: { child: Child }) {
  const { t } = useT();
  const { reload } = useDash();
  const router = useRouter();
  const [text, setText] = useState<ConsentText | null>(null);
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmingClear, setConfirmingClear] = useState(false);
  const [cleared, setCleared] = useState(false);

  useEffect(() => {
    api<ConsentText>("consents/text").then(setText, () => undefined);
  }, []);

  async function toggle(scope: Scope, on: boolean) {
    if (!text) return;
    setBusy(true);
    try {
      await api("consents", {
        method: "POST",
        body: { child_id: child.id, text_version: text.version, action: on ? "grant" : "revoke", scopes: [scope] },
      });
      await reload();
    } finally {
      setBusy(false);
    }
  }

  async function clearHistory() {
    setBusy(true);
    try {
      await api(`children/${child.id}/history`, { method: "DELETE" });
      setConfirmingClear(false);
      setCleared(true);
    } finally {
      setBusy(false);
    }
  }

  async function erase() {
    setBusy(true);
    await api(`children/${child.id}/data`, { method: "DELETE" });
    await reload();
    router.push("/dasbor");
  }

  return (
    <div className="space-y-6">
      <section className="glass rounded-2xl p-6 sm:p-7" aria-labelledby="consent-h">
        <h2 id="consent-h" className="text-lg font-bold">{t("set.consent")}</h2>
        <p className="mt-1 max-w-[62ch] text-sm text-slate">{t("dash.settingsLead")}</p>
        <ul className="mt-4 divide-y divide-ink/[0.07] border-y border-ink/[0.07]">
          {(text?.scopes ?? []).map((s) => {
            const on = child.consent_scopes.includes(s);
            return (
              <li key={s} className="flex items-center justify-between gap-4 py-3">
                <span>
                  <span className="block font-medium">{t(`scope.${s}`)}</span>
                  <span className="block text-sm text-slate">{t(`scopeHint.${s}`)}</span>
                </span>
                <Button variant={on ? "quiet" : "primary"} disabled={busy} onClick={() => toggle(s, !on)} className="shrink-0">
                  {on ? t("set.withdraw") : t("set.grant")}
                </Button>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="glass rounded-2xl p-6 sm:p-7" aria-labelledby="clear-h">
        <h2 id="clear-h" className="text-lg font-bold">{t("set.clearHistory")}</h2>
        <p className="mt-1 max-w-[62ch] text-sm text-slate">{t("set.clearHistoryHint")}</p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {confirmingClear ? (
            <>
              <Button variant="danger" disabled={busy} onClick={clearHistory}>{t("set.clearConfirm")}</Button>
              <Button variant="quiet" disabled={busy} onClick={() => setConfirmingClear(false)}>{t("common.cancel")}</Button>
            </>
          ) : (
            <Button variant="quiet" onClick={() => { setCleared(false); setConfirmingClear(true); }}>{t("set.clearHistory")}</Button>
          )}
          {cleared && <span role="status" className="text-sm text-aman">{t("set.cleared")}</span>}
        </div>
      </section>

      <section className="rounded-2xl border border-mendesak/30 bg-mendesak-soft/40 px-6 py-6" aria-labelledby="delete-h">
        <h2 id="delete-h" className="font-bold text-mendesak">{t("set.delete")}</h2>
        <p className="mt-1 max-w-[60ch] text-sm text-slate">{t("set.deleteHint")}</p>
        <label className="mt-4 block text-sm font-semibold" htmlFor={`del-${child.id}`}>
          {t("set.deleteConfirm")}
        </label>
        <div className="mt-1.5 flex flex-wrap gap-2">
          <input
            id={`del-${child.id}`}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="off"
            className="rounded-xl border border-ink/10 bg-white/75 px-3 py-2 outline-none focus:border-mendesak"
          />
          <Button variant="danger" disabled={busy || confirm !== child.nickname} onClick={erase}>
            {t("set.deleteButton")}
          </Button>
        </div>
      </section>
    </div>
  );
}
