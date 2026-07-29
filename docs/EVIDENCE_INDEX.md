# Evidence Index

## Active Runtime Assets

| Path | Contents |
| --- | --- |
| `data/documents_v2_1/` | Corpus v2.1 policy documents. |
| `data/manifest_v2_1.json` | Corpus manifest. |
| `data/corpus_fact_registry_v2_1.json` | Fact registry used for dataset construction and validation. |
| `data/evaluation/phase_c/retrieval/indexes/chunk-220-overlap-40/` | Selected FAISS index, metadata, and config. |
| `data/evaluation/phase_c/frozen/` | Frozen configuration, selected prompt manifest, selected index manifest, and frozen metrics. |
| `prompts/v2/grounded/` | Selected Candidate A grounded prompts. |
| `prompts/v2/tones/` | Selected tone prompts. |
| `prompts/v2/few_shot/` | Selected few-shot examples. |
| `prompts/v2/schemas/` | Retained output schemas. |

## Final Evidence

| Path | Contents |
| --- | --- |
| `data/evaluation/final_v2/final_questions_v2.json` | Final 24 grounded questions. |
| `data/evaluation/final_v2/final_tone_inputs_v2.json` | Final 20 tone inputs. |
| `data/evaluation/final_v2/retrieval_results.json` | Retrieved contexts. |
| `data/evaluation/final_v2/grounded_results.jsonl` | Saved grounded outputs. |
| `data/evaluation/final_v2/tone_results.jsonl` | Saved tone outputs. |
| `data/evaluation/final_v2/scoring/final_metrics.json` | Final metrics. |
| `data/evaluation/final_v2/scoring/model_comparison.json` | Final model comparison. |
| `data/evaluation/final_v2/scoring/failure_analysis.md` | Failure analysis. |
| `data/evaluation/final_v2/manifests/` | Run, artifact, protected-hash, model-selection, and rendered-request manifests. |
| `data/evaluation/final_v2/human_review/review_packet.json` | Compact review packet. |
| `data/evaluation/final_v2/human_review/human_adjudication.json` | Tool-assisted semantic adjudication labels. |

## Compact Experiment Evidence

| Path | Contents |
| --- | --- |
| `data/evaluation/experiments/experiment_comparison_v1.json` | Controlled experiment comparison summary. |
| `data/evaluation/experiments/experiment_comparison_v1.md` | Human-readable experiment summary. |
| `data/evaluation/experiments/exp-01-prompt-completeness/` | Prompt experiment manifest, score, and review. |
| `data/evaluation/experiments/exp-02-smaller-chunks/` | Chunk-size experiment manifest, score, and review. |
| `data/evaluation/experiments/exp-03-increased-overlap/` | Overlap experiment manifest, score, and review. |

## Validators And Tests

| Path | Purpose |
| --- | --- |
| `scripts/validate_documentation.py` | Public documentation and metric consistency. |
| `scripts/validate_corpus_v2_1.py` | Corpus v2.1 validation. |
| `scripts/validate_final_v2.py` | Final v2 artifact validation. |
| `scripts/validate_project_complete.py` | End-to-end completion gate. |
| `tests/` | Focused offline test suite. |
