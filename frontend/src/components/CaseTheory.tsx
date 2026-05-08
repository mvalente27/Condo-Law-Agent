"use client";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { StateCode, api } from "@/lib/api";
import HelpHint from "./HelpHint";

export default function CaseTheory({
  state,
  docIds,
}: {
  state: StateCode | "";
  docIds: string[];
}) {
  const [matter, setMatter] = useState("");
  const [county, setCounty] = useState("");
  const [out, setOut] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!state) {
      setError("Select a jurisdiction first.");
      return;
    }
    if (!matter.trim()) {
      setError("Describe the matter to generate a theory.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await api.caseTheory({
        state,
        matter_summary: matter.trim(),
        county: county.trim() || undefined,
        doc_ids: docIds,
      });
      setOut(r.theory);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card p-4 space-y-3">
      <div>
        <h2 className="text-sm font-semibold flex items-center">
          Case Theory Generator
          <HelpHint title="How Case Theory works">
            Give a short, anonymized matter summary and (optionally) a county.
            Returns the 3 strongest precedents from the active state's
            Supreme/Appeals/Land Court that defeat a Motion to Dismiss,
            with citations. If a case can't be verified, it returns
            "UNVERIFIED" rather than guessing.
          </HelpHint>
        </h2>
        <p className="text-xs text-slate-400">
          “Give me the 3 strongest precedents I can use to defeat a Motion to
          Dismiss in this specific county.”
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <input
          className="input sm:col-span-1"
          placeholder="County (optional)"
          value={county}
          onChange={(e) => setCounty(e.target.value)}
        />
        <textarea
          className="textarea sm:col-span-3"
          rows={4}
          placeholder="Matter summary (anonymized client facts)…"
          value={matter}
          onChange={(e) => setMatter(e.target.value)}
        />
      </div>
      <div>
        <button className="btn-primary" onClick={run} disabled={busy}>
          {busy ? "Generating…" : "Generate Theory"}
        </button>
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
      {out && (
        <div className="prose-legal max-w-none border-t border-border pt-3">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{out}</ReactMarkdown>
          <p className="mt-2 text-[11px] italic text-amber-300/80 not-prose">
            Verify every citation independently before relying on this output.
            AI-generated; not legal advice.
          </p>
        </div>
      )}
    </div>
  );
}
