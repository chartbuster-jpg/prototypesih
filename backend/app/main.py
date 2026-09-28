import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import admin, recommend, standards
from backend.app.config import ROOT, settings
from backend.app.db import Base, SessionLocal, engine
from backend.app.services.recommendation_engine import get_engine
from backend.app.services.seed import load_json_standards, seed_from_json

app = FastAPI(
    title="PS-108 BIS Standards Recommendation API",
    description="AI-powered Indian Standards recommendation for government procurement (SIH 2026)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(standards.router)
app.include_router(recommend.router)
app.include_router(admin.router)


def _ensure_dataset() -> None:
    json_path = Path(settings.standards_json_path)
    if json_path.exists() and load_json_standards():
        return
    script = ROOT / "data" / "scripts" / "generate_standards_dataset.py"
    subprocess.run([sys.executable, str(script)], check=False)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _ensure_dataset()
    db = SessionLocal()
    try:
        seed_from_json(db)
        get_engine(db).build_indexes()
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "standards_json": settings.standards_json_path}
