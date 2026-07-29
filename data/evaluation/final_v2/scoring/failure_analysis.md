# Final v2 Failure Analysis

## Grounded Failures

### final2-g-005 / ibm/granite-4-h-small

- Final label: wrong (human).
- Question: What standard applies to business records and corrections?
- Expected: Business records must be accurate and complete, and mistakes must be corrected promptly and transparently.
- Generated: Code of Conduct, Conflicts, and Reporting Policy
- Reviewer notes: The response gives only the policy title and does not answer the requested records-and-corrections standard.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

### final2-g-018 / ibm/granite-4-h-small

- Final label: partial (human).
- Question: For a planned exit that also involves company equipment, what must HR, IT Operations, and the employee do?
- Expected: For a planned employee exit, HR must notify IT Operations at least 2 working days before the last working day and standard system access must be disabled by the end of the final working day. Company equipment must be returned at the end of employment, and family members or visitors must not use company devices.
- Generated: HR must notify IT Operations at least 2 working days before the last working day and standard system access must be disabled by the end of the final working day. Equipment return must also follow the Flexible Work and Workplace Access Policy.
- Reviewer notes: Correctly states HR notice and access-disable timing, but gives only a vague cross-policy reference for equipment return and omits the no-family-or-visitor-use rule.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

### final2-g-020 / ibm/granite-4-h-small

- Final label: partial (human).
- Question: Across the five v2.1 policy documents, what next scheduled review date is stated?
- Expected: The Employee Leave, Flexible Work, Information Security, Travel Expense, and Code of Conduct policies each state the next scheduled review date as 2027-01-15.
- Generated: 2027-01-15
- Reviewer notes: The date is correct, but the five-document claim is not fully supported because the citations omit the Information Security review section and include a duplicate Flexible Work source.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

### final2-g-023 / ibm/granite-4-h-small

- Final label: unsupported_wrong (human).
- Question: What daily lunch allowance is paid for ordinary office work in Kuwait?
- Expected: I don't know based on the provided documents.
- Generated: KWD 12 for lunch
- Reviewer notes: Incorrectly substitutes the travel meal limit for a nonexistent ordinary-office lunch allowance.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

### final2-g-002 / mistralai/mistral-small-3-1-24b-instruct-2503

- Final label: partial (human).
- Question: What records rule applies to visitors in restricted workplace areas?
- Expected: A workplace visitor must be pre-registered by the host and escorted in restricted areas; visitor-access records are retained for 90 calendar days.
- Generated: Visitor-access records are retained for 90 calendar days.
- Reviewer notes: Correctly states the 90-calendar-day retention rule but omits pre-registration and escort requirements from the curated answer.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

### final2-g-016 / mistralai/mistral-small-3-1-24b-instruct-2503

- Final label: partial (human).
- Question: For workplace access governance, what visitor handling rule and access-review schedule apply?
- Expected: A workplace visitor must be pre-registered by the host and escorted in restricted areas, with visitor-access records retained for 90 calendar days. Managers must review team access at least quarterly, system owners must review privileged and finance-related access monthly, and unnecessary access must be removed within 3 working days of discovery.
- Generated: A workplace visitor must be pre-registered by the host and escorted in restricted areas. Managers must review team access at least quarterly.
- Reviewer notes: Preserves visitor pre-registration/escort and quarterly manager review, but omits 90-day retention, monthly system-owner review, and the 3-working-day removal rule.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

### final2-g-018 / mistralai/mistral-small-3-1-24b-instruct-2503

- Final label: partial (human).
- Question: For a planned exit that also involves company equipment, what must HR, IT Operations, and the employee do?
- Expected: For a planned employee exit, HR must notify IT Operations at least 2 working days before the last working day and standard system access must be disabled by the end of the final working day. Company equipment must be returned at the end of employment, and family members or visitors must not use company devices.
- Generated: HR must notify IT Operations at least 2 working days before the last working day. IT Operations must disable standard system access by the end of the final working day. The employee must return equipment following the Flexible Work and Workplace Access Policy.
- Reviewer notes: Preserves HR notice, access-disable timing, and equipment return at a high level, but omits the explicit end-of-employment timing and the no-family-or-visitor-use rule.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

### final2-g-020 / mistralai/mistral-small-3-1-24b-instruct-2503

- Final label: partial (human).
- Question: Across the five v2.1 policy documents, what next scheduled review date is stated?
- Expected: The Employee Leave, Flexible Work, Information Security, Travel Expense, and Code of Conduct policies each state the next scheduled review date as 2027-01-15.
- Generated: 2027-01-15
- Reviewer notes: The date is correct, but the five-document claim lacks the Information Security citation.
- Root cause: answer content or citation coverage did not preserve all required policy facts.
- Mitigation: keep the frozen prompts unchanged for this final, and record the defect for future controlled experiments only.

## Tone Failures

- ibm/granite-4-h-small::casual_message: 9 outputs failed final human-validity review.
- ibm/granite-4-h-small::concise_executive_briefing: 8 outputs failed final human-validity review.
- mistralai/mistral-small-3-1-24b-instruct-2503::casual_message: 7 outputs failed final human-validity review.
- mistralai/mistral-small-3-1-24b-instruct-2503::concise_executive_briefing: 5 outputs failed final human-validity review.
- mistralai/mistral-small-3-1-24b-instruct-2503::formal_report_summary: 1 outputs failed final human-validity review.
