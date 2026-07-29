# Prompt Design

## System And User Roles

System prompts define durable behavior: context-only answering, schema rules, unsupported refusal, or tone style. User prompts provide the specific question, retrieved context, grounded answer, protected elements, or target tone input.

## Grounded Prompts

Candidate A lives in `prompts/v2/grounded/`. Candidate B emphasized canonical refusal more aggressively but produced 31/36 structured-valid outputs. Candidate C changed completeness and constraint emphasis and matched A structurally, but had no decisive advantage. Candidate A was selected because it achieved 36/36 structured-valid outputs, 6/6 unsupported decisions correct, and no invented requested attributes.

## Grounded JSON Schema

`prompts/v2/schemas/grounded_output.schema.json` requires `answerable`, `answer`, and `citation_chunk_ids`. Unsupported answers use the canonical refusal. Document and section names are resolved locally from metadata.

## Tone Prompts

Tone assets live in `prompts/v2/tones/`. The tones are formal report summary, casual message, and concise executive briefing. Each has three few-shot examples in `prompts/v2/few_shot/` and returns `prompts/v2/schemas/tone_output.schema.json` JSON.

## Protected Semantic Slots

Tone prompts preserve factual content, source language, quantities, dates, authorities, negation, conditions, and exceptions while changing style.

## Malformed-Output Repair

The runtime allows one repair retry for malformed grounded or tone JSON. The retry asks only for valid JSON and does not repair semantic defects.

## Known Prompt Brittleness

Final v2 tone behavior remained less reliable than grounded answering. Granite produced 8/20 fully valid triplets and 16/20 distinct triplets; Mistral produced 9/20 fully valid triplets and 20/20 distinct triplets. Future prompt work should use a new development set.
