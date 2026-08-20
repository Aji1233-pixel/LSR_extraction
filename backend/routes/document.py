from fastapi import APIRouter, HTTPException, UploadFile
import time

from core.extraction.doctr_engine import DocTREngine
from core.llm.ollama_client import OllamaClient
from core.llm.field_extractor import FieldExtractor
from core.llm.document_extractor import DocumentExtractor
from core.validation.validator import DocumentValidator


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

document_extractor = DocumentExtractor(
    ollama_client
)

validator = DocumentValidator()

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
        # DOCUMENT LIST EXTRACTION
        # ====================================================

        document_data = (
            document_extractor.extract_documents(
                raw_text
            )
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        final_result = validator.validate(
            extracted_data
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

            "extracted_fields": final_result,

            "documents_prior_to_disbursal":
                document_data[
                    "documents_prior_to_disbursal"
                ],

            "documents_post_disbursal":
                document_data[
                    "documents_post_disbursal"
                ],

            "processing_time_seconds": round(
                total_time,
                2
            ),
        }

    except HTTPException:
        raise

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