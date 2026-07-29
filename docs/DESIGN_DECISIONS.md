# Design Decisions

## Synthetic Markdown Policy Corpus

Decision: use a fictional benchmark. Alternatives considered: real policies, product manuals, scraped PDFs. Evidence: `docs/DATASET_CARD.md`. Trade-off: privacy-safe control versus less natural prose. Final rationale: the benchmark isolates RAG behavior without sensitive data.

## Section-Aware Deterministic Parsing

Decision: parse Markdown sections before chunking. Alternatives considered: naive character windows. Evidence: corpus validator and document loader. Trade-off: requires clean Markdown. Final rationale: document and section citations are required.

## Fixed Token Chunking

Decision: deterministic token chunks. Alternatives considered: semantic chunking. Evidence: retrieval comparison. Trade-off: predictable but can split context. Final rationale: reproducibility was more important for this benchmark.

## 220/40 Selection

Decision: chunk 220 with overlap 40. Alternatives considered: 160/20 and 160/60. Evidence: `data/evaluation/experiments/retrieval_chunking_comparison.json`. Trade-off: moderate context and moderate index size. Final rationale: it retained full Top-5 performance with a smaller selected index than the high-overlap option.

## Watsonx Granite Multilingual Embeddings

Decision: `ibm/granite-embedding-278m-multilingual`. Alternatives considered: local embeddings. Evidence: frozen index manifest. Trade-off: rebuilds require credentials. Final rationale: it matches the assignment stack and gives 768-dimensional vectors.

## FAISS IndexFlatIP

Decision: exact FAISS `IndexFlatIP`. Alternatives considered: approximate indexes or managed stores. Evidence: `data/indexes/selected/index_config.json`. Trade-off: simple but not production-scale. Final rationale: exact search is appropriate for 70 chunks.

## Top-5

Decision: retrieve five chunks. Alternatives considered: Top-1 and Top-3. Evidence: Final retrieval metrics. Trade-off: more context can add distractors. Final rationale: Top-5 supports multi-source coverage.

## Candidate A

Decision: select Candidate A. Alternatives considered: B and C. Evidence: `data/evaluation/experiments/grounded_prompt_comparison.json`. Trade-off: A is not perfect. Final rationale: A had full structural validity, correct unsupported decisions, and no invented requested attributes, while B had malformed outputs.

## Strict JSON Schemas

Decision: schema-validate grounded and tone outputs. Alternatives considered: plain text. Evidence: `prompts/v2/schemas/`. Trade-off: repair logic is needed. Final rationale: structured output is auditable and CLI-friendly.

## Local Citation Resolution

Decision: resolve citation IDs locally. Alternatives considered: trust model-written source text. Evidence: runtime tests. Trade-off: metadata integrity is required. Final rationale: local resolution prevents fabricated source names.

## Canonical Refusal

Decision: use `I don't know based on the provided documents.` Alternatives considered: free-form refusal. Evidence: constants and metrics. Trade-off: less conversational. Final rationale: unsupported scoring is deterministic.

## One Bounded Repair Retry

Decision: retry malformed JSON once. Alternatives considered: no retry or unlimited retry. Evidence: runtime tests. Trade-off: semantic defects are not retried. Final rationale: parser resilience without hiding quality.

## Selected Tone Prompts And Few-Shots

Decision: baseline v2 prompts with three examples per tone. Alternatives considered: protected alternate tone prompts. Evidence: tone comparison. Trade-off: tone quality remains partial. Final rationale: alternate development gains did not justify post-final switching.

## Temperature And top_p

Decision: temperature 0.0 and top_p 1.0. Alternatives considered: more creative decoding. Evidence: frozen configuration. Trade-off: less variety. Final rationale: fair evaluation needs stable decoding.

## Granite Primary And Mistral Comparison

Decision: Granite primary, Mistral comparison. Alternatives considered: no comparison. Evidence: model comparison and model-selection evidence. Trade-off: pricing is unavailable. Final rationale: Mistral is a comparison model with a smaller nominal documented parameter count.

## Frozen Artifacts And CLI

Decision: protect artifacts with hashes and expose a CLI. Alternatives considered: prose-only evidence and larger UI. Evidence: manifests and `src/rag_foundations/cli.py`. Trade-off: less interactive UI. Final rationale: the CLI satisfies the assignment with a small inspectable surface.
