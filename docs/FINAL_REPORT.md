# Final Report: RAG Foundations Final v2

## Executive Summary

The project delivers a CLI-first RAG assistant over a byte-frozen synthetic benchmark. It meets the core grounded-answer requirement, resolves document and section citations locally, exposes three tone transformations, and reports limitations directly. Final scoring uses manual owner verification for 24 grounded semantic decisions and all 40 tone triplets, combined with deterministic-clean grounded labels.

## Project Objective And Scope

Build and evaluate a Watsonx-based RAG pipeline with ingestion, retrieval, grounded generation, citations, tone rewriting, structured output, malformed-output handling, experiments, model comparison, and a CLI.

## Dataset Summary And Synthetic-Data Limitations

Asteron Policies Corpus v2.1 contains five fictional Markdown policies, 60 sections, and 70 selected chunks. It is synthetic and benchmark-oriented; see `docs/DATASET_CARD.md`.

## Final Frozen Configuration

The frozen runtime uses `data/indexes/selected/`, chunk 220 / overlap 40, Top-5, FAISS `IndexFlatIP`, `ibm/granite-embedding-278m-multilingual`, Candidate A, baseline v2 tone prompts, Granite primary, Mistral comparison, temperature `0.0`, and top_p `1.0`.

## Evaluation Design

The grounded set contains 24 questions: 20 answerable and 4 unsupported. The tone set contains 20 inputs and three requested tones per input for each model.

## Retrieval Results

Hit@1 `0.95`, Hit@3 `1.0`, Hit@5 `1.0`, MRR `0.975`, expected-source coverage@5 `0.9`.

## Grounded Results

Granite answered 17/20 answerable questions correctly and refused 3/4 unsupported questions. Mistral answered 16/20 answerable questions correctly and refused 4/4 unsupported questions. Both strict grounded accuracy values were `0.8333`.

## Tone Results

Granite produced 8/20 fully valid triplets and 16/20 distinct triplets. Mistral produced 9/20 fully valid triplets and 20/20 distinct triplets.

## Fair Model Comparison

Only the generation model changed. Mistral is documented as a comparison model with a smaller nominal documented parameter count. Pricing evidence remains null.

## Failure Cases

### final2-g-005 / ibm/granite-4-h-small

Observed output: Code of Conduct, Conflicts, and Reporting Policy

Expected behavior: Business records must be accurate and complete, and mistakes must be corrected promptly and transparently.

Root cause: retrieval or generation did not preserve every required policy fact, or substituted a nearby unsupported fact.

Impact: lowers grounded completeness or unsupported-refusal reliability.

Future mitigation: add reranking or refine prompts on a new development set before a fresh final evaluation.

### final2-g-023 / ibm/granite-4-h-small

Observed output: KWD 12 for lunch

Expected behavior: I don't know based on the provided documents.

Root cause: retrieval or generation did not preserve every required policy fact, or substituted a nearby unsupported fact.

Impact: lowers grounded completeness or unsupported-refusal reliability.

Future mitigation: add reranking or refine prompts on a new development set before a fresh final evaluation.

### final2-g-016 / mistralai/mistral-small-3-1-24b-instruct-2503

Observed output: A workplace visitor must be pre-registered by the host and escorted in restricted areas. Managers must review team access at least quarterly.

Expected behavior: A workplace visitor must be pre-registered by the host and escorted in restricted areas, with visitor-access records retained for 90 calendar days. Managers must review team access at least quarterly, system owners must review privileged and finance-related access monthly, and unnecessary access must be removed within 3 working days of discovery.

Root cause: retrieval or generation did not preserve every required policy fact, or substituted a nearby unsupported fact.

Impact: lowers grounded completeness or unsupported-refusal reliability.

Future mitigation: add reranking or refine prompts on a new development set before a fresh final evaluation.

## Strengths

Strengths include retrieval quality, answerable grounding, citations, reproducibility, validation, and fair comparison.

## Weaknesses

Weaknesses include one Granite unsupported hallucination, partial multi-source answers, tone reliability, synthetic benchmark prose, live-service variability, and a large final-evaluation module.

## Acceptance Matrix

| Criterion | Status | Evidence |
| --- | --- | --- |
| >=70% grounded correctness | PASS | Granite achieved 17/20 answerable correct and strict grounded accuracy 0.8333. |
| Document + section citation | PASS | Citations resolve to document and section metadata. |
| Clear unsupported refusal | PARTIAL | Granite refused 3/4 unsupported questions; Mistral refused 4/4. |
| Three distinct recognizable tones | PARTIAL | Granite produced 16/20 distinct triplets; Mistral produced 20/20. |
| Structured tone output + few-shot | PASS | Tone JSON schema and few-shot files are retained. |
| Malformed-output handling | PASS | One bounded repair retry is implemented. |
| >=3 documented experiments | PASS | Four compact summaries are retained. |
| Evaluation report with retrieval, >=3 failures, 20 tone inputs, and model comparison | PASS | This report covers each item. |

## Owner-Review And Evidence-Integrity Statement

`data/evaluation/final_v2/human_review/owner_adjudication.json` records Adnan Wadee Abdullah's manual verification. The owner approved existing decisions without label changes. Corpus documents, selected prompts, few-shot files, raw model outputs, labels, selected FAISS binary, and numerical metrics were preserved.

## Conclusion

The project satisfies the RAG foundations goals and is ready for local Python environment setup, `.env` creation, and live smoke testing.

## Future Work

Future work: hybrid/BM25 retrieval, reranking, prompt refinement on a new development set, production document governance, API/UI, latency benchmarking, and a larger real-world corpus.
