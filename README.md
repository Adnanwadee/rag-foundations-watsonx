# Prompting & RAG Foundations on watsonx.ai

[![offline-ci](https://github.com/Adnanwadee/rag-foundations-watsonx/actions/workflows/ci.yml/badge.svg)](https://github.com/Adnanwadee/rag-foundations-watsonx/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)

A complete, CLI-first Retrieval-Augmented Generation system built with IBM watsonx.ai and FAISS. The project answers questions using a controlled policy-document corpus, returns traceable document and section citations, refuses unsupported questions, and transforms grounded answers into three distinct tones using structured prompts and few-shot examples.

> **Project status:** Complete, evaluated, live-tested, and validated through an offline GitHub Actions workflow.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Project Objectives](#project-objectives)
- [Key Capabilities](#key-capabilities)
- [System Architecture](#system-architecture)
- [Request Flow](#request-flow)
- [Final Configuration](#final-configuration)
- [Document Corpus](#document-corpus)
- [Repository Structure](#repository-structure)
- [Technology Stack](#technology-stack)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [watsonx.ai Configuration](#watsonxai-configuration)
- [Running the Assistant](#running-the-assistant)
- [Output Structure](#output-structure)
- [Offline Preflight and Index Validation](#offline-preflight-and-index-validation)
- [Rebuilding the FAISS Index](#rebuilding-the-faiss-index)
- [Testing and Validation](#testing-and-validation)
- [External-Call Behavior](#external-call-behavior)
- [Experiments](#experiments)
- [Evaluation Design](#evaluation-design)
- [Final Results](#final-results)
- [Supervisor Requirement Coverage](#supervisor-requirement-coverage)
- [Live Smoke-Test Summary](#live-smoke-test-summary)
- [Security and Reproducibility](#security-and-reproducibility)
- [Interpretation Notes and Scope](#interpretation-notes-and-scope)
- [Documentation](#documentation)

---

## Project Overview

This repository implements **Project 1: Prompting & RAG Foundations** using IBM watsonx.ai.

The system demonstrates two foundational AI-application capabilities:

1. **Grounded question answering:** retrieving evidence from a controlled document corpus and requiring the generation model to answer only from that evidence.
2. **Prompt-controlled rewriting:** transforming the same grounded answer into formal, casual, and executive tones while preserving its core information.

The project uses a frozen, evaluated configuration so that the documented experiments, selected index, prompts, model outputs, and final metrics remain reproducible and internally consistent.

The five Asteron policy documents are a **fictional, synthetic benchmark corpus** created specifically for controlled RAG evaluation. They are not real company policies and must not be interpreted as legal, employment, travel, or security guidance.

---

## Project Objectives

The implemented system is designed to:

- ingest structured Markdown documents;
- preserve document and section provenance during chunking;
- generate multilingual embeddings through watsonx.ai;
- store and search document vectors with FAISS;
- retrieve the Top-K most relevant chunks for a question;
- generate answers using retrieved evidence only;
- attach document, section, source-path, and supporting-quote citations;
- return a clear refusal when the corpus does not support an answer;
- transform grounded answers into three recognizable tones;
- validate generated JSON against explicit schemas;
- retry malformed structured output through a bounded repair path;
- expose the complete workflow through a command-line interface;
- compare chunking, retrieval, prompt, tone, and model choices;
- evaluate retrieval, grounded answers, unsupported questions, citations, and tone consistency.

---

## Key Capabilities

### Retrieval and grounding

- Deterministic document loading and manifest validation.
- Section-aware, token-aware chunking.
- Watsonx multilingual embedding generation.
- Persistent FAISS `IndexFlatIP` vector storage.
- Cosine-similarity retrieval.
- Frozen Top-5 retrieval configuration.
- Context-only grounded generation.
- Canonical unsupported-question refusal.
- Citation resolution against retrieved chunk metadata.

### Prompt engineering

- Separate system and user prompts.
- Selected grounded prompt: **Candidate A**.
- Three independent tone prompt templates.
- Three few-shot examples for each tone.
- Explicit grounded-answer and tone-output JSON schemas.
- Bounded structured-output repair.
- Deterministic generation settings for final evaluation.

### Interface and engineering quality

- Human-readable CLI output.
- Machine-readable `--json` output.
- Selection of one tone or all tones.
- Project-only logging to `stderr`.
- Clean JSON output on `stdout`.
- Offline corpus, index, documentation, reference, and project-completeness validation.
- Git-archive isolation validation.
- GitHub Actions CI without Watsonx credentials or live model calls.

---

## System Architecture

```mermaid
flowchart LR
    A["Synthetic Markdown Policies"] --> B["Manifest and Document Validation"]
    B --> C["Section-Aware Token Chunking"]
    C --> D["watsonx.ai Embeddings"]
    D --> E["Persistent FAISS Index"]

    Q["User Question"] --> F["Query Embedding"]
    F --> G["Top-5 Similarity Retrieval"]
    E --> G
    G --> H["Grounded Prompt: Candidate A"]
    H --> I["watsonx.ai Generation Model"]
    I --> J["Pydantic and JSON Validation"]
    J --> K["Citation Resolution"]

    K --> L["Grounded Answer"]
    L --> M{"Tone Requested?"}
    M -->|No| N["CLI or JSON Output"]
    M -->|Yes| O["Selected Tone Prompt + Few-Shot Examples"]
    O --> P["Tone Transformation"]
    P --> R["Tone Schema Validation"]
    R --> N
```

---

## Request Flow

A live question follows this sequence:

1. The CLI validates command-line arguments and loads runtime settings.
2. The question is embedded with the selected watsonx.ai embedding model.
3. The persisted FAISS index retrieves the five most similar chunks.
4. Retrieved chunks are rendered into the selected grounded prompt.
5. The primary generation model returns structured grounded JSON.
6. The result is validated against the grounded-output schema.
7. Citation identifiers are resolved to local document and section metadata.
8. When a tone is requested, the grounded answer is passed to the corresponding tone prompt.
9. Tone output is validated against the tone-output schema.
10. The final result is printed as human-readable text or valid JSON.

When the available evidence does not support an answer, the expected grounded response is:

```text
I don't know based on the provided documents.
```

In this case:

- `is_answerable` is `false`;
- `citations` is empty;
- the pipeline does not invent a policy answer.

---

## Final Configuration

The final evaluated configuration is frozen to prevent post-evaluation tuning.

| Component | Selected value |
| --- | --- |
| Corpus | Asteron Policies Corpus v2.1 |
| Documents | 5 |
| Sections | 60 |
| Registered facts | 89 |
| Selected vectors | 70 |
| Chunk size | 220 tokens |
| Chunk overlap | 40 tokens |
| Retrieval | Top-5 |
| Vector store | FAISS `IndexFlatIP` |
| Similarity metric | Cosine similarity |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Embedding dimension | 768 |
| Primary generation model | `ibm/granite-4-h-small` |
| Comparison generation model | `mistralai/mistral-small-3-1-24b-instruct-2503` |
| Grounded prompt | Candidate A |
| Tone prompts | Baseline v2 |
| Temperature | `0.0` |
| Top-p | `1.0` |
| Maximum output tokens | `500` |
| Maximum repair retries | 1 |
| Selected index ID | `selected-chunk-220-overlap-40` |
| Corpus version | `asteron-policies-v2.1` |

`sentence-transformers/all-MiniLM-L6-v2` is used only as a tokenizer asset for chunk-size measurement. Document and query embeddings are generated by `ibm/granite-embedding-278m-multilingual`.

---

## Document Corpus

The controlled corpus contains five fictional company-policy documents:

| Document | Main subject |
| --- | --- |
| `code_conduct_conflicts_reporting_policy.md` | Conduct expectations, conflicts of interest, reporting, investigations, and records |
| `employee_leave_attendance_policy.md` | Leave categories, attendance, approvals, and return-to-work requirements |
| `flexible_work_workplace_access_policy.md` | Flexible work arrangements, workplace access, visitors, and related responsibilities |
| `information_security_access_control_policy.md` | Account security, access reviews, privileged access, remote access, and incident handling |
| `travel_expense_corporate_card_policy.md` | Travel booking, class of service, receipts, expenses, reimbursement, and corporate cards |

The corpus was deliberately designed with:

- policy-specific facts;
- aliases and alternative phrasing;
- numeric thresholds and time limits;
- cross-section questions;
- unsupported questions;
- distractor clauses;
- similar concepts appearing in different policy contexts;
- rare markers used to verify retrieval behavior.

Detailed corpus construction, limitations, and intended use are documented in [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md).

---

## Repository Structure

```text
rag-foundations-watsonx/
├── .github/
│   └── workflows/
│       └── ci.yml
├── data/
│   ├── documents_v2_1/
│   ├── evaluation/
│   │   ├── development_v2_1/
│   │   ├── experiments/
│   │   └── final_v2/
│   ├── indexes/
│   │   └── selected/
│   ├── manifests/
│   │   └── frozen/
│   ├── corpus_fact_registry_v2_1.json
│   └── manifest_v2_1.json
├── docs/
├── prompts/
│   └── v2/
│       ├── few_shot/
│       ├── grounded/
│       ├── schemas/
│       └── tones/
├── scripts/
├── src/
│   └── rag_foundations/
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

### Important directories

| Path | Purpose |
| --- | --- |
| `src/rag_foundations/` | Runtime package, CLI, retrieval, generation, schemas, tone transformation, configuration, logging, and validation |
| `data/documents_v2_1/` | Five frozen synthetic source documents |
| `data/indexes/selected/` | Selected FAISS binary, metadata records, and index configuration |
| `data/manifests/frozen/` | Frozen runtime, prompt, and index manifests |
| `data/evaluation/experiments/` | Experiment summaries and selected decisions |
| `data/evaluation/final_v2/` | Final questions, retrieval results, raw outputs, scoring, owner review, metrics, and manifests |
| `prompts/v2/grounded/` | Selected grounded system and user prompts |
| `prompts/v2/tones/` | System and user templates for the three tones |
| `prompts/v2/few_shot/` | One JSON file per tone, with three examples in each file |
| `prompts/v2/schemas/` | Grounded-answer and tone-output JSON schemas |
| `scripts/` | Index building, dry-run, scoring, and validation commands |
| `tests/` | Offline unit, integration, CLI, configuration, regression, and artifact tests |
| `docs/` | Project plan, architecture, prompt design, experiments, evaluation, evidence, and final report |

---

## Technology Stack

The implementation uses direct, explicit project modules rather than a RAG orchestration framework.

| Library | Version | Purpose |
| --- | ---: | --- |
| Python | `3.11` | Supported runtime |
| `ibm-watsonx-ai` | `1.6.0` | watsonx.ai authentication, embeddings, and generation |
| `faiss-cpu` | `1.14.3` | Persistent vector index and similarity retrieval |
| `numpy` | `2.3.5` | Vector and numeric operations |
| `pydantic` | `2.13.4` | Runtime schemas and structured-output validation |
| `pydantic-settings` | `2.14.2` | Environment and `.env` configuration |
| `huggingface-hub` | `1.24.0` | Tokenizer-asset integration |
| `tokenizers` | `0.22.2` | Token-aware document chunking |
| `pytest` | `9.1.1` | Automated tests |
| `ruff` | `0.14.8` | Static analysis and linting |

The project does not require LangChain, LlamaIndex, Transformers, or Sentence Transformers for its runtime pipeline.

---

## System Requirements

- Python `>=3.11,<3.12`
- Git
- A local repository checkout
- Internet access for live watsonx.ai requests
- A valid IBM Cloud API key
- A watsonx.ai project ID
- Access to the selected embedding and generation models

The supported execution model is an **editable installation from the repository checkout** because the runtime intentionally reads prompt, corpus, manifest, evaluation, and index assets from repository-relative paths.

Run commands from the repository root.

---

## Installation

### 1. Clone the repository

```powershell
git clone https://github.com/Adnanwadee/rag-foundations-watsonx.git
cd rag-foundations-watsonx
```

### 2. Confirm Python 3.11

```powershell
python --version
```

Expected:

```text
Python 3.11.x
```

### 3. Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS or Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 4. Install the project and development tools

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### 5. Verify dependencies

```powershell
python -m pip check
```

Expected:

```text
No broken requirements found.
```

---

## watsonx.ai Configuration

Create a local environment file from the safe template.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS or Linux

```bash
cp .env.example .env
```

Edit `.env` and provide valid values:

```dotenv
WATSONX_URL=<your-watsonx-service-url>
WATSONX_PROJECT_ID=<your-watsonx-project-id>
WATSONX_API_KEY=<your-ibm-cloud-api-key>

# Optional: DEBUG, INFO, WARNING, ERROR, or CRITICAL
LOG_LEVEL=INFO
```

The three Watsonx values are required for live questions:

| Variable | Purpose |
| --- | --- |
| `WATSONX_URL` | Watsonx service endpoint |
| `WATSONX_PROJECT_ID` | Project used for model inference |
| `WATSONX_API_KEY` | IBM Cloud authentication |
| `LOG_LEVEL` | Optional project-logger level |

### Credential safety

- `.env` is ignored by Git.
- `.env` must never be committed.
- `.env.example` contains only empty credential placeholders and non-secret configuration comments.
- Runtime logs do not print credentials or settings objects.
- GitHub Actions does not require live credentials.
- Offline tests and validators make no Watsonx calls.

Confirm that `.env` is ignored:

```powershell
git check-ignore -v .env
git ls-files .env
```

The second command must produce no output.

---

## Running the Assistant

### Display CLI help

```powershell
python -m rag_foundations.cli --help
python -m rag_foundations.cli ask --help
```

### Ask a grounded question

```powershell
python -m rag_foundations.cli ask `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Request valid JSON only

```powershell
python -m rag_foundations.cli ask `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Request the formal report tone

```powershell
python -m rag_foundations.cli ask `
  --tone formal_report_summary `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Request the casual-message tone

```powershell
python -m rag_foundations.cli ask `
  --tone casual_message `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Request the concise executive briefing

```powershell
python -m rag_foundations.cli ask `
  --tone concise_executive_briefing `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Request all three tones

```powershell
python -m rag_foundations.cli ask `
  --all-tones `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Test an unsupported question

```powershell
python -m rag_foundations.cli ask `
  --json `
  "What is the company's policy for reimbursing employee gym memberships?"
```

The expected behavior is a refusal rather than an invented policy.

---

## Output Structure

### Grounded answer

The following is an abridged example from the live grounded workflow:

```json
{
  "question": "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?",
  "grounded_result": {
    "answer": "Premium economy for flights of 6 hours or more requires department head approval before booking. Business class is not reimbursable unless the Chief Operating Officer approves a specific exception before booking.",
    "is_answerable": true,
    "citations": [
      {
        "document_id": "policy-travel-expense-v2-1",
        "title": "Travel, Expense, and Corporate Card Policy",
        "section_heading": "3. Air Travel and Class of Service",
        "source_path": "data/documents_v2_1/travel_expense_corporate_card_policy.md",
        "corpus_version": "asteron-policies-v2.1",
        "index_id": "selected-chunk-220-overlap-40"
      }
    ]
  },
  "metadata": {
    "mode": "grounded_only",
    "top_k": 5,
    "generation_model_id": "ibm/granite-4-h-small",
    "embedding_model_id": "ibm/granite-embedding-278m-multilingual",
    "embedding_dimension": 768,
    "index_id": "selected-chunk-220-overlap-40"
  }
}
```

The complete runtime citation also contains:

- `citation_id`;
- `chunk_id`;
- retrieved evidence text from the supporting chunk.

### Unsupported answer

```json
{
  "question": "What is the company's policy for reimbursing employee gym memberships?",
  "grounded_result": {
    "answer": "I don't know based on the provided documents.",
    "is_answerable": false,
    "citations": []
  }
}
```

### Tone output shape

When one tone is requested, the response additionally contains:

```json
{
  "tone_result": {
    "tone": "formal_report_summary",
    "output": "<tone-transformed grounded answer>",
    "citations": [
      {
        "title": "<source document>",
        "section_heading": "<source section>"
      }
    ]
  }
}
```

When `--all-tones` is used, the response contains a structured collection of the three tone variations.

---

## Offline Preflight and Index Validation

The project includes a read-only FAISS builder preflight:

```powershell
python scripts/build_watsonx_faiss_index.py --preflight-only
```

The preflight validates the tracked corpus and persisted selected index without creating clients, downloading assets, calling external services, or writing files.

Expected values:

```text
Documents loaded: 5
Sections loaded: 60
Selected vectors: 70
Selected metadata records: 70
Chunk size/overlap: 220/40
Embedding model: ibm/granite-embedding-278m-multilingual
Embedding dimension: 768
External calls: 0
Files written: 0
```

The preflight also verifies that the selected index remains internally consistent with its configuration and metadata.

---

## Rebuilding the FAISS Index

The repository already includes the frozen selected index used by the evaluated runtime. Rebuilding is therefore not required for ordinary use or assessment.

To create a separate rebuilt index:

```powershell
python scripts/build_watsonx_faiss_index.py
```

The default rebuilt output is written under:

```text
artifacts/rebuilt-index/
```

A live rebuild may require:

- valid Watsonx credentials;
- network access;
- access to the selected embedding model;
- tokenizer assets.

The evaluated index under `data/indexes/selected/` is protected evidence and should not be overwritten during ordinary testing.

---

## Testing and Validation

The complete automated test suite passes.

Run the complete offline validation suite:

```powershell
python -m pip check
python -m compileall -q src scripts tests
python -m ruff check .
python -m pytest -q

python scripts/validate_references.py
python scripts/validate_corpus_v2_1.py
python scripts/validate_final_v2.py
python scripts/validate_project_complete.py

python scripts/run_final_v2.py --dry-run
python scripts/build_watsonx_faiss_index.py --preflight-only

python -m rag_foundations.cli --help
python -m rag_foundations.cli ask --help
```

Expected high-level results:

| Check | Expected result |
| --- | --- |
| Dependency consistency | No broken requirements |
| Compilation | Pass |
| Ruff | Pass |
| Pytest | Complete automated test suite passes |
| Reference and project-completeness validation | Pass |
| Reference validation | Pass |
| Corpus validation | 5 documents, 60 sections, 89 facts |
| Final v2 validation | Pass |
| Project completeness | Pass |
| Final v2 dry-run | `external_calls=0` |
| FAISS preflight | `External calls: 0`, `Files written: 0` |
| CLI help | Pass |
| Archive isolation | Pass |

The GitHub Actions workflow repeats the offline checks against tracked repository content and does not require a local `.env` file.

---

## External-Call Behavior

| Operation | External calls |
| --- | --- |
| Unit and integration tests | 0 |
| Corpus and artifact validators | 0 |
| Final-v2 dry-run | 0 |
| FAISS selected-index preflight | 0 |
| CLI help | 0 |
| Live grounded question | 1 query-embedding call + 1 grounded-generation call |
| One requested tone | Adds 1 tone-generation call |
| `--all-tones` | Adds 3 tone-generation calls |
| Malformed structured result | May add at most 1 bounded repair call for the affected generated object |
| Full index rebuild | Uses Watsonx embedding calls |

All logs are routed to `stderr`, while `--json` reserves `stdout` for parseable JSON.

---

## Experiments

Four controlled experiment artifacts are included.

### 1. Retrieval and chunking comparison

Compared chunk size and overlap configurations, including:

- `160 / 20`;
- `160 / 60`;
- `220 / 40`.

The selected configuration was:

```text
220-token chunks with 40-token overlap
```

Selection considered retrieval quality, context preservation, chunk count, and practical runtime size.

### 2. Grounded prompt comparison

Compared multiple grounded-prompt structures while holding retrieval and generation parameters constant.

The selected prompt was:

```text
Candidate A
```

It provided the best balance of:

- grounded-answer completeness;
- refusal behavior;
- citation structure;
- stable JSON generation;
- compatibility with bounded repair.

### 3. Tone prompt comparison

Compared the baseline tone templates with alternative prompt constructions.

The final project retained the baseline-v2 tone templates because the experiment did not establish a consistent overall advantage that justified post-final prompt replacement.

### 4. Model comparison

Compared:

- `ibm/granite-4-h-small`;
- `mistralai/mistral-small-3-1-24b-instruct-2503`.

The comparison held constant:

- the corpus;
- the selected FAISS index;
- Top-5 retrieval;
- prompt assets;
- test questions;
- tone inputs;
- temperature;
- top-p;
- scoring rubric.

The comparison model is described as having a **smaller nominal documented parameter count**. No pricing claim is made because pricing evidence was not part of the frozen evaluation.

Experiment artifacts are stored in:

```text
data/evaluation/experiments/
```

---

## Evaluation Design

### Grounded evaluation

The final grounded test set contains:

```text
24 questions
├── 20 answerable questions
└── 4 explicitly unsupported questions
```

The questions include:

- direct single-section questions;
- numeric and time-based policy questions;
- multi-condition questions;
- questions requiring more than one supporting clause;
- policy-context distractors;
- unsupported questions designed to test refusal.

### Tone evaluation

The tone test set contains:

```text
20 source inputs
× 3 tones
× 2 generation models
= 120 saved tone outputs
```

Tone inputs include:

- short inputs;
- long inputs;
- already-styled inputs;
- numeric and date-heavy inputs;
- non-English input;
- policy and non-policy factual content.

### Review layers

Final scoring combines:

1. deterministic validation;
2. structured-output checks;
3. targeted human semantic review;
4. separate manual owner verification.

The final review includes:

- 24 reviewed grounded decisions;
- 40 reviewed model-level tone triplets;
- preserved raw outputs and deterministic scoring layers;
- protected artifact hashes.

---

## Final Results

### Retrieval

| Metric | Result |
| --- | ---: |
| Hit@1 | `0.95` |
| Hit@3 | `1.00` |
| Hit@5 | `1.00` |
| Mean Reciprocal Rank | `0.975` |
| All-expected-source coverage@5 | `0.90` |

The selected Top-5 retriever found at least one expected source for every final grounded question.

### Grounded generation

| Metric | IBM Granite 4 Small | Mistral Small 3.1 24B |
| --- | ---: | ---: |
| Answerable questions correct | `17/20` | `16/20` |
| Answerable questions partial | `2/20` | `4/20` |
| Unsupported refusals correct | `3/4` | `4/4` |
| Valid citation records | `20` | `19` |
| Strict overall accuracy | `20/24` (`0.8333`) | `20/24` (`0.8333`) |
| Repair retries in final saved run | `0` | `0` |

Both models exceeded the project's required 70% grounded-performance threshold.

Granite produced one additional fully correct answerable response, while Mistral produced stronger unsupported-question refusal in the saved final evaluation. Their strict overall accuracy was equal.

### Tone transformation

| Metric | IBM Granite 4 Small | Mistral Small 3.1 24B |
| --- | ---: | ---: |
| Structurally valid tone outputs | `60/60` | `60/60` |
| Fully valid three-tone input sets | `8/20` | `9/20` |
| Recognizably distinct tone triplets | `16/20` | `20/20` |

The formal report summary was the most consistently reliable tone in the per-tone scoring. Tone outputs were structurally valid across all saved runs, while semantic and stylistic quality was separately evaluated rather than inferred from JSON validity alone.

Complete results and failure analysis are available in:

- [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md)
- [`docs/EVALUATION_METHOD.md`](docs/EVALUATION_METHOD.md)
- `data/evaluation/final_v2/scoring/final_metrics.json`
- `data/evaluation/final_v2/scoring/failure_analysis.md`
- `data/evaluation/final_v2/scoring/model_comparison.json`

---

## Supervisor Requirement Coverage

| Requirement | Implementation and evidence | Status |
| --- | --- | --- |
| Document ingestion | Manifest-backed Markdown loader | Complete |
| Document chunking | Section-aware 220/40 token configuration | Complete |
| Watsonx embeddings | Granite multilingual embedding model | Complete |
| Vector storage | Persistent FAISS selected index | Complete |
| Top-K retrieval | Frozen Top-5 retrieval | Complete |
| Grounded generation | Candidate A context-only prompt | Complete |
| Document and section citations | Citation schema and local metadata resolution | Complete |
| Unsupported refusal | Canonical refusal, `is_answerable=false`, empty citations | Implemented and evaluated |
| Formal report tone | Dedicated prompt and few-shot examples | Complete |
| Casual-message tone | Dedicated prompt and few-shot examples | Complete |
| Executive-briefing tone | Dedicated prompt and few-shot examples | Complete |
| Structured JSON output | Pydantic and JSON-schema validation | Complete |
| Malformed-output handling | One bounded repair retry and safe error path | Complete |
| Simple user interface | Human-readable and JSON CLI | Complete |
| At least three experiments | Four controlled experiment artifacts | Complete |
| At least 20 grounded questions | 24 final questions | Complete |
| At least three diagnosed failures | Detailed grounded and tone failure analysis | Complete |
| Tone evaluation on 20 inputs | 20 inputs and 120 saved tone outputs | Complete |
| Generation-model comparison | Granite versus Mistral controlled comparison | Complete |
| At least 70% performance | Strict grounded accuracy `0.8333` | Complete |

---

## Live Smoke-Test Summary

The frozen runtime was also exercised through real watsonx.ai calls after offline validation.

| Test | Result |
| --- | --- |
| Watsonx authentication | Pass |
| Query embedding | Pass |
| FAISS Top-5 retrieval | Pass |
| Supported grounded answer | Pass |
| Document and section citation | Pass |
| Unsupported-question refusal | Pass |
| Empty citations for unsupported question | Pass |
| Formal tone transformation | Pass |
| JSON schema validation | Pass |
| Repair retry required | No |
| `.env` ignored and untracked | Pass |
| Dependency verification | Pass |

The supported live question correctly returned the department-head and Chief Operating Officer approval requirements from the travel-policy section.

The unsupported gym-membership question returned the canonical refusal with no citations.

The formal-tone smoke test produced valid structured output and preserved the core policy requirements. Detailed observations, including the distinction between structural validity and strict semantic preservation, are recorded in [`docs/LIVE_SMOKE_TEST.md`](docs/LIVE_SMOKE_TEST.md).

Live timings are single-run operational observations and are not presented as a latency benchmark.

---

## Security and Reproducibility

The repository includes the following safeguards:

- `.env` is ignored and untracked.
- `.env.example` contains no credentials.
- The reference validator skips only the exact local repository-root `.env`.
- Nested `.env` files remain subject to validation.
- Project logging is isolated to the `rag_foundations` namespace.
- Logging does not reset the global root logger.
- Third-party DEBUG logging is not enabled by project `LOG_LEVEL`.
- JSON output remains isolated on `stdout`.
- Offline CI makes no Watsonx or Hugging Face calls.
- The FAISS preflight performs zero writes.
- Selected prompts, documents, evaluation artifacts, and index files are protected by deterministic hashes.
- Archive-isolation validation confirms that tracked repository content is sufficient for offline verification.
- No machine-specific path is stored in the repository.

---

## Interpretation Notes and Scope

### Synthetic benchmark corpus

The corpus was designed for controlled experimentation and evaluation. Results measure performance on this specific synthetic policy benchmark and should not be generalized directly to production legal, human-resources, financial, or security use cases.

### Grounding behavior

The system explicitly requests context-only answers and provides a canonical refusal path. As with any model-based pipeline, measured behavior is reported from the saved evaluation rather than described as an absolute guarantee.

### Tone transformation

Tone output is schema-validated and evaluated for factual preservation, language preservation, target-tone recognizability, and distinction across the three tones. Structural JSON validity does not by itself guarantee complete semantic equivalence, so semantic quality is reported separately in the evaluation.

### Timeout metadata

`request_timeout_seconds` is retained as runtime metadata and configuration information. It is not documented as a guaranteed low-level transport timeout enforced across every IBM SDK request.

### Packaging model

The supported workflow is a repository checkout with an editable installation. Prompt, data, index, and evaluation assets intentionally remain visible as repository resources rather than being hidden inside a standalone wheel.

### Live service behavior

Saved metrics refer to the frozen evaluated run. Live model responses and service latency may vary because the external platform and available model service are outside the repository's control.

---

## Documentation

| Document | Purpose |
| --- | --- |
| [`docs/PROJECT_REQUIREMENTS.md`](docs/PROJECT_REQUIREMENTS.md) | Original project scope and supervisor requirements |
| [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md) | Corpus design, composition, intended use, and limitations |
| [`docs/PROJECT_PLAN.md`](docs/PROJECT_PLAN.md) | Milestone implementation and completion plan |
| [`docs/DESIGN_DECISIONS.md`](docs/DESIGN_DECISIONS.md) | Selected design choices and their evidence |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Runtime components, data flow, and boundaries |
| [`docs/PROMPT_DESIGN.md`](docs/PROMPT_DESIGN.md) | Grounded and tone-prompt construction |
| [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) | Chunking, retrieval, prompt, tone, and model experiments |
| [`docs/EVALUATION_METHOD.md`](docs/EVALUATION_METHOD.md) | Evaluation datasets, metrics, scoring layers, and review process |
| [`docs/FINAL_REPORT.md`](docs/FINAL_REPORT.md) | Complete project implementation, results, failure analysis, and conclusions |
| [`docs/LIVE_SMOKE_TEST.md`](docs/LIVE_SMOKE_TEST.md) | Live watsonx.ai operational validation |
| [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md) | Mapping from each requirement to its supporting repository artifact |
| [`scripts/README.md`](scripts/README.md) | Script purpose, execution modes, external-call behavior, and safety notes |

The machine-readable evidence is retained under:

```text
data/evaluation/
data/indexes/selected/
data/manifests/frozen/
prompts/v2/
```

---

## Author

**Adnan Wadee Abdullah**

Project 1 — Prompting & RAG Foundations
Built with IBM watsonx.ai, FAISS, Python, structured prompting, and controlled evaluation.
