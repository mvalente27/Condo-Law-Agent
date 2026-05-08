"use client";
import { useState } from "react";

export default function HelpHint({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-block">
      <button
        type="button"
        aria-label={`Help: ${title}`}
        onClick={() => setOpen((v) => !v)}
        onBlur={() => setOpen(false)}
        className="ml-2 inline-flex h-4 w-4 items-center justify-center rounded-full border border-border text-[10px] text-slate-300 hover:border-accent hover:text-accent"
      >
        ?
      </button>
      {open && (
        <span className="absolute left-6 top-0 z-20 w-72 rounded-md border border-border bg-ink p-3 text-xs text-slate-200 shadow-xl">
          <span className="block font-semibold mb-1">{title}</span>
          <span className="block leading-relaxed">{children}</span>
        </span>
      )}
    </span>
  );
}
