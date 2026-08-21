import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.translation.translator import TamilTranslator


translator = TamilTranslator()

samples = [
    "Property Owner",
    "Applicant Name",
    "Bajaj Finance Limited",
    "SHREE SHYAM BAJAJ",
    "VIKRANT WASON",
    "Property Description"
]

for text in samples:
    tamil = translator.translate(text)

    print("\nEnglish :", text)
    print("Tamil   :", tamil)