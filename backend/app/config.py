from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")

    database_url: str = f"sqlite:///{ROOT / 'data' / 'bis_standards.db'}"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    faiss_index_path: str = str(ROOT / "data" / "index" / "faiss.index")
    bm25_index_path: str = str(ROOT / "data" / "index" / "bm25.pkl")
    standards_json_path: str = str(ROOT / "data" / "standards" / "standards.json")
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    bis_certification_portal: str = "https://bis.gov.in/certification"


settings = Settings()
