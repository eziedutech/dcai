"use client";

import Link from "next/link";
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

export function SiteHeader() {
  const { t } = useT();
  const nav = "hidden rounded-lg px-2.5 py-1.5 font-medium text-slate hover:bg-white/60 hover:text-ink md:inline";
  return (
    <header className="glass-bar sticky top-0 z-40">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-5 py-3.5 sm:px-8">
        <Logo />
        <nav className="flex items-center gap-1 text-sm sm:gap-2">
          <Link href="/cara-kerja" className={nav}>
            {t("nav.how")}
          </Link>
          <Link href="/privasi" className={nav}>
            {t("nav.privacy")}
          </Link>
          <Link href="/fakta" className={nav}>
            {t("nav.facts")}
          </Link>
          <Link href="/#tentang" className={nav}>
            {t("nav.about")}
          </Link>
          <LangToggle />
          <Link href="/dasbor" className="rounded-xl bg-navy px-3.5 py-2 font-semibold text-paper hover:bg-ink">
            {t("nav.dashboard")}
          </Link>
        </nav>
      </div>
    </header>
  );
}

export function SiteFooter() {
  const { t } = useT();
  return (
    <footer className="glass-bar mt-32 border-t border-ink/[0.07]">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-5 py-8 text-sm text-slate sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <p className="max-w-[60ch]">{t("home.foot")}</p>
        <div className="flex gap-4">
          <Link href="/cara-kerja" className="hover:text-ink">{t("nav.how")}</Link>
          <Link href="/privasi" className="hover:text-ink">{t("nav.privacy")}</Link>
          <Link href="/fakta" className="hover:text-ink">{t("nav.facts")}</Link>
          <Link href="/#tentang" className="hover:text-ink">{t("nav.about")}</Link>
        </div>
      </div>
    </footer>
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
