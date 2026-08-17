from fastapi import APIRouter, HTTPException, UploadFile
import time
from core.extraction.doctr_engine import DocTREngine
from core.llm.field_extractor import FieldExtractor
from core.validation.validator import DocumentValidator


router = APIRouter(
    prefix="/api",
    tags=["Document Extraction"],
)


# Load components once when backend starts.
doctr_engine = DocTREngine()
field_extractor = FieldExtractor()
validator = DocumentValidator()


@router.post("/extract")
def extract_document(file: UploadFile):

    total_start = time.perf_counter()

    print("\n")
    print("╔" + "═" * 48 + "╗")
    print("║        DOCUMENT EXTRACTION REQUEST          ║")
    print("╚" + "═" * 48 + "╝")

    try:

        # -------------------------------
        # File reading
        # -------------------------------

        file_start = time.perf_counter()

        file_bytes = file.file.read()

        file_time = time.perf_counter() - file_start

        print(
            f"⏱️ File reading: "
            f"{file_time:.2f} seconds"
        )

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # -------------------------------
        # DocTR
        # -------------------------------

        raw_text = doctr_engine.extract_text(
            file_bytes=file_bytes,
            filename=file.filename,
        )

        # -------------------------------
        # LLM
        # -------------------------------

        extracted_data = (
            field_extractor.extract_fields(
                raw_text
            )
        )

        # -------------------------------
        # Validation
        # -------------------------------

        final_result = validator.validate(
            extracted_data
        )

        # -------------------------------
        # Total
        # -------------------------------

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

        return {
            "success": True,
            "filename": file.filename,
            "extracted_fields": final_result,
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
            detail=f"Document processing failed: {exc}",
        ) from exc