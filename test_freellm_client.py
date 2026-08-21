from core.llm.freellm_client import call_llm


prompt = """
Extract the applicant name from this text.

Document text:

Applicant Name: SHREE SHYAM BAJAJ
Property Owner: VIKRANT WASON

Return only the applicant name.
"""


print("\n======================================")
print("      FREELLMAPI CLIENT TEST")
print("======================================")

result = call_llm(prompt)

print("\n========== FINAL RESULT ==========")
print(result)
print("==================================")