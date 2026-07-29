from __future__ import annotations

import hashlib

from rag_foundations.integrity import canonical_sha256_file, canonical_text_bytes, raw_sha256_file


def test_canonical_text_bytes_normalizes_lf_crlf_and_bare_cr() -> None:
    assert canonical_text_bytes(b"one\ntwo\n") == b"one\ntwo\n"
    assert canonical_text_bytes(b"one\r\ntwo\r\n") == b"one\ntwo\n"
    assert canonical_text_bytes(b"one\rtwo\r") == b"one\ntwo\n"


def test_canonical_text_bytes_preserves_utf8_content() -> None:
    text = "policy: مراجعة\r\n"
    assert canonical_text_bytes(text.encode("utf-8")) == "policy: مراجعة\n".encode("utf-8")


def test_raw_hash_differs_but_canonical_hash_matches_newline_variants(tmp_path) -> None:
    lf = tmp_path / "lf.json"
    crlf = tmp_path / "crlf.json"
    lf.write_bytes(b"{\n  \"ok\": true\n}\n")
    crlf.write_bytes(b"{\r\n  \"ok\": true\r\n}\r\n")

    assert raw_sha256_file(lf) != raw_sha256_file(crlf)
    assert canonical_sha256_file(lf) == canonical_sha256_file(crlf)


def test_binary_suffix_uses_raw_bytes(tmp_path) -> None:
    binary = tmp_path / "vectors.index"
    binary.write_bytes(b"\x00\r\n\xff\rdata")

    assert canonical_sha256_file(binary) == hashlib.sha256(binary.read_bytes()).hexdigest()
