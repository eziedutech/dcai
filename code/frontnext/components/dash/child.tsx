"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { follow } from "@/lib/sse";
import type { Conversation, EventRow, Insight, Level, Overview } from "@/lib/types";
import { LEVEL_STYLE, LevelBadge, Skeleton, appLabel, formatWhen } from "../ui";

type Data = { overview: Overview; events: EventRow[]; conversations: Conversation[] };

export function ChildView({ childId }: { childId: string }) {
  const { t, tx, lang } = useT();
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState(false);
  const [live, setLive] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    try {
      const [overview, events, conversations] = await Promise.all([
        api<Overview>(`children/${childId}/overview`),
        api<EventRow[]>(`children/${childId}/events?days=30&limit=40`),
        api<Conversation[]>(`children/${childId}/conversations?days=30`),
      ]);
      setData({ overview, events, conversations });
      setError(false);
    } catch {
      setError(true);
    }
  }, [childId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch on mount and child change
    void load();
    const stop = follow(`children/${childId}/stream`, () => {
      setLive(true);
      // Several updates arrive together (event, assessment, insight): reload once.
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
    <div className="mx-auto max-w-5xl">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-[2rem] font-bold tracking-[-0.02em]">{ov.nickname}</h1>
          <p className="text-slate">
            {ov.age_range} {t("common.age")}
          </p>
        </div>
        <p className="flex items-center gap-2 text-sm text-slate" aria-live="polite">
          <span aria-hidden className={`inline-block h-2 w-2 rounded-full ${live ? "bg-aman" : "bg-line"}`} />
          {live ? t("dash.live") : t("dash.window")}
        </p>
      </header>

      <LevelStrip ov={ov} />

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <section aria-labelledby="insight-h" className="glass rounded-3xl p-6 sm:p-7">
          <h2 id="insight-h" className="text-lg font-bold">{t("dash.latestInsight")}</h2>
          {ov.latest_insight ? (
            <InsightBlock insight={ov.latest_insight} />
          ) : (
            <p className="mt-3 max-w-[56ch] text-slate">{t("dash.noInsight")}</p>
          )}
        </section>
        <div className="space-y-6">
          <Protection ov={ov} childId={childId} />
          <section aria-labelledby="events-h" className="glass rounded-3xl p-6">
            <h2 id="events-h" className="text-lg font-bold">{t("dash.events")}</h2>
            {events.length === 0 ? (
              <p className="mt-3 text-slate">{t("dash.noEvents")}</p>
            ) : (
              <ol className="mt-3 ml-1 border-l-2 border-ink/10">
                {events.map((e) => (
                  <li key={e.id} className="relative py-2 pl-5">
                    <span
                      aria-hidden
                      className={`absolute top-[0.95rem] -left-[5px] h-2 w-2 rounded-full ${LEVEL_STYLE[e.level as Level]?.bar ?? "bg-slate"}`}
                    />
                    <p className="text-[0.95rem] font-medium">{tx(`event.${e.kind}`, e.kind)}</p>
                    <p className="text-sm text-slate tabular">{formatWhen(e.created_at, lang)}</p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </div>

      <section className="glass mt-6 rounded-3xl p-6 sm:p-7" aria-labelledby="conv-h">
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
    </div>
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
    <section className="glass relative mt-8 overflow-hidden rounded-3xl px-7 py-7" aria-labelledby="level-h">
      <div aria-hidden className={`absolute inset-0 ${s.bg} opacity-45`} />
      <div className="relative flex flex-wrap items-start justify-between gap-6">
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
      </div>
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
      <ul className="mt-2 space-y-2">
        {pi.conversation_starters.map((s) => (
          <li key={s} className="glass-fill rounded-xl border-l-4 !border-l-navy px-4 py-2.5 text-[1.02rem] font-medium">
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

function Protection({ ov, childId }: { ov: Overview; childId: string }) {
  const { t, tx, lang } = useT();
  return (
    <section aria-labelledby="prot-h" className="glass rounded-3xl p-6">
      <h2 id="prot-h" className="text-lg font-bold">{t("dash.protection")}</h2>
      {ov.devices.length === 0 ? (
        <div className="mt-3">
          <p className="text-slate">{t("dash.noDevice")}</p>
          <Link href={`/dasbor/tambah?anak=${childId}`} className="mt-2 inline-block font-semibold text-navy underline-offset-4 hover:underline">
            {t("dash.pairNow")}
          </Link>
        </div>
      ) : (
        <ul className="mt-3 space-y-4">
          {ov.devices.map((d) => (
            <li key={d.device_id}>
              <p className="flex items-center justify-between gap-3">
                <span className="font-medium">{d.name}</span>
                <span className={`text-sm font-semibold ${d.protection_on ? "text-aman" : "text-mendesak"}`}>
                  {d.protection_on ? t("dash.protectionOn") : t("dash.protectionOff")}
                </span>
              </p>
              <ul className="mt-1.5 space-y-0.5 text-sm text-slate">
                {Object.entries(d.services).map(([name, on]) => (
                  <li key={name} className="flex justify-between">
                    <span>{tx(`service.${name}`, name)}</span>
                    <span className={on ? "" : "font-semibold text-mendesak"}>{on ? t("dash.protectionOn") : t("dash.protectionOff")}</span>
                  </li>
                ))}
              </ul>
              {d.last_seen_at && (
                <p className="mt-1 text-sm text-slate tabular">
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
