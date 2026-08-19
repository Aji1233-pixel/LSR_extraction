from pathlib import Path
import requests
import streamlit as st

# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://127.0.0.1:8000/api/extract"

st.set_page_config(
    page_title="LSR Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================

CUSTOM_CSS = """
<style>
/* ---------- Global ---------- */
.stApp {
    background: #f5f8fc;
}
.main .block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e5eaf0;
}
section[data-testid="stSidebar"] > div {
    padding-top: 2rem;
}
.sidebar-logo {
    text-align: center;
    padding: 10px 0 25px 0;
}
.sidebar-icon {
    width: 58px;
    height: 58px;
    border-radius: 16px;
    background: linear-gradient(135deg, #2563eb, #0ea5e9);
    color: white;
    font-size: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: auto;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.20);
}
.sidebar-title {
    font-size: 20px;
    font-weight: 700;
    color: #172033;
    margin-top: 12px;
}
.sidebar-subtitle {
    color: #7b8798;
    font-size: 12px;
    margin-top: 4px;
}

/* ---------- Hero ---------- */
.hero {
    background: linear-gradient(135deg, #eff6ff 0%, #ffffff 55%, #ecfeff 100%);
    border: 1px solid #dbeafe;
    border-radius: 24px;
    padding: 38px 42px;
    margin-bottom: 25px;
    box-shadow: 0 8px 30px rgba(15, 23, 42, 0.04);
}
.hero-badge {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 15px;
}
.hero-title {
    font-size: 38px;
    line-height: 1.15;
    font-weight: 800;
    color: #172033;
    margin: 0;
}
.hero-title span {
    color: #2563eb;
}
.hero-description {
    color: #64748b;
    font-size: 16px;
    line-height: 1.7;
    max-width: 760px;
    margin-top: 14px;
}

/* ---------- Typography & Sections ---------- */
.section-title {
    font-size: 22px;
    font-weight: 750;
    color: #172033;
    margin-top: 28px;
    margin-bottom: 5px;
}
.section-subtitle {
    color: #7b8798;
    font-size: 14px;
    margin-bottom: 18px;
}

/* ---------- Upload Area ---------- */
div[data-testid="stFileUploader"] {
    background: white;
    border: 2px dashed #bfdbfe;
    border-radius: 18px;
    padding: 10px;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #60a5fa;
    background: #fafdff;
}

/* ---------- Buttons ---------- */
.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 48px;
    border: none;
    background: linear-gradient(135deg, #2563eb, #0ea5e9);
    color: white;
    font-weight: 700;
    font-size: 15px;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.20);
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(37, 99, 235, 0.28);
}

/* ---------- Cards ---------- */
.file-card {
    background: white;
    border: 1px solid #e5eaf0;
    border-radius: 16px;
    padding: 18px;
    margin: 15px 0;
    display: flex;
    align-items: center;
    gap: 15px;
    box-shadow: 0 5px 18px rgba(15, 23, 42, 0.03);
}
.file-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: #eff6ff;
    color: #2563eb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 23px;
}
.file-name {
    font-weight: 700;
    color: #172033;
    font-size: 14px;
}
.file-info {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 3px;
}

.result-card {
    background: white;
    border: 1px solid #e5eaf0;
    border-radius: 16px;
    padding: 20px;
    min-height: 115px;
    box-shadow: 0 5px 18px rgba(15, 23, 42, 0.035);
    margin-bottom: 15px;
}
.result-label {
    color: #7b8798;
    font-size: 12px;
    font-weight: 650;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
.result-value {
    color: #172033;
    font-size: 16px;
    font-weight: 700;
    line-height: 1.5;
    word-break: break-word;
}
.result-value.empty {
    color: #94a3b8;
    font-weight: 500;
    font-style: italic;
}

.property-card {
    background: white;
    border: 1px solid #e5eaf0;
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 5px 18px rgba(15, 23, 42, 0.035);
    line-height: 1.8;
    color: #475569;
    font-size: 14px;
}

.metric-card {
    background: white;
    border: 1px solid #e5eaf0;
    border-radius: 15px;
    padding: 18px;
    text-align: center;
}
.metric-number {
    font-size: 25px;
    font-weight: 800;
    color: #2563eb;
}
.metric-label {
    color: #7b8798;
    font-size: 12px;
    margin-top: 4px;
}

.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    padding: 30px 0 10px 0;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """<div class="sidebar-logo">
            <div class="sidebar-icon">📄</div>
            <div class="sidebar-title">LSR Intelligence</div>
            <div class="sidebar-subtitle">Document Extraction System</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("🧭 Navigation")

    page = st.radio(
        "Navigation",
        ["Document Extraction", "About"],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown(
        """**Pipeline**\n\n"""
        """📄 Document → 🔍 DocTR OCR → 🧠 Qwen 3B → ✅ Validation → 📊 Results"""
    )

    st.divider()
    st.caption("LSR Document Intelligence v1.0")


# ============================================================
# MAIN CONTENT AREA
# ============================================================

if page == "Document Extraction":
    st.markdown(
        """<div class="hero">
            <div class="hero-badge">AI-POWERED DOCUMENT ANALYSIS</div>
            <div class="hero-title">Extract LSR information <span>automatically.</span></div>
            <div class="hero-description">
                Upload a legal property document and let our document intelligence pipeline
                extract important information automatically using OCR and a local language model.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # File Upload Header
    st.markdown('<div class="section-title">Upload Document</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Supported formats: PDF, JPG, JPEG, PNG, TIFF</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose your LSR document",
        type=["pdf", "jpg", "jpeg", "png", "tif", "tiff"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        extension = Path(uploaded_file.name).suffix.upper().replace(".", "")

        st.markdown(
            f"""<div class="file-card">
                <div class="file-icon">📄</div>
                <div>
                    <div class="file-name">{uploaded_file.name}</div>
                    <div class="file-info">{extension} &nbsp;•&nbsp; {file_size_kb:.1f} KB</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        if st.button("✨ Extract Information", use_container_width=True):
            with st.spinner("Analyzing document with DocTR and AI..."):
                try:
                    response = requests.post(
                        API_URL,
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        },
                        timeout=600,
                    )

                    if response.status_code == 200:
                        st.session_state["extraction_result"] = response.json()
                        st.success("Document processed successfully!")
                    else:
                        try:
                            error_message = response.json().get("detail", "Unknown server error.")
                        except Exception:
                            error_message = response.text
                        st.error(f"Extraction failed: {error_message}")

                except requests.exceptions.ConnectionError:
                    st.error("Unable to connect to the FastAPI server. Make sure the backend is running.")
                except requests.exceptions.Timeout:
                    st.error("The document processing took too long. Please try again.")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

    # Display Results
    if "extraction_result" in st.session_state:
        result = st.session_state["extraction_result"]
        fields = result.get("extracted_fields", {})
        processing_time = result.get("processing_time_seconds")

        st.markdown('<div class="section-title">Extracted Information</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Information identified from the uploaded document</div>', unsafe_allow_html=True)

        # Metrics
        metric1, metric2, metric3 = st.columns(3)

        found_count = sum(1 for value in fields.values() if value not in [None, "", [], {}])

        with metric1:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-number">{found_count}</div>
                    <div class="metric-label">Fields Extracted</div>
                </div>""",
                unsafe_allow_html=True,
            )

        with metric2:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-number">{len(fields)}</div>
                    <div class="metric-label">Required Fields</div>
                </div>""",
                unsafe_allow_html=True,
            )

        with metric3:
            time_display = f"{processing_time:.1f}s" if processing_time is not None else "N/A"
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-number">{time_display}</div>
                    <div class="metric-label">Processing Time</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Basic Information Section
        st.markdown("### 📋 Basic Information")

        basic_fields = [
            ("lsr_date", "LSR Date"),
            ("company_name", "Company Name"),
            ("application_number", "Application Number"),
            ("applicant_name", "Applicant Name"),
            ("co_applicant_name", "Co-Applicant Name"),
            ("property_owner", "Property Owner"),
        ]

        for row_start in range(0, len(basic_fields), 2):
            col1, col2 = st.columns(2)
            row_fields = basic_fields[row_start : row_start + 2]

            for index, (field_name, label) in enumerate(row_fields):
                value = fields.get(field_name)

                if isinstance(value, list):
                    value = ", ".join(str(item) for item in value)

                if value in [None, "", [], {}]:
                    display_value = "Not found"
                    value_class = "result-value empty"
                else:
                    display_value = str(value)
                    value_class = "result-value"

                card_html = f"""<div class="result-card">
                    <div class="result-label">{label}</div>
                    <div class="{value_class}">{display_value}</div>
                </div>"""

                if index == 0:
                    col1.markdown(card_html, unsafe_allow_html=True)
                else:
                    col2.markdown(card_html, unsafe_allow_html=True)

        # Property Description Section
        st.markdown("### 🏠 Property Description")
        property_description = fields.get("property_description")

        if property_description:
            st.markdown(
                f"""<div class="property-card">{property_description}</div>""",
                unsafe_allow_html=True,
            )
        else:
            st.info("Property description was not found.")

        # Raw JSON Section
        with st.expander("🔍 View Raw Extraction JSON"):
            st.json(fields)

        # Footer
        st.markdown(
            """<div class="footer">
                LSR Document Intelligence &nbsp;•&nbsp; DocTR + Ollama + Qwen
            </div>""",
            unsafe_allow_html=True,
        )

# ============================================================
# ABOUT PAGE
# ============================================================
else:
    st.markdown(
        """<div class="hero">
            <div class="hero-badge">ABOUT THE SYSTEM</div>
            <div class="hero-title">LSR Document <span>Intelligence</span></div>
            <div class="hero-description">
                An AI-powered document information extraction system designed to automatically
                identify important information from legal property reports.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔍 DocTR\nOptical Character Recognition extracts text from uploaded documents.")

    with col2:
        st.markdown("### 🧠 Qwen 3B\nA local language model identifies the predefined fields from the extracted text.")

    with col3:
        st.markdown("### ⚡ FastAPI\nThe backend coordinates document processing and returns structured data.")

    st.markdown("---")
    st.markdown("### 📌 Extracted Fields")
    st.write(
        """
        The system currently extracts:
        - LSR Date
        - Company Name
        - Applicant Name
        - Co-Applicant Name
        - Property Owner
        - Application Number
        - Property Description
        """
    )