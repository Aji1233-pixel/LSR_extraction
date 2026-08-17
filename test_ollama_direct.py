import ollama
import json


text = """
Dated:17/01/2025
APP. NO. SME000014806684

To,
Bajaj Finance Limited,
Bhiwani

1. Name of the Applicant / Borrower/s: SHREE SHYAM BAJAJ

2. Name of the Co-Applicant / Borrower/s:
VIKRANT WASON, ABHINANDAN WASON

3. Name of the Property Owner: VIKRANT WASON

Property Address and Description:
Property having PID 3CVAUEG4 bearing a share 11/42
of Khewat No. 962 Khatoni No. 1097 Khasra No. 177//7/2.
Total land of 1K-2M-3Sarsai.
"""


prompt = f"""
Extract the following fields from the document.

Return ONLY JSON.

The JSON MUST contain ALL these keys:

{{
  "lsr_date": null,
  "company_name": null,
  "applicant_name": null,
  "co_applicant_name": null,
  "property_owner": null,
  "application_number": null,
  "property_description": null
}}

Rules:
- Extract values directly from the document.
- Do not invent values.
- If a value is genuinely absent, use null.
- Do not add extra keys.
- Do not provide explanations.

Document:
{text}
"""


print("Sending request to Ollama...")

response = ollama.chat(
    model="qwen2.5:3b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    format="json",
    options={
        "temperature": 0
    }
)

raw_response = response["message"]["content"]

print("\n========== RAW RESPONSE ==========")
print(raw_response)
print("==================================")

try:
    result = json.loads(raw_response)

    print("\n========== PARSED RESULT ==========")
    print(json.dumps(result, indent=2))
    print("===================================")

except json.JSONDecodeError as e:
    print("\nInvalid JSON:")
    print(e)