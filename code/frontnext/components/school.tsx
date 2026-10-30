"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { schoolApi, schoolMe, schoolSession } from "@/lib/school";
import type { ClassOverview, Staff, StaffClass } from "@/lib/types";
import type { Level } from "@/lib/types";
import { Button, Field, LangToggle, Logo, Skeleton } from "./ui";
import { LEVEL_STYLE } from "./ui";

const LEVELS: Level[] = ["aman", "perhatian", "waspada", "mendesak"];

export function StaffAuthForm({ mode }: { mode: "login" | "register" }) {
  const { t } = useT();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const form = new FormData(e.currentTarget);
    const body: Record<string, string> = {
      email: String(form.get("email") ?? ""),
      password: String(form.get("password") ?? ""),
    };
    if (mode === "register") {
      body.name = String(form.get("name") ?? "");
      body.school_name = String(form.get("school_name") ?? "");
    }
    try {
      await schoolSession(mode, body);
      router.push("/sekolah");
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setError(status === 401 ? t("auth.wrong") : status === 409 ? t("auth.taken") : status === 422 ? t("auth.invalid") : t("common.error"));
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto mt-16 max-w-md px-5">
      <div className="flex items-center justify-between">
        <Logo href="/" />
        <LangToggle />
      </div>
      <main className="glass mt-6 rounded-2xl p-7 sm:p-9">
        <p className="eyebrow">{t("sekolah.for")}</p>
        <h1 className="mt-2 text-[1.6rem] font-bold tracking-[-0.02em]">
          {mode === "login" ? t("sekolah.signinTitle") : t("sekolah.signupTitle")}
        </h1>
        <form onSubmit={submit} className="mt-8 space-y-5">
          {mode === "register" && (
            <>
              <Field id="name" name="name" label={t("sekolah.name")} autoComplete="name" required maxLength={80} />
              <Field id="school_name" name="school_name" label={t("sekolah.schoolName")} required maxLength={120} />
            </>
          )}
          <Field id="email" name="email" type="email" label={t("auth.email")} autoComplete="email" required />
          <Field
            id="password"
            name="password"
            type="password"
            label={t("auth.password")}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            hint={mode === "register" ? t("auth.passwordHint") : undefined}
            minLength={mode === "register" ? 10 : undefined}
            required
          />
          {error && (
            <p role="alert" className="rounded-lg bg-mendesak-soft px-3.5 py-2.5 text-sm font-medium text-mendesak">
              {error}
            </p>
          )}
          <Button type="submit" disabled={busy} className="w-full">
            {mode === "login" ? t("auth.signin") : t("auth.signup")}
          </Button>
        </form>
        <p className="mt-6 text-sm">
          <Link href={mode === "login" ? "/sekolah/daftar" : "/sekolah/masuk"} className="font-semibold text-navy underline-offset-4 hover:underline">
            {mode === "login" ? t("sekolah.toSignup") : t("sekolah.toSignin")}
          </Link>
        </p>
      </main>
    </div>
  );
}

export function SchoolDashboard() {
  const { t } = useT();
  const router = useRouter();
  const [staff, setStaff] = useState<Staff | null | undefined>(undefined);
  const [classes, setClasses] = useState<StaffClass[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [overview, setOverview] = useState<ClassOverview | null>(null);
  const [newCode, setNewCode] = useState<{ name: string; code: string } | null>(null);

  const loadClasses = useCallback(async () => {
    setClasses(await schoolApi<StaffClass[]>("classes"));
  }, []);

  useEffect(() => {
    (async () => {
      const me = await schoolMe();
      if (!me) {
        router.replace("/sekolah/masuk");
        return;
      }
      setStaff(me);
      await loadClasses().catch(() => undefined);
    })();
  }, [router, loadClasses]);

  async function openClass(id: string) {
    setSelected(id);
    setOverview(null);
    setOverview(await schoolApi<ClassOverview>(`classes/${id}/overview`));
  }

  async function createClass(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const name = String(form.get("name") ?? "").trim();
    if (!name) return;
    const created = await schoolApi<StaffClass>("classes", { method: "POST", body: { name } });
    setNewCode({ name: created.name, code: created.join_code ?? "" });
    e.currentTarget.reset();
    await loadClasses();
  }

  async function signOut() {
    await schoolSession("logout").catch(() => undefined);
    router.replace("/sekolah/masuk");
  }

  if (staff === undefined) return <div className="p-8"><Skeleton label={t("common.loading")} /></div>;
  if (staff === null) return null;

  return (
    <div className="mx-auto max-w-4xl px-5 py-8 sm:px-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Logo href="/" />
        </div>
        <div className="flex items-center gap-3 text-sm text-slate">
          <span>{staff.name}</span>
          <LangToggle />
          <button type="button" onClick={signOut} className="rounded-md px-2 py-1 font-medium hover:text-ink">
            {t("dash.signout")}
          </button>
        </div>
      </header>

      <h1 className="mt-8 text-[1.8rem] font-bold tracking-[-0.02em]">{t("sekolah.title")}</h1>
      <p className="mt-1 max-w-[60ch] text-slate">{t("sekolah.lead")}</p>

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
        <section className="glass rounded-2xl p-6">
          <h2 className="text-lg font-bold">{t("sekolah.classes")}</h2>
          {classes.length === 0 ? (
            <p className="mt-3 text-sm text-slate">{t("sekolah.noClasses")}</p>
          ) : (
            <ul className="mt-3 space-y-1.5">
              {classes.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => openClass(c.id)}
                    aria-current={selected === c.id}
                    className={`flex w-full items-center justify-between rounded-lg border px-3.5 py-2 text-left ${selected === c.id ? "border-navy bg-white/70" : "border-ink/10 bg-white/50 hover:border-navy/40"}`}
                  >
                    <span className="font-medium">{c.name}</span>
                    <span className="text-sm text-slate">{c.members} {t("sekolah.members")}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <form onSubmit={createClass} className="mt-5 flex items-end gap-2">
            <Field id="name" name="name" label={t("sekolah.newClass")} required maxLength={80} />
            <Button type="submit">{t("sekolah.create")}</Button>
          </form>
          {newCode && (
            <div className="glass-fill mt-3 rounded-lg px-3.5 py-2.5 text-sm">
              <p className="text-slate">{t("sekolah.codeFor")} <span className="font-semibold text-ink">{newCode.name}</span></p>
              <p className="mt-1 font-mono text-lg font-bold tracking-widest tabular">{newCode.code}</p>
              <p className="mt-1 text-slate">{t("sekolah.codeHint")}</p>
            </div>
          )}
        </section>

        <section className="glass rounded-2xl p-6" aria-live="polite">
          <h2 className="text-lg font-bold">{t("sekolah.overview")}</h2>
          {!selected ? (
            <p className="mt-3 text-sm text-slate">{t("sekolah.pickClass")}</p>
          ) : !overview ? (
            <p className="mt-3 text-sm text-slate">{t("common.loading")}</p>
          ) : overview.suppressed || !overview.by_level ? (
            <div className="mt-3">
              <p className="text-slate">{t("sekolah.suppressed")}</p>
              <p className="mt-1 text-sm text-slate">{t("sekolah.participating")}: {overview.total}</p>
            </div>
          ) : (
            <div className="mt-4">
              <p className="text-sm text-slate">{t("sekolah.participating")}: {overview.total} · {t("dash.window").toLowerCase()}</p>
              <ul className="mt-3 space-y-2">
                {LEVELS.map((lvl) => {
                  const n = overview.by_level?.[lvl] ?? 0;
                  const pct = overview.total ? Math.round((n / overview.total) * 100) : 0;
                  return (
                    <li key={lvl} className="flex items-center gap-3">
                      <span className="w-28 text-sm font-medium">{t(`level.${lvl}`)}</span>
                      <span className="h-2.5 flex-1 overflow-hidden rounded-full bg-ink/10">
                        <span className={`block h-full ${LEVEL_STYLE[lvl].bar}`} style={{ width: `${pct}%` }} />
                      </span>
                      <span className="w-8 text-right text-sm tabular">{n}</span>
                    </li>
                  );
                })}
              </ul>
              <p className="mt-4 text-sm">
                {t("sekolah.support")}:{" "}
                <span className="font-semibold">{overview.support === null ? t("sekolah.supportHidden") : overview.support}</span>
              </p>
              <p className="mt-4 text-xs text-slate">{t("sekolah.privacyNote")}</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
