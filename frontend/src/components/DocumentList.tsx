"use client";
import { DocumentSummary, api } from "@/lib/api";

export default function DocumentList({
  docs,
  selected,
  onToggle,
  onDeleted,
}: {
  docs: DocumentSummary[];
  selected: string[];
  onToggle: (id: string) => void;
  onDeleted: () => void;
}) {
  return (
    <div className="card p-4 space-y-3">
      <h2 className="text-sm font-semibold">Indexed Documents</h2>
      {docs.length === 0 && (
        <p className="text-xs text-slate-400">No documents yet.</p>
      )}
      <ul className="space-y-2">
        {docs.map((d) => (
          <li
            key={d.doc_id}
            className="rounded-md border border-border bg-ink p-2 text-xs"
          >
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selected.includes(d.doc_id)}
                onChange={() => onToggle(d.doc_id)}
                className="mt-0.5"
              />
              <div className="flex-1 min-w-0">
                <div className="truncate font-medium" title={d.filename}>
                  {d.filename}
                </div>
                <div className="text-slate-400">
                  {d.state || "—"} · {d.pages}p · {d.chunks} chunks
                  {d.ocr_pages > 0 && ` · OCR ${d.ocr_pages}`}
                </div>
              </div>
              <button
                className="text-slate-400 hover:text-red-400"
                onClick={async (e) => {
                  e.preventDefault();
                  await api.deleteDoc(d.doc_id);
                  onDeleted();
                }}
                title="Remove"
              >
                ✕
              </button>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
