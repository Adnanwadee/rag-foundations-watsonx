# Evaluation Methodology

## Evaluation Summary

| Item | Final-v2 design |
| --- | --- |
| Corpus | Asteron Policies Corpus v2.1 |
| Grounded questions | 24 |
| Answerable questions | 20 |
| Unsupported questions | 4 |
| Tone source inputs | 20 |
| Supported tones | 3 |
| Generation models | 2 |
| Retrieval result sets | 24 shared records |
| Grounded model outputs | 48 |
| Tone model outputs | 120 |
| Initial generation calls | 168 |
| Model-based semantic judge calls | 0 |
| Grounded outputs manually adjudicated | 24 of 48 |
| Tone triplets manually reviewed | 40 of 40 |
| Individual tone outputs covered by triplet review | 120 of 120 |
| Final scoring layer | `owner_verified_hybrid_final` |
| Final evaluation status | Complete and frozen |

---

## 1. Purpose

This document defines the evaluation methodology used for the final Prompting and RAG Foundations system.

It explains:

- how the final evaluation datasets were constructed;
- how retrieval quality was calculated;
- how grounded answers were labeled;
- how unsupported questions were evaluated;
- how citation validity was measured;
- how tone transformations were reviewed;
- how deterministic checks and manual semantic review were combined;
- how the Granite and Mistral comparison was controlled;
- how leakage and post-final tuning were prevented;
- how the final metrics can be reproduced from retained evidence.

The methodology deliberately separates:

```text
Retrieval success
Grounded-answer correctness
Unsupported-question refusal
Citation resolution
Structured-output validity
Tone factual preservation
Tone recognizability
Tone-triplet distinctness
```

These dimensions are related, but they are not interchangeable.

For example:

- retrieving the correct section does not guarantee a complete answer;
- valid JSON does not guarantee factual correctness;
- a factual rewrite does not guarantee a recognizable target tone;
- one valid tone output does not guarantee that all three tones are distinct.

---

## 2. Final Evaluation Datasets

## 2.1 Grounded Question Set

The grounded dataset is stored at:

```text
data/evaluation/final_v2/final_questions_v2.json
```

It contains:

```text
24 questions
├── 20 answerable
└── 4 unsupported
```

### Category distribution

| Category | Count |
| --- | ---: |
| Direct fact | 5 |
| Condition or exception | 5 |
| Multi-fact | 5 |
| Multi-section or source | 5 |
| Unsupported | 4 |
| **Total** | **24** |

### Purpose of the categories

#### Direct fact

Tests whether the system can locate and state one clearly supported policy fact.

#### Condition or exception

Tests whether the answer preserves:

- eligibility conditions;
- approval requirements;
- exceptions;
- timing constraints;
- modality.

#### Multi-fact

Requires more than one material fact in the same answer.

#### Multi-section or source

Requires evidence from:

- multiple sections;
- multiple source clauses;
- or more than one policy document.

#### Unsupported

Requests information that is absent from the corpus and should trigger the canonical refusal.

---

## 2.2 Grounded Question Metadata

Each final question includes structured evaluation metadata such as:

- question ID;
- question text;
- category;
- difficulty;
- expected answerability;
- expected answer;
- expected document IDs;
- expected section titles;
- expected source records;
- exact source quotations;
- fact IDs;
- clause IDs;
- atomic claims;
- claim materiality.

### Atomic claims

A complex expected answer is divided into material claims.

For example, one question may require all of the following:

```text
Visitor pre-registration
Escort in restricted areas
Visitor-record retention period
Quarterly access review
Monthly privileged-access review
Access removal deadline
```

Atomic claims make it possible to distinguish a complete answer from a directionally correct but incomplete answer.

---

## 2.3 Tone Input Set

The tone dataset is stored at:

```text
data/evaluation/final_v2/final_tone_inputs_v2.json
```

It contains:

```text
20 source inputs
```

The 20 tone inputs correspond to the 20 answerable grounded-question categories:

| Category | Tone inputs |
| --- | ---: |
| Direct fact | 5 |
| Condition or exception | 5 |
| Multi-fact | 5 |
| Multi-section or source | 5 |
| **Total** | **20** |

Each input is transformed into:

1. `formal_report_summary`;
2. `casual_message`;
3. `concise_executive_briefing`.

Both generation models process all three tones:

```text
20 inputs
× 3 tones
× 2 models
= 120 tone outputs
```

### Tone input content

Each tone record contains:

- tone-input ID;
- related grounded-question ID;
- original question;
- validated grounded source answer;
- category;
- source language;
- semantic requirements;
- protected numbers;
- protected dates;
- protected currencies;
- protected authorities.

### Language scope

All 20 frozen Final-v2 tone inputs use:

```text
source_language = en
```

Multilingual behavior was explored in development-related material, but it is not included in the denominator of the frozen Final-v2 tone metrics.

---

## 3. Dataset Freeze and Integrity

The final dataset manifest is:

```text
data/evaluation/final_v2/final_dataset_manifest.json
```

It records:

```text
Question count:       24
Tone input count:     20
Frozen:               true
Near-duplicate flags: 0
```

It also stores SHA-256 identities for:

- grounded questions;
- tone inputs;
- the frozen run plan.

After freezing:

- question wording was not changed;
- expected answers were not changed;
- tone source inputs were not changed;
- selected prompts were not changed;
- selected index assets were not changed;
- failed outputs were not replaced;
- no post-final prompt tuning was performed.

---

## 4. Final Execution Matrix

The frozen run plan is stored at:

```text
data/evaluation/final_v2/run_plan.json
```

### Planned and retained execution

| Task | Calculation | Total |
| --- | ---: | ---: |
| Query embeddings and retrieval | 24 questions | 24 |
| Grounded generations | 24 questions × 2 models | 48 |
| Tone generations | 20 inputs × 3 tones × 2 models | 120 |
| Initial chat generations | 48 + 120 | 168 |
| Model-based semantic judge calls | None | 0 |

### Shared retrieval

Retrieval was executed once for each of the 24 questions.

The same retained retrieval context was then used for both generation models.

This prevents the model comparison from being confounded by different retrieved evidence.

---

## 5. Evaluated Models

### Primary model

```text
ibm/granite-4-h-small
```

### Comparison model

```text
mistralai/mistral-small-3-1-24b-instruct-2503
```

The comparison model is described as having a smaller nominal documented parameter count.

No project-level pricing conclusion is reported because retained pricing evidence was not part of the frozen evaluation.

---

## 6. Controlled Model-Comparison Variables

Only the generation model changed.

The comparison held constant:

- corpus version;
- selected FAISS index;
- query embeddings;
- retrieved Top-5 chunks;
- Candidate A grounded prompt;
- Baseline-v2 tone prompts;
- few-shot examples;
- grounded questions;
- tone inputs;
- JSON schemas;
- temperature;
- top-p;
- output-token limits;
- repair policy;
- scoring rubric;
- manual review procedure.

### Frozen generation parameters

| Parameter | Value |
| --- | ---: |
| Temperature | `0.0` |
| Top-p | `1.0` |
| Grounded maximum tokens | 500 |
| Tone maximum tokens | 350 |
| Maximum repair retries | 1 |

Using one common application contract improves comparison fairness, although it does not represent separately optimized prompts for each model.

---

# 7. Retrieval Evaluation

## 7.1 Retrieval Population

Retrieval metrics are calculated over the:

```text
20 answerable questions
```

The four unsupported questions are excluded from retrieval Hit@K and MRR calculations because they intentionally have no expected supporting source.

Therefore:

```text
Retrieval denominator = 20
```

## 7.2 Expected Source Identity

An expected source is represented by the exact pair:

```text
(document_id, section_title)
```

A retrieved chunk counts as matching an expected source when both its:

- document ID;
- section heading;

match one of the question’s expected source records.

---

## 7.3 Hit@K

Hit@K measures whether at least one expected source appears within the first `K` retrieved chunks.

\[
\text{Hit@K}
=
\frac{
\text{answerable questions with at least one expected source by rank K}
}{
20
}
\]

### Interpretation

Hit@K asks:

> Did retrieval locate at least one relevant expected source within the first K positions?

It does not require every expected source to be present.

---

## 7.4 Hit@1

\[
\text{Hit@1}
=
\frac{19}{20}
=
0.95
\]

For 19 of the 20 answerable questions, an expected source was ranked first.

---

## 7.5 Hit@3

\[
\text{Hit@3}
=
\frac{20}{20}
=
1.00
\]

Every answerable question had at least one expected source within the first three results.

---

## 7.6 Hit@5

\[
\text{Hit@5}
=
\frac{20}{20}
=
1.00
\]

Every answerable question had at least one expected source within the selected Top-5 context.

---

## 7.7 Mean Reciprocal Rank

For each answerable question, the reciprocal rank is:

\[
RR_i
=
\frac{1}{r_i}
\]

where \(r_i\) is the rank of the first retrieved expected source.

Mean Reciprocal Rank is:

\[
MRR
=
\frac{1}{20}
\sum_{i=1}^{20}
RR_i
\]

Final result:

\[
MRR
=
0.975
\]

### Interpretation

The MRR result shows that expected evidence was usually ranked first, with a small number of cases receiving their first expected source at a later rank.

---

## 7.8 All-Expected-Source Coverage@5

Some questions require more than one expected source.

This metric passes only when every expected source for a question appears in the retrieved Top-5 set.

\[
\text{All-source coverage@5}
=
\frac{
\text{answerable questions where all expected sources appear in Top-5}
}{
20
}
\]

Final result:

\[
\text{All-source coverage@5}
=
\frac{18}{20}
=
0.90
\]

### Difference from Hit@5

A question can:

- pass Hit@5 because one expected section was retrieved;
- fail all-source coverage because another required section was absent.

This distinction is important for multi-section and multi-source questions.

---

## 7.9 Final Retrieval Results

| Metric | Numerator | Denominator | Result |
| --- | ---: | ---: | ---: |
| Hit@1 | 19 | 20 | `0.95` |
| Hit@3 | 20 | 20 | `1.00` |
| Hit@5 | 20 | 20 | `1.00` |
| MRR | Mean reciprocal first-source rank | 20 | `0.975` |
| All-expected-source coverage@5 | 18 | 20 | `0.90` |

---

## 7.10 Retrieval Metric Limitations

Retrieval metrics do not prove that:

- every retrieved chunk is relevant;
- the generation model used the evidence correctly;
- all clauses were included in the answer;
- the answer was factually complete;
- the cited chunks were the strongest possible sources.

Retrieval and generation are therefore scored separately.

---

# 8. Grounded Generation Evaluation

## 8.1 Grounded Evaluation Population

Each generation model answered all 24 questions:

```text
20 answerable
4 unsupported
```

Therefore:

```text
Grounded records per model = 24
Total grounded records      = 48
```

---

## 8.2 Grounded Labels

Each grounded model result receives one final label.

### `correct`

Used for an answerable question when the response:

- declares the question answerable;
- provides valid supporting citations;
- preserves all material expected claims;
- does not introduce a material contradiction.

### `partial`

Used for an answerable question when the response is directionally correct but omits one or more material expected claims.

Examples include omission of:

- a required condition;
- an exception;
- an approval authority;
- a deadline;
- one of several requested policy rules.

### `wrong`

Used for an answerable question when the response:

- fails to answer the question;
- provides materially incorrect information;
- declares a supported question unsupported;
- lacks required supporting citations;
- substitutes an unrelated policy statement.

### `unsupported_correct`

Used for an unsupported question when the final application output contains:

```text
I don't know based on the provided documents.
```

with:

```text
answerable = false
citation_chunk_ids = []
```

### `unsupported_wrong`

Used when an unsupported question receives:

- an invented answer;
- a nearby but contextually incorrect rule;
- supporting citations for a concept absent from the corpus;
- a non-refusal answerability decision.

---

## 8.3 Answerable Correct Rate

The denominator is the 20 answerable questions per model.

\[
\text{Answerable correct rate}
=
\frac{\text{correct answerable results}}{20}
\]

### Granite

\[
\frac{17}{20}
=
0.85
\]

### Mistral

\[
\frac{16}{20}
=
0.80
\]

---

## 8.4 Answerable Partial Rate

\[
\text{Answerable partial rate}
=
\frac{\text{partial answerable results}}{20}
\]

### Granite

\[
\frac{2}{20}
=
0.10
\]

### Mistral

\[
\frac{4}{20}
=
0.20
\]

A partial result is not counted as a strict success.

---

## 8.5 Unsupported Refusal Rate

The denominator is the four unsupported questions per model.

\[
\text{Unsupported refusal rate}
=
\frac{\text{unsupported\_correct}}{4}
\]

### Granite

\[
\frac{3}{4}
=
0.75
\]

### Mistral

\[
\frac{4}{4}
=
1.00
\]

---

## 8.6 Strict Overall Accuracy

Strict overall accuracy counts only:

- fully correct answerable results;
- correct unsupported refusals.

Partial results are treated as failures under this strict metric.

\[
\text{Strict accuracy}
=
\frac{
\text{correct}
+
\text{unsupported\_correct}
}{
24
}
\]

### Granite

\[
\frac{17 + 3}{24}
=
\frac{20}{24}
=
0.8333
\]

### Mistral

\[
\frac{16 + 4}{24}
=
\frac{20}{24}
=
0.8333
\]

Both models exceed the assignment threshold of:

```text
0.70
```

---

## 8.7 Grounded Result Breakdown

| Final label | Granite | Mistral |
| --- | ---: | ---: |
| Correct answerable | 17 | 16 |
| Partial answerable | 2 | 4 |
| Wrong answerable | 1 | 0 |
| Unsupported correct | 3 | 4 |
| Unsupported wrong | 1 | 0 |
| **Total** | **24** | **24** |

---

## 8.8 Citation Validity Count

The final metric named `citation_validity` counts answerable model records that contain at least one citation successfully resolved against the current retrieved chunk set.

The denominator is:

```text
20 answerable records per model
```

Results:

| Model | Answerable records with locally resolved citations |
| --- | ---: |
| Granite | `20/20` |
| Mistral | `19/20` |

### Citation resolution requirements

A citation identifier must:

1. be a string;
2. appear in the model output’s citation list;
3. belong to the current retrieved Top-5 set;
4. resolve to local chunk metadata.

The application then supplies:

- chunk ID;
- document ID;
- document title;
- section heading;
- source path.

### Interpretation boundary

A locally resolved citation proves that the cited chunk came from the retrieved evidence set.

It does not independently prove that:

- every expected source was cited;
- the answer used every required clause;
- the answer was complete;
- the cited chunk was semantically sufficient by itself.

That is why citation resolution, retrieval coverage, and answer correctness are separate metrics.

---

# 9. Structured-Output Evaluation

## 9.1 Raw Model Output

The raw model response is retained before application processing.

It may contain:

- valid JSON;
- malformed JSON;
- an incorrect field;
- an invalid tone identifier;
- an unsupported answer with noncanonical wording.

## 9.2 Raw Structured Validity

Raw structured validity means the original model output can be parsed and satisfies the expected model-level structure without repair.

This is different from final semantic correctness.

## 9.3 Application-Level Output

After parsing, the application may apply:

- schema validation;
- citation-ID validation;
- canonical unsupported normalization;
- at most one repair attempt.

The resulting application output is saved separately from the raw text.

## 9.4 Normalization

Normalization is not the same as a repair-generation call.

For an unsupported result, the application may normalize:

```text
answerable = false
citations = []
```

with noncanonical refusal wording into the canonical refusal:

```text
I don't know based on the provided documents.
```

Final normalization counts were:

| Model | Grounded normalization count |
| --- | ---: |
| Granite | 3 |
| Mistral | 0 |

## 9.5 Repair Retry

Repair means an additional model request was made because the generated object failed the required structural contract.

The final saved run recorded:

| Model | Grounded repairs | Tone repairs |
| --- | ---: | ---: |
| Granite | 0 | 0 |
| Mistral | 0 | 0 |

The repair mechanism remains tested through automated offline tests even though it was not needed by the retained Final-v2 outputs.

## 9.6 Transport Retry

A transport retry is different from a structured-output repair.

Transport retry concerns temporary communication or SDK failures.

Structured repair concerns invalid model content.

The project records these fields separately where available.

---

# 10. Deterministic Grounded Scoring

The deterministic layer provides the first evaluation pass.

It checks:

- expected answerability;
- application answerability;
- canonical unsupported behavior;
- citation presence;
- retained atomic-claim markers;
- numeric markers;
- important lexical claim terms.

For answerable questions, the deterministic scorer initially assigns:

- `correct`;
- `partial`;
- or `wrong`.

For unsupported questions, it assigns:

- `unsupported_correct`;
- or `unsupported_wrong`.

### Role of deterministic scoring

The deterministic layer is useful for:

- reproducibility;
- identifying obvious failures;
- locating records requiring semantic review;
- retaining clean structural labels;
- generating review requirements.

### Limitation

Lexical matching cannot fully determine semantic correctness.

It may miss:

- a subtle modality change;
- context substitution;
- an answer that repeats terms but changes meaning;
- a semantically correct paraphrase with different vocabulary.

Therefore, deterministic scoring is not the sole final authority.

---

# 11. Manual Grounded Review

## 11.1 Review Population

The final evidence contains:

```text
48 grounded model outputs
```

Of these:

```text
24 received explicit manual semantic decisions
24 retained deterministic-clean labels
```

The manually reviewed population consisted of:

- 18 mandatory flagged records;
- 6 clean representative samples;
- three clean samples per model.

### Mandatory review triggers

A grounded output was selected for mandatory semantic review when it involved one or more of:

- deterministic `partial`;
- deterministic `wrong`;
- `unsupported_wrong`;
- any unsupported question;
- repair behavior;
- application normalization.

This ensured that ambiguous and higher-risk cases received direct semantic review.

---

## 11.2 Grounded Manual Review Criteria

The reviewer compared each selected result against:

- the original user question;
- expected answerability;
- atomic expected claims;
- exact source quotations;
- retained retrieved chunks;
- final model output;
- resolved citations;
- the grounded-label rubric.

The reviewer assigned one of:

```text
correct
partial
wrong
unsupported_correct
unsupported_wrong
```

and retained reviewer notes where needed.

---

## 11.3 Owner Adjudication

The owner-review artifact is:

```text
data/evaluation/final_v2/human_review/owner_adjudication.json
```

It records:

```text
Grounded decisions reviewed:          24
Existing reviewed decisions changed:  No
Owner signoff:                        Yes
```

The owner approved the retained decisions without changing their labels.

This signoff is independent from the automated deterministic scoring layer; it is not presented as review by an external third-party organization.

---

# 12. Tone Evaluation

## 12.1 Individual Tone Output Population

Each model produced:

```text
20 formal outputs
20 casual outputs
20 executive outputs
```

Therefore:

```text
60 tone outputs per model
120 tone outputs total
```

---

## 12.2 Tone Triplets

For one model and one source input, the three tone outputs form one triplet:

```text
Formal
Casual
Executive
```

Each model therefore has:

```text
20 triplets
```

Across two models:

```text
40 tone triplets
```

All 40 triplets were manually reviewed.

---

## 12.3 Tone Evaluation Dimensions

Each individual tone output is evaluated across several dimensions.

### Structured validity

The result must:

- be valid JSON;
- contain the expected fields;
- use the exact requested tone identifier;
- provide a non-empty output string.

### Factual preservation

The output must preserve the grounded source answer’s material meaning.

This includes:

- subject;
- action;
- object;
- quantities;
- units;
- dates;
- deadlines;
- modality;
- conditions;
- exceptions;
- approval authorities;
- scope.

### Language preservation

The output must remain in the source language unless translation is explicitly requested.

All Final-v2 inputs are English, so the frozen denominator evaluates English-language preservation.

### Quantity, unit, and date preservation

This diagnostic dimension checks protected values such as:

- numeric quantities;
- monetary values;
- time units;
- dates;
- deadlines.

### Target-tone recognizability

The output must be recognizable as its requested style:

- formal report summary;
- casual message;
- concise executive briefing.

### Final individual validity

A human-reviewed tone output is considered finally valid when the reviewer confirms the required semantic, language, and style behavior for that output.

A result can therefore be:

- structurally valid;
- but not finally valid because it changes meaning or fails to express the requested tone.

---

## 12.4 Per-Tone Final Valid Rate

For one model and one tone:

\[
\text{Final-valid rate}
=
\frac{\text{finally valid outputs}}{20}
\]

### Granite

| Tone | Final valid | Rate |
| --- | ---: | ---: |
| Formal report summary | `20/20` | `1.00` |
| Casual message | `11/20` | `0.55` |
| Concise executive briefing | `12/20` | `0.60` |

### Mistral

| Tone | Final valid | Rate |
| --- | ---: | ---: |
| Formal report summary | `19/20` | `0.95` |
| Casual message | `13/20` | `0.65` |
| Concise executive briefing | `15/20` | `0.75` |

---

## 12.5 Tone Factual Preservation

### Granite

| Tone | Factual preservation |
| --- | ---: |
| Formal report summary | `20/20` |
| Casual message | `12/20` |
| Concise executive briefing | `17/20` |

### Mistral

| Tone | Factual preservation |
| --- | ---: |
| Formal report summary | `19/20` |
| Casual message | `17/20` |
| Concise executive briefing | `15/20` |

---

## 12.6 Tone Recognizability

### Granite

| Tone | Recognizable |
| --- | ---: |
| Formal report summary | `20/20` |
| Casual message | `19/20` |
| Concise executive briefing | `15/20` |

### Mistral

| Tone | Recognizable |
| --- | ---: |
| Formal report summary | `20/20` |
| Casual message | `16/20` |
| Concise executive briefing | `20/20` |

---

## 12.7 Structured Validity

All saved Final-v2 tone outputs were structurally valid:

| Model | Structurally valid outputs |
| --- | ---: |
| Granite | `60/60` |
| Mistral | `60/60` |
| **Total** | **120/120** |

This result demonstrates stable JSON generation.

It must not be interpreted as `120/120` successful semantic tone transformations.

---

# 13. Triplet-Level Tone Metrics

## 13.1 Triplet Distinctness

A tone triplet is distinct when the three outputs are recognizably different from one another in their intended styles.

\[
\text{Triplet distinctness rate}
=
\frac{\text{distinct triplets}}{20}
\]

### Results

| Model | Distinct triplets | Rate |
| --- | ---: | ---: |
| Granite | `16/20` | `0.80` |
| Mistral | `20/20` | `1.00` |

---

## 13.2 Fully Valid Triplet

A triplet is counted as fully valid only when:

1. the formal output is finally valid;
2. the casual output is finally valid;
3. the executive output is finally valid;
4. the three outputs are distinct.

Formally:

\[
\text{FullyValidTriplet}
=
FormalValid
\land CasualValid
\land ExecutiveValid
\land Distinct
\]

The rate is:

\[
\text{Fully valid triplet rate}
=
\frac{\text{fully valid triplets}}{20}
\]

### Results

| Model | Fully valid triplets | Rate |
| --- | ---: | ---: |
| Granite | `8/20` | `0.40` |
| Mistral | `9/20` | `0.45` |

This is deliberately stricter than counting individual structurally valid outputs.

---

# 14. Manual Tone Review

All:

```text
40 model-level tone triplets
```

were reviewed manually.

Because each triplet contains three outputs, the review covers:

```text
40 × 3 = 120 individual tone outputs
```

## 14.1 Individual Output Decisions

For every tone output, the reviewer recorded:

- factual preservation;
- language preservation;
- target-tone recognizability;
- final validity;
- reviewer notes where required.

## 14.2 Triplet Decision

For every source-input and model combination, the reviewer also recorded:

- whether the three tones were distinct;
- triplet-level reviewer notes.

## 14.3 Why All Tone Triplets Were Reviewed

The deterministic development signals were intentionally conservative and could not reliably decide natural style.

For example, keyword-based style rules cannot fully determine whether text:

- feels conversational;
- is executive-oriented;
- is genuinely distinct from the formal output;
- preserves meaning despite paraphrasing.

Therefore, all final tone triplets received human review.

---

# 15. Hybrid Final Scoring Layer

The authoritative scoring layer is:

```text
owner_verified_hybrid_final
```

It combines:

1. retained raw model evidence;
2. deterministic scoring;
3. manually reviewed grounded decisions;
4. manually reviewed tone triplets;
5. owner verification.

## 15.1 Grounded Combination

For each grounded record:

```text
Manual decision exists
    → use manual final label

No manual decision
    → retain deterministic-clean label
```

Final grounded composition:

| Model | Human-reviewed records | Deterministic-clean records |
| --- | ---: | ---: |
| Granite | 11 | 13 |
| Mistral | 13 | 11 |
| **Total** | **24** | **24** |

## 15.2 Tone Combination

All final tone triplets were human reviewed.

Therefore:

| Model | Human-reviewed triplets | Deterministic-only triplets |
| --- | ---: | ---: |
| Granite | 20 | 0 |
| Mistral | 20 | 0 |

---

# 16. Failure Analysis Method

Failures are retained rather than corrected after final scoring.

The failure-analysis artifact is:

```text
data/evaluation/final_v2/scoring/failure_analysis.md
```

Grounded failures are grouped into categories such as:

- non-responsive answer;
- partial multi-source synthesis;
- omitted condition;
- omitted authority or deadline;
- unsupported near-match substitution;
- missing or invalid citation behavior.

Tone failures include:

- factual drift;
- omitted protected detail;
- weak target-tone recognizability;
- formal and executive outputs being too similar;
- structurally valid output with semantic loss.

At least three representative failures are described in the final report with:

- question;
- expected behavior;
- generated behavior;
- diagnosis;
- potential future mitigation.

---

# 17. Leakage Prevention

## 17.1 Grounded Prompts

The grounded model receives:

- user question;
- retrieved Top-5 chunks;
- grounded prompt instructions.

It does not receive:

- expected answer;
- expected answerability label;
- atomic claims;
- fact IDs;
- expected document IDs;
- final rubric label.

## 17.2 Tone Prompts

The tone task intentionally receives the frozen grounded source answer because rewriting that answer is the task itself.

It does not receive:

- an expected transformed output;
- human validity labels;
- final tone scores;
- model-comparison results.

## 17.3 Semantic Judge Calls

The run plan records:

```text
semantic_judge_calls = 0
```

No language model was used as the final semantic judge.

Semantic decisions were made through retained deterministic checks and manual owner review.

---

# 18. Reconstructed Request Provenance

The rendered-request artifact is:

```text
data/evaluation/final_v2/manifests/rendered_requests.json
```

The original live request-capture file was not retained as a separate original artifact.

The request evidence was therefore deterministically reconstructed from:

- the frozen run plan;
- retained retrieval records;
- frozen prompt assets;
- frozen tone inputs.

The reconstructed request prompt hashes were verified against the prompt hashes stored with the saved outputs.

The artifact explicitly records:

```text
original_live_capture_available = false
equivalence_verified_against_saved_request_prompt_hashes = true
provenance = deterministically_reconstructed_from_frozen_run_plan_retrieval_and_prompt_assets
```

This limitation is disclosed rather than presenting reconstructed provenance as an original network capture.

---

# 19. Model-Comparison Interpretation

The comparison is multi-dimensional.

### Granite strengths in the saved evaluation

- more fully correct answerable outputs;
- fewer partial answerable outputs;
- one additional citation-resolved answerable record;
- strongest formal-tone result.

### Mistral strengths in the saved evaluation

- correct refusal on all unsupported questions;
- more fully valid tone triplets;
- distinct tone triplets across all 20 inputs.

### Equal strict grounded result

Both models achieved:

```text
20/24 = 0.8333
```

The equal aggregate result does not mean their error patterns were identical.

---

# 20. Statistical Interpretation

The reported metrics are descriptive benchmark results.

The project does not claim:

- statistical significance;
- confidence intervals;
- population-level generalization;
- universal model ranking.

The test sets are controlled and small:

```text
20 answerable grounded questions
4 unsupported grounded questions
20 tone inputs
```

A change of one record can materially affect a percentage.

For example:

```text
1 unsupported question = 25 percentage points
1 tone triplet         = 5 percentage points
1 answerable question  = 5 percentage points
```

The project therefore reports both:

- counts;
- rates.

---

# 21. Reproducibility and Evidence Preservation

The authoritative artifacts include:

```text
data/evaluation/final_v2/final_dataset_manifest.json
data/evaluation/final_v2/final_questions_v2.json
data/evaluation/final_v2/final_tone_inputs_v2.json
data/evaluation/final_v2/run_plan.json
data/evaluation/final_v2/retrieval_results.json
data/evaluation/final_v2/grounded_results.jsonl
data/evaluation/final_v2/tone_results.jsonl
data/evaluation/final_v2/scoring/deterministic_scores.json
data/evaluation/final_v2/human_review/owner_adjudication.json
data/evaluation/final_v2/scoring/final_metrics.json
data/evaluation/final_v2/scoring/model_comparison.json
data/evaluation/final_v2/scoring/failure_analysis.md
```

Protected hashes ensure that:

- datasets;
- raw outputs;
- scoring artifacts;
- prompts;
- selected index assets;

remain aligned with the reported final results.

---

# 22. Validation Commands

Run the Final-v2 validators with the project’s Python 3.11 environment:

```powershell
$PYTHON = "D:\PythonEnvs\project-01-rag-foundations\Scripts\python.exe"

& $PYTHON scripts/validate_references.py
& $PYTHON scripts/validate_corpus_v2_1.py
& $PYTHON scripts/validate_final_v2.py
& $PYTHON scripts/validate_project_complete.py
```

Run the read-only Final-v2 execution check:

```powershell
& $PYTHON scripts/run_final_v2.py --dry-run
```

Expected:

```text
external_calls: 0
```

The dry-run validates the frozen execution plan without:

- calling Watsonx;
- generating new outputs;
- changing the final results.

---

# 23. Interpretation Limitations

## 23.1 Synthetic corpus

The measured results apply to a controlled synthetic policy corpus.

They do not directly establish production performance on real enterprise data.

## 23.2 Small unsupported denominator

The unsupported refusal rate uses only four questions per model.

Results such as:

```text
3/4 = 0.75
4/4 = 1.00
```

should be interpreted alongside their counts.

## 23.3 Retrieval and synthesis are separate

A retrieved source can be correct while the generated answer remains incomplete.

## 23.4 Citation count is not complete semantic proof

A locally resolved citation confirms provenance but not full answer completeness.

## 23.5 Tone judgments include human assessment

Tone recognizability and distinction are partly subjective.

The project reduces ambiguity by:

- using a written rubric;
- preserving reviewer notes;
- reviewing all 40 triplets;
- retaining raw outputs.

## 23.6 Frozen service outputs

Saved Final-v2 metrics correspond to retained outputs.

Future live Watsonx responses may differ even with temperature `0.0`.

## 23.7 No cost or formal latency benchmark

The evaluation does not make a pricing conclusion or formal performance benchmark.

Live smoke-test timings are documented separately as operational observations.

---

# 24. Final Metric Summary

## Retrieval

| Metric | Result |
| --- | ---: |
| Hit@1 | `0.95` |
| Hit@3 | `1.00` |
| Hit@5 | `1.00` |
| MRR | `0.975` |
| All-expected-source coverage@5 | `0.90` |

## Grounded Generation

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Answerable correct | `17/20` | `16/20` |
| Answerable partial | `2/20` | `4/20` |
| Wrong answerable | `1/20` | `0/20` |
| Unsupported correct | `3/4` | `4/4` |
| Unsupported wrong | `1/4` | `0/4` |
| Citation-resolved answerable records | `20/20` | `19/20` |
| Strict overall accuracy | `20/24` | `20/24` |
| Repair retries | 0 | 0 |

## Tone Transformation

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Structurally valid outputs | `60/60` | `60/60` |
| Fully valid triplets | `8/20` | `9/20` |
| Distinct triplets | `16/20` | `20/20` |

---

# 25. Evidence Map

| Evidence | Path |
| --- | --- |
| Grounded dataset | `data/evaluation/final_v2/final_questions_v2.json` |
| Tone dataset | `data/evaluation/final_v2/final_tone_inputs_v2.json` |
| Dataset manifest | `data/evaluation/final_v2/final_dataset_manifest.json` |
| Frozen run plan | `data/evaluation/final_v2/run_plan.json` |
| Retrieval records | `data/evaluation/final_v2/retrieval_results.json` |
| Grounded outputs | `data/evaluation/final_v2/grounded_results.jsonl` |
| Tone outputs | `data/evaluation/final_v2/tone_results.jsonl` |
| Deterministic scores | `data/evaluation/final_v2/scoring/deterministic_scores.json` |
| Owner adjudication | `data/evaluation/final_v2/human_review/owner_adjudication.json` |
| Final metrics | `data/evaluation/final_v2/scoring/final_metrics.json` |
| Model comparison | `data/evaluation/final_v2/scoring/model_comparison.json` |
| Failure analysis | `data/evaluation/final_v2/scoring/failure_analysis.md` |
| Execution provenance | `data/evaluation/final_v2/manifests/execution_manifest.json` |
| Reconstructed requests | `data/evaluation/final_v2/manifests/rendered_requests.json` |
| Protected hashes | `data/evaluation/final_v2/manifests/protected_hashes.json` |
| Scoring implementation | `src/rag_foundations/final_v2.py` |
| Deterministic helper functions | `src/rag_foundations/evaluation_scoring.py` |

---

# 26. Final Evaluation Status

```text
Grounded dataset frozen:             Complete
Tone dataset frozen:                 Complete
Retrieval records:                   24
Grounded outputs:                    48
Tone outputs:                        120
Retrieval metrics:                   Complete
Grounded correctness scoring:        Complete
Unsupported refusal scoring:         Complete
Citation resolution scoring:         Complete
Tone structure scoring:              Complete
Tone semantic review:                Complete
Tone distinctness review:            Complete
Grounded manual decisions:           24
Tone triplet decisions:              40
Model-based semantic judges:         0
Owner verification:                  Complete
Failure analysis:                    Complete
Model comparison:                    Complete
Protected evidence:                  Complete
Post-final prompt tuning:             Not performed
```

The methodology provides a traceable evaluation from frozen inputs and retrieved evidence through raw model outputs, deterministic checks, manual semantic decisions, owner verification, and final reported metrics.