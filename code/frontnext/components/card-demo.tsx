"use client";

import { useT } from "@/lib/i18n";
import type { Level } from "@/lib/types";
import { useFrameClock } from "./demo";
import { LevelBadge } from "./ui";

// A synthetic chat in Messenger Z, the sample chat app: a "prize" asks for a student card,
// the child picks it from the gallery, dcAI checks it on the phone and blurs the personal
// lines before it is sent. The parent's view gets the patterns and the event, never the
// image. Colours follow the app (purple header, lavender wallpaper).

type Frame = {
  bubbles: number; // how many of BUBBLES are shown
  typing: boolean; // the contact is typing
  sheet: boolean; // the gallery is open
  checking: boolean; // the card bubble shows dcAI checking the image
  level: Level;
  patterns: number; // how many of PATTERNS the parent sees
  nudge: boolean;
  starter: boolean;
  ms: number;
};

const BUBBLES = [
  { from: "contact", key: "msg1", time: "19.02" },
  { from: "child", key: "reply1", time: "19.02" },
  { from: "contact", key: "msg2", time: "19.03" },
  { from: "child", key: "card", time: "19.03" },
  { from: "contact", key: "msg3", time: "19.04" },
] as const;
const PATTERNS = ["p0", "p1", "p2"] as const;

const base = { typing: false, sheet: false, checking: false, nudge: false, starter: false } as const;
const FRAMES: Frame[] = [
  { ...base, bubbles: 0, level: "aman", patterns: 0, ms: 150 },
  { ...base, bubbles: 0, typing: true, level: "aman", patterns: 0, ms: 550 },
  { ...base, bubbles: 1, level: "aman", patterns: 0, ms: 300 },
  { ...base, bubbles: 1, level: "perhatian", patterns: 1, ms: 400 },
  { ...base, bubbles: 2, level: "perhatian", patterns: 1, ms: 350 },
  { ...base, bubbles: 2, typing: true, level: "perhatian", patterns: 1, ms: 600 },
  { ...base, bubbles: 3, level: "perhatian", patterns: 1, ms: 300 },
  { ...base, bubbles: 3, level: "perhatian", patterns: 2, ms: 300 },
  { ...base, bubbles: 3, sheet: true, level: "perhatian", patterns: 2, ms: 800 },
  { ...base, bubbles: 4, checking: true, level: "perhatian", patterns: 2, ms: 900 },
  { ...base, bubbles: 4, level: "perhatian", patterns: 3, ms: 500 },
  { ...base, bubbles: 4, typing: true, level: "perhatian", patterns: 3, ms: 600 },
  { ...base, bubbles: 5, level: "perhatian", patterns: 3, ms: 300 },
  { ...base, bubbles: 5, level: "waspada", patterns: 3, ms: 350 },
  { ...base, bubbles: 5, level: "waspada", patterns: 3, nudge: true, ms: 450 },
  { ...base, bubbles: 5, level: "waspada", patterns: 3, nudge: true, starter: true, ms: 3000 },
];

const PURPLE = "#4C1D95";
// Every line is invented; on the phone they are blurred before sending.
const CARD_LINES = ["SMP Negeri 5 Makassar", "Nama: Rani Putri", "Jl. Mawar No. 12", "HP 0812-3456-7890"];

function Ticks() {
  return (
    <svg width="15" height="10" viewBox="0 0 16 10" aria-hidden className="inline-block" style={{ color: PURPLE }}>
      <path d="M1 5.5 3.8 8.2 9 2.2M6.5 8.2 7 8.6 13.8 1.4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Shield({ size = 12 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden className="shrink-0">
      <path d="M8 1.5 13 3.5v4c0 3.2-2.1 5.6-5 7-2.9-1.4-5-3.8-5-7v-4z" fill="currentColor" />
    </svg>
  );
}

/** The made-up card, sharp in the child's own gallery, blurred once dcAI has checked it. */
function Card({ blurred, small = false }: { blurred: boolean; small?: boolean }) {
  return (
    <span className={`block overflow-hidden rounded-lg bg-[#e8f0fe] text-left text-[#14233a] ${small ? "w-full" : "w-[12rem]"}`}>
      <span className={`block bg-[#1f3a5f] font-bold tracking-wide text-white ${small ? "px-1.5 py-0.5 text-[0.42rem]" : "px-2.5 py-1 text-[0.6rem]"}`}>
        KARTU PELAJAR
      </span>
      <span aria-hidden className={`block leading-tight ${small ? "space-y-0.5 px-1.5 py-1 text-[0.4rem]" : "space-y-1 px-2.5 py-2 text-[0.64rem]"}`}>
        {CARD_LINES.map((line) => (
          <span key={line} className={`block select-none ${blurred ? "blur-[3px]" : ""}`}>
            {line}
          </span>
        ))}
      </span>
    </span>
  );
}

function CardBubble({ checking }: { checking: boolean }) {
  const { t } = useT();
  if (checking) {
    return (
      <span className="flex h-[6.4rem] w-[12rem] items-center justify-center gap-2 rounded-lg bg-black/[0.05] text-[0.74rem] text-[#6b6578]">
        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#4C1D95]/25 border-t-[#4C1D95]" aria-hidden />
        {t("home.card.checking")}
      </span>
    );
  }
  return (
    <span className="arrive block">
      <span role="img" aria-label={t("home.card.card")} className="block">
        <Card blurred />
      </span>
      <span className="mt-1.5 flex items-start gap-1.5 text-[0.7rem] leading-snug text-[#1a1a1a]">
        <span style={{ color: PURPLE }} className="mt-px">
          <Shield size={11} />
        </span>
        {t("home.card.blurred")}
      </span>
    </span>
  );
}

function Typing() {
  return (
    <li aria-hidden className="arrive flex w-fit gap-1 rounded-2xl rounded-bl-md bg-white px-3.5 py-3 shadow-sm">
      {[0, 1, 2].map((i) => (
        <span key={i} className="typing-dot h-1.5 w-1.5 rounded-full bg-[#6b6578]/60" style={{ animationDelay: `${i * 160}ms` }} />
      ))}
    </li>
  );
}

function Phone({ f }: { f: Frame }) {
  const { t } = useT();
  return (
    <figure className="mx-auto w-full max-w-[22rem]">
      <figcaption className="mb-3 text-sm font-semibold text-slate">{t("home.card.phone")}</figcaption>
      <div className="rounded-[var(--radius-phone)] border-[7px] border-ink bg-ink p-1 shadow-[0_30px_60px_-30px_rgba(20,35,58,0.6)]">
        <div className="relative flex h-[32rem] flex-col overflow-hidden rounded-[22px] bg-[#f4f1f8]">
          {/* header */}
          <div className="flex items-center gap-2.5 px-3 pt-3 pb-2.5 text-white" style={{ background: PURPLE }}>
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
              <path d="M15 5 8 12l7 7" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <span aria-hidden className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-[#EA580C] text-[0.7rem] font-bold">AE</span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold">{t("home.card.contact")}</span>
              <span className="block text-[0.68rem] text-white/85">{f.typing ? t("home.card.typing") : t("home.card.online")}</span>
            </span>
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden className="opacity-90">
              <path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z" fill="currentColor" />
            </svg>
            <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden className="opacity-90">
              <circle cx="12" cy="5" r="2" fill="currentColor" />
              <circle cx="12" cy="12" r="2" fill="currentColor" />
              <circle cx="12" cy="19" r="2" fill="currentColor" />
            </svg>
          </div>

          {/* chat */}
          <ol className="flex min-h-0 flex-1 flex-col justify-end gap-1.5 overflow-hidden px-2.5 py-2.5 text-[0.86rem] leading-snug" aria-live="off">
            {BUBBLES.slice(0, f.bubbles).map((b) => {
              const mine = b.from === "child";
              return (
                <li
                  key={b.key}
                  className={`arrive max-w-[84%] px-2.5 pt-1.5 pb-1 text-[#1a1a1a] ${
                    mine ? "ml-auto rounded-2xl rounded-br-md bg-[#e9e0fb]" : "rounded-2xl rounded-bl-md bg-white shadow-sm"
                  }`}
                >
                  {b.key === "card" ? <CardBubble checking={f.checking} /> : t(`home.card.${b.key}`)}
                  <span className="mt-0.5 flex items-center justify-end gap-1 text-[0.62rem] text-[#6b6578]">
                    {b.time}
                    {mine && <Ticks />}
                  </span>
                </li>
              );
            })}
            {f.typing && <Typing />}
          </ol>

          {/* composer */}
          <div className="flex items-center gap-1.5 px-2 pb-2.5">
            <span className="flex flex-1 items-center gap-2 rounded-full bg-white px-3 py-2 text-[0.8rem] text-[#6b6578]">
              <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden>
                <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.8" />
                <path d="M8.5 14.5a4.5 4.5 0 0 0 7 0M9 10h.01M15 10h.01" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
              <span className="flex-1">{t("home.card.message")}</span>
              <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden className={f.sheet ? "text-[#4C1D95]" : ""}>
                <path d="M16.5 6.5v10a4.5 4.5 0 0 1-9 0V5a3 3 0 0 1 6 0v10.5a1.5 1.5 0 0 1-3 0V6.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
              </svg>
            </span>
            <span className="grid h-9 w-9 place-items-center rounded-full text-white" style={{ background: PURPLE }}>
              <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden>
                <path d="M3 20.5 21 12 3 3.5l.01 6.6L15 12 3.01 13.9z" fill="currentColor" />
              </svg>
            </span>
          </div>

          {/* gallery sheet */}
          <div
            aria-hidden={!f.sheet}
            className={`absolute inset-x-0 bottom-0 rounded-t-2xl bg-white px-4 pt-2.5 pb-5 shadow-[0_-12px_30px_-14px_rgba(20,35,58,0.45)] transition-transform duration-300 ${
              f.sheet ? "translate-y-0" : "translate-y-full"
            }`}
          >
            <span className="mx-auto mb-2.5 block h-1 w-9 rounded-full bg-[#c9c3d4]" />
            <p className="mb-2.5 text-sm font-semibold text-[#1a1a1a]">{t("home.card.gallery")}</p>
            <div className="grid grid-cols-2 gap-2.5">
              <span className="block rounded-xl p-1 ring-2 ring-[#4C1D95]">
                <Card blurred={false} small />
                <span className="mt-1 block text-[0.66rem] text-[#6b6578]">{t("home.card.cardName")}</span>
              </span>
              <span className="block p-1">
                <span className="block h-[3.1rem] rounded-lg bg-gradient-to-b from-[#7dc4ff] to-[#ffe0b2]" />
                <span className="mt-1 block text-[0.66rem] text-[#6b6578]">{t("home.card.landscape")}</span>
              </span>
            </div>
          </div>

          {/* dcAI's nudge arrives as a notification */}
          <div
            role="note"
            aria-hidden={!f.nudge}
            className={`absolute inset-x-2 top-2 rounded-2xl bg-white p-3 shadow-[0_14px_30px_-12px_rgba(20,35,58,0.55)] transition-all duration-300 ${
              f.nudge ? "translate-y-0 opacity-100" : "-translate-y-[120%] opacity-0"
            }`}
          >
            <p className="flex items-center gap-1.5 text-[0.68rem] text-[#6b6578]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/dcai-logo.png" alt="" width={12} height={14} className="h-3.5 w-auto" />
              <span className="font-semibold text-navy">dcAI</span>
              <span>· {t("home.card.now")}</span>
            </p>
            <p className="mt-1 text-[0.8rem] font-semibold text-ink">{t("home.card.nudgeTitle")}</p>
            <p className="mt-0.5 text-[0.78rem] leading-snug text-ink/85">{t("home.card.nudge")}</p>
          </div>
        </div>
      </div>
    </figure>
  );
}

export function CardDemo() {
  const { t } = useT();
  const { ref, f } = useFrameClock(FRAMES);
  return (
    <section className="mx-auto mt-8 max-w-6xl px-5 sm:px-8" aria-labelledby="card-h">
      <div ref={ref} className="glass grid items-start gap-8 rounded-[2rem] p-5 sm:p-8 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] lg:gap-12">
        <Phone f={f} />
        <div>
          <p className="eyebrow">{t("home.card.eyebrow")}</p>
          <h2 id="card-h" className="mt-3 max-w-[22ch] text-[2rem] font-bold leading-tight tracking-[-0.02em]">
            {t("home.card.title")}
          </h2>
          <p className="mt-4 max-w-[58ch] text-ink/75">{t("home.card.lead")}</p>

          <figure className="mt-7">
            <figcaption className="mb-3 text-sm font-semibold text-slate">{t("home.demo.parent")}</figcaption>
            <div className="glass-fill rounded-2xl bg-white/80 p-6">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-lg font-bold">Rani, 13-15</p>
                <span key={f.level} className="arrive">
                  <LevelBadge level={f.level} size="lg" />
                </span>
              </div>
              <p className="mt-5 text-sm font-semibold text-slate">{t("home.demo.patterns")}</p>
              <ul className="mt-2 flex min-h-[4.5rem] flex-wrap content-start gap-2">
                {f.patterns === 0 && <li className="text-sm text-slate">{t("home.demo.none")}</li>}
                {PATTERNS.slice(0, f.patterns).map((p) => (
                  <li
                    key={p}
                    className={`arrive flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium ${p === "p2" ? "bg-navy/10 text-navy" : "bg-mist"}`}
                  >
                    {p === "p2" && <Shield />}
                    {t(`home.card.${p}`)}
                  </li>
                ))}
              </ul>
              <div className={`grid transition-[grid-template-rows] duration-500 ${f.starter ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
                <div className="overflow-hidden">
                  <p className="mt-5 text-sm font-semibold text-slate">{t("home.demo.starter")}</p>
                  <p className="mt-1.5 text-[1.05rem] font-medium leading-snug">&ldquo;{t("home.card.starterText")}&rdquo;</p>
                </div>
              </div>
              <p className="mt-6 flex items-start gap-2 border-t border-line pt-4 text-sm text-slate">
                <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden className="mt-0.5 shrink-0">
                  <rect x="3" y="7" width="10" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
                  <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="currentColor" strokeWidth="1.5" />
                </svg>
                {t("home.card.noImage")}
              </p>
            </div>
          </figure>
        </div>
      </div>
    </section>
  );
}
