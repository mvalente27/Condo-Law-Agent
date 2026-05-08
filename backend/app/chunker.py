"""Token-aware chunking with page metadata."""
from __future__ import annotations

from dataclasses import dataclass

import tiktoken

from .pdf_ingest import PageText

_ENC = tiktoken.get_encoding("cl100k_base")


@dataclass
class Chunk:
    id: str
    text: str
    page_start: int
    page_end: int
    token_count: int


def _tokenize(text: str) -> list[int]:
    return _ENC.encode(text, disallowed_special=())


def _detokenize(tokens: list[int]) -> str:
    return _ENC.decode(tokens)


def chunk_pages(
    pages: list[PageText],
    doc_id: str,
    chunk_tokens: int,
    overlap_tokens: int,
) -> list[Chunk]:
    # Build a token stream with page boundaries.
    token_stream: list[int] = []
    page_marks: list[int] = []  # page number for each token index
    for p in pages:
        toks = _tokenize(p.text)
        token_stream.extend(toks)
        page_marks.extend([p.page] * len(toks))

    chunks: list[Chunk] = []
    if not token_stream:
        return chunks

    step = max(1, chunk_tokens - overlap_tokens)
    idx = 0
    n = 0
    while idx < len(token_stream):
        end = min(idx + chunk_tokens, len(token_stream))
        toks = token_stream[idx:end]
        text = _detokenize(toks).strip()
        if text:
            chunks.append(
                Chunk(
                    id=f"{doc_id}:{n}",
                    text=text,
                    page_start=page_marks[idx],
                    page_end=page_marks[end - 1],
                    token_count=len(toks),
                )
            )
            n += 1
        if end == len(token_stream):
            break
        idx += step
    return chunks
