# Dataset Card

## Dataset Identity

Name: Asteron Policies Corpus v2.1. The dataset contains five fictional Markdown policy documents for a fictional organization. It is a fully synthetic controlled benchmark with 60 sections and 70 deterministic chunks under the selected 220/40 configuration. It contains no personal, confidential, or real-company policy data.

## Intended Use

The corpus supports RAG ingestion and retrieval testing, grounding and citation testing, unsupported-question evaluation, multi-source and chunk-boundary testing, and tone-transformation inputs.

## Construction Principles

The documents intentionally include repeated section patterns, controlled distractor clauses, aliases, rare marker tokens, similar headings across documents, and unsupported concepts. These features make retrieval evaluation harder and more measurable because similar chunks compete, facts can appear near chunk boundaries, multi-source questions require coverage, and unsupported questions test false-positive resistance.

## Limitations

The prose is benchmark-oriented rather than production-natural. The documents are not legal or operational guidance. Repeated distractors reduce readability. Results do not generalize automatically to scanned PDFs, OCR noise, or large production corpora. A production system would use curated real policies, permissions, document lifecycle controls, and re-indexing.

## Ethics And Privacy

There are no real employee records, real company policies, personal information, or confidential data. The corpus is not for real decisions.

## Links

Linked from `README.md`, `docs/PROJECT_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/EVALUATION_METHOD.md`, and `docs/EVIDENCE_INDEX.md`.
