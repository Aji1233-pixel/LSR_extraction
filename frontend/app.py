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
# HELPER FUNCTIONS
# ============================================================

def format_field_value(val: str | list | None, default_text: str) -> str:
    """Formats raw values into readable string representations."""
    if val in (None, "", [], {}):
        return default_text
    if isinstance(val, list):
        return ", ".join(map(str, val))
    return str(val)


def prepare_documents(documents: list) -> list[dict]:
    """Formats document dictionaries for tabular display."""
    return [
        {
            "Document Name": doc.get("document_name") or "N/A",
            "Document Number": doc.get("document_number") or "N/A",
            "Document Date": doc.get("document_date") or "N/A",
            "Document Type": doc.get("document_copy_type") or "N/A",
            "Additional Details": doc.get("additional_details") or "N/A",
        }
        for doc in documents
        if isinstance(doc, dict)
    ]

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("📄 LSR Intelligence")
    st.caption("Document Extraction System")
    st.divider()

    page = st.radio(
        "Navigation",
        ["Document Extraction", "About"],
        label_visibility="collapsed",
    )
    st.divider()

    st.subheader("Pipeline")
    st.text(
        "📄 Document\n"
        "  ↓\n"
        "🔍 DocTR OCR\n"
        "  ↓\n"
        "🧠 Qwen 3B\n"
        "  ↓\n"
        "🌐 Translation\n"
        "  ↓\n"
        "📑 Document Extraction\n"
        "  ↓\n"
        "📊 Results"
    )
    st.divider()
    st.caption("LSR Document Intelligence v1.0")

# ============================================================
# MAIN CONTENT: DOCUMENT EXTRACTION
# ============================================================

if page == "Document Extraction":
    st.title("Extract LSR Information Automatically")
    st.caption("Upload a legal property document to extract key details using OCR and AI.")
    st.divider()

    st.subheader("Upload Document")
    uploaded_file = st.file_uploader(
        "Supported formats: PDF, JPG, JPEG, PNG, TIFF",
        type=["pdf", "jpg", "jpeg", "png", "tif", "tiff"],
    )

    if uploaded_file:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        extension = Path(uploaded_file.name).suffix.upper().replace(".", "")

        with st.container(border=True):
            st.write(f"**Selected File:** {uploaded_file.name}")
            st.caption(f"Format: {extension} | Size: {file_size_kb:.1f} KB")

        if st.button("✨ Extract Information", type="primary", use_container_width=True):
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
                    st.error("Unable to connect to backend server. Please verify FastAPI is running.")
                except requests.exceptions.Timeout:
                    st.error("Processing timed out. Please try again.")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

    # Display Results
    if "extraction_result" in st.session_state:
        result = st.session_state["extraction_result"]
        fields = result.get("extracted_fields", {})
        translated_fields = result.get("translated_fields", {})
        processing_time = result.get("processing_time_seconds")

        st.divider()
        st.subheader("📊 Extracted Information")

        # Top Metrics Section
        found_count = sum(1 for val in fields.values() if val not in (None, "", [], {}))
        time_display = f"{processing_time:.1f}s" if processing_time else "N/A"

        m1, m2, m3 = st.columns(3)
        m1.metric("Fields Extracted", found_count)
        m2.metric("Required Fields", len(fields))
        m3.metric("Processing Time", time_display)
        st.divider()

        # Basic Details Section
        st.subheader("📋 Basic Details")
        basic_fields = [
            ("lsr_date", "LSR Date"),
            ("company_name", "Company Name"),
            ("application_number", "Application Number"),
            ("applicant_name", "Applicant Name"),
            ("co_applicant_name", "Co-Applicant Name"),
            ("property_owner", "Property Owner"),
        ]

        for field_key, label in basic_fields:
            eng_text = format_field_value(fields.get(field_key), "Not found")
            tam_text = format_field_value(translated_fields.get(field_key), "கிடைக்கவில்லை")

            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.caption(f"🇬🇧 {label}")
                    st.write(f"**{eng_text}**")
            with col2:
                with st.container(border=True):
                    st.caption(f"🇮🇳 {label} (Tamil)")
                    st.write(f"**{tam_text}**")

        # Property Description Section
        st.divider()
        st.subheader("🏠 Property Description")
        prop_eng = fields.get("property_description")
        prop_tam = translated_fields.get("property_description")

        p_col1, p_col2 = st.columns(2)
        with p_col1:
            with st.container(border=True):
                st.caption("🇬🇧 English Description")
                st.write(prop_eng if prop_eng else "Property description not found.")
        with p_col2:
            with st.container(border=True):
                st.caption("🇮🇳 Tamil Description")
                st.write(prop_tam if prop_tam else "சொத்து விவரம் கிடைக்கவில்லை.")

        # Prior / Post Disbursal Tables
        st.divider()
        st.subheader("📋 Documents Prior to Disbursal")
        prior_docs = prepare_documents(result.get("documents_prior_to_disbursal", []))
        if prior_docs:
            st.dataframe(prior_docs, use_container_width=True, hide_index=True)
        else:
            st.info("No documents prior to disbursal found.")

        st.subheader("📋 Documents Post Disbursal")
        post_docs = prepare_documents(result.get("documents_post_disbursal", []))
        if post_docs:
            st.dataframe(post_docs, use_container_width=True, hide_index=True)
        else:
            st.info("No documents post disbursal found.")

        # Raw Data View
        with st.expander("🔍 View Raw Extraction Data"):
            st.json(result)

# ============================================================
# ABOUT PAGE
# ============================================================

else:
    st.title("About LSR Document Intelligence")
    st.write("An automated extraction pipeline designed to process legal property reports.")
    st.divider()

    col1, col2, col3 = st.columns(3)
    info_cards = [
        (col1, "### 🔍 DocTR", "OCR Engine", "Extracts raw optical text directly from uploaded files."),
        (col2, "### 🧠 Qwen 3B", "Language Model", "Parses unstructured text into target structured fields."),
        (col3, "### ⚡ FastAPI", "Backend Infrastructure", "Handles pipeline execution and translation services."),
    ]

    for col, title, sub, desc in info_cards:
        with col:
            with st.container(border=True):
                st.markdown(title)
                st.caption(sub)
                st.write(desc)

    st.divider()
    st.subheader("📌 Extracted Fields")
    st.markdown(
        """
- **LSR Date**
- **Company Name**
- **Applicant Name**
- **Co-Applicant Name**
- **Property Owner**
- **Application Number**
- **Property Description**
"""
    )