"""Create the Final v2 human review packet from saved evidence."""

from __future__ import annotations

import json

from rag_foundations.final_v2 import prepare_human_review


if __name__ == "__main__":
    print(json.dumps(prepare_human_review(), indent=2, sort_keys=True))
