# Frozen Retrieval And Prompt Decision

The retained frozen configuration selects `chunk-220-overlap-40`, grounded Candidate A, baseline v2 tone prompts, Top-5 retrieval, and `ibm/granite-4-h-small` as the primary generation model.

## Selected Files

- `data/evaluation/phase_c/frozen/frozen_configuration_v2.json`
- `data/evaluation/phase_c/frozen/frozen_prompt_manifest_v2.json`
- `data/evaluation/phase_c/frozen/frozen_index_manifest_v2.json`
- `data/evaluation/phase_c/retrieval/indexes/chunk-220-overlap-40/`

## Rationale

The selected index provided complete Hit@5 retrieval for the final setup while avoiding duplicate index artifacts. Candidate A and the baseline tone prompts are the prompt assets used by the validated Final v2 run and are protected by saved hashes.
