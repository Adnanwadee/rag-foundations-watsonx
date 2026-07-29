# Development Experiment Comparison

This retained summary covers the development experiment set only. Final v2 evidence is scored separately under `data/evaluation/final_v2/`.

| Configuration | Strict | Answerable Accuracy | Refusal Accuracy | Citation Validity | Correct | Partial | Wrong | Required-Fact Surface | Avg Total Latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline-calibrated | 0.833 | 0.800 | 1.000 | 1.000 | 8 | 2 | 0 | 0.676 | 1.2257 |
| exp-01-prompt-completeness | 0.750 | 0.700 | 1.000 | 1.000 | 7 | 3 | 0 | 0.735 | 1.2045 |
| exp-02-smaller-chunks | 0.833 | 0.800 | 1.000 | 1.000 | 8 | 2 | 0 | 0.706 | 1.4292 |
| exp-03-increased-overlap | 0.833 | 0.800 | 1.000 | 1.000 | 8 | 2 | 0 | 0.735 | 1.0909 |

## Experiment 3 Deterministic Effectiveness Audit

- Baseline chunks: 70 at size 220 / overlap 40.
- Experiment 3 chunks: 70 at size 220 / overlap 80.
- Identical chunk IDs: 0; different chunk IDs: 70.
- Identical normalized chunk text: 70; changed chunk text: 0; boundary-shifted chunks: 0.
- Same document/section/chunk-index assignments by position: 70/70.
- Development Top-5 document/section rankings identical: 12/12.
- Expected-source hit differences: 0.
- Citation document/section differences: 0.
- Manual score differences: 0.
- Finding: Experiment 3 was operationally inert for this corpus. The overlap setting changed IDs and index artifacts, but every section still fit within one chunk and no material retrieval or manual-quality gain was demonstrated.

## Selection Recommendation

Recommended candidate: `baseline-calibrated`

The existing production baseline is selected. Baseline, smaller chunks, and increased overlap tie on strict score, fully correct answerable accuracy, unsupported refusal accuracy, citation validity, and manual labels. Experiment 3 has higher secondary surface coverage and lower observed latency, but deterministic audit shows no material quality improvement and no changed normalized chunk content; it only requires a separate index and embedding regeneration. Under the tie-break policy, the existing production configuration is preferred.
