"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n";
import { CardDemo } from "./card-demo";
import { FactsBand, LiveDemo } from "./demo";
import { ModelsScene, SchoolScene } from "./illustrations";
import { Parallax } from "./motion";
import { APK_URL, APK_VERSION } from "@/lib/download";
import { SiteFooter, SiteHeader } from "./ui";

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
  people: (
    <path d="M9 11a3.2 3.2 0 1 0 0-6.4A3.2 3.2 0 0 0 9 11Z M3.5 19.5c.6-3 2.8-4.8 5.5-4.8s4.9 1.8 5.5 4.8 M16 11.2a2.8 2.8 0 1 0-.6-5.5 M17.2 14.9c1.9.5 3.1 2 3.5 4.3" />
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

/** The opening of each homepage section: the menu's word, the claim, one line under it. */
function SectionHead({ id, eyebrow, title, lead }: { id: string; eyebrow: string; title: string; lead: string }) {
  return (
    <div>
      <p className="eyebrow">{eyebrow}</p>
      <h2 id={id} className="mt-3 max-w-[26ch] text-[2.3rem] font-extrabold leading-[1.1] tracking-[-0.03em]">
        {title}
      </h2>
      <p className="mt-4 max-w-[60ch] text-lg text-ink/75">{lead}</p>
    </div>
  );
}

const sub = "text-[1.6rem] font-bold leading-tight tracking-[-0.02em]";

function Features() {
  const { t } = useT();
  const cards = [
    { n: 1, icon: "shield" },
    { n: 2, icon: "people" },
    { n: 3, icon: "clock" },
  ] as const;
  return (
    <div className="mt-20" aria-labelledby="feat-h">
      <p className="eyebrow">{t("home.feat.eyebrow")}</p>
      <h3 id="feat-h" className={`mt-3 max-w-[30ch] ${sub}`}>
        {t("home.feat.title")}
      </h3>
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
    </div>
  );
}

function Control() {
  const { t } = useT();
  return (
    <div id="privasi" className="mt-24 scroll-mt-24" aria-labelledby="control-h">
      <div className="grid gap-10 lg:grid-cols-[1fr_1.05fr] lg:items-start">
        <div className="lg:sticky lg:top-28">
          <p className="eyebrow">{t("home.control.eyebrow")}</p>
          <h3 id="control-h" className={`mt-3 ${sub}`}>
            {t("home.control.title")}
          </h3>
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
                {(["n1", "n2", "n4"] as const).map((k) => (
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
    </div>
  );
}

function Steps() {
  const { t } = useT();
  return (
    <div className="mt-24">
      <h3 className={`max-w-[30ch] ${sub}`}>{t("home.steps.title")}</h3>
      <ol className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {([1, 2, 3, 4] as const).map((n) => (
          <li key={n} className="glass rounded-3xl p-6">
            <p className="grid h-8 w-8 place-items-center rounded-full bg-navy text-sm font-bold text-paper tabular">{n}</p>
            <h3 className="mt-4 text-lg font-bold">{t(`home.step${n}.t`)}</h3>
            <p className="mt-2 text-[0.95rem] text-slate">{t(`home.step${n}.b`)}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}

function Schools() {
  const { t } = useT();
  return (
    <div className="mt-24" aria-labelledby="school-h">
      <div className="grid gap-10 lg:grid-cols-[1fr_1.05fr] lg:items-center">
        <div>
          <p className="eyebrow">{t("home.school.eyebrow")}</p>
          <h3 id="school-h" className={`mt-3 max-w-[30ch] ${sub}`}>
            {t("home.school.title")}
          </h3>
          <p className="mt-4 max-w-[56ch] text-slate">{t("home.school.lead")}</p>
          <ul className="mt-6 space-y-2.5">
            {([1, 2, 3] as const).map((i) => (
              <li key={i} className="flex gap-2.5 font-medium">
                <Check />
                {t(`home.school.i${i}`)}
              </li>
            ))}
          </ul>
          <Link href="/sekolah" className="mt-7 inline-flex rounded-xl bg-navy px-5 py-3 font-semibold text-paper hover:bg-ink">
            {t("home.school.cta")}
          </Link>
        </div>
        <SchoolScene className="mx-auto max-w-md lg:max-w-none" />
      </div>
    </div>
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
    <div className="mt-24">
      <div className="grid gap-10 lg:grid-cols-[1.1fr_1fr] lg:items-center">
        <div>
          <h3 className={sub}>{t("home.meta.title")}</h3>
          <p className="mt-4 max-w-[58ch] text-slate">{t("home.meta.lead")}</p>
        </div>
        <ModelsScene className="mx-auto max-w-md lg:max-w-none" />
      </div>
      <dl className="mt-10 grid gap-5 sm:grid-cols-3">
        {rows.map(([name, key]) => (
          <div key={name} className="border-t border-ink/15 pt-4">
            <dt className="font-bold">{name}</dt>
            <dd className="mt-2 text-slate">{t(key)}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-8 flex items-start gap-2.5 rounded-2xl bg-navy/[0.06] px-4 py-3 text-[0.95rem] text-ink/85">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/dcai-logo.png" alt="" width={14} height={16} className="mt-0.5 h-4 w-auto" />
        {t("home.meta.hackathon")}
      </p>
    </div>
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
    <section id="solusi" className="mx-auto mt-32 max-w-6xl scroll-mt-24 px-5 sm:px-8" aria-labelledby="about-h">
      <div className="grid gap-8 lg:grid-cols-2 lg:gap-16">
        <div>
          <p className="eyebrow">{t("home.others.eyebrow")}</p>
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

/** The hero's main action: the Android app. Until the release build is final there is no
 * file, and the button says so instead of linking to nothing. */
function DownloadButton() {
  const { t } = useT();
  const cls =
    "inline-flex items-center gap-2.5 rounded-xl bg-navy px-5 py-3 font-semibold text-paper shadow-[0_10px_24px_-14px_rgba(31,58,95,0.9)]";
  const icon = (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d="M12 3 5 6v5.5c0 4.5 3 8.1 7 9.5 4-1.4 7-5 7-9.5V6l-7-3Z M12 8.5v6M9.3 12l2.7 2.7 2.7-2.7" />
    </svg>
  );
  if (APK_URL) {
    return (
      <a href={APK_URL} download className={`${cls} hover:bg-ink`}>
        {icon}
        {t("home.download")}
      </a>
    );
  }
  return (
    <button type="button" disabled aria-describedby="download-soon" className={`${cls} cursor-not-allowed`}>
      {icon}
      {t("home.download")}
    </button>
  );
}

export function HomePage() {
  const { t } = useT();
  return (
    <>
      <SiteHeader home />
      <main>
        <section id="tentang" className="mx-auto max-w-6xl scroll-mt-24 px-5 pt-14 sm:px-8 sm:pt-20" aria-labelledby="hero-h">
          <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
            <Parallax speed={0.08}>
              <blockquote className="max-w-[58ch] border-l-2 border-navy/40 pl-4 text-[1.02rem] leading-relaxed text-slate italic">
                &ldquo;{t("home.tagline")}&rdquo;
              </blockquote>
              <h1 id="hero-h" className="mt-8 max-w-[18ch] text-[2.5rem] font-extrabold leading-[1.06] tracking-[-0.03em] text-ink sm:text-[3.6rem] lg:text-[3.25rem]">
                {t("home.title")}
              </h1>
              <p className="mt-6 max-w-[60ch] text-lg text-ink/75">{t("home.lead")}</p>
              <div className="mt-9 flex flex-wrap gap-3">
                <DownloadButton />
                <Link href="/#cara-kerja" className="glass-fill rounded-xl px-5 py-3 font-semibold hover:border-navy/40">
                  {t("home.seeHow")}
                </Link>
              </div>
              <p id="download-soon" className="mt-3 text-sm text-slate">
                {APK_URL ? t("home.downloadStore").replace("{v}", APK_VERSION) : t("home.downloadSoon")}
              </p>
            </Parallax>
            <AppShots />
          </div>
        </section>

        <section id="mengapa" className="mx-auto mt-28 max-w-6xl scroll-mt-24 px-5 sm:px-8" aria-labelledby="why-h">
          <SectionHead id="why-h" eyebrow={t("home.why.eyebrow")} title={t("home.why.title")} lead={t("home.why.lead")} />
          <FactsBand />
          <Features />
        </section>

        <section id="cara-kerja" className="mx-auto mt-32 max-w-6xl scroll-mt-24 px-5 sm:px-8" aria-labelledby="how-h">
          <SectionHead id="how-h" eyebrow={t("home.how.eyebrow")} title={t("home.how.title")} lead={t("home.how.lead")} />
          <div className="glass relative z-10 mt-10 rounded-[2rem] p-5 sm:p-8" aria-labelledby="demo-h">
            <p className="eyebrow">{t("home.demo.eyebrow")}</p>
            <h3 id="demo-h" className={`mt-3 max-w-[26ch] ${sub}`}>
              {t("home.demo.title")}
            </h3>
            <p className="mt-3 mb-7 max-w-[64ch] text-ink/75">{t("home.demo.lead")}</p>
            <LiveDemo />
          </div>
          <CardDemo />
          <Steps />
          <Control />
          <Schools />
          <Models />
        </section>

        <About />
      </main>
      <SiteFooter />
    </>
  );
}
