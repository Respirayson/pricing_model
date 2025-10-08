"""Ingestion pipeline for processing source documents."""

from .loader import iter_docs
from .text_extractor import extract_text
from .chunker import chunk_text

__all__ = ["iter_docs", "extract_text", "chunk_text"]
