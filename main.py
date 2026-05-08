"""
Senior New England Common Interest Counsel — CLI Entry Point
=============================================================
Interactive command-line interface for the Condo Law Agent.

Usage
-----
    python main.py
    python main.py --model gpt-4o-mini
    python main.py --pdf /path/to/declaration.pdf

Environment
-----------
    OPENAI_API_KEY  Required.  Your OpenAI API key.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from agent import CondoLawAgent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BANNER = r"""
╔══════════════════════════════════════════════════════════════════╗
║   Senior New England Common Interest Counsel                     ║
║   Legal Research & Strategy Agent                                ║
║   Jurisdictions: MA · CT · RI · NH · VT · ME                    ║
╠══════════════════════════════════════════════════════════════════╣
║  Commands:                                                       ║
║    /pdf <path>   — load a governing-document PDF                 ║
║    /reset        — clear conversation history                    ║
║    /jurisdiction — display confirmed jurisdiction                ║
║    /history      — display conversation history length           ║
║    /quit  or  /exit                                              ║
╚══════════════════════════════════════════════════════════════════╝
"""


def _require_api_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY environment variable is not set.\n"
            "Export your key before running:\n"
            "  export OPENAI_API_KEY='sk-...'\n",
            file=sys.stderr,
        )
        sys.exit(1)


def _stream_print(agent: CondoLawAgent, message: str, doc_text: str | None = None) -> None:
    """Print the agent response token-by-token with streaming."""
    print("\nCounsel: ", end="", flush=True)
    for chunk in agent.chat(message, document_text=doc_text, stream=True):  # type: ignore[union-attr]
        print(chunk, end="", flush=True)
    print("\n")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run_cli(model: str, initial_pdf: Path | None) -> None:
    _require_api_key()

    agent = CondoLawAgent(model=model)
    print(BANNER)

    pending_doc_text: str | None = None

    # Pre-load PDF if provided on the command line
    if initial_pdf:
        print(f"Loading PDF: {initial_pdf} …", flush=True)
        try:
            from agent import extract_pdf_text

            pending_doc_text = extract_pdf_text(initial_pdf)
            print(f"  ✓ Extracted {len(pending_doc_text):,} characters from document.\n")
        except RuntimeError as exc:
            print(f"  ✗ {exc}\n", file=sys.stderr)

    # Greet
    print("You: ", end="", flush=True)

    while True:
        try:
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            print("You: ", end="", flush=True)
            continue

        # ── Built-in commands ──────────────────────────────────────────
        if user_input.lower() in ("/quit", "/exit"):
            print("Goodbye.")
            break

        if user_input.lower() == "/reset":
            agent.reset()
            pending_doc_text = None
            print("  [Conversation reset.]\n")
            print("You: ", end="", flush=True)
            continue

        if user_input.lower() == "/jurisdiction":
            jur = agent.confirmed_jurisdiction or "Not yet confirmed"
            print(f"  [Confirmed jurisdiction: {jur}]\n")
            print("You: ", end="", flush=True)
            continue

        if user_input.lower() == "/history":
            turns = len(agent.history)
            print(f"  [Conversation history: {turns} message(s)]\n")
            print("You: ", end="", flush=True)
            continue

        if user_input.lower().startswith("/pdf "):
            pdf_path = Path(user_input[5:].strip())
            if not pdf_path.exists():
                print(f"  ✗ File not found: {pdf_path}\n", file=sys.stderr)
            else:
                print(f"  Loading PDF: {pdf_path} …", flush=True)
                try:
                    from agent import extract_pdf_text

                    pending_doc_text = extract_pdf_text(pdf_path)
                    print(
                        f"  ✓ Extracted {len(pending_doc_text):,} characters. "
                        f"The document will be included in your next message.\n"
                    )
                except RuntimeError as exc:
                    print(f"  ✗ {exc}\n", file=sys.stderr)
            print("You: ", end="", flush=True)
            continue

        # ── Normal message ─────────────────────────────────────────────
        doc_for_this_turn = pending_doc_text
        pending_doc_text = None  # consume once

        try:
            _stream_print(agent, user_input, doc_text=doc_for_this_turn)
        except Exception as exc:  # noqa: BLE001
            print(f"\n  ✗ API error: {exc}\n", file=sys.stderr)

        print("You: ", end="", flush=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Senior New England Common Interest Counsel — CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="OpenAI model name (default: gpt-4o)",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        default=None,
        metavar="FILE",
        help="Governing-document PDF to pre-load",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_cli(model=args.model, initial_pdf=args.pdf)
