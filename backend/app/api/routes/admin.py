from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.services.recommendation_engine import rebuild_indexes
from backend.app.services.seed import seed_from_json

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/seed")
def seed_database(force: bool = False, db: Session = Depends(get_db)):
    count = seed_from_json(db, force=force)
    rebuild_indexes(db)
    return {"standards_loaded": count}


@router.post("/rebuild-index")
def rebuild_search_index(db: Session = Depends(get_db)):
    rebuild_indexes(db)
    return {"status": "ok"}
