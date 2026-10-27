"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useDash } from "@/components/dash/shell";
import { useT } from "@/lib/i18n";

export default function Page() {
  const { kids } = useDash();
  const { t } = useT();
  const router = useRouter();
  useEffect(() => {
    if (kids.length > 0) router.replace(`/dasbor/anak/${kids[0].id}`);
  }, [kids, router]);
  if (kids.length > 0) return null;
  return (
    <div className="mx-auto max-w-xl py-16">
      <h1 className="text-[1.75rem] font-bold tracking-[-0.02em]">{t("dash.empty.title")}</h1>
      <p className="mt-3 text-slate">{t("dash.empty.body")}</p>
      <Link href="/dasbor/tambah" className="mt-6 inline-block rounded-lg bg-navy px-5 py-3 font-semibold text-paper hover:bg-ink">
        {t("dash.addChild")}
      </Link>
    </div>
  );
}
