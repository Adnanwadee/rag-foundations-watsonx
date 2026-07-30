# Project Plan and Implementation Map

## Project Information

| Item | Value |
| --- | --- |
| Project | Prompting & RAG Foundations |
| Stack | IBM watsonx.ai, FAISS, Python |
| Difficulty | Tier 1 — Foundation |
| Primary interface | Command-line interface |
| Document domain | Synthetic company-policy corpus |
| Primary generation model | `ibm/granite-4-h-small` |
| Comparison generation model | `mistralai/mistral-small-3-1-24b-instruct-2503` |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Final status | Implemented, evaluated, live-tested, and submission-ready |

---

## 1. Purpose of This Document

This document maps the original project brief to the completed implementation.

It explains:

- the problem being solved;
- the scope and boundaries of the project;
- the implementation strategy;
- the completed milestones;
- the artifacts produced for each milestone;
- the evaluation and quality-assurance plan;
- the final definition of completion.

The original assignment requirements are preserved in
[`PROJECT_REQUIREMENTS.md`](PROJECT_REQUIREMENTS.md).

Detailed implementation results are reported in:

- [`FINAL_REPORT.md`](FINAL_REPORT.md);
- [`EXPERIMENTS.md`](EXPERIMENTS.md);
- [`EVALUATION_METHOD.md`](EVALUATION_METHOD.md);
- [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md).

---

## 2. Problem Statement

Foundation models can generate fluent answers even when the required facts are unavailable or unsupported. This creates a risk of hallucination, especially when the model is asked about policy, procedural, or factual content.

The project addresses two related problems:

1. **Grounding:** How can a model answer questions using only a supplied document collection and provide traceable evidence for its answer?
2. **Prompt-controlled expression:** How can the same grounded answer be rewritten reliably in different communication styles without changing its core meaning?

The implemented solution is a Retrieval-Augmented Generation pipeline that:

- retrieves relevant evidence from a controlled corpus;
- sends that evidence to a watsonx.ai generation model;
- requires a structured grounded answer;
- resolves citations to local document and section metadata;
- refuses questions that are unsupported by the retrieved evidence;
- optionally transforms the grounded answer into one of three predefined tones.

---

## 3. Project Objectives

The project objectives were to build and evaluate a system that can:

1. load and validate a document corpus;
2. preserve document and section provenance;
3. split documents into useful retrieval chunks;
4. generate embeddings using watsonx.ai;
5. persist document embeddings in a FAISS vector index;
6. retrieve the most relevant chunks for a user question;
7. generate an answer using retrieved evidence only;
8. return the document name and section for each grounded citation;
9. return a clear refusal when the corpus does not contain the answer;
10. transform a grounded answer into:
    - a formal report summary;
    - a casual message;
    - a concise executive briefing;
11. use separate system and user prompts for each tone;
12. include few-shot examples for every tone;
13. return structured JSON;
14. handle malformed structured output without crashing;
15. expose the workflow through a simple CLI;
16. compare chunking, retrieval, prompt, and model choices;
17. evaluate at least 20 grounded questions;
18. evaluate tone consistency across 20 inputs;
19. diagnose at least three failures;
20. preserve reproducible evidence for all final results.

---

## 4. Scope

### 4.1 Included Scope

The completed project includes:

- five synthetic Markdown policy documents;
- a corpus manifest and fact registry;
- deterministic document loading;
- section-aware, token-aware chunking;
- watsonx.ai multilingual embeddings;
- a persistent FAISS `IndexFlatIP` store;
- cosine-similarity retrieval;
- frozen Top-5 retrieval;
- grounded generation with structured output;
- local citation resolution;
- unsupported-question refusal;
- three tone transformations;
- three few-shot examples per tone;
- bounded JSON repair;
- a human-readable and JSON CLI;
- four controlled experiment families;
- a 24-question grounded evaluation set;
- a 20-input tone evaluation set;
- two-model comparison;
- deterministic and human review layers;
- live watsonx.ai smoke tests;
- offline validators and regression tests;
- GitHub Actions CI;
- archive-isolation validation.

### 4.2 Explicit Non-Goals

The project does not attempt to provide:

- a production access-control or identity-management system;
- a production legal, HR, security, or travel-policy assistant;
- a REST API;
- a web or mobile UI;
- OCR or PDF extraction;
- hybrid keyword and vector search;
- model-based reranking;
- an additional fourth tone;
- autonomous self-evaluation and regeneration;
- fine-tuning or parameter-efficient training;
- production observability or distributed tracing;
- a formal latency or cost benchmark;
- a standalone wheel containing all corpus and prompt assets.

These items are either outside the Tier-1 assignment or listed as optional stretch goals.

---

## 5. Dataset Strategy

A fictional policy corpus was selected to provide a controlled and reproducible evaluation environment.

The corpus contains five documents covering:

1. conduct, conflicts, and reporting;
2. leave and attendance;
3. flexible work and workplace access;
4. information security and access control;
5. travel, expenses, and corporate cards.

The dataset was designed with:

- direct policy facts;
- numeric thresholds;
- approval roles;
- time limits;
- aliases;
- similar concepts in different contexts;
- cross-section questions;
- unsupported concepts;
- distractor clauses;
- rare markers for retrieval verification.

This design allows retrieval and grounding errors to be analyzed more precisely than they could be with uncontrolled or privacy-sensitive documents.

The corpus is synthetic and is not intended to represent real company guidance.

Detailed dataset information is available in
[`DATASET_CARD.md`](DATASET_CARD.md).

---

## 6. Implemented Architecture

The completed architecture is:

```text
Markdown policy documents
        ↓
Manifest and structural validation
        ↓
Section-aware document loading
        ↓
Token-aware chunking
        ↓
watsonx.ai document embeddings
        ↓
Persistent FAISS vector index
        ↓
User-question embedding
        ↓
Top-5 similarity retrieval
        ↓
Grounded Candidate A prompt
        ↓
watsonx.ai generation model
        ↓
JSON and Pydantic validation
        ↓
Citation resolution
        ↓
Grounded answer
        ↓
Optional tone transformation
        ↓
Tone JSON validation
        ↓
CLI or machine-readable JSON output
```

### Frozen final configuration

| Component | Final selection |
| --- | --- |
| Corpus version | `asteron-policies-v2.1` |
| Documents | 5 |
| Sections | 60 |
| Facts | 89 |
| Selected vectors | 70 |
| Chunk size | 220 tokens |
| Chunk overlap | 40 tokens |
| Retrieval depth | Top-5 |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Embedding dimension | 768 |
| Primary generation model | `ibm/granite-4-h-small` |
| Comparison model | `mistralai/mistral-small-3-1-24b-instruct-2503` |
| Grounded prompt | Candidate A |
| Tone prompt set | Baseline v2 |
| Temperature | `0.0` |
| Top-p | `1.0` |
| Maximum output tokens | 500 |
| Repair retries | Maximum of 1 |

The final configuration is frozen to prevent changes after final evaluation.

---

## 7. Milestone Implementation Map

## Milestone 1 — Understand the Problem

### Original objectives

- understand RAG architecture;
- understand embeddings and vector stores;
- understand chunking;
- distinguish system and user prompts;
- configure watsonx.ai access;
- choose a document set;
- define three tones;
- define a test strategy.

### Completed implementation

- RAG concepts and design choices were documented.
- A five-document synthetic policy corpus was selected.
- The three supported tones were defined:
  - formal report summary;
  - casual message;
  - concise executive briefing.
- watsonx.ai credentials and model access were verified through live tests.
- Retrieval, grounding, tone, malformed-output, and unsupported-question test strategies were defined.
- Development and final-evaluation phases were separated.

### Evidence

- `docs/DESIGN_DECISIONS.md`
- `docs/PROMPT_DESIGN.md`
- `docs/DATASET_CARD.md`
- `docs/EVALUATION_METHOD.md`
- `.env.example`

### Status

```text
COMPLETE
```

---

## Milestone 2 — Build Ingestion and Retrieval

### Original objectives

- load documents;
- split documents into chunks;
- generate embeddings;
- store vectors;
- retrieve Top-K chunks.

### Completed implementation

- Markdown documents are loaded from a validated manifest.
- Document headings are preserved as section metadata.
- Token-aware chunks retain document and section provenance.
- Document embeddings were generated using watsonx.ai.
- Vectors were stored in a persistent FAISS `IndexFlatIP`.
- Embeddings are normalized for cosine-similarity retrieval.
- The final selected index contains 70 vectors and 70 metadata records.
- User questions are embedded and searched using Top-5 retrieval.
- A read-only offline preflight verifies the corpus and selected index.

### Evidence

- `src/rag_foundations/document_loader.py`
- `src/rag_foundations/chunking.py`
- `src/rag_foundations/watsonx_embeddings.py`
- `src/rag_foundations/faiss_store.py`
- `src/rag_foundations/faiss_store.py`, `src/rag_foundations/frozen_v2_runtime.py`
- `scripts/build_watsonx_faiss_index.py`
- `data/manifest_v2_1.json`
- `data/indexes/selected/`

### Status

```text
COMPLETE
```

---

## Milestone 3 — Build Grounded Generation and the First Tone

### Original objectives

- construct a context-only RAG prompt;
- call a watsonx.ai generation model;
- return an answer with a citation;
- implement and test the formal-report tone.

### Completed implementation

- Multiple grounded prompt candidates were compared.
- Candidate A was selected as the final grounded prompt.
- The prompt requires the model to use only retrieved evidence.
- The grounded output includes:
  - answer text;
  - `is_answerable`;
  - citation identifiers.
- Citation identifiers are resolved locally to:
  - document title;
  - section heading;
  - source path;
  - retrieved supporting excerpt.
- Unsupported questions use a canonical refusal.
- The formal-report tone was implemented with:
  - a dedicated system prompt;
  - a dedicated user template;
  - three few-shot examples;
  - structured-output validation.

### Evidence

- `src/rag_foundations/grounded_generation.py`
- `src/rag_foundations/grounded_generation.py`, `src/rag_foundations/schemas.py`
- `src/rag_foundations/schemas.py`
- `prompts/v2/grounded/`
- `prompts/v2/tones/formal.system.txt`
- `prompts/v2/tones/formal.user.txt`
- `prompts/v2/few_shot/formal.json`
- `prompts/v2/schemas/grounded_output.schema.json`
- `prompts/v2/schemas/tone_output.schema.json`

### Status

```text
COMPLETE
```

---

## Milestone 4 — Complete the Three Tones and Structured Output

### Original objectives

- implement casual and executive tones;
- include few-shot examples;
- return consistent structured output;
- handle malformed output safely.

### Completed implementation

Three tone transformations are supported:

| Tone ID | Communication goal |
| --- | --- |
| `formal_report_summary` | Neutral, structured, professional summary |
| `casual_message` | Natural, approachable, conversational explanation |
| `concise_executive_briefing` | Compact decision-oriented briefing |

Each tone includes:

- a dedicated system prompt;
- a dedicated user prompt;
- three few-shot examples;
- a consistent JSON output schema;
- validation against Pydantic models;
- a bounded repair path when generated JSON is malformed.

The CLI can request:

- no tone;
- one selected tone;
- all three tones.

### Evidence

- `src/rag_foundations/tone_transformation.py`
- `src/rag_foundations/schemas.py`, `src/rag_foundations/frozen_v2_runtime.py`
- `src/rag_foundations/pipeline.py`
- `prompts/v2/tones/`
- `prompts/v2/few_shot/`
- `prompts/v2/schemas/tone_output.schema.json`
- `tests/test_tone_transformation.py`
- `tests/test_schemas.py`, `tests/test_grounded_generation.py`, `tests/test_tone_transformation.py`

### Status

```text
COMPLETE
```

---

## Milestone 5 — Improve and Iterate

### Original objectives

- compare chunk sizes and overlap;
- compare RAG prompts;
- attach source citations;
- test tone edge cases;
- document at least three experiments.

### Completed implementation

Four controlled experiment families were completed:

1. retrieval and chunking comparison;
2. grounded prompt comparison;
3. tone prompt comparison;
4. generation-model comparison.

The final selected configuration uses:

```text
Chunk size: 220 tokens
Chunk overlap: 40 tokens
Retrieval: Top-5
Grounded prompt: Candidate A
Tone prompts: Baseline v2
```

Tone edge cases included:

- very short inputs;
- long inputs;
- inputs already written in a target-like style;
- numeric and date-heavy content;
- non-English content.

### Evidence

- `data/evaluation/experiments/retrieval_chunking_comparison.json`
- `data/evaluation/experiments/grounded_prompt_comparison.json`
- `data/evaluation/experiments/tone_prompt_comparison.json`
- `data/evaluation/experiments/model_comparison.json`
- `docs/EXPERIMENTS.md`
- `docs/DESIGN_DECISIONS.md`

### Status

```text
COMPLETE
```

---

## Milestone 6 — Evaluate, Compare, and Reflect

### Original objectives

- create at least 20 grounded questions;
- calculate correctness;
- diagnose at least three errors;
- evaluate tone consistency on 20 inputs;
- compare a second generation model;
- produce a final report.

### Completed implementation

The final evaluation contains:

```text
24 grounded questions
├── 20 answerable
└── 4 unsupported

20 tone inputs
× 3 tones
× 2 models
= 120 tone outputs
```

The two generation models were evaluated under the same:

- corpus;
- selected index;
- retrieval configuration;
- prompts;
- generation parameters;
- grounded questions;
- tone inputs;
- schemas;
- scoring rubric.

The comparison model is discussed using its nominal documented parameter count. No unsupported pricing claim is used.

Final evaluation includes:

- retrieval accuracy;
- grounded-answer correctness;
- unsupported-question refusal;
- citation validity;
- structured-output validity;
- factual preservation;
- language preservation;
- tone recognizability;
- tone distinctness;
- failure diagnosis;
- model comparison;
- owner verification.

### Evidence

- `data/evaluation/final_v2/`
- `data/evaluation/final_v2/scoring/final_metrics.json`
- `data/evaluation/final_v2/scoring/failure_analysis.md`
- `data/evaluation/final_v2/scoring/model_comparison.json`
- `docs/EVALUATION_METHOD.md`
- `docs/FINAL_REPORT.md`
- `docs/EVIDENCE_INDEX.md`

### Status

```text
COMPLETE
```

---

## 8. Development and Final-Evaluation Separation

The project separates configuration selection from final reporting.

### Development phase

The development phase was used to:

- compare chunking candidates;
- compare retrieval depth;
- compare grounded prompt structures;
- compare tone prompt structures;
- select the final configuration.

Development evidence is stored under:

```text
data/evaluation/development_v2_1/
data/evaluation/experiments/
```

### Final phase

After configuration selection:

- the final corpus was frozen;
- the selected FAISS index was frozen;
- prompts were frozen;
- model and generation settings were frozen;
- final questions were executed;
- final results were scored;
- human review was recorded;
- protected hashes were generated.

No post-final prompt tuning was applied to improve individual test results.

This separation reduces the risk of selecting a configuration based on final-test performance.

---

## 9. Evaluation Plan

## 9.1 Retrieval Evaluation

Retrieval evaluation measures whether expected evidence appears among the retrieved chunks.

Primary metrics include:

- Hit@1;
- Hit@3;
- Hit@5;
- Mean Reciprocal Rank;
- all-expected-source coverage.

The selected retriever achieved:

| Metric | Result |
| --- | ---: |
| Hit@1 | `0.95` |
| Hit@3 | `1.00` |
| Hit@5 | `1.00` |
| Mean Reciprocal Rank | `0.975` |
| All-expected-source coverage@5 | `0.90` |

---

## 9.2 Grounded-Answer Evaluation

Grounded answers are evaluated for:

- answerability classification;
- factual correctness;
- completeness;
- unsupported refusal;
- citation presence;
- citation validity;
- strict overall result.

The final strict result was:

```text
20 / 24 = 0.8333
```

for both evaluated generation models.

This exceeds the required 70% acceptance threshold.

---

## 9.3 Tone Evaluation

Tone outputs are evaluated separately from grounded-answer correctness.

Dimensions include:

- structured-output validity;
- factual preservation;
- language preservation;
- target-tone recognizability;
- distinction across all three tones.

The tone evaluation includes 20 inputs and 120 saved outputs.

Structural validity and semantic/style quality are reported separately to avoid treating valid JSON as proof of a fully successful tone transformation.

---

## 9.4 Review Layers

Final results use multiple review layers:

1. deterministic artifact validation;
2. schema validation;
3. deterministic scoring;
4. targeted human semantic review;
5. separate manual owner verification.

The owner review covers:

- 24 grounded decisions;
- 40 model-level tone triplets.

Raw model outputs and review artifacts remain preserved for traceability.

---

## 10. Quality-Assurance Plan

The project uses offline validation as the primary quality gate.

### Automated checks

```powershell
python -m pip check
python -m compileall -q src scripts tests
python -m ruff check .
python -m pytest -q
```

Current result:

```text
complete automated test suite passes
```

### Repository validators

```powershell
python scripts/validate_references.py
python scripts/validate_corpus_v2_1.py
python scripts/validate_final_v2.py
python scripts/validate_project_complete.py
```

### Offline runtime checks

```powershell
python scripts/run_final_v2.py --dry-run
python scripts/build_watsonx_faiss_index.py --preflight-only
python -m rag_foundations.cli --help
python -m rag_foundations.cli ask --help
```

Expected behavior:

- zero external calls in dry-run;
- zero external calls in FAISS preflight;
- zero files written in FAISS preflight;
- valid CLI help without credentials.

### Archive isolation

GitHub Actions also validates a clean Git archive to confirm that offline verification does not depend on:

- `.env`;
- untracked files;
- local working-tree files;
- machine-specific paths.

---

## 11. Live Validation Plan and Completion

After offline checks passed, the runtime was tested with real watsonx.ai calls.

### Supported question

The system correctly answered the approval requirements for premium economy and business class and returned the expected travel-policy document and section citation.

### Unsupported question

A question about employee gym-membership reimbursement returned:

```text
I don't know based on the provided documents.
```

with:

- `is_answerable=false`;
- empty citations.

### Tone transformation

The formal-report transformation:

- returned valid structured output;
- used the correct tone identifier;
- preserved the core approval requirements;
- returned the supporting citation.

Detailed live observations are documented in
[`LIVE_SMOKE_TEST.md`](LIVE_SMOKE_TEST.md).

---

## 12. Risk Register and Mitigations

| Risk | Mitigation |
| --- | --- |
| Hallucinated unsupported answer | Context-only prompt, explicit answerability field, canonical refusal, unsupported test cases |
| Retrieval misses a relevant section | Top-5 retrieval and chunking experiments |
| Multi-section answer is incomplete | Coverage evaluation and targeted multi-condition questions |
| Fabricated citation | Citation IDs are resolved against retrieved local chunk metadata |
| Invalid model JSON | Explicit schemas, Pydantic validation, bounded repair |
| Prompt brittleness | Diverse grounded and tone test inputs |
| Tone changes factual meaning | Separate semantic-preservation evaluation and documented observations |
| Credentials committed to Git | Ignored root `.env`, safe `.env.example`, reference validator |
| Debug logs contaminate JSON | Project-only logger on `stderr`, JSON isolated on `stdout` |
| Evidence changes after scoring | Frozen manifests and protected aggregate hashes |
| Hidden local dependency | Git-archive isolation validation |
| Model-service variation | Frozen saved outputs and distinction between saved evaluation and live behavior |
| Synthetic-data overgeneralization | Explicit dataset disclosure and scope limitations |
| Post-final tuning bias | Development/final separation and frozen final configuration |

---

## 13. Deliverables and Completion Status

| Deliverable | Repository evidence | Status |
| --- | --- | --- |
| Written project plan | `docs/PROJECT_PLAN.md` | Complete |
| Five-document corpus | `data/documents_v2_1/` | Complete |
| Corpus manifest | `data/manifest_v2_1.json` | Complete |
| Fact registry | `data/corpus_fact_registry_v2_1.json` | Complete |
| Ingestion pipeline | `src/rag_foundations/document_loader.py` | Complete |
| Chunking pipeline | `src/rag_foundations/chunking.py` | Complete |
| Watsonx embedding integration | `src/rag_foundations/watsonx_embeddings.py` | Complete |
| FAISS index | `data/indexes/selected/` | Complete |
| Top-K retriever | `src/rag_foundations/faiss_store.py`, `src/rag_foundations/frozen_v2_runtime.py` | Complete |
| Grounded generation | `src/rag_foundations/grounded_generation.py` | Complete |
| Citations | `src/rag_foundations/grounded_generation.py`, `src/rag_foundations/schemas.py` | Complete |
| Unsupported refusal | Grounded prompt, schemas, tests, final outputs | Complete |
| Three tone templates | `prompts/v2/tones/` | Complete |
| Few-shot examples | `prompts/v2/few_shot/` | Complete |
| Structured output | `prompts/v2/schemas/`, Pydantic schemas | Complete |
| Malformed-output handling | Pydantic schemas and bounded repair paths | Complete |
| CLI | `src/rag_foundations/cli.py` | Complete |
| Four experiment artifacts | `data/evaluation/experiments/` | Complete |
| 24-question evaluation set | `data/evaluation/final_v2/` | Complete |
| Tone evaluation on 20 inputs | `data/evaluation/final_v2/` | Complete |
| Failure analysis | Final scoring artifacts | Complete |
| Model comparison | Experiment and final scoring artifacts | Complete |
| Live smoke test | `docs/LIVE_SMOKE_TEST.md` | Complete |
| Automated tests | `tests/` | Complete |
| Offline CI | `.github/workflows/ci.yml` | Complete |
| Final report | `docs/FINAL_REPORT.md` | Complete |
| Evidence map | `docs/EVIDENCE_INDEX.md` | Complete |

---

## 14. Acceptance Criteria

| Acceptance criterion | Final evidence | Status |
| --- | --- | --- |
| At least 70% grounded performance | Strict accuracy `0.8333` | Met |
| Document and section citations | Citation schema and resolved metadata | Met |
| Clear unsupported refusal | Canonical refusal and unsupported test set | Met |
| Three recognizable tones | Three prompts and evaluated triplets | Met |
| Structured tone output | JSON schema and Pydantic validation | Met |
| Few-shot example per tone | Three examples per tone | Exceeded |
| Malformed-output handling | One bounded repair retry | Met |
| At least three experiments | Four experiment families | Exceeded |
| At least 20 grounded questions | 24 questions | Exceeded |
| At least three diagnosed failures | Grounded and tone failure analysis | Exceeded |
| Tone evaluation across 20 inputs | 20 inputs, 120 outputs | Met |
| Model comparison | Granite and Mistral comparison | Met |
| Simple interface | CLI with grounded and tone modes | Met |

---

## 15. Definition of Done

The project is considered complete when all of the following are true:

- [x] The five-document corpus is frozen and validated.
- [x] The selected FAISS index is present and internally consistent.
- [x] Retrieval and grounded generation operate end to end.
- [x] Document and section citations are returned.
- [x] Unsupported questions have a refusal path.
- [x] All three tones are implemented.
- [x] Few-shot examples exist for every tone.
- [x] Structured-output validation and repair are implemented.
- [x] The CLI exposes grounded and tone requests.
- [x] At least three experiments are preserved.
- [x] At least 20 grounded questions are evaluated.
- [x] At least 20 tone inputs are evaluated.
- [x] At least three failure cases are diagnosed.
- [x] Two generation models are compared.
- [x] Final grounded performance exceeds 70%.
- [x] Live supported and unsupported questions are tested.
- [x] Offline tests and validators pass.
- [x] Git-archive isolation passes.
- [x] Credentials remain local and untracked.
- [x] Final documentation maps requirements to evidence.

---

## 16. Final Project Status

```text
Problem definition:                Complete
Corpus and ingestion:              Complete
Chunking and retrieval:            Complete
Watsonx integration:               Complete
Grounded generation:               Complete
Citation resolution:               Complete
Unsupported refusal:               Complete
Three tone transformations:        Complete
Structured-output handling:        Complete
CLI interface:                     Complete
Experiments:                       Complete
Final evaluation:                  Complete
Model comparison:                  Complete
Failure analysis:                  Complete
Live smoke testing:                Complete
Automated testing:                 complete automated test suite passes
Offline CI and archive validation: Complete
Submission documentation:         Complete
```

The project satisfies the Tier-1 assignment scope and retains all supporting evidence required to explain, run, validate, and assess the implementation.
