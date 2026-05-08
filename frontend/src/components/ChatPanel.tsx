"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ChatMessage, Citation, StateCode, api } from "@/lib/api";
import HelpHint from "./HelpHint";

export default function ChatPanel({
  state,
  docIds,
}: {
  state: StateCode | "";
  docIds: string[];
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);

  const send = async () => {
    if (!input.trim() || busy) return;
    const next = [...messages, { role: "user" as const, content: input.trim() }];
    setMessages(next);
    setInput("");
    setBusy(true);
    setError(null);
    try {
      const r = await api.chat({ state, doc_ids: docIds, messages: next });
      setMessages([...next, { role: "assistant", content: r.answer }]);
      setCitations(r.citations);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold flex items-center">
          Counsel Chat
          <HelpHint title="How Counsel Chat works">
            Ask jurisdiction-specific questions. The active state and any
            selected documents are sent to the AI engine with the firm's
            system prompt. Document text is anonymized and only the most relevant excerpts
            (TF-IDF top-k) are sent — citations show which pages were used.
            Cmd/Ctrl+Enter to send.
          </HelpHint>
        </h2>
        <span className="text-xs text-slate-400">
          {state || "no state"} · {docIds.length} doc{docIds.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="h-[460px] overflow-y-auto space-y-3 rounded-md border border-border bg-ink/40 p-3">
        {messages.length === 0 && (
          <p className="text-xs text-slate-500">
            Ask: “Reconcile Article VII of the Master Deed against MGL c.183A § 5.”
          </p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`text-sm ${m.role === "user" ? "text-slate-200" : "text-slate-100"}`}
          >
            <div className="label mb-1">{m.role}</div>
            <div className="prose-legal max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
            </div>
            {m.role === "assistant" && (
              <p className="mt-2 text-[11px] italic text-amber-300/80">
                Verify every citation independently before relying on this output.
                AI-generated; not legal advice.
              </p>
            )}
          </div>
        ))}
        {busy && <p className="text-xs text-slate-400">Thinking…</p>}
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>

      {citations.length > 0 && (
        <div className="text-xs text-slate-400">
          <div className="label mb-1">Retrieved excerpts</div>
          <ul className="space-y-1">
            {citations.map((c, i) => (
              <li key={i}>
                {c.filename} — p. {c.page_start}
                {c.page_end !== c.page_start ? `–${c.page_end}` : ""} (score {c.score.toFixed(2)})
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-2">
        <textarea
          className="textarea"
          rows={2}
          placeholder="Ask a question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) send();
          }}
        />
        <button className="btn-primary" onClick={send} disabled={busy}>
          Send
        </button>
      </div>
    </div>
  );
}
