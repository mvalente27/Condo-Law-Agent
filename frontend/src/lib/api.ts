export type StateCode = "MA" | "CT" | "RI" | "NH" | "VT" | "ME";

export const STATES: { code: StateCode; name: string }[] = [
  { code: "MA", name: "Massachusetts" },
  { code: "CT", name: "Connecticut" },
  { code: "RI", name: "Rhode Island" },
  { code: "NH", name: "New Hampshire" },
  { code: "VT", name: "Vermont" },
  { code: "ME", name: "Maine" },
];

export interface DocumentSummary {
  doc_id: string;
  filename: string;
  state: string | null;
  pages: number;
  chunks: number;
  ocr_pages: number;
}

export interface Citation {
  doc_id: string;
  filename: string;
  page_start: number;
  page_end: number;
  score: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ConflictFinding {
  clause: string;
  issue: string;
  statute_or_case: string | null;
  severity: "low" | "medium" | "high" | string;
}

// Static GH Pages build → must point at a hosted backend.
// Local dev → defaults to http://localhost:8000.
const BACKEND =
  (process.env.NEXT_PUBLIC_BACKEND_URL || "").replace(/\/+$/, "") ||
  (typeof window !== "undefined" && window.location.hostname === "localhost"
    ? "http://localhost:8000"
    : "");

const url = (p: string) => `${BACKEND}${p}`;

async function jsonOrThrow<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${r.status}: ${text || r.statusText}`);
  }
  return (await r.json()) as T;
}

export const api = {
  backendConfigured: () => Boolean(BACKEND),
  backendUrl: () => BACKEND,
  health: () => fetch(url("/api/health")).then(jsonOrThrow<Record<string, unknown>>),
  listDocs: () => fetch(url("/api/documents")).then(jsonOrThrow<DocumentSummary[]>),
  deleteDoc: (id: string) =>
    fetch(url(`/api/documents/${id}`), { method: "DELETE" }).then(
      jsonOrThrow<{ deleted: boolean }>,
    ),
  upload: async (file: File, state: StateCode | "") => {
    const fd = new FormData();
    fd.append("file", file);
    if (state) fd.append("state", state);
    const r = await fetch(url("/api/documents/upload"), { method: "POST", body: fd });
    return jsonOrThrow<DocumentSummary>(r);
  },
  chat: (body: {
    state: StateCode | "";
    doc_ids: string[];
    messages: ChatMessage[];
  }) =>
    fetch(url("/api/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(jsonOrThrow<{ answer: string; citations: Citation[] }>),
  conflicts: async (state: StateCode, docId: string) => {
    const fd = new FormData();
    fd.append("state", state);
    fd.append("doc_id", docId);
    const r = await fetch(url("/api/conflict-detector"), { method: "POST", body: fd });
    return jsonOrThrow<ConflictFinding[]>(r);
  },
  caseTheory: (body: {
    state: StateCode;
    matter_summary: string;
    county?: string;
    doc_ids: string[];
  }) =>
    fetch(url("/api/case-theory"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(jsonOrThrow<{ theory: string }>),
};
