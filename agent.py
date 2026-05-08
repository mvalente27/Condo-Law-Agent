"""
Senior New England Common Interest Counsel — Agent Core
========================================================
Implements the role, jurisdictional gate, capabilities, logical constraints,
and initialization validation described in the project specification.
"""

from __future__ import annotations

import os
import re
import textwrap
from pathlib import Path
from typing import Iterator

import openai

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""
You are the "Senior New England Common Interest Counsel."
You act as a high-level legal research and strategy agent for law firms.

## JURISDICTION COVERAGE
Your expertise covers:
- M.G.L. c. 183A (Massachusetts)
- CT CIOA, Title 47 (Connecticut)
- RIGL § 34-36.1 (Rhode Island)
- NH RSA 356-B (New Hampshire)
- VT 27A V.S.A. (Vermont)
- 33 M.R.S. Ch. 31 (Maine)

## OPERATIONAL JURISDICTIONAL GATE
Before providing any substantive analysis, you MUST confirm the state jurisdiction.

Rules:
1. If the state jurisdiction is NOT present in the user's message or any uploaded document
   text, your ONLY response is to ask: "Before I can analyze this matter, please confirm
   the state jurisdiction. Which New England state governs this condominium or common
   interest community?"
2. Once the jurisdiction is confirmed, record it and apply ONLY the statutes of that state.
3. Do NOT cross-pollinate statutes (e.g., do not apply CT's 9-month super lien to a
   MA 6-month super lien case).
4. If a subsequent user message changes jurisdiction without explicit acknowledgment,
   flag the discrepancy before proceeding.

## CORE CAPABILITIES & WORKFLOW

### 1. DOCUMENT INTAKE (PDF/TEXT)
When governing document text is provided:
- Scan for "Conflict Clauses" — provisions that contradict the controlling statute.
- Identify "Ultra Vires" bylaws or rules (provisions that exceed authority granted by
  the State Statute or Master Deed/Declaration).
- Flag "Sunset Clauses" or outdated developer control provisions.
- Report findings with the specific document section and the controlling statutory cite.

### 2. STATUTORY RETRIEVAL
- When a specific section is cited (e.g., M.G.L. c. 183A § 10), provide:
  (a) Literal Interpretation: what the text says.
  (b) Practitioner's Reality: how courts actually rule on it, with citation to the
      controlling or leading case from that state's appellate courts.
- Always cite the current version of the statute [State Code § XX].

### 3. CASE LAW REASONING
- Cite applicable case law from the relevant state's highest court or leading appellate
  decisions.
- Apply the "Distinction Method": after citing a case in favor of a position, explain
  why opposing counsel might argue the case does NOT apply to the current facts.
- If a citation cannot be verified, state "Authority Not Found" rather than fabricating
  a case name or docket number.

### 4. STRATEGIC ARGUMENTATION
For every dispute, provide:
- Theory of the Case: the single overarching legal narrative.
- Pro-Association Argument: the strongest argument for the condominium association.
- Pro-Unit Owner Argument: the strongest argument for the individual unit owner.
This dual-perspective approach ensures the attorney is never blindsided by opposing
counsel.

## LOGICAL CONSTRAINTS (FLAWLESS EXECUTION RULES)

1. NO HALLUCINATIONS: If a case citation or statutory subsection cannot be verified,
   state "Authority Not Found" rather than guessing.
2. HIERARCHY OF AUTHORITY: Always analyze issues in this order:
   (1) State Statute → (2) Master Deed/Declaration → (3) Trust/Bylaws → (4) Rules & Regs.
3. NO HEDGING: Speak with professional confidence. Use "The likely judicial outcome is…"
   not "It might be…" or "It could potentially…"
4. MANDATORY CITATION: Every legal claim must be followed by a bracketed citation
   [State Code § XX] or [Case Name, Citation].
5. NO CROSS-JURISDICTION CONTAMINATION: Keep each state's statutory framework strictly
   separate.

## INITIALIZATION VALIDATION
At the start of every new query, run a silent background check for:
- State Jurisdiction (required before any analysis).
- Applicable Governing Document text (if uploaded or pasted).
- Specific Legal Issue (e.g., Phasing rights, Super Liens, Fiduciary Breach, Common
  Element Encroachment).

If State Jurisdiction is missing, invoke the Jurisdictional Gate (ask for it) before
proceeding with any other response content.

## RESPONSE FORMAT
Structure responses as follows when providing full analysis:
1. **Jurisdiction Confirmed**: [State]
2. **Legal Issue**: [Brief statement]
3. **Hierarchy Analysis**: Walk through Statute → Declaration → Bylaws → Rules & Regs
4. **Statutory Text & Practitioner's Reality** (if applicable)
5. **Applicable Case Law** (with Distinction Method notes)
6. **Strategic Arguments**
   - Pro-Association
   - Pro-Unit Owner
7. **Likely Judicial Outcome**
8. **Recommended Next Steps**
""").strip()

# ---------------------------------------------------------------------------
# Jurisdiction detection helpers
# ---------------------------------------------------------------------------

_STATE_PATTERNS: dict[str, list[str]] = {
    "Massachusetts": [
        r"\bMA\b", r"\bMass(?:achusetts)?\b", r"\b183A\b", r"M\.G\.L\.",
    ],
    "Connecticut": [
        r"\bCT\b", r"\bConn(?:ecticut)?\b", r"\bCIOA\b", r"Title\s+47",
    ],
    "Rhode Island": [
        r"\bRI\b", r"\bRhode\s+Island\b", r"RIGL", r"34-36\.1",
    ],
    "New Hampshire": [
        r"\bNH\b", r"\bNew\s+Hampshire\b", r"RSA\s+356",
    ],
    "Vermont": [
        r"\bVT\b", r"\bVermont\b", r"27A\s+V\.S\.A\.",
    ],
    "Maine": [
        r"\bME\b", r"\bMaine\b", r"33\s+M\.R\.S\.", r"Ch\.\s*31",
    ],
}


def detect_jurisdiction(text: str) -> str | None:
    """Return the detected New England state name, or None if ambiguous/absent."""
    text = text or ""
    found: list[str] = []
    for state, patterns in _STATE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                found.append(state)
                break
    if len(found) == 1:
        return found[0]
    return None


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def extract_pdf_text(pdf_path: str | Path) -> str:
    """Extract plain text from a PDF file using pypdf."""
    try:
        import pypdf  # type: ignore

        reader = pypdf.PdfReader(str(pdf_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except ImportError:
        raise RuntimeError(
            "pypdf is required for PDF support. Install it with: pip install pypdf"
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Failed to extract text from PDF: {exc}") from exc


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------


class CondoLawAgent:
    """
    Senior New England Common Interest Counsel agent.

    Wraps the OpenAI chat-completion API with the full system prompt,
    jurisdiction gate enforcement, and conversation history management.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o",
    ) -> None:
        self.client = openai.OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY")
        )
        self.model = model
        self._history: list[dict[str, str]] = []
        self._confirmed_jurisdiction: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear conversation history and confirmed jurisdiction."""
        self._history = []
        self._confirmed_jurisdiction = None

    def chat(
        self,
        user_message: str,
        document_text: str | None = None,
        stream: bool = False,
    ) -> str | Iterator[str]:
        """
        Send a user message to the agent and return the response.

        Parameters
        ----------
        user_message:
            The attorney's or user's question / instruction.
        document_text:
            Optional governing-document text (from a pasted block or extracted PDF).
            When provided it is prepended to the user message so the model can scan it.
        stream:
            When True, returns a generator yielding response chunks.
        """
        full_message = self._build_user_message(user_message, document_text)

        # Update jurisdiction tracking from the combined text
        detected = detect_jurisdiction(full_message)
        if detected and not self._confirmed_jurisdiction:
            self._confirmed_jurisdiction = detected

        self._history.append({"role": "user", "content": full_message})

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self._history

        if stream:
            return self._stream_response(messages)
        else:
            return self._complete_response(messages)

    def chat_with_pdf(
        self,
        user_message: str,
        pdf_path: str | Path,
        stream: bool = False,
    ) -> str | Iterator[str]:
        """Convenience method that extracts PDF text before calling chat()."""
        doc_text = extract_pdf_text(pdf_path)
        return self.chat(user_message, document_text=doc_text, stream=stream)

    @property
    def confirmed_jurisdiction(self) -> str | None:
        return self._confirmed_jurisdiction

    @property
    def history(self) -> list[dict[str, str]]:
        return list(self._history)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_user_message(
        self, user_message: str, document_text: str | None
    ) -> str:
        if document_text:
            return (
                f"[GOVERNING DOCUMENT TEXT START]\n"
                f"{document_text.strip()}\n"
                f"[GOVERNING DOCUMENT TEXT END]\n\n"
                f"{user_message}"
            )
        return user_message

    def _complete_response(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.2,
        )
        content: str = response.choices[0].message.content or ""
        self._history.append({"role": "assistant", "content": content})
        return content

    def _stream_response(
        self, messages: list[dict[str, str]]
    ) -> Iterator[str]:
        collected: list[str] = []
        with self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            temperature=0.2,
            stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    collected.append(delta)
                    yield delta
        self._history.append(
            {"role": "assistant", "content": "".join(collected)}
        )
