"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { Guardian, Lang } from "@/lib/types";

import { useDash } from "./shell";

// General settings only. Everything about one child (consent, school, phone, data) now lives
// on that child's own page, under its tabs.
export function SettingsView() {
  const { t, setLang } = useT();
  const { guardian, setGuardian } = useDash();
  const [saved, setSaved] = useState(false);

  async function changeLang(language: Lang) {
    const g = await api<Guardian>("auth/me", { method: "PATCH", body: { language } });
    setGuardian(g);
    setLang(g.language);
    setSaved(true);
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-[1.75rem] font-bold tracking-[-0.02em]">{t("set.title")}</h1>

      <section className="glass mt-8 rounded-3xl p-6 sm:p-7" aria-labelledby="lang-h">
        <h2 id="lang-h" className="text-lg font-bold">{t("set.language")}</h2>
        <p className="mt-1 text-sm text-slate">{t("set.languageHint")}</p>
        <div className="mt-3 flex items-center gap-2">
          {(["id", "en"] as const).map((l) => (
            <button
              key={l}
              type="button"
              aria-pressed={guardian.language === l}
              onClick={() => changeLang(l)}
              className={`rounded-lg border px-4 py-2 font-medium ${
                guardian.language === l ? "border-navy bg-navy text-paper" : "border-ink/10 bg-white/60 hover:border-navy/50"
              }`}
            >
              {l === "id" ? "Bahasa Indonesia" : "English"}
            </button>
          ))}
          {saved && <span role="status" className="text-sm text-aman">{t("set.saved")}</span>}
        </div>
      </section>
    </div>
  );
}
