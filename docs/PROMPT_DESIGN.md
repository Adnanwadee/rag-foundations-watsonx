# Prompt Design — Grounded Generation and Tone Transformation

## Prompt-System Summary

| Item | Final design |
| --- | --- |
| Grounded prompt | Candidate A |
| Grounded system prompt | `prompts/v2/grounded/candidate_a.system.txt` |
| Grounded user prompt | `prompts/v2/grounded/candidate_a.user.txt` |
| Grounded model schema | `answerable`, `answer`, `citation_chunk_ids` |
| Unsupported response | Canonical refusal with empty citation IDs |
| Tone prompt families | Formal, casual, and executive |
| Prompt files per tone | One system prompt and one user prompt |
| Few-shot examples per tone | 3 |
| Tone model schema | `tone`, `output` |
| Prompt rendering | Strict repository-based template rendering |
| Structured-output repair | Maximum of one bounded retry |
| Final generation parameters | Temperature `0.0`, top-p `1.0` |
| Prompt integrity | Frozen prompt manifest and SHA-256 verification |

---

## 1. Purpose

This document explains the prompt-engineering strategy used by the Prompting and RAG Foundations project.

The prompt system has two separate responsibilities:

1. **Grounded generation**
   Convert a user question and retrieved document evidence into a concise answer that is supported by the supplied context.

2. **Tone transformation**
   Re-express an already validated grounded answer in one of three communication styles without intentionally changing its underlying facts.

The project intentionally separates these two tasks.

The tone model does not receive the full source corpus and is not responsible for answering the original policy question again. It receives the validated grounded answer and transforms only its expression.

This separation reduces the chance that tone rewriting becomes a second independent question-answering step.

---

## 2. Prompt Architecture

The prompt system uses four asset categories:

```text
prompts/v2/
├── grounded/
│   ├── candidate_a.system.txt
│   └── candidate_a.user.txt
├── tones/
│   ├── formal.system.txt
│   ├── formal.user.txt
│   ├── casual.system.txt
│   ├── casual.user.txt
│   ├── executive.system.txt
│   └── executive.user.txt
├── few_shot/
│   ├── formal.json
│   ├── casual.json
│   └── executive.json
└── schemas/
    ├── grounded_output.schema.json
    └── tone_output.schema.json
```

The assets are loaded and rendered through:

```text
src/rag_foundations/prompt_assets.py
```

The runtime does not construct the selected prompts from undocumented string fragments inside the CLI.

Keeping prompts as visible versioned files provides:

- easier review;
- independent prompt editing during development;
- stable hashes;
- clearer model-comparison controls;
- direct evidence for the assignment;
- separation between prompt content and Python orchestration.

---

## 3. System Prompts and User Prompts

The project follows a strict separation between persistent behavior and request-specific content.

## 3.1 System-prompt role

A system prompt defines the durable behavior of the model.

For grounded generation, it defines:

- evidence restrictions;
- answerability behavior;
- semantic-preservation requirements;
- citation rules;
- JSON structure;
- unsupported-question behavior.

For tone transformation, it defines:

- target style;
- semantic-preservation rules;
- language-preservation rules;
- output schema;
- restrictions against adding information;
- restrictions against creating citation metadata.

## 3.2 User-prompt role

A user prompt provides the content specific to one call.

For grounded generation, it contains:

- the user question;
- the retrieved document chunks.

For tone transformation, it contains:

- the original question;
- the validated grounded answer;
- the requested tone identity.

## 3.3 Why the separation matters

This design allows the same system behavior to be reused across many requests.

For example, the grounded system prompt remains fixed while the user message changes from:

```text
Question A + Retrieved Context A
```

to:

```text
Question B + Retrieved Context B
```

Similarly, the formal tone definition remains stable while different grounded answers are passed through its user template.

This improves:

- consistency;
- maintainability;
- experiment control;
- prompt comparison;
- model comparison;
- testability.

---

## 4. Strict Prompt-Asset Loading

Prompt loading is implemented in:

```text
src/rag_foundations/prompt_assets.py
```

The loader performs several checks before a prompt is used.

### Asset checks

- The requested prompt file must exist.
- The prompt must not be blank.
- Prompt variables are extracted explicitly.
- Prompt hashes are calculated.
- Only supported prompt versions are accepted.
- Only known tone identifiers are accepted.
- Every tone must contain exactly three few-shot examples.

### Template checks

Template variables use the syntax:

```text
{{ variable_name }}
```

The renderer rejects:

- missing variables;
- unknown extra variables;
- unresolved placeholders;
- blank rendered output.

This prevents a call from silently sending an incomplete prompt such as:

```text
Question:
{{ question }}
```

without replacing the required variable.

---

## 5. Grounded Prompt Assets

The final grounded prompt uses:

```text
prompts/v2/grounded/candidate_a.system.txt
prompts/v2/grounded/candidate_a.user.txt
```

The system and user messages are created through:

```python
grounded_messages(
    candidate="a",
    question=question,
    retrieved_context=retrieved_context,
)
```

The selected public runtime accepts only Candidate A.

---

## 6. Grounded System-Prompt Design

Candidate A begins by defining the model as:

```text
a document-grounded policy question-answering assistant
```

The model is instructed to use only the retrieved context supplied in the current user message.

It is explicitly told not to use:

- external knowledge;
- pretrained factual knowledge;
- assumptions;
- plausible guesses.

This is the principal prompt-level grounding control.

---

## 7. Exact-Question Requirement

Candidate A instructs the model to:

```text
Answer the exact question that was asked.
```

This instruction is important because a retrieved section may contain several related policy rules.

Without an exact-question constraint, the model may:

- summarize the entire retrieved section;
- answer a nearby policy question;
- return a policy title instead of the requested rule;
- provide an amount from the wrong context;
- omit a condition specifically requested by the user.

The final evaluation includes cases designed to detect these behaviors.

---

## 8. Semantic Elements Protected by the Grounded Prompt

For answerable questions, Candidate A instructs the model to preserve all material semantic elements.

These include:

- subject;
- action or predicate;
- object or policy concept;
- quantity;
- unit;
- date;
- deadline;
- modality;
- condition;
- exception;
- approval authority;
- scope.

The prompt also highlights distinctions such as:

```text
must
may
should
normally
working days
calendar days
```

These distinctions matter because changing modality or time-unit wording can change a policy rule.

### Example

The following statements are not equivalent:

```text
Access must be removed within 3 working days.
```

```text
Access should be reviewed after 3 calendar days.
```

A fluent rewrite can still be incorrect if it changes:

- `must` to `should`;
- `removed` to `reviewed`;
- `within` to `after`;
- `working days` to `calendar days`.

The prompt therefore treats these elements as factual content rather than optional style.

---

## 9. Entitlement and Deadline Guard

Candidate A contains an explicit rule against changing the type of a fact.

The model must not turn an:

- entitlement;
- amount;
- duration;
- limit;
- status;
- review date;

into a:

- request;
- submission;
- approval;
- deadline.

This rule was introduced because language models may convert concise facts into familiar procedural templates.

For example:

```text
Employees receive 30 days of annual leave.
```

must not become:

```text
Employees must request annual leave within 30 days.
```

The second sentence sounds plausible but expresses a completely different fact.

---

## 10. Condition and Exception Preservation

Candidate A instructs the model not to omit a material condition or exception requested by the question.

This is particularly important for rules such as:

```text
Premium economy is allowed for flights of six hours or more
when the department head approves it before booking.
```

A response that states only:

```text
Premium economy is allowed.
```

is incomplete because it removes:

- the six-hour condition;
- the approval authority;
- the before-booking requirement.

The final grounded evaluation contains multi-condition and multi-source questions specifically to measure this behavior.

---

## 11. Attribute Guard

Candidate A includes an explicit attribute guard.

The guard states that a:

- company name;
- person name;
- department name;
- policy title;
- unrelated proper noun;

must not be treated as the answer to a request for a:

- vendor;
- provider;
- product;
- brand;
- model;
- version;
- telephone number;
- address;
- allowance;
- assigned identifier;

unless the retrieved context explicitly states that relationship.

This guard was designed to reduce a common grounded-generation error:

> returning any prominent entity from the retrieved context even though it does not satisfy the requested attribute.

The development experiment measured:

```text
invented_requested_attributes
```

and Candidate A recorded:

```text
0
```

for the retained experiment cases.

---

## 12. Grounded User Prompt

The grounded user template is deliberately minimal:

```text
Question:
{{ question }}

Retrieved context:
{{ retrieved_context }}

Return the required JSON object only.
```

This user message has two variables:

| Variable | Content |
| --- | --- |
| `question` | The validated user question |
| `retrieved_context` | The five retrieved chunks rendered with their provenance |

The model receives the instructions in the system message and the request-specific evidence in the user message.

The prompt does not embed expected answers, fact-registry labels, or evaluation judgments into the live request.

---

## 13. Retrieved-Context Rendering

The frozen runtime renders the Top-5 retrieved chunks into one grounded context block.

Each evidence item includes identifying information required by the model to reference it through a chunk ID.

Conceptually, the context contains:

```text
Retrieved chunk ID
Document title
Section heading
Chunk text
```

The model is instructed to cite only chunk IDs present in the current retrieved context.

It must:

- cite only retrieved chunks;
- include every cited chunk ID once;
- avoid citing unrelated chunks;
- avoid copying irrelevant chunk text into the answer.

---

## 14. Grounded Model-Level JSON Contract

The model-facing grounded schema is:

```json
{
  "answerable": true,
  "answer": "Supported answer text",
  "citation_chunk_ids": [
    "retrieved-chunk-id"
  ]
}
```

The authoritative JSON schema is:

```text
prompts/v2/schemas/grounded_output.schema.json
```

It requires exactly three fields:

| Field | Type | Purpose |
| --- | --- | --- |
| `answerable` | Boolean | Whether the retrieved context supports the requested answer |
| `answer` | Non-empty string | The answer or canonical refusal |
| `citation_chunk_ids` | Unique string array | IDs of supporting retrieved chunks |

The schema uses:

```json
{
  "additionalProperties": false
}
```

Therefore, unexpected model-generated fields are not accepted as part of the selected contract.

---

## 15. Model Contract versus Application Contract

The model-level object uses:

```text
answerable
citation_chunk_ids
```

After validation and citation resolution, the application exposes a richer grounded result using fields such as:

```text
answer
is_answerable
citations
```

This distinction is intentional.

### Model responsibility

The model decides:

- whether the evidence supports an answer;
- what the concise answer should say;
- which retrieved chunk IDs support it.

### Application responsibility

The application validates and resolves:

- document ID;
- document title;
- section heading;
- source path;
- retrieved supporting excerpt;
- corpus version;
- index ID.

This means the model does not freely generate authoritative final citation metadata.

---

## 16. Local Citation Resolution

Candidate A instructs the model to return only retrieved chunk IDs.

The application then verifies that:

1. every citation ID belongs to the current Top-5 retrieved set;
2. duplicate IDs are rejected or normalized according to the application contract;
3. unsupported answers contain no citation IDs;
4. answerable results contain valid supporting IDs;
5. final document and section metadata comes from the local selected index.

This architecture reduces the chance of fabricated:

- document titles;
- section names;
- paths;
- retrieved supporting excerpts.

The model identifies evidence; the application owns citation metadata.

---

## 17. Unsupported-Question Prompt Contract

For an unsupported question, Candidate A instructs the model to:

```text
set answerable to false
```

use exactly:

```text
I don't know based on the provided documents.
```

and return:

```json
{
  "citation_chunk_ids": []
}
```

The complete expected model object is:

```json
{
  "answerable": false,
  "answer": "I don't know based on the provided documents.",
  "citation_chunk_ids": []
}
```

This contract supports:

- consistent user behavior;
- easy automated scoring;
- separation of unsupported answers from low-confidence guesses;
- empty citations when no evidence supports an answer.

Application-level normalization ensures that a correctly declared unsupported result is presented through the canonical refusal contract.

---

## 18. Grounded Prompt Comparison

The development experiment compared three prompt candidates.

The artifact is:

```text
data/evaluation/experiments/grounded_prompt_comparison.json
```

### Controlled variables

The experiment held constant:

- selected retrieval context;
- generation model;
- temperature `0.0`;
- top-p `1.0`;
- repair policy;
- development cases.

Only the grounded prompt candidate changed.

### Results

| Candidate | Runs | Structured JSON valid | Unsupported decisions correct | Unsupported answered incorrectly | Invented requested attributes |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 36 | `36/36` | `6/6` | 0 | 0 |
| B | 36 | `31/36` | `6/6` | 0 | 0 |
| C | 36 | `36/36` | `6/6` | 0 | 0 |

### Application canonicalization observations

| Candidate | Raw canonical refusals | Application canonical refusals | Combined repairs or normalizations |
| --- | ---: | ---: | ---: |
| A | 0 | 6 | 6 |
| B | 5 | 6 | 1 |
| C | 0 | 6 | 6 |

The combined `repairs_or_normalizations` metric must not be interpreted automatically as a model repair call in every case. It includes application-level handling needed to produce the canonical unsupported result.

### Selection

Candidate A was selected because it combined:

- complete structured-output validity;
- correct unsupported decisions;
- zero invented requested attributes;
- a concise direct contract;
- direct compatibility with local citation resolution.

Candidate B produced malformed JSON in five of 36 runs.

Candidate C matched Candidate A on the retained structural measures but did not demonstrate a stronger practical advantage.

### Experiment limitation

The prompt-comparison metrics emphasize:

- structure;
- unsupported behavior;
- requested-attribute safety.

They are not presented as complete human semantic grading of every answer.

---

## 19. Tone Transformation Strategy

The tone stage receives a validated grounded answer rather than raw retrieved evidence.

The conceptual flow is:

```text
Validated grounded answer
        ↓
Original question for unambiguous scope
        ↓
Selected tone system prompt
        ↓
Three few-shot examples
        ↓
Tone user prompt
        ↓
Model-generated JSON
        ↓
Tone schema validation
        ↓
Application-owned citation retention
```

The tone stage is therefore a controlled rewriting task, not a second RAG retrieval step.

---

## 20. Supported Tones

The project supports three tone identifiers.

| Tone ID | Communication objective |
| --- | --- |
| `formal_report_summary` | Professional, objective, neutral report-style summary |
| `casual_message` | Friendly, natural, conversational explanation |
| `concise_executive_briefing` | Compact, decision-oriented, scannable briefing |

Each tone uses a separate prompt pair.

---

## 21. Formal Report Prompt

### Assets

```text
prompts/v2/tones/formal.system.txt
prompts/v2/tones/formal.user.txt
prompts/v2/few_shot/formal.json
```

### Style requirements

The formal prompt requires output that is:

- professional;
- objective;
- neutral;
- complete;
- concise;
- suitable for a formal report.

### Output identity

```json
{
  "tone": "formal_report_summary",
  "output": "transformed text"
}
```

The formal tone showed the strongest final per-tone reliability for both evaluated models.

---

## 22. Casual Message Prompt

### Assets

```text
prompts/v2/tones/casual.system.txt
prompts/v2/tones/casual.user.txt
prompts/v2/few_shot/casual.json
```

### Style requirements

The casual prompt requires output that is:

- natural;
- conversational;
- friendly;
- clear;
- recognizably different from a formal report.

It explicitly avoids:

- slang;
- emojis;
- jokes;
- reduced factual precision.

### Output identity

```json
{
  "tone": "casual_message",
  "output": "transformed text"
}
```

The goal is approachable communication without changing the answer into an informal or imprecise paraphrase.

---

## 23. Concise Executive Briefing Prompt

### Assets

```text
prompts/v2/tones/executive.system.txt
prompts/v2/tones/executive.user.txt
prompts/v2/few_shot/executive.json
```

### Style requirements

The executive prompt requires output that is:

- direct;
- decision-oriented;
- concise;
- scannable;
- recognizably different from the formal and casual outputs.

### Output identity

```json
{
  "tone": "concise_executive_briefing",
  "output": "transformed text"
}
```

The prompt encourages compact labels and action-focused phrasing where appropriate, while retaining all material conditions and exceptions.

---

## 24. Shared Tone-Preservation Rules

All three tone system prompts include the same core information-preservation rules.

The model is instructed to preserve:

- source language;
- subject;
- action or predicate;
- object or policy concept;
- quantity;
- unit;
- date;
- deadline;
- modality;
- condition;
- exception;
- approval authority;
- scope.

The model is instructed not to:

- add facts;
- translate unless the source task requires translation;
- copy a semantic frame from a few-shot example;
- create citations;
- remove citations;
- alter citation metadata;
- include reasoning;
- include Markdown;
- include text outside the JSON object.

---

## 25. Use of the Original Question in Tone Transformation

The tone model receives both:

- the original question;
- the validated grounded answer.

However, the prompt states that the original question may be used only to restore unambiguous subject or scope when the grounded answer is a short fragment.

### Example

Grounded answer:

```text
15 minutes.
```

Original question:

```text
How long is the account lockout?
```

A valid formal transformation is:

```text
The account lockout duration is 15 minutes.
```

The question provides the missing subject:

```text
account lockout duration
```

It must not be used to introduce a new policy fact beyond the validated answer.

---

## 26. Tone User-Prompt Design

The selected tone user templates contain:

```text
Original question:
{{ original_question }}

Validated grounded answer:
{{ grounded_answer }}

Transform the answer into <tone>.
```

The request-specific variables are:

| Variable | Purpose |
| --- | --- |
| `original_question` | Restore unambiguous subject or scope where necessary |
| `grounded_answer` | Authoritative content to be rewritten |

The tone prompt does not receive:

- the full FAISS index;
- all source documents;
- expected evaluation labels;
- citation metadata to rewrite;
- alternative answers.

---

## 27. Few-Shot Prompting

The assignment requires at least one few-shot example per tone.

The final project provides:

```text
3 examples per tone
9 examples total
```

The files are:

```text
prompts/v2/few_shot/formal.json
prompts/v2/few_shot/casual.json
prompts/v2/few_shot/executive.json
```

Each file contains exactly three records.

---

## 28. Few-Shot Record Structure

Each few-shot record contains fields such as:

```json
{
  "example_id": "tone-example-001",
  "original_question": "Question text",
  "grounded_answer": "Validated fact",
  "expected_output": "Tone-transformed text",
  "demonstrates": [
    "style and JSON structure only",
    "semantic-slot preservation"
  ],
  "prohibited_transfer_fields": [
    "subject",
    "action",
    "relation",
    "object",
    "number",
    "unit",
    "condition",
    "exception",
    "authority"
  ]
}
```

The examples demonstrate style and content preservation.

They are not policy facts for the Asteron corpus.

---

## 29. Why Synthetic Few-Shot Examples Are Used

The few-shot examples use fictional, non-Asteron scenarios such as:

- equipment-inspection leave;
- temporary laboratory access;
- account-lockout duration.

This design reduces the chance that the model copies a real Asteron policy rule from an example into an unrelated answer.

The system prompts also explicitly state:

```text
Do not copy a semantic frame from a few-shot example.
```

Few-shot examples are intended to teach:

- tone;
- sentence structure;
- concise expansion of fragments;
- structured output behavior.

They are not intended to supply answer content.

---

## 30. Few-Shot Example Coverage

The three examples per tone cover different transformation patterns.

### Example type 1 — Complete entitlement statement

Grounded answer:

```text
Eligible technicians receive 3 paid equipment-inspection days per year.
```

This tests preservation of:

- subject;
- number;
- unit;
- annual scope;
- entitlement.

### Example type 2 — Condition and exception

Grounded answer:

```text
Temporary laboratory access may be approved for up to 4 calendar days when the laboratory manager gives written approval, unless Safety suspends access because of an active incident.
```

This tests preservation of:

- modality;
- maximum duration;
- time unit;
- approval authority;
- written-approval condition;
- exception.

### Example type 3 — Short fragment

Grounded answer:

```text
15 minutes.
```

This tests whether the model can restore the subject from the original question without adding a new factual rule.

---

## 31. Few-Shot Rendering

`prompt_assets.py` renders the examples into blocks conceptually shaped as:

```text
Few-shot example:
Original question: ...
Grounded answer: ...
Expected output: ...
```

The three example blocks are prepended to the selected tone system instructions.

The final tone call therefore receives:

```text
System message:
    Few-shot examples
    + selected tone instructions

User message:
    current original question
    + current validated grounded answer
```

This keeps style demonstrations and the current request clearly separated.

---

## 32. Tone Model-Level JSON Contract

The authoritative tone schema is:

```text
prompts/v2/schemas/tone_output.schema.json
```

The model-facing object contains:

```json
{
  "tone": "formal_report_summary",
  "output": "transformed text"
}
```

Required fields:

| Field | Type | Constraint |
| --- | --- | --- |
| `tone` | Enum string | Must be one of the three supported tone IDs |
| `output` | Non-empty string | Tone-transformed answer |

The schema rejects additional properties.

---

## 33. Citation Ownership During Tone Transformation

Tone prompts explicitly state:

```text
the application owns citation metadata
```

The model is instructed not to:

- create citations;
- alter citations;
- remove citations;
- include citation metadata in the rewritten text.

After tone validation, the application copies the already validated grounded citations into the final `ToneResult`.

This means the tone model changes only:

```text
output text
```

It does not modify the evidence record.

---

## 34. Generic and Frozen Tone Validation

The repository contains both generic development components and the frozen Final-v2 path.

### Generic tone component

The generic tone-transformation module includes checks for:

- JSON structure;
- expected tone identifier;
- selected citation-metadata leakage;
- selected exact surface markers;
- selected unsupported wording additions.

These checks support unit testing and development experimentation.

### Frozen Final-v2 path

The public frozen runtime validates:

- valid JSON;
- Pydantic tone schema;
- exact expected tone identifier;
- non-empty output;
- bounded repair behavior.

The application then retains the validated grounded citations locally.

### Semantic-preservation boundary

The prompt explicitly requires semantic preservation, but complete semantic equivalence cannot be proven through JSON validation alone.

Therefore, factual preservation is also evaluated empirically through:

- deterministic feature checks;
- human semantic review;
- owner verification;
- final tone metrics.

This is a deliberate distinction:

```text
Prompt instruction ≠ complete deterministic guarantee
```

---

## 35. Tone Prompt Comparison

The tone-development experiment compared:

- `baseline_v2`;
- `protected_v2_1`.

The artifact is:

```text
data/evaluation/experiments/tone_prompt_comparison.json
```

For each prompt family and tone, the experiment used:

```text
18 runs
```

### Evaluated dimensions

- structured validity;
- language preservation;
- number preservation;
- unit preservation;
- currency preservation;
- approval-authority preservation;
- condition preservation;
- exception preservation;
- negation preservation;
- modality preservation;
- scope preservation;
- citation-metadata absence;
- exact-copy behavior;
- rough style signal.

### Important metric distinction

`rough_style_signal` is a deterministic development proxy.

It is not a human judgment of complete tone quality.

Human-reviewed tone recognizability and factual preservation are reported separately in the final evaluation.

### Selection decision

Baseline v2 was retained because:

- it was fully integrated;
- all three tone prompt pairs were complete;
- all three few-shot sets were complete;
- schema behavior was stable;
- the alternate design did not demonstrate a decisive overall advantage;
- changing prompt families after final evaluation would represent post-final tuning.

---

## 36. Structured-Output Parsing

Grounded and tone responses are returned by the model as text.

The application then performs:

1. raw response extraction;
2. whitespace trimming;
3. JSON parsing;
4. Pydantic validation;
5. expected enum validation;
6. citation-ID validation for grounded output;
7. application-level result construction.

The model response is not treated as valid merely because it resembles JSON visually.

---

## 37. Bounded Repair Strategy

The final configuration allows:

```text
1 initial generation
+ at most 1 repair generation
```

for each generated object.

Repair is used when the result fails structural validation, for example:

- malformed JSON;
- missing required field;
- unexpected field;
- incorrect data type;
- incorrect tone identifier;
- invalid citation ID.

The repair message asks the model to return only a JSON object matching the expected structure.

---

## 38. Repair Boundaries

The repair path is designed to correct output formatting and contract violations.

It is not presented as a complete solution for:

- incomplete factual content;
- subtle semantic drift;
- an omitted exception;
- an incorrect policy interpretation;
- weak tone distinction;
- stylistic awkwardness.

A response may be structurally valid but still receive a lower semantic evaluation score.

This is why the project reports:

- structured validity;
- grounded correctness;
- citation validity;
- factual preservation;
- tone recognizability;

as separate measures.

---

## 39. Repair Failure Handling

If the initial output and the bounded repair output both fail validation:

- the runtime raises a typed `ModelOutputError`;
- the invalid output is not returned as a successful answer;
- the CLI prints a safe diagnostic to `stderr`;
- the CLI returns a non-zero process exit code;
- credentials are not included in the error.

The final saved evaluation recorded:

```text
0 grounded repair retries
0 tone repair retries
```

The repair path remains covered by automated tests.

---

## 40. Generation Parameters

The final grounded and tone prompts use deterministic low-variance sampling.

| Parameter | Grounded | Tone |
| --- | ---: | ---: |
| Temperature | `0.0` | `0.0` |
| Top-p | `1.0` | `1.0` |
| Maximum output tokens | 500 | 350 |
| Maximum repair retries | 1 | 1 |

These settings were selected to support:

- controlled comparison;
- reproducibility;
- stable JSON behavior;
- easier failure diagnosis;
- reduced stylistic randomness.

They do not guarantee byte-identical external model responses across time.

---

## 41. Final Grounded Prompt Results

The final grounded evaluation used:

```text
24 questions
20 answerable
4 unsupported
2 generation models
48 grounded model results
```

Results:

| Metric | Granite | Mistral |
| --- | ---: | ---: |
| Answerable correct | `17/20` | `16/20` |
| Answerable partial | `2/20` | `4/20` |
| Unsupported correct | `3/4` | `4/4` |
| Citation-valid records | 20 | 19 |
| Strict overall accuracy | `20/24` | `20/24` |

Both models achieved:

```text
0.8333 strict grounded accuracy
```

which exceeds the required 70% threshold.

---

## 42. Final Tone-Prompt Results

The final tone evaluation used:

```text
20 inputs
× 3 tones
× 2 models
= 120 saved tone outputs
```

### Structural validity

| Model | Structurally valid outputs |
| --- | ---: |
| Granite | `60/60` |
| Mistral | `60/60` |

### Fully valid three-tone sets

| Model | Fully valid triplets |
| --- | ---: |
| Granite | `8/20` |
| Mistral | `9/20` |

### Recognizably distinct three-tone sets

| Model | Distinct triplets |
| --- | ---: |
| Granite | `16/20` |
| Mistral | `20/20` |

### Per-tone final validity

| Model and tone | Final valid |
| --- | ---: |
| Granite — formal report | `20/20` |
| Granite — casual message | `11/20` |
| Granite — executive briefing | `12/20` |
| Mistral — formal report | `19/20` |
| Mistral — casual message | `13/20` |
| Mistral — executive briefing | `15/20` |

The formal-report prompt was the most consistently reliable tone in the final review.

---

## 43. Tone Edge Cases

The final tone set contains diverse input patterns.

These include:

- very short grounded answers;
- longer multi-clause answers;
- numeric values;
- units;
- dates and deadlines;
- approval authorities;
- conditions;
- exceptions;
- negation;
- already formal input;
- already casual input;
- already concise input;
- non-English input.

The purpose was to evaluate prompt brittleness beyond a small collection of easy examples.

---

## 44. Live Prompt Smoke Tests

The live grounded test confirmed that Candidate A could answer:

```text
What approval is required for premium economy on a flight of 6 hours or more,
and what approval is required for business class?
```

The result correctly preserved:

- the six-hour condition;
- department-head approval;
- before-booking timing;
- the Chief Operating Officer exception;
- the correct travel-policy citation.

The live unsupported test returned:

```text
I don't know based on the provided documents.
```

with:

```text
is_answerable=false
citations=[]
```

The live formal tone test returned valid JSON and a recognizable formal style while preserving the core approval authorities.

Detailed live observations are documented in:

```text
docs/LIVE_SMOKE_TEST.md
```

---

## 45. Prompt Brittleness and Interpretation

Prompt performance is measured rather than assumed.

Observed behavior shows that:

- structured output was highly reliable;
- grounded answering exceeded the required threshold;
- formal tone behavior was highly consistent;
- casual and executive transformations were more sensitive to input and model behavior;
- a valid JSON object does not by itself prove perfect factual preservation;
- retrieval success does not guarantee complete multi-source generation;
- unsupported near-match questions remain important tests.

These observations do not invalidate the prompt architecture.

They demonstrate why the project separates:

```text
structure
grounding
citation validity
factual preservation
tone recognizability
tone distinctness
```

into different evaluation dimensions.

---

## 46. Prompt-Injection Scope

The selected corpus is controlled and synthetic.

The project does not claim a complete defense against adversarial prompt injection embedded inside arbitrary third-party documents.

A production extension would require additional controls such as:

- document trust classification;
- explicit context delimiters;
- instruction-content separation;
- prompt-injection test cases;
- retrieval filtering;
- source authorization;
- model-output policy checks.

These controls are outside the Tier-1 assignment scope.

---

## 47. Prompt Integrity

Selected prompt assets are protected through:

```text
data/manifests/frozen/frozen_prompt_manifest_v2.json
data/evaluation/final_v2/manifests/protected_hashes.json
```

Before constructing the frozen live runtime, the application verifies the selected prompt assets.

Protected assets include:

- Candidate A system prompt;
- Candidate A user prompt;
- three tone system prompts;
- three tone user prompts;
- three few-shot files;
- grounded output schema;
- tone output schema.

This ensures that the live runtime remains aligned with the prompt configuration used by the retained final evaluation.

---

## 48. Prompt Development and Final-Evaluation Separation

Prompt candidates were compared during development.

After Candidate A and Baseline v2 were selected:

- prompt files were frozen;
- hashes were preserved;
- final questions were executed;
- final outputs were retained;
- scoring was completed;
- human review was recorded;
- owner verification was completed.

The final prompts were not changed to correct individual final-test failures.

Future prompt improvements should use:

- a new prompt version;
- a new development set;
- new hashes;
- a new evaluation run;
- separate final metrics.

---

## 49. Prompt-Related Test Coverage

| Test file | Main prompt coverage |
| --- | --- |
| `tests/test_prompt_assets_v2.py` | Prompt files, schemas, variables, rendering, and few-shot counts |
| `tests/test_grounded_generation.py` | Grounded JSON, citations, unsupported handling, and repair |
| `tests/test_tone_transformation.py` | Tone JSON, tone identifiers, semantic surface checks, and repair |
| `tests/test_frozen_v2_runtime.py` | Frozen Candidate A and Baseline-v2 runtime behavior |
| `tests/test_pipeline.py` | Grounded-only, one-tone, and all-tone orchestration |
| `tests/test_schemas.py` | Pydantic structured-output contracts |
| `tests/test_cli.py` | JSON output, tone selection, logging, and CLI behavior |
| `tests/test_integrity.py` | Prompt and protected-asset integrity |

The complete project test suite currently passes:

```text
the complete automated test suite
```

---

## 50. Prompt-Design Principles Demonstrated

The final prompt system demonstrates the following foundational concepts.

### Clear role definition

Each model call has one explicit responsibility.

### System/user separation

Persistent behavior is separated from request-specific content.

### Context-only grounding

The grounded model is told to rely only on retrieved evidence.

### Explicit unsupported behavior

Unsupported answers use a defined answerability contract and refusal.

### Structured generation

Both tasks use exact JSON contracts.

### Few-shot prompting

Each tone receives multiple representative examples.

### Semantic-slot preservation

Prompts explicitly identify the factual elements that must not change.

### Bounded repair

Malformed output receives one controlled retry.

### Local evidence ownership

The model references chunk IDs; the application resolves final citations.

### Controlled evaluation

Prompts are compared under fixed variables and then frozen.

### Honest metric separation

JSON validity, correctness, citations, and tone quality are evaluated independently.

---

## 51. Prompt Evidence Map

| Evidence | Path |
| --- | --- |
| Candidate A system prompt | `prompts/v2/grounded/candidate_a.system.txt` |
| Candidate A user prompt | `prompts/v2/grounded/candidate_a.user.txt` |
| Formal prompt pair | `prompts/v2/tones/formal.*.txt` |
| Casual prompt pair | `prompts/v2/tones/casual.*.txt` |
| Executive prompt pair | `prompts/v2/tones/executive.*.txt` |
| Formal few-shot file | `prompts/v2/few_shot/formal.json` |
| Casual few-shot file | `prompts/v2/few_shot/casual.json` |
| Executive few-shot file | `prompts/v2/few_shot/executive.json` |
| Grounded schema | `prompts/v2/schemas/grounded_output.schema.json` |
| Tone schema | `prompts/v2/schemas/tone_output.schema.json` |
| Prompt loader | `src/rag_foundations/prompt_assets.py` |
| Grounded generation | `src/rag_foundations/grounded_generation.py` |
| Tone transformation | `src/rag_foundations/tone_transformation.py` |
| Frozen runtime | `src/rag_foundations/frozen_v2_runtime.py` |
| Grounded comparison | `data/evaluation/experiments/grounded_prompt_comparison.json` |
| Tone comparison | `data/evaluation/experiments/tone_prompt_comparison.json` |
| Final metrics | `data/evaluation/final_v2/scoring/final_metrics.json` |
| Failure analysis | `data/evaluation/final_v2/scoring/failure_analysis.md` |
| Live prompt test | `docs/LIVE_SMOKE_TEST.md` |

---

## 52. Final Prompt-Design Status

```text
Grounded system prompt:          Complete
Grounded user prompt:            Complete
Context-only instruction:        Complete
Exact-question instruction:      Complete
Semantic-slot requirements:      Complete
Attribute guard:                 Complete
Unsupported contract:            Complete
Grounded JSON schema:            Complete
Local citation resolution:       Complete
Formal system/user prompts:      Complete
Casual system/user prompts:      Complete
Executive system/user prompts:   Complete
Few-shot examples:               3 per tone
Tone JSON schema:                Complete
Language-preservation rule:      Complete
Citation-ownership rule:         Complete
Bounded repair:                  Complete
Prompt experiments:              Complete
Prompt integrity protection:     Complete
Final grounded evaluation:       Complete
Final tone evaluation:           Complete
Live prompt validation:          Complete
```

The prompt design satisfies the assignment requirements for grounded answering, system-versus-user prompt separation, few-shot prompting, structured generation, unsupported-question behavior, malformed-output handling, and three controlled tone transformations.
