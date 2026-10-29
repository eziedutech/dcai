"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { ApiError, session } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { Guardian } from "@/lib/types";
import { Button, Field, SiteFooter, SiteHeader } from "./ui";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { t, lang, setLang } = useT();
  const router = useRouter();
  const params = useSearchParams();
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
      body.language = lang;
    }
    try {
      const { guardian } = await session<{ guardian: Guardian }>(mode, body);
      setLang(guardian.language);
      const next = params.get("lanjut");
      router.push(next && next.startsWith("/dasbor") ? next : "/dasbor");
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setError(
        status === 401 ? t("auth.wrong") : status === 409 ? t("auth.taken") : status === 422 ? t("auth.invalid") : t("common.error"),
      );
      setBusy(false);
    }
  }

  return (
    <>
      <SiteHeader />
      <main className="glass mx-auto mt-16 max-w-md rounded-3xl p-7 sm:p-9">
        <p className="eyebrow">{t("auth.for")}</p>
        <h1 className="mt-2 text-[1.75rem] font-bold tracking-[-0.02em]">
          {mode === "login" ? t("auth.signinTitle") : t("auth.signupTitle")}
        </h1>
        <form onSubmit={submit} className="mt-8 space-y-5" noValidate={false}>
          {mode === "register" && (
            <Field id="name" name="name" label={t("auth.name")} autoComplete="name" required maxLength={80} />
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
          <Link href={mode === "login" ? "/daftar" : "/masuk"} className="font-semibold text-navy underline-offset-4 hover:underline">
            {mode === "login" ? t("auth.toSignup") : t("auth.toSignin")}
          </Link>
        </p>
      </main>
      <SiteFooter />
    </>
  );
}
