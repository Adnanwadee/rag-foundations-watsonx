# Evaluation Method

## Dataset

Final v2 uses 24 grounded questions: 20 answerable and 4 unsupported. It also uses 20 tone inputs derived from answerable expected answers. The source corpus is synthetic; see `docs/DATASET_CARD.md`.

## Dataset Construction Rules

Questions cover direct facts, conditional or exception facts, multi-fact answers, multi-section or multi-source answers, and unsupported concepts.

## Edge Cases

The suite includes multi-source questions, unsupported questions, numeric/date cases, very short inputs, already target-tone-like inputs, and non-English development cases outside Final v2.

## Retrieval Metrics And Formulas

Hit@k is the fraction of answerable questions where an expected source appears by rank k. MRR is mean reciprocal rank. Expected-source coverage@5 is the fraction where all expected sources appear in Top-5.

## Grounded Rubric

Correct preserves all material expected facts. Partial is directionally right but incomplete. Wrong is incorrect for answerable cases. Unsupported correct refuses when absent. Unsupported wrong guesses or substitutes nearby facts.

## Citation Validity

Citation IDs must be retrieved chunk IDs and resolve locally to document and section metadata.

## Tone Rubric

Tone scoring checks JSON/schema validity, factual preservation, language preservation, target-tone recognizability, and triplet distinctness.

## Scoring Layers

Final scoring is owner-reviewed hybrid final scoring. The owner manually verified 24 grounded semantic decisions and all 40 tone triplet decisions in `data/evaluation/final_v2/human_review/owner_adjudication.json`. Deterministic-clean grounded labels were retained for structurally clean records.

## Leakage Prevention

Expected answers and rubric metadata are not sent to grounded generation prompts. Reconstructed request evidence is labeled as reconstructed provenance.

## Fair Model Comparison

Granite and Mistral use the same retrieval, prompts, inputs, temperature `0.0`, top_p `1.0`, and scoring rubric. No post-final prompt tuning is applied.

## Reproducibility

Saved evidence supports reported metrics. Live-service behavior may vary.
