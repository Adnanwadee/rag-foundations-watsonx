# Consolidated Project Plan And Implementation Map

## Purpose

Build a grounded RAG assistant over a synthetic five-policy corpus. The assistant must answer only from retrieved local policy text, return citations, refuse unsupported questions, and produce three tone variants for answerable outputs.

## Scope

The final repository preserves the validated implementation and curated evidence. It does not regenerate embeddings, prompts, saved model outputs, labels, or final metrics.

## Work Breakdown

| Workstream | Status | Evidence |
| --- | --- | --- |
| Corpus v2.1 loading | Complete | `data/documents_v2_1/`, `data/manifest_v2_1.json` |
| Chunking and selected index | Complete | `data/evaluation/phase_c/retrieval/indexes/chunk-220-overlap-40/` |
| Grounded generation | Complete | `src/rag_foundations/grounded_generation.py`, `src/rag_foundations/frozen_v2_runtime.py` |
| Tone transformation | Complete | `src/rag_foundations/tone_transformation.py`, `prompts/v2/tones/` |
| Final evaluation | Complete | `data/evaluation/final_v2/` |
| Independent owner signoff | Not complete | Final metrics set `independent_human_signoff` to `false`. |

## Risks And Mitigations

| Risk | Mitigation |
| --- | --- |
| Retrieval misses a required source | Use Top-5 retrieval and report Hit@k/MRR. |
| Generated answer includes unsupported claims | Enforce citation validation and canonical refusal for unsupported cases. |
| Tone rewrite changes facts | Use protected-elements inputs, few-shot examples, strict JSON, and final tone adjudication. |
| Live model reruns mutate evidence | Keep Final v2 outputs and metrics saved; validation uses offline files. |
