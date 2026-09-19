import time

from sqlalchemy.orm import Session

from backend.app.schemas.standard import (
    RecommendResponse,
    RecommendedStandard,
    StandardOut,
)
from backend.app.services.allied_standards import get_allied_standards
from backend.app.services.certification import get_certification_info
from backend.app.services.recommendation_engine import get_engine
from backend.app.services.translation import (
    detect_language,
    translate_standard_fields,
    translate_text,
)
from backend.app.services.version_validation import validate_version


def recommend_standards(
    db: Session,
    query: str,
    top_k: int = 5,
    source_language: str | None = None,
) -> RecommendResponse:
    t0 = time.perf_counter()
    detected = source_language or detect_language(query)
    query_en = query
    query_translated = None

    if detected != "en":
        query_en = translate_text(query, detected, "en")
        query_translated = query_en

    engine = get_engine(db)
    hits = engine.recommend(query_en, top_k=top_k)

    recommendations: list[RecommendedStandard] = []
    for row, score in hits:
        std_dict = row.to_dict()
        if detected != "en":
            std_dict = translate_standard_fields(std_dict, detected)
        std_out = StandardOut.model_validate(std_dict)
        recommendations.append(
            RecommendedStandard(
                standard=std_out,
                relevance_score=round(score, 4),
                version_info=validate_version(db, row),
                certification_info=get_certification_info(row),
                allied_standards=get_allied_standards(db, row),
            )
        )

    latency_ms = (time.perf_counter() - t0) * 1000
    return RecommendResponse(
        query=query,
        query_translated=query_translated,
        detected_language=detected,
        latency_ms=round(latency_ms, 2),
        recommendations=recommendations,
    )
