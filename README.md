# Senior New England Common Interest Counsel

A high-level legal research and strategy agent for law firms practicing condominium and common-interest community law across New England.

## Jurisdiction Coverage

| State | Primary Statute |
|---|---|
| Massachusetts | M.G.L. c. 183A |
| Connecticut | CT CIOA, Title 47 |
| Rhode Island | RIGL § 34-36.1 |
| New Hampshire | NH RSA 356-B |
| Vermont | 27A V.S.A. |
| Maine | 33 M.R.S. Ch. 31 |

## Features

- **Operational Jurisdictional Gate** — The agent asks for the state before providing any substantive analysis; it never cross-pollinates statutes between states.
- **Document Intake** — Paste or upload a governing-document PDF; the agent scans for Conflict Clauses, Ultra Vires provisions, and Sunset Clauses.
- **Statutory Retrieval** — For any cited section the agent gives the Literal Interpretation and the Practitioner's Reality (how courts actually rule).
- **Case Law Reasoning** — Uses the Distinction Method: it explains both why a case applies *and* why opposing counsel might argue it does not.
- **Strategic Argumentation** — Every dispute receives a Theory of the Case, a Pro-Association argument, and a Pro-Unit Owner argument.
- **Logical Constraints** — No hallucinations (`Authority Not Found` instead of fabricated citations), mandatory bracketed citations, hierarchy of authority enforced (Statute → Declaration → Bylaws → Rules & Regs), zero hedging language.

## Project Structure

```
.
├── agent.py          # Core agent class, system prompt, jurisdiction detection, PDF helpers
├── app.py            # Flask web UI (streaming chat, PDF upload)
├── main.py           # Interactive CLI
├── requirements.txt  # Python dependencies
└── tests/
    └── test_agent.py # Pytest suite (39 tests)
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your OpenAI API key

```bash
export OPENAI_API_KEY="sk-..."
```

### 3a. Run the web interface

```bash
python app.py
# Open http://localhost:5000
```

### 3b. Run the CLI

```bash
python main.py
# Optionally pre-load a governing document:
python main.py --pdf /path/to/declaration.pdf
# Use a different model:
python main.py --model gpt-4o-mini
```

## CLI Commands

| Command | Description |
|---|---|
| `/pdf <path>` | Load a governing-document PDF (used in the next message) |
| `/reset` | Clear conversation history and confirmed jurisdiction |
| `/jurisdiction` | Display the currently confirmed jurisdiction |
| `/history` | Show the number of messages in the current conversation |
| `/quit` or `/exit` | Exit the CLI |

## Example Session

```
You: I represent the association. A unit owner in our complex has not paid assessments
     for eight months. We are in Massachusetts.

Counsel:
**Jurisdiction Confirmed**: Massachusetts

**Legal Issue**: Collection of unpaid common expense assessments; super-lien priority.

**Hierarchy Analysis**:
1. State Statute — M.G.L. c. 183A § 6 governs the association's lien for unpaid
   common expenses...
...
**Likely Judicial Outcome**: The likely judicial outcome is that the association holds
a valid super-priority lien for six months of unpaid common expenses [M.G.L. c. 183A § 6(c)]...
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `FLASK_SECRET_KEY` | No | random | Flask session secret (set in production) |
| `FLASK_DEBUG` | No | `0` | Set to `1` to enable Flask debug mode |
| `PORT` | No | `5000` | Port for the web interface |

## Running Tests

```bash
pytest tests/ -v
```

## Architecture Notes

- **`agent.py`** exports `CondoLawAgent`, `detect_jurisdiction`, `extract_pdf_text`, and the `SYSTEM_PROMPT` constant. The agent class wraps the OpenAI chat-completion API with conversation history management and streaming support.
- **`app.py`** provides a Flask web application with Server-Sent Events streaming, per-session agent instances, and a self-contained single-file HTML/CSS/JS UI — no external JavaScript framework required.
- **`main.py`** provides a readline-compatible CLI with built-in slash commands.
- Temperature is deliberately set to `0.2` for deterministic, professional legal output.
