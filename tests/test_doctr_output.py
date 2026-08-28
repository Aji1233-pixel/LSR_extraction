from pathlib import Path
import sys
import time

from core.extraction.doctr_engine import DocTREngine


# ============================================================
# CONFIGURATION
# ============================================================

PDF_PATH = Path("LSR_test_02.pdf")

OUTPUT_PATH = Path("doctr_raw_output.txt")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("              DocTR OCR OUTPUT TEST")
    print("=" * 70)

    # --------------------------------------------------------
    # Check input file
    # --------------------------------------------------------

    if not PDF_PATH.exists():

        print(
            f"\n❌ PDF not found:\n"
            f"{PDF_PATH.resolve()}"
        )

        print(
            "\nPut the PDF in the project root or "
            "change PDF_PATH in this file."
        )

        sys.exit(1)

    print(
        f"\n📄 Input file:"
        f"\n   {PDF_PATH.resolve()}"
    )

    print(
        f"\n💾 Output file:"
        f"\n   {OUTPUT_PATH.resolve()}"
    )

    # --------------------------------------------------------
    # Load DocTR
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("Loading DocTR...")
    print("-" * 70)

    start_time = time.perf_counter()

    doctr_engine = DocTREngine()

    model_time = time.perf_counter() - start_time

    print(
        f"✅ DocTR loaded in "
        f"{model_time:.2f} seconds"
    )

    # --------------------------------------------------------
    # Read PDF
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("Reading PDF...")
    print("-" * 70)

    with open(
        PDF_PATH,
        "rb"
    ) as file:

        file_bytes = file.read()

    print(
        f"📦 File size: "
        f"{len(file_bytes) / 1024:.2f} KB"
    )

    # --------------------------------------------------------
    # OCR
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("Running DocTR OCR...")
    print("-" * 70)

    ocr_start = time.perf_counter()

    raw_text = doctr_engine.extract_text(
        file_bytes=file_bytes,
        filename=PDF_PATH.name,
    )

    ocr_time = (
        time.perf_counter()
        - ocr_start
    )

    # --------------------------------------------------------
    # Validate output
    # --------------------------------------------------------

    if raw_text is None:

        print(
            "\n❌ DocTR returned None."
        )

        sys.exit(1)

    if not isinstance(raw_text, str):

        print(
            "\n❌ DocTR did not return a string."
        )

        print(
            f"Returned type: "
            f"{type(raw_text)}"
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    characters = len(raw_text)

    words = len(raw_text.split())

    lines = raw_text.splitlines()

    non_empty_lines = [
        line
        for line in lines
        if line.strip()
    ]

    print("\n" + "=" * 70)
    print("              DOCTR OUTPUT SUMMARY")
    print("=" * 70)

    print(
        f"\n⏱️ OCR time       : {ocr_time:.2f} seconds"
    )

    print(
        f"📝 Characters     : {characters}"
    )

    print(
        f"📝 Words          : {words}"
    )

    print(
        f"📄 Total lines    : {len(lines)}"
    )

    print(
        f"📄 Non-empty lines: {len(non_empty_lines)}"
    )

    # --------------------------------------------------------
    # Save exact output
    # --------------------------------------------------------

    OUTPUT_PATH.write_text(
        raw_text,
        encoding="utf-8",
    )

    print(
        f"\n✅ Raw OCR output saved to:"
        f"\n   {OUTPUT_PATH.resolve()}"
    )

    # --------------------------------------------------------
    # Show first 100 lines
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("              FIRST 100 OCR LINES")
    print("=" * 70)

    for index, line in enumerate(
        lines[:100],
        start=1,
    ):

        print(
            f"{index:03d} | {line!r}"
        )

    # --------------------------------------------------------
    # Show exact Python representation
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("              RAW STRING REPRESENTATION")
    print("=" * 70)

    print(
        repr(raw_text[:3000])
    )

    print("\n" + "=" * 70)
    print("                    COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()