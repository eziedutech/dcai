"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n";
import { Parallax } from "./motion";
import { LevelBadge, SiteFooter, SiteHeader } from "./ui";

/** Child's screen on the left, parent's view on the right: the same moment, and only the
 * pattern crosses over. The one animation on the page. */
function SplitDemo() {
  const { t } = useT();
  const msgs = ["home.demo.msg1", "home.demo.msg2", "home.demo.msg3"] as const;
  const patterns = ["home.demo.p1", "home.demo.p2", "home.demo.p3", "home.demo.p4"] as const;
  return (
    <div className="grid items-stretch gap-6 lg:grid-cols-[minmax(0,22rem)_auto_minmax(0,1fr)]">
      <figure className="mx-auto w-full max-w-[22rem]">
        <figcaption className="mb-3 text-sm font-semibold text-slate">{t("home.demo.child")}</figcaption>
        <Parallax speed={-0.035}>
          <div className="rounded-[var(--radius-phone)] border-[7px] border-ink bg-ink p-1 shadow-[0_30px_60px_-30px_rgba(20,35,58,0.6)]">
            <div className="flex min-h-[27rem] flex-col rounded-[22px] bg-[#f4f6f9]">
              <div className="flex items-center gap-3 rounded-t-[22px] border-b border-line bg-white px-4 py-3">
                <span aria-hidden className="grid h-8 w-8 place-items-center rounded-full bg-mist text-sm font-bold text-slate">?</span>
                <span className="text-sm font-semibold">{t("home.demo.contact")}</span>
              </div>
              <ol className="flex flex-1 flex-col gap-2.5 px-3.5 py-4 text-[0.92rem] leading-snug">
                {msgs.map((m, i) => (
                  <li
                    key={m}
                    className="arrive max-w-[85%] rounded-2xl rounded-bl-md bg-white px-3.5 py-2 shadow-sm"
                    style={{ animationDelay: `${250 + i * 650}ms` }}
                  >
                    {t(m)}
                  </li>
                ))}
              </ol>
              <div
                className="arrive m-2.5 rounded-2xl border border-navy/15 bg-white p-3.5 shadow-[0_8px_24px_-12px_rgba(31,58,95,0.5)]"
                style={{ animationDelay: "2400ms" }}
                role="note"
              >
                <p className="mb-1 flex items-center gap-2 text-xs font-bold text-navy">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src="/dcai-logo.png" alt="" width={12} height={14} className="h-3.5 w-auto" />
                  dcAI
                </p>
                <p className="text-[0.92rem] leading-snug text-ink">{t("home.demo.nudge")}</p>
              </div>
            </div>
          </div>
        </Parallax>
      </figure>

      {/* What crosses from the phone to the parent: labels, never text. */}
      <div aria-hidden className="hidden items-center lg:flex">
        <svg width="72" height="24" viewBox="0 0 72 24">
          <path d="M2 12 H62" stroke="#566373" strokeWidth="1.5" strokeDasharray="4 5" />
          <path d="M60 6 L68 12 L60 18" fill="none" stroke="#566373" strokeWidth="1.5" />
        </svg>
      </div>

      <figure className="w-full">
        <figcaption className="mb-3 text-sm font-semibold text-slate">{t("home.demo.parent")}</figcaption>
        <div className="arrive glass-fill rounded-2xl bg-white/80 p-6" style={{ animationDelay: "2900ms" }}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-lg font-bold">Raka, 10-12</p>
            <LevelBadge level="mendesak" size="lg" />
          </div>
          <p className="mt-5 text-sm font-semibold text-slate">{t("home.demo.patterns")}</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {patterns.map((p) => (
              <li key={p} className="rounded-full bg-mist px-3 py-1 text-sm font-medium">
                {t(p)}
              </li>
            ))}
          </ul>
          <p className="mt-6 text-sm font-semibold text-slate">{t("home.demo.starter")}</p>
          <p className="mt-1.5 text-[1.05rem] font-medium leading-snug">&ldquo;{t("home.demo.starterText")}&rdquo;</p>
          <p className="mt-6 flex items-start gap-2 border-t border-line pt-4 text-sm text-slate">
            <LockIcon />
            {t("home.demo.noText")}
          </p>
        </div>
      </figure>
    </div>
  );
}

function LockIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden className="mt-0.5 shrink-0">
      <rect x="3" y="7" width="10" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

function Check() {
  return (
    <svg width="16" height="16" viewBox="0 0 18 18" aria-hidden className="mt-1 shrink-0">
      <path d="M3.5 9.5 L7.5 13 L14.5 5" fill="none" stroke="#1f3a5f" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// Line icons, one stroke weight, drawn for this page.
const ICONS = {
  shield: (
    <path d="M12 3 4.5 6v5.5c0 4.6 3.1 8.2 7.5 9.5 4.4-1.3 7.5-4.9 7.5-9.5V6L12 3Z M8.8 12.2l2.2 2.2 4.4-4.6" />
  ),
  heart: (
    <path d="M12 20s-7.5-4.4-7.5-10A4.2 4.2 0 0 1 12 7.6 4.2 4.2 0 0 1 19.5 10c0 5.6-7.5 10-7.5 10Z M8.5 12.5h2l1-2 1.5 4 1-2h1.5" />
  ),
  clock: (
    <path d="M12 21a8.5 8.5 0 1 0 0-17 8.5 8.5 0 0 0 0 17Z M12 8v4.5l3 1.8" />
  ),
} as const;

function Icon({ name }: { name: keyof typeof ICONS }) {
  return (
    <span aria-hidden className="grid h-11 w-11 place-items-center rounded-xl bg-navy/[0.07] text-navy ring-1 ring-navy/10">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
        {ICONS[name]}
      </svg>
    </span>
  );
}

function Features() {
  const { t } = useT();
  const cards = [
    { n: 1, icon: "shield" },
    { n: 2, icon: "heart" },
    { n: 3, icon: "clock" },
  ] as const;
  return (
    <section className="mx-auto mt-32 max-w-6xl px-5 sm:px-8" aria-labelledby="feat-h">
      <p className="eyebrow">{t("home.feat.eyebrow")}</p>
      <h2 id="feat-h" className="mt-3 max-w-[24ch] text-[2rem] font-bold leading-tight tracking-[-0.02em]">
        {t("home.feat.title")}
      </h2>
      <p className="mt-4 max-w-[60ch] text-slate">{t("home.feat.lead")}</p>
      <div className="mt-10 grid gap-5 md:grid-cols-3">
        {cards.map(({ n, icon }) => (
          <article key={n} className="glass row-span-4 grid grid-rows-subgrid gap-0 rounded-3xl p-7">
            <Icon name={icon} />
            <h3 className="mt-5 text-lg font-bold">{t(`home.feat.c${n}.t`)}</h3>
            <p className="mt-2 text-[0.97rem] leading-relaxed text-ink/80">{t(`home.feat.c${n}.b`)}</p>
            <ul className="mt-6 space-y-2.5 self-start border-t border-ink/[0.08] pt-5 text-[0.92rem] text-slate">
              {([1, 2, 3] as const).map((i) => (
                <li key={i} className="flex gap-2.5">
                  <Check />
                  {t(`home.feat.c${n}.i${i}`)}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

function Control() {
  const { t } = useT();
  return (
    <section id="privasi" className="mx-auto mt-32 max-w-6xl px-5 sm:px-8" aria-labelledby="control-h">
      <div className="grid gap-10 lg:grid-cols-[1fr_1.05fr] lg:items-start">
        <div className="lg:sticky lg:top-28">
          <p className="eyebrow">{t("home.control.eyebrow")}</p>
          <h2 id="control-h" className="mt-3 text-[2rem] font-bold leading-tight tracking-[-0.02em]">
            {t("home.control.title")}
          </h2>
          <p className="mt-4 max-w-[52ch] text-slate">{t("home.control.lead")}</p>
          <ul className="mt-6 space-y-2.5">
            {([1, 2, 3] as const).map((i) => (
              <li key={i} className="flex gap-2.5 font-medium">
                <Check />
                {t(`home.control.i${i}`)}
              </li>
            ))}
          </ul>
        </div>
        <div className="glass rounded-3xl p-7 sm:p-8">
          <h3 className="text-lg font-bold">{t("home.privacy.title")}</h3>
          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            <div>
              <p className="eyebrow">{t("home.privacy.stored")}</p>
              <ul className="mt-3 space-y-2 text-[0.95rem]">
                {(["s1", "s2", "s3", "s4", "s5"] as const).map((k) => (
                  <li key={k} className="glass-fill rounded-xl px-3.5 py-2">{t(`home.privacy.${k}`)}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="eyebrow">{t("home.privacy.never")}</p>
              <ul className="mt-3 space-y-2 text-[0.95rem]">
                {(["n1", "n2", "n3", "n4"] as const).map((k) => (
                  <li key={k} className="flex items-center gap-2 rounded-xl border border-dashed border-ink/15 px-3.5 py-2 font-medium">
                    <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden className="shrink-0 text-mendesak">
                      <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
                    </svg>
                    {t(`home.privacy.${k}`)}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="mt-6 flex gap-2 rounded-xl bg-navy/[0.06] px-4 py-3 text-[0.95rem]">
            <LockIcon />
            {t("home.privacy.note")}
          </p>
        </div>
      </div>
    </section>
  );
}

function Steps() {
  const { t } = useT();
  return (
    <section className="mx-auto mt-32 max-w-6xl px-5 sm:px-8">
      <h2 className="max-w-[30ch] text-[2rem] font-bold leading-tight tracking-[-0.02em]">{t("home.steps.title")}</h2>
      <ol className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {([1, 2, 3, 4] as const).map((n) => (
          <li key={n} className="glass rounded-3xl p-6">
            <p className="grid h-8 w-8 place-items-center rounded-full bg-navy text-sm font-bold text-paper tabular">{n}</p>
            <h3 className="mt-4 text-lg font-bold">{t(`home.step${n}.t`)}</h3>
            <p className="mt-2 text-[0.95rem] text-slate">{t(`home.step${n}.b`)}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

function Models() {
  const { t } = useT();
  const rows = [
    ["Muse Spark", "home.meta.muse"],
    ["Llama", "home.meta.llama"],
    ["ExecuTorch", "home.meta.next"],
  ] as const;
  return (
    <section className="mx-auto mt-32 max-w-6xl px-5 sm:px-8">
      <h2 className="text-[2rem] font-bold leading-tight tracking-[-0.02em]">{t("home.meta.title")}</h2>
      <dl className="mt-8 grid gap-5 sm:grid-cols-3">
        {rows.map(([name, key]) => (
          <div key={name} className="border-t border-ink/15 pt-4">
            <dt className="font-bold">{name}</dt>
            <dd className="mt-2 text-slate">{t(key)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

/** A platform's logo, the same size for every card. */
function Mark({ src }: { src: string }) {
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt="" width={44} height={52} className="h-[52px] w-auto self-start" />;
}

function About() {
  const { t } = useT();
  const products = [
    { key: "citra", name: "C.I.T.R.A.", full: "Core Integrity & Trustworthy Research Assistant", mark: <Mark src="/eco/citra.png" /> },
    { key: "bz", name: "Belajar Z", full: null, mark: <Mark src="/eco/belajarz.png" /> },
    { key: "numeria", name: "Numeria Arena", full: null, mark: <Mark src="/eco/numeria.png" /> },
  ] as const;
  return (
    <section id="tentang" className="mx-auto mt-32 max-w-6xl scroll-mt-24 px-5 sm:px-8" aria-labelledby="about-h">
      <div className="grid gap-8 lg:grid-cols-2 lg:gap-16">
        <div>
          <p className="eyebrow">{t("home.about.eyebrow")}</p>
          <h2 id="about-h" className="mt-3 text-[2rem] font-bold leading-tight tracking-[-0.02em]">{t("home.about.title")}</h2>
          <p className="mt-4 max-w-[50ch] text-[1.05rem] text-ink/80">{t("home.about.lead")}</p>
        </div>
        <div className="lg:pt-9">
          <h3 className="text-lg font-bold">{t("home.eco.title")}</h3>
          <p className="mt-2 max-w-[48ch] text-slate">{t("home.eco.lead")}</p>
        </div>
      </div>
      <div className="mt-10 grid gap-5 md:grid-cols-2">
        <article className="glass flex flex-col rounded-3xl p-7 ring-1 ring-navy/20">
          <div className="flex items-center justify-between gap-3">
            <Mark src="/eco/dcai.png" />
            <span className="rounded-full bg-navy px-2.5 py-0.5 text-xs font-semibold text-paper">{t("home.eco.here")}</span>
          </div>
          <p className="mt-4 text-lg font-bold">dcAI</p>
          <p className="text-sm font-medium text-slate">Digital Citizenship AI, Family Safety Guardian</p>
          <p className="mt-3 flex-1 text-[0.97rem] text-ink/80">{t("home.eco.dcai.b")}</p>
          <p className="mt-5 text-xs font-semibold tracking-wide text-slate uppercase">{t("home.eco.dcai.tag")}</p>
        </article>
        {products.map((p) => (
          <article key={p.key} className="glass flex flex-col rounded-3xl p-7">
            {p.mark}
            <p className="mt-4 text-lg font-bold">{p.name}</p>
            {p.full && <p className="text-sm font-medium text-slate">{p.full}</p>}
            <p className="mt-3 flex-1 text-[0.97rem] text-ink/80">{t(`home.eco.${p.key}.b`)}</p>
            <p className="mt-5 text-xs font-semibold tracking-wide text-slate uppercase">{t(`home.eco.${p.key}.tag`)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

/** A phone frame around a real screenshot of the app. */
function Phone({ src, alt, className = "" }: { src: string; alt: string; className?: string }) {
  return (
    <div className={`rounded-[2.2rem] bg-ink p-[7px] shadow-[0_40px_80px_-36px_rgba(20,35,58,0.65)] ring-1 ring-white/10 ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={alt} width={540} height={1200} className="block h-auto w-full rounded-[1.75rem]" />
    </div>
  );
}

/** The child's app, home and protections, as it runs on the phone (screenshots from the
 * Android emulator). The back phone drifts slower than the front one. */
function AppShots() {
  const { t, lang } = useT();
  return (
    <figure className="relative mx-auto aspect-[100/140] w-full max-w-[26rem]">
      <Parallax speed={0.05} className="absolute top-10 right-0 w-[56%]">
        <Phone src={`/app/${lang}-tiles.webp`} alt={t("home.shots.tiles")} className="opacity-95" />
      </Parallax>
      <Parallax speed={-0.04} className="absolute top-0 left-0 w-[60%]">
        <Phone src={`/app/${lang}-home.webp`} alt={t("home.shots.home")} />
      </Parallax>
      <figcaption className="sr-only">{t("home.shots.caption")}</figcaption>
    </figure>
  );
}

export function HomePage() {
  const { t } = useT();
  return (
    <>
      <SiteHeader />
      <main>
        <section className="mx-auto max-w-6xl px-5 pt-14 sm:px-8 sm:pt-20">
          <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
            <Parallax speed={0.08}>
              <blockquote className="max-w-[58ch] border-l-2 border-navy/40 pl-4 text-[1.02rem] leading-relaxed text-slate italic">
                &ldquo;{t("home.tagline")}&rdquo;
              </blockquote>
              <h1 className="mt-8 max-w-[18ch] text-[2.5rem] font-extrabold leading-[1.06] tracking-[-0.03em] text-ink sm:text-[3.6rem] lg:text-[3.25rem]">
                {t("home.title")}
              </h1>
              <p className="mt-6 max-w-[60ch] text-lg text-ink/75">{t("home.lead")}</p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Link href="/dasbor" className="rounded-xl bg-navy px-5 py-3 font-semibold text-paper shadow-[0_10px_24px_-14px_rgba(31,58,95,0.9)] hover:bg-ink">
                  {t("home.cta")}
                </Link>
                <Link href="/#privasi" className="glass-fill rounded-xl px-5 py-3 font-semibold hover:border-navy/40">
                  {t("home.cta2")}
                </Link>
              </div>
            </Parallax>
            <AppShots />
          </div>
          <div className="glass relative z-10 mt-16 rounded-[2rem] p-5 sm:p-8">
            <p className="eyebrow mb-5">{t("home.demo.eyebrow")}</p>
            <SplitDemo />
          </div>
        </section>

        <Features />
        <Steps />
        <Control />
        <Models />
        <About />
      </main>
      <SiteFooter />
    </>
  );
}
