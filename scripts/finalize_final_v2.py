"""Finalize Final v2 after human adjudication is supplied."""

from __future__ import annotations

import json

from rag_foundations.final_v2 import compute_scores, validate_final_v2, validate_human_adjudication


if __name__ == "__main__":
    validate_human_adjudication()
    scores = compute_scores()
    validate_final_v2(require_human=True)
    print(json.dumps(scores, indent=2, sort_keys=True))
