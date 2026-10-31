"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, api, session } from "@/lib/api";
import { APK_VERSION } from "@/lib/download";
import { useT } from "@/lib/i18n";
import type { Guardian, Lang } from "@/lib/types";
import { Button, Field } from "../ui";
import { useDash } from "./shell";

// General, account-level settings. Everything about one child lives on that child's page.
export function SettingsView() {
  const { t, setLang } = useT();
  const { guardian, setGuardian } = useDash();
  const router = useRouter();

  const [langSaved, setLangSaved] = useState(false);
  const [name, setName] = useState(guardian.name);
  const [nameSaved, setNameSaved] = useState(false);
  const [curPw, setCurPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [pwMsg, setPwMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function changeLang(language: Lang) {
    const g = await api<Guardian>("auth/me", { method: "PATCH", body: { language } });
    setGuardian(g);
    setLang(g.language);
    setLangSaved(true);
  }

  async function saveName(e: React.FormEvent) {
    e.preventDefault();
    const n = name.trim();
    if (!n || n === guardian.name) return;
    setBusy(true);
    try {
      const g = await api<Guardian>("auth/me", { method: "PATCH", body: { name: n } });
      setGuardian(g);
      setNameSaved(true);
    } finally {
      setBusy(false);
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    if (newPw.length < 10) return;
    setBusy(true);
    setPwMsg(null);
    try {
      await api("auth/change-password", {
        method: "POST",
        body: { current_password: curPw, new_password: newPw },
      });
      setCurPw("");
      setNewPw("");
      setPwMsg({ ok: true, text: t("set.passwordChanged") });
    } catch (err) {
      const text = err instanceof ApiError && err.status === 401 ? t("set.passwordWrong") : t("common.error");
      setPwMsg({ ok: false, text });
    } finally {
      setBusy(false);
    }
  }

  async function signOutAll() {
    setBusy(true);
    await session("logout-all").catch(() => undefined);
    router.replace("/masuk");
  }

  const docs = [
    ["/panduan", t("foot.guide")],
    ["/ketentuan", t("foot.terms")],
    ["/privasi", t("nav.privacy")],
    ["/next", t("nav.next")],
  ] as const;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-[1.75rem] font-bold tracking-[-0.02em]">{t("set.title")}</h1>

      <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="acc-h">
        <h2 id="acc-h" className="text-lg font-bold">{t("set.account")}</h2>
        <form onSubmit={saveName} className="mt-3 flex flex-wrap items-end gap-2">
          <Field
            id="guardian-name"
            label={t("auth.name")}
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setNameSaved(false);
            }}
            maxLength={80}
          />
          <Button type="submit" disabled={busy || !name.trim() || name.trim() === guardian.name}>
            {t("set.save")}
          </Button>
          {nameSaved && <span role="status" className="text-sm text-aman">{t("set.saved")}</span>}
        </form>
        <p className="mt-4 text-sm">
          <span className="font-semibold text-slate">{t("set.email")}: </span>
          <span className="tabular">{guardian.email}</span>
        </p>
      </section>

      <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="lang-h">
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
          {langSaved && <span role="status" className="text-sm text-aman">{t("set.saved")}</span>}
        </div>
      </section>

      <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="pw-h">
        <h2 id="pw-h" className="text-lg font-bold">{t("set.password")}</h2>
        <p className="mt-1 text-sm text-slate">{t("set.passwordHint")}</p>
        <form onSubmit={changePassword} className="mt-3 grid max-w-md gap-3">
          <Field
            id="cur-pw"
            type="password"
            label={t("set.currentPassword")}
            autoComplete="current-password"
            value={curPw}
            onChange={(e) => setCurPw(e.target.value)}
          />
          <Field
            id="new-pw"
            type="password"
            label={t("set.newPassword")}
            hint={t("auth.passwordHint")}
            autoComplete="new-password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <Button type="submit" disabled={busy || !curPw || newPw.length < 10}>
              {t("set.changePassword")}
            </Button>
            {pwMsg && (
              <span role="status" className={`text-sm ${pwMsg.ok ? "text-aman" : "text-mendesak"}`}>
                {pwMsg.text}
              </span>
            )}
          </div>
        </form>
      </section>

      <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="sess-h">
        <h2 id="sess-h" className="text-lg font-bold">{t("set.sessions")}</h2>
        <p className="mt-1 max-w-[60ch] text-sm text-slate">{t("set.sessionsHint")}</p>
        <Button variant="quiet" className="mt-3" disabled={busy} onClick={signOutAll}>
          {t("set.logoutAll")}
        </Button>
      </section>

      <section className="glass rounded-3xl p-6 sm:p-7" aria-labelledby="about-h">
        <h2 id="about-h" className="text-lg font-bold">{t("set.about")}</h2>
        <p className="mt-2 text-sm text-slate tabular">dcAI v{APK_VERSION}</p>
        <ul className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm">
          {docs.map(([href, label]) => (
            <li key={href}>
              <Link href={href} className="font-semibold text-navy underline-offset-4 hover:underline">
                {label}
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
