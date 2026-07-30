# Live watsonx.ai Smoke-Test Report

## Test Information

| Item | Value |
| --- | --- |
| Project | Prompting & RAG Foundations |
| Test type | Live end-to-end operational smoke test |
| Platform | IBM watsonx.ai |
| Interface | Project CLI |
| Runtime | Python 3.11.8 |
| Primary generation model | `ibm/granite-4-h-small` |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Vector store | Selected persistent FAISS index |
| Retrieval depth | Top-5 |
| Corpus version | `asteron-policies-v2.1` |
| Index ID | `selected-chunk-220-overlap-40` |
| Validation status | Completed successfully |

---

## 1. Purpose

This document records the final live operational tests performed against IBM watsonx.ai after the repository had passed its offline test and validation suite.

The objectives were to confirm that the frozen runtime could:

1. load local configuration safely;
2. authenticate with watsonx.ai;
3. generate a query embedding;
4. search the selected FAISS index;
5. generate a grounded answer;
6. resolve document and section citations;
7. refuse an unsupported question;
8. perform a tone transformation;
9. return valid structured JSON;
10. complete the workflow without an unexpected repair retry.

The tests were intended as targeted smoke tests, not as a latency, throughput, availability, or cost benchmark.

---

## 2. Environment Verification

Before live requests were executed, the project environment was verified.

### Interpreter

```text
Python 3.11.8
```

The editable installation resolved to the active repository checkout:

```text
src/rag_foundations/__init__.py
```

### Dependency validation

```powershell
python -m pip check
```

Result:

```text
No broken requirements found.
```

### Automated tests

```powershell
python -m pytest -q
```

Final code-hardening result:

```text
323 passed
```

This count reflects the final release-audit run on 2026-07-30.

### Offline validations

The following checks passed before the live calls:

```powershell
python -m compileall -q src scripts tests
python -m ruff check .

python scripts/validate_references.py
python scripts/validate_corpus_v2_1.py
python scripts/validate_final_v2.py
python scripts/validate_project_complete.py

python scripts/run_final_v2.py --dry-run
python scripts/build_watsonx_faiss_index.py --preflight-only
```

The final-v2 dry-run reported:

```text
external_calls: 0
```

The selected-index preflight reported:

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

---

## 3. Credential Safety

Live Watsonx credentials were stored only in the local repository-root `.env` file.

The repository was checked with:

```powershell
git check-ignore -v .env
git ls-files .env
```

Results confirmed that:

- `.env` was ignored by Git;
- `.env` was not tracked;
- no API key was stored in repository files;
- no credential value was copied into this report;
- project logs did not print settings or secret values.

The live tests verified configuration presence and authentication behavior without recording the API key or project ID.

---

## 4. End-to-End Components Exercised

The live tests exercised this complete path:

```text
Local .env configuration
        ↓
Watsonx authentication
        ↓
Question embedding
        ↓
Selected FAISS Top-5 retrieval
        ↓
Grounded Candidate A prompt
        ↓
Granite generation
        ↓
Structured JSON validation
        ↓
Citation resolution
        ↓
Optional tone transformation
        ↓
CLI JSON output
```

The tests therefore covered more than model availability alone. They verified the integration between local repository assets, the embedding service, the selected index, generation prompts, schemas, citations, and CLI serialization.

---

## 5. Live Test 1 — Supported Grounded Question

### Objective

Verify that the system can answer a directly supported policy question and return the correct approval authorities with a valid document and section citation.

### Command

```powershell
python -m rag_foundations.cli ask --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Question

> What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?

### Grounded answer

```text
Premium economy for flights of 6 hours or more requires department head approval before booking. Business class is not reimbursable unless the Chief Operating Officer approves a specific exception before booking.
```

### Answerability result

```json
{
  "is_answerable": true
}
```

### Resolved citation

| Field | Value |
| --- | --- |
| Document | Travel, Expense, and Corporate Card Policy |
| Section | 3. Air Travel and Class of Service |
| Document ID | `policy-travel-expense-v2-1` |
| Source path | `data/documents_v2_1/travel_expense_corporate_card_policy.md` |
| Corpus version | `asteron-policies-v2.1` |
| Index ID | `selected-chunk-220-overlap-40` |

### Supporting evidence

The resolved retrieved supporting excerpt contained both required rules:

- premium economy may be approved for flights of six hours or more when the department head approves before booking;
- business class is not reimbursable unless the Chief Operating Officer approves a specific exception before booking.

### Runtime metadata

| Metric | Observation |
| --- | ---: |
| Retrieved chunks | 5 |
| Grounded generation latency | `1.7861` seconds |
| Total request latency | `8.1232` seconds |
| Grounded repair used | No |
| Temperature | `0.0` |
| Top-p | `1.0` |
| Maximum output tokens | 500 |

These timings are single-request observations and are not presented as benchmark results.

### Result

```text
PASS
```

The response:

- answered both parts of the question;
- preserved the correct approval authorities;
- attached the correct document and section;
- returned valid JSON;
- required no repair retry;
- contained no unsupported policy statement.

---

## 6. Live Test 2 — Unsupported Question

### Objective

Verify that the system refuses a question whose answer is not contained in the corpus.

### Command

```powershell
python -m rag_foundations.cli ask --json `
  "What is the company's policy for reimbursing employee gym memberships?"
```

### Question

> What is the company's policy for reimbursing employee gym memberships?

### Grounded result

```json
{
  "answer": "I don't know based on the provided documents.",
  "is_answerable": false,
  "citations": []
}
```

### Runtime metadata

| Metric | Observation |
| --- | ---: |
| Retrieved chunks | 5 |
| Grounded generation latency | `0.9175` seconds |
| Total request latency | `8.1437` seconds |
| Grounded repair used | No |

### Interpretation

The retriever still returned the five nearest available chunks, which is expected behavior for vector retrieval.

The generation layer correctly determined that those chunks did not provide evidence for an employee gym-membership reimbursement policy.

The system therefore:

- did not convert semantic similarity into an invented answer;
- returned the canonical refusal;
- set `is_answerable` to `false`;
- returned an empty citation list;
- required no repair retry.

### Result

```text
PASS
```

---

## 7. Live Test 3 — Formal Report Tone

### Objective

Verify the complete grounded-answer and tone-transformation path using the formal-report tone.

### Command

```powershell
python -m rag_foundations.cli ask `
  --tone formal_report_summary `
  --json `
  "What approval is required for premium economy on a flight of 6 hours or more, and what approval is required for business class?"
```

### Grounded answer

```text
Premium economy for flights of 6 hours or more requires department head approval before booking. Business class is not reimbursable unless the Chief Operating Officer approves a specific exception before booking.
```

### Tone result

```text
For flights of six hours or longer, department head approval is required prior to booking premium economy class. Business class travel is not eligible for reimbursement under standard policy; however, the Chief Operating Officer may grant approval for specific exceptions on a case-by-case basis, provided the request is submitted and approved before the bookingis made.
```

### Structured tone fields

```json
{
  "tone": "formal_report_summary"
}
```

The tone result retained the same resolved travel-policy citation.

### Runtime metadata

| Metric | Observation |
| --- | ---: |
| Retrieved chunks | 5 |
| Grounded generation latency | `1.3951` seconds |
| Tone generation latency | `1.3543` seconds |
| Total request latency | `9.2624` seconds |
| Grounded repair used | No |
| Tone repair used | No |
| Tone prompt version | `baseline_v2::formal_report_summary` |

### Evaluation

| Dimension | Result |
| --- | --- |
| JSON structure | Pass |
| Tone identifier | Pass |
| Formal style recognizability | Pass |
| Core approval authorities | Preserved |
| Document and section citation | Preserved |
| Grounded repair retry | Not required |
| Tone repair retry | Not required |

### Qualitative observation

The output successfully demonstrated the intended formal style and retained the two central approval requirements.

It also contained:

- a minor spacing error in `bookingis`;
- limited wording expansion around the exception procedure.

This did not cause a runtime or schema failure, but it demonstrates why the project evaluates tone semantic preservation separately from structured JSON validity.

The observed output was retained as an honest live result rather than being manually rewritten or used for post-final prompt tuning.

### Result

```text
OPERATIONAL PASS
```

The complete grounded and tone pipeline executed successfully. The qualitative observation is consistent with the tone-evaluation methodology documented in the project.

---

## 8. Live Test 4 — Initial Ambiguous Query Observation

An earlier live question asked:

> What approval is required before international travel is booked?

The system returned supported class-of-service approval rules from the travel policy.

The answer was grounded in the retrieved section and did not invent the cited facts. However, the corpus does not define one general approval rule for all international travel.

This observation was used to improve the wording of the smoke-test question, not to modify the model, prompt, index, or evaluation artifacts.

The revised supported question explicitly asked about:

- premium economy on flights of six hours or more;
- business-class approval.

This produced the precise result recorded in Live Test 1.

The observation demonstrates an important testing principle:

> A smoke-test question should align precisely with the scope of the source rule being tested.

---

## 9. Smoke-Test Summary

| Capability | Result |
| --- | --- |
| Local configuration loading | Pass |
| Watsonx authentication | Pass |
| Query embedding | Pass |
| Selected FAISS index loading | Pass |
| Top-5 retrieval | Pass |
| Grounded generation | Pass |
| Structured grounded JSON | Pass |
| Answerability classification | Pass |
| Document citation | Pass |
| Section citation | Pass |
| Supporting-quote resolution | Pass |
| Canonical unsupported refusal | Pass |
| Empty unsupported citations | Pass |
| Formal tone transformation | Pass |
| Structured tone JSON | Pass |
| Citation retention through tone | Pass |
| Bounded repair path required | No |
| `.env` ignored and untracked | Pass |
| Credentials exposed | No |

---

## 10. Relationship to Saved Evaluation

The live smoke tests and the saved final evaluation serve different purposes.

### Saved final evaluation

The frozen evaluation provides:

- 24 grounded questions;
- 20 tone inputs;
- two generation models;
- 48 grounded results;
- 120 tone outputs;
- reproducible metrics;
- failure analysis;
- owner-reviewed labels.

### Live smoke tests

The live tests confirm:

- the current Watsonx credentials are valid;
- the external model service is reachable;
- query embedding operates;
- the selected local FAISS index operates;
- the CLI executes the full request path;
- structured output and citation resolution work in the current environment.

The live tests do not replace the final evaluation and are not included in the frozen evaluation metrics.

---

## 11. External-Call Accounting

### Supported grounded question

Expected live calls:

```text
1 query-embedding call
1 grounded-generation call
```

### One requested tone

Expected additional live call:

```text
1 tone-generation call
```

### Repair behavior

A malformed result may add one bounded repair call for the affected generated object.

No repair call was required in the three recorded live tests.

### Offline commands

The following made zero external model calls:

- automated tests;
- repository validators;
- final-v2 dry-run;
- selected-index preflight;
- CLI help;
- Git archive validation.

---

## 12. Security Review

No secret value is reproduced in this report.

The smoke-test process confirmed that:

- credentials remained in the local `.env`;
- `.env` was ignored by Git;
- `.env` was not tracked;
- project logs were routed to `stderr`;
- JSON output remained on `stdout`;
- credential values were not printed;
- GitHub Actions did not require credentials;
- the selected index and evaluation artifacts were not modified.

---

## 13. Final Conclusion

The live smoke tests confirmed that the submitted project operates end to end with IBM watsonx.ai.

The system successfully demonstrated:

1. authentication and model access;
2. live query embedding;
3. local FAISS Top-5 retrieval;
4. grounded answer generation;
5. document and section citation resolution;
6. correct refusal of an unsupported question;
7. formal tone transformation;
8. structured JSON output;
9. clean execution without repair retries.

The tests also confirmed that the repository’s offline evidence and live runtime are aligned:

```text
Corpus:            asteron-policies-v2.1
Documents:         5
Sections:          60
Selected vectors:  70
Chunking:          220 / 40
Retrieval:         Top-5
Embedding model:   Granite multilingual embeddings
Generation model:  Granite 4 Small
Grounded prompt:   Candidate A
Tone prompts:      Baseline v2
```

The live tests therefore provide operational confirmation that the frozen, evaluated project can be configured and executed successfully outside the saved evaluation workflow.
