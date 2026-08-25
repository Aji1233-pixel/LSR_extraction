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
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

# Ensure UTF-8 output so emoji/log messages don't crash
# on Windows consoles that default to cp1252.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
# HELPER FUNCTIONS
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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def render_bilingual_field(label, english_value, tamil_value):
    """Render a field with English on left, Tamil on right (both selectable)."""
    if english_value in [None, "", [], {}]:
        eng_display = "Not found"
        eng_class = "bilingual-value empty"
        tam_display = "—"
    else:
        eng_display = str(english_value)
        eng_class = "bilingual-value"
        tam_display = tamil_value or "—"

    html = f"""
    <div class="bilingual-card">
        <div class="bilingual-label">{label}</div>
        <div class="bilingual-row">
            <div class="bilingual-col">
                <div class="bilingual-col-title">English</div>
                <div class="{eng_class}">{eng_display}</div>
            </div>
            <div class="bilingual-col">
                <div class="bilingual-col-title">தமிழ் (Tamil)</div>
                <div class="bilingual-value tamil">{tam_display}</div>
            </div>
        </div>
    </div>
    """
    return html


def render_property_bilingual(english_desc, tamil_desc):
    """Render property description with English on left, Tamil on right."""
    if not english_desc:
        eng_display = "Not found"
        eng_class = "property-bilingual-text empty"
        tam_display = "—"
    else:
        eng_display = str(english_desc)
        eng_class = "property-bilingual-text"
        tam_display = tamil_desc or "—"

    html = f"""
    <div class="property-bilingual">
        <div class="property-bilingual-row">
            <div class="property-bilingual-col">
                <div class="property-bilingual-title">English</div>
                <div class="{eng_class}">{eng_display}</div>
            </div>
            <div class="property-bilingual-col">
                <div class="property-bilingual-title">தமிழ் (Tamil)</div>
                <div class="property-bilingual-text tamil">{tam_display}</div>
            </div>
        </div>
    </div>
    """
    return html


def render_doc_table(documents, title):
    """Render document list as a table."""
    st.markdown(f'<div class="doc-table-title">{title}</div>', unsafe_allow_html=True)
    if not documents:
        st.info("No documents found in this category.")
        return

    rows = []
    for doc in documents:
        doc_name = doc.get("document_name") or "—"
        doc_number = doc.get("document_number") or "—"
        doc_date = doc.get("document_date") or "—"
        doc_mode = doc.get("mode_of_document") or "—"
        extra = doc.get("additional_details") or ""
        rows.append({
            "Deed Name": doc_name,
            "Doc No.": doc_number,
            "Date": doc_date,
            "Mode": doc_mode,
            "Additional Details": extra,
        })

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


def reorder_property_description(text: str) -> str:
    """
    Reorder property description to show address first, then boundaries/extent.

    Expected input format contains:
    - Address/location info
    - Survey/khewat/khatoni details
    - Extent/measurements
    - Boundaries (North, South, East, West)
    """
    if not text:
        return text

    lines = text.strip().split('\n')

    # Categories for reordering
    address_lines = []
    survey_lines = []
    extent_lines = []
    boundary_lines = []
    other_lines = []

    boundary_keywords = ['north:', 'south:', 'east:', 'west:', 'north ', 'south ', 'east ', 'west ']
    extent_keywords = ['measuring', 'extent', 'area', 'sq.ft', 'sq ft', 'acre', 'hectare', 'cent', 'ground']
    survey_keywords = ['survey', 'khewat', 'khatoni', 'khata', 'plot no', 'plot number', 'door no', 'door number']
    address_keywords = ['situated', 'located', 'at ', 'address', 'road', 'street', 'village', 'town', 'city', 'district', 'pincode', 'pin code', 'chennai', 'main road']
    # Keep headers like "Bounded by:" with the boundary section
    header_keywords = ['bounded by', 'boundaries:', 'boundary:']

    for line in lines:
        line_lower = line.lower().strip()
        if not line_lower:
            continue

        is_boundary = any(kw in line_lower for kw in boundary_keywords)
        is_extent = any(kw in line_lower for kw in extent_keywords)
        is_survey = any(kw in line_lower for kw in survey_keywords)
        is_address = any(kw in line_lower for kw in address_keywords)
        is_header = any(kw in line_lower for kw in header_keywords)

        if is_boundary:
            boundary_lines.append(line)
        elif is_extent:
            extent_lines.append(line)
        elif is_survey:
            survey_lines.append(line)
        elif is_address:
            address_lines.append(line)
        elif is_header:
            boundary_lines.insert(0, line)  # Put header at start of boundaries
        else:
            other_lines.append(line)

    # Reorder: Address -> Survey -> Extent -> Boundaries -> Other
    reordered = []
    reordered.extend(address_lines)
    reordered.extend(survey_lines)
    reordered.extend(extent_lines)
    reordered.extend(boundary_lines)
    reordered.extend(other_lines)

    return '\n'.join(reordered) if reordered else text


def generate_pdf_report(result: dict) -> bytes:
    """Generate a PDF report from extraction results with dynamic layout."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=6,
        textColor=HexColor('#1e293b'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=20,
        textColor=HexColor('#64748b'),
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=16,
        spaceAfter=8,
        textColor=HexColor('#1e293b'),
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0,
    )

    field_label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=4,
        spaceAfter=2,
        textColor=HexColor('#64748b'),
        fontName='Helvetica-Bold',
        textTransform='uppercase'
    )

    field_value_style = ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        textColor=HexColor('#1e293b'),
        fontName='Helvetica',
        leading=15
    )

    tamil_value_style = ParagraphStyle(
        'TamilValue',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        textColor=HexColor('#059669'),
        fontName='Helvetica',
        leading=15
    )

    empty_style = ParagraphStyle(
        'EmptyValue',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        textColor=HexColor('#cbd5e1'),
        fontName='Helvetica-Oblique',
        leading=15
    )

    # Table cell style for wrapping
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica',
        spaceBefore=0,
        spaceAfter=0,
    )

    cell_style_bold = ParagraphStyle(
        'CellStyleBold',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        fontName='Helvetica-Bold',
        spaceBefore=0,
        spaceAfter=0,
        textColor=HexColor('#ffffff'),
    )

    story = []

    # Title
    story.append(Paragraph("LSR Document Intelligence", title_style))
    story.append(Paragraph("Extracted Information Report", subtitle_style))
    story.append(Spacer(1, 0.2*inch))

    # Metadata
    fields = result.get("extracted_fields", {})
    translated_fields = result.get("translated_fields", {})
    processing_time = result.get("processing_time_seconds")
    filename = result.get("filename", "Unknown")

    # Non-translatable fields notice
    story.append(Paragraph("Note: The following fields are not translated (dates, IDs, numbers): LSR Date, Application Number",
                          ParagraphStyle('Note', parent=styles['Normal'], fontSize=9, textColor=HexColor('#64748b'), fontName='Helvetica-Oblique')))
    story.append(Spacer(1, 0.15*inch))

    # Helper to add bilingual field
    def add_bilingual_field(label, eng_value, tam_value):
        story.append(Paragraph(label, field_label_style))
        if eng_value and str(eng_value).strip() not in ["Not found", "—", "None", ""]:
            story.append(Paragraph(f"English: {eng_value}", field_value_style))
            if tam_value and str(tam_value).strip() not in ["—", "None", ""]:
                story.append(Paragraph(f"தமிழ்: {tam_value}", tamil_value_style))
        else:
            story.append(Paragraph("Not found", empty_style))
        story.append(Spacer(1, 0.05*inch))

    # ========================================================
    # BASIC INFORMATION
    # ========================================================
    story.append(Paragraph("📋 Basic Information", section_style))

    basic_fields = [
        ("lsr_date", "LSR Date"),
        ("company_name", "Company Name"),
        ("application_number", "Application Number"),
        ("applicant_name", "Applicant Name"),
        ("co_applicant_name", "Co-Applicant Name"),
        ("property_owner", "Property Owner"),
    ]

    for field_name, label in basic_fields:
        value = fields.get(field_name)
        tamil_value = translated_fields.get(field_name)
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        add_bilingual_field(label, value, tamil_value)

    # ========================================================
    # PROPERTY DESCRIPTION (Reordered)
    # ========================================================
    story.append(Paragraph("🏠 Property Description", section_style))

    property_description = fields.get("property_description")
    property_tamil = translated_fields.get("property_description")

    if property_description:
        reordered_eng = reorder_property_description(property_description)
        reordered_tam = reorder_property_description(property_tamil) if property_tamil else ""
        story.append(Paragraph("English:", field_label_style))
        story.append(Paragraph(reordered_eng, field_value_style))
        if reordered_tam:
            story.append(Paragraph("தமிழ்:", field_label_style))
            story.append(Paragraph(reordered_tam, tamil_value_style))
    else:
        story.append(Paragraph("Not found", empty_style))

    # ========================================================
    # HELPER: Create dynamic document table
    # ========================================================
    def create_document_table(documents, title, header_color):
        """Create a document table with dynamic column widths and proper text wrapping."""
        if not documents:
            return None

        story.append(Paragraph(title, section_style))

        # Prepare data with Paragraph objects for text wrapping
        headers = ["Deed Name", "Doc No.", "Date", "Mode", "Additional Details"]
        doc_data = [headers]

        # Calculate max content length for each column to determine widths
        col_max_lengths = [len(h) for h in headers]

        for doc in documents:
            row = [
                str(doc.get("document_name") or "—"),
                str(doc.get("document_number") or "—"),
                str(doc.get("document_date") or "—"),
                str(doc.get("mode_of_document") or "—"),
                str(doc.get("additional_details") or "—"),
            ]
            for i, cell in enumerate(row):
                col_max_lengths[i] = max(col_max_lengths[i], len(cell))
            doc_data.append(row)

        # Calculate dynamic column widths based on content
        # Available width = page width - margins = 595 - 54 - 54 = 487 points ≈ 6.76 inches
        available_width = 6.5 * inch
        # Base widths proportional to max content, with minimums
        min_widths = [1.2*inch, 0.8*inch, 0.8*inch, 0.7*inch, 1.5*inch]
        total_min = sum(min_widths)

        if total_min > available_width:
            # Scale down proportionally
            scale = available_width / total_min
            col_widths = [w * scale for w in min_widths]
        else:
            # Distribute extra space proportionally to content needs
            extra = available_width - total_min
            total_content = sum(col_max_lengths)
            if total_content > 0:
                col_widths = [
                    min_widths[i] + (extra * col_max_lengths[i] / total_content)
                    for i in range(5)
                ]
            else:
                col_widths = min_widths

        # Convert to Paragraph objects for wrapping
        wrapped_data = []
        for row_idx, row in enumerate(doc_data):
            wrapped_row = []
            for col_idx, cell_text in enumerate(row):
                if row_idx == 0:
                    # Header row
                    wrapped_row.append(Paragraph(str(cell_text), cell_style_bold))
                else:
                    wrapped_row.append(Paragraph(str(cell_text), cell_style))
            wrapped_data.append(wrapped_row)

        table = Table(wrapped_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), header_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#ffffff'), HexColor('#f8fafc')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            # Allow row height to expand for wrapped text
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        story.append(table)

    # ========================================================
    # DOCUMENTS PRIOR TO DISBURSAL
    # ========================================================
    prior_docs = result.get("documents_prior_to_disbursal", [])
    create_document_table(prior_docs, "📋 Documents Prior to Disbursal", HexColor('#4f46e5'))

    # ========================================================
    # DOCUMENTS POST DISBURSAL
    # ========================================================
    post_docs = result.get("documents_post_disbursal", [])
    if post_docs:
        story.append(Spacer(1, 0.15*inch))
        create_document_table(post_docs, "📋 Documents Post Disbursal", HexColor('#06b6d4'))

    # Footer
    story.append(Spacer(1, 0.3*inch))
    processing_time = result.get('processing_time_seconds', 0) or 0
    filename = result.get('filename', 'Unknown')
    story.append(Paragraph(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Processing Time: {processing_time:.1f}s | Source: {filename}",
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=HexColor('#94a3b8'), alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def get_pdf_download_link(pdf_bytes: bytes, filename: str) -> str:
    """Generate a download link for PDF."""
    b64 = base64.b64encode(pdf_bytes).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="{filename}.pdf" class="download-btn">📥 Download PDF Report</a>'


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

    # ========================================================
    # RESULTS
    # ========================================================

    if "extraction_result" in st.session_state:
        result = st.session_state["extraction_result"]
        fields = result.get("extracted_fields", {})
        processing_time = result.get("processing_time_seconds")
        filename = result.get("filename", "Unknown")

        # ========================================================
        # NON-TRANSLATABLE FIELDS NOTICE
        # ========================================================
        st.markdown(
            """<div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 12px; padding: 16px 20px; margin-bottom: 24px;">
                <div style="display: flex; align-items: center; gap: 10px; color: #92400e; font-weight: 600; font-size: 14px;">
                    <span>ℹ️</span>
                    <span>Note: The following fields are NOT translated to Tamil (dates, IDs, numbers):</span>
                </div>
                <div style="margin-top: 8px; color: #b45309; font-size: 13px;">
                    <strong>LSR Date</strong> &nbsp;•&nbsp; <strong>Application Number</strong>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

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