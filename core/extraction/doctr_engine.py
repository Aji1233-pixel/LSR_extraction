from pathlib import Path

from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import time

class DocTREngine:
    """Handles document text extraction using docTR."""

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".tif",
        ".tiff",
    }

    def __init__(self):
        print("Loading DocTR model...")

        self.predictor = ocr_predictor(
            pretrained=True
        )

        print("DocTR model loaded.")

    def extract_text(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> str:

        total_start = time.perf_counter()

        print("\n" + "=" * 50)
        print("DOCUMENT PROCESSING STARTED")
        print("=" * 50)

        print(f"📄 File: {filename}")
        print(f"📦 File size: {len(file_bytes) / 1024:.2f} KB")

        extension = Path(filename).suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}"
            )

        # -------------------------------
        # Document loading
        # -------------------------------

        load_start = time.perf_counter()

        if extension == ".pdf":
            document = DocumentFile.from_pdf(file_bytes)
        else:
            document = DocumentFile.from_images(file_bytes)

        load_time = time.perf_counter() - load_start

        print(
            f"⏱️ Document loading: {load_time:.2f} seconds"
        )

        # -------------------------------
        # DocTR OCR
        # -------------------------------

        ocr_start = time.perf_counter()

        result = self.predictor(document)

        ocr_time = time.perf_counter() - ocr_start

        print(
            f"⏱️ DocTR OCR: {ocr_time:.2f} seconds"
        )

        # -------------------------------
        # Render OCR text
        # -------------------------------

        render_start = time.perf_counter()

        text = result.render()

        render_time = time.perf_counter() - render_start

        print(
            f"⏱️ OCR text rendering: "
            f"{render_time:.2f} seconds"
        )

        if not text or not text.strip():
            raise RuntimeError(
                "DocTR could not extract any text."
            )

        print(
            f"📝 Extracted characters: {len(text)}"
        )

        print(
            f"📝 Extracted words: {len(text.split())}"
        )

        total_time = time.perf_counter() - total_start

        print(
            f"⏱️ Total DocTR processing: "
            f"{total_time:.2f} seconds"
        )

        print("=" * 50)

        return text