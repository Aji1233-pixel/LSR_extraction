from fastapi import APIRouter, HTTPException, UploadFile
import time
import logging
import traceback

from core.extraction.doctr_engine import DocTREngine
from core.llm.freellm_client import FreeLLMClient
from core.llm.field_extractor import FieldExtractor
from core.llm.document_extractor import DocumentExtractor
from core.validation.validator import DocumentValidator
from core.translation.translator import TamilTranslator


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# ============================================================
# ROUTER
# ============================================================

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

# ------------------------------------------------------------
# OCR
# ------------------------------------------------------------

doctr_engine = DocTREngine()


# ------------------------------------------------------------
# Shared FreeLLM client
# ------------------------------------------------------------

freellm_client = FreeLLMClient()


# ------------------------------------------------------------
# Basic field extraction
# ------------------------------------------------------------

field_extractor = FieldExtractor(
    freellm_client
)


# ------------------------------------------------------------
# Prior/Post disbursal document extraction
# ------------------------------------------------------------

document_extractor = DocumentExtractor(
    freellm_client
)


# ------------------------------------------------------------
# Validation
# ------------------------------------------------------------

validator = DocumentValidator()


# ------------------------------------------------------------
# Tamil translation
# ------------------------------------------------------------

tamil_translator = TamilTranslator()


print("LSR extraction components initialized")
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
            f"File reading: "
            f"{file_time:.2f} seconds"
        )

        # ----------------------------------------------------
        # Empty file check
        # ----------------------------------------------------

        if not file_bytes:

            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        print(
            f"Filename: {file.filename}"
        )

        print(
            f"File size: "
            f"{len(file_bytes) / 1024:.2f} KB"
        )

        # ----------------------------------------------------
        # File size validation
        # ----------------------------------------------------

        MAX_FILE_SIZE = 20 * 1024 * 1024

        if len(file_bytes) > MAX_FILE_SIZE:

            raise HTTPException(
                status_code=400,
                detail=(
                    "File too large. "
                    "Maximum size is 20 MB."
                ),
            )

        # ====================================================
        # 2. DOCTR OCR
        # ====================================================

        print("\n")
        print("=" * 50)
        print("DOCTR OCR STARTED")
        print("=" * 50)

        doctr_start = time.perf_counter()

        try:

            raw_text = doctr_engine.extract_text(
                file_bytes=file_bytes,
                filename=file.filename,
            )

        except ValueError as exc:

            logger.error(
                f"OCR validation error: {exc}"
            )

            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except RuntimeError as exc:

            logger.error(
                f"OCR extraction failed: {exc}\n"
                f"{traceback.format_exc()}"
            )

            raise HTTPException(
                status_code=422,
                detail=(
                    "Could not extract text "
                    f"from document: {exc}"
                ),
            ) from exc

        doctr_time = (
            time.perf_counter()
            - doctr_start
        )

        print(
            f"DocTR OCR: "
            f"{doctr_time:.2f} seconds"
        )

        # ----------------------------------------------------
        # OCR result validation
        # ----------------------------------------------------

        if not raw_text or not raw_text.strip():

            raise HTTPException(
                status_code=422,
                detail=(
                    "No text could be extracted "
                    "from the uploaded document."
                ),
            )

        print(
            f"OCR characters: "
            f"{len(raw_text)}"
        )

        print(
            f"OCR words: "
            f"{len(raw_text.split())}"
        )

        # ====================================================
        # 3. BASIC FIELD EXTRACTION
        # ====================================================

        print("\n")
        print("=" * 50)
        print("BASIC FIELD EXTRACTION")
        print("=" * 50)

        field_start = time.perf_counter()

        try:

            extracted_data = (
                field_extractor.extract_fields(
                    raw_text
                )
            )

        except Exception as exc:

            logger.error(
                f"Field extraction failed: "
                f"{exc}\n"
                f"{traceback.format_exc()}"
            )

            raise RuntimeError(
                f"Field extraction failed: {exc}"
            ) from exc

        field_time = (
            time.perf_counter()
            - field_start
        )

        print(
            f"Basic field extraction: "
            f"{field_time:.2f} seconds"
        )

        # ====================================================
        # 4. DOCUMENT LIST EXTRACTION
        # ====================================================

        print("\n")
        print("=" * 50)
        print("DOCUMENT LIST EXTRACTION")
        print("=" * 50)

        document_start = time.perf_counter()

        try:

            document_data = (
                document_extractor.extract_documents(
                    raw_text
                )
            )

        except Exception as exc:

            logger.error(
                f"Document list extraction failed: "
                f"{exc}\n"
                f"{traceback.format_exc()}"
            )

            raise RuntimeError(
                f"Document list extraction failed: {exc}"
            ) from exc

        document_time = (
            time.perf_counter()
            - document_start
        )

        print(
            f"Document extraction: "
            f"{document_time:.2f} seconds"
        )

        # ====================================================
        # 5. VALIDATION
        # ====================================================

        print("\n")
        print("=" * 50)
        print("VALIDATION")
        print("=" * 50)

        validation_start = time.perf_counter()

        try:

            final_result = validator.validate(
                extracted_data
            )

        except Exception as exc:

            logger.error(
                f"Validation failed: "
                f"{exc}\n"
                f"{traceback.format_exc()}"
            )

            raise RuntimeError(
                f"Validation failed: {exc}"
            ) from exc

        validation_time = (
            time.perf_counter()
            - validation_start
        )

        print(
            f"Validation: "
            f"{validation_time:.2f} seconds"
        )

        # ====================================================
        # 6. TAMIL TRANSLATION
        # ====================================================

        print("\n")
        print("=" * 50)
        print("TAMIL TRANSLATION")
        print("=" * 50)

        translation_start = time.perf_counter()

        translated_fields = {}

        NO_TRANSLATE_FIELDS = {
            "lsr_date",
            "application_number",
        }

        # ----------------------------------------------------
        # Translate field by field
        # ----------------------------------------------------

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

                        translated_values.append(
                            None
                        )

                        continue

                    try:

                        translated_values.append(
                            tamil_translator.translate(
                                str(item)
                            )
                        )

                    except Exception as exc:

                        logger.warning(
                            f"Translation failed "
                            f"for {key}: {exc}"
                        )

                        # Keep original value
                        # instead of destroying data.
                        translated_values.append(
                            item
                        )

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

                logger.warning(
                    f"Translation failed "
                    f"for {key}: {exc}"
                )

                # IMPORTANT:
                # Keep English value if translation
                # fails instead of returning None.
                translated_fields[key] = value

        translation_time = (
            time.perf_counter()
            - translation_start
        )

        print(
            f"Tamil translation: "
            f"{translation_time:.2f} seconds"
        )

        # ====================================================
        # 7. SAFE DOCUMENT RESULTS
        # ====================================================

        if not isinstance(
            document_data,
            dict,
        ):

            document_data = {
                "documents_prior_to_disbursal": [],
                "documents_post_disbursal": [],
            }

        prior_documents = document_data.get(
            "documents_prior_to_disbursal",
            [],
        )

        post_documents = document_data.get(
            "documents_post_disbursal",
            [],
        )

        # ----------------------------------------------------
        # Ensure lists
        # ----------------------------------------------------

        if not isinstance(
            prior_documents,
            list,
        ):

            prior_documents = []

        if not isinstance(
            post_documents,
            list,
        ):

            post_documents = []

        # ====================================================
        # 8. TOTAL PROCESSING TIME
        # ====================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        print("\n")
        print("=" * 60)

        print(
            f"TOTAL REQUEST TIME: "
            f"{total_time:.2f} seconds"
        )

        print(
            f"OCR: "
            f"{doctr_time:.2f}s"
        )

        print(
            f"Basic fields: "
            f"{field_time:.2f}s"
        )

        print(
            f"Documents: "
            f"{document_time:.2f}s"
        )

        print(
            f"Validation: "
            f"{validation_time:.2f}s"
        )

        print(
            f"Translation: "
            f"{translation_time:.2f}s"
        )

        print("=" * 60)

        # ====================================================
        # 9. FINAL API RESPONSE
        # ====================================================

        response_data = {

            "success": True,

            "filename": file.filename,

            "extracted_fields": final_result,

            "translated_fields": translated_fields,

            "documents_prior_to_disbursal": (
                prior_documents
            ),

            "documents_post_disbursal": (
                post_documents
            ),

            "processing_time_seconds": round(
                total_time,
                2,
            ),
        }

        # ====================================================
        # 10. RESPONSE SUMMARY
        # ====================================================

        print("\n")
        print(
            "========== FINAL API RESPONSE =========="
        )

        print(
            f"File: {file.filename}"
        )

        print(
            f"Fields: {len(final_result)}"
        )

        print(
            f"Prior documents: "
            f"{len(prior_documents)}"
        )

        print(
            f"Post documents: "
            f"{len(post_documents)}"
        )

        print(
            f"Total time: "
            f"{total_time:.2f}s"
        )

        print(
            "========================================\n"
        )

        return response_data

    # ========================================================
    # HTTP EXCEPTION
    # ========================================================

    except HTTPException:
        raise

    # ========================================================
    # RUNTIME / LLM ERROR
    # ========================================================

    except RuntimeError as exc:

        error_message = str(exc)

        logger.error(
            f"Runtime error during processing: "
            f"{error_message}\n"
            f"{traceback.format_exc()}"
        )

        lowered = error_message.lower()

        # ----------------------------------------------------
        # LLM connection failure
        # ----------------------------------------------------

        if (
            "connect" in lowered
            or "connection" in lowered
        ):

            status_code = 503

            detail = (
                "AI service is unavailable. "
                "Please make sure the FreeLLM "
                "service is running."
            )

        # ----------------------------------------------------
        # Timeout
        # ----------------------------------------------------

        elif "timeout" in lowered:

            status_code = 504

            detail = (
                "AI service timed out. "
                "Please try again."
            )

        # ----------------------------------------------------
        # Other runtime error
        # ----------------------------------------------------

        else:

            status_code = 502

            detail = (
                f"AI processing failed: "
                f"{error_message}"
            )

        raise HTTPException(
            status_code=status_code,
            detail=detail,
        ) from exc

    # ========================================================
    # GENERAL EXCEPTION
    # ========================================================

    except Exception as exc:

        logger.error(
            f"Unexpected processing failure: "
            f"{exc}\n"
            f"{traceback.format_exc()}"
        )

        print("\n")
        print("PROCESSING FAILED")
        print(
            f"Error: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                f"Document processing failed: "
                f"{exc}"
            ),
        ) from exc