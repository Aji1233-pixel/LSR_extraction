from core.llm.freellm_client import FreeLLMClient


client = FreeLLMClient()

prompt = """
Extract the applicant name from this text.

Document:
Name of the Applicant: SHREE SHYAM BAJAJ

Return only the applicant name.
"""

result = client.generate(prompt)

print("\n========== FINAL RESULT ==========")
print(result)