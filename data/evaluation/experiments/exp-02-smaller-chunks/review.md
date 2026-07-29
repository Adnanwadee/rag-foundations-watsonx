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
- Retrieved chunks: chunk-c053e6a09a72a3fec790e405, chunk-7e8a089cd075cfb6098565a7, chunk-63a45f2550a6dd660c80053e, chunk-f6f17ed6b0920bac7171c810, chunk-d9a62125b441624921a77fab
- Generated answer: KWD 20
- Citations: policy-code-of-conduct
- Missing or incorrect facts: The courtesy must have an estimated value of KWD 20 or less., It must be appropriate., It must not be cash or a cash equivalent.
- Likely failure layer: conditional-fact preservation
- Evidence: Main answer is directionally correct, but one or more question-relative material facts are missing.
- Candidate experiment: Review this development failure when selecting the Phase 10D candidate configuration.

### dev-009

- Type: conditional_or_exception
- Expected facts: more than 2 consecutive working days, 3 separate undocumented sick leave absences, rolling 60-day period, immediately before or after annual leave may require documentation even if it is only 1 day
- Retrieved chunks: chunk-fb4e815591d1422d9d8effaf, chunk-243c967bb34bd4edc5483718, chunk-1d4673b1d744c0cdf3db09bf, chunk-5ed5ad9c65fcb93294bbf7f2, chunk-b39764fad54741e92b252181
- Generated answer: Medical documentation is required for sick leave lasting more than 2 consecutive working days. HR may also request documentation when the employee has 3 separate undocumented sick leave absences within a rolling 60-day period.
- Citations: policy-employee-leave
- Missing or incorrect facts: Sick leave immediately before or after annual leave may require documentation even if it is only 1 day.
- Likely failure layer: conditional-fact preservation
- Evidence: Main answer is directionally correct, but one or more question-relative material facts are missing.
- Candidate experiment: Review this development failure when selecting the Phase 10D candidate configuration.

### dev-005

- Type: conditional_or_exception
- Expected facts: phishing report button, security@asteron.example, within 1 hour of discovery if the employee interacted, by the end of the working day if the employee did not interact
- Retrieved chunks: chunk-43282ba590f94fff7d594721, chunk-7bb8b07b5eeb6833b17f14fb, chunk-b7b9ca586e5ef81a3a61bf54, chunk-25a9b0d560e5a56396519869, chunk-ae2b08b58bdb54db3b4633b8
- Generated answer: Employees should use the phishing report button or send the message to security@asteron.example. Suspicious emails must be reported within 1 hour of discovery when the employee clicked a link, opened an attachment, entered credentials, approved a payment change, or replied with confidential information. If the employee only received the message and did not interact with it, reporting by the end of the working day is acceptable.
- Citations: policy-it-security
- Missing or incorrect facts: None
- Likely failure layer: None
- Evidence: Generated answer preserves the question-relative material facts, remains supported by retrieved context, and has valid citations.
- Candidate experiment: None in Phase 10B
