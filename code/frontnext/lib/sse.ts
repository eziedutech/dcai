"use client";

// Server-Sent Events over fetch, so the session cookie path and our CSRF rules apply the
// same way as for every other call. Reconnects with Last-Event-ID: the server replays
// what was missed and closes streams every few minutes on purpose.

export type LiveMessage = { id: string; event: string; data: unknown };

export function follow(path: string, onMessage: (m: LiveMessage) => void): () => void {
  let stopped = false;
  let lastId = "";
  let controller = new AbortController();
  let retry = 3000;

  async function run() {
    while (!stopped) {
      try {
        const resp = await fetch(`/api/v1/${path}`, {
          headers: { accept: "text/event-stream", ...(lastId ? { "last-event-id": lastId } : {}) },
          signal: controller.signal,
          cache: "no-store",
        });
        if (resp.status === 401 || resp.status === 404) return;
        if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`);
        const reader = resp.body.pipeThrough(new TextDecoderStream()).getReader();
        let buffer = "";
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += value;
          let cut: number;
          while ((cut = buffer.indexOf("\n\n")) >= 0) {
            const block = buffer.slice(0, cut);
            buffer = buffer.slice(cut + 2);
            let id = "";
            let event = "message";
            const data: string[] = [];
            for (const line of block.split("\n")) {
              if (line.startsWith("id: ")) id = line.slice(4);
              else if (line.startsWith("event: ")) event = line.slice(7);
              else if (line.startsWith("data: ")) data.push(line.slice(6));
              else if (line.startsWith("retry: ")) retry = Number(line.slice(7)) || retry;
            }
            if (id) lastId = id;
            if (data.length) {
              try {
                onMessage({ id, event, data: JSON.parse(data.join("\n")) });
              } catch {
                // A malformed event is skipped; the next one still arrives.
              }
            }
          }
        }
      } catch {
        if (stopped) return;
      }
      await new Promise((r) => setTimeout(r, retry));
      controller = new AbortController();
    }
  }

  void run();
  return () => {
    stopped = true;
    controller.abort();
  };
}
