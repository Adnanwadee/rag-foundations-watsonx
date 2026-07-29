# Evaluation Method

## Dataset

Final v2 uses 24 grounded questions and 20 tone inputs:

- 20 answerable grounded questions
- 4 unsupported grounded questions
- 20 tone inputs derived from answerable cases

Evidence lives under `data/evaluation/final_v2/`.

## Scoring Layers

The final metrics use hybrid final scoring. Deterministic checks score exact structural properties, citation validity, refusal behavior, and surface preservation. Tool-assisted semantic adjudication resolves cases that need semantic judgment. Independent owner signoff is not complete.

## Retrieval Metrics

Retrieval is evaluated with Hit@1, Hit@3, Hit@5, MRR, and expected-source coverage at 5. Final values are recorded in `data/evaluation/final_v2/scoring/final_metrics.json`.

## Tone Metrics

Tone scoring checks structured JSON, language preservation, factual preservation, target-tone recognizability, and triplet distinctness. Tone evaluation is triplet-based because the requirement asks for three distinct recognizable tone transformations.
