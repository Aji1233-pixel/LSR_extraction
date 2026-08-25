import sys
from pathlib import Path
import requests
import streamlit as st
import base64
from io import BytesIO
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
<<<<<<< HEAD
# HELPER FUNCTIONS
# ============================================================

def format_field_value(val: str | list | None, default_text: str) -> str:
    """Formats raw values into readable string representations."""
    if val in (None, "", [], {}):
        return default_text
    if isinstance(val, list):
        return ", ".join(map(str, val))
    return str(val)

=======
# CUSTOM CSS - PREMIUM UI
# ============================================================

CUSTOM_CSS = """
<style>
/* ---------- Global ---------- */
.stApp {
    background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
}
.main .block-container {
    max-width: 1300px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* ---------- Top Navigation Bar ---------- */
.top-nav {
    background: #ffffff;
    border-radius: 18px;
    padding: 16px 28px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.top-nav-brand {
    display: flex;
    align-items: center;
    gap: 14px;
}
.top-nav-icon {
    width: 44px;
    height: 44px;
    border-radius: 13px;
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    color: white;
    font-size: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 6px 16px rgba(79, 70, 229, 0.25);
}
.top-nav-title {
    font-size: 19px;
    font-weight: 800;
    color: #1e293b;
    letter-spacing: -0.3px;
}
.top-nav-subtitle {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 1px;
}
.top-nav-links {
    display: flex;
    gap: 8px;
}
.top-nav-link {
    padding: 8px 16px;
    border-radius: 10px;
    background: #f1f5f9;
    color: #64748b;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
}
.top-nav-link:hover {
    background: #e2e8f0;
    color: #334155;
}
.top-nav-link.active {
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    color: white;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}

/* ---------- Hero ---------- */
.hero {
    background: linear-gradient(135deg, #eef2ff 0%, #ffffff 50%, #ecfeff 100%);
    border: 1px solid #e0e7ff;
    border-radius: 24px;
    padding: 36px 40px;
    margin-bottom: 28px;
    box-shadow: 0 8px 30px rgba(15, 23, 42, 0.03);
}
.hero-badge {
    display: inline-block;
    background: #e0e7ff;
    color: #4338ca;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    margin-bottom: 16px;
}
.hero-title {
    font-size: 34px;
    line-height: 1.2;
    font-weight: 800;
    color: #1e293b;
    margin: 0;
    letter-spacing: -0.5px;
}
.hero-title span {
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-description {
    color: #64748b;
    font-size: 15px;
    line-height: 1.7;
    max-width: 720px;
    margin-top: 14px;
}

/* ---------- Typography & Sections ---------- */
.section-title {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    margin-top: 32px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-title::before {
    content: '';
    width: 4px;
    height: 22px;
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    border-radius: 4px;
}
.section-subtitle {
    color: #94a3b8;
    font-size: 13px;
    margin-bottom: 20px;
    margin-left: 14px;
}

/* ---------- Upload Area ---------- */
div[data-testid="stFileUploader"] {
    background: white;
    border: 2px dashed #c7d2fe;
    border-radius: 18px;
    padding: 12px;
    transition: all 0.2s ease;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #6366f1;
    background: #fafaff;
}

/* ---------- Buttons ---------- */
.stButton > button {
    width: 100%;
    border-radius: 12px;
    min-height: 50px;
    border: none;
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    color: white;
    font-weight: 700;
    font-size: 15px;
    box-shadow: 0 6px 18px rgba(79, 70, 229, 0.22);
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 26px rgba(79, 70, 229, 0.3);
}

/* ---------- Cards ---------- */
.file-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px;
    margin: 18px 0;
    display: flex;
    align-items: center;
    gap: 15px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
}
.file-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: #eef2ff;
    color: #4f46e5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 23px;
}
.file-name {
    font-weight: 700;
    color: #1e293b;
    font-size: 14px;
}
.file-info {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 3px;
}

/* ---------- Bilingual Cards ---------- */
.bilingual-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px;
    min-height: 135px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
    margin-bottom: 16px;
    transition: all 0.2s ease;
}
.bilingual-card:hover {
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
    border-color: #c7d2fe;
}
.bilingual-label {
    color: #64748b;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 14px;
}
.bilingual-row {
    display: flex;
    gap: 0;
    align-items: stretch;
}
.bilingual-col {
    flex: 1;
    min-width: 0;
    padding: 0 16px;
}
.bilingual-col:first-child {
    padding-left: 0;
    border-right: 1px solid #f1f5f9;
}
.bilingual-col:last-child {
    padding-right: 0;
}
.bilingual-col-title {
    color: #94a3b8;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}
.bilingual-value {
    color: #1e293b;
    font-size: 15px;
    font-weight: 600;
    line-height: 1.6;
    word-break: break-word;
    user-select: text;
    cursor: text;
}
.bilingual-value.tamil {
    color: #059669;
    font-weight: 500;
}
.bilingual-value.empty {
    color: #cbd5e1;
    font-weight: 400;
    font-style: italic;
}

/* ---------- Property Description Bilingual ---------- */
.property-bilingual {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 26px;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
    transition: all 0.2s ease;
}
.property-bilingual:hover {
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
}
.property-bilingual-row {
    display: flex;
    gap: 0;
    align-items: stretch;
}
.property-bilingual-col {
    flex: 1;
    min-width: 0;
    padding: 0 24px;
}
.property-bilingual-col:first-child {
    padding-left: 0;
    border-right: 2px solid #f1f5f9;
}
.property-bilingual-col:last-child {
    padding-right: 0;
}
.property-bilingual-title {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #f1f5f9;
}
.property-bilingual-text {
    color: #1e293b;
    font-size: 14px;
    line-height: 1.9;
    word-break: break-word;
    white-space: pre-wrap;
    user-select: text;
    cursor: text;
}
.property-bilingual-text.tamil {
    color: #059669;
}
.property-bilingual-text.empty {
    color: #cbd5e1;
    font-weight: 400;
    font-style: italic;
}

/* ---------- Document Tables ---------- */
.doc-table-title {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 12px;
    margin-top: 22px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.doc-table-title::before {
    content: '';
    width: 3px;
    height: 16px;
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    border-radius: 3px;
}
.stDataFrame {
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
}

/* ---------- Metrics ---------- */
.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
    transition: all 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
}
.metric-number {
    font-size: 26px;
    font-weight: 800;
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label {
    color: #94a3b8;
    font-size: 12px;
    margin-top: 6px;
    font-weight: 600;
}

/* ---------- Footer ---------- */
.footer {
    text-align: center;
    color: #94a3b8;
    font-size: 12px;
    padding: 36px 0 12px 0;
}

/* ---------- Processing Spinner ---------- */
.processing-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(248, 250, 252, 0.85);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}
.processing-card {
    background: white;
    border-radius: 24px;
    padding: 40px 50px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(15, 23, 42, 0.1);
    max-width: 380px;
}
.processing-spinner {
    width: 56px;
    height: 56px;
    border: 4px solid #e0e7ff;
    border-top-color: #4f46e5;
    border-radius: 50%;
    margin: 0 auto 20px;
    animation: spin 0.8s linear infinite;
}
@keyframes spin {
    to { transform: rotate(360deg); }
}
.processing-title {
    font-size: 18px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 8px;
}
.processing-step {
    color: #64748b;
    font-size: 13px;
    line-height: 1.6;
}
.processing-step-item {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 6px 0;
    color: #94a3b8;
    font-size: 13px;
    transition: color 0.3s ease;
}
.processing-step-item.active {
    color: #4f46e5;
    font-weight: 600;
}
.processing-step-icon {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #e0e7ff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: white;
}
.processing-step-icon.active {
    background: linear-gradient(135deg, #4f46e5, #06b6d4);
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

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
# TOP NAVIGATION (replaces sidebar)
# ============================================================

<<<<<<< HEAD
with st.sidebar:
    st.title("📄 LSR Intelligence")
    st.caption("Document Extraction System")
    st.divider()
=======
st.markdown(
    """<div class="top-nav">
        <div class="top-nav-brand">
            <div class="top-nav-icon">📄</div>
            <div>
                <div class="top-nav-title">LSR Intelligence</div>
                <div class="top-nav-subtitle">Document Extraction System</div>
            </div>
        </div>
        <div class="top-nav-links">
            <a href="#" class="top-nav-link active">Document Extraction</a>
            <a href="#" class="top-nav-link">About</a>
        </div>
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

>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

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
<<<<<<< HEAD
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
=======

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
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

# ============================================================
# MAIN CONTENT: DOCUMENT EXTRACTION
# ============================================================

<<<<<<< HEAD
if page == "Document Extraction":
    st.title("Extract LSR Information Automatically")
    st.caption("Upload a legal property document to extract key details using OCR and AI.")
    st.divider()
=======
# Page state in session
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Document Extraction"

# Track processing state
if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False

if st.session_state["current_page"] == "Document Extraction":
    st.markdown(
        """<div class="hero">
            <div class="hero-badge">AI-POWERED DOCUMENT ANALYSIS</div>
            <div class="hero-title">Extract LSR information <span>automatically.</span></div>
            <div class="hero-description">
                Upload a legal property document and let our document intelligence pipeline
                extract important information automatically using OCR and FreeLLMAPI.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # File Upload Header
    st.markdown('<div class="section-title">Upload Document</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Supported formats: PDF, JPG, JPEG, PNG, TIFF</div>', unsafe_allow_html=True)
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

    st.subheader("Upload Document")
    uploaded_file = st.file_uploader(
        "Supported formats: PDF, JPG, JPEG, PNG, TIFF",
        type=["pdf", "jpg", "jpeg", "png", "tif", "tiff"],
    )

    extract_clicked = False

    if uploaded_file:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        extension = Path(uploaded_file.name).suffix.upper().replace(".", "")

        with st.container(border=True):
            st.write(f"**Selected File:** {uploaded_file.name}")
            st.caption(f"Format: {extension} | Size: {file_size_kb:.1f} KB")

<<<<<<< HEAD
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
=======
        extract_clicked = st.button("✨ Extract Information", use_container_width=True, key="extract_btn")

    # Handle extraction when button is clicked
    if extract_clicked and uploaded_file:
        st.session_state["is_processing"] = True
        st.session_state["pending_file"] = {
            "name": uploaded_file.name,
            "content": uploaded_file.getvalue(),
            "type": uploaded_file.type,
        }
        st.rerun()

    # Process the file if marked for processing
    if st.session_state.get("is_processing", False) and "pending_file" in st.session_state:
        pending_file = st.session_state["pending_file"]

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            import time as _time

            status_text.text("🔍 Step 1/3: Reading document...")
            progress_bar.progress(10)
            _time.sleep(0.5)

            status_text.text("📄 Step 2/3: Extracting text with DocTR OCR...")
            progress_bar.progress(30)

            response = requests.post(
                API_URL,
                files={
                    "file": (
                        pending_file["name"],
                        pending_file["content"],
                        pending_file["type"],
                    )
                },
                timeout=600,
            )

            status_text.text("🧠 Step 3/3: Analyzing with AI & translating...")
            progress_bar.progress(90)

            if response.status_code == 200:
                st.session_state["extraction_result"] = response.json()
                st.session_state["is_processing"] = False
                del st.session_state["pending_file"]
                progress_bar.progress(100)
                status_text.text("")
                st.success("Document processed successfully!")
                st.rerun()
            else:
                st.session_state["is_processing"] = False
                del st.session_state["pending_file"]
                progress_bar.progress(0)
                status_text.text("")
                try:
                    error_message = response.json().get("detail", "Unknown server error.")
                except Exception:
                    error_message = response.text
                st.error(f"Extraction failed: {error_message}")

        except requests.exceptions.ConnectionError:
            st.session_state["is_processing"] = False
            del st.session_state["pending_file"]
            progress_bar.progress(0)
            status_text.text("")
            st.error("Unable to connect to the FastAPI server. Make sure the backend is running.")
        except requests.exceptions.Timeout:
            st.session_state["is_processing"] = False
            del st.session_state["pending_file"]
            progress_bar.progress(0)
            status_text.text("")
            st.error("The document processing took too long. Please try again.")
        except Exception as exc:
            st.session_state["is_processing"] = False
            del st.session_state["pending_file"]
            progress_bar.progress(0)
            status_text.text("")
            st.error(f"Unexpected error: {exc}")
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

    # Display Results
    if "extraction_result" in st.session_state and not st.session_state.get("is_processing", False):
        result = st.session_state["extraction_result"]
        fields = result.get("extracted_fields", {})
        translated_fields = result.get("translated_fields", {})
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

<<<<<<< HEAD
        st.divider()
        st.subheader("📊 Extracted Information")
=======
        st.markdown('<div class="section-title">Extracted Information</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Information identified from the uploaded document (English | Tamil) — text is selectable for copying</div>', unsafe_allow_html=True)
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

        # Top Metrics Section
        found_count = sum(1 for val in fields.values() if val not in (None, "", [], {}))
        time_display = f"{processing_time:.1f}s" if processing_time else "N/A"

<<<<<<< HEAD
        m1, m2, m3 = st.columns(3)
        m1.metric("Fields Extracted", found_count)
        m2.metric("Required Fields", len(fields))
        m3.metric("Processing Time", time_display)
        st.divider()
=======
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

        # ========================================================
        # BASIC INFORMATION - Side by Side English/Tamil
        # ========================================================
        st.markdown("### 📋 Basic Information")
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

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
<<<<<<< HEAD
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
=======
            row_fields = basic_fields[row_start : row_start + 2]

            for index, (field_name, label) in enumerate(row_fields):
                value = fields.get(field_name)
                tamil_value = translated_fields.get(field_name)

                if isinstance(value, list):
                    value = ", ".join(str(item) for item in value)

                card_html = render_bilingual_field(label, value, tamil_value)

                if index == 0:
                    col1.markdown(card_html, unsafe_allow_html=True)
                else:
                    col2.markdown(card_html, unsafe_allow_html=True)

        # ========================================================
        # PROPERTY DESCRIPTION - Reordered (Address → Survey → Extent → Boundaries)
        # ========================================================
        st.markdown("### 🏠 Property Description")
        property_description = fields.get("property_description")
        property_tamil = translated_fields.get("property_description")

        # Reorder property description for better readability
        if property_description:
            reordered_eng = reorder_property_description(property_description)
            reordered_tam = reorder_property_description(property_tamil) if property_tamil else ""

            # Custom render for reordered property description
            st.markdown(
                f"""
                <div class="property-bilingual">
                    <div class="property-bilingual-row">
                        <div class="property-bilingual-col">
                            <div class="property-bilingual-title">English</div>
                            <div class="property-bilingual-text">{reordered_eng}</div>
                        </div>
                        <div class="property-bilingual-col">
                            <div class="property-bilingual-title">தமிழ் (Tamil)</div>
                            <div class="property-bilingual-text tamil">{reordered_tam if reordered_tam else '—'}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                render_property_bilingual(property_description, property_tamil),
                unsafe_allow_html=True,
            )

        # ========================================================
        # PDF DOWNLOAD BUTTON (using Streamlit's built-in download_button)
        # ========================================================
        pdf_filename = f"LSR_Report_{Path(filename).stem}_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Generate PDF on demand when download is clicked
        # We use a callback pattern to generate fresh PDF each time
        def generate_pdf_for_download():
            return generate_pdf_report(result)

        # Generate PDF now for the download button
        pdf_bytes = generate_pdf_report(result)

        st.markdown("<div style='text-align: center; margin: 32px 0 16px 0;'>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=f"{pdf_filename}.pdf",
            mime="application/pdf",
            use_container_width=False,
            type="primary",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # ========================================================
        # DOCUMENT TABLES
        # ========================================================

        st.markdown('<div class="section-title">📑 Documents</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Documents identified from the uploaded LSR document</div>', unsafe_allow_html=True)

        prior_docs = result.get("documents_prior_to_disbursal", [])
        post_docs = result.get("documents_post_disbursal", [])

        tab_prior, tab_post = st.tabs([
            "📋 Prior to Disbursal",
            "📋 Post Disbursal",
        ])

        with tab_prior:
            render_doc_table(prior_docs, "Documents Prior to Disbursal")

        with tab_post:
            render_doc_table(post_docs, "Documents Post Disbursal")

        # Raw JSON Section
        with st.expander("🔍 View Raw Extraction JSON"):
            st.json(result)

        # Footer
        st.markdown(
            """<div class="footer">
                LSR Document Intelligence &nbsp;•&nbsp; DocTR + FreeLLMAPI
            </div>""",
            unsafe_allow_html=True,
        )
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

# ============================================================
# ABOUT PAGE (hidden by default, accessible via nav)
# ============================================================
<<<<<<< HEAD

else:
    st.title("About LSR Document Intelligence")
    st.write("An automated extraction pipeline designed to process legal property reports.")
    st.divider()
=======
elif st.session_state["current_page"] == "About":
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
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216

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

<<<<<<< HEAD
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
=======
    with col2:
        st.markdown("### 🧠 FreeLLMAPI\nA cloud LLM gateway identifies the predefined fields from the extracted text.")

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
        - Property Description (with boundaries and extent)
        - Documents Prior to Disbursal (table with Deed Name, Doc No., Date, Mode)
        - Documents Post Disbursal (table with Deed Name, Doc No., Date, Mode)
        """
    )
>>>>>>> 29b7efe0f9ad3f96dadf6cc897634ca09cfe2216
