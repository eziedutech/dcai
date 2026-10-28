"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, me, session } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { Child, Guardian } from "@/lib/types";
import { LangToggle, Logo, Skeleton } from "../ui";

type Dash = {
  guardian: Guardian;
  kids: Child[];
  reload: () => Promise<Child[]>;
  setGuardian: (g: Guardian) => void;
};
const DashContext = createContext<Dash | null>(null);

export function useDash() {
  const ctx = useContext(DashContext);
  if (!ctx) throw new Error("useDash outside DashShell");
  return ctx;
}

export function DashShell({ children }: { children: React.ReactNode }) {
  const { t, setLang } = useT();
  const router = useRouter();
  const path = usePathname();
  const [guardian, setGuardian] = useState<Guardian | null>(null);
  const [kids, setKids] = useState<Child[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const reload = useCallback(async () => {
    const list = await api<Child[]>("children");
    setKids(list);
    return list;
  }, []);

  useEffect(() => {
    let live = true;
    (async () => {
      const g = await me();
      if (!live) return;
      if (!g) {
        router.replace(`/masuk?lanjut=${encodeURIComponent(location.pathname)}`);
        return;
      }
      setGuardian(g);
      setLang(g.language);
      try {
        await reload();
      } catch {
        if (live) setFailed(true);
      }
    })();
    return () => {
      live = false;
    };
  }, [reload, router, setLang]);

  async function signOut() {
    await session("logout").catch(() => undefined);
    router.replace("/masuk");
  }

  if (failed) {
    return <p className="p-8 text-slate">{t("common.error")}</p>;
  }
  if (!guardian || !kids) {
    return (
      <div className="px-5 py-10 sm:px-10 lg:pl-[18rem]">
        <Skeleton label={t("common.loading")} />
      </div>
    );
  }

  const link = (href: string, label: string) => {
    const active = path === href || path.startsWith(`${href}/`);
    return (
      <Link
        key={href}
        href={href}
        aria-current={active ? "page" : undefined}
        className={`block rounded-xl px-3 py-2 text-[0.95rem] ${
          active ? "bg-navy font-semibold text-paper shadow-[0_8px_20px_-12px_rgba(31,58,95,0.9)]" : "font-medium text-ink hover:bg-white/70"
        }`}
      >
        {label}
      </Link>
    );
  };

  return (
    <DashContext.Provider value={{ guardian, kids, reload, setGuardian }}>
      <div className="min-h-dvh lg:grid lg:grid-cols-[16rem_1fr]">
        <aside className="glass-bar sticky top-0 z-30 lg:h-dvh lg:border-r lg:border-b-0 lg:border-ink/[0.07]">
          <div className="flex items-center justify-between px-5 py-4 lg:py-5">
            <Logo href="/dasbor" />
            <button
              type="button"
              className="rounded-xl border border-ink/10 bg-white/60 px-3 py-1.5 text-sm font-semibold lg:hidden"
              aria-expanded={menuOpen}
              aria-controls="dash-nav"
              onClick={() => setMenuOpen((v) => !v)}
            >
              Menu
            </button>
          </div>
          <nav
            id="dash-nav"
            className={`${menuOpen ? "block" : "hidden"} px-3 pb-4 lg:block`}
            aria-label={t("nav.dashboard")}
            onClick={(e) => {
              if ((e.target as HTMLElement).closest("a")) setMenuOpen(false);
            }}
          >
            <p className="px-3 pb-1.5 text-sm font-semibold text-slate">{t("dash.children")}</p>
            <div className="space-y-0.5">
              {kids.map((k) => link(`/dasbor/anak/${k.id}`, k.nickname))}
              {link("/dasbor/tambah", `+ ${t("dash.addChild")}`)}
            </div>
            <div className="mt-5 space-y-0.5 border-t border-ink/[0.07] pt-4">
              {link("/dasbor/tanya", t("dash.ask"))}
              {link("/dasbor/pengaturan", t("dash.settings"))}
            </div>
            <div className="mt-5 flex items-center justify-between border-t border-ink/[0.07] px-1 pt-4">
              <button type="button" onClick={signOut} className="rounded-md px-2 py-1 text-sm font-medium text-slate hover:text-ink">
                {t("dash.signout")}
              </button>
              <LangToggle />
            </div>
          </nav>
        </aside>
        <main className="min-w-0 px-5 py-8 sm:px-10 lg:py-10">{children}</main>
      </div>
    </DashContext.Provider>
  );
}
