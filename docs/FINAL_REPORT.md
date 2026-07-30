# Final Report — Prompting & RAG Foundations

## Project Information

| Item | Value |
| --- | --- |
| Project | Prompting & RAG Foundations |
| Platform | IBM watsonx.ai |
| Vector store | FAISS |
| Interface | Command-line interface |
| Primary model | `ibm/granite-4-h-small` |
| Comparison model | `mistralai/mistral-small-3-1-24b-instruct-2503` |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Corpus | Asteron Policies Corpus v2.1 |
| Author and owner reviewer | Adnan Wadee Abdullah |
| Final status | Implemented, evaluated, live-tested, and validated |

---

## 1. Executive Summary

This project implements a complete Retrieval-Augmented Generation assistant using IBM watsonx.ai, FAISS, structured prompting, and a controlled synthetic policy corpus.

The assistant can:

- ingest and chunk policy documents;
- embed document chunks with a watsonx.ai embedding model;
- retrieve relevant evidence from a persistent FAISS index;
- generate answers using retrieved context only;
- return document and section citations;
- refuse unsupported questions instead of intentionally guessing;
- transform grounded answers into three communication tones;
- return machine-readable structured JSON;
- validate and repair malformed model output through a bounded retry path;
- expose the full workflow through a command-line interface.

The project also includes:

- four controlled experiment families;
- 24 final grounded questions;
- 20 final tone inputs;
- two generation models;
- 48 grounded model results;
- 120 tone outputs;
- deterministic validation;
- targeted human semantic review;
- independent owner verification;
- live Watsonx smoke tests;
- 306 passing automated tests;
- offline GitHub Actions validation.

The final selected retriever achieved:

- Hit@1: `0.95`;
- Hit@3: `1.00`;
- Hit@5: `1.00`;
- Mean Reciprocal Rank: `0.975`;
- all-expected-source coverage@5: `0.90`.

Both evaluated generation models achieved a strict grounded accuracy of:

```text
20 / 24 = 0.8333
```

This exceeds the assignment acceptance threshold of 70%.

---

## 2. Project Objective

The project addresses two foundational AI-application requirements.

### 2.1 Grounded question answering

A foundation model can generate plausible answers even when it does not have reliable evidence. The first objective was therefore to build a pipeline that:

1. retrieves evidence from a defined document collection;
2. provides the evidence to a generation model;
3. instructs the model to use only that evidence;
4. resolves citations to the source document and section;
5. returns a clear refusal when the answer is unsupported.

### 2.2 Prompt-controlled tone transformation

The second objective was to determine how reliably prompt structure can transform the same grounded content into different communication styles.

The system supports:

- `formal_report_summary`;
- `casual_message`;
- `concise_executive_briefing`.

Each tone uses:

- a dedicated system prompt;
- a dedicated user prompt;
- three few-shot examples;
- a shared structured-output schema;
- output validation;
- bounded malformed-output repair.

---

## 3. Assignment Requirement Coverage

The final implementation covers the complete Tier-1 project scope.

| Assignment requirement | Implemented solution |
| --- | --- |
| Document ingestion | Manifest-backed Markdown document loader |
| Document chunking | Section-aware, token-aware chunking |
| Watsonx embeddings | Granite multilingual embedding model |
| Vector storage | Persistent FAISS `IndexFlatIP` |
| Similarity retrieval | Normalized cosine-similarity Top-5 retrieval |
| Grounded generation | Candidate A context-only prompt |
| Document and section citation | Local citation resolution against retrieved chunks |
| Unsupported-question handling | Canonical refusal and empty citations |
| Formal-report tone | Dedicated prompt and three few-shot examples |
| Casual-message tone | Dedicated prompt and three few-shot examples |
| Executive-briefing tone | Dedicated prompt and three few-shot examples |
| Structured output | JSON schemas and Pydantic validation |
| Malformed-output handling | One bounded repair retry and safe failure handling |
| Simple interface | Human-readable and JSON CLI |
| Three or more experiments | Four experiment families |
| Twenty or more grounded questions | 24 final questions |
| Three or more diagnosed failures | Eight grounded review cases plus tone analysis |
| Tone evaluation on 20 inputs | 20 inputs across three tones and two models |
| Model comparison | Granite versus Mistral controlled comparison |
| At least 70% performance | Strict grounded accuracy of `0.8333` |

---

## 4. Dataset and Corpus Design

## 4.1 Corpus overview

The project uses **Asteron Policies Corpus v2.1**, a controlled synthetic benchmark composed of five fictional company-policy documents.

| Document | Subject |
| --- | --- |
| Code of Conduct, Conflicts, and Reporting Policy | Conduct, records, conflicts, reporting, investigations |
| Employee Leave and Attendance Policy | Leave, attendance, approvals, medical evidence |
| Flexible Work and Workplace Access Policy | Flexible work, devices, visitors, workplace access |
| Information Security and Access Control Policy | Accounts, access reviews, privileged access, incidents |
| Travel, Expense, and Corporate Card Policy | Travel approval, expenses, receipts, cards, reimbursement |

The final corpus contains:

```text
5 documents
60 sections
89 registered policy facts
70 selected retrieval chunks
```

## 4.2 Why a synthetic corpus was used

A synthetic corpus was selected because it provides:

- complete control over expected facts;
- no private or confidential company information;
- reproducible evaluation;
- known supported and unsupported concepts;
- controlled numerical thresholds;
- known aliases and alternative phrasing;
- deliberate distractors;
- multi-section and multi-document questions;
- precise failure diagnosis.

The documents are fictional and are not intended to provide real legal, employment, financial, travel, or security guidance.

## 4.3 Corpus difficulty features

The corpus includes:

- facts expressed through different terminology;
- similar concepts across multiple documents;
- numeric limits and deadlines;
- named approval authorities;
- exceptions and negative rules;
- related but non-equivalent policy concepts;
- cross-section questions;
- unsupported questions that resemble supported topics;
- long sections containing both relevant and distracting clauses.

Further details are provided in [`DATASET_CARD.md`](DATASET_CARD.md).

---

## 5. System Architecture

The implemented system follows this flow:

```text
Markdown documents
        ↓
Manifest validation
        ↓
Section-aware document loading
        ↓
Token-aware chunking
        ↓
watsonx.ai document embeddings
        ↓
Persistent FAISS vector store
        ↓
Question embedding
        ↓
Top-5 similarity retrieval
        ↓
Grounded prompt construction
        ↓
watsonx.ai generation
        ↓
Structured-output validation
        ↓
Citation resolution
        ↓
Grounded answer
        ↓
Optional tone transformation
        ↓
Tone-output validation
        ↓
CLI or JSON response
```

## 5.1 Main implementation components

| Component | Responsibility |
| --- | --- |
| `document_loader.py` | Load manifest-backed documents and preserve section metadata |
| `chunking.py` | Produce token-aware chunks with overlap and provenance |
| `watsonx_embeddings.py` | Generate document and query embeddings |
| `faiss_store.py` | Build, load, validate, and search the FAISS store |
| `grounded_generation.py` | Construct and validate grounded-generation requests |
| `tone_transformation.py` | Transform grounded answers into requested tones |
| `schemas.py` | Define Pydantic request and response contracts |
| `prompt_assets.py` | Load and verify prompt and few-shot assets |
| `frozen_v2_runtime.py` | Execute the final frozen retrieval and generation workflow |
| `pipeline.py` | Coordinate generic grounded and tone components |
| `cli.py` | Expose human-readable and JSON command-line modes |
| `logging_config.py` | Configure project-only logging on `stderr` |
| `integrity.py` | Protect and verify frozen assets |
| `final_v2.py` | Final evaluation planning, execution, validation, and scoring support |

Detailed architecture is documented in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## 6. Final Frozen Configuration

The final configuration was selected using development experiments and then frozen before final scoring.

| Component | Final value |
| --- | --- |
| Dataset version | `asteron-policies-v2.1` |
| Chunk size | 220 tokens |
| Chunk overlap | 40 tokens |
| Vector index | FAISS `IndexFlatIP` |
| Similarity | Cosine similarity through normalized vectors |
| Retrieval depth | Top-5 |
| Selected vectors | 70 |
| Selected metadata records | 70 |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Embedding dimension | 768 |
| Primary model | `ibm/granite-4-h-small` |
| Comparison model | `mistralai/mistral-small-3-1-24b-instruct-2503` |
| Grounded prompt | Candidate A |
| Tone prompt set | Baseline v2 |
| Temperature | `0.0` |
| Top-p | `1.0` |
| Maximum output tokens | 500 |
| Repair retries | Maximum of 1 |
| Selected index ID | `selected-chunk-220-overlap-40` |

The frozen configuration ensures that:

- final prompts remain unchanged;
- the final index remains unchanged;
- the corpus remains unchanged;
- saved raw outputs remain unchanged;
- final metrics can be traced to a stable configuration;
- individual final failures are not used for post-final tuning.

---

## 7. Document Ingestion and Chunking

## 7.1 Manifest-backed loading

Documents are loaded through a versioned manifest rather than by scanning arbitrary files.

This supports:

- deterministic file order;
- document identity validation;
- source-path validation;
- document-title consistency;
- corpus-version tracking;
- minimum-section checks;
- protection against missing or unexpected files.

## 7.2 Section preservation

Markdown headings are retained as section boundaries.

Each chunk contains metadata such as:

- chunk ID;
- document ID;
- document title;
- section heading;
- source path;
- corpus version;
- index ID.

This metadata later supports local citation resolution.

## 7.3 Chunking strategy

The selected chunking configuration is:

```text
Chunk size: 220 tokens
Chunk overlap: 40 tokens
```

Overlap reduces the risk that a relevant rule is separated from a condition, exception, threshold, or approval authority at a chunk boundary.

The final selected index contains:

```text
70 vectors
70 metadata records
```

---

## 8. Embeddings and FAISS Retrieval

## 8.1 Embedding model

The selected embedding model is:

```text
ibm/granite-embedding-278m-multilingual
```

It produces vectors with dimension:

```text
768
```

The multilingual model supports the project’s English corpus and also allows multilingual query behavior to be tested without changing the retrieval architecture.

## 8.2 FAISS index

The selected index uses:

```text
FAISS IndexFlatIP
```

Vectors are normalized, allowing inner-product search to represent cosine similarity.

The persisted store includes:

```text
data/indexes/selected/asteron_policies_watsonx.index
data/indexes/selected/index_config.json
data/indexes/selected/metadata.json
```

## 8.3 Query retrieval

For a user question:

1. the question is embedded;
2. the query vector is normalized;
3. FAISS returns the five nearest chunks;
4. chunk metadata is joined with similarity scores;
5. retrieved evidence is passed to the grounded prompt.

Top-5 was retained because it provided complete expected-source hit behavior in the final retrieval set while supporting multi-source questions.

## 8.4 Offline preflight

The builder includes a read-only preflight:

```powershell
python scripts/build_watsonx_faiss_index.py --preflight-only
```

It verifies:

```text
Documents loaded: 5
Sections loaded: 60
Selected vectors: 70
Selected metadata records: 70
Chunk size/overlap: 220/40
Embedding dimension: 768
External calls: 0
Files written: 0
```

This allows corpus and index consistency to be checked without Watsonx credentials, model calls, downloads, or index writes.

---

## 9. Grounded Generation

## 9.1 Grounded prompt

The final grounded prompt is **Candidate A**.

It instructs the model to:

- use only the supplied retrieved context;
- distinguish supported and unsupported questions;
- avoid adding facts from general model knowledge;
- provide a concise answer;
- return citation identifiers;
- follow the required JSON structure;
- return the canonical refusal when evidence is insufficient.

## 9.2 Answerability contract

A grounded result contains:

```json
{
  "answer": "<answer or refusal>",
  "is_answerable": true,
  "citations": []
}
```

For unsupported questions, the expected response is:

```text
I don't know based on the provided documents.
```

with:

```json
{
  "is_answerable": false,
  "citations": []
}
```

## 9.3 Citation resolution

The model returns citation identifiers associated with retrieved chunks.

The application resolves these identifiers locally to:

- chunk ID;
- document ID;
- document title;
- section heading;
- source path;
- supporting quote;
- corpus version;
- index ID.

This prevents the model from freely inventing document names or section metadata outside the retrieved evidence set.

---

## 10. Tone Transformation

The system can transform a grounded answer into three tones.

## 10.1 Formal report summary

Designed to be:

- professional;
- neutral;
- structured;
- suitable for formal reporting;
- explicit about obligations and conditions.

## 10.2 Casual message

Designed to be:

- approachable;
- natural;
- conversational;
- easy to understand;
- less formal without becoming inaccurate.

## 10.3 Concise executive briefing

Designed to be:

- compact;
- decision-oriented;
- focused on actions and implications;
- suitable for senior readers;
- free of unnecessary detail.

## 10.4 Prompt assets

Each tone has:

- one system prompt;
- one user prompt;
- one JSON few-shot file;
- three representative few-shot examples.

The prompt assets are stored under:

```text
prompts/v2/tones/
prompts/v2/few_shot/
```

## 10.5 Tone output contract

Tone output follows a consistent structure:

```json
{
  "tone": "formal_report_summary",
  "output": "<transformed answer>"
}
```

The runtime response also retains the supporting grounded citations.

---

## 11. Structured Output and Failure Handling

Model-generated JSON can be malformed even when a prompt clearly requests structured output.

The project therefore implements:

1. JSON extraction;
2. schema validation;
3. Pydantic validation;
4. canonical normalization where explicitly allowed;
5. one bounded repair retry;
6. a safe error path if validation still fails.

The repair path is bounded to prevent:

- unlimited retries;
- uncontrolled cost;
- infinite loops;
- repeated inconsistent outputs.

The final saved evaluation required no repair retries, while automated tests verify the malformed-output path independently.

---

## 12. Command-Line Interface

The project provides a CLI because the assignment requires a minimal UI **or** CLI.

### Grounded question

```powershell
python -m rag_foundations.cli ask `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### One tone

```powershell
python -m rag_foundations.cli ask `
  --tone formal_report_summary `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### All tones

```powershell
python -m rag_foundations.cli ask `
  --all-tones `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

The CLI supports:

- readable terminal output;
- machine-readable JSON;
- one tone;
- all three tones;
- help commands without credentials;
- project logging on `stderr`;
- clean JSON on `stdout`.

---

## 13. Experiment Design

Four experiment families were completed.

## 13.1 Retrieval and chunking comparison

### Question

How do chunk size and overlap affect expected-source retrieval and multi-source coverage?

### Compared configurations

| Configuration | Expected-source Hit@5 | Multi-source full coverage |
| --- | ---: | ---: |
| 220 / 40 | `0.9444` | 5 |
| 160 / 20 | `0.9444` | 5 |
| 160 / 60 | `0.9444` | 5 |

### Decision

All three configurations tied on the retained development metrics.

The project selected:

```text
220-token chunks with 40-token overlap
```

because it preserved the observed Top-5 performance with a simpler selected index than the higher-overlap alternative.

### Controlled variables

- same five documents;
- same development questions;
- same embedding model;
- same FAISS index type;
- same Top-5 retrieval;
- same similarity method.

---

## 13.2 Grounded prompt comparison

### Question

Which grounded prompt design provides the best combination of structured-output stability, unsupported handling, and resistance to invented requested attributes?

### Results

| Candidate | Runs | Structured JSON valid | Unsupported decisions correct | Unsupported answered | Repairs or normalizations |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 36 | 36 | 6 | 0 | 6 |
| B | 36 | 31 | 6 | 0 | 1 |
| C | 36 | 36 | 6 | 0 | 6 |

### Decision

Candidate A was selected because it combined:

- complete structured JSON validity;
- correct unsupported decisions;
- no invented requested attributes;
- concise grounded behavior.

Candidate B produced malformed JSON in five runs. Candidate C matched Candidate A on the retained structural checks but did not demonstrate a stronger practical advantage.

The development metrics focused on structural and unsupported behavior and were not treated as complete semantic grading for every answer.

---

## 13.3 Tone prompt comparison

### Question

Would an alternative protected tone-prompt design improve content preservation and tone recognizability over the integrated baseline prompts?

### Compared designs

- Baseline v2 tone prompts;
- Protected v2.1 alternate tone prompts.

### Evaluation dimensions

- structured validity;
- language preservation;
- numeric preservation;
- unit preservation;
- approval-authority preservation;
- condition preservation;
- exception preservation;
- negation preservation;
- modality preservation;
- deterministic style signals.

### Decision

Baseline v2 remained selected because:

- it was fully integrated;
- it had stable schema behavior;
- it contained complete few-shot coverage;
- the alternate design did not demonstrate a decisive overall advantage;
- changing prompts after final evaluation would represent post-final tuning.

The deterministic `rough_style_signal` was treated as a development proxy rather than a replacement for human tone review.

---

## 13.4 Generation-model comparison

### Compared models

- Primary: `ibm/granite-4-h-small`;
- Comparison: `mistralai/mistral-small-3-1-24b-instruct-2503`.

### Controlled variables

Only the generation model changed.

The comparison held constant:

- corpus;
- selected index;
- embeddings;
- Top-5 retrieval;
- prompts;
- grounded questions;
- tone inputs;
- temperature;
- top-p;
- output schemas;
- scoring rubric.

The comparison model is described as having a smaller nominal documented parameter count. Pricing was not used because no frozen pricing evidence was included in the evaluation.

---

## 14. Final Evaluation Design

## 14.1 Grounded question set

The final set contains:

```text
24 questions
├── 20 answerable
└── 4 unsupported
```

The set includes:

- direct factual questions;
- numeric questions;
- approval-authority questions;
- deadline and retention questions;
- exception questions;
- multi-condition questions;
- cross-section questions;
- cross-document questions;
- unsupported concepts;
- distractor-sensitive questions.

## 14.2 Tone input set

The final tone set contains:

```text
20 inputs
```

Each input was transformed into three tones by both generation models:

```text
20 inputs
× 3 tones
× 2 models
= 120 tone outputs
```

The set includes:

- short inputs;
- long inputs;
- numeric statements;
- deadlines;
- approval authorities;
- exceptions;
- already-styled text;
- non-English text;
- policy and non-policy factual inputs.

## 14.3 Evaluation layers

Final scoring combines:

1. raw model outputs;
2. deterministic schema and content checks;
3. targeted human semantic review;
4. independent owner verification;
5. preserved labels and metrics.

Owner verification covered:

```text
24 grounded semantic decisions
40 model-level tone triplets
```

The owner approved the existing reviewed decisions without changing labels.
This Final v2 report uses the owner-verified hybrid scoring layer and records manual owner verification of the preserved grounded and tone evaluation decisions.
---

## 15. Retrieval Results

| Metric | Result |
| --- | ---: |
| Hit@1 | `0.95` |
| Hit@3 | `1.00` |
| Hit@5 | `1.00` |
| Mean Reciprocal Rank | `0.975` |
| All-expected-source coverage@5 | `0.90` |

## 15.1 Interpretation

The final retriever returned at least one expected source within the Top-5 for every final grounded question.

The difference between Hit@5 and all-expected-source coverage@5 reflects questions that required multiple expected sections. The system consistently retrieved relevant evidence, while complete coverage of every expected source was achieved for 90% of the final cases.

---

## 16. Grounded Generation Results

| Metric | Granite 4 Small | Mistral Small 3.1 24B |
| --- | ---: | ---: |
| Answerable correct | `17/20` | `16/20` |
| Answerable correct rate | `0.85` | `0.80` |
| Answerable partial | `2/20` | `4/20` |
| Answerable partial rate | `0.10` | `0.20` |
| Unsupported correct | `3/4` | `4/4` |
| Unsupported refusal rate | `0.75` | `1.00` |
| Unsupported wrong | 1 | 0 |
| Citation-valid records | 20 | 19 |
| Strict overall accuracy | `20/24` | `20/24` |
| Strict overall rate | `0.8333` | `0.8333` |
| Final repair retries | 0 | 0 |

## 16.1 Granite interpretation

Granite produced:

- one more fully correct answerable response than Mistral;
- fewer partial answerable responses;
- valid citations across 20 retained cited records;
- one incorrect unsupported response.

Its final strict accuracy was `0.8333`.

## 16.2 Mistral interpretation

Mistral produced:

- complete refusal behavior across all four unsupported questions;
- four partial answerable responses;
- 19 citation-valid records;
- the same strict overall accuracy of `0.8333`.

## 16.3 Overall grounded comparison

Neither model dominated every dimension.

Granite performed better on fully correct answerable responses, while Mistral performed better on unsupported-question refusal.

Both models exceeded the 70% acceptance threshold.

---

## 17. Tone Results

## 17.1 Overall triplet results

| Metric | Granite 4 Small | Mistral Small 3.1 24B |
| --- | ---: | ---: |
| Tone input triplets | 20 | 20 |
| Fully valid triplets | `8/20` | `9/20` |
| Fully valid triplet rate | `0.40` | `0.45` |
| Distinct triplets | `16/20` | `20/20` |
| Distinct triplet rate | `0.80` | `1.00` |

A triplet is fully valid only when all three outputs for the same input satisfy the final human-reviewed validity criteria.

## 17.2 Per-tone results

| Model and tone | Structured valid | Factual preservation | Tone recognizable | Final valid |
| --- | ---: | ---: | ---: | ---: |
| Granite — Formal report | `20/20` | `20/20` | `20/20` | `20/20` |
| Granite — Casual message | `20/20` | `12/20` | `19/20` | `11/20` |
| Granite — Executive briefing | `20/20` | `17/20` | `15/20` | `12/20` |
| Mistral — Formal report | `20/20` | `19/20` | `20/20` | `19/20` |
| Mistral — Casual message | `20/20` | `17/20` | `16/20` | `13/20` |
| Mistral — Executive briefing | `20/20` | `15/20` | `20/20` | `15/20` |

## 17.3 Interpretation

All 120 saved tone outputs were structurally valid.

The formal-report tone was the most reliable tone for both models:

- Granite: `20/20` final valid;
- Mistral: `19/20` final valid.

Mistral produced recognizable distinction across all 20 three-tone sets. Granite produced recognizable distinction in 16 of 20 sets.

The results demonstrate that prompt structure and few-shot examples reliably control broad output style, while strict factual and stylistic preservation remains a separate evaluation concern.

---

## 18. Failure Analysis

The final evaluation preserved all observed failures rather than changing prompts after scoring.

The following cases illustrate three distinct failure types.

## 18.1 Failure Case 1 — Non-responsive grounded answer

### Case

```text
Question ID: final2-g-005
Model: ibm/granite-4-h-small
```

### Question

> What standard applies to business records and corrections?

### Expected answer

> Business records must be accurate and complete, and mistakes must be corrected promptly and transparently.

### Generated answer

> Code of Conduct, Conflicts, and Reporting Policy

### Diagnosis

The response returned only the policy title and did not answer the requested records-and-corrections standard.

The failure occurred at the generation stage: relevant policy context was available, but the generated answer did not preserve the required factual content.

### Controlled future mitigation

- evaluate stronger completeness instructions on a new development set;
- test reranking or context ordering;
- retain the current frozen result for honest final reporting.

---

## 18.2 Failure Case 2 — Unsupported concept confused with a related rule

### Case

```text
Question ID: final2-g-023
Model: ibm/granite-4-h-small
```

### Question

> What daily lunch allowance is paid for ordinary office work in Kuwait?

### Expected answer

> I don't know based on the provided documents.

### Generated answer

> KWD 12 for lunch

### Diagnosis

The system substituted a travel meal limit for a nonexistent ordinary-office lunch allowance.

This is an example of semantic over-association: a related monetary rule was retrieved or emphasized, but its travel context did not match the requested ordinary-office context.

### Controlled future mitigation

- strengthen context-qualification checks;
- test a relevance reranker;
- expand unsupported development cases containing near-match distractors;
- preserve the current final result without post-final tuning.

---

## 18.3 Failure Case 3 — Partial multi-source answer

### Case

```text
Question ID: final2-g-016
Model: mistralai/mistral-small-3-1-24b-instruct-2503
```

### Question

> For workplace access governance, what visitor handling rule and access-review schedule apply?

### Expected answer

The expected response required all of the following:

- visitor pre-registration;
- escort in restricted areas;
- visitor-record retention for 90 calendar days;
- quarterly manager access review;
- monthly privileged and finance-related access review;
- removal of unnecessary access within 3 working days.

### Generated answer

> A workplace visitor must be pre-registered by the host and escorted in restricted areas. Managers must review team access at least quarterly.

### Diagnosis

The answer preserved two major rules but omitted:

- the 90-day retention period;
- monthly system-owner review;
- the 3-working-day access-removal requirement.

This demonstrates that retrieving relevant evidence does not automatically guarantee complete synthesis of all required clauses.

### Controlled future mitigation

- test source-aware answer checklists;
- evaluate reranking for multi-source questions;
- add development questions that explicitly require all retrieved clauses;
- preserve the final output and score as recorded.

---

## 18.4 Additional grounded review cases

The full failure analysis also records:

- incomplete equipment-return and device-use requirements;
- incomplete support for a five-document review-date claim;
- omitted visitor pre-registration and escort requirements;
- partial multi-policy employee-exit answers.

The complete evidence is stored in:

```text
data/evaluation/final_v2/scoring/failure_analysis.md
```

---

## 19. Live Watsonx Smoke Testing

After offline validation, the frozen runtime was tested through real watsonx.ai requests.

## 19.1 Supported grounded question

### Question

> What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?

### Result

The system correctly stated:

- premium economy for flights of six hours or more requires department-head approval before booking;
- business class requires a specific Chief Operating Officer exception before booking.

The response included the correct citation:

```text
Travel, Expense, and Corporate Card Policy
Section 3. Air Travel and Class of Service
```

The grounded output was valid JSON and required no repair retry.

## 19.2 Unsupported question

### Question

> What is the company's policy for reimbursing employee gym memberships?

### Result

```text
I don't know based on the provided documents.
```

with:

```text
is_answerable: false
citations: []
```

The test confirmed that the unsupported path can reject an unrelated policy request without fabricating a policy rule.

## 19.3 Formal tone

The formal-report transformation:

- returned the correct tone identifier;
- produced valid structured output;
- preserved the core approval authorities;
- retained the source citation;
- required no repair retry.

The smoke test also illustrated why semantic review is kept separate from schema validation: the output included minor wording expansion and a spacing error even though the JSON structure was valid.

Detailed live observations are documented in [`LIVE_SMOKE_TEST.md`](LIVE_SMOKE_TEST.md).

---

## 20. Testing and Engineering Validation

The final code-hardening state passed:

```text
306 automated tests
```

The validation suite includes:

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

Final validation confirmed:

- Python `3.11.8`;
- no broken requirements;
- valid Python compilation;
- no Ruff violations;
- 306 passing tests;
- valid tracked JSON and JSONL files;
- zero external calls during dry-run;
- zero external calls and zero writes during FAISS preflight;
- `.env` ignored and untracked;
- no machine-specific paths committed;
- clean archive-isolation execution;
- unchanged protected prompts, documents, evaluations, and indexes.

---

## 21. Security and Evidence Integrity

The project includes the following safeguards.

### Credentials

- `.env` is ignored by Git.
- `.env` is not tracked.
- `.env.example` contains placeholders only.
- tests do not read or print real credentials.
- project logging does not log settings or API keys.
- GitHub Actions requires no Watsonx credentials.

### Logging

- only the `rag_foundations` logger namespace is configured;
- project logs are written to `stderr`;
- JSON remains isolated on `stdout`;
- repeated configuration does not duplicate handlers;
- third-party debug logging is not enabled globally.

### Frozen evidence

Deterministic aggregate hashes protect:

```text
prompts/
data/documents_v2_1/
data/evaluation/
data/indexes/
```

Final hardening preserved these hashes unchanged.

### Archive isolation

The repository was validated from a clean Git archive outside the working directory.

This confirms that offline verification does not depend on:

- local `.env` files;
- untracked files;
- machine-specific repository paths;
- working-tree-only artifacts.

---

## 22. Project Strengths

The project’s primary strengths are:

1. **Strong retrieval performance**
   Hit@5 reached `1.00`, with MRR `0.975`.

2. **Traceable evidence**
   Answers resolve citations to document, section, path, and supporting quote.

3. **Explicit unsupported handling**
   The runtime has a clear answerability field and canonical refusal path.

4. **Controlled evaluation**
   The project includes answerable, unsupported, multi-condition, and distractor-sensitive questions.

5. **Fair model comparison**
   Retrieval, prompts, parameters, inputs, and scoring remained fixed while only the generation model changed.

6. **Structured-output engineering**
   Pydantic validation, JSON schemas, normalization, and bounded repair prevent unhandled malformed output.

7. **Reproducibility**
   Frozen manifests, protected hashes, saved raw outputs, and archive validation preserve evidence integrity.

8. **Complete assignment coverage**
   The project exceeds the requested number of experiments, grounded questions, diagnosed failures, and few-shot examples.

9. **Practical interface**
   The CLI supports grounded output, individual tones, all tones, and machine-readable JSON.

10. **Transparent evaluation layers**
    Structural validity, semantic correctness, and tone quality are assessed separately.

---

## 23. Interpretation and Limitations

The following points define the correct scope of the results.

## 23.1 Synthetic benchmark

The corpus is controlled and synthetic. The results demonstrate the project architecture and evaluation method but should not be treated as production performance on real corporate documents.

## 23.2 Unsupported-question behavior

The system explicitly implements a refusal path, and the live unsupported test succeeded. The saved final evaluation also records one Granite near-match error, which provides useful evidence for future relevance and context-qualification work.

## 23.3 Multi-source completeness

Retrieval can locate relevant evidence while generation still omits one or more required clauses. Multi-source completeness is therefore evaluated separately from retrieval success.

## 23.4 Tone preservation

All saved tone outputs were structurally valid. Semantic preservation and tone recognizability were reviewed separately because valid JSON alone cannot guarantee faithful rewriting.

The formal-report tone showed the highest reliability in the final evaluation.

## 23.5 Model comparison

The comparison evaluates task behavior under controlled conditions. It does not make a pricing claim because frozen pricing evidence was not included.

## 23.6 Timeout metadata

`request_timeout_seconds` is retained as runtime metadata and configuration information. It is not presented as a guaranteed transport-level timeout across every IBM SDK request.

## 23.7 Packaging

The supported execution model is an editable installation from a repository checkout. The runtime intentionally accesses visible repository assets under `data/` and `prompts/`.

## 23.8 Live-service variation

Saved evaluation artifacts correspond to a frozen execution. Future live outputs and latency may vary with external service availability and model behavior.

---

## 24. Acceptance Matrix

| Acceptance criterion | Result | Status |
| --- | --- | --- |
| At least 70% grounded correctness | Strict accuracy `0.8333` | PASS |
| Document and section citations | Local citation resolution implemented and evaluated | PASS |
| Clear unsupported refusal | Canonical refusal path, four unsupported final cases, live refusal test | PASS WITH RECORDED EDGE CASE |
| Three distinct tones | Three dedicated prompts; Granite 16/20 and Mistral 20/20 distinct triplets | PASS |
| Structured tone output | `120/120` saved tone outputs structurally valid | PASS |
| At least one few-shot example per tone | Three examples per tone | PASS |
| Malformed-output handling | Bounded repair and safe failure path | PASS |
| At least three experiments | Four experiment families | PASS |
| At least 20 grounded questions | 24 final questions | PASS |
| At least three diagnosed failures | Detailed grounded and tone analysis | PASS |
| Tone evaluation on 20 inputs | 20 inputs and 120 outputs | PASS |
| Model comparison | Granite and Mistral under controlled variables | PASS |
| Simple interface | CLI with grounded, one-tone, and all-tone modes | PASS |

---

## 25. Final Conclusion

The project successfully demonstrates the two central goals of Prompting and RAG Foundations:

1. grounding model answers in supplied evidence;
2. controlling how grounded information is expressed through structured prompts.

The final system includes:

- a validated five-document corpus;
- section-aware chunking;
- Watsonx multilingual embeddings;
- persistent FAISS retrieval;
- Top-5 evidence selection;
- grounded generation;
- document and section citations;
- unsupported-question refusal;
- three tone transformations;
- few-shot prompting;
- structured JSON;
- bounded repair;
- a usable CLI;
- four experiment families;
- 24 grounded questions;
- 20 tone inputs;
- two-model comparison;
- failure analysis;
- live operational tests;
- 306 automated tests;
- offline and archive-isolated validation.

The final strict grounded accuracy of `0.8333` exceeds the required acceptance threshold, and the project preserves sufficient implementation, experiment, scoring, and evidence artifacts for a reviewer to understand and verify each major decision.

The repository is therefore complete for the Tier-1 assignment scope and ready for final submission.

---

## 26. Evidence References

| Evidence | Path |
| --- | --- |
| Original requirements | `docs/PROJECT_REQUIREMENTS.md` |
| Dataset card | `docs/DATASET_CARD.md` |
| Project plan | `docs/PROJECT_PLAN.md` |
| Design decisions | `docs/DESIGN_DECISIONS.md` |
| Architecture | `docs/ARCHITECTURE.md` |
| Prompt design | `docs/PROMPT_DESIGN.md` |
| Experiments | `docs/EXPERIMENTS.md` |
| Evaluation methodology | `docs/EVALUATION_METHOD.md` |
| Live smoke tests | `docs/LIVE_SMOKE_TEST.md` |
| Evidence index | `docs/EVIDENCE_INDEX.md` |
| Final metrics | `data/evaluation/final_v2/scoring/final_metrics.json` |
| Model comparison | `data/evaluation/final_v2/scoring/model_comparison.json` |
| Failure analysis | `data/evaluation/final_v2/scoring/failure_analysis.md` |
| Owner adjudication | `data/evaluation/final_v2/human_review/owner_adjudication.json` |
| Final questions | `data/evaluation/final_v2/final_questions_v2.json` |
| Final tone inputs | `data/evaluation/final_v2/final_tone_inputs_v2.json` |
| Grounded results | `data/evaluation/final_v2/grounded_results.jsonl` |
| Tone results | `data/evaluation/final_v2/tone_results.jsonl` |
| Selected index | `data/indexes/selected/` |
| Frozen manifests | `data/manifests/frozen/` |
| Prompt assets | `prompts/v2/` |