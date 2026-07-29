# Scripts

Final repository scripts:

- `validate_documentation.py`: validates public docs, links, metrics, and secret-like placeholders.
- `validate_corpus_v2_1.py`: validates the retained Corpus v2.1 manifest and documents.
- `validate_final_v2.py`: validates frozen Final v2 evidence.
- `validate_project_complete.py`: runs documentation and Final v2 completion validation.
- `run_final_v2.py`: supports offline dry-run; live execution requires explicit confirmation flags.
- `score_final_v2.py`: recomputes Final v2 scoring from saved evidence.
- `finalize_final_v2.py`: convenience wrapper for Final v2 finalization.
- `build_watsonx_faiss_index.py`: opt-in index builder for the retained corpus.
