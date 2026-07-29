"""Recompute deterministic Final v2 scores from saved evidence."""

from __future__ import annotations

import json

from rag_foundations.final_v2 import compute_scores


if __name__ == "__main__":
    print(json.dumps(compute_scores(), indent=2, sort_keys=True))
