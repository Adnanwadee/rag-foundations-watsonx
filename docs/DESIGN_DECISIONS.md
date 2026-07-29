# Design Decisions

## FAISS Vector Store

Selected configuration: `chunk-220-overlap-40`, `IndexFlatIP`, Top-5 retrieval, 768-dimensional `ibm/granite-embedding-278m-multilingual` vectors.

Reason: the selected index gave full Hit@5 coverage while keeping the index smaller than higher-overlap alternatives. The selected bytes are protected in `data/evaluation/phase_c/frozen/frozen_index_manifest_v2.json`.

## Grounded Prompt

Selected grounded prompt: Candidate A under `prompts/v2/grounded/`.

Reason: Candidate A was the frozen baseline used for the validated Final v2 run. The runtime verifies prompt hashes before creating live components.

## Tone Prompts

Selected tone prompts live under `prompts/v2/tones/` with examples in `prompts/v2/few_shot/`.

Reason: separate prompt files keep style instructions auditable while the JSON output schema keeps downstream parsing deterministic.

## Model Comparison

Primary model: `ibm/granite-4-h-small`. Comparison model: `mistralai/mistral-small-3-1-24b-instruct-2503`.

Reason: the comparison changed only the generation model. Retrieval, embeddings, prompts, datasets, and scoring stayed fixed.

## Trade-Offs

The project favors reproducibility over automatic re-execution. Saved outputs and hashes are treated as evidence, while live execution remains opt-in through explicit script flags.
