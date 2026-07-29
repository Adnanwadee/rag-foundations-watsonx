"""Validate project completion evidence."""

from __future__ import annotations

import json

from rag_foundations.final_v2 import validate_project_complete
from validate_documentation import validate_documentation
from validate_references import validate_references


if __name__ == "__main__":
    validate_documentation()
    validate_references()
    print(json.dumps(validate_project_complete(), indent=2, sort_keys=True))
