from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.schemas.standard import RecommendRequest, RecommendResponse
from backend.app.services.document_parser import extract_text_from_upload
from backend.app.services.recommendation_pipeline import recommend_standards

router = APIRouter(prefix="/api", tags=["recommendation"])


@router.post("/recommend-standards", response_model=RecommendResponse)
def recommend(body: RecommendRequest, db: Session = Depends(get_db)):
    return recommend_standards(
        db,
        query=body.query,
        top_k=body.top_k,
        source_language=body.source_language,
    )


@router.post("/recommend-standards/upload", response_model=RecommendResponse)
async def recommend_from_upload(
    file: UploadFile = File(...),
    top_k: int = Form(5),
    source_language: str | None = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    text = extract_text_from_upload(file.filename or "upload.txt", content)
    query = text[:8000] if text else ""
    return recommend_standards(db, query=query or "building materials procurement", top_k=top_k, source_language=source_language)
