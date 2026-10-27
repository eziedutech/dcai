"use client";

import Link from "next/link";
import { useT } from "@/lib/i18n";
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
        <div className="rounded-[var(--radius-phone)] border-[7px] border-ink bg-ink p-1 shadow-[0_24px_48px_-24px_rgba(20,35,58,0.55)]">
          <div className="flex min-h-[27rem] flex-col rounded-[22px] bg-[#f4f6f9]">
            <div className="flex items-center gap-3 border-b border-line bg-white px-4 py-3 rounded-t-[22px]">
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
                <svg width="14" height="14" viewBox="0 0 28 28" aria-hidden>
                  <rect x="1" y="5" width="18" height="22" rx="5" fill="#1f3a5f" />
                  <rect x="11" y="1" width="16" height="16" rx="8" fill="#fff" stroke="#1f3a5f" strokeWidth="3" />
                </svg>
                dcAI
              </p>
              <p className="text-[0.92rem] leading-snug text-ink">{t("home.demo.nudge")}</p>
            </div>
          </div>
        </div>
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
        <div className="arrive rounded-[var(--radius-panel)] border border-line bg-white p-6" style={{ animationDelay: "2900ms" }}>
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
            <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden className="mt-0.5 shrink-0">
              <rect x="3" y="7" width="10" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
            {t("home.demo.noText")}
          </p>
        </div>
      </figure>
    </div>
  );
}

function LayerTable() {
  const { t, lang } = useT();
  const rows: [string, boolean, boolean][] = [
    [t("home.layer.r1"), true, false],
    [t("home.layer.r2"), true, false],
    [t("home.layer.r3"), false, true],
    [t("home.layer.r4"), false, true],
    [t("home.layer.r5"), false, true],
    [t("home.layer.r6"), false, true],
  ];
  const mark = (on: boolean) =>
    on ? (
      <svg width="18" height="18" viewBox="0 0 18 18" role="img" aria-label={lang === "id" ? "ya" : "yes"}>
        <path d="M3.5 9.5 L7.5 13 L14.5 5" fill="none" stroke="#1f3a5f" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ) : (
      <svg width="14" height="18" viewBox="0 0 14 18" role="img" aria-label={lang === "id" ? "tidak" : "no"}>
        <path d="M3 9 H11" stroke="#d8dfe6" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  return (
    <table className="w-full text-left text-[0.95rem]">
      <thead>
        <tr className="border-b border-ink/80">
          <th className="py-2.5 pr-4 font-semibold" scope="col">
            <span className="sr-only">{lang === "id" ? "Fitur" : "Feature"}</span>
          </th>
          <th className="w-32 py-2.5 text-center font-semibold" scope="col">{t("home.layer.fl")}</th>
          <th className="w-32 py-2.5 text-center font-semibold" scope="col">{t("home.layer.dc")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(([label, fl, dc]) => (
          <tr key={label} className="border-b border-line">
            <th scope="row" className="py-3 pr-4 font-normal">{label}</th>
            <td className="py-3 text-center">{mark(fl)}</td>
            <td className="py-3 text-center">{mark(dc)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function HomePage() {
  const { t } = useT();
  const steps = [1, 2, 3, 4] as const;
  return (
    <>
      <SiteHeader />
      <main>
        <section className="mx-auto max-w-6xl px-5 pt-10 sm:px-8 sm:pt-16">
          <h1 className="max-w-[22ch] text-[2.4rem] font-extrabold leading-[1.08] tracking-[-0.025em] text-ink sm:text-[3.4rem]">
            {t("home.title")}
          </h1>
          <p className="mt-6 max-w-[62ch] text-lg text-slate">{t("home.lead")}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/dasbor" className="rounded-lg bg-navy px-5 py-3 font-semibold text-paper hover:bg-ink">
              {t("home.cta")}
            </Link>
            <Link href="/privasi" className="rounded-lg border border-line px-5 py-3 font-semibold hover:border-navy">
              {t("home.cta2")}
            </Link>
          </div>
          <div className="mt-16">
            <SplitDemo />
          </div>
        </section>

        <section className="mx-auto mt-28 grid max-w-6xl gap-10 px-5 sm:px-8 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <h2 className="text-[1.9rem] font-bold leading-tight tracking-[-0.02em]">{t("home.layer.title")}</h2>
            <p className="mt-4 max-w-[52ch] text-slate">{t("home.layer.lead")}</p>
          </div>
          <LayerTable />
        </section>

        <section className="mx-auto mt-28 max-w-6xl px-5 sm:px-8">
          <h2 className="max-w-[30ch] text-[1.9rem] font-bold leading-tight tracking-[-0.02em]">{t("home.steps.title")}</h2>
          <ol className="mt-10 grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((n) => (
              <li key={n} className="border-t-2 border-navy pt-4">
                <p className="text-sm font-bold text-navy tabular">{n}</p>
                <h3 className="mt-1 text-lg font-bold">{t(`home.step${n}.t`)}</h3>
                <p className="mt-2 text-[0.95rem] text-slate">{t(`home.step${n}.b`)}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="privasi" className="mx-auto mt-28 max-w-6xl px-5 sm:px-8">
          <h2 className="text-[1.9rem] font-bold leading-tight tracking-[-0.02em]">{t("home.privacy.title")}</h2>
          <div className="mt-8 grid gap-8 sm:grid-cols-2">
            <div>
              <h3 className="font-bold">{t("home.privacy.stored")}</h3>
              <ul className="mt-3 space-y-2 text-slate">
                {(["s1", "s2", "s3", "s4", "s5"] as const).map((k) => (
                  <li key={k} className="border-b border-line pb-2">{t(`home.privacy.${k}`)}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-bold">{t("home.privacy.never")}</h3>
              <ul className="mt-3 space-y-2">
                {(["n1", "n2", "n3", "n4"] as const).map((k) => (
                  <li key={k} className="border-b border-line pb-2 font-medium line-through decoration-mendesak/60 decoration-2">
                    {t(`home.privacy.${k}`)}
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <p className="mt-8 max-w-[62ch] rounded-[var(--radius-panel)] bg-mist px-5 py-4">{t("home.privacy.note")}</p>
        </section>

        <section className="mx-auto mt-28 max-w-6xl px-5 sm:px-8">
          <h2 className="text-[1.9rem] font-bold leading-tight tracking-[-0.02em]">{t("home.meta.title")}</h2>
          <dl className="mt-8 grid gap-8 sm:grid-cols-3">
            <div>
              <dt className="font-bold">Muse Spark</dt>
              <dd className="mt-2 text-slate">{t("home.meta.muse")}</dd>
            </div>
            <div>
              <dt className="font-bold">Llama</dt>
              <dd className="mt-2 text-slate">{t("home.meta.llama")}</dd>
            </div>
            <div>
              <dt className="font-bold">ExecuTorch</dt>
              <dd className="mt-2 text-slate">{t("home.meta.next")}</dd>
            </div>
          </dl>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
