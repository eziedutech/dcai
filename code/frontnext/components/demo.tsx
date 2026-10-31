"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";
import type { Level } from "@/lib/types";
import { LevelBadge } from "./ui";

// One synthetic chat played as if it were happening now. The contact types, messages
// arrive, the child answers; each time dcAI sees a pattern, only the pattern travels to the
// parent's view. Starts when the demo scrolls into view, loops, and shows the last frame
// at once when the reader asks for reduced motion.

type Bubble = { from: "contact" | "child"; key: "msg1" | "msg2" | "msg3" | "reply1" | "reply2" };
type Frame = {
  bubbles: number; // how many of BUBBLES are shown
  typing: "contact" | "child" | null;
  packet: string[] | null; // pattern keys on their way to the parent
  level: Level;
  patterns: number; // how many of PATTERNS the parent sees
  nudge: boolean;
  starter: boolean;
  ms: number; // how long this frame stays
};

const BUBBLES: Bubble[] = [
  { from: "contact", key: "msg1" },
  { from: "child", key: "reply1" },
  { from: "contact", key: "msg2" },
  { from: "child", key: "reply2" },
  { from: "contact", key: "msg3" },
];
const PATTERNS = ["p0", "p2", "p1", "p3", "p4"] as const;

const base = { typing: null, packet: null, nudge: false, starter: false } as const;
const FRAMES: Frame[] = [
  { ...base, bubbles: 0, level: "aman", patterns: 0, ms: 150 },
  { ...base, bubbles: 0, typing: "contact", level: "aman", patterns: 0, ms: 550 },
  { ...base, bubbles: 1, level: "aman", patterns: 0, ms: 250 },
  { ...base, bubbles: 1, packet: ["p0"], level: "aman", patterns: 0, ms: 450 },
  { ...base, bubbles: 1, typing: "child", level: "perhatian", patterns: 1, ms: 500 },
  { ...base, bubbles: 2, level: "perhatian", patterns: 1, ms: 350 },
  { ...base, bubbles: 2, typing: "contact", level: "perhatian", patterns: 1, ms: 600 },
  { ...base, bubbles: 3, level: "perhatian", patterns: 1, ms: 250 },
  { ...base, bubbles: 3, packet: ["p2", "p1"], level: "perhatian", patterns: 1, ms: 450 },
  { ...base, bubbles: 3, typing: "child", level: "waspada", patterns: 3, ms: 400 },
  { ...base, bubbles: 4, level: "waspada", patterns: 3, ms: 300 },
  { ...base, bubbles: 4, typing: "contact", level: "waspada", patterns: 3, ms: 600 },
  { ...base, bubbles: 5, level: "waspada", patterns: 3, ms: 250 },
  { ...base, bubbles: 5, packet: ["p3", "p4"], level: "waspada", patterns: 3, ms: 450 },
  { ...base, bubbles: 5, level: "mendesak", patterns: 5, ms: 350 },
  { ...base, bubbles: 5, level: "mendesak", patterns: 5, nudge: true, ms: 400 },
  { ...base, bubbles: 5, level: "mendesak", patterns: 5, nudge: true, starter: true, ms: 3000 },
];
/**
 * Plays frames in a loop while the demo is on screen. It starts as soon as a little of it
 * shows, so the reader arriving at the section sees it already moving; with reduced motion
 * it shows the last frame and stays.
 */
export function useFrameClock<F extends { ms: number }>(frames: F[]) {
  const ref = useRef<HTMLDivElement>(null);
  const [frame, setFrame] = useState(0);
  const [running, setRunning] = useState(false);
  const last = frames.length - 1;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one static frame
      setFrame(last);
      return;
    }
    const io = new IntersectionObserver(([e]) => setRunning(e.isIntersecting), { threshold: 0.05, rootMargin: "0px 0px 15% 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, [last]);

  useEffect(() => {
    if (!running) return;
    const id = setTimeout(() => setFrame((f) => (f >= last ? 0 : f + 1)), frames[frame].ms);
    return () => clearTimeout(id);
  }, [running, frame, frames, last]);

  return { ref, f: frames[frame], frame };
}

function Ticks() {
  return (
    <svg width="16" height="10" viewBox="0 0 16 10" aria-hidden className="inline-block">
      <path d="M1 5.5 3.8 8.2 9 2.2M6.5 8.2 7 8.6 13.8 1.4" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Typing({ side }: { side: "contact" | "child" }) {
  return (
    <li
      aria-hidden
      className={`arrive flex w-fit gap-1 rounded-2xl px-3.5 py-3 ${
        side === "contact" ? "rounded-bl-md bg-white shadow-sm" : "ml-auto rounded-br-md bg-navy/90"
      }`}
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className={`typing-dot h-1.5 w-1.5 rounded-full ${side === "contact" ? "bg-slate/60" : "bg-white/80"}`}
          style={{ animationDelay: `${i * 160}ms` }}
        />
      ))}
    </li>
  );
}

/** The bridge between the phone and the parent: only labels cross it, never text. */
function Bridge({ packet, frame }: { packet: string[] | null; frame: number }) {
  const { t } = useT();
  return (
    <div className="relative flex items-center justify-center py-2 lg:mt-[9.5rem] lg:w-28 lg:self-start lg:py-0" aria-hidden>
      {/* the track: vertical when stacked, horizontal beside */}
      <div className="absolute top-0 bottom-0 left-1/2 w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-navy/25 to-transparent lg:top-1/2 lg:right-0 lg:bottom-auto lg:left-0 lg:h-px lg:w-auto lg:translate-x-0 lg:-translate-y-1/2 lg:bg-gradient-to-r" />
      <div className="relative z-10 flex flex-col items-center gap-2">
        <span className="glass grid h-12 w-12 place-items-center rounded-2xl">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/dcai-logo.png" alt="" width={22} height={26} className="h-6 w-auto" />
        </span>
        <span className="glass-fill flex items-center gap-1 rounded-full px-2.5 py-1 text-[0.68rem] font-semibold whitespace-nowrap text-slate">
          <svg width="10" height="10" viewBox="0 0 16 16" aria-hidden>
            <rect x="3" y="7" width="10" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
            <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="currentColor" strokeWidth="1.6" />
          </svg>
          {t("home.demo.bridge")}
        </span>
      </div>
      {packet && (
        <span key={frame} className="packet absolute z-20 flex flex-col gap-1">
          {packet.map((p) => (
            <span key={p} className="rounded-full bg-navy px-2.5 py-1 text-[0.68rem] font-semibold whitespace-nowrap text-paper shadow-[0_8px_18px_-8px_rgba(31,58,95,0.8)]">
              {t(`home.demo.${p}` as "home.demo.p1")}
            </span>
          ))}
        </span>
      )}
    </div>
  );
}

// Published figures, quoted as their sources state them; each tile links to its source.
const UNICEF = "https://www.unicef.org/press-releases/1-5-children-across-21-countries-have-experienced-tech-facilitated-sexual";
const LANCET = "https://doi.org/10.1016/S2352-4642(24)00329-8";
const STATS = [
  { n: "s1", href: UNICEF },
  { n: "s3", href: UNICEF },
  { n: "s4", href: LANCET },
] as const;

/**
 * Why it matters: three published figures as a quiet band between the hero and the demos,
 * in the same hairline-column rhythm as the rest of the page and the number style of /fakta.
 */
export function FactsBand() {
  const { t } = useT();
  return (
    <div className="mt-10">
      <div className="flex flex-wrap items-baseline justify-end gap-3">
        <Link href="/fakta" className="inline-flex items-center gap-1.5 text-[0.88rem] font-semibold text-navy underline-offset-4 hover:underline">
          {t("home.stats.more")}
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
            <path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </Link>
      </div>
      <ul className="mt-5 grid gap-5 sm:grid-cols-3">
        {STATS.map(({ n, href }) => (
          <li key={n} className="glass flex flex-col rounded-3xl p-6 sm:p-7">
            <span aria-hidden className="block h-1 w-10 rounded-full bg-navy/70" />
            <p className="mt-5 text-[2.4rem] font-bold leading-none tracking-[-0.03em] text-navy tabular">{t(`home.stats.${n}.v`)}</p>
            <p className="mt-3 flex-1 text-[0.95rem] leading-snug text-ink/75">{t(`home.stats.${n}.b`)}</p>
            <a href={href} target="_blank" rel="noopener noreferrer" className="mt-5 inline-block border-t border-ink/[0.08] pt-4 text-[0.78rem] font-semibold text-slate underline-offset-4 hover:text-navy hover:underline">
              {t(`home.stats.${n}.src`)}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function LiveDemo() {
  const { t } = useT();
  const { ref, f, frame } = useFrameClock(FRAMES);
  const assessing = f.packet !== null;
  return (
    <div ref={ref} className="grid items-stretch gap-4 lg:grid-cols-[minmax(0,22rem)_auto_minmax(0,1fr)] lg:gap-6">
      <figure className="mx-auto w-full max-w-[22rem]">
        <figcaption className="mb-3 text-sm font-semibold text-slate">{t("home.demo.child")}</figcaption>
        <div className="rounded-[var(--radius-phone)] border-[7px] border-ink bg-ink p-1 shadow-[0_30px_60px_-30px_rgba(20,35,58,0.6)]">
          <div className="flex h-[30rem] flex-col overflow-hidden rounded-[22px] bg-[#f4f6f9]">
            <div className="flex items-center gap-3 border-b border-line bg-white px-4 py-3">
              <span aria-hidden className="grid h-8 w-8 place-items-center rounded-full bg-mist text-sm font-bold text-slate">?</span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold">{t("home.demo.contact")}</span>
                <span className={`block h-4 text-xs text-aman transition-opacity ${f.typing === "contact" ? "opacity-100" : "opacity-0"}`}>
                  {t("home.demo.typing")}
                </span>
              </span>
            </div>
            <ol className="flex min-h-0 flex-1 flex-col justify-end gap-2 overflow-hidden px-3.5 py-3 text-[0.9rem] leading-snug" aria-live="off">
              {BUBBLES.slice(0, f.bubbles).map((b) => (
                <li
                  key={b.key}
                  className={`arrive max-w-[82%] px-3.5 py-2 ${
                    b.from === "contact"
                      ? "rounded-2xl rounded-bl-md bg-white shadow-sm"
                      : "ml-auto rounded-2xl rounded-br-md bg-navy text-paper"
                  }`}
                >
                  {t(`home.demo.${b.key}`)}
                  {b.from === "child" && (
                    <span className="ml-1.5 inline-flex translate-y-px items-center text-[#8fd3c2]">
                      <Ticks />
                    </span>
                  )}
                </li>
              ))}
              {f.typing && <Typing side={f.typing} />}
            </ol>
            <div className={`grid transition-[grid-template-rows] duration-500 ${f.nudge ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
              <div className="overflow-hidden">
                <div role="note" className="m-2.5 rounded-2xl border border-navy/15 bg-white p-3.5 shadow-[0_8px_24px_-12px_rgba(31,58,95,0.5)]">
                  <p className="mb-1 flex items-center gap-2 text-xs font-bold text-navy">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/dcai-logo.png" alt="" width={12} height={14} className="h-3.5 w-auto" />
                    dcAI
                  </p>
                  <p className="text-[0.9rem] leading-snug text-ink">{t("home.demo.nudge")}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </figure>

      <Bridge packet={f.packet} frame={frame} />

      <div className="w-full">
        <p className="eyebrow">{t("home.demo.eyebrow")}</p>
        <h3 id="demo-h" className="mt-2 max-w-[22ch] text-[1.5rem] font-bold leading-tight tracking-[-0.02em]">
          {t("home.demo.title")}
        </h3>
        <p className="mt-2 mb-6 max-w-[52ch] text-[0.95rem] leading-snug text-ink/75">{t("home.demo.lead")}</p>
        <figure className="w-full">
          <figcaption className="mb-3 text-sm font-semibold text-slate">{t("home.demo.parent")}</figcaption>
          <div className="glass-fill rounded-2xl bg-white/80 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-lg font-bold">Raka, 10-12</p>
            <span key={f.level} className="arrive">
              <LevelBadge level={f.level} size="lg" />
            </span>
          </div>
          <p className="mt-5 flex items-center gap-2 text-sm font-semibold text-slate">
            {t("home.demo.patterns")}
            <span className={`text-xs font-medium text-navy transition-opacity ${assessing ? "opacity-100" : "opacity-0"}`}>
              {t("home.demo.analyzing")}
            </span>
          </p>
          <ul className="mt-2 flex min-h-[4.5rem] flex-wrap content-start gap-2">
            {f.patterns === 0 && <li className="text-sm text-slate">{t("home.demo.none")}</li>}
            {PATTERNS.slice(0, f.patterns).map((p) => (
              <li key={p} className="arrive rounded-full bg-mist px-3 py-1 text-sm font-medium">
                {t(`home.demo.${p}`)}
              </li>
            ))}
          </ul>
          <div className={`grid transition-[grid-template-rows] duration-500 ${f.starter ? "grid-rows-[1fr]" : "grid-rows-[0fr]"}`}>
            <div className="overflow-hidden">
              <p className="mt-5 text-sm font-semibold text-slate">{t("home.demo.starter")}</p>
              <p className="mt-1.5 text-[1.05rem] font-medium leading-snug">&ldquo;{t("home.demo.starterText")}&rdquo;</p>
            </div>
          </div>
          <p className="mt-6 flex items-start gap-2 border-t border-line pt-4 text-sm text-slate">
            <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden className="mt-0.5 shrink-0">
              <rect x="3" y="7" width="10" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            {t("home.demo.noText")}
          </p>
          </div>
        </figure>
      </div>
    </div>
  );
}
