"use client";

import { useRef, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { AskOut, AskTurn } from "@/lib/types";

type Turn = AskTurn & { meta?: Omit<AskOut, "answer"> };

const TOOL_LABEL: Record<string, { id: string; en: string }> = {
  list_children: { id: "daftar anak", en: "children" },
  get_overview: { id: "ringkasan", en: "overview" },
  list_conversations: { id: "percakapan", en: "conversations" },
  list_events: { id: "peristiwa", en: "events" },
  list_insights: { id: "insight", en: "insight" },
  how_dcai_works: { id: "cara kerja dcAI", en: "how dcAI works" },
};

/** Plain text with "- " lists, as the assistant is told to write. No HTML is rendered. */
function Answer({ text }: { text: string }) {
  const blocks: React.ReactNode[] = [];
  let list: string[] = [];
  const flush = () => {
    if (list.length) {
      blocks.push(
        <ul key={`l${blocks.length}`} className="list-disc space-y-1 pl-5">
          {list.map((li, i) => (
            <li key={i}>{li}</li>
          ))}
        </ul>,
      );
      list = [];
    }
  };
  for (const raw of text.split("\n")) {
    const line = raw.replace(/\*\*/g, "").trim();
    if (!line) continue;
    if (/^[-*] /.test(line)) list.push(line.slice(2));
    else {
      flush();
      blocks.push(<p key={`p${blocks.length}`}>{line}</p>);
    }
  }
  flush();
  return <div className="space-y-2">{blocks}</div>;
}

/** dcAI's mark beside its answers. */
function Avatar() {
  return (
    <span aria-hidden className="glass-fill grid h-9 w-9 shrink-0 place-items-center rounded-xl">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/dcai-logo.png" alt="" width={18} height={21} className="h-5 w-auto" />
    </span>
  );
}

const SUGGESTION_ICONS = [
  // a calendar week, a speech bubble, a lock
  "M5 6h14v13H5z M5 10h14 M9 4v4 M15 4v4",
  "M5 6h14v9H10l-4 3v-3H5z",
  "M7 11V8a5 5 0 0 1 10 0v3 M6 11h12v9H6z",
];

export function AskPanel() {
  const { t, lang } = useT();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  async function send(q: string) {
    const text = q.trim();
    if (!text || busy) return;
    setError(null);
    setBusy(true);
    setQuestion("");
    const history = turns.slice(-8).map(({ role, content }) => ({ role, content: content.slice(0, 2000) }));
    setTurns((prev) => [...prev, { role: "user", content: text }]);
    try {
      const out = await api<AskOut>("ask", { method: "POST", body: { question: text, history } });
      const { answer, ...meta } = out;
      setTurns((prev) => [...prev, { role: "assistant", content: answer, meta }]);
    } catch (err) {
      setError(err instanceof ApiError && err.status === 429 ? t("ask.tooMany") : t("common.error"));
      setTurns((prev) => prev.slice(0, -1));
      setQuestion(text);
    } finally {
      setBusy(false);
      requestAnimationFrame(() => endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }));
    }
  }

  const suggestions = [t("ask.s1"), t("ask.s2"), t("ask.s3")];
  const canSend = !busy && question.trim().length > 0;
  return (
    <div className="mx-auto flex min-h-[calc(100dvh-6rem)] max-w-3xl flex-col">
      <header className="flex items-start gap-4">
        <span aria-hidden className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-navy text-paper shadow-[0_10px_24px_-14px_rgba(31,58,95,0.9)]">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 5h14v10H10l-5 4z M9 9.5h6 M9 12h3.5" />
          </svg>
        </span>
        <div>
          <h1 className="text-[1.9rem] font-bold leading-tight tracking-[-0.02em]">{t("ask.title")}</h1>
          <p className="mt-1.5 max-w-[62ch] text-slate">{t("ask.lead")}</p>
        </div>
      </header>

      <div className="mt-8 flex-1 space-y-6" aria-live="polite">
        {turns.length === 0 && (
          <section aria-labelledby="ask-start">
            <p id="ask-start" className="eyebrow">
              {t("ask.start")}
            </p>
            <ul className="mt-3 grid gap-3 sm:grid-cols-3">
              {suggestions.map((s, i) => (
                <li key={s}>
                  <button
                    type="button"
                    onClick={() => send(s)}
                    className="glass group flex h-full w-full flex-col items-start gap-3 rounded-2xl p-4 text-left transition-shadow hover:ring-1 hover:ring-navy/25"
                  >
                    <span aria-hidden className="grid h-9 w-9 place-items-center rounded-xl bg-navy/[0.07] text-navy ring-1 ring-navy/10">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                        <path d={SUGGESTION_ICONS[i]} />
                      </svg>
                    </span>
                    <span className="flex-1 font-semibold leading-snug">{s}</span>
                    <span aria-hidden className="text-sm font-semibold text-navy transition-transform group-hover:translate-x-0.5">
                      &rarr;
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        )}
        {turns.map((turn, i) =>
          turn.role === "user" ? (
            <p key={i} className="ml-auto w-fit max-w-[80%] rounded-2xl rounded-br-md bg-navy px-4 py-2.5 text-paper shadow-[0_10px_24px_-16px_rgba(31,58,95,0.9)]">
              {turn.content}
            </p>
          ) : (
            <div key={i} className="flex max-w-[92%] gap-3">
              <Avatar />
              <div className="min-w-0">
                <div className="glass rounded-3xl rounded-tl-md px-5 py-4 text-[1.02rem] leading-relaxed">
                  <Answer text={turn.content} />
                </div>
                {turn.meta && (
                  <p className="mt-1.5 px-1 text-sm text-slate">
                    {turn.meta.source === "fallback"
                      ? t("ask.fallback")
                      : turn.meta.tools_used.length > 0 &&
                        `${t("ask.used")}: ${[...new Set(turn.meta.tools_used)]
                          .map((n) => TOOL_LABEL[n]?.[lang] ?? n)
                          .join(", ")}. ${t("dash.estimate")}`}
                  </p>
                )}
              </div>
            </div>
          ),
        )}
        {busy && (
          <div role="status" className="flex items-center gap-3 text-slate">
            <Avatar />
            <span className="glass flex items-center gap-1.5 rounded-2xl px-4 py-3">
              <span className="sr-only">{t("ask.thinking")}</span>
              {[0, 1, 2].map((d) => (
                <span key={d} aria-hidden className="typing-dot h-1.5 w-1.5 rounded-full bg-slate/60" style={{ animationDelay: `${d * 160}ms` }} />
              ))}
            </span>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form
        className="sticky bottom-4 mt-8"
        onSubmit={(e) => {
          e.preventDefault();
          void send(question);
        }}
      >
        {error && (
          <p role="alert" className="mb-2 rounded-xl bg-mendesak-soft px-3.5 py-2 text-sm font-medium text-mendesak">
            {error}
          </p>
        )}
        <div className="glass rounded-3xl p-2 shadow-[0_24px_50px_-28px_rgba(20,35,58,0.55)] focus-within:ring-2 focus-within:ring-navy/20">
          <div className="flex items-end gap-2">
            <label htmlFor="ask-q" className="sr-only">
              {t("ask.title")}
            </label>
            <textarea
              id="ask-q"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send(question);
                }
              }}
              rows={2}
              maxLength={800}
              placeholder={t("ask.placeholder")}
              className="min-h-[3.25rem] flex-1 resize-none bg-transparent px-3.5 py-2.5 text-[1.02rem] outline-none placeholder:text-slate/70"
            />
            <button
              type="submit"
              disabled={!canSend}
              aria-label={t("ask.send")}
              className={`grid h-11 w-11 shrink-0 place-items-center rounded-2xl transition-colors ${
                canSend ? "bg-navy text-paper hover:bg-ink" : "bg-navy/10 text-navy/40"
              }`}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
                <path d="M4 12 20 4l-4 16-4-7z M12 13 20 4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
              </svg>
            </button>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-ink/[0.06] px-3.5 pt-2 pb-1 text-xs text-slate">
            <span className="inline-flex items-center gap-1.5">
              <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden>
                <rect x="3" y="7" width="10" height="7" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
                <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="currentColor" strokeWidth="1.5" />
              </svg>
              {t("ask.notStored")}
            </span>
            <span className="hidden sm:inline">{t("ask.enter")}</span>
          </div>
        </div>
      </form>
    </div>
  );
}
