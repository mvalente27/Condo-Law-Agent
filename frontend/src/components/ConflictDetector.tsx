"use client";
import { useState } from "react";
import { ConflictFinding, DocumentSummary, StateCode, api } from "@/lib/api";
import HelpHint from "./HelpHint";

export default function ConflictDetector({
  state,
  docs,
}: {
  state: StateCode | "";
  docs: DocumentSummary[];
}) {
  const [results, setResults] = useState<Record<string, ConflictFinding[]>>({});
  const [busy, setBusy] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const isBusy = (id: string) => busy.has(id);
  const setDocBusy = (id: string, on: boolean) =>
    setBusy((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });

  const run = async (docId: string) => {
    if (!state) {
      setError("Select a jurisdiction first.");
      return;
    }
    setDocBusy(docId, true);
    setError(null);
    try {
      const r = await api.conflicts(state, docId);
      setResults((prev) => ({ ...prev, [docId]: r }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    } finally {
      setDocBusy(docId, false);
    }
  };

  const runAll = async () => {
    if (!state) {
      setError("Select a jurisdiction first.");
      return;
    }
    if (docs.length === 0) return;
    setError(null);
    await Promise.all(docs.map((d) => run(d.doc_id)));
  };

  return (
    <div className="card p-4 space-y-3">
      <div>
        <h2 className="text-sm font-semibold flex items-center">
          Conflict Detector
          <HelpHint title="How Conflict Detector works">
            Targets red-flag clauses (absolute discretion, fiduciary waivers,
            super-lien deviations, supermajority amendment locks, restraints
            on alienation) and asks the AI engine to reconcile them with the active
            state's Condominium Act and modern case law. Returns a JSON
            list of findings with severity. Run on one document or scan all
            selected at once.
          </HelpHint>
        </h2>
        <p className="text-xs text-slate-400">
          Flags clauses that conflict with the active state's Condominium Act
          or modern New England case law (e.g., absolute-discretion language).
        </p>
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      {docs.length === 0 && (
        <p className="text-xs text-slate-500">Select one or more documents on the left.</p>
      )}
      {docs.length > 0 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">
            {docs.length} document{docs.length === 1 ? "" : "s"} selected
          </span>
          <button
            className="btn-primary"
            disabled={busy.size > 0}
            onClick={runAll}
          >
            {busy.size > 0 ? `Scanning ${busy.size}…` : "Scan all selected"}
          </button>
        </div>
      )}
      <ul className="space-y-3">
        {docs.map((d) => (
          <li key={d.doc_id} className="rounded-md border border-border bg-ink/40 p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">{d.filename}</div>
              <button
                className="btn"
                disabled={isBusy(d.doc_id)}
                onClick={() => run(d.doc_id)}
              >
                {isBusy(d.doc_id) ? "Scanning…" : "Scan"}
              </button>
            </div>
            {results[d.doc_id] && (
              <ul className="mt-3 space-y-2">
                {results[d.doc_id].length === 0 && (
                  <li className="text-xs text-slate-400">No conflicts identified.</li>
                )}
                {results[d.doc_id].map((f, i) => (
                  <li key={i} className="rounded border border-border p-2 text-xs">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] uppercase ${
                          f.severity === "high"
                            ? "bg-red-500/20 text-red-300"
                            : f.severity === "medium"
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-slate-500/20 text-slate-300"
                        }`}
                      >
                        {f.severity}
                      </span>
                      <span className="text-slate-300">{f.issue}</span>
                    </div>
                    <blockquote className="mt-1 border-l-2 border-border pl-2 text-slate-400">
                      “{f.clause}”
                    </blockquote>
                    {f.statute_or_case && (
                      <div className="mt-1 text-slate-400">Authority: {f.statute_or_case}</div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
