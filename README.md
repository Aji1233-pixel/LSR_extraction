# 📄 LSR Document Intelligence

An AI-powered document intelligence system for extracting structured information from **LSR (Legal Scrutiny Report)** documents.

The application combines **DocTR OCR**, **FastAPI**, **Streamlit**, **LLM-based information extraction**, **validation**, **Tamil translation**, and **PDF report generation** to automatically process legal property documents.

---

## 🚀 Features

### 🔍 Document Processing

- Upload LSR documents in supported formats:
  - PDF
  - JPG
  - JPEG
  - PNG
  - TIFF
- Extract text using **DocTR OCR**
- Process legal/property documents automatically
- Validate uploaded files
- Handle empty and invalid documents gracefully

### 🤖 AI-Powered Information Extraction

The application uses an LLM to extract structured information from OCR text.

Currently, the system is designed around API-based LLM processing and uses **FreeLLMAPI** in the existing implementation.

The project architecture is being prepared for future support for multiple LLM providers such as:

- FreeLLM
- OpenAI
- Google Gemini
- Other future providers

The goal is to keep the extraction pipeline independent of the selected LLM provider.

---

## 📋 Extracted Information

The application extracts important LSR information, including:

| Field | Description |
|---|---|
| LSR Date | Date of the Legal Scrutiny Report |
| Company Name | Financial institution/company name |
| Application Number | Loan/application reference number |
| Applicant Name | Primary applicant |
| Co-Applicant Name | Co-applicant details |
| Property Owner | Owner(s) of the property |
| Property Description | Complete property details |

---

## 🏠 Property Description Processing

The application processes and displays property information in a more readable structure.

Property details may include:

- Address/location
- Village/town/city/district information
- Survey number
- Plot number
- Door number
- Khewat/Khatoni/Khata information where available
- Land/building extent
- Measurements
- Area
- Boundaries

Boundary information may include:

- North
- South
- East
- West

The property description can be reordered for improved readability:

```text
Address / Location
        ↓
Survey / Property Identification Details
        ↓
Extent / Measurements
        ↓
Boundaries
        ↓
Other Relevant Details
