# Scripts

## `build_watsonx_faiss_index.py`

Purpose: rebuild a FAISS index from the synthetic corpus with watsonx embeddings. Offline/live: live. Inputs: corpus and credentials. Output: `artifacts/rebuilt-index/` by default or `--output-dir`. Evidence modification: does not modify frozen evidence unless `--output-dir data/indexes/selected --overwrite` is explicit. Safety: validates 5 documents, 60 sections, 70 chunks, 768 dimensions, 70 vectors, and model ID.

## `run_final_v2.py`

Purpose: Final v2 dry-run and guarded live execution. Offline/live: `--dry-run` is offline; `--execute` and `--resume` are live with confirmation. Inputs: frozen datasets, prompts, retrieval evidence, and credentials. Output: Final v2 evidence. Evidence modification: dry-run none; live execution writes evidence.

## `score_final_v2.py`

Purpose: recompute deterministic and owner-verified scoring from saved evidence. Offline/live: offline. Inputs: saved outputs and `owner_adjudication.json`. Output: scoring JSON and failure analysis. Evidence modification: score artifacts only when intentionally run.

## `validate_corpus_v2_1.py`

Purpose: validate corpus counts, checksums, fact registry, and synthetic declaration. Offline/live: offline. Evidence modification: none.



## `validate_references.py`

Purpose: parse JSON/JSONL, validate retained repository paths, reject personal absolute paths, reject stale workflow terms outside immutable evidence text, and detect obvious credentials. Offline/live: offline. Evidence modification: none.

## `validate_final_v2.py`

Purpose: validate Final v2 datasets, saved output counts, owner artifact, metrics provenance, hashes, and model-selection evidence. Offline/live: offline. Evidence modification: none.

## `validate_project_complete.py`

Purpose: run documentation and project-completion checks together. Offline/live: offline. Evidence modification: none.
