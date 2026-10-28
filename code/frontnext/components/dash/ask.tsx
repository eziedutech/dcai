"use client";

import { useRef, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import type { AskOut, AskTurn } from "@/lib/types";
import { Button } from "../ui";

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
  return (
    <div className="mx-auto flex max-w-3xl flex-col">
      <h1 className="text-[1.75rem] font-bold tracking-[-0.02em]">{t("ask.title")}</h1>
      <p className="mt-2 max-w-[62ch] text-slate">{t("ask.lead")}</p>

      <div className="mt-8 space-y-6" aria-live="polite">
        {turns.length === 0 && (
          <ul className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <li key={s}>
                <button
                  type="button"
                  onClick={() => send(s)}
                  className="glass-fill rounded-full px-4 py-2 text-[0.95rem] font-medium hover:border-navy/50"
                >
                  {s}
                </button>
              </li>
            ))}
          </ul>
        )}
        {turns.map((turn, i) =>
          turn.role === "user" ? (
            <p key={i} className="ml-auto max-w-[80%] rounded-2xl rounded-br-md bg-navy px-4 py-2.5 text-paper">
              {turn.content}
            </p>
          ) : (
            <div key={i} className="max-w-[90%]">
              <div className="glass-fill rounded-3xl rounded-bl-md bg-white/80 px-5 py-4 text-[1.02rem]">
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
          ),
        )}
        {busy && (
          <p role="status" className="text-slate">
            {t("ask.thinking")}
            <span aria-hidden className="inline-block w-6 animate-pulse">...</span>
          </p>
        )}
        <div ref={endRef} />
      </div>

      <form
        className="sticky bottom-0 mt-8 bg-paper pt-3 pb-4"
        onSubmit={(e) => {
          e.preventDefault();
          void send(question);
        }}
      >
        {error && (
          <p role="alert" className="mb-2 text-sm font-medium text-mendesak">
            {error}
          </p>
        )}
        <div className="flex gap-2">
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
            className="min-h-[3.25rem] flex-1 resize-none rounded-xl border border-ink/10 bg-white/75 px-3.5 py-2.5 outline-none focus:border-navy focus:ring-2 focus:ring-navy/20"
          />
          <Button type="submit" disabled={busy || !question.trim()} className="self-end">
            {t("ask.send")}
          </Button>
        </div>
        <p className="mt-2 text-sm text-slate">{t("ask.notStored")}</p>
      </form>
    </div>
  );
}
