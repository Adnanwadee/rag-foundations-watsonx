"""Explicit byte-integrity hashing helpers."""

from __future__ import annotations

import hashlib
from pathlib import Path


BINARY_SUFFIXES = {
    ".index",
    ".faiss",
    ".npy",
    ".npz",
    ".pkl",
    ".joblib",
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
}


def raw_sha256_file(path: Path | str) -> str:
    """Return SHA-256 over the exact bytes stored at path."""

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_text_bytes(data: bytes) -> bytes:
    """Normalize CRLF and bare CR newlines to LF for text-hash comparison."""

    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_sha256_file(path: Path | str) -> str:
    """Return SHA-256 over canonical repository bytes.

    Text files are newline-normalized for cross-platform manifests. Known binary artifacts use
    exact raw bytes and are never passed through text normalization.
    """

    p = Path(path)
    data = p.read_bytes()
    if p.suffix.lower() in BINARY_SUFFIXES:
        return hashlib.sha256(data).hexdigest()
    return hashlib.sha256(canonical_text_bytes(data)).hexdigest()
