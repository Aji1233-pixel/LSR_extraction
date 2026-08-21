from fastapi import APIRouter, HTTPException, UploadFile
import time

from core.extraction.doctr_engine import DocTREngine
from core.llm.freellm_client import FreeLLMClient
from core.llm.field_extractor import FieldExtractor
from core.llm.document_extractor import DocumentExtractor
from core.validation.validator import DocumentValidator
from core.translation.translator import TamilTranslator


router = APIRouter(
    prefix="/api",
    tags=["Document Extraction"],
)


# ============================================================
# INITIALIZE COMPONENTS ONCE
# ============================================================

print("\n" + "=" * 60)
print("INITIALIZING LSR DOCUMENT EXTRACTION SYSTEM")
print("=" * 60)

# OCR
doctr_engine = DocTREngine()

# One shared FreeLLM client
freellm_client = FreeLLMClient()

# Basic field extraction
field_extractor = FieldExtractor(
    freellm_client
)

# Prior/Post disbursal document extraction
document_extractor = DocumentExtractor(
    freellm_client
)

# Validation
validator = DocumentValidator()

# Tamil translation
tamil_translator = TamilTranslator()

print("✅ LSR extraction components initialized")
print("=" * 60)
print()


# ============================================================
# EXTRACT DOCUMENT
# ============================================================

@router.post("/extract")
def extract_document(file: UploadFile):

    total_start = time.perf_counter()

    print("\n")
    print("╔" + "═" * 48 + "╗")
    print("║        DOCUMENT EXTRACTION REQUEST          ║")
    print("╚" + "═" * 48 + "╝")

    try:

        # ====================================================
        # 1. FILE READING
        # ====================================================

        file_start = time.perf_counter()

        file_bytes = file.file.read()

        file_time = (
            time.perf_counter()
            - file_start
        )

        print(
            f"⏱️ File reading: "
            f"{file_time:.2f} seconds"
        )

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        print(
            f"📄 Filename: {file.filename}"
        )

        print(
            f"📦 File size: "
            f"{len(file_bytes) / 1024:.2f} KB"
        )

        # ====================================================
        # 2. DOCTR OCR
        # ====================================================

        print("\n" + "=" * 50)
        print("🔍 DOCTR OCR STARTED")
        print("=" * 50)

        doctr_start = time.perf_counter()

        raw_text = doctr_engine.extract_text(
            file_bytes=file_bytes,
            filename=file.filename,
        )

        doctr_time = (
            time.perf_counter()
            - doctr_start
        )

        print(
            f"⏱️ DocTR OCR: "
            f"{doctr_time:.2f} seconds"
        )

        print(
            f"📝 OCR characters: "
            f"{len(raw_text)}"
        )

        print(
            f"📝 OCR words: "
            f"{len(raw_text.split())}"
        )

        if not raw_text or not raw_text.strip():
            raise HTTPException(
                status_code=422,
                detail=(
                    "No text could be extracted "
                    "from the uploaded document."
                )
            )

        # ====================================================
        # 3. BASIC FIELD EXTRACTION
        # ====================================================

        print("\n" + "=" * 50)
        print("📋 BASIC FIELD EXTRACTION")
        print("=" * 50)

        field_start = time.perf_counter()

        extracted_data = (
            field_extractor.extract_fields(
                raw_text
            )
        )

        field_time = (
            time.perf_counter()
            - field_start
        )

        print(
            f"⏱️ Basic field extraction: "
            f"{field_time:.2f} seconds"
        )

        # ====================================================
        # 4. DOCUMENT LIST EXTRACTION
        # ====================================================

        print("\n" + "=" * 50)
        print("📑 DOCUMENT LIST EXTRACTION")
        print("=" * 50)

        document_start = time.perf_counter()

        document_data = (
            document_extractor.extract_documents(
                raw_text
            )
        )

        document_time = (
            time.perf_counter()
            - document_start
        )

        print(
            f"⏱️ Document extraction: "
            f"{document_time:.2f} seconds"
        )

        # ====================================================
        # 5. VALIDATION
        # ====================================================

        print("\n" + "=" * 50)
        print("✅ VALIDATION")
        print("=" * 50)

        validation_start = time.perf_counter()

        final_result = validator.validate(
            extracted_data
        )

        validation_time = (
            time.perf_counter()
            - validation_start
        )

        print(
            f"⏱️ Validation: "
            f"{validation_time:.2f} seconds"
        )

        # ====================================================
        # 6. TAMIL TRANSLATION
        # ====================================================

        print("\n" + "=" * 50)
        print("🌐 TAMIL TRANSLATION")
        print("=" * 50)

        translation_start = time.perf_counter()

        translated_fields = {}

        # These should remain exactly as extracted.
        NO_TRANSLATE_FIELDS = {
            "lsr_date",
            "application_number",
        }

        for key, value in final_result.items():

            # ------------------------------------------------
            # Missing value
            # ------------------------------------------------

            if (
                value is None
                or str(value).strip() == ""
            ):
                translated_fields[key] = None
                continue

            # ------------------------------------------------
            # Date / application number
            # ------------------------------------------------

            if key in NO_TRANSLATE_FIELDS:
                translated_fields[key] = value
                continue

            # ------------------------------------------------
            # List value
            # ------------------------------------------------

            if isinstance(value, list):

                translated_values = []

                for item in value:

                    if item is None:
                        translated_values.append(None)
                        continue

                    try:
                        translated_values.append(
                            tamil_translator.translate(
                                str(item)
                            )
                        )

                    except Exception as exc:

                        print(
                            f"⚠️ Translation failed "
                            f"for {key}: {exc}"
                        )

                        translated_values.append(None)

                translated_fields[key] = (
                    translated_values
                )

                continue

            # ------------------------------------------------
            # Normal string
            # ------------------------------------------------

            try:

                translated_fields[key] = (
                    tamil_translator.translate(
                        str(value)
                    )
                )

            except Exception as exc:

                print(
                    f"⚠️ Translation failed "
                    f"for {key}: {exc}"
                )

                translated_fields[key] = None

        translation_time = (
            time.perf_counter()
            - translation_start
        )

        print(
            f"⏱️ Tamil translation: "
            f"{translation_time:.2f} seconds"
        )

        # ====================================================
        # 7. SAFE DOCUMENT RESULTS
        # ====================================================

        if not isinstance(document_data, dict):

            document_data = {
                "documents_prior_to_disbursal": [],
                "documents_post_disbursal": [],
            }

        prior_documents = document_data.get(
            "documents_prior_to_disbursal",
            []
        )

        post_documents = document_data.get(
            "documents_post_disbursal",
            []
        )

        if not isinstance(prior_documents, list):
            prior_documents = []

        if not isinstance(post_documents, list):
            post_documents = []

        # ====================================================
        # 8. TOTAL PROCESSING TIME
        # ====================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        print("\n" + "=" * 55)

        print(
            f"🏁 TOTAL REQUEST TIME: "
            f"{total_time:.2f} seconds"
        )

        print(
            f"🔍 OCR: "
            f"{doctr_time:.2f}s"
        )

        print(
            f"📋 Basic fields: "
            f"{field_time:.2f}s"
        )

        print(
            f"📑 Documents: "
            f"{document_time:.2f}s"
        )

        print(
            f"🌐 Translation: "
            f"{translation_time:.2f}s"
        )

        print("=" * 55)

        # ====================================================
        # 9. FINAL API RESPONSE
        # ====================================================

        response_data = {

            "success": True,

            "filename": file.filename,

            # Basic information
            "extracted_fields": final_result,

            # Tamil fields
            "translated_fields": translated_fields,

            # Prior documents
            "documents_prior_to_disbursal":
                prior_documents,

            # Post documents
            "documents_post_disbursal":
                post_documents,

            # Processing time
            "processing_time_seconds": round(
                total_time,
                2
            ),
        }

        # ====================================================
        # 10. RESPONSE SUMMARY
        # ====================================================

        print("\n")
        print(
            "========== FINAL API RESPONSE SUMMARY =========="
        )

        print(
            f"📄 File: {file.filename}"
        )

        print(
            f"📋 Basic fields: "
            f"{len(final_result)}"
        )

        print(
            f"📑 Prior documents: "
            f"{len(prior_documents)}"
        )

        print(
            f"📑 Post documents: "
            f"{len(post_documents)}"
        )

        print(
            f"⏱️ Total: "
            f"{total_time:.2f}s"
        )

        print(
            "================================================\n"
        )

        return response_data

    # ========================================================
    # HTTP EXCEPTION
    # ========================================================

    except HTTPException:
        raise

    # ========================================================
    # GENERAL EXCEPTION
    # ========================================================

    except Exception as exc:

        print("\n")
        print("❌ PROCESSING FAILED")
        print(
            f"Error: {exc}"
        )
        print("\n")

        raise HTTPException(
            status_code=500,
            detail=(
                f"Document processing failed: {exc}"
            ),
        ) from exc