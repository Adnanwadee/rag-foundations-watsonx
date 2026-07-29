# RAG Foundations

CLI-first retrieval-augmented generation project for Asteron policy questions. The application loads the local Corpus v2.1 policy set, retrieves from the frozen `data/evaluation/phase_c/retrieval/indexes/chunk-220-overlap-40/` FAISS index, generates grounded answers with citations, refuses unsupported questions, and can transform answer tone into formal, casual, and concise executive styles.

Final v2 is complete and reproducible from saved evidence. Scoring uses hybrid final scoring: tool-assisted semantic adjudication plus deterministic-clean labels. Independent owner signoff is not complete.

## Repository Map

| Path | Purpose |
| --- | --- |
| `src/rag_foundations/` | Runtime package, CLI, retrieval, generation, tone transformation, schemas, and validation helpers. |
| `data/documents_v2_1/` | Five-policy Corpus v2.1 source set. |
| `data/evaluation/phase_c/retrieval/indexes/chunk-220-overlap-40/` | Selected FAISS index, metadata, and index config. |
| `prompts/v2/` | Selected Candidate A grounded prompt, selected tone prompts, few-shot examples, and output schemas. |
| `data/evaluation/final_v2/` | Final questions, tone inputs, retrieval, saved outputs, metrics, comparison, manifests, and adjudication evidence. |
| `data/evaluation/experiments/` | Compact experiment summaries and score artifacts. |
| `docs/` | Supervisor-facing project documentation. |
| `scripts/` | Final validation and Final v2 helper scripts. |

## Setup

Use Python 3.11.

```powershell
python -m pip install -e ".[dev]"
```

Runtime watsonx.ai credentials are read from environment variables. The ordinary validation commands below do not make external model calls.

## CLI

```powershell
python -m rag_foundations.cli --help
python -m rag_foundations.cli ask --help
python -m rag_foundations.cli ask "What receipt threshold applies to expense documentation?"
```

Live answering requires valid watsonx.ai configuration. Final evidence validation and dry-run checks use saved files only.

## Validation

```powershell
python -m compileall src scripts
python -m ruff check src scripts tests
python -m pytest -q
python scripts/validate_documentation.py
python scripts/validate_corpus_v2_1.py
python scripts/validate_final_v2.py
python scripts/validate_project_complete.py
python -m rag_foundations.cli --help
python -m rag_foundations.cli ask --help
python scripts/run_final_v2.py --dry-run
```

## Final v2 Metrics

| Area | IBM Granite 4 Small | Mistral Small 3.1 24B |
| --- | ---: | ---: |
| Grounded correct answerable | 17/20 | 16/20 |
| Unsupported refusals correct | 3/4 | 4/4 |
| Strict grounded accuracy | 0.8333 | 0.8333 |
| Fully valid tone triplets | 8/20 | 9/20 |
| Distinct tone triplets | 16/20 | 20/20 |

Retrieval metrics: Hit@1 `0.95`, Hit@3 `1.0`, Hit@5 `1.0`, MRR `0.975`.

## Acceptance Matrix

| Criterion | Status | Evidence |
| --- | --- | --- |
| >=70% grounded correctness | PASS | Granite achieved 17/20 answerable correct and 0.8333 strict grounded accuracy. |
| Document + section citation | PASS | Citation validation and local citation resolution are covered by saved outputs and tests. |
| Clear unsupported refusal | PARTIAL | Granite refused 3/4 unsupported questions; Mistral refused 4/4. |
| Three distinct recognizable tones | PARTIAL | Granite produced 16/20 distinct triplets; Mistral produced 20/20. |
| Structured tone output + few-shot | PASS | Selected tone prompts use structured JSON and three few-shot examples per tone. |
| Malformed-output handling | PASS | Grounded and tone paths parse strict JSON and allow one bounded repair retry. |
| >=3 documented experiments | PASS | Chunking, prompt, tone, and model comparison evidence is documented in `docs/EXPERIMENTS.md`. |
| Evaluation report with retrieval, >=3 failures, 20 tone inputs, and model comparison | PASS | `docs/FINAL_REPORT.md` ties metrics to retained Final v2 evidence. |

## Documentation

- `docs/PROJECT_PLAN.md`
- `docs/DESIGN_DECISIONS.md`
- `docs/ARCHITECTURE.md`
- `docs/PROMPT_DESIGN.md`
- `docs/EXPERIMENTS.md`
- `docs/EVALUATION_METHOD.md`
- `docs/FINAL_REPORT.md`
- `docs/EVIDENCE_INDEX.md`
- `docs/PROJECT_REQUIREMENTS.md`
