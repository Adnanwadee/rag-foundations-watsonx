def test_public_imports_succeed() -> None:
    import rag_foundations

    assert rag_foundations.UNSUPPORTED_ANSWER == "I don't know based on the provided documents."


def test_module_imports_do_not_require_environment() -> None:
    from rag_foundations import config, errors, logging_config, schemas

    assert config.AppSettings
    assert errors.RAGFoundationsError
    assert logging_config.configure_logging
    assert schemas.DocumentMetadata
