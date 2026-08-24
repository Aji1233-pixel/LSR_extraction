from pathlib import Path
from io import BytesIO
import html
import textwrap

import requests
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# CONFIGURATION
# ============================================================

API_URL = "http://127.0.0.1:8000/api/extract"

st.set_page_config(
    page_title="LSR Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CUSTOM CSS
# ============================================================

CUSTOM_CSS = textwrap.dedent(
    """
    <style>

    /* ======================================================
       GLOBAL
    ====================================================== */

    .stApp {
        background: #f5f8fc;
    }

    .main .block-container {
        max-width: 1250px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* ======================================================
       SIDEBAR
    ====================================================== */

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5eaf0;
    }

    .sidebar-logo {
        text-align: center;
        padding: 10px 0 20px 0;
    }

    .sidebar-icon {
        width: 58px;
        height: 58px;
        border-radius: 16px;
        background: linear-gradient(
            135deg,
            #2563eb,
            #0ea5e9
        );
        color: white;
        font-size: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: auto;
        box-shadow:
            0 8px 20px rgba(37, 99, 235, 0.20);
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

    /* ======================================================
       HERO
    ====================================================== */

    .hero {
        background:
            linear-gradient(
                135deg,
                #eff6ff 0%,
                #ffffff 55%,
                #ecfeff 100%
            );

        border: 1px solid #dbeafe;
        border-radius: 24px;

        padding: 38px 42px;
        margin-bottom: 25px;

        box-shadow:
            0 8px 30px rgba(15, 23, 42, 0.04);
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
        max-width: 780px;
        margin-top: 14px;
    }

    /* ======================================================
       SECTIONS
    ====================================================== */

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

    /* ======================================================
       UPLOAD
    ====================================================== */

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

    /* ======================================================
       BUTTON
    ====================================================== */

    .stButton > button {
        width: 100%;
        border-radius: 12px;

        min-height: 48px;

        border: none;

        background:
            linear-gradient(
                135deg,
                #2563eb,
                #0ea5e9
            );

        color: white;

        font-weight: 700;
        font-size: 15px;

        box-shadow:
            0 6px 18px rgba(
                37,
                99,
                235,
                0.20
            );

        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        transform: translateY(-1px);

        box-shadow:
            0 10px 24px rgba(
                37,
                99,
                235,
                0.28
            );
    }

    /* ======================================================
       FILE CARD
    ====================================================== */

    .file-card {
        background: white;

        border: 1px solid #e5eaf0;
        border-radius: 16px;

        padding: 18px;
        margin: 15px 0;

        box-shadow:
            0 5px 18px rgba(
                15,
                23,
                42,
                0.03
            );
    }

    .file-name {
        font-weight: 700;
        color: #172033;
        font-size: 15px;
    }

    .file-info {
        color: #94a3b8;
        font-size: 12px;
        margin-top: 5px;
    }

    /* ======================================================
       RESULT CARD
    ====================================================== */

    .result-card {
        background: white;

        border: 1px solid #e5eaf0;
        border-radius: 16px;

        padding: 20px;

        min-height: 115px;

        box-shadow:
            0 5px 18px rgba(
                15,
                23,
                42,
                0.035
            );

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

        font-size: 15px;
        font-weight: 650;

        line-height: 1.5;
        word-break: break-word;
    }

    .result-value.empty {
        color: #94a3b8;
        font-weight: 500;
        font-style: italic;
    }

    /* ======================================================
       PROPERTY
    ====================================================== */

    .property-card {
        background: white;

        border: 1px solid #e5eaf0;
        border-radius: 18px;

        padding: 24px;

        box-shadow:
            0 5px 18px rgba(
                15,
                23,
                42,
                0.035
            );

        line-height: 1.8;
        color: #475569;
        font-size: 14px;
    }

    /* ======================================================
       METRICS
    ====================================================== */

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

    /* ======================================================
       LANGUAGE TITLE
    ====================================================== */

    .language-title {
        font-size: 16px;
        font-weight: 750;
        color: #172033;

        padding: 10px 0;
        margin-bottom: 8px;
    }

    /* ======================================================
       FOOTER
    ====================================================== */

    .footer {
        text-align: center;
        color: #94a3b8;

        font-size: 12px;

        padding: 30px 0 10px 0;
    }

    </style>
    """
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def display_value(value, default="Not available"):
    """Convert extracted values into safe display text."""

    if value is None:
        return default

    if isinstance(value, list):
        values = [
            str(item)
            for item in value
            if item not in (None, "")
        ]

        if not values:
            return default

        return ", ".join(values)

    if isinstance(value, dict):
        return str(value)

    text = str(value).strip()

    if not text:
        return default

    return text


def safe_html(value):
    """Escape extracted text before placing it inside HTML."""

    return html.escape(
        display_value(value)
    )


def prepare_documents(documents):
    """
    Convert backend document objects into
    frontend table rows.
    """

    rows = []

    if not isinstance(documents, list):
        return rows

    for document in documents:

        if not isinstance(document, dict):
            continue

        rows.append(
            {
                "Document Name": display_value(
                    document.get("document_name"),
                    "N/A",
                ),

                "Document Number": display_value(
                    document.get("document_number"),
                    "N/A",
                ),

                "Document Date": display_value(
                    document.get("document_date"),
                    "N/A",
                ),

                "Document Type": display_value(
                    document.get("document_copy_type"),
                    "N/A",
                ),

                "Additional Details": display_value(
                    document.get("additional_details"),
                    "N/A",
                ),
            }
        )

    return rows


def render_result_card(
    label,
    value,
    default="Not available",
):
    """Render a single result card."""

    text = display_value(
        value,
        default,
    )

    is_empty = text == default

    css_class = (
        "result-value empty"
        if is_empty
        else "result-value"
    )

    return f"""
    <div class="result-card">
        <div class="result-label">
            {html.escape(label)}
        </div>

        <div class="{css_class}">
            {html.escape(text)}
        </div>
    </div>
    """


def generate_pdf(result):
    """
    Generate a PDF report from the backend JSON response.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=10,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
    )

    story = []

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "LSR Document Intelligence Report",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"File: {html.escape(str(result.get('filename', 'N/A')))}",
            body_style,
        )
    )

    story.append(
        Spacer(1, 8)
    )

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Basic Information",
            heading_style,
        )
    )

    fields = result.get(
        "extracted_fields",
        {},
    )

    basic_fields = [
        ("LSR Date", "lsr_date"),
        ("Company Name", "company_name"),
        ("Applicant Name", "applicant_name"),
        ("Co-Applicant Name", "co_applicant_name"),
        ("Property Owner", "property_owner"),
        ("Application Number", "application_number"),
    ]

    basic_data = [
        [
            Paragraph("<b>Field</b>", small_style),
            Paragraph("<b>Value</b>", small_style),
        ]
    ]

    for label, key in basic_fields:

        value = display_value(
            fields.get(key),
            "Not available",
        )

        basic_data.append(
            [
                Paragraph(
                    html.escape(label),
                    small_style,
                ),
                Paragraph(
                    html.escape(value),
                    small_style,
                ),
            ]
        )

    basic_table = Table(
        basic_data,
        colWidths=[
            55 * mm,
            115 * mm,
        ],
        repeatRows=1,
    )

    basic_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#eaf2ff"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#d7dee8"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(basic_table)

    # --------------------------------------------------------
    # PROPERTY DESCRIPTION
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Property Description",
            heading_style,
        )
    )

    property_description = display_value(
        fields.get("property_description"),
        "Property description not available.",
    )

    story.append(
        Paragraph(
            html.escape(property_description),
            body_style,
        )
    )

    # --------------------------------------------------------
    # DOCUMENT TABLE FUNCTION
    # --------------------------------------------------------

    def add_document_section(
        title,
        documents,
    ):

        story.append(
            Paragraph(
                title,
                heading_style,
            )
        )

        rows = prepare_documents(
            documents
        )

        if not rows:

            story.append(
                Paragraph(
                    "No documents found.",
                    body_style,
                )
            )

            return

        table_data = [
            [
                Paragraph(
                    "<b>Document Name</b>",
                    small_style,
                ),
                Paragraph(
                    "<b>Document Number</b>",
                    small_style,
                ),
                Paragraph(
                    "<b>Date</b>",
                    small_style,
                ),
                Paragraph(
                    "<b>Type</b>",
                    small_style,
                ),
                Paragraph(
                    "<b>Additional Details</b>",
                    small_style,
                ),
            ]
        ]

        for row in rows:

            table_data.append(
                [
                    Paragraph(
                        html.escape(
                            row["Document Name"]
                        ),
                        small_style,
                    ),
                    Paragraph(
                        html.escape(
                            row["Document Number"]
                        ),
                        small_style,
                    ),
                    Paragraph(
                        html.escape(
                            row["Document Date"]
                        ),
                        small_style,
                    ),
                    Paragraph(
                        html.escape(
                            row["Document Type"]
                        ),
                        small_style,
                    ),
                    Paragraph(
                        html.escape(
                            row["Additional Details"]
                        ),
                        small_style,
                    ),
                ]
            )

        table = Table(
            table_data,
            colWidths=[
                43 * mm,
                30 * mm,
                25 * mm,
                20 * mm,
                52 * mm,
            ],
            repeatRows=1,
        )

        table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#eaf2ff"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.4,
                        colors.HexColor("#d7dee8"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        4,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(table)

    # --------------------------------------------------------
    # DOCUMENTS
    # --------------------------------------------------------

    add_document_section(
        "Documents Prior to Disbursal",
        result.get(
            "documents_prior_to_disbursal",
            [],
        ),
    )

    add_document_section(
        "Documents Post Disbursal",
        result.get(
            "documents_post_disbursal",
            [],
        ),
    )

    # --------------------------------------------------------
    # PROCESSING INFORMATION
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "Processing Information",
            heading_style,
        )
    )

    processing_time = result.get(
        "processing_time_seconds",
        "N/A",
    )

    story.append(
        Paragraph(
            f"Processing Time: "
            f"{html.escape(str(processing_time))} seconds",
            body_style,
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-logo">
            <div class="sidebar-icon">📄</div>
            <div class="sidebar-title">
                LSR Intelligence
            </div>
            <div class="sidebar-subtitle">
                Document Extraction System
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("🧭 Navigation")

    page = st.radio(
        "Navigation",
        [
            "Document Extraction",
            "About",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    st.markdown(
        """
        **Pipeline**

        📄 Document

        ↓

        🔍 DocTR OCR

        ↓

        🧠 FreeLLM

        ↓

        📋 Field Extraction

        ↓

        📑 Document Extraction

        ↓

        🌐 Tamil Translation

        ↓

        ✅ Validation

        ↓

        📊 Results
        """
    )

    st.divider()

    st.caption(
        "LSR Document Intelligence v1.0"
    )


# ============================================================
# DOCUMENT EXTRACTION PAGE
# ============================================================

if page == "Document Extraction":

    # --------------------------------------------------------
    # HERO
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="hero">

            <div class="hero-badge">
                AI-POWERED DOCUMENT ANALYSIS
            </div>

            <div class="hero-title">
                Extract LSR information
                <span>automatically.</span>
            </div>

            <div class="hero-description">
                Upload a Legal Search Report and let the
                document intelligence pipeline extract
                important property, applicant and document
                information automatically.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # UPLOAD
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        '📤 Upload Legal Search Report'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-subtitle">'
        'Supported formats: PDF, JPG, JPEG, PNG, TIFF'
        '</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Choose your LSR document",
        type=[
            "pdf",
            "jpg",
            "jpeg",
            "png",
            "tif",
            "tiff",
        ],
        label_visibility="collapsed",
    )

    if uploaded_file:

        file_bytes = uploaded_file.getvalue()

        file_size_kb = (
            len(file_bytes) / 1024
        )

        extension = (
            Path(uploaded_file.name)
            .suffix
            .upper()
            .replace(".", "")
        )

        st.markdown(
            f"""
            <div class="file-card">

                <div style="
                    font-size: 32px;
                ">
                    📄
                </div>

                <div>

                    <div class="file-name">
                        {html.escape(uploaded_file.name)}
                    </div>

                    <div class="file-info">
                        {extension}
                        &nbsp;•&nbsp;
                        {file_size_kb:.1f} KB
                    </div>

                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "✨ Start Extraction",
            use_container_width=True,
        ):

            # Clear previous result
            st.session_state.pop(
                "extraction_result",
                None,
            )

            progress = st.progress(
                0,
                text="Starting extraction...",
            )

            try:

                progress.progress(
                    10,
                    text="📄 Reading document...",
                )

                progress.progress(
                    25,
                    text="🔍 Running DocTR OCR...",
                )

                response = requests.post(
                    API_URL,
                    files={
                        "file": (
                            uploaded_file.name,
                            file_bytes,
                            uploaded_file.type,
                        )
                    },
                    timeout=600,
                )

                progress.progress(
                    80,
                    text="🧠 Processing extracted information...",
                )

                if response.status_code == 200:

                    result = response.json()

                    progress.progress(
                        100,
                        text="✅ Extraction completed!",
                    )

                    st.session_state[
                        "extraction_result"
                    ] = result

                    st.success(
                        "Document processed successfully!"
                    )

                else:

                    try:
                        error_message = (
                            response.json()
                            .get(
                                "detail",
                                "Unknown backend error.",
                            )
                        )

                    except Exception:
                        error_message = response.text

                    progress.empty()

                    st.error(
                        f"Extraction failed: "
                        f"{error_message}"
                    )

            except requests.exceptions.ConnectionError:

                progress.empty()

                st.error(
                    "❌ Unable to connect to FastAPI. "
                    "Make sure the backend is running on "
                    "http://127.0.0.1:8000"
                )

            except requests.exceptions.Timeout:

                progress.empty()

                st.error(
                    "⏱️ Document processing timed out. "
                    "Please try again."
                )

            except Exception as exc:

                progress.empty()

                st.error(
                    f"❌ Unexpected error: {exc}"
                )

    # ========================================================
    # RESULTS
    # ========================================================

    if "extraction_result" in st.session_state:

        result = st.session_state[
            "extraction_result"
        ]

        fields = result.get(
            "extracted_fields",
            {},
        )

        translated_fields = result.get(
            "translated_fields",
            {},
        )

        prior_docs = result.get(
            "documents_prior_to_disbursal",
            [],
        )

        post_docs = result.get(
            "documents_post_disbursal",
            [],
        )

        processing_time = result.get(
            "processing_time_seconds",
            "N/A",
        )

        # ----------------------------------------------------
        # RESULT HEADER
        # ----------------------------------------------------

        st.divider()

        st.markdown(
            '<div class="section-title">'
            '📊 Extraction Results'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-subtitle">'
            'Information identified from the uploaded Legal Search Report'
            '</div>',
            unsafe_allow_html=True,
        )

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------

        extracted_count = sum(
            1
            for value in fields.values()
            if value not in (
                None,
                "",
                [],
                {},
            )
        )

        total_documents = (
            len(prior_docs)
            + len(post_docs)
        )

        metric1, metric2, metric3, metric4, metric5 = (
            st.columns(5)
        )

        metric1.metric(
            "Fields Extracted",
            f"{extracted_count}/{len(fields)}",
        )

        metric2.metric(
            "Total Documents",
            total_documents,
        )

        metric3.metric(
            "Prior Disbursal",
            len(prior_docs),
        )

        metric4.metric(
            "Post Disbursal",
            len(post_docs),
        )

        metric5.metric(
            "Processing Time",
            (
                f"{processing_time}s"
                if processing_time != "N/A"
                else "N/A"
            ),
        )

        # ====================================================
        # BASIC INFORMATION
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '📋 Basic Information'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-subtitle">'
            'Key information extracted from the LSR'
            '</div>',
            unsafe_allow_html=True,
        )

        basic_fields = [
            (
                "lsr_date",
                "LSR Date",
            ),
            (
                "company_name",
                "Company Name",
            ),
            (
                "application_number",
                "Application Number",
            ),
            (
                "applicant_name",
                "Applicant Name",
            ),
            (
                "co_applicant_name",
                "Co-Applicant Name",
            ),
            (
                "property_owner",
                "Property Owner",
            ),
        ]

        # ----------------------------------------------------
        # ENGLISH / TAMIL
        # ----------------------------------------------------

        english_col, tamil_col = st.columns(2)

        with english_col:

            st.markdown(
                '<div class="language-title">'
                '🇬🇧 English'
                '</div>',
                unsafe_allow_html=True,
            )

            for key, label in basic_fields:

                st.markdown(
                    render_result_card(
                        label,
                        fields.get(key),
                        "Not available",
                    ),
                    unsafe_allow_html=True,
                )

        with tamil_col:

            st.markdown(
                '<div class="language-title">'
                '🇮🇳 தமிழ்'
                '</div>',
                unsafe_allow_html=True,
            )

            for key, label in basic_fields:

                st.markdown(
                    render_result_card(
                        label,
                        translated_fields.get(key),
                        "கிடைக்கவில்லை",
                    ),
                    unsafe_allow_html=True,
                )

        # ====================================================
        # PROPERTY DESCRIPTION
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '🏠 Property Description'
            '</div>',
            unsafe_allow_html=True,
        )

        property_description = fields.get(
            "property_description"
        )

        translated_property_description = (
            translated_fields.get(
                "property_description"
            )
        )

        property_eng_col, property_tam_col = (
            st.columns(2)
        )

        with property_eng_col:

            st.markdown(
                '<div class="language-title">'
                '🇬🇧 English'
                '</div>',
                unsafe_allow_html=True,
            )

            if property_description:

                st.markdown(
                    f"""
                    <div class="property-card">
                        {safe_html(property_description)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.info(
                    "Property description was not found."
                )

        with property_tam_col:

            st.markdown(
                '<div class="language-title">'
                '🇮🇳 தமிழ்'
                '</div>',
                unsafe_allow_html=True,
            )

            if translated_property_description:

                st.markdown(
                    f"""
                    <div class="property-card">
                        {safe_html(
                            translated_property_description
                        )}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.info(
                    "சொத்து விவரம் கிடைக்கவில்லை."
                )

        # ====================================================
        # PRIOR DOCUMENTS
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '📑 Documents Prior to Disbursal'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-subtitle">'
            'Documents required before disbursal'
            '</div>',
            unsafe_allow_html=True,
        )

        prior_table = prepare_documents(
            prior_docs
        )

        if prior_table:

            st.dataframe(
                prior_table,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No documents prior to disbursal found."
            )

        # ====================================================
        # POST DOCUMENTS
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '📑 Documents Post Disbursal'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-subtitle">'
            'Documents required after disbursal'
            '</div>',
            unsafe_allow_html=True,
        )

        post_table = prepare_documents(
            post_docs
        )

        if post_table:

            st.dataframe(
                post_table,
                use_container_width=True,
                hide_index=True,
            )

        else:

            st.info(
                "No documents post disbursal found."
            )

        # ====================================================
        # REPORT GENERATION
        # ====================================================

        st.markdown(
            '<div class="section-title">'
            '📄 Report Generation'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="section-subtitle">'
            'Generate a PDF report containing the extracted information'
            '</div>',
            unsafe_allow_html=True,
        )

        report_col1, report_col2 = st.columns(
            [3, 1]
        )

        with report_col1:

            st.markdown(
                """
                <div class="file-card">

                    <div style="font-size:30px;">
                        📄
                    </div>

                    <div>

                        <div class="file-name">
                            LSR Extraction Report
                        </div>

                        <div class="file-info">
                            Basic information • Property description
                            • Required documents
                        </div>

                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with report_col2:

            pdf_bytes = generate_pdf(
                result
            )

            filename = (
                Path(
                    result.get(
                        "filename",
                        "LSR_Report",
                    )
                ).stem
                + "_Report.pdf"
            )

            st.download_button(
                "📥 Generate PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )

        # ====================================================
        # RAW JSON
        # ====================================================

        with st.expander(
            "🔍 View Raw Backend Response"
        ):

            st.json(result)

        # ====================================================
        # FOOTER
        # ====================================================

        st.markdown(
            """
            <div class="footer">
                LSR Document Intelligence
                &nbsp;•&nbsp;
                DocTR + FreeLLM + FastAPI
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# ABOUT PAGE
# ============================================================

else:

    st.markdown(
        """
        <div class="hero">

            <div class="hero-badge">
                ABOUT THE SYSTEM
            </div>

            <div class="hero-title">
                LSR Document
                <span>Intelligence</span>
            </div>

            <div class="hero-description">
                An AI-assisted document extraction system
                designed to process Legal Search Reports
                and return structured property information.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            ### 🔍 DocTR

            **OCR Engine**

            Extracts text from uploaded PDF and
            image-based legal documents.
            """
        )

    with col2:

        st.markdown(
            """
            ### 🧠 FreeLLM

            **Language Model**

            Converts OCR text into structured
            information required by the application.
            """
        )

    with col3:

        st.markdown(
            """
            ### ⚡ FastAPI

            **Backend**

            Coordinates OCR, extraction,
            validation and translation.
            """
        )

    st.divider()

    st.subheader(
        "📌 Extracted Information"
    )

    st.markdown(
        """
        The system currently extracts:

        - **LSR Date**
        - **Company Name**
        - **Applicant Name**
        - **Co-Applicant Name**
        - **Property Owner**
        - **Application Number**
        - **Property Description**
        - **Documents Prior to Disbursal**
        - **Documents Post Disbursal**

        Document records contain:

        - Document Name
        - Document Number
        - Document Date
        - Document Type
        - Additional Details
        """
    )

    st.divider()

    st.subheader(
        "🔄 Processing Pipeline"
    )

    st.markdown(
        """
        **Upload**

        ↓

        **DocTR OCR**

        ↓

        **FreeLLM Extraction**

        ↓

        **Document Extraction**

        ↓

        **Validation**

        ↓

        **Tamil Translation**

        ↓

        **Structured JSON**

        ↓

        **Dashboard + PDF Report**
        """
    )