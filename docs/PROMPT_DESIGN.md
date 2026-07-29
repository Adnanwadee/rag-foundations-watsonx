# Prompt Design

## Grounded Prompts

The active grounded prompt is Candidate A:

- `prompts/v2/grounded/candidate_a.system.txt`
- `prompts/v2/grounded/candidate_a.user.txt`

The prompt receives only the question and retrieved context. Expected answers, labels, and scoring metadata are not sent to the generation model.

## Tone Prompts

The selected tones are:

- formal report summary
- casual message
- concise executive briefing

Each tone has a system prompt, user prompt, and three few-shot examples under `prompts/v2/`.

## Output Schemas

The retained schemas are:

- `prompts/v2/schemas/grounded_output.schema.json`
- `prompts/v2/schemas/tone_output.schema.json`

Both outputs are strict JSON objects. The runtime allows one bounded repair retry when model output is malformed or fails validation.

## Guardrails

Grounded answers must cite retrieved chunk IDs. Unsupported questions must use the canonical refusal: `I don't know based on the provided documents.`
