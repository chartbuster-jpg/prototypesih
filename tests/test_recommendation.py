import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db import Base
from backend.app.services.recommendation_engine import StandardsRecommendationEngine
from backend.app.services.seed import seed_from_json
from backend.app.models.standard import StandardModel
from backend.app.services.version_validation import validate_version


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_seed_and_hybrid_search(db_session):
    count = seed_from_json(db_session, force=True)
    assert count >= 500
    eng = StandardsRecommendationEngine(db_session)
    eng.build_indexes(force=True)
    results = eng.recommend("galvanized steel water supply pipes", top_k=5)
    assert len(results) >= 1
    is_numbers = [r[0].is_number for r in results]
    assert any(n in ("IS 1239", "IS 4759", "IS 4985") for n in is_numbers) or len(is_numbers) == 5


def test_version_validation(db_session):
    seed_from_json(db_session, force=True)
    row = db_session.query(StandardModel).filter_by(is_number="IS 456").first()
    assert row is not None
    info = validate_version(db_session, row)
    assert info.current_version
    assert info.latest_version
