from io import BytesIO
from pathlib import Path
import textwrap

import requests
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
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

    .stApp {
        background-color: #f8fafc;
    }

    .block-container {
        max-width: 1280px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 2rem;
        border-radius: 18px;
        background: linear-gradient(
            135deg,
            #0f4c81,
            #2563a6
        );
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 25px rgba(15, 76, 129, 0.15);
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 750;
        margin-bottom: 0.4rem;
    }

    .hero-subtitle {
        font-size: 1rem;
        opacity: 0.92;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0f4c81;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }

    .language-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f4c81;
        margin-bottom: 0.5rem;
    }

    .upload-box {
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #dbe4ef;
        background: white;
        margin-bottom: 1rem;
    }

    </style>
    """
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def display_value(value, default="Not available"):
    """Safely format extracted values for frontend display."""

    if value is None:
        return default

    if isinstance(value, str):
        cleaned = value.strip()

        if not cleaned:
            return default

        if cleaned.lower() in {
            "none",
            "null",
            "n/a",
            "not available",
        }:
            return default

        return cleaned

    if isinstance(value, list):
        values = [
            str(item).strip()
            for item in value
            if item is not None and str(item).strip()
        ]

        if not values:
            return default

        return ", ".join(values)

    return str(value)


def prepare_documents(documents):
    """Prepare backend document objects for Streamlit tables."""

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


def sanitize_text_for_pdf(text):
    """Prevent PDF generation from failing on unsupported characters."""

    if not text:
        return "N/A"

    return (
        str(text)
        .encode("ascii", "xmlcharrefreplace")
        .decode("utf-8")
    )


# ============================================================
# PDF PAGE NUMBER CANVAS
# ============================================================

class NumberedCanvas(canvas.Canvas):
    """Generate Page X of Y footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):

        total_pages = len(self._saved_page_states)

        for state in self._saved_page_states:

            self.__dict__.update(state)

            self.saveState()

            self.setFont("Helvetica", 8)
            self.setFillColor(
                colors.HexColor("#64748B")
            )

            self.setStrokeColor(
                colors.HexColor("#E2E8F0")
            )

            self.setLineWidth(0.5)

            self.line(
                15 * mm,
                12 * mm,
                A4[0] - 15 * mm,
                12 * mm,
            )

            page_text = (
                f"Page {self._pageNumber} "
                f"of {total_pages}"
            )

            self.drawRightString(
                A4[0] - 15 * mm,
                8 * mm,
                page_text,
            )

            self.drawString(
                15 * mm,
                8 * mm,
                "LSR Document Intelligence",
            )

            self.restoreState()

            super().showPage()

        super().save()


# ============================================================
# PDF GENERATION
# ============================================================

def generate_pdf_report(result):
    """Generate complete extraction PDF report."""

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F4C81"),
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=15,
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0F4C81"),
        spaceBefore=12,
        spaceAfter=6,
    )

    normal_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
    )

    header_style = ParagraphStyle(
        "TableHeader",
        parent=normal_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F4C81"),
    )

    story = []

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "LSR Document Intelligence",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "Legal Search Report — Extraction & Analysis Report",
            subtitle_style,
        )
    )

    filename = result.get(
        "filename",
        "Unknown",
    )

    processing_time = result.get(
        "processing_time_seconds",
        "N/A",
    )

    story.append(
        Paragraph(
            (
                f"<b>File Name:</b> "
                f"{sanitize_text_for_pdf(filename)}"
                f"&nbsp;&nbsp; | &nbsp;&nbsp;"
                f"<b>Processing Time:</b> "
                f"{processing_time} seconds"
            ),
            normal_style,
        )
    )

    story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # Basic Information
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "1. Basic Information",
            heading_style,
        )
    )

    fields = result.get(
        "extracted_fields",
        {},
    )

    translated = result.get(
        "translated_fields",
        {},
    )

    field_mappings = [
        ("lsr_date", "LSR Date"),
        ("company_name", "Company Name"),
        ("application_number", "Application Number"),
        ("applicant_name", "Applicant Name"),
        ("co_applicant_name", "Co-Applicant Name"),
        ("property_owner", "Property Owner"),
    ]

    basic_data = [
        [
            Paragraph("Field", header_style),
            Paragraph("English Value", header_style),
            Paragraph("Tamil Value", header_style),
        ]
    ]

    for key, label in field_mappings:

        english = sanitize_text_for_pdf(
            display_value(
                fields.get(key)
            )
        )

        tamil = sanitize_text_for_pdf(
            display_value(
                translated.get(key),
                "கிடைக்கவில்லை",
            )
        )

        basic_data.append(
            [
                Paragraph(label, normal_style),
                Paragraph(english, normal_style),
                Paragraph(tamil, normal_style),
            ]
        )

    basic_table = Table(
        basic_data,
        colWidths=[
            40 * mm,
            70 * mm,
            70 * mm,
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
                    colors.HexColor("#F1F5F9"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
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

    story.append(basic_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # Property Description
    # --------------------------------------------------------

    story.append(
        Paragraph(
            "2. Property Description",
            heading_style,
        )
    )

    english_description = sanitize_text_for_pdf(
        display_value(
            fields.get(
                "property_description"
            )
        )
    )

    tamil_description = sanitize_text_for_pdf(
        display_value(
            translated.get(
                "property_description"
            ),
            "கிடைக்கவில்லை",
        )
    )

    property_table = Table(
        [
            [
                Paragraph(
                    "English Description",
                    header_style,
                ),
                Paragraph(
                    "Tamil Description",
                    header_style,
                ),
            ],
            [
                Paragraph(
                    english_description,
                    normal_style,
                ),
                Paragraph(
                    tamil_description,
                    normal_style,
                ),
            ],
        ],
        colWidths=[
            90 * mm,
            90 * mm,
        ],
        repeatRows=1,
    )

    property_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#F1F5F9"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
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

    story.append(property_table)
    story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # Document Tables
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

        table_data = [
            [
                Paragraph(
                    "Document Name",
                    header_style,
                ),
                Paragraph(
                    "Document Number",
                    header_style,
                ),
                Paragraph(
                    "Document Date",
                    header_style,
                ),
                Paragraph(
                    "Document Type",
                    header_style,
                ),
                Paragraph(
                    "Additional Details",
                    header_style,
                ),
            ]
        ]

        rows = prepare_documents(documents)

        if not rows:

            table_data.append(
                [
                    Paragraph(
                        "No documents found.",
                        normal_style,
                    ),
                    Paragraph(
                        "N/A",
                        normal_style,
                    ),
                    Paragraph(
                        "N/A",
                        normal_style,
                    ),
                    Paragraph(
                        "N/A",
                        normal_style,
                    ),
                    Paragraph(
                        "N/A",
                        normal_style,
                    ),
                ]
            )

        else:

            for row in rows:

                table_data.append(
                    [
                        Paragraph(
                            sanitize_text_for_pdf(
                                row["Document Name"]
                            ),
                            normal_style,
                        ),
                        Paragraph(
                            sanitize_text_for_pdf(
                                row["Document Number"]
                            ),
                            normal_style,
                        ),
                        Paragraph(
                            sanitize_text_for_pdf(
                                row["Document Date"]
                            ),
                            normal_style,
                        ),
                        Paragraph(
                            sanitize_text_for_pdf(
                                row["Document Type"]
                            ),
                            normal_style,
                        ),
                        Paragraph(
                            sanitize_text_for_pdf(
                                row["Additional Details"]
                            ),
                            normal_style,
                        ),
                    ]
                )

        table = Table(
            table_data,
            colWidths=[
                43 * mm,
                30 * mm,
                25 * mm,
                25 * mm,
                57 * mm,
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
                        colors.HexColor("#F1F5F9"),
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
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
        story.append(Spacer(1, 10))

    add_document_section(
        "3. Documents Prior to Disbursal",
        result.get(
            "documents_prior_to_disbursal",
            [],
        ),
    )

    add_document_section(
        "4. Documents Post Disbursal",
        result.get(
            "documents_post_disbursal",
            [],
        ),
    )

    document.build(
        story,
        canvasmaker=NumberedCanvas,
    )

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# PROJECT HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            📄 LSR Document Intelligence
        </div>
        <div class="hero-subtitle">
            Legal Search Report Extraction & Analysis System
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# UPLOAD SECTION
# ============================================================

st.markdown(
    '<div class="section-title">📤 Upload Legal Search Report</div>',
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Select an LSR document",
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

    file_size_kb = len(file_bytes) / 1024

    extension = (
        Path(uploaded_file.name)
        .suffix
        .upper()
        .replace(".", "")
    )

    st.markdown(
        '<div class="upload-box">',
        unsafe_allow_html=True,
    )

    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:
        st.caption("Filename")
        st.markdown(
            f"**{uploaded_file.name}**"
        )

    with info_col2:
        st.caption("File Type")
        st.write(
            f"**{extension}**"
        )

    with info_col3:
        st.caption("File Size")
        st.write(
            f"**{file_size_kb:.1f} KB**"
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    st.write("")

    start_extraction = st.button(
        "✨ Start Extraction",
        type="primary",
        use_container_width=True,
    )

    # ========================================================
    # EXTRACTION
    # ========================================================

    if start_extraction:

        with st.status(
            "🔄 Extraction Started...",
            expanded=True,
        ) as status:

            st.write(
                "Uploading document to FastAPI..."
            )

            try:

                response = requests.post(
                    API_URL,
                    files={
                        "file": (
                            uploaded_file.name,
                            file_bytes,
                            uploaded_file.type
                            or "application/octet-stream",
                        )
                    },
                    timeout=900,
                )

                st.write(
                    "Running OCR, LLM extraction and translation..."
                )

                if response.status_code == 200:

                    result = response.json()

                    result["filename"] = (
                        uploaded_file.name
                    )

                    st.session_state[
                        "extraction_result"
                    ] = result

                    status.update(
                        label="✅ Extraction Completed Successfully",
                        state="complete",
                        expanded=False,
                    )

                    st.success(
                        "Document processed successfully."
                    )

                else:

                    try:
                        error_detail = (
                            response.json()
                            .get(
                                "detail",
                                "Unknown backend error.",
                            )
                        )
                    except Exception:
                        error_detail = response.text

                    status.update(
                        label="❌ Extraction Failed",
                        state="error",
                        expanded=True,
                    )

                    st.error(
                        f"Backend Error: {error_detail}"
                    )

            except requests.exceptions.ConnectionError:

                status.update(
                    label="❌ Backend Connection Failed",
                    state="error",
                    expanded=True,
                )

                st.error(
                    "Unable to connect to FastAPI. "
                    "Make sure the backend is running."
                )

            except requests.exceptions.Timeout:

                status.update(
                    label="❌ Processing Timeout",
                    state="error",
                    expanded=True,
                )

                st.error(
                    "The extraction took too long. "
                    "Please try again."
                )

            except Exception as exc:

                status.update(
                    label="❌ Unexpected Error",
                    state="error",
                    expanded=True,
                )

                st.error(
                    f"Unexpected error: {exc}"
                )


# ============================================================
# RESULTS
# ============================================================

if "extraction_result" in st.session_state:

    result = st.session_state[
        "extraction_result"
    ]

    fields = result.get(
        "extracted_fields",
        {},
    )

    translated = result.get(
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

    st.divider()

    # ========================================================
    # PROCESSING SUMMARY
    # ========================================================

    st.markdown(
        '<div class="section-title">📊 Processing Summary</div>',
        unsafe_allow_html=True,
    )

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

    # ========================================================
    # BASIC INFORMATION
    # ========================================================

    st.markdown(
        '<div class="section-title">📋 Basic Information</div>',
        unsafe_allow_html=True,
    )

    english_col, tamil_col = st.columns(2)

    with english_col:

        st.markdown(
            '<div class="language-title">🇬🇧 English</div>',
            unsafe_allow_html=True,
        )

    with tamil_col:

        st.markdown(
            '<div class="language-title">🇮🇳 தமிழ்</div>',
            unsafe_allow_html=True,
        )

    basic_fields = [
        ("lsr_date", "LSR Date"),
        ("company_name", "Company Name"),
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

    for key, label in basic_fields:

        english_value = display_value(
            fields.get(key),
            "Not available",
        )

        tamil_value = display_value(
            translated.get(key),
            "கிடைக்கவில்லை",
        )

        col1, col2 = st.columns(2)

        with col1:

            with st.container(
                border=True
            ):

                st.caption(label)

                st.write(
                    english_value
                )

        with col2:

            with st.container(
                border=True
            ):

                st.caption(label)

                st.write(
                    tamil_value
                )

    # ========================================================
    # PROPERTY DESCRIPTION
    # ========================================================

    st.markdown(
        '<div class="section-title">🏠 Property Description</div>',
        unsafe_allow_html=True,
    )

    property_col1, property_col2 = (
        st.columns(2)
    )

    with property_col1:

        st.markdown(
            '<div class="language-title">🇬🇧 English Description</div>',
            unsafe_allow_html=True,
        )

        with st.container(
            border=True
        ):

            st.write(
                display_value(
                    fields.get(
                        "property_description"
                    ),
                    "Property description not available.",
                )
            )

    with property_col2:

        st.markdown(
            '<div class="language-title">🇮🇳 Tamil Description</div>',
            unsafe_allow_html=True,
        )

        with st.container(
            border=True
        ):

            st.write(
                display_value(
                    translated.get(
                        "property_description"
                    ),
                    "சொத்து விவரம் கிடைக்கவில்லை.",
                )
            )

    # ========================================================
    # PRIOR DOCUMENTS
    # ========================================================

    st.markdown(
        '<div class="section-title">📑 Documents Prior to Disbursal</div>',
        unsafe_allow_html=True,
    )

    prior_rows = prepare_documents(
        prior_docs
    )

    if prior_rows:

        st.dataframe(
            prior_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Document Name": st.column_config.TextColumn(
                    "Document Name",
                    width="large",
                ),
                "Document Number": st.column_config.TextColumn(
                    "Document Number",
                    width="medium",
                ),
                "Document Date": st.column_config.TextColumn(
                    "Document Date",
                    width="medium",
                ),
                "Document Type": st.column_config.TextColumn(
                    "Document Type",
                    width="medium",
                ),
                "Additional Details": st.column_config.TextColumn(
                    "Additional Details",
                    width="large",
                ),
            },
        )

    else:

        st.info(
            "No documents prior to disbursal found."
        )

    # ========================================================
    # POST DOCUMENTS
    # ========================================================

    st.markdown(
        '<div class="section-title">📑 Documents Post Disbursal</div>',
        unsafe_allow_html=True,
    )

    post_rows = prepare_documents(
        post_docs
    )

    if post_rows:

        st.dataframe(
            post_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Document Name": st.column_config.TextColumn(
                    "Document Name",
                    width="large",
                ),
                "Document Number": st.column_config.TextColumn(
                    "Document Number",
                    width="medium",
                ),
                "Document Date": st.column_config.TextColumn(
                    "Document Date",
                    width="medium",
                ),
                "Document Type": st.column_config.TextColumn(
                    "Document Type",
                    width="medium",
                ),
                "Additional Details": st.column_config.TextColumn(
                    "Additional Details",
                    width="large",
                ),
            },
        )

    else:

        st.info(
            "No documents post disbursal found."
        )

    # ========================================================
    # PDF REPORT
    # ========================================================

    st.markdown(
        '<div class="section-title">📄 Generate Report</div>',
        unsafe_allow_html=True,
    )

    try:

        pdf_bytes = generate_pdf_report(
            result
        )

        st.download_button(
            label="📥 Generate & Download PDF Report",
            data=pdf_bytes,
            file_name=(
                f"LSR_Report_"
                f"{result.get('filename', 'extracted')}.pdf"
            ),
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    except Exception as pdf_error:

        st.warning(
            f"PDF generation warning: {pdf_error}"
        )

    # ========================================================
    # RAW JSON
    # ========================================================

    with st.expander(
        "🔍 View Raw Extraction JSON"
    ):

        st.json(result)