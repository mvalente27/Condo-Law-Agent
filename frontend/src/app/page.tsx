"use client";

import { useEffect, useState } from "react";
import { STATES, StateCode, DocumentSummary, api } from "@/lib/api";
import StatePicker from "@/components/StatePicker";
import UploadPanel from "@/components/UploadPanel";
import DocumentList from "@/components/DocumentList";
import ChatPanel from "@/components/ChatPanel";
import ConflictDetector from "@/components/ConflictDetector";
import CaseTheory from "@/components/CaseTheory";
import HowToUse from "@/components/HowToUse";

type Tab = "chat" | "conflicts" | "theory";

const HIDE_KEY = "cla.hideHowTo";

export default function Page() {
  const [state, setState] = useState<StateCode | "">("MA");
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [tab, setTab] = useState<Tab>("chat");
  const [showHow, setShowHow] = useState(false);

  const refresh = async () => setDocs(await api.listDocs());

  useEffect(() => {
    if (typeof window !== "undefined") {
      setShowHow(window.localStorage.getItem(HIDE_KEY) !== "1");
    }
    if (!api.backendConfigured()) return;
    refresh().catch(() => undefined);
  }, []);

  const dismissHow = () => {
    if (typeof window !== "undefined") window.localStorage.setItem(HIDE_KEY, "1");
    setShowHow(false);
  };

  const toggleDoc = (id: string) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-border bg-panel/60 backdrop-blur">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">
              Condo Law Agent <span className="text-slate-400 font-normal">— New England</span>
            </h1>
            <p className="text-xs text-slate-400">
              Jurisdiction-aware research assistant for MA, CT, RI, NH, VT, ME.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="btn" onClick={() => setShowHow(true)}>
              How to use
            </button>
            <StatePicker value={state} onChange={setState} states={STATES} />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl w-full px-6 py-6 grid grid-cols-12 gap-6 flex-1">
        {!api.backendConfigured() && (
          <div className="col-span-12 rounded-md border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200">
            Backend URL is not configured. Set <code>NEXT_PUBLIC_BACKEND_URL</code> at
            build time (e.g. in the GitHub Pages workflow) to the public URL of
            your FastAPI deployment.
          </div>
        )}
        {showHow && <HowToUse onDismiss={dismissHow} />}
        <aside className="col-span-12 md:col-span-4 lg:col-span-3 space-y-6">
          <UploadPanel state={state} onUploaded={refresh} />
          <DocumentList
            docs={docs}
            selected={selected}
            onToggle={toggleDoc}
            onDeleted={refresh}
          />
        </aside>

        <section className="col-span-12 md:col-span-8 lg:col-span-9 space-y-4">
          <nav className="flex gap-2">
            {(["chat", "conflicts", "theory"] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`btn ${tab === t ? "border-accent text-accent" : ""}`}
              >
                {t === "chat" ? "Chat" : t === "conflicts" ? "Conflict Detector" : "Case Theory"}
              </button>
            ))}
          </nav>

          <div className={tab === "chat" ? "" : "hidden"}>
            <ChatPanel state={state} docIds={selected} />
          </div>
          <div className={tab === "conflicts" ? "" : "hidden"}>
            <ConflictDetector
              state={state}
              docs={docs.filter((d) => selected.includes(d.doc_id))}
            />
          </div>
          <div className={tab === "theory" ? "" : "hidden"}>
            <CaseTheory state={state} docIds={selected} />
          </div>
        </section>
      </main>
    </div>
  );
}
