# 🇮🇳 AI-Powered Indian Standards Recommendation System

### SIH 2026 — PS-108

An AI-powered procurement assistant that understands natural-language product/technical requirements and recommends relevant Indian Standards using **Hybrid RAG: BM25 + Semantic Embeddings + FAISS + Cross-Encoder Reranking**. It also supports PDF/DOCX tender documents, multilingual input, version validation, certification and related-standard information.

---

## 🚀 1. What This Project Does

The system converts an unstructured procurement requirement into ranked Indian Standard recommendations.

### Core Workflow

**User Query / PDF / DOCX**
->
**Language Detection & Translation**
->
**BM25 Keyword Retrieval + FAISS Semantic Retrieval**
->
**Candidate Merging**
->
**Cross-Encoder Reranking**
->
**Top-K Recommended Standards**
->
**Version + Certification + Allied Standards**
->
**Final Results on Dashboard**

The pipeline follows:

> **Understand → Retrieve → Rerank → Validate → Explain**

It can identify relevant standards even when the user's wording differs from the wording used in the standards database.

---

# 🧠 2. AI Workflow — How It Works

1. **Input Understanding**
   Accepts natural-language queries or PDF/DOCX tender documents.

2. **Language Processing**
   Detects the input language and translates it to English when required.

3. **Hybrid Retrieval**

   * **BM25** → exact keyword/technical-term matching.
   * **Sentence Transformers + FAISS** → semantic similarity search.

4. **Candidate Generation**
   BM25 and FAISS results are merged into a common candidate pool.

5. **AI Reranking**
   A **Cross-Encoder** evaluates the query against each candidate and produces relevance scores.

6. **Procurement Intelligence**
   Recommendations are enriched with version/amendment information, certification, normative references, testing, safety, installation and related standards.

---

# 📁 3. Project Structure

```text
prototypesih/
├── backend/
│   └── app/
│       ├── api/routes/
│       │   ├── recommend.py
│       │   ├── standards.py
│       │   └── admin.py
│       ├── services/
│       │   ├── recommendation_engine.py
│       │   ├── recommendation_pipeline.py
│       │   ├── document_parser.py
│       │   ├── translation.py
│       │   ├── version_validation.py
│       │   ├── certification.py
│       │   └── allied_standards.py
│       ├── config.py
│       ├── db.py
│       └── main.py
├── frontend/
│   └── streamlit_app.py
├── data/
│   └── standards/
├── data/scripts/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Important Components

| Component               | Purpose                        |
| ----------------------- | ------------------------------ |
| Recommendation Engine   | BM25 + FAISS + Cross-Encoder   |
| Recommendation Pipeline | End-to-end AI workflow         |
| Document Parser         | PDF/DOCX extraction            |
| Translation             | Language detection/translation |
| Version Validation      | Version and amendment checking |
| Certification           | Certification information      |
| Allied Standards        | Related/normative standards    |
| Streamlit App           | User dashboard                 |
| Admin APIs              | Data and index management      |

---

# 🖥️ 4. Dashboard

### 🔎 Recommend Standards

The Streamlit dashboard allows users to:

* Enter a product/technical requirement.
* Select or detect language.
* Upload PDF/DOCX tender documents.
* Select the number of recommendations.

Results display:

* Ranked standards
* Relevance score
* Detected/translated query
* Standard information
* Version validation
* Certification information
* Normative/testing/safety/installation standards
* Related standards

### ⚙️ Admin

Provides:

* Reload standards
* Rebuild BM25 + FAISS indexes
* Add standards
* View database count

---

# 🛠️ 5. Technology Stack

### Backend

* Python 3.11
* FastAPI
* Uvicorn
* Pydantic
* SQLAlchemy
* Alembic

### AI / RAG

* Sentence Transformers — `all-MiniLM-L6-v2`
* FAISS CPU
* BM25
* Cross-Encoder — `ms-marco-MiniLM-L-6-v2`

### Processing

* pypdf
* python-docx
* langdetect
* deep-translator

### Frontend & Infrastructure

* Streamlit
* SQLite
* PostgreSQL 16
* Docker / Docker Compose

---

# 🌐 6. Ports

| Service    |   Port | Purpose     |
| ---------- | -----: | ----------- |
| FastAPI    | `8000` | Backend/API |
| Streamlit  | `8501` | Dashboard   |
| PostgreSQL | `5432` | Database    |

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🔌 7. API Endpoints

### Recommendation

```text
POST /api/recommend-standards
```

Natural-language standard recommendation.

```text
POST /api/recommend-standards/upload
```

PDF/DOCX-based recommendation.

### Standards

```text
GET    /api/standards
GET    /api/standards/count
GET    /api/standards/{standard_id}
POST   /api/standards
PUT    /api/standards/{standard_id}
DELETE /api/standards/{standard_id}
```

### Admin

```text
POST /api/admin/seed
POST /api/admin/rebuild-index
```

### Health

```text
GET /health
```

---

# ▶️ 8. Quick Start

```bash
git clone <repository-url>
cd prototypesih

python -m venv .venv
pip install -r requirements.txt

python data/scripts/generate_standards_dataset.py
```

### Start API

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### Start Dashboard

```bash
streamlit run frontend/streamlit_app.py
```




# 📌 9. Prototype Status

### Implemented

* Hybrid AI recommendation engine
* BM25 retrieval
* FAISS semantic retrieval
* Cross-Encoder reranking
* PDF/DOCX processing
* Multilingual input
* Version validation
* Certification information
* Allied standards
* Streamlit dashboard
* Standards CRUD
* Index rebuilding
* SQLite/PostgreSQL support
* Docker deployment

### Important Note

The current dataset contains **500+ BIS-style records with a mixture of curated real IS numbers and synthetic entries**. For production, it should be replaced with authoritative official BIS data.

---

# 🎯 10. Future Vision

```text
Procurement Requirement
        ↓
AI Understanding
        ↓
Applicable Indian Standards
        ↓
Version & Amendment Validation
        ↓
Certification & Related Standards
        ↓
Specification Assistance
        ↓
Future Compliance Intelligence
```

The current prototype provides the **AI retrieval and recommendation foundation** for an intelligent procurement-support platform.
