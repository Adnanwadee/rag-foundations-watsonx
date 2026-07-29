# Architecture

## Offline Ingestion And Indexing

Corpus v2.1 documents are stored in `data/documents_v2_1/` and described by `data/manifest_v2_1.json`. The document loader validates manifest shape, source paths, checksums, titles, and section counts.

The selected index is stored at `data/evaluation/phase_c/retrieval/indexes/chunk-220-overlap-40/`. Its metadata preserves document IDs, section headings, chunk IDs, retriever configuration, and source paths.

## Query-Time Runtime

1. `rag_foundations.cli` parses the user command.
2. `frozen_v2_runtime.verify_frozen_v2_artifacts()` validates protected prompts, manifests, and selected index hashes.
3. The embedding provider embeds the question with `ibm/granite-embedding-278m-multilingual`.
4. FAISS retrieves Top-5 chunks from the selected index.
5. Grounded generation renders Candidate A prompts and parses strict JSON.
6. Citation validation resolves chunk IDs back to local document sections.
7. Optional tone transformation renders the selected tone prompt and parses strict JSON.

## Integrity Controls

Protected hashes are recorded in `data/evaluation/final_v2/manifests/protected_hashes.json`. Runtime validation confirms selected prompt bytes, selected index bytes, corpus manifest, fact registry, frozen configuration, and development set hashes before live components are created.
