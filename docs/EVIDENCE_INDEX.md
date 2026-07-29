# Evidence Index

## Active Runtime Assets

| Path | Purpose | Status | Used by |
| --- | --- | --- | --- |
| `data/documents_v2_1/` | Synthetic corpus source files | frozen | runtime, validation, documentation |
| `data/manifest_v2_1.json` | Document manifest and checksums | frozen | validation |
| `data/corpus_fact_registry_v2_1.json` | Curated fact registry | frozen | evaluation documentation |
| `data/indexes/selected/` | Selected FAISS binary, metadata, and config | frozen | runtime, validation |
| `data/manifests/frozen/` | Runtime, prompt, and index manifests | frozen | runtime, validation |
| `prompts/v2/` | Grounded, tone, few-shot, and schema assets | frozen | runtime, validation |

## Final Evaluation Evidence

| Path | Purpose | Status | Used by |
| --- | --- | --- | --- |
| `data/evaluation/final_v2/final_questions_v2.json` | Final grounded dataset | frozen | validation, documentation |
| `data/evaluation/final_v2/final_tone_inputs_v2.json` | Final tone dataset | frozen | validation, documentation |
| `data/evaluation/final_v2/retrieval_results.json` | Saved retrieval results with sanitized path metadata | sanitized metadata | validation, documentation |
| `data/evaluation/final_v2/grounded_results.jsonl` | Raw grounded model outputs and application outputs | raw model output | validation, scoring |
| `data/evaluation/final_v2/tone_results.jsonl` | Raw tone model outputs | raw model output | validation, scoring |
| `data/evaluation/final_v2/human_review/owner_adjudication.json` | Manual owner verification decisions | owner-reviewed | scoring, validation, documentation |
| `data/evaluation/final_v2/scoring/deterministic_scores.json` | Deterministic score layer | deterministic score | validation |
| `data/evaluation/final_v2/scoring/final_metrics.json` | Final owner-verified metrics | deterministic score, owner-reviewed | validation, documentation |
| `data/evaluation/final_v2/scoring/model_comparison.json` | Granite/Mistral comparison | deterministic score, owner-reviewed | validation, documentation |
| `data/evaluation/final_v2/manifests/artifact_manifest.json` | Hashes for retained Final v2 evidence | frozen | validation |
| `data/evaluation/final_v2/manifests/protected_hashes.json` | Protected corpus, prompt, index, and manifest hashes | frozen | runtime, validation |
| `data/evaluation/final_v2/manifests/rendered_requests.json` | Reconstructed request provenance | reconstructed provenance | validation |

## Experiment Summaries

| Path | Purpose | Status | Used by |
| --- | --- | --- | --- |
| `data/evaluation/experiments/retrieval_chunking_comparison.json` | Chunking and retrieval comparison | experiment summary | documentation |
| `data/evaluation/experiments/grounded_prompt_comparison.json` | Candidate A/B/C prompt comparison | experiment summary | documentation |
| `data/evaluation/experiments/tone_prompt_comparison.json` | Tone prompt comparison | experiment summary | documentation |
| `data/evaluation/experiments/model_comparison.json` | Final v2 model comparison summary | experiment summary | documentation |

## Validators And Tests

| Path | Purpose | Status | Used by |
| --- | --- | --- | --- |
| `scripts/validate_documentation.py` | Documentation validation | active | CI |
| `scripts/validate_references.py` | JSON, path, residue, and credential checks | active | CI |
| `scripts/validate_corpus_v2_1.py` | Corpus validation | active | CI |
| `scripts/validate_final_v2.py` | Final v2 validation | active | CI |
| `scripts/validate_project_complete.py` | Combined validation | active | CI |

## Dataset Disclosure

The dataset is synthetic. See `docs/DATASET_CARD.md` for intended use, limitations, and privacy boundaries.
