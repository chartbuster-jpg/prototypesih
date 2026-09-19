import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.models.standard import StandardModel
from backend.app.schemas.standard import StandardCreate, StandardOut, StandardUpdate
from backend.app.services.recommendation_engine import rebuild_indexes
from backend.app.services.seed import _search_text

router = APIRouter(prefix="/api/standards", tags=["standards"])


@router.get("", response_model=list[StandardOut])
def list_standards(
    skip: int = 0,
    limit: int = Query(50, le=200),
    domain: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(StandardModel)
    if domain:
        q = q.filter(StandardModel.domain == domain)
    rows = q.offset(skip).limit(limit).all()
    return [StandardOut.model_validate(r.to_dict()) for r in rows]


@router.get("/count")
def count_standards(db: Session = Depends(get_db)):
    return {"count": db.query(StandardModel).count()}


@router.get("/{standard_id}", response_model=StandardOut)
def get_standard(standard_id: int, db: Session = Depends(get_db)):
    row = db.query(StandardModel).filter(StandardModel.id == standard_id).first()
    if not row:
        raise HTTPException(404, "Standard not found")
    return StandardOut.model_validate(row.to_dict())


@router.post("", response_model=StandardOut)
def create_standard(body: StandardCreate, db: Session = Depends(get_db)):
    data = body.model_dump()
    row = StandardModel(
        is_number=data["is_number"],
        part=data.get("part"),
        title=data["title"],
        domain=data["domain"],
        publication_date=data["publication_date"],
        amendment_history_json=json.dumps(data.get("amendment_history", [])),
        superseded_by=data.get("superseded_by"),
        normative_references_json=json.dumps(data.get("normative_references", [])),
        certification=data["certification"],
        abstract=data["abstract"],
        tags_json=json.dumps(data.get("tags", [])),
        pdf_url=data.get("pdf_url"),
        search_text=_search_text(data),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    rebuild_indexes(db)
    return StandardOut.model_validate(row.to_dict())


@router.put("/{standard_id}", response_model=StandardOut)
def update_standard(standard_id: int, body: StandardUpdate, db: Session = Depends(get_db)):
    row = db.query(StandardModel).filter(StandardModel.id == standard_id).first()
    if not row:
        raise HTTPException(404, "Standard not found")
    data = body.model_dump(exclude_unset=True)
    for key, val in data.items():
        if key == "amendment_history":
            row.amendment_history_json = json.dumps(val or [])
        elif key == "normative_references":
            row.normative_references_json = json.dumps(val or [])
        elif key == "tags":
            row.tags_json = json.dumps(val or [])
        else:
            setattr(row, key, val)
    merged = row.to_dict()
    row.search_text = _search_text(merged)
    db.commit()
    db.refresh(row)
    rebuild_indexes(db)
    return StandardOut.model_validate(row.to_dict())


@router.delete("/{standard_id}")
def delete_standard(standard_id: int, db: Session = Depends(get_db)):
    row = db.query(StandardModel).filter(StandardModel.id == standard_id).first()
    if not row:
        raise HTTPException(404, "Standard not found")
    db.delete(row)
    db.commit()
    rebuild_indexes(db)
    return {"deleted": True}
