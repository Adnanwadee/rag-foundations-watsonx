# Experiments

## Chunking Configurations

The selected runtime uses `chunk-220-overlap-40`. Compact experiment summaries are retained under `data/evaluation/experiments/` and selected retrieval evidence is retained under `data/evaluation/phase_c/retrieval/`.

Controlled variables included corpus, embedding model, Top-K, generation model, prompt family, and scoring method. The independent variable changed by experiment:

- prompt completeness
- smaller chunk size
- increased overlap

## Prompt Candidate Result

Candidate A remained selected for Final v2 because it was the frozen prompt used by the validated run and is protected by prompt hashes in `data/evaluation/phase_c/frozen/frozen_prompt_manifest_v2.json`.

## Tone Prompt Result

The selected tone prompts used structured JSON and three examples per tone. Final scoring showed tone validity remained the main weakness: Granite had 8/20 fully valid triplets and Mistral had 9/20.

## Granite Vs Mistral Final v2 Comparison

The final comparison changed only the generation model. Retrieval, embeddings, questions, tone inputs, prompts, and scoring stayed fixed.

| Metric | IBM Granite 4 Small | Mistral Small 3.1 24B |
| --- | ---: | ---: |
| Answerable correct | 17/20 | 16/20 |
| Unsupported correct | 3/4 | 4/4 |
| Strict grounded accuracy | 0.8333 | 0.8333 |
| Fully valid tone triplets | 8/20 | 9/20 |
| Distinct tone triplets | 16/20 | 20/20 |
