"""Validate frozen Final v2 artifacts and saved execution evidence."""

from __future__ import annotations

import json

from rag_foundations.final_v2 import validate_final_v2


if __name__ == "__main__":
    print(json.dumps(validate_final_v2(), indent=2, sort_keys=True))
