from core.llm.ollama_client import OllamaClient
from core.llm.document_extractor import DocumentExtractor


sample_text = """
22. Steps / Documents Prior to disbursal: Documents Must to Have

1
Sale Deed No. 10462 dated 03/01/2025 executed by
Manoj Kumar S/o Sh. Gyan Chand in favour of
Sh. Vikrant Wason

2
Sale Deed No. 4169 dated 01/08/2023 executed by
Sh. Subhash Chander S/o Sh. Asha Nand &
Vikrant S/o Sh. Bishambhar Dayal Singh in favour
of Sh. Manoj Kumar Tageja

5
Mutation No. 42236 entered in favour of Vikrant
S/o Sh. Bishambhar Dayal Singh

23. Documents required post disbursal: N.A
"""


client = OllamaClient()

extractor = DocumentExtractor(client)

result = extractor.extract_documents(sample_text)

print("\n========== FINAL RESULT ==========")

print(result)