# Development Baseline Review

This retained review covers the development experiment set only. Final v2 evidence is scored separately under `data/evaluation/final_v2/`.

## Score Summary

- Strict overall score: 0.833
- Correct answerable: 8
- Partial answerable: 2
- Wrong answerable: 0
- Unsupported correct: 2

## Question Scores

| Question ID | Type | Difficulty | Score | Rationale |
| --- | --- | --- | --- | --- |
| dev-001 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-002 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-003 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-004 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-005 | conditional_or_exception | medium | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-006 | conditional_or_exception | medium | partial | Main answer is directionally correct, but one or more question-relative material facts are missing. |
| dev-007 | unanswerable | easy | unsupported_correct | Expected-unanswerable question returned the exact canonical refusal with empty citations. |
| dev-008 | unanswerable | easy | unsupported_correct | Expected-unanswerable question returned the exact canonical refusal with empty citations. |
| dev-009 | conditional_or_exception | medium | partial | Main answer is directionally correct, but one or more question-relative material facts are missing. |
| dev-010 | direct_fact | easy | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-011 | multi_fact | medium | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |
| dev-012 | multi_fact | medium | correct | Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations. |

## High-Risk Correct Cases

Fewer than three partial or wrong development cases occurred, so the highest-risk correct cases are listed.

### dev-006

- Type: conditional_or_exception
- Expected facts: KWD 20 or less, appropriate, not cash or a cash equivalent
- Retrieved chunks: chunk-71c5b7f68a8c6d8ea8319027, chunk-f418978c818775c55c49f835, chunk-886aa12d93ced5db31d96bd9, chunk-9d24ec70a568bb5d34d667c4, chunk-6544e9a6be5fa01600223fa9
- Generated answer: KWD 20
- Citations: policy-code-of-conduct
- Missing or incorrect facts: The courtesy must have an estimated value of KWD 20 or less., It must be appropriate., It must not be cash or a cash equivalent.
- Likely failure layer: conditional-fact preservation
- Evidence: Main answer is directionally correct, but one or more question-relative material facts are missing.
- Candidate experiment: Review this development failure when selecting the Phase 10D candidate configuration.

### dev-009

- Type: conditional_or_exception
- Expected facts: more than 2 consecutive working days, 3 separate undocumented sick leave absences, rolling 60-day period, immediately before or after annual leave may require documentation even if it is only 1 day
- Retrieved chunks: chunk-32c5978083055ae9ea4a0816, chunk-cc64a7d771b7a62f2783dade, chunk-1b7eb8cc29049048113f8a18, chunk-cbac2aed10c675fba3bd9d68, chunk-355fe3ba334d064978d07e1c
- Generated answer: Medical documentation is required for sick leave lasting more than 2 consecutive working days. HR may also request documentation when the employee has 3 separate undocumented sick leave absences within a rolling 60-day period.
- Citations: policy-employee-leave
- Missing or incorrect facts: Sick leave immediately before or after annual leave may require documentation even if it is only 1 day.
- Likely failure layer: conditional-fact preservation
- Evidence: Main answer is directionally correct, but one or more question-relative material facts are missing.
- Candidate experiment: Review this development failure when selecting the Phase 10D candidate configuration.

### dev-005

- Type: conditional_or_exception
- Expected facts: phishing report button, security@asteron.example, within 1 hour of discovery if the employee interacted, by the end of the working day if the employee did not interact
- Retrieved chunks: chunk-c7bf5ada74a04b412bdfce8f, chunk-3beceee343524cec215fbcf3, chunk-fb3d68e54f6308b99a64efa7, chunk-2c095c8f168d701011050277, chunk-8033c171a7d9774733898f12
- Generated answer: Employees should use the phishing report button or send the suspicious email to security@asteron.example. If the employee clicked a link, opened an attachment, entered credentials, approved a payment change, or replied with confidential information, the report must be made within 1 hour of discovery. If the employee only received the message and did not interact with it, reporting by the end of the working day is acceptable.
- Citations: policy-it-security
- Missing or incorrect facts: None
- Likely failure layer: None
- Evidence: Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations.
- Candidate experiment: None in Phase 10B
