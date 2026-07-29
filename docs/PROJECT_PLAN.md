# Consolidated Project Plan and Implementation Map

## Problem Statement

Build a small RAG assistant that answers questions only from supplied documents, cites document and section sources, refuses unsupported questions, and rewrites grounded answers in three distinct tones.

## Goals

Implement deterministic ingestion, section-aware chunking, FAISS retrieval, grounded JSON generation, citation resolution, tone transformation, saved-evidence evaluation, and a CLI. The dataset disclosure is in `docs/DATASET_CARD.md`.

## Scope

Scope includes the synthetic corpus, Watsonx embeddings, selected FAISS index, Granite primary generation, Mistral comparison, strict schemas, bounded repair, offline validation, and supervisor documentation.

## Non-Goals

No production permissions system, REST API, UI, OCR pipeline, latency benchmark, real policy dataset, `.env` creation, final environment setup, external calls in this pass, or GitHub push.

## Synthetic Dataset Rationale

A fictional controlled corpus avoids privacy risk and makes retrieval stress cases measurable through repeated patterns, distractors, aliases, rare markers, similar headings, and unsupported concepts.

## Milestone Mapping

| Original milestone | Implementation evidence |
| --- | --- |
| Understand the problem | `docs/DESIGN_DECISIONS.md`, `docs/PROMPT_DESIGN.md` |
| Build ingestion and retrieval | `src/rag_foundations/document_loader.py`, `src/rag_foundations/chunking.py`, `data/indexes/selected/` |
| Build grounded generation and first tone | `src/rag_foundations/grounded_generation.py`, `prompts/v2/grounded/`, `prompts/v2/tones/formal.system.txt` |
| Build remaining tones and structure output | `src/rag_foundations/tone_transformation.py`, `prompts/v2/tones/`, `prompts/v2/few_shot/` |
| Improve and iterate | `data/evaluation/experiments/`, `docs/EXPERIMENTS.md` |
| Evaluate, compare models, and reflect | `docs/FINAL_REPORT.md`, `data/evaluation/final_v2/scoring/` |

## Planned Architecture

Documents are validated, parsed into sections, chunked, embedded, stored in FAISS, retrieved with Top-5 search, passed to Candidate A, validated against JSON and citations, optionally rewritten by tone prompts, and emitted by the CLI.

## Evaluation Plan

Use 24 grounded questions, 20 answerable and 4 unsupported, plus 20 tone inputs. Score retrieval, grounded correctness, unsupported refusal, citations, schemas, factual preservation, language preservation, tone recognizability, and triplet distinctness.

## Fairness Controls

Granite and Mistral share corpus, index, retrieval, prompts, inputs, temperature, top_p, schemas, and rubric. No post-final prompt tuning is applied.

## Deliverables And Status

Corpus, manifest, fact registry, selected index, prompts, schemas, CLI, compact experiments, Final v2 saved outputs, owner verification, docs, and validators are complete. Live smoke testing remains pending local environment and `.env` setup.

## Risks And Mitigations

Hallucination is mitigated by context-only prompts and unsupported refusal. Retrieval miss is mitigated by Top-5. Multi-source incompleteness is reported. Citation fabrication is blocked by local citation resolution. Prompt brittleness and tone reliability remain limitations. Malformed JSON receives one repair retry. Credential exposure is mitigated by ignored `.env`. Evidence drift is mitigated by hashes. Model-version drift and synthetic-to-production generalization are disclosed.
