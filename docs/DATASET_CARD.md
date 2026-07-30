# Dataset Card — Asteron Policies Corpus v2.1

## Dataset Summary

| Item | Value |
| --- | --- |
| Dataset name | Asteron Policies Corpus |
| Dataset version | `asteron-policies-v2.1` |
| Organization represented | Asteron — fictional organization |
| Data type | Synthetic Markdown policy documents |
| Number of documents | 5 |
| Sections per document | 12 |
| Total sections | 60 |
| Total manifest word count | 11,250 |
| Registered policy facts | 89 |
| Normative facts | 89 |
| Selected retrieval chunks | 70 |
| Selected chunk size | 220 tokens |
| Selected overlap | 40 tokens |
| Selected embedding dimension | 768 |
| Primary language | English |
| Personal or confidential data | None |
| Real company policy data | None |
| Legal or operational authority | None |
| Intended purpose | Controlled RAG development and evaluation |

---

## 1. Dataset Identity

The **Asteron Policies Corpus v2.1** is a fully synthetic document collection created for the Prompting and RAG Foundations project.

It represents policy documents belonging to a fictional organization named **Asteron**.

The dataset was constructed to support controlled experiments involving:

- document ingestion;
- section-aware chunking;
- semantic retrieval;
- vector-store construction;
- grounded question answering;
- source citation;
- unsupported-question refusal;
- multi-source answer synthesis;
- prompt evaluation;
- model comparison.

The corpus does not contain material copied from a real organization and must not be interpreted as actual:

- employment guidance;
- legal advice;
- human-resources policy;
- travel policy;
- financial guidance;
- access-control guidance;
- information-security instruction.

---

## 2. Motivation

A controlled synthetic corpus was selected instead of real company documents for four main reasons.

### 2.1 Known ground truth

The expected facts, conditions, exceptions, authorities, quantities, and deadlines are explicitly known.

This allows the project to determine whether:

- retrieval found the correct source;
- generation preserved the correct value;
- an approval authority was omitted or changed;
- an unsupported answer was invented;
- a multi-source answer was incomplete.

### 2.2 Privacy and confidentiality

No employee records, confidential policies, customer information, credentials, or proprietary company content are required.

### 2.3 Reproducibility

The same five documents, manifest, fact registry, selected chunks, index configuration, and evaluation questions can be retained in the repository.

This allows another reviewer to verify the project without obtaining external documents.

### 2.4 Controlled difficulty

The documents intentionally include:

- related policy concepts;
- similar headings;
- numeric thresholds;
- deadlines;
- approval authorities;
- conditions and exceptions;
- negative rules;
- related but non-equivalent concepts;
- repeated narrative structures;
- distractor clauses;
- rare lexical markers;
- unsupported topics.

These properties make retrieval and grounding behavior measurable rather than relying only on easy keyword matches.

---

## 3. Dataset Composition

The corpus contains five versioned Markdown documents.

| Document ID | Document title | Owner | Sections | Words | Registered facts | Selected chunks |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| `policy-employee-leave-v2-1` | Employee Leave and Attendance Policy | People Operations | 12 | 2,253 | 14 | 14 |
| `policy-flexible-work-v2-1` | Flexible Work and Workplace Access Policy | People Operations | 12 | 2,255 | 18 | 14 |
| `policy-information-security-v2-1` | Information Security and Access Control Policy | Information Security | 12 | 2,235 | 19 | 14 |
| `policy-travel-expense-v2-1` | Travel, Expense, and Corporate Card Policy | Finance | 12 | 2,263 | 23 | 14 |
| `policy-code-conduct-v2-1` | Code of Conduct, Conflicts, and Reporting Policy | Legal Coordination | 12 | 2,244 | 15 | 14 |
| **Total** | **Five documents** | — | **60** | **11,250** | **89** | **70** |

All five manifest records use:

```text
Version:            2.1
Effective date:     2026-07-28
Next review date:   2027-01-15
Document type:      policy
Synthetic content:  true
Legal advice:       false
```

The dates are fictional benchmark metadata and do not establish real policy validity.

---

## 4. Document Content

## 4.1 Employee Leave and Attendance Policy

**Source path:**

```text
data/documents_v2_1/employee_leave_attendance_policy.md
```

The document covers:

1. purpose and scope;
2. definitions and working days;
3. annual-leave entitlement and accrual;
4. probation, advance leave, and eligibility;
5. long-leave requests and approval;
6. sick-leave notification and evidence;
7. emergency and family leave;
8. coverage, handover, and calendar controls;
9. carryover, expiry, and extensions;
10. unplanned absence and return to work;
11. records and payroll;
12. exceptions, ownership, and review.

The fact registry contains 14 facts for this document.

Representative question types include:

- annual-leave entitlement;
- probation restrictions;
- advance-leave limits;
- approval requirements;
- long-leave notice periods;
- sickness-notification timing;
- carryover and expiry.

---

## 4.2 Flexible Work and Workplace Access Policy

**Source path:**

```text
data/documents_v2_1/flexible_work_workplace_access_policy.md
```

The document covers:

1. purpose and scope;
2. flexible-work eligibility;
3. standard location and weekly limits;
4. approval workflow;
5. duration and renewal;
6. core hours and availability;
7. office and client obligations;
8. working from outside Kuwait;
9. temporary and continuity arrangements;
10. equipment and workspace;
11. workplace access and visitors;
12. exceptions, ownership, and review.

The fact registry contains 18 facts for this document.

Representative question types include:

- flexible-work eligibility;
- approval and review;
- office-attendance obligations;
- working outside Kuwait;
- visitor handling;
- visitor-record retention;
- equipment and connectivity.

---

## 4.3 Information Security and Access Control Policy

**Source path:**

```text
data/documents_v2_1/information_security_access_control_policy.md
```

The document covers:

1. purpose and scope;
2. identities and passwords;
3. multi-factor authentication and sessions;
4. access requests and least privilege;
5. privileged and emergency access;
6. data classification and storage;
7. remote access and device security;
8. phishing and suspicious messages;
9. incidents and lost devices;
10. access review and removal;
11. joiners, movers, and exits;
12. exceptions, endpoint protection, and review.

The fact registry contains 19 facts for this document.

Representative question types include:

- account sharing;
- authentication requirements;
- privileged-access approvals;
- emergency access;
- remote-device requirements;
- incident reporting;
- periodic access review;
- removal of unnecessary access.

---

## 4.4 Travel, Expense, and Corporate Card Policy

**Source path:**

```text
data/documents_v2_1/travel_expense_corporate_card_policy.md
```

The document covers:

1. purpose and scope;
2. pre-approval and booking;
3. air travel and class of service;
4. accommodation;
5. ground transport and mileage;
6. meals and daily limits;
7. entertainment and business gifts;
8. training, mobile, and internet costs;
9. receipts and missing documentation;
10. submission deadlines and currency conversion;
11. corporate cards and personal charges;
12. exceptions, disputes, ownership, and review.

The fact registry contains 23 facts for this document.

Representative question types include:

- travel pre-approval;
- premium-economy approval;
- business-class exceptions;
- hotel limits;
- meal thresholds;
- receipt requirements;
- expense deadlines;
- corporate-card handling.

---

## 4.5 Code of Conduct, Conflicts, and Reporting Policy

**Source path:**

```text
data/documents_v2_1/code_conduct_conflicts_reporting_policy.md
```

The document covers:

1. purpose and scope;
2. expected conduct and manager responsibilities;
3. conflicts of interest;
4. outside employment and relationships;
5. gifts, hospitality, and serious offences;
6. procurement integrity;
7. confidentiality and records accuracy;
8. reporting channels;
9. non-retaliation;
10. investigations and discipline;
11. acknowledgments and new joiners;
12. ownership, guidance, and review.

The fact registry contains 15 facts for this document.

Representative question types include:

- conflict disclosure;
- outside employment;
- gifts and hospitality;
- records accuracy;
- available reporting channels;
- non-retaliation;
- investigation behavior;
- annual acknowledgment.

---

## 5. Source Format

All source documents are stored as UTF-8 Markdown files.

The documents use:

- one document title;
- versioned metadata;
- second-level Markdown headings for policy sections;
- descriptive prose;
- explicit policy statements;
- section-specific rules;
- controlled benchmark clauses.

The ingestion pipeline uses the Markdown headings to preserve section provenance.

The source files are loaded through:

```text
data/manifest_v2_1.json
```

rather than by scanning arbitrary Markdown files.

This supports deterministic:

- document identity;
- loading order;
- source-path validation;
- title validation;
- section-count validation;
- checksum verification;
- version tracking.

---

## 6. Manifest

The authoritative corpus manifest is:

```text
data/manifest_v2_1.json
```

For each document, the manifest records:

- corpus version;
- document ID;
- document title;
- document type;
- owner;
- version;
- effective date;
- next review date;
- source path;
- section count;
- ordered section titles;
- word count;
- SHA-256 checksum;
- synthetic-content flag;
- legal-advice flag;
- summary;
- tags.

The manifest-level fields also confirm:

```text
corpus_version:              asteron-policies-v2.1
document_count:              5
synthetic_training_content:  true
legal_advice:                false
```

---

## 7. Fact Registry

The structured fact registry is stored at:

```text
data/corpus_fact_registry_v2_1.json
```

It contains:

```text
89 facts
89 normative facts
89 structured semantic-clause records
```

### Fact distribution

| Fact prefix | Document | Count |
| --- | --- | ---: |
| `EL` | Employee Leave and Attendance | 14 |
| `FW` | Flexible Work and Workplace Access | 18 |
| `IS` | Information Security and Access Control | 19 |
| `EX` | Travel, Expense, and Corporate Card | 23 |
| `CO` | Code of Conduct, Conflicts, and Reporting | 15 |
| **Total** | — | **89** |

Each fact record identifies:

- a stable fact ID;
- source document ID;
- source section;
- canonical statement;
- exact source quote;
- normative status;
- one or more semantic-clause fields.

The semantic representation can record:

- subject;
- predicate;
- object;
- scope;
- modality;
- negation;
- quantities and units;
- conditions;
- exceptions;
- approval authorities;
- source quotation.

Not every field contains a value for every fact. The structure is used to preserve the types of information that are important when assessing grounded answers.

### Intended role of the registry

The registry supports:

- question design;
- expected-answer preparation;
- semantic review;
- quantity and authority checking;
- failure diagnosis;
- traceability from an answer to a policy clause.

It is not used to replace retrieval during the live assistant workflow.

The assistant retrieves from document chunks, not directly from the fact registry.

---

## 8. Deliberate Benchmark Features

The source documents include several controlled features intended to make the benchmark more diagnostic.

## 8.1 Similar topics across documents

Related concepts appear in multiple policy contexts.

Examples include:

- approvals;
- records;
- reviews;
- exceptions;
- reporting;
- access;
- employee responsibilities.

This creates competition between semantically similar chunks.

## 8.2 Conditions and exceptions

Rules often contain:

- eligibility conditions;
- time windows;
- named approval authorities;
- exceptions;
- prohibited behavior;
- negative statements.

This tests whether the generated answer preserves the entire rule rather than one isolated phrase.

## 8.3 Numeric details

The corpus contains controlled:

- day counts;
- hour limits;
- monetary limits;
- retention periods;
- review frequencies;
- submission deadlines.

Numeric questions help reveal whether a model:

- copies the correct number;
- omits its unit;
- applies it to the wrong context;
- confuses a related limit.

## 8.4 Multi-source requirements

Some evaluation questions require evidence from:

- more than one section;
- more than one document;
- multiple clauses inside a long section.

This separates retrieval-hit performance from complete answer synthesis.

## 8.5 Unsupported concepts

The final question set includes concepts not contained in the corpus.

These cases test whether the model:

- returns the canonical refusal;
- leaves citations empty;
- avoids substituting a loosely related policy rule.

## 8.6 Distractor clauses

Some sections contain descriptive benchmark prose and related but non-normative language.

The distractors are intended to test whether retrieval and generation distinguish the actual policy commitment from surrounding text.

## 8.7 Rare lexical markers

Controlled lexical markers appear in selected descriptive clauses.

Their role is diagnostic: they make it possible to distinguish chunks and inspect retrieval behavior under repeated section structures.

These markers are not policy requirements and should not be treated as expected-answer facts.

---

## 9. Chunking Representation

The selected retrieval representation uses:

```text
Chunk size:         220 tokens
Chunk overlap:      40 tokens
Chunker ID:         section-token-v1-size-220-overlap-40-minilm
Token-count method: sentence-transformers/all-MiniLM-L6-v2 tokenizer
```

The selected chunk metadata is stored in:

```text
data/indexes/selected/metadata.json
```

### Selected chunk statistics

| Statistic | Value |
| --- | ---: |
| Total chunks | 70 |
| Chunks per document | 14 |
| Minimum recorded token count | 112 |
| Maximum recorded token count | 220 |
| Mean recorded token count | Approximately 162.7 |
| Sections represented by one chunk | 50 |
| Sections represented by two chunks | 10 |

Every document contains 12 sections but produces 14 chunks:

```text
12 section records
+ 2 additional chunks created by longer sections
= 14 chunks per document
```

The ten sections that exceed one selected chunk are distributed across the five documents, with two long sections per document.

### Chunk metadata

Each selected chunk record includes:

- checksum;
- chunk ID;
- chunk index;
- chunker configuration ID;
- corpus version;
- document ID;
- document title;
- source path;
- section heading;
- token count;
- embedding model ID;
- embedding dimension;
- FAISS position;
- selected index ID;
- chunk text.

This allows a retrieved vector position to be traced back to the exact source document and section.

---

## 10. Selected Vector Index

The selected index is stored under:

```text
data/indexes/selected/
```

The index configuration is stored at:

```text
data/indexes/selected/index_config.json
```

### Selected index properties

| Property | Value |
| --- | --- |
| Index ID | `selected-chunk-220-overlap-40` |
| Index version | `faiss-flat-ip-v1` |
| Index type | FAISS flat inner-product |
| Similarity metric | Cosine similarity |
| Vector count | 70 |
| Metadata count | 70 |
| Embedding model | `ibm/granite-embedding-278m-multilingual` |
| Embedding dimension | 768 |
| Corpus version | `asteron-policies-v2.1` |

The vectors are normalized so that inner-product search represents cosine similarity.

The selected index is a frozen project artifact and is not rebuilt during ordinary validation.

---

## 11. Relationship to Evaluation Data

The document corpus and the evaluation sets are separate artifacts.

### Knowledge corpus

```text
data/documents_v2_1/
data/manifest_v2_1.json
data/corpus_fact_registry_v2_1.json
data/indexes/selected/
```

### Development and experiment evidence

```text
data/evaluation/development_v2_1/
data/evaluation/experiments/
```

### Final evaluation evidence

```text
data/evaluation/final_v2/
```

The final grounded evaluation contains:

```text
24 questions
├── 20 answerable
└── 4 unsupported
```

The final tone evaluation contains:

```text
20 source inputs
× 3 tones
× 2 models
= 120 saved tone outputs
```

No model fine-tuning was performed on the corpus.

The documents act as a retrieval knowledge base, while the question and tone-input artifacts are used for evaluation.

---

## 12. Development and Final-Evaluation Separation

Chunking, retrieval depth, and prompt candidates were compared during development.

After selecting the final configuration:

- the corpus was frozen;
- the selected chunks were frozen;
- the FAISS index was frozen;
- the prompt assets were frozen;
- the final question set was frozen;
- final outputs were saved;
- scoring and owner review were preserved.

The final configuration was not changed to correct individual final-test failures.

This reduces the risk of post-final tuning and preserves the interpretability of the reported metrics.

---

## 13. Intended Uses

The dataset is suitable for:

- educational RAG projects;
- document-loader testing;
- chunking experiments;
- semantic-retrieval experiments;
- vector-index validation;
- source-citation testing;
- unsupported-question testing;
- prompt-engineering exercises;
- structured-output evaluation;
- grounded-answer scoring;
- tone-transformation evaluation;
- controlled model comparison;
- regression testing;
- demonstration of evidence preservation.

---

## 14. Uses Outside the Intended Scope

The dataset should not be used as:

- actual company policy;
- legal advice;
- employee guidance;
- a basis for disciplinary decisions;
- financial or expense authority;
- information-security authority;
- a production access-control policy;
- real travel approval guidance;
- a source for medical or leave decisions;
- a benchmark for unrestricted general-domain RAG;
- proof of production readiness on noisy enterprise documents.

---

## 15. Data Quality Controls

The repository applies several quality checks.

### 15.1 Manifest validation

The validator confirms:

- five expected documents;
- valid source paths;
- matching document IDs and titles;
- expected section counts;
- source checksums;
- corpus version;
- fact-registry consistency.

### 15.2 Structural checks

The corpus validator checks:

- 60 total sections;
- 89 registered facts;
- minimum document and section requirements;
- chunking preflight;
- repeated-content characteristics;
- expected corpus identity.

### 15.3 Selected-index checks

The FAISS preflight confirms:

- 70 vectors;
- 70 metadata records;
- selected 220/40 chunk configuration;
- embedding model identity;
- embedding dimension 768;
- internal index and metadata consistency;
- zero external calls;
- zero file writes.

### 15.4 Protected hashes

The final repository protects aggregate hashes for:

```text
data/documents_v2_1/
data/evaluation/
data/indexes/
prompts/
```

The final code-hardening pass preserved these values unchanged.

---

## 16. Validation Commands

### Validate the corpus

```powershell
python scripts/validate_corpus_v2_1.py
```

Expected high-level result:

```text
Documents: 5
Sections: 60
Facts: 89
Status: OK
```

### Validate the selected index without external calls

```powershell
python scripts/build_watsonx_faiss_index.py --preflight-only
```

Expected high-level result:

```text
Documents loaded: 5
Sections loaded: 60
Selected vectors: 70
Selected metadata records: 70
Chunk size/overlap: 220/40
Embedding model: ibm/granite-embedding-278m-multilingual
Embedding dimension: 768
External calls: 0
Files written: 0
```

### Validate all final evidence

```powershell
python scripts/validate_final_v2.py
python scripts/validate_project_complete.py
```

---

## 17. Privacy and Confidentiality

The corpus contains no known:

- real employee names;
- real personnel records;
- customer information;
- financial account information;
- API keys;
- authentication tokens;
- real organization identifiers;
- confidential business data;
- proprietary internal documents.

The Asteron organization, policies, roles, dates, limits, and procedures are fictional benchmark content.

The corpus is appropriate for inclusion in the project repository because it does not require access to private or licensed company documents.

---

## 18. Ethical Considerations

Synthetic policy text can still resemble authoritative guidance.

For this reason, the repository explicitly identifies the content as fictional and synthetic.

Users should not:

- apply the rules to real employees;
- present the documents as real legal requirements;
- use generated answers for employment decisions;
- rely on the corpus for security approval;
- use travel or expense values as real reimbursement rules;
- interpret benchmark dates as current legal requirements.

The primary ethical benefit of the dataset is that it allows grounded-answer behavior to be studied without exposing real people or organizations.

---

## 19. Limitations

## 19.1 Benchmark-oriented language

The documents contain repeated descriptive patterns and controlled distractors.

This improves diagnostic value but reduces the naturalness of the prose compared with real corporate policy documents.

## 19.2 Markdown-only source format

The corpus does not test:

- scanned PDFs;
- OCR errors;
- page headers and footers;
- tables extracted from PDFs;
- images or diagrams;
- broken encodings;
- document-layout reconstruction.

## 19.3 Small corpus size

Five documents are sufficient for the Tier-1 assignment, but the results do not automatically predict behavior on:

- thousands of documents;
- rapidly changing knowledge bases;
- multiple departments with conflicting policies;
- permission-restricted enterprise content.

## 19.4 Controlled vocabulary

Some aliases and lexical markers are deliberately constructed.

Real users may use more varied, ambiguous, misspelled, or domain-specific language.

## 19.5 Synthetic expected answers

The fact registry provides unusually clear ground truth.

Real policy interpretation can involve ambiguity, legal context, superseded versions, or conflicting documents.

## 19.6 Evaluation specificity

Reported metrics measure behavior on this versioned corpus, selected index, prompt set, question set, and model configuration.

They should not be interpreted as universal RAG accuracy.

## 19.7 No policy lifecycle simulation

The corpus includes version and review metadata but does not implement:

- policy approval workflows;
- superseded-document resolution;
- effective-date filtering;
- incremental re-indexing;
- role-based document access;
- deletion or retention workflows.

---

## 20. Potential Production Extensions

A production-oriented dataset and ingestion workflow would additionally require:

- approved real source documents;
- document-owner verification;
- privacy and legal review;
- document-level permissions;
- source-system connectors;
- PDF and OCR processing;
- table and layout extraction;
- version and supersession handling;
- scheduled re-indexing;
- stale-content detection;
- access logging;
- audit trails;
- retention controls;
- multilingual policy review;
- larger-scale retrieval evaluation;
- adversarial and security testing.

These extensions are outside the Tier-1 project scope.

---

## 21. Reproducibility

The corpus can be reproduced and verified from tracked repository files.

Important artifacts include:

```text
data/manifest_v2_1.json
data/corpus_fact_registry_v2_1.json
data/documents_v2_1/
data/indexes/selected/index_config.json
data/indexes/selected/metadata.json
data/indexes/selected/asteron_policies_watsonx.index
```

The manifest contains per-document SHA-256 checksums.

The selected index configuration records:

- corpus version;
- chunker configuration;
- embedding model;
- embedding dimension;
- vector count;
- similarity metric;
- index version;
- index identity.

The final project validators and protected-hash manifests verify that the corpus and selected index have not changed after evaluation.

---

## 22. Versioning

### Current version

```text
asteron-policies-v2.1
```

### Version identity

| Field | Value |
| --- | --- |
| Corpus version | `asteron-policies-v2.1` |
| Manifest ID | `asteron-policies-v2-1-manifest` |
| Document version | `2.1` |
| Selected index ID | `selected-chunk-220-overlap-40` |
| Selected chunker ID | `section-token-v1-size-220-overlap-40-minilm` |

A future corpus version should use:

- new document versions;
- a new manifest ID;
- recalculated source checksums;
- a new fact registry;
- a newly built index;
- a new selected-index ID;
- new evaluation evidence.

Existing frozen evaluation artifacts should not be silently reused with changed source documents.

---

## 23. Final Dataset Status

```text
Synthetic disclosure:        Complete
Document count:              5
Section count:               60
Manifest word count:         11,250
Registered facts:            89
Selected chunks:             70
Selected vectors:            70
Metadata records:            70
Manifest validation:         Pass
Fact-registry validation:    Pass
Selected-index validation:   Pass
Privacy review:              No real personal data
Protected-hash verification: Pass
Final-evaluation freeze:     Complete
```

The Asteron Policies Corpus v2.1 is therefore suitable for the controlled educational RAG, grounding, citation, refusal, prompt, and model-comparison tasks implemented in this repository.
