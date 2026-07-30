# Design Decisions and Engineering Rationale

## Document Purpose

This document records the main engineering decisions behind the final Prompting and RAG Foundations implementation.

Each decision is presented using the same structure:

- **Decision**
- **Alternatives considered**
- **Evidence**
- **Trade-off**
- **Final rationale**

The purpose is to make the final architecture explainable and auditable without presenting undocumented assumptions or private reasoning.

All decisions are based on:

- the original project requirements;
- retained development experiments;
- the implemented code;
- the frozen Final-v2 configuration;
- saved evaluation evidence;
- offline and live validation results.

---

## Final Decision Summary

| Area | Final decision |
| --- | --- |
| Knowledge domain | Synthetic company-policy corpus |
| Source format | Structured Markdown |
| Ingestion | Manifest-backed, section-aware deterministic loading |
| Chunking method | Token-aware fixed-size windows inside sections |
| Chunk size and overlap | 220 tokens with 40-token overlap |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Vector store | FAISS `IndexFlatIP` |
| Similarity | Cosine similarity through normalized vectors |
| Retrieval depth | Top-5 |
| Grounded prompt | Candidate A |
| Grounded output | Strict JSON validated with Pydantic |
| Citations | Model returns retrieved chunk IDs; application resolves metadata locally |
| Unsupported answer | Canonical refusal with `is_answerable=false` and empty citations |
| Malformed output | Maximum of one bounded repair retry |
| Tone design | Three separate prompt pairs with three few-shot examples each |
| Generation sampling | Temperature `0.0`, top-p `1.0` |
| Primary model | `ibm/granite-4-h-small` |
| Comparison model | `mistralai/mistral-small-3-1-24b-instruct-2503` |
| Runtime configuration | Frozen selected configuration and protected hashes |
| Interface | CLI with human-readable and JSON modes |
| Logging | Project-only logger on `stderr` |
| Packaging model | Editable installation from a repository checkout |
| Validation strategy | Offline tests, validators, dry-run, preflight, and archive isolation |

---

# 1. Use a Synthetic Company-Policy Corpus

## Decision

Use five fictional company-policy documents designed specifically for controlled RAG development and evaluation.

## Alternatives considered

1. Real internal company policies.
2. Publicly available company or government reports.
3. Product manuals.
4. A smaller set of unstructured example paragraphs.
5. A generated synthetic policy corpus with known ground truth.

## Evidence

The original assignment allowed the document domain to be selected freely and identified company policies as a suitable default.

The final corpus provides:

```text
5 documents
60 sections
89 registered facts
70 selected retrieval chunks
```

The corpus includes:

- direct facts;
- numeric thresholds;
- approval authorities;
- conditions;
- exceptions;
- related concepts;
- distractor clauses;
- cross-section questions;
- unsupported questions.

The complete corpus is versioned as:

```text
asteron-policies-v2.1
```

## Trade-off

### Benefits

- Known and reviewable ground truth.
- No private or confidential material.
- Reproducible evaluation.
- Precise diagnosis of retrieval and generation errors.
- Easy inclusion in the repository.

### Costs

- Less natural variation than a large real enterprise corpus.
- No OCR, PDF-layout, table-extraction, or document-permission challenges.
- Results cannot be generalized directly to production policy assistants.

## Final rationale

A controlled synthetic corpus was the most appropriate choice for a six-day Tier-1 assignment because it enabled reliable retrieval, grounding, refusal, and citation evaluation without privacy or licensing concerns.

---

# 2. Use Structured Markdown as the Source Format

## Decision

Store the source corpus as UTF-8 Markdown files with explicit section headings.

## Alternatives considered

1. PDF documents.
2. Plain-text files without headings.
3. HTML pages.
4. Word documents.
5. JSON records containing isolated facts.
6. Structured Markdown documents.

## Evidence

The assignment focuses on RAG and prompting foundations rather than OCR or document-layout extraction.

Markdown provides:

- visible document structure;
- deterministic section headings;
- readable source files;
- straightforward version control;
- direct mapping from headings to citations.

The final documents each contain 12 defined policy sections.

## Trade-off

### Benefits

- Simple and deterministic parsing.
- Human-readable source files.
- Clean section provenance.
- No extraction noise from page numbers, headers, or footers.

### Costs

- Does not represent common production PDF ingestion problems.
- Assumes headings and source encoding are well formed.
- Does not test table, image, or layout extraction.

## Final rationale

Markdown isolates the intended RAG learning objectives—chunking, retrieval, grounding, citations, and prompts—without adding unrelated OCR and layout complexity.

---

# 3. Use Manifest-Backed Deterministic Ingestion

## Decision

Load documents through a versioned manifest instead of scanning all files in a directory.

## Alternatives considered

1. Recursively load every Markdown file.
2. Hard-code a list of filenames inside Python.
3. Store all source text directly in code.
4. Use a versioned manifest containing document identity and integrity metadata.

## Evidence

The final manifest records:

- corpus version;
- document IDs;
- titles;
- source paths;
- owners;
- expected section headings;
- section counts;
- word counts;
- SHA-256 source checksums;
- synthetic-content declarations.

The corpus validator confirms:

```text
Documents: 5
Sections: 60
Facts: 89
```

## Trade-off

### Benefits

- Deterministic file selection and order.
- Detects missing, renamed, or modified source documents.
- Separates document identity from filesystem discovery.
- Supports version and checksum validation.

### Costs

- The manifest must be updated when the corpus changes.
- A source change requires coordinated updates to derived artifacts.
- More initial setup than directory scanning.

## Final rationale

A versioned manifest makes the knowledge base explicit, reproducible, and auditable. This is more suitable for a frozen evaluation than implicit filesystem discovery.

---

# 4. Preserve Markdown Sections During Parsing

## Decision

Treat Markdown section headings as retrieval and citation boundaries before applying token-based chunking.

## Alternatives considered

1. Split the entire document into fixed windows without section awareness.
2. Split only on paragraphs.
3. Split only on sentences.
4. Use model-based semantic segmentation.
5. Preserve document sections and split only sections that exceed the token limit.

## Evidence

The assignment requires every grounded answer to identify:

- the source document;
- the source section.

The corpus has stable and meaningful section headings. The final selected metadata records retain a section heading for every chunk.

## Trade-off

### Benefits

- Direct section-level provenance.
- Cleaner document and section citations.
- Reduces chunks that mix unrelated policy sections.
- Makes retrieved evidence easier to inspect.

### Costs

- Depends on consistent Markdown structure.
- Long sections still require secondary splitting.
- Very short neighboring sections are not automatically merged.

## Final rationale

Section-aware parsing directly supports the citation requirement and preserves the policy structure that a reviewer expects to see.

---

# 5. Use Token-Aware Fixed-Size Chunking

## Decision

Apply deterministic token-aware windows within sections.

## Alternatives considered

1. Character-count chunking.
2. Word-count chunking.
3. Sentence-only splitting.
4. Paragraph-only splitting.
5. Model-based semantic chunking.
6. Token-aware fixed-size windows with overlap.

## Evidence

Generation and embedding models process tokens rather than characters or words.

Token-aware chunking provides a predictable relationship between:

- chunk length;
- context size;
- embedding input size;
- generation prompt size.

The selected chunk metadata records the token count for every chunk.

## Trade-off

### Benefits

- Predictable chunk sizes.
- Reproducible output.
- Compatible with model context constraints.
- Easier controlled comparison between configurations.

### Costs

- Requires a tokenizer asset.
- A fixed limit does not always align perfectly with semantic boundaries.
- Tokenizer availability or cache state may affect a full rebuild.

## Final rationale

Token-aware fixed windows offered the clearest controlled experiment for a foundational project, while section preservation limited the main weakness of arbitrary fixed-size splitting.

---

# 6. Select 220 Tokens with 40-Token Overlap

## Decision

Use:

```text
Chunk size:     220 tokens
Chunk overlap:  40 tokens
```

## Alternatives considered

The retained development comparison evaluated:

1. `160 / 20`
2. `160 / 60`
3. `220 / 40`

## Evidence

The retained development experiment recorded the following Top-5 results:

| Chunk size / overlap | Expected-source Hit@5 | Multi-source full-coverage count |
| --- | ---: | ---: |
| `160 / 20` | `0.9444` | 5 |
| `160 / 60` | `0.9444` | 5 |
| `220 / 40` | `0.9444` | 5 |

The three candidates tied on the retained development retrieval measures.

The selected `220/40` configuration produced:

```text
70 chunks
70 vectors
70 metadata records
```

Final retrieval later confirmed strong behavior:

```text
Hit@1: 0.95
Hit@3: 1.00
Hit@5: 1.00
MRR:   0.975
```

The final results were used to confirm the frozen configuration, not to select it after final testing.

## Trade-off

### `160 / 20`

- More focused windows.
- Less repeated context.
- Greater risk that a condition and its exception appear in separate chunks.

### `160 / 60`

- Higher boundary protection.
- More repeated content.
- Greater retrieval redundancy.

### `220 / 40`

- More context per chunk.
- Moderate overlap.
- Potentially less granular than a 160-token window.

## Final rationale

Because all three configurations tied on the retained development retrieval measures, `220/40` was selected as a balanced configuration that retained complete clauses with moderate overlap and no demonstrated retrieval disadvantage.

No claim is made that the choice was selected using the final test set or that it produced a smaller index unless directly supported by a measured artifact.

---

# 7. Use Watsonx Granite Multilingual Embeddings

## Decision

Use:

```text
ibm/granite-embedding-278m-multilingual
```

with an expected vector dimension of:

```text
768
```

## Alternatives considered

1. A different Watsonx embedding model.
2. A local sentence-transformer embedding model.
3. API embeddings from another provider.
4. Sparse keyword vectors.
5. The selected Watsonx multilingual embedding model.

## Evidence

The assigned stack is IBM watsonx.ai.

The selected model:

- is available through Watsonx;
- supports multilingual text;
- produces the 768-dimensional vectors stored in the selected FAISS index;
- was successfully used during index construction;
- was successfully used during live query smoke tests.

The selected index configuration and preflight both verify the exact model ID and dimension.

## Trade-off

### Benefits

- Direct alignment with the required platform.
- One embedding architecture for document and query text.
- Supports multilingual-query experiments.
- Avoids adding a separate local embedding framework.

### Costs

- Live embedding requires Watsonx credentials and network access.
- A complete index rebuild depends on external service availability.
- Service-side model behavior may change outside the repository.

## Final rationale

The selected model satisfies the Watsonx stack requirement and provides one consistent embedding space for the frozen document index and live user questions.

---

# 8. Use FAISS `IndexFlatIP`

## Decision

Store normalized vectors in a persistent FAISS `IndexFlatIP` index.

## Alternatives considered

1. Chroma.
2. A managed cloud vector database.
3. Watsonx-managed retrieval.
4. An in-memory NumPy similarity search.
5. FAISS approximate-nearest-neighbor indexes.
6. FAISS exact inner-product search.

## Evidence

The project has a small frozen corpus:

```text
70 vectors
768 dimensions
```

At this scale, exact search is computationally practical.

Vectors are L2-normalized, allowing:

```text
inner product = cosine similarity
```

The selected store persists:

```text
FAISS binary
metadata.json
index_config.json
```

## Trade-off

### Benefits

- Lightweight local persistence.
- Exact nearest-neighbor results.
- No additional database server.
- Works in offline tests after index creation.
- Easy to include and validate in the repository.

### Costs

- FAISS does not provide document permissions or metadata filtering by itself.
- No distributed scaling or managed lifecycle.
- Metadata must be maintained separately.
- A flat index is not designed for very large enterprise collections.

## Final rationale

FAISS `IndexFlatIP` is appropriate for a small controlled benchmark because it is simple, exact, local, and easy to reproduce without introducing infrastructure unrelated to the assignment.

---

# 9. Normalize Vectors and Interpret Inner Product as Cosine Similarity

## Decision

L2-normalize document and query vectors before FAISS search.

## Alternatives considered

1. Raw inner-product similarity.
2. Euclidean distance.
3. Cosine similarity implemented manually with NumPy.
4. Normalized vectors with FAISS inner-product search.

## Evidence

The selected index configuration records cosine similarity behavior.

Normalizing both vectors allows FAISS `IndexFlatIP` to rank by cosine similarity while retaining the standard FAISS search interface.

## Trade-off

### Benefits

- Semantically interpretable similarity measure.
- Efficient exact search through FAISS.
- Consistent document and query processing.

### Costs

- Normalization must be applied consistently.
- Incorrectly mixing normalized and unnormalized vectors would invalidate scores.
- Similarity values are specific to the selected embedding space.

## Final rationale

Normalized inner-product search provides the desired cosine-ranking behavior with minimal implementation complexity.

---

# 10. Use Top-5 Retrieval

## Decision

Retrieve the five nearest chunks for each grounded question.

## Alternatives considered

1. Top-1.
2. Top-3.
3. Top-5.
4. Top-10.
5. Dynamic Top-K based on a similarity threshold.

## Evidence

The development process included questions requiring:

- multiple clauses;
- multiple sections;
- more than one expected source;
- separation of a rule from related distractors.

Top-1 was considered too restrictive for multi-source questions. Higher retrieval depths introduce more irrelevant context and larger grounded prompts.

Top-5 was frozen during development before final evaluation.

The final retrieval results later confirmed:

| Metric | Result |
| --- | ---: |
| Hit@1 | `0.95` |
| Hit@3 | `1.00` |
| Hit@5 | `1.00` |
| All-expected-source coverage@5 | `0.90` |

## Trade-off

### Lower Top-K

- Smaller prompt.
- Less distractor text.
- Greater risk of missing a second required section.

### Higher Top-K

- More possible evidence.
- More token use.
- Greater chance of irrelevant or competing clauses.
- More context for the generation model to reconcile.

## Final rationale

Top-5 provides enough evidence capacity for multi-section questions without unnecessarily expanding the prompt to ten or more chunks.

The final metrics are reported as confirmation, not as the basis for post-final selection.

---

# 11. Select Grounded Prompt Candidate A

## Decision

Use Candidate A as the frozen grounded-generation prompt.

## Alternatives considered

The retained grounded-prompt experiment compared:

1. Candidate A.
2. Candidate B.
3. Candidate C.

## Evidence

The retained experiment summary recorded:

| Candidate | Runs | Application-valid structured outputs | Unsupported decisions correct | Unsupported questions answered incorrectly |
| --- | ---: | ---: | ---: | ---: |
| A | 36 | 36 | 6 | 0 |
| B | 36 | 31 | 6 | 0 |
| C | 36 | 36 | 6 | 0 |

Candidate B produced five malformed outputs before successful application-level handling.

Candidate A and Candidate C tied on the retained structural and unsupported-decision measures.

Candidate A’s contract aligned directly with the implemented schema:

- explicit answerability;
- context-only answer;
- citation chunk IDs;
- canonical unsupported response;
- no arbitrary document metadata generated by the model.

Candidate C did not demonstrate a retained measurable advantage sufficient to justify additional prompt complexity or a different final contract.

## Trade-off

### Benefits

- Complete application-level structured validity in the retained comparison.
- Correct unsupported decisions in the development comparison.
- Direct compatibility with the application schema.
- Clear citation-ID contract.

### Costs

- Prompt instructions cannot guarantee perfect semantic behavior.
- A structurally valid answer may still be incomplete.
- The model may still associate an unsupported question with a related retrieved rule.

## Final rationale

Candidate A was selected because it combined stable structured behavior, correct development unsupported decisions, and direct compatibility with the final answerability and citation architecture.

It was not selected merely because it was later frozen.

---

# 12. Require Structured JSON and Pydantic Validation

## Decision

Require grounded and tone model outputs to follow explicit JSON contracts and validate them with Pydantic.

## Alternatives considered

1. Free-form text output.
2. Markdown sections.
3. Regex extraction from natural language.
4. Provider-specific structured-output features only.
5. Prompted JSON with application-level parsing and schema validation.

## Evidence

The assignment explicitly requires consistent structured tone output and graceful malformed-output handling.

The project retains:

```text
prompts/v2/schemas/grounded_output.schema.json
prompts/v2/schemas/tone_output.schema.json
```

The final saved tone evaluation produced:

```text
120 / 120 structurally valid tone outputs
```

Automated tests also exercise malformed JSON behavior.

## Trade-off

### Benefits

- Predictable application contract.
- Machine-readable CLI output.
- Explicit answerability and tone fields.
- Stronger validation than free-form text parsing.
- Clear failure handling.

### Costs

- Models may occasionally produce malformed JSON.
- A valid JSON object can still contain a semantically weak answer.
- Schema validation adds implementation complexity.

## Final rationale

Structured JSON is essential for reliable application behavior, but the project intentionally evaluates semantic correctness separately from structural validity.

---

# 13. Resolve Citations Locally from Retrieved Chunk IDs

## Decision

Allow the model to return only citation IDs from the retrieved context, then resolve authoritative citation metadata locally.

## Alternatives considered

1. Ask the model to generate document titles and section names freely.
2. Match answer sentences to documents after generation.
3. Return no citations.
4. Return retrieved chunk IDs and resolve metadata from the local store.

## Evidence

The acceptance criteria require document and section citations.

The local metadata store already contains:

- document ID;
- document title;
- section heading;
- source path;
- supporting text;
- corpus version;
- index ID.

The application rejects citation IDs that are not in the current retrieved set.

## Trade-off

### Benefits

- Reduces fabricated citation metadata.
- Keeps source titles and section names authoritative.
- Connects every citation to current retrieval evidence.
- Supports source paths and supporting quotes.

### Costs

- The model must reference valid retrieved chunk IDs.
- Citation validation can fail even when answer text is broadly correct.
- Correct citations do not independently guarantee answer completeness.

## Final rationale

Local resolution is safer and more auditable than allowing a language model to invent final source metadata.

---

# 14. Use a Canonical Unsupported Refusal

## Decision

Normalize supported unsupported decisions to:

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

## Alternatives considered

1. Allow a free-form refusal.
2. Return an empty answer.
3. Use only a similarity-score threshold.
4. Return the nearest related policy with a warning.
5. Use an explicit model answerability decision and canonical refusal.

## Evidence

The assignment requires a clear “I don't know” instead of guessing.

The live unsupported smoke test returned the canonical refusal correctly.

The final evaluation also measured unsupported behavior separately:

| Model | Correct unsupported refusals |
| --- | ---: |
| Granite | `3/4` |
| Mistral | `4/4` |

## Trade-off

### Benefits

- Consistent user experience.
- Easy automated evaluation.
- Empty citations clearly indicate no supporting evidence.
- Avoids stylistic variation in unsupported responses.

### Costs

- Fixed wording is less conversational.
- Model answerability classification is not infallible.
- Vector retrieval always returns nearest chunks even when none truly answer the question.

## Final rationale

A canonical refusal creates a clear and testable unsupported contract. The measured evaluation is reported honestly rather than treating the refusal instruction as an absolute guarantee.

---

# 15. Use One Bounded Repair Retry

## Decision

Allow at most one repair-generation attempt for each malformed grounded or tone output.

## Alternatives considered

1. No repair.
2. Unlimited retries until valid JSON appears.
3. Multiple fixed retries.
4. Local heuristic rewriting only.
5. One bounded model-assisted repair retry.

## Evidence

Models can return:

- text outside JSON;
- malformed quoting;
- missing required fields;
- an incorrect tone identifier;
- invalid citation structures.

The assignment requires the pipeline to handle malformed output without crashing.

The saved final run required:

```text
0 repair retries
```

while automated tests verify the repair path.

## Trade-off

### No retry

- Lowest latency and call count.
- More user-visible failures from small formatting errors.

### Unlimited or multiple retries

- Higher chance of eventual valid output.
- Unbounded cost, latency, and inconsistency risk.

### One retry

- Handles common formatting failures.
- Adds at most one call for the affected generated object.
- May still fail after the retry.

## Final rationale

One repair retry provides graceful recovery while keeping external-call growth, latency, and failure behavior bounded.

---

# 16. Use Three Separate Tone Prompts

## Decision

Define an independent prompt pair for each supported tone:

1. `formal_report_summary`
2. `casual_message`
3. `concise_executive_briefing`

## Alternatives considered

1. One shared prompt with only a tone-name variable.
2. A single generic rewrite instruction.
3. Fine-tuning a model for style.
4. Three independent system and user prompt templates.

## Evidence

The assignment requires three recognizably different tones and emphasizes system-prompt design.

Separate prompt pairs allow each tone to define:

- vocabulary;
- structure;
- degree of formality;
- target audience;
- concision;
- prohibited style behavior.

The final evaluation retained:

```text
20 tone inputs
3 tones
2 models
120 tone outputs
```

Tone distinctness results were:

| Model | Distinct three-tone sets |
| --- | ---: |
| Granite | `16/20` |
| Mistral | `20/20` |

## Trade-off

### Benefits

- Stronger and more explicit tone definitions.
- Easier independent prompt development.
- More recognizable differences than one generic prompt.

### Costs

- More prompt assets to maintain.
- Greater risk of prompt drift between tones.
- Each requested tone requires an additional generation call for answerable results.

## Final rationale

Independent templates provide the clearest way to teach and evaluate prompt-controlled style differences, which is a central learning objective of the assignment.

---

# 17. Include Three Few-Shot Examples per Tone

## Decision

Store three representative examples in one JSON file for each tone.

## Alternatives considered

1. Zero-shot instructions only.
2. One example per tone.
3. Three examples per tone.
4. A large prompt library.
5. Fine-tuning.

## Evidence

The assignment requires at least one few-shot example per tone.

The final project contains:

```text
formal.json     → 3 examples
casual.json     → 3 examples
executive.json  → 3 examples
```

The examples demonstrate:

- expected output shape;
- style characteristics;
- factual preservation;
- numeric and condition handling;
- language preservation expectations.

## Trade-off

### Benefits

- Exceeds the minimum requirement.
- Gives the model multiple style demonstrations.
- Makes the structured output shape concrete.

### Costs

- Increases prompt length and token usage.
- Poorly selected examples could introduce style bias.
- Few-shot prompting does not guarantee semantic equivalence.

## Final rationale

Three examples provide broader tone guidance than a single example while keeping prompt size practical.

---

# 18. Retain Baseline-v2 Tone Prompts

## Decision

Keep the integrated baseline-v2 tone prompt set as the final selected tone configuration.

## Alternatives considered

1. Baseline-v2 prompts.
2. Protected v2.1 alternate tone prompts.
3. Redesign all tone prompts after final evaluation.
4. Use different prompt sets for the two models.

## Evidence

The development comparison evaluated the baseline and alternate prompt designs using:

- structured validity;
- language preservation;
- numeric preservation;
- unit preservation;
- authority preservation;
- condition preservation;
- exception preservation;
- negation and modality preservation;
- deterministic style proxies.

The alternate design did not demonstrate a decisive overall advantage across the retained development measures.

The baseline prompt set was already:

- complete for all three tones;
- integrated with the runtime;
- covered by tests;
- compatible with the selected schema;
- paired with three few-shot examples per tone.

The final tone evaluation later showed that tone transformation remained a more challenging task than structural JSON generation. Those final outcomes were documented rather than used for post-final prompt switching.

## Trade-off

### Benefits

- Stable integrated runtime behavior.
- Avoids post-final configuration changes.
- Preserves reproducibility of saved tone evidence.

### Costs

- Some final tone outputs remain imperfect in factual or style preservation.
- A future prompt redesign may improve individual tones.
- Development proxies did not fully predict final human-reviewed performance.

## Final rationale

Baseline v2 remained selected because the alternate design did not show a decisive retained advantage, and changing prompts after final evaluation would weaken the integrity of the frozen comparison.

---

# 19. Use Temperature 0.0 and Top-p 1.0

## Decision

Use:

```text
temperature = 0.0
top_p = 1.0
```

for the final grounded and tone evaluation configuration.

## Alternatives considered

1. Higher temperature for more diverse output.
2. Reduced top-p nucleus sampling.
3. Different parameters for each tone.
4. Deterministic low-variance generation settings.

## Evidence

The project evaluates:

- correctness;
- refusal behavior;
- citation validity;
- factual preservation;
- style adherence;
- model differences.

High output variation would make repeated comparison and failure diagnosis less controlled.

The final configuration and saved artifacts consistently record temperature `0.0` and top-p `1.0`.

## Trade-off

### Benefits

- Lower stochastic variation.
- Easier model comparison.
- More reproducible prompt experiments.
- Cleaner failure analysis.

### Costs

- Less creative variation in casual rewriting.
- External model services may still produce non-identical results.
- Deterministic parameters do not guarantee deterministic service output.

## Final rationale

Low-variance generation settings are better suited to controlled RAG and prompt evaluation than creative sampling.

---

# 20. Use Granite 4 Small as the Primary Generation Model

## Decision

Use:

```text
ibm/granite-4-h-small
```

as the default generation model in the frozen CLI runtime.

## Alternatives considered

1. Mistral Small as the primary model.
2. Another Watsonx model.
3. Different primary models for grounding and tone.
4. Granite as primary with one controlled comparison model.

## Evidence

Final grounded results were:

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Answerable correct | `17/20` | `16/20` |
| Answerable partial | `2/20` | `4/20` |
| Unsupported correct | `3/4` | `4/4` |
| Citation-valid records | 20 | 19 |
| Strict overall accuracy | `20/24` | `20/24` |

Granite produced:

- one additional fully correct answerable result;
- fewer partial answerable results;
- one additional citation-valid record.

Mistral performed better on unsupported refusal.

## Trade-off

### Granite strengths

- Better fully correct answerable count.
- Fewer partial answers.
- Strong citation-validity count.
- Strong formal-tone result.

### Granite limitations

- One incorrect unsupported answer.
- Lower tone-triplet distinctness than Mistral.
- Casual and executive tone quality was less consistent.

## Final rationale

Granite was retained as the primary model because the project prioritizes grounded answer correctness and citation behavior in the main RAG workflow.

The model comparison is presented as multi-dimensional rather than claiming Granite is superior in every category.

---

# 21. Use Mistral Small 3.1 24B as the Comparison Model

## Decision

Use:

```text
mistralai/mistral-small-3-1-24b-instruct-2503
```

as the controlled comparison generation model.

## Alternatives considered

1. No model comparison.
2. A second Granite model.
3. A substantially larger model.
4. A different smaller model available through Watsonx.
5. Mistral Small 3.1 24B.

## Evidence

The assignment requires replacing the generation model with a smaller or cheaper alternative and evaluating the effect.

The retained comparison evidence supports describing Mistral by its smaller nominal documented parameter count relative to the primary model configuration.

No frozen pricing evidence was retained, so the project does not claim that Mistral was cheaper in the tested environment.

Mistral produced:

- `4/4` correct unsupported refusals;
- `20/20` distinct tone triplets;
- the same strict grounded accuracy as Granite: `0.8333`.

## Trade-off

### Benefits

- Provides a meaningful controlled comparison.
- Strong unsupported behavior.
- Strong tone distinctness.
- Available through the same Watsonx platform.

### Costs

- More partial answerable responses.
- One fewer citation-valid record.
- No supported project-level price conclusion.

## Final rationale

Mistral provides a credible controlled comparison because it changes the generation model while preserving the remaining runtime and evaluation variables.

---

# 22. Change Only the Generation Model During Model Comparison

## Decision

Hold retrieval, prompts, data, parameters, and scoring constant while changing only the generation model.

## Alternatives considered

1. Tune each model independently for its best possible result.
2. Use different prompts for each model.
3. Rebuild separate indexes for each model.
4. Keep all non-model variables constant.

## Evidence

The final comparison used the same:

- corpus;
- selected index;
- query retrieval results;
- Top-5 configuration;
- grounded prompt;
- tone prompts;
- few-shot examples;
- grounded questions;
- tone inputs;
- temperature;
- top-p;
- schemas;
- evaluation rubric.

## Trade-off

### Benefits

- Differences are easier to attribute to the generation model.
- Provides a fair controlled comparison.
- Avoids confounding prompt or retrieval changes.

### Costs

- A shared prompt may not be individually optimal for both models.
- The result measures performance under one common application contract, not each model’s maximum achievable performance.

## Final rationale

A controlled comparison is more defensible for the assignment than separately optimizing each model and comparing incomparable configurations.

---

# 23. Freeze the Final Configuration Before Final Evaluation

## Decision

Freeze the selected corpus, index, prompts, models, parameters, and final datasets before retaining the final results.

## Alternatives considered

1. Continue tuning after every final error.
2. Use the final test set as an ongoing development set.
3. Report only the best later rerun.
4. Separate development selection from final evaluation and freeze the selected configuration.

## Evidence

The repository preserves:

```text
data/manifests/frozen/frozen_configuration_v2.json
data/manifests/frozen/frozen_index_manifest_v2.json
data/manifests/frozen/frozen_prompt_manifest_v2.json
data/evaluation/final_v2/run_plan.json
```

Final outputs, scores, and owner review were preserved without rewriting failed responses.

## Trade-off

### Benefits

- Reduces test-set leakage.
- Preserves honest failures.
- Keeps metrics connected to one configuration.
- Supports reproducibility of saved evidence.

### Costs

- Known final errors remain visible.
- Improvements require a new development and evaluation cycle.
- The frozen runtime is less configurable.

## Final rationale

A frozen final configuration is necessary for a credible evaluation. Correcting individual final outputs through additional tuning would make the reported results less trustworthy.

---

# 24. Protect Final Assets with Hashes

## Decision

Use deterministic SHA-256 verification for prompts, source documents, selected indexes, and final evidence.

## Alternatives considered

1. Rely only on Git history.
2. Check filenames and file counts.
3. Store timestamps.
4. Protect key artifacts with byte or canonical-text hashes.

## Evidence

Protected areas include:

```text
prompts/
data/documents_v2_1/
data/evaluation/
data/indexes/
```

The final hardening pass confirmed unchanged aggregate hashes for all four areas.

The runtime verifies selected prompt and index assets before constructing live components.

## Trade-off

### Benefits

- Detects accidental artifact changes.
- Prevents silent prompt or index drift.
- Connects saved metrics to preserved inputs and outputs.

### Costs

- Legitimate changes require a deliberate new integrity workflow.
- Text normalization rules must be consistent.
- Hash verification does not prove semantic quality by itself.

## Final rationale

Hash protection is appropriate because the selected prompts, index, and evaluation outputs are evidence, not ordinary mutable runtime files.

---

# 25. Preserve Raw Outputs and Review Evidence

## Decision

Retain raw model outputs, application-level results, deterministic scores, failure analysis, and owner verification.

## Alternatives considered

1. Retain only aggregate metrics.
2. Replace weak outputs with corrected examples.
3. Retain only human-reviewed labels.
4. Preserve the complete compact evidence chain.

## Evidence

The repository retains:

```text
retrieval_results.json
grounded_results.jsonl
tone_results.jsonl
deterministic_scores.json
owner_adjudication.json
final_metrics.json
model_comparison.json
failure_analysis.md
```

The retained evidence supports tracing a reported metric back to individual saved outputs.

## Trade-off

### Benefits

- Strong auditability.
- Enables independent review.
- Prevents selective reporting.
- Preserves failures as learning evidence.

### Costs

- Larger repository.
- More artifacts to validate.
- Documentation must distinguish raw, application-valid, reviewed, and final evidence.

## Final rationale

Aggregate metrics alone would not be sufficient to defend the evaluation. Preserving the evidence chain makes the report inspectable and credible.

---

# 26. Use a CLI Instead of a Larger User Interface

## Decision

Provide a command-line interface with readable and JSON output modes.

## Alternatives considered

1. Streamlit.
2. Flask or FastAPI.
3. A web frontend.
4. A notebook-only demonstration.
5. A CLI.

## Evidence

The assignment accepts a minimal UI **or** CLI.

The implemented CLI supports:

- grounded-only questions;
- one selected tone;
- all three tones;
- human-readable output;
- machine-readable JSON;
- safe help commands;
- non-zero exit codes for failures.

The CLI is covered by automated tests and offline CI.

## Trade-off

### Benefits

- Small implementation surface.
- Easy to test.
- Easy to run in CI.
- Suitable for piping JSON into other tools.
- Keeps focus on RAG and prompting.

### Costs

- Less visually engaging than a web interface.
- Requires terminal familiarity.
- No persistent conversation or interactive dashboard.

## Final rationale

A CLI satisfies the assignment while minimizing unrelated frontend work and maximizing testability and reproducibility.

---

# 27. Separate Project Logs from JSON Output

## Decision

Write project logs to `stderr` and reserve `stdout` for normal CLI output or valid JSON.

## Alternatives considered

1. Print all diagnostics to stdout.
2. Configure the global Python root logger.
3. Disable logging.
4. Configure only the `rag_foundations` logger namespace on stderr.

## Evidence

The CLI supports:

```powershell
python -m rag_foundations.cli ask --json "Question"
```

Machine-readable output must remain parseable.

Automated tests verify that:

- JSON stdout parses successfully;
- project diagnostics appear on stderr;
- repeated configuration does not duplicate handlers;
- the root logger is not reset;
- third-party debug logging is not globally enabled.

## Trade-off

### Benefits

- Clean machine-readable output.
- Safe use in shell pipelines.
- No global effect on IBM SDK, HTTP, or host-application loggers.
- Configurable project diagnostics.

### Costs

- Users must capture stderr separately when debugging.
- Logger-handler ownership requires explicit implementation.

## Final rationale

Separating output channels is a standard CLI design and is necessary for reliable `--json` behavior.

---

# 28. Use an Editable Repository Installation

## Decision

Support:

```powershell
python -m pip install -e ".[dev]"
```

from a repository checkout.

## Alternatives considered

1. A standalone wheel containing all assets.
2. A Docker-only distribution.
3. Running through `PYTHONPATH` without installation.
4. An editable package plus visible repository assets.

## Evidence

The runtime intentionally accesses:

```text
data/
prompts/
```

through repository-relative paths.

Keeping these resources visible makes:

- prompts reviewable;
- the corpus inspectable;
- index evidence accessible;
- evaluation artifacts easy to assess.

## Trade-off

### Benefits

- Transparent assessment.
- Simple local development.
- Prompt and data assets remain visible.
- Direct alignment with the repository’s frozen evidence.

### Costs

- The wheel is not documented as independently portable.
- Commands should be run from a valid repository checkout.
- Packaging the assets for production would require additional work.

## Final rationale

An editable checkout is appropriate for an educational repository whose prompts, data, and evaluation evidence are first-class deliverables.

---

# 29. Use Offline Validation as the Main Quality Gate

## Decision

Make tests, validators, dry-run, selected-index preflight, and archive isolation the primary repeatable validation path.

## Alternatives considered

1. Run live Watsonx requests in every CI build.
2. Validate only through unit tests.
3. Validate manually before submission.
4. Use comprehensive offline validation and targeted live smoke tests.

## Evidence

The final code state passes:

```text
306 automated tests
```

Offline validation covers:

- dependency consistency;
- Python compilation;
- Ruff;
- corpus integrity;
- reference and secret checks;
- Final-v2 evidence;
- project completeness;
- CLI help;
- Final-v2 dry-run;
- selected-index preflight;
- clean Git-archive execution.

The dry-run and preflight both report zero external calls.

## Trade-off

### Benefits

- Stable and repeatable CI.
- No credentials in GitHub Actions.
- No external service cost.
- No failures caused solely by model-service availability.
- Verifies the exact tracked repository.

### Costs

- Offline tests cannot fully prove current external service availability.
- Mocked model behavior does not replace live integration testing.

## Final rationale

Offline validation provides the strongest repeatable quality gate, while a small set of documented live smoke tests confirms Watsonx integration separately.

---

# 30. Keep Live Smoke Tests Separate from Frozen Metrics

## Decision

Document live supported, unsupported, and tone requests separately from the saved final evaluation.

## Alternatives considered

1. Add live smoke results directly to final metrics.
2. Rerun the complete evaluation live before every submission.
3. Use saved evaluation only.
4. Preserve frozen metrics and document live operational checks separately.

## Evidence

The frozen evaluation contains:

```text
24 grounded questions
20 tone inputs
2 generation models
48 grounded results
120 tone results
```

The live smoke tests confirm:

- authentication;
- query embedding;
- FAISS retrieval;
- grounded generation;
- citation resolution;
- unsupported refusal;
- tone execution.

Live outputs may vary with external service behavior.

## Trade-off

### Benefits

- Preserves reproducible saved metrics.
- Still demonstrates current end-to-end operation.
- Avoids mixing single live observations with controlled evaluation results.

### Costs

- Live smoke results are not a statistical benchmark.
- Future service behavior may differ from both saved and recorded live outputs.

## Final rationale

Frozen evaluation and live operational validation answer different questions and should remain clearly separated.

---

# 31. Do Not Add Stretch Goals to the Final Scope

## Decision

Stop at the complete Tier-1 requirements and do not add reranking, hybrid search, REST APIs, or self-evaluation before submission.

## Alternatives considered

1. Add a model reranker.
2. Add BM25 hybrid retrieval.
3. Add a fourth tone.
4. Add an API and frontend.
5. Finalize and validate the required scope.

## Evidence

The completed project already includes:

- all required ingestion and retrieval components;
- grounded generation and citations;
- unsupported refusal;
- three tones;
- few-shot prompting;
- malformed-output handling;
- four experiments;
- full evaluation;
- model comparison;
- CLI;
- 306 tests;
- live smoke testing.

The remaining stretch goals would add new variables requiring new experiments and regression testing.

## Trade-off

### Benefits

- Keeps the final repository focused.
- Reduces submission risk.
- Preserves the frozen evidence.
- Avoids introducing unvalidated features.

### Costs

- The final system does not demonstrate optional advanced retrieval methods.
- Production capabilities remain outside scope.

## Final rationale

Completing and defending the required system is more valuable than adding unvalidated stretch features immediately before submission.

---

# 32. Decision-to-Evidence Map

| Decision | Main evidence |
| --- | --- |
| Synthetic corpus | `docs/DATASET_CARD.md`, `data/manifest_v2_1.json` |
| Manifest-backed loading | `document_loader.py`, corpus validator |
| Section preservation | `document_loader.py`, selected metadata |
| Token-aware chunking | `chunking.py`, selected index config |
| 220/40 selection | `retrieval_chunking_comparison.json` |
| Granite embeddings | selected index config and frozen configuration |
| FAISS `IndexFlatIP` | `faiss_store.py`, selected index |
| Top-5 | frozen configuration and retrieval experiment |
| Candidate A | `grounded_prompt_comparison.json` |
| Structured JSON | schemas, Pydantic models, tests |
| Local citations | frozen runtime and retrieved metadata |
| Canonical refusal | grounded prompt, tests, final outputs |
| One repair retry | generation modules and malformed-output tests |
| Three tone prompts | `prompts/v2/tones/` |
| Three examples per tone | `prompts/v2/few_shot/` |
| Baseline-v2 tones | `tone_prompt_comparison.json` |
| Temperature 0 / top-p 1 | frozen configuration and run plan |
| Granite primary | final metrics and model comparison |
| Mistral comparison | final metrics and model comparison |
| Frozen configuration | frozen manifests |
| Protected hashes | `protected_hashes.json`, integrity module |
| CLI | `cli.py` and CLI tests |
| Project-only logging | `logging_config.py` and CLI tests |
| Editable installation | `pyproject.toml`, runtime asset layout |
| Offline quality gate | CI workflow and validators |
| Separate live smoke tests | `docs/LIVE_SMOKE_TEST.md` |

---

# 33. Final Decision Status

```text
Corpus strategy:                Finalized
Source format:                  Finalized
Ingestion model:                Finalized
Chunking method:                Finalized
Chunk size and overlap:         Finalized
Embedding model:                Finalized
Vector store:                   Finalized
Similarity method:              Finalized
Retrieval depth:                Finalized
Grounded prompt:                Finalized
Structured-output contract:     Finalized
Citation architecture:          Finalized
Unsupported behavior:           Finalized
Repair policy:                  Finalized
Tone prompt design:             Finalized
Few-shot strategy:              Finalized
Generation parameters:          Finalized
Primary model:                  Finalized
Comparison model:               Finalized
Evaluation fairness controls:   Finalized
Frozen evidence policy:         Finalized
Interface:                      Finalized
Logging:                        Finalized
Packaging model:                Finalized
Validation strategy:            Finalized
Stretch-goal boundary:          Finalized
```

These decisions collectively produce a focused, reproducible, and reviewable implementation of the Tier-1 Prompting and RAG Foundations assignment.