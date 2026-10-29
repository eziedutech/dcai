"use client";

import { TOPICS } from "@/lib/facts";
import { useT } from "@/lib/i18n";
import { PageIntro, ReadNext, SiteFooter, SiteHeader } from "./ui";

// Source names are written once, in Indonesian; English swaps the few joining words.
function sourceLabel(src: string, lang: string) {
  if (lang === "id") return src;
  return src
    .replace("dkk.", "et al.")
    .replace(", melalui ", ", via ")
    .replace(" dan ", " and ")
    .replace(", dari ", ", from ")
    .replace("studi HBSC", "HBSC study")
    .replace("jajak pendapat U-Report", "U-Report poll");
}

export function FactsPage() {
  const { t, lang } = useT();
  return (
    <>
      <SiteHeader />
      <main className="mx-auto max-w-5xl px-5 pt-14 sm:px-8">
        <PageIntro eyebrow={t("facts.eyebrow")} title={t("facts.title")} lead={t("facts.lead")} />

        <nav aria-label={t("facts.topics")} className="mt-8 flex flex-wrap gap-2">
          {TOPICS.map((topic) => (
            <a key={topic.key} href={`#${topic.key}`} className="glass-fill rounded-full px-3.5 py-1.5 text-sm font-semibold hover:border-navy/40">
              {topic.title[lang]}
            </a>
          ))}
        </nav>

        <div className="mt-10 space-y-6">
          {TOPICS.map((topic) => (
            <section key={topic.key} id={topic.key} className="glass scroll-mt-24 rounded-3xl p-6 sm:p-8" aria-labelledby={`${topic.key}-h`}>
              <h2 id={`${topic.key}-h`} className="text-[1.35rem] font-bold tracking-[-0.01em]">{topic.title[lang]}</h2>
              <ul className="mt-5 divide-y divide-ink/[0.07]">
                {topic.facts.map((f) => (
                  <li key={f.url + f.v.en} className="grid gap-x-6 gap-y-1 py-4 sm:grid-cols-[8.5rem_1fr]">
                    <p className="text-[1.75rem] font-extrabold leading-none tracking-tight text-navy tabular">{f.v[lang]}</p>
                    <div>
                      <p className="text-[0.98rem] leading-relaxed">{f.text[lang]}</p>
                      <a href={f.url} target="_blank" rel="noopener noreferrer" className="mt-1.5 inline-block text-sm font-semibold text-slate underline-offset-4 hover:text-navy hover:underline">
                        {sourceLabel(f.src, lang)}, {f.date}
                      </a>
                    </div>
                  </li>
                ))}
              </ul>
              {topic.note && <p className="mt-2 rounded-xl bg-navy/[0.05] px-4 py-3 text-sm text-ink/80">{topic.note[lang]}</p>}
              {topic.dcai && (
                <p className="mt-4 flex items-start gap-2.5 border-t border-ink/[0.07] pt-4 text-[0.95rem]">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src="/dcai-logo.png" alt="" width={16} height={19} className="mt-0.5 h-[19px] w-auto" />
                  <span>
                    <span className="font-semibold">{t("facts.dcai")}</span> {topic.dcai[lang]}
                  </span>
                </p>
              )}
            </section>
          ))}
        </div>

        <section className="mt-10 max-w-[70ch] text-sm text-slate">
          <h2 className="font-bold text-ink">{t("facts.method.t")}</h2>
          <p className="mt-2">{t("facts.method.b")}</p>
        </section>
        <ReadNext current="/fakta" />
      </main>
      <SiteFooter />
    </>
  );
}
