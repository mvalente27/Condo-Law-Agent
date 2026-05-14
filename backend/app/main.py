from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .anonymizer import anonymize
from .chunker import chunk_pages
from .config import Settings, get_settings
from .pdf_ingest import extract_pdf
from .prompts import CASE_THEORY_PROMPT, CONFLICT_DETECTOR_PROMPT, build_system_prompt
from .retriever import DocumentIndex, store
from .statute_linker import linkify
from .xai_client import XAIError, chat_completion

app = FastAPI(title="Condo Law Agent API", version="0.1.0")

_settings = get_settings()
_origins = [o.strip() for o in _settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SUPPORTED_STATES = {"MA", "CT", "RI", "NH", "VT", "ME"}


def _validate_state(state: str | None) -> str | None:
    if state is None or state == "":
        return None
    s = state.upper()
    if s not in SUPPORTED_STATES:
        raise HTTPException(400, f"Unsupported state '{state}'. Use one of {sorted(SUPPORTED_STATES)}.")
    return s


# ---------- Schemas ----------


class DocumentSummary(BaseModel):
    doc_id: str
    filename: str
    state: str | None
    pages: int
    chunks: int
    ocr_pages: int


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    state: str | None = None
    doc_ids: list[str] = []
    messages: list[ChatMessage]
    top_k: int | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]] = []


class ConflictFinding(BaseModel):
    clause: str
    issue: str
    statute_or_case: str | None = None
    severity: str


class CaseTheoryRequest(BaseModel):
    state: str
    matter_summary: str
    county: str | None = None
    doc_ids: list[str] = []


# ---------- Endpoints ----------


@app.get("/api/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    return {
        "status": "ok",
        "model": settings.xai_model,
        "zdr": settings.xai_zero_data_retention,
        "xai_configured": bool(settings.xai_api_key),
        "supported_states": sorted(SUPPORTED_STATES),
    }


@app.get("/api/documents", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    out: list[DocumentSummary] = []
    for d in store.list():
        out.append(
            DocumentSummary(
                doc_id=d.doc_id,
                filename=d.filename,
                state=d.state,
                pages=(d.chunks[-1].page_end if d.chunks else 0),
                chunks=len(d.chunks),
                ocr_pages=0,
            )
        )
    return out


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str) -> dict[str, bool]:
    return {"deleted": store.remove(doc_id)}


@app.post("/api/documents/upload", response_model=DocumentSummary)
async def upload_document(
    file: UploadFile = File(...),
    state: str | None = Form(default=None),
    settings: Settings = Depends(get_settings),
) -> DocumentSummary:
    state_v = _validate_state(state)
    if file.content_type not in {"application/pdf", "application/octet-stream"} and not (
        file.filename or ""
    ).lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF uploads are supported.")

    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit.")

    pages = extract_pdf(data)
    # Anonymize before indexing so retrieval text never carries PII.
    for p in pages:
        p.text = anonymize(p.text)

    doc_id = uuid.uuid4().hex[:12]
    chunks = chunk_pages(
        pages,
        doc_id=doc_id,
        chunk_tokens=settings.chunk_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    index = DocumentIndex(
        doc_id=doc_id,
        filename=file.filename or "document.pdf",
        state=state_v,
        chunks=chunks,
    )
    store.add(index)
    return DocumentSummary(
        doc_id=doc_id,
        filename=index.filename,
        state=state_v,
        pages=pages[-1].page if pages else 0,
        chunks=len(chunks),
        ocr_pages=sum(1 for p in pages if p.ocr_used),
    )


def _gather_context(
    doc_ids: list[str], query: str, top_k: int
) -> tuple[str, list[dict[str, Any]]]:
    parts: list[str] = []
    citations: list[dict[str, Any]] = []
    for did in doc_ids:
        idx = store.get(did)
        if not idx:
            continue
        for hit in idx.search(query, top_k=top_k):
            tag = f"[{idx.filename} p.{hit.chunk.page_start}-{hit.chunk.page_end}]"
            parts.append(f"{tag}\n{hit.chunk.text}")
            citations.append(
                {
                    "doc_id": idx.doc_id,
                    "filename": idx.filename,
                    "page_start": hit.chunk.page_start,
                    "page_end": hit.chunk.page_end,
                    "score": hit.score,
                }
            )
    return ("\n\n---\n\n".join(parts), citations)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, settings: Settings = Depends(get_settings)) -> ChatResponse:
    state_v = _validate_state(req.state)
    if not req.messages:
        raise HTTPException(400, "messages must not be empty")

    last_user = next(
        (m.content for m in reversed(req.messages) if m.role == "user"), ""
    )
    top_k = req.top_k or settings.top_k
    context, citations = _gather_context(req.doc_ids, last_user, top_k)

    system = build_system_prompt(state_v)
    if context:
        system += (
            "\n\n### DOCUMENT CONTEXT (anonymized excerpts)\n"
            "Cite excerpts by their bracketed [filename p.X-Y] tags when used.\n\n"
            + context
        )

    messages = [{"role": "system", "content": system}]
    for m in req.messages:
        messages.append({"role": m.role, "content": anonymize(m.content)})

    try:
        answer = await chat_completion(messages)
    except XAIError as e:
        raise HTTPException(502, str(e))

    return ChatResponse(answer=linkify(answer, state_v), citations=citations)


@app.post("/api/conflict-detector", response_model=list[ConflictFinding])
async def conflict_detector(
    state: str = Form(...),
    doc_id: str = Form(...),
    settings: Settings = Depends(get_settings),
) -> list[ConflictFinding]:
    state_v = _validate_state(state)
    idx = store.get(doc_id)
    if not idx:
        raise HTTPException(
            404,
            "Document not found on the server. The backend may have restarted "
            "(free-tier instances reset on idle/redeploy). Please re-upload the file.",
        )

    # Use targeted retrieval against red-flag language.
    probe = (
        "absolute discretion sole discretion waiver fiduciary indemnify "
        "super lien priority restraint on alienation amendment supermajority"
    )
    context, _ = _gather_context([doc_id], probe, top_k=settings.top_k * 2)
    system = build_system_prompt(state_v) + "\n\n" + CONFLICT_DETECTOR_PROMPT
    user = f"ACTIVE STATE: {state_v}\n\nGOVERNING DOCUMENT EXCERPTS:\n{context}"

    try:
        raw = await chat_completion(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.0,
            max_tokens=6000,
            response_format={"type": "json_object"},
        )
    except XAIError as e:
        raise HTTPException(502, str(e))

    findings = _parse_findings(raw)
    if not findings and raw.strip():
        # Retry once without JSON mode; some models are flaky in JSON mode.
        try:
            raw = await chat_completion(
                [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": user
                        + "\n\nReturn ONLY a JSON array. No prose, no code fences.",
                    },
                ],
                temperature=0.0,
                max_tokens=6000,
            )
            findings = _parse_findings(raw)
        except XAIError:
            pass
    if not findings:
        # Surface raw model output so the user/operator can see what happened
        # instead of getting an empty list silently.
        snippet = (raw or "").strip()[:500] or "<empty model response>"
        raise HTTPException(
            502,
            f"Conflict scan returned no parseable findings. Model output: {snippet}",
        )
    return [ConflictFinding(**f) for f in findings]


def _parse_findings(raw: str) -> list[dict[str, Any]]:
    raw = raw.strip()
    # Accept either a JSON array or an object wrapping one.
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to recover an array slice.
        start, end = raw.find("["), raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                return []
        else:
            return []

    if isinstance(data, dict):
        for key in ("findings", "results", "items", "data"):
            if key in data and isinstance(data[key], list):
                data = data[key]
                break
        else:
            data = [data]
    if not isinstance(data, list):
        return []

    cleaned: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        cleaned.append(
            {
                "clause": str(item.get("clause", ""))[:500],
                "issue": str(item.get("issue", "")),
                "statute_or_case": item.get("statute_or_case") or None,
                "severity": str(item.get("severity", "medium")).lower(),
            }
        )
    return cleaned


@app.post("/api/case-theory")
async def case_theory(req: CaseTheoryRequest) -> dict[str, str]:
    state_v = _validate_state(req.state)
    settings = get_settings()
    context, _ = _gather_context(req.doc_ids, req.matter_summary, top_k=settings.top_k)
    system = build_system_prompt(state_v) + "\n\n" + CASE_THEORY_PROMPT
    user = (
        f"ACTIVE STATE: {state_v}\n"
        f"COUNTY: {req.county or 'N/A'}\n\n"
        f"MATTER SUMMARY (anonymized):\n{anonymize(req.matter_summary)}\n\n"
        + (f"DOCUMENT EXCERPTS:\n{context}" if context else "")
    )
    try:
        raw = await chat_completion(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=4000,
        )
    except XAIError as e:
        raise HTTPException(502, str(e))
    if not raw or not raw.strip():
        raise HTTPException(
            502, "Case theory returned an empty response. Try again or shorten the matter summary."
        )
    return {"theory": linkify(raw, state_v)}
