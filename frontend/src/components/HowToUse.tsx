"use client";

export default function HowToUse({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="col-span-12 card p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">How to use this dashboard</h2>
          <p className="text-xs text-slate-400">
            A 60-second tour. Closes for good once dismissed.
          </p>
        </div>
        <button className="btn" onClick={onDismiss}>Got it</button>
      </div>

      <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-sm">
        <li className="rounded-md border border-border bg-ink/40 p-3">
          <div className="text-xs font-semibold text-accent">1 · Pick jurisdiction</div>
          <p className="mt-1 text-slate-300">
            Top-right dropdown. Every answer is locked to that state's
            Condominium Act and case law — no cross-pollination.
          </p>
        </li>
        <li className="rounded-md border border-border bg-ink/40 p-3">
          <div className="text-xs font-semibold text-accent">2 · Upload documents</div>
          <p className="mt-1 text-slate-300">
            Drop in Master Deeds, Declarations, Bylaws, or Rules (PDF, up to
            50 MB). Scanned legacy deeds are OCR'd automatically. Names,
            addresses, units, emails and phones are stripped before any text
            leaves this server.
          </p>
        </li>
        <li className="rounded-md border border-border bg-ink/40 p-3">
          <div className="text-xs font-semibold text-accent">3 · Select what to use</div>
          <p className="mt-1 text-slate-300">
            Check the box next to each document in the left panel. Only
            checked documents are searched for relevant excerpts on each
            request.
          </p>
        </li>
        <li className="rounded-md border border-border bg-ink/40 p-3">
          <div className="text-xs font-semibold text-accent">4 · Choose a tool</div>
          <p className="mt-1 text-slate-300">
            <b>Chat</b> for IRAC research, <b>Conflict Detector</b> for
            governing-doc red flags, <b>Case Theory</b> for the 3 strongest
            precedents to defeat a Motion to Dismiss.
          </p>
        </li>
      </ol>

      <div className="grid gap-3 md:grid-cols-3 text-xs">
        <div className="rounded-md border border-border p-3">
          <div className="font-semibold text-slate-200 mb-1">Chat</div>
          <p className="text-slate-400">
            Ask jurisdiction-specific questions. Cmd/Ctrl+Enter sends.
            Citations show which document pages were used.
          </p>
          <p className="mt-2 text-slate-300">
            Try: <i>"Reconcile Article VII against MGL c.183A § 5 using IRAC."</i>
          </p>
        </div>
        <div className="rounded-md border border-border p-3">
          <div className="font-semibold text-slate-200 mb-1">Conflict Detector</div>
          <p className="text-slate-400">
            Per-document scan. Flags absolute-discretion language, fiduciary
            waivers, super-lien deviations, supermajority locks, etc., with
            severity coding.
          </p>
          <p className="mt-2 text-slate-300">
            Select one document, then click <i>Scan</i>.
          </p>
        </div>
        <div className="rounded-md border border-border p-3">
          <div className="font-semibold text-slate-200 mb-1">Case Theory</div>
          <p className="text-slate-400">
            Paste an anonymized matter summary and (optionally) a county.
            Returns 3 precedents with citations; unverifiable cases are
            marked UNVERIFIED rather than guessed.
          </p>
        </div>
      </div>

      <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
        <b>Test phase notice:</b> upload only non-sensitive or anonymized
        documents. Output is attorney work-product to verify, not legal advice.
        First request after a quiet period may take ~30 seconds while the
        service wakes up.
      </div>
    </div>
  );
}
