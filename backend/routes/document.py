from fastapi import APIRouter, HTTPException, UploadFile
import time
import concurrent.futures
import traceback
import logging

from core.extraction.doctr_engine import DocTREngine
from core.llm.freellm_client import FreeLLMClient
from core.llm.field_extractor import FieldExtractor
from core.llm.document_extractor import DocumentExtractor
from core.validation.validator import DocumentValidator
from core.translation.translator import TamilTranslator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api",
    tags=["Document Extraction"],
)


# ============================================================
# LOAD COMPONENTS ONCE WHEN BACKEND STARTS
# ============================================================

# ============================================================
# LOAD COMPONENTS ONCE WHEN BACKEND STARTS
# ============================================================

doctr_engine = DocTREngine()

freellm_client = FreeLLMClient()

field_extractor = FieldExtractor(freellm_client)

document_extractor = DocumentExtractor(freellm_client)

validator = DocumentValidator()

# Pass the LLM client directly to TamilTranslator
tamil_translator = TamilTranslator(freellm_client=freellm_client)

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

        # Validate file size (max 20 MB)
        MAX_FILE_SIZE = 20 * 1024 * 1024
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=(
                    "File too large. Maximum size is "
                    f"{MAX_FILE_SIZE // (1024*1024)} MB."
                )
            )

        # ====================================================
        # DOCTR OCR
        # ====================================================

        try:
            raw_text = doctr_engine.extract_text(
                file_bytes=file_bytes,
                filename=file.filename,
            )
        except ValueError as exc:
            # Unsupported file type etc.
            logger.error(f"OCR validation error: {exc}")
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc
        except RuntimeError as exc:
            # OCR could not extract any text
            logger.error(
                f"OCR extraction failed: {exc}\n"
                f"{traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=422,
                detail=(
                    "Could not extract text from document: "
                    f"{exc}"
                ),
            ) from exc

        # ====================================================
        # PARALLEL EXTRACTION (Fields + Documents)
        # ====================================================

        extract_start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_fields = executor.submit(field_extractor.extract_fields, raw_text)
            future_docs = executor.submit(document_extractor.extract_documents, raw_text)

            extracted_data = future_fields.result()
            document_data = future_docs.result()

        extract_time = time.perf_counter() - extract_start

        print(
            f"Parallel extraction: "
            f"{extract_time:.2f} seconds"
        )

        # DEBUG: Print extracted data
        print(f"DEBUG extracted_data: {extracted_data}")

        # ====================================================
        # VALIDATION
        # ====================================================

        final_result = validator.validate(
            extracted_data
        )

        # ====================================================
        # TAMIL TRANSLATION (Skip dates, numbers, IDs)
        # ====================================================

        translated_fields = {}
        translation_start = time.perf_counter()

        # Fields that should NOT be translated (dates, IDs, numbers)
        NO_TRANSLATE_FIELDS = {
            "lsr_date",
            "application_number",
        }

        try:
            for key, value in final_result.items():
                if value and isinstance(value, str) and value.strip():
                    # Skip translation for dates and numbers
                    if key in NO_TRANSLATE_FIELDS:
                        translated_fields[key] = value
                    else:
                        try:
                            translated_fields[key] = tamil_translator.translate(value)
                        except Exception as field_exc:
                            # Per-field graceful failure: keep English value
                            logger.warning(
                                f"Translation failed for '{key}': {field_exc}"
                            )
                            translated_fields[key] = value
                else:
                    translated_fields[key] = None
        except Exception as exc:
            print(f"⚠️ Translation failed: {exc}")
            # Fall back to English values rather than nulling everything
            translated_fields = dict(final_result)

        translation_time = time.perf_counter() - translation_start
        print(f"⏱️ Tamil translation: {translation_time:.2f} seconds")

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

            "translated_fields": translated_fields,

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

    except concurrent.futures.TimeoutError as exc:
        logger.error(
            f"Extraction timeout: {exc}\n{traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=504,
            detail="Document processing timed out. Please try again.",
        ) from exc

    except RuntimeError as exc:
        # LLM failures, connection errors etc.
        error_message = str(exc)
        logger.error(
            f"Runtime error during processing: "
            f"{error_message}\n{traceback.format_exc()}"
        )

        lowered = error_message.lower()

        if "timed out" in lowered or "timeout" in lowered:
            status_code = 504
            detail = "AI service timed out. Please try again."
        elif "connect" in lowered:
            status_code = 503
            detail = (
                "AI service is unavailable. Please make sure "
                "the LLM service is running."
            )
        else:
            status_code = 502
            detail = f"AI processing failed: {error_message}"

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        ) from exc

    except Exception as exc:

        logger.error(
            f"Unexpected processing failure: {exc}\n"
            f"{traceback.format_exc()}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Document processing failed: {exc}"
            ),
        ) from exc