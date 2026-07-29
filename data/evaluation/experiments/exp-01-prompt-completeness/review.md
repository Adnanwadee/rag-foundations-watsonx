# Development Baseline Review

This retained review covers the development experiment set only. Final v2 evidence is scored separately under `data/evaluation/final_v2/`.

## Score Summary

- Strict overall score: 0.750
- Correct answerable: 7
- Partial answerable: 3
- Wrong answerable: 0
- Unsupported correct: 2

## Question Scores

| Question ID | Type | Difficulty | Score | Rationale |
| --- | --- | --- | --- | --- |
| dev-001 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-002 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-003 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-004 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-005 | conditional_or_exception | medium | partial | Main answer is directionally correct, but one or more question-relative material facts are missing. |
| dev-006 | conditional_or_exception | medium | partial | Main answer is directionally correct, but one or more question-relative material facts are missing. |
| dev-007 | unanswerable | easy | unsupported_correct | Expected-unanswerable question returned the exact canonical refusal with empty citations. |
| dev-008 | unanswerable | easy | unsupported_correct | Expected-unanswerable question returned the exact canonical refusal with empty citations. |
| dev-009 | conditional_or_exception | medium | partial | Main answer is directionally correct, but one or more question-relative material facts are missing. |
| dev-010 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-011 | multi_fact | medium | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-012 | multi_fact | medium | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |

## Failure Review

### dev-005

- Type: conditional_or_exception
- Expected facts: phishing report button, security@asteron.example, within 1 hour of discovery if the employee interacted, by the end of the working day if the employee did not interact
- Retrieved chunks: chunk-5e5453af148058e641f3d8cd, chunk-72fe0184b06d6f4561a4552a, chunk-e4e0ed2f312c0193f46ccbef, chunk-8af0e96ab0c10f4a76089f79, chunk-89e4d2d8d018ec68c6ebebc5
- Generated answer: Employees should use the phishing report button or send the suspicious email to security@asteron.example.
- Citations: policy-it-security
- Missing or incorrect facts: If the employee interacted with the suspicious email, it must be reported within 1 hour of discovery., If the employee only received the message and did not interact, reporting by the end of the working day is acceptable.
- Likely failure layer: conditional-fact preservation
- Evidence: Main answer is directionally correct, but one or more question-relative material facts are missing.
- Candidate experiment: Review this development failure when selecting the Phase 10D candidate configuration.

### dev-006

- Type: conditional_or_exception
- Expected facts: KWD 20 or less, appropriate, not cash or a cash equivalent
- Retrieved chunks: chunk-4877ca42faadfdcd3cfddbdd, chunk-938a56463ead28582c210489, chunk-975146e9923216dff91d83a8, chunk-5108f63914c6dfa3ffd548c6, chunk-4ed20f9730d8c7bac9f1f39f
- Generated answer: KWD 20
- Citations: policy-code-of-conduct
- Missing or incorrect facts: The courtesy must have an estimated value of KWD 20 or less., It must be appropriate., It must not be cash or a cash equivalent.
- Likely failure layer: conditional-fact preservation
- Evidence: Main answer is directionally correct, but one or more question-relative material facts are missing.
- Candidate experiment: Review this development failure when selecting the Phase 10D candidate configuration.

### dev-009

- Type: conditional_or_exception
- Expected facts: more than 2 consecutive working days, 3 separate undocumented sick leave absences, rolling 60-day period, immediately before or after annual leave may require documentation even if it is only 1 day
- Retrieved chunks: chunk-b1b03c037a4a09ef5088a66e, chunk-bfc0fe48728597f912a8a416, chunk-224312e02a9769f111423ae9, chunk-850fa9f574aba4e4f88bc2c3, chunk-bc712494c54de08d55eb2f24
- Generated answer: Medical documentation is required for sick leave lasting more than 2 consecutive working days. HR may also request documentation when the employee has 3 separate undocumented sick leave absences within a rolling 60-day period.
- Citations: policy-employee-leave
- Missing or incorrect facts: Sick leave immediately before or after annual leave may require documentation even if it is only 1 day.
- Likely failure layer: conditional-fact preservation
- Evidence: Main answer is directionally correct, but one or more question-relative material facts are missing.
- Candidate experiment: Review this development failure when selecting the Phase 10D candidate configuration.
