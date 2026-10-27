"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { Child, ConsentText, Device, Scope } from "@/lib/types";
import { Button, Field, formatWhen } from "../ui";
import { useDash } from "./shell";

const AGES = ["10-12", "13-15", "16-17"] as const;

export function AddChild() {
  const { t } = useT();
  const params = useSearchParams();
  const { kids, reload } = useDash();
  const existing = kids.find((k) => k.id === params.get("anak"));
  const [child, setChild] = useState<Child | null>(existing ?? null);
  const [step, setStep] = useState<1 | 2 | 3>(existing ? (existing.consent_scopes.length ? 3 : 2) : 1);

  const steps = [t("add.step1"), t("add.step2"), t("add.step3")];
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-[1.75rem] font-bold tracking-[-0.02em]">{t("add.title")}</h1>
      <ol className="mt-6 flex gap-2 text-sm" aria-label={t("add.title")}>
        {steps.map((label, i) => {
          const n = (i + 1) as 1 | 2 | 3;
          const state = n < step ? "done" : n === step ? "now" : "next";
          return (
            <li
              key={label}
              aria-current={state === "now" ? "step" : undefined}
              className={`flex-1 border-t-4 pt-2 ${state === "next" ? "border-line text-slate" : "border-navy font-semibold"}`}
            >
              <span className="tabular">{n}</span> {label}
            </li>
          );
        })}
      </ol>
      <div className="mt-8">
        {step === 1 && (
          <ProfileStep
            onDone={async (c) => {
              setChild(c);
              await reload();
              setStep(2);
            }}
          />
        )}
        {step === 2 && child && (
          <ConsentStep
            child={child}
            onDone={async () => {
              await reload();
              setStep(3);
            }}
          />
        )}
        {step === 3 && child && <PairStep child={child} />}
      </div>
    </div>
  );
}

function ProfileStep({ onDone }: { onDone: (c: Child) => Promise<void> }) {
  const { t } = useT();
  const [age, setAge] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <form
      className="space-y-6"
      onSubmit={async (e) => {
        e.preventDefault();
        const nickname = String(new FormData(e.currentTarget).get("nickname") ?? "").trim();
        if (!nickname || !age) return setError(t("auth.invalid"));
        setBusy(true);
        try {
          await onDone(await api<Child>("children", { method: "POST", body: { nickname, age_range: age } }));
        } catch {
          setError(t("common.error"));
          setBusy(false);
        }
      }}
    >
      <Field id="nickname" name="nickname" label={t("add.nickname")} hint={t("add.nicknameHint")} required maxLength={40} />
      <fieldset>
        <legend className="mb-2 text-sm font-semibold">{t("add.age")}</legend>
        <div className="flex flex-wrap gap-2">
          {AGES.map((a) => (
            <label
              key={a}
              className={`cursor-pointer rounded-lg border px-4 py-2.5 font-medium tabular has-[:focus-visible]:outline has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-navy ${
                age === a ? "border-navy bg-navy text-paper" : "border-line bg-white hover:border-navy"
              }`}
            >
              <input type="radio" name="age" value={a} className="sr-only" checked={age === a} onChange={() => setAge(a)} />
              {a} {t("common.age")}
            </label>
          ))}
        </div>
      </fieldset>
      {error && <p role="alert" className="text-sm font-medium text-mendesak">{error}</p>}
      <Button type="submit" disabled={busy}>{t("add.next")}</Button>
    </form>
  );
}

function ConsentStep({ child, onDone }: { child: Child; onDone: () => Promise<void> }) {
  const { t, lang } = useT();
  const [text, setText] = useState<ConsentText | null>(null);
  const [picked, setPicked] = useState<Set<Scope>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api<ConsentText>("consents/text").then(setText, () => setError(t("common.error")));
  }, [t]);
  if (!text) return <p role="status" className="text-slate">{error ?? t("common.loading")}</p>;

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        if (picked.size === 0) return setError(t("add.needScope"));
        setBusy(true);
        try {
          await api("consents", {
            method: "POST",
            body: { child_id: child.id, text_version: text.version, action: "grant", scopes: [...picked] },
          });
          await onDone();
        } catch {
          setError(t("common.error"));
          setBusy(false);
        }
      }}
    >
      <p className="max-w-[62ch] text-slate">{t("add.consentLead")}</p>
      <div className="mt-4 max-h-80 overflow-y-auto rounded-[var(--radius-panel)] border border-line bg-white px-5 py-4 text-[0.95rem] whitespace-pre-line" tabIndex={0}>
        {lang === "id" ? text.id : text.en}
      </div>
      <p className="mt-2 text-sm text-slate tabular">v{text.version}</p>
      <fieldset className="mt-6 space-y-3">
        {text.scopes.map((s) => (
          <label key={s} className="flex cursor-pointer gap-3 rounded-lg border border-line bg-white px-4 py-3 has-[:checked]:border-navy">
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 accent-[#1f3a5f]"
              checked={picked.has(s)}
              onChange={(e) => {
                const next = new Set(picked);
                if (e.target.checked) next.add(s);
                else next.delete(s);
                setPicked(next);
              }}
            />
            <span>
              <span className="block font-semibold">{t(`scope.${s}`)}</span>
              <span className="block text-sm text-slate">{t(`scopeHint.${s}`)}</span>
            </span>
          </label>
        ))}
      </fieldset>
      {error && <p role="alert" className="mt-4 text-sm font-medium text-mendesak">{error}</p>}
      <Button type="submit" disabled={busy} className="mt-6">{t("add.agree")}</Button>
    </form>
  );
}

function PairStep({ child }: { child: Child }) {
  const { t, lang } = useT();
  const router = useRouter();
  const [code, setCode] = useState<{ code: string; expires_at: string } | null>(null);
  const [paired, setPaired] = useState<Device | null>(null);
  const [error, setError] = useState(false);

  async function newCode() {
    try {
      setCode(await api(`children/${child.id}/pairing-codes`, { method: "POST" }));
    } catch {
      setError(true);
    }
  }
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one code per visit
    void newCode();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // The phone pairs on its own; this page notices within a few seconds.
  useEffect(() => {
    if (paired) return;
    const started = Date.now();
    const id = setInterval(async () => {
      try {
        const list = await api<Device[]>(`children/${child.id}/devices`);
        const fresh = list.find((d) => !d.revoked && Date.parse(d.paired_at) >= started - 60_000);
        if (fresh) setPaired(fresh);
      } catch {
        // keep polling
      }
    }, 3000);
    return () => clearInterval(id);
  }, [child.id, paired]);

  return (
    <div>
      <p className="max-w-[56ch] text-slate">{t("add.pairLead")}</p>
      {error && <p role="alert" className="mt-4 text-mendesak">{t("common.error")}</p>}
      {code && (
        <div className="mt-6 rounded-[var(--radius-panel)] border border-line bg-white px-6 py-8 text-center">
          <p className="font-mono text-[2.6rem] font-bold tracking-[0.18em] text-navy tabular" aria-live="polite">
            {code.code}
          </p>
          <p className="mt-2 text-sm text-slate">
            {t("add.validUntil")} {formatWhen(code.expires_at, lang)}
          </p>
        </div>
      )}
      {paired && (
        <p role="status" className="mt-6 rounded-lg bg-aman-soft px-4 py-3 font-semibold text-aman">
          {t("add.paired")}: {paired.name}
        </p>
      )}
      <div className="mt-6 flex flex-wrap gap-3">
        <Button variant="quiet" onClick={newCode} type="button">{t("add.newCode")}</Button>
        <Button type="button" onClick={() => router.push(`/dasbor/anak/${child.id}`)}>{t("add.done")}</Button>
      </div>
    </div>
  );
}
