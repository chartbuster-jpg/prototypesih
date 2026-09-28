import json
import os

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="BIS Standards Recommendation | PS-108",
    page_icon="📋",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 40%); }
    .score-pill { background:#0f766e;color:white;padding:4px 10px;border-radius:999px;font-size:0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("AI-Powered Indian Standards Recommendation")
st.caption("SIH 2026 · PS-108 · Procurement specification assistant (English + Indian languages)")

tab_search, tab_admin = st.tabs(["Recommend Standards", "Admin"])

with tab_search:
    col1, col2 = st.columns([2, 1])
    with col1:
        query = st.text_area(
            "Product description or technical specification",
            placeholder="Example: Galvanized steel water supply pipes for municipal project...",
            height=120,
        )
    with col2:
        lang = st.selectbox(
            "Input language",
            ["auto", "en", "hi", "ta", "te", "bn", "mr", "gu", "kn", "ml", "or", "pa"],
        )
        top_k = st.slider("Results", 3, 10, 5)
        uploaded = st.file_uploader("Tender document (PDF/DOCX)", type=["pdf", "docx"])

    if st.button("Get Recommendations", type="primary"):
        with st.spinner("Searching BIS standards (hybrid RAG)..."):
            try:
                if uploaded is not None:
                    files = {"file": (uploaded.name, uploaded.getvalue())}
                    data = {"top_k": str(top_k)}
                    if lang != "auto":
                        data["source_language"] = lang
                    resp = requests.post(
                        f"{API_BASE}/api/recommend-standards/upload",
                        files=files,
                        data=data,
                        timeout=120,
                    )
                else:
                    payload = {"query": query, "top_k": top_k}
                    if lang != "auto":
                        payload["source_language"] = lang
                    resp = requests.post(
                        f"{API_BASE}/api/recommend-standards",
                        json=payload,
                        timeout=120,
                    )
                resp.raise_for_status()
                result = resp.json()
            except Exception as exc:
                st.error(f"API error: {exc}. Start backend: uvicorn backend.app.main:app --reload")
                st.stop()

        st.success(f"Completed in {result['latency_ms']} ms · Detected language: {result['detected_language']}")
        if result.get("query_translated"):
            st.info(f"Translated query (EN): {result['query_translated']}")

        for i, rec in enumerate(result["recommendations"], start=1):
            s = rec["standard"]
            label = f"{i}. {s['is_number']}" + (f" ({s['part']})" if s.get("part") else "")
            with st.expander(f"{label} — {s['title']}  ·  score {rec['relevance_score']:.2f}", expanded=i == 1):
                st.markdown(f"**Domain:** {s['domain']}")
                st.write(s["abstract"])
                st.markdown(f'<span class="score-pill">Relevance {rec["relevance_score"]:.2f}</span>', unsafe_allow_html=True)

                v = rec["version_info"]
                st.subheader("Version validation")
                st.write(
                    {
                        "current_version": v["current_version"],
                        "latest_version": v["latest_version"],
                        "is_latest": v["is_latest"],
                        "amendments": v["amendments"],
                        "superseded_by": v["superseded_by"],
                        "key_changes": v["key_changes"],
                    }
                )

                c = rec["certification_info"]
                st.subheader("Certification")
                st.write(c)

                a = rec["allied_standards"]
                st.subheader("Allied standards")
                cols = st.columns(2)
                with cols[0]:
                    st.markdown("**Normative references**")
                    st.json([x["is_number"] for x in a["normative_references"]] or ["—"])
                    st.markdown("**Test methods**")
                    st.json([f"{x['is_number']}: {x['title'][:60]}" for x in a["test_methods"][:3]])
                with cols[1]:
                    st.markdown("**Safety / Installation**")
                    st.json(
                        {
                            "safety": [x["is_number"] for x in a["safety_standards"][:3]],
                            "installation": [x["is_number"] for x in a["installation_standards"][:3]],
                            "related": [x["is_number"] for x in a["related_products"][:3]],
                        }
                    )

with tab_admin:
    st.subheader("Standards database admin")
    if st.button("Seed / reload standards from JSON"):
        r = requests.post(f"{API_BASE}/api/admin/seed", params={"force": True}, timeout=120)
        st.write(r.json())
    if st.button("Rebuild search indexes (BM25 + FAISS)"):
        r = requests.post(f"{API_BASE}/api/admin/rebuild-index", timeout=120)
        st.write(r.json())

    st.markdown("### Add standard")
    with st.form("add_standard"):
        is_number = st.text_input("IS Number", "IS 9999")
        part = st.text_input("Part", "")
        title = st.text_input("Title", "")
        domain = st.selectbox("Domain", ["Construction Materials", "Testing Methods", "Safety Standards", "Installation Standards", "Electronics", "Chemicals", "Precious Metals"])
        pub = st.text_input("Publication date", "2025-01-01")
        certification = st.text_input("Certification", "BIS Product Certification: Voluntary")
        abstract = st.text_area("Abstract")
        refs = st.text_input("Normative references (comma-separated IS numbers)")
        if st.form_submit_button("Create"):
            payload = {
                "is_number": is_number,
                "part": part or None,
                "title": title,
                "domain": domain,
                "publication_date": pub,
                "certification": certification,
                "abstract": abstract,
                "normative_references": [x.strip() for x in refs.split(",") if x.strip()],
                "amendment_history": [],
                "tags": [],
            }
            r = requests.post(f"{API_BASE}/api/standards", json=payload, timeout=60)
            st.code(json.dumps(r.json(), indent=2))

    try:
        count = requests.get(f"{API_BASE}/api/standards/count", timeout=10).json()
        st.metric("Standards in database", count.get("count", 0))
    except Exception:
        st.warning("API not reachable.")
