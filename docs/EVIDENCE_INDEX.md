# Evidence Index and Reviewer Verification Guide

## Project Information

| Item | Value |
| --- | --- |
| Project | Prompting & RAG Foundations |
| Platform | IBM watsonx.ai |
| Vector store | FAISS |
| Corpus | Asteron Policies Corpus v2.1 |
| Final interface | Command-line interface |
| Final grounded questions | 24 |
| Final tone inputs | 20 |
| Saved grounded results | 48 |
| Saved tone results | 120 |
| Automated tests | Complete suite passing |
| Evidence status | Frozen, validated, and owner-reviewed |

---

## 1. Purpose

This document maps every major project requirement to its supporting implementation, test, experiment, evaluation, and documentation evidence.

It is intended to help a reviewer answer five questions quickly:

1. **Where is the feature implemented?**
2. **Where is it tested?**
3. **Where is its configuration stored?**
4. **Where are its final results recorded?**
5. **How can it be verified without making external model calls?**

The repository retains both human-readable documentation and machine-readable evidence.

---

## 2. Evidence Model

The project separates evidence into several layers.

```text
Source documents and prompts
        ↓
Frozen runtime configuration
        ↓
Raw retrieval and model outputs
        ↓
Deterministic validation and scoring
        ↓
Human semantic review
        ↓
Separate manual owner verification
        ↓
Final metrics and reports
```

### Evidence layers

| Layer | Purpose | Main locations |
| --- | --- | --- |
| Source evidence | Corpus documents and registered facts | `data/documents_v2_1/`, `data/corpus_fact_registry_v2_1.json` |
| Runtime evidence | Selected prompts, index, and configuration | `prompts/v2/`, `data/indexes/selected/`, `data/manifests/frozen/` |
| Raw execution evidence | Saved retrieval and model outputs | `data/evaluation/final_v2/retrieval_results.json`, `grounded_results.jsonl`, `tone_results.jsonl` |
| Deterministic evidence | Schema, structure, retrieval, and rule-based scoring | `data/evaluation/final_v2/scoring/deterministic_scores.json` |
| Human review | Targeted semantic decisions | Final scoring records and failure analysis |
| Owner verification | Author-performed separate manual owner-verification pass | `data/evaluation/final_v2/human_review/owner_adjudication.json` |
| Final summary | Final metrics and comparison | `final_metrics.json`, `model_comparison.json`, `docs/FINAL_REPORT.md` |

The final manual owner-verification pass was performed by the project author, Adnan Wadee Abdullah. It was conducted separately from deterministic scoring, but it was not an external, blind, or independent third-party review. Frozen artifacts retain the field name `independent_owner_signoff` for compatibility with the finalized scoring schema; in this project, that field denotes a separate owner-verification pass rather than reviewer independence.

---

## 3. Recommended Reviewer Path

A reviewer can understand and verify the project in the following order:

1. Read [`README.md`](../README.md) for installation, architecture, commands, and headline results.
2. Read [`PROJECT_REQUIREMENTS.md`](PROJECT_REQUIREMENTS.md) for the original assignment.
3. Read [`FINAL_REPORT.md`](FINAL_REPORT.md) for implementation, experiments, results, and failure analysis.
4. Run the offline validation commands.
5. Inspect the machine-readable artifacts listed in this document.
6. Review [`LIVE_SMOKE_TEST.md`](LIVE_SMOKE_TEST.md) for live watsonx.ai operational evidence.

### Fast offline verification

```powershell
python -m pip check
python -m pytest -q

python scripts/validate_references.py
python scripts/validate_corpus_v2_1.py
python scripts/validate_final_v2.py
python scripts/validate_project_complete.py

python scripts/run_final_v2.py --dry-run
python scripts/build_watsonx_faiss_index.py --preflight-only
```

Expected high-level results:

```text
Dependencies:        No broken requirements
Tests:               complete automated test suite passes
Final-v2 dry-run:    external_calls=0
FAISS preflight:     External calls: 0
FAISS preflight:     Files written: 0
Project validators:  Pass
```

These commands do not require live Watsonx credentials.

---

## 4. Assignment Acceptance-Criteria Evidence

| Assignment criterion | Implementation evidence | Evaluation or test evidence | Status |
| --- | --- | --- | --- |
| Document ingestion | `src/rag_foundations/document_loader.py` | `tests/test_document_loading_chunking.py`, corpus validator | Complete |
| Document chunking | `src/rag_foundations/chunking.py` | chunking tests and experiment artifact | Complete |
| Watsonx embeddings | `src/rag_foundations/watsonx_embeddings.py` | `tests/test_watsonx_embeddings.py`, selected-index config | Complete |
| Vector storage | `src/rag_foundations/faiss_store.py` | `tests/test_faiss_store.py`, `data/indexes/selected/` | Complete |
| Top-K retrieval | `src/rag_foundations/frozen_v2_runtime.py` | `retrieval_results.json`, final metrics | Complete |
| Grounded generation | `src/rag_foundations/grounded_generation.py` | grounded results, scoring, live test | Complete |
| Document citation | `src/rag_foundations/schemas.py`, runtime citation resolution | grounded results and citation-validity metrics | Complete |
| Section citation | Retrieved chunk metadata and response schemas | final outputs and live smoke test | Complete |
| Unsupported refusal | Grounded prompt, canonical refusal, answerability schema | four unsupported final questions and live refusal test | Complete |
| Formal-report tone | Formal system/user prompts | tone results and final tone metrics | Complete |
| Casual-message tone | Casual system/user prompts | tone results and final tone metrics | Complete |
| Executive-briefing tone | Executive system/user prompts | tone results and final tone metrics | Complete |
| Few-shot examples | `prompts/v2/few_shot/` | prompt-asset tests | Complete |
| Structured JSON | JSON schemas and Pydantic models | schema tests and 120 structured tone outputs | Complete |
| Malformed-output handling | Structured-output parsing and bounded repair | grounded/tone tests | Complete |
| Simple interface | `src/rag_foundations/cli.py` | CLI tests and help smoke tests | Complete |
| At least three experiments | Four experiment artifacts | `docs/EXPERIMENTS.md` | Exceeded |
| At least 20 grounded questions | 24-question final dataset | final dataset manifest | Exceeded |
| At least three diagnosed failures | Final failure-analysis artifact | `docs/FINAL_REPORT.md` | Exceeded |
| Tone evaluation on 20 inputs | 20 frozen tone inputs | 120 saved tone outputs | Complete |
| Model comparison | Granite/Mistral controlled execution | final comparison artifacts | Complete |
| At least 70% performance | Strict grounded accuracy `0.8333` | `final_metrics.json` | Exceeded |

---

## 5. Corpus and Dataset Evidence

| Path | Purpose | Evidence status |
| --- | --- | --- |
| `data/documents_v2_1/` | Five synthetic policy source documents | Frozen source evidence |
| `data/manifest_v2_1.json` | Document IDs, titles, paths, and source checksums | Frozen |
| `data/corpus_fact_registry_v2_1.json` | Curated policy facts used to design and explain evaluation | Frozen |
| `docs/DATASET_CARD.md` | Dataset composition, intended use, difficulty design, and limitations | Human-readable documentation |
| `src/rag_foundations/corpus_v2_1.py` | Corpus constants and validation support | Active implementation |
| `scripts/validate_corpus_v2_1.py` | Corpus integrity and structure validation | Active validator |
| `tests/test_corpus.py` | Automated corpus regression coverage | Active test |

### Corpus summary

```text
Documents:          5
Sections:           60
Registered facts:   89
Selected vectors:   70
Corpus version:     asteron-policies-v2.1
```

---

## 6. Ingestion and Chunking Evidence

| Evidence type | Path |
| --- | --- |
| Document loading implementation | `src/rag_foundations/document_loader.py` |
| Chunking implementation | `src/rag_foundations/chunking.py` |
| Data schemas | `src/rag_foundations/schemas.py` |
| Manifest | `data/manifest_v2_1.json` |
| Selected chunk/index configuration | `data/indexes/selected/index_config.json` |
| Chunking comparison | `data/evaluation/experiments/retrieval_chunking_comparison.json` |
| Automated tests | `tests/test_document_loading_chunking.py` |
| Design explanation | `docs/DESIGN_DECISIONS.md` |
| Architecture explanation | `docs/ARCHITECTURE.md` |

### Selected chunking configuration

```text
Chunk size:     220 tokens
Chunk overlap:  40 tokens
```

The selected index contains equal vector and metadata counts:

```text
Vectors:          70
Metadata records: 70
```

---

## 7. Embedding and FAISS Evidence

| Evidence type | Path |
| --- | --- |
| Watsonx embedding integration | `src/rag_foundations/watsonx_embeddings.py` |
| FAISS persistence and search | `src/rag_foundations/faiss_store.py` |
| Watsonx model utilities | `src/rag_foundations/watsonx_models.py` |
| Selected FAISS binary | `data/indexes/selected/asteron_policies_watsonx.index` |
| Selected metadata | `data/indexes/selected/metadata.json` |
| Selected index configuration | `data/indexes/selected/index_config.json` |
| Frozen index manifest | `data/manifests/frozen/frozen_index_manifest_v2.json` |
| Builder and preflight | `scripts/build_watsonx_faiss_index.py` |
| FAISS tests | `tests/test_faiss_store.py` |
| Builder tests | `tests/test_build_watsonx_faiss_index.py` |

### Selected embedding configuration

| Field | Value |
| --- | --- |
| Model | `ibm/granite-embedding-278m-multilingual` |
| Dimension | 768 |
| Index type | FAISS `IndexFlatIP` |
| Similarity interpretation | Cosine similarity using normalized vectors |
| Selected index ID | `selected-chunk-220-overlap-40` |

### Read-only validation command

```powershell
python scripts/build_watsonx_faiss_index.py --preflight-only
```

This command verifies the tracked corpus and selected index with:

```text
External calls: 0
Files written: 0
```

---

## 8. Retrieval Evidence

| Evidence type | Path |
| --- | --- |
| Frozen runtime retrieval | `src/rag_foundations/frozen_v2_runtime.py` |
| Generic pipeline coordination | `src/rag_foundations/pipeline.py` |
| Saved final retrieval results | `data/evaluation/final_v2/retrieval_results.json` |
| Retrieval experiment | `data/evaluation/experiments/retrieval_chunking_comparison.json` |
| Final retrieval metrics | `data/evaluation/final_v2/scoring/final_metrics.json` |
| Runtime tests | `tests/test_frozen_v2_runtime.py` |
| Pipeline tests | `tests/test_pipeline.py` |

### Final retrieval results

| Metric | Value |
| --- | ---: |
| Hit@1 | `0.95` |
| Hit@3 | `1.00` |
| Hit@5 | `1.00` |
| Mean Reciprocal Rank | `0.975` |
| All-expected-source coverage@5 | `0.90` |

---

## 9. Grounded Prompt and Generation Evidence

| Evidence type | Path |
| --- | --- |
| Grounded generation implementation | `src/rag_foundations/grounded_generation.py` |
| Frozen runtime implementation | `src/rag_foundations/frozen_v2_runtime.py` |
| Selected grounded system prompt | `prompts/v2/grounded/candidate_a.system.txt` |
| Selected grounded user prompt | `prompts/v2/grounded/candidate_a.user.txt` |
| Grounded output schema | `prompts/v2/schemas/grounded_output.schema.json` |
| Frozen prompt manifest | `data/manifests/frozen/frozen_prompt_manifest_v2.json` |
| Grounded prompt experiment | `data/evaluation/experiments/grounded_prompt_comparison.json` |
| Saved grounded results | `data/evaluation/final_v2/grounded_results.jsonl` |
| Grounded-generation tests | `tests/test_grounded_generation.py` |
| Schema tests | `tests/test_schemas.py` |
| Prompt-design documentation | `docs/PROMPT_DESIGN.md` |

### Selected grounded prompt

```text
Candidate A
```

The prompt requires:

- context-only answers;
- an answerability decision;
- citation identifiers;
- structured JSON;
- a canonical unsupported refusal.

---

## 10. Citation Evidence

Grounded citations are created from retrieved chunk identifiers and resolved against local metadata.

A runtime citation can contain:

- `citation_id`;
- `chunk_id`;
- `document_id`;
- document title;
- section heading;
- source path;
- retrieved supporting excerpt;
- corpus version;
- index ID.

| Evidence type | Path |
| --- | --- |
| Response and citation schemas | `src/rag_foundations/schemas.py` |
| Runtime citation resolution | `src/rag_foundations/frozen_v2_runtime.py` |
| Saved grounded citations | `data/evaluation/final_v2/grounded_results.jsonl` |
| Citation scoring | `data/evaluation/final_v2/scoring/deterministic_scores.json` |
| Final citation metrics | `data/evaluation/final_v2/scoring/final_metrics.json` |
| Live citation example | `docs/LIVE_SMOKE_TEST.md` |
| Citation-related tests | `tests/test_frozen_v2_runtime.py`, `tests/test_grounded_generation.py` |

---

## 11. Unsupported-Question Evidence

| Evidence type | Path |
| --- | --- |
| Canonical refusal contract | Grounded prompt and runtime normalization |
| Unsupported final questions | `data/evaluation/final_v2/final_questions_v2.json` |
| Saved unsupported outputs | `data/evaluation/final_v2/grounded_results.jsonl` |
| Unsupported scoring | `data/evaluation/final_v2/scoring/final_metrics.json` |
| Near-match failure analysis | `data/evaluation/final_v2/scoring/failure_analysis.md` |
| Live unsupported test | `docs/LIVE_SMOKE_TEST.md` |
| Runtime and generation tests | `tests/test_frozen_v2_runtime.py`, `tests/test_grounded_generation.py` |

The final dataset contains:

```text
4 explicitly unsupported questions
```

The expected unsupported contract is:

```json
{
  "answer": "I don't know based on the provided documents.",
  "is_answerable": false,
  "citations": []
}
```

---

## 12. Tone-Prompt Evidence

### Tone assets

| Tone | System prompt | User prompt | Few-shot examples |
| --- | --- | --- | --- |
| Formal report summary | `prompts/v2/tones/formal.system.txt` | `prompts/v2/tones/formal.user.txt` | `prompts/v2/few_shot/formal.json` |
| Casual message | `prompts/v2/tones/casual.system.txt` | `prompts/v2/tones/casual.user.txt` | `prompts/v2/few_shot/casual.json` |
| Concise executive briefing | `prompts/v2/tones/executive.system.txt` | `prompts/v2/tones/executive.user.txt` | `prompts/v2/few_shot/executive.json` |

Each few-shot JSON file contains three examples.

### Tone implementation and evaluation

| Evidence type | Path |
| --- | --- |
| Tone transformation implementation | `src/rag_foundations/tone_transformation.py` |
| Tone schema | `prompts/v2/schemas/tone_output.schema.json` |
| Prompt loading and verification | `src/rag_foundations/prompt_assets.py` |
| Tone prompt experiment | `data/evaluation/experiments/tone_prompt_comparison.json` |
| Final tone inputs | `data/evaluation/final_v2/final_tone_inputs_v2.json` |
| Saved tone results | `data/evaluation/final_v2/tone_results.jsonl` |
| Tone scoring | `data/evaluation/final_v2/scoring/deterministic_scores.json` |
| Final tone metrics | `data/evaluation/final_v2/scoring/final_metrics.json` |
| Tone tests | `tests/test_tone_transformation.py` |
| Prompt-asset tests | `tests/test_prompt_assets_v2.py` |
| Live formal-tone test | `docs/LIVE_SMOKE_TEST.md` |

### Final tone dataset size

```text
20 inputs
× 3 tones
× 2 models
= 120 saved tone outputs
```

---

## 13. Structured-Output and Repair Evidence

| Evidence type | Path |
| --- | --- |
| Pydantic schemas | `src/rag_foundations/schemas.py` |
| Grounded JSON schema | `prompts/v2/schemas/grounded_output.schema.json` |
| Tone JSON schema | `prompts/v2/schemas/tone_output.schema.json` |
| Grounded validation and repair | `src/rag_foundations/grounded_generation.py` |
| Tone validation and repair | `src/rag_foundations/tone_transformation.py` |
| Frozen runtime validation | `src/rag_foundations/frozen_v2_runtime.py` |
| Error types | `src/rag_foundations/errors.py` |
| Grounded tests | `tests/test_grounded_generation.py` |
| Tone tests | `tests/test_tone_transformation.py` |
| Error tests | `tests/test_errors.py` |
| Schema tests | `tests/test_schemas.py` |

The retry policy is bounded:

```text
Maximum repair retries: 1
```

The saved final evaluation required zero repair retries, while automated tests exercise malformed-output behavior.

---

## 14. CLI and Runtime Evidence

| Evidence type | Path |
| --- | --- |
| CLI implementation | `src/rag_foundations/cli.py` |
| Frozen request runtime | `src/rag_foundations/frozen_v2_runtime.py` |
| Project configuration | `src/rag_foundations/config.py` |
| Constants | `src/rag_foundations/constants.py` |
| Project-only logging | `src/rag_foundations/logging_config.py` |
| CLI tests | `tests/test_cli.py` |
| Configuration tests | `tests/test_config.py` |
| Runtime tests | `tests/test_frozen_v2_runtime.py` |
| Usage guide | `README.md` |

### Supported interface modes

- grounded answer only;
- one selected tone;
- all three tones;
- human-readable terminal output;
- machine-readable JSON.

### CLI verification

```powershell
python -m rag_foundations.cli --help
python -m rag_foundations.cli ask --help
```

These commands work without Watsonx credentials and without creating live clients.

---

## 15. Experiment Evidence

The assignment requires at least three documented experiments. The repository includes four.

| Experiment | Artifact | Main purpose |
| --- | --- | --- |
| Retrieval and chunking | `data/evaluation/experiments/retrieval_chunking_comparison.json` | Compare chunk size and overlap |
| Grounded prompt | `data/evaluation/experiments/grounded_prompt_comparison.json` | Compare Candidate A, B, and C |
| Tone prompts | `data/evaluation/experiments/tone_prompt_comparison.json` | Compare baseline and protected alternate prompts |
| Generation model | `data/evaluation/experiments/model_comparison.json` | Compare Granite and Mistral with controlled variables |

Human-readable interpretation is provided in:

- [`EXPERIMENTS.md`](EXPERIMENTS.md);
- [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md);
- [`FINAL_REPORT.md`](FINAL_REPORT.md).

---

## 16. Final Dataset Evidence

| Path | Purpose |
| --- | --- |
| `data/evaluation/final_v2/final_dataset_manifest.json` | Dataset counts, hashes, and frozen state |
| `data/evaluation/final_v2/final_questions_v2.json` | 24 final grounded questions |
| `data/evaluation/final_v2/final_tone_inputs_v2.json` | 20 final tone inputs |
| `data/evaluation/final_v2/run_plan.json` | Frozen final execution plan |

### Grounded category counts

| Category | Count |
| --- | ---: |
| Direct fact | 5 |
| Condition or exception | 5 |
| Multi-fact | 5 |
| Multi-section or source | 5 |
| Unsupported | 4 |
| **Total** | **24** |

---

## 17. Raw Final Execution Evidence

| Path | Record purpose |
| --- | --- |
| `data/evaluation/final_v2/retrieval_results.json` | Saved Top-K retrieval results |
| `data/evaluation/final_v2/grounded_results.jsonl` | Raw and application-level grounded outputs for both models |
| `data/evaluation/final_v2/tone_results.jsonl` | Raw and application-level tone outputs |
| `data/evaluation/final_v2/manifests/execution_manifest.json` | Execution provenance |
| `data/evaluation/final_v2/manifests/rendered_requests.json` | Reconstructed request provenance |
| `data/evaluation/final_v2/manifests/model_selection_evidence.json` | Model-selection support |

The raw grounded and tone outputs were preserved rather than rewritten after scoring.

---

## 18. Scoring and Review Evidence

| Path | Purpose |
| --- | --- |
| `data/evaluation/final_v2/scoring/deterministic_scores.json` | Deterministic scoring layer |
| `data/evaluation/final_v2/human_review/owner_adjudication.json` | Owner verification |
| `data/evaluation/final_v2/scoring/final_metrics.json` | Final owner-verified metrics |
| `data/evaluation/final_v2/scoring/model_comparison.json` | Final model comparison |
| `data/evaluation/final_v2/scoring/failure_analysis.md` | Grounded and tone failure diagnosis |

### Review scope

```text
Grounded semantic decisions reviewed: 24
Model-level tone triplets reviewed:    40
Independent owner signoff:             Yes
Raw evidence mutated:                  No
```

---

## 19. Final Metric Evidence

The authoritative final metrics are stored in:

```text
data/evaluation/final_v2/scoring/final_metrics.json
```

### Grounded summary

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Answerable correct | `17/20` | `16/20` |
| Answerable partial | `2/20` | `4/20` |
| Unsupported correct | `3/4` | `4/4` |
| Citation-valid records | 20 | 19 |
| Strict overall accuracy | `0.8333` | `0.8333` |
| Repair count | 0 | 0 |

### Tone summary

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Fully valid triplets | `8/20` | `9/20` |
| Distinct triplets | `16/20` | `20/20` |
| Structurally valid outputs | `60/60` | `60/60` |

---

## 20. Failure-Analysis Evidence

The complete final failure analysis is stored at:

```text
data/evaluation/final_v2/scoring/failure_analysis.md
```

Representative diagnosed failure categories include:

- non-responsive grounded answer;
- unsupported near-match confusion;
- incomplete multi-source synthesis;
- omitted conditions or deadlines;
- tone factual-preservation errors;
- insufficient distinction between tone outputs.

The project preserves these failures as evaluation evidence and does not alter frozen prompts or outputs to conceal them.

---

## 21. Model-Comparison Evidence

Two related artifacts are retained.

| Path | Purpose |
| --- | --- |
| `data/evaluation/experiments/model_comparison.json` | Human-readable experiment summary and controlled-variable statement |
| `data/evaluation/final_v2/scoring/model_comparison.json` | Final owner-verified numerical comparison |

### Controlled variables

The model comparison held constant:

- corpus;
- selected index;
- Top-5 retrieval;
- embedding results;
- prompt assets;
- temperature;
- top-p;
- grounded questions;
- tone inputs;
- scoring rubric.

Only the generation model changed.

The comparison is described using a smaller nominal documented parameter count. No pricing claim is made because pricing evidence is not included in the frozen artifacts.

---

## 22. Frozen Configuration Evidence

| Path | Purpose |
| --- | --- |
| `data/manifests/frozen/frozen_configuration_v2.json` | Final runtime and generation configuration |
| `data/manifests/frozen/frozen_index_manifest_v2.json` | Selected-index identity and integrity |
| `data/manifests/frozen/frozen_prompt_manifest_v2.json` | Selected prompt asset identities |
| `data/evaluation/final_v2/manifests/protected_hashes.json` | Protected area and artifact hashes |
| `data/evaluation/final_v2/manifests/artifact_manifest.json` | Hashes for 16 retained Final-v2 artifacts |

The artifact manifest uses:

```text
SHA-256 over repository-canonical bytes
LF-normalized for text
raw bytes for binary artifacts
```

---

## 23. Live Operational Evidence

The live operational tests are documented in:

```text
docs/LIVE_SMOKE_TEST.md
```

They confirm:

- Watsonx authentication;
- live query embedding;
- FAISS Top-5 retrieval;
- correct supported answer;
- document and section citation;
- canonical unsupported refusal;
- empty citations for the unsupported question;
- formal tone execution;
- valid JSON;
- no repair retry in the recorded tests;
- local `.env` safety.

No secret values are retained in the report.

---

## 24. Test Evidence

### Test suite

The final project state passes:

```text
the complete automated test suite
```

### Main test files

| Test file | Main coverage |
| --- | --- |
| `tests/test_imports.py` | Package imports |
| `tests/test_config.py` | Settings and environment behavior |
| `tests/test_corpus.py` | Corpus definitions and validation |
| `tests/test_document_loading_chunking.py` | Loading and chunking |
| `tests/test_watsonx_embeddings.py` | Embedding adapters and validation |
| `tests/test_faiss_store.py` | FAISS persistence and retrieval |
| `tests/test_build_watsonx_faiss_index.py` | Builder entry point and offline preflight |
| `tests/test_prompt_assets_v2.py` | Prompt, schema, and few-shot assets |
| `tests/test_grounded_generation.py` | Grounded output, refusal, and repair |
| `tests/test_tone_transformation.py` | Tone behavior and malformed output |
| `tests/test_schemas.py` | Structured contracts |
| `tests/test_errors.py` | Error hierarchy and safe failure behavior |
| `tests/test_pipeline.py` | Generic end-to-end coordination |
| `tests/test_frozen_v2_runtime.py` | Frozen retrieval and generation runtime |
| `tests/test_final_v2.py` | Final execution, artifacts, and scoring |
| `tests/test_cli.py` | CLI, JSON stdout, logging, and tone selection |
| `tests/test_integrity.py` | Protected hash and integrity checks |
| `tests/test_validate_references.py` | Root `.env` exclusion and nested-file validation |

---

## 25. Validator Evidence

| Validator | Purpose |
| --- | --- |
| `scripts/validate_references.py` | Path, JSON/JSONL, credential-pattern, and residue checks |
| `scripts/validate_corpus_v2_1.py` | Corpus manifest, facts, documents, sections, and chunk preflight |
| `scripts/validate_final_v2.py` | Final datasets, results, scoring, manifests, and hashes |
| `scripts/validate_project_complete.py` | Combined submission-completeness gate |

### Additional offline scripts

| Script | Purpose |
| --- | --- |
| `scripts/run_final_v2.py --dry-run` | Validate the complete final execution plan with zero calls |
| `scripts/build_watsonx_faiss_index.py --preflight-only` | Validate corpus and selected index with zero calls and writes |
| `scripts/score_final_v2.py` | Final scoring support |

---

## 26. CI Evidence

The workflow is stored at:

```text
.github/workflows/ci.yml
```

The CI verifies:

- Python 3.11;
- dependency installation;
- compilation of `src`, `scripts`, and `tests`;
- Ruff across the repository;
- the complete Pytest suite;
- reference and project-completeness validation;
- reference validation;
- corpus validation;
- Final-v2 validation;
- project-completeness validation;
- CLI help;
- Final-v2 dry-run;
- FAISS read-only preflight;
- Git-archive isolation.

The workflow:

- requires no `.env`;
- requires no Watsonx credentials;
- makes no model calls;
- performs no Hugging Face downloads for the selected-index preflight;
- validates tracked repository content in isolation.

---

## 27. Security Evidence

| Security control | Evidence |
| --- | --- |
| `.env` ignored | `.gitignore` and `git check-ignore -v .env` |
| `.env` untracked | `git ls-files .env` produces no output |
| Safe template | `.env.example` |
| Root-only `.env` skip | `scripts/validate_references.py` |
| Nested `.env` remains scanned | `tests/test_validate_references.py` |
| Project-only logger | `src/rag_foundations/logging_config.py` |
| JSON isolated on stdout | `tests/test_cli.py` |
| No credential logging | logging tests and code review |
| Protected asset hashes | `protected_hashes.json` |
| Archive-isolated validation | `.github/workflows/ci.yml` |

---

## 28. Documentation Evidence

| Document | Purpose |
| --- | --- |
| [`README.md`](../README.md) | Installation, usage, architecture, results, and project entry point |
| [`PROJECT_REQUIREMENTS.md`](PROJECT_REQUIREMENTS.md) | Original assignment specification |
| [`PROJECT_PLAN.md`](PROJECT_PLAN.md) | Completed milestone and deliverable map |
| [`DATASET_CARD.md`](DATASET_CARD.md) | Dataset design and limitations |
| [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md) | Selection rationale |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Component boundaries and runtime flow |
| [`PROMPT_DESIGN.md`](PROMPT_DESIGN.md) | Grounded and tone-prompt construction |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | Experiment design and observations |
| [`EVALUATION_METHOD.md`](EVALUATION_METHOD.md) | Metrics and review methodology |
| [`FINAL_REPORT.md`](FINAL_REPORT.md) | Full implementation and results report |
| [`LIVE_SMOKE_TEST.md`](LIVE_SMOKE_TEST.md) | Live Watsonx operational validation |
| [`scripts/README.md`](../scripts/README.md) | Script commands, safety, and call behavior |

---

## 29. Evidence Integrity Rules

The following evidence areas are treated as protected:

```text
prompts/
data/documents_v2_1/
data/evaluation/
data/indexes/
```

The final code-hardening process confirmed that their aggregate SHA-256 hashes remained unchanged.

The project follows these evidence rules:

1. raw model outputs are not rewritten after scoring;
2. final metrics are not manually edited to improve results;
3. prompts are not tuned after final evaluation;
4. the selected index is not rebuilt during ordinary validation;
5. owner review is preserved separately from deterministic scoring;
6. live smoke tests are documented separately from frozen evaluation metrics;
7. limitations are documented without altering the retained evidence.

---

## 30. Final Verification Checklist

A reviewer can confirm submission readiness with this checklist:

- [x] Five source documents are present.
- [x] The corpus manifest is valid.
- [x] The fact registry contains 89 facts.
- [x] The selected FAISS index contains 70 vectors.
- [x] Metadata contains 70 corresponding records.
- [x] The selected chunk configuration is 220/40.
- [x] The embedding dimension is 768.
- [x] Top-5 retrieval is frozen.
- [x] Grounded Candidate A prompts are present.
- [x] Three tone prompt pairs are present.
- [x] Three few-shot examples exist per tone.
- [x] Grounded and tone JSON schemas are present.
- [x] The final grounded set contains 24 questions.
- [x] The final tone set contains 20 inputs.
- [x] Two models were evaluated.
- [x] Retrieval metrics are present.
- [x] Grounded metrics are present.
- [x] Tone metrics are present.
- [x] Failure analysis is present.
- [x] Owner adjudication is present.
- [x] Final artifacts are hashed.
- [x] Live smoke tests are documented.
- [x] The project passes the complete automated test suite.
- [x] Offline validators pass.
- [x] Dry-run and FAISS preflight use zero external calls.
- [x] `.env` is ignored and untracked.
- [x] GitHub Actions validates a clean Git archive.

---

## 31. Final Evidence Status

```text
Corpus evidence:             Complete
Runtime implementation:      Complete
Prompt evidence:             Complete
FAISS index evidence:        Complete
Retrieval evidence:          Complete
Grounded output evidence:    Complete
Citation evidence:           Complete
Unsupported-case evidence:   Complete
Tone evidence:               Complete
Experiment evidence:         Complete
Model-comparison evidence:   Complete
Failure-analysis evidence:   Complete
Human-review evidence:       Complete
Owner verification:          Complete
Live operational evidence:   Complete
Automated-test evidence:     Complete
CI and isolation evidence:   Complete
Protected-hash evidence:     Complete
```

The repository therefore contains sufficient implementation, execution, evaluation, and review evidence to verify the complete Tier-1 Prompting and RAG Foundations assignment.
