INGESTION_RESULT_KEYS = (
    "pdf_analysis",
    "pdf_extractions",
    "knowledge_apply_result",
    "selected_extraction_standards",
    "apply_extraction_standards",
)


def reset_for_document_change(session_state, document_sha256: str | None) -> bool:
    """Clear staged review data when the selected source PDF changes."""
    state_key = "pdf_analysis_document_sha256"
    if session_state.get(state_key) == document_sha256:
        return False
    for key in INGESTION_RESULT_KEYS:
        session_state.pop(key, None)
    session_state[state_key] = document_sha256
    return True
