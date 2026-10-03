import json
import hashlib
import os
import re

import requests
import streamlit as st
import streamlit.components.v1 as components
from frontend.ingestion_state import reset_for_document_change

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
LANGUAGE_CODES = {
    1: "en",
    2: "hi",
    3: "ta",
    4: "te",
    5: "bn",
    6: "mr",
    7: "gu",
    8: "kn",
    9: "ml",
    10: "or",
    11: "pa",
}


def _batches(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _context_checks(query, standard):
    query_text = query.lower()
    scope = " ".join(
        [standard.get("title", ""), standard.get("abstract", ""), standard.get("domain", "")]
        + standard.get("tags", [])
    ).lower()
    terms = {
        "Product category": ("pipe", "tank", "valve", "cement", "concrete", "wire", "cable", "pump", "brick", "tile", "switch", "helmet"),
        "Material": ("steel", "stainless", "iron", "pvc", "plastic", "concrete", "cement", "aluminium", "aluminum", "copper", "timber", "wood", "glass", "rubber"),
        "Application": ("water", "drinking", "potable", "construction", "building", "electrical", "structural", "drainage", "irrigation", "industrial", "supply"),
        "Capacity / dimensions": ("mm", "cm", "meter", "metre", "litre", "liter", "capacity", "diameter", "size"),
        "Installation / environment": ("indoor", "outdoor", "buried", "underground", "exposed", "coastal", "installation", "environment", "temperature"),
    }
    checks = []
    for label, candidates in terms.items():
        mentioned = [term for term in candidates if term in query_text]
        if label == "Capacity / dimensions":
            import re

            mentioned.extend(re.findall(r"\b\d+(?:\.\d+)?\s?(?:mm|cm|m|l|litre|liter|kg|kw|kva|bar)\b", query_text))
            mentioned = list(dict.fromkeys(mentioned))
        supported = [term for term in mentioned if term in scope]
        if mentioned:
            checks.append((label, bool(supported), ", ".join(supported or mentioned)))
    return checks


def _review_gaps(query):
    text = query.lower()
    categories = {
        "Performance": ("performance", "pressure", "load", "strength", "efficiency", "tolerance", "rating"),
        "Testing": ("test", "testing", "inspection", "sampling", "method"),
        "Safety": ("safety", "hazard", "fire", "electrical protection", "risk"),
        "Marking and labelling": ("marking", "label", "labelling", "traceability", "packaging"),
    }
    return [label for label, terms in categories.items() if not any(term in text for term in terms)]


def _context_summary(query):
    text = query.lower()
    phrases = {
        "Product": ("water storage tank", "storage tank", "tank", "pipe", "cement", "concrete", "valve", "pump", "wire", "cable", "brick", "tile", "helmet"),
        "Material": ("stainless steel", "steel", "pvc", "plastic", "concrete", "cement", "copper", "aluminium", "aluminum", "timber", "wood", "glass", "rubber"),
        "Application": ("potable water", "drinking water", "water supply", "construction", "building", "drainage", "irrigation", "electrical", "structural", "industrial"),
        "Environment": ("outdoors", "outdoor", "indoors", "indoor", "buried", "underground", "coastal", "exposed"),
    }
    facts = {label: next((phrase for phrase in options if phrase in text), None) for label, options in phrases.items()}
    facts["Capacity / dimensions"] = next(iter(re.findall(r"\b\d+(?:\.\d+)?\s?(?:mm|cm|m|l|litre|liter|kg|kw|kva|bar)\b", text)), None)
    return facts


def _render_dependency_map(rec):
    allied = rec.get("allied_standards", {})
    primary = rec["standard"]
    identity = primary["is_number"] + (f" ({primary['part']})" if primary.get("part") else "")
    st.caption("Select a node to inspect its record. Solid links are explicit references; dashed links are candidates based on database category.")
    with st.container(border=True):
        st.caption("PRIMARY STANDARD")
        st.markdown(f"**{identity} — {primary['title']}**")
    st.markdown("<div style='text-align:center;font-size:1.4rem;color:#54717b'>↓</div>", unsafe_allow_html=True)
    explicit = allied.get("normative_references", [])
    records_by_node = {"primary": (primary, "Primary standard")}
    node_key_prefix = hashlib.sha1(identity.encode("utf-8")).hexdigest()[:10]
    selected_state_key = f"dependency_selected_{node_key_prefix}"
    if explicit:
        st.markdown("**Explicit normative references**")
        columns = st.columns(min(2, len(explicit)))
        for index, row in enumerate(explicit):
            node_key = f"ref:{row['is_number']}"
            records_by_node[node_key] = (row, "Normative reference stated in the primary record")
            with columns[index % len(columns)]:
                st.markdown("┊")
                if st.button(
                    f"{row['is_number']} · {row['title']}",
                    key=f"dep_{node_key_prefix}_{index}",
                    type="primary" if st.session_state.get(selected_state_key) == node_key else "secondary",
                    use_container_width=True,
                ):
                    st.session_state[selected_state_key] = node_key
    else:
        st.caption("No explicit normative reference was found in the available record.")

    for label, key in (("Test method candidates", "test_methods"), ("Safety candidates", "safety_standards"), ("Installation candidates", "installation_standards"), ("Related product candidates", "related_products")):
        rows = allied.get(key, [])
        if rows:
            with st.expander(f"{label} · {len(rows)} · candidate links"):
                columns = st.columns(min(2, len(rows[:5])))
                for index, row in enumerate(rows[:5]):
                    node_key = f"candidate:{key}:{row['is_number']}"
                    records_by_node[node_key] = (row, f"Unverified {label.lower()} candidate")
                    with columns[index % len(columns)]:
                        if st.button(
                            f"{row['is_number']} · {row['title']}",
                            key=f"dep_{node_key_prefix}_{key}_{index}",
                            type="primary" if st.session_state.get(selected_state_key) == node_key else "secondary",
                            use_container_width=True,
                        ):
                            st.session_state[selected_state_key] = node_key

    selected_node = st.session_state.get(selected_state_key, "primary")
    selected = records_by_node.get(selected_node, records_by_node["primary"])
    row, relationship = selected
    st.markdown("**Selected node details**")
    st.markdown(f"#### {row['is_number']} — {row['title']}")
    st.caption(relationship)
    detail_cols = st.columns(2)
    detail_cols[0].write(f"Domain: {row.get('domain') or 'Not identified'}")
    detail_cols[1].write(f"Date field in prototype record: {row.get('publication_date') or 'Not identified'}")
    st.write(row.get("abstract") or "No description is available in this record.")
    st.caption("The bundled catalogue contains generated demo entries and dates. Verify this record against the official BIS catalogue.")


def _render_recommendations(result, query):
    st.markdown('<div id="recommendation-results"></div>', unsafe_allow_html=True)
    st.caption(f"Review ready · {result['latency_ms']} ms · Language: {result['detected_language']}")
    translated_query = result.get("translated_query") or result.get("query_translated")
    if translated_query:
        st.caption(f"English translation used for search: {translated_query}")
    if result.get("translation_warning"):
        st.warning(result["translation_warning"])
    recommendations = result.get("recommendations", [])
    if not recommendations:
        st.info("No close standards were found. Add product, material, use, or performance details and try again.")
        return

    audit_query = result.get("translated_query") or result.get("query") or query
    missing_gaps = _review_gaps(audit_query)
    audit_issues = []
    selected_standards = []

    def render_details(rec, identity, checks, *, add_audit_issue=True):
        review_tab, dependency_tab, evidence_tab = st.tabs(["Review", "Dependencies", "Evidence"])
        with review_tab:
            with st.expander("Why this standard may fit"):
                if checks:
                    for label, matched, terms in checks:
                        st.write(f"{'✓' if matched else '⚠'} {label} · {terms}" if matched else f"⚠ {label} mentioned ({terms}); confirm it is covered by the standard.")
                else:
                    st.write("The tender text has few explicit product-context details. Review the scope and source evidence before selecting.")
                st.caption("Context fit is a screening aid from tender text and record fields, not a legal applicability determination.")
            if add_audit_issue and st.checkbox("Select this standard", key=f"selected_standard_{identity}"):
                selected_standards.append(identity)
            with st.expander("Certification & regulatory check"):
                cert = rec.get("certification", rec.get("certification_info", {}))
                st.write(f"BIS certification record: {cert.get('bis_certification') or 'Not identified in available record'}")
                st.write(f"CRS: {'Mentioned in record' if cert.get('crs_applicable') else 'Not identified in available record'}")
                st.write(f"Hallmarking: {'Mentioned in record' if cert.get('hallmarking') else 'Not identified in available record'}")
                st.info("QCO status is not established by the retrieved record. Verify current regulatory requirements before finalizing a tender.")
                if cert.get("certification_portal_link"):
                    st.link_button("Check BIS certification information", cert["certification_portal_link"])
                if add_audit_issue:
                    audit_issues.append(("Certification verification", identity, "Confirm the current certification and QCO position with an authoritative source."))
        with dependency_tab:
            _render_dependency_map(rec)
        with evidence_tab:
            evidence = rec.get("evidence", [])
            if evidence:
                for item in evidence:
                    st.write(item.get("relevant_text", ""))
                    location = " · ".join(part for part in (item.get("source_document"), f"Page {item['page']}" if item.get("page") else None) if part)
                    if location:
                        st.caption(location)
            else:
                st.caption("No document-page evidence is attached to this result yet. Review the standard record directly.")

    for rank, rec in enumerate(recommendations[:1], start=1):
        standard = rec["standard"]
        identity = standard["is_number"] + (f" ({standard['part']})" if standard.get("part") else "")
        checks = _context_checks(audit_query, standard)
        product_match = next((matched for label, matched, _ in checks if label == "Product category"), False)
        matched_count = sum(matched for _, matched, _ in checks)
        fit = "High" if product_match and matched_count >= 2 else "Moderate" if product_match else "Review needed"
        title = f"{identity} — {standard['title']}"
        if rank == 1:
            with st.container(border=True):
                st.caption("TOP RECOMMENDATION")
                st.markdown(f"#### {title}")
                st.caption(f"Context fit: **{fit}** · {rec.get('why_matched', 'Retrieved from the available standards index.')}")
                st.write(standard.get("abstract") or "The available standards record has no description.")
                render_details(rec, identity, checks)

    if len(recommendations) > 1:
        with st.expander(f"Other recommended standards · {len(recommendations) - 1}"):
            for rank, rec in enumerate(recommendations[1:], start=2):
                standard = rec["standard"]
                identity = standard["is_number"] + (f" ({standard['part']})" if standard.get("part") else "")
                checks = _context_checks(audit_query, standard)
                product_match = next((matched for label, matched, _ in checks if label == "Product category"), False)
                fit = "Strong context match" if product_match and sum(matched for _, matched, _ in checks) >= 2 else "Context match" if product_match else "Review applicability"
                st.markdown(f"**{rank}. {identity} — {standard['title']}**")
                st.caption(f"{fit} · {rec.get('why_matched', 'Retrieved from the available standards index.')}")
                st.write(standard.get("abstract") or "The available standards record has no description.")
                if st.checkbox("Select this standard", key=f"selected_standard_{identity}"):
                    selected_standards.append(identity)
                if st.button("View details", key=f"open_secondary_details_{identity}"):
                    st.session_state["selected_secondary_standard"] = identity
                audit_issues.append(("Certification verification", identity, "Confirm the current certification and QCO position with an authoritative source."))

    selected_secondary_identity = st.session_state.get("selected_secondary_standard")
    selected_secondary = next(
        (
            rec for rec in recommendations[1:]
            if selected_secondary_identity
            == rec["standard"]["is_number"] + (f" ({rec['standard']['part']})" if rec["standard"].get("part") else "")
        ),
        None,
    )
    if selected_secondary:
        standard = selected_secondary["standard"]
        identity = standard["is_number"] + (f" ({standard['part']})" if standard.get("part") else "")
        checks = _context_checks(audit_query, standard)
        with st.container(border=True):
            detail_col, close_col = st.columns([5, 1])
            detail_col.markdown(f"#### Standard details · {identity}")
            if close_col.button("Close details", key="close_secondary_details"):
                st.session_state.pop("selected_secondary_standard", None)
                st.rerun()
            detail_col.write(standard["title"])
            render_details(selected_secondary, identity, checks, add_audit_issue=False)

    if selected_standards:
        st.caption("Selected standards: " + " · ".join(selected_standards))

    context = _context_summary(audit_query)
    detected = sum(bool(value) for value in context.values())
    with st.expander(f"Requirement understanding · {detected} of 5 details detected"):
        st.write(" · ".join(f"{label}: {value.title() if value else 'Not explicit'}" for label, value in context.items()))
        st.caption("Detected from tender text; use as a screening aid only.")

    for category in missing_gaps:
        audit_issues.append((f"{category} review", "Tender text", f"No explicit {category.lower()} detail was detected in the submitted tender text."))
    if missing_gaps:
        with st.expander(f"Specification gap review · {len(missing_gaps)} prompts"):
            st.caption("Prompts reflect text not detected in the tender; they are not findings that a standard requires these items.")
            for category in missing_gaps:
                st.markdown(f"**{category}**")
                st.write(f"No explicit {category.lower()} terms were detected. Confirm whether this topic applies, then compare the tender with the selected standard's scope and source requirements.")
                relation_key = "safety_standards" if category == "Safety" else "test_methods" if category in {"Testing", "Performance"} else "related_products"
                candidates = recommendations[0].get("allied_standards", {}).get(relation_key, [])
                if candidates:
                    st.markdown("**Database candidates to review**")
                    for row in candidates[:3]:
                        st.write(f"{row['is_number']} — {row['title']}")
                    st.caption("Candidate relevance has not been verified.")

    verification_items = [item for item in audit_issues if "Certification" in item[0]]
    potential_gaps = [item for item in audit_issues if item not in verification_items]
    with st.expander(f"Tender Risk & Gap Audit · {len(audit_issues)} review items"):
        st.caption("Decision support from tender wording and prototype records. No severity or standards requirement is inferred without authoritative evidence.")
        st.markdown("#### Critical")
        st.caption("No critical finding can be confirmed from this screening pass.")
        st.markdown("#### Missing requirements")
        st.caption("No standards-backed missing requirement was established. Compare the tender with the official standard text.")
        if potential_gaps:
            st.markdown("#### Potential gaps · detail not explicit")
            for index, (title, subject, detail) in enumerate(potential_gaps, start=1):
                with st.container(border=True):
                    label_col, status_col = st.columns([4, 1])
                    label_col.markdown(f"**{title}**")
                    label_col.caption(subject)
                    status_col.caption("Review")
                    with st.popover("View details"):
                        st.write(detail)
                        st.caption("Confirm whether this topic applies; the prompt is not an authoritative requirement.")
        if verification_items:
            st.markdown("#### Verification required")
            for title, subject, detail in verification_items:
                with st.container(border=True):
                    label_col, status_col = st.columns([4, 1])
                    label_col.markdown(f"**{title}**")
                    label_col.caption(subject)
                    status_col.caption("Verify")
                    with st.popover("View details"):
                        st.write(detail)
                        st.caption("Check the current official BIS catalogue and regulatory sources before procurement.")

st.set_page_config(
    page_title="BIS Standards Recommendation | PS-108",
    page_icon="📋",
    layout="wide",
)

st.markdown(
    """
    <style>
    :root { color-scheme: light; }
    .stApp { background: #f3f6f8; color: #152b3b; }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1220px; padding: .9rem 2rem 2rem; }
    h1, h2, h3 { color: #16354a; letter-spacing: -0.025em; }
    h1 { font-weight: 700; }
    p, li, label, [data-testid="stMarkdownContainer"] { color: #203847; }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: #455a69 !important; }
    input::placeholder, textarea::placeholder { color: #536777 !important; opacity: 1 !important; }
    [data-testid="stTabs"] [role="tablist"] { gap: .5rem; border-bottom: 1px solid #dce4e9; }
    [data-testid="stTabs"] button[role="tab"] { color: #4d6473; font-weight: 600; }
    [data-testid="stTabs"] button[aria-selected="true"] { color: #075b65; }
    div[data-testid="stRadio"] div[role="radiogroup"] { gap: .35rem; border-bottom: 1px solid #dce4e9; padding-bottom: .35rem; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] { background: #fff; border: 1px solid #dce5ea; border-radius: 8px; padding: .35rem .8rem; }
    div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child { display: none; }
    div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background: #e5f1ef; border-color: #075b65; color: #075b65; font-weight: 700; }
    [data-testid="stExpander"] { background: #fff; border: 1.5px solid #afc0c9; border-radius: 10px; margin: .3rem 0; }
    [data-testid="stMetric"] { background: #fff; border: 1px solid #dce5ea; border-radius: 9px; padding: .35rem .65rem; }
    [data-testid="stMetricLabel"] { font-size: .78rem; }
    [data-testid="stMetricValue"] { font-size: 1.15rem; }
    [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"] { margin-bottom: .15rem; }
    div.stButton > button[kind="primary"] { background: #075b65; border-color: #075b65; }
    div.st-key-analyze_tender_submit button[kind="primary"], div.st-key-admin_sign_in button[kind="primary"] { background: #0095f6 !important; border-color: #0095f6 !important; color: #ffffff !important; opacity: 1 !important; }
    div.st-key-analyze_tender_submit button[kind="primary"] p, div.st-key-admin_sign_in button[kind="primary"] p { color: #ffffff !important; }
    div.st-key-admin_analyze_pdf button { background: #0095f6 !important; border-color: #0095f6 !important; color: #ffffff !important; }
    div.st-key-admin_analyze_pdf button p { color: #ffffff !important; }
    div.st-key-detailed_bis_pdf [data-testid="stFileUploader"] button { background: #008080 !important; border-color: #008080 !important; color: #ffffff !important; }
    div.st-key-detailed_bis_pdf [data-testid="stFileUploader"] button p { color: #ffffff !important; }
    div.st-key-tender_upload [data-testid="stFileUploader"] button { background: #008080 !important; border-color: #008080 !important; color: #ffffff !important; }
    div.st-key-tender_upload [data-testid="stFileUploader"] button p { color: #ffffff !important; }
    div.st-key-admin_logout button { background: #dc2626 !important; border-color: #dc2626 !important; color: #ffffff !important; }
    div.st-key-admin_logout button p { color: #ffffff !important; }
    div.stButton > button { border-radius: 8px; font-weight: 600; }
    .product-header { display:flex; align-items:center; gap:.75rem; padding:.7rem 1rem; margin-bottom:.55rem; background:#12364b; color:#fff; border-radius:11px; }
    .product-mark { display:flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:8px; background:#d8eeea; color:#075b65; font-weight:800; font-size:1rem; }
    .product-name { font-size:1rem; font-weight:700; letter-spacing:.01em; }
    .product-subtitle { color:#c9d8df; font-size:.86rem; margin-top:.15rem; }
    @media (max-width: 700px) { .block-container { padding: .6rem .75rem 2rem; } .product-header { padding: .6rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="product-header"><div class="product-mark">IS</div><div><div class="product-name">BIS Procurement Standards</div><div class="product-subtitle">Standards discovery and specification support · PS-108</div></div></div>',
    unsafe_allow_html=True,
)

def _record_page_navigation():
    current = st.session_state.get("page_navigation", "Recommend Standards")
    previous = st.session_state.get("previous_page_navigation", current)
    if current != previous:
        st.session_state.setdefault("page_navigation_history", []).append(previous)
        st.session_state["previous_page_navigation"] = current


if "page_navigation" not in st.session_state:
    st.session_state["page_navigation"] = "Recommend Standards"
    st.session_state["previous_page_navigation"] = "Recommend Standards"

if st.session_state.get("page_navigation_history"):
    if st.button("← Back", key="page_navigation_back"):
        history = st.session_state["page_navigation_history"]
        st.session_state["page_navigation"] = history.pop()
        st.session_state["previous_page_navigation"] = st.session_state["page_navigation"]
        st.rerun()

current_page = st.radio(
    "Main navigation",
    ["Recommend Standards", "Admin"],
    horizontal=True,
    label_visibility="collapsed",
    key="page_navigation",
    on_change=_record_page_navigation,
)

if current_page == "Recommend Standards":
    st.subheader("Know Accurate Standards and Reviews")

    scroll_to_results = st.session_state.pop("scroll_to_recommendation_results", False)
    stored_result = st.session_state.get("recommendation_result")
    if stored_result:
        if st.button("← Back to tender input", key="back_to_tender_input"):
            st.session_state.pop("recommendation_result", None)
            st.session_state.pop("recommendation_query", None)
            st.session_state.pop("selected_secondary_standard", None)
            st.rerun()
        _render_recommendations(stored_result, st.session_state.get("recommendation_query", ""))

    input_section = st.expander("Update tender input", expanded=False) if stored_result else st.container(border=True)
    with input_section:
        col1, col2 = st.columns([2, 1])
        with col1:
            query = st.text_area(
                "**Product description or technical specification**",
                placeholder="Example: 5000 litre stainless steel potable water storage tank for outdoor installation",
                height=84,
                help="Include product, material, intended use, capacity or dimensions, and operating environment when known.",
            )
        with col2:
            language_number = st.selectbox(
                "Input language",
                options=list(range(12)),
                format_func=lambda number: "Auto detect" if number == 0 else {
                    1: "English", 2: "Hindi", 3: "Tamil", 4: "Telugu", 5: "Bengali", 6: "Marathi",
                    7: "Gujarati", 8: "Kannada", 9: "Malayalam", 10: "Odia", 11: "Punjabi",
                }[number],
                key="input_language_number",
            )
        uploaded = st.file_uploader("Or upload a tender (PDF/DOCX)", type=["pdf", "docx"], key="tender_upload")
        if uploaded is not None:
            st.caption(f"Selected: {uploaded.name} · {uploaded.size / 1024:.0f} KB · select the remove icon to replace it.")
        analyze_clicked = st.button("Analyze tender", type="primary", key="analyze_tender_submit")

        if analyze_clicked:
            if uploaded is None and len(query.strip()) < 2:
                st.warning("Enter a product description or upload a tender before analyzing.")
                st.stop()
            with st.spinner("Analyzing procurement requirements and finding relevant Indian Standards…"):
                try:
                    if uploaded is not None:
                        files = {"file": (uploaded.name, uploaded.getvalue())}
                        data = {"top_k": "5"}
                        if language_number != 0:
                            data["source_language"] = LANGUAGE_CODES[int(language_number)]
                        resp = requests.post(
                            f"{API_BASE}/api/recommend-standards/upload",
                            files=files,
                            data=data,
                            timeout=120,
                        )
                    else:
                        payload = {"query": query, "top_k": 5}
                        if language_number != 0:
                            payload["source_language"] = LANGUAGE_CODES[int(language_number)]
                        resp = requests.post(
                            f"{API_BASE}/api/recommend-standards",
                            json=payload,
                            timeout=120,
                        )
                    resp.raise_for_status()
                    result = resp.json()
                    st.session_state["recommendation_result"] = result
                    st.session_state["recommendation_query"] = result.get("query") or query or (uploaded.name if uploaded else "")
                    st.session_state.pop("selected_secondary_standard", None)
                    st.session_state["scroll_to_recommendation_results"] = True
                    st.rerun()
                except requests.Timeout:
                    st.error("The search took too long. Try a shorter requirement or retry in a moment.")
                except requests.HTTPError as exc:
                    detail = None
                    if exc.response is not None:
                        try:
                            detail = exc.response.json().get("detail")
                        except ValueError:
                            detail = None
                    st.error(detail or "The search request could not be completed. Check the input and retry.")
                except requests.RequestException:
                    st.error("The recommendation service is unavailable. Check that the backend is running.")

    if scroll_to_results:
        components.html(
            """<script>
            const parentWindow = window.parent;
            parentWindow.requestAnimationFrame(() => parentWindow.requestAnimationFrame(() => {
              const target = parentWindow.document.getElementById('recommendation-results');
              if (target) target.scrollIntoView({behavior: 'instant', block: 'start'});
              else {
                const main = parentWindow.document.querySelector('[data-testid="stAppViewContainer"]');
                if (main) main.scrollTo({top: 0, behavior: 'instant'});
              }
            }));
            </script>""",
            height=0,
        )

if current_page == "Admin":
    admin_token = st.session_state.get("admin_token")
    if not admin_token:
        st.subheader("Admin login")
        username = st.text_input("Username", placeholder="Enter username", key="admin_username")
        password = st.text_input("Password", type="password", key="admin_password")
        submitted = st.button("Sign in", type="primary", key="admin_sign_in")
        if submitted:
            try:
                response = requests.post(
                    f"{API_BASE}/api/admin/login",
                    json={"username": username, "password": password},
                    timeout=15,
                )
                if response.ok:
                    st.session_state["admin_token"] = response.json()["access_token"]
                    st.rerun()
                detail = response.json().get("detail", "Login failed.")
                st.error(detail)
            except requests.RequestException:
                st.error("Could not reach the API. Check that the backend is running.")
    else:
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        heading_col, logout_col = st.columns([5, 1], vertical_alignment="center")
        if logout_col.button("Log out", key="admin_logout"):
            try:
                requests.post(f"{API_BASE}/api/admin/logout", headers=admin_headers, timeout=10)
            except requests.RequestException:
                pass
            st.session_state.pop("admin_token", None)
            reset_for_document_change(st.session_state, None)
            st.rerun()

        heading_col.markdown("### Add/Update New Standards")
        detailed_pdf = st.file_uploader(
            "Detailed BIS Standards Document (PDF)",
            type=["pdf"],
            key="detailed_bis_pdf",
        )
        detailed_pdf_content = detailed_pdf.getvalue() if detailed_pdf is not None else None
        document_hash = (
            hashlib.sha256(detailed_pdf_content).hexdigest()
            if detailed_pdf_content is not None
            else None
        )
        reset_for_document_change(st.session_state, document_hash)
        if st.button("Analyze PDF", disabled=detailed_pdf is None, key="admin_analyze_pdf"):
            try:
                response = requests.post(
                    f"{API_BASE}/api/admin/documents/analyze",
                    files={"file": (detailed_pdf.name, detailed_pdf_content, "application/pdf")},
                    headers=admin_headers,
                    timeout=180,
                )
                if response.ok:
                    st.session_state["pdf_analysis"] = response.json()
                    st.session_state.pop("pdf_extractions", None)
                    st.session_state.pop("knowledge_apply_result", None)
                else:
                    st.error(response.json().get("detail", "The PDF could not be analyzed."))
            except requests.RequestException:
                st.error("The document analysis service is unavailable. Please retry.")

        analysis = st.session_state.get("pdf_analysis")
        if analysis:
            summary_cols = st.columns(3)
            summary_cols[0].metric("Pages", analysis["page_count"])
            summary_cols[1].metric("Pages with text", analysis["pages_with_text"])
            summary_cols[2].metric("IS standards detected", analysis["standards_found"])
            if analysis.get("warnings"):
                for warning in analysis["warnings"]:
                    st.warning(warning)
            if analysis["standards"]:
                st.dataframe(
                    [
                        {
                            "IS number": item["is_number"],
                            "Title": item["title"] or "Title not detected",
                            "Pages": ", ".join(str(page) for page in item["page_numbers"]),
                        }
                        for item in analysis["standards"]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                standard_numbers = [item["is_number"] for item in analysis["standards"]]
                if st.button("Select all detected standards", key="select_all_extraction_standards"):
                    st.session_state["selected_extraction_standards"] = standard_numbers
                selected_numbers = st.multiselect(
                    "Select standards for structured extraction (processed in batches of 20)",
                    options=standard_numbers,
                    key="selected_extraction_standards",
                )
                if st.button("Extract selected fields with AI", disabled=not selected_numbers or detailed_pdf is None):
                    batches = list(_batches(selected_numbers, 20))
                    analysis_id = analysis.get("analysis_id")
                    extraction_result = {
                        "source_document": detailed_pdf.name,
                        "extracted": [],
                        "failed": [],
                    }
                    progress = st.progress(0, text="Preparing extraction batches…")
                    status = st.empty()
                    st.session_state.pop("knowledge_apply_result", None)
                    st.session_state["pdf_extractions"] = extraction_result
                    extraction_complete = True
                    for batch_index, batch in enumerate(batches, start=1):
                        status.caption(
                            f"Extracting batch {batch_index} of {len(batches)} · "
                            f"{len(extraction_result['extracted'])} extracted · "
                            f"{len(extraction_result['failed'])} failed"
                        )
                        try:
                            batch_data = {"is_numbers": ",".join(batch)}
                            if analysis_id:
                                batch_data["analysis_id"] = analysis_id
                            response = requests.post(
                                f"{API_BASE}/api/admin/documents/extract",
                                data=batch_data,
                                headers=admin_headers,
                                timeout=900,
                            )
                            if response.status_code == 410:
                                response = requests.post(
                                    f"{API_BASE}/api/admin/documents/extract",
                                    files={"file": (detailed_pdf.name, detailed_pdf_content, "application/pdf")},
                                    data=batch_data,
                                    headers=admin_headers,
                                    timeout=900,
                                )
                            if not response.ok:
                                extraction_complete = False
                                st.error(response.json().get("detail", "Structured extraction failed."))
                                break
                            batch_result = response.json()
                            analysis_id = batch_result.get("analysis_id", analysis_id)
                            if analysis_id:
                                st.session_state["pdf_analysis"]["analysis_id"] = analysis_id
                            extraction_result["extracted"].extend(batch_result.get("extracted", []))
                            extraction_result["failed"].extend(batch_result.get("failed", []))
                            st.session_state["pdf_extractions"] = extraction_result
                            progress.progress(
                                batch_index / len(batches),
                                text=f"Completed extraction batch {batch_index} of {len(batches)}",
                            )
                        except requests.RequestException:
                            extraction_complete = False
                            st.error("The extraction service became unavailable. Completed batches are retained for review.")
                            break
                    status.caption(
                        f"{'Extraction finished' if extraction_complete else 'Extraction stopped; completed batches retained'} · "
                        f"{len(extraction_result['extracted'])} extracted · "
                        f"{len(extraction_result['failed'])} failed"
                    )

            extraction_result = st.session_state.get("pdf_extractions")
            if extraction_result:
                st.markdown("#### Extraction review — no database changes have been applied")
                st.caption(f"Extracted {len(extraction_result['extracted'])} standard(s); {len(extraction_result['failed'])} failed.")
                extracted_records = extraction_result["extracted"]
                record_numbers = [record["extraction"]["is_number"] for record in extracted_records]
                if extracted_records:
                    st.dataframe(
                        [
                            {
                                "IS number": record["extraction"]["is_number"],
                                "Title": record["extraction"].get("title") or "Title not found",
                                "Pages": ", ".join(map(str, record.get("source_pages", []))),
                                "Description": record["extraction"].get("description") or "",
                            }
                            for record in extracted_records
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
                    records_by_number = {
                        record["extraction"]["is_number"]: record for record in extracted_records
                    }
                    inspect_number = st.selectbox(
                        "Inspect one extracted standard",
                        options=record_numbers,
                        key="inspect_extracted_standard",
                    )
                    inspected_record = records_by_number[inspect_number]
                    extracted = inspected_record["extraction"]
                    st.markdown(f"**{extracted['is_number']} — {extracted.get('title') or 'Title not found'}**")
                    st.caption(
                        f"Source: {inspected_record['source_document']} · "
                        f"Pages {', '.join(map(str, inspected_record['source_pages'])) or 'not detected'}"
                    )
                    st.write(extracted.get("description") or "No description found in source text.")
                    for field in (
                        "products", "applications", "materials", "properties", "requirements",
                        "testing", "normative_references", "related_terms",
                    ):
                        values = extracted.get(field, [])
                        if values:
                            st.markdown(f"**{field.replace('_', ' ').title()}**")
                            st.write(" · ".join(values))
                    st.markdown("**Source excerpt**")
                    st.write(inspected_record.get("source_excerpt") or "No source excerpt available.")
                for failure in extraction_result["failed"]:
                    st.warning(f"{failure['is_number']}: {failure['reason']}")

                if extracted_records:
                    apply_numbers = st.multiselect(
                        "Review and select records to apply",
                        options=record_numbers,
                        default=record_numbers,
                        key="apply_extraction_standards",
                    )
                    if st.button("Apply selected reviewed records", disabled=not apply_numbers or detailed_pdf is None):
                        records = [records_by_number[number] for number in apply_numbers]
                        analysis_id = st.session_state.get("pdf_analysis", {}).get("analysis_id")
                        batches = list(_batches(records, 20))
                        apply_result = {
                            "source_document_id": None,
                            "processed": 0,
                            "new": [],
                            "updated": [],
                            "unchanged": [],
                            "conflicts": [],
                            "standard_ids": {},
                            "indexes_updated": False,
                            "apply_incomplete": False,
                        }
                        progress = st.progress(0, text="Preparing knowledge base batches…")
                        status = st.empty()
                        st.session_state["knowledge_apply_result"] = apply_result
                        for batch_index, batch in enumerate(batches, start=1):
                            status.caption(
                                f"Processed: {apply_result['processed']} / {len(records)} · "
                                f"New: {len(apply_result['new'])} · Updated: {len(apply_result['updated'])} · "
                                f"Conflicts: {len(apply_result['conflicts'])} · Batch {batch_index} of {len(batches)}"
                            )
                            try:
                                batch_data = {
                                    "records_json": json.dumps(batch, ensure_ascii=False),
                                    "rebuild_search_indexes": "true" if batch_index == len(batches) else "false",
                                }
                                if analysis_id:
                                    batch_data["analysis_id"] = analysis_id
                                response = requests.post(
                                    f"{API_BASE}/api/admin/documents/apply",
                                    data=batch_data,
                                    headers=admin_headers,
                                    timeout=900,
                                )
                                if response.status_code == 410:
                                    response = requests.post(
                                        f"{API_BASE}/api/admin/documents/apply",
                                        files={"file": (detailed_pdf.name, detailed_pdf_content, "application/pdf")},
                                        data=batch_data,
                                        headers=admin_headers,
                                        timeout=900,
                                    )
                                if not response.ok:
                                    apply_result["apply_incomplete"] = True
                                    apply_result["apply_error"] = response.json().get(
                                        "detail", "Could not apply the reviewed records."
                                    )
                                    st.error(apply_result["apply_error"])
                                    break
                                batch_result = response.json()
                                analysis_id = batch_result.get("analysis_id", analysis_id)
                                if analysis_id:
                                    st.session_state["pdf_analysis"]["analysis_id"] = analysis_id
                                apply_result["source_document_id"] = batch_result.get("source_document_id")
                                apply_result["processed"] += batch_result.get("processed", 0)
                                for key in ("new", "updated", "unchanged", "conflicts"):
                                    apply_result[key].extend(batch_result.get(key, []))
                                apply_result["standard_ids"].update(batch_result.get("standard_ids", {}))
                                apply_result["indexes_updated"] = batch_result.get("indexes_updated", False)
                                st.session_state["knowledge_apply_result"] = apply_result
                                progress.progress(
                                    batch_index / len(batches),
                                    text=f"Applied batch {batch_index} of {len(batches)}",
                                )
                                status.caption(
                                    f"Processed: {apply_result['processed']} / {len(records)} · "
                                    f"New: {len(apply_result['new'])} · Updated: {len(apply_result['updated'])} · "
                                    f"Conflicts: {len(apply_result['conflicts'])} · Batch {batch_index} of {len(batches)}"
                                )
                            except requests.RequestException:
                                apply_result["apply_incomplete"] = True
                                apply_result["apply_error"] = "The knowledge base service became unavailable."
                                st.error("The knowledge base service became unavailable. Earlier batches were saved; indexes may need rebuilding.")
                                break
                        st.session_state["knowledge_apply_result"] = apply_result
                        status.caption(f"Applied {apply_result['processed']} reviewed record(s)")

                    apply_result = st.session_state.get("knowledge_apply_result")
                    if apply_result:
                        st.markdown("#### Knowledge base update")
                        status_cols = st.columns(3)
                        status_cols[0].metric("New", len(apply_result["new"]))
                        status_cols[1].metric("Updated", len(apply_result["updated"]))
                        status_cols[2].metric("Unchanged", len(apply_result["unchanged"]))
                        if apply_result["new"]:
                            st.write("**New standards:** " + ", ".join(apply_result["new"]))
                        if apply_result["updated"]:
                            st.write("**Updated standards:** " + ", ".join(apply_result["updated"]))
                        if apply_result.get("apply_incomplete"):
                            st.warning(
                                f"Only {apply_result['processed']} reviewed record(s) were saved. "
                                "Search indexes may be stale; resolve the issue and use the admin rebuild action."
                            )
                        elif not apply_result["indexes_updated"]:
                            st.warning("Knowledge records were saved, but search indexes did not rebuild. Use the admin rebuild action and retry search.")
                        else:
                            st.success("Knowledge records and search indexes updated.")

        if st.button("Merge bundled standards without replacing ingested knowledge"):
            r = requests.post(
                f"{API_BASE}/api/admin/seed", params={"force": True}, headers=admin_headers, timeout=120
            )
            if r.ok:
                st.success(
                    f"Merge complete. {r.json().get('standards_loaded', 0)} standards are available; "
                    "existing standards, PDF knowledge, and evidence were preserved."
                )
            else:
                st.error(r.json().get("detail", "Could not seed standards."))
        if st.button("Rebuild search indexes (BM25 + FAISS)"):
            r = requests.post(f"{API_BASE}/api/admin/rebuild-index", headers=admin_headers, timeout=120)
            st.success("Search indexes rebuilt.") if r.ok else st.error(r.json().get("detail", "Index rebuild failed."))

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
                r = requests.post(
                    f"{API_BASE}/api/standards", json=payload, headers=admin_headers, timeout=60
                )
                if r.ok:
                    st.success(f"Created {r.json()['is_number']}.")
                else:
                    st.error(r.json().get("detail", "Could not create standard."))

        try:
            count = requests.get(f"{API_BASE}/api/standards/count", timeout=10).json()
            st.metric("Standards in database", count.get("count", 0))
        except requests.RequestException:
            st.warning("API not reachable.")
