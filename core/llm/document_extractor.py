import json
import re
import time

from .ollama_client import OllamaClient


class DocumentExtractor:
    """Extracts documents required before and after loan disbursal."""

    # Compiled Regex Patterns
    RE_DATE_DATED = re.compile(
        r"\s+dated\s*:?\s*\d{1,2}[./-]\d{1,2}[./-]\d{2,4}", re.IGNORECASE
    )
    RE_DOC_NUMBER = re.compile(r"\s+No\.?\s*[A-Za-z0-9/-]+", re.IGNORECASE)
    RE_TRAILING_DATE = re.compile(r"\s+\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$")
    RE_EXTRACT_DATE = re.compile(r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}")
    RE_HAS_DIGIT = re.compile(r"\d")

    # Static Lookups
    INVALID_PHRASES = (
        "issued by",
        "in the name of",
        "executed by",
        "in favour of",
        "in favor of",
        "original",
        "xerox",
        "photocopy",
        "online",
        "certified",
        "not specified",
    )

    COPY_TYPES = {
        "original": "Original",
        "xerox": "Xerox",
        "photocopy": "Photocopy",
        "certified copy": "Certified Copy",
        "certified": "Certified",
        "online copy": "Online Copy",
        "online": "Online",
    }

    INVALID_DETAILS = {
        "null",
        "none",
        "n/a",
        "na",
        "not specified",
        "not available",
    }

    def __init__(self):
        self.ollama = OllamaClient()

    def _build_prompt(self, text: str) -> str:
        return f"""
Extract ONLY the documents listed under these two sections:

1. Steps / Documents Prior to disbursal
2. Documents required post disbursal

Ignore:

- List of all Documents that were perused and verified
- Documents mentioned elsewhere in the legal report
- Documents from tracing of title
- Documents from other sections

For every document return exactly these fields:

- document_name
- document_number
- document_date
- document_copy_type
- additional_details


============================================================
DOCUMENT SEPARATION RULES
============================================================

1. Treat every listed document as an independent record.

2. Information belongs ONLY to the document it is explicitly
   associated with.

3. NEVER copy information from one document to another.

4. NEVER carry a date from the previous document to the next document.

5. NEVER carry a number from the previous document to the next document.

6. NEVER carry an "issued by", "in the name of", "executed by",
   or similar description from one document to another.


============================================================
DOCUMENT NAME
============================================================

7. document_name must contain ONLY the actual document name.

8. Do NOT include the document date in document_name.

9. Do NOT include the document number in document_name.

10. Remove phrases such as:

    dated 25-09-1998
    dated 05-02-2001
    No.2867/1998

Example:

Source:
Partition Deed No.2867/1998 dated 25-09-1998

Correct:

"document_name": "Partition Deed"


============================================================
DOCUMENT NUMBER
============================================================

11. document_number must contain ONLY an actual document number
    or reference number.

12. Examples of valid document numbers:

    2867/1998
    123/2020
    4567
    Doc.No.1234

13. The following are NOT document numbers:

    issued by Greater Chennai Corporation
    issued by Tahsildar, Egmore Taluk
    in the name of Vasantha Kumar
    executed by Mrs.Indumathi
    executed by Mrs.Bhuvaneshwari
    in favour of Vastu Housing Finance Corporation Limited

14. If no actual document number exists:

    "document_number": null


============================================================
DOCUMENT DATE
============================================================

15. document_date must contain ONLY an actual date.

16. Preserve the date exactly as written in the source.

17. If the document does not explicitly contain a date:

    "document_date": null

18. NEVER infer a date.

19. NEVER copy a date from another document.

20. A date belongs ONLY to the document to which it is explicitly
    associated.


============================================================
DOCUMENT COPY TYPE
============================================================

21. document_copy_type represents how the document copy is provided
    in the LSR.

Possible values include:

    Original
    Xerox
    Photocopy
    Certified Copy
    Certified
    Online Copy
    Online

22. Extract the value exactly as stated in the source.

23. Do NOT guess the copy type.

24. Do NOT copy the copy type from another document.

25. If the copy type is not explicitly available:

    "document_copy_type": null

26. IMPORTANT:

    "Original", "Xerox", "Online", etc. MUST NEVER be placed inside
    document_number.

    They belong ONLY in document_copy_type.


============================================================
ADDITIONAL DETAILS
============================================================

27. additional_details contains useful descriptive/reference
    information that does NOT belong in:

    - document_name
    - document_number
    - document_date
    - document_copy_type

28. Examples:

    issued by Greater Chennai Corporation

    issued by Tahsildar, Egmore Taluk

    in the name of Mr.Vasantha Kumar

    executed by Mrs.Indumathi

    executed by Mrs.Bhuvaneshwari and Mrs.Malini

    in favour of Vastu Housing Finance Corporation Limited

29. IMPORTANT:

    additional_details should be preserved whenever such information
    is explicitly associated with the document.

30. Do NOT move descriptive information into document_number.

31. Do NOT move descriptive information into document_date.

32. Do NOT move descriptive information into document_copy_type.

33. If there is no useful additional information:

    "additional_details": null


============================================================
MISSING VALUES
============================================================

34. Never guess.

35. Never infer.

36. Use null when information is not explicitly available.

37. Missing document number:

    "document_number": null

38. Missing document date:

    "document_date": null

39. Missing copy type:

    "document_copy_type": null

40. Missing additional information:

    "additional_details": null


============================================================
IMPORTANT EXAMPLES
============================================================

Example 1:

Source:

Partition Deed No.2867/1998 dated 25-09-1998
Original

Output:

{{
    "document_name": "Partition Deed",
    "document_number": "2867/1998",
    "document_date": "25-09-1998",
    "document_copy_type": "Original",
    "additional_details": null
}}


Example 2:

Source:

Town Survey Field Register Extract dated 05-02-2001
in the name of Mr.Vasantha Kumar
Original

Output:

{{
    "document_name": "Town Survey Field Register Extract",
    "document_number": null,
    "document_date": "05-02-2001",
    "document_copy_type": "Original",
    "additional_details": "in the name of Mr.Vasantha Kumar"
}}


Example 3:

Source:

Death Certificate of Vasantha Kumar
issued by Greater Chennai Corporation
Online

Output:

{{
    "document_name": "Death Certificate of Vasantha Kumar",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Online",
    "additional_details": "issued by Greater Chennai Corporation"
}}


Example 4:

Source:

Legal Heir-Ship Certificate of Vasantha Kumar
issued by Tahsildar, Egmore Taluk
Online

Output:

{{
    "document_name": "Legal Heir-Ship Certificate of Vasantha Kumar",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Online",
    "additional_details": "issued by Tahsildar, Egmore Taluk"
}}


Example 5:

Source:

Property Tax Receipt
in the name of Vasantha Kumar
Xerox

Output:

{{
    "document_name": "Property Tax Receipt",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Xerox",
    "additional_details": "in the name of Vasantha Kumar"
}}


Example 6:

Source:

Proposed MODTD in favour of Vastu Housing Finance Corporation Limited
Original

Output:

{{
    "document_name": "Proposed MODTD",
    "document_number": null,
    "document_date": null,
    "document_copy_type": "Original",
    "additional_details": "in favour of Vastu Housing Finance Corporation Limited"
}}


============================================================
FINAL JSON STRUCTURE
============================================================

Return ONLY this JSON structure:

{{
    "documents_prior_to_disbursal": [
        {{
            "document_name": "...",
            "document_number": null,
            "document_date": null,
            "document_copy_type": null,
            "additional_details": null
        }}
    ],

    "documents_post_disbursal": [
        {{
            "document_name": "...",
            "document_number": null,
            "document_date": null,
            "document_copy_type": null,
            "additional_details": null
        }}
    ]
}}

Do NOT return markdown.
Do NOT return explanations.
Return valid JSON only.


============================================================
DOCUMENT TEXT
============================================================

{text}
""".strip()

    def _parse_response(self, response: str) -> dict:
        if not response or not response.strip():
            raise RuntimeError("Document extractor returned an empty response.")

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"Document extractor returned invalid JSON: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError("Document extractor response must be a JSON object.")

        return data

    def _clean_document_name(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        if not val:
            return None

        # Clean "dated <date>" and "dated: <date>" via single precompiled pattern
        val = self.RE_DATE_DATED.sub("", val)
        val = self.RE_DOC_NUMBER.sub("", val)
        val = self.RE_TRAILING_DATE.sub("", val)

        val = val.strip(" -,:;")
        return val if val else None

    def _is_valid_document_number(self, value) -> bool:
        if not value:
            return False

        val = str(value).strip()
        if not val:
            return False

        lower = val.lower()
        if any(phrase in lower for phrase in self.INVALID_PHRASES):
            return False

        return bool(self.RE_HAS_DIGIT.search(val))

    def _clean_document_date(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        if not val:
            return None

        match = self.RE_EXTRACT_DATE.search(val)
        return match.group(0) if match else None

    def _clean_copy_type(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        return self.COPY_TYPES.get(val.lower())

    def _clean_additional_details(self, value) -> str | None:
        if not value:
            return None

        val = str(value).strip()
        if not val or val.lower() in self.INVALID_DETAILS:
            return None

        return val

    def _normalize_document(self, document: dict) -> dict | None:
        if not isinstance(document, dict):
            return None

        cleaned_name = self._clean_document_name(document.get("document_name"))
        cleaned_date = self._clean_document_date(document.get("document_date"))
        cleaned_copy = self._clean_copy_type(document.get("document_copy_type"))
        cleaned_details = self._clean_additional_details(
            document.get("additional_details")
        )

        doc_num = None
        original_number = document.get("document_number")

        if self._is_valid_document_number(original_number):
            doc_num = str(original_number).strip()
        elif original_number:
            invalid_num = str(original_number).strip()
            if invalid_num:
                if cleaned_details:
                    if invalid_num.lower() not in cleaned_details.lower():
                        cleaned_details = f"{cleaned_details}; {invalid_num}"
                else:
                    cleaned_details = invalid_num

        return {
            "document_name": self._clean_document_name(cleaned_name),
            "document_number": doc_num,
            "document_date": cleaned_date,
            "document_copy_type": cleaned_copy,
            "additional_details": cleaned_details,
        }

    def _normalize_documents(self, documents: list) -> list[dict]:
        if not isinstance(documents, list):
            return []

        normalized = []
        for doc in documents:
            cleaned = self._normalize_document(doc)
            if cleaned is not None:
                normalized.append(cleaned)

        return normalized

    def extract_documents(self, text: str) -> dict:
        if not text or not text.strip():
            raise ValueError("OCR text cannot be empty.")

        print("\n" + "=" * 55)
        print("DOCUMENT LIST EXTRACTION STARTED")
        print("=" * 55)
        print(f"📝 Input characters: {len(text)}")
        print(f"📝 Input words: {len(text.split())}")

        # Prompt construction
        start = time.perf_counter()
        prompt = self._build_prompt(text)
        print(f"⏱️ Prompt construction: {time.perf_counter() - start:.2f} seconds")
        print(f"📝 Prompt characters: {len(prompt)}")

        # Ollama call
        start = time.perf_counter()
        response = self.ollama.generate(prompt)
        print(f"⏱️ Ollama response: {time.perf_counter() - start:.2f} seconds")
        print("\n========== RAW DOCUMENT RESPONSE ==========")
        print(response)
        print("============================================")

        # Parse JSON
        start = time.perf_counter()
        data = self._parse_response(response)
        print(f"⏱️ JSON parsing: {time.perf_counter() - start:.2f} seconds")

        # Normalize
        prior_docs = self._normalize_documents(
            data.get("documents_prior_to_disbursal", [])
        )
        post_docs = self._normalize_documents(data.get("documents_post_disbursal", []))

        result = {
            "documents_prior_to_disbursal": prior_docs,
            "documents_post_disbursal": post_docs,
        }

        # Debug logs
        print("\n========== CLEAN DOCUMENT RESULT ==========")
        print(json.dumps(result, indent=4, ensure_ascii=False))
        print("============================================")
        print(f"📋 Prior-disbursal documents: {len(prior_docs)}")
        print(f"📋 Post-disbursal documents: {len(post_docs)}")
        print("=" * 55)

        return result