"use client";
import { useRef, useState } from "react";
import { StateCode, api } from "@/lib/api";

export default function UploadPanel({
  state,
  onUploaded,
}: {
  state: StateCode | "";
  onUploaded: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      await api.upload(file, state);
      onUploaded();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  return (
    <div className="card p-4 space-y-3">
      <div>
        <h2 className="text-sm font-semibold">Upload Governing Document</h2>
        <p className="text-xs text-slate-400">
          PDF up to 50MB. OCR runs automatically on scanned legacy deeds.
          Text is anonymized before any external API call.
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        disabled={busy}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handle(f);
        }}
        className="text-xs file:mr-3 file:rounded file:border-0 file:bg-accent file:px-3 file:py-1.5 file:text-ink file:font-semibold"
      />
      {busy && <p className="text-xs text-slate-400">Indexing…</p>}
      {error && <p className="text-xs text-red-400">{error}</p>}
      {!state && (
        <p className="text-xs text-amber-400">Select a jurisdiction first for best results.</p>
      )}
    </div>
  );
}
