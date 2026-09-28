import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.models.standard import StandardModel


def _search_text(row: dict) -> str:
    parts = [
        row.get("is_number", ""),
        row.get("part") or "",
        row.get("title", ""),
        row.get("domain", ""),
        row.get("abstract", ""),
        " ".join(row.get("tags", [])),
        " ".join(row.get("normative_references", [])),
    ]
    return " ".join(p for p in parts if p).lower()


def load_json_standards(path: str | None = None) -> list[dict]:
    p = Path(path or settings.standards_json_path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def seed_from_json(db: Session, path: str | None = None, force: bool = False) -> int:
    if not force and db.query(StandardModel).count() > 0:
        return db.query(StandardModel).count()

    if force:
        db.query(StandardModel).delete()
        db.commit()

    rows = load_json_standards(path)
    if not rows:
        return 0

    for row in rows:
        db.add(
            StandardModel(
                is_number=row["is_number"],
                part=row.get("part"),
                title=row["title"],
                domain=row["domain"],
                publication_date=row["publication_date"],
                amendment_history_json=json.dumps(row.get("amendment_history", [])),
                superseded_by=row.get("superseded_by"),
                normative_references_json=json.dumps(row.get("normative_references", [])),
                certification=row.get("certification", ""),
                abstract=row.get("abstract", ""),
                tags_json=json.dumps(row.get("tags", [])),
                pdf_url=row.get("pdf_url"),
                search_text=_search_text(row),
            )
        )
    db.commit()
    return db.query(StandardModel).count()
