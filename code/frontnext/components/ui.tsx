"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useT } from "@/lib/i18n";
import type { Level } from "@/lib/types";

export const LEVEL_STYLE: Record<Level, { text: string; bg: string; bar: string }> = {
  aman: { text: "text-aman", bg: "bg-aman-soft", bar: "bg-aman" },
  perhatian: { text: "text-perhatian", bg: "bg-perhatian-soft", bar: "bg-perhatian" },
  waspada: { text: "text-waspada", bg: "bg-waspada-soft", bar: "bg-waspada" },
  mendesak: { text: "text-mendesak", bg: "bg-mendesak-soft", bar: "bg-mendesak" },
};

const LEVELS: Level[] = ["aman", "perhatian", "waspada", "mendesak"];

/** The level as a word with its position on the four-step scale. Colour never carries
 * the meaning alone. */
export function LevelBadge({ level, size = "sm" }: { level: Level; size?: "sm" | "lg" }) {
  const { t } = useT();
  const s = LEVEL_STYLE[level];
  const rank = LEVELS.indexOf(level);
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full ${s.bg} ${s.text} font-semibold ${
        size === "lg" ? "px-3.5 py-1.5 text-base" : "px-2.5 py-0.5 text-sm"
      }`}
    >
      <span aria-hidden className="flex gap-0.5">
        {LEVELS.map((l, i) => (
          <span
            key={l}
            className={`inline-block rounded-sm ${size === "lg" ? "h-3.5 w-1.5" : "h-2.5 w-1"} ${
              i <= rank ? s.bar : "bg-current opacity-20"
            }`}
          />
        ))}
      </span>
      {t(`level.${level}`)}
    </span>
  );
}

export function Logo({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="inline-flex items-center gap-2.5 text-ink">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/dcai-logo.png" alt="dcAI" width={30} height={35} className="h-9 w-auto" />
      <span className="flex flex-col whitespace-nowrap leading-tight">
        <span className="text-[0.9rem] font-extrabold tracking-tight sm:text-[1.02rem]">Digital Citizenship AI</span>
        <span className="text-[0.72rem] font-semibold text-slate sm:text-[0.78rem]">Family Safety Guardian</span>
      </span>
    </Link>
  );
}

/** A globe and the code of the other language; the full name is the accessible label. */
export function LangToggle() {
  const { lang, setLang, t } = useT();
  return (
    <button
      type="button"
      onClick={() => setLang(lang === "id" ? "en" : "id")}
      className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-semibold text-slate hover:bg-white/60 hover:text-ink"
      aria-label={t("nav.lang")}
      title={t("nav.lang")}
    >
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden>
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3Z" />
      </svg>
      <span aria-hidden>{lang === "id" ? "EN" : "ID"}</span>
    </button>
  );
}

/** The homepage is one page of sections; other pages are documents with their own menu. */
const HOME_NAV = [
  ["tentang", "nav.homeAbout"],
  ["mengapa", "nav.why"],
  ["cara-kerja", "nav.howHome"],
  ["solusi", "nav.others"],
] as const;
const PAGE_NAV = [
  ["/", "nav.home"],
  ["/cara-kerja", "nav.howPage"],
  ["/fakta", "nav.facts"],
  ["/privasi", "nav.privacy"],
] as const;

/** Which homepage section is on screen, for the menu. */
function useActiveSection(on: boolean) {
  const [active, setActive] = useState<string | null>(null);
  useEffect(() => {
    if (!on) return;
    const els = HOME_NAV.map(([id]) => document.getElementById(id)).filter((e): e is HTMLElement => e !== null);
    const io = new IntersectionObserver(
      (entries) => {
        const seen = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (seen[0]) setActive(seen[0].target.id);
      },
      { rootMargin: "-45% 0px -50% 0px" },
    );
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, [on]);
  return active;
}

/** A tapped item in the phone menu closes the menu, also when it only scrolls the page. */
function closeMenu(e: React.MouseEvent<HTMLElement>) {
  e.currentTarget.closest("details")?.removeAttribute("open");
}

export function SiteHeader({ home = false }: { home?: boolean }) {
  const { t } = useT();
  const pathname = usePathname();
  const active = useActiveSection(home);
  const items = home
    ? HOME_NAV.map(([id, key]) => ({ href: `/#${id}`, label: t(key), on: active === id }))
    : PAGE_NAV.map(([href, key]) => ({ href, label: t(key), on: pathname === href }));
  const link = (on: boolean) =>
    `rounded-lg px-2.5 py-1.5 font-medium transition-colors hover:bg-white/60 hover:text-ink ${on ? "text-ink" : "text-slate"}`;
  return (
    <header className="glass-bar sticky top-0 z-40">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
        <Logo />
        <nav className="flex items-center gap-1 text-sm sm:gap-2" aria-label={t("nav.menu")}>
          <span className="hidden items-center gap-1 lg:flex">
            {items.map((i) => (
              <Link key={i.href} href={i.href} className={link(i.on)} aria-current={i.on ? (home ? "true" : "page") : undefined}>
                {i.label}
                <span aria-hidden className={`mx-auto mt-0.5 block h-0.5 rounded-full bg-navy transition-all ${i.on ? "w-4" : "w-0"}`} />
              </Link>
            ))}
          </span>
          <LangToggle />
          <Link href="/dasbor" className="hidden rounded-xl bg-navy px-3.5 py-2 font-semibold whitespace-nowrap text-paper hover:bg-ink sm:inline-flex">
            {t("nav.parent")}
          </Link>
          <details className="group relative lg:hidden">
            <summary className="grid h-9 w-9 cursor-pointer list-none place-items-center rounded-lg text-slate hover:bg-white/60 hover:text-ink [&::-webkit-details-marker]:hidden">
              <span className="sr-only">{t("nav.menu")}</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden>
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </summary>
            <div className="absolute right-0 mt-2 flex w-60 flex-col rounded-2xl border border-ink/[0.08] bg-white p-2 shadow-[0_18px_40px_-18px_rgba(20,35,58,0.45)]">
              {items.map((i) => (
                <Link key={i.href} href={i.href} className={`${link(i.on)} py-2`} onClick={closeMenu}>
                  {i.label}
                </Link>
              ))}
              <Link href="/dasbor" className="mt-1 rounded-xl bg-navy px-3.5 py-2 text-center font-semibold text-paper hover:bg-ink sm:hidden">
                {t("nav.parent")}
              </Link>
            </div>
          </details>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  const { t } = useT();
  const cols = [
    {
      h: t("foot.product"),
      links: [
        ["/#cara-kerja", t("nav.howHome")],
        ["/cara-kerja", t("nav.howPage")],
        ["/fakta", t("nav.facts")],
        ["/#tentang", t("foot.download")],
      ],
    },
    {
      h: t("foot.people"),
      links: [
        ["/masuk", t("foot.signin")],
        ["/daftar", t("foot.signup")],
        ["/dasbor", t("foot.dashboard")],
      ],
    },
    {
      h: t("foot.policy"),
      links: [
        ["/privasi", t("nav.privacy")],
        ["/#solusi", t("foot.ecosystem")],
      ],
    },
  ];
  return (
    <footer className="glass-bar mt-32 border-t border-ink/[0.07]">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-12 sm:px-8 md:grid-cols-[1.4fr_repeat(3,1fr)]">
        <div>
          <Logo />
          <p className="mt-4 max-w-[38ch] text-sm leading-relaxed text-slate">{t("foot.about")}</p>
        </div>
        {cols.map((c) => (
          <nav key={c.h} aria-label={c.h}>
            <p className="eyebrow">{c.h}</p>
            <ul className="mt-3 space-y-2 text-sm">
              {c.links.map(([href, label]) => (
                <li key={href + label}>
                  <Link href={href} className="text-slate hover:text-ink">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        ))}
      </div>
      <div className="border-t border-ink/[0.07]">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-5 text-xs text-slate sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <p>{t("foot.rights")}</p>
          <p>{t("foot.synthetic")}</p>
        </div>
      </div>
    </footer>
  );
}

/** The top of every document page: the same eyebrow, title and lead as the homepage. */
export function PageIntro({ eyebrow, title, lead }: { eyebrow: string; title: string; lead: string }) {
  return (
    <div>
      <p className="eyebrow">{eyebrow}</p>
      <h1 className="mt-3 max-w-[22ch] text-[2.4rem] font-extrabold leading-tight tracking-[-0.03em]">{title}</h1>
      <p className="mt-4 max-w-[64ch] text-lg text-ink/75">{lead}</p>
    </div>
  );
}

/** The other document pages, at the end of each one. */
export function ReadNext({ current }: { current: "/cara-kerja" | "/fakta" | "/privasi" }) {
  const { t } = useT();
  const pages = [
    ["/cara-kerja", t("nav.howPage"), t("page.moreHow")],
    ["/fakta", t("nav.facts"), t("page.moreFacts")],
    ["/privasi", t("nav.privacy"), t("page.morePrivacy")],
  ].filter(([href]) => href !== current);
  return (
    <nav aria-label={t("page.more")} className="mt-16">
      <p className="eyebrow">{t("page.more")}</p>
      <ul className="mt-4 grid gap-4 sm:grid-cols-2">
        {pages.map(([href, title, line]) => (
          <li key={href}>
            <Link href={href} className="glass group flex h-full items-start justify-between gap-4 rounded-3xl p-6 hover:ring-1 hover:ring-navy/25">
              <span>
                <span className="block text-lg font-bold">{title}</span>
                <span className="mt-1 block text-[0.95rem] text-slate">{line}</span>
              </span>
              <svg width="18" height="18" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden className="mt-1.5 shrink-0 text-navy transition-transform group-hover:translate-x-0.5">
                <path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function Button({
  children,
  variant = "primary",
  className = "",
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "quiet" | "danger" }) {
  const styles = {
    primary: "bg-navy text-paper hover:bg-ink disabled:bg-slate",
    quiet: "border border-ink/10 bg-white/60 text-ink hover:border-navy/50 hover:bg-white/80",
    danger: "bg-mendesak text-paper hover:brightness-90 disabled:opacity-50",
  }[variant];
  return (
    <button
      {...rest}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-[0.95rem] font-semibold transition-colors disabled:cursor-not-allowed ${styles} ${className}`}
    >
      {children}
    </button>
  );
}

export function Field({
  label,
  hint,
  error,
  ...rest
}: React.InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string; error?: string }) {
  const hintId = rest.id ? `${rest.id}-hint` : undefined;
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold text-ink">{label}</span>
      <input
        {...rest}
        aria-describedby={hint || error ? hintId : undefined}
        aria-invalid={error ? true : undefined}
        className="w-full rounded-xl border border-ink/10 bg-white/75 px-3.5 py-2.5 text-ink outline-none placeholder:text-slate/70 focus:border-navy focus:ring-2 focus:ring-navy/20"
      />
      {(hint || error) && (
        <span id={hintId} className={`mt-1.5 block text-sm ${error ? "text-mendesak" : "text-slate"}`}>
          {error ?? hint}
        </span>
      )}
    </label>
  );
}

/** Placeholder panels while data loads, shaped like the page that follows, so nothing
 * jumps when it arrives. */
export function Skeleton({ label }: { label: string }) {
  return (
    <div role="status" aria-label={label} className="mx-auto max-w-5xl">
      <div className="shimmer h-9 w-40 rounded-xl" />
      <div className="glass mt-8 h-40 rounded-3xl p-7">
        <div className="shimmer h-4 w-48 rounded-lg" />
        <div className="shimmer mt-4 h-7 w-32 rounded-full" />
        <div className="shimmer mt-5 h-4 w-72 max-w-full rounded-lg" />
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <div className="glass h-72 rounded-3xl p-7">
          <div className="shimmer h-5 w-40 rounded-lg" />
          <div className="shimmer mt-5 h-4 w-full rounded-lg" />
          <div className="shimmer mt-3 h-4 w-5/6 rounded-lg" />
          <div className="shimmer mt-3 h-4 w-2/3 rounded-lg" />
        </div>
        <div className="glass h-72 rounded-3xl p-6">
          <div className="shimmer h-5 w-36 rounded-lg" />
          <div className="shimmer mt-5 h-4 w-full rounded-lg" />
          <div className="shimmer mt-3 h-4 w-3/4 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function formatWhen(iso: string, lang: string) {
  return new Intl.DateTimeFormat(lang === "id" ? "id-ID" : "en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

const KNOWN_APPS: Record<string, string> = {
  "dev.eziedutech.dcai.samplechat": "Messenger Z",
  "com.whatsapp": "WhatsApp",
  "com.instagram.android": "Instagram",
  "com.zhiliaoapp.musically": "TikTok",
  "com.roblox.client": "Roblox",
  "com.discord": "Discord",
  "org.telegram.messenger": "Telegram",
  "com.mobile.legends": "Mobile Legends",
  "com.dts.freefireth": "Free Fire",
  "com.facebook.orca": "Messenger",
  "com.snapchat.android": "Snapchat",
  "com.google.android.youtube": "YouTube",
};
const GENERIC = new Set(["android", "client", "app", "mobile", "lite", "messenger", "com", "org"]);

/** A readable app name from a package name: known apps by name, others by their most
 * telling segment ("com.example.gamechat" reads "gamechat"). */
export function appLabel(pkg: string | null) {
  if (!pkg) return null;
  if (KNOWN_APPS[pkg]) return KNOWN_APPS[pkg];
  const parts = pkg.split(".").filter((p) => !GENERIC.has(p));
  return parts[parts.length - 1] ?? pkg;
}
