"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { Child, ConsentText, Device, Guardian, Lang, Scope } from "@/lib/types";
import { Button, formatWhen } from "../ui";
import { useDash } from "./shell";

export function SettingsView() {
  const { t, setLang } = useT();
  const { guardian, setGuardian, kids } = useDash();
  const [saved, setSaved] = useState(false);
  const [text, setText] = useState<ConsentText | null>(null);
  useEffect(() => {
    api<ConsentText>("consents/text").then(setText, () => undefined);
  }, []);

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

      {kids.map((k) => (
        <ChildSettings key={k.id} child={k} text={text} />
      ))}
    </div>
  );
}

function ChildSettings({ child, text }: { child: Child; text: ConsentText | null }) {
  const { t, lang } = useT();
  const { reload } = useDash();
  const router = useRouter();
  const [devices, setDevices] = useState<Device[]>([]);
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Device[]>(`children/${child.id}/devices`).then(setDevices, () => undefined);
  }, [child.id]);

  async function toggle(scope: Scope, on: boolean) {
    if (!text) return;
    setBusy(true);
    try {
      await api("consents", {
        method: "POST",
        body: { child_id: child.id, text_version: text.version, action: on ? "grant" : "revoke", scopes: [scope] },
      });
      await reload();
    } finally {
      setBusy(false);
    }
  }

  async function revoke(id: string) {
    await api(`devices/${id}`, { method: "DELETE" });
    setDevices(await api<Device[]>(`children/${child.id}/devices`));
  }

  async function erase() {
    setBusy(true);
    await api(`children/${child.id}/data`, { method: "DELETE" });
    await reload();
    router.push("/dasbor");
  }

  return (
    <section className="glass mt-6 rounded-3xl p-6 sm:p-7" aria-labelledby={`c-${child.id}`}>
      <h2 id={`c-${child.id}`} className="text-[1.35rem] font-bold">
        {child.nickname} <span className="font-normal text-slate">{child.age_range} {t("common.age")}</span>
      </h2>

      <h3 className="mt-6 font-bold">{t("set.consent")}</h3>
      <ul className="mt-3 divide-y divide-ink/[0.07] border-y border-ink/[0.07]">
        {(text?.scopes ?? []).map((s) => {
          const on = child.consent_scopes.includes(s);
          return (
            <li key={s} className="flex items-center justify-between gap-4 py-3">
              <span>
                <span className="block font-medium">{t(`scope.${s}`)}</span>
                <span className="block text-sm text-slate">{t(`scopeHint.${s}`)}</span>
              </span>
              <Button variant={on ? "quiet" : "primary"} disabled={busy} onClick={() => toggle(s, !on)} className="shrink-0">
                {on ? t("set.withdraw") : t("set.grant")}
              </Button>
            </li>
          );
        })}
      </ul>

      <h3 className="mt-8 font-bold">{t("set.devices")}</h3>
      {devices.length === 0 ? (
        <p className="mt-2 text-slate">{t("dash.noDevice")}</p>
      ) : (
        <ul className="mt-3 divide-y divide-ink/[0.07] border-y border-ink/[0.07]">
          {devices.map((d) => (
            <li key={d.id} className="flex items-center justify-between gap-4 py-3">
              <span>
                <span className="block font-medium">{d.name}</span>
                <span className="block text-sm text-slate tabular">
                  {formatWhen(d.paired_at, lang)}, v{d.app_version}
                </span>
              </span>
              {d.revoked ? (
                <span className="text-sm text-slate">{t("set.revoked")}</span>
              ) : (
                <Button variant="quiet" onClick={() => revoke(d.id)}>{t("set.revoke")}</Button>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-8 rounded-2xl border border-mendesak/30 bg-mendesak-soft/40 px-5 py-5">
        <h3 className="font-bold text-mendesak">{t("set.delete")}</h3>
        <p className="mt-1 max-w-[60ch] text-sm text-slate">{t("set.deleteHint")}</p>
        <label className="mt-4 block text-sm font-semibold" htmlFor={`del-${child.id}`}>
          {t("set.deleteConfirm")}
        </label>
        <div className="mt-1.5 flex flex-wrap gap-2">
          <input
            id={`del-${child.id}`}
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            autoComplete="off"
            className="rounded-xl border border-ink/10 bg-white/75 px-3 py-2 outline-none focus:border-mendesak"
          />
          <Button variant="danger" disabled={busy || confirm !== child.nickname} onClick={erase}>
            {t("set.deleteButton")}
          </Button>
        </div>
      </div>
    </section>
  );
}
