from sqlalchemy.orm import Session

from backend.app.models.standard import StandardModel
from backend.app.schemas.standard import VersionInfo


def get_latest_version(db: Session, is_number: str) -> StandardModel | None:
    rows = (
        db.query(StandardModel)
        .filter(StandardModel.is_number == is_number)
        .order_by(StandardModel.publication_date.desc())
        .all()
    )
    if not rows:
        return None
    # Prefer non-superseded
    active = [r for r in rows if not r.superseded_by]
    return active[0] if active else rows[0]


def validate_version(db: Session, standard: StandardModel) -> VersionInfo:
    latest = get_latest_version(db, standard.is_number)
    if not latest:
        latest = standard

    is_latest = standard.id == latest.id and not standard.superseded_by

    key_changes = None
    if not is_latest and latest.id != standard.id:
        key_changes = (
            f"Newer edition published on {latest.publication_date}. "
            f"Review amendments: {', '.join(latest.amendment_history) or 'none listed'}."
        )
    elif standard.superseded_by:
        key_changes = f"Superseded by {standard.superseded_by}. Use latest edition for procurement."

    return VersionInfo(
        current_version=standard.publication_date,
        latest_version=latest.publication_date,
        is_latest=is_latest,
        amendments=standard.amendment_history,
        superseded_by=standard.superseded_by,
        key_changes=key_changes,
    )
