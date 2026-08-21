from fastapi import APIRouter, HTTPException, UploadFile
import time

from core.extraction.doctr_engine import DocTREngine
from core.llm.ollama_client import OllamaClient
from core.llm.field_extractor import FieldExtractor
from core.llm.document_extractor import DocumentExtractor
from core.validation.validator import DocumentValidator
from core.translation.translator import TamilTranslator


router = APIRouter(
    prefix="/api",
    tags=["Document Extraction"],
)


# ============================================================
# LOAD COMPONENTS ONCE WHEN BACKEND STARTS
# ============================================================

doctr_engine = DocTREngine()

ollama_client = OllamaClient()

field_extractor = FieldExtractor()

# IMPORTANT:
# DocumentExtractor creates its own OllamaClient.
# Do NOT pass ollama_client here.
document_extractor = DocumentExtractor()

validator = DocumentValidator()

translator = TamilTranslator()


# ============================================================
# TRANSLATION
# ============================================================

def translate_fields(fields: dict) -> dict:
    """
    Translate only the basic extracted fields into Tamil.

    Document lists are intentionally NOT translated.
    """

    translated_fields = {}

    for field_name, value in fields.items():

        if value is None:
            translated_fields[field_name] = None
            continue

        if isinstance(value, list):

            translated_fields[field_name] = [
                translator.translate(str(item))
                for item in value
            ]

            continue

        if not str(value).strip():
            translated_fields[field_name] = None
            continue

        try:

            translated_fields[field_name] = (
                translator.translate(
                    str(value)
                )
            )

        except Exception as exc:

            print(
                f"⚠️ Translation failed for "
                f"{field_name}: {exc}"
            )

            translated_fields[field_name] = None

    return translated_fields


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
        # FILE READING
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

        # ====================================================
        # DOCTR OCR
        # ====================================================

        print("\n" + "=" * 50)
        print("DOCUMENT PROCESSING STARTED")
        print("=" * 50)

        raw_text = doctr_engine.extract_text(
            file_bytes=file_bytes,
            filename=file.filename,
        )

        # ====================================================
        # BASIC FIELD EXTRACTION
        # ====================================================

        extracted_data = (
            field_extractor.extract_fields(
                raw_text
            )
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        validated_data = validator.validate(
            extracted_data
        )

        # ====================================================
        # TRANSLATION
        # ====================================================

        print("\n" + "=" * 50)
        print("TRANSLATION STARTED")
        print("=" * 50)

        translation_start = time.perf_counter()

        translated_fields = translate_fields(
            validated_data
        )

        translation_time = (
            time.perf_counter()
            - translation_start
        )

        print(
            f"⏱️ Translation: "
            f"{translation_time:.2f} seconds"
        )

        print("=" * 50)

        # ====================================================
        # DOCUMENT LIST EXTRACTION
        # ====================================================

        document_data = (
            document_extractor.extract_documents(
                raw_text
            )
        )

        # ====================================================
        # TOTAL PROCESSING TIME
        # ====================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        print("\n" + "=" * 50)
        print(
            f"🏁 TOTAL REQUEST TIME: "
            f"{total_time:.2f} seconds"
        )
        print("=" * 50 + "\n")

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "success": True,

            "filename": file.filename,

            # ----------------------------------------------
            # BASIC INFORMATION - ENGLISH
            # ----------------------------------------------

            "extracted_fields": validated_data,

            # ----------------------------------------------
            # BASIC INFORMATION - TAMIL
            # ----------------------------------------------

            "translated_fields": translated_fields,

            # ----------------------------------------------
            # DOCUMENTS PRIOR TO DISBURSAL
            # ----------------------------------------------

            "documents_prior_to_disbursal":
                document_data[
                    "documents_prior_to_disbursal"
                ],

            # ----------------------------------------------
            # DOCUMENTS POST DISBURSAL
            # ----------------------------------------------

            "documents_post_disbursal":
                document_data[
                    "documents_post_disbursal"
                ],

            # ----------------------------------------------
            # PROCESSING TIME
            # ----------------------------------------------

            "processing_time_seconds": round(
                total_time,
                2
            ),
        }

    # ========================================================
    # HTTP ERROR
    # ========================================================

    except HTTPException:
        raise

    # ========================================================
    # GENERAL ERROR
    # ========================================================

    except Exception as exc:

        print(
            f"❌ Processing failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Document processing failed: {exc}"
            ),
        ) from exc