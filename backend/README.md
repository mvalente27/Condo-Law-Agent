# Backend — Condo Law Agent

FastAPI middleware: PDF ingest + OCR, anonymization, token chunking,
in-memory TF-IDF RAG, xAI Chat Completions client (with ZDR header),
statute linkifier, and conflict / case-theory endpoints.

## Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit XAI_API_KEY
uvicorn app.main:app --reload
```

System packages required for OCR: `tesseract-ocr`, `poppler-utils`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health + config flags |
| POST | `/api/documents/upload` (multipart: `file`, `state`) | Ingest PDF (OCR fallback) |
| GET | `/api/documents` | List indexed docs |
| DELETE | `/api/documents/{doc_id}` | Drop a doc from memory |
| POST | `/api/chat` | RAG chat (state-aware) |
| POST | `/api/conflict-detector` (form: `state`, `doc_id`) | Flag clauses conflicting with state law |
| POST | `/api/case-theory` | Generate 3 strongest precedents to defeat MTD |

Anonymization strips emails, phones, addresses, unit numbers, ZIPs,
and a conservative person-name heuristic *before* text leaves the
service. Documents are held in-process only; restart clears state.
