# Controlled Experiments and Selection Evidence

## Experiment Summary

| Experiment | Changed variable | Selected outcome |
| --- | --- | --- |
| Retrieval and chunking | Chunk size and overlap | `220 / 40` |
| Grounded prompt | Candidate A, B, or C | Candidate A |
| Tone prompt family | Baseline v2 or Protected v2.1 | Baseline v2 |
| Generation model | Granite or Mistral | Granite retained as primary; Mistral retained as comparison |

---

## 1. Purpose

This document records the controlled experiments used to select and evaluate the final Prompting and RAG Foundations configuration.

The experiments answer four main engineering questions:

1. Which chunk size and overlap provide suitable retrieval behavior?
2. Which grounded prompt produces the most reliable structured and unsupported-question behavior?
3. Which tone-prompt family provides the best practical balance between preservation, structure, and recognizable style?
4. How does the primary Granite generation model compare with Mistral when all other variables remain fixed?

Each experiment is documented using:

- research question and hypothesis;
- dataset;
- controlled variables;
- changed variable;
- metrics;
- numeric results;
- observation;
- selection decision;
- limitations.

The active experiment artifacts are stored under:

```text
data/evaluation/experiments/
```

---

## 2. Experimental Design Principles

The experiments follow several controls intended to make the resulting decisions interpretable.

### 2.1 One principal changed variable

Each experiment changes one main variable while keeping the remaining relevant variables constant.

Examples:

- the chunking experiment changes chunk size and overlap;
- the grounded-prompt experiment changes prompt wording;
- the model comparison changes only the generation model.

### 2.2 Development evidence before final evaluation

Chunking and prompt selections were made from development evidence before the final evaluation configuration was frozen.

The final evaluation was then used to measure the selected system, not to repeatedly tune it.

### 2.3 Saved evidence

Experiment summaries are stored as machine-readable JSON.

The selected configuration is also retained through:

```text
data/manifests/frozen/
data/evaluation/final_v2/run_plan.json
data/evaluation/final_v2/manifests/
```

### 2.4 Metric separation

The project does not treat all validation dimensions as equivalent.

It distinguishes between:

- retrieval success;
- raw model JSON validity;
- application-valid structured output;
- grounded semantic correctness;
- citation validity;
- unsupported-question correctness;
- tone factual preservation;
- tone recognizability;
- tone distinctness.

A valid JSON object is not automatically considered a correct grounded answer or successful tone transformation.

---

# Experiment 1 — Retrieval and Chunking Comparison

## 3. Research Question

Which fixed chunk-size and overlap configuration preserves expected-source retrieval and multi-source coverage without adding unnecessary retrieval complexity?

## 3.1 Hypothesis

A moderately sized chunk with enough overlap to protect boundary information should preserve relevant policy conditions and exceptions while remaining specific enough for semantic retrieval.

## 3.2 Dataset

The experiment used:

```text
Asteron Policies Corpus v2.1
36 development retrieval records
5 synthetic Markdown documents
```

The corpus contains:

```text
5 documents
60 sections
89 registered facts
```

## 3.3 Controlled Variables

The following variables remained constant:

- five synthetic Markdown source documents;
- development retrieval questions;
- watsonx.ai Granite multilingual embeddings;
- FAISS `IndexFlatIP`;
- normalized cosine-similarity search;
- Top-5 retrieval;
- expected-source annotations;
- retrieval-scoring method.

## 3.4 Changed Variable

The changed variable was the chunk-size and overlap configuration.

| Configuration ID | Chunk size | Overlap |
| --- | ---: | ---: |
| `chunk-160-overlap-20` | 160 tokens | 20 tokens |
| `chunk-160-overlap-60` | 160 tokens | 60 tokens |
| `chunk-220-overlap-40` | 220 tokens | 40 tokens |

## 3.5 Metrics

### Expected-source Hit@5

A record passes when at least one expected source appears among the first five retrieved chunks.

\[
\text{Expected-source Hit@5}
=
\frac{\text{records with an expected source in Top-5}}
{\text{development retrieval records}}
\]

### Multi-source full-coverage count

For questions with multiple expected sources, this metric counts how many records retrieved every expected source within Top-5.

## 3.6 Results

| Configuration | Development records | Expected-source Hit@5 | Multi-source full coverage |
| --- | ---: | ---: | ---: |
| `chunk-160-overlap-20` | 36 | `0.9444` | 5 |
| `chunk-160-overlap-60` | 36 | `0.9444` | 5 |
| `chunk-220-overlap-40` | 36 | `0.9444` | 5 |

## 3.7 Observation

All three configurations tied on the retained development metrics.

The results indicate that, for this controlled corpus:

- increasing overlap from 20 to 60 did not improve the recorded Hit@5;
- reducing chunk size from 220 to 160 did not improve the recorded multi-source coverage;
- `220/40` retained the same observed development retrieval quality as both 160-token alternatives.

The experiment artifact does not include a complete per-candidate vector-count or byte-size table. Therefore, this report does not use an unverified index-size advantage as the primary selection argument.

## 3.8 Decision

The selected configuration was:

```text
Chunk size:     220 tokens
Chunk overlap:  40 tokens
```

The decision was based on:

- no measured retrieval disadvantage;
- moderate rather than high overlap;
- greater context capacity per chunk;
- reduced risk of separating a rule from its condition or exception;
- a balanced choice between contextual completeness and retrieval specificity.

The selected persisted index contains:

```text
70 vectors
70 metadata records
```

## 3.9 Final Confirmation

After the configuration was frozen, the final retrieval evaluation produced:

| Metric | Final result |
| --- | ---: |
| Hit@1 | `0.95` |
| Hit@3 | `1.00` |
| Hit@5 | `1.00` |
| Mean Reciprocal Rank | `0.975` |
| All-expected-source coverage@5 | `0.90` |

These final results confirm that the selected configuration performed strongly. They were not used to retroactively select the configuration.

## 3.10 Limitation

This experiment measures retrieval evidence, not generation quality.

A correct source appearing in Top-5 does not guarantee that the generation model will:

- use every relevant clause;
- preserve every condition;
- answer the exact question;
- refuse an unsupported near-match;
- create a complete multi-source answer.

## 3.11 Evidence

```text
data/evaluation/experiments/retrieval_chunking_comparison.json
data/evaluation/final_v2/retrieval_results.json
data/evaluation/final_v2/scoring/final_metrics.json
data/indexes/selected/index_config.json
```

---

# Experiment 2 — Grounded Prompt Candidate Comparison

## 4. Research Question

Which grounded prompt provides the strongest practical combination of:

- structured JSON reliability;
- unsupported-question handling;
- resistance to invented requested attributes;
- compatibility with local citation resolution?

## 4.1 Hypothesis

A prompt that explicitly separates answerability, answer text, and retrieved citation IDs should produce more stable application behavior than a prompt with less balanced or more narrowly emphasized instructions.

## 4.2 Dataset

The experiment used controlled development grounded cases from:

```text
Asteron Policies Corpus v2.1
```

Each candidate was executed:

```text
36 times
```

The development set included answerable and unsupported cases.

## 4.3 Controlled Variables

The following variables remained constant:

- selected retrieval contexts;
- generation model;
- temperature `0.0`;
- top-p `1.0`;
- output schema;
- repair and normalization policy;
- development questions;
- evaluation logic.

## 4.4 Changed Variable

Only the grounded system and user prompt wording changed.

| Candidate | Main design emphasis |
| --- | --- |
| Candidate A | Balanced grounding, citations, refusal, and structured output |
| Candidate B | More explicit canonical-refusal wording |
| Candidate C | Alternate completeness and constraint emphasis |

## 4.5 Metrics

### Structured JSON valid

Number of raw generated outputs that successfully parsed and matched the expected model-level JSON contract.

### Unsupported decisions correct

Number of unsupported cases correctly classified as unsupported.

### Unsupported answered

Number of unsupported cases for which the model produced an answer instead of refusing.

### Invented requested attributes

Number of cases where the output supplied a requested attribute not explicitly supported by the retrieved context.

### Repairs or normalizations

Application-level handling used to produce the final canonical contract.

This field combines more than one behavior and must not be interpreted as an external model-repair call in every case. For example, canonical normalization of an already correct unsupported decision may be included.

## 4.6 Results

| Candidate | Runs | Raw structured JSON valid | Unsupported correct | Unsupported answered | Invented attributes | Repairs or normalizations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 36 | `36/36` | `6/6` | 0 | 0 | 6 |
| B | 36 | `31/36` | `6/6` | 0 | 0 | 1 |
| C | 36 | `36/36` | `6/6` | 0 | 0 | 6 |

### Canonical-refusal behavior

| Candidate | Raw canonical refusals | Application canonical refusals |
| --- | ---: | ---: |
| A | 0 | 6 |
| B | 5 | 6 |
| C | 0 | 6 |

## 4.7 Observation

All three candidates correctly classified the six unsupported development cases.

Candidate B produced five malformed raw JSON outputs:

```text
31 valid outputs from 36 runs
```

Candidate A and Candidate C both produced valid raw structured output in all 36 runs.

Candidate A and Candidate C also both recorded:

```text
0 invented requested attributes
```

Candidate C did not demonstrate a retained measurable advantage over Candidate A on the recorded experiment dimensions.

## 4.8 Decision

The selected grounded prompt was:

```text
Candidate A
```

Candidate A was selected because it provided:

- `36/36` structured JSON validity;
- `6/6` correct unsupported decisions;
- zero unsupported questions answered;
- zero invented requested attributes;
- a concise answerability contract;
- direct compatibility with retrieved chunk IDs and local citation resolution.

## 4.9 Why Candidate B Was Not Selected

Candidate B improved the frequency of raw canonical-refusal wording, but it produced malformed JSON in five of 36 runs.

The project prioritizes a reliable application contract over one isolated wording advantage.

## 4.10 Why Candidate C Was Not Selected

Candidate C matched Candidate A on the retained structural and unsupported metrics but did not provide a stronger practical advantage.

Selecting Candidate A avoided adding prompt complexity without measurable benefit.

## 4.11 Limitation

The development experiment primarily measured:

- structure;
- unsupported decisions;
- requested-attribute safety.

It was not a complete human semantic review of every answer.

Final evaluation later showed that a structurally valid grounded response may still be:

- partially complete;
- non-responsive;
- missing a clause;
- incorrect for an unsupported near-match.

## 4.12 Evidence

```text
data/evaluation/experiments/grounded_prompt_comparison.json
prompts/v2/grounded/candidate_a.system.txt
prompts/v2/grounded/candidate_a.user.txt
prompts/v2/schemas/grounded_output.schema.json
```

---

# Experiment 3 — Tone Prompt Family Comparison

## 5. Research Question

Does the Protected v2.1 tone-prompt family provide a clear overall advantage over the integrated Baseline v2 family in:

- structured-output reliability;
- factual preservation;
- language preservation;
- recognizable target style?

## 5.1 Hypothesis

More explicit semantic-protection instructions may improve preservation of numbers, conditions, authorities, and modality, but additional constraints may also reduce stylistic transformation or produce outputs that remain too close to the source.

## 5.2 Dataset

The experiment used:

```text
18 development tone inputs
3 tone types
2 prompt families
```

Each prompt-family and tone combination was evaluated over 18 runs.

Total recorded tone generations:

```text
18 inputs × 3 tones × 2 prompt families = 108 outputs
```

## 5.3 Controlled Variables

The following remained constant:

- development tone inputs;
- Granite generation model;
- temperature `0.0`;
- top-p `1.0`;
- output schema;
- repair policy;
- metric extraction logic.

## 5.4 Changed Variable

The changed variable was the tone-prompt family:

1. `baseline_v2`;
2. `protected_v2_1`.

Both families were evaluated for:

- `formal_report_summary`;
- `casual_message`;
- `concise_executive_briefing`.

## 5.5 Metrics

The experiment evaluated:

- JSON structure;
- source-language preservation;
- number preservation;
- unit preservation;
- currency preservation;
- approval-authority preservation;
- condition preservation;
- exception preservation;
- modality preservation;
- negation preservation;
- scope preservation;
- citation-metadata absence;
- exact-copy behavior;
- deterministic style signal.

### Important interpretation

`rough_style_signal` is a deterministic development proxy.

It is not:

- a human tone score;
- a complete semantic review;
- proof that a tone is naturally written;
- proof that three outputs are recognizably distinct.

Final tone quality was evaluated separately through human-reviewed Final-v2 evidence.

## 5.6 Key Results

| Prompt family and tone | Structure | Language | Numbers | Units | Modality | Authorities | Conditions | Rough style signal |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline — Casual | `18/18` | `18/18` | `13/15` | `7/8` | `3/9` | `6/7` | `6/6` | `8/18` |
| Baseline — Executive | `18/18` | `18/18` | `15/15` | `7/8` | `6/9` | `6/7` | `6/6` | `1/18` |
| Baseline — Formal | `18/18` | `17/18` | `13/15` | `7/8` | `7/9` | `7/7` | `5/6` | `18/18` |
| Protected — Casual | `18/18` | `18/18` | `15/15` | `8/8` | `8/9` | `6/7` | `6/6` | `4/18` |
| Protected — Executive | `18/18` | `17/18` | `15/15` | `7/8` | `8/9` | `7/7` | `6/6` | `0/18` |
| Protected — Formal | `18/18` | `17/18` | `14/15` | `8/8` | `9/9` | `7/7` | `6/6` | `17/18` |

## 5.7 Observation

Both prompt families produced:

```text
18/18 structurally valid outputs for every tone
```

Protected v2.1 improved several preservation dimensions during development, including:

- casual number preservation: `15/15` versus `13/15`;
- casual unit preservation: `8/8` versus `7/8`;
- casual modality preservation: `8/9` versus `3/9`;
- executive modality preservation: `8/9` versus `6/9`;
- formal modality preservation: `9/9` versus `7/9`.

However, Protected v2.1 did not demonstrate a consistent style advantage.

Its deterministic style signals were:

```text
Casual:     4/18
Executive:  0/18
Formal:    17/18
```

compared with Baseline v2:

```text
Casual:     8/18
Executive:  1/18
Formal:    18/18
```

The development evidence therefore showed a trade-off:

- stronger preservation in several protected-prompt dimensions;
- no decisive improvement in broad target-style signaling.

## 5.8 Decision

The selected tone-prompt family remained:

```text
Baseline v2
```

The decision was based on:

- complete structural reliability;
- full integration with the runtime;
- complete few-shot coverage;
- stable application behavior;
- no decisive overall recognizability advantage from the alternate family;
- avoidance of post-final prompt switching.

## 5.9 Final Generalization Check

The final evaluation used:

```text
20 inputs
× 3 tones
× 2 models
= 120 tone outputs
```

Final triplet-level results were:

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Fully valid tone triplets | `8/20` | `9/20` |
| Distinct tone triplets | `16/20` | `20/20` |
| Structurally valid individual outputs | `60/60` | `60/60` |

These results show that perfect development structure did not imply perfect final semantic and stylistic reliability.

The final set exposed brittleness that was not fully visible in the 18-input development comparison.

## 5.10 Limitation

The development experiment had several limitations:

- deterministic style signals are conservative proxies;
- 18 development inputs cannot represent every writing pattern;
- structurally valid JSON does not prove semantic preservation;
- the same prompt may interact differently with another generation model;
- development improvements may not generalize to the final holdout set.

## 5.11 Evidence

```text
data/evaluation/experiments/tone_prompt_comparison.json
prompts/v2/tones/
prompts/v2/few_shot/
prompts/v2/schemas/tone_output.schema.json
data/evaluation/final_v2/tone_results.jsonl
data/evaluation/final_v2/scoring/final_metrics.json
```

---

# Experiment 4 — Granite versus Mistral Model Comparison

## 6. Research Question

How does the primary Granite generation model compare with Mistral, a comparison model with a smaller nominal documented parameter count, when retrieval, prompts, data, parameters, and scoring remain fixed?

## 6.1 Hypothesis

The two models may show different trade-offs between:

- answerable-question completeness;
- unsupported-question refusal;
- citation validity;
- factual preservation;
- tone distinctness.

A smaller nominal model does not necessarily perform worse on every application dimension.

## 6.2 Dataset

The controlled Final-v2 comparison used:

```text
24 grounded questions
├── 20 answerable
└── 4 unsupported

20 tone inputs
× 3 tones
= 60 tone outputs per model
```

Across both models, the retained evidence contains:

```text
48 grounded model results
120 tone outputs
```

## 6.3 Controlled Variables

The following remained constant:

- corpus;
- selected FAISS index;
- Top-5 retrieval;
- retrieved contexts;
- embedding model and query embeddings;
- Candidate A grounded prompts;
- Baseline-v2 tone prompts;
- few-shot examples;
- output schemas;
- temperature `0.0`;
- top-p `1.0`;
- repair policy;
- final grounded questions;
- final tone inputs;
- evaluation rubric.

## 6.4 Changed Variable

Only the generation model changed.

### Primary model

```text
ibm/granite-4-h-small
```

### Comparison model

```text
mistralai/mistral-small-3-1-24b-instruct-2503
```

The comparison model is described using its smaller nominal documented parameter count.

Pricing evidence was not retained:

```json
{
  "pricing_evidence": null
}
```

Therefore, the project does not claim that the comparison model was cheaper in the tested environment.

## 6.5 Grounded Metrics

| Metric | Granite | Mistral |
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
| Repair count | 0 | 0 |

## 6.6 Tone Metrics

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Tone input triplets | 20 | 20 |
| Fully valid triplets | `8/20` | `9/20` |
| Fully valid triplet rate | `0.40` | `0.45` |
| Distinct triplets | `16/20` | `20/20` |
| Distinct triplet rate | `0.80` | `1.00` |
| Structurally valid outputs | `60/60` | `60/60` |

## 6.7 Metric Deltas

Using:

```text
comparison result − primary result
```

the retained model-comparison artifact records:

| Metric delta | Result |
| --- | ---: |
| Answerable correct-rate delta | `-0.05` |
| Strict grounded-accuracy delta | `0.00` |
| Fully valid triplet-rate delta | `+0.05` |
| Distinct triplet-rate delta | `+0.20` |

## 6.8 Observation

Granite produced:

- one additional fully correct answerable result;
- two fewer partial answerable results;
- one additional citation-valid record.

Mistral produced:

- correct refusal on all four unsupported questions;
- one additional fully valid tone triplet;
- distinct tone triplets for all 20 inputs.

Both models achieved the same strict grounded accuracy:

```text
20/24 = 0.8333
```

## 6.9 Decision

Granite remained the primary runtime model because the main application prioritizes grounded answer quality and complete answerable responses.

Mistral remained the comparison model because it demonstrated useful strengths in:

- unsupported refusal;
- tone distinction;
- comparable strict overall grounded accuracy.

The result is not interpreted as one model being universally superior.

Instead, the comparison demonstrates a task-dependent trade-off:

```text
Granite → stronger fully correct answerable count
Mistral → stronger unsupported refusal and tone distinctness
```

## 6.10 Review Method

The final model comparison uses the owner-verified hybrid scoring layer:

```text
Scoring layer:                  owner_verified_hybrid_final
Grounded semantic decisions:   24 reviewed
Tone triplets:                 40 reviewed
Independent owner signoff:     true
```

## 6.11 Limitation

The comparison measures performance under one common application contract.

It does not represent:

- each model’s individually optimized prompt configuration;
- a broad general-domain benchmark;
- a cost benchmark;
- a latency benchmark;
- a production-scale enterprise evaluation.

Using the same prompts improves fairness but may not maximize either model’s best possible performance.

## 6.12 Evidence

```text
data/evaluation/experiments/model_comparison.json
data/evaluation/final_v2/scoring/model_comparison.json
data/evaluation/final_v2/scoring/final_metrics.json
data/evaluation/final_v2/grounded_results.jsonl
data/evaluation/final_v2/tone_results.jsonl
data/evaluation/final_v2/human_review/owner_adjudication.json
```

---

# 7. Cross-Experiment Decision Chain

The final selected configuration is the result of the following sequence:

```text
Controlled synthetic corpus
        ↓
Compare chunk size and overlap
        ↓
Select 220 / 40
        ↓
Compare grounded Candidate A / B / C
        ↓
Select Candidate A
        ↓
Compare Baseline v2 / Protected v2.1 tone prompts
        ↓
Retain Baseline v2
        ↓
Freeze corpus, index, prompts, and parameters
        ↓
Run Final v2 with Granite and Mistral
        ↓
Score retrieval, grounding, refusal, citations, and tones
        ↓
Perform owner verification
        ↓
Retain metrics and failures without post-final tuning
```

---

# 8. Selected Final Configuration

| Component | Final selection |
| --- | --- |
| Corpus | `asteron-policies-v2.1` |
| Chunk size | 220 tokens |
| Chunk overlap | 40 tokens |
| Vector index | FAISS `IndexFlatIP` |
| Retrieval | Top-5 |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Embedding dimension | 768 |
| Grounded prompt | Candidate A |
| Tone prompt family | Baseline v2 |
| Primary generation model | `ibm/granite-4-h-small` |
| Comparison generation model | `mistralai/mistral-small-3-1-24b-instruct-2503` |
| Temperature | `0.0` |
| Top-p | `1.0` |
| Maximum repair retries | 1 |

---

# 9. Historical Context

Earlier exploratory and Final-v1-related artifacts may remain in the repository for auditability and chronology.

They are not treated as the active selection evidence for the submitted Final-v2 system.

The authoritative active experiment chain is:

```text
data/evaluation/experiments/retrieval_chunking_comparison.json
data/evaluation/experiments/grounded_prompt_comparison.json
data/evaluation/experiments/tone_prompt_comparison.json
data/evaluation/experiments/model_comparison.json
```

The final evaluated system is defined by:

```text
data/manifests/frozen/
data/evaluation/final_v2/
data/indexes/selected/
prompts/v2/
```

Historical evidence must not be mixed with Final-v2 metrics or described as the current runtime.

---

# 10. Experiment Integrity

The project applies the following experiment-integrity rules:

1. Development experiments are separated from the final evaluation.
2. Only one main variable is changed per controlled comparison.
3. Final raw outputs are preserved.
4. Weak or failed outputs are not rewritten.
5. The final prompts are not tuned after Final-v2 scoring.
6. The selected FAISS index is not rebuilt during ordinary validation.
7. Model comparison uses shared retrieval and prompts.
8. Pricing claims are excluded without retained evidence.
9. Deterministic proxy metrics are not presented as human judgments.
10. Structural validity is not presented as proof of semantic correctness.
11. Live smoke tests remain separate from frozen metrics.
12. Final metrics remain traceable to machine-readable artifacts.

---

# 11. Main Findings

## Retrieval

All three development chunking candidates tied on the retained retrieval metrics.

The selected `220/40` configuration later achieved:

```text
Hit@5 = 1.00
MRR = 0.975
```

on the final retrieval set.

## Grounded prompt

Candidate A and Candidate C were structurally reliable, while Candidate B produced five malformed JSON outputs.

Candidate A was selected because it combined reliable structure with a simple answerability and citation-ID contract.

## Tone prompts

Protected v2.1 improved several preservation measures during development but did not establish a decisive overall style advantage.

Baseline v2 remained the frozen selected prompt family.

## Model comparison

Granite and Mistral tied on strict grounded accuracy.

Their strengths differed:

```text
Granite:
- more fully correct answerable outputs;
- fewer partial answerable outputs;
- one more citation-valid record.

Mistral:
- perfect unsupported refusal in the saved set;
- more fully valid tone triplets;
- complete tone-triplet distinctness.
```

---

# 12. Experiment Limitations

The experiments should be interpreted within the project’s scope.

### Synthetic corpus

Results may not transfer directly to noisy enterprise documents.

### Small retrieval index

Exact FAISS search over 70 vectors does not represent large-scale vector-database behavior.

### Development-set size

The retrieval, grounded-prompt, and tone-prompt development sets are intentionally controlled but limited.

### Prompt and model interaction

A prompt that performs well with one model may behave differently with another.

### Deterministic proxies

Metrics such as `rough_style_signal` are useful for screening but do not replace human review.

### External model behavior

Future live responses may vary even with temperature `0.0`.

### No individual model optimization

The model comparison uses a common prompt configuration for fairness rather than separately optimizing each model.

---

# 13. Final Experiment Status

```text
Retrieval/chunking comparison:   Complete
Grounded Candidate A/B/C test:   Complete
Tone prompt-family comparison:   Complete
Generation-model comparison:     Complete
Numerical results retained:      Complete
Controlled variables recorded:   Complete
Selection decisions documented:  Complete
Limitations documented:          Complete
Final configuration frozen:      Complete
Post-final prompt tuning:         Not performed
Owner verification:              Complete
```

The project therefore exceeds the assignment requirement of at least three documented chunking and prompt experiments with written observations.