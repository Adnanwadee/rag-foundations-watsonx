# Final Report: RAG Foundations Final v2

## Summary

The final system meets the core RAG requirements with a frozen local corpus, selected FAISS index, grounded JSON answers, local citations, unsupported refusal, tone transformation, and a CLI. Final scoring uses tool-assisted semantic adjudication plus deterministic-clean labels.

## Final v2 Metrics

| Area | IBM Granite 4 Small | Mistral Small 3.1 24B |
| --- | ---: | ---: |
| Grounded correct answerable | 17/20 | 16/20 |
| Unsupported refusals correct | 3/4 | 4/4 |
| Strict grounded accuracy | 0.8333 | 0.8333 |
| Fully valid tone triplets | 8/20 | 9/20 |
| Distinct tone triplets | 16/20 | 20/20 |

Retrieval: Hit@1 `0.95`, Hit@3 `1.0`, Hit@5 `1.0`, MRR `0.975`.

## Failure Cases

Representative failures from `data/evaluation/final_v2/scoring/failure_analysis.md`:

- Granite question 005 returned a policy title instead of the requested records-and-corrections standard.
- Granite question 018 omitted one equipment-use rule in a multi-source exit question.
- Granite question 023 answered with a travel meal limit when the ordinary office lunch allowance was unsupported.
- Tone outputs sometimes changed modal wording, omitted qualifications, or failed target-tone recognizability.

## Model Comparison

Mistral improved unsupported refusal and tone distinctness, while Granite had one more answerable grounded correct case. Strict grounded accuracy tied at 0.8333.

## Acceptance Matrix

| Criterion | Status | Evidence |
| --- | --- | --- |
| >=70% grounded correctness | PASS | Granite achieved 17/20 answerable correct and 0.8333 strict grounded accuracy. |
| Document + section citation | PASS | Citation validation and local citation resolution are covered by saved outputs and tests. |
| Clear unsupported refusal | PARTIAL | Granite refused 3/4 unsupported questions; Mistral refused 4/4. |
| Three distinct recognizable tones | PARTIAL | Granite produced 16/20 distinct triplets; Mistral produced 20/20. |
| Structured tone output + few-shot | PASS | Selected tone prompts use structured JSON and three few-shot examples per tone. |
| Malformed-output handling | PASS | Grounded and tone paths parse strict JSON and allow one bounded repair retry. |
| >=3 documented experiments | PASS | Chunking, prompt, tone, and model comparison evidence is documented in `docs/EXPERIMENTS.md`. |
| Evaluation report with retrieval, >=3 failures, 20 tone inputs, and model comparison | PASS | This report includes retrieval metrics, failure cases, 20 tone inputs, and model comparison. |

## Limitations

The saved final run is evidence-backed but not independently signed off by the owner. Live model behavior can change over time, so the repository treats saved Final v2 outputs as the metric source of truth.
