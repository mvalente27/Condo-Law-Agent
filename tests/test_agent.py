"""
Tests for the Senior New England Common Interest Counsel agent.
================================================================
Run with:  pytest tests/
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch

import pytest

from agent import (
    SYSTEM_PROMPT,
    CondoLawAgent,
    detect_jurisdiction,
    extract_pdf_text,
)


# ---------------------------------------------------------------------------
# detect_jurisdiction tests
# ---------------------------------------------------------------------------


class TestDetectJurisdiction:
    def test_massachusetts_abbrev(self):
        assert detect_jurisdiction("This is a MA condo case.") == "Massachusetts"

    def test_massachusetts_statute(self):
        assert detect_jurisdiction("Per M.G.L. c. 183A § 10, the lien is valid.") == "Massachusetts"

    def test_connecticut_full(self):
        assert detect_jurisdiction("Connecticut CIOA Title 47 applies here.") == "Connecticut"

    def test_connecticut_abbrev(self):
        assert detect_jurisdiction("CT super lien case.") == "Connecticut"

    def test_rhode_island(self):
        assert detect_jurisdiction("Under RIGL § 34-36.1 the owner failed to pay.") == "Rhode Island"

    def test_new_hampshire(self):
        assert detect_jurisdiction("NH RSA 356-B governs this HOA.") == "New Hampshire"

    def test_vermont(self):
        assert detect_jurisdiction("Vermont 27A V.S.A. section 3-116.") == "Vermont"

    def test_maine(self):
        assert detect_jurisdiction("Maine 33 M.R.S. Ch. 31 applies.") == "Maine"

    def test_no_jurisdiction(self):
        assert detect_jurisdiction("The unit owner failed to pay assessments.") is None

    def test_empty_string(self):
        assert detect_jurisdiction("") is None

    def test_none_input(self):
        assert detect_jurisdiction(None) is None  # type: ignore[arg-type]

    def test_ambiguous_returns_none(self):
        # Two states detected — should return None (ambiguous)
        result = detect_jurisdiction("MA case but CT CIOA also mentioned.")
        assert result is None

    def test_case_insensitive_state(self):
        # "vermont" lowercase
        assert detect_jurisdiction("vermont law applies here.") == "Vermont"


# ---------------------------------------------------------------------------
# System prompt content tests
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    def test_jurisdictions_listed(self):
        for state_ref in ["183A", "CIOA", "34-36.1", "356-B", "27A V.S.A.", "33 M.R.S."]:
            assert state_ref in SYSTEM_PROMPT, f"Expected '{state_ref}' in system prompt"

    def test_jurisdictional_gate_present(self):
        assert "JURISDICTIONAL GATE" in SYSTEM_PROMPT.upper() or "Jurisdictional Gate" in SYSTEM_PROMPT

    def test_no_hallucination_rule(self):
        assert "Authority Not Found" in SYSTEM_PROMPT

    def test_hierarchy_of_authority(self):
        assert "State Statute" in SYSTEM_PROMPT
        assert "Master Deed" in SYSTEM_PROMPT or "Declaration" in SYSTEM_PROMPT
        assert "Bylaws" in SYSTEM_PROMPT

    def test_pro_association_and_pro_owner(self):
        assert "Pro-Association" in SYSTEM_PROMPT
        assert "Pro-Unit Owner" in SYSTEM_PROMPT

    def test_no_cross_contamination_rule(self):
        assert "cross-pollinate" in SYSTEM_PROMPT.lower() or "cross_pollinate" in SYSTEM_PROMPT.lower()

    def test_mandatory_citation_rule(self):
        assert "MANDATORY CITATION" in SYSTEM_PROMPT or "mandatory citation" in SYSTEM_PROMPT.lower()

    def test_strategic_argumentation(self):
        assert "Theory of the Case" in SYSTEM_PROMPT

    def test_distinction_method(self):
        assert "Distinction Method" in SYSTEM_PROMPT

    def test_hierarchy_ordered(self):
        """Statute must appear before Declaration which must appear before Bylaws."""
        statute_pos = SYSTEM_PROMPT.index("State Statute")
        declaration_pos = SYSTEM_PROMPT.index("Declaration")
        bylaws_pos = SYSTEM_PROMPT.index("Bylaws")
        assert statute_pos < declaration_pos < bylaws_pos


# ---------------------------------------------------------------------------
# CondoLawAgent unit tests (mocked OpenAI client)
# ---------------------------------------------------------------------------


def _make_mock_response(content: str) -> MagicMock:
    """Build a fake openai ChatCompletion response."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = content
    return mock


def _make_mock_stream_response(chunks: list[str]):
    """Build a fake streaming response iterator."""
    mock_chunks = []
    for text in chunks:
        c = MagicMock()
        c.choices = [MagicMock()]
        c.choices[0].delta.content = text
        mock_chunks.append(c)

    # Context manager that yields chunks
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=iter(mock_chunks))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestCondoLawAgent:
    @patch("agent.openai.OpenAI")
    def test_init_default_model(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        agent = CondoLawAgent(api_key="test-key")
        assert agent.model == "gpt-4o"

    @patch("agent.openai.OpenAI")
    def test_init_custom_model(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        agent = CondoLawAgent(api_key="test-key", model="gpt-4o-mini")
        assert agent.model == "gpt-4o-mini"

    @patch("agent.openai.OpenAI")
    def test_history_empty_on_init(self, mock_openai_cls):
        mock_openai_cls.return_value = MagicMock()
        agent = CondoLawAgent(api_key="test-key")
        assert agent.history == []

    @patch("agent.openai.OpenAI")
    def test_chat_appends_history(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response(
            "Before I can analyze, please confirm state jurisdiction."
        )

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("Unit owner is not paying assessments.")

        assert len(agent.history) == 2  # user + assistant
        assert agent.history[0]["role"] == "user"
        assert agent.history[1]["role"] == "assistant"

    @patch("agent.openai.OpenAI")
    def test_chat_includes_system_prompt(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("reply")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("test message")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages") or (
            call_args.args[0] if call_args.args else call_args.kwargs["messages"]
        )
        system_messages = [m for m in messages if m["role"] == "system"]
        assert len(system_messages) == 1
        assert system_messages[0]["content"] == SYSTEM_PROMPT

    @patch("agent.openai.OpenAI")
    def test_document_text_prepended(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("reply")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("Scan for conflicts.", document_text="ARTICLE I: The board has absolute power.")

        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs.get("messages") or call_args.kwargs["messages"]
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "GOVERNING DOCUMENT TEXT START" in user_msg["content"]
        assert "ARTICLE I: The board has absolute power." in user_msg["content"]
        assert "Scan for conflicts." in user_msg["content"]

    @patch("agent.openai.OpenAI")
    def test_reset_clears_history(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("reply")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("MA condo dispute.")
        assert len(agent.history) == 2

        agent.reset()
        assert agent.history == []
        assert agent.confirmed_jurisdiction is None

    @patch("agent.openai.OpenAI")
    def test_jurisdiction_detected_from_message(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("reply")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("In Massachusetts, under M.G.L. c. 183A, the super lien applies.")
        assert agent.confirmed_jurisdiction == "Massachusetts"

    @patch("agent.openai.OpenAI")
    def test_jurisdiction_none_when_absent(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("reply")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("The unit owner refuses to pay.")
        assert agent.confirmed_jurisdiction is None

    @patch("agent.openai.OpenAI")
    def test_jurisdiction_detected_from_document_text(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("reply")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat(
            "Please scan for conflicts.",
            document_text="This declaration is governed by RIGL § 34-36.1.",
        )
        assert agent.confirmed_jurisdiction == "Rhode Island"

    @patch("agent.openai.OpenAI")
    def test_stream_returns_iterator(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_stream_response(
            ["Hello", " from", " counsel."]
        )

        agent = CondoLawAgent(api_key="test-key")
        result = agent.chat("NH RSA 356-B question.", stream=True)

        # Should be an iterator, not a string
        import types
        assert isinstance(result, types.GeneratorType)

        chunks = list(result)
        assert chunks == ["Hello", " from", " counsel."]

    @patch("agent.openai.OpenAI")
    def test_stream_appends_history(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_stream_response(
            ["Jurisdiction", " confirmed."]
        )

        agent = CondoLawAgent(api_key="test-key")
        list(agent.chat("Vermont condo question.", stream=True))

        assert len(agent.history) == 2
        assert agent.history[1]["content"] == "Jurisdiction confirmed."

    @patch("agent.openai.OpenAI")
    def test_multiple_turns_accumulate_history(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("ok")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("MA condo question 1.")
        agent.chat("Follow up question.")
        agent.chat("Third question.")

        assert len(agent.history) == 6  # 3 user + 3 assistant

    @patch("agent.openai.OpenAI")
    def test_temperature_is_low(self, mock_openai_cls):
        """Low temperature ensures deterministic, professional legal responses."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_mock_response("reply")

        agent = CondoLawAgent(api_key="test-key")
        agent.chat("CT CIOA question.")

        call_args = mock_client.chat.completions.create.call_args
        temp = call_args.kwargs.get("temperature")
        assert temp is not None and temp <= 0.3


# ---------------------------------------------------------------------------
# extract_pdf_text tests
# ---------------------------------------------------------------------------


class TestExtractPdfText:
    def test_missing_pypdf_raises_runtime_error(self, tmp_path):
        """If pypdf is not installed, a helpful RuntimeError is raised."""
        dummy_pdf = tmp_path / "test.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 fake content")

        with patch.dict("sys.modules", {"pypdf": None}):
            with pytest.raises(RuntimeError, match="pypdf"):
                extract_pdf_text(str(dummy_pdf))

    def test_invalid_file_raises_runtime_error(self, tmp_path):
        """A corrupt/non-PDF file should raise RuntimeError."""
        bad_file = tmp_path / "bad.pdf"
        bad_file.write_bytes(b"this is not a pdf")

        with pytest.raises(RuntimeError):
            extract_pdf_text(str(bad_file))
