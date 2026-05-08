# Condo Law Agent

Custom dashboard for **Senior New England Common Interest Counsel** —
state-aware (MA, CT, RI, NH, VT, ME) Document RAG over Master Deeds,
Declarations, Bylaws, and Rules, powered by the **xAI** Chat Completions API.

## Architecture

```
┌──────────────────────┐    ┌────────────────────────┐    ┌────────────────┐
│ Frontend (Next.js)   │ ─► │ Middleware (FastAPI)   │ ─► │ xAI API        │
│ - State switcher     │    │ - PDF + OCR ingest     │    │ Grok-2 / 3     │
│ - Upload PDFs        │    │ - Anonymization        │    │ ZDR header on  │
│ - Chat / Conflict /  │    │ - Token chunking       │    └────────────────┘
│   Case-Theory tabs   │    │ - TF-IDF RAG retrieval │
└──────────────────────┘    │ - Statute linkifier    │
                            └────────────────────────┘
```

## Privacy & Security

- **Zero Data Retention** — `x-zero-data-retention: true` header sent on every
  xAI request. Configurable via `XAI_ZERO_DATA_RETENTION`.
- **Anonymization Layer** — heuristics strip emails, phones, street addresses,
  unit numbers, ZIPs, and conservative person-name patterns *before* any text
  leaves the middleware. See `backend/app/anonymizer.py`.
- **In-process index only** — uploaded documents stay in middleware memory and
  are never persisted to disk by default. Restart clears state.
- **No cross-pollination of state law** — enforced by system prompt.

> This is firm tooling, not a substitute for counsel review. Add disk
> encryption, SSO, and audit logging before production deployment.

## Modules

| Module | Endpoint | Purpose |
| --- | --- | --- |
| Statute Linker | applied to all answers | Hyperlinks `MGL c.183A § X`, `CGS § 47-X`, `RIGL § 34-36.1-X`, `RSA 356-B:X`, `27A VSA § X-X`, `33 MRS § X` to official sites. |
| Conflict Detector | `POST /api/conflict-detector` | Flags clauses conflicting with the active state's Condominium Act / case law (e.g., "absolute discretion"). |
| Case Theory Generator | `POST /api/case-theory` | "3 strongest precedents to defeat a Motion to Dismiss in this county." |

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env   # set XAI_API_KEY
docker compose up --build
```

- Frontend: http://localhost:3000
- API:      http://localhost:8000/api/health

## Quick start (local dev)

Backend:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit XAI_API_KEY
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

`/api/*` from the frontend is rewritten to `BACKEND_URL` (default
`http://localhost:8000`).

## System Prompt (V3)

The active prompt lives in `backend/app/prompts.py`. Edit there to tune role,
operational rules, hierarchy of law, workflow, and banned actions.

## Roadmap

- Persistent vector store (pgvector / Qdrant) with per-firm encryption.
- Per-state case law evaluation set with hallucination guardrails.
- SSO + audit log + per-matter access scopes.
- Streaming chat responses.
