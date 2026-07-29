# Experiments

## Chunking Configurations

Research question / hypothesis: Which chunk size and overlap best preserves expected-source retrieval while keeping the index simple? Dataset: Asteron Policies Corpus v2.1 development retrieval set. Controlled variables: corpus, embedding model, FAISS type, Top-5, query set, and similarity metric. Changed variable: chunk size and overlap. Metrics: expected-source hit rate at 5 and multi-source full coverage.

| Configuration | Chunk | Overlap | Records | Hit@5 | Multi-source full coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| chunk-220-overlap-40 | 220 | 40 | 36 | 0.9444 | 5 |
| chunk-160-overlap-20 | 160 | 20 | 36 | 0.9444 | 5 |
| chunk-160-overlap-60 | 160 | 60 | 36 | 0.9444 | 5 |

Observation: all settings tied on retained quality. Selection decision: `chunk-220-overlap-40` retained full Top-5 performance with a smaller, simpler selected index than the high-overlap option. Limitation: retrieval does not prove generation quality.

## Grounded Candidate Comparison

Research question / hypothesis: Which grounded prompt best balances JSON validity, unsupported handling, and false-positive resistance? Dataset: controlled development grounded cases. Controlled variables: selected retrieval context, Granite model, temperature `0.0`, top_p `1.0`, schema, and repair policy. Changed variable: Candidate A, B, or C prompt wording.

| Candidate | Runs | Structured JSON | Unsupported correct | Invented attributes | Repairs or normalizations |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 36 | 36/36 | 6/6 | 0 | 6 |
| B | 36 | 31/36 | 6/6 | 0 | 1 |
| C | 36 | 36/36 | 6/6 | 0 | 6 |

Observation: Candidate B had five malformed outputs; A and C were structurally clean. Selection decision: Candidate A because it provided complete structure, correct unsupported decisions, no invented requested attributes, and concise behavior. Freezing happened after this selection.

## Tone Prompt Comparison

Research question / hypothesis: Does the protected alternate tone prompt improve preservation and style reliability over baseline v2? Dataset: same development tone inputs and model controls. Controlled variables: source inputs, Granite model, temperature `0.0`, top_p `1.0`, schema, and repair policy. Changed variable: tone prompt design.

| Prompt/tone | Runs | Structure | Numbers | Modality | Style signal |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_v2::casual_message | 18 | 18/18 | 13/15 | 3/9 | 8/18 |
| baseline_v2::concise_executive_briefing | 18 | 18/18 | 15/15 | 6/9 | 1/18 |
| baseline_v2::formal_report_summary | 18 | 18/18 | 13/15 | 7/9 | 18/18 |
| protected_v2_1::casual_message | 18 | 18/18 | 15/15 | 8/9 | 4/18 |
| protected_v2_1::concise_executive_briefing | 18 | 18/18 | 15/15 | 8/9 | 0/18 |
| protected_v2_1::formal_report_summary | 18 | 18/18 | 14/15 | 9/9 | 17/18 |
Observation: the alternate improved some preservation dimensions but not overall recognizability. Selection decision: baseline v2 remained selected because it was stable, integrated, and not clearly beaten. Limitation: development behavior did not fully generalize to Final v2.

## Granite Vs Mistral Final v2 Comparison

Research question / hypothesis: How does Granite compare with Mistral, a comparison model with a smaller nominal documented parameter count? Dataset: unchanged Final v2 grounded questions and tone inputs. Controlled variables: corpus, index, prompts, parameters, schemas, repair policy, and rubric. Changed variable: generation model only.

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Answerable correct | 17/20 | 16/20 |
| Unsupported correct | 3/4 | 4/4 |
| Strict grounded accuracy | 0.8333 | 0.8333 |
| Fully valid tone triplets | 8/20 | 9/20 |
| Distinct tone triplets | 16/20 | 20/20 |

Observation: strict grounded accuracy tied; Mistral improved unsupported refusal and tone distinctness. Pricing evidence remains null.
