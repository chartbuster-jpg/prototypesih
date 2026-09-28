from sqlalchemy.orm import Session

from backend.app.models.standard import StandardModel
from backend.app.schemas.standard import AlliedStandards, StandardOut
from backend.app.services.recommendation_engine import get_engine


def _to_out(row: StandardModel) -> StandardOut:
    return StandardOut.model_validate(row.to_dict())


def _by_is_numbers(db: Session, refs: list[str], limit: int = 10) -> list[StandardModel]:
    if not refs:
        return []
    cleaned = [r.replace("IS ", "").strip() for r in refs]
    q = db.query(StandardModel).filter(StandardModel.is_number.in_(refs))
    found = q.limit(limit).all()
    if found:
        return found
    # fuzzy match on is_number suffix
    out = []
    for ref in cleaned:
        num = ref if ref.startswith("IS") else f"IS {ref}"
        row = db.query(StandardModel).filter(StandardModel.is_number == num).first()
        if row:
            out.append(row)
    return out[:limit]


def query_standards_by_domain(db: Session, domain_keyword: str, product_domain: str, limit: int = 5) -> list[StandardModel]:
    domain_map = {
        "testing": "Testing Methods",
        "safety": "Safety Standards",
        "installation": "Installation Standards",
    }
    domain = domain_map.get(domain_keyword, product_domain)
    return (
        db.query(StandardModel)
        .filter(StandardModel.domain == domain)
        .limit(limit * 3)
        .all()
    )[:limit]


def find_similar_standards(db: Session, standard: StandardModel, top_k: int = 3) -> list[StandardModel]:
    engine = get_engine(db)
    query = f"{standard.title} {standard.domain} {' '.join(standard.tags)}"
    hits = engine.recommend(query, top_k=top_k + 5)
    rows = [row for row, _score in hits if row.id != standard.id][:top_k]
    if not rows:
        return (
            db.query(StandardModel)
            .filter(StandardModel.domain == standard.domain, StandardModel.id != standard.id)
            .limit(top_k)
            .all()
        )
    return rows


def get_allied_standards(db: Session, standard: StandardModel) -> AlliedStandards:
    normative = _by_is_numbers(db, standard.normative_references)
    test_methods = query_standards_by_domain(db, "testing", standard.domain)
    safety = query_standards_by_domain(db, "safety", standard.domain)
    installation = query_standards_by_domain(db, "installation", standard.domain)
    related = find_similar_standards(db, standard, top_k=3)

    return AlliedStandards(
        normative_references=[_to_out(r) for r in normative],
        test_methods=[_to_out(r) for r in test_methods],
        safety_standards=[_to_out(r) for r in safety],
        installation_standards=[_to_out(r) for r in installation],
        related_products=[_to_out(r) for r in related],
    )
