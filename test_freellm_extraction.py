import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = os.getenv(
    "FREELLM_BASE_URL",
    "http://127.0.0.1:31415/v1"
)

API_KEY = os.getenv("FREELLM_API_KEY")

MODEL = "gemini-3-flash-preview"


sample_text = """
KANSAL LAW ASSOCIATES
SANJAY KANSAL
ADVOCATE

Dated: 17/01/2025

APP. NO. SME000014806684

To,
Bajaj Finance Limited,
Bhiwani

Subject: Legal Opinion in respect of Property having PID 3CVAUEG4.

1. Name of the Applicant/ Borrower/s:
SHREE SHYAM BAJAJ

2. Name of the Co - Applicant/ Borrower/s:
VIKRANT WASON, ABHINANDAN WASON

3. Name of the Property Owner:
VIKRANT WASON

Property Address and Description:
Property having PID 3CVAUEG4 bearing a share 11/42
Baqdar OK-11M of Tadadi 2K-2M of Khewat No. 962
Khatoni No. 1097 Khasra No. 177//7/2 (2-2).

Total land of 1K-2M-3Sarsai of Waka Vidhya Nagar,
Maham Road Bhiwani Lohad Tehsil & District Bhiwani.
"""


prompt = f"""
Extract the requested fields from the document.

Rules:
- Return ONLY valid JSON.
- Use exactly the field names below.
- Do not add fields.
- Do not invent information.
- Use null when a field is not found.
- Preserve the document's values.

Required fields:
lsr_date
company_name
applicant_name
co_applicant_name
property_owner
application_number
property_description

Document:
{sample_text}
"""


headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


payload = {
    "model": MODEL,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0
}


print("=" * 60)
print("        FREELLM EXTRACTION TEST")
print("=" * 60)

print(f"Model: {MODEL}")

start = time.perf_counter()

response = requests.post(
    f"{BASE_URL}/chat/completions",
    headers=headers,
    json=payload,
    timeout=300
)

elapsed = time.perf_counter() - start

print(f"\n⏱️ API time: {elapsed:.2f} seconds")
print(f"HTTP status: {response.status_code}")

response.raise_for_status()

data = response.json()

result = data["choices"][0]["message"]["content"]

print("\n========== RAW RESPONSE ==========")
print(result)
print("==================================")

try:

    parsed = json.loads(result)

    print("\n========== PARSED JSON ==========")
    print(json.dumps(
        parsed,
        indent=2,
        ensure_ascii=False
    ))
    print("=================================")

except json.JSONDecodeError:

    print("\n⚠️ Model did not return valid JSON.")