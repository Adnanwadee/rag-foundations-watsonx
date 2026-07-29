"""Validate Corpus v2.1 and its curated fact registry."""

from __future__ import annotations

from rag_foundations.corpus_v2_1 import validate_corpus_v2_1


def main() -> int:
    result = validate_corpus_v2_1()
    for key, value in result.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
