# PS-108: AI-Powered Indian Standards Recommendation for Procurement

SIH 2026 prototype — hybrid RAG (BM25 + FAISS + cross-encoder reranking) over 500+ BIS-style standards records (SP 21 / building materials focus).

## Phase 1 features (implemented)

| Feature | Endpoint / UI |
|--------|------------------|
| Standards database (500+) | `data/standards/standards.json`, PostgreSQL/SQLite |
| Hybrid recommendation | `POST /api/recommend-standards` |
| Allied standards | Included in recommendation payload |
| Version validation | `version_info` per result |
| Certification | `certification_info` per result |
| Web UI | Streamlit `:8501` |
| Hindi + 10 languages | `source_language` + auto-detect + translation |
| Admin CRUD | `GET/POST/PUT/DELETE /api/standards`, Admin tab |

## Quick start (Windows / local)

```powershell
cd C:\Users\goura\Projects\ps108-bis-recommendation
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Generate dataset (520 standards)
python data/scripts/generate_standards_dataset.py

# API (seeds DB + builds indexes on startup)
$env:PYTHONPATH = "."
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open API docs: http://127.0.0.1:8000/docs

```powershell
# UI (new terminal)
$env:API_BASE_URL = "http://127.0.0.1:8000"
streamlit run frontend/streamlit_app.py
```

## Example API call

```bash
curl -X POST http://127.0.0.1:8000/api/recommend-standards \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Steel tubes for water supply with zinc coating\", \"top_k\": 5}"
```

## Docker (PostgreSQL)

```bash
docker compose up --build
```

## Tests

```powershell
$env:PYTHONPATH = "."
pytest tests/ -q
```

## Notes

- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2`
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Translation:** `deep-translator` (prototype). Swap in AI4Bharat IndicTrans2 for production.
- Dataset mixes curated real IS numbers with synthetic SP-21-style entries for volume; replace with official BIS exports for production.

## Project layout

```
backend/app/          FastAPI services & RAG engine
frontend/             Streamlit UI
data/standards/       JSON dataset
data/scripts/         Dataset generator
tests/                pytest suite
```

Phase 2 (GFR checker, compliance matrix, Telegram bot) is **not** started until Phase 1 is validated in your environment.
