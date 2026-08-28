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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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
# ROYAL PREMIUM TECH AI COLOR PALETTE & UI STYLING
# Background: Deep Imperial Space Navy (#050811 / #0A1128)
# Accents: Electric Gold (#FFD700 / #D4AF37), Tech Cloud Blue (#38BDF8)
# Text & Containers: Soft Cloud White (#F8FAFC), Translucent Obsidian Glass
# ============================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* ---------- Alpine Lake Natural Theme ---------- */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.stApp {
    background: linear-gradient(180deg, #0A192F 0%, #06111E 50%, #030810 100%) !important;
    background-attachment: fixed !important;
    color: #F0F9FF !important;
}

[data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: transparent !important;
}

.main .block-container {
    max-width: 1280px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* ---------- Top Navigation Glass Header ---------- */
.top-nav {
    background: rgba(10, 25, 47, 0.85) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(14, 165, 169, 0.3) !important;
    border-radius: 20px;
    padding: 16px 32px;
    margin-bottom: 32px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.top-nav-brand {
    display: flex;
    align-items: center;
    gap: 16px;
}
.top-nav-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
    background: linear-gradient(135deg, #0EA5A9 0%, #0D9488 100%);
    color: #FFFFFF;
    font-size: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px rgba(14, 165, 169, 0.4);
    font-weight: 800;
}
.top-nav-title {
    font-size: 22px;
    font-weight: 800;
    color: #FFFFFF;
    letter-spacing: -0.3px;
}
.top-nav-subtitle {
    color: #2DD4BF;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.top-nav-links {
    display: flex;
    gap: 12px;
}
.top-nav-link {
    padding: 10px 20px;
    border-radius: 12px;
    background: rgba(15, 32, 59, 0.6);
    color: #94A3B8;
    font-size: 13px;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.top-nav-link:hover {
    background: rgba(14, 165, 169, 0.15);
    color: #2DD4BF;
    border-color: rgba(45, 212, 191, 0.4);
}
.top-nav-link.active {
    background: linear-gradient(135deg, #14B8A6 0%, #0F766E 100%);
    color: #FFFFFF;
    font-weight: 700;
    box-shadow: 0 4px 20px rgba(20, 184, 166, 0.35);
}

/* ---------- AI Hero Interface Card ---------- */
.hero {
    position: relative;
    background: radial-gradient(100% 100% at 80% 20%, rgba(14, 165, 169, 0.25) 0%, rgba(10, 25, 47, 0.9) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(45, 212, 191, 0.3);
    border-radius: 28px;
    padding: 44px 48px;
    margin-bottom: 36px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.15);
    overflow: hidden;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(45, 212, 191, 0.12);
    color: #2DD4BF;
    border: 1px solid rgba(45, 212, 191, 0.35);
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.2px;
    margin-bottom: 18px;
    text-transform: uppercase;
}
.hero-title {
    font-size: 38px;
    line-height: 1.2;
    font-weight: 800;
    color: #FFFFFF;
    margin: 0;
    letter-spacing: -0.8px;
}
.hero-title span {
    background: linear-gradient(135deg, #CCFBF1 0%, #2DD4BF 50%, #0EA5A9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-description {
    color: #CBD5E1;
    font-size: 16px;
    line-height: 1.7;
    max-width: 780px;
    margin-top: 16px;
    font-weight: 400;
}

/* ---------- Typography & Section Headers ---------- */
.section-title {
    font-size: 22px;
    font-weight: 700;
    color: #FFFFFF;
    margin-top: 36px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
    letter-spacing: -0.3px;
}
.section-title::before {
    content: '';
    width: 4px;
    height: 24px;
    background: linear-gradient(180deg, #2DD4BF 0%, #0F766E 100%);
    border-radius: 4px;
    box-shadow: 0 0 10px rgba(45, 212, 191, 0.4);
}
.section-subtitle {
    color: #94A3B8;
    font-size: 13px;
    margin-bottom: 24px;
    margin-left: 16px;
    font-weight: 400;
}

/* ---------- CALM ICE-TURQUOISE FILE UPLOADER (SOLID BLACK TEXT) ---------- */
div[data-testid="stFileUploader"] {
    background: rgba(204, 251, 241, 0.95) !important;
    border: 2px dashed #0D9488 !important;
    border-radius: 20px !important;
    padding: 28px !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: #0F766E !important;
    background: rgba(240, 253, 250, 0.98) !important;
    box-shadow: 0 12px 35px rgba(13, 148, 136, 0.25) !important;
}

/* FORCE ALL UPLOADER TEXT TO PURE BLACK */
div[data-testid="stFileUploader"] *,
div[data-testid="stFileUploader"] span, 
div[data-testid="stFileUploader"] label,
div[data-testid="stFileUploader"] p,
div[data-testid="stFileUploader"] div,
div[data-testid="stFileUploader"] small {
    color: #000000 !important;
    font-weight: 700 !important;
}

/* "Browse files" Button with high contrast */
div[data-testid="stFileUploader"] button {
    background: #0D9488 !important;
    color: #FFFFFF !important;
    border: 1px solid #0F766E !important;
    border-radius: 12px !important;
    padding: 8px 22px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3) !important;
}

div[data-testid="stFileUploader"] button * {
    color: #FFFFFF !important;
}

div[data-testid="stFileUploader"] button:hover {
    background: #0F766E !important;
    border-color: #115E59 !important;
    box-shadow: 0 6px 16px rgba(15, 118, 110, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* ---------- Action Button ---------- */
.stButton > button {
    width: 100%;
    border-radius: 16px;
    min-height: 56px;
    border: none;
    background: linear-gradient(135deg, #14B8A6 0%, #0D9488 50%, #0F766E 100%);
    color: #FFFFFF;
    font-weight: 800;
    font-size: 16px;
    letter-spacing: 0.3px;
    box-shadow: 0 8px 25px -5px rgba(20, 184, 166, 0.4);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 32px 0 rgba(20, 184, 166, 0.6);
    background: linear-gradient(135deg, #2DD4BF 0%, #14B8A6 50%, #0D9488 100%);
    color: #FFFFFF;
}

/* ---------- Structured Glass File Card ---------- */
.file-card {
    background: rgba(15, 32, 59, 0.85);
    border: 1px solid rgba(45, 212, 191, 0.3);
    border-radius: 20px;
    padding: 20px 28px;
    margin: 20px 0;
    display: flex;
    align-items: center;
    gap: 18px;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}
.file-icon {
    width: 52px;
    height: 52px;
    border-radius: 16px;
    background: rgba(45, 212, 191, 0.15);
    color: #2DD4BF;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    border: 1px solid rgba(45, 212, 191, 0.4);
}
.file-name {
    font-weight: 700;
    color: #FFFFFF;
    font-size: 16px;
}
.file-info {
    color: #94A3B8;
    font-size: 13px;
    margin-top: 4px;
}

/* ---------- High-Contrast Bilingual Cards ---------- */
.bilingual-card {
    background: rgba(10, 25, 47, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 20px;
    padding: 24px;
    min-height: 140px;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    margin-bottom: 20px;
    transition: all 0.3s ease;
}
.bilingual-card:hover {
    border-color: rgba(45, 212, 191, 0.5);
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6);
    transform: translateY(-2px);
}
.bilingual-label {
    color: #2DD4BF;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 16px;
}
.bilingual-row {
    display: flex;
    gap: 0;
    align-items: stretch;
}
.bilingual-col {
    flex: 1;
    min-width: 0;
    padding: 0 18px;
}
.bilingual-col:first-child {
    padding-left: 0;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
.bilingual-col:last-child {
    padding-right: 0;
}
.bilingual-col-title {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
}
.bilingual-value {
    color: #F0F9FF;
    font-size: 15px;
    font-weight: 600;
    line-height: 1.6;
    word-break: break-word;
}
.bilingual-value.tamil {
    color: #34D399;
    font-weight: 500;
}
.bilingual-value.empty {
    color: #64748B;
    font-weight: 400;
    font-style: italic;
}

/* ---------- Property Description Card ---------- */
.property-bilingual {
    background: rgba(10, 25, 47, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 22px;
    padding: 30px;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    transition: all 0.3s ease;
}
.property-bilingual:hover {
    border-color: rgba(45, 212, 191, 0.5);
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
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}
.property-bilingual-col:last-child {
    padding-right: 0;
}
.property-bilingual-title {
    color: #2DD4BF;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 16px;
    padding-bottom: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.property-bilingual-text {
    color: #F0F9FF;
    font-size: 15px;
    line-height: 1.8;
    word-break: break-word;
    white-space: pre-wrap;
}
.property-bilingual-text.tamil {
    color: #34D399;
}
.property-bilingual-text.empty {
    color: #64748B;
    font-weight: 400;
    font-style: italic;
}

/* ---------- Stat Metrics ---------- */
.metric-card {
    background: rgba(10, 25, 47, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 24px;
    text-align: center;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(45, 212, 191, 0.4);
}
.metric-number {
    font-size: 32px;
    font-weight: 800;
    background: linear-gradient(135deg, #CCFBF1 0%, #2DD4BF 50%, #0EA5A9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label {
    color: #94A3B8;
    font-size: 12px;
    margin-top: 6px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ---------- Tables & Native Components ---------- */
.doc-table-title {
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 16px;
    margin-top: 24px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.doc-table-title::before {
    content: '';
    width: 3px;
    height: 18px;
    background: #2DD4BF;
    border-radius: 3px;
}
.stDataFrame {
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 16px;
    overflow: hidden;
    background: rgba(10, 25, 47, 0.7);
}

button[data-baseweb="tab"] {
    color: #94A3B8 !important;
    background-color: transparent !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 12px 20px !important;
}
button[aria-selected="true"] {
    color: #2DD4BF !important;
    border-bottom-color: #2DD4BF !important;
}

.footer {
    text-align: center;
    color: #64748B;
    font-size: 13px;
    padding: 48px 0 20px 0;
    font-weight: 500;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ============================================================
# TOP NAVIGATION
# ============================================================

st.markdown(
    """<div class="top-nav">
        <div class="top-nav-brand">
            <div class="top-nav-icon">📄</div>
            <div>
                <div class="top-nav-title">LSR Intelligence</div>
                <div class="top-nav-subtitle">Next-Gen Document Extraction AI</div>
            </div>
        </div>
        <div class="top-nav-links">
            <a href="#" class="top-nav-link active">Document Extraction</a>
            <a href="#" class="top-nav-link">About System</a>
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


def reorder_property_description(text: str) -> str:
    """Reorder property description to show address first, then boundaries/extent."""
    if not text:
        return text

    lines = text.strip().split('\n')

    address_lines = []
    survey_lines = []
    extent_lines = []
    boundary_lines = []
    other_lines = []

    boundary_keywords = ['north:', 'south:', 'east:', 'west:', 'north ', 'south ', 'east ', 'west ']
    extent_keywords = ['measuring', 'extent', 'area', 'sq.ft', 'sq ft', 'acre', 'hectare', 'cent', 'ground']
    survey_keywords = ['survey', 'khewat', 'khatoni', 'khata', 'plot no', 'plot number', 'door no', 'door number']
    address_keywords = ['situated', 'located', 'at ', 'address', 'road', 'street', 'village', 'town', 'city', 'district', 'pincode', 'pin code', 'chennai', 'main road']
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
            boundary_lines.insert(0, line)
        else:
            other_lines.append(line)

    reordered = []
    reordered.extend(address_lines)
    reordered.extend(survey_lines)
    reordered.extend(extent_lines)
    reordered.extend(boundary_lines)
    reordered.extend(other_lines)

    return '\n'.join(reordered) if reordered else text


# ============================================================
# TAMIL FONT REGISTRATION (Nirmala UI - Windows built-in)
# ============================================================
try:
    pdfmetrics.registerFont(TTFont('Nirmala', r'C:\Windows\Fonts\Nirmala.ttc', subfontIndex=0))
    pdfmetrics.registerFontFamily('Nirmala', normal='Nirmala', bold='Nirmala', italic='Nirmala', boldItalic='Nirmala')
    TAMIL_FONT_AVAILABLE = True
except Exception as e:
    print(f"[WARN] Could not register Nirmala Tamil font: {e}")
    TAMIL_FONT_AVAILABLE = False


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

    tamil_font_name = 'Nirmala' if TAMIL_FONT_AVAILABLE else 'Helvetica'

    tamil_value_style = ParagraphStyle(
        'TamilValue',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        textColor=HexColor('#059669'),
        fontName=tamil_font_name,
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

    story.append(Paragraph("LSR Document Intelligence", title_style))
    story.append(Paragraph("Extracted Information Report", subtitle_style))
    story.append(Spacer(1, 0.2*inch))

    fields = result.get("extracted_fields", {})
    translated_fields = result.get("translated_fields", {})
    processing_time = result.get("processing_time_seconds")
    filename = result.get("filename", "Unknown")

    NO_TRANSLATE_FIELDS_PDF = {"lsr_date", "application_number"}

    def add_bilingual_field(label, eng_value, tam_value, field_name=None):
        story.append(Paragraph(label, field_label_style))
        if eng_value and str(eng_value).strip() not in ["Not found", "—", "None", ""]:
            story.append(Paragraph(f"English: {eng_value}", field_value_style))
            if (tam_value and str(tam_value).strip() not in ["—", "None", ""] and
                (field_name is None or field_name not in NO_TRANSLATE_FIELDS_PDF) and
                tam_value != eng_value):
                story.append(Paragraph(f"தமிழ்: {tam_value}", tamil_value_style))
        else:
            story.append(Paragraph("Not found", empty_style))
        story.append(Spacer(1, 0.05*inch))

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
        add_bilingual_field(label, value, tamil_value, field_name)

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

    def create_document_table(documents, title, header_color):
        if not documents:
            return None

        story.append(Paragraph(title, section_style))

        headers = ["Deed Name", "Doc No.", "Date", "Mode", "Additional Details"]
        doc_data = [headers]

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

        available_width = 6.5 * inch
        min_widths = [1.2*inch, 0.8*inch, 0.8*inch, 0.7*inch, 1.5*inch]
        total_min = sum(min_widths)

        if total_min > available_width:
            scale = available_width / total_min
            col_widths = [w * scale for w in min_widths]
        else:
            extra = available_width - total_min
            total_content = sum(col_max_lengths)
            if total_content > 0:
                col_widths = [
                    min_widths[i] + (extra * col_max_lengths[i] / total_content)
                    for i in range(5)
                ]
            else:
                col_widths = min_widths

        wrapped_data = []
        for row_idx, row in enumerate(doc_data):
            wrapped_row = []
            for col_idx, cell_text in enumerate(row):
                if row_idx == 0:
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
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))
        story.append(table)

    prior_docs = result.get("documents_prior_to_disbursal", [])
    create_document_table(prior_docs, "📋 Documents Prior to Disbursal", HexColor('#1e293b'))

    post_docs = result.get("documents_post_disbursal", [])
    if post_docs:
        story.append(Spacer(1, 0.15*inch))
        create_document_table(post_docs, "📋 Documents Post Disbursal", HexColor('#0284c7'))

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

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Document Extraction"

if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False

if st.session_state["current_page"] == "Document Extraction":
    st.markdown(
        """<div class="hero">
            <div class="hero-badge">⚡ NEXT-GEN INTELLIGENCE ENGINE</div>
            <div class="hero-title">Automated LSR Data <span>Extraction System.</span></div>
            <div class="hero-description">
                Transform complex legal property reports into structured bilingual data. Powered by DocTR character recognition and neural language parsing.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Upload Legal Document</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Supported formats: PDF, JPG, JPEG, PNG, TIFF</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose your LSR document",
        type=["pdf", "jpg", "jpeg", "png", "tif", "tiff"],
        label_visibility="collapsed",
    )

    extract_clicked = False

    if uploaded_file:
        file_size_kb = len(uploaded_file.getvalue()) / 1024
        extension = Path(uploaded_file.name).suffix.upper().replace(".", "")

        st.markdown(
            f"""<div class="file-card">
                <div class="file-icon">📄</div>
                <div>
                    <div class="file-name">{uploaded_file.name}</div>
                    <div class="file-info">{extension} Document &nbsp;•&nbsp; {file_size_kb:.1f} KB</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        extract_clicked = st.button("✨ Execute AI Extraction", use_container_width=True, key="extract_btn")

    if extract_clicked and uploaded_file:
        st.session_state["is_processing"] = True
        st.session_state["pending_file"] = {
            "name": uploaded_file.name,
            "content": uploaded_file.getvalue(),
            "type": uploaded_file.type,
        }
        st.rerun()

    if st.session_state.get("is_processing", False) and "pending_file" in st.session_state:
        pending_file = st.session_state["pending_file"]

        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            import time as _time

            status_text.text("🔍 Step 1/3: Ingesting file payload...")
            progress_bar.progress(10)
            _time.sleep(0.5)

            status_text.text("📄 Step 2/3: Executing OCR matrix scan...")
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

            status_text.text("🧠 Step 3/3: Running LLM entity parsing & translation...")
            progress_bar.progress(90)

            if response.status_code == 200:
                st.session_state["extraction_result"] = response.json()
                st.session_state["is_processing"] = False
                del st.session_state["pending_file"]
                progress_bar.progress(100)
                status_text.text("")
                st.success("Analysis Complete!")
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
            st.error("Unable to connect to backend server. Verify API service status.")
        except requests.exceptions.Timeout:
            st.session_state["is_processing"] = False
            del st.session_state["pending_file"]
            progress_bar.progress(0)
            status_text.text("")
            st.error("Processing request timed out. Please try again.")
        except Exception as exc:
            st.session_state["is_processing"] = False
            del st.session_state["pending_file"]
            progress_bar.progress(0)
            status_text.text("")
            st.error(f"Unexpected error: {exc}")

    if "extraction_result" in st.session_state and not st.session_state.get("is_processing", False):
        result = st.session_state["extraction_result"]
        fields = result.get("extracted_fields", {})
        translated_fields = result.get("translated_fields", {})
        processing_time = result.get("processing_time_seconds")
        filename = result.get("filename", "Unknown")

        st.markdown('<div class="section-title">Extracted Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Selectable English and Tamil structured output fields</div>', unsafe_allow_html=True)

        metric1, metric2, metric3 = st.columns(3)

        found_count = sum(1 for value in fields.values() if value not in [None, "", [], {}])

        with metric1:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-number">{found_count}</div>
                    <div class="metric-label">Fields Identified</div>
                </div>""",
                unsafe_allow_html=True,
            )

        with metric2:
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-number">{len(fields)}</div>
                    <div class="metric-label">Target Schema</div>
                </div>""",
                unsafe_allow_html=True,
            )

        with metric3:
            time_display = f"{processing_time:.1f}s" if processing_time is not None else "N/A"
            st.markdown(
                f"""<div class="metric-card">
                    <div class="metric-number">{time_display}</div>
                    <div class="metric-label">Execution Time</div>
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("### 📋 Primary Attributes")

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
                tamil_value = translated_fields.get(field_name)

                if isinstance(value, list):
                    value = ", ".join(str(item) for item in value)

                card_html = render_bilingual_field(label, value, tamil_value)

                if index == 0:
                    col1.markdown(card_html, unsafe_allow_html=True)
                else:
                    col2.markdown(card_html, unsafe_allow_html=True)

        st.markdown("### 🏠 Legal Property Boundaries & Description")
        property_description = fields.get("property_description")
        property_tamil = translated_fields.get("property_description")

        if property_description:
            reordered_eng = reorder_property_description(property_description)
            reordered_tam = reorder_property_description(property_tamil) if property_tamil else ""

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

        pdf_filename = f"LSR_Report_{Path(filename).stem}_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"

        def generate_pdf_for_download():
            return generate_pdf_report(result)

        pdf_bytes = generate_pdf_report(result)

        st.markdown("<div style='text-align: center; margin: 36px 0 20px 0;'>", unsafe_allow_html=True)
        st.download_button(
            label="📥 Export PDF Analysis Report",
            data=pdf_bytes,
            file_name=f"{pdf_filename}.pdf",
            mime="application/pdf",
            use_container_width=False,
            type="primary",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="section-title">📑 Associated Documents</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Catalog of disbursal documentation mapped from scan</div>', unsafe_allow_html=True)

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

        with st.expander("🔍 Inspection & Developer JSON Output"):
            st.json(result)

        st.markdown(
            """<div class="footer">
                LSR Intelligence Hub &nbsp;•&nbsp; Enterprise OCR & AI Platform
            </div>""",
            unsafe_allow_html=True,
        )

elif st.session_state["current_page"] == "About":
    st.markdown(
        """<div class="hero">
            <div class="hero-badge">ARCHITECTURAL OVERVIEW</div>
            <div class="hero-title">LSR Document <span>Intelligence Hub</span></div>
            <div class="hero-description">
                High-performance document processing pipeline optimized for parsing legal titles and property documentation.
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔍 DocTR OCR Engine\nPerforms character recognition and spatial block text extraction.")

    with col2:
        st.markdown("### 🧠 LLM Neural Gateway\nExtracts target schema fields and renders language translations.")

    with col3:
        st.markdown("### ⚡ Fast API Core\nAsynchronous REST backend handling data verification and PDF rendering.")

    st.markdown("---")
    st.markdown("### 📌 Schematized Output Fields")
    st.write(
        """
        - LSR Date & Company Name
        - Applicant & Co-Applicant Info
        - Property Ownership Details
        - Unique Application Numbers
        - Property Description & Boundaries
        - Prior/Post Disbursal Documentation Schedules
        """
    )